# Annoter la modération avec Gemini (Antigravity)

Gemini travaille seul dans le projet, comme agent d'Antigravity : il choisit le mode de chaque lot, tire les lots,
les lit, enregistre ses lectures. Toi, tu n'as qu'à :

1. Ouvrir le dossier `DavidLisnard` dans Antigravity et démarrer une **nouvelle** conversation avec Gemini.
2. Coller le prompt ci-dessous, en changeant au besoin le nombre de lots sur la première ligne.
3. À la fin, demander à Claude de relire les lots de Gemini. Claude relit chaque lot en entier, corrige avec
   `python -m moderation relire K`, puis donne le taux d'accord avec Gemini.

Le modèle n'est pas réentraîné sur des lots de Gemini qui n'ont pas été relus.

---

## Prompt à coller

```
Fais 4 lots d'annotation pour la modération Facebook de ce projet, l'un après l'autre, tout seul, sans me demander
de confirmation entre les lots.

CONTEXTE
Le projet modère le groupe Facebook de soutien « Soutien David Lisnard 2027 » (David Lisnard, maire de Cannes,
candidat à la présidentielle 2027 avec son mouvement Nouvelle Énergie). Un modèle classe chaque commentaire ;
tes lectures servent à l'entraîner. Le dossier de travail est la racine du projet (celui qui contient
PROCESS.md et le dossier moderation/). Les commandes se lancent depuis ce dossier, dans le terminal (Windows,
« python » est dans le PATH).

CE QUE TU AS LE DROIT DE FAIRE
- Lancer uniquement ces commandes :
    python -m moderation etat
    python -m moderation tirer 250 <mode>
    python -m moderation noter <K> <fichier> --par gemini
- Lire les fichiers donnees/moderation/lots/lot_K.txt.
- Créer tes fichiers de réponse donnees/moderation/lots/gemini_K.txt.
Rien d'autre : ne modifie aucun autre fichier (ni code, ni annotations.csv, ni lot_K.json). Ne lance jamais
« entrainer », « relire », « classer », « publier », « site », « motdepasse », ni l'option « --test ». Si une
commande échoue, arrête-toi et montre-moi le message d'erreur, sans essayer de contourner.

POUR CHAQUE LOT
1. Choisis le mode (voir « Choix du mode ») et lance : python -m moderation tirer 250 <mode>
   La commande affiche le numéro K du lot et crée donnees/moderation/lots/lot_K.txt.
2. Lis lot_K.txt EN ENTIER, du #1 au dernier numéro (environ 250), sans en sauter. Si le fichier est trop long
   pour une seule lecture, lis-le en plusieurs morceaux jusqu'à la fin.
3. Écris donnees/moderation/lots/gemini_K.txt avec exactement ces trois lignes :
     L: numéros séparés par des virgules
     I: numéros séparés par des virgules
     Q: numéros séparés par des virgules
   Les numéros sont ceux des « #N » du lot. Les numéros absents sont « autre ». Une ligne vide s'écrit
   « L: aucun ». Un numéro ne figure qu'une fois.
4. Lance : python -m moderation noter K donnees/moderation/lots/gemini_K.txt --par gemini
   Vérifie que la commande affiche « Lot K : 250 annotations enregistrées ». Si elle affiche « Envoi à Supabase
   impossible », ce n'est pas grave : note-le pour ton compte rendu et continue.

CHOIX DU MODE
Lance d'abord « python -m moderation etat ». Puis, sur l'ensemble des lots :
- un lot sur quatre en mode « hasard » (pour que les annotations restent représentatives) ;
- sinon surtout « questions » : c'est le point faible du modèle (il trouve mal les questions) ;
- un lot « insultes » de temps en temps, pour apprendre à distinguer les insultes qui visent Lisnard ;
- « doutes » quand les autres modes n'ont plus rien à tirer (la commande affiche alors « Rien à tirer »).
Avec 4 lots : questions, insultes, questions, hasard.

COMMENT LIRE UN LOT
Pour chaque commentaire, tu vois la publication sous laquelle il est écrit, parfois le commentaire auquel il
répond (« En réponse à »), puis le COMMENTAIRE lui-même. Tu classes UNIQUEMENT la ligne COMMENTAIRE ; la
publication et « En réponse à » ne servent qu'à comprendre de qui ou de quoi il parle.

Chaque commentaire reçoit UNE seule catégorie :

L = INSULTANT, et l'insulte vise David Lisnard, Nouvelle Énergie, leurs représentants ou leurs soutiens en tant
    que tels (« Lisnard macron la même merde », « Nouvelle merde », « encore une merde pro-Lisnard »,
    « c'est un Macron 2 abruti » quand il s'agit de Lisnard). Sous une publication qui parle de Lisnard, « il »,
    « ce type », « ce candidat » le désignent souvent : vérifie avec le contexte.
I = INSULTANT, et l'insulte vise autre chose ou quelqu'un d'autre : une autre personnalité ou un autre parti
    (Mélenchon, LFI, Macron, RN, Attal…), un groupe de personnes, un journaliste, ou un autre commentateur. Un
    soutien de Lisnard qui insulte ses adversaires, c'est I. En cas de doute sur la cible, I.
Q = QUESTION qui appelle une réponse de l'équipe : vraie question sur le candidat, son programme, ses positions,
    le mouvement, l'adhésion, un événement ; doute sincère (« est-ce qu'il compte vraiment… ? ») ; demande
    d'aide ou d'information ; affirmation FAUSSE sur Lisnard ou Nouvelle Énergie qu'il faudrait rectifier.
(rien) = AUTRE : tout le reste, y compris les soutiens, les éloges, les « Bravo », les critiques polies, les
    avis, les blagues sans insulte, les émojis seuls.

Ce qui est INSULTANT (L ou I) : injure ou grossièreté qui vise une personne ou un groupe (con, connard, abruti,
débile, ordure, pourriture, merde, « pauvre type », « faux cul »…), menace ou appel à la violence (« une balle »,
« je lui mets une gifle », « il faut l'enfermer »), propos haineux, raciste, homophobe ou déshumanisant
(« vermine », « nuisibles », « parasites » pour des personnes), attaque personnelle méprisante sur le physique,
l'âge ou la santé mentale (« vieux sénile », « grand malade », « taré »).
Ce qui N'EST PAS insultant : une critique même dure mais sans injure (« il ment », « programme irréaliste »,
« opportuniste », « je ne voterai jamais pour lui ») ; un gros mot qui ne vise personne (« putain, enfin un
vrai candidat », « on est dans la merde ») ; « facho », « gaucho » employés seuls comme étiquette politique sans
mépris ajouté → AUTRE ; une moquerie légère sans injure → AUTRE.

Ce qui N'EST PAS une question : une question rhétorique ou ironique (« Qui peut encore voter pour lui ? »,
« Et ça vous étonne ? »), une question adressée à un autre commentateur pour se disputer, une question
insultante (alors L ou I).

Si un commentaire est à la fois insultant et une question, l'insulte l'emporte (L ou I).

Garde le même niveau d'exigence du premier au dernier lot : ne deviens ni plus sévère ni plus indulgent avec
la fatigue.

COMPTE RENDU FINAL
Quand tous les lots sont faits, donne-moi en quelques lignes : les numéros des lots faits et leur mode, et pour
chacun le nombre de L, I et Q. Ajoute les éventuels messages d'erreur, et les commentaires qui t'ont fait
hésiter (numéro de lot et #N) avec la raison en une phrase.
```
