"""Les cinq notes (0 à 20) et la cible, telles que les définit docs/GRILLE.md."""

CRITERES = ["tonalite", "forme", "systeme", "idees", "pertinence"]
REPROCHES = ("forme", "systeme", "idees")  # notes symétriques : 0 reproche fort · 10 non évoqué · 20 éloge

# Cible : L (le commentaire parle de Lisnard) ou A (autre chose). Au-delà de cette probabilité de A, la tonalité et
# les reproches valent 10 : ils ne concernent pas Lisnard.
SEUIL_A = 0.6

TITRES = {"tonalite": "Tonalité", "forme": "Forme", "systeme": "Système", "idees": "Idées", "pertinence": "Pertinence"}
COURTS = {"tonalite": "Ton", "forme": "Forme", "systeme": "Syst.", "idees": "Idées", "pertinence": "Pert."}
EXPLICATIONS = {
    "tonalite": "0 hostile · 10 neutre · 20 très favorable",
    "forme": "élocution, charisme, communication : 0 reproche fort · 10 non évoqué · 20 éloge",
    "systeme": "trop proche du système, de Macron : 0 reproche fort · 10 non évoqué · 20 perçu hors système",
    "idees": "ses idées, son programme : 0 rejet · 10 non évoqué · 20 adhésion",
    "pertinence": "0 n'apporte rien · 8 avis sans argument · 20 avis argumenté",
}
