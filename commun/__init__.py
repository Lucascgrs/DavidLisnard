"""Socle partagé par la collecte, l'analyse et l'interface.

- config : emplacements des dossiers, réglages (perimetre.json, cles.json), liste des sources ;
- fichiers : lecture et écriture des JSON et des CSV (écriture atomique) ;
- textes : dates, accents, noms de fichiers, empreintes ;
- taches : une seule collecte ou analyse à la fois (verrou), arrêt propre, lancement en arrière-plan ;
- journal : affichage à l'écran et dans donnees/journal.log.
"""
