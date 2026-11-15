# Vérification factuelle des affirmations de David Lisnard

Ce paquet vérifie, thème par thème, ce que dit David Lisnard, à partir de données publiques téléchargées et
recalculées. Le plan d'origine est le PDF `Plan_verification_Lisnard.pdf` (dossier PROJECT). La liste des thèmes
vient du « Dossier de vérification Lisnard » d'un collègue.

**Tableau de tous les verdicts** : `SYNTHESE.md`. **Toutes les affirmations** : `registre_affirmations.csv`.

## Organisation

```
verification/
├── corpus/                     Parquet du RAG copiés depuis R2 (lecture seule) + inventaire.json
├── commun/                     corpus, téléchargements tracés, lecture des formats Eurostat/OCDE/FMI
├── conclusions.py, site.py      le site public : conclusion courte de chaque affirmation, générateur des pages
├── site/                       pages du site (générées), styles, script des filtres, vercel.json
├── registre_affirmations.csv   toutes les affirmations, avec leur verdict (généré)
├── SYNTHESE.md                 tableau des verdicts (généré)
└── themes/NN_nom/
    ├── affirmations.csv        citations exactes, date, support, adresse, versions successives
    ├── position.md             ce que pense Lisnard sur le thème, ses mesures
    ├── telecharger.py          refait tous les téléchargements
    ├── sources.csv             catalogue des fichiers bruts : organisme, niveau, adresse, dates, SHA-256
    ├── brut/<organisme>/       fichiers tels que téléchargés, jamais retouchés
    ├── calculs/
    │   ├── calculer.py         tous les calculs, à partir de brut/
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
python -m verification site deployer        … et le met en ligne : https://verification-lisnard.vercel.app
```

## Le site

Une page d'accueil et une page par thème (ce qu'il dit, ce que disent les chiffres, conclusion). Le site affiche,
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
