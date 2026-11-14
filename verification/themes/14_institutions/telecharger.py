"""Thème 14 — Institutions, référendum et normes : téléchargement des sources brutes.  python -m verification telecharger 14"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
AMF = "https://www.amf.asso.fr/inc/fichier.php"

SOURCES = [
    Source("AMF-CEVIPOF-DEMISSIONS-CP", "Observatoire de la démocratie de proximité AMF-Cevipof (Sciences Po), d'après le Répertoire national des élus",
           "Les démissions de maires : enquête sur un phénomène sans précédent, communiqué et principaux enseignements (juin 2025)", "B",
           AMF, "amf_cevipof/demissions_maires_communique.pdf", ["INS-01"], outil="curl",
           params={"FTP": "25142afcc8ee81b3670011d492076bca.pdf", "ID_DOC": "42676"},
           note="Étude publiée par l'AMF, que présidait David Lisnard : conflit d'intérêts à signaler ; données du ministère de l'Intérieur"),
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
