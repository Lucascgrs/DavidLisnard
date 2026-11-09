# DavidLisnard : commentaires et analyse des avis

Le projet récupère les commentaires publiés autour de David Lisnard sur YouTube, Instagram et dans une discussion
WhatsApp d'adhérents. À chaque lancement, il ne prend que ce qui est nouveau.

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
│   ├── textes.py                    dates, accents, empreintes
│   ├── taches.py                    une tâche à la fois (verrou), arrêt propre, lancement en arrière-plan
│   └── journal.py                   journal à l'écran et dans donnees/journal.log
├── collecte/                        « python -m collecte »
│   ├── __main__.py                  une source après l'autre, bilan, puis notation des nouveaux
│   ├── depot.py                     format des lignes, ajout sans doublon, état, Excel, bilan
│   ├── sources/                     youtube.py, whatsapp.py, instagram.py
│   ├── perimetre.py                 ajout et retrait de chaînes et de comptes
│   ├── planification.py             Planificateur de tâches de Windows
│   └── connexion_instagram.py       session du compte Instagram
├── analyse/                         « python -m analyse »
│   ├── __main__.py, notation.py     notes de tout le corpus par le modèle en service
│   ├── corpus.py                    copie de travail des commentaires (auteurs pseudonymisés)
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
│   └── theme.py                     thème Windows 11, couleurs, composants
├── docs/
│   ├── GRILLE.md                    ce que veut dire chaque note (la référence de l'annotation)
│   ├── PLAN_COLLECTE.md             conception et historique de la collecte
│   └── PLAN_ANALYSE.md              conception et historique de l'analyse (état des modèles au § 12)
├── donnees/                         tout ce qui est collecté et calculé (privé, voir plus bas)
├── modeles/                         modèles entraînés : vN/ (versions), affineN/ (réseaux affinés)
└── sessions/                        sessions de navigateur (privé)
```

## Commandes

**Collecte**

```
python -m collecte                          toutes les sources (YouTube, WhatsApp, Instagram)
python -m collecte youtube                  une seule source
python -m collecte --reessayer instagram    relancer une source marquée abandonnée
```

**Analyse**

```
python -m analyse                           note ce qui ne l'est pas encore (aussi lancé après chaque collecte)
python -m analyse --sources youtube --du 2026-01-01
python -m analyse --refaire                 renote tout avec le modèle en service
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
| Tableau de bord | Une carte par source : état (prête, en cours, arrêt demandé, abandonnée), total, dernier lancement ; Lancer (ou Réessayer), Arrêter, Forcer l'arrêt, Ouvrir l'Excel, Dossier. « Tout lancer » en haut. Journal en direct. |
| YouTube | Chaînes suivies et leurs commentaires. Ajouter une chaîne par son lien, son @pseudo ou son identifiant, avec sa règle : toutes les vidéos, ou celles qui citent le mot-clé. Retirer, changer la règle, mot-clé, durée de relecture. |
| Instagram | Comptes suivis : posts dans la période, posts lus, commentaires. Ajouter ou retirer un compte. Date de début, posts par lancement, durée de relecture, seuil d'abandon. |
| WhatsApp | Communauté et discussion lues, nombre de messages. |
| Planification | Collecte automatique chaque jour à une heure donnée, éventuellement toutes les N heures. Tâche « DavidLisnard - collecte des commentaires » du Planificateur de tâches, qui lance `Collecter.bat`. |
| Analyse › Commentaires | Filtres (sources, comptes, période, type, recherche, plages de notes, cible, fiabilité, analysé ou non), tableau, détail, « Corriger les notes », export Excel, analyse de la sélection. |
| Analyse › Synthèse | Chiffres clés, perception (critiques · non évoqué · éloges), évolution par mois, sources, exemples. La case « écarter pertinence < 5 » retire l'ironie indécidable, les émojis seuls et le hors-sujet. |
| Analyse › Modèle | Qualité mesurée, apport du réseau affiné, réentraînement, analyse automatique après chaque collecte. |

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
| YouTube | API officielle YouTube Data v3 : dates exactes, réponses rattachées à leur commentaire. Le quota gratuit est de 10 000 unités par jour (la première collecte complète en a pris environ 4 500). Si le quota est atteint, la suite reprend au lancement suivant. |
| WhatsApp | L'application du PC est relancée avec un port de lecture local, ouvert seulement pendant la collecte. Le script ouvre la discussion, remonte jusqu'au dernier message connu, lit la page, et complète par l'export intégré. Il ne fait que lire. La discussion a les messages éphémères activés : collecter au moins une fois par jour. |
| Instagram | Chrome visible, connecté avec le compte dédié. Le script ouvre chaque post et fait défiler les commentaires. La source est abandonnée d'elle-même en cas de blocage, ou si 10 posts prennent plus de 30 minutes. |

**Périmètre (`config/perimetre.json`).** On ne le change que volontairement, pour que les collectes restent
comparables.
- **YouTube** :
  - `"regle": "toutes"` : toutes les vidéos de la chaîne ;
  - `"regle": "mention"` : les vidéos dont le titre ou la description contient le mot-clé (« Lisnard ») ;
  - une vidéo déjà lue est relue si elle a gagné des commentaires ou a moins de 30 jours.
- **WhatsApp** : la communauté et la discussion suivies, sous le nom affiché (accents et pluriels ignorés).
- **Instagram** :
  - comptes suivis, date de début (`depuis`), posts lus au plus par lancement ;
  - âge maximal d'un post relu (21 jours) et seuil d'abandon ;
  - les posts jamais lus passent d'abord. Depuis le 2026-11-09, l'arriéré s'arrête au 2026-07-31.

**Fichiers.** `donnees/<source>/` contient :
- un CSV par compte suivi, qui ne fait que grandir ;
- `<source>_tout.xlsx`, qui les rassemble et est recréé à chaque lancement ;
- `etat.json`, ce qui a déjà été lu.

Le dernier lancement est dans `donnees/bilan.md`, tous les lancements dans `donnees/historique.md`, le détail dans
`donnees/journal.log`. Une source qui échoue n'arrête pas les autres : son erreur est dans le bilan.

**Colonnes (toutes les sources) :**

| Colonne | Contenu |
|---|---|
| `source` | youtube, whatsapp, instagram |
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
| Facebook, X | Connexion obligatoire et fortes protections anti-robots (Facebook) ; API payante (X). |

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
  - un réseau e5 affiné, qui lit chaque commentaire avec son parent et le titre de la publication ;
  - un modèle à vecteurs, plus stable sur les reproches rares.
- **Mesures de qualité** : `donnees/analyse/RAPPORT_MODELE.md` et l'onglet Analyse › Modèle.

**Fichiers de l'analyse** (`donnees/analyse/`) :
- `scores.csv` : les notes du modèle ;
- `corrections.csv` : les notes corrigées à la main dans l'interface. Elles priment, et servent au prochain
  entraînement ;
- `exports/` : les exports Excel ;
- `avancement.json` : l'analyse en cours.

## Précautions

- Ces fichiers relient des personnes à des opinions politiques : ce sont des données sensibles au sens du RGPD.
  C'est particulièrement vrai pour la discussion WhatsApp, qui est privée et où `auteur_id` contient le numéro de
  téléphone.
- Tout reste en local. `donnees/`, `sessions/`, `modeles/`, `config/cles.json` et `config/compte.json` sont exclus
  du partage par `.gitignore`.
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
