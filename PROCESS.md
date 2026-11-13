# Mettre à jour le projet : la marche à suivre

Quand l'utilisateur demande de « mettre à jour le projet », Claude suit ces étapes **dans cet ordre**, depuis le
dossier `DavidLisnard/`. Chaque étape dit quoi lancer, comment savoir si elle est utile, et ce qui ne doit **jamais**
être refait (ce qui est déjà lu, noté ou rangé ne l'est jamais une deuxième fois).

Le détail de chaque commande est dans [README.md](README.md) ; les règles de notation dans
[docs/GRILLE.md](docs/GRILLE.md).

## Vue d'ensemble

| # | Étape | Quand | Ne traite que |
|---|---|---|---|
| 0 | Vérifier que rien ne tourne | toujours | — |
| 1 | Collecter, sauvegarder, noter, publier | toujours | le nouveau sur chaque source |
| 2 | Contrôler le bilan | toujours | — |
| 3 | Annoter | si un besoin est constaté (critères plus bas) | des lots tirés pour ce besoin |
| 4 | Réentraîner, renoter | si ≥ 1 000 annotations nouvelles, ou sur demande | — |
| 5 | Lire les nouveaux commentaires pour les thèmes | si `à lire` > 0 | les commentaires jamais lus |
| 6 | Fusionner les thèmes proches | après une lecture | — |
| 7 | Catégoriser les commentaires de la sélection | si `etat` en compte « sans catégorie » | ceux sans catégorie |
| 8 | Réécrire les synthèses qui ont changé | si `a-resumer` en liste | les synthèses signalées |
| 9 | Document de fonctionnement | toujours | — |
| 10 | Sauvegarde, publication | toujours | ce qui a changé |
| 11 | Compte rendu à l'utilisateur | toujours | — |
| M | Modération Facebook : annoter, réentraîner (le classement, lui, suit seul la collecte) | **seulement si l'utilisateur le demande** | le nouveau |

## 0. Vérifier que rien ne tourne

- Pas de fichier `donnees/<tâche>/EN_COURS` (collecte, analyse, réentraînement) : sinon attendre la fin.
- **Un seul calcul lourd à la fois** (réentraînement, renotation complète) : deux en parallèle vont jusqu'à 9 fois
  plus lentement.

## 1. Collecter (tout s'enchaîne seul)

```
python -m collecte
```

Une seule commande fait, dans l'ordre : la collecte du nouveau sur YouTube, Bluesky, Instagram, Facebook et X (incrémentale,
`etat.json` par source), la sauvegarde `donnees/sauvegardes/donnees.zip`, la mise à jour de `corpus.csv` (doublons,
« j'aime ») et des vecteurs, la notation des **seuls nouveaux** commentaires par le modèle en service, puis
`python -m web publier`, et enfin l'export vers le dataset Hugging Face du groupe (le fichier des sources qui ont changé
remplace l'ancien) (`python -m huggingface`, [docs/HUGGINGFACE.md](docs/HUGGINGFACE.md)), et, si Facebook a ramené du
neuf, le classement des nouveaux commentaires Facebook pour la modération (partie M ; quelques secondes, envoyé dans
la table privée `moderation` de Supabase). Facebook prend le plus de temps (jusqu'à 120 min par lancement, tant que l'arriéré
depuis le 2026-07-31 n'est pas fini), puis Instagram (50 posts) : lancer en arrière-plan avec `python -u` et un
journal. X peut aussi prendre jusqu'à 120 min tant que son arriéré n'est pas fini. Si `donnees/facebook/EN_COURS`
(ou `donnees/x/EN_COURS`) existe, une collecte de cette source tourne déjà : attendre (étape 0).

Si la publication est refusée par le classifieur de Claude Code (« Production Deploy »), ne pas la contourner : le
dire à l'utilisateur, qui la lance lui-même (étape 10).

## 2. Contrôler le bilan

- Lire `donnees/bilan.md` : nouveaux commentaires par source, erreurs.
- Modération (si Facebook a ramené du neuf) : le journal finit par « ### Modération : N commentaires classés,
  X à modérer, Y questions ». « Modération impossible » ou « Envoi à Supabase impossible » dans
  `donnees/moderation/journal.log` : relancer `python -m moderation classer` (ou `publier`), sans rien d'autre.
- Source « abandonnée » (Instagram freiné, 10 posts en plus de 30 min) : ne pas insister le jour même ;
  `python -m collecte --reessayer instagram` à la prochaine mise à jour.
- Quota YouTube atteint : rien à faire, la suite reprend au lancement suivant.
- Session Instagram expirée : `python -m collecte.connexion_instagram` (demande l'utilisateur).
- Facebook :
  - « partiel (temps ou quota) » : normal tant que l'arriéré n'est pas fini, la suite reprend au lancement suivant ;
  - « partiel (freinage) » ou « en repos » : Facebook a freiné, la source se repose 3 h ; ne pas relancer avant ;
  - « impossible » : Facebook demande une vérification ; `python -m collecte.connexion_facebook` (Chrome visible,
    l'utilisateur peut devoir valider), puis `--verifier`. Une simple session expirée se refait seule.
- X : mêmes états que Facebook. « impossible » : session refusée même après une nouvelle connexion ;
  `python -m collecte.connexion_x --verifier`, puis `python -m collecte.connexion_x` (Chrome visible). Si X répond
  « temporairement limité votre connexion », ne pas réessayer le jour même : demander à l'utilisateur les cookies
  `auth_token` et `ct0` du compte (navigateur connecté, F12 → Application → Cookies) et les mettre dans
  `sessions/x_cookies.json`.

## 3. Annoter, si besoin

```
python -m analyse.annotation etat
```

**Quand c'est utile** (sinon passer à l'étape 5) :
- une source, une chaîne ou un compte nouveau a beaucoup de commentaires mais presque aucun annoté : `tirer-actif N
  --source facebook` (ou `bluesky`, `x`) tire sur cette source seule, dont un quart parmi les commentaires les plus
  éloignés de tout ce qui est annoté ; `tirer-hasard N [jeu] --source facebook` donne un lot au hasard. **Facebook
  et X n'ont encore aucune annotation** (Bluesky très peu) : en annoter quelques lots avant le prochain réentraînement ;
- le modèle hésite beaucoup ou se contredit : `tirer-actif N`, `tirer-suspects` ;
- l'utilisateur le demande (par exemple `tirer-longs N` pour les commentaires argumentés).

**Comment**, lot par lot (100 commentaires) : `voir N` → écrire les notes dans un fichier du scratchpad au format
`n L|A ton forme systeme idees pertinence # remarque` → `noter N fichier`. Pour une cible A, les quatre premières
notes valent 10. Réenregistrer un lot remplace ses anciennes notes.

**Contre la dérive** (déjà arrivée deux fois, lots 18-142 et 210-222) : après chaque série de lots, comparer la
pertinence et la tonalité moyennes à celles des lots 1 à 17 pour des commentaires semblables ; un « Bravo ! »
vaut 8, pas 0 (docs/GRILLE.md, « Garde-fou contre la dérive »). Recaler avant d'enregistrer.

## 4. Réentraîner et renoter, si besoin

**Quand** : au moins 1 000 annotations de plus que celles du modèle en service (champ `annotations` de
`modeles/vN/infos.json`, à comparer au total de `annotation etat`), ou sur demande.

```
python -u -m analyse.ensemble tout > journal.log 2>&1      environ 7 h sur le processeur, en arrière-plan
python -m analyse                                         renote tout le corpus avec la nouvelle version
python -m analyse.ton_inverse                             contrôle : part de « ton inversé » sur le test
```

- Rien d'autre de lourd pendant ce temps. Les annotations ajoutées pendant l'entraînement ne servent qu'au suivant.
- `python -m analyse` voit seul que les notes viennent d'une ancienne version et renote tout (2 à 5 h, à 10-30 commentaires par seconde).
- Comparer les mesures de `donnees/analyse/RAPPORT_MODELE.md` à celles de la version précédente et le dire.
- Garder les deux dernières versions `modeles/vN/` et leurs réseaux `affineN` (champ `reseau` de `infos.json`) ;
  proposer de supprimer les plus anciennes (environ 570 Mo chacune).

## 5. Lire les nouveaux commentaires pour les thèmes

```
python -m critiques etat
```

`etat` donne « N à lire ». S'il vaut 0, passer à l'étape 7. Sinon, jusqu'à « Rien de nouveau à lire » :

```
python -m critiques tirer        prépare le lot suivant (100 commentaires jamais lus)
python -m critiques voir K       le lot, précédé de la liste des thèmes
python -m critiques noter K fichier
```

- Une ligne par thème abordé : `n | T5 | E | phrase` pour un éloge, `n | T5 | C3 | phrase` ou `n | T5 | D2 | phrase`
  pour une critique ou un doute, `n | -` si le commentaire n'aborde aucun thème. Un thème absent se déclare par une
  ligne `+ Nom du thème | famille | définition`, puis s'utilise par son nom : `n | Nom du thème | C3 | phrase`.
- **La catégorie se donne à la lecture, une seule fois** : `noter` refuse un C ou un D sans chiffre de 1 à 5
  (1 opposition de principe, 2 demande de précision, 3 objection sur une mesure, 4 doute sur la faisabilité,
  5 suggestion), et un E avec. Les commentaires déjà catégorisés ne sont jamais repris.
- Ce qui est lu entre dans `lus.csv` et n'est jamais relu, même si sa note change ensuite. Après un réentraînement,
  la sélection (cible L, pertinence ≥ 12, 20 mots ou plus) peut s'élargir : seuls les nouveaux entrants sont à lire.
- Les critiques et doutes restés sans catégorie se traitent à l'étape 7.
- Contrôler la dérive comme à l'étape 3 : relire de temps en temps les lots précédents pour garder les mêmes thèmes
  et les mêmes catégories.

## 6. Fusionner les thèmes proches

```
python -m critiques proches            paires de thèmes qui pourraient fusionner
python -m critiques fusionner fichier  seulement si deux thèmes disent vraiment la même chose
```

Une fusion signale d'elle-même les synthèses du thème gardé comme à réécrire.

## 7. Catégoriser les commentaires de la sélection restés sans catégorie

La sélection est celle de l'étape 5 (les commentaires lus et rangés dans les thèmes). Chacune de leurs critiques et
chacun de leurs doutes doit avoir une des 5 catégories : 1 opposition de principe, 2 demande de précision,
3 objection sur une mesure, 4 doute sur la faisabilité, 5 suggestion. Les éloges n'en ont pas.

```
python -m critiques etat               ligne « Critiques et doutes par catégorie : … ; N sans catégorie »
python -m critiques trier [N]          le lot suivant de critiques et doutes sans catégorie
python -m critiques ranger K fichier   lignes « numéro catégorie », par exemple « 12 3 »
```

- Seuls ceux qui n'ont **pas encore** de catégorie sont traités : une catégorie déjà donnée n'est jamais reprise.
- Normalement il n'en reste aucun, puisque l'étape 5 donne la catégorie à la lecture. S'il en reste (rangés avant le
  2026-11-12, ou après une fusion ou un import), **dire d'abord à l'utilisateur combien il y en a** et ne les
  catégoriser qu'avec son accord.
- Même contrôle de dérive qu'à l'étape 5 : garder les mêmes critères que les lots précédents (`donnees/critiques/tris/`).

## 8. Réécrire les synthèses qui ont changé, et elles seules

```
python -m critiques a-resumer          les synthèses à écrire ou réécrire, avec les phrases arrivées depuis
python -m critiques syntheses fichier  lignes « T5 C | texte »
```

`a-resumer` signale un couple thème-sens sans synthèse dès 3 commentaires, et une synthèse qui a reçu depuis au
moins 5 commentaires et 25 % de plus. Les autres restent telles quelles. Lire la synthèse actuelle et les nouvelles
phrases, puis réécrire en gardant ce qui reste vrai.

## 9. Document de fonctionnement

```
python -m docs
```

Puis relire `docs/FONCTIONNEMENT.pdf` : tous les chiffres, carte « Ton inversé » comprise, se mettent à jour seuls.
Si la mise à jour a changé une structure ou une méthode (source, stockage, grille, modèle, publication, commande),
modifier d'abord `docs/FONCTIONNEMENT.html`, `README.md` et ce fichier (règle de `CLAUDE.md`).

## 10. Sauvegarde et publication

```
python -m commun.sauvegarde            la sauvegarde de l'étape 1 précède les annotations et les thèmes du jour
python -m web publier                  envoie ce qui a changé (notes, thèmes, synthèses)
python -m web deployer                 seulement si web/site/ a changé
python -m huggingface                  si des notes, des thèmes ou des commentaires ont changé depuis la collecte
                                       (annotation, renotation) : remplace le fichier des seules sources changées
```

Sur Hugging Face, chaque source n'a qu'un fichier : quand elle change, le nouveau remplace l'ancien, une source
inchangée ne repart pas. `python -m huggingface etat` montre ce qui est en attente.

Si le classifieur refuse `publier` ou `deployer`, ne pas contourner : demander à l'utilisateur de les lancer.

## 11. Compte rendu à l'utilisateur

Dire en quelques lignes : commentaires nouveaux par source, annotations ajoutées, version du modèle et ses mesures
si elle a changé, commentaires lus pour les thèmes et leurs catégories, nombre de critiques et doutes restés sans catégorie,
synthèses réécrites, commentaires Facebook classés pour la modération (à modérer, questions), ce qui est en ligne et
ce qui reste à lancer de son côté.

## M. Modération des commentaires Facebook (facultatif, seulement sur demande)

À part du reste du projet (paquet `moderation/`, onglet « Modération » de l'interface, détail dans
`moderation/__init__.py`). Demandée par le gestionnaire d'un groupe Facebook de soutien : chaque commentaire Facebook
est classé « insultant » (à modérer), « question » (appelle une réponse) ou « autre ». Seul le **classement** des
nouveaux commentaires se fait seul, à la fin de `python -m collecte` quand Facebook a ramené du neuf (étape 1).
**L'annotation et le réentraînement ne se font pas pendant une mise à jour ordinaire** : seulement quand
l'utilisateur le demande (« annote pour la modération », « réentraîne la modération »…).

```
python -m moderation etat                       où on en est (classés, annotés, mesures du modèle)
python -m moderation classer                    classe les commentaires Facebook pas encore classés (0,1 s chacun)
python -m moderation tirer 250 questions        prépare un lot à annoter (modes : hasard, questions, insultes, doutes)
python -m moderation noter K lecture.txt        enregistre la lecture du lot K
python -m moderation entrainer                  réentraîne (≈ 30 min) puis reclasse tout (≈ 30 min)
python -m moderation motdepasse                 change le mot de passe du site de modération (par l'utilisateur)
python -m moderation site deployer              remet en ligne le site de modération après une modification des pages
```

Le site de modération lit la base en direct : rien à faire à la mise à jour, la publication suffit.

- **Classer** : automatique à la fin de chaque collecte qui ramène du neuf sur Facebook ; à la main par le bouton
  « Classer les nouveaux » ou la commande (par exemple si la collecte a été lancée source par source sans Facebook,
  ou si l'envoi a échoué). Seuls les commentaires sans catégorie de la version en service sont traités ; ceux dont
  le texte est vide sont écartés, ceux dont la publication n'a pas de texte connu sont gardés.
- **Annoter** : Claude lit le lot (`donnees/moderation/lots/lot_K.txt`) et écrit un fichier avec une ligne
  `I: numéros` (insultants) et une ligne `Q: numéros` (questions) ; tout le reste du lot est « autre ». Les règles
  sont celles de `moderation/__init__.py` : une critique dure sans injure n'est pas insultante ; une question
  rhétorique n'est pas une question ; les commentaires positifs sont « autre ». Le mode `questions` est le plus
  utile tant que le modèle trouve mal les questions. Un commentaire annoté ne l'est jamais deux fois ; plusieurs
  lots peuvent être tirés d'avance, ils ne se chevauchent pas (un lot tiré réserve ses commentaires). Le jeu de test
  (573 commentaires, `jeu=test`) ne change pas, pour que les versions restent comparables (`--test` seulement si
  l'utilisateur veut l'agrandir).
- **Réentraîner** : sur demande, après des annotations (bouton « Réentraîner le modèle » ou commande). Jamais en
  même temps qu'une analyse ou un autre calcul lourd (étape 0). Ajouter une ligne à `docs/HISTORIQUE.md` avec la
  version (m2, m3…) et ses mesures, puis `python -m docs`.
- **Supabase** : chaque `classer`, `noter` et `entrainer` envoie ensuite ce qui a changé dans la table privée
  `moderation` (probabilités, version, annotation, et le commentaire : texte, auteur, date, publication, sauf s'il
  est déjà dans `commentaires` ; catégorie retenue, auteur et lien direct se lisent dans la vue
  `moderation_complete`). Elle
  n'a aucune règle de lecture publique : le site ne la voit pas. Si l'envoi échoue (réseau, base en pause), le
  journal le dit : relancer `python -m moderation publier`. Rien ne va sur le site ni sur Hugging Face, et
  l'onglet, qui montre les auteurs et les liens, reste local.
