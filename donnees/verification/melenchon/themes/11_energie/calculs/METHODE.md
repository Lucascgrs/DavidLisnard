# Méthode des calculs — Mélenchon, thème 11, Énergie et nucléaire

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 20/11/2026 ; le bulletin pétrolier européen et la production d'électricité sont repris du dossier de
David Lisnard (même fichier, même empreinte).

## M1 — Prix du gaz depuis mai 2017 (`NRJ-01`)

- Entrée : `EUROSTAT-IPCH-ENERGIE` (indice des prix harmonisé, poste « gaz », base 2025 = 100). Calcul : hausse de
  mai 2017 (élection d'Emmanuel Macron) à août 2026 (dernier mois connu le jour du discours) et à septembre 2026.

## M2 — Les prix pendant les gilets jaunes (`NRJ-02`)

- Entrée : `CE-BULLETIN-PETROLIER` (prix hebdomadaires toutes taxes en France, en € pour 1 000 litres). Calcul : prix
  le plus haut d'une semaine d'octobre 2018 à mars 2019, et de 2005 à 2021, pour le gazole et l'essence SP95.

## M3 — Les marges de raffinage (`NRJ-03`)

- Entrée : `DGEC-MARGE-RAFFINAGE` (marge brute de raffinage sur Brent, moyennes mensuelles, en €/t). Calcul :
  rapport entre août ou septembre 2026 et janvier ou février 2026, les deux mois qui précèdent la hausse de mars 2026.
- Cette marge est un indicateur « théorique » du ministère : la valeur d'un panier de produits raffinés à Rotterdam
  moins le prix du Brent. Elle ne mesure ni les coûts des raffineries ni leur bénéfice.

## M4 — Le prix de 1,70 € (`NRJ-04`)

- Entrée : `DGEC-PRIX-CARBURANTS` (prix hebdomadaires toutes taxes, gazole et SP95-E10). Calcul : moyenne de février
  2026 (avant la hausse) et de septembre 2026 (moment de la proposition), puis baisse nécessaire pour revenir à 1,70 €.

## M5 — Renouvelables et nucléaire (`NRJ-05`)

- Entrées : `EUROSTAT-PART-RENOUVELABLES` (part des renouvelables dans la consommation finale brute d'énergie) ;
  `EUROSTAT-PRODUCTION-ELEC` (production brute d'électricité : nucléaire, renouvelables, total). Dernière année
  disponible.
