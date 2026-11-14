# Méthode des calculs — thème 10, Logement et urbanisme

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF sont dans `LUS_DANS_LES_PDF`, avec la phrase exacte vérifiée. Données téléchargées le
14/11/2026. Graphique : `graphiques/logements_commences.png`.

## M1 — Logements commencés et population (`LOG-01`)

- Entrées :
  - `SDES-LOGEMENTS-MENSUEL` : logements commencés par mois, série brute « Tous Logements », France hors Mayotte,
    données estimées (Sitadel), de janvier 2002 à septembre 2026 ;
  - `CREDOC-1986-CONSTRUCTION` : CRÉDOC, *Consommation*, 1986, pour les années 1970 (« de 500 000 en 1971 », « 556
    000 logements » en 1973, niveau repassé sous 500 000 « en 1976 ») ;
  - `EUROSTAT-POPULATION` : population au 1er janvier, France métropolitaine (série FX, jusqu'en 2013) et France
    entière (FR, depuis 1982).
- Calculs :
  - sommes annuelles des 12 mois (années complètes seulement) ;
  - somme glissante des 12 mois connus avant l'audition du 22/10/2025 (octobre 2024 à septembre 2025) et des 12
    derniers mois ;
  - hausse de la population : FX 2013 − FX 1974, puis FR 2025 − FX 1974 (y compris les DOM, 1,9 million en 2013
    d'après FR − FX) ;
  - logements commencés pour 1 000 habitants = logements / population × 1 000. Pour 1974, 500 000 est une borne
    basse, car le nombre réel dépassait ce seuil.
- Limites :
  - les données SDES « estimées » sont révisées, et un chiffre cité en 2022 peut différer de la série actuelle ;
  - aucune série officielle téléchargeable avant 2000 n'a été trouvée, d'où le recours au CRÉDOC.

## M2 — Dépenses publiques de logement (`LOG-02`)

- Entrées :
  - `EUROSTAT-COFOG-LOGEMENT` : dépenses des administrations publiques (S13) par fonction. On retient GF0601
    (développement du logement) et GF1006 (logement, au titre de la protection sociale : allocations), ainsi que
    GF06 (logement et équipements collectifs au sens large) ;
  - `EUROSTAT-PROTSOC-LOGEMENT` : prestations sociales de logement (SESPROS, fonction HOU).
- Calculs :
  - « dépenses publiques de logement » = GF0601 + GF1006, en % du PIB (deux valeurs arrondies à 0,1 point par
    Eurostat, d'où une incertitude de ± 0,1 point), pour la France et l'UE à 27, en 2019, 2021 et 2024 ;
  - montant 2021 en Md€ (MIO_EUR / 1 000) ;
  - rapport France / UE des prestations de logement.
- Les 40 Md€ de Lisnard correspondent plutôt au « compte du logement » (aides publiques, y compris les dépenses
  fiscales), qui n'a pas été téléchargé.

## M3 — Fiscalité immobilière (`LOG-03`)

- Entrée : `OCDE-RECETTES-IMMOBILIER` (statistiques des recettes publiques, ensemble des administrations) :
  - recettes fiscales totales (_T) ;
  - impôts sur le patrimoine (4000) ;
  - impôts récurrents sur la propriété immobilière (4100 : taxes foncière et d'habitation) ;
  - impôts sur les transactions mobilières et immobilières (4400 : droits de mutation).
- Calculs : 4100 / total, puis (4100 + 4400) / total, en %, pour la France et la moyenne non pondérée de l'OCDE
  (OECD_REP), en 2021 et 2023.
- Limite : 4400 contient aussi des taxes sur les transactions financières. Le périmètre « fiscalité liée au
  logement » de Lisnard n'est pas défini.
