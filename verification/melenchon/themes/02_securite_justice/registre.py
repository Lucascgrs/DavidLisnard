"""Mélenchon, thème 2 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 2
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("02")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="SECU-01", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Selon l’Observatoire français des drogues et tendances addictives, 23,1 % des adultes fument "
                  "quotidiennement, 7 % boivent de l’alcool chaque jour, et le cannabis compte 900 000 usagers quotidiens.",
         grandeur_testee="Usages quotidiens de tabac, d'alcool et de cannabis (OFDT, chiffres clés 2025)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
