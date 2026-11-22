"""Mélenchon, thème 15 — Culture, numérique et intelligence artificielle (et espace) : téléchargement des sources.

python -m verification melenchon telecharger 15        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("ESA-ENVIRONNEMENT-SPATIAL-2026", "Agence spatiale européenne (bureau des débris spatiaux)",
           "ESA's Annual Space Environment Report, édition 10.1 (8 septembre 2026)", "A",
           "https://www.sdo.esoc.esa.int/environment_report/Space_Environment_Report_latest.pdf",
           "esa/space_environment_report_2026.pdf", ["CULT-01"], outil="curl", date_publication="2026-09-08"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
