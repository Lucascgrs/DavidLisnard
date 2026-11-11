# DavidLisnard : commentaires et analyse des avis

Le projet récupère les commentaires publiés autour de David Lisnard sur YouTube, Bluesky, Instagram et dans une
discussion WhatsApp d'adhérents. À chaque lancement, il ne prend que ce qui est nouveau.

Chaque commentaire reçoit ensuite cinq notes de 0 à 20 et une cible :
- tonalité ;
- forme ;
- proximité avec le système ;
- idées ;
- pertinence ;
- cible : parle-t-il de Lisnard ?

Les notes viennent d'un modèle entraîné sur plus de 14 000 commentaires notés à la main selon
[docs/GRILLE.md](docs/GRILLE.md).

## Démarrage

| Pour | Faire |
|---|---|
| Tout piloter (collecte, comptes suivis, analyse, synthèse) | double-clic sur `Interface.bat` (ou `python -m interface`) |
| Collecter sans l'interface | double-clic sur `Collecter.bat` (ou `python -m collecte`) |
| Installer les bibliothèques | `python -m pip install -r requirements.txt` |

Toutes les commandes se lancent depuis le dossier du projet.

Ce qu'il faut faire une seule fois :
- **Bluesky** : rien à faire, l'API est ouverte et sans compte.
- **YouTube** : la clé de l'API YouTube Data v3 est dans `config/cles.json` (modèle : `config/cles.exemple.json`).
  Sans clé, pas de collecte YouTube. Conseil : sur console.cloud.google.com → Identifiants, restreindre la clé à
  « YouTube Data API v3 ».
- **WhatsApp** : l'application du PC doit être liée au téléphone. Si elle ne l'est pas, la collecte affiche le QR
  code et attend 10 minutes (sur le téléphone : WhatsApp → Appareils connectés → Connecter un appareil). Fait le
  2026-11-07.
- **Instagram** : la session du compte dédié est dans `sessions/cookies_web.json`. Pour la refaire :
  `python -m collecte.connexion_instagram`, avec le compte décrit dans `config/compte.json` (modèle :
  `config/compte.exemple.json`).

## Organisation

```
DavidLisnard/
├── Interface.bat, Collecter.bat     lanceurs (double-clic)
├── requirements.txt
├── config/                          réglages
│   ├── perimetre.json               ce qui est collecté (modifiable depuis l'interface ; copie en .bak)
│   ├── cles.json                    clé YouTube (privée)
│   ├── compte.json                  compte Instagram de collecte (privé)
│   └── planification.json           collecte automatique choisie dans l'interface
├── commun/                          socle partagé
│   ├── config.py                    emplacements, sources, lecture des réglages
│   ├── fichiers.py                  JSON et CSV (écriture atomique)
│   ├── sauvegarde.py                « python -m commun.sauvegarde » : la sauvegarde unique (voir « Sauvegarde »)
│   ├── textes.py                    dates, accents, empreintes
│   ├── taches.py                    une tâche à la fois (verrou), arrêt propre, lancement en arrière-plan
│   └── journal.py                   journal à l'écran et dans donnees/journal.log
├── collecte/                        « python -m collecte »
│   ├── __main__.py                  une source après l'autre, bilan, puis notation des nouveaux
│   ├── depot.py                     format des lignes, ajout sans doublon, état, Excel, bilan
│   ├── sources/                     youtube.py, bluesky.py, whatsapp.py, instagram.py
│   ├── perimetre.py                 ajout et retrait de chaînes et de comptes
│   ├── planification.py             Planificateur de tâches de Windows
│   └── connexion_instagram.py       session du compte Instagram
├── analyse/                         « python -m analyse »
│   ├── __init__.py                  modèle de langue de départ et mode hors ligne (voir « Modèles »)
│   ├── __main__.py, notation.py     notes de tout le corpus par le modèle en service
│   ├── corpus.py                    copie de travail des commentaires (auteurs pseudonymisés, doublons marqués)
│   ├── vecteurs.py                  vecteurs de sens (e5 multilingue)
│   ├── annotation.py                lots à noter à la main, enregistrement vérifié des notes
│   ├── modele.py                    modèle à vecteurs et briques communes
│   ├── affinage.py                  réseau e5 affiné (lit le commentaire avec son parent)
│   ├── ensemble.py                  combinaison des deux : la version en service
│   ├── mesures.py                   qualité sur le jeu de test, rapport
│   ├── criteres.py, stockage.py, versions.py   définitions, fichiers, versions enregistrées
│   └── recalage_pertinence.py       correction de la dérive d'annotation du 2026-11-09
├── interface/                       « python -m interface »
│   ├── application.py               fenêtre, en-tête, boucles de rafraîchissement
│   ├── onglets_collecte.py          tableau de bord, YouTube, Instagram, WhatsApp, planification
│   ├── onglet_analyse.py            onglet Analyse et ses sous-onglets :
│   │   analyse_commentaires.py, analyse_synthese.py, analyse_modele.py
│   ├── onglet_themes.py             onglet Thèmes (lecture par thèmes, voir « Thèmes »)
│   └── theme.py                     thème Windows 11, couleurs, composants
├── critiques/                       « python -m critiques » : thèmes des éloges et des critiques (voir « Thèmes »)
│   ├── __main__.py                  commandes (tirer, voir, noter, synthèses…)
│   └── donnees.py                   sélection, lots, rattachements, comptes par thème
├── web/                             le site public, « python -m web » (voir « Site public »)
│   ├── export.py                    ce qui est publié : commentaires, publications, statistiques
│   ├── publication.py               installer la base, publier les données, mettre les pages en ligne
│   ├── supabase.py, vercel.py       les deux services (API, sans Node)
│   ├── acces.py                     jetons et clés (config/web.json, privé)
│   ├── schema.sql                   tables, recherche en français, filtres, droits de lecture
│   └── site/                        les pages : index (le projet), statistiques, commentaires, thèmes ; css/, js/
├── docs/
│   ├── FONCTIONNEMENT.html / .pdf   document illustré « comment marche le projet » (source / PDF, python -m docs)
│   ├── GRILLE.md                    ce que veut dire chaque note (la référence de l'annotation)
│   ├── PLAN_COLLECTE.md             conception et historique de la collecte
│   └── PLAN_ANALYSE.md              conception et historique de l'analyse (état des modèles au § 12)
├── donnees/                         tout ce qui est collecté et calculé (privé, voir plus bas)
├── modeles/                         modèles entraînés : vN/ (versions), affineN/ (réseaux affinés) ; voir « Modèles »
└── sessions/                        sessions de navigateur (privé)
```

## Commandes

**Collecte**

```
python -m collecte                          toutes les sources (YouTube, Bluesky, WhatsApp, Instagram)
python -m collecte youtube                  une seule source
python -m collecte --reessayer instagram    relancer une source marquée abandonnée
```

**Thèmes** (lecture à la demande, voir « Thèmes »)

```
python -m critiques etat                    où en est la lecture
python -m critiques tirer | voir N | noter N fichier   lire le lot suivant
python -m critiques syntheses fichier       enregistrer les synthèses par thème et par sens
```

**Sauvegarde** (voir « Sauvegarde »)

```
python -m commun.sauvegarde                 refaire la sauvegarde (aussi faite à la fin de chaque collecte)
python -m commun.sauvegarde --voir          ce que contient la sauvegarde actuelle
```

**Analyse**

```
python -m analyse                           note ce qui ne l'est pas encore (aussi lancé après chaque collecte)
python -m analyse --sources youtube --du 2026-01-01
python -m analyse --refaire                 renote tout avec le modèle en service
```

**Document de fonctionnement**

```
python -m docs                              regénère docs/FONCTIONNEMENT.pdf depuis docs/FONCTIONNEMENT.html
```

**Site public**

```
python -m web tout                          installer la base, publier les données, mettre les pages en ligne
python -m web publier                       envoyer ce qui a changé (aussi fait après chaque collecte)
python -m web deployer                      remettre les pages en ligne après une modification de web/site/
python -m web apercu                        les pages en local (http://localhost:8000), sur les données en ligne
```

**Annotation et entraînement**

```
python -m analyse.annotation etat              où en est l'annotation
python -m analyse.annotation tirer-actif 100   prochain lot : commentaires où le modèle hésite
python -m analyse.annotation tirer-reponses 100   prochain lot : réponses, lues avec leur parent
python -m analyse.annotation voir 143          afficher un lot
python -m analyse.annotation noter 143 notes.txt   enregistrer ses notes (vérifiées)
python -m analyse.ensemble tout                réentraînement complet : réseau affiné puis combinaison (3 à 4 h)
python -m analyse.ensemble construire affineN  combinaison seule à partir d'un réseau déjà affiné (25 min)
```

Un réentraînement occupe tout le processeur : ne jamais en lancer deux à la fois. La nouvelle version
(`modeles/vN/`) est utilisée dès l'analyse suivante.

## Interface

| Onglet | Ce qu'on y fait |
|---|---|
| Tableau de bord | Une carte par source (YouTube, Bluesky, WhatsApp, Instagram) : état (prête, en cours, arrêt demandé, abandonnée), total, dernier lancement ; Lancer (ou Réessayer), Arrêter, Forcer l'arrêt, Ouvrir l'Excel, Dossier. « Tout lancer » en haut. Journal en direct. |
| YouTube | Chaînes suivies et leurs commentaires. Ajouter une chaîne par son lien, son @pseudo ou son identifiant, avec sa règle : toutes les vidéos, ou celles qui citent le mot-clé. Retirer, changer la règle, mot-clé, durée de relecture. Case « Chercher aussi ailleurs que sur les chaînes suivies » : les vidéos des autres chaînes trouvées par la recherche (dernière ligne du tableau). |
| Instagram | Comptes suivis : posts dans la période, posts lus, commentaires. Ajouter ou retirer un compte. Date de début, posts par lancement, durée de relecture, seuil d'abandon. |
| WhatsApp | Communauté et discussion lues, nombre de messages. |
| Planification | Collecte automatique chaque jour à une heure donnée, éventuellement toutes les N heures. Tâche « DavidLisnard - collecte des commentaires » du Planificateur de tâches, qui lance `Collecter.bat`. |
| Analyse › Commentaires | Filtres (sources, comptes, période, type, recherche, plages de notes, cible, fiabilité, analysé ou non, doublons masqués ou montrés), tableau, détail, « Corriger les notes », export Excel, analyse de la sélection. |
| Analyse › Synthèse | Chiffres clés, perception (critiques · non évoqué · éloges), évolution par mois, sources, exemples. La case « écarter pertinence < 5 » retire l'ironie indécidable, les émojis seuls et le hors-sujet. La case « Pondérer par les « j'aime » » fait peser chaque commentaire 1 + ses « j'aime » (voir « Doublons et « j'aime » »). |
| Analyse › Modèle | Qualité mesurée, apport du réseau affiné, réentraînement, analyse automatique après chaque collecte. |
| Thèmes | Les thèmes des éloges, critiques et doutes : filtres par famille, sens et mot, comptes en commentaires et en auteurs distincts, évolution par mois, synthèses et commentaires de chaque thème. |

À savoir :
- **Lancer.** La collecte ou l'analyse tourne en arrière-plan. Elle continue si l'on ferme la fenêtre, et
  l'interface la retrouve à la réouverture. Une même tâche n'est jamais lancée deux fois en même temps, même depuis
  le terminal ou la planification. Le verrou est le fichier `donnees/<tâche>/EN_COURS`.
- **Arrêter.** L'arrêt est propre : la tâche s'arrête à la fin de la vidéo, du post ou du lot en cours (fichier
  `donnees/<tâche>/ARRET`). Ce qui est lu est gardé. Pour WhatsApp, la lecture en cours est refaite entièrement au
  lancement suivant, pour ne pas laisser de trou.
- **Erreurs.** Les erreurs inattendues de l'interface s'affichent et sont notées dans
  `donnees/erreurs_interface.log`.

## Collecte

| Source | Méthode |
|---|---|
| YouTube | API officielle YouTube Data v3 : dates exactes, réponses rattachées à leur commentaire. Le quota gratuit est de 10 000 unités par jour (la première collecte complète en a pris environ 4 500). Si le quota est atteint, la suite reprend au lancement suivant. En plus des chaînes suivies, la recherche du mot-clé dans tout YouTube (`search.list`, 100 unités par page de 50 vidéos) ramène les vidéos des autres chaînes. |
| Bluesky | API publique `api.bsky.app`, gratuite et sans compte. Recherche des messages qui citent le mot-clé, puis lecture des réponses de chaque fil. L'API refuse la pagination par curseur sans compte : on avance par dates. |
| WhatsApp | L'application du PC est relancée avec un port de lecture local, ouvert seulement pendant la collecte. Le script ouvre la discussion, remonte jusqu'au dernier message connu, lit la page, et complète par l'export intégré. Il ne fait que lire. La discussion a les messages éphémères activés : collecter au moins une fois par jour. |
| Instagram | Chrome visible, connecté avec le compte dédié. Le script ouvre chaque post et fait défiler les commentaires. La source est abandonnée d'elle-même en cas de blocage, ou si 10 posts prennent plus de 30 minutes. |

**Périmètre (`config/perimetre.json`).** On ne le change que volontairement, pour que les collectes restent
comparables.
- **YouTube** :
  - `"regle": "toutes"` : toutes les vidéos de la chaîne ;
  - `"regle": "mention"` : les vidéos dont le titre ou la description contient le mot-clé (« Lisnard ») ;
  - une vidéo déjà lue est relue si elle a gagné des commentaires ou a moins de 30 jours ;
  - `"recherche"` : au-delà des chaînes suivies. `active`, `depuis` (date la plus ancienne), `pages_par_lancement`
    (5 pages = 500 unités de quota au plus). Seules les vidéos dont le titre ou la description contient le mot-clé
    sont gardées, et celles des chaînes suivies sont laissées à leur propre règle. Les commentaires vont dans
    `donnees/youtube/autres_chaines.csv`, chacun sous le nom de sa chaîne (groupe « autre »). À chaque lancement :
    d'abord les vidéos récentes, puis la suite de l'arriéré.
- **Bluesky** (`"bluesky"`) : `depuis`, `pages_par_lancement` (100 messages par page), `relire_si_moins_de_jours`
  (7 : réponses et « j'aime » des messages récents sont mis à jour). Sont pris : les messages qui citent le mot-clé,
  toutes les réponses sous un message de tête qui le cite, et les réponses à une réponse qui le cite. Un seul
  compte, « Recherche « Lisnard » », dans `donnees/bluesky/`. La « publication » est le message de tête du fil.
- **WhatsApp** : la communauté et la discussion suivies, sous le nom affiché (accents et pluriels ignorés).
- **Instagram** :
  - comptes suivis, date de début (`depuis`), posts lus au plus par lancement ;
  - âge maximal d'un post relu (21 jours) et seuil d'abandon ;
  - les posts jamais lus passent d'abord. Depuis le 2026-11-09, l'arriéré s'arrête au 2026-07-31.

**Fichiers.** `donnees/<source>/` contient :
- un CSV par compte suivi, qui ne fait que grandir ;
- `<source>_tout.xlsx`, qui les rassemble et est recréé à chaque lancement ;
- `etat.json`, ce qui a déjà été lu ;
- `likes.json`, les « j'aime » qui ont changé depuis la première collecte d'un commentaire (voir « Doublons et
  « j'aime » »).

Le dernier lancement est dans `donnees/bilan.md`, tous les lancements dans `donnees/historique.md`, le détail dans
`donnees/journal.log`. Une source qui échoue n'arrête pas les autres : son erreur est dans le bilan.

**Colonnes (toutes les sources) :**

| Colonne | Contenu |
|---|---|
| `source` | youtube, bluesky, whatsapp, instagram |
| `compte_source` | chaîne, compte ou discussion où le commentaire a été pris |
| `publication_id`, `publication_titre`, `publication_lien`, `publication_date` | la vidéo ou le post commenté (vide pour WhatsApp) |
| `commentaire_id` | identifiant donné par la plateforme |
| `type` | `principal` ou `réponse` |
| `parent_id` | commentaire auquel il répond (vide si principal, ou si le message cité n'a pas été retrouvé) |
| `auteur`, `auteur_id` | pseudo ou nom affiché, et identifiant du compte |
| `date` | heure de Paris |
| `date_exacte` | `oui` (YouTube, Instagram : à la seconde), `à la minute` (WhatsApp) |
| `texte` | le commentaire |
| `likes` | mentions « j'aime » au moment de la collecte |
| `collecte_le` | date de la première collecte de la ligne |

Les textes qui commencent par `=`, `+`, `-` ou `@` sont précédés d'une espace, pour qu'Excel ne les prenne pas pour
des formules.

**Sources non collectées :**

| Source | Raison |
|---|---|
| TikTok | Techniquement possible et accepté par toi le 2026-11-07. Il suffirait de piloter un Chrome normal par son port de débogage : la liste des vidéos et l'API des commentaires répondent. Mais le classifieur de sécurité de Claude Code refuse ces commandes. |
| Reddit | Reddit bloque ce réseau, même dans un navigateur normal, et son API exige un compte avec une application déclarée. |
| Facebook, Threads, X | Connexion obligatoire et fortes protections anti-robots (Facebook, Threads) ; API payante (X). À tenter seulement si la recherche YouTube et Bluesky ne suffisent pas, et avec un compte créé pour la collecte (comme celui d'Instagram), pour qu'un bannissement ne touche pas un compte personnel. |

## Analyse

| Critère | 0 | 10 | 20 |
|---|---|---|---|
| Tonalité envers Lisnard | hostile | neutre | très favorable |
| Forme (élocution, charisme, communication) | reproche fort | non évoqué | éloge |
| Système (trop proche de Macron, de l'establishment) | reproche fort | non évoqué | perçu hors système |
| Idées (programme, positions) | rejet | non évoqué | adhésion |
| Pertinence pour l'analyse | n'apporte rien | avis sans argument (« Bravo ! » = 8) | avis argumenté |

Chaque commentaire a aussi :
- une **cible** : L s'il parle de Lisnard, A sinon (la tonalité et les reproches valent alors 10) ;
- une **fiabilité** : bonne, moyenne ou faible.

**Comment c'est fait** (détail et historique des versions dans [docs/PLAN_ANALYSE.md](docs/PLAN_ANALYSE.md), § 12) :
- **Copie de travail** : `donnees/analyse/corpus.csv`, avec les auteurs pseudonymisés. Les fichiers de collecte ne
  sont jamais modifiés.
- **Annotation** : les commentaires sont notés à la main par Claude, par lots de 100, selon la grille
  (`donnees/analyse/annotation/`).
  - Un jeu de test fixe de 500 commentaires tirés au hasard n'est jamais appris : il sert à mesurer.
  - Les réponses sont lues avec le commentaire auquel elles répondent.
- **Ironie** :
  - comprise : notée selon son sens réel ;
  - indécidable : pertinence basse (0 à 3), pour pouvoir l'écarter.
- **Modèle en service** (`modeles/vN/`, la version la plus récente). C'est la moyenne pondérée de deux modèles :
  - un réseau e5 affiné, qui lit chaque commentaire (256 jetons au plus) avec son parent (128) et le titre de la
    publication (20) ;
  - un modèle à vecteurs, plus stable sur les reproches rares.
- **Mesures de qualité** : `donnees/analyse/RAPPORT_MODELE.md` et l'onglet Analyse › Modèle.

**Doublons et « j'aime ».**
- **Doublon** : le même texte, du même auteur, dans la même source (un compte qui colle « Au top 👌 » sous
  164 publications). La casse, les accents, la ponctuation et les espaces ne comptent pas. Seul le premier publié
  compte ; les suivants restent dans les fichiers et sont notés, mais sortent de la synthèse, du site et des thèmes
  (colonne `doublon_de` de `corpus.csv` ; case « Montrer aussi les doublons » dans l'interface). Le même texte écrit
  par des personnes différentes n'est pas un doublon : ce sont autant de voix. Le 2026-11-11 : 9 424 doublons sur
  155 044 commentaires (6,1 %).
- **Vue pondérée par les « j'aime »**, en option, dans la Synthèse et sur la page Statistiques du site : chaque
  commentaire pèse 1 + ses « j'aime » (lui-même et ceux qui l'approuvent), au lieu d'une voix par commentaire.
  Les « j'aime » sont ceux de la dernière lecture : quand une publication est relue, les nouveaux comptes vont dans
  `donnees/<source>/likes.json`. Un commentaire dont la publication n'est plus relue garde ses « j'aime » d'alors.

**Modèles** (`modeles/`).
- On garde les versions en service récentes (`v10`, `v11` et les suivantes) et le réseau affiné de chacune
  (`reseau` dans `modeles/vN/infos.json` : `affine7` pour v10, `affine8` pour v11). Les versions v1 à v9, l'essai
  `essai_long` et les réseaux `affine1` à `affine6` ont été supprimés le 2026-11-11 (3,3 Go). Avant de supprimer un
  `affineN`, vérifier qu'aucune version gardée ne le cite.
- **Hors ligne.** Le modèle de départ (e5) est sur le disque depuis son premier téléchargement. Tant que cette copie
  existe, `analyse/__init__.py` met `HF_HUB_OFFLINE=1` : plus de vérification en ligne à chaque chargement, donc plus
  de message « You are sending unauthenticated requests to the HF Hub », un chargement plus rapide, et tout marche
  sans connexion. Le réglage se lève seul si l'on change de modèle de départ (`MODELE_LANGUE`, pas encore
  téléchargé). Pour forcer une vérification en ligne : `$env:HF_HUB_OFFLINE = "0"` avant la commande.

**Fichiers de l'analyse** (`donnees/analyse/`) :
- `scores.csv` : les notes du modèle ;
- `corrections.csv` : les notes corrigées à la main dans l'interface. Elles priment, et servent au prochain
  entraînement ;
- `exports/` : les exports Excel ;
- `avancement.json` : l'analyse en cours.

## Site public

Le site montre le travail à tout le monde : explication du projet, statistiques filtrables par semaine,
commentaires filtrables (curseurs, puces) avec la vidéo d'origine, thèmes des éloges et des critiques. Adresse : `site_url` dans `config/web.json`.

- **Pages** (`web/site/`, HTML + JavaScript sans bibliothèque ni étape de construction) hébergées par **Vercel**.
- **Données** dans **Supabase** (PostgreSQL) : tables `commentaires`, `publications`, `syntheses`. Le public lit avec
  la clé publique, en lecture seule (règles RLS de `web/schema.sql`) ; seul `python -m web publier` écrit, avec la clé
  secrète. Les filtres de la page Commentaires sont appliqués par la base (fonctions `selection` et `evolution`) ;
  la page Statistiques recalcule tout dans le navigateur à partir du « cube » (comptages par semaine et par compte).
- **Pas d'API à héberger** (ni Railway ni autre) : les pages interrogent Supabase directement. Les deux offres
  gratuites suffisent (base d'environ 150 Mo sur 500).
- **Ce qui est publié** : les commentaires notés de YouTube, d'Instagram et de Bluesky, sans auteur ni doublon.
  WhatsApp (discussion privée d'adhérents) ne l'est jamais.
- **Date et modèle** : chaque page affiche, sous son titre et en pied de page, la date de la dernière collecte et
  la version du modèle (avec sa date d'entraînement), lues dans la synthèse « meta ».
- **Pondération** : sur la page Statistiques, l'interrupteur « Pondérer par les « j'aime » » (colonnes `p_…` du cube).
- **Mise à jour** : après chaque collecte qui ramène du neuf, la publication suit la notation (seules les lignes
  nouvelles ou changées partent, grâce à `donnees/web/publie.json`). Bouton « Mettre à jour le site » dans l'onglet
  Analyse → Modèle.
- **Mise en place** (une fois) : coller un jeton Vercel (vercel.com/account/settings/tokens) et un jeton Supabase
  (supabase.com/dashboard/account/tokens) dans `config/web.json`, puis `python -m web tout`.
- Un projet Supabase gratuit sans aucune visite pendant 7 jours est mis en pause : `python -m web installer` le relance.

## Thèmes

Ce qu'on lui reproche et ce qu'on salue, rangé par thème (onglet **Thèmes** de l'interface, page **Thèmes** du site) :

- **Sélection** : les commentaires qui parlent de lui (cible L), de pertinence 12 ou plus, d'au moins 20 mots, de
  fiabilité bonne ou moyenne (les notes relues et corrigées comptent comme bonnes). Un même texte collé plusieurs
  fois n'est lu qu'une fois.
- **Lecture** : chaque commentaire retenu est lu par Claude, avec son parent et le titre de la publication. Il est
  rattaché à un ou plusieurs thèmes avec un sens (éloge, critique, doute ou question) et une phrase courte. La liste
  des thèmes se construit pendant la lecture ; les thèmes proches sont fusionnés à la fin d'un passage, puis une
  synthèse est rédigée par thème et par sens.
- **Comptes** : en commentaires et en auteurs distincts (empreinte anonyme), pour qu'un habitué ne pèse pas plus
  qu'un autre. Le site ne garde que YouTube et Instagram, sans auteurs.
- **Mise à jour** : à la demande, pas à chaque collecte, et toujours par Claude. `python -m critiques tirer`,
  `voir`, `noter` jusqu'à « Rien de nouveau à lire », puis `proches`, `fusionner`, `syntheses` et
  `python -m web publier`. Seuls les commentaires nouveaux sont lus : ce qui a été lu ne l'est jamais deux fois.
- **Pas de rangement automatique.** Ranger seuls les nouveaux commentaires par proximité de leurs vecteurs a été
  essayé et mesuré le 2026-11-11, puis retiré : 20 à 30 % de rangements justes avec le commentaire lu le plus
  proche ; 84 % avec un classement appris et sévère, mais pour 8 % des commentaires seulement.
- **Fichiers** : `donnees/critiques/` (`themes.json`, `rattachements.csv`, `lus.csv`, `lots/`, `notes/`).

## Sauvegarde

`donnees/sauvegardes/donnees.zip` : une copie compressée de ce qu'on ne peut pas refaire.
- **Contenu**, dans cet ordre : WhatsApp et Instagram d'abord (messages éphémères, anciennes publications), puis
  YouTube et Bluesky (CSV bruts, `etat.json`, `likes.json`), puis le travail fait à la main : annotations
  (`donnees/analyse/annotation/`), corrections de l'interface, lecture par thèmes (`donnees/critiques/`).
  Environ 18 Mo, une seconde.
- **Une seule sauvegarde** : la nouvelle est écrite dans un fichier temporaire, relue en entier, puis remplace
  l'ancienne. On n'est jamais sans sauvegarde.
- **Garde-fou** : les CSV de collecte ne font que grandir. Si l'un d'eux a rétréci ou disparu, l'ancienne
  sauvegarde est gardée, la nouvelle est mise de côté (`donnees_a_verifier.zip`) et le journal le signale.
  `--forcer` passe outre.
- **Quand** : à la fin de chaque collecte, et à la demande (bouton « Sauvegarder » de l'interface ou
  `python -m commun.sauvegarde`).

## Précautions

- Ces fichiers relient des personnes à des opinions politiques : ce sont des données sensibles au sens du RGPD.
  C'est particulièrement vrai pour la discussion WhatsApp, qui est privée et où `auteur_id` contient le numéro de
  téléphone.
- Tout reste en local, sauf ce que publie le site : texte et notes des commentaires publics YouTube, Instagram et Bluesky,
  sans auteur ni identifiant d'auteur (`web/export.py`). `donnees/`, `sessions/`, `modeles/`, `config/cles.json`,
  `config/compte.json` et `config/web.json` sont exclus du partage par `.gitignore`.
- Pseudonymiser les auteurs avant toute analyse partagée : la copie de travail de l'analyse l'est déjà.

## Ancienne organisation (avant le 2026-11-09)

Les plans de `docs/` citent parfois les anciens chemins :

| Avant | Maintenant |
|---|---|
| `python collecter.py …`, `commun.py`, `sources/*.py` | `python -m collecte …`, `commun/` et `collecte/depot.py`, `collecte/sources/` |
| `python analyser.py …` | `python -m analyse …` (`analyse/notation.py`) |
| `python interface.py`, `interface_analyse.py`, `theme.py` | `python -m interface`, `interface/` |
| `perimetre.json`, `cles.json`, `compte.json` | `config/` |
| `python essais/connexion.py` | `python -m collecte.connexion_instagram` |
| `essais/` (méthodes Instagram comparées le 2026-11-07) | retiré ; copie dans `donnees/sauvegardes/code_avant_reorganisation_2026-11-09.zip` |
| `analyse/GRILLE.md`, `PLAN.md`, `PLAN_ANALYSE.md` | `docs/GRILLE.md`, `docs/PLAN_COLLECTE.md`, `docs/PLAN_ANALYSE.md` |
| `python -m analyse.modele entrainer` (modèle à vecteurs seul) | remplacé par `python -m analyse.ensemble tout` |
