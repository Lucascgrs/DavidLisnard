"""Affirmations du thème 16 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 16"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Cannes : bilan municipal"
A = [
    dict(id="CAN-01", id_corpus="7bb8eb15b36fdea8", priorite=1,
         citation="nous tablons sur a minima encore -1 M€ en 2025, pour un total de baisse de la dette communale de -77,5 M€ depuis 2014",
         autres_versions="« En 10 ans, la Mairie de Cannes a baissé la dette chaque année, pour un total de -71,5M€ » (24/10/2024) ; « un désendettement record (-77,5 M€ depuis 2014) » (21/08/2025)",
         grandeur_testee="Encours de la dette du budget principal de Cannes au 31 décembre (DGFiP)"),
    dict(id="CAN-02", id_corpus="ef666f9ce0ecedd3", priorite=1,
         citation="une multiplication par dix de la capacité d’autofinancement (55,92 M€ en 2024 contre 5,48 M€ en 2014).",
         grandeur_testee="Capacité d'autofinancement nette du budget principal (DGFiP)"),
    dict(id="CAN-03", id_corpus="ef666f9ce0ecedd3", priorite=1,
         citation="une stabilité des taux communaux d’impôts locaux pendant 11 ans, assortie d’abattements protecteurs et même d’une baisse de -3,6 % en 2025",
         autres_versions="« Les impôts n'ont jamais été augmentés » (24/10/2024)",
         grandeur_testee="Taux communaux de taxe foncière et de taxe d'habitation (DGFiP)"),
    dict(id="CAN-04", id_corpus="58d49e5ca43698f1", priorite=2,
         citation="Ce qui a permis de diminuer les dépenses de fonctionnement (-65,9 millions€ depuis 2014) et de baisser la dette (-71,5 millions€ depuis 2014).",
         grandeur_testee="Charges de fonctionnement du budget principal (DGFiP)"),
    dict(id="CAN-05", id_corpus="026251ce51ef0b11", priorite=2,
         citation="Dans une ville contrastée, au taux de pauvreté (21%) supérieur à la moyenne nationale (14%)",
         grandeur_testee="Taux de pauvreté à 60 % du niveau de vie médian (Insee, Filosofi 2021)"),
    dict(id="CAN-06", id_corpus="dc4fe2444d772ffa", priorite=2,
         citation="les ponctions de l’Etat sur les finances de la Ville de Cannes qui s’élèvent à 139 millions d’euros depuis 2014 !",
         grandeur_testee="Baisse cumulée de la dotation globale de fonctionnement de Cannes (DGFiP)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
