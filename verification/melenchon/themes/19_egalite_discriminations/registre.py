"""Mélenchon, thème 19 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 19
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("19")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="EGAL-01", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Les femmes gagnent en moyenne 22 % de moins que les hommes",
         autres_versions="la suite de la phrase, « et constituent 70 % des travailleurs pauvres », n'a pas été vérifiée",
         grandeur_testee="Écart de revenu salarial moyen entre femmes et hommes, secteur privé, 2024 (Insee)"),
    dict(id="EGAL-02", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Placé au cinquième rang des États européens pour les droits LGBTI en 2017, notre pays a dégringolé à "
                  "la quinzième place",
         grandeur_testee="Rang de la France dans la carte des droits LGBTI d'ILGA-Europe, 2017 et 2026"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
