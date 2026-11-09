"""Collecte : récupère ce qui est nouveau depuis le dernier lancement, source par source.

    python -m collecte                          toutes les sources
    python -m collecte youtube whatsapp         seulement celles-là
    python -m collecte --reessayer instagram    relance une source abandonnée (critère des 30 minutes)

Résultats : donnees/<source>/ (un CSV par compte + <source>_tout.xlsx), donnees/bilan.md, donnees/journal.log.
Une source qui échoue n'arrête pas les suivantes. Si du neuf a été collecté, les nouveaux commentaires sont ensuite
notés par le modèle (option de l'onglet Analyse, cochée par défaut).
"""
import argparse
import importlib
import sys
import time
import traceback

from collecte.depot import Depot, SourceImpossible, ecrire_bilan
from commun.config import SOURCES
from commun.journal import Journal
from commun.taches import ArretDemande, DejaEnCours, verrou
from commun.textes import maintenant


def lancer(nom: str, journal: Journal, reessayer: bool) -> dict:
    try:
        with verrou(nom, sans_veille=True):
            return collecter(nom, journal, reessayer)
    except DejaEnCours as e:
        journal(f"== {nom} : déjà en cours de collecte (processus {e.pid}), on n'en lance pas une deuxième")
        return {"source": nom, "statut": "déjà en cours", "nouveaux": 0, "par_compte": {}, "total": Depot(nom).total(),
                "duree": "0.0 min"}


def collecter(nom: str, journal: Journal, reessayer: bool) -> dict:
    depot = Depot(nom)
    debut = time.time()
    resultat = {"source": nom}
    if depot.etat.get("abandon") and not reessayer:
        resultat.update(statut="abandonnée", message=f"{depot.etat['abandon']} "
                        f"(relancer avec « python -m collecte --reessayer {nom} »)", total=depot.total())
        journal(f"== {nom} : abandonnée ({depot.etat['abandon']})")
        return resultat
    if reessayer:
        depot.etat.pop("abandon", None)
    journal(f"== {nom}")
    try:
        module = importlib.import_module(f"collecte.sources.{nom}")
        resultat.update(module.collecter(depot, journal) or {})
        resultat.setdefault("statut", "ok")
    except SourceImpossible as e:
        resultat.update(statut="impossible", message=str(e))
        journal(f"   impossible : {e}")
    except ArretDemande:
        resultat.update(statut="arrêtée", message="Arrêt demandé : ce qui a été lu est enregistré, la suite reprendra "
                                                  "au prochain lancement.")
        journal("   arrêtée à la demande")
    except KeyboardInterrupt:
        resultat.update(statut="interrompue")
        raise
    except Exception as e:
        resultat.update(statut="erreur", message=f"{type(e).__name__} : {e}")
        journal(f"   erreur : {type(e).__name__} : {e}")
        journal(traceback.format_exc())
    finally:
        resultat["nouveaux"] = depot.nouveaux
        resultat["par_compte"] = depot.par_compte
        resultat["total"] = depot.total()
        resultat["duree"] = f"{(time.time() - debut) / 60:.1f} min"
        depot.etat["dernier"] = {"le": maintenant(), "statut": resultat.get("statut", "interrompue"),
                                 "nouveaux": depot.nouveaux, "duree": resultat["duree"],
                                 "message": resultat.get("message", "")}
        depot.sauver_etat()
        try:
            xlsx = depot.excel()
            if xlsx:
                journal(f"   {depot.nouveaux} nouveaux, {resultat['total']} au total → {xlsx}")
        except Exception as e:
            journal(f"   Excel non écrit : {e}")
    return resultat


def noter_les_nouveaux(journal: Journal) -> None:
    """Après une collecte qui a ramené du neuf : notes des nouveaux commentaires, si un modèle existe et si l'option
    de l'onglet Analyse est cochée. Une erreur ici ne fait jamais échouer la collecte."""
    from analyse import stockage, versions
    if not stockage.reglages()["apres_collecte"] or not versions.derniere_version():
        return
    try:
        with verrou("analyse"):
            from analyse.notation import analyser
            journal("### Analyse des nouveaux commentaires")
            r = analyser(journal=journal)
            journal(f"### Analyse terminée : {r['notes']} commentaires notés (modèle {r['version']})")
    except DejaEnCours:
        journal("== analyse : déjà en cours, les nouveaux commentaires seront notés par elle ou à la prochaine")
    except ArretDemande:
        journal("### Analyse arrêtée à la demande")
    except BaseException as e:
        journal(f"### Analyse impossible : {type(e).__name__}: {e}")


def main():
    if sys.stdout:  # absent quand on est lancé sans console
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m collecte", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*", help=f"sources à collecter parmi {', '.join(SOURCES)} (défaut : toutes)")
    ap.add_argument("--reessayer", action="store_true", help="relancer une source marquée abandonnée")
    args = ap.parse_args()
    inconnues = [s for s in args.sources if s not in SOURCES]
    if inconnues:
        ap.error(f"source inconnue : {', '.join(inconnues)} (possibles : {', '.join(SOURCES)})")
    choisies = args.sources or list(SOURCES)
    journal = Journal()
    journal(f"### Lancement : {', '.join(choisies)}")
    resultats = []
    try:
        for nom in choisies:
            resultats.append(lancer(nom, journal, args.reessayer))
    finally:
        journal(f"### Fini. Bilan : {ecrire_bilan(resultats)}")
    if any(r.get("nouveaux") for r in resultats):
        noter_les_nouveaux(journal)


if __name__ == "__main__":
    main()
