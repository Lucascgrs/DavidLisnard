# Culture, numérique et intelligence artificielle : analyse et verdicts

**En bref.** Sur le numérique et l'IA, Lisnard reprend fidèlement de bonnes sources : le rapport Draghi, le
Stanford AI Index, l'étude BCG-SIA sur Taïwan. Ses chiffres sont exacts.

Sur la culture, son écart entre Paris et la province (801 € contre 24 € par habitant) est très exagéré : la
statistique publique donne 196 € en Île-de-France contre 21 € ailleurs. L'écart est donc de 9 à 1, et non de 33 à
1, et il tient surtout aux grands établissements nationaux.

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Exact | 3 | NUM-01, 02, 04 |
| Trompeur | 1 | CULT-01 |
| Invérifiable | 1 | NUM-03 |
| Opinion ou promesse | 1 | CULT-02 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Fichiers : `brut/`, `sources.csv`. Données du
14/11/2026.

---

## NUM-01 — « En cinquante ans, l'Europe n'a pas engendré une seule entreprise valorisée à plus de 100 milliards d'euros, quand les six géants américains au-dessus de 1 000 milliards sont tous nés sur cette période » (Le Diplomate, 29/06/2026)

**Verdict : exact.** Confiance : forte.

- C'est la traduction exacte d'une phrase du rapport Draghi (2024) : aucune entreprise de l'UE de plus de 100 Md€ de
  capitalisation n'a été « créée à partir de rien » en cinquante ans, alors que les six entreprises américaines
  valant plus de 1 000 Md€ l'ont toutes été. [M1]
- Il omet une nuance : « créée à partir de rien ». Des entreprises européennes de plus de 100 Md€ existent, mais
  elles sont plus anciennes ou issues de fusions.

## NUM-02 — « En 2025, l'investissement privé dans l'intelligence artificielle a atteint près de 286 milliards de dollars aux États-Unis, vingt-trois fois le niveau chinois » (29/06/2026)

**Verdict : exact.** Confiance : forte.

- Selon le Stanford AI Index 2026, l'investissement privé dans l'IA a atteint 285,9 Md$ aux États-Unis en 2025,
  contre 12,4 Md$ en Chine (23 fois moins) et 20,9 Md$ en Europe. [M2]
- Le rapport précise que l'investissement privé sous-estime la dépense chinoise, qui passe aussi par des fonds
  publics.

## NUM-03 — « La Chine est désormais en tête dans 57 des 64 technologies critiques recensées » (29/06/2026)

**Verdict : invérifiable** avec les sources accessibles.

- Le chiffre vient du Critical Technology Tracker de l'Australian Strategic Policy Institute (ASPI), dont le site a
  refusé l'accès automatique (code 403).
- Sa version du 29/08/2026 (« 66 » sur « 74 ») correspond probablement à une mise à jour du même classement. Ce
  classement de l'ASPI repose sur les publications scientifiques les plus citées, pas sur la production
  industrielle.

## NUM-04 — « Taïwan, où se fabriquent plus de 90 % des semi-conducteurs les plus avancés » (29/06/2026)

**Verdict : exact.** Confiance : moyenne.

- Selon l'étude BCG et Semiconductor Industry Association (2021), 92 % de la capacité mondiale de production sous
  10 nanomètres se trouvait à Taïwan en 2019, et le reste en Corée du Sud. [M3]
- Les données ont sept ans. Des usines avancées ouvrent aux États-Unis et au Japon, mais l'ordre de grandeur reste
  celui couramment admis.

## CULT-01 — « Le ministère de la Culture dépense en moyenne 801 euros par habitant parisien contre 24 euros par habitant de la province » (Le Point, cité le 22/05/2025)

**Verdict : trompeur.** Confiance : moyenne.

- Selon l'Insee, d'après le service statistique du ministère, les dépenses du ministère de la Culture s'élevaient en
  2018 à 196 € par habitant en Île-de-France, contre 21 € en moyenne hors Île-de-France. [M4]
- L'écart est donc de 9 à 1, pas de 33 à 1 comme le suggèrent ses 801 € contre 24 €. Aucun chiffre « par habitant
  parisien » n'est publié.
- Cet écart tient surtout aux grands établissements nationaux (Louvre, Opéra, Bibliothèque nationale), comptés là
  où ils sont implantés mais fréquentés par tous les Français et par les touristes.
- Le déséquilibre en faveur de l'Île-de-France est réel et documenté. Le chiffre qu'il donne l'exagère beaucoup.

## CULT-02 — Mesure : « un grand ministère unique de l'Instruction, de la Recherche et de la Culture » (17/07/2026)

**Verdict : opinion ou promesse.** Choix d'organisation gouvernementale ; pas de coût chiffré.

---

## Ce qui reste à faire ou à vérifier

- [ ] Rapport complet de l'ASPI (Critical Technology Tracker) pour NUM-03.
- [ ] Données plus récentes du DEPS (dépenses du ministère par région, après 2018) et origine du « 801 € ».
- [ ] « 70 % des brevets d'IA viennent des États-Unis, de Chine, du Japon et de Corée du Sud » (2023) : OMPI,
  Technology Trends 2019.
