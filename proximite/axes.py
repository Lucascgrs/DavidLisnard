"""Les trois axes et leurs sous-thèmes (la grille complète, avec les repères de notation : docs/GRILLE_PROXIMITE.md).

Chaque mesure est rangée dans un sous-thème et notée de -3 à +3 sur l'axe de ce sous-thème : le signe dit de quel
côté de l'axe elle tire, la valeur absolue à quel point. Les sous-thèmes « hors axes » (institutions, autres sujets)
sont affichés mais n'entrent dans aucune coordonnée : ils ne se lisent pas sur ces trois oppositions.
"""

AXES = {
    "E": {
        "nom": "Économie et social",
        "moins": "Intervention et redistribution",
        "plus": "Libéralisme économique",
        "definition": "Le rôle de l'État dans l'économie. À gauche (-) : plus de dépense publique et d'impôts sur les "
                      "hauts revenus et le capital, droits des salariés, prestations étendues, soutien à la demande, "
                      "secteur public. À droite (+) : baisse des prélèvements et de la dépense, liberté d'entreprendre, "
                      "flexibilité du travail, politique de l'offre, place du privé et de la concurrence.",
    },
    "O": {
        "nom": "Ordre et immigration",
        "moins": "Libertés, prévention, accueil",
        "plus": "Autorité, sanction, fermeture",
        "definition": "Sécurité, justice, immigration, mœurs et école. À gauche (-) : prévention, droits des "
                      "personnes, libertés publiques, accueil et régularisation, progressisme des mœurs. À droite (+) : "
                      "fermeté pénale, pouvoirs de police, contrôle et réduction de l'immigration, identité, autorité.",
    },
    "S": {
        "nom": "Souveraineté et monde",
        "moins": "Europe et ouverture",
        "plus": "Souveraineté nationale",
        "definition": "La France face à l'Europe et au monde. À gauche (-) : intégration européenne, défense et "
                      "décisions communes, libre-échange, alliances. À droite (+) : primauté du droit national, sortie "
                      "ou refus des traités, protectionnisme et relocalisation, indépendance militaire.",
    },
}

# code → (axe, nom). Axe None : hors axes.
SOUS_THEMES = {
    "E1": ("E", "Impôts et prélèvements"),
    "E2": ("E", "Dépense publique, dette, État"),
    "E3": ("E", "Travail, salaires, emploi"),
    "E4": ("E", "Protection sociale, retraites, santé"),
    "E5": ("E", "Entreprises, industrie, agriculture"),
    "E6": ("E", "Logement et services publics"),
    "E7": ("E", "Énergie et environnement"),
    "O1": ("O", "Sécurité et police"),
    "O2": ("O", "Justice et peines"),
    "O3": ("O", "Immigration, asile, nationalité"),
    "O4": ("O", "Laïcité, identité, mœurs"),
    "O5": ("O", "Libertés publiques et numérique"),
    "O6": ("O", "École et éducation"),
    "S1": ("S", "Union européenne"),
    "S2": ("S", "Défense et diplomatie"),
    "S3": ("S", "Commerce, protectionnisme, relocalisation"),
    "H1": (None, "Institutions et démocratie"),
    "H2": (None, "Autres sujets"),
}

# Ce que veut dire une note vers -3 ou vers +3 dans chaque sous-thème, en un ou deux mots (affiché sur le site, au-dessus
# de la colonne du sous-thème ; le détail est dans docs/GRILLE_PROXIMITE.md).
POLES = {
    "E1": ("plus d'impôts", "moins d'impôts"),
    "E2": ("plus de dépense", "moins d'État"),
    "E3": ("droits des salariés", "flexibilité"),
    "E4": ("plus de prestations", "moins de prestations"),
    "E5": ("aides, État actionnaire", "concurrence, moins de normes"),
    "E6": ("plus de public", "plus de privé"),
    "E7": ("normes, plan public", "moins de contraintes"),
    "O1": ("prévention", "pouvoirs de police"),
    "O2": ("réinsertion", "peines sévères"),
    "O3": ("accueil", "fermeture"),
    "O4": ("progressisme", "identité, tradition"),
    "O5": ("libertés", "surveillance"),
    "O6": ("égalité", "autorité, sélection"),
    "S1": ("plus d'Europe", "moins d'Europe"),
    "S2": ("défense commune", "indépendance"),
    "S3": ("libre-échange", "protectionnisme"),
}

NOTE_MIN, NOTE_MAX = -3, 3


def axe_de(code: str) -> str | None:
    return SOUS_THEMES[code][0]
