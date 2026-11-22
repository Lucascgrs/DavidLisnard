"""Mélenchon, thème 17 — Inégalités, pauvreté et grandes fortunes : téléchargement des sources brutes.

python -m verification melenchon telecharger 17        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
INSEE = "https://www.insee.fr/fr/statistiques/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"

REPRISES = [
    ("EUROSTAT-SMIC-PAYS", "06_economie_travail", ["INEG-06"], "melenchon"),
    ("EUROSTAT-POPULATION", "01_dette_depense_fiscalite", ["INEG-05"], "melenchon"),
]
SOURCES = [
    Source("INSEE-PAUVRETE-TAUX", "Insee (enquêtes Revenus fiscaux et sociaux)",
           "Taux de pauvreté selon le seuil de pauvreté, données annuelles de 1975 à 2024", "A",
           INSEE + "fichier/2408282/reve-pauv-taux-seuil.xlsx", "insee/taux_pauvrete_1975_2024.xlsx",
           ["INEG-01", "INEG-02"], licence=LO, outil="curl", date_publication="2026-07-09"),
    Source("INSEE-PAUVRETE-NOMBRE", "Insee (enquêtes Revenus fiscaux et sociaux)",
           "Personnes pauvres selon le seuil de pauvreté, données annuelles de 1975 à 2024", "A",
           INSEE + "fichier/2408345/reve-pauv-nbre-personne-seuil.xlsx", "insee/personnes_pauvres_1975_2024.xlsx",
           ["INEG-01", "INEG-03"], licence=LO, outil="curl", date_publication="2026-07-09"),
    Source("INSEE-SEUILS-PAUVRETE", "Insee", "Seuils de pauvreté mensuels, données annuelles de 1975 à 2024 (page)", "A",
           INSEE + "2499760", "insee/seuils_pauvrete.html", ["INEG-06", "INEG-07"], licence=LO, outil="curl"),
    Source("INSEE-AIDE-ALIMENTAIRE-2022", "Insee", "Insee Première n° 1907 : les bénéficiaires de l'aide alimentaire "
           "(enquête fin 2021)", "A", INSEE + "fichier/6466177/IP_1907.pdf", "insee/IP1907_aide_alimentaire.pdf",
           ["INEG-04"], licence=LO, outil="curl", date_publication="2022-07"),
    Source("EUROSTAT-CHAUFFAGE", "Eurostat (enquête SRCV / EU-SILC)",
           "Personnes ne pouvant pas chauffer convenablement leur logement, France (ilc_mdes01)", "A",
           EUROSTAT + "ilc_mdes01", "eurostat/ilc_mdes01_fr.json", ["INEG-05"], licence=CCBY,
           params={"geo": "FR", "hhcomp": "TOTAL", "rskpovth": "TOTAL", "unit": "PC", "sinceTimePeriod": "2018"}),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
