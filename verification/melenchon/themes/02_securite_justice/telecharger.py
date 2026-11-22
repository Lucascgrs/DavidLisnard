"""Mélenchon, thème 2 — Sécurité, justice et narcotrafic : téléchargement des sources brutes.

python -m verification melenchon telecharger 2        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("OFDT-CHIFFRES-CLES-2025", "Observatoire français des drogues et des tendances addictives (OFDT)",
           "Drogues et addictions, chiffres clés 2025", "A",
           "https://www.ofdt.fr/sites/ofdt/files/2025-04/dacc_2025.pdf", "ofdt/drogues_addictions_chiffres_cles_2025.pdf",
           ["SECU-01"], licence="Licence ouverte Etalab 2.0", outil="curl", date_publication="2025-04"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
