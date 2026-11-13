"""Session du compte Facebook de collecte (sessions/facebook_cookies.json), utilisée par la source Facebook.

    python -m collecte.connexion_facebook              connexion avec FB_MAIL et FB_MDP de config/facebook.env
    python -m collecte.connexion_facebook --verifier   dit si la session enregistrée marche encore

La connexion ouvre une seule fois Chrome, visible, avec un profil à part (sessions/facebook_profil/) : rien du
compte personnel n'y est chargé, et si Facebook demande une vérification (code reçu par mail, captcha), on peut y
répondre dans cette fenêtre (jusqu'à 10 minutes). La collecte, elle, n'ouvre aucun navigateur : elle envoie ses
requêtes avec les cookies enregistrés ici. Elle relance d'elle-même cette connexion si la session a expiré.
"""
import argparse
import json
import re
import sys
import time

from commun.config import FICHIER_FACEBOOK_ENV, SESSIONS, lire_env

FICHIER_COOKIES = SESSIONS / "facebook_cookies.json"
PROFIL = SESSIONS / "facebook_profil"
ATTENTE_MAX_S = 600
# En-têtes d'une vraie navigation : sans eux, Facebook répond « Error » (HTTP 400) aux pages demandées par un script.
NAVIGATEUR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/151.0.0.0 Safari/537.36")
NAVIGATION = {
    "user-agent": NAVIGATEUR,
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "fr-FR,fr;q=0.9",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}


class ErreurConnexion(Exception):
    """Erreur à montrer telle quelle."""


def identifiants() -> tuple[str, str]:
    env = lire_env(FICHIER_FACEBOOK_ENV)
    mail, mdp = env.get("FB_MAIL", ""), env.get("FB_MDP", "")
    if not mail or not mdp:
        raise ErreurConnexion("config/facebook.env absent ou incomplet : copier config/facebook.exemple.env en "
                              "config/facebook.env et y mettre FB_MAIL et FB_MDP du compte de collecte.")
    return mail, mdp


def lire_cookies() -> list[dict]:
    try:
        return json.loads(FICHIER_COOKIES.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []


def sauver_cookies(cookies: list[dict]) -> None:
    SESSIONS.mkdir(exist_ok=True)
    tmp = FICHIER_COOKIES.with_suffix(".tmp")
    tmp.write_text(json.dumps(cookies, indent=1), encoding="utf-8")
    tmp.replace(FICHIER_COOKIES)


def verifier() -> str | None:
    """Nom du compte connecté si la session enregistrée marche, sinon None."""
    import requests
    cookies = lire_cookies()
    if not any(c.get("name") == "c_user" for c in cookies):
        return None
    s = requests.Session()
    s.headers.update(NAVIGATION)
    for c in cookies:
        s.cookies.set(c["name"], c["value"], domain=".facebook.com")
    try:
        r = s.get("https://www.facebook.com/", timeout=60)
    except requests.RequestException:
        return None
    m = re.search(r'"USER_ID":"(\d+)","NAME":"([^"]*)"', r.text)
    return m.group(2) if m and m.group(1) != "0" else None


def connecter(journal=print) -> None:
    """Ouvre Chrome, se connecte avec config/facebook.env, attend la session, enregistre les cookies."""
    from playwright.sync_api import sync_playwright
    mail, mdp = identifiants()
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(str(PROFIL), channel="chrome", headless=False,
                                                       locale="fr-FR", viewport={"width": 1100, "height": 800})
        except Exception as e:
            raise ErreurConnexion(f"Chrome introuvable pour la connexion Facebook ({str(e).splitlines()[0][:120]}).")
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            if not any(c["name"] == "c_user" for c in ctx.cookies()):
                for libelle in ("Autoriser tous les cookies", "Allow all cookies",
                                "Refuser les cookies optionnels", "Decline optional cookies"):
                    try:
                        page.get_by_role("button", name=libelle).first.click(timeout=2000)
                        break
                    except Exception:
                        pass
                page.fill("input[name=email]", mail)
                page.wait_for_timeout(800)
                page.fill("input[name=pass]", mdp)
                page.wait_for_timeout(600)
                page.keyboard.press("Enter")
                journal("   connexion envoyée ; si Facebook demande une vérification, y répondre dans la fenêtre Chrome "
                        f"(attente jusqu'à {ATTENTE_MAX_S // 60} min)")
            debut = time.time()
            while not any(c["name"] == "c_user" for c in ctx.cookies()):
                if time.time() - debut > ATTENTE_MAX_S:
                    raise ErreurConnexion(f"Pas de session Facebook après {ATTENTE_MAX_S // 60} min (page : {page.url}). "
                                          "Vérification non faite, ou identifiants refusés.")
                page.wait_for_timeout(2000)
            page.wait_for_timeout(5000)  # laisse Facebook poser xs, fr, etc.
            sauver_cookies([{"name": c["name"], "value": c["value"]} for c in ctx.cookies()
                            if "facebook.com" in c["domain"]])
        finally:
            ctx.close()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m collecte.connexion_facebook", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verifier", action="store_true", help="dit seulement si la session enregistrée marche")
    args = ap.parse_args()
    if not args.verifier:
        try:
            connecter()
        except ErreurConnexion as e:
            print(f"Échec : {e}")
            sys.exit(1)
    nom = verifier()
    print(f"Session Facebook valable : connecté en tant que « {nom} »." if nom else
          "Pas de session Facebook valable : lancer « python -m collecte.connexion_facebook ».")
    sys.exit(0 if nom else 1)


if __name__ == "__main__":
    main()
