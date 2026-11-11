"""Thèmes des critiques et des éloges : lecture par Claude des commentaires argumentés, un par un.

Méthode (docs/PROPOSITIONS_CRITIQUES.pdf, option E, choisie le 2026-11-11) :
- sélection : parle de lui (cible L), pertinence ≥ 12, 20 mots ou plus, fiabilité bonne ou moyenne (les notes
  relues par Claude et les corrections comptent comme bonnes), une seule fois par texte ;
- chaque commentaire est lu ; pour chaque thème qu'il aborde, on note le sens (E éloge, C critique, D doute ou
  question) et une phrase courte ; un thème absent de la liste est créé ;
- à la fin de chaque passage, les thèmes proches sont fusionnés ;
- mise à jour à la demande : les nouveaux commentaires sélectionnés sont lus de la même façon.

Fichiers dans donnees/critiques/ (voir critiques/donnees.py).
"""
