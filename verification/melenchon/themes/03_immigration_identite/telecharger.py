"""Mélenchon, thème 3 — Immigration, islamisme et identité : téléchargement des sources brutes.

python -m verification melenchon telecharger 3        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("SP-NATIONALITE-NE-EN-FRANCE", "Service-public.fr (direction de l'information légale et administrative)",
           "Nationalité française d'un enfant né en France de parents étrangers (F295)", "A",
           "https://www.service-public.fr/particuliers/vosdroits/F295", "droit/service_public_F295_nationalite.html",
           ["IMMI-01"], licence="Licence ouverte Etalab 2.0", outil="curl"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
