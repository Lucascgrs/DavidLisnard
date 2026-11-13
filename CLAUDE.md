# Règles du projet DavidLisnard

## Mise à jour du projet (PROCESS.md)

- Quand l'utilisateur demande de « mettre à jour le projet » (ou de collecter, annoter, ranger les thèmes…), suivre
  `PROCESS.md` étape par étape, dans l'ordre, et finir par le compte rendu de l'étape 11.
- Ne jamais refaire ce qui est déjà fait : un commentaire lu pour les thèmes (`lus.csv`), une catégorie donnée, une
  annotation enregistrée ne se refont pas. Seul le nouveau est traité.
- Tout changement d'enchaînement, de commande ou de critère (quand annoter, quand réentraîner…) se reporte dans
  `PROCESS.md` dans la même tâche.

## Documentation

- `README.md` : se servir du projet. `PROCESS.md` : la mise à jour. `docs/FONCTIONNEMENT.html/.pdf` : comment ça
  marche. `docs/GRILLE.md` : la notation. `docs/HISTORIQUE.md` : décisions, essais abandonnés, versions du modèle
  (y ajouter une ligne à chaque décision ou version, plutôt que de créer un nouveau document de conception).

## Document de fonctionnement (docs/FONCTIONNEMENT.pdf)

Le document illustré qui explique comment marche le projet est tenu à jour en même temps que le projet.

- Source modifiable : `docs/FONCTIONNEMENT.html`. PDF : `docs/FONCTIONNEMENT.pdf`, regénéré par `python -m docs`.
  Ne jamais modifier le PDF à la main.
- Les chiffres (nombre de commentaires par source, annotations, version du modèle et ses mesures, thèmes…)
  sont des `{{nom}}` remplis à la génération par `chiffres()` dans `docs/__main__.py`. Il suffit de relancer
  `python -m docs` pour les mettre à jour.
- **Toute modification de structure ou de méthode oblige à mettre à jour ce document dans la même tâche** :
  modifier `docs/FONCTIONNEMENT.html` (texte, schémas, et `chiffres()` si besoin), puis relancer `python -m docs` et
  relire le PDF obtenu. Sont concernés en particulier :
  - une source ajoutée, retirée ou collectée autrement (API, navigateur, flux), ou un changement du périmètre ;
  - un changement de l'endroit ou de la forme du stockage (dossiers de `donnees/`, `corpus.csv`, tables Supabase) ;
  - un changement de la grille de notation (critères, échelles, règles de cible ou d'ironie) ou de la façon
    d'annoter ;
  - un autre modèle de départ, une autre architecture, d'autres réglages d'entraînement (couches figées, époques,
    taux d'apprentissage, longueurs d'entrée), une autre façon de combiner ou d'étalonner les modèles ;
  - un changement de la priorité des notes affichées (corrections, notes relues, modèle) ;
  - un changement de ce qui est publié, de l'hébergement du site ou de ses pages ;
  - une nouvelle commande ou un nouvel enchaînement dans un lancement.
- Un simple réentraînement (nouvelle version vN) ou une collecte ne demandent que `python -m docs` (la carte
  « Ton inversé » se calcule elle aussi à la génération, par `analyse/ton_inverse.py`, sur les notes du corpus :
  la générer après la renotation complète).
- Les erreurs du générateur (« Valeurs manquantes dans chiffres() ») signalent un `{{nom}}` sans valeur : ajouter
  la valeur dans `chiffres()`, ne pas retirer la vérification.
