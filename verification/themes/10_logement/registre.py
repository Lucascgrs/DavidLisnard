"""Affirmations du thème 10 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 10"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Logement et urbanisme"
A = [
    dict(id="LOG-01", id_corpus="b2184cb482fda5bf", priorite=1,
         citation="Aujourd'hui, on a 10 millions d'habitants de plus et on est en dessous de 300 000 logements par an.",
         autres_versions="« Quand le président Pompidou meurt en 1974, il y a 10 millions d'habitants de moins en France. Et il y a quasiment 500 000 logements neufs par an » (même audition) ; « déjà faible, à 437 000, en 2017, le nombre de logements mis en chantier en France n’a cessé de diminuer, jusqu’à 345 000 en 2021 » (22/12/2022) ; « seuls 258.500 logements ont été mis en chantier sur un an » (09/05/2025)",
         grandeur_testee="Logements commencés par an (SDES) ; population (Eurostat, Insee)"),
    dict(id="LOG-02", id_corpus="cb930ca4d36b4e69", priorite=2,
         citation="40 milliards d’euros de dépenses publiques, toutes administrations confondues, qui sont consacrés en France à la politique du logement (soit 1,2 % du PIB contre 0,5 % en moyenne européenne selon les données Eurostat)",
         grandeur_testee="Dépenses publiques de logement en % du PIB, France et UE (Eurostat, COFOG et protection sociale)"),
    dict(id="LOG-03", id_corpus="cb930ca4d36b4e69", priorite=2,
         citation="la fiscalité liée au logement, qui pèse en France 6 % des prélèvements obligatoires contre 3,3 % en moyenne dans l’OCDE",
         grandeur_testee="Impôts sur le patrimoine immobilier en % des recettes fiscales (OCDE)"),
    dict(id="LOG-04", id_corpus="9bd690b50b94ed7b", date="2026-09-01", priorite=3,
         citation="plus des deux tiers des Français sont aujourd’hui en théorie éligibles au logement social",
         grandeur_testee="Part des ménages sous les plafonds de ressources du logement social", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
