"""Mélenchon, thème 12 — Agriculture : téléchargement des sources brutes.

python -m verification melenchon telecharger 12        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

SOURCES = [
    Source("EUROSTAT-EMPLOI-AGRICOLE", "Eurostat (comptes nationaux)",
           "Emploi dans l'agriculture, la sylviculture et la pêche, France (nama_10_a10_e, branche A)", "A",
           EUROSTAT + "nama_10_a10_e", "eurostat/nama_10_a10_e_agriculture_fr.json", ["AGRI-01"], licence="CC BY 4.0",
           params={"geo": "FR", "nace_r2": "A", "unit": "THS_PER", "na_item": ["EMP_DC", "SAL_DC"],
                   "sinceTimePeriod": "2000"}),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
