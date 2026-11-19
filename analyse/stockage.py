"""Les fichiers de l'analyse, tous dans donnees/analyse/.

- corpus.csv : la table centrale, une ligne par commentaire : ce qui vient de la collecte, les notes du modèle et le
  classement de la modération (analyse/corpus.py) ;
- vecteurs/ : vecteurs de sens des textes (analyse/vecteurs.py) ;
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
CORRECTIONS = ANALYSE / "corrections.csv"
ANNOTATION = ANALYSE / "annotation"
AVANCEMENT = ANALYSE / "avancement.json"
REGLAGES = ANALYSE / "reglages.json"
RAPPORT = ANALYSE / "RAPPORT_MODELE.md"
EXPORTS = ANALYSE / "exports"
JOURNAL_REENTRAINEMENT = ANALYSE / "reentrainement.log"
CONSTANCE = ANNOTATION / "constance.json"

CHAMPS_CORRECTIONS = ["cle", "cible"] + CRITERES + ["le"]
# Notes du modèle telles que les lit le reste du code ; dans le corpus, « version » et « le » s'appellent
# note_version et note_le.
EN_COLONNE = {"version": "note_version", "le": "note_le"}


def lire_scores(corpus: list[dict] | None = None) -> dict[str, dict]:
    """Les notes du modèle, par clé : {cle, version, 5 notes, cible, p_autre, fiabilite, le}. Lues dans le corpus
    (colonnes note_…), ou dans les lignes `corpus` déjà chargées."""
    from analyse.corpus import CHAMPS_NOTES, lire_colonnes
    if corpus is None:
        lignes = lire_colonnes(CHAMPS_NOTES + ["cle"]).values()
    else:
        lignes = (l for l in corpus if l.get("note_version"))
    retour = {v: k for k, v in EN_COLONNE.items()}
    return {l["cle"]: {"cle": l["cle"], **{retour.get(c, c): l.get(c) or "" for c in CHAMPS_NOTES}} for l in lignes}


def enregistrer_scores(scores: dict[str, dict]) -> int:
    """Écrit dans le corpus les notes du modèle de ces commentaires ({cle: {version, 5 notes, cible, …, le}})."""
    from analyse.corpus import CHAMPS_NOTES, enregistrer
    return enregistrer({k: {EN_COLONNE.get(c, c): v for c, v in n.items()} for k, n in scores.items()}, CHAMPS_NOTES)


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
    notes = lire_scores(corpus)
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
