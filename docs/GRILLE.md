# Grille d'annotation

Elle fixe ce que veut dire chaque note. Le modèle apprend ces notes : il reproduit cette grille.

Notes entières de 0 à 20. Chaque commentaire est lu avec son contexte : compte, titre de la vidéo ou du post,
commentaire auquel il répond. Une note juge **le commentaire lui-même**. Le contexte sert seulement à le comprendre.

## Cible : de qui parle le commentaire ?

- **L** : le commentaire dit quelque chose de David Lisnard, de son mouvement (Nouvelle Énergie), de sa
  candidature, de ses idées ou de ses propos.
  - Il peut le nommer, ou le désigner sans le nommer : « il », « ce maire », « vous » sous son post, ou l'orateur de
    la vidéo.
  - Il peut aussi réagir à ce qu'il propose : approuver, contester, compléter.
  - Il peut enfin le comparer à d'autres.
- **A** : tout le reste :
  - d'autres personnalités seulement ;
  - le journaliste ;
  - une dispute entre commentateurs ;
  - la politique en général, sans rapport avec ce qu'il dit.

  Règle : **A ⇒ tonalité, forme, système et idées valent 10**, et la pertinence reste basse (0 à 4).

## 1. Tonalité envers Lisnard

| Note | Sens | Exemple |
|---|---|---|
| 0 | haine, insulte | « Une flinguée décérébrée » (sous sa vidéo, visant lui ou son camp) |
| 3 | rejet net | « Ce mec est un vendu ! » |
| 6 | critique modérée, doute, déception | « J'aime bien Lisnard mais s'il s'allie à Philippe vous allez décevoir » → 8 |
| 10 | neutre, mitigé, question sans parti pris | « Svp BFM, parlez plus du programme » |
| 14 | approbation mesurée | « Il a l'air très intéressant, mais a-t-il le potentiel d'être élu ? » → 13 |
| 17 | soutien clair | « Heureuse de pouvoir enfin voter pour un candidat qui fait sens » |
| 20 | enthousiasme, soutien fervent | « Mille fois bravo, notre futur Président 👏👏👏 » |

## 2. Forme : élocution, manière de parler, charisme, communication, présence

Note symétrique.

| Note | Sens | Exemples |
|---|---|---|
| 0 | reproche fort et central | « aucun charisme, il endort tout le monde » |
| 5 | reproche | « trop technique, on ne comprend rien », « manque de punch », « sa com est ratée » |
| 10 | la forme n'est pas évoquée (cas le plus fréquent) | |
| 15 | éloge | « il parle clair », « calme et posé », « belle prestance », « il a du répondant » |
| 20 | éloge fort et central | « quel orateur, quelle aisance, il a écrasé le débat » |

Ce qui compte comme forme :
- **Oui** : la façon de s'exprimer et l'aisance en débat (« il les a démontés », s'il vise la façon de faire). Aussi
  le charisme, la prestance, le physique et la tenue, la qualité de sa communication (vidéos, réseaux), le ton
  (agressif, mou, arrogant).
- **Non** : l'intelligence ou la compétence en général. Elles vont dans la tonalité, et dans les idées si elles
  portent sur ses propositions.

## 3. Système : proximité avec Macron, l'establishment, la droite classique

Note symétrique.

| Note | Sens | Exemples |
|---|---|---|
| 0 | reproche fort et central | « c'est Macron en plus vieux », « encore un produit du système », « LR recyclé » |
| 5 | allusion | « vieux politicien », « un de plus », « vendu », « même moule », « il a soutenu Macron », « droite molle » |
| 10 | non évoqué | |
| 15 | perçu comme différent, indépendant, hors système | « enfin quelqu'un de libre », « pas un politicien de carrière », « il ose dire ce que les autres taisent » |
| 20 | fortement et explicitement | « le seul vraiment hors système, l'anti-Macron » |

## 4. Idées : ses idées, son programme, ses positions

Note symétrique.

| Note | Sens | Exemples |
|---|---|---|
| 0 | rejet argumenté ou total | « programme ruineux et irréaliste », « ses idées sont dangereuses » |
| 5 | critique d'une idée, ou idées jugées creuses, déjà vues | « la fin du collège unique, une idée usée », « aucune vision » → 2 |
| 10 | ses idées ne sont pas évoquées | |
| 15 | approbation d'une idée ou de ses positions | « pragmatisme et liberté », « oui à la baisse des dépenses » |
| 20 | adhésion argumentée ou forte à son programme | |

Une idée ajoutée par le commentateur (« et la suppression de la CSG ? ») vaut 10 à 12, sauf si elle s'accompagne
d'un jugement sur les siennes. Un désaccord sur une idée précise (« il faut aussi le Frexit ») vaut 7 à 9.

## 5. Pertinence pour l'analyse

Ce que le commentaire apprend sur la façon dont Lisnard est perçu.

| Note | Sens | Exemples |
|---|---|---|
| 0 | spam, illisible, sans rapport, attaque entre commentateurs | « @x Et sinon sur le fond ? » |
| 2 | politique générale ou autre personnalité, sans lien avec lui (souvent cible A) | |
| 5 | réaction minimale | émojis seuls, « Top », « 👍 » |
| 8 | avis sans argument | « Bravo ! », « Lisnard président » |
| 12 | avis avec une raison ou un point précis | « Bravo pour la sécurité à Cannes » |
| 16 | avis argumenté, critique constructive, doute précis | |
| 20 | argumentation détaillée et riche sur lui, ses idées ou sa façon de faire | |

**Garde-fou contre la dérive.** Au fil des lots 18 à 142, la pertinence a glissé vers le bas : des « Bravo » notés 0,
des avis argumentés notés 3. Elle a été recalée le 2026-11-09 (analyse/recalage_pertinence.py, bilan dans
donnees/analyse/annotation/recalage/bilan.json). Repères à vérifier régulièrement :
- un éloge sans argument vaut 8, pas 0 ;
- la moyenne des commentaires visant Lisnard doit rester autour de 8 à 9 ;
- 0 est réservé au spam et aux attaques entre commentateurs.

`python -m analyse.annotation etat` ne contrôle pas cela. Un contrôle rapide consiste à comparer la moyenne d'un lot
récent avec celle des lots 1 à 17.

## Cas difficiles

- **Ironie** : on note l'intention réelle. « Bravo, encore un énarque 👏 » → tonalité 4, système 3.
  - Indices : éloge démesuré ou contredit par le contexte, guillemets, « 😂 », « mdr », « … », « bien sûr »,
    « quel courage », points d'exclamation en série, et surtout le commentaire auquel il répond.
  - Ironie comprise : on note le sens réel, avec la pertinence habituelle. La remarque commence par
    « ironie ».
  - **Ironie indécidable** : on ne sait pas si l'auteur loue ou se moque, par exemple « Le sauveur 😂 » sans
    autre contexte, ou un mot qui peut être sincère ou moqueur. On ne devine pas.
    - Cible L, tonalité et reproches à 10.
    - **Pertinence 2 ou 3**, pour que ces commentaires puissent être écartés de l'analyse.
    - La remarque commence par « ironie ? ».
- **Réponse** : on la lit **à la lumière du commentaire auquel elle répond**, affiché en entier.
  - « Exactement » sous « Encore un macroniste » → cible L, tonalité 4, système 4 : la réponse reprend l'avis du
    parent.
  - « 😂😂 » sous une moquerie de Lisnard → tonalité 6, pertinence 4. Sous un éloge, c'est souvent une moquerie
    de l'éloge : tonalité 7 à 8, ou ironie indécidable.
  - « T'as rien compris, il est contre Macron » sous « Macron bis » → cible L, tonalité 14, système 15 : on note
    ce que la réponse dit de Lisnard, même quand elle contredit le parent.
  - « Il a raison » ou « non » : le sens dépend entièrement du parent, que l'on reprend.
  - « D'accord avec vous » sous un éloge de Lisnard → cible L, tonalité proche du parent, pertinence 6.
  - Une réponse qui ne discute que du commentateur → A.
- **Question sincère** : tonalité 10. La pertinence dépend de ce qu'elle révèle, par exemple « que pense-t-il de
  l'immigration ? » → 9.
- **Comparaison** : si elle le met en balance avec d'autres, la cible est L, et l'on note ce qui le concerne.
- **Éloge et critique mêlés** : tonalité selon la balance, et chaque critère selon ce qui est dit.
- **Langue étrangère** : mêmes règles.
- **Sondages, chances d'être élu** : ce n'est pas un reproche de forme ni de système. La tonalité suit le souhait
  exprimé.
- **Ville de Cannes, son action de maire** : jugement sur son action → tonalité et, s'il vise une politique menée,
  idées.
