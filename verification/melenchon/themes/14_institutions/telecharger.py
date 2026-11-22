"""Mélenchon, thème 14 — Institutions, référendum et normes : téléchargement des sources brutes.

python -m verification melenchon telecharger 14        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("AN-FICHE-64", "Assemblée nationale",
           "Fiche de synthèse n° 64 : la responsabilité du Gouvernement (article 49, état fin 2024)", "B",
           "https://www.assemblee-nationale.fr/dyn/contenu/telechargement/629167/file/Fiche%2064%20-%20Responsabilit%C3%A9%20du%20Gouvernement.pdf",
           "assemblee/fiche_64_responsabilite_gouvernement.pdf", ["INST-01"], outil="curl"),
    Source("INTERIEUR-REFERENDUM-2005", "Ministère de l'Intérieur (data.gouv.fr)",
           "Référendum du 29 mai 2005 : résultats par régions, départements, circonscriptions et cantons", "A",
           "https://static.data.gouv.fr/50/cd65a14d56f53f704af4922d75223773ca39b5f92ceecd7d69a07ed1e19c53.xls",
           "interieur/referendum_2005.xls", ["INST-02"], licence="Licence ouverte Etalab 2.0"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
