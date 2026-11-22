# Grille de la proximité des candidats

Chaque mesure d'un programme est rangée dans **un** sous-thème et reçoit **une note de -3 à +3** sur l'axe de ce
sous-thème. Le code des axes et sous-thèmes est dans `proximite/axes.py`.

## Les trois axes

| Axe | -3 | +3 |
|---|---|---|---|---|
| **E · Économie et social** | intervention et redistribution : dépense publique, impôts sur les hauts revenus et le capital, droits des salariés, prestations étendues, soutien à la demande, secteur public | libéralisme économique : baisse des prélèvements et de la dépense, liberté d'entreprendre, flexibilité du travail, politique de l'offre, privé et concurrence |
| **O · Ordre et immigration** | libertés, prévention, accueil : droits des personnes, libertés publiques, régularisation, progressisme des mœurs, pédagogie | autorité, sanction, fermeture : fermeté pénale, pouvoirs de police, réduction de l'immigration, identité, assimilation, discipline |
| **S · Souveraineté et monde** | Europe et ouverture : intégration européenne, décisions et défense communes, libre-échange, alliances | souveraineté nationale : primauté du droit national, sortie ou refus des traités, protectionnisme, relocalisation, indépendance militaire |

Sécurité et immigration forment un seul axe : dans les programmes, elles vont presque toujours ensemble. Cela laisse le
troisième axe à l'Europe et au monde, qui sépare des candidats que les deux premiers rapprochent (un souverainiste et
un libéral pro-européen peuvent être voisins sur l'économie).

## Les sous-thèmes

| Axe | Code | Sous-thème | vers −3 | vers +3 |
|---|---|---|---|---|
| E | E1 | Impôts et prélèvements | plus d'impôts | moins d'impôts |
| E | E2 | Dépense publique, dette, État (taille et coût de l'État, fonction publique, budget) | plus de dépense | moins d'État |
| E | E3 | Travail, salaires, emploi | droits des salariés | flexibilité |
| E | E4 | Protection sociale, retraites, santé | plus de prestations | moins de prestations |
| E | E5 | Entreprises, industrie, agriculture (aides, normes, nationalisations, marchés) | aides, État actionnaire | concurrence, moins de normes |
| E | E6 | Logement et services publics (hors école) | plus de public | plus de privé |
| E | E7 | Énergie et environnement | normes, plan public | moins de contraintes |
| O | O1 | Sécurité et police | prévention | pouvoirs de police |
| O | O2 | Justice et peines | réinsertion | peines sévères |
| O | O3 | Immigration, asile, nationalité | accueil | fermeture |
| O | O4 | Laïcité, identité, mœurs (fin de vie, famille, religion, mémoire, culture nationale) | progressisme | identité, tradition |
| O | O5 | Libertés publiques et numérique (surveillance, données, expression, manifestations) | libertés | surveillance |
| O | O6 | École et éducation (autorité, exigence, sélection ↔ égalité, émancipation) | égalité | autorité, sélection |
| S | S1 | Union européenne | plus d'Europe | moins d'Europe |
| S | S2 | Défense et diplomatie | défense commune | indépendance |
| S | S3 | Commerce, protectionnisme, relocalisation | libre-échange | protectionnisme |
| — | H1 | Institutions et démocratie (hors axes : RIC, proportionnelle, mandats, décentralisation) | — | — |
| — | H2 | Autres sujets (hors axes : culture, sport, outre-mer quand rien ne les rattache à un axe) | — | — |

Les mesures H1 et H2 sont affichées mais n'entrent dans aucune coordonnée. Les colonnes « vers −3 » et « vers +3 »
sont affichées sur le site au-dessus de chaque sous-thème (`POLES` dans `proximite/axes.py`).

## Les notes

| Note | Sens |
|---|---|
| ±3 | rupture : la mesure la plus nette de ce côté (nationaliser des banques, Frexit, moratoire sur toute immigration, supprimer l'impôt sur le revenu…) |
| ±2 | mesure franche de ce côté (rétablir l'ISF, peines planchers, quotas migratoires, report net de l'âge de départ) |
| ±1 | inflexion modérée ou ciblée (un crédit d'impôt, quelques places de prison, un encadrement partiel) |
| 0 | la mesure relève du sous-thème mais ne tire d'aucun côté (moderniser un outil, une étude, un plan de gestion) |

Règles :

- **La mesure, pas le discours.** On note ce que la mesure fait, pas le ton du paragraphe ni le parti du candidat. La
  même mesure reçoit la même note chez tous.
- **Un sous-thème par mesure** : celui de son effet principal. Une hausse d'impôt pour financer l'écologie est en E1 ;
  une taxe aux frontières sur les produits étrangers en S3.
- **Le signe suit l'axe, pas le sous-thème** : un plan d'investissement public dans le nucléaire est en E7 et tire vers
  l'intervention (-1) ; une baisse des normes environnementales pour les agriculteurs est en E5 (+1 ou +2).
- **Une mesure composée** (« baisser l'IS et taxer les superprofits ») se coupe en deux mesures.
- **On ne garde que les mesures** : une proposition précise ou un engagement d'action. Les constats, les valeurs, les
  intentions vagues (« redonner confiance ») ne sont pas relevés.
- **Formulation** : courte et fidèle, dans les mots du programme ; pas de commentaire.

## Des mesures aux positions

1. Note d'un sous-thème : moyenne des notes de ses mesures.
2. Position sur un axe : moyenne des notes des sous-thèmes de cet axe où le candidat a au moins une mesure. Chaque
   sous-thème pèse autant : un programme très détaillé sur la fiscalité ne pèse pas plus sur l'économie que ses autres
   sous-thèmes.
3. Un candidat sans aucune mesure sur un axe y est placé à 0 et signalé (« pas de mesure ») : sa position sur cet axe
   n'est pas connue.
4. Distance entre deux candidats : distance euclidienne dans l'espace des trois axes (de 0, identiques, à √108 ≈ 10,4,
   aux deux coins opposés). Elle est affichée aussi sur 100 (0 = identiques, 100 = opposés en tout).
   Le site donne aussi la distance sur un seul axe : l'écart des deux positions, sur 100 (100 = l'un à −3, l'autre
   à +3).
