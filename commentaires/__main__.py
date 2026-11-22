"""Le site public : https://analyse-commentaires-lisnard.vercel.app (adresse exacte dans config/web.json).

    python -m commentaires installer     crée ou met à jour la base Supabase, relève ses clés (une fois, ou après schema.sql)
    python -m commentaires publier       envoie les commentaires notés nouveaux ou changés, recalcule les statistiques
    python -m commentaires publier --tout  renvoie tout
    python -m commentaires deployer      met en ligne les pages de commentaires/site/ (après une modification des pages)
    python -m commentaires tout          les trois à la suite
    python -m commentaires apercu        ouvre les pages en local (http://localhost:8000), sur les données en ligne
    python -m commentaires motdepasse    choisit le mot de passe du site (le demande deux fois) ; ferme les sessions ouvertes
                                avec l'ancien. Sans connexion, le site ne montre rien.

Après chaque collecte qui ramène du neuf, la publication se fait seule (commun/collecte/__main__.py).
"""
import argparse
import functools
import http.server
import sys
import webbrowser

from commun.taches import DejaEnCours, verrou
from commentaires import publication


def apercu(port: int) -> None:
    gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(publication.SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), gestion) as serveur:
        print(f"Aperçu sur http://localhost:{port} (Ctrl+C pour arrêter)")
        webbrowser.open(f"http://localhost:{port}")
        serveur.serve_forever()


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m commentaires", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["installer", "publier", "deployer", "tout", "apercu", "motdepasse"])
    ap.add_argument("--tout", action="store_true", help="publier : renvoyer toutes les lignes")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    if args.action == "apercu":
        return apercu(args.port)
    if args.action == "motdepasse":
        from commentaires import comptes
        return publication.definir_mot_de_passe(comptes.demander_mot_de_passe("du site"))
    try:
        if args.action in ("installer", "publier", "tout"):
            with verrou("web"):  # une seule écriture dans la base à la fois
                if args.action in ("installer", "tout"):
                    print("== Installation de la base")
                    publication.installer()
                if args.action in ("publier", "tout"):
                    print("== Publication des données")
                    publication.publier(tout=args.tout)
        if args.action in ("deployer", "tout"):
            with verrou("web_pages"):
                print("== Mise en ligne des pages")
                publication.deployer()
    except DejaEnCours as e:
        sys.exit(f"Déjà en cours (processus {e.pid}) : attendre sa fin.")


if __name__ == "__main__":
    main()
