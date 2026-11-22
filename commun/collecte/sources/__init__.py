"""Une source = un module avec une fonction collecter(depot, journal) -> dict.

Le dictionnaire renvoyé peut contenir « statut » (« ok » par défaut), « message » et « details » (liste de lignes),
repris dans le bilan. Une source lève collecte.depot.SourceImpossible quand elle ne peut pas être lue maintenant,
et appelle depot.verifier_arret() entre deux éléments pour s'arrêter proprement à la demande.
"""
