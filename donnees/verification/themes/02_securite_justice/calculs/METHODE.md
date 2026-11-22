# Méthode des calculs — thème 2, Sécurité, justice et narcotrafic

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), écrits dans `resultats.csv`.
Les chiffres lus dans des PDF sont recopiés dans `LUS_DANS_LES_PDF` avec la phrase exacte ; le script vérifie qu'elle
figure dans le PDF avant de calculer. Données téléchargées le 14/11/2026.

## M1 — Évolution de la délinquance enregistrée (`SECU-01`)

- Entrée : `SSMSI-DELINQUANCE-DEP` (faits enregistrés par la police et la gendarmerie, par département, 2016-2025,
  édition juillet 2026). Somme des départements = France entière (métropole et outre-mer).
- Indicateurs : « Homicides », « Tentatives d'homicide », « Violences physiques intrafamiliales » et « Violences
  physiques hors cadre familial ». Leur somme sert d'équivalent aux « coups et blessures volontaires » des anciennes
  publications : le SSMSI a refondu ses indicateurs en 2024 et recalculé toute la série. Les chiffres publiés à
  l'époque (que Lisnard reprend) peuvent donc différer des séries actuelles.
- Calculs : évolution = valeur de l'année d'arrivée / valeur de l'année de départ − 1, sur les périodes citées par
  Lisnard (2017 → 2021, 2017 → 2022, 2017 → 2025, 2016 → 2025).
- Part de la hausse due aux violences intrafamiliales = hausse des violences intrafamiliales / hausse du total des
  violences physiques, 2017 → 2025.
- Limite : ce sont des faits **enregistrés**. Une hausse peut venir d'un meilleur dépôt de plainte (c'est le cas des
  violences conjugales depuis 2017, selon le SSMSI). L'enquête de victimation « Vécu et ressenti en matière de
  sécurité » permettrait de corriger cet effet ; son rapport n'a pas pu être téléchargé (site du ministère protégé).

## M2 — Places de prison et taux de détention (`SECU-02`)

- Entrées : `DAP-DETENUS-2026-09` et `DAP-DETENUS-2025-09` (tableau 6 : détenus et places opérationnelles, France
  entière) ; `SENAT-PENITENTIAIRE-PLF2026` (22 361 places manquantes au 1er octobre 2025, calculées établissement par
  établissement) ; `COE-SPACE-I-2024` (détenus pour 100 000 habitants au 31 janvier 2024, médiane de 51
  administrations pénitentiaires).
- Calcul : détenus − places opérationnelles. C'est un minimum : comme certains établissements ne sont pas pleins,
  supprimer toute suroccupation demande plus de places que cette différence (d'où le chiffre plus élevé du Sénat).

## M3 — Exécution des peines (`SECU-03`)

- Entrées : `RSJ-2025-EXECUTION` (taux de mise à exécution des peines d'emprisonnement ferme : 57 % au jugement et
  79 % à un an, en 2024) ; `RSJ-2026-EXECUTION` (58 % au jugement en 2025, 90 % à cinq ans pour les peines devenues
  exécutoires en 2020) ; `IGJ-EXECUTION-PEINES-2022`.
- Calcul : part non exécutée = 100 − taux de mise à exécution, à chaque horizon. Le taux à six mois n'est pas publié
  dans ces fichiers : il est compris entre le taux au jugement et le taux à un an.

## M4 — Moyens de la justice comparés à l'Europe (`SECU-04`)

- Entrée : `CEPEJ-FRANCE-2024` (fiche France de l'étude CEPEJ pour la Commission européenne, données 2024 : juges et
  procureurs pour 100 000 habitants, France et médiane de l'UE).
- Le budget en % du PIB n'est pas dans ce fichier : non vérifié ici.

## M5 — Polices municipales (`SECU-05`)

- Entrées : `PM-EFFECTIFS-2024` (enquête annuelle du ministère de l'Intérieur : ligne « TOTAL NATIONAL », 4 592
  communes ou intercommunalités ayant un service, 28 846 policiers municipaux) ; `PM-EFFECTIFS-2014` (ligne
  « totaux » : 20 448 policiers municipaux) ; `GEO-COMMUNES` (34 969 communes).
- Calculs : services / communes (borne haute, car un service intercommunal couvre plusieurs communes) ; lignes ayant
  au moins un policier municipal / communes (borne basse) ; évolution des effectifs 2014 → 2024.

## M6 — Narcotrafic (`SECU-06`)

- Entrée : `SENAT-NARCOTRAFIC-2024` (« 3,5 milliards d'euros, en fourchette basse », chiffre du ministre de
  l'Économie). Aucun calcul.

## M7 — Le coût de 20 000 places (`SECU-07`) — ESTIMATION

- Entrées : `SENAT-PLAN15000-2023` (coût total du plan 15 000 réévalué à 5,55 Md€ en juin 2023) ;
  `SENAT-PENITENTIAIRE-PLF2026` (coût moyen d'une journée de détention : 128 € en 2024 ; 7 504 places brutes livrées
  fin octobre 2025).
- Calculs : coût par place = 5,55 Md€ / 15 000 ; 20 000 places × ce coût ; fonctionnement = 20 000 × 128 € × 365.
- **Estimation, non fiable à 100 %** : coût moyen d'un programme en cours, sans l'inflation depuis 2023 ni le
  personnel supplémentaire à recruter au-delà du coût moyen de détention.

## M8 — Majorité pénale à 16 ans (`SECU-08`)

- Entrée : `CC-2002-461-DC`, considérant 26 : « l'atténuation de la responsabilité pénale des mineurs en fonction de
  l'âge » est un principe fondamental reconnu par les lois de la République. Aucun calcul : analyse juridique
  résumée, à confirmer par des constitutionnalistes.
