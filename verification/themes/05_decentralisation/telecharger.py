"""Thème 5 — Décentralisation et collectivités : téléchargement des sources brutes.  python -m verification telecharger 5"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
OFGL = "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets/"
CCBY, LO, PARL = "CC BY 4.0", "Licence ouverte Etalab 2.0", "Documents parlementaires, réutilisation libre"
DGF = {"select": "exer,sum(montant) as total", "where": "agregat='Dotation globale de fonctionnement'", "group_by": "exer", "limit": "100"}

SOURCES = [
    Source("AN-QE-50991", "Assemblée nationale (réponse du ministère à la question écrite n° 50991, 14e législature)",
           "Contribution des communes et des intercommunalités au redressement des finances publiques, 2014-2016", "A",
           "https://questions.assemblee-nationale.fr/dyn/14/questions/QANR5L14QE50991.pdf", "assemblee/QE50991_contribution_2014_2016.pdf",
           ["DEC-01"], licence=PARL),
    Source("AN-QE-95791", "Assemblée nationale (réponse du ministère à la question écrite n° 95791, 14e législature)",
           "Contribution du bloc communal au redressement des finances publiques, 2015-2017", "A",
           "https://questions.assemblee-nationale.fr/dyn/14/questions/QANR5L14QE95791.pdf", "assemblee/QE95791_contribution_2017.pdf",
           ["DEC-01"], licence=PARL),
    Source("OFGL-DGF-COMMUNES", "Observatoire des finances et de la gestion publique locales (OFGL)",
           "Dotation globale de fonctionnement perçue par les communes, par année (somme des comptes, 2018-2025)", "A",
           OFGL + "ofgl-base-communes/records", "ofgl/dgf_communes_par_annee.json", ["DEC-01"], licence=LO, params=DGF),
    Source("OFGL-DGF-GFP", "Observatoire des finances et de la gestion publique locales (OFGL)",
           "Dotation globale de fonctionnement perçue par les intercommunalités à fiscalité propre, par année (2018-2025)", "A",
           OFGL + "ofgl-base-gfp/records", "ofgl/dgf_intercommunalites_par_annee.json", ["DEC-01"], licence=LO, params=DGF),
    Source("EUROSTAT-DETTE-SECTEURS", "Eurostat", "Dette publique par sous-secteur (gov_10dd_edpt1)", "A", EUROSTAT + "gov_10dd_edpt1",
           "eurostat/gov_10dd_edpt1_secteurs.json", ["DEC-02"], licence=CCBY,
           params={"na_item": "GD", "unit": ["PC_GDP", "MIO_EUR"], "sector": ["S13", "S1311", "S1312", "S1313", "S1314"],
                   "sinceTimePeriod": "1995"}),
    Source("EUROSTAT-DEPENSES-SECTEURS", "Eurostat", "Dépenses publiques par sous-secteur (gov_10a_main, TE)", "A", EUROSTAT + "gov_10a_main",
           "eurostat/gov_10a_main_secteurs.json", ["DEC-03"], licence=CCBY,
           params={"na_item": "TE", "unit": ["PC_GDP", "MIO_EUR"], "sector": ["S13", "S1311", "S1312", "S1313", "S1314"],
                   "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-DETTE-LOCALE-TRIM", "Eurostat", "Dette publique trimestrielle par sous-secteur, France (gov_10q_ggdebt)", "A",
           EUROSTAT + "gov_10q_ggdebt", "eurostat/gov_10q_ggdebt_fr_secteurs.json", ["DEC-02"], licence=CCBY,
           params={"geo": "FR", "na_item": "GD", "unit": ["PC_GDP", "MIO_EUR"], "sector": ["S13", "S1313"], "sinceTimePeriod": "2000-Q1"}),
    Source("EUROSTAT-INFLATION", "Eurostat", "Indice des prix à la consommation harmonisé, France, moyenne annuelle (prc_hicp_aind)", "A",
           EUROSTAT + "prc_hicp_aind", "eurostat/prc_hicp_aind_fr.json", ["DEC-01"], licence=CCBY,
           params={"geo": "FR", "coicop": "CP00", "unit": "INX_A_AVG", "sinceTimePeriod": "2010"}),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:28} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
