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


RELUE, CORRIGEE = "relue", "corrigée"
LONGUEUR_PARTAGE = 60  # un texte plus court (« Exactement », « 😂 ») change de sens selon le parent : pas partagé


def lire_notes(corpus: list[dict] | None = None) -> dict[str, dict]:
    """Les notes à afficher et à publier, par clé de commentaire. Dans l'ordre de priorité :
    1. les corrections faites à la main dans l'interface (fiabilité « corrigée ») ;
    2. les notes données par Claude en annotation (fiabilité « relue ») : sur le commentaire annoté et, si l'on
       donne le corpus, sur les autres copies du même texte long (le même avis collé sous plusieurs posts) ;
    3. les notes du modèle.
    Les lots de contrôle de constance (renotation à l'aveugle) ne comptent pas."""
    from analyse.annotation import LOTS_CONSTANCE, annotations
    notes = lire_scores()
    par_texte = {}
    for a in annotations():
        if int(a["lot"]) >= LOTS_CONSTANCE:
            continue
        n = {"cle": a["cle"], "cible": a["cible"], **{c: a[c] for c in CRITERES}, "fiabilite": RELUE}
        notes[a["cle"]] = n
        par_texte[a["texte_cle"]] = n
    if corpus and par_texte:
        for l in corpus:
            n = par_texte.get(l["texte_cle"])
            if n and len(l["texte"]) >= LONGUEUR_PARTAGE and notes.get(l["cle"], {}).get("fiabilite") != RELUE:
                notes[l["cle"]] = {**n, "cle": l["cle"]}
    for cle, c in lire_corrections().items():
        notes[cle] = {**c, "fiabilite": CORRIGEE}
    return notes


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
