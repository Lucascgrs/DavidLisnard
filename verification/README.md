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
```

## Règles

- **Hiérarchie des sources** : A statistique publique, B contrôle et évaluation (Cour des comptes, Sénat…), C
  recherche, D think tanks et parties prenantes (jamais arbitres), E presse.
- **Échelle de verdict** : exact, plutôt exact, trompeur, faux, invérifiable, opinion ou promesse.
- **Estimations** : tout chiffrage de mesure est marqué « estimation, non fiable à 100 % » dans `resultats.csv` et
  dans `analyse.md` (le contrôle `verifier` le vérifie).
- **Chiffres lus dans un PDF** : recopiés une seule fois dans `calculer.py`, avec la phrase exacte. Le script vérifie
  qu'elle figure dans le PDF avant de calculer.
- **Rien n'est partagé** (R2, groupe) sans l'accord de l'utilisateur.
