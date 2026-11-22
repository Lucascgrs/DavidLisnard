# Méthode des calculs — Mélenchon, thème 1, Dette, dépense publique et fiscalité

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les documents sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le 20/11/2026 ;
la note du Haut-commissariat au Plan et les pages sur l'impôt sur les sociétés sont reprises du dossier de David
Lisnard.

## M1 — Les aides aux entreprises (`DETTE-01`)

- Entrée : `HCSP-AIDES-2025` (note n° 157, juillet 2025, qui résume les deux estimations de la commission d'enquête du
  Sénat : 211 Md€ et 108 Md€ pour 2023, et leurs périmètres). Aucun calcul.

## M2 — Le déficit (`DETTE-02`)

- Entrée : `EUROSTAT-DEFICITS` (besoin de financement, comptabilité nationale, État et ensemble des administrations
  publiques, 2024 et 2025).

## M3 — Le patrimoine public (`DETTE-03`)

- Entrées : `EUROSTAT-PATRIMOINE-NF` (actifs non financiers produits et non produits) ; `EUROSTAT-PATRIMOINE-FIN`
  (actifs et passifs financiers, non consolidés) ; `EUROSTAT-POPULATION` (population au 1er janvier 2026).
- Calcul : patrimoine net = actifs non financiers + actifs financiers − passifs, fin 2025 ; puis par habitant. Le
  bilan de l'État seul n'est pas diffusé par Eurostat.

## M4 — Les pays endettés à plus de 100 % (`DETTE-04`)

- Entrées : `EUROSTAT-DETTE-PAYS` (dette au sens de Maastricht, 2025) ; `EUROSTAT-PIB-PAYS-2025`.
- Calcul : pays de l'UE au-dessus de 100 % du PIB ; somme de leurs PIB rapportée à celui de l'UE et de la zone euro.

## M5 — La Grèce (`DETTE-05`)

- Entrée : `EUROSTAT-DETTE-PAYS` (dette et solde en % du PIB, 2008, 2009, 2010, 2025).

## M6 — L'impôt sur les sociétés (`DETTE-06`)

- Entrées : `SP-IMPOT-SOCIETES` (taux normal de 25 %) ; `BOFIP-CONTRIBUTION-EXCEPTIONNELLE` (41,2 % de l'impôt dû
  pour les entreprises de plus de 3 Md€ de chiffre d'affaires). Taux facial = 25 × (1 + 0,412).

## M7 — Le barème de l'impôt sur le revenu (`DETTE-07`)

- Entrée : `SP-BAREME-IR` (barème applicable aux revenus de 2025 : cinq tranches).
