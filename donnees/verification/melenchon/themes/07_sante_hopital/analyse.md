# Santé et hôpital : analyse et verdicts

**En bref.** Il sous-estime la baisse des lits de l'hôpital public (98 000 en vingt-cinq ans, pas 80 000), mais une
grande partie vient de la transformation de lits de long séjour en places d'Ehpad. Ses deux autres chiffres grossissent
le constat : les déserts médicaux couvrent moins d'un tiers de la population, et les cancers évitables le sont surtout
par le tabac, l'alcool et l'alimentation, pas par « l'environnement ».

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Plutôt exact | 1 | SANTE-01 |
| Trompeur | 2 | SANTE-02, 03 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Fichiers : `brut/`, `sources.csv`. Données du
20/11/2026.

---

## SANTE-01 — « En vingt-cinq ans, l'hôpital public a perdu 80 000 lits » (programme)

**Verdict : plutôt exact.** Confiance : forte.

- Les hôpitaux publics comptaient 322 255 lits en 1999 et 224 057 en 2024 : 98 198 lits en moins en vingt-cinq ans.
  Le chiffre du programme est même en dessous de la réalité. [M1]
- Une partie de la baisse n'est pas une perte pour les patients : les lits de soins de longue durée (tous statuts)
  sont passés de 83 928 à 28 963, la plupart transformés en places d'Ehpad, qui ne sont plus comptées comme des lits
  d'hôpital. Le reste suit le développement de la chirurgie et de la médecine sans nuit à l'hôpital.

## SANTE-02 — « Plus d'un tiers de la population vit dans un désert médical » (programme)

**Verdict : trompeur.** Confiance : moyenne.

- Selon l'indicateur d'accessibilité aux médecins généralistes de la DREES (2024), 18,2 % de la population vit dans une
  commune sous-dense (moins de 2,5 consultations accessibles par an et par habitant, le seuil de la DREES). [M2]
- Avec un seuil plus large (moins de 3 consultations), on arrive à 31,7 %, encore en dessous d'un tiers ; il faut
  descendre à moins de 4 consultations (61,1 %) pour le dépasser.
- « Désert médical » n'a pas de définition unique, mais au seuil officiel la part est deux fois plus faible que ce
  qu'il annonce. Les « 6 millions de personnes » sans médecin traitant n'ont pas été vérifiés ici.

## SANTE-03 — « 40 % des cancers sont évitables en agissant sur l'environnement » (programme)

**Verdict : trompeur.** Confiance : forte.

- Selon le Centre international de recherche sur le cancer, 41 % des cancers diagnostiqués en 2015 chez les adultes
  auraient pu être évités : le chiffre est juste. [M3]
- Mais il s'agit surtout du mode de vie : tabac, alcool, alimentation, surpoids. La pollution de l'air, les substances
  chimiques et le radon expliquent ensemble 1,7 % des cancers ; en ajoutant les infections et les expositions
  professionnelles, 9,3 %.
- Attribuer les 40 % à « l'environnement » donne au chiffre un sens qu'il n'a pas.

---

## Ce qui reste à faire ou à vérifier

- [ ] Vérifier « 6 millions de personnes n'ont pas de médecin traitant » (Assurance maladie).
- [ ] Vérifier les chiffres de l'OFDT cités par le programme (23,1 % de fumeurs quotidiens, 900 000 usagers quotidiens
  de cannabis) : le PDF « Drogues et addictions, chiffres clés » n'était pas téléchargeable le 20/11/2026.
- [ ] Vérifier « nous ferons le 100 % Sécu parce que c'est 5 fois moins cher que le système privé » (frais de gestion
  de l'Assurance maladie et des complémentaires, DREES).
