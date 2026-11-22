"""Mélenchon, thème 9 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 9
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("09")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="RET-01", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Abroger la réforme Macron passant l’âge de départ à la retraite à 64 ans, puis abaisser l’âge de "
                  "départ jusqu’à restaurer le droit à la retraite à 60 ans à taux plein pour 40 annuités de cotisations",
         autres_versions="« nous abrogerons la retraite Et nous reviendrons dans un premier temps à 62 ans. Et mon but "
                         "est d'arriver le plus vite possible, retourner à 60 ans » (débat du Medef, 27/08/2026)",
         grandeur_testee="Âge légal de départ et trimestres exigés pour le taux plein aujourd'hui (service-public.fr)",
         verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
