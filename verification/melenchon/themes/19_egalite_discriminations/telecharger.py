"""Mélenchon, thème 19 — Égalité femmes-hommes et discriminations : téléchargement des sources brutes.

python -m verification melenchon telecharger 19        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("INSEE-FOCUS-ECARTS-SALAIRE-2024", "Insee", "Insee Focus : écarts de salaire entre femmes et hommes en 2024 "
           "(secteur privé)", "A", "https://www.insee.fr/fr/statistiques/8743657", "insee/focus_ecarts_salaire_2024.html",
           ["EGAL-01"], licence="Licence ouverte Etalab 2.0", date_publication="2026-02"),
    Source("ILGA-RAINBOW-MAP-2017", "ILGA-Europe (association), copie publiée par l'Inter-LGBT",
           "Rainbow Europe Map, mai 2017 (classement des pays)", "D",
           "https://www.inter-lgbt.org/wp-content/uploads/2018/02/rainbow_europe_map_2017.pdf",
           "ilga/rainbow_europe_map_2017.pdf", ["EGAL-02"], outil="curl", date_publication="2017-05"),
    Source("ILGA-RAINBOW-MAP-2026", "ILGA-Europe (association)", "Rainbow Map 2026 (classement et commentaires par pays)",
           "D", "https://www.ilga-europe.org/report/rainbow-map-2026/", "ilga/rainbow_map_2026.html", ["EGAL-02"],
           outil="curl", date_publication="2026-05"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
