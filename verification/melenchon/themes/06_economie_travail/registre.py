"""Mélenchon, thème 6 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 6
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("06")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
MEDEF = "prises-de-parole-melenchon:youtube:KClFp_-Wh-w:"
A = [
    dict(id="ECO-01", id_corpus="prises-de-parole-melenchon:instagram:Dfoo_aBtqS3:1", priorite=1,
         citation="Juste pour que vous sachiez, comparé avec les voisins, sur les 10 dernières années, en France le SMIC "
                  "il a augmenté de 27%. […] le SMIC, dans les mêmes dix années, a augmenté de 86,5 en Espagne.",
         autres_versions="« Le Portugal, autrefois c'était les fauchés de la bande. 73% en 10 ans d'augmentation de leur "
                         "salaire minimum. 62% en Allemagne » ; « 52% d'augmentation aux Pays-Bas, 45% en Belgique » "
                         "(même intervention)",
         grandeur_testee="Salaire minimum mensuel brut, 1er semestre 2016 → 1er semestre 2026 (Eurostat)"),
    dict(id="ECO-02", id_corpus="prises-de-parole-melenchon:instagram:Dfoo_aBtqS3:1", priorite=2,
         citation="Et eux, là-bas, ils ont fait 86,5 et ils font le plus fort taux de croissance de toute l'Europe, 3,8.",
         grandeur_testee="Croissance du PIB en volume, pays de l'UE, 2024 et 2025 (Eurostat)"),
    dict(id="ECO-03", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="pour 1 offre d’emploi vacant, on compte 17 chômeurs dans notre pays !",
         grandeur_testee="Chômeurs au sens du BIT et emplois vacants (Eurostat, Insee, Dares)"),
    dict(id="ECO-04", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="87 % des embauches ont lieu en contrats courts.",
         grandeur_testee="Déclarations préalables à l'embauche par nature de contrat (Urssaf)"),
    dict(id="ECO-05", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="les deux quinquennats Macron ont aggravé ce phénomène : la production industrielle n’a toujours pas "
                  "retrouvé son niveau d’avant Covid-19.",
         grandeur_testee="Indice de la production industrielle, 2019 → 2025 (Eurostat)"),
    dict(id="ECO-06", id_corpus=MEDEF + "137", priorite=3,
         citation="nous sommes classés dans les pays, par la Banque mondiale, dans les 15% de pays où c'est le plus "
                  "facile de faire des affaires.",
         grandeur_testee="Rang de la France au classement Doing Business (dernière édition, 2020)"),
    dict(id="ECO-07", id_corpus=MEDEF + "315", priorite=1,
         citation="Comment faisons-nous pour être le pays record d'Europe des morts au travail ?",
         autres_versions="« La France détient le record européen des morts du travail » (programme) ; « on est le pays "
                         "record d'Europe pour les accidents du travail » (12/11/2026)",
         grandeur_testee="Accidents du travail mortels, nombre et taux pour 100 000 travailleurs, pays de l'UE (Eurostat)"),
    dict(id="ECO-08", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Chaque année, on déplore 1 000 décès : accidentés sur des sites dangereux ou par négligence des "
                  "donneurs d’ordres, travailleurs atteints de maladies professionnelles incurables, poussés au "
                  "suicide face à des situations insupportables.",
         grandeur_testee="Décès reconnus par la branche accidents du travail et maladies professionnelles (2024)"),
    dict(id="ECO-09", id_corpus="prises-de-parole-melenchon:youtube:80bBtk2lTiI:12", priorite=1,
         citation="Eh bien, les prix ont augmenté pour les aliments de plus de 30%. J'ai dit 30%, pas 3%.",
         grandeur_testee="Indice des prix de l'alimentation (IPCH), depuis 2021 et depuis 2017"),
    dict(id="ECO-10", id_corpus=MEDEF + "224", priorite=3,
         citation="Et dans ce pays, les salaires et la consommation populaire, la consommation populaire, c'est 55% du "
                  "PIB.",
         autres_versions="« 55% du PIB de ce pays, c'est ça, c'est de la consommation populaire » (16/09/2026)",
         grandeur_testee="Consommation des ménages et rémunération des salariés en % du PIB (Eurostat)"),
    dict(id="ECO-11", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=3,
         citation="Planifier le rattrapage de la France en matière de robotisation de l’industrie pour revenir à hauteur "
                  "avec l’Allemagne, soit 400 robots pour 10 000 salariés",
         grandeur_testee="Densité de robots industriels (IFR)", verifiable="partiellement"),
    dict(id="ECO-12", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Augmenter immédiatement le SMIC à 1 700 € net mensuel et les minima sociaux",
         grandeur_testee="SMIC mensuel brut en 2026 et hausse impliquée", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
