# DavidLisnard : plan de l'analyse des commentaires

> Journal de conception, tenu au fil du projet. Les chemins et commandes cités sont ceux de l'époque : depuis la réorganisation du 2026-11-09, voir [README.md](../README.md), tableau « Ancienne organisation ».

Rédigé le 2026-11-08, puis réalisé le même jour après les réponses de la section 10. L'état d'avancement est en
section 11.

Deux parties :
1. **La page « Analyse » de l'interface.** On choisit les commentaires (sources, comptes, période…), on lance
   l'analyse, on voit chaque commentaire avec ses notes et une synthèse. Dans un premier temps, elle ne fait
   qu'afficher : le bouton « Lancer l'analyse » ne fera rien tant que le modèle n'existe pas.
2. **Le modèle.** Il donne à chaque commentaire une note de 0 à 20 sur chaque critère. Il apprend sur un jeu de
   commentaires que je note moi-même, selon une grille écrite, sur une copie des données collectées.

---

## 1. Où on part

| | |
|---|---|
| Commentaires collectés (2026-11-08) | 97 357 : YouTube 58 684, Instagram 38 660 (arriéré en cours), WhatsApp 13 (historique en attente) |
| Principaux / réponses | 70 475 / 26 882 |
| Longueur | médiane 66 caractères ; 25 % font moins de 26 caractères ; 10 % plus de 290 |
| Période | de 2015 à aujourd'hui (YouTube), depuis janvier 2025 (Instagram) |
| Mots-clés repérés | « Lisnard » 14 %, « Macron » 4,7 %, « système » 1,1 %, vocabulaire de l'élocution (parle, voix, débit, charisme…) ~4 % (avec beaucoup de faux positifs), idée/programme 3 % |
| Machine | processeur 16 cœurs, 25 Go de mémoire, **pas de carte graphique** ; PyTorch (version processeur), scikit-learn, LightGBM, pandas déjà installés |

Deux conséquences :
- **Les reproches que tu vises sont rares.** Si je tire les commentaires au hasard, il y aura peut-être
  20 exemples de reproche sur l'élocution dans 2 000 commentaires. Un modèle n'apprend rien avec si peu. Il faut
  donc aller chercher ces cas exprès (section 5.3).
- **Pas de carte graphique.** Réentraîner entièrement un gros modèle de langue prendrait des nuits. On passe donc
  par un modèle déjà entraîné qui transforme chaque commentaire en vecteur de nombres, calculé une seule fois. Des
  petits modèles rapides apprennent ensuite les notes à partir de ces vecteurs (section 6).

---

## 2. Les critères

Chaque commentaire reçoit une note entière de 0 à 20 par critère. Je propose les définitions ci-dessous. Elles
seront détaillées dans une grille d'annotation (`docs/GRILLE.md`), avec des exemples réels pour chaque niveau
(0, 5, 10, 15, 20) et des règles pour les cas difficiles.

| # | Critère | 0 | 10 | 20 |
|---|---|---|---|---|
| 1 | **Tonalité envers David Lisnard** (« bénéfique ou non », positif ou négatif) | très hostile | neutre, ou sans avis sur lui | très favorable |
| 2 | **Reproche sur la forme** : élocution, manière de parler, charisme, présence, communication | aucun reproche de ce type | reproche présent mais secondaire | reproche central et appuyé (« il parle comme un robot, aucun charisme ») |
| 3 | **Reproche « trop proche du système »** : ressemble à Macron, macroniste, élite, énarque, establishment, « UMPS », « même moule », « recyclé » | aucun | allusion | reproche central (« c'est Macron en plus vieux ») |
| 4 | **Reproche sur le fond** : ses idées, son programme, ses positions sont mauvais, irréalistes ou incohérents | aucun | critique d'une idée en passant | rejet argumenté de ses idées |
| 5 | **Pertinence pour l'analyse** : est-ce que le commentaire nous apprend quelque chose sur la façon dont Lisnard est perçu ? | inutile : spam, hors sujet, émoji seul, insulte sans contenu, dispute entre commentateurs sans rapport | avis sans argument (« Bravo ! », « Lisnard président ») | avis argumenté ou critique constructive |

Je propose d'ajouter un **sixième champ, qui n'est pas une note : « De qui parle le commentaire ? »** (Lisnard, un
autre, plusieurs, personne en particulier).

- Sous une vidéo de CNEWS où Lisnard débat avec quelqu'un, « il est nul » peut viser le journaliste.
- Sans ce champ, la tonalité serait faussée : on lirait comme une attaque contre Lisnard un commentaire qui vise
  quelqu'un d'autre.
- Règle : si le commentaire ne parle pas de Lisnard, la tonalité vaut 10 (sans avis) et les trois reproches valent 0.

Les reproches 2, 3 et 4 sont des notes d'intensité : 0 veut dire « ce reproche n'apparaît pas ». Les éloges (« il
parle bien », « enfin des idées claires ») se lisent dans la tonalité. Si tu préfères une note symétrique (0 =
forte critique de l'élocution, 10 = rien, 20 = éloge de l'élocution), c'est faisable : c'est la question 1 de la
section 10.

Le modèle donnera aussi un **indice de fiabilité** pour chaque commentaire (section 6.4). Il sert à repérer les
notes à prendre avec précaution.

---

## 3. Partie 1 : la page « Analyse » de l'interface

### 3.1 Disposition

Un nouvel onglet « Analyse » dans l'interface actuelle, avec trois sous-onglets : **Commentaires**, **Synthèse**,
**Modèle**.

```
┌ Analyse ───────────────────────────────────────────────────────────────────────────────────────────┐
│ [Commentaires] [Synthèse] [Modèle]                                                                 │
│ ┌ Filtres ──────────────────┐ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Sources                   │ │ 12 480 commentaires dans la sélection · 9 210 analysés           │ │
│ │  [x] YouTube              │ │ [Lancer l'analyse]  [Arrêter]   ████████░░ 74 %                  │ │
│ │  [x] Instagram            │ ├──────────────────────────────────────────────────────────────────┤ │
│ │  [ ] WhatsApp             │ │ Date       Source  Compte   Texte                  Ton Frm Sys … │ │
│ │ Comptes (liste à cocher)  │ │ 2026-11-06 YT      CNEWS    « Il ne passe pas à …   6  14  2  … │ │
│ │ Période                   │ │ 2026-11-06 IG      @davidl… « Bravo pour Cannes …  18   0  0  … │ │
│ │  du [2026-01-01] au [   ] │ │ …                                      (pages de 500 lignes)    │ │
│ │  [7 j] [30 j] [2026] [Tout]│ ├──────────────────────────────────────────────────────────────────┤ │
│ │ Type  (•) tous ( ) princ. │ │ Détail : texte complet, publication commentée, commentaire       │ │
│ │ Recherche [ macron     ]  │ │ parent, lien « Ouvrir », les 5 notes en barres, fiabilité,       │ │
│ │ Notes                     │ │ [Corriger les notes] (plus tard : enrichit l'entraînement)       │ │
│ │  Pertinence ≥ [ 8 ]       │ └──────────────────────────────────────────────────────────────────┘ │
│ │  Tonalité de [0] à [20]   │                                                                      │
│ │  … (min/max par critère)  │                                                                      │
│ │ [x] Masquer « ne parle    │                                                                      │
│ │     pas de Lisnard »      │                                                                      │
│ │ [ ] Seulement non analysés│                                                                      │
│ │ [Appliquer] [Réinitial.]  │                                                                      │
│ │ [Exporter vers Excel]     │                                                                      │
│ └───────────────────────────┘                                                                      │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Les filtres (combinables)

- **Sources** : cases à cocher. Toutes cochées par défaut = « analyse sur tout ».
- **Comptes** : liste à cocher, qui suit les sources cochées (chaînes YouTube, comptes Instagram, discussion
  WhatsApp). On peut aussi filtrer par groupe : officiel, soutien, média, commentateur.
- **Période** : date de début et date de fin, plus des raccourcis (7 jours, 30 jours, année en cours, tout). La date
  utilisée est celle du commentaire.
- **Type** : tous, principaux seulement, réponses seulement.
- **Recherche** dans le texte, sans tenir compte des accents.
- **Notes** : un minimum et un maximum par critère, par exemple « Pertinence ≥ 8 » pour retirer les
  commentaires qui n'apportent rien. Plus une case « masquer ceux qui ne parlent pas de Lisnard ».
- **État** : tous, analysés seulement, pas encore analysés.
- Les derniers filtres utilisés sont retenus d'une ouverture à l'autre.

### 3.3 Le tableau

- **Colonnes** : date, source, compte, auteur (pseudonymisé si tu le souhaites, voir section 9), début du texte,
  les 5 notes, cible, fiabilité.
- **Tri et couleurs** : un clic sur un titre de colonne trie. Les notes sont colorées du rouge au vert ; pour un
  reproche, rouge = reproche fort.
- **Affichage par pages de 500 lignes** : Tkinter devient lent au-delà de quelques milliers de lignes. Le filtrage
  porte, lui, sur tous les commentaires, ce qui reste rapide en mémoire (100 000 lignes, moins d'une seconde).
- **Panneau de détail** : un clic sur un commentaire affiche le texte complet, la vidéo ou le post commenté, le
  commentaire parent si c'est une réponse, un bouton « Ouvrir » vers le lien d'origine et les notes en barres.
- **Correction des notes** (plus tard, étape 7) : le bouton « Corriger les notes » enregistre ta correction dans
  `donnees/analyse/corrections.csv`. Ces corrections servent ensuite à réentraîner le modèle.
- **Exporter vers Excel** : la sélection filtrée, avec toutes les notes, dans `donnees/analyse/exports/`.

### 3.4 Lancer l'analyse

- **Ce que fait le bouton** : il note les commentaires de la sélection qui ne l'ont pas encore été par la version
  actuelle du modèle. Les commentaires déjà notés ne sont pas refaits.
- **Comme pour la collecte** : `python analyser.py --sources … --comptes … --du … --au …` tourne en arrière-plan,
  avec le même verrou (`EN_COURS`), le même arrêt propre (`ARRET`) et une barre d'avancement.
- **Durée estimée** : environ 20 à 40 minutes pour la première analyse des ~100 000 commentaires (le calcul des
  vecteurs domine), puis quelques secondes à quelques minutes pour les nouveaux.
- **Option** (case dans l'onglet Planification) : « analyser automatiquement les nouveaux commentaires après
  chaque collecte ».
- **Dans la version purement visuelle** (étape 1), le bouton affiche : « Le modèle n'est pas encore entraîné ».
  Les colonnes de notes affichent « — ». Je n'affiche aucune note inventée pour la démonstration, pour ne pas
  risquer de les confondre avec des vraies.

### 3.5 Sous-onglet Synthèse (sur la sélection filtrée)

- Nombre de commentaires, part analysée, part jugée non pertinente.
- Moyenne et répartition de chaque note : histogramme en 5 tranches (0-4, 5-8, 9-12, 13-16, 17-20).
- Évolution dans le temps, par semaine ou par mois : tonalité moyenne et part de chaque reproche.
- Comparaison par source, par groupe de comptes et par compte.
- Pour chaque reproche, les commentaires où il est le plus fort, à lire en exemple.
- Les graphiques sont faits avec matplotlib dans la page, comme dans CryptoPatterns.

### 3.6 Sous-onglet Modèle

- Version en service, date d'entraînement, nombre de commentaires annotés.
- Qualité mesurée par critère (section 7).
- Lien vers `analyse/RAPPORT_MODELE.md`.
- Bouton « Réentraîner » : ajouté à l'étape 7, une fois qu'il y a des corrections.

---

## 4. Données : la copie de travail

Comme tu l'as demandé, on ne travaille jamais sur les fichiers de collecte eux-mêmes.

```
donnees/analyse/
  corpus/corpus_2026-11-08.csv     copie figée de tous les commentaires au moment de la préparation
  annotation/lot_001.csv …         commentaires à annoter, par lots de 100
  annotation/annotations.csv       mes notes (une ligne par commentaire annoté)
  annotation/controle.csv          commentaires annotés deux fois, pour mesurer ma constance
  annotation/tes_notes.csv         les commentaires que tu notes toi-même (validation, section 5.5)
  vecteurs/                        vecteurs des commentaires (calculés une fois, réutilisés)
  scores.csv                       notes du modèle : source, commentaire_id, version, 5 notes, cible, fiabilité
  corrections.csv                  tes corrections depuis l'interface
  exports/                         exports Excel
modeles/v1/, v2/ …                 modèles entraînés + leurs mesures de qualité
```

- **Clé unique** : `source` + `commentaire_id`. Un commentaire n'est jamais compté deux fois, même s'il apparaît
  dans plusieurs copies.
- **Colonnes de la copie** : identifiants, source, compte, groupe du compte, date, type, texte, titre de la
  publication et texte du commentaire parent. Ces deux derniers servent de contexte : « D'accord avec vous ! » ne
  veut rien dire sans le commentaire auquel il répond.
- **Auteurs pseudonymisés** : les noms sont remplacés par une empreinte. Ni l'annotation ni le modèle n'en ont
  besoin.
- **Nettoyage minimal** : espaces normalisées et liens remplacés par `[lien]`. Les émojis sont gardés, car ils
  portent souvent la tonalité.
- **Doublons de texte** (« 👏👏👏 », « Bravo ! ») : annotés une seule fois. La note vaut pour tous les
  commentaires au texte identique.

---

## 5. Partie 2a : l'annotation (c'est moi qui note)

### 5.1 La grille, d'abord

Avant toute note, j'écris `docs/GRILLE.md`. On y trouve :
- la définition de chaque critère ;
- les repères de 0, 5, 10, 15 et 20, illustrés de vrais commentaires du corpus ;
- les règles des cas difficiles :
  - ironie : « Bravo, encore un énarque 👏 » = hostile + système ;
  - questions sincères ;
  - citations ;
  - commentaires qui comparent à un autre candidat ;
  - commentaires en anglais ;
  - réponses à un autre commentateur ;
  - mélange d'éloge et de critique.

Tu la relis avant que je note à grande échelle. C'est le meilleur moyen que mes notes correspondent à ce que tu as
en tête.

### 5.2 Le format

- **Lots de 100 commentaires**, chacun avec son contexte : compte, titre de la publication, commentaire parent.
- **Pour chaque commentaire**, j'écris : la cible, les 5 notes et, seulement pour les cas limites, une
  justification de quelques mots. Ces justifications servent à relire et corriger la grille.
- **Un script vérifie chaque lot** : identifiants présents, notes entières entre 0 et 20, cohérence avec la règle de
  la cible (pas de reproche si le commentaire ne parle pas de Lisnard).

### 5.3 Quels commentaires annoter (échantillonnage)

Premier tour, environ 2 000 commentaires :
- **1 200 tirés au hasard, mais équilibrés** par source, par groupe de comptes (officiel, soutien, média,
  commentateur), par type (principal ou réponse), par longueur et par année. Ils donnent une image fidèle du corpus
  et servent aussi à mesurer la qualité.
- **800 choisis exprès pour les cas rares** :
  - mots-clés de chaque reproche : Macron, système, énarque, élite, LR, « même moule » ; parle, voix, débit,
    charisme, « endort », « robot », lunettes ; idées, programme, propositions, « irréaliste » ;
  - commentaires proches, au sens des vecteurs, de ceux déjà repérés comme reproches ;
  - commentaires longs, plus souvent argumentés.

Un échantillon de test (environ 300 commentaires tirés au hasard dans le premier groupe) est mis de côté dès le
départ. Le modèle ne le voit jamais pendant l'entraînement : c'est sur lui qu'on mesure la qualité.

Tours suivants, environ 500 à 1 000 commentaires par tour : **apprentissage actif**. Le modèle v1 note tout le
corpus, puis j'annote en priorité :
- les commentaires où il hésite le plus ;
- ceux où ses différentes méthodes ne sont pas d'accord ;
- ceux qui sont loin de tout ce qui a déjà été annoté.

C'est la façon la plus économique d'améliorer un modèle.

Cible totale : **3 000 à 4 000 commentaires annotés**, soit 3 à 4 % du corpus.

### 5.4 Ma constance

- 150 commentaires sont annotés deux fois, à des moments différents, sans que je voie ma première note.
- L'écart moyen entre mes deux notes donne le plafond réaliste : on ne peut pas attendre du modèle qu'il soit plus
  constant que moi.
- D'expérience, ce genre de note est stable à ±2 ou 3 points sur 20. Une précision plus fine serait illusoire.

### 5.5 Ta validation

- Après mes 200 premiers commentaires, tu notes toi-même 100 commentaires dans une petite page de l'interface
  (sans voir mes notes).
- On compare tes notes et les miennes critère par critère. Si on diverge sur un critère, c'est la grille qui est
  mal définie : je la corrige avant de continuer.
- Coût pour toi : environ 30 à 45 minutes, une seule fois. C'est l'étape qui a le plus d'effet sur la qualité
  finale.

### 5.6 Comment je fais l'annotation, concrètement

- **Option A (ce que tu as demandé)** : je note les lots dans nos conversations. Environ 30 à 40 lots de 100. Ce
  sera étalé sur plusieurs sessions, et ça consomme ton quota d'utilisation de Claude Code.
- **Option B** : un script `analyse/annoter_api.py` appelle l'API Claude avec la même grille. Pour 3 000 à
  4 000 commentaires, le coût serait de quelques euros. C'est plus rapide et reproductible, mais il faut une clé
  API Anthropic. Tu en as une pour n8n : il faudrait la mettre dans `cles.json`.
- **Dans les deux cas**, les commentaires sont envoyés à Anthropic pour être lus. Pour YouTube et Instagram, ce sont
  des commentaires publics. **WhatsApp est une discussion privée** : je propose de **ne pas l'annoter**. Le modèle
  notera quand même ses messages, en local, sans rien envoyer. Il faudra juste savoir qu'il a appris sur des
  commentaires publics.

---

## 6. Partie 2b : le modèle

### 6.1 Principe

```
commentaire (+ titre de la publication + commentaire parent)
      │
      ▼
modèle de langue déjà entraîné, multilingue, sur le processeur  ──►  vecteur de 768 nombres (calculé 1 fois)
      │                                                                    │
      ▼                                                                    ▼
caractéristiques simples (mots et morceaux de mots,          un petit modèle par critère
longueur, émojis, mention de Lisnard, de Macron…)  ───────►  (régression), choisi par validation croisée
                                                                           │
                                                                           ▼
                                                     notes 0-20 arrondies + cible + fiabilité
```

### 6.2 Les étapes du modèle

1. **Référence simple (quelques minutes)**
   - Mots et morceaux de mots (TF-IDF) → régression linéaire par critère.
   - Elle donne une borne basse. Si le modèle principal ne fait pas nettement mieux, il y a un problème.
2. **Modèle principal**
   - **Les vecteurs** : un modèle multilingue de phrases téléchargé une fois, `intfloat/multilingual-e5-base`
     (bon en français, environ 1,1 Go). Si c'est trop lent, `multilingual-e5-small`.
   - **Coût de calcul** : environ 20 à 40 minutes pour les ~100 000 commentaires, une seule fois. Ensuite, seuls les
     nouveaux sont calculés.
   - **Ce qui reçoit le contexte** : le commentaire seul, puis le commentaire suivi du titre de la publication et du
     commentaire parent. Je compare les deux versions.
   - **Les petits modèles par critère** : régression ridge, LightGBM et petit réseau. Je garde le meilleur de
     chaque critère en validation croisée, ou une moyenne des meilleurs.
   - **Pour la cible** : un classifieur à 4 classes.
3. **Option, si un critère reste faible**
   - Réentraîner un petit modèle de langue français (CamemBERT ou e5-small) sur les annotations, une nuit de calcul
     sur le processeur.
   - Je ne le ferai que si l'étape 2 ne suffit pas sur les reproches rares.

### 6.3 Points techniques

- **Notes de 0 à 20** : apprises comme des valeurs continues, puis bornées à [0, 20] et arrondies. Pour les
  reproches rares, les exemples forts pèsent plus lourd à l'entraînement, sinon le modèle répondrait toujours 0.
- **Règle de la cible appliquée après le modèle** : si la cible n'est pas Lisnard (avec une bonne confiance), la
  tonalité passe à 10 et les reproches à 0.
- **Bibliothèques à installer** : `sentence-transformers`, qui installe aussi `transformers` et `tokenizers`. À
  vérifier dès le départ : qu'elles s'installent bien sous Python 3.14. Sinon, je calcule les vecteurs directement
  avec PyTorch, déjà installé.
- **Versions** : chaque modèle est rangé dans `modeles/vN/` avec sa configuration, ses mesures et la liste des
  annotations utilisées. Chaque note de `scores.csv` porte la version qui l'a produite. Un nouveau modèle refait
  les notes en arrière-plan.

### 6.4 Fiabilité

Pour chaque commentaire, je combine trois signaux :
- l'écart entre les modèles de l'ensemble ;
- la distance aux commentaires annotés ;
- la confiance du classifieur de cible.

Le tout donne un indice de fiabilité (faible, moyenne, bonne). Dans l'interface, on peut masquer les notes peu
fiables. Ce sont aussi ces commentaires que j'annote en priorité au tour suivant.

---

## 7. Mesurer la qualité

Les mesures se font sur l'échantillon de test, jamais vu à l'entraînement, et vont dans
`analyse/RAPPORT_MODELE.md`, ainsi que dans le sous-onglet Modèle.

| Mesure | Ce qu'elle dit |
|---|---|
| Écart moyen (en points sur 20) | combien le modèle se trompe en moyenne, comparé à ma propre constance (5.4) |
| Corrélation de rang | est-ce qu'il classe les commentaires dans le bon ordre (le plus utile pour trier) |
| Détection des reproches forts : précision et rappel de « note ≥ 10 » | sur les critères rares, l'écart moyen est trompeur (répondre 0 partout donne un bon écart moyen) |
| Exactitude de la cible | part des commentaires dont la cible est juste |
| Résultats par source | vérifier que le modèle ne marche pas seulement sur Instagram, par exemple |

Objectifs indicatifs pour la v1 :
- tonalité et pertinence : écart moyen ≤ 3 points ;
- reproches forts : rappel ≥ 70 % ;
- cible : exactitude ≥ 85 %.

S'ils ne sont pas atteints, je le dis avec les chiffres, et on fait un tour d'annotation de plus ou l'option 6.2-3.

---

## 8. Étapes, dans l'ordre, et comment chacune est validée

| # | Étape | Ce qui est livré | Validation |
|---|---|---|---|
| 1 | Page Analyse, visuelle | Onglet Analyse : filtres, tableau paginé, détail, synthèse (comptages seulement), Modèle (vide) ; bouton « Lancer » qui affiche « Modèle pas encore entraîné » | Tu navigues dans tes vrais commentaires avec les filtres |
| 2 | Copie et préparation | `corpus_…csv`, pseudonymisation, contexte (titre, parent), dédoublonnage des textes | Comptages identiques aux fichiers de collecte |
| 3 | Grille | `docs/GRILLE.md` avec exemples réels | Tu la relis et tu la corriges |
| 4 | Annotation pilote | 200 commentaires notés par moi + tes 100 + comparaison | Accord suffisant ; sinon, la grille est corrigée |
| 5 | Annotation, tour 1 | environ 2 000 commentaires (dont 800 ciblés), 150 en double | Contrôles automatiques + ma constance mesurée |
| 6 | Modèle v1 | Vecteurs, référence simple, modèle principal, rapport | Mesures de la section 7 |
| 7 | Branchement | `analyser.py`, bouton Lancer, notes dans le tableau, synthèse complète, export, corrections, analyse auto après collecte | Analyse complète du corpus ; relance incrémentale en quelques secondes |
| 8 | Tours suivants | Apprentissage actif, +500 à 1 000 annotations par tour, modèle v2, v3… | Les mesures s'améliorent ; on s'arrête quand elles plafonnent |
| 9 | Suivi | Chaque mois, 100 nouveaux commentaires annotés pour vérifier que le modèle ne dérive pas (nouveaux sujets, nouvelle campagne) | Écart stable |

L'étape 1 ne dépend pas des autres. Je peux la faire tout de suite, puis enchaîner avec 2 et 3.

---

## 9. Ce que j'en pense : limites et précautions

- **Ironie et sarcasme**
  - Dans les commentaires politiques, ils sont partout (« Quel visionnaire 👏👏 »).
  - Le contexte (publication, commentaire parent) et des exemples ciblés dans la grille aident. Il restera quand
    même des erreurs : c'est la principale source d'erreurs de ce genre de modèle.
- **Le modèle reproduit ma lecture**
  - Il apprend mes notes, donc mes choix d'interprétation.
  - C'est pour ça que ta validation (5.5) et la grille écrite comptent plus que le choix de l'algorithme.
- **Les reproches rares resteront les moins précis**
  - Élocution et « système » : à lire comme des indicateurs de tendance (« la part des commentaires qui reprochent
    l'élocution double en mars »), pas comme une vérité commentaire par commentaire.
- **Ne pas comparer les sources entre elles sans précaution**
  - Sous ses propres posts Instagram, ce sont surtout des abonnés, donc plutôt favorables.
  - Sous les vidéos de médias, le public est plus large et plus critique.
  - Une moyenne « toutes sources » mélange ces publics. La synthèse affichera toujours la répartition par source à
    côté.
- **Précision des notes sur 20**
  - Ni moi ni un humain ne sommes constants à 1 point près. Les notes seront affichées arrondies, et la synthèse
    raisonne en tranches.
- **RGPD**
  - Noter les opinions politiques de personnes identifiables est un traitement de données sensibles.
  - Je propose :
    - tout garder en local ;
    - des auteurs pseudonymisés dans les fichiers d'analyse ;
    - pas de classement ni de profil par auteur, seulement des analyses par commentaire et en agrégé ;
    - pas d'annotation de WhatsApp par Claude (5.6).
- **Langues** : quelques commentaires sont en anglais ou dans d'autres langues. Le modèle multilingue les gère, et
  la grille dit comment les noter.

---

## 10. Décisions (réponses du 2026-11-08)

1. **Reproches : notes symétriques.** 0 = forte critique, 10 = non évoqué, 20 = éloge (forme, système, idées).
   Les sections 2 et 6 sont à lire avec cette échelle : là où elles disent « 0 = absent », c'est désormais 10.
2. **Cible : gardée**, réduite à deux valeurs, L (parle de Lisnard, de son mouvement ou de ses idées) et A (autre
   chose). Si A, la tonalité et les trois reproches valent 10.
3. **« Bravo ! » sans argument : pertinence 8.**
4. **Annotation dans la conversation** (option A), pas par l'API.
5. **WhatsApp annoté comme le reste** et noté par le modèle.
6. **Pas de validation par l'utilisateur** : je valide moi-même (échantillons de test, contrôle de constance).
   L'onglet Analyse permet quand même de corriger une note ; la correction sert au réentraînement suivant.

## 11. État au 2026-11-08

| Étape | État |
|---|---|
| 1. Page Analyse | faite : onglet « Analyse » de l'interface (interface_analyse.py), testée fenêtre masquée |
| 2. Copie et préparation | faite : `analyse/corpus.py` → donnees/analyse/corpus.csv (121 379 commentaires, 97 259 textes distincts, comptages identiques à la collecte) |
| 3. Grille | faite : docs/GRILLE.md |
| 4-5. Annotation, tour 1 | faite : 1 629 commentaires (1 209 pour apprendre, 300 de test tirés au hasard, 120 de test parmi les commentaires ciblés) ; contrôle de constance sur 100 (donnees/analyse/annotation/CONSTANCE.md, surestimé car même session) |
| 6. Modèle | v1 puis v2 (après le tour actif) : entrées normalisées, ridge pour tonalité et pertinence, classement en 3 classes pour forme/système/idées, étalonnage des parts sur la répartition annotée ; mesures dans donnees/analyse/RAPPORT_MODELE.md, référence TF-IDF dans donnees/analyse/reference_tfidf.json |
| 7. Branchement | fait : analyser.py, bouton Lancer, corrections, export, analyse automatique après chaque collecte qui ramène du neuf |
| 8. Tours suivants | tour 2 fait (300 commentaires choisis par le modèle, lots 18-20 → v2). Suivants : `python -m analyse.annotation tirer-actif 300`, annotation, `python -m analyse.modele entrainer`, puis `python analyser.py` |

Fichiers :
- `analyse/annotation.py` : tirage des lots, affichage, enregistrement vérifié des notes.
- `analyse/vecteurs.py` : vecteurs e5, calculés une fois.
- `analyse/modele.py` : entraînement, mesures, rapport.
- `analyser.py` : notation du corpus.

## 12. État au 2026-11-09

**Annotation.** Plus de 12 000 commentaires notés par Claude (lots 1 à 123), dont environ 3 000 réponses lues avec
leur commentaire parent. Trois façons de tirer un lot :
- `tirer-reponses N` : réponses, de préférence sous un parent qui parle de Lisnard ;
- `tirer-actif N` : là où le modèle hésite ;
- `tirer-hasard N [jeu]` : au hasard, pour garder un échantillon représentatif.

Le jeu de test (500 au hasard et 120 parmi les commentaires ciblés) n'a pas changé depuis le tour 1. Toutes les
versions se comparent donc sur les mêmes commentaires.

**Ironie et réponses** (règles dans docs/GRILLE.md, « Cas difficiles ») :
- Une réponse se note à la lumière de son parent : « Un argument choc ! 😂 » sous une critique de Lisnard est une
  défense de Lisnard.
- **Ironie comprise** : on note le sens réel, et la remarque commence par « ironie ». Par exemple, « Un excellent
  présidentiable… MDR » reçoit une tonalité basse.
- **Ironie indécidable** : cible L, 10 partout, pertinence 0 à 3, et la remarque commence par « ironie ? ». Le filtre
  « écarter pertinence < 5 » de la Synthèse retire ces commentaires.
- `voir` affiche le parent sur 450 caractères, la publication et le titre de la vidéo.

**Constance réelle** (renotation à l'aveugle dans une autre session, CONSTANCE.md) :
- cible identique à 96 % ;
- écart moyen de 0,57 en tonalité et de 1,31 en pertinence.

Un modèle ne peut pas faire mieux que ce plancher.

**Modèle.** La méthode à vecteurs seule plafonne : v3 fait comme v2, avec une tonalité à rho 0,62. Le gain vient de
deux pièces :
- `analyse/affinage.py` : multilingual-e5-base affiné sur le processeur.
  - Il lit « commentaire + Il répond à : parent + Publication : titre ».
  - Il a 12 sorties : cible, tonalité, pertinence, et 3 classes pour chacun des trois reproches.
  - 12 % de l'entraînement sert de réglage : on garde la meilleure époque.
- `analyse/ensemble.py` : mélange du réseau et du modèle à vecteurs.
  - Les poids par critère, l'étalonnage par rang et les seuils de fiabilité sont choisis sur le réglage.
  - `construire <réseau>` produit `modeles/vN`.
  - `tout` enchaîne l'affinage et la construction ; c'est le bouton de réentraînement de l'interface.

| Version | Réseau (annotations) | Tonalité rho / écart | Pertinence rho / écart | Système rho | Idées rho | Cible |
|---|---|---|---|---|---|---|
| v3 vecteurs seuls | — (3 729) | 0,62 / 2,45 | — | — | — | 77 % |
| v4 | affine2 (4 429) | 0,658 / 2,33 | 0,728 / 2,28 | 0,35 | 0,39 | 80,4 % |
| v5 | affine3 (≈5 100), vecteurs sur 10 929 | 0,705 / 2,16 | 0,715 / 2,31 | 0,46 | 0,44 | 81,4 % |
| v6 | affine4 (10 929), vecteurs sur 13 729 | 0,713 / 2,02 | 0,646 / 3,14 | 0,44 | 0,43 | 81,4 % |
| v7 | affine4, pertinence recalée, vecteurs sur 14 129 | 0,715 / 2,02 | 0,736 / 2,07 | 0,43 | 0,44 | 81,0 % |
| **v8** | affine5 (11 888, pertinence recalée), vecteurs sur 14 129 | **0,736 / 1,93** | **0,753 / 2,04** | **0,53** | **0,50** | 80,8 % |

Ces mesures portent sur le même test de 500 commentaires tirés au hasard. Pour la forme, la corrélation passe de 0,30
(v4) à 0,37 (v7 et v8).

**v8 est en service** : `python -m analyse` prend la dernière version, et le corpus entier a été renoté par v8 le
2026-11-09. Son réseau, affine5, a appris sur la pertinence recalée ; le réseau pèse désormais 0,60 en pertinence
(0,45 dans v7) et 0,75 en idées (0,50).

Suite possible : annoter de nouveaux lots en contrôlant les moyennes contre les lots 1 à 17 (voir docs/GRILLE.md), puis
`python -m analyse.ensemble tout`.

**Interface.** interface/theme.py (sv_ttk) : cartes, chiffres clés, barres « critiques · non évoqué · éloges », évolution
mensuelle, jauges d'écart avec un repère de constance.

**Dérive de la pertinence, recalée.**

Constat :
- Le jeu de test (lots 1 à 17) suit la grille. Les annotations suivantes ont glissé : la pertinence moyenne des
  commentaires visant Lisnard passe de 8,8 (lots 1 à 17) à 0,8 (lots 131 à 142).
- Les éloges sans argument ont été notés 0 au lieu de 8.
- C'est ce qui a fait reculer la pertinence de v6 (corrélation 0,65, écart 3,1) alors que la tonalité progressait.

Correction (`analyse/recalage_pertinence.py`) :
- 400 commentaires des lots 18 à 142 ont été renotés à l'aveugle selon la grille.
- Une régression (ancienne note, lot, longueur, tonalité, reproches) en déduit la note de la grille. En validation
  croisée : écart 1,54 et corrélation 0,87, contre 3,61 et 0,70 pour l'ancienne note brute. C'est proche de la
  constance mesurée (1,31).
- 11 393 pertinences ont été réécrites. La copie d'avant est `annotations_avant_recalage.csv`.

Les reproches « système » et « idées » sont aussi moins souvent notés dans les lots récents, en partie à cause du
type de lots tirés. Ce point est à surveiller.

**Pièges rencontrés :**
- Deux calculs lourds en parallèle se ralentissent énormément : 14 fils chacun, jusqu'à 9 fois plus lent. On lance
  un entraînement à la fois.
- Les journaux en arrière-plan doivent passer par `python -u`.
- Les annotations ajoutées pendant un affinage ne servent qu'au suivant.

## 13. Réorganisation du 2026-11-09

Le projet a été restructuré en paquets (`commun/`, `collecte/`, `analyse/`, `interface/`), avec les réglages dans
`config/` et la documentation dans `docs/` (plan dans README.md). Sans perte de fonction :
- le code en double est regroupé : lecture et écriture des CSV, verrous et lancement en arrière-plan, versions des
  modèles, étalonnage, fiabilité, mesures ;
- le code mort est retiré : essais Instagram, entraînement du modèle à vecteurs seul (remplacé par
  `analyse.ensemble`), référence TF-IDF ;
- avant/après, sur les mêmes données : la copie de travail est identique octet pour octet, et les notes de v8 sur un
  échantillon de 300 commentaires sont identiques ;
- v8 reconstruit à partir d'affine5 avec le nouveau code donne les mêmes mesures. L'interface a été testée fenêtre
  masquée ;
- `recalage_pertinence appliquer` lit désormais l'ancienne note dans la copie d'avant le recalage : le relancer ne
  change rien, et il ne touche jamais les lots postérieurs au 142.
