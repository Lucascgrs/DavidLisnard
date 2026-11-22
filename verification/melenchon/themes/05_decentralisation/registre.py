"""Mélenchon, thème 5 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 5
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("05")
A = [
    dict(id="DEC-01", id_corpus="prises-de-parole-melenchon:youtube:KClFp_-Wh-w:140", priorite=2,
         citation="80% des maires ont la soixantaine et plus et sont partis en retraite.",
         grandeur_testee="Âge et catégorie socioprofessionnelle des maires (répertoire national des élus, novembre 2026)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
