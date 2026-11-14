"""Affirmations du thème 2 (citations relevées dans le corpus) → affirmations.csv.  python <ce fichier>"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Sécurité, justice et narcotrafic"
A = [
    dict(id="SECU-01", id_corpus="8de9e3ea7edd829f", priorite=1,
         citation="Derrière les chiffres de la délinquance et de la criminalité qui explosent ces dernières années (+ 51 % de coups et blessures volontaires et + 15 % d’homicides depuis 2017)",
         autres_versions="« augmentation de 12 % des homicides depuis 2017, de 11 % des viols et de 32 % des coups et blessures volontaires » (21/07/2022) ; « En seulement 6 ans, les violences volontaires ont augmenté de 63% » (X, 01/2024) ; « depuis 2017, coups et blessures en hausse de 51 %, homicides en hausse de 16 %, tentatives d’homicides en hausse de 90% » (programme) ; « Les coups et blessures volontaires ont bondi de 50% en dix ans. Le nombre d’homicides a augmenté de 43% » (Saint-Raphaël, 03/07/2026)",
         grandeur_testee="Faits de violences physiques et homicides enregistrés par la police et la gendarmerie (SSMSI)"),
    dict(id="SECU-02", id_corpus="2abdd148d9963bfb", date="2023-08-18", priorite=1,
         citation="Avec ce paradoxe d’une surpopulation carcérale et d’un sous-taux d’incarcération par rapport aux autres pays, conséquence du manque de 20 000 places.",
         autres_versions="« Il nous manque 20 000 places de prison depuis 15 ans » (30/03/2025) ; « augmenter la capacité carcérale d’au moins 30 000 places » (06/10/2025) ; « nous n’avons pas les 30 000 places de prison nécessaires » (24/07/2026)",
         grandeur_testee="Détenus moins places opérationnelles (DAP) ; taux de détention pour 100 000 habitants comparé à l'Europe (SPACE I)"),
    dict(id="SECU-03", id_corpus="0d687f1de32dbc4d", priorite=1,
         citation="Que la justice a adapté sa doctrine à sa pénurie de moyens : il avance que 40 % des peines d’emprisonnement ne sont pas exécutées au bout de six mois.",
         autres_versions="« 45 % des peines de prison ne sont toujours pas exécutées six mois après avoir été prononcées » (tribune, 08/03/2021) ; « une condamnation sur deux n'est pas appliquée parce qu'on manque d'équipement » (Grand Angle, 30/03/2025)",
         grandeur_testee="Taux de mise à exécution des peines d'emprisonnement ferme (SDSE, IGJ)"),
    dict(id="SECU-04", id_corpus="9bd690b50b94ed7b", priorite=2,
         citation="Le budget de la justice est de loin le plus faible d’Europe (0,20% du PIB) ainsi que par le nombre des juges (10,9 pour 100 000 habitants, la médiane étant de 17,7) et procureurs.",
         grandeur_testee="Juges et procureurs pour 100 000 habitants, budget de la justice (CEPEJ)"),
    dict(id="SECU-05", id_corpus="c1ed84f9ce122d62", priorite=2,
         citation="s’appuie sur la police municipale, présente dans seulement 12 % des communes.",
         autres_versions="« Seulement 10% des 35 000 communes de France disposent d’une Police Municipale » (23/03/2023) ; « il y a 20% des communes qui ont une police municipale » (Sud Radio, 25/09/2024) ; « 86 % des communes françaises ne disposent d’aucune police municipale » (30/06/2026) ; « la police municipale dans 14 % des communes » (23/10/2026) ; « + 36 % d’effectifs de police municipale en dix ans, pour un coût de 2,2 milliards d’euros par an » (04/02/2026)",
         grandeur_testee="Communes dotées d'un service de police municipale ; effectifs 2014-2024 (ministère de l'Intérieur)"),
    dict(id="SECU-06", id_corpus="0c2b053bb9fc4923", date="2024-05-15", priorite=3,
         citation="En France, le chiffre d’affaires annuel du narcotrafic est estimé entre 3 et 6 milliards €.",
         autres_versions="« le chiffre d'affaires du narcotrafic, on l'évalue à 8 milliards » (28/08/2026)",
         grandeur_testee="Estimation du chiffre d'affaires du trafic de stupéfiants (Sénat 2024)"),
    dict(id="SECU-07", type="mesure", id_corpus="a0f53f821eea41ab", priorite=1,
         citation="Nous construirons enfin les 20 000 places de prison manquantes",
         autres_versions="répété depuis 2021 ; « au moins 30 000 places » (06/10/2025)",
         grandeur_testee="Besoin réel de places ; coût d'une place (plan 15 000)", verifiable="partiellement"),
    dict(id="SECU-08", type="mesure", id_corpus="07f430db4fe07236", priorite=2,
         citation="S’agissant des mineurs, je propose d’abaisser à 16 ans l’âge de la majorité pénale et de diminuer l’excuse de minorité, pour la porter de 50 % de la peine aujourd’hui à 20 ou 30 %.",
         grandeur_testee="Faisabilité juridique (principe constitutionnel de la justice des mineurs)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
