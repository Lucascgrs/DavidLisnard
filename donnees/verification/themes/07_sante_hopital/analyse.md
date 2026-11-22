# Santé et hôpital : analyse et verdicts

**En bref.** Les difficultés d'accès aux soins sont réelles, mais les chiffres de Lisnard les grossissent
systématiquement.

- **Les « 87 % de désert médical »** viennent du zonage qui ouvre droit aux aides à l'installation. Selon l'indicateur
  de la DREES, 18 % de la population vit en zone sous-dense pour les généralistes.
- **Le « tiers » de non-soignants** à l'hôpital est en fait de 26 % (11 % pour les seuls administratifs).
- **« Plus que ses voisins »** : l'Allemagne dépense plus que la France. L'écart avec la moyenne européenne est
  d'environ 34 Md€, pas 60.
- **Les chiffres OCDE** de son livret 2026 datent de 2018-2019.

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Trompeur | 4 | SANTE-01, 02, 03, 04 |
| Invérifiable | 2 | SANTE-05, 06 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Fichiers : `brut/`, `sources.csv`. Données du
14/11/2026.

---

## SANTE-01 — « 87 % du territoire manque de médecins » (programme Santé, 2026)

**Verdict : trompeur.** Confiance : forte.

- Selon l'accessibilité potentielle localisée de la DREES (2024), 18,2 % de la population vit dans une commune
  sous-dense en médecins généralistes (moins de 2,5 consultations accessibles par an et par habitant). Ces communes
  sont 38 % des communes : souvent petites et rurales, elles couvrent beaucoup de territoire mais peu d'habitants.
  [M1]
- Avec un seuil très large (moins de 4 consultations), on atteint 61 % de la population et 83 % des communes.
- Le chiffre de 87 % correspond au zonage des ARS (zones d'intervention prioritaire et zones d'action
  complémentaire). Ce zonage sert à attribuer les aides à l'installation et ratisse volontairement large. Ce n'est pas
  une mesure des déserts médicaux, comme le relevait aussi le dossier du collègue.
- Ses versions varient : « du territoire », « des Français ». Sur la population, le chiffre est encore plus éloigné
  des mesures de la DREES.

## SANTE-02 — « Un tiers du personnel hospitalier n'est pas soignant » (programme Santé)

**Verdict : trompeur.** Confiance : forte.

- En 2024, les hôpitaux publics et privés emploient 1,41 million de salariés. Les non-soignants en représentent
  26,2 % : filière administrative (158 600) et autres non-soignants, c'est-à-dire personnels techniques, ouvriers,
  médico-techniques et socio-éducatifs (209 500). [M2]
- La seule filière administrative pèse 11,3 %. L'argument de la « bureaucratie » mélange donc administratifs et
  personnels indispensables au fonctionnement (cuisine, entretien, biomédical, logistique).

## SANTE-03 — « Ce n'est pas une question de moyens – la France dépense plus que ses voisins » (programme Santé)

**Verdict : trompeur.** Confiance : forte.

- En 2024, la dépense courante de santé représente 11,3 % du PIB en France, 3e de l'UE, mais derrière l'Allemagne
  (12,2 %). La moyenne de l'UE est de 10,2 %. [M3]
- Par habitant, en pouvoir d'achat comparable, la France n'est que 8e de l'UE. Allemagne, Autriche, Pays-Bas,
  Luxembourg, Belgique, Suède et Irlande dépensent plus.
- Sa version chiffrée (« 12 % du PIB, soit 60 milliards de plus que la moyenne européenne ») est surestimée : 11,3 %
  du PIB, et environ 34 Md€ d'écart avec la moyenne de l'UE.
- La thèse « organisation plutôt que moyens » relève de l'opinion. Les chiffres ne permettent pas de dire que la
  France dépense nettement plus que ses grands voisins.

## SANTE-04 — « 3,2 médecins pour 1 000 habitants (26e rang de l'OCDE) […] 9,5 nouveaux diplômés pour 100 000 habitants (30e sur 36 pays) » (Livret Santé, 2026)

**Verdict : trompeur (données anciennes présentées comme actuelles).** Confiance : moyenne.

- Ses chiffres correspondent aux données de 2018-2019 : 3,16 médecins en exercice pour 1 000 habitants en 2019, 9,51
  diplômés pour 100 000 habitants en 2018. [M4]
- Les dernières données de l'OCDE (2023) donnent 3,9 médecins pour 1 000 habitants, au niveau de la médiane des pays
  renseignés (12e sur 24), et 11,3 diplômés pour 100 000 habitants (21e sur 26, sous la médiane de 14,6).
- La série française fait un saut en 2020, très probablement dû à un changement de méthode. Le niveau réel a peu
  changé, mais la place de la France dans les classements dépend de la série utilisée. Son point sur le faible nombre
  de diplômés reste juste. « 26e de l'OCDE » n'est pas reproductible avec les données actuelles.

## SANTE-05 — « 22 % des services d'urgences publiques n'ont pas la capacité d'assurer un accueil continu » (Livret Santé)

**Verdict : invérifiable avec la statistique publique.** Le chiffre vient vraisemblablement des enquêtes du syndicat
Samu-Urgences de France sur les fermetures et la régulation de l'accès aux urgences. Aucune statistique publique
(DREES) ne le mesure. Il varie entre 22 % et 23 % selon ses prises de parole.

## SANTE-06 — « Elle ne produit plus que 30 % des médicaments qu'elle consomme » (programme Santé)

**Verdict : invérifiable en l'état.** Aucune source n'est citée. Le résultat dépend de la mesure retenue : volume,
valeur, médicaments finis ou principes actifs. Il faut l'étude du LEEM ou de l'ANSM d'où vient le chiffre.

---

## Ce qui reste à faire ou à vérifier

- [ ] Retrouver le bilan national du zonage des ARS (2022-2025) pour confirmer l'origine des 87 %.
- [ ] Vérifier dans les notes de l'OCDE la cause de la rupture de série française de 2020.
- [ ] Obtenir les enquêtes de Samu-Urgences de France et la source des 30 % de médicaments.
