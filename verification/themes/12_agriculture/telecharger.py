"""Thème 12 — Agriculture : téléchargement des sources brutes.  python -m verification telecharger 12"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
COMEXT = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"
CHAPITRES = [f"{i:02d}" for i in range(1, 25)] + ["1604", "1605"]

SOURCES = [
    Source("TRESOR-COMMERCE-2025", "Ministère de l'Économie et ministère de l'Europe (Douanes / DSECE)", "Résultats du commerce extérieur en 2025 (6 février 2026)", "A",
           "https://www.tresor.economie.gouv.fr/Articles/c4e4f991-256d-4547-9835-70659a315ce5/files/58428a93-fb0f-4dae-a887-aac58cd554fa",
           "douanes/resultats_commerce_exterieur_2025.pdf", ["AGRI-01", "AGRI-03"], licence=LO, outil="curl"),
    Source("ACADEMIE-AGRI-COMMERCE", "Académie d'agriculture de France (T. Pouch, d'après Douanes et Agreste)", "Le commerce extérieur agroalimentaire français, fiche révisée en août 2026", "C",
           "https://academie-agriculture.fr/sites/default/files/publications/encyclopedie/commerce_exterieur_agroalimentaire.pdf",
           "academie/commerce_exterieur_agroalimentaire.pdf", ["AGRI-01"], outil="curl"),
    Source("COMEXT-AGROALIMENTAIRE", "Eurostat (Comext, données des Douanes)", "Commerce de la France, chapitres 01 à 24 du système harmonisé et positions 1604-1605 (ds-045409)", "A",
           COMEXT + "ds-045409", "eurostat/comext_fr_chapitres_01_24.json", ["AGRI-01", "AGRI-02", "AGRI-03"], licence=CCBY,
           params={"reporter": "FR", "partner": "WORLD", "product": CHAPITRES, "flow": ["1", "2"], "freq": "A", "indicators": "VALUE_IN_EUROS",
                   "time": [str(a) for a in range(2000, 2026)]}),
    Source("AN-QE102524-SUICIDE", "Assemblée nationale (réponse du ministère de l'Agriculture)", "Question écrite n° 102524 (XIVe législature) : surmortalité par suicide des exploitants agricoles", "A",
           "https://www.assemblee-nationale.fr/dyn/14/questions/QANR5L14QE102524.pdf", "assemblee/QANR5L14QE102524.pdf", ["AGRI-04"], outil="curl"),
    Source("AN-QE23624-SUICIDE-MSA", "Assemblée nationale (question citant l'étude de la MSA)", "Question écrite n° 23624 (XVe législature) : risque de suicide supérieur d'environ 12 % en 2015", "C",
           "https://www.assemblee-nationale.fr/dyn/15/questions/QANR5L15QE23624.pdf", "assemblee/QANR5L15QE23624.pdf", ["AGRI-04"], outil="curl",
           note="chiffre de la MSA rapporté par un député, pas par l'organisme lui-même"),
    Source("SPF-BEH-2018-SUICIDE", "Santé publique France (Bulletin épidémiologique hebdomadaire n° 27, 2018)", "Mortalité par suicide des salariés agricoles affiliés à la MSA ; rappel de l'étude sur les exploitants 2007-2011", "A",
           "https://beh.santepubliquefrance.fr/beh/2018/27/pdf/2018_27_2.pdf", "spf/BEH_2018_27_2.pdf", ["AGRI-04"], outil="curl"),
    Source("INSEE-PAUVRETE-EXPLOITANTS", "Insee et ministère de l'Agriculture (SSP), Insee Première", "Les exploitants agricoles vivent plus souvent sous le seuil de pauvreté que l'ensemble de la population (données 2020)", "A",
           "https://insee.fr/fr/statistiques/8376591", "insee/8376591.html", ["AGRI-05"], licence=LO),
    Source("EUROSTAT-REVENU-AGRICOLE", "Eurostat (comptes économiques de l'agriculture)", "Indicateurs de revenu agricole A, B et C, indices et variations annuelles (aact_eaa06)", "A",
           EUROSTAT + "aact_eaa06", "eurostat/aact_eaa06_fr.json", ["AGRI-06"], licence=CCBY, params={"geo": "FR", "unit": ["I20", "I_N_1", "CLV20_EUR_AWU"]}),
    Source("EUROSTAT-ENGRAIS", "Eurostat", "Consommation d'engrais minéraux, azote et phosphore (aei_fm_usefert)", "A",
           EUROSTAT + "aei_fm_usefert", "eurostat/aei_fm_usefert_fr.json", ["AGRI-07"], licence=CCBY, params={"geo": "FR"}),
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
