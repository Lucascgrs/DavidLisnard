"""Facebook : les groupes publics qui parlent de David Lisnard et sa Page officielle (config/perimetre.json, rubrique
« facebook » : « groupes » et « pages »).

Meta a fermé l'API des groupes en avril 2024 : il n'y a plus de voie officielle. On envoie, avec les cookies du compte
de collecte (sessions/facebook_cookies.json, créé par « python -m collecte.connexion_facebook »), les mêmes requêtes
internes que le site de Facebook, par la bibliothèque facebook-gql-scraper. Aucun navigateur ne s'ouvre pendant la
collecte. Trois corrections de cette bibliothèque (classe Client) : pages demandées avec des en-têtes de navigation
(sinon HTTP 400), jeton fb_dtsg lu aussi sous sa forme « DTSGInitialData », et pas de fausse « session expirée » sur
les fichiers statiques de fbcdn.net (ils répondent toujours « logged-out »).

Ce qui est pris, dans chaque groupe : chaque post (sa ligne a un titre vide, son texte est le commentaire, comme le
message de tête d'un fil Bluesky), chaque commentaire sous le post (type « principal », titre = texte du post) et
chaque réponse à un commentaire (type « réponse », parent_id = le commentaire). Les autocollants et images sans texte
sont laissés de côté. Un fichier par groupe : donnees/facebook/<nom du groupe>.csv.

Le fil d'un groupe se lit du plus récent au plus ancien (ordre chronologique, 3 posts par requête) ; les commentaires
aussi (tous, sans le filtre « plus pertinents »), environ 8 par requête, plus une requête par commentaire qui a des
réponses. À chaque lancement :
1. le récent : du haut du fil jusqu'aux posts de plus de « relire_si_moins_de_jours » jours (ou jusqu'à la frontière
   de l'arriéré si elle est plus haute). Un post jamais lu est lu en entier ; un post déjà lu n'est relu que si son
   nombre de commentaires a augmenté, et seulement jusqu'à retomber sur 10 commentaires déjà connus d'affilée ;
2. l'arriéré : on reprend le fil à la frontière (curseur gardé dans etat.json) et on descend jusqu'à « depuis ». Le
   temps restant est partagé entre les groupes dont l'arriéré n'est pas fini.

Rythme (config/perimetre.json), pour ne pas faire bloquer le compte sans traîner : une pause tirée au hasard entre
deux requêtes (« pause_entre_requetes_s », 1,5 à 3 s, soit environ 1 500 requêtes à l'heure, le rythme d'une lecture
humaine soutenue), une pause longue toutes les « pause_longue.toutes_les_requetes » requêtes, au plus
« minutes_par_lancement » minutes par lancement et « requetes_par_jour » requêtes par jour (compteur dans etat.json).
Mesures du 2026-11-12 : suivre le nouveau des deux groupes demande environ 1 000 requêtes par jour (environ 3 000
commentaires) ; l'arriéré depuis le 2026-07-31, environ 50 000 requêtes, soit une dizaine de jours au quota.
Le moindre signe de freinage (limite de débit, blocage temporaire, erreur HTTP 429 ou 5xx) arrête le lancement, et la
source se repose « repos_apres_freinage_heures » heures. Une session expirée relance seule la connexion (Chrome visible, config/facebook.env) une fois ; une
vérification demandée par Facebook rend la source « impossible » jusqu'à une connexion à la main.
"""
import logging
import random
import re
import time
from datetime import datetime, timedelta, timezone

from collecte.connexion_facebook import (FICHIER_COOKIES, NAVIGATEUR, NAVIGATION, ErreurConnexion, connecter,
                                         lire_cookies, sauver_cookies)
from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import SESSIONS, perimetre
from commun.textes import abreger, date_paris

FICHIER_ETAT_GQL = SESSIONS / "facebook_gql_etat.json"  # identifiants des requêtes internes et jeton, en cache
DELAI_S = 60  # attente maximale d'une réponse de Facebook
CONNUS_DAFFILEE = 10  # relecture d'un post : on s'arrête après 10 commentaires déjà connus d'affilée
# Réponses de Facebook qui signalent un freinage ou une vérification (codes d'erreur de l'API interne).
FREINAGE = re.compile(r'"(?:error|code)":\s*(?:1675004|1675007|368)\b|rate limit|temporarily blocked|'
                      r"temporairement bloqu|trop vite|going too fast", re.I)
VERIFICATION = re.compile(r'"(?:error|code)":\s*(?:1357001|1357004|1348007)\b|/checkpoint/', re.I)


class Freinage(Exception):
    """Facebook freine ou bloque passagèrement : on arrête ce lancement, la source se repose."""


class Budget(Exception):
    """Le temps de ce lancement (ou de la part d'un groupe) ou le nombre de requêtes du jour est atteint."""

    def __init__(self, jour: bool):
        super().__init__("quota du jour atteint" if jour else "temps écoulé")
        self.jour = jour


def _client(depot, conf, journal):
    """La bibliothèque n'est importée qu'ici : son absence ne gêne pas les autres sources."""
    try:
        import facebook_gql_scraper as fgs
        from facebook_gql_scraper.exceptions import DtsgTokenFetchError, SessionExpiredError
    except ImportError:
        raise SourceImpossible("Bibliothèque absente : python -m pip install -r requirements.txt "
                               "(facebook-gql-scraper).")
    logging.getLogger("facebook_gql_scraper").setLevel(logging.ERROR)

    class Client(fgs.FacebookContext):
        def __init__(self):
            super().__init__(cookies_file=str(FICHIER_COOKIES), state_file=str(FICHIER_ETAT_GQL),
                             user_agent=NAVIGATEUR, quiet=True)
            self.session.hooks["response"].append(self._controler)
            # La bibliothèque n'impose aucun délai : une connexion que Facebook laisse ouverte sans répondre a figé
            # une collecte (2026-11-12). Chaque requête a donc 60 s au plus, et deux nouveaux essais.
            envoyer = self.session.request

            def avec_delai(method, url, **kw):
                import requests
                kw.setdefault("timeout", DELAI_S)
                for essai in range(3):
                    try:
                        return envoyer(method, url, **kw)
                    except (requests.Timeout, requests.ConnectionError) as e:
                        if essai == 2:
                            raise Freinage(f"Facebook ne répond plus ({type(e).__name__})")
                        time.sleep(30 * (essai + 1))
            self.session.request = avec_delai
            pmin, pmax = conf.get("pause_entre_requetes_s", [1.5, 3.0])
            longue = conf.get("pause_longue") or {}
            self.pause = (float(pmin), float(pmax))
            self.longue_toutes = int(longue.get("toutes_les_requetes", 150))
            self.longue = tuple(float(x) for x in longue.get("secondes", [60, 120]))
            self.par_jour = int(conf.get("requetes_par_jour", 6000))
            self.limite = float("inf")  # heure (time.time) où le lancement ou la part du groupe s'arrête
            self.requetes = 0
            self._derniere = 0.0

        # --- Corrections de la bibliothèque ---
        def get(self, url):
            r = self.session.get(url, headers={**NAVIGATION, "content-type": None, "origin": None, "priority": None})
            # fbcdn.net (fichiers statiques, sans cookies) répond toujours « set-login: logged-out ».
            if "facebook.com" in url.split("/")[2] and self._check_session_dead(r):
                raise SessionExpiredError("Facebook Cookies are expired.")
            return r

        def _get_fb_dtsg(self):
            if self.fb_dtsg:
                return self.fb_dtsg
            html = self.get("https://www.facebook.com/").text
            if VERIFICATION.search(html[:200000]) and '"USER_ID":"0"' in html:
                raise SourceImpossible("Facebook demande une vérification du compte : lancer "
                                       "« python -m collecte.connexion_facebook » et y répondre dans la fenêtre.")
            m = (re.search(r'\{"name":"fb_dtsg","value":"([^"]+)"\}', html)
                 or re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', html))
            if not m:
                if '"USER_ID":"0"' in html or "c_user" not in self.session.cookies:
                    raise SessionExpiredError("Facebook Cookies are expired.")
                raise DtsgTokenFetchError("Could not find fb_dtsg")
            self.fb_dtsg = m.group(1)
            self._save_state()
            return self.fb_dtsg

        # --- Rythme et quotas : avant chaque requête interne (les nouveaux essais de la bibliothèque compris) ---
        def post(self, *args, **kwargs):
            jour = depot.etat.setdefault("jour", {})
            aujourdhui = datetime.now().strftime("%Y-%m-%d")
            if jour.get("date") != aujourdhui:
                jour.update(date=aujourdhui, requetes=0)
            if jour["requetes"] >= self.par_jour:
                raise Budget(jour=True)
            if self.requetes and self.requetes % self.longue_toutes == 0:
                time.sleep(max(0.0, min(random.uniform(*self.longue), self.limite - time.time())))
            attente = self._derniere + random.uniform(*self.pause) - time.time()
            if attente > 0:
                time.sleep(attente)
            if time.time() >= self.limite:  # après les pauses : un lancement ne déborde pas de son temps
                raise Budget(jour=False)
            self._derniere = time.time()
            self.requetes += 1
            jour["requetes"] += 1
            return super().post(*args, **kwargs)

        def _controler(self, r, *_, **__):
            """Chaque réponse de facebook.com : un freinage ou une vérification arrête tout de suite."""
            if "facebook.com" not in r.url:
                return
            if "/checkpoint" in r.url:
                raise SourceImpossible("Facebook demande une vérification du compte : lancer "
                                       "« python -m collecte.connexion_facebook » et y répondre dans la fenêtre.")
            if r.status_code == 429 or r.status_code >= 500:
                raise Freinage(f"Facebook répond HTTP {r.status_code}")
            if "/api/graphql" in r.url:
                debut = r.text[:4000]
                if VERIFICATION.search(debut):
                    raise SourceImpossible("Facebook demande une vérification du compte : lancer "
                                           "« python -m collecte.connexion_facebook » et y répondre dans la fenêtre.")
                if ('"errors"' in debut or '"error"' in debut) and FREINAGE.search(debut):
                    raise Freinage(f"Facebook freine les requêtes ({abreger(debut, 160)})")

        def garder_cookies(self):
            """Les cookies renouvelés par Facebook pendant la collecte remplacent les anciens."""
            neufs = {c.name: c.value for c in self.session.cookies if "facebook.com" in (c.domain or "")}
            if neufs.get("c_user") and neufs.get("xs"):
                anciens = {c["name"]: c["value"] for c in lire_cookies()}
                anciens.update(neufs)
                sauver_cookies([{"name": k, "value": v} for k, v in anciens.items()])

    return fgs, SessionExpiredError, Client


# --- Lignes ---------------------------------------------------------------------------------------------------------

_TITRE_MD = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+", re.M)


def _texte(d: dict) -> str:
    """Le texte tel qu'écrit : la bibliothèque rend la mise en forme des posts en Markdown (« # **Titre** »), on
    retire ces marques (les hashtags, collés à leur mot, restent)."""
    return _TITRE_MD.sub("", (d.get("text") or "").replace("**", "")).strip()


def _lien(url: str | None, suivi: dict, pid: str) -> str:
    defaut = (f"https://www.facebook.com/groups/{suivi['id']}/permalink/{pid}/" if suivi["type"] == "groupe"
              else f"https://www.facebook.com/{suivi['id']}/posts/{pid}/")
    return (url or defaut).replace("://web.facebook.com", "://www.facebook.com")


def _pub(post: dict, suivi: dict) -> dict:
    return {"publication_id": str(post["id"]), "publication_titre": abreger(_texte(post), 300),
            "publication_lien": _lien(post.get("url"), suivi, str(post["id"])),
            "publication_date": date_paris(int(post["creation_time"])) if post.get("creation_time") else ""}


def _ligne(d: dict, pub: dict, parent: str = "") -> dict:
    auteur = d.get("author") or {}
    return {**pub, "commentaire_id": str(d["id"]), "type": REPONSE if parent else PRINCIPAL, "parent_id": parent,
            "auteur": auteur.get("name") or "", "auteur_id": str(auteur.get("id") or ""),
            "date": date_paris(int(d["creation_time"])) if d.get("creation_time") else "", "date_exacte": "oui",
            "texte": _texte(d), "likes": d.get("reaction_count", "")}


def _ligne_post(post: dict, pub: dict) -> dict:
    return {**_ligne(post, pub), "publication_titre": ""}  # le post est lui-même le commentaire


# --- Lecture d'un groupe --------------------------------------------------------------------------------------------

class Lecteur:
    def __init__(self, fgs, client, depot, journal, conf):
        self.fgs, self.client, self.depot, self.journal = fgs, client, depot, journal
        self.depuis = datetime.fromisoformat(conf.get("depuis", "2026-07-31")).replace(tzinfo=timezone.utc).timestamp()
        self.limite_relire = time.time() - int(conf.get("relire_si_moins_de_jours", 7)) * 86400
        self.lus = self.nouveaux = 0

    def lire_post(self, p, compte: str, suivi: dict, etat_post: dict | None) -> int:
        """Lit un post (en entier s'il n'a jamais été lu jusqu'au bout, sinon jusqu'aux commentaires déjà connus).
        Renvoie le nombre de lignes nouvelles. Le post n'est marqué lu qu'une fois sa lecture finie."""
        d = p._data
        pub = _pub(d, suivi)
        relecture = etat_post is not None
        lignes = [_ligne_post(d, pub)] if _texte(d) else []
        connus, daffilee = set(self.depot.connus(compte)), 0
        try:
            for c in (p.get_comments() if int(d.get("comments_count") or 0) else ()):
                cd = c._data
                daffilee = daffilee + 1 if relecture and str(cd["id"]) in connus else 0
                if _texte(cd):
                    lignes.append(_ligne(cd, pub))
                if int(cd.get("reply_count") or 0) > self.depot.reponses_connues(compte, str(cd["id"])):
                    for r in c.get_replies():
                        if _texte(r._data):
                            lignes.append(_ligne(r._data, pub, parent=str(cd["id"])))
                if relecture and daffilee >= CONNUS_DAFFILEE:
                    break
        finally:
            # Même interrompue (temps écoulé, freinage), une lecture garde ce qu'elle a lu ; le post, lui, ne sera
            # marqué lu qu'à la fin d'une lecture complète.
            ajoutes = self.depot.ajouter(compte, lignes)
            self.nouveaux += ajoutes
        self.lus += 1
        return ajoutes

    def parcourir(self, suivi: dict, etat: dict, arriere: bool) -> str:
        """Un passage dans le fil du groupe : le récent (arriere=False) ou la suite de l'arriéré. Renvoie la raison
        de l'arrêt (« fini », « relu », « arriéré terminé »…). Les exceptions Budget et Freinage remontent ; l'état
        est enregistré après chaque post."""
        compte = suivi["nom"]
        cls = self.fgs.Group if suivi["type"] == "groupe" else self.fgs.Profile  # une Page se lit comme un profil
        it = cls(self.client, {"id": str(suivi["id"])}).get_posts()
        frontiere = etat.get("frontiere")  # où l'arriéré s'est arrêté : {curseur, tampon, date}
        if arriere:
            if etat.get("complet") or not frontiere:
                return "rien"
            it._cursor, it._raw_buffer = frontiere["curseur"], list(frontiere.get("tampon") or [])
            it._exhausted = not frontiere["curseur"] and not frontiere.get("tampon")
        posts = etat.setdefault("posts", {})  # posts de moins de N jours déjà lus : {id: {date, annonces}}
        vus = 0
        for p in it:
            self.depot.verifier_arret()
            d = p._data
            pid, date = str(d.get("id")), int(d.get("creation_time") or 0)
            vus += 1
            if not arriere and (date < self.limite_relire or (frontiere and date <= frontiere["date"])):
                return "récent lu"
            if date and date < self.depuis:
                etat.update(complet=True, frontiere=None)
                return "arriéré terminé"
            annonces = int(d.get("comments_count") or 0)
            deja = posts.get(pid)
            if deja is None or annonces > deja.get("annonces", 0):
                n = self.lire_post(p, compte, suivi, deja)
                posts[pid] = {"date": date, "annonces": annonces}
                if n:
                    self.journal(f"    {compte} : post du {date_paris(date)[:16]}, {annonces} commentaires annoncés, "
                                 f"{n} lignes nouvelles")
            # Au-delà de la frontière (ou à la première lecture), la frontière descend avec nous.
            if not etat.get("complet") and (arriere or not frontiere):
                etat["frontiere"] = {"curseur": it._cursor if not it._exhausted else None,
                                     "tampon": list(it._raw_buffer), "date": date}
            for k in [k for k, v in posts.items() if v["date"] < self.limite_relire]:
                del posts[k]
            self.depot.sauver_etat()
        if not arriere and vus == 0:  # les autres suivis continuent ; celui-ci sera retenté au prochain lancement
            return "FIL VIDE (groupe supprimé, ou devenu privé sans que le compte de collecte en soit membre ?)"
        etat.update(complet=True, frontiere=None)
        return "arriéré terminé"


def suivis(conf: dict) -> list[dict]:
    """Les groupes puis les Pages suivis, chacun avec son type (« groupe » ou « page »)."""
    return ([{**g, "type": "groupe"} for g in conf.get("groupes") or []]
            + [{**g, "type": "page"} for g in conf.get("pages") or []])


def _lancement(depot, journal, conf) -> dict:
    fgs, SessionExpiredError, Client = _client(depot, conf, journal)
    if not FICHIER_COOKIES.exists():
        raise SessionExpiredError("pas de session")
    client = Client()
    lecteur = Lecteur(fgs, client, depot, journal, conf)
    debut = time.time()
    fin = debut + float(conf.get("minutes_par_lancement", 120)) * 60
    groupes = suivis(conf)
    etats = depot.etat.setdefault("groupes", {})  # par identifiant : groupes et Pages (clé gardée « groupes »)
    details, statut, message = [], "ok", ""
    try:
        # 1. Le récent, groupe par groupe.
        for g in groupes:
            etat = etats.setdefault(str(g["id"]), {"nom": g["nom"]})
            client.limite = fin
            r = lecteur.parcourir(g, etat, arriere=False)
            journal(f"  {g['nom']} : {r}")
        # 2. L'arriéré, le temps restant partagé entre les groupes qui en ont un.
        while True:
            restants = [g for g in groupes if not etats[str(g["id"])].get("complet")
                        and etats[str(g["id"])].get("frontiere")]
            if not restants or time.time() >= fin:
                break
            part = (fin - time.time()) / len(restants)
            for g in restants:
                client.limite = min(fin, time.time() + part)
                try:
                    r = lecteur.parcourir(g, etats[str(g["id"])], arriere=True)
                    journal(f"  {g['nom']} : {r}")
                except Budget as b:
                    if b.jour:
                        raise
            if time.time() >= fin - 30:
                break
    except Budget as b:
        statut = "partiel"
        message = ("Quota de requêtes du jour atteint : la suite reprendra demain." if b.jour else
                   "Temps du lancement écoulé : la suite reprendra au prochain lancement.")
    except Freinage as e:
        heures = float(conf.get("repos_apres_freinage_heures", 3))
        depot.etat["repos_jusqua"] = (datetime.now() + timedelta(hours=heures)).isoformat(timespec="seconds")
        statut, message = "partiel (freinage)", (f"{e}. Arrêt de ce lancement et repos de {heures:g} h ; rien n'est "
                                                 "perdu, la suite reprendra ensuite.")
        journal(f"  {message}")
    finally:
        client.garder_cookies()
        depot.sauver_etat()
    for g in groupes:
        e = etats.get(str(g["id"]), {})
        f = e.get("frontiere") or {}
        details.append(f"{g['nom']} : arriéré " + ("terminé" if e.get("complet") else
                                                    f"remonté jusqu'au {date_paris(f['date'])[:10]}" if f.get("date")
                                                    else "pas commencé"))
    jour = depot.etat.get("jour", {})
    details.append(f"{lecteur.lus} posts lus, {client.requetes} requêtes en {(time.time() - debut) / 60:.0f} min "
                   f"({jour.get('requetes', 0)} aujourd'hui sur {client.par_jour} permises)")
    return {"statut": statut, "message": message, "details": details}


def collecter(depot, journal) -> dict:
    conf = perimetre().get("facebook") or {}
    if not suivis(conf):
        raise SourceImpossible("Aucun groupe ni Page Facebook dans config/perimetre.json (rubrique « facebook »).")
    repos = depot.etat.get("repos_jusqua")
    if repos and datetime.now() < datetime.fromisoformat(repos):
        return {"statut": "en repos", "message": f"Facebook a freiné au dernier lancement : repos jusqu'au "
                                                 f"{repos.replace('T', ' ')[:16]}, rien n'est lu d'ici là."}
    depot.etat.pop("repos_jusqua", None)
    for essai in range(2):
        try:
            return _lancement(depot, journal, conf)
        except SourceImpossible:
            raise
        except Exception as e:
            if type(e).__name__ != "SessionExpiredError":
                if type(e).__name__ in ("SchemaChangedError", "DocIdStillInvalidError", "DtsgTokenStillInvalidError",
                                        "DtsgTokenFetchError", "EmptyNodeError"):
                    raise SourceImpossible(f"Facebook a changé ses requêtes internes ({type(e).__name__} : {e}). "
                                           "Mettre à jour la bibliothèque : python -m pip install -U "
                                           "facebook-gql-scraper")
                raise
            if essai:
                raise SourceImpossible("Session Facebook refusée même après une nouvelle connexion : lancer "
                                       "« python -m collecte.connexion_facebook ».")
            journal("  session Facebook expirée : nouvelle connexion (fenêtre Chrome)")
            try:
                connecter(journal)
            except ErreurConnexion as erreur:
                raise SourceImpossible(f"Connexion Facebook impossible : {erreur}")
