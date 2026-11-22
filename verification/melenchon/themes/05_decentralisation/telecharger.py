"""Mélenchon, thème 5 — Décentralisation et collectivités : téléchargement des sources brutes.

python -m verification melenchon telecharger 5        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("RNE-MAIRES", "Ministère de l'Intérieur (répertoire national des élus)",
           "Répertoire national des élus : maires (date de naissance, catégorie socioprofessionnelle)", "A",
           "https://static.data.gouv.fr/resources/repertoire-national-des-elus-1/20261120-104746/elus-maire-mai.csv",
           "interieur/rne_maires_2026-11-20.csv", ["DEC-01"], licence="Licence ouverte Etalab 2.0",
           date_publication="2026-11-20", note="Mandats issus des élections municipales de mars 2026."),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
