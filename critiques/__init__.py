"""Thèmes des critiques et des éloges : lecture par Claude des commentaires argumentés, un par un.

Méthode (option E, choisie le 2026-11-11 ; les options écartées sont dans docs/HISTORIQUE.md) :
- sélection : parle de lui (cible L), pertinence ≥ 12, 20 mots ou plus, fiabilité bonne ou moyenne (les notes
  relues par Claude et les corrections comptent comme bonnes), une seule fois par texte ;
- chaque commentaire est lu ; pour chaque thème qu'il aborde, on note le sens (E éloge, C critique, D doute ou
  question) et une phrase courte ; un thème absent de la liste est créé ;
- à la fin de chaque passage, les thèmes proches sont fusionnés ;
- mise à jour à la demande : les nouveaux commentaires sélectionnés sont lus de la même façon ;
- chaque critique ou doute reçoit aussi une catégorie, selon ce que le programme peut en faire
  (docs/TRI_DES_CRITIQUES.pdf, méthode A, choisie le 2026-11-12) : 1 opposition de principe, 2 demande de précision,
  3 objection sur une mesure, 4 doute sur la faisabilité, 5 suggestion. Notée à la lecture (« C3 »), ou après coup
  avec « trier » et « ranger » ; filtre « Catégorie » dans l'onglet et sur la page Thèmes ;
- seules les synthèses qui ont reçu assez de nouveaux commentaires sont réécrites (« a-resumer »).

Mise à jour pas à pas : PROCESS.md, étapes 5 à 8.

Fichiers dans donnees/critiques/ (voir critiques/donnees.py).
"""
