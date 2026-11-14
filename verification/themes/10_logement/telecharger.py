"""Thème 10 — Logement et urbanisme : téléchargement des sources brutes.  python -m verification telecharger 10"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
DIDO = "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"
COL = {"withColumnName": "true", "withColumnDescription": "false"}

SOURCES = [
    Source("SDES-LOGEMENTS-MENSUEL", "Ministère de la Transition écologique (SDES, base Sitadel)",
           "Logements autorisés et commencés, séries mensuelles nationales (données estimées)", "A",
           DIDO + "175486a6-76a3-4c6c-a34b-aeb96758910b/csv", "sdes/logements_mensuel_national.csv", ["LOG-01"], licence=LO, params=COL),
    Source("EUROSTAT-POPULATION", "Eurostat (données Insee)", "Population au 1er janvier, France entière et France métropolitaine (demo_gind)", "A",
           EUROSTAT + "demo_gind", "eurostat/demo_gind_population.json", ["LOG-01"], licence=CCBY,
           params={"geo": ["FR", "FX"], "indic_de": "JAN", "sinceTimePeriod": "1960"}),
    Source("EUROSTAT-COFOG-LOGEMENT", "Eurostat", "Dépenses publiques par fonction : logement et équipements collectifs (gov_10a_exp, GF06, GF0601 et GF1006)", "A",
           EUROSTAT + "gov_10a_exp", "eurostat/gov_10a_exp_logement.json", ["LOG-02"], licence=CCBY,
           params={"sector": "S13", "cofog99": ["GF06", "GF0601", "GF1006"], "na_item": "TE", "unit": ["PC_GDP", "MIO_EUR"], "sinceTimePeriod": "2018"}),
    Source("EUROSTAT-PROTSOC-LOGEMENT", "Eurostat", "Prestations sociales de logement (spr_exp_func, fonction HOU)", "A",
           EUROSTAT + "spr_exp_func", "eurostat/spr_exp_func_logement.json", ["LOG-02"], licence=CCBY,
           params={"spfunc": "HOU", "unit": ["PC_GDP", "MIO_EUR"], "sinceTimePeriod": "2018"}),
    Source("OCDE-RECETTES-IMMOBILIER", "OCDE (statistiques des recettes publiques)", "Recettes fiscales totales et impôts sur le patrimoine (4000, 4100, 4400)", "A",
           "https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_OECD@DF_RSOECD,/..S13._T+T_4000+T_4100+T_4400._T.PT_B1GQ.A",
           "ocde/recettes_patrimoine.csv", ["LOG-03"], licence=CCBY, params={"startPeriod": "2019", "format": "csvfilewithlabels"}),
    Source("CREDOC-1986-CONSTRUCTION", "CRÉDOC (revue Consommation)", "Article de 1986 sur l'investissement en logement : séries de mises en chantier 1950-1985", "B",
           "https://www.credoc.fr/download/pdf/Sou/Sou1986-3360.pdf", "credoc/Sou1986-3360.pdf", ["LOG-01"], outil="curl",
           note="Pas de série longue officielle téléchargeable avant 2000 ; chiffres de 1971-1976 lus dans le texte"),
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
