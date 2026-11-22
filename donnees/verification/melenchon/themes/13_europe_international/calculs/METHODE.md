# Méthode des calculs — Mélenchon, thème 13, Europe et international

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 20/11/2026 ; le PIB des pays est repris du thème 1 de Jean-Luc Mélenchon, les dépenses de défense de
l'OTAN du dossier de David Lisnard.

## M1 — Le poids de la France et de la Grèce (`EUR-01`)

- Entrée : `EUROSTAT-PIB-PAYS-2025` (PIB 2025 en euros courants). Calcul : PIB du pays / PIB de l'UE et de la zone euro.

## M2 — La dette américaine (`EUR-02`)

- Entrée : `TRESOR-US-DETTE` (« Debt to the Penny », dette fédérale totale, quotidienne). Valeur du dernier jour publié
  à la date de chaque déclaration.

## M3 — L'objectif de 5 % (`EUR-03`) — ESTIMATION

- Entrées : `OTAN-DEPENSES-2025` (dépenses de défense de la France, 2,05 % du PIB en 2025) ; `EUROSTAT-PIB-PAYS-2025`.
- Calcul : (5 − 2,05) % × PIB 2025. **Estimation, non fiable à 100 %** : le PIB futur et la définition retenue
  changent le montant.
