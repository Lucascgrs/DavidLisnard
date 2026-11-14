# Méthode des calculs — thème 1, Dette, dépense publique et fiscalité

Tous les résultats sont produits par `calculer.py` à partir des fichiers de `brut/` (inscrits dans `sources.csv`),
et écrits dans `resultats.csv`. La colonne `methode` de ce fichier renvoie aux sections ci-dessous. Relancer
`python -m verification calculer 1` refait tout.

**Seule saisie manuelle** : les chiffres lus dans des PDF (budget de l'État, rapports du Sénat, du Haut-Commissariat
au plan, de Fipeco, de la DGFiP). Ils sont regroupés dans `LUS_DANS_LES_PDF` en tête de `calculer.py`, chacun avec
la phrase exacte du PDF. Avant tout calcul, le script vérifie que chaque phrase figure bien dans le texte du PDF.
Sinon il s'arrête.

**Conventions** : « UE à 27 » = les 27 États membres actuels (agrégats exclus des classements). « OCDE » = les 38
membres. Les rangs sont comptés du plus élevé au plus bas. Les montants sont en euros courants.

**Données révisées** : Eurostat et l'OCDE révisent leurs séries. Les chiffres ci-dessous sont ceux téléchargés le
14/11/2026 (Eurostat : mise à jour d'octobre 2026). Ils peuvent différer légèrement de ceux disponibles le jour où
Lisnard a parlé. Les verdicts en tiennent compte quand l'écart compte.

---

## M1 — Rang de la France pour la dépense publique (`DETTE-01`)

- Entrées : `EUROSTAT-GOV10A-MAIN` (na_item `TE`, unit `PC_GDP`, secteur S13) ; `FMI-FM-DEPENSES` (Fiscal Monitor,
  dépenses des administrations publiques, % du PIB, 210 pays).
- Calcul : on classe les pays par dépense publique en % du PIB pour chaque année et on lit le rang de la France.
  Trois périmètres : UE à 27 (Eurostat), monde (FMI, tous pays), OCDE (FMI restreint aux 38 membres).
- Choix : l'indicateur est celui que cite Lisnard (dépense publique totale rapportée au PIB). Le FMI est la seule
  source qui couvre le monde entier avec une méthode commune.

## M2 — Rang de la France pour les prélèvements obligatoires (`DETTE-02`)

- Entrées : `EUROSTAT-TAXAG` (na_item `D2_D5_D91_D61_M_D995` : impôts et cotisations sociales, y compris
  cotisations imputées, % du PIB) ; `OCDE-RECETTES-FISCALES` (catégorie `_T` : recettes fiscales totales, secteur S13,
  % du PIB) ; `FMI-FM-RECETTES` (recettes publiques totales).
- Calcul : classement par année, comme en M1.
- Choix : trois définitions coexistent. Celle de l'Insee (45,4 % en 2022, citée par Lisnard), celle d'Eurostat (qui
  inclut les cotisations imputées et donne un taux plus élevé), celle de l'OCDE (qui sert aux comparaisons
  internationales). Le FMI ne donne que les recettes publiques totales, qui comprennent des recettes non fiscales :
  ce n'est qu'un contrôle.

## M3 — Rapport entre les intérêts de la dette et le budget de la Justice (`DETTE-03`)

```latex
\text{rapport} = \frac{\text{charge d'interets}}{\text{credits de paiement de la mission Justice}}
```

- Numérateur, trois variantes :
  1. charge de la dette de l'État en comptabilité budgétaire (programme 117) : 58,0 Md€ en loi de finances 2026,
     61,6 Md€ en prévision révisée 2026 (`SENAT-EFE-PLF2027`) ; 51,4 Md€ au PLF 2024 (`PLF2024-DESTINATION`) ;
  2. intérêts payés par toutes les administrations publiques (État, Sécurité sociale, collectivités), en
     comptabilité nationale : année 2024 (`EUROSTAT-GOV10A-MAIN`, `D41PAY`) et somme des quatre derniers trimestres
     publiés, du 3e trimestre 2025 au 2e trimestre 2026 (`EUROSTAT-INTERETS-TRIM`), faute d'année 2026 complète.
- Dénominateur : crédits de paiement de la mission Justice **hors pensions**, tels que publiés dans `BUDGET-VERT-PLF2026`
  (exécution 2024 : 9,83 Md€ ; PLF 2026 : 10,63 Md€). Avec les cotisations de pension (PLF 2025 : 12,46 Md€ au lieu
  de 10,46 Md€, `PLF2025-DESTINATION`), le rapport baisse d'environ 15 %.
- Limite : les crédits Justice de la loi de finances 2026 votée n'ont pas été téléchargés ; on utilise ceux du PLF
  2026, qui en diffèrent peu (ordre de grandeur de 0,1 à 0,3 Md€).

## M4 — La charge de la dette, premier poste de l'État ? (`DETTE-04`)

- Entrées : `PAP2026-ENGAGEMENTS-FIN` (LFI 2025 : 54,207 Md€ ; PLF 2026 : 58,615 Md€) ; `SENAT-EFE-PLF2027` (LFI
  2026 : 58,0 Md€ ; révisé 2026 : 61,6 Md€ ; PLF 2027 : 71,9 Md€ ; Enseignement scolaire PLF 2027 : 65,5 Md€ ;
  Défense PLF 2027 : 63,4 Md€) ; `BUDGET-VERT-PLF2026` pour les missions Enseignement scolaire et Défense en 2025
  et 2026 (hors pensions) ; `EUROSTAT-GOV10A-MAIN` et `EUROSTAT-INTERETS-TRIM` pour les intérêts de toutes les
  administrations.
- Calcul : comparaison directe des montants, même périmètre (crédits de paiement hors pensions, convention reprise
  par le Sénat).

## M5 — Niveau de la dette (`DETTE-05`)

- Entrée : `EUROSTAT-DETTE-TRIM` (dette brute au sens de Maastricht, France, trimestriel, millions d'euros et % du
  PIB).
- Calcul : lecture du trimestre correspondant à la date de la déclaration (avril 2026 : dernier trimestre publié =
  3e trimestre 2025 ; juillet 2026 : 1er trimestre 2026).

## M6 — Croissance de la dette comparée à celle du PIB (`DETTE-06`)

- Entrées : `EUROSTAT-EDP-DETTE` (dette annuelle en millions d'euros), `EUROSTAT-PIB` (PIB aux prix courants).
- Calculs :
  - hausse de la dette 2017 → 2024 = dette 2024 / dette 2017 − 1 (2024 est la dernière année connue en avril 2025) ;
  - hausse du PIB 2017 → 2024, même formule ;
  - « 40 % plus vite » sur dix ans : rapport (croissance de la dette) / (croissance du PIB), sur 2015 → 2025 et
    2016 → 2025. Un rapport de 1,4 signifierait « 40 % plus vite ».

## M7 — Dette si la France avait suivi la zone euro depuis 2017 (`DETTE-07`)

```latex
\text{dette}_{cf} = \left(\text{ratio}_{FR,2017} + \Delta\text{ratio}_{ZE,2017\to T}\right) \times \text{PIB}_{FR,T}
```

- On garde le PIB français réel de l'année T et on suppose que le ratio dette/PIB de la France a varié comme celui
  de la zone euro à 20 depuis 2017. L'écart avec la dette réelle donne la « dette en moins ».
- Intérêts : on suppose le taux moyen inchangé, donc des intérêts proportionnels à l'encours. Baisse des intérêts =
  dette en moins / dette réelle. C'est une borne haute (une dette plus faible aurait aussi pu être financée à un
  taux un peu plus bas, mais pas au point de diviser la charge par deux).
- Entrées : `EUROSTAT-EDP-DETTE` (% du PIB, France et EA20), `EUROSTAT-PIB`.

## M8 — Détention par les non-résidents et refinancement (`DETTE-08`)

- Entrée : `BDF-NONRESIDENTS` (Banque de France, part de la dette négociable de l'État détenue par les
  non-résidents, trimestriel).
- Refinancement : amortissements de titres à moyen et long terme prévus en 2026 (175,8 Md€) / encours de la dette
  négociable fin 2024 (2 601,6 Md€), lus dans `PAP2026-ENGAGEMENTS-FIN`. Les titres courts (BTF, environ 200 Md€ à
  3-12 mois) sont refinancés plusieurs fois par an : ils ne sont pas comptés ici.
- Non vérifié par fichier : la « maturité moyenne de huit ans » (l'Agence France Trésor publie 8 ans et 184 jours
  fin 2025, mais son site bloque les téléchargements automatiques) et la part « hors zone euro » (27 %), qui n'est
  pas publiée en données ouvertes.

## M9 — Déficit et recettes (`DETTE-09`)

- Entrées : `EUROSTAT-GOV10A-MAIN` (B9, TR) ; `PAP2026-ENGAGEMENTS-FIN` (déficit budgétaire de l'État : 155,9 Md€ en
  2024, 130,5 Md€ révisé 2025) ; `VM2026-TOME1` (recettes nettes de l'État : 348,9 Md€ en 2024, 377,0 Md€ révisé
  2025).
- Calcul : déficit / recettes, pour toutes les administrations et pour l'État seul.

## M10 — Dépenses sociales (`DETTE-10`)

- Entrées : `EUROSTAT-PROTSOC-FONC` (% du PIB), `EUROSTAT-PROTSOC-TYPE` (millions d'euros et standard de pouvoir
  d'achat par habitant), `OCDE-SOCX` (dépenses sociales publiques, % du PIB et dollars PPA par habitant).
- Calculs : rang de la France en % du PIB (UE, OCDE) et **par habitant** (Europe : UE + Suisse, Norvège, Islande ;
  OCDE). « Par rapport à la population » signifie par habitant : c'est le classement retenu pour juger la formule.
- Montant : total des dépenses de protection sociale 2024 (prestations + frais de gestion).

## M11 — Aides publiques aux entreprises (`DETTE-11`)

- Entrées : `SENAT-AIDES-2025-SYN`, `HCSP-AIDES-2025`, `CLERSE-AIDES-2022`. Aucun calcul : on aligne les
  estimations publiées, de la plus étroite à la plus large, avec leur périmètre.
- « 40 Md€ au début des années 2000 » : le Clersé écrit que ces aides sont passées « de 3 % du PIB environ » au
  début des années 2000 à 6,44 % en 2019 ; 3 % du PIB de 2000 (environ 1 480 Md€) font environ 44 Md€.

## M12 — Prélèvements sur les entreprises (`DETTE-12`)

- Entrées : `FIPECO-PO-ENTREPRISES-2022` et `FIPECO-PO-ENTREPRISES-2019` (impôts sur la production et sur les
  bénéfices + cotisations patronales des sociétés non financières, en % du PIB) ; `IFRAP-148MD` (origine du « 13,2 %
  contre 7,3 % »).
- Calcul : écart France - Allemagne. Fipeco ne publie pas de moyenne de la zone euro ; l'iFRAP compare à « ses
  concurrents » sans préciser le calcul.

## M13 — Impôts de production (`DETTE-13`)

- Entrées : `EUROSTAT-TAXAG` (`D29`, autres impôts sur la production, tous payeurs, % du PIB) ; `FIPECO-IMPOTS-PRODUCTION-2022`
  (impôts sur la production payés par les seules sociétés : 3,3 % du PIB contre 1,5 % dans la zone euro en 2022).
- Calcul : médiane des 27 pays de l'UE et rang de la France. La Suède est première parce qu'elle classe une grande
  taxe sur les salaires dans cette catégorie.

## M14 — Coin fiscal et social sur le salaire moyen (`DETTE-14`)

- Entrée : `OCDE-IMPOTS-SALAIRES` (mesure `AV_TW`, célibataire sans enfant au salaire moyen, % du coût du travail).
- Calcul : rang parmi les 38 pays de l'OCDE ; moyennes OCDE (`OECD_REP`) et des 22 pays de l'UE membres de
  l'OCDE (`EU22OECD`).

## M15 — Concentration de l'impôt sur le revenu (`DETTE-15`)

- Entrées : `DGFIP-IR-2023-PDF` (revenus 2023 : 45 % de foyers imposés, les 10 % les plus aisés paient 76 % de
  l'impôt net) ; `DGFIP-IR-2024` (tableau 4, impôt net moyen par dixième de revenu, revenus 2024).
- Calcul pour 2024 : les dixièmes contiennent le même nombre de foyers, donc la part du dernier dixième = sa moyenne
  / somme des dix moyennes.
- Remarque : la DGFiP compte des foyers fiscaux, pas des ménages.

## M16 — Niches fiscales (`DETTE-16`)

- Entrées : `VM2025-TOME2` (474 dépenses fiscales, 85,1 Md€ en 2025, dont 42,07 Md€ sur l'impôt sur le revenu) ;
  `VM2026-TOME1` (impôt net sur le revenu en LFI 2025 : 94,5 Md€) ; `VM2026-TOME2` (465 dépenses fiscales en 2026).
- Calcul : 42,07 / 94,5.

## M17 — Droits de succession et de donation (`DETTE-17`)

- Entrées : `OCDE-RECETTES-FISCALES` (catégorie 4300, impôts sur les successions, héritages et donations, % du PIB) ;
  `EUROSTAT-PIB` ; `EUROSTAT-TAXAG` (`D91`) pour contrôle.
- Calcul : montant par pays = taux OCDE × PIB Eurostat en euros, pour les 22 pays de l'UE membres de l'OCDE ;
  part de la France = montant France / somme. Les 5 pays de l'UE hors OCDE (Bulgarie, Croatie, Chypre, Malte,
  Roumanie) en sont exclus : leurs droits de succession sont très faibles ou inexistants. Le contrôle par `D91`
  (tous les impôts en capital, UE à 27) donne une part un peu plus basse.

## M18 — Taxes sur les carburants (`DETTE-18`)

- Entrée : `CE-BULLETIN-PETROLIER` (prix hebdomadaires avec et sans taxes, par pays, essence SP95 et gazole).
- Calcul : part des taxes = 1 − prix hors taxes / prix toutes taxes, pour la semaine du 4 mai 2026 (la plus proche de
  la déclaration du 7 mai) et en moyenne sur 2025 ; rang dans l'UE.
- La part des taxes baisse quand le pétrole monte (l'accise est un montant fixe par litre) : il faut lire les deux
  dates.

## M19 — Imposition cumulée du capital (`DETTE-19`)

- Entrées, textes en vigueur : `SP-IMPOT-SOCIETES` (IS à 25 %), `BOFIP-CONTRIBUTION-EXCEPTIONNELLE` (20,6 % ou
  41,2 % de l'IS selon le chiffre d'affaires, exercices 2025 et 2026), `SP-PRELEVEMENTS-SOCIAUX` (prélèvements
  sociaux 18,6 %, flat tax 31,4 % en 2026), `SP-CEHR-CDHR` (contribution exceptionnelle de 3 ou 4 % ; contribution
  différentielle assurant 20 % d'imposition minimale des très hauts revenus). Contribution sociale sur l'IS de 3,3 %
  au-delà de 763 000 € d'IS (article 235 ter ZC du code général des impôts), appliquée en borne haute.

```latex
\text{taux cumule} = 1 - (1 - t_{IS}) \times (1 - t_{dividende})
```

- Taux d'IS : 25 % × 1,033 = 25,8 % (entreprise ordinaire), × 1,412 = 36,5 % (chiffre d'affaires ≥ 3 Md€).
- Taux sur le dividende : 31,4 % (flat tax), 35,4 % (+ contribution de 4 %), 38,6 % (impôt porté à 20 % par la
  contribution différentielle + 18,6 % de prélèvements sociaux).
- Il s'agit de taux légaux marginaux, pas de taux effectifs moyens (qui tiennent compte des déductions).

## M20 — Le plan de 200 à 300 Md€ d'économies (`DETTE-20`) — ESTIMATION

- Entrées : `EUROSTAT-GOV10A-MAIN` (dépense 2025 : 1 714 Md€ ; 57,3 % du PIB), `EUROSTAT-PIB`.
- Calcul : économies / dépense 2025 ; économies / PIB 2025 ; dépense après économies = 57,3 % − économies / PIB, puis
  nouveau rang dans l'UE en laissant les autres pays à leur niveau de 2025.
- **Estimation, non fiable à 100 %** : à PIB inchangé, sans effet des économies sur la croissance ni sur les
  recettes, et sans tenir compte de l'évolution des autres pays d'ici 2032.

## M21 — Le partage 120 / 40 / 40 (`DETTE-21`) — ESTIMATION

- Entrées : `EUROSTAT-SALARIES` (emploi salarié, comptes nationaux, 27,1 millions en 2025) ; C3S (4,3 Md€ en 2022,
  `FIPECO-IMPOTS-PRODUCTION-2022`) et CVAE (part de l'État 2025 : 4,069 Md€, `VM2026-TOME1`).
- Calcul : 120 Md€ / nombre de salariés / 12 mois. Première année : 60 % de 80 Md€, même formule.
- **Estimation, non fiable à 100 %** : suppose que toute la baisse de cotisations se retrouve en salaire net et se
  répartit également entre salariés. En réalité elle dépendrait des cotisations visées (patronales ou salariales),
  des niveaux de salaire et des négociations.

## M22 — Ramener les prélèvements à la moyenne de la zone euro (`DETTE-22`) — ESTIMATION

- Entrées : `EUROSTAT-TAXAG` (France 46,0 %, zone euro 41,3 % en 2025), `EUROSTAT-PIB`.
- Calcul : (taux France − taux zone euro) × PIB 2025.
- **Estimation, non fiable à 100 %** : à PIB inchangé ; avec la définition de l'OCDE l'écart serait différent.
