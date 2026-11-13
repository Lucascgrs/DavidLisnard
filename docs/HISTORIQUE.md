# DavidLisnard : historique des choix

Ce qui a été décidé, essayé ou abandonné, et pourquoi. Le fonctionnement actuel est dans [README.md](../README.md),
la marche à suivre pour une mise à jour dans [PROCESS.md](../PROCESS.md).

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

- La méthode à vecteurs seule plafonne (v3 ≈ v2) : le gain vient du réseau affiné (`analyse/affinage.py`, qui lit le
  commentaire avec son parent et le titre) et de la combinaison des deux (`analyse/ensemble.py`).
- v11 (256 jetons pour le commentaire au lieu de 128) a été mise en service le 2026-11-11 à la demande de
  l'utilisateur, pour lire en entier les longs commentaires, alors que sa qualité est égale à celle de v10.
- v12 (2026-11-12, 8 h 47 d'entraînement) : 21 969 annotations au lieu de 18 014 (4 000 longs commentaires ajoutés,
  les messages WhatsApp retirés). Elle progresse sur toutes les notes, surtout les idées (0,37 → 0,47) et le système (0,60 → 0,64).
  Son test (489 commentaires) est celui de v11 sans les messages WhatsApp : la comparaison est très proche, pas
  exacte.
- Ton inversé (critique notée comme un éloge ou l'inverse) : 1,5 % avec v9, 2,0 % avec v11, 1,5 % avec v12 (6 sur 401 ; 0 sur 66
  parmi les argumentés).
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

## Dataset Hugging Face du groupe

- 2026-11-13 : export vers `rag-politique/politique-sources` (`python -m huggingface`, règles dans
  [HUGGINGFACE.md](HUGGINGFACE.md)). Le groupe a accepté un type de source de plus, `data/commentaires/nouvelle-energie/`,
  **un seul Parquet par source**, daté de sa dernière mise à jour : quand une source change, son fichier remplace
  l'ancien dans le même commit (choix de l'utilisateur : pas de fichiers presque identiques côte à côte, écart assumé
  à la règle « on ajoute, on ne réécrit pas » ; une première version par lots incrémentaux n'a jamais été envoyée),
  une source inchangée ne repart pas. Le site (Supabase) reste tel quel. **Avec le nom affiché des auteurs**, à la demande de l'utilisateur (pas d'anonymisation, contrairement
  au site) ; l'identifiant de plateforme ne part pas. Nos colonnes différant des autres fichiers, l'export tient dans
  le README du dataset une configuration `commentaires` à part et fait lister à `default` les autres dossiers. Lancé
  après chaque collecte qui ramène du neuf, et par un bouton de l'interface.
- 2026-11-13 (soir) : à la demande de l'utilisateur, les commentaires passent dans le dataset **privé**
  `rag-politique/politique-sources-privees` et **sans nom d'auteur** : la colonne `auteur` est remplacée par `auteur_id`, HMAC-SHA256 (clé locale
  `AUTEUR_CLE`, 16 caractères) de « source|identifiant de plateforme » — stable d'un export à l'autre, impossible à
  remonter même en essayant des noms (contrairement à un simple hachage). Les fichiers et la configuration
  `commentaires` ont été retirés du dataset public, dont le README a été rétabli à l'identique ; la note sur nos
  colonnes est désormais dans le README du dataset privé.
  Ensuite, avec son accord, l'historique de `main` du dataset public a été écrasé en un seul commit (44 fichiers
  identiques à l'octet près, empreintes dans `donnees/huggingface/public_avant_squash.json`), et 4 blocs de stockage
  de nos anciens fichiers ont été supprimés définitivement, puis, avec son autorisation, les 8 autres (rangés sous
  `commentaires/train/`, qui portaient les deux autres versions). Vérifié : plus aucun de nos fichiers téléchargeable,
  même par le numéro d'un ancien commit, et plus aucun bloc de stockage inutilisé dans le dataset public.

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

## Pistes non faites

- Threads, X : à tenter seulement avec un compte créé pour la collecte, pour qu'un
  bannissement ne touche pas un compte personnel.
- Annoter des lots Facebook (aucune annotation) et Bluesky (très peu) avant le prochain réentraînement :
  `tirer-actif N --source facebook`.

## Ancienne organisation (avant le 2026-11-09)

| Avant | Maintenant |
|---|---|
| `python collecter.py …`, `commun.py`, `sources/*.py` | `python -m collecte …`, `commun/` et `collecte/depot.py`, `collecte/sources/` |
| `python analyser.py …` | `python -m analyse …` (`analyse/notation.py`) |
| `python interface.py`, `interface_analyse.py`, `theme.py` | `python -m interface`, `interface/` |
| `perimetre.json`, `cles.json`, `compte.json` | `config/` |
| `essais/` (méthodes Instagram comparées le 2026-11-07) | retiré ; copie dans `donnees/sauvegardes/code_avant_reorganisation_2026-11-09.zip` |
| `python -m analyse.modele entrainer` (vecteurs seuls) | `python -m analyse.ensemble tout` |
