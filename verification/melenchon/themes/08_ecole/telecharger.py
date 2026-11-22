"""Mélenchon, thème 8 — École et enseignement : téléchargement des sources brutes.

python -m verification melenchon telecharger 8        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
LO = "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("DEPP-NI-26-05-BAC", "Ministère de l'Éducation nationale (DEPP)",
           "Note d'information n° 26.05 : résultats définitifs du baccalauréat 2025", "A",
           "https://www.education.gouv.fr/sites/default/files/document/Education%20nationale_DEPP_NI%2026-05-Bac.pdf-479534.pdf",
           "depp/NI_26-05_bac_2025.pdf", ["ECOLE-01"], licence=LO, outil="curl", date_publication="2026-02"),
    Source("INSEE-IP1426-ECRIT", "Insee", "Insee Première n° 1426 : les compétences des adultes à l'écrit, en calcul et à "
           "l'oral (enquête Information et vie quotidienne 2011)", "A",
           "https://www.insee.fr/fr/statistiques/1281410", "insee/IP1426_competences_ecrit.html", ["ECOLE-02"],
           licence=LO, outil="curl", date_publication="2012-12-18"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
