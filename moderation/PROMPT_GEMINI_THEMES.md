# Ranger les commentaires Facebook par thème avec Gemini (Antigravity)

But : que le site de modération propose, sous chaque commentaire qui appelle une réponse, les réponses préparées
de son thème (bouton « Réponses »). Gemini range les commentaires dans les thèmes existants ; il travaille seul
dans le projet, comme agent d'Antigravity. Toi, tu n'as qu'à :

1. Ouvrir le dossier `DavidLisnard` dans Antigravity et démarrer une **nouvelle** conversation avec Gemini
   (Gemini Flash suffit, en mode « high »).
2. Coller le prompt ci-dessous, en changeant au besoin le nombre de lots sur la première ligne.
3. Rien d'autre : chaque lot enregistré part seul dans Supabase, et le site montre les thèmes à la prochaine
   actualisation.

Où on en est : `python -m moderation themes etat` (« À ranger : N »). Ce qui est rangé ne l'est jamais deux fois ;
les commentaires les plus récents passent en premier. Après chaque collecte, il en arrive de nouveaux : relancer le
même prompt de temps en temps.

---

## Prompt à coller

```
Fais 5 lots de classement par thème des commentaires Facebook de ce projet, l'un après l'autre, tout seul, sans me
demander de confirmation entre les lots.

CONTEXTE
Le projet aide les modérateurs du groupe Facebook de soutien « Cap 2027 avec David Lisnard » (David Lisnard, maire
de Cannes, candidat à la présidentielle 2027 avec son mouvement Nouvelle Énergie). Pour chaque commentaire qui
appelle une réponse (question, critique, doute), le site propose des réponses préparées, rangées par thème. Ton
travail : dire de quel(s) thème(s) parle chaque commentaire. Le dossier de travail est la racine du projet (celui
qui contient PROCESS.md et le dossier moderation/). Les commandes se lancent depuis ce dossier, dans le terminal
(Windows, « python » est dans le PATH).

CE QUE TU AS LE DROIT DE FAIRE
- Lancer uniquement ces commandes :
    python -m moderation themes etat
    python -m moderation themes tirer 100
    python -m moderation themes noter <K> <fichier> --par gemini
- Lire les fichiers donnees/moderation/lots_themes/lot_K.txt.
- Créer tes fichiers de réponse donnees/moderation/lots_themes/gemini_K.txt.
Rien d'autre : ne modifie aucun autre fichier (ni code, ni themes.csv, ni lot_K.json, ni reponses.xlsx). Ne lance
aucune autre commande (ni « reponses », ni « publier », ni « site »). Si une commande échoue, arrête-toi et
montre-moi le message d'erreur, sans essayer de contourner. Seule exception : si « noter » refuse ton fichier
(numéro manquant, thème inconnu), corrige ton fichier gemini_K.txt et relance « noter ».

POUR CHAQUE LOT
1. Lance : python -m moderation themes tirer 100
   La commande affiche le numéro K du lot et crée donnees/moderation/lots_themes/lot_K.txt. Si elle affiche
   « Rien à tirer », arrête-toi : tout est rangé.
2. Lis lot_K.txt EN ENTIER. Il commence par la liste des THÈMES (identifiant — nom : définition), puis les
   COMMENTAIRES numérotés #1, #2… Chaque commentaire est précédé de la publication sous laquelle il est écrit et,
   pour une réponse, du commentaire auquel il répond : ce contexte sert à comprendre de quoi il parle, mais tu ne
   ranges que la ligne « COMMENTAIRE ». Si le fichier est trop long pour une seule lecture, lis-le en plusieurs
   morceaux jusqu'au dernier numéro.
3. Écris donnees/moderation/lots_themes/gemini_K.txt avec UNE LIGNE PAR COMMENTAIRE, pour tous les numéros du lot,
   dans l'ordre :
     1: T31
     2: T9 T42
     3: -
   C'est-à-dire le numéro, deux-points, puis 1 à 3 identifiants de thèmes séparés par des espaces (le thème
   principal d'abord), ou « - » si le commentaire ne parle d'aucun thème de la liste. N'écris rien d'autre dans ce
   fichier.
4. Lance : python -m moderation themes noter K donnees/moderation/lots_themes/gemini_K.txt --par gemini
   Vérifie que la commande affiche « Lot K : … commentaires rangés ». Si elle affiche « Envoi à Supabase
   impossible », ce n'est pas grave : note-le pour ton compte rendu et continue.

RÈGLES POUR CHOISIR LES THÈMES
- Range selon CE QUE DIT le commentaire, pas selon la publication. Le but : retrouver la réponse préparée qui lui
  répond. Demande-toi : « à quelle objection ou à quelle question faudrait-il répondre ? ».
- Seulement les identifiants de la liste en tête du lot (T1, T2… et éventuellement M-… : des thèmes ajoutés par les
  modérateurs). N'invente jamais de thème.
- 1 thème dans la plupart des cas ; 2 ou 3 seulement si le commentaire aborde vraiment plusieurs sujets distincts.
- « - » quand le commentaire ne porte sur aucun thème : simple réaction (« n'importe quoi », « bof »), message
  hors sujet, dispute entre commentateurs sans argument, commentaire trop vague pour savoir de quoi il parle.
- Repères fréquents :
  · « Macron bis », « macroniste », « recyclé de la macronie », « comme Macron en 2017 » → T31 ;
  · RN, Le Pen, Bardella, « votez RN », alliance avec le RN ou l'UDR, Ciotti → T33 ;
  · primaire, Attal, Philippe, union des droites, Retailleau, division de la droite → T43 ;
  · LR, « droite molle », Sarkozy, Pécresse, « vieux de la vieille » → T32 ;
  · Knafo, Zemmour, Reconquête → T34 ;
  · « politicien comme les autres », « système », carrière → T35 ;
  · pensions, retraités, 2 200 € → T9 ; capitalisation, bourse → T8 ; âge de départ → T49 ;
  · économies, dépense publique, austérité → T1 ; « où trouve-t-il l'argent », chiffrage → T2 ;
  · impôts, « candidat des riches » → T6 ; Europe, UE, Frexit, CEDH → T10 ; immigration → T11 ;
  · Cannes, son bilan de maire → T37 ; « une ville n'est pas un pays » → T38 ;
  · « il ne pourra rien faire », majorité, promesses → T42 ; chances de gagner, sondages, vote utile → T44 ;
  · Bolloré, CNews, milliardaires, qui le finance → T36 ; médias qui l'ignorent ou le caricaturent → T55.
  Pour tout le reste, lis les définitions de la liste.
- Une question sincère se range comme une critique : par son sujet (« Et les retraités ? » → T9).
- Un message de soutien sans objection (« Bravo », « Allez David ! ») → « - », sauf s'il défend une idée précise
  contre une critique (« Ce n'est pas un Macron bis, il a demandé sa démission » → T31).

À LA FIN
Donne-moi un compte rendu court : les lots faits (numéro, nombre de commentaires rangés, nombre de « - »), les
thèmes les plus fréquents, et les erreurs éventuelles.
```
