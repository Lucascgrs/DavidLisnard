# Méthode des calculs — thème 9, Retraites et protection sociale

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF sont dans `LUS_DANS_LES_PDF`, avec la phrase exacte vérifiée. Données téléchargées le
14/11/2026.

## M1 — Le déficit « réel » des retraites (`RET-01`)

- Entrée : `CC-RETRAITES-2025` (Cour des comptes, février 2025) : déficit tous régimes prévu pour 2025 (6,6 Md€) ;
  taux de cotisation employeur de l'État (78,28 % pour les fonctionnaires civils depuis 2025, 126,07 % pour les
  militaires) ; constat que la contribution de l'État « mêle » cotisation employeur, solidarité et équilibre, d'où
  « autant de formules de calcul que de conventions comptables », « sans effet sur le solde des finances
  publiques ».
- Le calcul de l'institut Molinari (2,8 % du PIB) traite comme une subvention la part de la contribution de l'État
  qui dépasse le taux d'un employeur privé. C'est une convention parmi d'autres : elle n'a pas été refaite ici.

## M2 — 116 Md€ de capitalisation (`RET-02`) — ESTIMATION

- Entrées : `CC-RETRAITES-2025` (dépenses de retraite 2023 : 388,4 Md€) ; `EUROSTAT-PROTSOC-VIEILLESSE` (dépenses
  « vieillesse » 2024).
- Calculs : 116 / dépenses de retraite ; total implicite si 116 Md€ valaient 40 % (116 / 0,4).

## M3 — Le smicard et ses 320 000 € (`RET-03`) — ESTIMATION

- Entrée : `EUROSTAT-SMIC` (salaire minimum brut mensuel, 2e semestre 2025 : 1 802 €).

```latex
320\,000 = v \times \frac{(1+r)^{40} - 1}{r}, \quad v = 0{,}10 \times 12 \times \text{SMIC brut mensuel}
```

- On résout en r (rendement annuel constant). Puis on calcule le capital obtenu avec 4,7 % par an (rendement de
  l'Erafp depuis 2006), et la valeur actuelle de 320 000 € avec 2 % d'inflation par an (320 000 / 1,02^40). **Estimation, non fiable à 100 %** : SMIC constant (sans hausse), aucun frais, aucune
  fiscalité, rendement nominal.

## M4 — Rendement de l'Erafp (`RET-04`)

- Entrée : `ERAFP-RA-2025` (rapport annuel 2025 : « Le TRI global depuis 2006 s'élève à 4,7 % à fin 2025 […] (4,3 %) »
  à fin 2024). Aucun calcul.

## M5 — Le régime de retraite de la SNCF (`RET-05`)

- Entrée : `BUDGET-VERT-PLF2026` (crédits 2025 : action « Régime de retraite du personnel de la SNCF » du programme
  198, mission Justice hors pensions).
- Calculs : subvention de l'État / crédits Justice ; 5,5 Md€ / crédits Justice. Le montant total des pensions du
  régime (5,5 Md€ selon Lisnard) n'a pas été téléchargé (rapport de la caisse de prévoyance et de retraite de la
  SNCF).
