"""Collecte des commentaires : YouTube, Bluesky, Instagram, Facebook (groupes publics) et X.

- __main__ : la commande « python -m collecte » (une source après l'autre, bilan, puis notation des nouveaux) ;
- depot : format des lignes, ajout sans doublon, état, Excel et bilan ;
- sources/ : un module par plateforme, avec une fonction collecter(depot, journal) ;
- perimetre : modifier perimetre.json (ajout de chaînes et de comptes depuis l'interface) ;
- planification : la collecte automatique par le Planificateur de tâches de Windows ;
- connexion_instagram : créer ou vérifier la session du compte Instagram de collecte ;
- connexion_facebook : créer ou vérifier la session du compte Facebook de collecte (config/facebook.env) ;
- connexion_x : créer ou vérifier la session du compte X de collecte (config/x.env).
"""
