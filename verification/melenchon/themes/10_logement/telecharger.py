"""Mélenchon, thème 10 — Logement et urbanisme : téléchargement des sources brutes.

python -m verification melenchon telecharger 10        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
LO = "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("BDT-LOGEMENTS-SOCIAUX-2024", "Banque des Territoires (Localtis), chiffres du ministère du Logement",
           "Près de 99.000 logements sociaux financés en 2024 (29 janvier 2025)", "E",
           "https://www.banquedesterritoires.fr/pres-de-99000-logements-sociaux-finances-en-2024",
           "presse/bdt_logements_sociaux_2024.html", ["LOG-01", "LOG-03"], outil="curl", date_publication="2025-01-29",
           note="Reprend les chiffres publiés par le ministère du Logement le 28 janvier 2025."),
    Source("FPL-ETRE-HUMAIN-130", "Fondation pour le logement des défavorisés (ex-Fondation Abbé Pierre)",
           "Être humain n° 130 (janvier 2026) : chiffres clés du mal-logement", "D",
           "https://www.fondationpourlelogement.fr/wp-content/uploads/2026/01/etre-humain-130-web.pdf",
           "fondation_logement/etre_humain_130.pdf", ["LOG-01", "LOG-02"], outil="curl", date_publication="2026-01"),
    Source("INSEE-DEF-SANS-DOMICILE", "Insee", "Définition : sans-domicile", "A",
           "https://www.insee.fr/fr/metadonnees/definition/c1256", "insee/definition_sans_domicile.html", ["LOG-02"],
           licence=LO, outil="curl"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
