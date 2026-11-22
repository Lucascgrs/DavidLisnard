# Méthode des calculs — Mélenchon, thème 17, Inégalités, pauvreté et grandes fortunes

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 20/11/2026.

## M1 — Le nombre de personnes pauvres (`INEG-01`, `INEG-03`)

- Entrée : `INSEE-PAUVRETE-NOMBRE` (personnes sous le seuil de 60 % du niveau de vie médian, en milliers, France
  métropolitaine, enquêtes Revenus fiscaux et sociaux). Calcul : 2024 − 2017.

## M2 — Le taux de pauvreté, record ou non (`INEG-02`)

- Entrée : `INSEE-PAUVRETE-TAUX` (taux à 60 %, 1975 à 2024). Les années suivies d'un renvoi dans le fichier (1996,
  2010, 2012, 2020) ouvrent une nouvelle série ; les années 1975 à 1990 sont des données rétropolées.
- Calcul : taux 2024 ; taux le plus élevé de 1996 à 2022 ; taux de 1975, 1979 et 1984.

## M3 — L'aide alimentaire (`INEG-04`)

- Entrée : `INSEE-AIDE-ALIMENTAIRE-2022` (estimation de 2 à 4 millions de bénéficiaires sur une année, fin 2021).

## M4 — Se chauffer (`INEG-05`)

- Entrées : `EUROSTAT-CHAUFFAGE` (part de la population qui ne peut pas chauffer convenablement son logement) ;
  `EUROSTAT-POPULATION`. Calcul : part × population au 1er janvier.

## M5 — Le SMIC et le seuil de pauvreté (`INEG-06`) — ESTIMATION

- Entrées : `EUROSTAT-SMIC-PAYS` (SMIC brut 2024, moyenne des deux semestres) ; `INSEE-SEUILS-PAUVRETE` (seuil 2024 :
  1 337 €). Le net est estimé en retirant 20,95 % de cotisations salariales. **Estimation, non fiable à 100 %.**

## M6 — Le seuil de 1 337 € (`INEG-07`)

- Entrée : `INSEE-SEUILS-PAUVRETE` (seuils mensuels, euros courants, 2024). Aucun calcul.
