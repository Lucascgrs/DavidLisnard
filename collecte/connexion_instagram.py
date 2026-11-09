"""Session du compte Instagram de collecte (sessions/cookies_web.json), utilisée par la source Instagram.

    python -m collecte.connexion_instagram                       connexion avec utilisateur et mot de passe de
                                                                 config/compte.json (demande le code reçu si besoin)
    python -m collecte.connexion_instagram --sessionid <valeur>  reprend la session d'un navigateur déjà connecté
    python -m collecte.connexion_instagram --verifier            dit si la session enregistrée marche encore

Le navigateur s'ouvre avec un profil vierge : rien du compte personnel n'y est chargé.
"""
import argparse
import json
import os
import random
import sys
import time

import requests
from playwright.sync_api import sync_playwright

from collecte.sources.instagram import FICHIER_COOKIES
from commun.config import FICHIER_COMPTE, SESSIONS

APP_ID_WEB = "936619743392459"  # identifiant fixe de l'application web instagram.com
NAVIGATEUR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
VISIBLE = os.environ.get("LISNARD_INVISIBLE") != "1"  # fenêtre visible par défaut
FICHIER_CODE = SESSIONS / "code.txt"


class ErreurInstagram(Exception):
    """Erreur à montrer telle quelle."""


def charger_compte() -> dict:
    """config/compte.json : {"utilisateur": "...", "mot_de_passe": "...", "sessionid": "..."}.
    Le sessionid seul suffit ; le mot de passe ne sert qu'à la première connexion."""
    if not FICHIER_COMPTE.exists():
        raise ErreurInstagram("config/compte.json absent : copier config/compte.exemple.json et le remplir.")
    return json.loads(FICHIER_COMPTE.read_text(encoding="utf-8"))


def cookies_web() -> dict:
    """Cookies de session instagram.com : ceux enregistrés par la connexion, sinon le sessionid de compte.json."""
    if FICHIER_COOKIES.exists():
        cookies = json.loads(FICHIER_COOKIES.read_text(encoding="utf-8"))
    else:
        sessionid = (charger_compte().get("sessionid") or "").strip()
        if not sessionid:
            raise ErreurInstagram("Aucune session : lancer la connexion, ou mettre le cookie sessionid dans "
                                  "config/compte.json.")
        cookies = {"sessionid": sessionid}
    cookies.setdefault("ds_user_id", cookies["sessionid"].split("%3A")[0].split(":")[0])
    cookies.setdefault("csrftoken", "")
    return cookies


def sauver_cookies(cookies: dict) -> None:
    SESSIONS.mkdir(exist_ok=True)
    FICHIER_COOKIES.write_text(json.dumps(cookies, indent=2), encoding="utf-8")


def verifier() -> str:
    """Renvoie le pseudo connecté, ou lève ErreurInstagram."""
    c = cookies_web()
    r = requests.get(f"https://www.instagram.com/api/v1/users/{c['ds_user_id']}/info/", cookies=c,
                     headers={"User-Agent": NAVIGATEUR, "X-IG-App-ID": APP_ID_WEB}, timeout=30,
                     allow_redirects=False)
    if r.status_code != 200:
        raise ErreurInstagram(f"Session refusée ({r.status_code}) : {r.text[:200]}")
    return r.json()["user"]["username"]


def lancer_navigateur(pw):
    """Chrome installé sur la machine (le Chromium de Playwright ne se télécharge pas ici), sinon Edge."""
    for canal in ("chrome", "msedge", None):
        try:
            return (pw.chromium.launch(headless=not VISIBLE, channel=canal, slow_mo=50) if canal
                    else pw.chromium.launch(headless=not VISIBLE, slow_mo=50))
        except Exception:
            continue
    raise ErreurInstagram("Aucun navigateur utilisable (Chrome, Edge ou Chromium de Playwright).")


def lire_code() -> str:
    """Code de vérification : tapé au clavier, ou (lancement sans terminal) déposé dans sessions/code.txt ;
    on attend jusqu'à 15 minutes, le navigateur reste ouvert pendant ce temps."""
    if sys.stdin and sys.stdin.isatty():
        return input("Code reçu par mail (ou par SMS) : ").strip()
    FICHIER_CODE.unlink(missing_ok=True)
    print(f"En attente du code dans {FICHIER_CODE} (15 min max)…", flush=True)
    for _ in range(180):
        if FICHIER_CODE.exists() and FICHIER_CODE.read_text(encoding="utf-8").strip():
            code = FICHIER_CODE.read_text(encoding="utf-8").strip()
            FICHIER_CODE.unlink()
            return code
        time.sleep(5)
    raise ErreurInstagram("Pas de code reçu en 15 minutes.")


def connexion_navigateur() -> None:
    compte = charger_compte()
    if not compte.get("utilisateur") or not compte.get("mot_de_passe"):
        raise ErreurInstagram("Il faut utilisateur et mot_de_passe dans config/compte.json.")
    with sync_playwright() as pw:
        nav = lancer_navigateur(pw)
        ctx = nav.new_context(user_agent=NAVIGATEUR, locale="en-US", viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        for texte in ("Allow all cookies", "Only allow essential cookies", "Decline optional cookies"):
            bouton = page.get_by_role("button", name=texte)
            if bouton.count():
                bouton.first.click()
                page.wait_for_timeout(1500)
                break
        page.locator("input[name='username'], input[name='email']").first.type(
            compte["utilisateur"], delay=random.randint(80, 160))
        page.locator("input[name='password'], input[name='pass']").first.type(
            compte["mot_de_passe"], delay=random.randint(80, 160))
        page.keyboard.press("Enter")
        page.wait_for_timeout(9000)

        if "challenge" in page.url or "auth_platform" in page.url or "two_factor" in page.url:
            print("Instagram demande une vérification :", page.url)
            for nom in ("Send Security Code", "Continue", "Send code"):
                b = page.get_by_role("button", name=nom)
                if b.count():
                    b.first.click()
                    page.wait_for_timeout(4000)
                    break
            code = lire_code()
            champ = page.locator("input[name='security_code'], input[name='verificationCode'], "
                                 "input[autocomplete='one-time-code'], input[type='text']").first
            champ.type(code, delay=120)
            page.keyboard.press("Enter")
            page.wait_for_timeout(9000)

        cookies = {c["name"]: c["value"] for c in ctx.cookies() if "instagram.com" in c["domain"]}
        adresse, texte = page.url, page.inner_text("body")[:600]
        if not cookies.get("sessionid"):
            SESSIONS.mkdir(exist_ok=True)
            page.screenshot(path=str(SESSIONS / "echec_connexion.png"))  # la page du navigateur, pas l'écran
        nav.close()
    if not cookies.get("sessionid"):
        raise ErreurInstagram(f"Connexion refusée (pas de cookie de session).\nPage : {adresse}\n{texte}")
    sauver_cookies({k: cookies[k] for k in ("sessionid", "csrftoken", "ds_user_id", "mid", "ig_did", "rur")
                    if k in cookies})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser(prog="python -m collecte.connexion_instagram",
                                description="Connexion au compte de collecte Instagram")
    a.add_argument("--sessionid", help="valeur du cookie sessionid d'un navigateur connecté")
    a.add_argument("--verifier", action="store_true", help="tester la session enregistrée")
    args = a.parse_args()
    try:
        if args.sessionid:
            sauver_cookies({"sessionid": args.sessionid.strip()})
        elif not args.verifier:
            connexion_navigateur()
        print("Connecté en tant que", verifier())
    except ErreurInstagram as e:
        sys.exit(f"Échec : {e}")


if __name__ == "__main__":
    main()
