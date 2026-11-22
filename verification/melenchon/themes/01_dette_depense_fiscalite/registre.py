"""Mélenchon, thème 1 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 1
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("01")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
YT = "prises-de-parole-melenchon:youtube:"
A = [
    dict(id="DETTE-01", id_corpus=YT + "80bBtk2lTiI:41", priorite=1,
         citation="le budget de l'État doit être débarrassé de la charge des aides sans contrepartie au capital dont le "
                  "sénateur communiste Fabien Gué, directeur de l'Humanité, a chiffré le prélèvement à 210 milliards. "
                  "[…] celui qui a été fixé par le président membre de Les Républicains, qui lui a dit « Ah non, non, "
                  "non, il n'y en a que pour 120 milliards ».",
         autres_versions="« Monsieur Fabien Guay a parlé de 210 milliards d'aides. Le président de cette commission, qui "
                         "est Les Républicains […] lui parle de 120 milliards » (débat du Medef, 27/08/2026) ; « 20 "
                         "milliards, c'est 10% de ce qu'on donne aux entreprises » (12/11/2026)",
         grandeur_testee="Aides publiques aux entreprises en 2023 selon la commission d'enquête du Sénat"),
    dict(id="DETTE-02", id_corpus=YT + "KClFp_-Wh-w:43", priorite=1,
         citation="Le déficit de l'Etat est de 150 milliards. Si je décide instantanément de céder, de cesser les aides "
                  "aux entreprises, il n'y a plus de déficit de l'Etat.",
         grandeur_testee="Déficit de l'État et des administrations publiques, 2024 et 2025 (Eurostat)"),
    dict(id="DETTE-03", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Le patrimoine de l’État est pourtant supérieur à sa dette : en France, chaque enfant naît avec plus "
                  "de 10 000 euros d’actif public !",
         grandeur_testee="Patrimoine net des administrations publiques et de l'État, par habitant (Eurostat)"),
    dict(id="DETTE-04", id_corpus=YT + "2QZwlpyS3qk:60", priorite=2,
         citation="Il y a 5 pays qui sont au-delà de 100% d'endettement par rapport au PIB, et ces 5 pays représentent "
                  "50% du PIB de l'Europe.",
         grandeur_testee="Pays de l'UE dont la dette dépasse 100 % du PIB en 2025, et leur poids (Eurostat)"),
    dict(id="DETTE-05", id_corpus=YT + "80bBtk2lTiI:55", priorite=3,
         citation="Malheureuse Grèce qui avait à l'époque un déficit égal à 110% du PIB de l'époque.",
         autres_versions="« aujourd'hui, la Grèce […] doit à une dette égale à plus de 130% de son PIB » (même discours)",
         grandeur_testee="Dette et déficit de la Grèce en % du PIB, 2007-2025 (Eurostat)"),
    dict(id="DETTE-06", id_corpus=YT + "KClFp_-Wh-w:352", priorite=3,
         citation="Aujourd'hui, le taux moyen, je me marre quand j'entends des déclarations sur les taux confiscatoires, "
                  "c'est 25% la loi.",
         grandeur_testee="Taux normal de l'impôt sur les sociétés et contribution exceptionnelle"),
    dict(id="DETTE-07", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Rendre l’impôt sur le revenu plus progressif avec un barème à 14 tranches contre 5 aujourd’hui",
         grandeur_testee="Nombre de tranches du barème de l'impôt sur le revenu", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
