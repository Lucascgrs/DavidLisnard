# Règles du projet DavidLisnard

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
- Un simple réentraînement (nouvelle version vN) ou une collecte ne demandent que `python -m docs`.
  Exception : la carte « Ton inversé » porte une mesure faite à part, datée dans le texte : la remesurer ou la
  dater à nouveau après un réentraînement.
- Les erreurs du générateur (« Valeurs manquantes dans chiffres() ») signalent un `{{nom}}` sans valeur : ajouter
  la valeur dans `chiffres()`, ne pas retirer la vérification.
