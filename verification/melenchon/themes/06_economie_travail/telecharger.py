"""Mélenchon, thème 6 — Économie, travail et entreprises : téléchargement des sources brutes.

python -m verification melenchon telecharger 6        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"
PAYS_SMIC = ["FR", "ES", "PT", "DE", "NL", "BE"]

SOURCES = [
    Source("EUROSTAT-SMIC-PAYS", "Eurostat", "Salaires minimums mensuels bruts, six pays (earn_mw_cur)", "A",
           EUROSTAT + "earn_mw_cur", "eurostat/earn_mw_cur_6pays.json", ["ECO-01", "ECO-12"], licence=CCBY,
           params={"geo": PAYS_SMIC, "currency": "EUR", "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-CROISSANCE", "Eurostat", "Croissance du PIB en volume, tous pays (nama_10_gdp, CLV_PCH_PRE)", "A",
           EUROSTAT + "nama_10_gdp", "eurostat/croissance_pib_pays.json", ["ECO-02"], licence=CCBY,
           params={"unit": "CLV_PCH_PRE", "na_item": "B1GQ", "sinceTimePeriod": "2022"}),
    Source("EUROSTAT-EMPLOIS-VACANTS", "Eurostat (enquête Acemo de la Dares)",
           "Emplois vacants, trimestriel, France (jvs_q_nace2)", "A", EUROSTAT + "jvs_q_nace2",
           "eurostat/jvs_q_nace2_fr.json", ["ECO-03"], licence=CCBY,
           params={"geo": "FR", "nace_r2": "B-S", "s_adj": "NSA", "sinceTimePeriod": "2023-Q1"}),
    Source("EUROSTAT-CHOMEURS", "Eurostat (enquête Emploi de l'Insee)",
           "Chômeurs au sens du BIT, 15-74 ans, trimestriel, France (une_rt_q)", "A", EUROSTAT + "une_rt_q",
           "eurostat/une_rt_q_fr.json", ["ECO-03"], licence=CCBY,
           params={"geo": "FR", "age": "Y15-74", "sex": "T", "s_adj": "SA", "unit": "THS_PER",
                   "sinceTimePeriod": "2023-Q1"}),
    Source("URSSAF-DPAE", "Urssaf Caisse nationale",
           "Déclarations préalables à l'embauche, France entière, par secteur et nature de contrat (trimestriel)", "A",
           "https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38/exports/csv",
           "urssaf/dpae_france_na38_2019_2026.csv", ["ECO-04"], licence=LO,
           params={"where": 'annee>="2019"', "delimiter": ";"},
           note="Hors intérim. Diffusion suspendue de novembre 2025 au 30 octobre 2026 (erreurs sur le type de contrat "
                "en 2025), reprise avec des corrections selon l'Urssaf."),
    Source("EUROSTAT-PROD-INDUS", "Eurostat", "Indice de la production industrielle, annuel, France (sts_inpr_a)", "A",
           EUROSTAT + "sts_inpr_a", "eurostat/sts_inpr_a_fr.json", ["ECO-05"], licence=CCBY,
           params={"geo": "FR", "nace_r2": ["B-D", "C"], "unit": "I21", "s_adj": "CA", "sinceTimePeriod": "2015"}),
    Source("BM-DOING-BUSINESS-2019", "Banque mondiale (Doing Business, archive)",
           "Rang au classement de la facilité de faire des affaires, données 2019 (rapport Doing Business 2020)", "A",
           "https://api.worldbank.org/v2/country/all/indicator/IC.BUS.EASE.XQ",
           "banque_mondiale/doing_business_rang_2019.json", ["ECO-06"], licence=CCBY,
           params={"format": "json", "date": "2019", "source": "1", "per_page": "400"},
           note="Classement arrêté par la Banque mondiale en septembre 2021 après des irrégularités dans les données."),
    Source("EUROSTAT-AT-MORTELS", "Eurostat (statistiques européennes des accidents du travail)",
           "Accidents du travail mortels : nombre et taux d'incidence pour 100 000 travailleurs (hsw_n2_02)", "A",
           EUROSTAT + "hsw_n2_02", "eurostat/hsw_n2_02.json", ["ECO-07"], licence=CCBY,
           params={"nace_r2": "TOTAL", "sinceTimePeriod": "2019"}),
    Source("REPSS-ATMP-2026", "Sécurité sociale (annexe 1 au projet de loi d'approbation des comptes 2025)",
           "Rapport d'évaluation des politiques de sécurité sociale, accidents du travail et maladies professionnelles "
           "(données 2024)", "B",
           "https://www.assemblee-nationale.fr/dyn/contenu/visualisation/1112994/file/PLACSS%202025%20Annexe%201%20-%20REPSS%20AT-MP%202026.pdf",
           "securite_sociale/REPSS_ATMP_2026.pdf", ["ECO-07", "ECO-08"], licence=LO, outil="curl",
           date_publication="2026"),
    Source("EUROSTAT-IPCH", "Eurostat", "Indice des prix à la consommation harmonisé, France, base 2025 (prc_hicp_minr)",
           "A", EUROSTAT + "prc_hicp_minr", "eurostat/prc_hicp_minr_fr.json", ["ECO-09"], licence=CCBY,
           params={"geo": "FR", "unit": "I25", "coicop18": ["TOTAL", "CP011"], "sinceTimePeriod": "2017-01"}),
    Source("EUROSTAT-PIB-EMPLOIS", "Eurostat", "PIB, consommation des ménages et rémunération des salariés (nama_10_gdp)",
           "A", EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_conso_fr.json", ["ECO-10"], licence=CCBY,
           params={"geo": "FR", "unit": "CP_MEUR", "na_item": ["B1GQ", "P31_S14", "P31_S14_S15", "D1"],
                   "sinceTimePeriod": "2015"}),
    Source("IFR-DENSITE-2025", "International Federation of Robotics (fédération professionnelle)",
           "Robot Density Surges in Europe, Asia, and Americas (World Robotics 2025, communiqué)", "D",
           "https://ifr.org/ifr-press-releases/news/robot-density-surges-in-europe-asia-and-americas",
           "ifr/robot_density_2025.html", ["ECO-11"], outil="curl"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
