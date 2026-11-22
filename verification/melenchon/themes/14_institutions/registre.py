"""Mélenchon, thème 14 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 14
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("14")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="INST-01", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Depuis 2017, le « 49.3 » a été utilisé à 32 reprises, au mépris de la volonté populaire.",
         grandeur_testee="Engagements de responsabilité sur un texte (article 49, alinéa 3) depuis 2017"),
    dict(id="INST-02", id_corpus="prises-de-parole-melenchon:youtube:R7t9n_z35to:19", priorite=2,
         citation="Le peuple français a voté à 55% non.",
         autres_versions="« Le peuple français a voté non à 55% » (Fête de l'Humanité, 12/09/2026)",
         grandeur_testee="Résultat du référendum du 29 mai 2005 (ministère de l'Intérieur)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
