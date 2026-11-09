"""Analyse des commentaires : note ce qui ne l'est pas encore par le modèle en service.

    python -m analyse                                 tout ce qui n'est pas encore noté par le modèle actuel
    python -m analyse --sources youtube,whatsapp      seulement ces sources
    python -m analyse --du 2026-01-01 --au 2026-06-30 seulement cette période (date du commentaire)
    python -m analyse --refaire                       renote aussi ce qui l'a déjà été par ce modèle

Comme la collecte : un seul lancement à la fois (donnees/analyse/EN_COURS) et arrêt propre (donnees/analyse/ARRET).
Les autres commandes de l'analyse (annotation, entraînement) sont décrites dans README.md.
"""
import argparse
import sys

from analyse import stockage
from analyse.notation import NOM, analyser
from commun.journal import Journal
from commun.taches import ArretDemande, DejaEnCours, verrou


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="python -m analyse", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", default="", help="youtube,instagram,whatsapp (toutes par défaut)")
    ap.add_argument("--du", default="", help="AAAA-MM-JJ")
    ap.add_argument("--au", default="", help="AAAA-MM-JJ")
    ap.add_argument("--refaire", action="store_true")
    args = ap.parse_args()
    journal = Journal()
    try:
        with verrou(NOM):
            journal("### Analyse des commentaires")
            try:
                r = analyser([s for s in args.sources.split(",") if s], args.du or None, args.au or None,
                             args.refaire, journal)
                journal(f"### Analyse terminée : {r['notes']} commentaires notés (modèle {r['version']})")
            except ArretDemande:
                stockage.avancement("arrêtée")
                journal("### Analyse arrêtée à la demande (ce qui est noté est gardé)")
            except SystemExit as e:
                stockage.avancement("impossible", message=str(e))
                journal(f"### Analyse impossible : {e}")
    except DejaEnCours as e:
        journal(f"== analyse : déjà en cours (processus {e.pid})")


if __name__ == "__main__":
    main()
