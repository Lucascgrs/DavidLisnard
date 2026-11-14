"""Thème 6 — Économie, travail et entreprises : téléchargement des sources brutes.  python -m verification telecharger 6"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY = "CC BY 4.0"
PDB = "OECD/DSD_PDB@DF_PDB_LV/"
SERIES = ",".join(PDB + f"{p}.A.GDPHRS._T.{u}.Q._Z._Z._Z" for p in ("USA", "EA20", "FRA", "DEU") for u in ("USD_PPP_H", "XDC_H")) + "," + ",".join(
    PDB + f"{p}.A.GDPHRS._T.USD_PPP_H.V._Z._Z._Z" for p in ("USA", "EA20", "FRA", "DEU"))

SOURCES = [
    Source("EUROSTAT-COMMERCE-BIENS", "Eurostat (comptes nationaux)", "Exportations et importations de biens, prix courants (nama_10_gdp, P61 et P71)",
           "A", EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_biens.json", ["ECO-01"], licence=CCBY,
           params={"geo": "FR", "unit": "CP_MEUR", "na_item": ["P61", "P71", "P6", "P7"], "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-COMMERCE-DOUANES", "Eurostat (statistiques du commerce international de biens, données douanières)",
           "Solde, exportations et importations de biens de la France avec le monde (ext_lt_intratrd)", "A",
           EUROSTAT + "ext_lt_intratrd", "eurostat/ext_lt_intratrd_fr.json", ["ECO-01"], licence=CCBY,
           params={"geo": "FR", "partner": "WORLD", "sitc06": "TOTAL", "indic_et": ["MIO_BAL_VAL", "MIO_EXP_VAL", "MIO_IMP_VAL"],
                   "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-PIB-PAYS", "Eurostat (comptes nationaux)", "PIB aux prix courants, pays comparés (nama_10_gdp, B1GQ)", "A",
           EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_pays.json", ["ECO-02"], licence=CCBY,
           params={"unit": "CP_MEUR", "na_item": "B1GQ", "sinceTimePeriod": "2020"}),
    Source("EUROSTAT-VA-BRANCHES", "Eurostat (comptes nationaux)", "Valeur ajoutée brute par branche (nama_10_a10)", "A",
           EUROSTAT + "nama_10_a10", "eurostat/nama_10_a10.json", ["ECO-02"], licence=CCBY,
           params={"unit": "CP_MEUR", "na_item": "B1G", "nace_r2": ["TOTAL", "B-E", "C"], "sinceTimePeriod": "2000"}),
    Source("OCDE-PRODUCTIVITE", "OCDE (base de données de la productivité, diffusée par DBnomics)",
           "PIB par heure travaillée, volume, États-Unis, zone euro, France, Allemagne", "A",
           "https://api.db.nomics.world/v22/series", "ocde/pib_par_heure.json", ["ECO-03"], licence=CCBY,
           params={"series_ids": SERIES, "observations": "1"}),
    Source("EUROSTAT-CHOMAGE-ANNUEL", "Eurostat (enquête sur les forces de travail)", "Taux de chômage par âge, annuel (une_rt_a)", "A",
           EUROSTAT + "une_rt_a", "eurostat/une_rt_a.json", ["ECO-04"], licence=CCBY,
           params={"age": ["Y15-24", "Y15-74"], "sex": "T", "unit": "PC_ACT", "sinceTimePeriod": "2019"}),
    Source("EUROSTAT-CHOMAGE-TRIM", "Eurostat (enquête sur les forces de travail)", "Taux de chômage trimestriel corrigé des variations saisonnières (une_rt_q)",
           "A", EUROSTAT + "une_rt_q", "eurostat/une_rt_q_fr.json", ["ECO-04"], licence=CCBY,
           params={"geo": "FR", "age": "Y15-74", "sex": "T", "unit": "PC_ACT", "s_adj": "SA", "sinceTimePeriod": "2024-Q1"}),
    Source("EUROSTAT-RD", "Eurostat", "Dépense intérieure de recherche et développement par secteur d'exécution, % du PIB (rd_e_gerdtot)", "A",
           EUROSTAT + "rd_e_gerdtot", "eurostat/rd_e_gerdtot.json", ["ECO-05"], licence=CCBY,
           params={"unit": "PC_GDP", "sectperf": ["TOTAL", "GOV", "HES", "BES"], "sinceTimePeriod": "2018"}),
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
