# Méthode des calculs — thème 12, Agriculture

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF et pages HTML sont dans `LUS`, avec la phrase exacte vérifiée dans le document. Données
téléchargées le 14/11/2026. Graphique : `graphiques/solde_agroalimentaire.png`.

## M1 — Solde et importations agroalimentaires (`AGRI-01`, `AGRI-03`)

- Entrées :
  - `TRESOR-COMMERCE-2025` : résultats officiels des Douanes, solde agricole et agroalimentaire de +0,2 Md€ en 2025
    et de +7,7 Md€ en 2019 ;
  - `ACADEMIE-AGRI-COMMERCE` : déficit en 2025 « si l'on inclut les produits de la mer », une première depuis 1978 ;
  - `COMEXT-AGROALIMENTAIRE` : importations (flux 1) et exportations (flux 2) de la France, tous partenaires, pour
    les chapitres 01 à 24 du système harmonisé et les positions 1604-1605 (préparations de poisson et de
    crustacés).
- Calculs :
  - solde = exportations − importations, sommées sur les chapitres 01 à 24 ;
  - « hors produits de la mer » : on retire le chapitre 03 et les positions 1604 et 1605 des deux flux ;
  - hausse des importations 2025 / 2024.
- Limite : le périmètre officiel des Douanes, la nomenclature de produits CPF, n'est pas celui des chapitres 01 à
  24. Les niveaux diffèrent donc de quelques milliards d'euros. Les tendances, elles, concordent.

## M2 — Importations depuis 2000 (`AGRI-02`)

- Entrée : `COMEXT-AGROALIMENTAIRE`.
- Calcul : importations 2022 / importations 2000, en euros courants, pour les chapitres 01 à 24, puis hors produits
  de la mer et hors tabac (chapitre 24).
- Limite : les euros sont courants, sans correction de l'inflation.

## M3 — Suicide des agriculteurs (`AGRI-04`)

- Entrées :
  - `AN-QE102524-SUICIDE` : réponse du ministère de l'Agriculture, qui cite une surmortalité par suicide des
    exploitants de 22 à 28 % (MSA, années 2007-2011) ;
  - `AN-QE23624-SUICIDE-MSA` : étude de la MSA, risque supérieur d'environ 12 % en 2015 ;
  - `SPF-BEH-2018-SUICIDE` : contexte.
- Calcul : une surmortalité de 28 % correspond à 1,28 fois le risque moyen ; « 7 fois plus » correspondrait à
  +600 %.
- Limite : les publications de Santé publique France sur les exploitants n'ont pas pu être téléchargées : le site
  renvoie une page HTML au lieu du PDF.

## M4 — Pauvreté des exploitants (`AGRI-05`)

- Entrée : `INSEE-PAUVRETE-EXPLOITANTS` (Insee et SSP, données 2020) : 17,7 % des exploitants sous le seuil de
  pauvreté monétaire, contre 14,4 % dans l'ensemble de la population. Aucun calcul.

## M5 — Revenu agricole sur 30 ans (`AGRI-06`)

- Entrée : `EUROSTAT-REVENU-AGRICOLE`, variations annuelles en volume (unité I_N_1) de deux indicateurs :
  - l'indicateur C : revenu net d'entreprise agricole total, en termes réels ;
  - l'indicateur B : le même revenu par unité de travail non salarié.
- Calcul : évolution sur la période = produit des indices annuels / 100, moins 1 (1994 → 2024 et 1995 → 2025). Les
  indices en niveau ne commencent qu'en 2001.

## M6 — Engrais azotés (`AGRI-07`)

- Entrée : `EUROSTAT-ENGRAIS` (consommation d'engrais minéraux, en tonnes d'azote). Aucun calcul.
- Limite : la part importée n'a pas été mesurée ici. Il faudrait les quantités importées (Comext, position 3102,
  en tonnes de produit), la teneur en azote et la production nationale.
