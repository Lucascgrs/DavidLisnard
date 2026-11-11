"""Bluesky : API publique (api.bsky.app), sans compte ni clé.

On cherche le mot-clé dans tous les messages publics (app.bsky.feed.searchPosts), puis on lit les réponses.

Ce qui est pris :
- chaque message qui contient le mot-clé ;
- sous un message de tête (pas une réponse) qui le contient : toutes les réponses du fil, comme les commentaires sous
  une vidéo qui parle de lui ;
- sous une réponse qui le contient : les réponses à cette réponse.

Comment c'est rangé (mêmes colonnes que les autres sources) :
- un seul compte, « Recherche « Lisnard » », donc un seul fichier ;
- la « publication » est le message de tête du fil : son texte sert de titre aux réponses (le message de tête
  lui-même n'a pas de titre : son texte est déjà le commentaire) ;
- type « principal » pour un message de tête, « réponse » sinon, avec parent_id = le message auquel il répond (qui
  n'est pas toujours collecté : une réponse qui cite Lisnard sous un message qui n'en parle pas) ;
- commentaire_id = « did/rkey », par exemple « did:plc:abc…/3kxyz… » : de quoi retrouver le message
  (https://bsky.app/profile/<did>/post/<rkey>).

À chaque lancement :
1. recherche des messages publiés depuis la dernière recherche (moins un jour de marge) ; la première fois, on
   remonte jusqu'à « depuis » (config/perimetre.json), au plus « pages_par_lancement » pages de 100 par lancement ;
2. relecture des messages de moins de « relire_si_moins_de_jours » jours : « j'aime » et nouvelles réponses ;
3. lecture du fil de chaque message qui a gagné des réponses.
etat.json garde les messages encore à suivre : ceux dont le fil n'a pas été lu (arrêt en cours de route) et ceux
qui sont assez récents pour être relus.

L'API refuse la pagination par curseur sans compte (403) : on avance par dates, avec « until ».
"""
import time
from datetime import datetime, timedelta, timezone

import requests

from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import perimetre
from commun.textes import abreger, contient, date_paris

API = "https://api.bsky.app/xrpc/"
TYPE_MESSAGE = "app.bsky.feed.post"
PAUSE = 0.15  # secondes entre deux appels : très en dessous de la limite (3 000 appels par 5 minutes)


def nom_compte(mot: str) -> str:
    return f"Recherche « {mot} »"


class Api:
    def __init__(self, journal):
        self.journal = journal
        self.appels = 0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "collecte-commentaires/1.0"

    def appel(self, methode: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        for essai in range(6):
            time.sleep(PAUSE)
            try:
                r = self.session.get(API + methode, params=params, timeout=40)
            except requests.RequestException as e:
                attente = 5 * (essai + 1)
                self.journal(f"    réseau : {type(e).__name__}, nouvel essai dans {attente} s")
                time.sleep(attente)
                continue
            self.appels += 1
            if r.status_code == 200:
                return r.json()
            if r.status_code == 400 and "NotFound" in r.text:  # message supprimé depuis la recherche
                return {"_erreur": "introuvable"}
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(float(r.headers.get("retry-after", 0) or 0) or 10 * (essai + 1))
                continue
            raise SourceImpossible(f"API Bluesky : HTTP {r.status_code} sur {methode} ({r.text[:120]})")
        raise SourceImpossible(f"API Bluesky injoignable après 6 essais ({methode}).")


# --- Identifiants, dates et lignes ------------------------------------------------------------------------------------

def identifiant(uri: str) -> str:
    """« at://did:plc:abc/app.bsky.feed.post/3kxyz » → « did:plc:abc/3kxyz »."""
    did, _, rkey = uri.removeprefix("at://").split("/")
    return f"{did}/{rkey}"


def adresse(ident: str) -> str:
    did, rkey = ident.split("/")
    return f"at://{did}/{TYPE_MESSAGE}/{rkey}"


def lien(ident: str) -> str:
    did, rkey = ident.split("/")
    return f"https://bsky.app/profile/{did}/post/{rkey}"


def _iso(d: datetime) -> str:
    d = d.astimezone(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


def _date(texte) -> datetime | None:
    """La date d'un message (écrite par l'application de son auteur : parfois absente ou fantaisiste)."""
    try:
        d = datetime.fromisoformat(str(texte).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _paris(texte) -> str:
    d = _date(texte)
    return date_paris(d) if d else ""


def _racine(post: dict) -> str | None:
    """Adresse du message de tête du fil, ou None si ce message est lui-même une tête."""
    return ((post["record"].get("reply") or {}).get("root") or {}).get("uri")


def _ligne(post: dict, tete: dict | None) -> dict:
    """La ligne d'un message. tete : {id, texte, date} du message de tête de son fil (None si c'est lui)."""
    r = post["record"]
    ident = identifiant(post["uri"])
    parent = ((r.get("reply") or {}).get("parent") or {}).get("uri")
    auteur = post.get("author", {})
    pub = tete or {"id": ident, "texte": "", "date": r.get("createdAt")}
    return {
        "publication_id": pub["id"], "publication_titre": abreger(pub["texte"], 300),
        "publication_lien": lien(pub["id"]), "publication_date": _paris(pub["date"]),
        "commentaire_id": ident, "type": REPONSE if parent else PRINCIPAL,
        "parent_id": identifiant(parent) if parent else "",
        "auteur": auteur.get("displayName") or auteur.get("handle", ""), "auteur_id": auteur.get("did", ""),
        "date": _paris(r.get("createdAt")), "date_exacte": "oui",
        "texte": r.get("text", ""), "likes": post.get("likeCount", ""),
    }


# --- Recherche et fils ------------------------------------------------------------------------------------------------

def chercher(api: Api, mot: str, depuis: datetime, avant: datetime | None, pages: int):
    """Messages contenant le mot, des plus récents aux plus anciens, entre deux dates.
    Renvoie (messages, date du plus ancien, vrai si la recherche est allée au bout)."""
    trouves, vus = [], set()
    for _ in range(pages):
        d = api.appel("app.bsky.feed.searchPosts", q=mot, sort="latest", limit=100, since=_iso(depuis),
                      until=_iso(avant) if avant else None)
        posts = d.get("posts", [])
        nouveaux = [p for p in posts if p["uri"] not in vus]
        dates = [x for x in (_date(p["record"].get("createdAt")) for p in nouveaux) if x]
        if not nouveaux or not dates:
            return trouves, avant, True
        vus.update(p["uri"] for p in nouveaux)
        trouves += nouveaux
        avant = min(dates)  # on repart du plus ancien message de la page (« until » le rend à nouveau : il est écarté)
        # Une page peut compter moins de 100 messages sans être la dernière (98 ou 99, constaté le 2026-11-11) :
        # la dernière est celle qui n'annonce pas de suite, ou qui ne ramène rien de nouveau.
        if not d.get("cursor"):
            return trouves, avant, True
    return trouves, avant, False


def reponses_du_fil(api: Api, uri: str) -> list[dict]:
    """Toutes les réponses sous un message, à toute profondeur (les messages supprimés ou bloqués sont ignorés)."""
    d = api.appel("app.bsky.feed.getPostThread", uri=uri, depth=1000, parentHeight=0)
    sortie = []

    def descendre(noeud):
        for r in noeud.get("replies") or []:
            if r.get("post") and r["post"].get("record"):
                sortie.append(r["post"])
                descendre(r)

    descendre(d.get("thread") or {})
    return sortie


def messages(api: Api, uris: list[str]) -> dict[str, dict]:
    """Les messages demandés, par adresse (25 par appel) ; ceux qui ont disparu sont absents."""
    sortie = {}
    for i in range(0, len(uris), 25):
        d = api.appel("app.bsky.feed.getPosts", uris=uris[i:i + 25])
        sortie.update({p["uri"]: p for p in d.get("posts", [])})
    return sortie


# --- Collecte ---------------------------------------------------------------------------------------------------------

def collecter(depot, journal) -> dict:
    p = perimetre()
    conf, mot = p.get("bluesky") or {}, p.get("mot_cle", "Lisnard")
    compte = nom_compte(mot)
    api = Api(journal)
    pages = int(conf.get("pages_par_lancement", 60))
    jours = int(conf.get("relire_si_moins_de_jours", 7))
    depuis = datetime.fromisoformat(conf.get("depuis", "2025-01-01")).replace(tzinfo=timezone.utc)
    etat = depot.etat.setdefault("recherche", {})
    suivis = depot.etat.setdefault("messages", {})  # id → {date, reponses, lu} des messages encore à suivre
    debut = datetime.now(timezone.utc)

    # 1. Les messages qui citent le mot-clé : les nouveaux, puis la suite de l'arriéré.
    trouves = []
    if etat.get("le"):
        apres = max(depuis, _date(etat["le"]) - timedelta(days=1))
        recents, _, fini = chercher(api, mot, apres, None, pages)
        trouves += recents
        pages -= max(1, -(-len(recents) // 100))
        if not fini:
            journal(f"  plus de {len(recents)} messages récents : la suite au prochain lancement")
    else:
        etat["arriere"], etat["complet"] = None, False
    etat["le"] = debut.isoformat(timespec="seconds")
    if not etat.get("complet") and pages > 0:
        anciens, plus_ancien, fini = chercher(api, mot, depuis, _date(etat.get("arriere")), pages)
        trouves += anciens
        if plus_ancien:
            etat["arriere"] = plus_ancien.isoformat()
        etat["complet"] = fini
        journal(f"  arriéré remonté jusqu'au {(etat.get('arriere') or '')[:10]}" + (" (terminé)" if fini else ""))
    trouves = {identifiant(x["uri"]): x for x in trouves if contient(x["record"].get("text", ""), mot)}
    journal(f"  {len(trouves)} messages trouvés par la recherche « {mot} »")

    # 2. Les messages déjà suivis : récents (réponses et « j'aime » à mettre à jour) ou dont le fil reste à lire.
    limite = (debut - timedelta(days=jours)).isoformat()
    a_revoir = [i for i in suivis if i not in trouves]
    revus = {identifiant(u): m for u, m in messages(api, [adresse(i) for i in a_revoir]).items()}
    for i in set(a_revoir) - set(revus):  # supprimé par son auteur depuis
        del suivis[i]
    candidats = trouves | revus

    # Le texte des messages de tête, qui sert de titre aux réponses.
    tetes = {x["uri"]: x for x in candidats.values() if not _racine(x)}
    tetes.update(messages(api, sorted({_racine(x) for x in candidats.values()} - set(tetes) - {None})))

    def tete_de(post: dict) -> dict | None:
        racine = _racine(post)
        if not racine:
            return None
        t = tetes.get(racine)
        return {"id": identifiant(racine), "texte": t["record"].get("text", "") if t else "",
                "date": t["record"].get("createdAt") if t else None}

    ajoutes = depot.ajouter(compte, [_ligne(x, tete_de(x)) for x in trouves.values()])
    depot.ajouter(compte, [_ligne(x, tete_de(x)) for x in revus.values()])  # déjà enregistrés : « j'aime » seulement
    for i, x in trouves.items():
        # Une date absente ou dans le futur (horloge de l'auteur) compte comme « maintenant ».
        date = min(_date(x["record"].get("createdAt")) or debut, debut).astimezone(timezone.utc)
        suivis.setdefault(i, {"date": date.isoformat(), "reponses": 0})
    depot.sauver_etat()

    # 3. Les réponses, sous chaque message qui en a gagné depuis sa dernière lecture.
    a_lire = [i for i, x in candidats.items() if (x.get("replyCount") or 0) > suivis[i].get("reponses", 0)]
    journal(f"  {ajoutes} nouveaux messages, {len(revus)} messages récents revus, {len(a_lire)} fils à lire")
    n_reponses = 0
    for n, i in enumerate(a_lire, 1):
        depot.verifier_arret()
        x = candidats[i]
        tete = tete_de(x) or {"id": i, "texte": x["record"].get("text", ""), "date": x["record"].get("createdAt")}
        n_reponses += depot.ajouter(compte, [_ligne(r, tete) for r in reponses_du_fil(api, x["uri"])])
        suivis[i].update(reponses=x.get("replyCount") or 0, lu=True)
        if n % 25 == 0 or n == len(a_lire):
            depot.sauver_etat()
            journal(f"    [{n}/{len(a_lire)}] fils lus, {n_reponses} réponses nouvelles")
    # Tout est lu : on ne garde que les messages assez récents pour être relus au prochain lancement.
    for i in [i for i, v in suivis.items() if v.get("date", "") < limite]:
        del suivis[i]
    for v in suivis.values():
        v["lu"] = True
    depot.sauver_etat()
    return {"details": [f"{len(trouves)} messages citant « {mot} », dont {ajoutes} nouveaux ; {len(a_lire)} fils lus, "
                        f"{n_reponses} réponses nouvelles",
                        "arriéré " + ("terminé" if etat.get("complet") else
                                      f"remonté jusqu'au {(etat.get('arriere') or '?')[:10]}"),
                        f"{api.appels} appels à l'API publique de Bluesky (gratuite, sans compte)"]}
