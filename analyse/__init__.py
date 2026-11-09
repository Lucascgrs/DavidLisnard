"""Analyse des commentaires : 5 notes de 0 à 20 et une cible pour chacun, selon docs/GRILLE.md.

Chaîne de traitement :
- corpus : copie de travail des commentaires collectés (auteurs pseudonymisés) ;
- vecteurs : vecteurs de sens des textes (e5 multilingue) ;
- annotation : les commentaires notés à la main par Claude, qui servent d'exemples et de mesure ;
- modele : le modèle à vecteurs et ce que partagent tous les modèles ;
- affinage : le réseau e5 affiné, qui lit chaque commentaire avec son parent et son titre ;
- ensemble : la combinaison des deux, mise en service (modeles/vN/) ;
- mesures : qualité sur le jeu de test et rapport ;
- notation : notes de tout le corpus par le modèle en service (« python -m analyse ») ;
- criteres, stockage, versions : définitions, fichiers de donnees/analyse/, versions enregistrées ;
- recalage_pertinence : correction ponctuelle de la dérive d'annotation du 2026-11-09.
"""
