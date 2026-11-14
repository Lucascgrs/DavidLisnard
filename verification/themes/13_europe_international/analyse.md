# Europe et international : analyse et verdicts

**En bref.** Le constat central de Lisnard est exact : le PIB par habitant de la France, mesuré en pouvoir
d'achat, est passé sous la moyenne de l'UE en 2022, pour la première fois depuis le début de la série (1995). Le
rapport Draghi dit bien ce qu'il lui fait dire, et ses calculs sur la défense sont justes.

Il grossit en revanche le déclassement :

- la France n'est pas passée derrière l'Italie ;
- elle n'était pas 7e mondiale il y a trente ans, mais 11e à 13e ;
- le déficit commercial de l'UE avec la Chine de 2025 n'est pas un record (2022 était pire).

| Verdict | Nombre | Affirmations |
| --- | --- | --- |
| Exact | 3 | EUR-01, 04, 05 |
| Trompeur | 1 | EUR-03 |
| Faux | 2 | EUR-02, 06 |

Chiffres : `calculs/resultats.csv`. Méthode : `calculs/METHODE.md`. Graphique :
`calculs/graphiques/pib_par_habitant_spa.png`. Fichiers : `brut/`, `sources.csv`. Données du 14/11/2026.

---

## EUR-01 — « La France vient de passer en richesse par habitant, c'est la première fois dans notre histoire contemporaine […] en dessous de la moyenne européenne » (CNews, 28/10/2026)

**Verdict : exact.** Confiance : forte.

- En SPA (standards de pouvoir d'achat), le PIB par habitant de la France est à 98 en 2022, puis à 99 en 2023 et en
  2024, pour une moyenne de l'UE à 27 de 100. [M1]
- De 1995 à 2021, il n'était jamais descendu sous 101. Il valait 116 à 118 à la fin des années 1990.
- « Vient de passer » est un peu daté : le passage sous la moyenne date de 2022, comme il l'écrit lui-même ailleurs
  (« depuis 2022 »). L'écart reste faible (1 à 2 points) et sujet à révision. Mais la tendance, une baisse continue
  depuis 2000, est nette.

## EUR-02 — « On vient de passer derrière l'Italie en création de richesse par habitant » (26/06/2025)

**Verdict : faux.** Confiance : moyenne.

- Selon les données actuelles d'Eurostat, la France et l'Italie sont à égalité en 2022 (98). La France repasse
  devant d'un point en 2023 et en 2024 (99 contre 98). [M1]
- L'Italie a beaucoup rattrapé son retard depuis 2020. La France n'est pas pour autant passée derrière.
- Un écart d'un point est dans la marge des révisions. Les données disponibles en juin 2025 ont pu donner un
  classement différent, ce qui n'a pas été vérifié ici.

## EUR-03 — « On était au 7e rang de création de richesse par habitant il y a 30 ans, […] on est au 27e rang » (franceinfo, 24/09/2025)

**Verdict : trompeur.** Confiance : forte.

- En dollars courants (FMI, tous pays), la France est bien 27e en 2024 (26e en 2025). Mais elle était 13e en 1995,
  pas 7e. [M2]
- Aucun des quatre classements calculés ne la place 7e en 1995 :
  - hors pays de moins d'un million d'habitants : 11e en 1995, 20e à 21e aujourd'hui ;
  - en parité de pouvoir d'achat : 21e en 1995, 30e aujourd'hui (16e et 22e hors petits pays).
- Le nombre de pays classés est passé de 175 à 195. Une partie du recul de rang tient donc à des pays nouvellement
  mesurés.
- Le recul est réel, mais il le fait paraître deux fois plus fort qu'il n'est. Sa version du Livre noir (« 11e dans
  les années 80 […] 24e ») est plus proche des données : 12e en 1980 en dollars courants.

## EUR-04 — « Selon le rapport Draghi, cette seule divergence explique 70 % de l'écart de PIB par habitant entre l'Union européenne et les États-Unis » (15/05/2026)

**Verdict : exact.** Confiance : forte.

- Le rapport Draghi (partie A) écrit : « Around 70% of the gap in per capita GDP with US at PPP is explained by
  lower productivity in the EU ». [M3]
- La phrase précédente de Lisnard (zone euro à « 98 % » de la productivité horaire américaine en 1995, « 82 % » en
  2019) ne reprend pas les chiffres de Draghi : l'UE à 95 % en 1995, puis « en dessous de 80 % ». Elle vient
  d'une autre source, non identifiée. Le sens est le même.

## EUR-05 — « La France consacre 57 milliards d'euros à sa défense, soit à peine 2 % de la richesse nationale » (L'Opinion, 06/03/2026)

**Verdict : exact.** Confiance : forte.

- 57 Md€ représentent 1,9 % du PIB de 2025. Avec la définition plus large de l'OTAN, la France dépense 61,8 Md€ en
  2025, soit 2,05 % du PIB. [M4]
- Ses calculs du 03/03/2026 sont justes :
  - passer de 2,06 % à 3 % du PIB coûterait 28 Md€ par an (il dit 27) ;
  - passer à 3,5 % coûterait 43 Md€ (« plus de 40 »).

## EUR-06 — « Le déficit commercial de l'Union européenne avec Pékin a atteint le niveau record de 360 milliards d'euros en 2025 » (29/06/2026)

**Verdict : faux.** Confiance : forte.

- Selon Eurostat (Comext), le déficit de l'UE avec la Chine est de 375 Md€ en 2025. Le record est celui de 2022 :
  398 Md€, l'année de la flambée des prix et des importations. [M5]
- Le déficit est très élevé et repart à la hausse depuis 2023 (300 Md€), mais 2025 n'est pas un record.

---

## Ce qui reste à faire ou à vérifier

- [ ] Vintage des données Eurostat de juin 2025, pour savoir si l'Italie apparaissait alors devant la France (EUR-02).
- [ ] Source des « 98 % / 82 % » de productivité horaire (EUR-04) : OCDE ou Conference Board.
- [ ] « 13 000 actes juridiques contraignants contre 5 500 aux États-Unis » : source non identifiée.
- [ ] Budget des armées 2026 (loi de finances) pour les 57 Md€.
