"""Proximité des candidats : chaque mesure des programmes publiés pour la présidentielle 2027, rangée dans un
sous-thème de l'un des trois axes, et notée de -3 à +3 ; les candidats sont ensuite placés dans l'espace des trois
axes et comparés entre eux (« python -m proximite », voir docs/GRILLE_PROXIMITE.md).

Le code est ici ; les données dans donnees/proximite/ (suivies dans git : ce sont des programmes publics).
"""
from pathlib import Path

from commun.config import DONNEES as DONNEES_PROJET

RACINE = Path(__file__).resolve().parent           # le code : proximite/
DONNEES = DONNEES_PROJET / "proximite"
CANDIDATS = DONNEES / "candidats.json"             # la liste des candidats et de leurs programmes (candidats2027.org)
DOCUMENTS = DONNEES / "documents.csv"              # chaque document téléchargé, son empreinte, s'il a été lu
BRUT = DONNEES / "brut"                            # PDF et pages HTML tels que téléchargés (hors git)
TEXTES = DONNEES / "textes"                        # leur texte, un fichier par document
MESURES = DONNEES / "mesures"                      # les mesures relevées et notées, un CSV par candidat
POSITIONS = DONNEES / "positions.json"             # notes par sous-thème et par axe, coordonnées, distances
SITE = RACINE / "site"
