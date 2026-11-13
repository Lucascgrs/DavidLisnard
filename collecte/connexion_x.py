"""Session du compte X de collecte (sessions/x_cookies.json), utilisée par la source X.

    python -m collecte.connexion_x              connexion avec X_PSEUDO et X_MDP de config/x.env
    python -m collecte.connexion_x --verifier   dit si la session enregistrée marche encore

X refuse toute connexion par mot de passe venant d'un script (« flow name login is currently not accessible »,
constaté le 2026-11-12) : la seule voie est la session d'un vrai navigateur. La connexion ouvre donc une fois Chrome,
visible, avec un profil à part (sessions/x_profil/) : rien du compte personnel n'y est chargé. Le pseudo et le mot de
passe sont saisis tout seuls ; si X demande une vérification (adresse mail, code reçu, captcha), X_MAIL est saisie si
elle est dans config/x.env, sinon on peut répondre dans la fenêtre (jusqu'à 10 minutes). On garde les cookies
auth_token et ct0, qui suffisent aux requêtes.

La collecte, elle, n'ouvre aucun navigateur : elle envoie ses requêtes avec ces cookies. Elle relance d'elle-même
cette connexion si la session a expiré. Ne jamais se déconnecter de ce compte dans le profil : la déconnexion annule
la session enregistrée.

Le profil garde toujours une copie de la session valable (y compris des cookies recopiés à la main dans
sessions/x_cookies.json). Une reconnexion essaie d'abord, sans fenêtre et sans mot de passe, de la faire renouveler
par X en ouvrant x.com/home ; le mot de passe ne sert que si X a annulé la session elle-même (le 2026-11-12 et le
2026-11-13, X refusait la connexion par mot de passe de ce Chrome piloté : « temporairement limité »).
"""
import argparse
import json
import sys
import time

from commun.config import FICHIER_X_ENV, SESSIONS, lire_env

FICHIER_COOKIES = SESSIONS / "x_cookies.json"
PROFIL = SESSIONS / "x_profil"
ATTENTE_MAX_S = 600
NECESSAIRES = ("auth_token", "ct0")


class ErreurConnexion(Exception):
    """Erreur à montrer telle quelle."""


def identifiants() -> tuple[str, str, str]:
    env = lire_env(FICHIER_X_ENV)
    pseudo, mdp = env.get("X_PSEUDO", "").lstrip("@"), env.get("X_MDP", "")
    if not pseudo or not mdp:
        raise ErreurConnexion("config/x.env absent ou incomplet : copier config/x.exemple.env en config/x.env et y "
                              "mettre X_PSEUDO et X_MDP du compte de collecte.")
    return pseudo, mdp, env.get("X_MAIL", "")


def lire_cookies() -> dict[str, str]:
    """{nom: valeur} des cookies enregistrés (vide s'il n'y en a pas)."""
    try:
        return {c["name"]: c["value"] for c in json.loads(FICHIER_COOKIES.read_text(encoding="utf-8"))}
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        return {}


def sauver_cookies(cookies: dict[str, str]) -> None:
    SESSIONS.mkdir(exist_ok=True)
    tmp = FICHIER_COOKIES.with_suffix(".tmp")
    tmp.write_text(json.dumps([{"name": k, "value": v} for k, v in cookies.items()], indent=1), encoding="utf-8")
    tmp.replace(FICHIER_COOKIES)


def chaine_cookies(cookies: dict[str, str] | None = None) -> str:
    """« auth_token=…; ct0=… », la forme attendue par twscrape."""
    cookies = lire_cookies() if cookies is None else cookies
    return "; ".join(f"{k}={cookies[k]}" for k in NECESSAIRES if cookies.get(k))


def verifier(cookies: dict[str, str] | None = None) -> str | None:
    """Pseudo du compte connecté si la session (enregistrée par défaut) marche, sinon None (une requête à X)."""
    cookies = lire_cookies() if cookies is None else cookies
    if not all(cookies.get(k) for k in NECESSAIRES):
        return None
    try:
        from curl_cffi import requests
    except ImportError:
        return None
    try:
        r = requests.get("https://x.com/home", impersonate="chrome", timeout=60,
                         cookies={k: cookies[k] for k in NECESSAIRES})
    except Exception:
        return None
    # Connecté, la page porte l'écran du compte (« screen_name » de l'utilisateur) ; déconnecté, la page d'accueil.
    import re
    m = re.search(r'"screen_name":"([A-Za-z0-9_]{1,15})"', r.text)
    return m.group(1) if r.status_code == 200 and m else None


def _cliquer(page, *libelles: str) -> bool:
    for libelle in libelles:
        try:
            # La page de novembre 2026 a deux boutons « Continuer », dont un caché : seul le visible compte.
            boutons = page.get_by_role("button", name=libelle, exact=True)
            for i in range(boutons.count()):
                if boutons.nth(i).is_visible():
                    boutons.nth(i).click(timeout=1500)
                    return True
        except Exception:
            pass
    return False


def _cookies_du_profil(ctx) -> dict[str, str]:
    return {c["name"]: c["value"] for c in ctx.cookies() if c["domain"].endswith("x.com")}


def _semer(ctx, cookies: dict[str, str]) -> None:
    """Met auth_token et ct0 dans le profil (comme si on s'y était connecté)."""
    ctx.add_cookies([{"name": k, "value": cookies[k], "domain": ".x.com", "path": "/", "secure": True,
                      "httpOnly": k == "auth_token", "sameSite": "None", "expires": time.time() + 365 * 86400}
                     for k in NECESSAIRES if cookies.get(k)])


def renouveler(journal=print) -> bool:
    """Sans fenêtre ni mot de passe : fait renouveler la session par X à partir du profil (ou des cookies
    enregistrés), l'enregistre et rend True ; rend False si X a annulé la session (il faut alors le mot de passe)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(str(PROFIL), channel="chrome", headless=True, locale="fr-FR")
        except Exception as e:
            raise ErreurConnexion(f"Chrome introuvable pour la connexion X ({str(e).splitlines()[0][:120]}).")
        try:
            fichier = lire_cookies()
            candidats = [c for c in ({k: v for k, v in _cookies_du_profil(ctx).items() if k in NECESSAIRES},
                                     {k: v for k, v in fichier.items() if k in NECESSAIRES})
                         if c.get("auth_token")]
            for cookies in candidats:
                _semer(ctx, cookies)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                try:
                    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=120000)
                    page.wait_for_timeout(5000)
                except Exception:
                    continue
                c = {k: v for k, v in _cookies_du_profil(ctx).items() if k in NECESSAIRES}
                if all(c.get(k) for k in NECESSAIRES) and verifier(c):
                    sauver_cookies(c)
                    journal("   session X renouvelée par le profil, sans mot de passe")
                    return True
            # Session annulée par X : on la retire du profil pour que la connexion par mot de passe reparte de zéro.
            for k in NECESSAIRES:
                ctx.clear_cookies(name=k)
            return False
        finally:
            ctx.close()


def connecter(journal=print) -> None:
    """Renouvelle la session par le profil si X l'accepte ; sinon ouvre Chrome et se connecte avec config/x.env,
    attend la session, enregistre auth_token et ct0."""
    if renouveler(journal):
        return
    from playwright.sync_api import sync_playwright
    pseudo, mdp, mail = identifiants()
    journal("   session X annulée par X : connexion par mot de passe (fenêtre Chrome)")
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(str(PROFIL), channel="chrome", headless=False,
                                                       locale="fr-FR", viewport={"width": 1100, "height": 800})
        except Exception as e:
            raise ErreurConnexion(f"Chrome introuvable pour la connexion X ({str(e).splitlines()[0][:120]}).")

        def session() -> dict[str, str]:
            return {c["name"]: c["value"] for c in ctx.cookies() if c["domain"].endswith("x.com")}

        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            if not session().get("auth_token"):
                page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=120000)
                _cliquer(page, "Refuser les cookies non nécessaires", "Refuser les cookies non essentiels",
                         "Refuse non-essential cookies", "Accepter tous les cookies", "Accept all cookies")
                # Deux pages de connexion vues : l'ancienne (« Suivant ») et celle de novembre 2026
                # (/i/jf/onboarding, champ « username_or_email », bouton « Continuer »).
                champ = page.locator("input[name=username_or_email], input[autocomplete~=username]").first
                champ.wait_for(state="visible", timeout=60000)
                page.wait_for_timeout(800)
                champ.fill(pseudo)
                page.wait_for_timeout(700)
                _cliquer(page, "Continuer", "Suivant", "Continue", "Next")
                # Selon X : le mot de passe, ou d'abord une vérification (mail, téléphone ou pseudo). Attention : la
                # première page porte déjà un champ « password » considéré comme visible (constaté le 2026-11-13) ;
                # on n'est sur la page du mot de passe qu'une fois le champ du pseudo disparu.
                mot_de_passe = page.locator("input[name=password]").first
                verification = page.locator("input[data-testid=ocfEnterTextTextInput]").first

                def page_du_mot_de_passe() -> bool:
                    return mot_de_passe.is_visible() and not champ.is_visible()

                debut = time.time()
                while time.time() - debut < 60 and not page_du_mot_de_passe():
                    try:
                        corps = page.inner_text("body", timeout=2000)
                    except Exception:
                        corps = ""
                    if "temporairement limité votre connexion" in corps or "temporarily limited" in corps:
                        raise ErreurConnexion("X limite les connexions de ce compte pour l'instant (« Nous avons "
                                              "temporairement limité votre connexion », affiché après le pseudo) : "
                                              "réessayer dans quelques heures, sans multiplier les essais.")
                    if verification.is_visible() and not champ.is_visible():
                        verification.fill(mail or pseudo)
                        page.wait_for_timeout(600)
                        _cliquer(page, "Continuer", "Suivant", "Continue", "Next")
                        page.wait_for_timeout(2500)
                    page.wait_for_timeout(1000)
                journal("   pseudo envoyé ; page du mot de passe " + ("affichée" if page_du_mot_de_passe() else
                                                                    "absente après 60 s"))
                if page_du_mot_de_passe():
                    mot_de_passe.fill(mdp)
                    page.wait_for_timeout(600)
                    if not _cliquer(page, "Se connecter", "Log in", "Continuer", "Continue"):
                        page.keyboard.press("Enter")
                journal("   connexion envoyée ; si X demande une vérification, y répondre dans la fenêtre Chrome "
                        f"(attente jusqu'à {ATTENTE_MAX_S // 60} min)")
            debut = time.time()
            while not (session().get("auth_token") and session().get("ct0")):
                try:
                    corps = page.inner_text("body", timeout=2000)
                except Exception:
                    corps = ""
                if "temporairement limité votre connexion" in corps or "temporarily limited" in corps:
                    raise ErreurConnexion("X limite les connexions de ce compte pour l'instant (« Nous avons "
                                          "temporairement limité votre connexion ») : réessayer dans quelques heures, "
                                          "sans multiplier les essais.")
                if time.time() - debut > ATTENTE_MAX_S:
                    raise ErreurConnexion(f"Pas de session X après {ATTENTE_MAX_S // 60} min (page : {page.url}). "
                                          "Vérification non faite, ou identifiants refusés.")
                page.wait_for_timeout(2000)
            # Une page connectée pour que X renouvelle ct0 si besoin, puis on relit les cookies.
            if "x.com/home" not in page.url:
                page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            c = session()
            sauver_cookies({k: c[k] for k in NECESSAIRES})
        except BaseException:
            # La page au moment de l'échec (seulement la page de Chrome), pour comprendre sans refaire d'essai.
            try:
                page.screenshot(path=str(SESSIONS / "x_connexion_echec.png"))
                journal(f"   page au moment de l'échec : {SESSIONS / 'x_connexion_echec.png'}")
            except Exception:
                pass
            raise
        finally:
            ctx.close()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m collecte.connexion_x", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verifier", action="store_true", help="dit seulement si la session enregistrée marche")
    ap.add_argument("--profil", action="store_true",
                    help="recopie seulement la session enregistrée dans le profil et la fait renouveler (après avoir "
                         "collé des cookies à la main dans sessions/x_cookies.json), sans mot de passe")
    args = ap.parse_args()
    if args.profil:
        if not renouveler():
            print("Échec : X refuse la session de sessions/x_cookies.json (annulée ou incomplète).")
            sys.exit(1)
    elif not args.verifier:
        try:
            connecter()
        except ErreurConnexion as e:
            print(f"Échec : {e}")
            sys.exit(1)
    nom = verifier()
    print(f"Session X valable : connecté en tant que @{nom}." if nom else
          "Pas de session X valable : lancer « python -m collecte.connexion_x ».")
    sys.exit(0 if nom else 1)


if __name__ == "__main__":
    main()
