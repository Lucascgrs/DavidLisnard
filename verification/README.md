# Vérification factuelle des affirmations des candidats

Ce paquet vérifie, thème par thème, ce que disent les candidats, à partir de données publiques téléchargées et
recalculées. Le premier fait est David Lisnard (Nouvelle Énergie) : le plan d'origine est le PDF
`Plan_verification_Lisnard.pdf` (dossier PROJECT), la liste des thèmes vient du « Dossier de vérification Lisnard »
d'un collègue. Le second est Jean-Luc Mélenchon (La France insoumise), depuis le 20/11/2026.

**Tableau de tous les verdicts** : `donnees/verification/SYNTHESE.md` (Lisnard),
`donnees/verification/melenchon/SYNTHESE.md` (Mélenchon). **Toutes les affirmations** : les
`registre_affirmations.csv` à côté.

## Plusieurs candidats, mêmes thèmes

- Une fiche par personne dans `commun/personnes.py` : nom, parti, dossiers du parti dans le bucket R2 du RAG, dossiers
  de scripts et de données, site et projet Vercel. David Lisnard garde ses dossiers d'origine ; chaque autre personne
  a un sous-dossier du nom de sa clé : `verification/melenchon/` (conclusions.py, themes/, site/) et
  `donnees/verification/melenchon/` (corpus/, themes/, registre, synthèse).
- Un catalogue commun des thèmes dans `commun/themes.py` : **même numéro, même nom de dossier, même intitulé pour tout
  le monde**. C'est ce qui permettra de superposer les candidats. Un sujet qui n'entre dans aucun thème existant
  reçoit le numéro suivant (17 inégalités et pauvreté, 18 climat et environnement, 19 égalité femmes-hommes et
  discriminations, ajoutés avec Mélenchon) ; une personne n'a pas forcément tous les thèmes (16, le bilan de Cannes,
  n'existe que pour Lisnard). `python -m verification themes` montre qui est vérifié sur quoi.
- Les identifiants d'affirmation gardent le préfixe du thème (`ECO-01`, `NRJ-03`…) : ils sont propres à chaque personne.
- Un fichier déjà téléchargé pour une personne (même série, même document) est repris tel quel pour l'autre :
  `REPRISES` dans `telecharger.py`, fonction `commun.sources.reprendre()` (copie, même empreinte, date d'origine, note
  « repris du dossier … »).
- Corpus de Mélenchon : programme L'Avenir en commun (2026) et transcriptions de vidéos découpées par locuteur. Seuls
  les passages où il parle sont lus (`parle_personne`) ; les transcriptions complètes non découpées
  (`sous_type` « YouTube ») ne sont jamais citées. Les citations orales viennent d'une transcription automatique.
- Les thèmes écrits après ceux de Lisnard utilisent `commun/calculs.py` (vérification des phrases recopiées dans les
  PDF et pages HTML, écriture de `resultats.csv`) ; leur colonne « ce qu'il dit » s'appelle `chiffre_annonce`
  (`chiffre_lisnard` chez Lisnard, les deux sont lues par le site).

## Organisation

```
verification/                     le code et le site
├── commun/                     corpus, téléchargements tracés, lecture des formats Eurostat/OCDE/FMI ; chemins.py
├── conclusions.py, site.py      le site public : conclusion courte de chaque affirmation, générateur des pages
├── site/                       site commun « Vérification politique » : index.html et un dossier par politique
│                               (générés), styles, script des filtres, vercel.json (écrits à la main)
└── themes/NN_nom/              les scripts du thème
    ├── registre.py             écrit affirmations.csv
    ├── telecharger.py          refait tous les téléchargements
    └── calculs/calculer.py     tous les calculs, à partir de brut/

donnees/verification/             toutes les données (suivies dans git, publiques)
├── corpus/                     Parquet du RAG copiés depuis R2 (lecture seule) + inventaire.json
├── registre_affirmations.csv   toutes les affirmations, avec leur verdict (généré)
├── SYNTHESE.md                 tableau des verdicts (généré)
└── themes/NN_nom/              même nom que le dossier des scripts
    ├── affirmations.csv        citations exactes, date, support, adresse, versions successives
    ├── position.md             ce que pense Lisnard sur le thème, ses mesures
    ├── sources.csv             catalogue des fichiers bruts : organisme, niveau, adresse, dates, SHA-256
    ├── brut/<organisme>/       fichiers tels que téléchargés, jamais retouchés
    ├── calculs/
    │   ├── METHODE.md          chaque calcul expliqué (sections M1, M2…)
    │   ├── resultats.csv       une ligne par affirmation et par variante de périmètre
    │   └── graphiques/
    └── analyse.md              verdict de chaque affirmation et pourquoi
```

## Commandes

```
python -m verification corpus               copie le corpus Nouvelle Énergie depuis R2
python -m verification chercher "<motif>"   retrouve une phrase dans le corpus
python -m verification telecharger 1        refait les téléchargements du thème 1
python -m verification calculer 1           refait les calculs du thème 1 (quelques minutes : lecture des PDF)
python -m verification verifier             contrôles : catalogue, empreintes, renvois, verdicts, estimations
python -m verification synthese             régénère registre_affirmations.csv et SYNTHESE.md
python -m verification site                 régénère le site statique (site/)
python -m verification site apercu          … et l'ouvre en local (http://localhost:8010)
python -m verification site deployer        … et le met en ligne : https://verification-politique.vercel.app
python -m verification themes               catalogue commun des thèmes et personnes vérifiées sur chacun

python -m verification melenchon <commande> les mêmes commandes pour Jean-Luc Mélenchon (corpus LFI, données dans
                                            donnees/verification/melenchon/) ; « site » régénère toujours le site
                                            commun, avec tous les politiques
```

Ajouter un candidat : une fiche dans `commun/personnes.py`, `python -m verification <clé> corpus`, puis pour chaque
thème du catalogue les trois scripts dans `verification/<clé>/themes/NN_nom/` et, dans les données, `position.md`,
`analyse.md`, `calculs/METHODE.md` ; enfin la couche de lecture `verification/<clé>/conclusions.py`.

## Le site

Un seul site pour tous les politiques, « Vérification politique » (https://verification-politique.vercel.app) :
`site/index.html` pour choisir un politique et comparer les thèmes communs, puis un dossier par politique
(`site/lisnard/`, `site/melenchon/`) avec son accueil, une page par thème (ce qu'il dit, ce que disent les chiffres,
conclusion) et ses graphiques. Un sélecteur dans l'en-tête passe d'un politique à l'autre. Le site affiche,
à la place du verdict, une étiquette qui dit la nature de l'écart (« Superlatif », « Chiffre grossi »…) et une
famille de couleur (`etiquette()` dans `site.py`) ; les verdicts d'`analyse.md` ne changent pas. Tout est écrit en dur dans les pages : aucune base de données, aucun appel réseau. `site.py` lit les
fichiers des thèmes ; `conclusions.py` ajoute, pour chaque affirmation, la conclusion en une phrase, le type d'écart
(qui sert d'étiquette) et le petit graphique « annoncé /
mesuré ». La génération s'arrête si une affirmation n'y a pas d'entrée, ou si une
valeur d'un graphique ne figure pas dans `analyse.md`. Après un changement dans un thème : relancer
`python -m verification site deployer`. Ne pas modifier les `*.html` de `site/` à la main.

## Règles

- **Hiérarchie des sources** : A statistique publique, B contrôle et évaluation (Cour des comptes, Sénat…), C
  recherche, D think tanks et parties prenantes (jamais arbitres), E presse.
- **Échelle de verdict** : exact, plutôt exact, trompeur, faux, invérifiable, opinion ou promesse.
- **Estimations** : tout chiffrage de mesure est marqué « estimation, non fiable à 100 % » dans `resultats.csv` et
  dans `analyse.md` (le contrôle `verifier` le vérifie).
- **Chiffres lus dans un PDF** : recopiés une seule fois dans `calculer.py`, avec la phrase exacte. Le script vérifie
  qu'elle figure dans le PDF avant de calculer.
- **Rien n'est partagé** (R2, groupe) sans l'accord de l'utilisateur.
