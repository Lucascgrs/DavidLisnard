"""Affirmations du thème 12 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 12"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Agriculture"
A = [
    dict(id="AGRI-01", id_corpus="6e2b70813bb3145e", priorite=1,
         citation="Pour la première fois depuis 1978, nous sommes déficitaires sur le plan de l'agroalimentaire.",
         grandeur_testee="Solde du commerce extérieur agricole et agroalimentaire (Douanes, Eurostat Comext)"),
    dict(id="AGRI-02", id_corpus="73386076fa8c892d", priorite=2,
         citation="La France importe plus du double de denrées alimentaires aujourd’hui qu’en l’an 2000, soit 63 milliards d’euros.",
         grandeur_testee="Importations agricoles et alimentaires, 2000 et 2022 (Eurostat Comext)"),
    dict(id="AGRI-03", id_corpus="208e6d529faaec48", priorite=1,
         citation="L’excédent agroalimentaire atteignait 10,4 milliards d’euros en 2022. Il est tombé à 4,9 milliards en 2024, puis à 200 millions en 2025,aux portes du déficit ! Les importations agroalimentaires ont bondi à plus de 64 milliards, en hausse de 8,5 % sur un an.",
         grandeur_testee="Solde et importations agroalimentaires 2022-2025 (Douanes, Eurostat Comext)"),
    dict(id="AGRI-04", id_corpus="292ede70b5681372", priorite=1,
         citation="Juste, il y a 7 fois plus de suicides chez les agriculteurs que la moyenne des Français.",
         grandeur_testee="Surmortalité par suicide des agriculteurs (MSA, Santé publique France)"),
    dict(id="AGRI-05", id_corpus="292ede70b5681372", priorite=1,
         citation="On a presque 40% des agriculteurs qui sont en dessous du seuil de pauvreté.",
         autres_versions="« Un agriculteur sur quatre vit sous le seuil de pauvreté » (27/02/2026 et 03/09/2026)",
         grandeur_testee="Taux de pauvreté monétaire des exploitants agricoles (Insee, SSP)"),
    dict(id="AGRI-06", id_corpus="97dd60a6f16c95e8", priorite=2,
         citation="En trente ans, le revenu net agricole a diminué de 40 %.",
         autres_versions="« En trente ans, le revenu net agricole a fondu de 40 % » (27/02/2026)",
         grandeur_testee="Revenu net d'entreprise agricole en termes réels (Eurostat, comptes de l'agriculture)"),
    dict(id="AGRI-07", id_corpus="e36276f5cf8a341e", date="2026-01-06", priorite=2,
         citation="La France consomme environ 2,2 millions de tonnes d’engrais azotés par an, importées à 80–90 %.",
         autres_versions="« Nous importons 100 % de nos engrais potassiques et 70 % des azotés » (27/02/2026)",
         grandeur_testee="Consommation d'engrais azotés (Eurostat) ; part importée"),
    dict(id="AGRI-08", id_corpus="292ede70b5681372", priorite=3,
         citation="Aujourd'hui, les cotisations sociales, par exemple, sur les exploitations agricoles, c'est 45% du revenu des agriculteurs.",
         autres_versions="« En Allemagne, c'est 30%. En Espagne, c'est 25% » (même entretien) ; « 45 % de charges (15 % en Espagne) » (X, 24/02/2026)",
         grandeur_testee="Cotisations sociales des exploitants rapportées à leur revenu", verifiable="partiellement"),
    dict(id="AGRI-09", type="mesure", id_corpus="97dd60a6f16c95e8", priorite=3,
         citation="Supprimer les impôts de production qui pénalisent l’agriculture française",
         grandeur_testee="Mesure", verifiable="non"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
