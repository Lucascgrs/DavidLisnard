"""Mélenchon, thème 8 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 8
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("08")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="ECOLE-01", id_corpus="prises-de-parole-melenchon:youtube:KClFp_-Wh-w:143", priorite=1,
         citation="La jeunesse de notre pays, peu de gens ont l'air de le savoir, 50% d'une classe d'âge passe dans "
                  "l'enseignement technologique, dans l'enseignement professionnel et dans l'apprentissage.",
         autres_versions="« savez-vous combien il y a de jeunes gens, dans une génération, qui est dans l'enseignement "
                         "professionnel, l'apprentissage ou la filière technologique. 50% ! » (28/10/2026) ; répété le "
                         "12/11/2026",
         grandeur_testee="Proportion de bacheliers dans une génération selon la voie, 2025 (DEPP)"),
    dict(id="ECOLE-02", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Les difficultés de lecture touchent un adulte sur dix, les empêchant d’être autonomes dans la vie "
                  "quotidienne. C’est près de 4 millions de personnes dans l’Hexagone : un tiers vit dans les espaces "
                  "ruraux et six sur dix sont des femmes.",
         grandeur_testee="Adultes en situation d'illettrisme et en difficulté à l'écrit, selon le sexe (Insee, 2011)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
