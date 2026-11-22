"""Mélenchon, thème 3 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 3
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("03")
A = [
    dict(id="IMMI-01", id_corpus="prises-de-parole-melenchon:youtube:R7t9n_z35to:77", priorite=2,
         citation="Parce que maintenant, c'est seulement quand tu as 18 ans, ou bien si tu as demandé à 16 ans, alors "
                  "toi tu peux être français mais pas ton frère, ou pas ta soeur.",
         grandeur_testee="Règles d'accès à la nationalité des enfants nés en France de parents étrangers"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
