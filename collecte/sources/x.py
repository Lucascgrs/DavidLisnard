"""X (anciennement Twitter) : les posts des comptes suivis et ceux qui citent le mot-clé, avec les réponses dessous.

X n'a plus d'accès sans compte ni d'API gratuite utilisable. On envoie, avec les cookies du compte de collecte
(sessions/x_cookies.json, créé par « python -m collecte.connexion_x »), les mêmes requêtes internes que le site, par
la bibliothèque twscrape (sessions/x_twscrape.db garde son état). Aucun navigateur ne s'ouvre pendant la collecte.

Tout passe par la recherche de X, la seule voie qui rende toutes les réponses d'un post (essai du 2026-11-12 sur un
post de David Lisnard à 441 réponses annoncées : 544 lignes par la recherche « conversation_id: », sous-réponses
comprises, contre 36 par la lecture du post) :
- comptes suivis (« comptes » dans config/perimetre.json, onglet X de l'interface) : leurs posts, ni republications
  ni réponses à d'autres (« from:pseudo -filter:retweets -filter:replies »), qu'ils citent le mot-clé ou non, et
  toutes les réponses dessous. Un fichier par compte (« @pseudo »). Un post de moins de « relire_si_moins_de_jours »
  jours est revu à chaque lancement : s'il a gagné des réponses, seules les nouvelles sont lues (« since_id: ») ;
- recherche : les posts d'autres comptes qui citent le mot-clé (« Lisnard -filter:retweets -filter:replies », sans
  les comptes suivis), et toutes les réponses dessous, lues une fois que le post a « attendre_reponses_jours » jours
  (l'essentiel des réponses arrive dans les deux premiers jours). Un seul fichier, « Recherche « Lisnard » ». Les
  réponses qui citent le mot-clé sous les posts des comptes suivis sont déjà prises avec eux.
Les fils de la recherche, souvent de quelques réponses, sont lus par paquets (« conversation_id:A OR
conversation_id:B… ») : une requête pour dix petits fils au lieu de dix.

Comment c'est rangé (mêmes colonnes que les autres sources, comme Facebook) : le post lui-même est une ligne de type
« principal » au titre vide (son texte est le commentaire) ; une réponse directe au post est « principal » avec pour
titre le texte du post ; une réponse à une réponse est « réponse », parent_id = le message auquel elle répond. Les
mentions « @pseudo » qu'X place en tête des réponses sont retirées du texte. commentaire_id = l'identifiant du post
X (https://x.com/i/status/<id>).

Chaque requête (une page de 20 posts) avance du plus récent au plus ancien et repart du dernier identifiant lu
(« max_id: ») : un arrêt en cours de route ne fait rien perdre. Dans chaque lancement, dans l'ordre : le récent des
comptes suivis, le récent de la recherche, les fils à lire, puis l'arriéré jusqu'à « depuis »,
une page de chaque suivi à tour de rôle (comptes et recherche), en lisant les fils trouvés au fur et à mesure.

Rythme (config/perimetre.json), pour ne pas faire suspendre le compte sans traîner : X permet 50 recherches par quart
d'heure et par compte (mesuré le 2026-11-12) ; on en fait au plus « recherches_par_quart_heure » (40), avec une pause
tirée au hasard entre deux requêtes (« pause_entre_requetes_s »). On lit aussi les compteurs de X dans chaque réponse
(x-rate-limit-remaining) : quand il n'en reste presque plus, on attend leur remise à zéro. Au plus
« minutes_par_lancement » minutes par lancement et « requetes_par_jour » requêtes par jour. Un freinage de X
(erreur 429, compte bloqué un moment) arrête le lancement et la source se repose « repos_apres_freinage_heures »
heures. Une session expirée relance seule la connexion (Chrome visible, config/x.env) une fois.
"""
import asyncio
import random
from contextlib import aclosing
import re
import time
from collections import deque
from datetime import datetime, timedelta, timezone

from collecte.connexion_x import ErreurConnexion, chaine_cookies, connecter, lire_cookies
from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import SESSIONS, perimetre
from commun.taches import ArretDemande, arret_demande
from commun.textes import abreger, date_paris

BASE = SESSIONS / "x_twscrape.db"
COMPTE_TWSCRAPE = "collecte"
FENETRE_S = 15 * 60          # fenêtre des limites de X
MARGE_COMPTEUR = 2           # on attend la remise à zéro quand X annonce 2 requêtes restantes ou moins
GROS_FIL = 60                # au-delà de 60 réponses annoncées, un fil est lu seul (et repris s'il est coupé)
PAQUET = 10                  # petits fils lus ensemble
EPOQUE_X = 1288834974657     # origine des identifiants de X (millisecondes)
_MENTIONS_EN_TETE = re.compile(r"^(?:@\w{1,15}\s+)+")


class Budget(BaseException):
    """Temps du lancement ou quota du jour atteint. BaseException : twscrape rattrape les Exception."""

    def __init__(self, jour: bool):
        super().__init__("quota du jour atteint" if jour else "temps écoulé")
        self.jour = jour


class Freinage(BaseException):
    """X freine (429, compte bloqué un moment) : on arrête ce lancement, la source se repose."""


class SessionMorte(BaseException):
    """Cookies refusés par X (session expirée ou compte suspendu)."""


class Arret(BaseException):
    """Arrêt demandé depuis l'interface, remonté à travers twscrape."""


def nom_recherche(mot: str) -> str:
    return f"Recherche « {mot} »"


def nom_compte_suivi(c: dict) -> str:
    return f"@{c['pseudo']}"


def date_de(ident) -> datetime:
    """La date d'un post se lit dans son identifiant."""
    return datetime.fromtimestamp(((int(ident) >> 22) + EPOQUE_X) / 1000, tz=timezone.utc)


def lien(pseudo: str, ident) -> str:
    return f"https://x.com/{pseudo}/status/{ident}" if pseudo else f"https://x.com/i/status/{ident}"


# --- Rythme -----------------------------------------------------------------------------------------------------------

class Rythme:
    """Avant chaque requête : quotas, pauses, fenêtre de 15 minutes, compteurs annoncés par X, arrêt demandé."""

    def __init__(self, depot, conf: dict, fin: float):
        self.depot, self.fin = depot, fin
        pmin, pmax = conf.get("pause_entre_requetes_s", [3, 8])
        self.pause = (float(pmin), float(pmax))
        self.par_quart = int(conf.get("recherches_par_quart_heure", 40))
        self.par_jour = int(conf.get("requetes_par_jour", 3000))
        self.historique: dict[str, deque] = {}
        self.compteurs: dict[str, tuple[int, int]] = {}  # file → (restantes, remise à zéro)
        self.requetes = 0
        self._derniere = 0.0

    async def dormir(self, secondes: float) -> None:
        if time.time() + secondes > self.fin:
            raise Budget(jour=False)
        fin = time.time() + secondes
        while time.time() < fin:
            if arret_demande(self.depot.source):
                raise Arret()
            await asyncio.sleep(min(5.0, fin - time.time()))

    async def avant(self, file: str) -> None:
        jour = self.depot.etat.setdefault("jour", {})
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        if jour.get("date") != aujourdhui:
            jour.update(date=aujourdhui, requetes=0)
        if jour["requetes"] >= self.par_jour:
            raise Budget(jour=True)
        if arret_demande(self.depot.source):
            raise Arret()
        attente = self._derniere + random.uniform(*self.pause) - time.time()
        h = self.historique.setdefault(file, deque())
        while h and h[0] < time.time() - FENETRE_S:
            h.popleft()
        limite = self.par_quart if file == "SearchTimeline" else 2 * self.par_quart
        if len(h) >= limite:
            attente = max(attente, h[0] + FENETRE_S - time.time() + 2)
        restantes, remise = self.compteurs.get(file, (99, 0))
        if restantes <= MARGE_COMPTEUR and remise > time.time():
            attente = max(attente, remise - time.time() + 3)
        if attente > 0:
            await self.dormir(attente)
        self._derniere = time.time()
        h.append(self._derniere)
        self.requetes += 1
        jour["requetes"] += 1

    def apres(self, file: str, reponse) -> None:
        try:
            restantes = int(reponse.headers.get("x-rate-limit-remaining", -1))
            remise = int(reponse.headers.get("x-rate-limit-reset", -1))
        except (TypeError, ValueError):
            return
        if restantes >= 0 and remise > 0:
            self.compteurs[file] = (restantes, remise)


def _brancher(rythme: Rythme) -> None:
    """Chaque requête HTTP de twscrape passe par le rythme (nouveaux essais compris)."""
    from twscrape import queue_client
    _brancher.rythme = rythme
    if getattr(queue_client.Ctx, "_rythme_branche", False):
        queue_client.Ctx._rythme = rythme
        return
    origine = queue_client.Ctx.req

    async def req(self, method, url, params=None):
        file = str(url).rsplit("/", 1)[-1]
        r = queue_client.Ctx._rythme
        await r.avant(file)
        rep = await origine(self, method, url, params=params)
        r.apres(file, rep)
        if rep.status_code == 429:
            raise Freinage("X répond HTTP 429 (trop de requêtes)")
        return rep

    queue_client.Ctx.req = req
    queue_client.Ctx._rythme = rythme
    queue_client.Ctx._rythme_branche = True
    _brancher.rythme = rythme


# --- twscrape ---------------------------------------------------------------------------------------------------------

async def _api():
    try:
        from twscrape import API
        from twscrape.logger import set_log_level
    except ImportError:
        raise SourceImpossible("Bibliothèque absente : python -m pip install -r requirements.txt (twscrape).")
    set_log_level("ERROR")
    cookies = chaine_cookies()
    if not cookies or "auth_token" not in cookies:
        raise SessionMorte()
    api = API(str(BASE), raise_when_no_account=True)
    comptes = {a.username: a for a in await api.pool.get_all()}
    a = comptes.get(COMPTE_TWSCRAPE)
    deja = a and a.active and all(a.cookies.get(k) == v for k, v in lire_cookies().items() if k in ("auth_token", "ct0"))
    if not deja:
        if a:
            await api.pool.delete_accounts([COMPTE_TWSCRAPE])
        await api.pool.add_account_cookies(COMPTE_TWSCRAPE, cookies)
    return api


async def _attente_du_compte(api) -> float:
    """Après un NoAccountError : secondes à attendre avant que twscrape relâche la recherche (blocage noté après
    une limite atteinte). Session morte ou compte suspendu : SessionMorte."""
    a = next((x for x in await api.pool.get_all() if x.username == COMPTE_TWSCRAPE), None)
    if a is None or not a.active:
        raise SessionMorte()
    fin = (a.locks or {}).get("SearchTimeline")
    if fin is None:
        return 0.0
    fin = fin if isinstance(fin, datetime) else datetime.fromisoformat(str(fin))
    fin = fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc)
    return max(0.0, (fin - datetime.now(timezone.utc)).total_seconds())


async def chercher(api, requete: str):
    """Les pages d'une recherche (« Récents »), chacune comme une liste de posts. Si twscrape a noté un blocage
    passager (limite de X atteinte) avant la première page, on l'attend (au plus 16 min, dans le temps du lancement) ;
    après, ou plus long, c'est un freinage."""
    from twscrape.accounts_pool import NoAccountError
    from twscrape.models import parse_tweets
    for essai in range(2):
        pages = 0
        try:
            # Refermée dès qu'on en sort : twscrape garde le compte « occupé » tant qu'une recherche reste ouverte.
            async with aclosing(api.search_raw(requete)) as reponses:
                async for rep in reponses:
                    pages += 1
                    yield list(parse_tweets(rep))
            return
        except NoAccountError:
            attente = await _attente_du_compte(api)
            if pages or essai or attente > 16 * 60:
                raise Freinage(f"X a bloqué un moment les recherches du compte ({attente / 60:.0f} min)")
            await _brancher.rythme.dormir(attente + 5)


# --- Lignes -----------------------------------------------------------------------------------------------------------

def _texte(t, est_reponse: bool) -> str:
    texte = (t.rawContent or "").strip()
    return _MENTIONS_EN_TETE.sub("", texte).strip() if est_reponse else texte


def _ligne(t, racine: dict) -> dict:
    """racine : {id, titre, lien, date} du post en tête du fil."""
    est_racine = str(t.id) == racine["id"]
    parent = str(t.inReplyToTweetId or "")
    return {
        "publication_id": racine["id"], "publication_titre": "" if est_racine else racine["titre"],
        "publication_lien": racine["lien"], "publication_date": racine["date"],
        "commentaire_id": str(t.id),
        "type": REPONSE if parent and parent != racine["id"] else PRINCIPAL,
        "parent_id": parent if parent and parent != racine["id"] else "",
        "auteur": t.user.displayname or t.user.username, "auteur_id": str(t.user.id),
        "date": date_paris(t.date), "date_exacte": "oui",
        "texte": _texte(t, not est_racine), "likes": t.likeCount,
    }


def _racine(t) -> dict:
    return {"id": str(t.id), "titre": abreger(_texte(t, False), 300), "lien": lien(t.user.username, t.id),
            "date": date_paris(t.date)}


# --- Collecte ---------------------------------------------------------------------------------------------------------

class Lecteur:
    def __init__(self, api, depot, journal, conf, mot):
        self.api, self.depot, self.journal, self.conf = api, depot, journal, conf
        self.depuis = datetime.fromisoformat(conf.get("depuis", "2026-07-31")).replace(tzinfo=timezone.utc)
        self.maintenant = datetime.now(timezone.utc)
        self.relire = self.maintenant - timedelta(days=int(conf.get("relire_si_moins_de_jours", 7)))
        self.attendre = timedelta(days=float(conf.get("attendre_reponses_jours", 2)))
        self.mot = mot
        self.suivis = conf.get("comptes") or []
        self.etat_req = depot.etat.setdefault("requetes", {})
        self.fils = depot.etat.setdefault("fils", {})  # id du post → ce qu'il reste à lire sous lui
        self.posts = self.reponses = self.fils_lus = 0

    # Les requêtes de posts (comptes suivis, recherche)
    def requete(self, cle: str) -> str:
        if cle == "recherche":
            exclus = " ".join(f"-from:{c['pseudo']}" for c in self.suivis)
            return f"{self.mot} -filter:retweets -filter:replies {exclus}".strip()
        return f"from:{cle.lstrip('@')} -filter:retweets -filter:replies"

    def cles(self) -> list[tuple[str, str]]:
        """(clé de l'état, nom du fichier) : les comptes suivis puis la recherche."""
        sortie = [(nom_compte_suivi(c), nom_compte_suivi(c)) for c in self.suivis]
        if self.conf.get("recherche", True):
            sortie.append(("recherche", nom_recherche(self.mot)))
        return sortie

    def ranger(self, cle: str, compte: str, posts: list) -> None:
        """Enregistre des posts trouvés et note les fils à lire sous eux."""
        lignes = []
        for t in posts:
            if t.date < self.depuis:
                continue
            racine = _racine(t)
            lignes.append(_ligne(t, racine))
            f = self.fils.get(racine["id"])
            suivi = cle != "recherche"
            if f is None:
                if str(t.id) in self.depot.connus(compte) and (not suivi or t.date < self.relire):
                    continue  # déjà lu à un lancement précédent, et sorti de la période de relecture
                f = self.fils[racine["id"]] = {"compte": compte, "suivi": suivi, "racine": racine, "annonces": 0,
                                               "fini": False}
            f["vues"] = max(f.get("vues", 0), t.replyCount)
            if suivi:
                if t.replyCount > f["annonces"]:
                    f["a_lire"] = True
            elif not f["fini"]:
                # Un post de la recherche est lu une fois, quand ses réponses sont arrivées. Trouvé tout jeune, son
                # nombre de réponses ne dit encore rien : on le lira de toute façon (en paquet, ça ne coûte presque
                # rien) ; trouvé plus vieux, seulement s'il en a.
                pret = t.date + self.attendre
                f["pret"] = pret.isoformat()
                f["a_lire"] = t.replyCount > 0 or pret > self.maintenant
        self.posts += self.depot.ajouter(compte, lignes)

    async def page_de_posts(self, cle: str, compte: str, recent: bool) -> bool:
        """Lit le récent (recent=True) ou une page de l'arriéré. Renvoie vrai s'il reste de l'arriéré."""
        e = self.etat_req.setdefault(cle, {})
        base = self.requete(cle)
        if recent:
            if not e.get("haut"):
                return True  # jamais lu : tout passe par l'arriéré
            if cle == "recherche":
                q = f"{base} since_id:{e['haut']}"
            else:  # depuis la période de relecture (réponses gagnées), ou depuis le dernier post vu si plus ancien
                debut = max(self.depuis, min(self.relire, date_de(e["haut"]) - timedelta(days=1)))
                q = f"{base} since:{debut:%Y-%m-%d}"
            haut = int(e["haut"])
            async for page in chercher(self.api, q):
                self.ranger(cle, compte, page)
                haut = max([haut] + [t.id for t in page])
                self.depot.sauver_etat()
            e["haut"] = str(haut)
            return not e.get("complet")
        if e.get("complet"):
            return False
        q = f"{base} since:{self.depuis:%Y-%m-%d}" + (f" max_id:{int(e['bas']) - 1}" if e.get("bas") else "")
        async with aclosing(chercher(self.api, q)) as pages:
            async for page in pages:
                if not page:
                    continue
                self.ranger(cle, compte, page)
                ids = [t.id for t in page]
                e["bas"] = str(min(ids + ([int(e["bas"])] if e.get("bas") else [])))
                e["haut"] = str(max(ids + ([int(e["haut"])] if e.get("haut") else [])))
                self.depot.sauver_etat()
                return True  # une page à la fois : les fils trouvés passent avant la page suivante
        e["complet"] = True
        if not e.get("haut"):
            e["haut"] = str((int(self.maintenant.timestamp() * 1000) - EPOQUE_X) << 22)
        self.depot.sauver_etat()
        return False

    # Les fils
    def a_lire(self) -> list[str]:
        """Les fils prêts, comptes suivis d'abord, du plus récent au plus ancien."""
        maintenant = datetime.now(timezone.utc).isoformat()
        prets = [i for i, f in self.fils.items() if f.get("a_lire") and f.get("pret", "") <= maintenant]
        return sorted(prets, key=lambda i: (not self.fils[i]["suivi"], -int(i)))

    async def lire_fil(self, ident: str) -> None:
        """Un gros fil (ou un fil de compte suivi), seul : la suite de sa lecture, ou ses nouvelles réponses."""
        f = self.fils[ident]
        q = f"conversation_id:{ident}"
        if f["fini"] and f.get("haut"):
            q += f" since_id:{f['haut']}"
        elif f.get("bas"):
            q += f" max_id:{int(f['bas']) - 1}"
        async for page in chercher(self.api, q):
            if not page:
                continue
            self.reponses += self.depot.ajouter(f["compte"], [_ligne(t, f["racine"]) for t in page
                                                              if t.conversationIdStr == ident])
            ids = [t.id for t in page]
            if not f["fini"]:
                f["bas"] = str(min(ids + ([int(f["bas"])] if f.get("bas") else [])))
            f["haut"] = str(max(ids + ([int(f["haut"])] if f.get("haut") else [])))
            self.depot.sauver_etat()
        self._fini(ident)

    async def lire_paquet(self, idents: list[str]) -> None:
        """Plusieurs petits fils de la recherche, en une seule suite de requêtes."""
        par_id = {i: self.fils[i] for i in idents}
        q = " OR ".join(f"conversation_id:{i}" for i in idents)
        async for page in chercher(self.api, q):
            for i, f in par_id.items():
                lignes = [_ligne(t, f["racine"]) for t in page if t.conversationIdStr == i]
                if lignes:
                    self.reponses += self.depot.ajouter(f["compte"], lignes)
            self.depot.sauver_etat()
        for i in idents:
            self._fini(i)

    def _fini(self, ident: str) -> None:
        f = self.fils[ident]
        f.update(fini=True, a_lire=False, annonces=max(f["annonces"], f.get("vues", 0)))
        f.pop("bas", None)
        self.fils_lus += 1
        if not f["suivi"] or date_de(ident) < self.relire:
            del self.fils[ident]  # plus rien à y relire
        self.depot.sauver_etat()

    async def lire_les_fils(self) -> None:
        while True:
            prets = self.a_lire()
            if not prets:
                return
            i = prets[0]
            f = self.fils[i]
            if f["suivi"] or f.get("vues", 0) > GROS_FIL or f.get("bas"):
                await self.lire_fil(i)
            else:
                paquet = [j for j in prets if not self.fils[j]["suivi"] and self.fils[j].get("vues", 0) <= GROS_FIL
                          and not self.fils[j].get("bas")][:PAQUET]
                await self.lire_paquet(paquet)
            if self.fils_lus and self.fils_lus % 20 == 0:
                self.journal(f"    {self.fils_lus} fils lus, {self.reponses} réponses nouvelles")

    async def tout(self) -> None:
        cles = self.cles()
        for cle, compte in cles:  # 1. le récent
            await self.page_de_posts(cle, compte, recent=True)
        self.journal(f"  récent lu : {self.posts} posts nouveaux, {len(self.a_lire())} fils à lire")
        await self.lire_les_fils()  # 2. les fils
        # 3. L'arriéré, une page de chaque suivi à tour de rôle (fils compris) : la recherche avance en même temps que
        # les comptes au lieu d'attendre qu'ils soient tous finis.
        restants, tour = list(cles), 0
        while restants:
            tour += 1
            for cle, compte in list(restants):
                if not await self.page_de_posts(cle, compte, recent=False):
                    restants.remove((cle, compte))
                await self.lire_les_fils()
            if tour % 5 == 0:
                self.journal("  arriéré : " + " ; ".join(
                    f"{compte} {date_de(self.etat_req[cle]['bas']):%Y-%m-%d}" for cle, compte in restants
                    if self.etat_req.get(cle, {}).get("bas")) + f" ; {self.posts} posts et {self.reponses} réponses "
                    "nouveaux")


def _avancement(depot, conf, mot) -> list[str]:
    e = depot.etat.get("requetes", {})
    sortie = []
    for c in (conf.get("comptes") or []) + ([None] if conf.get("recherche", True) else []):
        cle = nom_compte_suivi(c) if c else "recherche"
        x = e.get(cle, {})
        nom = nom_compte_suivi(c) if c else nom_recherche(mot)
        sortie.append(f"{nom} : arriéré " + ("terminé" if x.get("complet") else
                                             f"remonté jusqu'au {date_de(x['bas']):%Y-%m-%d}" if x.get("bas")
                                             else "pas commencé"))
    return sortie


def _lancement(depot, journal, conf, mot) -> dict:
    debut = time.time()
    fin = debut + float(conf.get("minutes_par_lancement", 120)) * 60
    rythme = Rythme(depot, conf, fin)
    _brancher(rythme)
    statut, message = "ok", ""

    async def deroule():
        api = await _api()
        lecteur = Lecteur(api, depot, journal, conf, mot)
        try:
            await lecteur.tout()
        finally:
            depot.sauver_etat()
            journal(f"  {lecteur.posts} posts et {lecteur.reponses} réponses nouveaux, {lecteur.fils_lus} fils lus")
        return lecteur

    try:
        asyncio.run(deroule())
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
    except Arret:
        raise ArretDemande()
    finally:
        depot.sauver_etat()
    jour = depot.etat.get("jour", {})
    details = _avancement(depot, conf, mot)
    details.append(f"{rythme.requetes} requêtes en {(time.time() - debut) / 60:.0f} min "
                   f"({jour.get('requetes', 0)} aujourd'hui sur {rythme.par_jour} permises)")
    return {"statut": statut, "message": message, "details": details}


def collecter(depot, journal) -> dict:
    p = perimetre()
    conf, mot = p.get("x") or {}, p.get("mot_cle", "Lisnard")
    if not conf.get("comptes") and not conf.get("recherche", True):
        raise SourceImpossible("Aucun compte X suivi et recherche désactivée (config/perimetre.json, rubrique « x »).")
    repos = depot.etat.get("repos_jusqua")
    if repos and datetime.now() < datetime.fromisoformat(repos):
        return {"statut": "en repos", "message": f"X a freiné au dernier lancement : repos jusqu'au "
                                                 f"{repos.replace('T', ' ')[:16]}, rien n'est lu d'ici là."}
    depot.etat.pop("repos_jusqua", None)
    for essai in range(2):
        try:
            return _lancement(depot, journal, conf, mot)
        except SessionMorte:
            if essai:
                raise SourceImpossible("Session X refusée même après une nouvelle connexion : lancer "
                                       "« python -m collecte.connexion_x » (compte suspendu ?).")
            journal("  session X expirée : nouvelle connexion (fenêtre Chrome)")
            try:
                connecter(journal)
            except ErreurConnexion as erreur:
                raise SourceImpossible(f"Connexion X impossible : {erreur}")
