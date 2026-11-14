"""Chemins du paquet verification/."""
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CORPUS = RACINE / "corpus"
THEMES = RACINE / "themes"
REGISTRE = RACINE / "registre_affirmations.csv"
SYNTHESE = RACINE / "SYNTHESE.md"
