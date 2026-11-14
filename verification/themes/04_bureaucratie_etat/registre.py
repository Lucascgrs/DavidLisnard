"""Affirmations du thème 4 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 4"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Bureaucratie, normes et réforme de l'État"
A = [
    dict(id="BUR-01", id_corpus="8ca17e14d81e76af", priorite=1,
         citation="On recense 1 153 organismes publics, pour 100 milliards d’euros de fonctionnement et 500 000 recrutements supplémentaires.",
         autres_versions="« Nous supprimerons donc la moitié des 418 agences de l’État, qui ont recruté 410 000 personnes depuis 15 ans et qui dépensent 85 milliards d’euros par an » (24/01/2025) ; « 1200 opérateurs-agences qui ont recruté 420 000 fonctionnaires, qui dépensent 83 milliards, on pense même que c'est 100 milliards » (29/11/2025) ; « 1153 organismes d’Etat créés ces dernières décennies […] qui comptent plus de 500 000 agents, coûtent 100 milliards » (03/07/2026)",
         grandeur_testee="Nombre d'organismes, emplois et financements publics des opérateurs (Sénat 2025, jaune budgétaire)"),
    dict(id="BUR-02", id_corpus="9f151c835be7146c", priorite=2,
         citation="L’excès de bureaucratie capte les ressources : 34 % des agents sont en fonction « administrante », contre 24 % en Allemagne.",
         autres_versions="« un taux d’emplois délégués aux tâches administratives de 33 % en France dans la fonction publique contre 25 % dans un pays comme l’Allemagne et de 24 % en moyenne en Europe » (09/06/2022) ; « 34/35% de fonction administrante » (27/09/2024)",
         grandeur_testee="Part des emplois publics consacrés à des tâches administratives (aucune nomenclature standard)", verifiable="non"),
    dict(id="BUR-03", id_corpus="fa7566d963750530", priorite=2,
         citation="on a 21 % d'emplois public en France l'Allemagne c'est 11",
         grandeur_testee="Emploi des administrations publiques en % de l'emploi total (OCDE)"),
    dict(id="BUR-04", id_corpus="05c4eae6873ce899", priorite=3,
         citation="le poids écrasant des normes dans notre pays et leur fréquente contradiction qui nous coûtent 3 points de PIB",
         autres_versions="« la bureaucratie coûte près de 3 points de PIB » (05/2026)",
         grandeur_testee="Coût des normes et charges administratives en % du PIB", verifiable="partiellement"),
    dict(id="BUR-05", id_corpus="1cd9653671ac54bb", priorite=3,
         citation="Depuis 2002, le nombre de mots du Code de l’environnement a bondi de 946 %",
         autres_versions="« Selon le Secrétariat général du Gouvernement, le droit français compte aujourd’hui 47,6 millions de mots » (même document) ; « le Code de l’environnement est ainsi passé de près de 100 000 à 1 million de mots en vingt ans » (18/01/2023) ; « 1700 décrets […] 88 codes » (06/01/2021)",
         grandeur_testee="Taille des codes (indicateurs de l'activité normative du SGG)", verifiable="partiellement"),
    dict(id="BUR-06", type="mesure", id_corpus="0a305de8b1f03d07", priorite=1,
         citation="On doit baisser la dépense publique dès la première année d'un Canada de 80 milliards d'euros en taillant dans les 1200 entités publiques",
         autres_versions="« supprimer la moitié des 418 agences de l’État » (24/01/2025) ; « dès la première année, on peut réduire de au moins 8 milliards, c'est l'hypothèse basse, le budget de fonctionnement de ces agences » (BFMTV, 04/11/2026)",
         grandeur_testee="Économies possibles sur les agences (Sénat 2025)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
