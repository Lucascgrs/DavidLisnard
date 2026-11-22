# Méthode des calculs — thème 3, Immigration, islamisme et identité

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans des PDF sont recopiés dans `LUS_DANS_LES_PDF` avec la phrase exacte, vérifiée avant tout calcul.
Données téléchargées le 14/11/2026.

Le site statistique de la direction générale des étrangers en France refuse les téléchargements automatiques. Les
titres de séjour et les éloignements viennent donc d'Eurostat, qui publie les données transmises par la France.
Le champ diffère un peu des publications françaises : premiers titres d'au moins trois mois, sans les mineurs.

## M1 — Premiers titres de séjour par motif (`IMMI-01`)

- Entrée : `EUROSTAT-PREMIERS-TITRES` (migr_resfirst, France, ressortissants de pays tiers, toutes durées ≥ 3 mois,
  motifs : famille, études, activité rémunérée, autres).
- Calcul : part du motif « activité rémunérée » (EMP) dans le total, par année. Le motif « autres » comprend la
  protection internationale (réfugiés), les titres humanitaires et divers.

## M2 — Diviser par huit (`IMMI-02`) — ESTIMATION

- Calcul : total 2025 / 8 ; comparaison avec la somme des titres familiaux et « autres » (largement fondés sur des
  droits : vie familiale, asile).
- **Estimation, non fiable à 100 %** : à motifs constants ; ne tient pas compte des effets juridiques (directives
  européennes, article 8 de la CEDH, convention de Genève).

## M3 — Exécution des obligations de quitter le territoire (`IMMI-03`)

```latex
\text{taux d'execution} = \frac{\text{ressortissants renvoyes (migr\_eirtn)}}{\text{ressortissants ayant recu l'ordre de partir (migr\_eiord)}}
```

- Entrées : `EUROSTAT-OQTF`, `EUROSTAT-RETOURS` (France, UE à 27). Calcul pour la France, l'UE à 27 et l'UE hors
  France (UE − France), par année. Ce ratio rapporte les départs d'une année aux décisions de la même année : c'est
  l'indicateur utilisé par la Commission européenne, approximatif car un départ peut suivre une décision antérieure.
- Contrôle : `CC-IMMIGRATION-IRREGULIERE-2024` (« autour de 10 % » des OQTF exécutées).

## M4 — Aide médicale de l'État (`IMMI-04`)

- Entrée : `SENAT-SANTE-PLF2026` (dépenses réelles 2024 : 1 387 M€, dont 1 256 M€ pour l'AME de droit commun ;
  465 208 bénéficiaires fin 2024 ; +70 % de dépenses en dix ans).
- Économie maximale d'une suppression = dépense de l'AME de droit commun. **Estimation, non fiable à 100 %** : borne
  haute, sans le coût de l'aide d'urgence de remplacement ni le report de soins vers l'hôpital.

## M5 — Sondage Ifop (`IMMI-05`)

- Entrée : `IFOP-ISLAM-2025` (présentation des résultats). Aucun calcul : vérification de la citation, de la taille
  d'échantillon (1 005 musulmans) et de la question. Marge d'erreur indicative pour un échantillon de 1 000 : ±3
  points autour de 38 %.

## M6 — Naissances selon la nationalité des parents (`IMMI-06`)

- Entrées : `INSEE-NAISSANCES-NATIONALITE` (figure 1, 1998-2025) ; `EUROSTAT-NAISSANCES` (naissances vivantes).
- Calculs : évolution sur vingt ans des naissances « deux parents français » et « au moins un parent étranger » (un
  parent étranger + deux parents étrangers), pour plusieurs fenêtres (1998-2018, 2002-2022, 2003-2023) ; baisse des
  naissances 2010 → 2025.
- Rupture : depuis 2023, le « second parent » peut être la mère n'ayant pas accouché (Insee).
