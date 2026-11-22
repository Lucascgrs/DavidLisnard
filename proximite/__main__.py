"""python -m proximite <commande>

  collecter [candidat]       liste des candidats (candidats2027.org), téléchargement des programmes, texte de chaque
                             document ; signale les documents nouveaux ou modifiés
  lire <candidat> [page]     tout le texte des documents à lire, par pages (lu en entier par Claude)
  relire <candidat>          remet tous les documents du candidat « à lire »
  noter <candidat> <fichier> enregistre les mesures relevées dans un document (format : proximite/mesures.py)
  etat                       documents à lire, mesures relevées par candidat
  lu <candidat> [fichier]    marque comme lus les documents du candidat (après avoir écrit ses mesures)
  calculer                   notes par sous-thème et par axe, coordonnées, distances → donnees/proximite/positions.json
  site [apercu|deployer]     régénère le site (proximite/site/) ; apercu l'ouvre en local, deployer le met en ligne

La lecture des programmes (relever les mesures, les ranger, les noter) se fait à la main par Claude, en entier, selon
docs/GRILLE_PROXIMITE.md, dans donnees/proximite/mesures/<candidat>.csv.
"""
import sys


def main(args: list[str]) -> None:
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not args or args[0] in {"-h", "--help", "aide"}:
        print(__doc__)
        return
    cmd, reste = args[0], args[1:]
    if cmd == "collecter":
        from .collecte import collecter
        collecter(seul=reste[0] if reste else None)
    elif cmd == "lire":
        from .mesures import lire
        lire(reste[0], int(reste[1]) if len(reste) > 1 else 1)
    elif cmd == "relire":
        from .mesures import relire
        relire(reste[0])
    elif cmd == "noter":
        from .mesures import noter
        noter(reste[0], reste[1])
    elif cmd == "etat":
        from .mesures import etat
        etat()
    elif cmd == "lu":
        from .mesures import marquer_lu
        marquer_lu(reste[0], reste[1] if len(reste) > 1 else None)
    elif cmd == "calculer":
        from .positions import calculer
        calculer()
    elif cmd == "site":
        from .site import main as site
        site(reste)
    else:
        raise SystemExit(f"Commande inconnue : {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
