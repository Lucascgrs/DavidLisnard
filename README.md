# DavidLisnard : commentaires et analyse des avis

Le projet récupère les commentaires publiés autour de David Lisnard sur YouTube, Bluesky, Instagram et dans
sur Facebook (sa Page officielle et cinq groupes publics de soutiens) et sur X (ses comptes, ceux de soutiens et les
posts qui le citent). À chaque lancement, il ne prend que ce qui est nouveau.

Chaque commentaire reçoit ensuite cinq notes de 0 à 20 et une cible :
- tonalité ;
- forme ;
- proximité avec le système ;
- idées ;
- pertinence ;
- cible : parle-t-il de Lisnard ?

Les notes viennent d'un modèle entraîné sur les commentaires notés à la main par Claude selon
[docs/GRILLE.md](docs/GRILLE.md). Les commentaires argumentés sont en plus lus par Claude et rangés par thème.

À part, pour les modérateurs des groupes Facebook : chaque commentaire Facebook est aussi classé « à modérer »,
« question » ou « autre » par un second modèle, juste après la collecte (voir « Modération »).

| Document | Pour |
|---|---|
| [docs/PROCESS.md](docs/PROCESS.md) | **mettre à jour le projet** : toutes les étapes, dans l'ordre |
| ce README | se servir du projet : commandes, fichiers, réglages |
| [docs/FONCTIONNEMENT.pdf](docs/FONCTIONNEMENT.pdf) | comprendre comment il marche (illustré, chiffres à jour) |
| [docs/GRILLE.md](docs/GRILLE.md) | ce que veut dire chaque note (la référence de l'annotation) |
| [docs/HISTORIQUE.md](docs/HISTORIQUE.md) | ce qui a été décidé, essayé ou abandonné, versions du modèle |
| [docs/TRI_DES_CRITIQUES.pdf](docs/TRI_DES_CRITIQUES.pdf) | la méthode des 5 catégories de critiques et de doutes |

## Démarrage

| Pour | Faire |
|---|---|
| Tout piloter (collecte, comptes suivis, analyse, synthèse, modération) | double-clic sur `Interface.bat` (ou `python -m commun.interface`) |
| Collecter sans l'interface | double-clic sur `Collecter.bat` (ou `python -m commun.collecte`) |
| Regarder un entraînement en cours (lot lu, perte, poids) | s'ouvre seule au lancement de l'affinage ; la fermer n'arrête pas l'entraînement ; rouvrir : `Suivi.bat` (ou `python -m commun.suivi`) |
| Installer les bibliothèques | `python -m pip install -r requirements.txt` |

Toutes les commandes se lancent depuis le dossier du projet.

Ce qu'il faut faire une seule fois :
- **Bluesky** : rien à faire, l'API est ouverte et sans compte.
- **YouTube** : la clé de l'API YouTube Data v3 est dans `config/cles.json` (modèle : `config/cles.exemple.json`).
  Sans clé, pas de collecte YouTube. Conseil : sur console.cloud.google.com → Identifiants, restreindre la clé à
  « YouTube Data API v3 ».
- **Instagram** : la session du compte dédié est dans `donnees/sessions/cookies_web.json`. Pour la refaire :
  `python -m commun.collecte.connexion_instagram`, avec le compte décrit dans `config/compte.json` (modèle :
  `config/compte.exemple.json`).
- **Facebook** : le compte dédié (« Fande Lisnard ») est dans `config/facebook.env` (`FB_MAIL`, `FB_MDP` ; modèle :
  `config/facebook.exemple.env`). `python -m commun.collecte.connexion_facebook` ouvre Chrome une seule fois pour se
  connecter et enregistre la session (`donnees/sessions/facebook_cookies.json`) ; `--verifier` dit si elle est encore valide.
- **X** : le compte dédié (`fandelisnard`) est dans `config/x.env` (`X_PSEUDO`, `X_MDP`, `X_MAIL` facultatif ;
  modèle : `config/x.exemple.env`). La session (`donnees/sessions/x_cookies.json` : cookies `auth_token` et `ct0`) se fait
  par `python -m commun.collecte.connexion_x`, qui ouvre Chrome (profil `donnees/sessions/x_profil/`) et saisit pseudo et mot de
  passe ; X refuse le mot de passe envoyé par un script. Si X limite les connexions (« Nous avons temporairement
  limité votre connexion », arrivé le 2026-11-13 après plusieurs essais), attendre quelques heures, ou copier les
  deux cookies depuis un navigateur connecté (F12 → Application → Cookies → x.com) dans `donnees/sessions/x_cookies.json`,
  puis lancer `python -m commun.collecte.connexion_x --profil`, qui les recopie dans le profil. Le profil garde ainsi la
  session : quand elle expire, la collecte la fait renouveler par X sans fenêtre ni mot de passe ; le mot de passe ne
  sert que si X a annulé la session. `--verifier` dit si la session marche. Ne jamais se déconnecter de ce compte : la déconnexion tue la session.

## Organisation

```
DavidLisnard/
├── README.md                        se servir du projet (ce fichier)
├── CLAUDE.md                        règles de travail de Claude sur ce projet
├── Interface.bat, Collecter.bat, Suivi.bat   lanceurs (double-clic)
├── requirements.txt
├── config/                          réglages
│   ├── perimetre.json               ce qui est collecté (modifiable depuis l'interface ; copie en .bak)
│   ├── cles.json                    clé YouTube (privée)
│   ├── compte.json                  compte Instagram de collecte (privé)
│   ├── facebook.env                 compte Facebook de collecte (privé ; modèle facebook.exemple.env)
│   ├── x.env                        compte X de collecte (privé ; modèle x.exemple.env)
│   ├── web.json, cloudflare.env     accès Supabase et Vercel, clés R2 (privés)
│   └── planification.json           collecte automatique choisie dans l'interface
│
│   ── Un dossier par site web ──
├── commentaires/                    le site public des commentaires, « python -m commentaires » (voir « Site public »)
│   ├── export.py                    ce qui est publié : commentaires, publications, statistiques
│   ├── publication.py               installer la base, publier les données, mettre les pages en ligne
│   ├── supabase.py, vercel.py       les deux services (API, sans Node)
│   ├── acces.py, comptes.py         jetons et clés (config/web.json, privé), comptes de connexion
│   ├── schema.sql                   tables, recherche en français, filtres, droits de lecture (aussi pour la modération)
│   └── site/                        les pages : index (le projet), commentaires, thèmes ; css/, js/
├── moderation/                      le site de modération, « python -m moderation » (voir « Modération »)
│   ├── __main__.py                  commandes (etat, classer, tirer, noter, entrainer…)
│   ├── donnees.py                   commentaires Facebook, annotations, notes, lots
│   ├── modele.py                    entraînement, mesures, classement
│   ├── publication.py, reponses.py  envoi vers Supabase, réponses préparées
│   ├── PROMPT_GEMINI*.md            consignes de lecture des commentaires
│   └── site.py, site/               les pages du site de modération
├── verification/                    le site de vérification des chiffres, « python -m verification »
│   │                                (voir verification/README.md)
│   ├── commun/, conclusions.py, …   corpus, téléchargements, contrôles, synthèse
│   ├── themes/NN_nom/               les scripts de chaque thème (registre, téléchargement, calculs)
│   └── site.py, site/               les pages du site de vérification
├── proximite/                       la proximité des candidats, « python -m proximite » (voir « Proximité des candidats »)
│   ├── collecte.py                  liste des candidats (candidats2027.org), programmes, texte de chaque document
│   ├── axes.py                      les trois axes et leurs sous-thèmes (grille : docs/GRILLE_PROXIMITE.md)
│   ├── mesures.py, positions.py     lecture, mesures notées ; positions sur les axes et distances
│   └── site.py, site/               les pages du site « Proximité des candidats »
│
│   ── Code commun aux sites ──
├── commun/
│   ├── config.py                    emplacements, sources, lecture des réglages
│   ├── fichiers.py                  JSON et CSV (écriture atomique)
│   ├── sauvegarde.py                « python -m commun.sauvegarde » : la sauvegarde unique (voir « Sauvegarde »)
│   ├── textes.py                    dates, accents, empreintes
│   ├── taches.py                    une tâche à la fois (verrou), arrêt propre, lancement en arrière-plan
│   ├── journal.py                   journal à l'écran et dans donnees/journal.log
│   ├── collecte/                    « python -m commun.collecte » (Collecter.bat)
│   │   ├── __main__.py              une source après l'autre, bilan, sauvegarde, notation des nouveaux, site,
│   │   │                            Cloudflare R2, puis classement des nouveaux Facebook pour la modération
│   │   ├── depot.py                 format des lignes, ajout sans doublon, état, bilan
│   │   ├── sources/                 youtube.py, bluesky.py, instagram.py, facebook.py, x.py
│   │   ├── perimetre.py             ajout et retrait de chaînes, comptes, groupes et Pages
│   │   ├── planification.py         Planificateur de tâches de Windows
│   │   └── connexion_*.py           sessions des comptes de collecte Instagram, Facebook, X (--verifier)
│   ├── analyse/                     « python -m commun.analyse »
│   │   ├── __init__.py              modèle de langue de départ et mode hors ligne (voir « Modèles »)
│   │   ├── __main__.py, notation.py notes de tout le corpus par le modèle en service
│   │   ├── corpus.py                table centrale des commentaires (auteurs pseudonymisés, doublons, notes)
│   │   ├── vecteurs.py              vecteurs de sens (e5 multilingue)
│   │   ├── annotation.py            lots à noter à la main, enregistrement vérifié des notes
│   │   ├── modele.py                modèle à vecteurs et briques communes
│   │   ├── affinage.py              réseau e5 affiné (lit le commentaire avec son parent)
│   │   ├── ensemble.py              combinaison des deux : la version en service
│   │   ├── mesures.py               qualité sur le jeu de test, rapport
│   │   ├── ton_inverse.py           part des critiques notées comme des éloges (ou l'inverse) sur le test
│   │   ├── criteres.py, stockage.py, versions.py   définitions, fichiers, versions enregistrées
│   │   └── recalage_pertinence.py   correction de la dérive d'annotation du 2026-11-09
│   ├── critiques/                   « python -m commun.critiques » : thèmes des éloges et des critiques (voir « Thèmes »)
│   ├── interface/                   « python -m commun.interface » (Interface.bat) : la fenêtre de pilotage
│   │   ├── application.py           fenêtre, en-tête, boucles de rafraîchissement
│   │   ├── onglets_collecte.py      tableau de bord, YouTube, Bluesky, Instagram, Facebook, X, planification
│   │   ├── onglet_analyse.py        onglet Analyse et ses sous-onglets (analyse_commentaires, _synthese, _modele)
│   │   ├── onglet_themes.py, onglet_moderation.py   onglets Thèmes et Modération
│   │   └── theme.py                 thème Windows 11, couleurs, composants
│   ├── suivi/                       « python -m commun.suivi » (Suivi.bat) : suivi d'un affinage en cours
│   └── cloudflare/                  « python -m commun.cloudflare » : export vers le bucket R2 du groupe (voir « Cloudflare R2 »)
│
│   ── Documentation ──
├── docs/                            « python -m docs » regénère FONCTIONNEMENT.pdf
│   ├── PROCESS.md                   la mise à jour du projet, étape par étape
│   ├── FONCTIONNEMENT.html / .pdf   document illustré « comment marche le projet » (source / PDF)
│   ├── GRILLE.md                    ce que veut dire chaque note (la référence de l'annotation)
│   ├── GRILLE_PROXIMITE.md          axes, sous-thèmes et notes de la proximité des candidats
│   ├── CLOUDFLARE.md                règles du stockage R2 du groupe et ce que nous y déposons
│   ├── HISTORIQUE.md                décisions, essais abandonnés, versions du modèle, ancienne organisation
│   ├── TRI_DES_CRITIQUES.pdf        méthode des 5 catégories de critiques et de doutes (choisie le 2026-11-12)
│   └── Plan_… / Synthese_verification_Lisnard.pdf   plan et synthèse de la vérification des chiffres
│
│   ── Données (privé et hors git, sauf verification/ et la bibliothèque de la modération) ──
└── donnees/                         toutes les données, celles de chaque site comprises (voir plus bas)
    ├── youtube/, bluesky/, instagram/, facebook/, x/   commentaires collectés, source par source
    ├── analyse/, critiques/, web/, cloudflare/   corpus, annotations, notes, états des publications
    ├── moderation/                  annotations et notes de la modération ; reponses.xlsx (réponses préparées)
    │                                et mots_surveilles.txt, suivis dans git
    ├── proximite/                   candidats.json, documents.csv, textes/ et brut/ des programmes, notes/ (lecture),
    │                                mesures/ (une ligne par mesure notée), positions.json (suivis dans git, sauf brut/)
    ├── verification/                corpus du RAG, registre, SYNTHESE.md, et par thème : affirmations, sources,
    │                                brut/, calculs/, analyse (publiques, suivies dans git)
    ├── sauvegardes/                 la sauvegarde unique
    ├── modeles/                     modèles entraînés : vN/ (versions), affineN/ (réseaux affinés), moderation/
    │                                (voir « Modèles »)
    └── sessions/                    sessions de navigateur et cookies : Instagram, facebook_profil/,
                                     facebook_cookies.json, x_profil/, x_cookies.json, x_twscrape.db
```

## Commandes

**Collecte**

```
python -m commun.collecte                          toutes les sources (YouTube, Bluesky, Instagram, Facebook, X), puis
                                            notation, site, Cloudflare R2 et classement pour la modération
python -m commun.collecte youtube                  une seule source
python -m commun.collecte --reessayer instagram    relancer une source marquée abandonnée
```

**Thèmes** (lecture à la demande, voir « Thèmes »)

```
python -m commun.critiques etat                    où en est la lecture
python -m commun.critiques tirer | voir N | noter N fichier   lire le lot suivant
python -m commun.critiques proches | fusionner fichier   thèmes qui pourraient fusionner, et fusion
python -m commun.critiques a-resumer               les synthèses à écrire ou réécrire depuis la dernière fois
python -m commun.critiques syntheses fichier       enregistrer les synthèses par thème et par sens
python -m commun.critiques trier [N] | ranger K fichier   catégorie des critiques et doutes restés sans catégorie
```

**Modération Facebook** (à part, à la demande, voir « Modération »)

```
python -m moderation etat                  classés, annotés, mesures du modèle
python -m moderation classer               classe les commentaires Facebook pas encore classés
python -m moderation tirer 250 questions   lot à annoter (modes : hasard, questions, insultes, doutes)
python -m moderation noter K fichier       enregistre la lecture du lot K (« I: … », « Q: … ») ;
                                          --par gemini si Gemini l'a lue (moderation/PROMPT_GEMINI.md)
python -m moderation relire K fichier      relecture par Claude d'un lot lu par Gemini
python -m moderation entrainer             réentraîne (≈ 30 min) puis reclasse tout
python -m moderation publier [--tout]      envoie ce qui a changé dans la table privée moderation de Supabase
python -m moderation motdepasse           choisit le mot de passe du site de modération (ferme les sessions ouvertes)
python -m moderation site deployer        met en ligne le site de modération (moderation/site/)
python -m moderation site apercu          ouvre le site de modération en local (http://localhost:8001)
python -m moderation reponses             synchronise les réponses préparées : donnees/moderation/reponses.xlsx ↔ Supabase
python -m moderation themes etat          réponses préparées, commentaires rangés par thème, reste à ranger
python -m moderation themes tirer [N]     lot à ranger par thème (100, questions d'abord, des plus longues ; mode tout : aussi
                                          ceux qui n'appellent pas de réponse)
python -m moderation themes noter K f     enregistre la lecture (« 12: T31 T43 », « 12: - ») ; --par gemini
                                          (moderation/PROMPT_GEMINI_THEMES.md)
```

**Sauvegarde** (voir « Sauvegarde »)

```
python -m commun.sauvegarde                 refaire la sauvegarde (aussi faite à la fin de chaque collecte)
python -m commun.sauvegarde --voir          ce que contient la sauvegarde actuelle
```

**Analyse**

```
python -m commun.analyse                           note ce qui ne l'est pas encore (aussi lancé après chaque collecte)
python -m commun.analyse --sources youtube --du 2026-01-01
python -m commun.analyse --refaire                 renote tout avec le modèle en service
```

**Document de fonctionnement**

```
python -m docs                              regénère docs/FONCTIONNEMENT.pdf depuis docs/FONCTIONNEMENT.html
```

**Site public**

```
python -m commentaires tout                          installer la base, publier les données, mettre les pages en ligne
python -m commentaires publier                       envoyer ce qui a changé (aussi fait après chaque collecte)
python -m commentaires deployer                      remettre les pages en ligne après une modification de commentaires/site/
python -m commentaires apercu                        les pages en local (http://localhost:8000), sur les données en ligne
python -m commentaires motdepasse                    choisir le mot de passe du site (ferme les sessions ouvertes)
```

**Annotation et entraînement**

```
python -m commun.analyse.annotation etat              où en est l'annotation
python -m commun.analyse.annotation tirer-actif 100   prochain lot : commentaires où le modèle hésite
python -m commun.analyse.annotation tirer-reponses 100   prochain lot : réponses, lues avec leur parent
python -m commun.analyse.annotation tirer-longs 4000  lots de commentaires longs (40 mots ou plus), répartis entre sources et comptes
python -m commun.analyse.annotation voir 143          afficher un lot
python -m commun.analyse.annotation noter 143 notes.txt   enregistrer ses notes (vérifiées)
python -m commun.analyse.ensemble tout                réentraînement complet : réseau affiné puis combinaison (environ 7 h)
python -m commun.analyse.ensemble construire affineN  combinaison seule à partir d'un réseau déjà affiné (25 min)
python -m commun.analyse.ton_inverse                  part de « ton inversé » sur le test, avec les notes du corpus
```

Un réentraînement occupe tout le processeur : ne jamais en lancer deux à la fois. La nouvelle version
(`donnees/modeles/vN/`) est utilisée dès l'analyse suivante.

## Interface

| Onglet | Ce qu'on y fait |
|---|---|
| Tableau de bord | Une carte par source (YouTube, Bluesky, Instagram, Facebook, X ; celles de Facebook et de X donnent l'arriéré par groupe ou par compte, les requêtes du jour et le repos éventuel) : état (prête, en cours, arrêt demandé, abandonnée), total, dernier lancement ; Lancer (ou Réessayer), Arrêter, Forcer l'arrêt, Ouvrir l'Excel, Dossier. « Tout lancer » en haut. Journal en direct. |
| YouTube | Chaînes suivies et leurs commentaires. Ajouter une chaîne par son lien, son @pseudo ou son identifiant, avec sa règle : toutes les vidéos, ou celles qui citent le mot-clé. Retirer, changer la règle, mot-clé, durée de relecture. Case « Chercher aussi ailleurs que sur les chaînes suivies » : les vidéos des autres chaînes trouvées par la recherche (dernière ligne du tableau). |
| Bluesky | Réglages (date de début, pages par lancement, durée de relecture) et ce qui est suivi : la recherche « Lisnard », qu'on ne peut pas retirer (le mot-clé se règle dans l'onglet YouTube), puis les comptes suivis, avec leur arriéré et leurs commentaires. Ajouter un compte par son pseudo ou son lien, retirer la sélection, donner le groupe choisi à la sélection. |
| Instagram | Comptes suivis : posts dans la période, posts lus, commentaires. Ajouter ou retirer un compte. Date de début, posts par lancement, durée de relecture, seuil d'abandon. |
| Facebook | Réglages (date de début, durée de relecture, minutes par lancement, requêtes par jour) et les groupes et Pages suivis, avec leur arriéré et leurs commentaires. Ajouter un groupe ou une Page en collant son lien : une seule page lue avec les cookies du compte de collecte en donne l'identifiant et le nom. Retirer la sélection, donner le groupe choisi à la sélection. |
| X | Réglages (date de début, relecture des posts suivis, attente avant de lire les réponses d'un post qui le cite, minutes par lancement, requêtes par jour, recherches par quart d'heure) et ce qui est suivi : la recherche « Lisnard », qu'on ne peut pas retirer, puis les comptes suivis, avec leur arriéré et leurs commentaires. Ajouter un compte par son @pseudo ou le lien de son profil (une requête avec le compte de collecte en donne l'identifiant et le nom). Retirer la sélection, donner le groupe choisi à la sélection. |
| Planification | Collecte automatique chaque jour à une heure donnée, éventuellement toutes les N heures. Tâche « DavidLisnard - collecte des commentaires » du Planificateur de tâches, qui lance `Collecter.bat`. |
| Analyse › Commentaires | Filtres (sources, comptes, période, type, recherche, plages de notes, cible, fiabilité, analysé ou non, doublons masqués ou montrés), tableau, détail, « Corriger les notes », export Excel, analyse de la sélection. |
| Analyse › Synthèse | Chiffres clés, perception (critiques · non évoqué · éloges), évolution par mois, sources, exemples. La case « écarter pertinence < 5 » retire l'ironie indécidable, les émojis seuls et le hors-sujet. La case « Pondérer par les « j'aime » » fait peser chaque commentaire 1 + ses « j'aime » (voir « Doublons et « j'aime » »). |
| Analyse › Modèle | Qualité mesurée, apport du réseau affiné, réentraînement, analyse automatique après chaque collecte. |
| Modération | Commentaires Facebook classés « à modérer », « question » ou « autre » par le modèle de modération (ou par l'annotation de Claude) : combien sont traités et annotés, qualité du modèle, filtres par catégorie, groupe et mot, tri par sûreté ou date ; pour chaque commentaire, l'auteur, la publication, son lien (double-clic pour l'ouvrir) et les probabilités. Boutons « Classer les nouveaux », « Réentraîner le modèle », Journal, Arrêter. Local seulement : rien sur le site. |
| Thèmes | Les thèmes des éloges, critiques et doutes : filtres par famille, sens, catégorie des critiques et des doutes, période et mot, comptes en commentaires et en auteurs distincts, évolution par mois, synthèses et commentaires de chaque thème. |

À savoir :
- **Lancer.** La collecte ou l'analyse tourne en arrière-plan. Elle continue si l'on ferme la fenêtre, et
  l'interface la retrouve à la réouverture. Une même tâche n'est jamais lancée deux fois en même temps, même depuis
  le terminal ou la planification. Le verrou est le fichier `donnees/<tâche>/EN_COURS`.
- **Arrêter.** L'arrêt est propre : la tâche s'arrête à la fin de la vidéo, du post ou du lot en cours (fichier
  `donnees/<tâche>/ARRET`). Ce qui est lu est gardé.
- **Erreurs.** Les erreurs inattendues de l'interface s'affichent et sont notées dans
  `donnees/erreurs_interface.log`.

## Collecte

| Source | Méthode |
|---|---|
| YouTube | API officielle YouTube Data v3 : dates exactes, réponses rattachées à leur commentaire. Le quota gratuit est de 10 000 unités par jour (la première collecte complète en a pris environ 4 500). Si le quota est atteint, la suite reprend au lancement suivant. En plus des chaînes suivies, la recherche du mot-clé dans tout YouTube (`search.list`, 100 unités par page de 50 vidéos) ramène les vidéos des autres chaînes. |
| Bluesky | API publique `api.bsky.app`, gratuite et sans compte. Recherche des messages qui citent le mot-clé, puis lecture des réponses de chaque fil. L'API refuse la pagination par curseur sans compte : on avance par dates. Les comptes suivis se lisent en entier (`getAuthorFeed`), curseur compris. |
| Instagram | Chrome visible, connecté avec le compte dédié. Le script ouvre chaque post et fait défiler les commentaires. La source est abandonnée d'elle-même en cas de blocage, ou si 10 posts prennent plus de 30 minutes. |
| Facebook | Sa Page officielle et des groupes publics de soutiens. Meta a fermé l'API des groupes en 2024 : la bibliothèque `facebook-gql-scraper` envoie, avec les cookies du compte dédié, les requêtes internes du site (aucun navigateur pendant la collecte ; trois corrections dans `commun/collecte/sources/facebook.py`). Rythme humain : 1,5 à 3 s entre deux requêtes (environ 1 500 requêtes et 3 600 commentaires à l'heure), 120 min par lancement, 6 000 requêtes par jour. Au moindre freinage, arrêt et repos de 3 h. Chaque requête a 60 s au plus, avec deux nouveaux essais (après 30 s, puis 60 s) avant l'arrêt. |
| X | Ses comptes, des comptes de soutiens et les posts qui le citent. X n'a plus d'accès gratuit : la bibliothèque `twscrape` envoie, avec les cookies du compte dédié, les recherches internes du site (aucun navigateur pendant la collecte). Tout passe par la recherche, seule à rendre toutes les réponses d'un post (« conversation_id: »). X permet 50 recherches par quart d'heure : on en fait 40 au plus, avec 3 à 8 s entre deux requêtes (environ 3 200 posts à l'heure), 120 min par lancement, 3 000 requêtes par jour. Au moindre freinage, arrêt et repos de 3 h. |

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
  toutes les réponses sous un message de tête qui le cite, et les réponses à une réponse qui le cite, dans
  `donnees/bluesky/` sous le compte « Recherche « Lisnard » » (groupe « autre »). La « publication » est le message
  de tête du fil.
  - `comptes` : `{handle, did, nom, groupe}`. Tous les messages d'un compte suivi, qu'ils citent le mot-clé ou non
    (sans ses partages), et toutes leurs réponses, dans un fichier par compte (`@handle`, par exemple
    `lephoenicks_bsky_social.csv`) et sous le groupe du compte. À chaque lancement : le récent depuis le passage
    précédent (moins un jour), puis l'arriéré au curseur jusqu'à `depuis`, sur le même budget de pages que la
    recherche (état dans `etat.json`, `comptes`). Un message trouvé à la fois par la recherche et par un compte est
    rangé sous le compte. David Lisnard n'a pas de compte Bluesky : aucun compte n'est suivi pour l'instant.
- **Instagram** :
  - comptes suivis, date de début (`depuis`), posts lus au plus par lancement ;
  - âge maximal d'un post relu (21 jours) et seuil d'abandon ;
  - les posts jamais lus passent d'abord. Depuis le 2026-11-09, l'arriéré s'arrête au 2026-07-31.
- **Facebook** (`"facebook"`) :
  - `groupes` : `{nom, id, groupe}`, groupe « soutien ». Les cinq plus gros groupes publics sur Lisnard (recherche
    du 2026-11-12) : « Cap 2027 avec David Lisnard » (environ 167 000 membres), « Soutien David Lisnard 2027 »
    (112 000), « Soutien à David Lisnard » (119 000 ; suspendu par son administrateur jusqu'au 1er décembre : lu,
    mais pas d'adhésion possible avant), « Soutien Lisnard Lot, Cantal et Aveyron » (25 000) et « Nouvelle Énergie 13
    - Bouches-du-Rhône » (21 000), ces deux derniers rejoints par le compte de collecte. Un groupe privé de 33 000
    membres (« soutien à David lisnard pour 2027 ») est écarté exprès : adhésion sur accord, et contenu non public
    qu'on ne publierait pas ;
  - `pages` : `{nom, id, groupe}`, groupe « officiel » : la Page certifiée « David Lisnard » (`lisnard.david`,
    environ 145 000 abonnés). Une Page se lit comme un profil, avec la même mécanique que les groupes (le récent
    puis l'arriéré ; sa frontière est aussi rangée sous `groupes.<id>` dans `etat.json`) ;
  - `depuis` (2026-07-31), `relire_si_moins_de_jours` (7), `minutes_par_lancement` (120), `requetes_par_jour`
    (6 000), `pause_entre_requetes_s`, `pause_longue`, `repos_apres_freinage_heures` (3) ;
  - sont pris : le post lui-même (titre vide, comme le message de tête d'un fil Bluesky), ses commentaires
    (`principal`, titre = texte du post) et leurs réponses (`réponse`), sans autocollants ni images seules. Un CSV
    par groupe ou par Page dans `donnees/facebook/` ;
  - à chaque lancement : d'abord le récent (jusqu'à 7 jours ; un post déjà lu n'est relu que si ses commentaires
    ont augmenté, et jusqu'à 10 commentaires connus d'affilée), puis l'arriéré, repris au curseur gardé dans
    `etat.json` jusqu'à `depuis`. Suivre le nouveau demande environ 1 000 requêtes par jour ; l'arriéré
    (environ 50 000 requêtes) prend une dizaine de jours au quota ;
  - états possibles dans le bilan : ok, partiel (temps ou quota), partiel (freinage), en repos, impossible
    (Facebook demande une vérification : refaire `python -m commun.collecte.connexion_facebook`). Une session expirée se
    refait seule, une fois. Un fil vide (groupe supprimé ou devenu privé) est sauté (« FIL VIDE » dans le journal)
    sans arrêter les autres.
- **X** (`"x"`) :
  - `comptes` : `{pseudo, id, nom, groupe}`. Suivis le 2026-11-13 : `@davidlisnard` et `@Nouv_Energie` (son
    mouvement, le compte qu'il republie le plus), groupe « officiel » ; `@AvecLisnard` (environ 8 400 abonnés) et
    `@DavidLPresident` (« Lisnard Président », 5 800), groupe « soutien », les deux plus gros comptes de soutien
    trouvés par la recherche de comptes. Sont pris leurs posts (`from:pseudo -filter:retweets -filter:replies` : ni
    republications, ni réponses à d'autres), qu'ils citent le mot-clé ou non, et toutes les réponses dessous, dans
    un fichier par compte (`@pseudo`, par exemple `davidlisnard.csv`) ;
  - `recherche` (vrai) : les posts des autres comptes qui citent le mot-clé (`Lisnard -filter:retweets
    -filter:replies -from:<comptes suivis>`, environ 70 par jour) et toutes leurs réponses, dans « Recherche
    « Lisnard » » (groupe « autre »). Les réponses qui citent « Lisnard » sous les posts des comptes suivis (plus de
    300 par jour) sont déjà prises avec eux ;
  - `depuis` (2026-07-31, comme Instagram et Facebook), `relire_si_moins_de_jours` (7 : un post suivi qui a gagné
    des réponses est relu, seulement pour les nouvelles, `since_id:`), `attendre_reponses_jours` (2 : les
    réponses d'un post qui le cite sont lues une fois, quand il a deux jours), `minutes_par_lancement` (120),
    `requetes_par_jour` (3 000), `recherches_par_quart_heure` (40), `pause_entre_requetes_s` ([3, 8]),
    `repos_apres_freinage_heures` (3) ;
  - rangement comme Facebook : le post (titre vide), les réponses directes (`principal`, titre = texte du post), les
    réponses aux réponses (`réponse`, `parent_id`). Les « @pseudo » qu'X met en tête des réponses sont retirés du
    texte ;
  - à chaque lancement : le récent des comptes suivis, celui de la recherche, les fils à lire, puis l'arriéré
    (une page de 20 posts de chaque suivi à tour de rôle, recherche comprise), repris au dernier identifiant lu (`max_id:`). Les petits
    fils de la recherche sont lus par paquets de dix (`conversation_id:A OR conversation_id:B…`). État dans
    `etat.json` : `requetes` (haut, bas, complet par compte et pour la recherche) et `fils` (ce qu'il reste à lire) ;
  - états possibles dans le bilan : ok, partiel (temps ou quota), partiel (freinage), en repos, impossible (session
    refusée même après une nouvelle connexion : compte suspendu ?).

**Fichiers.** `donnees/<source>/` contient :
- un CSV par compte suivi, qui ne fait que grandir (le bouton « Dossier » de l'onglet l'ouvre) ;
- `etat.json`, ce qui a déjà été lu ;
- `likes.json`, les « j'aime » qui ont changé depuis la première collecte d'un commentaire (voir « Doublons et
  « j'aime » »).

Le dernier lancement est dans `donnees/bilan.md`, tous les lancements dans `donnees/historique.md`, le détail dans
`donnees/journal.log`. Une source qui échoue n'arrête pas les autres : son erreur est dans le bilan.

**Colonnes (toutes les sources) :**

| Colonne | Contenu |
|---|---|
| `source` | youtube, bluesky, instagram, facebook, x |
| `compte_source` | chaîne ou compte où le commentaire a été pris |
| `publication_id`, `publication_titre`, `publication_lien`, `publication_date` | la vidéo ou le post commenté |
| `commentaire_id` | identifiant donné par la plateforme |
| `type` | `principal` ou `réponse` |
| `parent_id` | commentaire auquel il répond (vide si principal, ou si le message cité n'a pas été retrouvé) |
| `auteur`, `auteur_id` | pseudo ou nom affiché, et identifiant du compte |
| `date` | heure de Paris |
| `date_exacte` | `oui` (YouTube, Instagram, Facebook, X : à la seconde) |
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
| WhatsApp | Collecté jusqu'au 2026-11-12 (discussion « Échanges entre adhérents » de Nouvelle Énergie 34), puis retiré à ta demande avec tout ce qui en venait (messages, notes, annotations, thèmes, sauvegarde) : des échanges entre militants, pas l'avis du public. |
| Threads | Connexion obligatoire et fortes protections anti-robots. À tenter seulement avec un compte créé pour la collecte (comme ceux d'Instagram, de Facebook et de X), pour qu'un bannissement ne touche pas un compte personnel. |
| Facebook, hors périmètre | Seuls sa Page officielle et cinq groupes publics sont suivis. Les groupes privés sont écartés : adhésion sur accord, et contenu qu'on ne publierait pas. |

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

**Comment c'est fait** (historique des versions dans [docs/HISTORIQUE.md](docs/HISTORIQUE.md)) :
- **Table centrale** : `donnees/analyse/corpus.csv`, une ligne par commentaire, avec les auteurs pseudonymisés, les
  notes du modèle d'analyse (colonnes `note_version`, les cinq notes, `cible`, `p_autre`, `fiabilite`, `note_le`) et,
  pour Facebook, le classement de la modération (colonnes `mod_…`). Les fichiers de collecte ne sont jamais modifiés.
  Le corpus se recalcule (collecte + modèles) ; le travail fait à la main reste à part, dans de petits fichiers reliés
  par la clé du commentaire et sans copie du texte. Chaque tâche n'écrit que ses colonnes, sous un verrou
  (`donnees/analyse/CORPUS_VERROU`).
- **Annotation** : les commentaires sont notés à la main par Claude, par lots de 100, selon la grille
  (`donnees/analyse/annotation/`).
  - Un jeu de test fixe de 500 commentaires tirés au hasard n'est jamais appris : il sert à mesurer.
  - Les réponses sont lues avec le commentaire auquel elles répondent.
- **Ironie** :
  - comprise : notée selon son sens réel ;
  - indécidable : pertinence basse (0 à 3), pour pouvoir l'écarter.
- **Modèle en service** (`donnees/modeles/vN/`, la version la plus récente). C'est la moyenne pondérée de deux modèles :
  - un réseau e5 affiné, qui lit chaque commentaire (256 jetons au plus) avec son parent (128) et le titre de la
    publication (20) ;
  - un modèle à vecteurs, plus stable sur les reproches rares.
- **Mesures de qualité** : `donnees/analyse/RAPPORT_MODELE.md` et l'onglet Analyse › Modèle.

**Doublons et « j'aime ».**
- **Doublon** : le même texte, du même auteur, dans la même source (un compte qui colle « Au top 👌 » sous
  164 publications). La casse, les accents, la ponctuation et les espaces ne comptent pas. Seul le premier publié
  compte ; les suivants restent dans les fichiers et sont notés, mais sortent de la synthèse, du site et des thèmes
  (colonne `doublon_de` de `corpus.csv` ; case « Montrer aussi les doublons » dans l'interface). Le même texte écrit
  par des personnes différentes n'est pas un doublon : ce sont autant de voix.
- **Vue pondérée par les « j'aime »**, en option, dans la Synthèse : chaque
  commentaire pèse 1 + ses « j'aime » (lui-même et ceux qui l'approuvent), au lieu d'une voix par commentaire.
  Les « j'aime » sont ceux de la dernière lecture : quand une publication est relue, les nouveaux comptes vont dans
  `donnees/<source>/likes.json`. Un commentaire dont la publication n'est plus relue garde ses « j'aime » d'alors.

**Modèles** (`donnees/modeles/`).
- On ne garde que la version en service et son réseau affiné (`reseau` dans `donnees/modeles/vN/infos.json`) : après un
  réentraînement validé, l'ancienne `vN` et son `affineN` sont supprimés (leurs mesures restent dans
  `docs/HISTORIQUE.md`).
- **Hors ligne.** Le modèle de départ (e5) est sur le disque depuis son premier téléchargement. Tant que cette copie
  existe, `commun/analyse/__init__.py` met `HF_HUB_OFFLINE=1` : plus de vérification en ligne à chaque chargement, donc plus
  de message « You are sending unauthenticated requests to the HF Hub », un chargement plus rapide, et tout marche
  sans connexion. Le réglage se lève seul si l'on change de modèle de départ (`MODELE_LANGUE`, pas encore
  téléchargé). Pour forcer une vérification en ligne : `$env:HF_HUB_OFFLINE = "0"` avant la commande.

**Fichiers de l'analyse** (`donnees/analyse/`) :
- `corpus.csv` : la table centrale (voir plus haut), notes du modèle comprises ;
- `annotation/annotations.csv` : les notes de Claude ; `pertinence_origine` garde la pertinence d'avant un recalage ;
- `corrections.csv` : les notes corrigées à la main dans l'interface. Elles priment, et servent au prochain
  entraînement ;
- `exports/` : les exports Excel ;
- `avancement.json` : l'analyse en cours.

## Site public

Le site montre le travail, **avec un mot de passe** (`python -m commentaires motdepasse`, à communiquer) : explication du projet,
commentaires filtrables (curseurs, puces) avec la vidéo d'origine, thèmes des éloges et des critiques. Adresse : `site_url` dans `config/web.json`.

- **Pages** (`commentaires/site/`, HTML + JavaScript sans bibliothèque ni étape de construction) hébergées par **Vercel**.
- **Données** dans **Supabase** (PostgreSQL), modèle normalisé (`commentaires/schema.sql`) : `sources`, `comptes` (et leur
  groupe), `publications`, `utilisateurs` (auteurs, **privée**), `commentaires` (le texte, les notes et des numéros
  vers les autres tables), `syntheses`, et `moderation` (privée). Chaque donnée n'est écrite qu'une fois ; les fichiers
  locaux gardent leur forme, la publication les traduit. Sans connexion, la base ne rend rien : le site se connecte
  au compte partagé des lecteurs (Supabase Auth, adresse fixe, on ne tape que le mot de passe, rôle `lecteur`,
  inscriptions fermées) et lit en lecture seule (règles RLS, `peut_lire()`) ; changer le mot de passe recrée le compte
  et ferme les sessions ; seuls `python -m commentaires publier` et `python -m moderation publier` écrivent, avec la clé secrète. Les filtres de
  la page Commentaires sont appliqués par la base (fonctions `selection` et `evolution`, qui prennent le filtre jsonb
  comme paramètre unique et sans nom ; `commentaire` lit un commentaire par sa clé « source:code ») ;
  la page Le projet et la frise de la page Commentaires lisent le « cube » (comptages par semaine et par compte).
- **Pas d'API à héberger** (ni Railway ni autre) : les pages interrogent Supabase directement. Les deux offres
  gratuites suffisent (base d'environ 115 Mo sur 500).
- **Ce qui est publié** : les commentaires notés de YouTube, d'Instagram, de Bluesky et de Facebook, sans
  auteur ni doublon. Sur le site, la Page Facebook est rangée avec ses comptes officiels et les groupes avec les
  chaînes de soutiens (« Chaînes et groupes
  de soutien ») et chaque commentaire renvoie à son post (« Voir sur Facebook »). Après l'ajout de Facebook,
  `commentaires/site/` a changé : `python -m commentaires deployer` est à relancer une fois.
- **Date et modèle** : chaque page affiche, sous son titre et en pied de page, la date de la dernière collecte et
  la version du modèle (avec sa date d'entraînement), lues dans la synthèse « meta ».
- **Mise à jour** : après chaque collecte qui ramène du neuf, la publication suit la notation (seules les lignes
  nouvelles ou changées partent, grâce à `donnees/web/publie.json`). Bouton « Mettre à jour le site » dans l'onglet
  Analyse → Modèle.
- **Mise en place** (une fois) : coller un jeton Vercel (vercel.com/account/settings/tokens) et un jeton Supabase
  (supabase.com/dashboard/account/tokens) dans `config/web.json`, puis `python -m commentaires tout`.
- Un projet Supabase gratuit sans aucune visite pendant 7 jours est mis en pause : `python -m commentaires installer` le relance.

### Site de la vérification

Un second site, sans mot de passe ni base de données : https://verification-politique.vercel.app (« Vérification
politique », depuis le 21/11/2026 ; il remplace verification-lisnard.vercel.app, supprimé). On y choisit un politique
(David Lisnard, Jean-Luc Mélenchon…) ; il présente, thème par thème, ce qu'il dit, les chiffres publics, les calculs et
une conclusion, et l'accueil compare les politiques thème par thème. Il est généré à partir du paquet `verification/`
(voir `verification/README.md`). Les données sont écrites en dur dans les pages :
après un changement dans un thème, `python -m verification site deployer` (même jeton Vercel que ci-dessus) ;
`python -m verification site apercu` pour le voir en local.

## Cloudflare R2

Les commentaires notés partent aussi vers le stockage du groupe RAG politique sur Cloudflare R2, dans le bucket
**privé** `rag-politique-sources-privees` (jamais le bucket public `rag-politique-sources`). Règles et détail :
[docs/CLOUDFLARE.md](docs/CLOUDFLARE.md).

```
python -m commun.cloudflare              refait le fichier de chaque source, envoie ceux qui ont changé
python -m commun.cloudflare preparer     seulement les Parquet, dans donnees/cloudflare/lots/
python -m commun.cloudflare envoyer      seulement l'envoi des fichiers préparés qui diffèrent du bucket
python -m commun.cloudflare etat         par source : fichier, commentaires, déposé ou en attente
```

- Rangement : `data/commentaires/nouvelle-energie/<source>_<AAAA-MM-JJ>.parquet`, **un seul fichier par source**,
  daté de sa dernière mise à jour. Quand une source change, le nouveau fichier est déposé et vérifié, puis l'ancien
  supprimé ; une source inchangée ne repart pas.
- Contenu : tous les commentaires notés de la source, sans doublon, notes du moment. **Aucun nom de compte** : la colonne
  `auteur_id` est un identifiant opaque (HMAC avec la clé `AUTEUR_CLE` de `config/cloudflare.env`, créée seule),
  le même pour tous les commentaires d'un même compte.
- Le site (Supabase, Vercel) n'en dépend pas : R2 est une sortie en plus.
- Automatique après chaque collecte qui ramène du neuf ; bouton **Export Cloudflare** en haut de l'interface.
- Clés : `config/cloudflare.env` (privé, hors git ; modèle `config/cloudflare.exemple.env`).

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
  qu'un autre. Le site publie toutes les sources sans auteurs (chaque auteur y devient un simple numéro,
  pour compter les auteurs distincts d'une période).
- **Période** (page du site) : curseur sur les 12 derniers mois, précédés d'un cran « Depuis le début » qui regroupe
  le reste, et raccourcis 3, 6, 12 mois, Tout. Comptes, barres et commentaires se limitent à la période ; chaque
  thème affiche sa part des avis et la compare à la période précédente de même durée (« en hausse », « en baisse »).
  Sur le site, sujets, types d'avis et types de critique sont des colonnes de cases (une ou plusieurs) ; classement par nombre
  de commentaires ou d'auteurs. Les synthèses
  restent celles de toute la période. L'adresse de la page garde la période choisie.
- **Catégorie des critiques et des doutes** ([docs/TRI_DES_CRITIQUES.pdf](docs/TRI_DES_CRITIQUES.pdf)) : chaque
  critique (C) ou doute (D) porte une catégorie, ce que le programme peut en faire : 1 opposition de principe,
  2 demande de précision, 3 objection sur une mesure, 4 doute sur la faisabilité, 5 suggestion. Les éloges n'en ont
  pas. Elle est donnée à la lecture (`n | T5 | C3 | phrase` ; `noter` refuse un C ou un D sans chiffre, ou un E avec),
  donc une seule fois par commentaire. `trier` et `ranger` ne servent qu'à ce qui aurait été rangé sans catégorie.
  L'onglet Thèmes de l'interface filtre par catégorie (Toutes, Tout sauf les oppositions de principe, ou une seule) ;
  la page Thèmes du site par « Type de critique », une ou plusieurs (paramètre d'adresse `cat`, liste séparée par
  des virgules) ; un filtre actif écarte les éloges.
- **Synthèses** : une par thème et par sens dès 3 commentaires. `a-resumer` ne signale que celles qui manquent ou
  ont reçu depuis au moins 5 commentaires et 25 % de plus (repère `synthese_le` dans `themes.json`).
- **Mise à jour** : à la demande, pas à chaque collecte, et toujours par Claude ([docs/PROCESS.md](docs/PROCESS.md),
  étapes 5 à 8). Seuls les commentaires nouveaux sont lus : ce qui a été lu ne l'est jamais deux fois. Le rangement
  automatique par vecteurs a été essayé puis retiré ([docs/HISTORIQUE.md](docs/HISTORIQUE.md)).
- **Fichiers** : `donnees/critiques/` (`themes.json`, `rattachements.csv` avec sa colonne `categorie`, `lus.csv`, `lots/`, `tris/`, `notes/`).

## Modération

À part de l'analyse : demandée par le gestionnaire d'un groupe Facebook de soutien (2026-11-13). Chaque commentaire
Facebook collecté (groupes et Page suivis, sans les publications elles-mêmes) reçoit une catégorie :

- **insultant** (à modérer) : injure ou grossièreté qui vise une personne ou un groupe, menace, appel à la violence,
  propos haineux ou déshumanisant, attaque personnelle méprisante. Une critique dure sans injure n'en est pas une ;
- **question** : appelle une réponse de l'équipe (question sur le candidat, son programme, le mouvement ; doute
  sincère ; demande d'aide ; affirmation fausse à rectifier). Une question rhétorique n'en est pas une ;
- **autre** : tout le reste, commentaires positifs compris.

- **Modèle** : multilingual-e5-base affiné en trois classes sur les annotations de Claude
  (`donnees/modeles/moderation/`, version m1 le 2026-11-13 : 2 000 annotations, test de 573). Environ 0,1 s par commentaire.
  Les modèles déjà entraînés à la toxicité, le zero-shot et Qwen3-4B ont été essayés et écartés
  ([docs/HISTORIQUE.md](docs/HISTORIQUE.md)).
- **Mesures** (test, ramenées à la population) : accord avec Claude ≈ 90 % ; à modérer : ≈ 57 % des alertes justes
  (≈ 78 % en comptant les cas limites), ≈ 87 % des vraies insultes trouvées ; questions : ≈ 48 % justes, ≈ 52 %
  trouvées, le point faible. Relire avant de supprimer ou de bannir.
- **Classement automatique** à la fin de chaque collecte qui ramène du neuf sur Facebook (quelques secondes, puis
  envoi dans Supabase) ; aussi par le bouton « Classer les nouveaux ». Les commentaires au texte vide sont écartés.
- **À la demande seulement** ([docs/PROCESS.md](docs/PROCESS.md), partie M) : annoter des lots (`tirer` / `noter`, par
  Claude, ou par Gemini avec le prompt de `moderation/PROMPT_GEMINI.md` puis relus par Claude avec `relire`),
  réentraîner.
- **Fichiers** : `donnees/moderation/` (`annotations.csv` sans copie du texte, `lots/`, `journal.log`) ; le
  classement du modèle est dans les colonnes `mod_…` du corpus. Les annotations et les lots sont dans la sauvegarde. L'onglet, qui montre les auteurs, reste local.
- **Supabase** : table **privée** `moderation` (`commentaires/schema.sql`), une ligne par commentaire classé ou annoté, même
  clé que `commentaires` (source, code) : `p_insultant`, `p_question`, `p_autre`, `version`, `annotation`,
  `classe_le`, et des numéros vers `publications` et `utilisateurs` (table privée des auteurs). Le texte, l'auteur, la
  date et la publication n'y sont écrits que si le commentaire n'est pas déjà dans `commentaires`. La vue privée
  `moderation_complete` remet tout en une ligne : catégorie retenue (l'annotation si elle existe, sinon le modèle),
  origine, catégorie du modèle, texte, auteur, lien direct. Sécurité par ligne active sans règle de lecture : seule la
  clé secrète la lit, le site ne la voit pas. Envoi
  incrémental (`donnees/moderation/publie.json`) après chaque `classer`, `noter` et `entrainer`, ou par
  `python -m moderation publier [--tout]`. Rien sur Cloudflare.
- **Site de modération** (2026-11-13, https://moderation-lisnard.vercel.app, projet Vercel `moderation-lisnard`, pages dans `moderation/site/`, code dans
  `moderation/site.py`) : réservé aux modérateurs, à part du site public. On n'y entre qu'avec le mot de passe choisi
  par `python -m moderation motdepasse` (compte Supabase Auth partagé, rôle « moderateur » ; inscriptions fermées ;
  changer le mot de passe coupe aussitôt les sessions ouvertes). Tous les groupes Facebook de la base
  (`moderation_publications()`), avec un filtre « Groupes » en haut de toutes les vues, « Cap 2027 avec David Lisnard »
  coché par défaut ; seul ce groupe est rangé par thème pour les réponses préparées (le site le rappelle). Compteurs du haut calculés sur les filtres en cours (groupes, période, thème, recherches) ; compteurs « à traiter » (insultants, questions, mots surveillés),
  vue Commentaires (filtres catégorie, mots surveillés, certitude, suivi, période,
  texte, auteur, publication ; tri par date, insulte, question, auteurs signalés), vues Auteurs et Publications,
  vue Statistiques (évolution des insultants, questions et mots surveillés par jour ou par semaine ; commentaires
  marqués « traité » par modérateur, et bilan par modérateur d'après le prénom donné à la connexion). Mots
  surveillés : liste `donnees/moderation/mots_surveilles.txt` (provisoire, en attendant celle du gestionnaire), recopiée
  dans `js/mots.js` au déploiement ; simple filtre dans le navigateur (accents, majuscules, lettres répétées et
  chiffres déguisés ignorés ; mots surlignés), sans lien avec le modèle. Liens vers le commentaire sur Facebook, la publication,
  le profil de l'auteur et sa fiche de membre du groupe (où un administrateur peut le retirer ou le bloquer : l'API
  des groupes Facebook est fermée depuis 2024, on ne peut pas le faire depuis le site). Marques « Traité » /
  « Sans suite » partagées entre modérateurs (table `moderation_suivi`, jamais touchée par la publication).
  **Ménager la base gratuite** : chaque navigateur télécharge tout une fois (≈ 18 requêtes, 2 à 7 Mo), le garde
  (IndexedDB, effacé à la déconnexion), puis ne demande que ce qui a changé (`moderation.maj` daté par un
  déclencheur, `moderation_retires` pour les retraits, `moderation_suivi.le`) : 4 requêtes vides au démarrage ou
  par « Actualiser » (jamais seules). Les marques des autres modérateurs, elles, sont redemandées toutes les 10 s
  page visible (1 requête par index, vide presque toujours) et changent les cartes sur place. Filtres, tris et comptages se
  font dans le navigateur (`js/donnees.js`, `js/app.js`), sans requête ; tout retélécharger au bout de 7 jours.
- **Réponses préparées** (2026-11-19, `moderation/reponses.py`, `js/reponses.js`) : sur chaque commentaire, le bouton
  « 💬 Réponses » ouvre un panneau avec les réponses toutes faites de ses thèmes, regroupées par objection (« C'est
  un Macron bis »…) et repliées : on voit le style (chiffres, argumentée, courte, bienveillante, punchline) et le
  titre ; dépliée, le texte, ses sources, un mot de GIF pour les punchlines, et les boutons « Copier » et « Copier
  et ouvrir le commentaire » (Facebook ne laisse aucun site remplir sa zone de réponse : on clique sur « Répondre »
  et on colle). Option « Commencer par le prénom de l'auteur ». Recherche dans toutes les réponses, choix d'un autre
  thème, filtre « Thème » dans la liste. Les modérateurs ajoutent, modifient et retirent des réponses et ajoutent des
  thèmes (identifiants M-…), signés de leur prénom. **Bibliothèque** : `donnees/moderation/reponses.xlsx` (feuilles
  « Réponses », « Thèmes », « Lisez-moi »), tables `reponses` et `reponses_themes` (lues et écrites par le seul
  compte des modérateurs, jamais supprimées : `actif`), synchronisées dans les deux sens par
  `python -m moderation reponses` (ce qui n'a changé que d'un côté passe de l'autre ; conflit : le site l'emporte,
  la version du fichier est montrée ; une ligne effacée du fichier est désactivée). **Thèmes des commentaires** :
  ceux de la lecture de Claude pour l'analyse (critiques et doutes), sinon ceux des lots `themes tirer` / `noter`
  (Gemini ou Claude ; `donnees/moderation/themes.csv`, `lots_themes/`), envoyés dans la colonne `themes` de la
  table `moderation`. Chiffres des réponses : seulement des faits sourcés (`verification/`, corpus Nouvelle
  Énergie) ; les vérifier avant de publier.
  Vues `moderation_lignes`, `moderation_pubs` et fonction `suivre()` dans `commentaires/schema.sql` ; rien à faire à la
  publication. Après une modification des pages : `python -m moderation site deployer`.

## Proximité des candidats

À part du reste (paquet `proximite/`, données dans `donnees/proximite/`), à la demande seulement. Les programmes
publiés pour la présidentielle 2027 sont lus mesure par mesure ; chaque mesure est rangée dans un sous-thème de l'un
des trois axes (économie et social, ordre et immigration, souveraineté et monde) et notée de −3 à +3 selon
[docs/GRILLE_PROXIMITE.md](docs/GRILLE_PROXIMITE.md). Les candidats sont ensuite placés sur les trois axes et
comparés (distances).

```
python -m proximite collecter [candidat]    liste des candidats et programmes (export de candidats2027.org),
                                            téléchargement, texte de chaque document ; signale le nouveau et le modifié
python -m proximite etat                    documents à lire et mesures par candidat
python -m proximite lire <candidat> [page]  texte complet des documents à lire, par pages de 30 000 caractères
python -m proximite relire <candidat>       remet tous les documents du candidat « à lire » (relecture complète)
python -m proximite noter <candidat> <fichier>       enregistre les mesures relevées (format : proximite/mesures.py)
python -m proximite calculer                positions par sous-thème et par axe, distances → positions.json
python -m proximite site [apercu|deployer]  régénère proximite/site/donnees.js ; aperçu local (port 8020) ou Vercel
```

- **Sources** : la liste vient de `https://candidats2027.org/api/export` (candidatures en lice, PDF ou page officielle
  de chaque programme). Quand la page d'un programme renvoie à ses chapitres ou à ses PDF, la recette du candidat
  (`RECETTES` dans `proximite/collecte.py`) dit quels liens suivre.
- **Lecture** : faite par Claude, qui lit chaque document en entier ; le code ne trie ni ne présélectionne rien (il
  télécharge, extrait le texte, retire les doublons entre documents et découpe en pages). Les mesures d'un candidat s'écrivent dans
  `donnees/proximite/notes/<candidat>.txt` (une ligne `O1 +2 | texte de la mesure`, un `## document` par document lu),
  puis `noter` les range dans `donnees/proximite/mesures/<candidat>.csv` et marque les documents lus. Un document lu
  et inchangé n'est pas relu ; un document modifié l'est, et ses mesures remplacent les anciennes.
- **Programmes de référence** : `REFERENCES` dans `proximite/collecte.py` ajoute d'anciens programmes, hors de
  l'export, lus et notés selon la même grille (Emmanuel Macron 2017, 119 mesures) ; le site les montre à part,
  « pour comparaison », avec l'année dans le nom.
- **Premier essai (21/11/2026)** : 13 programmes, 2 357 mesures, tous lus en entier.
- **Site** : statique, une seule page (`proximite/site/index.html`) : programmes, carte (une ligne par axe, puis un
  plan à deux axes au choix ; SVG dessiné par `js/carte.js`), distances (tous les axes ou un seul au choix), notes par thème (un axe à la fois, avec sa
  clé de lecture). Seul `donnees.js` est régénéré. Mise en ligne
  sur Vercel (projet « proximite-candidats ») avec le jeton du site public (`config/web.json`).

## Sauvegarde

`donnees/sauvegardes/donnees.zip` : une copie compressée de ce qu'on ne peut pas refaire.
- **Contenu**, dans cet ordre : Instagram d'abord (anciennes publications, qu'on ne peut pas recollecter), puis
  YouTube, Bluesky et Facebook (CSV bruts, `etat.json`, `likes.json`), puis le travail fait à la main : annotations
  (`donnees/analyse/annotation/`), corrections de l'interface, lecture par thèmes (`donnees/critiques/`),
  annotations de la modération (`donnees/moderation/`). Environ 18 Mo, une seconde.
- **Une seule sauvegarde** : la nouvelle est écrite dans un fichier temporaire, relue en entier, puis remplace
  l'ancienne. On n'est jamais sans sauvegarde.
- **Garde-fou** : les CSV de collecte ne font que grandir. Si l'un d'eux a rétréci ou disparu, l'ancienne
  sauvegarde est gardée, la nouvelle est mise de côté (`donnees_a_verifier.zip`) et le journal le signale.
  `--forcer` passe outre.
- **Quand** : à la fin de chaque collecte, et à la demande (bouton « Sauvegarder » de l'interface ou
  `python -m commun.sauvegarde`).

## Précautions

- Ces fichiers relient des personnes à des opinions politiques : ce sont des données sensibles au sens du RGPD.
- Tout reste en local, sauf ce que publie le site : texte et notes des commentaires publics YouTube, Instagram, Bluesky et Facebook,
  sans auteur ni identifiant d'auteur (`commentaires/export.py`). `donnees/` (avec `sessions/` et `modeles/`), `config/cles.json`,
  `config/compte.json` et `config/web.json` sont exclus du partage par `.gitignore`, sauf `donnees/verification/`
  (données publiques) et `donnees/moderation/reponses.xlsx` et `mots_surveilles.txt`.
- Pseudonymiser les auteurs avant toute analyse partagée : la copie de travail de l'analyse l'est déjà.
