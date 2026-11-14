# Méthode des calculs — thème 5, Décentralisation et collectivités

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
montants lus dans les réponses ministérielles (PDF) sont dans `LUS_DANS_LES_PDF`, avec la phrase exacte vérifiée.
Données téléchargées le 14/11/2026.

## M1 — Les « 80 milliards prélevés sur la DGF » (`DEC-01`)

- Entrées : `AN-QE-50991` (contribution 2014 : communes 558 M€, intercommunalités 252 M€) ; `AN-QE-95791` (2 071 M€
  en 2015 et en 2016, 1 035,5 M€ en 2017) ; `OFGL-DGF-COMMUNES` et `OFGL-DGF-GFP` (DGF perçue, 2018-2025) ;
  `EUROSTAT-INFLATION` (indice des prix harmonisé, France).
- Baisse annuelle par rapport à 2013 : 0,81 Md€ en 2014, 2,88 en 2015, 4,95 en 2016, puis 5,99 Md€ par an depuis
  2017. Elle n'a jamais été rendue.
- Cumul en euros courants = somme des baisses annuelles de 2014 à l'année choisie. Cette méthode compte la même baisse
  chaque année où elle s'applique : c'est celle de l'AMF. Elle est légitime (la perte se répète chaque année), mais il
  faut le dire.
- **Estimation, non fiable à 100 %** : perte due à l'absence d'indexation = Σ (DGF 2018 × prix de l'année / prix
  2018 − DGF réelle de l'année), de 2019 à 2025.

## M2 — Dette des collectivités (`DEC-02`)

- Entrée : `EUROSTAT-DETTE-LOCALE-TRIM` (dette au sens de Maastricht, sous-secteur S1313 « administrations
  publiques locales », % du PIB et millions d'euros, trimestriel depuis 2000). Contrôle : `EUROSTAT-DETTE-SECTEURS`.
- Calculs : niveau au 4e trimestre de chaque année ; part de la dette locale dans la dette publique totale.
- Limite : la série commence en 2000, on ne peut pas remonter à « il y a trente ans » (1996).

## M3 — Poids des collectivités dans la dépense (`DEC-03`)

- Entrée : `EUROSTAT-DEPENSES-SECTEURS` (dépenses totales par sous-secteur, 2024 : S1313 administrations locales,
  S1312 États fédérés et régions autonomes, S13 total).
- Calculs : dépense locale en % du PIB ; dépense locale / dépense publique totale ; mêmes ratios en ajoutant S1312
  (Länder allemands, communautés autonomes espagnoles, régions et États fédérés belges et autrichiens). La France n'a
  pas de sous-secteur S1312 : ses régions sont dans S1313.
- Les dépenses des sous-secteurs ne sont pas consolidées (les transferts entre administrations sont comptés deux
  fois) : les parts sont des ordres de grandeur, comparables entre pays.
