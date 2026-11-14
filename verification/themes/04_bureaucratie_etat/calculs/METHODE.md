# Méthode des calculs — thème 4, Bureaucratie, normes et réforme de l'État

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans des PDF sont recopiés dans `LUS_DANS_LES_PDF` avec la phrase exacte, vérifiée avant tout calcul.
Données téléchargées le 14/11/2026.

## M1 — Agences et opérateurs (`BUR-01`)

- Entrées : `SENAT-AGENCES-2025` et `SENAT-AGENCES-2025-SYN` (1 153 organismes publics nationaux, dont 434
  opérateurs ; 402 489 ETPT sous plafond et 77 058 hors plafond ; 77,0 Md€ de financements publics au PLF 2025, 80,6
  Md€ en 2024 ; l'IGF comptait 1 244 agences en 2012) ; `JAUNE-OPERATEURS-PLF2026` (liste des opérateurs).
- Calcul : charges de personnel et de fonctionnement = 2,2 Md€ / 8 % ≈ 27,5 Md€, car le Sénat écrit qu'une baisse de
  8 % de ces charges économiserait 2,2 Md€.
- Les « financements publics » (77 Md€) comprennent des transferts que les opérateurs reversent : formation
  professionnelle (France compétences, 15,1 Md€), infrastructures (AFITF, 4,6 Md€), rénovation des logements (ANAH,
  3,8 Md€). Ce n'est pas du « fonctionnement ».

## M2 — Fonctions « administrantes » (`BUR-02`)

Aucun calcul possible : aucune statistique publique ne classe les emplois publics en fonctions « administrantes » de
façon comparable entre pays. L'origine des 33-34 % n'a pas été retrouvée.

## M3 — Emploi public (`BUR-03`)

- Entrée : `OCDE-EMPLOI-PUBLIC-2025` (Panorama des administrations publiques 2025, série « Employment in government,
  percentage of employment, general government », France et Allemagne, 2021-2023).

## M4 — Coût des normes (`BUR-04`)

Pas de fichier : la seule estimation connue, de l'ordre de 3 à 4 % du PIB, date des années 2000 (méthode des coûts
standards, OCDE et Commission européenne). Elle n'a pas été actualisée par la statistique publique.

## M5 — Taille des codes (`BUR-05`)

Pas de fichier : les statistiques de la norme du Secrétariat général du Gouvernement sont sur Légifrance, qui refuse
les téléchargements automatiques. À déposer à la main dans `brut/sgg/`.

## M6 — Économies sur les agences (`BUR-06`) — ESTIMATION

- Calculs : 80 Md€ / 77 Md€ de financements publics de tous les opérateurs ; 8 Md€ / 27,5 Md€ de charges de
  personnel et de fonctionnement.
- **Estimation, non fiable à 100 %** : simples rapports d'ordres de grandeur, sans tenir compte des missions qui
  seraient reprises par l'État ou supprimées.
