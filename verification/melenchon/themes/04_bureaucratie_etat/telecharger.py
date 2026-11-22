"""Mélenchon, thème 4 — Bureaucratie, normes et réforme de l'État : téléchargement des sources brutes.

python -m verification melenchon telecharger 4        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

SOURCES = [
    Source("EUROSTAT-REMUNERATIONS-DEPENSES", "Eurostat",
           "Rémunération des salariés et dépense totale des administrations publiques et de l'État, % du PIB "
           "(gov_10a_main)", "A", EUROSTAT + "gov_10a_main", "eurostat/gov_10a_main_d1_te_fr.json",
           ["ETAT-01", "ETAT-02"], licence="CC BY 4.0",
           params={"geo": "FR", "sector": ["S13", "S1311"], "na_item": ["D1PAY", "TE"], "unit": "PC_GDP",
                   "sinceTimePeriod": "1995"}),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
