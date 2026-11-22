# Méthode des calculs — thème 6, Économie, travail et entreprises

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Aucun
chiffre n'est lu dans un PDF pour ce thème. Données téléchargées le 14/11/2026.

## M1 — Déficit commercial (`ECO-01`)

- Entrées : `EUROSTAT-COMMERCE-DOUANES` (solde des échanges de biens de la France avec le monde, données douanières,
  importations valorisées CAF) ; `EUROSTAT-COMMERCE-BIENS` (exportations P61 et importations P71 de biens, comptes
  nationaux).
- Le chiffre publié par les douanes françaises (importations FAB, hors frais de transport) se situe entre les deux.
  Il n'a pas pu être téléchargé : le site des douanes n'a pas d'API ouverte.

## M2 — Poids de l'industrie (`ECO-02`)

- Entrées : `EUROSTAT-VA-BRANCHES` (valeur ajoutée brute par branche : C industrie manufacturière, B-E industrie au
  sens large, TOTAL) ; `EUROSTAT-PIB-PAYS` (PIB).
- Calculs : valeur ajoutée de l'industrie manufacturière / PIB et / valeur ajoutée totale (la valeur ajoutée totale
  représente environ 89 % du PIB) ; rang dans l'UE à 27 de la part manufacturière.

## M3 — Productivité (`ECO-03`)

- Entrée : `OCDE-PRODUCTIVITE` (PIB par heure travaillée : volume en monnaie nationale pour la croissance ; dollars
  en parités de pouvoir d'achat courantes pour comparer les niveaux).
- Calculs : hausse 2010 → 2023 ; rapport zone euro / États-Unis en 1995, 2019, 2023.
- Le rapport Draghi utilise des niveaux en parités de pouvoir d'achat constantes et une autre base de calcul. Les
  séries actuelles de l'OCDE ne reproduisent pas le passage de 98 % à 82 %.

## M4 — Chômage (`ECO-04`)

- Entrées : `EUROSTAT-CHOMAGE-ANNUEL` (taux de chômage au sens du BIT, 15-24 ans, France, Allemagne, zone euro à 21,
  UE) ; `EUROSTAT-CHOMAGE-TRIM` (France, 15-74 ans, données corrigées des variations saisonnières).

## M5 — Recherche et développement (`ECO-05`)

- Entrée : `EUROSTAT-RD` (dépense intérieure de R&D en % du PIB par secteur d'exécution : entreprises BES, État GOV,
  enseignement supérieur HES ; 2023).
- La « recherche publique » correspond aux secteurs GOV + HES ; la dépense totale ajoute les entreprises.
