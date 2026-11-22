"""Mélenchon, thème 1 — Dette, dépense publique et fiscalité : téléchargement des sources brutes.

python -m verification melenchon telecharger 1        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"
T01 = "01_dette_depense_fiscalite"

REPRISES = [
    ("HCSP-AIDES-2025", T01, ["DETTE-01"]),
    ("SP-IMPOT-SOCIETES", T01, ["DETTE-06"]),
    ("BOFIP-CONTRIBUTION-EXCEPTIONNELLE", T01, ["DETTE-06"]),
]
SOURCES = [
    Source("EUROSTAT-DEFICITS", "Eurostat", "Solde des administrations publiques et de l'État, France (gov_10a_main, B9)",
           "A", EUROSTAT + "gov_10a_main", "eurostat/gov_10a_main_b9_fr.json", ["DETTE-02"], licence=CCBY,
           params={"geo": "FR", "sector": ["S13", "S1311"], "na_item": "B9", "unit": ["MIO_EUR", "PC_GDP"],
                   "sinceTimePeriod": "2019"}),
    Source("EUROSTAT-PATRIMOINE-NF", "Eurostat", "Actifs non financiers des administrations publiques, France "
           "(nama_10_nfa_bs)", "A", EUROSTAT + "nama_10_nfa_bs", "eurostat/nama_10_nfa_bs_apu_fr.json", ["DETTE-03"],
           licence=CCBY, params={"geo": "FR", "sector": ["S13", "S1311"], "unit": "CP_MEUR", "asset10": ["N1N", "N2N"],
                                 "sinceTimePeriod": "2020"}),
    Source("EUROSTAT-PATRIMOINE-FIN", "Eurostat", "Actifs et passifs financiers des administrations publiques, France "
           "(nasa_10_f_bs)", "A", EUROSTAT + "nasa_10_f_bs", "eurostat/nasa_10_f_bs_apu_fr.json", ["DETTE-03"],
           licence=CCBY, params={"geo": "FR", "sector": ["S13", "S1311"], "unit": "MIO_EUR", "co_nco": "NCO",
                                 "na_item": "F", "finpos": ["ASS", "LIAB"], "sinceTimePeriod": "2020"}),
    Source("EUROSTAT-POPULATION", "Eurostat", "Population au 1er janvier, France (demo_gind)", "A",
           EUROSTAT + "demo_gind", "eurostat/demo_gind_fr.json", ["DETTE-03"], licence=CCBY,
           params={"geo": "FR", "indic_de": "JAN", "sinceTimePeriod": "2020"}),
    Source("EUROSTAT-DETTE-PAYS", "Eurostat (notifications de déficit et de dette)",
           "Dette et solde publics en % du PIB, tous pays (gov_10dd_edpt1)", "A", EUROSTAT + "gov_10dd_edpt1",
           "eurostat/gov_10dd_edpt1_pays.json", ["DETTE-04", "DETTE-05"], licence=CCBY,
           params={"na_item": ["GD", "B9"], "sector": "S13", "unit": "PC_GDP", "sinceTimePeriod": "2007"}),
    Source("EUROSTAT-PIB-PAYS-2025", "Eurostat", "PIB en euros courants, tous pays et agrégats, 2025 (nama_10_gdp)", "A",
           EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_pays_2025.json", ["DETTE-04"], licence=CCBY,
           params={"unit": "CP_MEUR", "na_item": "B1GQ", "time": "2025"}),
    Source("SP-BAREME-IR", "Service-public.fr (direction de l'information légale et administrative)",
           "Impôt sur le revenu : calcul et barème (tranches et taux)", "A",
           "https://www.service-public.fr/particuliers/vosdroits/F1419", "droit/service_public_bareme_ir.html",
           ["DETTE-07"], licence=LO, outil="curl"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
