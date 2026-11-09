# DavidLisnard : plan de collecte des commentaires

> Journal de conception, tenu au fil du projet. Les chemins et commandes cités sont ceux de l'époque : depuis la réorganisation du 2026-11-09, voir [README.md](../README.md), tableau « Ancienne organisation ».

Mis à jour le 2026-11-07.

## État au 2026-11-07 (exécution du plan)

| Source | État |
|---|---|
| YouTube | Fait. 22 chaînes, 1 183 vidéos, 58 608 commentaires sur 58 610 annoncés, en 9 min (environ 4 500 unités de quota sur 10 000) |
| WhatsApp | Marche (validé en réel le 2026-11-07 au soir). La discussion s'appelle à l'écran « NE 34 - Échanges entre adhérents ». Auteur (nom et numéro), date à la minute, texte, réponses rattachées au message cité. Deux limites : l'historique n'arrive sur le PC qu'une fois la synchronisation du téléphone terminée (« La synchronisation est en pause » au premier lancement, seuls les messages du jour étaient lisibles), et la discussion a les **messages éphémères** activés : un message non collecté avant son effacement est perdu, donc il faut lancer la collecte régulièrement |
| Instagram | Marche, sans blocage. 3 793 commentaires sur 40 posts, en environ 18 min par lancement de 20 posts. 1 301 posts depuis le 2025-01-01 : il en restait 1 267 à lire le 2026-11-07, à raison de 50 par lancement (réglable dans perimetre.json). Une fois lu, un post n'est relu pour ses nouveaux commentaires que s'il a moins de 21 jours (`relire_si_moins_de_jours`) : on ne revient pas sur les vieux posts. Instagram n'affiche qu'une partie des commentaires qu'il annonce (souvent 40 à 90 %) |
| TikTok | Faisable techniquement, mais bloqué côté Claude Code. Avec un Chrome normal piloté par le port de débogage, la liste des vidéos et l'API des commentaires répondent (essai du 2026-11-07 : 44 vidéos, 16 commentaires sur une vidéo). Tu as donné ton accord, mais le classifieur de sécurité de Claude Code refuse ces commandes (« Bot Check Circumvention »). Le module ne sera écrit que si tu l'autorises dans les réglages de Claude Code |
| Reddit | Écarté. Le réseau est bloqué par Reddit, même dans un navigateur, et l'API exige un compte avec une application déclarée |
| Facebook, X | Pas tentés : mêmes protections que TikTok (Facebook), API payante (X) |

Interface graphique (2026-11-07) : `Interface.bat` ou `python interface.py`, avec un bouton Lancer et un bouton Arrêter par source, l'ajout et le retrait des comptes suivis, les réglages et la collecte automatique quotidienne.

Le mode d'emploi est dans [README.md](README.md).

## 1. Objectif

Rassembler dans des fichiers Excel/CSV les commentaires publiés autour de David Lisnard, une source par dossier.
Tout doit tourner seul : tu lances une commande, et le script ouvre ce qu'il faut, récupère ce qui est nouveau depuis
la dernière fois, met les fichiers à jour et écrit un bilan. Personne (ni toi ni Claude) n'a de travail à faire à la main
entre deux lancements.

```
python collecter.py                  toutes les sources, l'une après l'autre
python collecter.py youtube whatsapp seulement celles-là
```

Un raccourci `Collecter.bat` lance la même commande d'un double-clic. Une source qui échoue n'arrête pas les autres : son
erreur est écrite dans le bilan et la suivante démarre.

## 2. Règles communes

### Périmètre constant

`perimetre.json` fixe pour chaque source :
- les comptes, chaînes ou discussions suivis ;
- la date de début ;
- la règle de choix des publications : « toutes », ou « le titre ou la description contient Lisnard ».

On ne le change que volontairement, et le bilan indique la version du périmètre utilisée.

### Ce qui est récupéré à chaque lancement (incrémental)

- **Nouvelles publications** (vidéos, posts) jamais vues : tous leurs commentaires et réponses.
- **Publications déjà vues** : on les relit seulement si leur nombre de commentaires annoncé a augmenté depuis la dernière
  fois, ou si elles ont moins de 30 jours.
- **WhatsApp** : seulement les messages postés après le dernier déjà enregistré.
- On ne supprime jamais rien. La fusion se fait par identifiant, donc sans doublon. Un commentaire supprimé entre-temps
  sur la plateforme reste dans nos fichiers.
- L'état de chaque source (publications vues, nombre de commentaires, dernier message lu) est dans
  `donnees/<source>/etat.json`. Si une collecte est coupée, la suivante reprend où elle s'était arrêtée.

### Une ligne par commentaire, mêmes colonnes partout

| Colonne | Contenu |
|---|---|
| `source` | youtube, instagram, whatsapp… |
| `compte_source` | chaîne, compte ou discussion où le commentaire a été pris |
| `publication_titre`, `publication_lien`, `publication_date` | la vidéo ou le post commenté (vide pour WhatsApp) |
| `commentaire_id` | identifiant de la plateforme (sinon empreinte date + auteur + texte) |
| `type` | `principal` ou `réponse` |
| `parent_id` | commentaire auquel il répond (vide si principal) |
| `auteur` | pseudo ou nom affiché |
| `date` | heure de Paris |
| `date_exacte` | oui / non (non = déduite de « il y a 3 mois ») |
| `texte` | le commentaire en entier |
| `likes` | si disponible |
| `collecte_le` | date de la première collecte de ce commentaire |

### Fichiers

```
donnees/
  youtube/    <chaîne>.csv … , youtube_tout.xlsx, etat.json, brut/
  instagram/  <compte>.csv … , instagram_tout.xlsx, etat.json, brut/
  whatsapp/   echange_entre_adherents.csv, whatsapp_tout.xlsx, etat.json
  …           une source = un dossier, même organisation
  bilan.md    dernier lancement : par source, nouvelles publications, nouveaux commentaires, durée, erreurs,
              commentaires annoncés / récupérés
```

- Les CSV sont en `;` et en UTF-8 avec BOM : ils s'ouvrent directement dans Excel.
- Le fichier `_tout.xlsx` est recréé à chaque lancement à partir des CSV.
- Les textes qui commencent par `=`, `+`, `-` ou `@` sont neutralisés pour qu'Excel ne les prenne pas pour des formules.
- `brut/` garde les réponses brutes des plateformes : on peut tout reparser sans rien retélécharger.

## 3. YouTube (faisable, priorité 1)

### Méthode

- **API officielle YouTube Data v3**, si une clé est présente dans `cles.json` :
  - dates exactes, lien réponse → parent ;
  - nombre de commentaires de 50 vidéos pour une seule unité de quota, ce qui permet de ne relire que les vidéos qui ont
    bougé ;
  - quota gratuit de 10 000 unités par jour, très au-delà du besoin.
- **Sans clé, yt-dlp** (déjà installé, essayé ici avec succès) prend le relais tout seul :
  - mêmes données ;
  - mais la date vient de « il y a 3 mois », d'où `date_exacte = non` ;
  - plus on lance souvent, plus les nouveaux commentaires sont datés finement.
- La clé se crée une fois, en 5 minutes, sur console.cloud.google.com, sans carte bancaire. La marche à suivre sera dans
  le README.
- Titres demandés en français : sans cette précaution, la recherche renvoie des titres traduits automatiquement en
  anglais.

### Périmètre

Les chaînes viennent d'une recherche réelle « David Lisnard » du 2026-11-07.

1. **Toutes les vidéos, sans limite de date** :
   - David Lisnard (`UC2XZY-bjIEmyLZ9MPJQytZg`) ;
   - Nouvelle Énergie avec David Lisnard.
2. **Médias, vidéos qui parlent de lui** (recherche « Lisnard » dans chaque chaîne) : CNEWS, BFMTV, RMC, Sud Radio,
   Public Sénat, Europe 1, M6 Info, LCI, franceinfo, LCP.
3. **Commentateurs politiques**, même règle : Le point de rupture, DME En Direct, CharbOfficiel, Antoine Gehant,
   Sardoche Clips, « Et si l'économie sauvait l'écologie ? ».

### Limites

- Les commentaires supprimés ou retenus par la chaîne sont invisibles pour tout le monde.
- Les vidéos aux commentaires fermés sont notées dans le bilan.

## 4. WhatsApp : « Échange entre adhérents » (faisable, priorité 1)

Il s'agit de la discussion « Échange entre adhérents » de la communauté Nouvelle Énergie 34, et d'elle seule.

### Ce que fait le script à chaque lancement

1. Il ouvre l'application WhatsApp du PC, ou la redémarre si elle est déjà ouverte, et la met en plein écran.
2. Il ouvre la communauté Nouvelle Énergie 34, puis la discussion « Échange entre adhérents ».
3. Il remonte la discussion jusqu'au dernier message déjà enregistré. La première fois, il remonte jusqu'au début de
   l'historique disponible. S'il voit le bouton « obtenir les messages plus anciens depuis le téléphone », il clique
   dessus.
4. Pour chaque message, il lit :
   - l'auteur ;
   - la date et l'heure ;
   - le texte ;
   - le bloc « en réponse à » s'il y en a un : le message devient alors une `réponse` rattachée au message d'origine.
5. Il ignore les messages système (« a ajouté », « a quitté »), les médias sans texte et les messages supprimés.
6. Il remet WhatsApp dans son état normal et le laisse ouvert.

C'est mieux que l'export manuel : on sait qui répond à qui, il n'y a pas de limite à 40 000 messages, et on ne prend
que la suite.

### Comment l'application est lue

L'application installée (5319275A.WhatsAppDesktop 2.2642, `WhatsApp.Root.exe`) affiche les discussions dans une page
web intégrée (WebView2). Le script lit donc la page elle-même, sans aucune capture d'écran.

- **Méthode principale.** Le script lance WhatsApp avec un port de débogage local, grâce au réglage WebView2
  `AdditionalBrowserArguments` que Windows lit dans `HKCU\Software\Policies\Microsoft\Edge\WebView2`. Il s'y connecte
  avec Playwright et lit la page.
  - Le port n'écoute que sur la machine elle-même.
  - Le réglage est retiré et WhatsApp redémarré normalement en fin de collecte : ce port, tant qu'il est ouvert, laisse
    n'importe quel programme du PC lire WhatsApp.
- **Secours** : l'arbre d'accessibilité de Windows (pywinauto, à installer). Même lecture, plus lente, sans port.
- **Second secours** : si l'application propose « Exporter la discussion », le script clique dessus lui-même, mais on
  perd alors les réponses.

### À vérifier au premier essai

- Jusqu'où remonte l'historique synchronisé sur le PC.
- Le nom exact de la communauté et de la discussion à l'écran.
- La forme de la date pour les vieux messages.

## 5. Instagram (à tenter, avec un critère d'abandon)

### Méthode

- La méthode « navigateur » (M4), qui marche déjà en partie : un Chrome visible connecté avec le compte dédié
  fanlisnard.
- On lit ce que la page reçoit elle-même, sans requêtes fabriquées.
- Il reste à faire défiler toute la liste des commentaires et à ouvrir les « Voir les réponses ».

### Périmètre

- Tous les posts de @davidlisnard depuis le 2025-01-01 (modifiable dans `perimetre.json`).
- Puis le compte de Nouvelle Énergie, si l'essai est concluant.

### Critère d'abandon (ta règle)

Essai sur 10 posts. Instagram est abandonné, et le bilan dit pourquoi, si l'essai :
- dépasse 30 minutes ;
- ou déclenche un blocage (`feedback_required`, page figée sur le logo, demande de vérification).

Sinon, collecte par lots raisonnables à chaque lancement (20 posts au plus), avec reprise automatique.

### Avant l'essai

Le compte a été freiné le 2026-11-07 : il faut le laisser se reposer quelques jours et l'utiliser un peu sur le
téléphone.

## 6. Autres sources

| Source | Statut | Pourquoi / comment |
|---|---|---|
| Reddit | Faisable | Fils de r/france et r/francepolitique qui citent Lisnard. Peu de volume, mais d'autres publics |
| Telegram | Si elle existe | Uniquement si Nouvelle Énergie y a un canal public. Lecture de la page publique t.me/s/… |
| TikTok | À tenter | Même méthode navigateur et même critère d'abandon qu'Instagram |
| Facebook (page David Lisnard) | Un essai, puis abandon probable | Connexion obligatoire et protection anti-robots très forte. Un seul essai avec le critère d'Instagram |
| X / Twitter | Abandonné | API payante, collecte sans API presque fermée depuis 2023 |
| Commentaires de presse | Abandonné | Réservés aux abonnés, peu de contenu |

## 7. Organisation du code

```
DavidLisnard/
  PLAN.md, README.md
  perimetre.json      comptes, chaînes, discussion, dates, règles
  cles.json           clé YouTube (facultative), hors partage
  compte.json         compte Instagram dédié (déjà là)
  collecter.py        point d'entrée unique
  Collecter.bat       double-clic
  commun.py           format commun, fusion sans doublon, CSV + Excel, bilan
  sources/
    youtube.py        API ou yt-dlp, selon la présence de la clé
    whatsapp.py       ouverture de l'application, navigation, lecture, remise en état
    instagram.py      reprend m4_navigateur.py
    reddit.py, tiktok.py…
  essais/             anciennes méthodes Instagram m1 à m3 et tester.py, gardées pour mémoire
```

## 8. Ordre de réalisation

| Étape | Contenu | Vérification |
|---|---|---|
| 1 | Format commun, fusion, bilan, `collecter.py` | Une relance immédiate n'ajoute aucune ligne |
| 2 | YouTube : 3 vidéos, puis la chaîne Lisnard, puis médias et commentateurs | Nombre annoncé = nombre récupéré, vidéo par vidéo |
| 3 | WhatsApp : ouverture, navigation, lecture des 50 derniers messages, puis tout l'historique | Lecture des 50 derniers comparée à ce que tu vois ; une relance ne reprend que les nouveaux |
| 4 | Reddit, et Telegram s'il existe | Idem |
| 5 | Instagram : essai sur 10 posts, application du critère d'abandon | Temps et blocages écrits dans le bilan |
| 6 | TikTok, puis l'essai Facebook, même critère | Idem |

À la fin de chaque étape, la source tourne seule depuis `collecter.py`. Le README dit comment la lancer et ce qu'il
faut faire une seule fois : créer la clé YouTube, vérifier que WhatsApp est connecté sur le PC.

## 9. Précautions

- Ces fichiers relient des personnes nommées à des opinions politiques, ce qui en fait des données sensibles au sens du
  RGPD. C'est particulièrement vrai pour la discussion WhatsApp, qui est privée et où les non-contacts apparaissent par
  leur numéro.
- Tout reste en local. Une colonne `auteur_pseudo` (code stable à la place du nom) peut être ajoutée pour toute analyse
  partagée.
- Rythme humain sur Instagram, TikTok et Facebook : pauses, petits lots, arrêt net au premier blocage, pas de relance
  en boucle.
- WhatsApp : le script ne fait que lire. Il n'envoie rien et ne marque rien comme lu ailleurs que dans cette discussion.

## 10. Réglages par défaut, modifiables dans perimetre.json

- YouTube : pas de limite de date.
- Instagram et TikTok : depuis le 2025-01-01.
- WhatsApp : tout l'historique disponible, puis la suite.
- Relecture des publications de moins de 30 jours à chaque lancement.
