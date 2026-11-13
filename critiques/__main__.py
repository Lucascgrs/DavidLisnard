"""Thèmes des critiques et des éloges (voir critiques/__init__.py et docs/FONCTIONNEMENT.pdf).

    python -m critiques etat                  où en est la lecture
    python -m critiques tirer [N]             prépare le lot suivant (100 commentaires par défaut)
    python -m critiques voir 3 [depuis]       affiche le lot 3, précédé de la liste des thèmes
    python -m critiques noter 3 lecture.txt   vérifie et enregistre la lecture du lot 3
    python -m critiques liste                 les thèmes, avec leur définition et leurs comptes
    python -m critiques proches [N]           les paires de thèmes qui pourraient fusionner
    python -m critiques fusionner f.txt       applique des fusions et des renommages
    python -m critiques a-resumer             les synthèses à écrire ou réécrire depuis la dernière fois, et elles seules
    python -m critiques syntheses f.txt       enregistre les synthèses rédigées par thème et par sens
    python -m critiques trier [N]             affiche le lot suivant de critiques et doutes sans catégorie (N textes)
    python -m critiques ranger 3 tri.txt      enregistre les catégories du lot de tri 3 (lignes « numéro catégorie »)

Chaque critique (C) ou doute (D) porte une catégorie de 1 à 5, notée à la lecture (« 12 | T5 | C3 | phrase ») :
1 opposition de principe, 2 demande de précision, 3 objection sur une mesure, 4 doute sur la faisabilité,
5 suggestion. « trier » et « ranger » servent à ce qui a été rangé avant que la catégorie existe.

Tous les rattachements sont faits par Claude, à la lecture. Mise à jour, à la demande : tirer / voir / noter jusqu'à
« Rien de nouveau à lire », puis proches, fusionner, a-resumer et syntheses, et enfin « python -m web publier » pour le site.
Une lecture ne porte que sur les commentaires nouveaux : ce qui est lu ne l'est jamais deux fois.
"""
import sys

from critiques import donnees


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help", "aide"):
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    if cmd == "etat":
        donnees.etat()
    elif cmd == "tirer":
        donnees.tirer(int(args[0]) if args else donnees.TAILLE_LOT)
    elif cmd == "voir":
        donnees.voir(int(args[0]), int(args[1]) if len(args) > 1 else 1)
    elif cmd == "noter":
        donnees.noter(int(args[0]), args[1])
    elif cmd == "liste":
        donnees.liste()
    elif cmd == "proches":
        donnees.proches(int(args[0]) if args else 60)
    elif cmd == "fusionner":
        donnees.fusionner(args[0])
    elif cmd == "a-resumer":
        donnees.a_resumer()
    elif cmd == "syntheses":
        donnees.syntheses(args[0])
    elif cmd == "trier":
        donnees.trier(int(args[0]) if args else donnees.TAILLE_LOT)
    elif cmd == "ranger":
        donnees.ranger(int(args[0]), args[1])
    else:
        raise SystemExit(f"Commande inconnue : {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
