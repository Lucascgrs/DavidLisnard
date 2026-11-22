# Méthode des calculs — thème 7, Santé et hôpital

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Données
téléchargées le 14/11/2026.

## M1 — « 87 % du territoire en désert médical » (`SANTE-01`)

- Entrée : `DREES-APL-GENERALISTES` (feuille « APL 2024 » : accessibilité potentielle localisée aux médecins
  généralistes, en consultations accessibles par an et par habitant, et population de chaque commune) ;
  `DREES-APL-LISEZMOI` (méthode).
- Calculs : part de la population et part des communes dont l'APL est inférieure à 2,5 (seuil de sous-densité
  retenu par la DREES) et à 4 (seuil plus large).
- Le chiffre de 87 % correspond au zonage des ARS (zones d'intervention prioritaire et d'action complémentaire), qui
  sert à distribuer les aides à l'installation. Il n'a pas été trouvé en fichier national.

## M2 — Personnel hospitalier non soignant (`SANTE-02`)

- Entrée : `DREES-EFFECTIFS-HOSPITALIERS` (effectifs salariés par profession détaillée, public et privé, dernière
  année 2024).
- Calcul : (filière administrative + « autres non soignants ») / total des salariés, médecins et internes compris.
  « Autres non soignants » regroupe les personnels techniques, ouvriers, médico-techniques non soignants et
  socio-éducatifs.

## M3 — Dépense de santé (`SANTE-03`)

- Entrée : `EUROSTAT-DEPENSE-SANTE` (dépense courante de santé, tous financeurs, % du PIB, standard de pouvoir
  d'achat par habitant, millions d'euros ; année 2024, la dernière renseignée pour la plupart des pays).
- Calculs : rangs dans l'UE à 27 ; écart avec la moyenne de l'UE en euros = (taux France − taux UE) × PIB, le PIB
  étant déduit de la dépense en euros divisée par son taux.

## M4 — Médecins et diplômés (`SANTE-04`)

- Entrées : `OCDE-MEDECINS` (médecins en exercice pour 1 000 habitants), `OCDE-DIPLOMES` (diplômés en médecine pour
  100 000 habitants).
- Calcul : dernière année disponible pour la France et rang parmi les pays de l'OCDE renseignés la même année.
- La série française fait un saut de 3,16 (2019) à 3,74 médecins pour 1 000 habitants (2020). Une hausse de 18 % en
  un an n'est pas plausible : c'est très probablement une rupture de méthode, à confirmer dans les notes de l'OCDE.
