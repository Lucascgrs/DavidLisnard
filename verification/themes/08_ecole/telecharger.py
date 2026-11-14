"""Thème 8 — École et enseignement : téléchargement des sources brutes.  python -m verification telecharger 8

Les sites de l'OCDE et du ministère de l'Éducation nationale (notes de la DEPP) refusent les téléchargements
automatiques. Les scores PISA 2022 viennent d'une reproduction officielle du tableau I.2.1 de l'OCDE publiée par le
ministère japonais de l'Éducation (MEXT).
"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("OCDE-PISA-2022-MEXT", "OCDE, PISA 2022 Results Volume I (tableaux reproduits par le ministère japonais de l'Éducation, MEXT)",
           "PISA 2022 : tableau I.2.1, performance des pays en mathématiques", "A",
           "https://www.mext.go.jp/content/20250213-mxt_chousa02-000040311-08.pdf", "ocde/PISA2022_tableau_I.2.1_MEXT.pdf",
           ["ECOLE-01"], outil="curl", date_publication="2023-12-05",
           note="Reproduction à l'identique des tableaux de l'OCDE (site oecd.org protégé) ; PDF chiffré, lisible avec pypdf + cryptography."),
    Source("BM-PISA-2000-2018", "Banque mondiale (indicateurs repris de l'OCDE)", "Score moyen PISA en mathématiques par pays, 2000-2018 (LO.PISA.MAT)",
           "A", "https://api.worldbank.org/v2/country/all/indicator/LO.PISA.MAT", "banque_mondiale/LO.PISA.MAT.json", ["ECOLE-01"],
           licence=CCBY, params={"format": "json", "per_page": "20000", "date": "2000:2022"}, entetes={}),
    Source("EUROSTAT-COFOG-EDUCATION", "Eurostat", "Dépenses des administrations publiques par fonction : enseignement (gov_10a_exp, GF09)", "A",
           EUROSTAT + "gov_10a_exp", "eurostat/gov_10a_exp_education_fr.json", ["ECOLE-02"], licence=CCBY,
           params={"geo": "FR", "sector": "S13", "cofog99": ["GF09", "GF0901", "GF0902", "TOTAL"], "na_item": "TE",
                   "unit": ["MIO_EUR", "PC_GDP"], "sinceTimePeriod": "1995"}),
    Source("EUROSTAT-PRIX-PIB", "Eurostat", "Déflateur du PIB et PIB en volume, France (nama_10_gdp)", "A", EUROSTAT + "nama_10_gdp",
           "eurostat/nama_10_gdp_deflateur_fr.json", ["ECOLE-02"], licence=CCBY,
           params={"geo": "FR", "na_item": "B1GQ", "unit": ["PD15_EUR", "CP_MEUR"], "sinceTimePeriod": "1995"}),
    Source("EUROSTAT-ELEVES", "Eurostat", "Élèves et étudiants inscrits par niveau (educ_uoe_enra01)", "A", EUROSTAT + "educ_uoe_enra01",
           "eurostat/educ_uoe_enra01_fr.json", ["ECOLE-02"], licence=CCBY,
           params={"geo": "FR", "isced11": ["ED1", "ED2", "ED3", "ED1-8"], "sex": "T", "worktime": "TOTAL", "sinceTimePeriod": "2013"}),
    Source("BUDGET-VERT-PLF2026", "Ministère de l'Économie (direction du Budget)",
           "PLF 2026 — Budget vert : crédits de paiement par programme", "A",
           "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/plf-2026-budget-vert/exports/csv",
           "budget/plf2026_budget_vert.csv", ["ECOLE-03"], licence=LO, params={"delimiter": ";"}),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:26} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
