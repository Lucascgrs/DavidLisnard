# Méthode des calculs — Mélenchon, thème 10, Logement et urbanisme

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les documents sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le 20/11/2026.

## M1 — Les demandes de logement social (`LOG-01`)

- Entrées : `BDT-LOGEMENTS-SOCIAUX-2024` (chiffres du ministère du Logement : 2,76 millions de ménages demandeurs au
  31 décembre 2024) ; `FPL-ETRE-HUMAIN-130` (2,9 millions de ménages, début 2026). Aucun calcul.

## M2 — Les sans-domicile (`LOG-02`)

- Entrées : `FPL-ETRE-HUMAIN-130` (350 000 personnes sans domicile) ; `INSEE-DEF-SANS-DOMICILE` (définition). La
  Fondation est une partie prenante (niveau D) : son chiffre est repris tel quel, sans recalcul.

## M3 — Les logements sociaux financés (`LOG-03`)

- Entrée : `BDT-LOGEMENTS-SOCIAUX-2024` (98 682 logements sociaux financés en 2024, 91 208 en 2023). Calcul :
  200 000 / 98 682.
