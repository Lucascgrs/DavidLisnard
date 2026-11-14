# Méthode des calculs — thème 16, Cannes : bilan municipal

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 14/11/2026. Graphique : `graphiques/dette_cannes.png`.

## Données communes

- `DGFIP-COMPTES-CANNES-*` : comptes individuels des communes publiés par la DGFiP sur data.economie.gouv.fr. Il y a
  un fichier par millésime, de 2008 (qui reprend 2000-2008) à 2025, et l'on en extrait la ligne de Cannes
  (département 006, commune 029).
- Ces comptes portent sur le budget principal seul : les budgets annexes ne sont pas compris.
- Montants en milliers d'euros, convertis en millions. Champs utilisés :
  - `dette` : encours de la dette au 31 décembre ;
  - `caf` et `cafn` : capacité d'autofinancement brute et nette ;
  - `charge` : charges de fonctionnement ;
  - `dgf` : dotation globale de fonctionnement ;
  - `tfb`, `tfnb`, `tth` : taux communaux votés.

## M1 — Dette (`CAN-01`)

- Calculs :
  - encours fin d'année N − encours fin 2013, dernier exercice avant l'élection d'avril 2014, pour N = 2023, 2024
    et 2025 ;
  - contexte : variation 2001-2008 ;
  - capacité de désendettement 2025 = encours / CAF brute.

## M2 — Capacité d'autofinancement (`CAN-02`)

- CAF nette = CAF brute − remboursement en capital de la dette. Son équivalent à l'OFGL s'appelle « épargne nette »
  (55,92 M€ en 2024 sur data.ofgl.fr, 56,01 M€ ici).
- Calculs :
  - rapport 2024 / 2014 ;
  - rapport des moyennes sur trois ans (2023-2025 contre 2011-2013), moins sensible au choix des années.

## M3 — Taux d'imposition (`CAN-03`)

- Calculs :
  - nombre de taux différents de 2014 à 2024, par taxe ;
  - évolution du taux de 2024 à 2025.
- Le passage du foncier bâti de 17,50 % à 28,12 % en 2021 est mécanique. Ce n'est pas une hausse : la part
  départementale (10,62 points) a été transférée aux communes avec la suppression de la taxe d'habitation sur les
  résidences principales.

## M4 — Dépenses de fonctionnement (`CAN-04`)

- Calcul : différence des charges de fonctionnement entre deux exercices, en euros courants, pour plusieurs couples
  d'années.

## M5 — Pauvreté (`CAN-05`)

- Entrée : `INSEE-FILOSOFI-2021` (fichiers `cc_filosofi_2021_COM.csv` et `cc_filosofi_2021_METRO.csv`) : taux de
  pauvreté à 60 % du niveau de vie médian (variable TP6021). Aucun calcul.

## M6 — « Ponctions de l'État » (`CAN-06`) — ESTIMATION

- Calcul : somme, sur 2014-2022, des écarts entre la DGF de l'année de référence et la DGF de chaque année.
  - Avec 2013 comme référence : la DGF passe de 47,2 M€ en 2013 à 30,4 M€ en 2014. Cette chute inhabituelle
    suggère un changement de périmètre, qui n'a pas été vérifié.
  - Avec 2014 comme référence.
- **Estimation, non fiable à 100 %** : la DGF n'est qu'une partie des « ponctions » possibles. La péréquation (FPIC)
  et d'autres prélèvements ne sont pas comptés.
