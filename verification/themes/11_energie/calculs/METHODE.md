# Méthode des calculs — thème 11, Énergie et nucléaire

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF et pages HTML sont dans `LUS`, avec la phrase exacte vérifiée dans le document. Données
téléchargées le 14/11/2026. Graphique : `graphiques/prix_electricite_entreprises.png`.

## M1 — Mix électrique (`NRJ-01`, `NRJ-02`)

- Entrée : `EUROSTAT-PRODUCTION-ELEC` (production brute d'électricité, GWh) : total, nucléaire (N900H), renouvelables
  et biocarburants (RA000), énergies fossiles (FE).
- Calculs :
  - part du nucléaire = N900H / TOTAL ;
  - part décarbonée = (N900H + RA000) / TOTAL.
- Limite : RTE publie des parts calculées sur la production nette, qui peuvent différer de quelques dixièmes de
  point.

## M2 — Part de la France dans le PIB et les émissions mondiales (`NRJ-03`)

- Entrées :
  - `FMI-PIB-DOLLARS` (PIB en dollars courants, France et monde, base WEO) ;
  - `FMI-PIB-PPA-PART` (part du PIB mondial en parité de pouvoir d'achat) ;
  - `GCB-OWID-CO2` (Global Carbon Budget : CO2 fossile, territorial et de consommation).
- Calculs : PIB France / PIB monde ; CO2 France / CO2 monde, en émissions territoriales (2023 et 2025) et en
  émissions de consommation, c'est-à-dire importations comprises (2024).

## M3 — Croissance et émissions de l'UE depuis 30 ans (`NRJ-04`)

- Entrées :
  - `EUROSTAT-PIB-VOLUME` (PIB de l'UE à 27 en volume, euros chaînés de 2010, depuis 1995) ;
  - `EUROSTAT-GES` (émissions totales hors UTCATF, aviation internationale comprise : TOTX4_MEMO).
- Calculs : PIB 2025 / PIB 1995 − 1 ; émissions 2024 / émissions 1994 − 1, puis 2024 / 1990 − 1.

## M4 — Prix de l'électricité des entreprises (`NRJ-05`)

- Entrées :
  - `EUROSTAT-PRIX-ENTREPRISES` (consommateurs non résidentiels, €/kWh, semestriel), par tranche de consommation,
    hors TVA et taxes récupérables (X_VAT) ou toutes taxes comprises (I_TAX) ;
  - `EIA-PRIX-SECTEURS` (prix moyen par secteur aux États-Unis, en cents par kWh) ;
  - `EUROSTAT-CHANGE-USD` (taux de change moyen annuel).
- Calculs :
  - prix annuel = moyenne des deux semestres, × 1 000 pour passer en €/MWh ;
  - hausse = moyenne 2024 / moyenne 2021 − 1, par tranche ;
  - prix américain en €/MWh = cents/kWh × 10 / (dollars pour 1 €).
- Choix : pour une entreprise, la TVA est récupérable. Le prix pertinent est donc le prix hors TVA, comme le prix
  américain, qui n'inclut pas de TVA.

## M5 — Accise sur l'électricité (`NRJ-06`)

- Entrées :
  - `BOFIP-ACCISE-2026` : tarifs au 1er février 2026, majoration pour les zones non interconnectées comprise ;
  - `AN-QE16278-TICFE` : réponse du gouvernement publiée en juillet 2019, TICFE à 22,5 €/MWh pour les ménages ;
  - `STROMSTG-3` et `STROMSTG-9B` : loi allemande sur la taxe sur l'électricité, tarif de 20,50 €/MWh et
    allègement de 20 €/MWh pour l'industrie manufacturière et l'agriculture.
- Calculs : 30,85 / 22,5 − 1 ; 20,50 − 20 = 0,50 €/MWh.

## M6 — Charges de soutien aux renouvelables (`NRJ-07`)

- Entrées :
  - `CRE-CSPE-2026` : délibération 2025-180, qui donne le total des charges à compenser en 2026 et le tableau par
    filière (éolien terrestre : −3 422,6 M€ constatés pour 2023, 1 300,1 M€ prévus pour 2026) ;
  - `CRE-CSPE-2026-ANNEXE1` : tableau 4, coût d'achat unitaire de l'obligation d'achat (colonne « Eolien à terre » :
    97,5 €/MWh en 2024, 100,6 €/MWh prévus en 2026).
- Calcul : 1 300,1 M€ / 12,94 Md€.

## M7 — Gaz de schiste (`NRJ-08`)

- Entrées :
  - `EIA-GAZ-SCHISTE-2013` (U.S. Energy Information Administration, 2013) : ressources techniquement récupérables
    de 137 Tcf (1 000 milliards de pieds cubes) pour la France et 148 Tcf pour la Pologne ;
  - `EUROSTAT-GAZ` (consommation intérieure observée, millions de m³).
- Calculs : 137 × 28,3168 = milliards de m³ (1 pied³ = 0,0283168 m³) ; stock / consommation annuelle, pour 2019 et
  2024.

## M8 — DPE, PPE et réseau (`NRJ-09`, `NRJ-10`, `NRJ-11`)

- `AN-QE9713-DPE` : coefficient de l'électricité de 2,3 jusqu'en 2025, puis 1,9. Un coefficient de 2,3 compte
  1 kWh d'électricité comme 2,3 kWh d'énergie primaire, soit 130 % de plus.
- `PPE-2020` : « 14 réacteurs nucléaires seront arrêtés d'ici 2035 ».
- `CRE-CONSULTATION-SDDR` : 37 Md€ d'investissements de raccordement en mer sur 2025-2039 (22 GW), plus 10 Md€
  pour les mises en service à partir de 2040. Aucun calcul.
