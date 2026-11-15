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
import http.server
import json
import webbrowser
from pathlib import Path

from web import acces, comptes
from web.vercel import Vercel

ICI = Path(__file__).resolve().parent
SITE = ICI / "site"
CONFIG_JS = SITE / "js" / "config.js"
MOTS = ICI / "mots_surveilles.txt"
MOTS_JS = SITE / "js" / "mots.js"
PROJET_VERCEL = "moderation-lisnard"
EMAIL = "moderateurs@moderation-lisnard.app"  # adresse du compte partagé, jamais montrée : on ne tape que le mot de passe


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
    ecrire_mots()


def lire_mots() -> list[dict]:
    """Les mots surveillés (mots_surveilles.txt) : [{mot, rubrique}], dans l'ordre du fichier, sans doublon."""
    sortie, rubrique, vus = [], "", set()
    for ligne in MOTS.read_text(encoding="utf-8").splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        if not ligne:
            continue
        if ligne.startswith("[") and ligne.endswith("]"):
            rubrique = ligne[1:-1].strip()
        elif ligne.lower() not in vus:
            vus.add(ligne.lower())
            sortie.append({"mot": ligne, "rubrique": rubrique})
    return sortie


def ecrire_mots() -> None:
    """js/mots.js, lu par le site : la comparaison (accents, lettres répétées, chiffres déguisés) se fait là-bas."""
    MOTS_JS.write_text(
        "// Écrit par « python -m moderation site deployer » depuis moderation/mots_surveilles.txt : ne pas modifier.\n"
        f"export const MOTS = {json.dumps(lire_mots(), ensure_ascii=False)};\n", encoding="utf-8", newline="\n")


def definir_mot_de_passe(mot_de_passe: str, journal=print) -> None:
    """(Re)crée le compte des modérateurs avec ce mot de passe ; ferme toutes les sessions de l'ancien compte."""
    comptes.definir_mot_de_passe(EMAIL, "moderateur", mot_de_passe, journal)


def demander_mot_de_passe() -> str:
    return comptes.demander_mot_de_passe("des modérateurs")


def deployer(journal=print) -> str:
    a = acces.exiger("vercel_jeton")
    ecrire_config()
    comptes.fermer_inscriptions(journal)
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

