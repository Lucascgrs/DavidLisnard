"""Interface graphique (tkinter, thème Windows 11) : « python -m interface » ou double-clic sur Interface.bat.

- application : la fenêtre, l'en-tête, la barre de messages, les boucles de rafraîchissement ;
- onglets_collecte : tableau de bord, YouTube, Instagram, WhatsApp, planification ;
- onglet_analyse : l'onglet Analyse et ses trois sous-onglets (analyse_commentaires, analyse_synthese,
  analyse_modele) ;
- theme : couleurs, polices et petits composants graphiques.

L'interface ne collecte et ne note rien elle-même : elle lance « python -m collecte » et « python -m analyse » en
arrière-plan, comme on le ferait à la main, et lit leurs fichiers.
"""
