# Méthode des calculs — thème 13, Europe et international

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le 14/11/2026.
Graphique : `graphiques/pib_par_habitant_spa.png`.

## M1 — PIB par habitant par rapport à l'UE (`EUR-01`, `EUR-02`)

- Entrée : `EUROSTAT-PIB-HAB-SPA` : PIB par habitant en standards de pouvoir d'achat (SPA), indice UE à 27 = 100,
  de 1995 à 2024.
- Calculs :
  - minimum de l'indice français de 1995 à 2021 ;
  - valeurs de 2022 à 2024 ;
  - écart France − Italie, en points.
- Limite : Eurostat arrondit l'indice à l'unité et le révise chaque année. Un écart d'un point entre deux pays
  n'est pas significatif.

## M2 — Rang mondial de la France (`EUR-03`)

- Entrées :
  - `FMI-PIB-HAB-DOLLARS` (PIB par habitant en dollars courants) et `FMI-PIB-HAB-PPA` (en parité de pouvoir
    d'achat), base WEO ;
  - `FMI-POPULATION` ;
  - `FMI-PAYS` (liste des pays, qui sert à exclure les regroupements régionaux).
- Calcul : on classe les pays par PIB par habitant décroissant et on lit le rang de la France en 1980, 1995, 2024
  et 2025. Deux classements : tous les pays, puis seulement les pays de plus d'un million d'habitants (le classement
  « tous pays » place devant la France des micro-États comme le Luxembourg, Macao ou Saint-Marin).
- Limite : le nombre de pays classés augmente avec le temps (137 en 1980, 195 en 2025). Une partie du recul de rang
  tient donc à l'entrée de nouveaux pays dans les données.

## M3 — Rapport Draghi (`EUR-04`)

- Entrée : `DRAGHI-2024-A`, partie A du rapport :
  - « Around 70% of the gap in per capita GDP with US at PPP is explained by lower productivity in the EU » ;
  - productivité du travail de l'UE à 95 % du niveau américain en 1995, puis « below 80% ».
- Aucun calcul.

## M4 — Dépenses de défense (`EUR-05`)

- Entrées :
  - `OTAN-DEPENSES-2025` : dépenses de défense de la France en millions d'euros courants (tableau 1) et en % du PIB
    (tableau 3), estimations pour 2024 et 2025 ;
  - `EUROSTAT-PIB-COURANT` : PIB de la France en 2025.
- Calculs :
  - 57 / PIB 2025 ;
  - coût de la hausse de 2,06 % à 3 % (et à 3,5 %) = écart de taux × PIB 2025.
- Limite : la définition de l'OTAN, qui inclut notamment les pensions et la gendarmerie en opérations, donne un
  montant plus élevé que le budget des armées de la loi de finances.

## M5 — Commerce de l'UE avec la Chine (`EUR-06`)

- Entrée : `COMEXT-UE-CHINE` : importations (flux 1) et exportations (flux 2) de l'UE avec la Chine, tous produits,
  de 2010 à 2025.
- Calculs : solde = exportations − importations ; année du solde le plus négatif.
