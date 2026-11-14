"""Affirmations du thème 5 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 5"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Décentralisation et collectivités"
A = [
    dict(id="DEC-01", id_corpus="7fb92e900b9f2b78", priorite=1,
         citation="Depuis 2014, l’État a prélevé plus de 80 milliards d’euros sur la DGF (dotation globale de fonctionnement) des communes et intercommunalités.",
         autres_versions="« C'est 47 milliards qui ont été piochés dans les recettes des collectivités depuis 2014 » (19/10/2022) ; « 71 milliards d'euros de prélèvements de l'État sur la seule DGF […] depuis 2010 » (21/11/2024) ; « 81 milliards de prélèvements » (17/11/2025) ; « 82 milliards d'euros de dotation prélevés depuis 2010 » (04/02/2026)",
         grandeur_testee="Cumul des baisses de DGF du bloc communal depuis 2014 (contribution au redressement des finances publiques)"),
    dict(id="DEC-02", id_corpus="5eda774950e0d12c", priorite=1,
         citation="Par rapport à la richesse nationale, la dette de toutes les collectivités françaises représente aujourd’hui 8,9 % du PIB.",
         autres_versions="« Non seulement 91 % de la dette publique est du fait de l’État et de la Sécu » (même tribune) ; « la dette du millefeuille territorial représente 8,8 % de la richesse française, contre 9 % il y a trente ans » (13/08/2026) ; « 9 % du PIB, un niveau stable depuis 35 ans » (04/02/2026) ; « les collectivités portent 8 % de la dette publique contre 92 % » (FAQ, 2026)",
         grandeur_testee="Dette des administrations publiques locales (Maastricht), en % du PIB et de la dette publique"),
    dict(id="DEC-03", id_corpus="5eda774950e0d12c", priorite=1,
         citation="le total des dépenses des services publics décentralisés (les dépenses des collectivités) est de 11 % de la richesse produite, contre une moyenne européenne de presque 20 %.",
         autres_versions="« Si le total des dépenses des administrations publiques locales en France représente 19 % […] la moyenne européenne, elle, est de 34 % » (même tribune) ; « 19 % de la dépense publique relèvent des collectivités locales (34 % en Europe) » (23/04/2025) ; « 19 % de la dépense publique, contre 35 % en moyenne en Europe, et moins de 11 % du PIB, contre 18 % chez nos voisins » (13/08/2026)",
         grandeur_testee="Dépense des administrations locales (et des États fédérés) en % du PIB et de la dépense publique, UE"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
