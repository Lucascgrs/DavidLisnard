"""Collecte : récupère ce qui est nouveau depuis le dernier lancement, source par source.

    python -m collecte                          toutes les sources
    python -m collecte youtube bluesky          seulement celles-là
    python -m collecte --reessayer instagram    relance une source abandonnée (critère des 30 minutes)

Résultats : donnees/<source>/ (un CSV par compte + <source>_tout.xlsx), donnees/bilan.md, donnees/journal.log.
Une source qui échoue n'arrête pas les suivantes. À la fin, les données sont sauvegardées
(donnees/sauvegardes/donnees.zip). Si du neuf a été collecté, les nouveaux commentaires sont ensuite notés par le
modèle (option de l'onglet Analyse, cochée par défaut), puis publiés sur le site (« python -m web ») et
exportés vers le bucket R2 privé du groupe sur Cloudflare (« python -m cloudflare »). Le
rangement par thèmes, lui, se fait à la demande : c'est Claude qui lit (« python -m critiques »). Enfin, si
Facebook a ramené du neuf, les nouveaux commentaires Facebook sont classés pour la modération (« python -m
moderation classer », à part de l'analyse) et envoyés dans la table privée « moderation » de Supabase.
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


def sauvegarder(journal: Journal) -> None:
    """À la fin de chaque collecte : la sauvegarde unique des données qu'on ne peut pas refaire (commun/sauvegarde.py).
    Une erreur ici ne fait jamais échouer la collecte."""
    from commun import sauvegarde
    try:
        sauvegarde.sauvegarder_sous_verrou(journal)
    except sauvegarde.SauvegardeRefusee as e:
        journal(f"### SAUVEGARDE REFUSÉE : {e}")
    except BaseException as e:
        journal(f"### Sauvegarde impossible : {type(e).__name__}: {e}")


def publier_le_site(journal: Journal) -> None:
    """Après les notes : met à jour le site public, si son installation est faite (python -m web installer). Une
    erreur ici ne fait jamais échouer la collecte."""
    from web import acces
    if not acces.pret_a_publier():
        return
    try:
        with verrou("web"):
            from web.publication import publier
            journal("### Publication sur le site")
            publier(journal=journal)
    except DejaEnCours:
        journal("== site : une publication est déjà en cours")
    except BaseException as e:
        journal(f"### Publication sur le site impossible : {type(e).__name__}: {e}")


def exporter_vers_cloudflare(journal: Journal) -> None:
    """Après la publication : le fichier de chaque source qui a changé remplace l'ancien dans le bucket R2 du groupe
    (python -m cloudflare, docs/CLOUDFLARE.md). Dans un processus à part, comme les autres envois. Une erreur ici ne
    fait jamais échouer la collecte."""
    import os
    import subprocess
    from commun.config import RACINE
    from commun.taches import PYTHON
    journal("### Export vers Cloudflare R2")
    try:
        r = subprocess.run([PYTHON, "-m", "cloudflare"], cwd=RACINE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode:
            journal(f"### Export vers Cloudflare R2 impossible : {(r.stderr or r.stdout).strip().splitlines()[-1:]}")
    except Exception as e:
        journal(f"### Export vers Cloudflare R2 impossible : {type(e).__name__}: {e}")


def classer_pour_la_moderation(journal: Journal) -> None:
    """Si Facebook a ramené du neuf : classe les nouveaux commentaires pour la modération (moderation/, à part de
    l'analyse) et envoie le résultat dans la table privée « moderation » de Supabase. Quelques secondes. Une erreur
    ici ne fait jamais échouer la collecte."""
    from moderation import donnees, modele
    if not donnees.infos_modele():
        return
    journal("### Modération : classement des nouveaux commentaires Facebook")
    try:
        modele.classer()
        e = donnees.etat()
        journal(f"### Modération : {e['classes']} commentaires classés, {e['insultants']} à modérer, "
                f"{e['questions']} questions (détail : donnees/moderation/journal.log)")
    except DejaEnCours:
        journal("== modération : déjà en cours, les nouveaux seront classés par elle ou à la prochaine")
    except ArretDemande:
        journal("### Modération arrêtée à la demande")
    except BaseException as e:
        journal(f"### Modération impossible : {type(e).__name__}: {e}")


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
    sauvegarder(journal)
    if any(r.get("nouveaux") for r in resultats):
        noter_les_nouveaux(journal)
        publier_le_site(journal)
        exporter_vers_cloudflare(journal)
    if any(r.get("nouveaux") for r in resultats if r.get("source") == "facebook"):
        classer_pour_la_moderation(journal)


if __name__ == "__main__":
    main()
