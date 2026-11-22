# DavidLisnard : historique des choix

Ce qui a été décidé, essayé ou abandonné, et pourquoi. Le fonctionnement actuel est dans [README.md](../README.md),
la marche à suivre pour une mise à jour dans [PROCESS.md](PROCESS.md).

Ce fichier remplace, depuis le 2026-11-12, les journaux de conception `PLAN_COLLECTE.md`, `PLAN_ANALYSE.md`,
`PROPOSITIONS_CRITIQUES.html/.pdf` et la liste `AMELIORATIONS.md`. Leur texte intégral reste dans l'historique git du
projet (`git show 17b7f43:docs/PLAN_ANALYSE.md`, par exemple).

## Collecte

| Date | Ce qui s'est passé |
|---|---|
| 2026-11-07 | Plan de collecte : une commande, incrémentale, une source par dossier, mêmes colonnes partout (CSV en `;`, UTF-8 avec BOM, ouvrables dans Excel), rien n'est jamais supprimé, fusion par identifiant. |
| 2026-11-07 | YouTube par l'API officielle : 22 chaînes (les siennes et celles de ses soutiens en entier ; médias et commentateurs, vidéos qui citent « Lisnard »), 58 608 commentaires en 9 min. yt-dlp était prévu en secours sans clé (dates approximatives) ; la clé est là, il n'a pas servi. Titres demandés en français, sinon la recherche les traduit. |
| 2026-11-07 | Instagram : quatre méthodes comparées, seule la quatrième (Chrome visible piloté, compte dédié, lecture de ce que la page reçoit) tient. Critère d'abandon fixé par l'utilisateur : 10 posts en plus de 30 min, ou un blocage. Rythme humain : petits lots, arrêt net au premier blocage, pas de relance en boucle. |
| 2026-11-07 | TikTok : techniquement faisable (Chrome normal piloté par son port de débogage), accepté par l'utilisateur, mais refusé par le classifieur de sécurité de Claude Code. Reddit : bloqué par le réseau. Telegram : pas de canal public. X : API payante. Facebook, Threads : connexion obligatoire, à tenter avec un compte créé pour la collecte. |
| 2026-11-09 | Arriéré Instagram arrêté au 2026-07-31. Réorganisation du code en paquets (voir plus bas). |
| 2026-11-11 | Recherche du mot-clé dans tout YouTube (au-delà des chaînes suivies) et source Bluesky (API publique, sans compte). |
| 2026-11-12 | Source Facebook : deux groupes publics de soutiens (« Cap 2027 avec David Lisnard », « Soutien David Lisnard 2027 »), compte dédié, requêtes internes du site par `facebook-gql-scraper` (API des groupes fermée par Meta en 2024), avec trois corrections de la bibliothèque (en-têtes de navigation, jeton `DTSGInitialData`, fausse « session expirée » sur fbcdn.net). Arriéré depuis le 2026-07-31, rythme humain, quota par jour, repos de 3 h au moindre freinage. Pas de colonne de source ajoutée au modèle (elle casserait les modèles enregistrés) : Facebook se reconnaît au groupe « soutien », et le réseau affiné lit la source dans son texte d'entrée. |
| 2026-11-12 (soir) | Facebook étendu : trois groupes publics de plus (les cinq plus gros sur Lisnard) et la Page officielle certifiée (groupe « officiel », lue comme un profil). Un groupe privé de 33 000 membres écarté (adhésion sur accord, contenu non public). Robustesse : 60 s au plus par requête et deux nouveaux essais, après une connexion restée ouverte qui avait figé la collecte 10 min ; un fil vide est sauté au lieu de rendre la source impossible. |
| 2026-11-12 (soir) | Bluesky peut suivre des comptes en entier (tous leurs messages et réponses, `getAuthorFeed`), en plus de la recherche du mot-clé. Aucun n'est suivi : David Lisnard n'a pas de compte Bluesky (vérifié par `searchActors`). Interface : onglets Bluesky et Facebook (réglages, ce qui est suivi, ajout par un lien, retrait, groupe), dans l'ordre YouTube, Bluesky, Instagram, Facebook. |
| 2026-11-12 | WhatsApp (discussion « Échanges entre adhérents » de Nouvelle Énergie 34, lue dans l'application du PC par un port WebView2) retiré à la demande de l'utilisateur, avec tout ce qui en venait : des échanges entre militants, pas l'avis du public. |
| 2026-11-13 | Source X : compte dédié `fandelisnard`, bibliothèque `twscrape` (requêtes internes du site avec les cookies, sans navigateur). Essais du 2026-11-12 hors projet : twikit 2.3.3 cassé, son fork twifork sans mode invité (X a fermé l'accès sans compte), Scweet 5.8 rend 399 réponses mais une liste vide sans erreur si la session est mauvaise, twscrape `tweet_replies` 36 seulement sur un post à 441 réponses annoncées, la recherche `conversation_id:` 544 (sous-réponses comprises) : tout passe donc par la recherche. Limite mesurée : 50 recherches par quart d'heure et par compte ; on en fait 40. Suivis : `@davidlisnard`, `@Nouv_Energie` (officiel), `@AvecLisnard`, `@DavidLPresident` (soutien), plus la recherche des posts qui citent « Lisnard », depuis le 2026-07-31. Connexion par mot de passe refusée par X depuis un script (« flow name login is currently not accessible ») : connexion dans un Chrome visible (`collecte.connexion_x`), puis limitée par X après plusieurs essais le même soir (« temporairement limité votre connexion ») ; la première session vient des cookies copiés à la main. |
| 2026-11-15 | Facebook : après une nouvelle connexion, le jeton `fb_dtsg` gardé en cache par la bibliothèque (`sessions/facebook_gql_etat.json`) restait celui de l'ancienne session ; Facebook refusait alors toutes les requêtes internes, ce que la collecte prenait pour une « demande de vérification ». `connexion_facebook` efface désormais ce jeton à chaque connexion. |
| 2026-11-22 | Mise à jour : **X** répond « Internal server error » à toutes les recherches (session valable, `twscrape` 0.21.0 à jour) ; la collecte prenait ces réponses vides pour « aucune réponse » et retirait les fils de la liste à lire (790 fils de la recherche et les fils suivis remis à lire à la main, état gardé dans `donnees/x/etat_avant_reparation_2026-11-22.json`). Désormais une erreur de X sans aucun post devient un freinage (`chercher()` de `commun/collecte/sources/x.py`) : rien n'est marqué lu. **Facebook** montre un écran « Continuer » (profil connu) au lieu du formulaire : `connexion_facebook.py` le gère. **Analyse** : les modèles enregistrés avant la réorganisation nomment encore le paquet `analyse` ; un renvoi des anciens noms vers `commun.analyse` (dans `commun/analyse/__init__.py`) les recharge sans les refaire. |

## Analyse

**Point de départ (2026-11-08).** 97 357 commentaires, pas de carte graphique (16 cœurs, 25 Go). D'où : un modèle de
langue déjà entraîné (e5 multilingue) qui donne des vecteurs, puis de petits modèles qui apprennent les notes. Les
reproches visés sont rares : il faut aller les chercher exprès (tirages ciblés), un tirage au hasard n'en donne
presque pas. Grille écrite d'abord ([GRILLE.md](GRILLE.md)), annotation par Claude, jeu de test fixe jamais appris.

**Versions du modèle.** Toutes mesurées sur le même test de 500 commentaires tirés au hasard.

| Version | Réseau (annotations) | Tonalité rho / écart | Pertinence rho / écart | Système rho | Idées rho | Cible |
|---|---|---|---|---|---|---|
| v1, v2 | — (vecteurs seuls, 1 629 puis 1 929) | | | | | |
| v3 | — (vecteurs seuls, 3 729) | 0,62 / 2,45 | — | — | — | 77 % |
| v4 | affine2 (4 429) | 0,658 / 2,33 | 0,728 / 2,28 | 0,35 | 0,39 | 80,4 % |
| v5 | affine3 (≈ 5 100) | 0,705 / 2,16 | 0,715 / 2,31 | 0,46 | 0,44 | 81,4 % |
| v6 | affine4 (10 929) | 0,713 / 2,02 | 0,646 / 3,14 | 0,44 | 0,43 | 81,4 % |
| v7 | affine4, pertinence recalée | 0,715 / 2,02 | 0,736 / 2,07 | 0,43 | 0,44 | 81,0 % |
| v8 | affine5 (11 888) | 0,736 / 1,93 | 0,753 / 2,04 | 0,53 | 0,50 | 80,8 % |
| v10 | affine7 (18 014) | 0,738 / 1,79 | — | 0,49 | — | — |
| v11 | affine8 (18 014), 256 jetons | 0,739 / 1,83 | 0,76 / 2,00 | 0,60 | 0,37 | 82 % |
| v12 | affine9 (21 969), sans WhatsApp | 0,761 / 1,80 | 0,779 / 1,90 | 0,64 | 0,47 | 82,8 % |
| v13 | affine10 (26 557) | 0,787 / 1,58 | 0,797 / 1,86 | 0,62 | 0,44 | 83,6 % |

- La méthode à vecteurs seule plafonne (v3 ≈ v2) : le gain vient du réseau affiné (`analyse/affinage.py`, qui lit le
  commentaire avec son parent et le titre) et de la combinaison des deux (`analyse/ensemble.py`).
- v11 (256 jetons pour le commentaire au lieu de 128) a été mise en service le 2026-11-11 à la demande de
  l'utilisateur, pour lire en entier les longs commentaires, alors que sa qualité est égale à celle de v10.
- v12 (2026-11-12, 8 h 47 d'entraînement) : 21 969 annotations au lieu de 18 014 (4 000 longs commentaires ajoutés,
  les messages WhatsApp retirés). Elle progresse sur toutes les notes, surtout les idées (0,37 → 0,47) et le système (0,60 → 0,64).
  Son test (489 commentaires) est celui de v11 sans les messages WhatsApp : la comparaison est très proche, pas
  exacte.
- v13 (2026-11-14, 10 h 12 d'affinage) : 26 557 annotations au lieu de 21 969 (les 3 000 du 2026-11-13, recalées,
  et 1 588 autres). Même test de 489 commentaires que v12. Elle progresse nettement sur la tonalité (écart 1,80 → 1,58)
  et un peu sur la pertinence et la cible, recule un peu sur le système (0,64 → 0,62) et les idées (0,47 → 0,44).
  Renotation complète du corpus (207 472 commentaires, X compris pour la première fois) le même jour.
- Ton inversé (critique notée comme un éloge ou l'inverse) : 1,5 % avec v9, 2,0 % avec v11, 1,5 % avec v12 (6 sur 401 ; 0 sur 66
  parmi les argumentés), 1,0 % avec v13 (4 sur 401 ; 0 sur 66).
- Le 2026-11-11, v1 à v9, l'essai `essai_long` et les réseaux `affine1` à `affine6` ont été supprimés (3,3 Go).
- 2026-11-13 : 3 000 annotations de plus à la demande de l'utilisateur (lots 244 à 274, total 26 557) : 436 Facebook
  (la source n'en avait que 90), 300 Bluesky, 1 600 `tirer-actif`, 291 longs, 300 réponses, 73 au hasard. Le contrôle
  de dérive a montré la pertinence des cibles L à 6,9 au lieu de 8,8 (lots 1 à 17), le retard portant sur les
  commentaires de 8 mots et plus : elle a été relevée de 1 à 4 points selon la longueur et la tonalité (écart à
  la moyenne des lots 1 à 17), sauf les notes 0 à 3 et les lots « longs » 268-270 déjà au niveau ; moyenne 8,6
  ensuite. Copie avant recalage : `annotations_avant_recalage_lots244-274.csv`, bilan dans
  `recalage/bilan_lots244-274.json`. Pas encore de réentraînement (v12 a 21 969 annotations).

**Dérive de la pertinence, recalée (2026-11-09).** Des lots 18 à 142, la pertinence moyenne des commentaires visant
Lisnard est passée de 8,8 à 0,8 : des « Bravo » notés 0 au lieu de 8. C'est ce qui a fait reculer v6.
`analyse/recalage_pertinence.py` a renoté 400 commentaires à l'aveugle, en a déduit par régression la note de la
grille (écart 1,54, contre 3,61 pour l'ancienne note), et a réécrit 11 393 pertinences ; la copie d'avant est
`annotations_avant_recalage.csv`. Le relancer ne change rien et ne touche jamais les lots après le 142. La même
dérive est réapparue le 2026-11-12 sur les lots 210 à 222 (commentaires longs), corrigée de la même façon avant
enregistrement : d'où le contrôle des moyennes par lot (PROCESS.md, étape 3).

**Constance.** 100 commentaires renotés à l'aveugle dans une autre session : cible identique à 96 %, écart moyen de
0,57 en tonalité et de 1,31 en pertinence. Aucun modèle ne peut faire mieux que ce plancher.

**Pièges rencontrés.**
- Deux calculs lourds en parallèle se ralentissent énormément (jusqu'à 9 fois) : un seul à la fois.
- Les journaux en arrière-plan doivent passer par `python -u`.
- Les annotations ajoutées pendant un réentraînement ne servent qu'au suivant.
- Fenêtre de suivi (2026-11-14, `python -m suivi`) : une sonde est injectée dans l'entraînement déjà lancé par `sys.remote_exec` (Python 3.14), sans l'interrompre.
  Elle lit seulement les variables de `affinage.entrainer` (lot, sorties, perte, poids) et ne ralentit rien de mesurable.
  Une sonde d'une autre version arrête la précédente. Piège : `pas_total` est une variable de cellule (lambda du planificateur).
  Depuis, `affinage.entrainer` démarre la sonde et ouvre la fenêtre dans un processus à part (`ouvrir_suivi`, désactivable par LISNARD_SANS_SUIVI=1).
- Les colonnes de `SOURCES` et `GROUPES` de `analyse/modele.py` définissent les entrées du modèle : ne pas les
  retirer (la colonne « whatsapp » reste, toujours à 0).

## Thèmes des critiques

- **2026-11-11, option E** (parmi cinq méthodes comparées) : Claude lit un par un tous les commentaires argumentés
  qui parlent de lui (pertinence ≥ 12, 20 mots ou plus), les range dans des thèmes qu'il crée au fil de la lecture,
  avec un sens (éloge, critique, doute) et une phrase ; fusion des thèmes proches, puis une synthèse par thème et par
  sens. Ensuite, à la demande (environ une fois par mois), seuls les nouveaux sont lus. Écartées : B, Claude par
  l'API en automatique (clé et crédit facturés à part, déjà écarté pour l'annotation) ; C, un modèle de langue local
  (20 à 40 h de calcul, et il recrée des thèmes déjà existants sous d'autres noms) ; D, les vecteurs seuls (ils
  regroupent des phrases qui se ressemblent, pas des idées : « trop européen » et « pas assez européen » finissent
  ensemble). A, tout relire dans la conversation, est la base de E.
- **2026-11-11, rangement automatique essayé puis retiré** : ranger les nouveaux par proximité de vecteurs donnait
  20 à 30 % de rangements justes ; un classement appris et sévère, 84 % mais pour 8 % des commentaires seulement.
- **2026-11-12, méthode A de [TRI_DES_CRITIQUES.pdf](TRI_DES_CRITIQUES.pdf)** : chaque critique ou doute reçoit une
  catégorie de 1 à 5 (ce que le programme peut en faire). Les 4 020 critiques et doutes existants ont été triés en
  26 lots ; les nouveaux reçoivent leur catégorie à la lecture. La partie « réponses du programme » du PDF est
  reportée : pas de programme pour l'instant.
- **2026-11-12** : commande `a-resumer`, pour ne réécrire que les synthèses qui ont reçu assez de nouveaux
  commentaires.

## Site

- 2026-11-09 : site public sur Vercel (pages statiques) et Supabase (données), sans auteurs ni doublons.
- 2026-11-11 : Bluesky publié, vue pondérée par les « j'aime », date de la dernière collecte en haut de page ; les
  passages dans les médias (`apparitions/`) retirés partout, à la demande : hors sujet.
- 2026-11-12 : filtre de période et filtre de catégorie sur la page Thèmes. Groupes Facebook publiés (« Chaînes et
  groupes de soutien », lien vers le post et le commentaire).
- 2026-11-13 : à la demande de l'utilisateur, **base Supabase normalisée** (modèle en étoile) : tables `sources`,
  `comptes` (avec leur groupe), `publications` (rattachées à un compte), `utilisateurs` (privée : identifiant et nom
  des auteurs, jamais lue par le site) ; `commentaires` ne garde que ses propres données et des numéros (source,
  publication, utilisateur, parent par son code), sa clé devient (source, code) ; la semaine et la taille en mots
  sont calculées par la base, la recherche passe par un index d'expression (plus de colonne `recherche` stockée).
  `moderation` ne garde que la classification et des numéros ; le texte, l'auteur, la date et la publication n'y sont
  écrits que si le commentaire n'est pas déjà dans `commentaires`, et la catégorie retenue, l'origine et la
  catégorie du modèle se calculent dans la vue `moderation_complete`. Les fichiers locaux ne changent pas : la
  publication les traduit. Base : 215 Mo → 113 Mo (`commentaires` 198 → 89 Mo ; `utilisateurs` 12 Mo). Pièges
  rencontrés : avec un paramètre nommé, l'API passe le filtre comme une valeur par ligne et une sous-requête des
  comptes était refaite pour chaque commentaire (> 8 s), et les jointures planifiées sans connaître le filtre
  prenaient 30 s ; `selection` et `evolution` prennent donc un paramètre jsonb unique et sans nom (le corps de la
  requête, passé tel quel). Les anciennes tables sont gardées dans le schéma `ancien` (non exposé) jusqu'à
  vérification. Différence connue : pour les 1 773 commentaires Facebook déjà sur le site, l'onglet de modération lit
  le texte nettoyé du corpus (retours à la ligne en espaces, 431 cas) et le nom sans espace final (36 cas).

- 2026-11-14 : à la demande de l'utilisateur, **le site est protégé par un mot de passe**, comme le site de
  modération : compte Supabase Auth partagé `lecteurs@analyse-lisnard.app` (rôle `lecteur`, `python -m web
  motdepasse`), le rôle `anon` ne lit plus rien (tables et fonctions). Les tables `sources`, `comptes`,
  `publications` et `syntheses` ne s'ouvrent qu'à `peut_lire()` (lecteur ou modérateur, compte encore existant) ;
  `commentaires` s'ouvre à tout compte connecté (il n'existe que les deux comptes partagés ; inscriptions et
  connexions anonymes fermées) et `selection()` / `commentaire()` vérifient `peut_lire()`. Essai écarté : la même
  règle sur `commentaires` interdit l'index plein texte (`@@` n'est pas « leakproof » : 6 s au lieu de 0,1 s,
  au bord du délai de 8 s). Une ancienne session garde donc l'accès direct à la table jusqu'à l'expiration de son
  jeton (1 h au plus) après un changement de mot de passe. Pages en `noindex`, bouton « Se déconnecter » ;
  fonctions des comptes partagées avec la modération (`web/comptes.py`).
- 2026-11-14 : à la demande de l'utilisateur, **page Statistiques retirée** du site (jugée trop brouillonne) : plus
  d'onglet, l'accueil renvoie vers Commentaires et Thèmes, `/statistiques.html` redirige vers l'accueil. Le « cube »
  reste publié (page Le projet, frise de la page Commentaires) ; sa vue pondérée par les « j'aime » n'a plus de page.
- 2026-11-14 : à la demande de l'utilisateur, filtres de la page Commentaires simplifiés : « Comptes » n'a plus que
  « Comptes officiels » et « Autres comptes » (la liste compte par compte reste), « Sujet » devient « Tous / Lisnard /
  Autres », la fiabilité « Toutes / Moyenne et plus / Bonne » (« moyenne et plus » écarte les notes de fiabilité
  faible, 27 % des commentaires : ce n'est pas « toutes »).
- 2026-11-14 : à la demande de l'utilisateur, page Thèmes simplifiée : bloc « Comment c'est fait » retiré ; période
  en curseur sur les mois (12 derniers mois et un cran « Depuis le début » : 95 % des rattachements datent de ces 12
  mois, quelques-uns de 2015, qui écrasaient un curseur sur tous les mois) ; sujets, types d'avis et « Type de
  critique » (ex « Critiques et doutes : ce que le programme peut en faire ») en puces à choix multiple ;
  classement par nombre de commentaires ou d'auteurs seulement (« En hausse » et « Ordre alphabétique » retirés).
  Puis, toujours à sa demande : sous le curseur, une colonne par filtre (Sujets, Type d'avis, Type de critique,
  Classer par), choix les uns sous les autres avec case à cocher (rond pour le classement) ; colonnes côte à côte
  quand la largeur le permet, les unes sous les autres sinon ; recherche de thème retirée.

## Stockage du groupe sur Cloudflare R2

- 2026-11-14 : les commentaires notés partent vers Cloudflare R2, bucket privé `rag-politique-sources-privees`
  (`python -m cloudflare`, règles dans [CLOUDFLARE.md](CLOUDFLARE.md)), en vue d'une API de données du groupe ; tout
  l'ancien export a été retiré du projet. Mêmes règles qu'avant : `data/commentaires/nouvelle-energie/`, **un seul
  Parquet par source** remplacé en entier quand il change (l'ancien est supprimé après vérification du nouveau),
  **sans nom d'auteur** (`auteur_id` = HMAC-SHA256 de « source|identifiant de plateforme », clé locale `AUTEUR_CLE`,
  gardée telle quelle : les identifiants n'ont pas changé). Le bucket public `rag-politique-sources` et le bucket
  privé ont été remplis le 2026-11-13 avec les fichiers du groupe, vérifiés par empreinte. Base D1 envisagée pour les
  commentaires puis écartée : l'offre gratuite limite à 100 000 lignes écrites par jour, R2 suffit pour l'instant.

## Modération Facebook

Demandée le 2026-11-13 par le gestionnaire d'un groupe Facebook de soutien : repérer les commentaires à modérer et
ceux qui appellent une réponse. À part de l'analyse (paquet `moderation/`, onglet « Modération »).

| Date | Ce qui s'est passé |
|---|---|
| 2026-11-13 | Essais sur de vrais commentaires Facebook, relus par Claude (573 : les 173 signalés par textdetox sur 1 500 tirés au hasard, et 400 tirés parmi les autres ; poids 1327/400 pour ramener ces derniers à la population). **textdetox/xlmr-large-toxicity-classifier-v2** (le meilleur modèle public de toxicité en français) : 27 % seulement de ses alertes sont de vraies insultes, il signale des soutiens (« On sera des vôtres », « Lisnard président ! ») et confond ton vif et injure : écarté. **bge-m3-zeroshot-v2.0** (classement sans entraînement, 4 catégories) : 90 % d'alertes justes au seuil 0,7 mais 54 % des insultes trouvées, 3 s par commentaire : écarté. **Qwen3-4B-Instruct-2507** avec une consigne en français (lecture de la probabilité des lettres I/Q/P/A) : 93 % des insultes trouvées, aucun soutien signalé, mais 57 % d'alertes justes ou limites et 6 s par commentaire sur le processeur (30 h pour les 18 000) : écarté pour la lenteur. Les modèles de 8 à 14 milliards de paramètres n'ont pas été essayés (llama.cpp refusé par le contrôle automatique). |
| 2026-11-13 | Affinage de petits modèles sur 2 000 commentaires Facebook annotés par Claude (600 signalés par textdetox, 250 avec « ? », 1 150 au hasard). xlmr-base de textdetox : 71 % d'accord. **multilingual-e5-base : 80 % d'accord en 4 catégories**, 86 % d'alertes justes ou limites, 43 insultes sur 49, 0,09 s par commentaire. Combiner e5 avec textdetox ou xlmr n'apporte rien. |
| 2026-11-13 | À la demande de l'utilisateur, la catégorie « positif » rejoint « autre » (seul compte ce qu'il faut modérer ou à quoi répondre) : réentraînement en 3 catégories, **version m1** en service. Test : accord 90 %, à modérer 57 % justes (78 % avec les limites) et 87 % trouvés, questions 48 % justes et 52 % trouvées (92 exemples seulement à l'entraînement : annoter des questions est la prochaine amélioration). Intégré à part : rien ne tourne pendant la collecte, rien sur le site. Stockage dans Supabase demandé par l'utilisateur : **table à part `moderation`, privée** (aucune règle de lecture publique, pas d'auteurs), plutôt qu'une colonne de `commentaires`, qui est lisible par le public et ne contient que les commentaires déjà notés par l'analyse. |
| 2026-11-13 | Le classement des nouveaux commentaires Facebook est branché à la fin de `python -m collecte` (si Facebook a ramené du neuf), à la demande de l'utilisateur ; annotation et réentraînement restent à la demande. Les commentaires dont la publication n'a pas de texte connu (≈ 5 000, photo ou vidéo seule) sont gardés : leur propre texte compte ; seuls les textes vides sont écartés, comme depuis le début. |
| 2026-11-13 | À la demande de l'utilisateur, 1 000 nouvelles annotations de modération par Claude (4 lots de 250 : 2 « questions », 1 « insultes », 1 « hasard » ; 162 insultants, 108 questions), puis **version m2** (3 000 annotations d'entraînement, même test de 573). Test : accord 91 % (m1 90 %), à modérer 62 % justes (57 %) et 81 % trouvés (87 %), questions 70 % justes (48 %) et 57 % trouvées (52 %). Correction de `tirer` : les lots tirés d'avance réservent leurs commentaires (deux lots tirés à la suite se chevauchaient). |
| 2026-11-13 | Pour un futur onglet des administrateurs du groupe, la table privée `moderation` reçoit le commentaire lui-même (texte, auteur, identifiant de l'auteur, date, réponse à, publication). Le lien n'est pas recopié : la vue privée `moderation_complete` le forme à partir de `publications.lien` (+ `comment_id`, `reply_comment_id`). Les 664 publications Facebook manquantes sont ajoutées à `publications` sans écraser celles du site. Coût : 6 → 10 Mo (base 226 Mo sur 500). Avant, seuls 10 % des commentaires classés (61 « à modérer » sur 734) se retrouvaient dans `commentaires`, qui n'a pas d'auteurs. |
| 2026-11-13 | **Site de modération** à la demande de l'utilisateur, à part du site public (projet Vercel `moderation-lisnard`, `moderation/site/`). Accès par mot de passe choisi par l'utilisateur : compte Supabase Auth partagé (adresse fixe, on ne tape que le mot de passe) portant `app_metadata.role = moderateur`, inscriptions fermées ; les tables privées `moderation` et `utilisateurs` ne s'ouvrent qu'à ce rôle (règles RLS), et `est_moderateur()` vérifie que le compte existe encore, si bien que changer le mot de passe (compte recréé) coupe toutes les sessions. Écartés : la protection par mot de passe de Vercel (payante) et une fonction serveur qui lirait avec la clé secrète (clé secrète hors de la base, plus de pièces). Retirer ou bloquer un membre depuis le site est impossible (API des groupes Facebook fermée en 2024) : le site ouvre sa fiche de membre du groupe, où l'administrateur le fait. Ajout d'un suivi partagé « Traité » / « Sans suite » (`moderation_suivi`). Première version : vues calculées par la base à chaque recherche (0,3 à 0,5 s sur 17 841 commentaires). |
| 2026-11-13 | À la demande de l'utilisateur (offre gratuite de Supabase), le travail passe dans le navigateur : téléchargement complet une seule fois (≈ 18 pages de 1 000), gardé dans IndexedDB, puis seulement les nouveautés (colonne `maj` datée par déclencheur, table `moderation_retires` remplie à la suppression, suivi par date ; « à traiter » est écrit au lieu d'effacer la marque). Mesuré en ligne : rechargement = 4 requêtes vides (8 octets, 0,2 ms de base chacune), aucune requête pour filtrer ou trier, une par marque. Vues `moderation_site`, `moderation_auteurs`, `moderation_publications`, `moderation_bilan` retirées. Site mis en ligne : https://moderation-lisnard.vercel.app. |
| 2026-11-13 | Connexion X automatique réessayée (une fois, profil temporaire) : toujours « temporairement limité votre connexion » juste après le pseudo. Le profil `sessions/x_profil/` n'avait aucune session : `collecte.connexion_x` y recopie maintenant la session valable et, à l'expiration, la fait renouveler par X sans fenêtre ni mot de passe (essai réel : fichier de cookies vidé, session rendue par le profil) ; le mot de passe ne sert que si X annule la session. Nouvelle option `--profil` après des cookies collés à la main. |
| 2026-11-14 | Retours du gestionnaire du groupe, à la demande de l'utilisateur. **Site** : plus de couleurs (bleu et jaune de Nouvelle Énergie), onglet **Statistiques** (évolution des insultants, questions et mots surveillés ; « traité » par modérateur dans le temps et bilan par modérateur), mode d'emploi retiré, un seul groupe montré (« Soutien David Lisnard 2027 », restriction posée dans la règle de lecture de la base, les autres groupes restent pour l'entraînement). **Mots surveillés** : filtre hors modèle (choix de l'utilisateur), liste provisoire de 167 mots ou expressions écrite par Claude dans `moderation/mots_surveilles.txt`, en attendant la liste officielle. **Cible des insultes** : Claude a relu les 443 insultants annotés avec leur publication ; 16 seulement visent Lisnard ou Nouvelle Énergie (3 %), trop peu pour une classe du modèle. Retenu : la cible L/A de l'analyse principale (qui lit aussi la publication et le parent), remplacée par la lecture pour un insultant annoté (`L:` / `I:`). Sur les insultants déjà notés par l'analyse, elle dit L un peu trop souvent (elle note « parle de Lisnard », pas « l'insulte le vise ») : à mesurer sur les prochains lots. **Annotation par Gemini** (choix de l'utilisateur) : prompt `moderation/PROMPT_GEMINI.md`, `noter --par gemini`, relecture complète par Claude (`relire`), colonne `par` ; les lots montrent désormais la publication et le commentaire parent. Pas de réentraînement : la renotation v13 de l'analyse tournait. |
| 2026-11-14 | Premiers lots lus par **Gemini** dans Antigravity (prompt `moderation/PROMPT_GEMINI.md`, l'agent choisit les modes) : lots 5 à 8 (questions, insultes, questions, hasard), 1 000 commentaires, relus en entier par Claude (`relire`). Accord 90 % (87 %, 88 %, 89 %, 98 % par lot). Par rapport à Claude, les insultants de Gemini sont justes à 86 % et il en trouve 95 % ; ses questions sont justes à 73 % et il en trouve 82 %. Ses erreurs : questions adressées à un autre commentateur ou rhétoriques comptées comme questions ; étiquettes sans injure (« fasciste », « bolcheviques », « traître ») comptées comme insultes ; il voit trop souvent la cible Lisnard (7 L, dont 3 retenus) ; il manque les affirmations fausses à rectifier (« il était macroniste »). Toutes les annotations de Gemini sont désormais relues. Le prompt reçoit une partie « Erreurs déjà vues », avec des exemples tirés de ces lots, pour les prochains. |
| 2026-11-14 | À la demande de l'utilisateur (plusieurs modérateurs connectés en même temps) : les marques « Traité » / « Sans suite » des autres sont redemandées toutes les **10 s** page visible (au lieu de 3 min) et changent la carte sur place, sans la retirer de la liste ; les nouveaux commentaires ne sont plus redemandés tout seuls toutes les 15 min, seulement à l'ouverture du site et au bouton « Actualiser ». Coût : une requête par index, vide presque toujours. Supabase Realtime écarté : il faudrait la bibliothèque supabase-js et une connexion ouverte par modérateur, pour un gain de quelques secondes. |
| 2026-11-14 | Lots 9 à 12 de **Gemini** (questions, insultes, questions, hasard ; 844 commentaires : le lot « insultes » s'est arrêté à 94, plus aucun candidat probable), avec le prompt corrigé, relus en entier par Claude. Accord **95 %** (90 % pour les lots 5 à 8). Ses insultants sont justes à 96 % et il en trouve 87 % ; ses questions sont justes à 98 % et il en trouve 81 %. Il est devenu trop prudent : il oublie des questions (absence de Lisnard des médias, « Et Sarah Knafo ? », le futur gouvernement, doutes sur un sondage) et des insultes sur l'intelligence ou des comparaisons à la Gestapo. Le prompt reçoit un point 5 sur ces oublis, et le point 2 est corrigé : la désindexation et l'abattement de 10 % sont de vraies pistes du programme, à préciser par l'équipe et non des affirmations fausses. |
| 2026-11-14 | À la demande de l'utilisateur, le compteur « dont visant Lisnard / NE » est retiré du haut du site de modération : le filtre « Sujet » (Lisnard / Nouvelle Énergie) fait la même chose. Restent quatre compteurs : insultants, questions, mots surveillés à traiter, marqués « traité ». |
| 2026-11-15 | Une collecte Facebook s'est arrêtée à 22:07 sur `PermissionError [WinError 5]` en remplaçant `facebook/etat.json` (fichier momentanément tenu par un autre programme : interface, antivirus, indexation). Correctif : `commun/fichiers.py` réessaie le remplacement jusqu'à 20 s (`remplacer`), pour `ecrire_json` et `ecrire_csv`. X n'était pas arrêté : lecture des fils au rythme voulu (≈ 40 requêtes / 15 min, ≈ 40 fils par heure). |
| 2026-11-19 | **Réponses préparées**, à la demande du gestionnaire du groupe (débunker le RN et l'accusation de « Macron bis », répondre à tous les commentaires). Choix : réutiliser les **thèmes de l'analyse** (T1…T59) plutôt que des catégories nouvelles ; ranger chaque commentaire qui appelle une réponse (question, ou négatif sur Lisnard / NE, tonalité ≤ 8 ; non insultant, 5 mots ou plus ; 3 214 le 2026-11-19) par lots lus par **Gemini Flash** (prompt `moderation/PROMPT_GEMINI_THEMES.md`, pour ménager les crédits Claude) ou par Claude, comme pour les thèmes de l'analyse : aucune méthode automatique n'est fiable sur 60 thèmes avec si peu de texte. Les 897 commentaires du groupe déjà lus par Claude pour l'analyse (critiques et doutes) gardent leurs thèmes. Bibliothèque de départ écrite par Claude : **89 réponses, 36 objections, 30 thèmes**, en cinq styles (chiffres, argumentée, courte, bienveillante, punchline avec un mot de GIF), avec seulement des faits sourcés (ses propres textes du corpus Nouvelle Énergie, chiffres jugés exacts ou plutôt exacts par `verification/`, mesures dites comme des propositions), la source sous chaque réponse. Rangement dans `moderation/reponses.xlsx` (demande de l'utilisateur : un fichier Excel) et dans les tables `reponses` et `reponses_themes` de Supabase, que les modérateurs modifient depuis le site (ajouter, modifier, retirer une réponse, ajouter un thème ; jamais de suppression). `python -m moderation reponses` synchronise dans les deux sens par fusion à trois voies (empreintes de la dernière synchronisation) : en cas de conflit, le site l'emporte. Pré-remplir la zone de réponse de Facebook est impossible depuis un autre site : « Copier et ouvrir le commentaire ». Colonne `themes` ajoutée à `moderation` : renvoi complet des 51 221 lignes une fois (modèle 4 de `moderation/publication.py`). |
| 2026-11-19 | À la demande de l'utilisateur, la **cible** de la modération (« vise Lisnard / NE », 2026-11-14) est retirée partout : elle ne marchait pas et n'apportait rien. Site : filtre « Sujet », badge et réglage des Statistiques retirés ; Supabase : colonnes `cible` et `annotation_cible` de `moderation` supprimées (vues recréées), renvoi complet (modèle 5 de `moderation/publication.py`) ; annotations : colonne `cible` retirée d'`annotations.csv` et lignes `L:` des lectures fondues dans `I:` (les catégories ne changent pas) ; lecture en deux lignes `I:` / `Q:` (prompt Gemini réécrit). Le modèle de modération ne l'avait jamais apprise. Les commentaires à ranger pour les réponses préparées : question, ou tonalité de l'analyse ≤ 8 (sans la cible, presque les mêmes : l'analyse donne 10 à ceux qui ne parlent pas de Lisnard). La cible de l'analyse principale (site public) ne change pas. |
| 2026-11-20 | **Réponses préparées complétées** à la demande de l'utilisateur : 198 réponses ajoutées par Claude (R-0090 à R-0287), soit **287 réponses sur les 60 thèmes**, chacun avec au moins 4 réponses et 3 styles (les 29 thèmes vides et ceux à 1-3 réponses). Objections tirées des synthèses des thèmes (critiques et doutes, `themes.json`). Mêmes règles de sources : chiffres jugés exacts ou plutôt exacts par `verification/`, chiffres officiels relevés par ses analyses (DREES, OCDE, Cour des comptes, DGFiP : par exemple 18,2 % de la population en zone sous-dense, 4,7 % par an pour l'Erafp, dette de Cannes de 255 à 174 M€), propos de Lisnard tirés du corpus `verification/corpus` ; sans chiffre sourcé, réponse sans chiffre (retards, Covid, 17 octobre 1961). R-0062 corrigée : « ancien président de l'AMF » devient « élu en 2021 à la tête de l'AMF » (encore président en août 2026 d'après le corpus). Vérifié au passage : le site de modération ne reçoit que le groupe « Cap 2027 avec David Lisnard » (règle `moderateurs` de la table `moderation` et vue `moderation_pubs`, `moderation_publications()` de `web/schema.sql`) : session de modérateur simulée dans Supabase, 31 161 commentaires visibles, tous de ce groupe, aucun des 5 autres groupes Facebook. |
| 2026-11-19 | Lots 13 à 16 de **Gemini** (questions, insultes, questions, hasard ; 1 000 commentaires, sans la cible), relus en entier par Claude : accord **87,5 %** (90 %, 78 %, 86 %, 96 % par lot ; 125 corrections). Le lot « insultes » est le plus faible : Gemini laisse passer « gauchiasse » (insultant 21 fois sur 23 dans les lectures de Claude), le message collé partout « couper l'herbe sous les pieds des enfoirés qui nous gouvernent » (insultant à chaque fois), « débiles », « suceurs de babouches », « QI de courge ». Il oublie aussi des questions : reproches sur les retraités sans point d'interrogation, « Attal de droite ? », la primaire « entre macronistes », « il a voté Macron / parrainé Mélenchon ». Point 6 ajouté au prompt. Puis, à la demande de l'utilisateur, **1 000 annotations de plus par Claude** (lots 17 à 20 : questions, insultes, questions, hasard ; 217 insultants, 224 questions ; 7 417 annotations en tout) et **1 000 commentaires rangés par thème par Claude** (lots 7 à 16 ; 1 508 rangés, dont 1 295 avec un thème ; 2 040 restent à ranger). |
| 2026-11-20 | **Version m3** de la modération (6 844 annotations d'entraînement, même test de 573). Test : accord 90 % (m2 91 %), à modérer 60 % justes (62 %) et **87 % trouvés** (81 %), questions 56 % justes (70 %) et 52 % trouvées (57 %). Gardée à la demande de l'utilisateur (deux fois plus de données) ; le test ne compte que 25 questions et 49 insultants (une question ≈ 4 points), l'écart sur les questions est en partie du hasard. 51 221 commentaires reclassés (2 092 insultants, 2 778 questions) et envoyés à Supabase. |
| 2026-11-20 | À la demande de l'utilisateur (améliorer nettement les questions et les insultes), **relecture complète par Claude des 3 573 annotations du 2026-11-13** (le test de 573 et les 3 000 premières d'entraînement), à l'aveugle (sans la prédiction du modèle), avec les règles actuelles du prompt Gemini (points 1 à 6). Ces annotations avaient été faites avant que les règles ne s'élargissent : elles étaient nettement plus strictes que les lots suivants, et le modèle apprenait une règle et était mesuré sur une autre. Test : 75 changements sur 573 (87 % d'accord), tous dans le même sens (42 « autre » → insultant, 31 → question) : il compte désormais 92 insultants et 54 questions au lieu de 49 et 25, ce qui rend aussi la mesure moins bruitée. Entraînement : 354 changements sur 3 000 (88 % d'accord ; 141 → insultant, 166 → question, 46 dans l'autre sens). Mesuré sur le test corrigé, m3 signale juste (87 % de ses insultes, 86 % de ses questions) mais en manque beaucoup (61 % des insultes et 40 % des questions trouvées). Limite : une cinquantaine des commentaires du test avaient été vus avec la prédiction de m3 juste avant la relecture. Version d'avant gardée dans `donnees/moderation/annotations_avant_relecture_2026-11-20.csv`. |
| 2026-11-20 | **Relecture complète par Claude des 1 844 annotations de Gemini du 2026-11-14**, avec les mêmes règles : 92,6 % d'accord, 137 changements (102 « autre » → question : affirmations fausses à rectifier, retraites, primaire, sondages, absence médiatique, groupes locaux, « et Sarah Knafo ? » ; 13 question → autre ; 14 insultant → autre ; 7 autre → insultant ; 1 insultant → question). Version d'avant gardée dans `donnees/moderation/annotations_avant_relecture_gemini_2026-11-20.csv`. |
| 2026-11-20 | **Essais pour améliorer la modération** (banc à part : 1 359 annotations d'entraînement mises de côté par empreinte de la clé, mesure F sans pondération ; le test de 573 ne compte que 54 questions). Retenu : le modèle lit le **commentaire parent en second segment** (« En réponse à : … », 300 caractères, ou « Commentaire direct. ») : insultes F 0,808 → 0,822, questions 0,676 → 0,700, accord 82,6 → 83,7 %, entraînement 15 % plus long. Écartés : titre de la publication en plus (questions 0,738 mais insultes du test 0,784 → 0,698, 60 % plus lent) ; **CamemBERTa v2** (accord 65 %, n'apprend pas en 4 époques) ; **mmBERT-base** (questions 0,670, un peu sous e5) ; moyenne e5 + mmBERT (+0,004, deux fois le coût) ; seuils réglés par classe (rien de stable sur le test). La moitié environ des erreurs restantes sont des annotations discutables : la relecture des étiquettes a plus apporté que le changement de modèle. |
| 2026-11-20 | **Version m4** de la modération : contexte du parent, annotations relues (6 844 d'entraînement, test corrigé de 573 : 92 insultants, 54 questions). Sur ce test, comparée à m3 : insultes 91 % justes (m3 87 %) et **71 % trouvées** (61 %), questions 69 % justes (86 %) et **64 % trouvées** (40 %) ; F insultes 0,71 → 0,80, questions 0,55 → 0,66 ; accord 88 %. 51 221 commentaires reclassés (2 409 insultants, 4 528 questions ; m3 : 2 092 et 2 778) et envoyés à Supabase. m3 gardé dans `modeles/moderation_m3/` (à supprimer si m4 convient). |
| 2026-11-20 | À la demande de l'utilisateur, **2 000 commentaires du groupe « Cap 2027 » rangés par thème par Claude** pour les réponses préparées (lots 17 à 36). Nouvel ordre de tirage, demandé par l'utilisateur : **les questions d'abord, puis les autres commentaires qui appellent une réponse, chaque fois du plus long au plus court** (`a_lire()` de `moderation/reponses.py`, au lieu des plus récents d'abord) ; consigne reprise dans `moderation/PROMPT_GEMINI_THEMES.md` pour les prochains lots de Gemini. 1 865 questions (toutes celles qui restaient) puis 135 critiques longues ; 1 889 avec au moins un thème, 111 sans. Thèmes les plus fréquents : union des droites et primaire (524), pensions des retraités (501), proximité avec Macron (331, surtout le vote de 2017 et le parrainage de Mélenchon), rapport au RN (134), chances en 2027 (107). Beaucoup de questions pratiques (adhésion, carte, groupe local, meeting, direct) n'ont pas de thème : « - ». Restent 952 commentaires à ranger. |
| 2026-11-20 | Suite, à la demande de l'utilisateur : **les 952 derniers commentaires du groupe « Cap 2027 » rangés par Claude** (lots 37 à 46, critiques et doutes du plus long au plus court) ; plus rien à ranger (4 460 commentaires rangés en tout). Les plus courts (« Macron bis », « tout seul il perdra », moqueries) ont souvent un thème quand ils visent un reproche précis, sinon « - ». |
| 2026-11-16 | Le site de modération suit le groupe « Cap 2027 avec David Lisnard » (et non plus « Soutien David Lisnard 2027 », choisi par erreur) : règle `moderation_publications()` de `web/schema.sql`, titre du site, documents. À réappliquer : relancer `web/schema.sql` dans Supabase. |
| 2026-11-22 | À la demande de l'utilisateur, **le site de modération montre de nouveau tous les groupes Facebook** (6 groupes, 51 221 commentaires en session de modérateur simulée), avec un choix des groupes en haut de toutes les vues (cases à cocher, gardées dans l'adresse), « Cap 2027 avec David Lisnard » coché par défaut, et une phrase qui rappelle que seul ce groupe est rangé par thème pour les réponses préparées. `moderation_publications()` ne filtre plus par nom de groupe (appliqué avec `python -m commentaires installer`) ; menu de l'auteur : une fiche par groupe ; cache du navigateur en version 5 (tout retéléchargé une fois). |
| 2026-11-22 | À la demande de l'utilisateur, les **compteurs du haut** du site de modération (insultants, questions, mots surveillés à traiter, traités) suivent les filtres en cours (groupes, période, thème, recherches, auteur, publication) au lieu d'être globaux ; ceux que fixe une tuile (catégorie, suivi, mots surveillés, certitude) ne comptent pas, et un clic sur une tuile garde les autres filtres. |

## Vérification factuelle (depuis le 2026-11-14)

- 2026-11-14 : paquet `verification/` créé à partir du « Dossier de vérification Lisnard » d'un collègue (16 thèmes, 69 affirmations) et du corpus RAG copié depuis R2. Décisions de l'utilisateur : un thème terminé avant le suivant, thème pilote = dette, dépense publique et fiscalité, échelle à six verdicts, tout en local jusqu'à son accord, chiffrages de mesures autorisés mais marqués comme estimations.
- 2026-11-14 : thème 1 terminé (22 affirmations, 41 sources). Le site de l'Agence France Trésor refuse les téléchargements automatiques : la maturité moyenne de la dette reste à déposer à la main.
- 2026-11-14 : les 16 thèmes terminés, 112 affirmations : 27 exactes, 27 plutôt exactes, 21 trompeuses, 11 fausses, 13 invérifiables, 13 opinions. Sites inaccessibles aux robots ce jour-là (à reprendre à la main ou plus tard) : Agence France Trésor, Légifrance, education.gouv.fr, oecd.org, DGEF et Interstats, Santé publique France (exploitants agricoles), ASPI ; data.gouv.fr et vie-publique.fr en panne (503) pour le thème 14. Comptes communaux : comptes individuels de la DGFiP sur data.economie.gouv.fr (2000-2025), plus longs que l'OFGL (2018-2025). `commun/lecture.fmi` lit désormais les fichiers du FMI à plusieurs pays.
- 2026-11-14 : publication, à la demande de l'utilisateur, dans le bucket R2 public `rag-politique-sources` (`python -m cloudflare verification`, `--essai` pour voir sans rien envoyer) : `originaux/ne/verification/<thème>/` (affirmations.csv, sources.csv, brut/) et `data/programmes/nouvelle-energie/verification/` (contenu de calculs/, SYNTHESE.md, registre_affirmations.csv) ; section balisée dans le README du bucket. Ne touche que ces préfixes.
- 2026-11-20 : publication R2 de la vérification arrêtée (décision de l'utilisateur) : `commun/cloudflare/verification.py` et la commande `python -m commun.cloudflare verification` retirés ; les fichiers bruts ne sont plus republiés. Sur le bucket public, les données déjà déposées restent, les 16 `calculer.py` sont supprimés (pas de code sur R2). Les originaux (`originaux/ne/verification/`, 197 fichiers) avaient été retirés par un autre membre du groupe lors de sa réorganisation du bucket.
- 2026-11-15 : site public de la vérification, à la demande de l'utilisateur : `python -m verification site deployer` → https://verification-lisnard.vercel.app (projet Vercel « verification-lisnard », à part du site des commentaires). Choix de l'utilisateur : hébergement Vercel, aucune connexion à Supabase, données figées dans les pages. Une page par thème (ce qu'il dit, ce que disent les chiffres, conclusion), calcul et sources repliés pour rester lisible. Les conclusions courtes, les types d'écart (arrondi, superlatif, périmètres mélangés…) et les valeurs des petits graphiques sont écrits par Claude dans `verification/conclusions.py` à partir des `analyse.md` ; le générateur refuse une valeur absente de `analyse.md`. `web/vercel.py` envoie désormais les images en base64.
- 2026-11-15 : retours de l'utilisateur sur le site de la vérification. Pages « Toutes les affirmations » et « Méthode » supprimées (elles embrouillaient ; redirigées vers l'accueil), ainsi que le sommaire en pastilles, « Évolution » et « Sources qu'il cite » de « Ce qu'il dit », « Quand il s'écarte des chiffres », « Ce qui reste à vérifier » et « Lire un verdict ». « Ce qu'il dit » en cartes, une par idée ; affirmations en cartes numérotées séparées ; « Pourquoi » point par point. **Étiquettes à la place des verdicts** : l'utilisateur trouve abusif d'écrire « faux » pour une phrase vraie mais grossie par un superlatif (ex. les 950 Md€ de dépenses sociales). Le site montre donc le type d'écart (« Superlatif », « Chiffre grossi »…) et une famille de couleur (exact, proche, à nuancer, inexact, invérifiable, promesse) ; un superlatif, un arrondi ou un chiffre daté ne descend jamais sous « à nuancer ». Les verdicts d'`analyse.md`, de `SYNTHESE.md` et du registre ne changent pas.

- 2026-11-20 : **deuxième candidat, Jean-Luc Mélenchon (La France insoumise)**, à la demande de l'utilisateur, pour
  pouvoir à terme superposer les candidats thème par thème. `verification/` devient multi-personnes sans rien changer
  pour David Lisnard (dossiers, site et projet Vercel identiques ; le site Lisnard régénéré est identique octet pour
  octet) : `commun/personnes.py` (une fiche par personne), `commun/themes.py` (catalogue commun : mêmes numéros et
  mêmes noms de dossier pour tous), `python -m verification melenchon <commande>`. Données dans
  `donnees/verification/melenchon/`, scripts et site dans `verification/melenchon/`. Corpus : les Parquet `lfi` du
  bucket R2 (programme L'Avenir en commun 2026, passages vidéo YouTube et Instagram découpés par locuteur) ; seuls les
  passages où il parle sont lus (`parle_personne`), les transcriptions complètes non découpées ne sont jamais citées.
  Trois nouveaux thèmes, numérotés à la suite pour tout le monde : 17 inégalités et pauvreté, 18 climat et
  environnement, 19 égalité femmes-hommes et discriminations. Un fichier déjà téléchargé pour une personne est repris
  tel quel pour l'autre (`sources.reprendre()`, même empreinte, date d'origine). Premier état : 15 thèmes, 53
  affirmations (9 exactes, 20 plutôt exactes, 4 trompeuses, 10 fausses, 10 opinions ou promesses). Pas encore faits :
  2 (sécurité), 9 (retraites), 14 (institutions : pages officielles du 49.3 et des référendums bloquées aux robots ce
  jour-là).
- 2026-11-21 : **un seul site pour tous les politiques**, à la demande de l'utilisateur : « Vérification politique »,
  https://verification-politique.vercel.app (projet Vercel `verification-politique`). Le projet `verification-lisnard`
  est supprimé de Vercel (son adresse ne répond plus). `verification/site/` contient l'accueil général (choix du
  politique, tableau des 19 thèmes communs avec la barre de verdicts de chacun) et un dossier par politique
  (`lisnard/`, `melenchon/`) ; un sélecteur dans l'en-tête de toutes les pages. Ajouter un politique dans
  `commun/personnes.py` l'ajoute au site dès qu'il a un thème terminé. Les cartes de thème montrent le numéro commun
  du thème, pas leur rang. Données : la vérification s'appuie sur ce qui est en local ; le bucket R2 n'est qu'une
  source parmi d'autres, copiée en local avant usage (`python -m verification <clé> corpus`), et Internet sert à
  compléter (décision de l'utilisateur).
- 2026-11-21 : Mélenchon complété sur les thèmes 2 (chiffres de l'OFDT), 9 (retraite à 60 ans : âge légal et
  trimestres actuels, service-public.fr) et 14 (49.3 : 25 recours de 2017 à fin 2024 selon l'Assemblée nationale,
  « 32 » invérifiable faute de décompte officiel de 2025-2026 ; référendum de 2005 : 54,67 % de « non »). Il est
  vérifié sur ses 18 thèmes, 57 affirmations. Les dossiers locaux `paroles-candidat`, `paroles-youtube` et
  `Lisnard-en-paroles`, qui contenaient des transcriptions de Mélenchon, ne sont plus sur le disque : le corpus local
  est la copie des Parquet LFI de R2 dans `donnees/verification/melenchon/corpus/`.

## Données centralisées (2026-11-19)

À la demande de l'utilisateur, qui trouvait les mêmes données rangées dans plusieurs fichiers, chaque information n'a
plus qu'une place. Sources de vérité : les CSV de collecte et le travail fait à la main (annotations, corrections,
thèmes, catégories de modération). Tout le reste se recalcule et va dans `donnees/analyse/corpus.csv`, la table
centrale (une ligne par commentaire).

| Avant | Maintenant |
|---|---|
| `donnees/analyse/scores.csv` (notes du modèle, une ligne par commentaire) | colonnes `note_version`, 5 notes, `cible`, `p_autre`, `fiabilite`, `note_le` du corpus |
| `donnees/moderation/notes.csv` (classement de la modération) | colonnes `mod_categorie`, `mod_p_…`, `mod_version`, `mod_le` du corpus |
| la modération relisait les CSV Facebook elle-même | elle lit le corpus (texte nettoyé : espaces, liens en `[lien]`) ; mesures du modèle m2 inchangées sur le test |
| texte recopié dans `moderation/annotations.csv` | retiré : le texte se lit dans le corpus par la clé |
| `annotations_avant_recalage.csv` et `…_lots244-274.csv` (copies complètes, seule la pertinence différait) | colonne `pertinence_origine` d'`annotations.csv` (11 393 + 1 319 notes) |
| noms d'auteurs relus à part par le site, Cloudflare et la modération | une seule lecture : `analyse.corpus.auteurs()` |
| `<source>_tout.xlsx`, recopie des CSV à chaque collecte (46 Mo) | supprimés ; bouton « Dossier » de l'onglet |
| deux versions du modèle gardées (v11, v12, `affine8`, `affine9` : 1,1 Go) | seule la version en service (v13, `affine10`) |
| journaux de lancements à la main à la racine de `donnees/` | `donnees/journaux/` |

Deux tâches écrivent le corpus (notation et modération) : chacune n'écrit que ses colonnes, sous un verrou
(`donnees/analyse/CORPUS_VERROU`). Vérifié avant et après : notes affichées, export du site, fichiers Cloudflare
(mêmes empreintes), modération, thèmes, ton inversé identiques. Restent volontairement à part : les relations
un-à-plusieurs (un commentaire peut avoir plusieurs thèmes : `rattachements.csv`), les lots (numéros des réponses de
Claude) et l'état de chaque envoi (`publie.json`, `cloudflare/etat.json`). Anciens fichiers gardés une fois dans
`donnees/sauvegardes/avant_centralisation_2026-11-19.zip`.

## Pistes non faites

- Threads, X : à tenter seulement avec un compte créé pour la collecte, pour qu'un
  bannissement ne touche pas un compte personnel.
- Annoter des lots Facebook (aucune annotation) et Bluesky (très peu) avant le prochain réentraînement :
  `tirer-actif N --source facebook`.

## Réorganisation des dossiers (2026-11-20)

Un dossier par site web (le code), un pour le code commun, un pour la documentation, et un seul pour toutes les
données, celles des sites comprises.

| Avant | Maintenant |
|---|---|
| `web/`, `python -m web …` | `commentaires/`, `python -m commentaires …` (le site public des commentaires) |
| `moderation/`, `verification/` | inchangés (les deux autres sites) |
| `collecte/`, `analyse/`, `critiques/`, `interface/`, `suivi/`, `cloudflare/` | `commun/collecte/`, `commun/analyse/`… ; `python -m commun.collecte`, `python -m commun.analyse`… |
| `PROCESS.md` (racine) | `docs/PROCESS.md` |
| `modeles/`, `sessions/` (racine) | `donnees/modeles/`, `donnees/sessions/` |
| `moderation/reponses.xlsx`, `moderation/mots_surveilles.txt` | `donnees/moderation/` (toujours suivis dans git) |
| `verification/corpus/`, `registre_affirmations.csv`, `SYNTHESE.md`, et dans chaque thème tout sauf les scripts | `donnees/verification/` (même arborescence, suivie dans git) ; les scripts `registre.py`, `telecharger.py`, `calculs/calculer.py` restent dans `verification/themes/` et trouvent leurs données par `verification.commun.chemins.donnees_de()` |

Les lanceurs `.bat` restent à la racine (même chemin pour les tâches planifiées de Windows). Les dossiers de données
(`donnees/web/`, verrou « web »…) gardent leur nom. Les lignes plus haut citent les anciens chemins, laissés tels quels.

## Ancienne organisation (avant le 2026-11-09)

| Avant | Maintenant |
|---|---|
| `python collecter.py …`, `commun.py`, `sources/*.py` | `python -m collecte …`, `commun/` et `collecte/depot.py`, `collecte/sources/` |
| `python analyser.py …` | `python -m analyse …` (`analyse/notation.py`) |
| `python interface.py`, `interface_analyse.py`, `theme.py` | `python -m interface`, `interface/` |
| `perimetre.json`, `cles.json`, `compte.json` | `config/` |
| `essais/` (méthodes Instagram comparées le 2026-11-07) | retiré ; copie dans `donnees/sauvegardes/code_avant_reorganisation_2026-11-09.zip` |
| `python -m analyse.modele entrainer` (vecteurs seuls) | `python -m analyse.ensemble tout` |

## Proximité des candidats (2026-11-21)

Nouveau sous-projet `proximite/` : placer les candidats à la présidentielle 2027 les uns par rapport aux autres à
partir de leurs programmes publiés (liste : candidats2027.org). Premier essai sur 13 programmes, 2 357 mesures, à
refaire quand tous seront publiés.

- **Trois axes** : économie et social, ordre et immigration, souveraineté et monde. Sécurité et immigration réunies
  en un seul axe (elles vont presque toujours ensemble dans les programmes), ce qui laisse le troisième à l'Europe et
  au monde, qui sépare des candidats que les deux autres rapprochent. Institutions et autres sujets relevés sans
  compter sur un axe.
- **Notes de −3 à +3** par mesure ; position sur un axe = moyenne des sous-thèmes (chacun pèse autant), pour qu'un
  programme très détaillé sur un sujet ne pèse pas plus.
- **Lecture complète par Claude, sans tri par le code** (décision de l'utilisateur, 21/11). Un premier passage avait
  lu les programmes très longs dans une version resserrée (puces et mesures clés de Mélenchon, propositions phares de
  Philippe, passages repérés par mots-clés chez Ruffin, Becht et Branco) : abandonné, car c'est à Claude de lire et de
  juger, pas à un filtre. Option `--tri` retirée ; Branco, Becht, Philippe, Cazeneuve, Ruffin et le complément de
  Mélenchon relus en entier (1 826 → 2 357 mesures).
- **Carte 3D** dessinée sans bibliothèque (canvas), pour un site entièrement statique sans script extérieur.
- **2026-11-21, carte 3D remplacée** (demande de l'utilisateur : « trop brouillon, incompréhensible ») : une ligne de
  −3 à +3 par axe, chaque candidat nommé dessus (noms en étages pour ne pas se chevaucher), puis un plan à deux axes
  au choix aux quatre quarts nommés ; SVG sans bibliothèque. Tableau des distances : noms des colonnes à l'horizontale
  (ils étaient retournés). Notes par thème : un axe à la fois avec un sélecteur, sans le nombre de mesures, et une clé
  de lecture en couleur (−3 et +3 nommés). En-tête réduit à « Présidentielle 2027 ».
- **2026-11-21, Emmanuel Macron 2017 ajouté pour comparaison** (au choix entre 2017 et 2022 : 2017, sa première
  élection) : programme d'En Marche lu en entier, 119 mesures (E +0,0, O +0,6, S −0,3). Mécanisme `REFERENCES` dans
  `proximite/collecte.py` pour les anciens programmes, hors de l'export de candidats2027.org.
- **2026-11-21, distances par axe** (demande de l'utilisateur) : le tableau des distances se lit sur les trois axes
  (comme avant) ou sur un seul au choix ; sur un axe, distance = écart des positions, 100 = l'un à −3 et l'autre à +3.
- **2026-11-22, sens de chaque sous-thème** (demande de l'utilisateur) : au-dessus de chaque colonne des notes par
  thème, ce que veut dire −3 et +3 en un ou deux mots (`POLES` dans `proximite/axes.py`, repris dans la grille).
  Section « Méthode » retirée du site.

