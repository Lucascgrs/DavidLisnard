# Méthode des calculs — Mélenchon, thème 18, Climat, eau et environnement

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 20/11/2026 ; les émissions de gaz à effet de serre sont reprises du dossier de David Lisnard.

## M1 — Les records de chaleur (`CLIM-01`)

- Entrée : `C3S-ERA5-TEMPERATURE` (température mondiale quotidienne et écart à la moyenne 1991-2020).
- Calcul : moyenne annuelle des écarts quotidiens ; une année est un record si elle dépasse toutes les précédentes
  depuis 1940 ; sinon, son rang parmi les années déjà écoulées.

## M2 — L'objectif de −65 % (`CLIM-02`) — ESTIMATION

- Entrée : `EUROSTAT-GES` (émissions de la France hors puits de carbone, inventaire transmis à l'ONU).
- Calculs : baisse 1990 → 2024 ; rythme annuel moyen 2014 → 2024 ; rythme annuel nécessaire de 2024 à 2033 pour
  atteindre 35 % du niveau de 1990. **Estimation, non fiable à 100 %** : base 1990 supposée, baisse régulière.

## M3 — La forêt (`CLIM-03`)

- Entrée : `IGN-MEMENTO-2025` (taux de boisement de 32 % ; mortalité +125 % par rapport à la décennie précédente).
  Aucun calcul.
