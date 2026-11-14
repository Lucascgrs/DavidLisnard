"""Thème 16 — Cannes, bilan municipal : téléchargement des sources brutes.  python -m verification telecharger 16"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
ECO = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
LO = "Licence ouverte Etalab 2.0"
CANNES = {"where": 'dep="006" and icom="029"', "limit": "20"}
MILLESIMES = ["2008", "20090", "2010", "2011-2015", "2016", "2017", "2018", "2019-2020", "2021", "2022", "2023-2024", "2025"]

SOURCES = [
    Source(f"DGFIP-COMPTES-CANNES-{m}", "Direction générale des finances publiques (data.economie.gouv.fr)",
           f"Comptes individuels des communes, fichier global {m} : ligne de Cannes (budget principal, en milliers d'euros)", "A",
           ECO + f"comptes-individuels-des-communes-fichier-global-{m}/records", f"dgfip/comptes_cannes_{m}.json",
           ["CAN-01", "CAN-02", "CAN-03", "CAN-04", "CAN-06"], licence=LO, params=CANNES)
    for m in MILLESIMES
] + [
    Source("INSEE-FILOSOFI-2021", "Insee (Filosofi 2021, géographie 2024)", "Revenus, pauvreté et niveau de vie en 2021 : bases communales et France métropolitaine", "A",
           "https://www.insee.fr/fr/statistiques/fichier/7756729/base-cc-filosofi-2021-geo2024_csv.zip", "insee/base-cc-filosofi-2021-geo2024_csv.zip",
           ["CAN-05"], licence=LO, outil="curl"),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:34} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
