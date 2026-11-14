"""Affirmations du thème 15 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 15"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Culture, numérique et intelligence artificielle"
A = [
    dict(id="NUM-01", id_corpus="127b429195e1c2ac", priorite=2,
         citation="En cinquante ans, l’Europe n’a pas engendré une seule entreprise valorisée à plus de 100 milliards d’euros, quand les six géants américains au-dessus de 1 000 milliards sont tous nés sur cette période.",
         grandeur_testee="Rapport Draghi (2024), partie A"),
    dict(id="NUM-02", id_corpus="127b429195e1c2ac", priorite=1,
         citation="En 2025, l’investissement privé dans l’intelligence artificielle a atteint près de 286 milliards de dollars aux États-Unis, vingt-trois fois le niveau chinois.",
         grandeur_testee="Investissement privé dans l'IA (Stanford HAI, AI Index 2026)"),
    dict(id="NUM-03", id_corpus="127b429195e1c2ac", priorite=3,
         citation="Et la Chine est désormais en tête dans 57 des 64 technologies critiques recensées.",
         autres_versions="« Sur soixante-quatorze technologies de rupture […] soixante-six aujourd'hui voient la Chine en position dominante » (discours, 29/08/2026)",
         grandeur_testee="Critical Technology Tracker (ASPI)"),
    dict(id="NUM-04", id_corpus="127b429195e1c2ac", priorite=2,
         citation="Taïwan, où se fabriquent plus de 90 % des semi-conducteurs les plus avancés, demeure un point de bascule du monde.",
         grandeur_testee="Capacités de production de semi-conducteurs avancés (BCG et Semiconductor Industry Association, 2021)"),
    dict(id="CULT-01", id_corpus="30d6446e8ef0bfdb", priorite=2,
         citation="« Le ministère de la Culture dépense en moyenne 801 euros par habitant parisien contre 24 euros par habitant de la province… »",
         grandeur_testee="Dépenses du ministère de la Culture par habitant et par région (Insee, DEPS)"),
    dict(id="CULT-02", type="mesure", id_corpus="09a35c9f8adb6111", priorite=3,
         citation="je ferais un grand ministère unique de l'Instruction, de la Recherche et de la Culture.",
         autres_versions="« Si notre pays doit absolument conserver un audiovisuel public, celui-ci doit être populaire et de qualité, sinon il disparaîtra de lui-même » (29/05/2026)",
         grandeur_testee="Mesure", verifiable="non"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
