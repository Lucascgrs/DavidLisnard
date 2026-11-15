"""Couche de lecture du site (python -m verification site) : pour chaque affirmation, la conclusion en une phrase,
le type d'écart avec les données et, quand un chiffre se compare directement, un petit graphique à barres.

Rien ici n'ajoute de fait : tout est repris de themes/<thème>/analyse.md. Le générateur (site.py) le contrôle :
- chaque affirmation de affirmations.csv a une entrée ici, et inversement ;
- chaque valeur « fait » ou « repere » d'un graphique figure telle quelle dans la section de l'affirmation dans
  analyse.md (les valeurs « dit » sont celles de la citation).

Une barre = (libellé, valeur écrite à la française, rôle). Rôles : « dit » (ce qu'il annonce), « fait » (donnée
publique), « repere » (point de comparaison).
"""

# Phrase d'accroche de chaque thème (page d'accueil et haut de la page du thème).
ACCROCHES = {
    "01": "Le diagnostic tient sur l'essentiel, mais il pousse presque toujours le chiffre ou le classement d'un cran.",
    "02": "Le constat tient sur les prisons et les moyens de la justice, pas sur toute sa lecture de la délinquance.",
    "03": "Les chiffres de base sont souvent justes ; deux comparaisons sont forcées et la mesure phare bute sur le "
          "droit.",
    "04": "Le décompte des organismes publics est exact, mais la présentation des agences prête à confusion et "
          "trois chiffres n'ont pas de source.",
    "05": "Proche des chiffres officiels sur la dette locale et les dotations ; sa comparaison européenne mélange "
          "communes et États fédérés.",
    "06": "Les grandes lignes du diagnostic sont confirmées, mais deux chiffres sont loin des données ou mal étiquetés.",
    "07": "Les difficultés d'accès aux soins sont réelles, mais ses chiffres les grossissent systématiquement.",
    "08": "La baisse du niveau est réelle, mais la France n'est pas « dernière d'Europe » et ses chiffres de dépense "
          "ne tiennent pas.",
    "09": "Ses chiffres, souvent repris de l'institut Molinari, sont systématiquement plus favorables à la "
          "capitalisation que les sources publiques.",
    "10": "Globalement juste : la construction s'est effondrée et la France dépense plus que ses voisins, même s'il "
          "grossit un peu l'écart.",
    "11": "Des chiffres presque toujours bien recopiés, mais deux comparaisons mal construites.",
    "12": "Le diagnostic économique tient ; deux chiffres sociaux qu'il répète sont très au-dessus de la "
          "réalité.",
    "13": "Le constat central est exact (la France est passée sous la moyenne européenne), mais il grossit le "
          "déclassement.",
    "14": "Surtout des propositions institutionnelles, donc des opinions ; le seul chiffre vérifiable est juste dans "
          "l'ordre de grandeur.",
    "15": "Fidèle à de bonnes sources sur le numérique et l'IA ; très exagéré sur l'écart culturel entre Paris et la "
          "province.",
    "16": "Le bilan financier qu'il revendique est confirmé par les comptes publics, avec deux nuances sur les années "
          "de comparaison.",
}

# Types d'écart entre ce qu'il dit et ce que disent les données : (étiquette affichée, définition). L'étiquette
# remplace le verdict sur le site ; la couleur dit à quel point la phrase s'éloigne des chiffres (site.py, etiquette()).
ECARTS = {
    "arrondi": ("Arrondi",
                "L'ordre de grandeur est le bon ; le chiffre est arrondi, souvent dans le sens qui l'arrange."),
    "superlatif": ("Superlatif",
                   "« Record », « premier », « dernier » : la France est bien ou mal placée, mais pas à la place "
                   "annoncée."),
    "perimetre": ("Périmètres mélangés",
                  "Le chiffre existe, mais il ne mesure pas ce que dit la phrase, ou il est comparé à un chiffre qui "
                  "ne couvre pas la même chose."),
    "contexte": ("Contexte manquant",
                 "Le chiffre est juste, mais il manque l'élément qui change la lecture : année de départ choisie, cas "
                 "extrême, méthode non dite."),
    "date": ("Chiffre daté", "Le chiffre a été vrai, mais il est ancien ou dépassé."),
    "gonfle": ("Chiffre grossi", "La réalité va dans le même sens, mais le chiffre réel est nettement plus faible."),
    "erreur": ("Erreur de fait", "Les données publiques disent autre chose."),
    "source": ("Source fragile",
               "Pas de source, source mal attribuée, ou source proche de ses thèses."),
    "inaccessible": ("Données inaccessibles",
                     "Les données officielles existent sans doute, mais n'ont pas pu être consultées le jour de "
                     "l'analyse."),
}

# Graphiques déjà produits par calculs/calculer.py : affirmation → (fichier de calculs/graphiques/, légende).
# Le premier graphique d'un thème est aussi repris dans sa conclusion.
FIGURES = {
    "DETTE-01": ("depense_publique_ue.png", "Dépense publique en % du PIB : France, Finlande et moyenne de l'UE."),
    "DETTE-03": ("charge_dette_2026.png", "Intérêts de la dette et grandes missions de l'État en 2026."),
    "SECU-01": ("violences_2016_2025.png", "Violences et homicides enregistrés, base 100 en 2017."),
    "IMMI-01": ("premiers_titres_motifs.png", "Premiers titres de séjour délivrés, par motif."),
    "ECO-03": ("productivite_2010_2024.png", "Productivité horaire depuis 2010."),
    "LOG-01": ("logements_commences.png", "Logements commencés par an."),
    "NRJ-05": ("prix_electricite_entreprises.png",
               "Prix de l'électricité des entreprises françaises en 2024, selon leur consommation."),
    "AGRI-01": ("solde_agroalimentaire.png", "Solde des échanges agricoles et agroalimentaires."),
    "EUR-01": ("pib_par_habitant_spa.png", "PIB par habitant en standards de pouvoir d'achat (UE à 27 = 100)."),
    "CAN-01": ("dette_cannes.png", "Dette de la ville de Cannes."),
}


def _b(titre: str, unite: str, *lignes: tuple) -> dict:
    return {"titre": titre, "unite": unite, "lignes": lignes}


LECTURE = {
    # ------------------------------------------------------------------ 01 Dette, dépense publique et fiscalité
    "DETTE-01": dict(
        resume="Première de l'UE et de l'OCDE en 2022 et 2023, mais pas « du monde », et dépassée par la Finlande "
               "depuis 2024.",
        ecart="superlatif",
        barres=_b("Dépense publique", "% du PIB",
                  ("Il annonce", "58", "dit"), ("France, 2022", "58,4", "fait"), ("France, 2024", "57,0", "fait"),
                  ("Finlande, 2024", "57,9", "repere"))),
    "DETTE-02": dict(
        resume="Première de l'OCDE en 2022 (45,9 % selon l'OCDE, 45,4 % selon l'Insee). Depuis, le Danemark est "
               "repassé devant : ses reprises de 2026 ne sont plus exactes."),
    "DETTE-03": dict(
        resume="Pour la dette de l'État, le rapport est de 5,5 à 5,8. « 7 fois » n'est atteint qu'en comptant les "
               "intérêts de toutes les administrations.",
        ecart="perimetre",
        barres=_b("Intérêts de la dette rapportés au budget de la Justice, 2026", "fois",
                  ("Il annonce", "7", "dit"), ("Dette de l'État, loi de finances", "5,5", "fait"),
                  ("Dette de l'État, prévision révisée", "5,8", "fait"),
                  ("Toutes les administrations", "6,9", "fait"))),
    "DETTE-04": dict(
        resume="66 Md€ est la charge de toutes les administrations. Celle de l'État (54,2 Md€ en 2025) restait "
               "derrière l'Enseignement scolaire ; la phrase ne devient vraie qu'avec le budget 2027.",
        ecart="perimetre",
        barres=_b("Charge de la dette et Enseignement scolaire, 2025", "Md€",
                  ("Il annonce", "66", "dit"), ("Charge de la dette de l'État", "54,2", "fait"),
                  ("Intérêts de toutes les administrations", "65,7", "fait"),
                  ("Enseignement scolaire", "64,3", "repere"))),
    "DETTE-05": dict(
        resume="Eurostat publie aujourd'hui 3 484 Md€ et 117,3 % du PIB pour le même trimestre : la différence vient "
               "d'une simple révision.",
        barres=_b("Dette publique au 3e trimestre 2025", "Md€",
                  ("Il annonce", "3 482", "dit"), ("Eurostat", "3 484", "fait"))),
    "DETTE-06": dict(
        resume="De 2017 à 2024, la dette a augmenté de 1 043 Md€ (+46,1 %) et le PIB de 28,1 %.",
        barres=_b("Hausse de 2017 à 2024", "%",
                  ("Dette, il annonce", "46", "dit"), ("Dette", "46,1", "fait"),
                  ("Richesse nationale, il annonce", "27", "dit"), ("PIB", "28,1", "fait"))),
    "DETTE-07": dict(
        resume="Les 400 Md€ de dette en moins sont justes (environ 430 Md€). Mais cela fait 13 % de la dette : les "
               "intérêts baisseraient d'environ 13 %, pas de moitié.",
        ecart="gonfle",
        barres=_b("Baisse des intérêts si la France avait suivi la zone euro", "%",
                  ("Il annonce (« divisées par deux »)", "50", "dit"), ("Calcul", "13", "fait"))),
    "DETTE-08": dict(
        resume="54,7 % est le chiffre exact du 1er trimestre 2025, pour la dette négociable de l'État. « 12,5 % "
               "refinancés par an » est une approximation, et les « 27 % hors zone euro » sont invérifiables.",
        ecart="arrondi"),
    "DETTE-09": dict(
        resume="Le déficit de 170 Md€ est exact, mais il représente 11 % des recettes publiques. « 37,8 % » n'a de "
               "sens que pour l'État seul.",
        ecart="perimetre",
        barres=_b("Déficit rapporté aux recettes", "%",
                  ("Il annonce (« recettes publiques »)", "37,8", "dit"),
                  ("Toutes les administrations, 2024", "11", "fait"), ("État seul, 2024", "45", "fait"),
                  ("État seul, 2025", "35", "fait"))),
    "DETTE-10": dict(
        resume="Le montant est juste et la France est en tête en % du PIB. Mais « par rapport à la population », "
               "c'est-à-dire par habitant, elle n'est que 8e en Europe et dans l'OCDE.",
        ecart="superlatif"),
    "DETTE-11": dict(
        resume="144 Md€ se situe dans la fourchette des estimations publiques, qui vont de 45 à 211 Md€ selon ce "
               "qu'on compte. Il ne dit pas quel périmètre il retient.",
        ecart="contexte",
        barres=_b("Aides aux entreprises : les estimations publiques", "Md€",
                  ("Il annonce", "144", "dit"), ("Aides d'État au sens européen (2022)", "45", "fait"),
                  ("Inspection générale des finances", "88", "fait"), ("Sénat, sens restreint", "108", "fait"),
                  ("Haut-Commissariat au plan", "112", "fait"), ("Clersé (2019)", "157", "fait"),
                  ("Sénat, sens large (2023)", "211", "fait"))),
    "DETTE-12": dict(
        resume="Le niveau français est juste (12,6 % du PIB). Mais le « 7,3 % » de la zone euro vient d'une tribune "
               "de l'iFRAP sans méthode publiée : l'Allemagne seule est à 9,3 %.",
        ecart="source",
        barres=_b("Prélèvements sur les entreprises", "% du PIB",
                  ("France, il annonce", "13,2", "dit"), ("France (Fipeco, 2022)", "12,6", "fait"),
                  ("Zone euro, il annonce", "7,3", "dit"), ("Allemagne (Fipeco)", "9,3", "repere"))),
    "DETTE-13": dict(
        resume="L'écart de « plus du double » tient sur les deux bases de calcul, mais il compare un chiffre "
               "« entreprises seules » à une médiane « tous payeurs ».",
        ecart="perimetre",
        barres=_b("Impôts de production", "% du PIB",
                  ("France, il annonce", "3,6", "dit"), ("France, sociétés seules (2022)", "3,3", "fait"),
                  ("Médiane européenne, il annonce", "1,2", "dit"), ("Zone euro, sociétés seules", "1,5", "fait"))),
    "DETTE-14": dict(
        resume="La France est 3e de l'OCDE, derrière la Belgique et l'Allemagne, pas première.",
        ecart="superlatif",
        barres=_b("Part du coût d'un salarié moyen prélevée (OCDE)", "%",
                  ("Belgique", "52,5", "repere"), ("Allemagne", "49,3", "repere"), ("France", "47,2", "fait"))),
    "DETTE-15": dict(
        resume="45 % des foyers ont payé l'impôt sur les revenus de 2023, donc 55 % n'en ont pas payé. Les 10 % les "
               "plus aisés en paient même 76 %, plus qu'il ne le dit.",
        barres=_b("Impôt sur le revenu (revenus 2023)", "%",
                  ("Foyers non imposés, il annonce", "55", "dit"), ("Foyers non imposés", "55", "fait"),
                  ("Part payée par les 10 % les plus aisés, il annonce", "70", "dit"),
                  ("Part payée par les 10 % les plus aisés", "76", "fait"))),
    "DETTE-16": dict(
        resume="Le budget 2025 recense bien 474 niches pour 85,1 Md€, dont 42,1 Md€ sur l'impôt sur le revenu, soit "
               "45 % de ses recettes."),
    "DETTE-17": dict(
        resume="La France perçoit 45 à 47 % des droits de succession et de donation des pays de l'UE membres de "
               "l'OCDE, et c'est là qu'ils pèsent le plus en % du PIB."),
    "DETTE-18": dict(
        resume="Début mai 2026, les taxes pesaient 50 % du prix de l'essence et 45 % du gazole. La France est 9e de "
               "l'UE pour l'essence, pas première.",
        ecart="gonfle",
        barres=_b("Part des taxes dans le prix à la pompe", "%",
                  ("Il annonce", "60", "dit"), ("Essence SP95, mai 2026", "50", "fait"),
                  ("Gazole, mai 2026", "45", "fait"), ("Essence, moyenne 2025", "57", "fait"),
                  ("Gazole, moyenne 2025", "54", "fait"))),
    "DETTE-19": dict(
        resume="Vrai seulement dans le cas le plus extrême : 61 % pour une très grande entreprise et un actionnaire "
               "très aisé. Dans le cas ordinaire, le taux cumulé est de 49 %.",
        ecart="contexte",
        barres=_b("Taux d'imposition cumulé sur un dividende", "%",
                  ("Il annonce (« excède »)", "60", "dit"), ("Entreprise ordinaire, flat tax", "49", "fait"),
                  ("Très grande entreprise, jusqu'à", "59", "fait"),
                  ("Très grande entreprise et actionnaire très aisé", "61", "fait"))),
    "DETTE-20": dict(
        resume="Les ordres de grandeur sont cohérents (200 Md€ font bien 7 points de PIB). Une phrase est fausse : "
               "après ces économies, la France ne resterait pas la plus dépensière d'Europe, elle passerait au 6e "
               "rang."),
    "DETTE-21": dict(
        resume="Le calcul tient : 120 Md€ font 369 € par mois et par salarié, si toute la baisse de cotisations "
               "allait au salaire net. Sur les 40 Md€ d'impôts de production, seuls 8 Md€ environ sont détaillés.",
        barres=_b("Gain mensuel par salarié", "€ par mois",
                  ("Il annonce (« presque 400 euros »)", "400", "dit"),
                  ("120 Md€ partagés entre 27,1 millions de salariés", "369", "fait"))),
    "DETTE-22": dict(
        resume="Le chiffrage est trop bas : combler l'écart avec la zone euro (4,7 points de PIB) demanderait "
               "environ 140 Md€, pas 100.",
        barres=_b("Baisse de prélèvements nécessaire", "Md€",
                  ("Il annonce", "100", "dit"), ("Pour atteindre la moyenne de la zone euro", "140", "fait"))),

    # ------------------------------------------------------------------ 02 Sécurité, justice et narcotrafic
    "SECU-01": dict(
        resume="Les chiffres sont proches, mais les trois quarts de la hausse des violences viennent des violences "
               "intrafamiliales, que les victimes signalent beaucoup plus qu'avant.",
        ecart="contexte",
        barres=_b("Hausse de 2017 à 2022", "%",
                  ("Violences, il annonce", "51", "dit"), ("Violences enregistrées", "44", "fait"),
                  ("dont violences intrafamiliales", "84", "fait"), ("dont hors cadre familial", "17", "fait"),
                  ("Homicides, il annonce", "15", "dit"), ("Homicides", "14,7", "fait"))),
    "SECU-02": dict(
        resume="Il manque bien plus de 20 000 places. Mais la France n'incarcère pas moins qu'ailleurs : son taux de "
               "détention est au-dessus de la médiane européenne.",
        ecart="erreur",
        barres=_b("Détenus pour 100 000 habitants, janvier 2024", "",
                  ("France", "111,5", "fait"), ("Médiane européenne", "104,8", "repere"),
                  ("Allemagne", "71,2", "repere"))),
    "SECU-03": dict(
        resume="42 % des peines ne sont pas exécutées le jour du jugement, mais 21 % un an après et 10 % cinq ans "
               "après. Son chiffre décrit le jour du jugement, pas « six mois ».",
        ecart="perimetre",
        barres=_b("Peines de prison ferme pas encore exécutées", "%",
                  ("Il annonce (« au bout de six mois »)", "40", "dit"), ("Le jour du jugement", "42", "fait"),
                  ("Un an après", "21", "fait"), ("Cinq ans après", "10", "fait"))),
    "SECU-04": dict(
        resume="La France a bien environ deux fois moins de juges que la médiane. « Le budget le plus faible "
               "d'Europe » n'a pas pu être vérifié, et la CEPEJ ne classe pas la France dernière.",
        ecart="superlatif",
        barres=_b("Juges professionnels pour 100 000 habitants", "",
                  ("France, il annonce", "10,9", "dit"), ("France (2024)", "11,6", "fait"),
                  ("Médiane, il annonce", "17,7", "dit"), ("Médiane de l'UE (2024)", "23,4", "fait"))),
    "SECU-05": dict(
        resume="4 592 communes ou intercommunalités ont une police municipale, sur 34 969 communes : 11 à 13 %.",
        barres=_b("Communes dotées d'une police municipale", "%",
                  ("Il annonce", "12", "dit"), ("Au plus", "13", "fait"),
                  ("Avec au moins un agent", "11", "fait"))),
    "SECU-06": dict(
        resume="Le Sénat retient 3,5 Md€ « en fourchette basse » : sa fourchette est cohérente. Son « 8 milliards » "
               "de 2026 n'a aucune source publique.",
        ecart="source"),
    "SECU-07": dict(
        resume="Le besoin est confirmé (22 361 places manquantes selon le Sénat). Coût estimé : environ 7,4 Md€. Le "
               "plan précédent, prévu pour 2027, n'avait livré que 7 504 places sur 15 000 fin 2025."),
    "SECU-08": dict(
        resume="Obstacle constitutionnel probable : l'atténuation de la responsabilité pénale des mineurs selon "
               "l'âge est un principe fondamental reconnu par le Conseil constitutionnel."),

    # ------------------------------------------------------------------ 03 Immigration, islamisme et identité
    "IMMI-01": dict(
        resume="13,5 % des premiers titres de 2025 ont un motif professionnel. Mais le premier motif est les études "
               "(31 %), pas la famille : « immigration de peuplement » est une lecture politique.",
        barres=_b("Premiers titres de séjour de 2025, par motif", "%",
                  ("Travail, il annonce", "13", "dit"), ("Travail", "13,5", "fait"), ("Études", "31", "repere"),
                  ("Humanitaire et divers", "31", "repere"), ("Famille", "24", "repere"))),
    "IMMI-02": dict(
        resume="Diviser par huit laisserait environ 47 000 titres. Or famille et asile en représentent 208 000, "
               "fondés sur des droits : la mesure suppose les changements juridiques qu'il propose par ailleurs.",
        barres=_b("Premiers titres de séjour par an", "titres",
                  ("Ce que laisserait une division par huit", "47 000", "dit"),
                  ("Titres familiaux et humanitaires, 2025", "208 000", "fait"),
                  ("Tous les premiers titres, 2025", "377 000", "fait"))),
    "IMMI-03": dict(
        resume="Le taux d'exécution est bien très faible (7,5 à 13,8 % selon l'année). Mais l'écart avec l'Europe "
               "est de 14 à 26 points, jamais 35.",
        ecart="gonfle",
        barres=_b("Écart d'exécution des OQTF avec l'Europe", "points",
                  ("Il annonce (« plus de »)", "35", "dit"), ("Avec l'UE à 27, 2022", "14", "fait"),
                  ("Avec l'UE hors France, 2022", "20", "fait"), ("En 2025, au plus bas", "18", "fait"),
                  ("En 2025, au plus haut", "26", "fait"))),
    "IMMI-04": dict(
        resume="Le coût est exact (1 387 M€ en 2024) et les bénéficiaires un peu arrondis (465 208). « Deux fois "
               "plus qu'il y a quinze ans » n'a pas pu être vérifié : +70 % en dix ans selon le Sénat.",
        ecart="arrondi"),
    "IMMI-05": dict(
        resume="Le sondage Ifop est cité fidèlement. Mais le « 19 % il y a trente ans » mesurait une autre "
               "question : la comparaison dans le temps est fragile.",
        ecart="perimetre"),
    "IMMI-06": dict(
        resume="Ses chiffres sont ceux de 1998-2018. Sur les vingt dernières années connues, la baisse des "
               "naissances de deux parents français est plus forte (−24,8 %) et la hausse des autres plus faible "
               "(+33,8 %).",
        ecart="date"),

    # ------------------------------------------------------------------ 04 Bureaucratie, normes et réforme de l'État
    "BUR-01": dict(
        resume="Le décompte est exact. Mais ces organismes n'ont pas été créés récemment, les 480 000 emplois sont "
               "un stock et non des recrutements, et le fonctionnement pèse 27,5 Md€, pas 100.",
        ecart="perimetre",
        barres=_b("Ce que coûtent les opérateurs de l'État", "Md€",
                  ("Il annonce (« de fonctionnement »)", "100", "dit"), ("Financements publics reçus", "77", "fait"),
                  ("dont personnel et fonctionnement", "27,5", "fait"))),
    "BUR-02": dict(
        resume="Aucune statistique publique ne compare la part des fonctions « administrantes » entre pays. Le "
               "chiffre est cité sans source.",
        ecart="source"),
    "BUR-03": dict(
        resume="L'OCDE confirme. Mais en Allemagne, hôpitaux, crèches et services sociaux sont souvent gérés par "
               "des associations ou des entreprises : l'écart ne mesure pas à lui seul la bureaucratie.",
        barres=_b("Emploi public dans l'emploi total, 2021", "%",
                  ("France, il annonce", "21", "dit"), ("France (OCDE)", "21,4", "fait"),
                  ("Allemagne, il annonce", "11", "dit"), ("Allemagne (OCDE)", "11,6", "fait"))),
    "BUR-04": dict(
        resume="Le chiffre reprend des estimations des années 2000. Il n'existe pas d'évaluation publique récente "
               "pour la France.",
        ecart="date"),
    "BUR-05": dict(
        resume="Les statistiques officielles, publiées sur Légifrance, n'ont pas pu être téléchargées. Ses propres "
               "versions varient d'un texte à l'autre.",
        ecart="inaccessible"),
    "BUR-06": dict(
        resume="80 Md€, c'est plus que tout ce que reçoivent les opérateurs (77 Md€). Sa version à 8 Md€ est plus "
               "réaliste mais reste très ambitieuse.",
        barres=_b("Économies annoncées et budget des opérateurs", "Md€",
                  ("Économies annoncées la première année", "80", "dit"),
                  ("Tous les financements publics des opérateurs", "77", "fait"),
                  ("Baisse que le Sénat jugeait déjà difficile", "2,2", "repere"))),

    # ------------------------------------------------------------------ 05 Décentralisation et collectivités
    "DEC-01": dict(
        resume="Les baisses de dotation cumulées atteignent 62,5 Md€ fin 2025. On n'arrive à 80 Md€ qu'en ajoutant "
               "l'effet de l'inflation sur une dotation gelée ; la baisse annuelle est d'environ 6 Md€.",
        ecart="contexte",
        barres=_b("Baisses de dotation cumulées depuis 2014", "Md€",
                  ("Il annonce (« plus de »)", "80", "dit"), ("Cumul à fin 2025", "62,5", "fait"),
                  ("Cumul à fin 2026", "68,5", "fait"),
                  ("Fin 2025, inflation comprise (estimation)", "74", "fait"))),
    "DEC-02": dict(
        resume="Le niveau est exact (9,0 % du PIB fin 2024). Mais la dette locale n'est pas « stable depuis trente "
               "ans » : elle était à 7,2 % du PIB en 2000.",
        barres=_b("Dette des collectivités locales", "% du PIB",
                  ("Il annonce", "8,9", "dit"), ("Fin 2024", "9,0", "fait"), ("En 2000", "7,2", "repere"),
                  ("Pic de 2020", "9,9", "repere"))),
    "DEC-03": dict(
        resume="Les collectivités françaises dépensent autant que la moyenne des administrations locales de l'UE. "
               "Les « presque 20 % » ajoutent les Länder et les régions autonomes, qui sont des États fédérés.",
        ecart="perimetre",
        barres=_b("Dépenses des collectivités, 2024", "% du PIB",
                  ("France, il annonce", "11", "dit"), ("France", "11,3", "fait"),
                  ("Moyenne européenne, il annonce", "20", "dit"), ("UE, administrations locales", "11,2", "fait"),
                  ("UE, États fédérés compris", "17,1", "fait"))),

    # ------------------------------------------------------------------ 06 Économie, travail et entreprises
    "ECO-01": dict(
        resume="Selon la définition, le déficit des échanges de biens va de 55 à 103 Md€ en 2024. Le chiffre des "
               "douanes françaises est autour de 80 Md€.",
        ecart="arrondi",
        barres=_b("Déficit des échanges de biens, 2024", "Md€",
                  ("Il annonce", "80", "dit"), ("Comptes nationaux", "55", "fait"),
                  ("Données douanières d'Eurostat", "103", "fait"))),
    "ECO-02": dict(
        resume="Le chiffre français est juste (10,2 % du PIB, 5e plus faible de l'UE). Mais l'Espagne est à 10,8 %, "
               "presque comme la France, et non à 13,6 %.",
        ecart="perimetre",
        barres=_b("Industrie manufacturière, 2024", "% du PIB",
                  ("France, il annonce", "10,6", "dit"), ("France", "10,2", "fait"),
                  ("Italie, il annonce", "16", "dit"), ("Italie", "15,0", "fait"),
                  ("Espagne, il annonce", "13,6", "dit"), ("Espagne", "10,8", "fait"))),
    "ECO-03": dict(
        resume="Selon l'OCDE : +14,1 % aux États-Unis et +9,1 % dans la zone euro. Son « 5 % » est en fait celui de "
               "la France. Le décrochage existe, mais pas dans ces proportions.",
        ecart="gonfle",
        barres=_b("Hausse de la productivité horaire, 2010-2023", "%",
                  ("États-Unis, il annonce", "22", "dit"), ("États-Unis", "14,1", "fait"),
                  ("Europe, il annonce", "5", "dit"), ("Zone euro", "9,1", "fait"),
                  ("Allemagne", "11,8", "repere"), ("France", "5,8", "repere"))),
    "ECO-04": dict(
        resume="Eurostat donne pour 2024 : France 18,8 %, Allemagne 6,6 %, zone euro 14,7 %.",
        barres=_b("Chômage des 15-24 ans, 2024", "%",
                  ("France, il annonce", "18,8", "dit"), ("France", "18,8", "fait"),
                  ("Allemagne, il annonce", "6,7", "dit"), ("Allemagne", "6,6", "fait"),
                  ("Zone euro", "14,7", "fait"))),
    "ECO-05": dict(
        resume="Ses chiffres sont ceux de la recherche totale, entreprises comprises. Pour la seule recherche "
               "publique, la France dépense un peu plus que les États-Unis.",
        ecart="perimetre",
        barres=_b("Recherche publique (État et universités)", "% du PIB",
                  ("France, il annonce", "2,2", "dit"), ("France", "0,70", "fait"),
                  ("Allemagne, il annonce", "3,1", "dit"), ("Allemagne", "0,90", "fait"),
                  ("États-Unis, il annonce", "3,5", "dit"), ("États-Unis", "0,65", "fait"))),

    # ------------------------------------------------------------------ 07 Santé et hôpital
    "SANTE-01": dict(
        resume="Selon la DREES, 18,2 % de la population vit en zone sous-dense en généralistes. Les 87 % viennent du "
               "zonage qui ouvre droit aux aides à l'installation, volontairement large.",
        ecart="perimetre",
        barres=_b("Zones qui manquent de médecins généralistes", "%",
                  ("Il annonce (« du territoire »)", "87", "dit"),
                  ("Population en zone sous-dense (DREES)", "18,2", "fait"),
                  ("Communes sous-denses", "38", "fait"), ("Population, avec un seuil très large", "61", "fait"))),
    "SANTE-02": dict(
        resume="Les non-soignants sont 26,2 % du personnel, et les seuls administratifs 11,3 %. Le reste fait "
               "tourner l'hôpital : cuisine, entretien, biomédical, logistique.",
        ecart="gonfle",
        barres=_b("Part du personnel hospitalier, 2024", "%",
                  ("Il annonce (« un tiers »)", "33", "dit"), ("Non-soignants", "26,2", "fait"),
                  ("dont filière administrative", "11,3", "fait"))),
    "SANTE-03": dict(
        resume="La France dépense plus que la moyenne de l'UE, mais moins que l'Allemagne. L'écart avec la moyenne "
               "est d'environ 34 Md€, pas 60.",
        ecart="gonfle",
        barres=_b("Dépense courante de santé, 2024", "% du PIB",
                  ("Il annonce", "12", "dit"), ("France", "11,3", "fait"), ("Allemagne", "12,2", "repere"),
                  ("Moyenne de l'UE", "10,2", "repere"))),
    "SANTE-04": dict(
        resume="Ses chiffres datent de 2018-2019. En 2023, la France compte 3,9 médecins pour 1 000 habitants, au "
               "niveau de la médiane. Le faible nombre de nouveaux diplômés, lui, reste vrai.",
        ecart="date",
        barres=_b("Médecins pour 1 000 habitants", "",
                  ("Il annonce", "3,2", "dit"), ("OCDE, 2023", "3,9", "fait"))),
    "SANTE-05": dict(
        resume="Le chiffre vient vraisemblablement des enquêtes d'un syndicat d'urgentistes. Aucune statistique "
               "publique ne le mesure.",
        ecart="source"),
    "SANTE-06": dict(
        resume="Aucune source n'est citée, et le résultat dépend de ce qu'on mesure : volume, valeur, médicaments "
               "finis ou principes actifs.",
        ecart="source"),

    # ------------------------------------------------------------------ 08 École et enseignement
    "ECOLE-01": dict(
        resume="À PISA 2022, la France est 15e sur 26 pays de l'UE, au niveau de la moyenne de l'OCDE. La baisse du "
               "niveau, elle, est bien réelle : 21 points perdus depuis 2018.",
        ecart="superlatif",
        barres=_b("Score de la France en mathématiques (PISA)", "points",
                  ("2003", "511", "fait"), ("2018", "495", "fait"), ("2022", "474", "fait"),
                  ("Moyenne de l'OCDE, 2022", "472", "repere"))),
    "ECOLE-02": dict(
        resume="La dépense publique d'éducation a augmenté de 81 % en euros courants et de 23 % une fois l'inflation "
               "retirée, jamais de 40 %. En part du PIB, elle a baissé.",
        ecart="erreur",
        barres=_b("Hausse de la dépense publique d'éducation, 2000-2024", "%",
                  ("Il annonce", "40", "dit"), ("En euros courants", "81", "fait"),
                  ("En euros constants", "23", "fait"))),
    "ECOLE-03": dict(
        resume="Le point de départ est juste (64,3 Md€ pour l'enseignement scolaire). Mais son « 30 milliards » "
               "n'est accompagné d'aucun calcul.",
        ecart="source"),
    "ECOLE-04": dict(
        resume="« Comme cela a fonctionné » n'est pas démontré : en Suède et au Chili, ces systèmes sont associés à "
               "plus de ségrégation scolaire, et leurs effets sur le niveau sont débattus."),

    # ------------------------------------------------------------------ 09 Retraites et protection sociale
    "RET-01": dict(
        resume="Ce « vrai déficit » repose sur une convention comptable que la Cour des comptes ne retient pas. "
               "Elle prévoit un déficit de 6,6 Md€ en 2025, environ 0,2 % du PIB.",
        ecart="source",
        barres=_b("Déficit des retraites", "% du PIB",
                  ("Il annonce (institut Molinari, 2020)", "2,8", "dit"),
                  ("Cour des comptes, prévision 2025", "0,2", "fait"))),
    "RET-02": dict(
        resume="Le calcul est incohérent : 116 Md€ font 30 % des retraites versées, pas 40 %. Le financement de la "
               "transition n'est pas expliqué.",
        barres=_b("Ce que représentent 116 Md€ dans le total des retraites", "%",
                  ("Il annonce", "40", "dit"), ("Calcul sur les dépenses de 2023", "30", "fait"))),
    "RET-03": dict(
        resume="Il faut 5,8 % de rendement par an pendant 40 ans, sans aucun frais. Au rendement de l'Erafp, on "
               "obtient environ 243 000 €. Et 320 000 € dans 40 ans valent environ 145 000 € d'aujourd'hui.",
        ecart="gonfle",
        barres=_b("Capital après 40 ans de cotisation à 10 % du SMIC", "€",
                  ("Il annonce", "320 000", "dit"), ("Au rendement de l'Erafp", "243 000", "fait"),
                  ("320 000 € en euros d'aujourd'hui", "145 000", "fait"))),
    "RET-04": dict(
        resume="Le rapport annuel de l'Erafp donne 4,7 % par an depuis 2006 (4,3 % un an plus tôt), pas 5,4 %.",
        ecart="gonfle",
        barres=_b("Rendement annuel de l'Erafp depuis 2006", "%",
                  ("Il annonce", "5,4", "dit"), ("À fin 2025", "4,7", "fait"), ("À fin 2024", "4,3", "fait"))),
    "RET-05": dict(
        resume="5,5 Md€ serait le total des pensions, financé en partie par les cotisations. Ce que paie le "
               "contribuable est la subvention de l'État : 3,2 Md€, soit 31 % du budget de la Justice.",
        ecart="perimetre",
        barres=_b("Régime de retraite de la SNCF et budget de la Justice, 2025", "Md€",
                  ("Il annonce (total des pensions)", "5,5", "dit"), ("Subvention de l'État au régime", "3,2", "fait"),
                  ("Budget de la Justice", "10,5", "repere"))),

    # ------------------------------------------------------------------ 10 Logement et urbanisme
    "LOG-01": dict(
        resume="258 600 logements commencés sur les douze mois connus au moment où il parle, contre plus de 500 000 "
               "par an de 1971 à 1975. La population a même augmenté de plus de 10 millions."),
    "LOG-02": dict(
        resume="Le rapport de 2 à 1 avec l'Europe est juste en temps normal. Mais ses deux chiffres viennent "
               "d'années différentes, et les 40 Md€ d'une autre source.",
        ecart="perimetre",
        barres=_b("Dépenses publiques de logement", "% du PIB",
                  ("France, il annonce", "1,2", "dit"), ("Europe, il annonce", "0,5", "dit"),
                  ("France, 2021", "1,2", "fait"), ("UE, 2021", "0,8", "fait"),
                  ("France, 2024", "1,0", "fait"), ("UE, 2024", "0,5", "fait"))),
    "LOG-03": dict(
        resume="La France est bien au-dessus de l'OCDE. Mais à périmètre égal, c'est 6,0 % contre 3,9 % : environ "
               "1,5 fois plus, et non 1,8 fois.",
        ecart="perimetre",
        barres=_b("Fiscalité immobilière dans les recettes fiscales", "%",
                  ("France, il annonce", "6", "dit"), ("France, 2023", "6,0", "fait"),
                  ("OCDE, il annonce", "3,3", "dit"), ("OCDE, même périmètre, 2023", "3,9", "fait"))),
    "LOG-04": dict(
        resume="Le croisement entre les revenus des ménages et les plafonds du logement social n'a pas été fait. Un "
               "ordre de grandeur de 60 à 70 % circule dans le secteur, sans source statistique vérifiée.",
        ecart="source"),

    # ------------------------------------------------------------------ 11 Énergie et nucléaire
    "NRJ-01": dict(
        resume="69,8 % de la production en 2019, la dernière année complète connue au moment de la tribune."),
    "NRJ-02": dict(
        resume="En 2024, nucléaire et renouvelables ont fourni 93,9 % de la production. Ce n'était pas vrai en "
               "2022 (86 %), année de pannes et de sécheresse."),
    "NRJ-03": dict(
        resume="La part des émissions est juste, et monte à 1,03 % en comptant les importations. Son 2,4 % du PIB "
               "mondial ne correspond à aucune mesure courante.",
        ecart="arrondi",
        barres=_b("Poids de la France dans le monde", "%",
                  ("PIB, il annonce", "2,4", "dit"), ("PIB, aux taux de change", "2,85", "fait"),
                  ("PIB, en pouvoir d'achat", "2,17", "fait"), ("Émissions, il annonce", "0,7", "dit"),
                  ("Émissions de CO2", "0,71", "fait"), ("Émissions, importations comprises", "1,03", "fait"))),
    "NRJ-04": dict(
        resume="Le PIB de l'UE a progressé de 62,8 % en trente ans et ses émissions ont baissé de 33 %. Deux "
               "chiffres un peu arrondis à son avantage, mais le constat tient.",
        ecart="arrondi",
        barres=_b("L'Union européenne sur trente ans", "%",
                  ("Hausse du PIB, il annonce", "70", "dit"), ("Hausse du PIB, 1995-2025", "62,8", "fait"),
                  ("Baisse des émissions, il annonce", "37", "dit"),
                  ("Baisse des émissions, 1994-2024", "33", "fait"))),
    "NRJ-05": dict(
        resume="165 €/MWh est la moyenne de toutes les entreprises françaises, petites comprises. Les grands "
               "industriels paient 78 à 79 €/MWh, à peu près comme l'industrie américaine.",
        ecart="perimetre",
        barres=_b("Prix de l'électricité, 2024", "€/MWh",
                  ("France, il annonce (toutes entreprises)", "165", "dit"),
                  ("Grands industriels français", "78", "fait"), ("États-Unis, il annonce", "73", "dit"),
                  ("Industrie américaine", "75", "fait"), ("Commerce américain", "118", "repere"))),
    "NRJ-06": dict(
        resume="Les chiffres sont justes, à une coquille près. Mais il compare les ménages français à l'industrie "
               "allemande : les ménages allemands paient 20,50 €/MWh.",
        ecart="perimetre",
        barres=_b("Accise sur l'électricité", "€/MWh",
                  ("Ménages français, il annonce", "30,35", "dit"), ("Ménages français", "30,85", "fait"),
                  ("Ménages allemands", "20,50", "repere"), ("Industrie allemande", "0,50", "fait"))),
    "NRJ-07": dict(
        resume="La délibération de la CRE donne bien ces montants. Il omet qu'en 2023, quand les prix de marché "
               "étaient très hauts, l'éolien terrestre a reversé 3,4 Md€ à l'État."),
    "NRJ-08": dict(
        resume="Le chiffre est juste, mais il vient de l'agence américaine EIA (2013), pas de l'Agence "
               "internationale de l'énergie. L'estimation a 13 ans et aucun forage n'a pu la confirmer.",
        ecart="source"),
    "NRJ-09": dict(
        resume="Un coefficient de 2,3 signifie 130 % de plus, pas 230 %. Il traduisait le rendement des centrales, "
               "et a été abaissé à 1,9 en 2026.",
        ecart="erreur",
        barres=_b("Supplément appliqué à l'électricité dans le DPE", "%",
                  ("Il annonce", "230", "dit"), ("Ce que donne un coefficient de 2,3", "130", "fait"))),
    "NRJ-10": dict(
        resume="La programmation pluriannuelle de l'énergie d'avril 2020 prévoyait bien l'arrêt de 14 réacteurs "
               "d'ici 2035."),
    "NRJ-11": dict(
        resume="RTE prévoit 37 Md€ pour les parcs mis en service d'ici 2039, et 10 Md€ de plus pour les suivants : "
               "le total est plutôt de 47 Md€."),
    "NRJ-12": dict(
        resume="Les six premiers EPR2 sont déjà engagés par le gouvernement actuel. Ce qui le distingue est surtout "
               "l'arrêt du soutien à l'éolien en mer. Coût non chiffré."),

    # ------------------------------------------------------------------ 12 Agriculture
    "AGRI-01": dict(
        resume="Selon les Douanes, le solde de 2025 reste très légèrement positif (+0,2 Md€). Il ne devient négatif "
               "qu'en comptant les produits de la mer.",
        ecart="perimetre"),
    "AGRI-02": dict(
        resume="Les importations ont été multipliées par 2,7 à 2,8 entre 2000 et 2022, en euros courants : une "
               "partie de la hausse vient des prix."),
    "AGRI-03": dict(
        resume="Le chiffre de 2025 et la hausse des importations sont exacts. Ses niveaux de 2022 et 2024 n'ont pas "
               "pu être recoupés au même périmètre, mais la chute qu'il décrit est réelle."),
    "AGRI-04": dict(
        resume="La surmortalité par suicide des exploitants est réelle et grave, mais elle est de 12 à 28 % "
               "au-dessus de la population générale : 1,1 à 1,3 fois, pas 7 fois.",
        ecart="gonfle",
        barres=_b("Risque de suicide des agriculteurs, par rapport à la population", "fois",
                  ("Il annonce", "7", "dit"), ("Estimation la plus haute", "1,3", "fait"),
                  ("Estimation la plus basse", "1,1", "fait"))),
    "AGRI-05": dict(
        resume="17,7 % des exploitants vivaient sous le seuil de pauvreté en 2020, contre 14,4 % pour l'ensemble de "
               "la population.",
        ecart="gonfle",
        barres=_b("Part sous le seuil de pauvreté, 2020", "%",
                  ("Il annonce (« presque »)", "40", "dit"), ("Exploitants agricoles", "17,7", "fait"),
                  ("Ensemble de la population", "14,4", "repere"))),
    "AGRI-06": dict(
        resume="Le revenu total de la branche a bien reculé de 35 à 48 % en trente ans. Mais il y a beaucoup moins "
               "d'agriculteurs : par actif, le revenu réel a augmenté de 22 à 51 %.",
        ecart="contexte"),
    "AGRI-07": dict(
        resume="La consommation est tombée à 1,82 million de tonnes en 2024. La part importée n'a pas été mesurée, "
               "et il donne lui-même deux chiffres différents.",
        ecart="source"),
    "AGRI-08": dict(
        resume="Aucune source publique ne compare ce ratio entre pays, et ses chiffres varient d'une prise de "
               "parole à l'autre.",
        ecart="source"),
    "AGRI-09": dict(
        resume="Le coût de la mesure n'est chiffré ni dans ses textes ni ici."),

    # ------------------------------------------------------------------ 13 Europe et international
    "EUR-01": dict(
        resume="En pouvoir d'achat, le PIB par habitant de la France est passé sous la moyenne de l'UE en 2022, "
               "pour la première fois depuis le début de la série en 1995."),
    "EUR-02": dict(
        resume="France et Italie étaient à égalité en 2022. La France est repassée devant d'un point en 2023 et en "
               "2024.",
        ecart="erreur",
        barres=_b("PIB par habitant en pouvoir d'achat, 2024 (UE = 100)", "",
                  ("France", "99", "fait"), ("Italie", "98", "repere"))),
    "EUR-03": dict(
        resume="La France est bien 27e en 2024, mais elle était 13e en 1995, pas 7e. Le recul est réel ; il le fait "
               "paraître deux fois plus fort.",
        ecart="gonfle"),
    "EUR-04": dict(
        resume="Le rapport Draghi écrit bien qu'environ 70 % de l'écart de PIB par habitant avec les États-Unis "
               "s'explique par une productivité plus faible."),
    "EUR-05": dict(
        resume="57 Md€ représentent 1,9 % du PIB de 2025, et 2,05 % avec la définition plus large de l'OTAN."),
    "EUR-06": dict(
        resume="Le déficit est de 375 Md€ en 2025, mais ce n'est pas un record : celui de 2022 était de 398 Md€.",
        ecart="superlatif",
        barres=_b("Déficit commercial de l'UE avec la Chine", "Md€",
                  ("2025, il annonce (« record »)", "360", "dit"), ("2025", "375", "fait"),
                  ("2022, le record", "398", "fait"), ("2023", "300", "fait"))),

    # ------------------------------------------------------------------ 14 Institutions, référendum et normes
    "INS-01": dict(
        resume="L'étude AMF-Cevipof compte 40 démissions par mois, et 3,2 fois plus qu'en 2008-2014, pas 4 fois. Le "
               "phénomène est réel et inédit.",
        ecart="arrondi",
        barres=_b("Démissions de maires par mois depuis 2020", "",
                  ("Il annonce", "42", "dit"), ("Étude AMF-Cevipof", "40", "fait"))),
    "INS-02": dict(
        resume="Les indicateurs officiels du Secrétariat général du Gouvernement n'ont pas pu être téléchargés le "
               "jour de l'analyse.",
        ecart="inaccessible"),
    "INS-03": dict(
        resume="Les ordres de grandeur sont ceux couramment publiés, mais les sources officielles étaient "
               "indisponibles le jour de l'analyse.",
        ecart="inaccessible"),
    "INS-04": dict(
        resume="Un choix politique : faire primer la loi sur un traité suppose de réviser la Constitution et "
               "mettrait la France en contradiction avec ses engagements, sauf à les dénoncer ou les renégocier."),

    # ------------------------------------------------------------------ 15 Culture, numérique et IA
    "NUM-01": dict(
        resume="Traduction exacte d'une phrase du rapport Draghi, à une nuance près : il s'agit d'entreprises "
               "« créées à partir de rien »."),
    "NUM-02": dict(
        resume="Stanford AI Index 2026 : 285,9 Md$ aux États-Unis, contre 12,4 Md$ en Chine.",
        barres=_b("Investissement privé dans l'IA, 2025", "Md$",
                  ("États-Unis, il annonce", "286", "dit"), ("États-Unis", "285,9", "fait"),
                  ("Europe", "20,9", "repere"), ("Chine", "12,4", "repere"))),
    "NUM-03": dict(
        resume="Le chiffre vient d'un classement australien dont le site a refusé l'accès. Il repose sur les "
               "publications scientifiques, pas sur la production industrielle.",
        ecart="inaccessible"),
    "NUM-04": dict(
        resume="Selon l'étude BCG-SIA, 92 % de la capacité de production la plus avancée se trouvait à Taïwan en "
               "2019. Les données ont sept ans."),
    "CULT-01": dict(
        resume="La statistique publique donne 196 € par habitant en Île-de-France contre 21 € ailleurs : un écart "
               "de 9 à 1, pas de 33 à 1, dû surtout aux grands établissements nationaux.",
        ecart="gonfle",
        barres=_b("Dépenses du ministère de la Culture", "€ par habitant",
                  ("Paris, il annonce", "801", "dit"), ("Île-de-France (2018)", "196", "fait"),
                  ("Province, il annonce", "24", "dit"), ("Hors Île-de-France (2018)", "21", "fait"))),
    "CULT-02": dict(
        resume="Un choix d'organisation du gouvernement, sans coût chiffré."),

    # ------------------------------------------------------------------ 16 Cannes, bilan municipal
    "CAN-01": dict(
        resume="La dette a baissé de 81,3 M€ entre fin 2013 et fin 2025, plus que ce qu'il annonçait. Elle avait "
               "toutefois plus que doublé de 2001 à 2008, quand il était premier adjoint.",
        barres=_b("Baisse de la dette depuis fin 2013", "M€",
                  ("Il annonce (prévision pour fin 2025)", "77,5", "dit"), ("À fin 2024", "76,1", "fait"),
                  ("À fin 2025", "81,3", "fait"))),
    "CAN-02": dict(
        resume="Le calcul est juste, mais 2014 est le point le plus bas de la période. Sur des moyennes de trois "
               "ans, la progression est de 2,8 fois.",
        ecart="contexte",
        barres=_b("Progression de l'épargne nette de la ville", "fois",
                  ("Il annonce (2014 à 2024)", "10", "dit"), ("De 2014 à 2024", "10,1", "fait"),
                  ("Sur des moyennes de trois ans", "2,8", "fait"))),
    "CAN-03": dict(
        resume="Les taux communaux n'ont pas bougé de 2014 à 2024, hors transfert mécanique de la part "
               "départementale en 2021, puis ont baissé de 3,6 % en 2025."),
    "CAN-04": dict(
        resume="L'ordre de grandeur est le sien, mais 2014 est un point haut et les dépenses remontent depuis 2023.",
        ecart="contexte",
        barres=_b("Baisse des charges de fonctionnement", "M€",
                  ("Il annonce (depuis 2014)", "65,9", "dit"), ("De 2014 à 2023", "63,5", "fait"),
                  ("De 2013 à 2023", "52,5", "fait"))),
    "CAN-05": dict(
        resume="Insee : 21,0 % à Cannes, contre 14,9 % en France métropolitaine.",
        barres=_b("Taux de pauvreté, 2021", "%",
                  ("Cannes, il annonce", "21", "dit"), ("Cannes", "21,0", "fait"),
                  ("France, il annonce", "14", "dit"), ("France métropolitaine", "14,9", "fait"))),
    "CAN-06": dict(
        resume="Il ne précise pas ce qu'il compte. Pour la seule dotation globale de fonctionnement, on trouve "
               "environ 102 M€ de baisse cumulée.",
        ecart="source"),
}
