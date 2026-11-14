"""Affirmations du thème 6 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 6

Les affirmations économiques déjà traitées dans le thème 1 (prélèvements sur les entreprises, impôts de production,
dépenses sociales, coin fiscal) ne sont pas reprises ici.
"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Économie, travail et entreprises"
A = [
    dict(id="ECO-01", id_corpus="bae9e369da70f247", date="2026-04", priorite=2,
         citation="Le déficit commercial fut d’environ 80 milliards d'euros en 2024.",
         autres_versions="« 114 milliards en un an » (25/08/2022) ; « un déficit commercial structurel de 100 milliards d’euros » (19/07/2024) ; « Les champions qui nous gouvernent […] ont créé 100 milliards de déficit de commerce » (26/06/2024)",
         grandeur_testee="Solde des échanges de biens (comptes nationaux, Eurostat)"),
    dict(id="ECO-02", id_corpus="bae9e369da70f247", date="2026-04", priorite=1,
         citation="En part du PIB, la France est l'un des pays devenu les moins industrialisés d'Europe : 10,6%, contre par exemple 16% pour l'Italie et 13,6% pour l'Espagne.",
         autres_versions="« L’industrie représente moins de 10 % du PIB français contre 19 % en Allemagne » (15/05/2026) ; « on n'est plus qu'à 10,3 % de PIB produit par la production industrielle » (29/08/2026)",
         grandeur_testee="Valeur ajoutée de l'industrie manufacturière en % de la valeur ajoutée totale (Eurostat)"),
    dict(id="ECO-03", id_corpus="1cd9653671ac54bb", priorite=1,
         citation="Les chiffres sont là : de 2010 à 2023, la productivité du travail a progressé de 22% aux États-Unis et de 5% en Europe.",
         autres_versions="« La productivité horaire de la zone euro, qui atteignait 98 % de celle des États-Unis en 1995, n’en représentait plus que 82 % en 2019 » (15/05/2026, citant le rapport Draghi)",
         grandeur_testee="PIB par heure travaillée, volume, États-Unis et zone euro (OCDE)"),
    dict(id="ECO-04", id_corpus="e6d304a2ef06bf0b", priorite=2,
         citation="Le chômage des 15-24 ans atteint 18,8 %, contre 6,7 % en Allemagne et moins de 15 % en moyenne dans la zone euro.",
         autres_versions="« L'INSEE confirme : 8,1 % de chômage au 1er trimestre 2026 » (22/05/2026)",
         grandeur_testee="Taux de chômage au sens du BIT, 15-24 ans (Eurostat)"),
    dict(id="ECO-05", id_corpus="36ef214f9db258f7", priorite=2,
         citation="Celle de la recherche publique : la France y consacre 2,2 % du PIB contre 3,1 % en Allemagne et 3,5 % aux États-Unis",
         grandeur_testee="Dépense intérieure de R&D (totale et publique) en % du PIB (Eurostat)"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
