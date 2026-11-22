# Méthode des calculs — Mélenchon, thème 6, Économie, travail et entreprises

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les documents sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le 20/11/2026.

## M1 — Salaires minimums en dix ans (`ECO-01`)

- Entrée : `EUROSTAT-SMIC-PAYS` (salaire minimum mensuel brut en euros, ramené par Eurostat sur 12 mois, ce qui
  compte les 14 mois espagnols et portugais).
- Calcul : hausse entre le 1er semestre 2016 et le 1er semestre 2026, pour chaque pays ; pour la France, aussi
  entre le 2e semestre 2015 et le 2e semestre 2025. Hausses nominales, sans tenir compte de l'inflation.

## M2 — La croissance espagnole (`ECO-02`)

- Entrée : `EUROSTAT-CROISSANCE` (PIB en volume, variation annuelle). Classement des 27 pays de l'UE en 2024 et 2025.

## M3 — Chômeurs par emploi vacant (`ECO-03`)

- Entrées : `EUROSTAT-CHOMEURS` (chômeurs au sens du BIT, 15-74 ans, données corrigées) ; `EUROSTAT-EMPLOIS-VACANTS`
  (emplois vacants, enquête de la Dares, toutes tailles d'entreprises et entreprises de 10 salariés ou plus).
- Calcul : moyenne des quatre derniers trimestres communs, puis chômeurs / emplois vacants. Le ratio dépend des
  définitions : les inscrits à France Travail sont plus nombreux que les chômeurs au sens du BIT, et les offres
  déposées à France Travail ne sont pas les emplois vacants.

## M4 — Embauches en CDD (`ECO-04`)

- Entrée : `URSSAF-DPAE` (déclarations préalables à l'embauche, hors intérim, par nature de contrat).
- Calcul : part des CDD (moins et plus d'un mois) et part des CDD de moins d'un mois dans le total, par année. Une
  déclaration n'est pas une personne : un même salarié peut signer de nombreux CDD courts dans l'année.

## M5 — Production industrielle (`ECO-05`)

- Entrée : `EUROSTAT-PROD-INDUS` (indice 2021 = 100, corrigé des jours ouvrables). Calcul : 2025 / 2019.

## M6 — Classement Doing Business (`ECO-06`)

- Entrée : `BM-DOING-BUSINESS-2019` (rang de facilité à faire des affaires, données 2019, édition 2020, la dernière).
  Calcul : rang de la France / nombre d'économies classées.

## M7 — Accidents du travail mortels en Europe (`ECO-07`)

- Entrée : `EUROSTAT-AT-MORTELS` (nombre et taux standardisé pour 100 000 travailleurs, tous secteurs). Classement des
  27 pays de l'UE pour les deux dernières années.

## M8 — Les décès liés au travail (`ECO-08`)

- Entrée : `REPSS-ATMP-2026` (2024 : 764 accidents du travail mortels, 316 accidents de trajet mortels, 215 maladies
  professionnelles mortelles). Calcul : sommes selon le périmètre.

## M9 — Prix de l'alimentation (`ECO-09`)

- Entrée : `EUROSTAT-IPCH` (indice des prix à la consommation harmonisé, base 2025 = 100, produits alimentaires et
  boissons non alcoolisées, et ensemble). Calcul : hausse jusqu'à août 2026, dernier mois connu le jour du discours,
  depuis mai 2017, janvier 2021 et janvier 2022 ; hausse de l'ensemble des prix sur un an.

## M10 — Consommation et salaires dans le PIB (`ECO-10`)

- Entrée : `EUROSTAT-PIB-EMPLOIS` (euros courants, 2025). Calcul : consommation des ménages, consommation des ménages
  et des institutions sans but lucratif, rémunération des salariés, rapportées au PIB.

## M11 — Densité de robots (`ECO-11`)

- Entrée : `IFR-DENSITE-2025` (communiqué de la fédération professionnelle des robots : Allemagne 449, UE 231). Le
  chiffre français n'est pas dans le communiqué.

## M12 — SMIC à 1 700 € net (`ECO-12`) — ESTIMATION

- Entrée : `EUROSTAT-SMIC-PAYS` (SMIC brut, 1er semestre 2026). Le net est estimé en retirant 20,95 % de
  cotisations salariales (taux moyen au niveau du SMIC). **Estimation, non fiable à 100 %.**
