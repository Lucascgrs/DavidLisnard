"""Mélenchon, thème 18 — Climat, eau et environnement : téléchargement des sources brutes.

python -m verification melenchon telecharger 18        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

REPRISES = [
    ("EUROSTAT-GES", "11_energie", ["CLIM-02"]),
]
SOURCES = [
    Source("C3S-ERA5-TEMPERATURE", "Copernicus Climate Change Service (ECMWF), réanalyse ERA5",
           "Température moyenne mondiale de l'air près de la surface, quotidienne, 1940-2026 (Climate Pulse)", "A",
           "https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv",
           "copernicus/era5_daily_series_2t_global.csv", ["CLIM-01"], licence="Licence Copernicus (CC BY 4.0)",
           note="Les valeurs des derniers jours sont provisoires."),
    Source("IGN-MEMENTO-2025", "IGN (inventaire forestier national), copie publiée par cdurable.info",
           "Mémento de l'inventaire forestier, édition 2025", "A",
           "https://cdurable.info/wp-content/uploads/2025/10/memento2025.pdf", "ign/memento_inventaire_forestier_2025.pdf",
           ["CLIM-03"], outil="curl", date_publication="2025-10-14",
           note="Document de l'IGN ; le lien officiel n'était plus en ligne le 20/11/2026."),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
