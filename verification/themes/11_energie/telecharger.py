"""Thème 11 — Énergie et nucléaire : téléchargement des sources brutes.  python -m verification telecharger 11"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CRE = "https://www.cre.fr/fileadmin/Documents/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"
IMF = "https://www.imf.org/external/datamapper/api/v1/"

SOURCES = [
    Source("EUROSTAT-PRODUCTION-ELEC", "Eurostat", "Production brute d'électricité par combustible (nrg_bal_peh)", "A",
           EUROSTAT + "nrg_bal_peh", "eurostat/nrg_bal_peh_fr.json", ["NRJ-01", "NRJ-02"], licence=CCBY,
           params={"geo": "FR", "nrg_bal": "GEP", "unit": "GWH", "siec": ["TOTAL", "N900H", "RA000", "RA130", "FE"],
                   "sinceTimePeriod": "2015"}),
    Source("FMI-PIB-DOLLARS", "Fonds monétaire international (WEO)", "PIB en dollars courants, France et monde (NGDPD)", "A",
           IMF + "NGDPD/FRA/WEOWORLD", "fmi/ngdpd_fra_monde.json", ["NRJ-03"], entetes={}),
    Source("FMI-PIB-PPA-PART", "Fonds monétaire international (WEO)", "Part du PIB mondial en parité de pouvoir d'achat (PPPSH)", "A",
           IMF + "PPPSH/FRA", "fmi/pppsh_fra.json", ["NRJ-03"], entetes={}),
    Source("GCB-OWID-CO2", "Global Carbon Budget 2025, mis en forme par Our World in Data", "Émissions de CO2 territoriales et de consommation par pays", "B",
           "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv", "owid/owid-co2-data.csv", ["NRJ-03"], licence=CCBY),
    Source("EUROSTAT-PIB-VOLUME", "Eurostat", "PIB en volume, UE à 27 (nama_10_gdp, CLV10_MEUR)", "A",
           EUROSTAT + "nama_10_gdp", "eurostat/nama_10_gdp_ue.json", ["NRJ-04"], licence=CCBY,
           params={"geo": ["EU27_2020", "FR"], "na_item": "B1GQ", "unit": "CLV10_MEUR"}),
    Source("EUROSTAT-GES", "Eurostat (inventaires CCNUCC)", "Émissions de gaz à effet de serre, UE à 27 (env_air_gge)", "A",
           EUROSTAT + "env_air_gge", "eurostat/env_air_gge_ue.json", ["NRJ-04"], licence=CCBY,
           params={"geo": ["EU27_2020", "FR"], "airpol": ["GHG", "CO2"], "src_crf": ["TOTX4_MEMO", "TOTXMEMO"], "unit": "THS_T"}),
    Source("EUROSTAT-PRIX-ENTREPRISES", "Eurostat", "Prix de l'électricité des consommateurs non résidentiels, par tranche (nrg_pc_205)", "A",
           EUROSTAT + "nrg_pc_205", "eurostat/nrg_pc_205_fr.json", ["NRJ-05"], licence=CCBY,
           params={"geo": ["FR", "DE", "EU27_2020"], "currency": "EUR", "unit": "KWH", "tax": ["X_TAX", "X_VAT", "I_TAX"], "sinceTimePeriod": "2020-S1"}),
    Source("EIA-PRIX-SECTEURS", "U.S. Energy Information Administration (Electric Power Annual)", "Prix moyen de l'électricité par secteur (tableau 2.4)", "A",
           "https://www.eia.gov/electricity/annual/xls/epa_02_04.xlsx", "eia/epa_02_04.xlsx", ["NRJ-05"], licence="domaine public (État fédéral américain)"),
    Source("EUROSTAT-CHANGE-USD", "Eurostat (BCE)", "Taux de change euro/dollar, moyenne annuelle (ert_bil_eur_a)", "A",
           EUROSTAT + "ert_bil_eur_a", "eurostat/ert_bil_eur_a_usd.json", ["NRJ-05"], licence=CCBY,
           params={"currency": "USD", "statinfo": "AVG", "sinceTimePeriod": "2019"}),
    Source("BOFIP-ACCISE-2026", "Direction générale des finances publiques (BOFiP)", "BOI-RES-EAT-000240 : tarifs d'accise sur l'électricité au 1er février 2026", "A",
           "https://bofip.impots.gouv.fr/bofip/14903-PGP.html/identifiant=BOI-RES-EAT-000240-20251224", "bofip/BOI-RES-EAT-000240-20251224.html", ["NRJ-06"],
           licence=LO, outil="curl"),
    Source("AN-QE16278-TICFE", "Assemblée nationale (réponse du gouvernement)", "Question écrite n° 16278 (XVe législature) : TICFE à 22,5 €/MWh pour les ménages", "A",
           "https://questions.assemblee-nationale.fr/dyn/15/questions/QANR5L15QE16278.pdf", "assemblee/QANR5L15QE16278.pdf", ["NRJ-06"], outil="curl"),
    Source("STROMSTG-3", "Bundesministerium der Justiz (gesetze-im-internet.de)", "Stromsteuergesetz § 3 : tarif de la taxe sur l'électricité", "A",
           "https://www.gesetze-im-internet.de/stromstg/__3.html", "allemagne/stromstg_3.html", ["NRJ-06"], outil="curl"),
    Source("STROMSTG-9B", "Bundesministerium der Justiz (gesetze-im-internet.de)", "Stromsteuergesetz § 9b : allègement pour l'industrie manufacturière", "A",
           "https://www.gesetze-im-internet.de/stromstg/__9b.html", "allemagne/stromstg_9b.html", ["NRJ-06"], outil="curl"),
    Source("CRE-CSPE-2026", "Commission de régulation de l'énergie", "Délibération n° 2025-180 du 10 juillet 2025 : charges de service public de l'énergie pour 2026", "A",
           CRE + "Deliberations/2025/250710_2025-180_CSPE_2025-2026.pdf", "cre/250710_2025-180_CSPE_2025-2026.pdf", ["NRJ-07"], licence=LO, outil="curl"),
    Source("CRE-CSPE-2026-ANNEXE1", "Commission de régulation de l'énergie", "Délibération n° 2025-180, annexe 1 : charges liées au soutien aux énergies renouvelables", "A",
           CRE + "Deliberations/2025/250710_2025-180_CSPE_2025-2026_Annexe_1.pdf", "cre/250710_2025-180_CSPE_2025-2026_Annexe_1.pdf", ["NRJ-07"], licence=LO, outil="curl"),
    Source("EIA-GAZ-SCHISTE-2013", "U.S. Energy Information Administration", "Technically Recoverable Shale Oil and Shale Gas Resources (2013), synthèse", "A",
           "https://www.eia.gov/analysis/studies/worldshalegas/pdf/overview.pdf", "eia/worldshalegas_overview.pdf", ["NRJ-08"], licence="domaine public (État fédéral américain)"),
    Source("EUROSTAT-GAZ", "Eurostat", "Consommation intérieure brute de gaz naturel, France (nrg_cb_gas, millions de m³)", "A",
           EUROSTAT + "nrg_cb_gas", "eurostat/nrg_cb_gas_fr.json", ["NRJ-08"], licence=CCBY,
           params={"geo": "FR", "nrg_bal": "IC_OBS", "siec": "G3000", "unit": "MIO_M3", "sinceTimePeriod": "2010"}),
    Source("AN-QE9713-DPE", "Assemblée nationale (réponse du gouvernement)", "Question écrite n° 9713 (XVIIe législature) : coefficient de l'électricité du DPE abaissé de 2,3 à 1,9", "A",
           "https://www.assemblee-nationale.fr/dyn/17/questions/QANR5L17QE9713.pdf", "assemblee/QANR5L17QE9713.pdf", ["NRJ-09"], outil="curl"),
    Source("PPE-2020", "Ministère de la Transition écologique", "Programmation pluriannuelle de l'énergie 2019-2023 / 2024-2028 (avril 2020)", "A",
           "https://www.ecologie.gouv.fr/sites/default/files/documents/20200422%20Programmation%20pluriannuelle%20de%20l%27e%CC%81nergie.pdf",
           "ppe/PPE_2020.pdf", ["NRJ-10"], licence=LO, outil="curl"),
    Source("CRE-CONSULTATION-SDDR", "Commission de régulation de l'énergie", "Consultation publique n° 2025-08 sur le schéma décennal de développement du réseau de RTE", "A",
           CRE + "Consultations_publiques/2025/250918_Consultation_2025-08_SDDR_RTE.pdf", "cre/250918_Consultation_2025-08_SDDR_RTE.pdf", ["NRJ-11"], licence=LO, outil="curl"),
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
