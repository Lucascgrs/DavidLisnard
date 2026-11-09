"""YouTube : API officielle Data v3 (dates exactes), avec la clé de config/cles.json.

À chaque lancement :
1. on liste les vidéos du périmètre (toutes celles d'une chaîne, ou celles qui parlent de Lisnard) ;
2. on demande leur nombre de commentaires (50 vidéos pour 1 unité de quota) ;
3. on lit une vidéo si elle est nouvelle, si elle a gagné des commentaires, ou si elle a moins de N jours ;
4. pour une vidéo relue, on ne redemande les réponses que des fils qui en ont gagné.
"""
import time
from datetime import datetime, timedelta, timezone

import requests

from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import cles, perimetre
from commun.textes import contient, date_paris

API = "https://www.googleapis.com/youtube/v3/"
COUT = {"search": 100}  # les autres appels coûtent 1 unité
QUOTA_JOUR = 10_000


class QuotaAtteint(Exception):
    pass


class Api:
    def __init__(self, cle: str, journal):
        self.cle, self.journal = cle, journal
        self.unites = 0
        self.session = requests.Session()
        self.session.headers["Accept-Language"] = "fr-FR,fr"

    def appel(self, methode: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None} | {"key": self.cle}
        for essai in range(6):
            try:
                r = self.session.get(API + methode, params=params, timeout=40)
            except requests.RequestException as e:  # le réseau d'ici coupe parfois
                attente = 5 * (essai + 1)
                self.journal(f"    réseau : {type(e).__name__}, nouvel essai dans {attente} s")
                time.sleep(attente)
                continue
            self.unites += COUT.get(methode, 1)
            if r.status_code == 200:
                return r.json()
            raisons = {e.get("reason") for e in r.json().get("error", {}).get("errors", [])} if r.content else set()
            if "quotaExceeded" in raisons or "dailyLimitExceeded" in raisons:
                raise QuotaAtteint()
            if raisons & {"commentsDisabled", "videoNotFound", "forbidden", "channelNotFound",
                          "playlistNotFound", "notFound"}:
                return {"_erreur": sorted(raisons)[0]}
            if r.status_code in (500, 502, 503, 429):
                time.sleep(5 * (essai + 1))
                continue
            raise SourceImpossible(f"API YouTube : HTTP {r.status_code} {sorted(raisons)} sur {methode}")
        raise SourceImpossible(f"API YouTube injoignable après 6 essais ({methode}).")

    def pages(self, methode: str, **params):
        jeton = None
        while True:
            d = self.appel(methode, pageToken=jeton, **params)
            if "_erreur" in d:
                yield d
                return
            yield d
            jeton = d.get("nextPageToken")
            if not jeton:
                return


# --- Découverte des vidéos ------------------------------------------------------

def videos_toutes(api: Api, chaine: dict, etat_chaine: dict) -> list[str]:
    """Toutes les vidéos de la chaîne via sa playlist « uploads ». Après la première fois,
    on s'arrête dès qu'une page entière ne contient que des vidéos déjà connues."""
    uploads = "UU" + chaine["id"][2:]
    connues = set(etat_chaine.get("videos", []))
    trouvees = []
    for page in api.pages("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50):
        if "_erreur" in page:
            return trouvees
        ids = [it["contentDetails"]["videoId"] for it in page.get("items", [])]
        trouvees += ids
        if etat_chaine.get("complet") and ids and all(i in connues for i in ids):
            break
    etat_chaine["complet"] = True  # la liste a été parcourue jusqu'au bout au moins une fois
    return trouvees


def videos_mention(api: Api, chaine: dict, etat_chaine: dict, mot: str) -> list[str]:
    """Vidéos de la chaîne trouvées par la recherche YouTube du mot-clé (100 unités par page de 50).
    Après la première fois, seulement celles publiées depuis la dernière recherche (moins 3 jours de marge)."""
    depuis = None
    if etat_chaine.get("recherche_le"):
        d = datetime.fromisoformat(etat_chaine["recherche_le"]) - timedelta(days=3)
        depuis = d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    debut = datetime.now(timezone.utc).isoformat(timespec="seconds")
    trouvees = []
    for page in api.pages("search", part="id", channelId=chaine["id"], q=mot, type="video",
                          order="date", maxResults=50, publishedAfter=depuis):
        if "_erreur" in page:
            break
        trouvees += [it["id"]["videoId"] for it in page.get("items", []) if it["id"].get("videoId")]
    etat_chaine["recherche_le"] = debut
    return trouvees


def details(api: Api, ids: list[str]) -> dict[str, dict]:
    sortie = {}
    for i in range(0, len(ids), 50):
        d = api.appel("videos", part="snippet,statistics", id=",".join(ids[i:i + 50]), maxResults=50)
        for it in d.get("items", []):
            s, st = it["snippet"], it.get("statistics", {})
            sortie[it["id"]] = {
                "titre": s.get("title", ""), "description": s.get("description", ""),
                "date": s.get("publishedAt", ""), "chaine": s.get("channelTitle", ""),
                "commentaires": int(st["commentCount"]) if "commentCount" in st else None,
                "live": s.get("liveBroadcastContent", "none"),
            }
    return sortie


# --- Lecture des commentaires ------------------------------------------------------

def _ligne(c: dict, video_id: str, video: dict, type_: str, parent: str | None) -> dict:
    s = c["snippet"]
    return {
        "publication_id": video_id, "publication_titre": video["titre"],
        "publication_lien": f"https://www.youtube.com/watch?v={video_id}",
        "publication_date": date_paris(video["date"]),
        "commentaire_id": c["id"], "type": type_, "parent_id": parent or "",
        "auteur": s.get("authorDisplayName", ""),
        "auteur_id": (s.get("authorChannelId") or {}).get("value", ""),
        "date": date_paris(s.get("publishedAt")), "date_exacte": "oui",
        "texte": s.get("textOriginal") or s.get("textDisplay", ""),
        "likes": s.get("likeCount", ""),
    }


def commentaires_video(api: Api, depot, compte: str, video_id: str, video: dict) -> tuple[list[dict], str | None]:
    lignes = []
    for page in api.pages("commentThreads", part="snippet,replies", videoId=video_id, maxResults=100,
                          textFormat="plainText", order="time"):
        if "_erreur" in page:
            return lignes, page["_erreur"]
        for fil in page.get("items", []):
            haut = fil["snippet"]["topLevelComment"]
            lignes.append(_ligne(haut, video_id, video, PRINCIPAL, None))
            nb = fil["snippet"].get("totalReplyCount", 0)
            incluses = (fil.get("replies") or {}).get("comments", [])
            if nb and len(incluses) >= nb:
                lignes += [_ligne(r, video_id, video, REPONSE, haut["id"]) for r in incluses]
            elif nb and nb > depot.reponses_connues(compte, haut["id"]):
                for p in api.pages("comments", part="snippet", parentId=haut["id"], maxResults=100,
                                   textFormat="plainText"):
                    if "_erreur" in p:
                        break
                    lignes += [_ligne(r, video_id, video, REPONSE, haut["id"]) for r in p.get("items", [])]
    return lignes, None


# --- Collecte ------------------------------------------------------------------

def collecter(depot, journal) -> dict:
    cle = cles().get("youtube", "").strip()
    if not cle:
        raise SourceImpossible("Pas de clé YouTube : la mettre dans config/cles.json ({\"youtube\": \"…\"}).")
    p = perimetre()
    conf, mot = p["youtube"], p.get("mot_cle", "Lisnard")
    jours = conf.get("relire_si_moins_de_jours", 30)
    api = Api(cle, journal)
    etat = depot.etat.setdefault("chaines", {})
    vues = depot.etat.setdefault("videos", {})  # id → {commentaires, lu_le, ferme}
    details_bilan, quota = [], False
    limite = datetime.now(timezone.utc) - timedelta(days=jours)

    try:
        for chaine in conf["chaines"]:
            depot.verifier_arret()
            ec = etat.setdefault(chaine["id"], {"nom": chaine["nom"], "videos": []})
            if chaine["regle"] == "toutes":
                ids = videos_toutes(api, chaine, ec)
            else:
                ids = videos_mention(api, chaine, ec, mot)
            anciennes = set(ec["videos"])
            tous = list(dict.fromkeys(ec["videos"] + ids))
            infos = details(api, tous)
            if chaine["regle"] == "mention":  # la recherche YouTube ramène du bruit : on garde la règle stricte
                tous = [i for i in tous if i in infos and
                        contient(infos[i]["titre"] + " " + infos[i]["description"], mot)]
            nouvelles = [i for i in tous if i not in anciennes]
            ec["videos"] = tous
            depot.sauver_etat()
            a_lire = []
            for vid in tous:
                v, deja = infos.get(vid), vues.get(vid)
                if not v or v["live"] != "none":
                    continue
                if deja is None:
                    a_lire.append(vid)
                elif v["commentaires"] is not None and v["commentaires"] > deja.get("commentaires", 0):
                    a_lire.append(vid)
                elif v["date"] and datetime.fromisoformat(v["date"].replace("Z", "+00:00")) > limite:
                    a_lire.append(vid)
            journal(f"  {chaine['nom']} : {len(tous)} vidéos dans le périmètre "
                    f"({len(nouvelles)} nouvelles), {len(a_lire)} à lire")
            for n, vid in enumerate(a_lire, 1):
                depot.verifier_arret()
                v = infos[vid]
                if v["commentaires"] == 0:
                    vues[vid] = {"commentaires": 0, "lu_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                    continue
                lignes, erreur = commentaires_video(api, depot, chaine["nom"], vid, v)
                ajoutes = depot.ajouter(chaine["nom"], lignes)
                vues[vid] = {"commentaires": v["commentaires"] or 0,
                             "lu_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                if erreur:
                    vues[vid]["ferme"] = erreur
                depot.sauver_etat()
                journal(f"    [{n}/{len(a_lire)}] {v['titre'][:70]} : {len(lignes)} lus, {ajoutes} nouveaux"
                        f" ({v['commentaires']} annoncés){' — ' + erreur if erreur else ''}")
    except QuotaAtteint:
        quota = True
        depot.sauver_etat()
        journal("  quota YouTube du jour atteint : la suite sera reprise au prochain lancement")

    fermees = sum(1 for v in vues.values() if v.get("ferme") == "commentsDisabled")
    details_bilan.append(f"{len(vues)} vidéos lues au total, dont {fermees} aux commentaires fermés")
    details_bilan.append(f"quota utilisé pendant ce lancement : environ {api.unites} unités sur {QUOTA_JOUR}")
    return {"details": details_bilan,
            "message": "Quota du jour atteint : la collecte reprendra au prochain lancement." if quota else "",
            "statut": "partiel (quota)" if quota else "ok"}
