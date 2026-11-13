"""Site de modération des commentaires Facebook, réservé aux modérateurs (pages dans moderation/site/).

Pages statiques sur Vercel (projet à part du site public), qui lisent Supabase après connexion :

- connexion par Supabase Auth : un seul compte partagé, dont l'adresse est fixe (EMAIL) et dont le mot de passe est
  choisi par l'utilisateur (« python -m moderation motdepasse ») puis communiqué aux modérateurs. Le compte porte
  app_metadata.role = « moderateur », que seule la clé secrète peut écrire ; les inscriptions sont fermées ;
- les règles de la base (web/schema.sql, « Site de modération ») ne laissent lire les tables privées moderation et
  utilisateurs, et les vues moderation_site / moderation_auteurs / moderation_publications, qu'à ce compte ;
- changer le mot de passe recrée le compte : toutes les sessions ouvertes sont aussitôt fermées (est_moderateur()
  vérifie que le compte existe encore). Le suivi (« traité », « sans suite ») ne dépend pas du compte et reste.

Rien n'est copié vers le site : il lit la base à chaque recherche. La clé dans les pages est la clé publique ; sans
connexion, elle ne donne accès à rien de la modération.
"""
import functools
import getpass
import http.server
import json
import webbrowser
from pathlib import Path

import requests

from web import acces
from web.supabase import Gestion, _verifier, entetes
from web.vercel import Vercel

ICI = Path(__file__).resolve().parent
SITE = ICI / "site"
CONFIG_JS = SITE / "js" / "config.js"
PROJET_VERCEL = "moderation-lisnard"
EMAIL = "moderateurs@moderation-lisnard.app"  # adresse du compte partagé, jamais montrée : on ne tape que le mot de passe
LONGUEUR_MIN = 10


def _acces() -> dict:
    return acces.exiger("supabase_url", "supabase_cle_publique", "supabase_cle_secrete", "supabase_jeton",
                        "supabase_projet")


def ecrire_config() -> None:
    a = _acces()
    CONFIG_JS.write_text(
        "// Écrit par « python -m moderation site deployer ». Clé publique : sans connexion, elle ne donne accès à rien\n"
        "// de la modération (règles de web/schema.sql).\n"
        f"export const SUPABASE_URL = {json.dumps(a['supabase_url'])};\n"
        f"export const SUPABASE_CLE = {json.dumps(a['supabase_cle_publique'])};\n"
        f"export const EMAIL = {json.dumps(EMAIL)};\n", encoding="utf-8", newline="\n")


def fermer_inscriptions(journal=print) -> None:
    """Personne ne peut se créer un compte : le seul compte est celui des modérateurs."""
    a = _acces()
    g = Gestion(a["supabase_jeton"])
    chemin = f"/projects/{a['supabase_projet']}/config/auth"
    if not g.appel("GET", chemin).get("disable_signup"):
        g.appel("PATCH", chemin, json={"disable_signup": True})
        journal("   inscriptions fermées sur Supabase Auth")


def _admin(methode: str, chemin: str, **kw):
    a = _acces()
    r = _verifier(requests.request(methode, a["supabase_url"] + "/auth/v1/admin" + chemin,
                                   headers={**entetes(a["supabase_cle_secrete"]), "Content-Type": "application/json"},
                                   timeout=60, **kw))
    return r.json() if r.content else None


def definir_mot_de_passe(mot_de_passe: str, journal=print) -> None:
    """(Re)crée le compte des modérateurs avec ce mot de passe ; ferme toutes les sessions de l'ancien compte."""
    if len(mot_de_passe) < LONGUEUR_MIN:
        raise ValueError(f"mot de passe trop court ({LONGUEUR_MIN} caractères au moins)")
    fermer_inscriptions(journal)
    page = 1
    while True:
        users = (_admin("GET", "/users", params={"page": page, "per_page": 200}) or {}).get("users", [])
        for u in users:
            if (u.get("email") or "").lower() == EMAIL:
                _admin("DELETE", f"/users/{u['id']}")
                journal("   ancien compte supprimé : les sessions ouvertes sont fermées")
        if len(users) < 200:
            break
        page += 1
    _admin("POST", "/users", json={"email": EMAIL, "password": mot_de_passe, "email_confirm": True,
                                   "app_metadata": {"role": "moderateur"}})
    journal("   compte des modérateurs créé avec le nouveau mot de passe")


def demander_mot_de_passe() -> str:
    while True:
        m1 = getpass.getpass(f"Nouveau mot de passe des modérateurs ({LONGUEUR_MIN} caractères au moins) : ")
        if len(m1) < LONGUEUR_MIN:
            print("Trop court.")
            continue
        if getpass.getpass("Le retaper : ") != m1:
            print("Les deux saisies diffèrent.")
            continue
        return m1


def deployer(journal=print) -> str:
    a = acces.exiger("vercel_jeton")
    ecrire_config()
    fermer_inscriptions(journal)
    url = Vercel(a["vercel_jeton"]).deployer(SITE, journal, projet=PROJET_VERCEL)
    acces.sauver(moderation_url=url)
    journal(f"   en ligne : {url}")
    return url


def apercu(port: int = 8001) -> None:
    ecrire_config()
    gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), gestion) as serveur:
        print(f"Aperçu sur http://localhost:{port} (Ctrl+C pour arrêter)")
        webbrowser.open(f"http://localhost:{port}")
        serveur.serve_forever()

