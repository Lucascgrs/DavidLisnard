"""Mélenchon, thème 11 — Énergie et nucléaire : téléchargement des sources brutes.

python -m verification melenchon telecharger 11        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
DOCS = "https://www.ecologie.gouv.fr/sites/default/files/documents/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"

REPRISES = [
    ("CE-BULLETIN-PETROLIER", "01_dette_depense_fiscalite", ["NRJ-02"]),
    ("EUROSTAT-PRODUCTION-ELEC", "11_energie", ["NRJ-05"]),
]
SOURCES = [
    Source("EUROSTAT-IPCH-ENERGIE", "Eurostat", "Indice des prix à la consommation harmonisé, gaz et carburants, France, "
           "base 2025 (prc_hicp_minr)", "A", EUROSTAT + "prc_hicp_minr", "eurostat/prc_hicp_minr_energie_fr.json",
           ["NRJ-01"], licence=CCBY,
           params={"geo": "FR", "unit": "I25", "coicop18": ["TOTAL", "CP0452", "CP0722"], "sinceTimePeriod": "2017-01"}),
    Source("DGEC-MARGE-RAFFINAGE", "Ministère de la Transition écologique (DGEC)",
           "Historique de la marge brute de raffinage sur Brent depuis 2015 (moyennes mensuelles)", "A",
           DOCS + "Historique%20de%20la%20marge%20brute%20de%20raffinage%20sur%20Brent%20depuis%202015%20%28moyennes%20mensuelles%29.xlsx",
           "dgec/marge_brute_raffinage_mensuelle.xlsx", ["NRJ-03"], licence=LO, outil="curl",
           note="Marge « théorique » : panier de produits raffinés à Rotterdam moins le Brent, pas la marge réelle des "
                "raffineries françaises."),
    Source("DGEC-PRIX-CARBURANTS", "Ministère de la Transition écologique (DGEC)",
           "Prix de vente hors taxes et toutes taxes des carburants routiers depuis janvier 2020 (hebdomadaire)", "A",
           DOCS + "Prix%20HTT%20et%20TTC%20depuis%20janvier%202020_0.xlsx", "dgec/prix_carburants_2020_2026.xlsx",
           ["NRJ-02", "NRJ-04"], licence=LO, outil="curl"),
    Source("EUROSTAT-PART-RENOUVELABLES", "Eurostat",
           "Part des énergies renouvelables dans la consommation finale brute d'énergie (nrg_ind_ren)", "A",
           EUROSTAT + "nrg_ind_ren", "eurostat/nrg_ind_ren_fr.json", ["NRJ-05"], licence=CCBY,
           params={"geo": ["FR", "EU27_2020"], "nrg_bal": "REN", "unit": "PC", "sinceTimePeriod": "2015"}),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
