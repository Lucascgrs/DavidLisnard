"""Mélenchon, thème 4 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 4
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("04")
MEDEF = "prises-de-parole-melenchon:youtube:KClFp_-Wh-w:42"
A = [
    dict(id="ETAT-01", id_corpus=MEDEF, priorite=1,
         citation="Le salaire des fonctionnaires a reculé de 6 points dans le PIB.",
         grandeur_testee="Rémunération des salariés des administrations publiques et de l'État, % du PIB, 2004 → 2024"),
    dict(id="ETAT-02", id_corpus=MEDEF, priorite=1,
         citation="La dépense de l'État de 7 points en 20 ans. Donc il faut cesser de dire que l'État jetterait "
                  "l'argent par les fenêtres.",
         grandeur_testee="Dépense totale de l'État et des administrations publiques, % du PIB, 2004 → 2024"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
