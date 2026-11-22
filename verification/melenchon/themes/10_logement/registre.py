"""Mélenchon, thème 10 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 10
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("10")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
BATIMENT = "prises-de-parole-melenchon:youtube:5-zstKCtO3k:3"
A = [
    dict(id="LOG-01", id_corpus=BATIMENT, priorite=1,
         citation="2 800 000 personnes qui sont en attente d'un logement social",
         autres_versions="« Près de 3 millions de ménages attendent l’attribution d’un logement public » (programme) ; "
                         "« Il y a 2,8 millions de gens qui attendent d'avoir un logement » (28/09/2026)",
         grandeur_testee="Demandes de logement social en attente (ministère du Logement)"),
    dict(id="LOG-02", id_corpus=BATIMENT, priorite=1,
         citation="350 000 personnes qui n'ont plus aucun logement d'aucune sorte et qui sont à la rue",
         grandeur_testee="Personnes sans domicile (Fondation pour le logement) et définition de l'Insee"),
    dict(id="LOG-03", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Produire 200 000 logements publics par an et 30 000 logements jeunes pendant 5 ans aux normes "
                  "écologiques les plus ambitieuses",
         grandeur_testee="Logements sociaux financés par l'État en 2024", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
