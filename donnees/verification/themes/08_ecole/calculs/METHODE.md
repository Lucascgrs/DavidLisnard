# Méthode des calculs — thème 8, École et enseignement

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 14/11/2026.

## M1 — Classement PISA (`ECOLE-01`)

- Entrées : `OCDE-PISA-2022-MEXT` (tableau I.2.1 de l'OCDE, PISA 2022, score moyen en mathématiques par pays, reproduit
  à l'identique par le ministère japonais de l'Éducation ; le site de l'OCDE refuse les téléchargements automatiques) ;
  `BM-PISA-2000-2018` (scores PISA en mathématiques 2000-2018, repris de l'OCDE par la Banque mondiale).
- Calculs : rang de la France parmi les 26 pays de l'UE ayant participé à PISA 2022 (le Luxembourg n'y a pas
  participé) ; variation du score français 2018 → 2022.
- Limite : seules les mathématiques sont classées ici. L'écrit et les sciences donnent des positions voisines. TIMSS
  2023 (CM1, 4e) n'a pas pu être téléchargé (site de la DEPP protégé).

## M2 — Dépense d'éducation (`ECOLE-02`)

- Entrées : `EUROSTAT-COFOG-EDUCATION` (dépense des administrations publiques pour l'enseignement, fonction 09,
  millions d'euros et % du PIB) ; `EUROSTAT-PRIX-PIB` (déflateur du PIB, base 2015) ; `EUROSTAT-ELEVES` (élèves du
  primaire, du collège et du lycée).
- Calculs : hausse 2000 → 2024 et 2001 → 2024 en euros courants, puis en euros constants (dépense / déflateur).
- Limite : c'est la dépense publique, pas la dépense intérieure d'éducation de la DEPP (qui ajoute les familles et
  les entreprises). Le compte de l'éducation de la DEPP n'a pas pu être téléchargé.

## M3 — « 60 milliards » (`ECOLE-03`)

- Entrée : `BUDGET-VERT-PLF2026` (crédits de paiement 2025 de la mission Enseignement scolaire, hors pensions).
- Aucun calcul de son « 30 milliards » n'est possible : il n'en donne ni la méthode ni les hypothèses.
