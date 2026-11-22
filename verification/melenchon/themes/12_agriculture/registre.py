"""Mélenchon, thème 12 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 12
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("12")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="AGRI-01", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Instaurer une agriculture relocalisée, diversifiée et écologique et créer 500 000 emplois agricoles",
         grandeur_testee="Emploi dans l'agriculture, la sylviculture et la pêche, 2000-2025 (Eurostat)",
         verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
