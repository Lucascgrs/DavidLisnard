"""Mélenchon, thème 15 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 15
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("15")
A = [
    dict(id="CULT-01", id_corpus="prises-de-parole-melenchon:youtube:VRToI5PbTNE:5", priorite=2,
         citation="avec un million d'objets de plus de 10 cm et 128 millions d'objets de moins d'un centimètre, la "
                  "première couche proche de la Terre est déjà en état de quasi-saturation.",
         autres_versions="« on en est à 128 millions d'objets de moins d'un millimètre, et à 10 millions d'objets de plus "
                         "de 10 centimètres » (même jour, autre vidéo)",
         grandeur_testee="Objets en orbite par taille selon le modèle MASTER de l'Agence spatiale européenne (2026)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
