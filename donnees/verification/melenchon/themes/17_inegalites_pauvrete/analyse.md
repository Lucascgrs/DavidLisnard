# Inégalités, pauvreté et grandes fortunes : analyse et verdicts

**En bref.** Ses chiffres sur la pauvreté viennent de l'Insee et sont justes : près d'un million de pauvres en plus
depuis 2017, un taux de 15,4 %, un seuil de 1 337 €. Il les pousse parfois d'un cran : « plus de 10 millions » de
pauvres (9,8 millions) et un « record jamais enregistré » (le taux était plus haut dans les années 1970).

- Le chiffre de l'aide alimentaire (« 8 millions ») est deux fois plus élevé que le haut de la fourchette de l'Insee.
- À l'inverse, il sous-estime le nombre de personnes qui ne peuvent pas se chauffer : environ 8 millions, pas 4.

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Exact | 2 | INEG-01, 06 |
| Plutôt exact | 2 | INEG-02, 03 |
| Faux | 2 | INEG-04, 05 |
| Opinion ou promesse | 1 | INEG-07 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Fichiers : `brut/`, `sources.csv`. Données du
20/11/2026.

---

## INEG-01 — « Depuis 2017, un million de personnes ont basculé dans la pauvreté » (programme)

**Verdict : exact.** Confiance : forte.

- Selon l'Insee, le nombre de personnes sous le seuil de pauvreté (60 % du niveau de vie médian) est passé de
  8,89 millions en 2017 à 9,82 millions en 2024 : 0,93 million de plus. [M1]

## INEG-02 — « Plus de 15 % des Français qui vivent sous le seuil de pauvreté : un record jamais enregistré » (programme)

**Verdict : plutôt exact.** Confiance : forte.

- Le taux de pauvreté est de 15,4 % en 2023 et en 2024 : c'est le plus haut depuis le début de la série annuelle en
  1996 (15,3 % cette année-là). [M2]
- Mais « jamais enregistré » va trop loin : les séries rétropolées de l'Insee donnent 17,0 % en 1975.

## INEG-03 — « Quand il y a plus de 10 millions de pauvres » (Instagram, 09/11/2026)

**Verdict : plutôt exact.** Confiance : forte.

- L'Insee compte 9,82 millions de personnes pauvres en 2024. « Plus de 10 millions » arrondit vers le haut ; sa
  version du 18 octobre, « 9 millions », arrondit vers le bas. [M1]

## INEG-04 — « 8 millions de personnes à l'aide alimentaire » (Fête de l'Humanité, 12/09/2026)

**Verdict : faux.** Confiance : moyenne.

- L'Insee estime le nombre de bénéficiaires de l'aide alimentaire sur une année « entre 2 et 4 millions de personnes
  en France métropolitaine » (enquête de fin 2021). [M3]
- 8 millions, c'est deux fois le haut de cette fourchette. L'Insee souligne que les sources se recoupent mal et
  qu'aucune estimation nationale plus récente n'a été trouvée : le besoin a pu augmenter depuis 2021, mais pas dans
  ces proportions selon les données disponibles.

## INEG-05 — « 4 millions d'entre eux ne parviennent pas à se chauffer correctement » (programme)

**Verdict : faux.** Confiance : moyenne.

- Selon l'enquête européenne sur les conditions de vie, 11,5 % des habitants déclarent en 2025 ne pas pouvoir
  chauffer convenablement leur logement, soit environ 7,9 millions de personnes (8,1 millions en 2024). [M4]
- Le chiffre du programme est donc deux fois trop bas : la réalité est plus grave que ce qu'il annonce. Il peut venir
  d'une autre mesure (ménages plutôt que personnes, autre enquête) que le programme ne cite pas.

## INEG-06 — « Un salarié au SMIC gagne à peine plus que le seuil de pauvreté » (programme)

**Verdict : exact.** **Estimation, non fiable à 100 %.** [M5]

- En 2024, un SMIC à temps plein rapporte environ 1 397 € net par mois, 4,5 % de plus que le seuil de pauvreté d'une
  personne seule (1 337 €).
- La comparaison vaut pour une personne seule sans autre revenu ; la prime d'activité s'y ajoute, et un smicard à
  temps partiel ou avec des enfants passe sous le seuil.

## INEG-07 — Mesure : « le revenu mensuel de chaque personne atteindra le seuil de pauvreté (1 337 euros pour une personne seule) » (programme)

**Verdict : opinion ou promesse.** Confiance : forte.

- 1 337 € par mois est bien le seuil de pauvreté à 60 % pour une personne seule en 2024, le dernier publié par
  l'Insee. [M6]
- Le coût d'une telle garantie dépend de ce qu'elle remplace (RSA, prime d'activité, allocations logement) ; il n'est
  pas chiffré dans le passage relevé.

---

## Ce qui reste à faire ou à vérifier

- [ ] Retrouver la source des « 4 millions » qui ne peuvent pas se chauffer et des « 800 000 » qui ne peuvent pas
  acheter de vêtements neufs (programme).
- [ ] Vérifier « un parent sur trois se prive de manger pour nourrir ses enfants » (baromètre d'une association).
