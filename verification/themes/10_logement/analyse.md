# Logement et urbanisme : analyse et verdicts

**En bref.** Sur le logement, Lisnard est globalement juste.

- La construction s'est effondrée : 265 000 logements commencés en 2024, le plus bas depuis le début de la série
  (2002), contre plus de 500 000 par an de 1971 à 1975.
- La population a même augmenté davantage qu'il ne le dit.
- La France dépense environ deux fois plus que la moyenne européenne pour le logement, et sa fiscalité immobilière
  pèse plus lourd que la moyenne de l'OCDE.
- Il a tendance à grossir l'écart avec l'étranger. Une de ses versions de 2022 donnait un chiffre de 2021 que les
  données actuelles ne confirment pas.

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Exact | 1 | LOG-01 |
| Plutôt exact | 2 | LOG-02, 03 |
| Invérifiable | 1 | LOG-04 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Graphique :
`calculs/graphiques/logements_commences.png`. Fichiers : `brut/`, `sources.csv`. Données du 14/11/2026.

---

## LOG-01 — « Aujourd'hui, on a 10 millions d'habitants de plus et on est en dessous de 300 000 logements par an » (audition à l'Assemblée, 22/10/2025), après « quasiment 500 000 logements neufs par an » en 1974

**Verdict : exact.** Confiance : forte.

- **Au moment de l'audition**, le SDES compte 258 600 logements commencés sur les 12 mois connus (octobre 2024 à
  septembre 2025). C'est aussi le chiffre qu'il citait en mai 2025 (« 258.500 sur un an »).
  - Sur les années civiles : 264 700 en 2024, le plus bas depuis 2002, et 268 400 en 2025. [M1]
  - Depuis, la construction remonte : 315 000 sur les 12 mois jusqu'à septembre 2026. Ces données sont encore
    estimées et seront révisées.
- **En 1974** : d'après le CRÉDOC (1986), les mises en chantier ont dépassé 500 000 de 1971 à 1975, avec un pic de
  556 000 en 1973, et ne sont repassées sous 500 000 qu'en 1976. « Quasiment 500 000 » est donc même un peu en
  dessous de la réalité. Une série officielle téléchargeable pour ces années n'a pas été trouvée.
- **La population** a augmenté davantage que « 10 millions » :
  - +11,4 millions en métropole entre 1974 et 2013, date où s'arrête la série métropolitaine d'Eurostat ;
  - +16,6 millions entre la métropole de 1974 et la France entière de 2025, DOM compris (1,9 million en 2013).
- Rapporté à la population, on construit 2,5 fois moins qu'en 1974 : 3,9 logements commencés pour 1 000 habitants
  en 2025, contre au moins 9,6 en 1974.
- **Réserve sur sa version de 2022** (« 437 000 en 2017 […] jusqu'à 345 000 en 2021 ») :
  - 2017 est juste : 433 900 dans la série actuelle ;
  - 2021 ne l'est pas : 422 300, une année de rebond après 2020, et non le point bas d'une baisse continue. La
    série a pu être révisée depuis 2022, mais aucune version publiée à 345 000 n'a été retrouvée.

## LOG-02 — « 40 milliards d'euros de dépenses publiques […] consacrés en France à la politique du logement (soit 1,2 % du PIB contre 0,5 % en moyenne européenne selon les données Eurostat) » (22/12/2022)

**Verdict : plutôt exact.** Confiance : moyenne.

- On retient les dépenses publiques consacrées au logement au sens d'Eurostat : développement du logement
  (GF0601) plus allocations logement (GF1006). [M2]
  - **2019** : France 1,1 % du PIB, UE 0,5 %.
  - **2021** : France 1,2 %, UE 0,8 %.
  - **2024** : France 1,0 %, UE 0,5 %.
- Le rapport d'environ 2 pour 1 est donc juste en temps normal. Mais le couple « 1,2 contre 0,5 » prend le chiffre
  français de 2021 et le chiffre européen d'une autre année. En 2021-2023, la moyenne européenne était
  temporairement plus haute (0,8 à 0,9 %).
- Pour les seules allocations logement : 0,63 % du PIB en France contre 0,36 % dans l'UE en 2021, soit 1,8 fois
  plus.
- Les 40 Md€ ne correspondent pas aux dépenses d'Eurostat, qui donnent 30,5 Md€ en 2021. Ils correspondent plutôt
  au « compte du logement » du ministère, qui ajoute les avantages fiscaux. Ce compte n'a pas été téléchargé ici.
  Les deux chiffres de sa phrase viennent donc de sources différentes.

## LOG-03 — « La fiscalité liée au logement, qui pèse en France 6 % des prélèvements obligatoires contre 3,3 % en moyenne dans l'OCDE » (22/12/2022)

**Verdict : plutôt exact.** Confiance : moyenne.

- La France est bien nettement au-dessus de la moyenne de l'OCDE. L'écart dépend du périmètre retenu. [M3]
  - **Taxes foncières et d'habitation** (impôts récurrents sur l'immobilier) : 4,6 % des recettes fiscales en 2021
    contre 3,0 % dans l'OCDE ; 4,3 % contre 2,8 % en 2023.
  - **En ajoutant les droits de mutation** (impôts sur les transactions) : 6,8 % contre 4,4 % en 2021 ; 6,0 % contre
    3,9 % en 2023.
- Son « 6 % » correspond au périmètre large. Mais sur ce même périmètre, la moyenne de l'OCDE est d'environ 4 %, et
  non 3,3 %. Il compare un périmètre large pour la France à un périmètre plus étroit pour l'OCDE.
- L'écart réel est d'environ 1,5 fois, et non 1,8 fois.

## LOG-04 — « Plus des deux tiers des Français sont aujourd'hui en théorie éligibles au logement social » (programme)

**Verdict : invérifiable** avec les données téléchargées ici.

- Pour le vérifier, il faut comparer la distribution des revenus fiscaux de référence des ménages, selon leur
  taille et leur zone, aux plafonds de ressources du logement social. Ce croisement n'a pas été fait.
- Un ordre de grandeur de ce type (60 à 70 % des ménages sous les plafonds du logement social standard) circule
  dans le secteur. Il n'a pas été vérifié ici auprès d'une source statistique publique.
- La phrase suivante du programme, « les bailleurs sociaux préfèrent des locataires plus solvables », relève de
  l'appréciation.

---

## Ce qui reste à faire ou à vérifier

- [ ] Télécharger le « compte du logement » du SDES (aides publiques, dépenses fiscales comprises) pour confronter
  les 40 Md€ de LOG-02.
- [ ] Trouver une série officielle des mises en chantier avant 2000 (SDES ou Insee), pour remplacer le CRÉDOC.
- [ ] LOG-04 : croiser les déciles de revenu de l'Insee (fichier localisé social et fiscal, Filosofi) avec les
  plafonds PLUS de l'arrêté annuel.
- [ ] Mesure SRU : il écrit « 20 % et bientôt 25 % ». La loi du 18 janvier 2013 a déjà porté le taux à 25 % pour la
  plupart des communes concernées. À sourcer : Légifrance a bloqué l'accès automatique.
