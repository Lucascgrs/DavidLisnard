"""Mélenchon, thème 17 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 17
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("17")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="INEG-01", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Depuis 2017, un million de personnes ont basculé dans la pauvreté.",
         autres_versions="« Un million de personnes de plus dans la pauvreté » (Fête de l'Humanité, 12/09/2026)",
         grandeur_testee="Personnes sous le seuil de pauvreté à 60 %, 2017 → 2024 (Insee)"),
    dict(id="INEG-02", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="En tout, ce sont plus de 15 % des Français qui vivent sous le seuil de pauvreté : un record jamais "
                  "enregistré.",
         grandeur_testee="Taux de pauvreté à 60 %, 1975 → 2024 (Insee)"),
    dict(id="INEG-03", id_corpus="prises-de-parole-melenchon:instagram:DfhMmkLoQh7:1", priorite=2,
         citation="Quand il y a plus de 10 millions de pauvres, les perturbations économiques mondiales qui paraissent "
                  "éloignées deviennent vite des enjeux de survie quotidienne pour des millions de gens.",
         autres_versions="« On parle de 9 millions de gens qui sont dans la pauvreté » (18/10/2026)",
         grandeur_testee="Nombre de personnes pauvres en 2024 (Insee)"),
    dict(id="INEG-04", id_corpus="prises-de-parole-melenchon:youtube:80bBtk2lTiI:9", priorite=2,
         citation="Un million de personnes de plus dans la pauvreté, 8 millions de personnes à l'aide alimentaire",
         grandeur_testee="Bénéficiaires de l'aide alimentaire sur une année (Insee)"),
    dict(id="INEG-05", id_corpus=PROG, date="2026", support=AEC, priorite=3,
         citation="4 millions d’entre eux ne parviennent pas à se chauffer correctement",
         grandeur_testee="Personnes ne pouvant pas chauffer convenablement leur logement (Eurostat, enquête SRCV)"),
    dict(id="INEG-06", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="un salarié au SMIC gagne à peine plus que le seuil de pauvreté.",
         grandeur_testee="SMIC net à temps plein et seuil de pauvreté d'une personne seule, 2024"),
    dict(id="INEG-07", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Créer une garantie d’autonomie, qui permettra que nul ne soit privé de sa dignité pour vivre : le "
                  "revenu mensuel de chaque personne atteindra le seuil de pauvreté (1 337 euros pour une personne seule)",
         grandeur_testee="Seuil de pauvreté à 60 % en 2024 (Insee)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
