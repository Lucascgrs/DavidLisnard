"""Les fichiers de l'analyse, tous dans donnees/analyse/.

- corpus.csv : copie de travail des commentaires collectés (analyse/corpus.py) ;
- vecteurs/ : vecteurs de sens des textes (analyse/vecteurs.py) ;
- scores.csv : les notes du modèle, une ligne par commentaire ;
- corrections.csv : les notes corrigées à la main dans l'interface (elles priment et servent à l'entraînement) ;
- annotation/ : lots, annotations de Claude, constance, recalage (analyse/annotation.py) ;
- avancement.json : où en est l'analyse en cours (lu par l'interface) ;
- reglages.json : options de l'onglet Analyse ;
- RAPPORT_MODELE.md : qualité mesurée du modèle en service ;
- exports/ : exports Excel faits depuis l'interface.
"""
from datetime import datetime

from analyse.criteres import CRITERES
from commun.config import DONNEES
from commun.fichiers import ecrire_csv, ecrire_json, lire_csv, lire_csv_par_cle, lire_json
from commun.textes import maintenant

ANALYSE = DONNEES / "analyse"
CORPUS = ANALYSE / "corpus.csv"
VECTEURS = ANALYSE / "vecteurs"
SCORES = ANALYSE / "scores.csv"
CORRECTIONS = ANALYSE / "corrections.csv"
ANNOTATION = ANALYSE / "annotation"
AVANCEMENT = ANALYSE / "avancement.json"
REGLAGES = ANALYSE / "reglages.json"
RAPPORT = ANALYSE / "RAPPORT_MODELE.md"
EXPORTS = ANALYSE / "exports"
JOURNAL_REENTRAINEMENT = ANALYSE / "reentrainement.log"
CONSTANCE = ANNOTATION / "constance.json"

CHAMPS_SCORES = ["cle", "version"] + CRITERES + ["cible", "p_autre", "fiabilite", "le"]
CHAMPS_CORRECTIONS = ["cle", "cible"] + CRITERES + ["le"]


def lire_scores() -> dict[str, dict]:
    return lire_csv_par_cle(SCORES)


def ecrire_scores(scores: dict[str, dict]) -> None:
    ecrire_csv(SCORES, scores.values(), CHAMPS_SCORES)


def lire_corrections() -> dict[str, dict]:
    return lire_csv_par_cle(CORRECTIONS)


def enregistrer_correction(cle: str, cible: str, notes: dict) -> None:
    """Remplace la correction de ce commentaire s'il en avait déjà une."""
    lignes = [c for c in lire_csv(CORRECTIONS) if c["cle"] != cle]
    lignes.append({"cle": cle, "cible": cible, **notes, "le": datetime.now().isoformat(timespec="seconds")})
    ecrire_csv(CORRECTIONS, lignes, CHAMPS_CORRECTIONS)


def reglages() -> dict:
    return {"apres_collecte": True, **(lire_json(REGLAGES, {}) or {})}


def sauver_reglages(**valeurs) -> None:
    ecrire_json(REGLAGES, {**reglages(), **valeurs})


def avancement(etape: str, fait: int = 0, total: int = 0, **autres) -> None:
    ecrire_json(AVANCEMENT, {"etape": etape, "fait": fait, "total": total, "le": maintenant(), **autres})


def lire_avancement() -> dict:
    return lire_json(AVANCEMENT, {}) or {}
