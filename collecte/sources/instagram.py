"""Instagram : Chrome visible, connecté avec le compte dédié (sessions/cookies_web.json, créé par
« python -m collecte.connexion_instagram »), qui ouvre le profil puis chaque post et fait défiler ses commentaires.
On lit ce qu'Instagram envoie lui-même à la page : le JSON intégré au HTML (premiers commentaires)
et les réponses réseau (suite des commentaires, réponses).

Critère d'abandon (config/perimetre.json) : 10 posts en plus de N minutes, ou un blocage
(redirection vers la connexion ou une vérification, page figée) → source abandonnée.
"""
import json
import random
import time
from datetime import datetime, timezone

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import SESSIONS, perimetre
from commun.fichiers import lire_json
from commun.textes import date_paris

FICHIER_COOKIES = SESSIONS / "cookies_web.json"
TOURS_SANS_NOUVEAU = 6
LIMITE_PAR_POST_S = 600

# Un tour de lecture : ouvrir les « View all N replies » pas encore ouverts, puis amener à l'écran l'indicateur
# « Loading... » du bas de la liste, ce qui fait charger la page suivante. La molette, elle, fait défiler la page
# entière et sort le panneau de l'écran. Renvoie [réponses ouvertes, indicateurs présents].
SUITE = """() => {
  window.scrollTo(0, 0);
  let n = 0;
  for (const el of document.querySelectorAll('[role=button], button, span')) {
    const t = (el.innerText || '').trim();
    if (el.children.length <= 2 && /^View (all )?(\\d+ )?(more )?repl(y|ies)/i.test(t) && !el.dataset.lisnard) {
      el.dataset.lisnard = '1'; el.click(); n++;
    }
  }
  const sp = [...document.querySelectorAll('svg[aria-label="Loading..."], [aria-label="Load more comments"]')];
  if (sp.length) sp[sp.length - 1].scrollIntoView({block: 'end'});
  window.scrollTo(0, 0);
  return [n, sp.length];
}"""


class Freinage(Exception):
    """Instagram refuse de servir une page (erreur HTTP, deux fois de suite) : c'est un freinage passager, pas un
    blocage du compte. On arrête ce lancement proprement, sans abandonner la source."""


def _parcourir(objet, trouve):
    if isinstance(objet, dict):
        trouve(objet)
        for v in objet.values():
            _parcourir(v, trouve)
    elif isinstance(objet, list):
        for v in objet:
            _parcourir(v, trouve)


class Instagram:
    def __init__(self, journal):
        self.journal = journal
        self.reponses: list = []

    def __enter__(self):
        cookies = lire_json(FICHIER_COOKIES, None)
        if not cookies or not cookies.get("sessionid"):
            raise SourceImpossible("Pas de session Instagram : lancer une fois « python -m collecte.connexion_instagram ».")
        self.pw = sync_playwright().start()
        try:
            self.nav = self.pw.chromium.launch(channel="chrome", headless=False, slow_mo=50)
        except Exception:
            self.pw.stop()
            raise SourceImpossible("Chrome introuvable pour Instagram.")
        self.ctx = self.nav.new_context(locale="en-US", viewport={"width": 1280, "height": 900})
        self.ctx.add_cookies([{"name": k, "value": v, "domain": ".instagram.com", "path": "/", "secure": True}
                              for k, v in cookies.items() if v])
        self.page = self.ctx.new_page()
        self.page.on("response", self._capter)
        return self

    def __exit__(self, *_):
        self.nav.close()
        self.pw.stop()

    def _capter(self, r):
        if "instagram.com" in r.url and ("/api/" in r.url or "graphql" in r.url):
            try:
                self.reponses.append(r.json())
            except Exception:
                pass

    def ouvrir(self, url: str):
        for essai in range(2):
            try:
                self.page.goto(url, wait_until="commit", timeout=180000)
                break
            except PlaywrightError as e:
                if essai:
                    raise Freinage(f"Instagram ne sert plus les pages ({str(e).splitlines()[0][:120]})")
                self.journal(f"    page refusée par Instagram, nouvel essai dans 1 minute ({url})")
                self.page.wait_for_timeout(60000)
        for _ in range(40):
            self.page.wait_for_timeout(1500)
            if self.page.query_selector("body") and len(self.page.inner_text("body").strip()) > 40:
                break
        else:
            raise SourceImpossible("Instagram reste sur l'écran de chargement : compte freiné.")
        self.page.wait_for_timeout(random.uniform(2500, 4000))
        if any(m in self.page.url for m in ("/accounts/login", "/challenge", "/suspended")):
            raise SourceImpossible(f"Instagram demande une connexion ou une vérification ({self.page.url}).")

    def json_integre(self) -> list:
        sortie = []
        for t in self.page.eval_on_selector_all('script[type="application/json"]', "els => els.map(e => e.textContent)"):
            try:
                sortie.append(json.loads(t))
            except ValueError:
                pass
        return sortie

    def posts(self, pseudo: str, depuis: float, connus: set) -> tuple[dict[str, dict], bool]:
        """Fait défiler le profil jusqu'à la date de début, ou, si `connus` vient d'une liste déjà complète,
        jusqu'à retomber sur des posts déjà listés. Renvoie (posts trouvés, date de début atteinte)."""
        self.reponses.clear()
        self.ouvrir(f"https://www.instagram.com/{pseudo}/")
        trouves, lu, calme, debut_atteint = {}, 0, 0, False

        def post(o):
            if isinstance(o.get("code"), str) and "taken_at" in o and ("pk" in o or "id" in o):
                leg = o.get("caption") or {}
                trouves.setdefault(o["code"], {
                    "code": o["code"], "date": int(o["taken_at"]),
                    "legende": leg.get("text", "") if isinstance(leg, dict) else "",
                    "commentaires": o.get("comment_count") or 0})

        for d in self.json_integre():
            _parcourir(d, post)
        while calme < 4:
            avant = len(trouves)
            for d in self.reponses[lu:]:
                _parcourir(d, post)
            lu = len(self.reponses)
            dates = sorted(p["date"] for p in trouves.values())
            # au-delà des 3 posts épinglés, le plus récent des plus vieux passe sous la date de début : fini
            if len(dates) > 3 and dates[3] < depuis:
                debut_atteint = True
                break
            if connus and sum(1 for c in trouves if c in connus) >= 15:  # 15 : au-delà des posts épinglés
                break
            calme = calme + 1 if len(trouves) == avant else 0
            self.page.mouse.move(640, 500)
            for _ in range(3):
                self.page.mouse.wheel(0, random.uniform(800, 1200))
                self.page.wait_for_timeout(random.uniform(300, 600))
            self.page.wait_for_timeout(random.uniform(2500, 4000))
        return {k: v for k, v in trouves.items() if v["date"] >= depuis}, debut_atteint

    def commentaires(self, post: dict, pseudo: str) -> list[dict]:
        self.reponses.clear()
        self.ouvrir(f"https://www.instagram.com/p/{post['code']}/")
        vus: dict[str, dict] = {}

        def comm(o):
            if not (isinstance(o.get("text"), str) and isinstance(o.get("user"), dict)
                    and ("created_at" in o or "created_at_utc" in o) and ("pk" in o or "id" in o)):
                return
            cid = str(o.get("pk") or o["id"])
            if cid in vus or o.get("type") == "caption" or o["text"] == post["legende"]:
                return
            parent = o.get("parent_comment_id") or o.get("replied_to_comment_id")
            u = o["user"]
            vus[cid] = {
                "publication_id": post["code"], "publication_titre": post["legende"][:300],
                "publication_lien": f"https://www.instagram.com/p/{post['code']}/",
                "publication_date": date_paris(post["date"]),
                "commentaire_id": cid, "type": REPONSE if parent else PRINCIPAL, "parent_id": str(parent or ""),
                "auteur": u.get("username", ""), "auteur_id": str(u.get("pk") or u.get("id") or ""),
                "date": date_paris(int(o.get("created_at_utc") or o["created_at"])), "date_exacte": "oui",
                "texte": o["text"], "likes": o.get("comment_like_count", ""),
            }

        for d in self.json_integre():
            _parcourir(d, comm)
        lu, calme, debut = 0, 0, time.time()
        while calme < TOURS_SANS_NOUVEAU and time.time() - debut < LIMITE_PAR_POST_S:
            avant = len(vus)
            for d in self.reponses[lu:]:
                _parcourir(d, comm)
            lu = len(self.reponses)
            calme = calme + 1 if len(vus) == avant else 0
            ouvertes, indicateurs = self.page.evaluate(SUITE)
            if indicateurs == 0 and ouvertes == 0 and calme >= 4:
                break  # plus d'indicateur de chargement : Instagram n'a plus rien à envoyer
            self.page.wait_for_timeout(random.uniform(2200, 3200))
        for d in self.reponses[lu:]:
            _parcourir(d, comm)
        return list(vus.values())


def _sortie_de_veille(t0: float) -> bool:
    """Un post ne dure jamais plus de LIMITE_PAR_POST_S (plus le chargement) : bien au-delà, l'horloge a sauté
    parce que le PC s'est mis en veille pendant la lecture."""
    return time.time() - t0 > LIMITE_PAR_POST_S + 900


def collecter(depot, journal) -> dict:
    conf = perimetre()["instagram"]
    depuis = datetime.fromisoformat(conf.get("depuis", "2025-01-01")).replace(tzinfo=timezone.utc).timestamp()
    par_lancement = conf.get("posts_par_lancement", 20)
    seuil_min = conf.get("abandon_si_10_posts_depassent_minutes", 30)
    # Un post déjà lu n'est relu (pour ses nouveaux commentaires) que s'il a moins de N jours : on ne revient pas
    # sur les vieux posts, seul l'arriéré jamais lu continue d'avancer.
    relire_depuis = time.time() - conf.get("relire_si_moins_de_jours", 21) * 86400
    vus = depot.etat.setdefault("posts", {})
    essai = depot.etat.setdefault("essai", {"posts": 0, "secondes": 0.0})
    details = []

    def abandon(raison: str):
        depot.etat["abandon"] = f"abandonnée le {datetime.now():%Y-%m-%d} : {raison}"
        depot.sauver_etat()
        raise SourceImpossible(depot.etat["abandon"])

    freine = ""
    with Instagram(journal) as ig:
        for pseudo in conf["comptes"]:
            if freine:
                break
            # La liste complète des posts est gardée dans l'état : après la première fois, on ne fait défiler
            # le profil que jusqu'aux posts déjà listés (quelques secondes au lieu de 6 minutes).
            liste = depot.etat.setdefault("liste", {}).setdefault(pseudo, {})
            complete = depot.etat.setdefault("liste_complete", {})
            try:
                trouves, debut_atteint = ig.posts(pseudo, depuis, set(liste) if complete.get(pseudo) else set())
            except SourceImpossible as e:
                abandon(str(e))
            except Freinage as e:
                freine = str(e)
                journal(f"  {freine} : arrêt de ce lancement, la suite reprendra au prochain")
                break
            liste.update(trouves)
            if debut_atteint:
                complete[pseudo] = True
            depot.sauver_etat()
            posts = {k: v for k, v in liste.items() if v["date"] >= depuis}
            # D'abord les posts jamais lus (du plus récent au plus ancien), ensuite ceux de moins de N jours qui
            # ont gagné des commentaires depuis leur dernière lecture (les plus anciennement lus d'abord).
            jamais = [p for p in sorted(posts.values(), key=lambda p: -p["date"]) if p["code"] not in vus]
            a_relire = sorted((p for p in posts.values() if p["code"] in vus and p["date"] >= relire_depuis
                               and p["commentaires"] > vus[p["code"]].get("commentaires", 0)),
                              key=lambda p: vus[p["code"]].get("lu_le", ""))
            a_lire = jamais + a_relire
            journal(f"  @{pseudo} : {len(posts)} posts depuis le début du périmètre, {len(a_lire)} à lire "
                    f"(au plus {par_lancement} par lancement)")
            for n, p in enumerate(a_lire[:par_lancement], 1):
                depot.verifier_arret()
                t0 = time.time()
                try:
                    lignes = ig.commentaires(p, pseudo)
                except (SourceImpossible, Freinage) as e:
                    # Une page qui ne charge pas juste après une mise en veille du PC (réseau pas encore revenu)
                    # n'est pas un blocage du compte : on arrête ce lancement sans abandonner la source.
                    if isinstance(e, SourceImpossible) and not _sortie_de_veille(t0):
                        abandon(str(e))
                    freine = f"PC sorti de veille ({e})" if _sortie_de_veille(t0) else str(e)
                    journal(f"  {freine} : arrêt de ce lancement, la suite reprendra au prochain")
                    break
                ajoutes = depot.ajouter(f"@{pseudo}", lignes)
                duree = time.time() - t0
                if _sortie_de_veille(t0):
                    # Le post a été lu de part et d'autre d'une veille : on le garde, mais on n'enchaîne pas, et
                    # sa durée ne compte pas dans l'essai des 10 premiers posts.
                    vus[p["code"]] = {"commentaires": p["commentaires"],
                                      "lu_le": datetime.now(timezone.utc).isoformat()}
                    depot.sauver_etat()
                    freine = f"PC sorti de veille pendant le post {p['code']} ({len(lignes)} lus, {ajoutes} nouveaux)"
                    journal(f"  {freine} : arrêt de ce lancement, la suite reprendra au prochain")
                    break
                vus[p["code"]] = {"commentaires": p["commentaires"], "lu_le": datetime.now(timezone.utc).isoformat()}
                journal(f"    [{n}/{min(len(a_lire), par_lancement)}] {p['code']} : {len(lignes)} lus, {ajoutes} "
                        f"nouveaux ({p['commentaires']} annoncés), {duree:.0f} s")
                if essai["posts"] < 10:
                    essai["posts"] += 1
                    essai["secondes"] += duree
                    if essai["posts"] == 10:
                        details.append(f"essai : 10 posts en {essai['secondes'] / 60:.1f} min")
                        if essai["secondes"] > seuil_min * 60:
                            abandon(f"10 posts en {essai['secondes'] / 60:.0f} min (> {seuil_min} min)")
                depot.sauver_etat()
                time.sleep(random.uniform(4, 9))
            reste = max(0, len(a_lire) - par_lancement)
            if reste:
                details.append(f"@{pseudo} : {reste} posts restent à lire aux prochains lancements")
    if freine:
        return {"details": details, "statut": "partiel (freinage)",
                "message": f"{freine}. Rien n'est perdu : la suite reprendra au prochain lancement (laisser "
                           "reposer le compte une heure ou deux)."}
    return {"details": details}
