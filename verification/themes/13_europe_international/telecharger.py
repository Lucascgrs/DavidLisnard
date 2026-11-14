"""Thème 13 — Europe et international : téléchargement des sources brutes.  python -m verification telecharger 13"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
COMEXT = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/"
IMF = "https://www.imf.org/external/datamapper/api/v1/"
CCBY = "CC BY 4.0"

SOURCES = [
    Source("EUROSTAT-PIB-HAB-SPA", "Eurostat", "PIB par habitant en standards de pouvoir d'achat, indice UE à 27 = 100 (prc_ppp_ind)", "A",
           EUROSTAT + "prc_ppp_ind", "eurostat/prc_ppp_ind_pib_hab.json", ["EUR-01", "EUR-02"], licence=CCBY,
           params={"na_item": "VI_PPS_EU27_2020_HAB", "ppp_cat": "GDP"}),
    Source("FMI-PIB-HAB-DOLLARS", "Fonds monétaire international (WEO)", "PIB par habitant en dollars courants, tous pays (NGDPDPC)", "A",
           IMF + "NGDPDPC", "fmi/ngdpdpc.json", ["EUR-03"], entetes={}),
    Source("FMI-PIB-HAB-PPA", "Fonds monétaire international (WEO)", "PIB par habitant en parité de pouvoir d'achat, tous pays (PPPPC)", "A",
           IMF + "PPPPC", "fmi/ppppc.json", ["EUR-03"], entetes={}),
    Source("FMI-POPULATION", "Fonds monétaire international (WEO)", "Population, tous pays (LP, millions)", "A",
           IMF + "LP", "fmi/lp.json", ["EUR-03"], entetes={}),
    Source("FMI-PAYS", "Fonds monétaire international", "Liste des pays du datamapper (pour exclure les regroupements)", "A",
           IMF + "countries", "fmi/countries.json", ["EUR-03"], entetes={}),
    Source("DRAGHI-2024-A", "Commission européenne (rapport de M. Draghi)", "The future of European competitiveness, partie A : stratégie de compétitivité (septembre 2024)", "A",
           "https://commission.europa.eu/document/download/97e481fd-2dc3-412d-be4c-f152a8232961_en?filename=The%20future%20of%20European%20competitiveness%20_%20A%20competitiveness%20strategy%20for%20Europe.pdf",
           "commission/draghi_partie_A.pdf", ["EUR-04"], licence="réutilisation autorisée (décision 2011/833/UE)", outil="curl"),
    Source("OTAN-DEPENSES-2025", "OTAN", "Defence expenditure of NATO countries (2014-2025), communiqué du 27 août 2025", "A",
           "https://www.nato.int/nato_static_fl2014/assets/pdf/2025/8/pdf/250827-def-exp-2025-en.pdf", "otan/def_exp_2025.pdf", ["EUR-05"], outil="curl"),
    Source("EUROSTAT-PIB-COURANT", "Eurostat", "PIB de la France en euros courants (nama_10_gdp, CP_MEUR)", "A",
           EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_fr.json", ["EUR-05"], licence=CCBY,
           params={"geo": "FR", "na_item": "B1GQ", "unit": "CP_MEUR", "sinceTimePeriod": "2020"}),
    Source("COMEXT-UE-CHINE", "Eurostat (Comext)", "Commerce de l'UE avec la Chine, tous produits (ds-045409)", "A",
           COMEXT + "ds-045409", "eurostat/comext_ue_chine.json", ["EUR-06"], licence=CCBY,
           params={"reporter": "EU", "partner": "CN", "product": "TOTAL", "flow": ["1", "2"], "freq": "A", "indicators": "VALUE_IN_EUROS",
                   "time": [str(a) for a in range(2010, 2026)]}),
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
