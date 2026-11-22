# Méthode des calculs — Mélenchon, thème 7, Santé et hôpital

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 20/11/2026 ; l'accessibilité potentielle localisée (APL) de la DREES est reprise du dossier de David
Lisnard, et lue de la même façon.

## M1 — Les lits de l'hôpital public (`SANTE-01`)

- Entrées : `EUROSTAT-LITS-PROPRIETAIRE` (lits selon le statut : public, privé non lucratif, privé lucratif) ;
  `EUROSTAT-LITS-TYPE` (lits selon le type de soins : aigus, longue durée, réadaptation, psychiatrie).
- Calcul : lits publics de la dernière année connue moins ceux de vingt-cinq ans plus tôt ; même calcul pour les lits
  de longue durée, tous statuts.

## M2 — Les déserts médicaux (`SANTE-02`)

- Entrée : `DREES-APL-GENERALISTES` (APL 2024 par commune et population). Calcul : part de la population vivant dans
  une commune dont l'APL est inférieure à 2,5 (seuil de sous-densité de la DREES), 3 et 4 consultations par an et par
  habitant.

## M3 — Les cancers évitables (`SANTE-03`)

- Entrée : `CIRC-CANCERS-EVITABLES-2018` (41 % des cancers de 2015 attribuables aux facteurs de risque étudiés ;
  parts de la pollution de l'air, des substances chimiques, du radon, des infections et des expositions
  professionnelles). Calcul : sommes de ces parts.
