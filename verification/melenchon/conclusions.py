"""Couche de lecture des pages de Jean-Luc Mélenchon sur le site commun (python -m verification site) : pour chaque affirmation, la
conclusion en une phrase, le type d'écart avec les données et, quand un chiffre se compare directement, un petit
graphique à barres. Même format et mêmes contrôles que verification/conclusions.py (David Lisnard) ; les types d'écart
(ECARTS) sont communs.

Rien ici n'ajoute de fait : tout est repris de donnees/verification/melenchon/themes/<thème>/analyse.md.
"""
from verification.conclusions import ECARTS  # noqa: F401  (communs à toutes les personnes)

# Phrase d'accroche de chaque thème (page d'accueil et haut de la page du thème).
ACCROCHES = {
    "01": "Les ordres de grandeur sur la dette et le déficit sont bons ; les imprécisions tiennent aux périmètres.",
    "02": "Des chiffres de l'OFDT fidèlement repris sur le tabac et le cannabis.",
    "09": "La retraite à 60 ans pour 40 annuités défait deux réformes : âge légal et durée de cotisation.",
    "14": "Juste sur le référendum de 2005 ; le décompte des 49.3 n'est pas vérifiable au-delà de 2024.",
    "03": "Une description juste, mais incomplète, du droit du sol actuel.",
    "12": "Une mesure très ambitieuse : 72 % d'emplois agricoles en plus.",
    "04": "La part de l'État dans le PIB a bien baissé, mais trois à six fois moins qu'il ne le dit.",
    "05": "Les retraités sont nombreux parmi les maires, mais bien moins que les 80 % annoncés.",
    "15": "Le constat d'orbites encombrées est juste, mais le nombre de gros débris est multiplié par quinze.",
    "06": "Ses chiffres sur les salaires, les prix et les morts au travail tiennent ; deux comparaisons sont fausses.",
    "07": "La baisse des lits est même plus forte qu'il ne le dit ; déserts médicaux et cancers évitables sont "
          "grossis.",
    "08": "Juste sur le poids des filières professionnelles ; faux sur l'illettrisme, qui touche plus les hommes.",
    "10": "Des chiffres proches des sources, mais lus de façon plus alarmante qu'ils ne le disent.",
    "11": "Justes sur la flambée du gaz et des marges de raffinage ; faux sur le prix des carburants au temps des "
          "gilets jaunes.",
    "13": "Des ordres de grandeur justes sur le poids de la France en Europe et la dette américaine.",
    "17": "Des chiffres de l'Insee justes sur la pauvreté, parfois arrondis vers le haut ; l'aide alimentaire est "
          "très surestimée.",
    "19": "Deux chiffres exacts, dont l'écart de salaire de 22 %, qui tient surtout au temps de travail.",
    "18": "Fidèle à l'inventaire forestier ; deux des quatre records de chaleur annoncés n'en sont pas.",
}

# Graphiques produits par calculs/calculer.py : affirmation → (fichier de calculs/graphiques/, légende).
FIGURES = {}


def _b(titre: str, unite: str, *lignes: tuple) -> dict:
    return {"titre": titre, "unite": unite, "lignes": lignes}


LECTURE = {
    # ------------------------------------------------------------------ 01 Dette, dépense publique et fiscalité
    "DETTE-01": dict(
        resume="Le Sénat donne deux estimations pour 2023 : 211 Md€ et 108 Md€. Le chiffre bas n'est pas 120 Md€.",
        ecart="arrondi",
        barres=_b("Aides publiques aux entreprises en 2023", "Md€",
                  ("Il annonce, chiffre haut", "210", "dit"), ("Sénat, estimation large", "211", "fait"),
                  ("Il annonce, chiffre bas", "120", "dit"), ("Sénat, estimation restreinte", "108", "fait"))),
    "DETTE-02": dict(
        resume="151,6 Md€ pour l'ensemble des administrations en 2025, 130,3 Md€ pour l'État seul.",
        ecart="perimetre",
        barres=_b("Déficit public en 2025", "Md€",
                  ("Il annonce", "150", "dit"), ("Toutes les administrations", "151,6", "fait"),
                  ("État seul", "130,3", "fait"))),
    "DETTE-03": dict(
        resume="Patrimoine net des administrations : +811 Md€, soit 11 729 € par habitant ; l'État seul n'est pas "
               "vérifié.",
        ecart="perimetre"),
    "DETTE-04": dict(
        resume="Grèce, Italie, France, Belgique, Espagne : 49 % du PIB de la zone euro.",
        barres=_b("Poids des cinq pays endettés à plus de 100 %, 2025", "%",
                  ("Il annonce", "50", "dit"), ("Dans la zone euro", "49,4", "fait"), ("Dans l'UE", "41,5", "fait"))),
    "DETTE-05": dict(
        resume="110 % du PIB était la dette grecque de 2008, pas son déficit (10,3 %).",
        ecart="perimetre"),
    "DETTE-06": dict(
        resume="25 % est le taux normal légal ; les plus grandes entreprises paient en 2025 environ 35 % avec la "
               "contribution exceptionnelle.",
        ecart="contexte"),
    "DETTE-07": dict(
        resume="Le barème compte bien cinq tranches (de 0 % à 45 %) ; les 14 tranches proposées ne sont pas détaillées "
               "ici."),
    # ------------------------------------------------------------------ 02 Sécurité, justice et narcotrafic
    "SECU-01": dict(
        resume="23,1 % de fumeurs quotidiens et 900 000 usagers quotidiens de cannabis : les chiffres de l'OFDT ; le "
               "7 % d'alcool n'est pas confirmé.",
        ecart="arrondi"),
    # ------------------------------------------------------------------ 03 Immigration, islamisme et identité
    "IMMI-01": dict(
        resume="18 ans de plein droit et 16 ans sur demande, c'est juste ; il oublie la demande possible dès 13 ans.",
        ecart="contexte"),
    # ------------------------------------------------------------------ 04 Bureaucratie, normes et réforme de l'État
    "ETAT-01": dict(
        resume="−0,7 point de PIB pour l'ensemble des salaires publics depuis 2004, −1,0 pour l'État : pas −6.",
        ecart="gonfle",
        barres=_b("Recul de la rémunération des salariés publics, 2004 → 2024", "points de PIB",
                  ("Il annonce", "6", "dit"), ("État", "1,0", "fait"), ("Toutes les administrations", "0,7", "fait"))),
    "ETAT-02": dict(
        resume="−2,2 points pour l'État depuis 2004, et +3,0 points pour l'ensemble des administrations.",
        ecart="gonfle",
        barres=_b("Recul de la dépense de l'État, 2004 → 2024", "points de PIB",
                  ("Il annonce", "7", "dit"), ("État", "2,2", "fait"))),
    # ------------------------------------------------------------------ 05 Décentralisation et collectivités
    "DEC-01": dict(
        resume="53,7 % des maires ont 60 ans ou plus et 36,2 % sont retraités : loin des 80 %.",
        ecart="gonfle",
        barres=_b("Maires élus en 2026", "%",
                  ("Il annonce", "80", "dit"), ("60 ans ou plus", "53,7", "fait"), ("Retraités", "36,2", "fait"))),
    # ------------------------------------------------------------------ 06 Économie, travail et entreprises
    "ECO-01": dict(
        resume="Exact pour l'Espagne, le Portugal et l'Allemagne ; la hausse française est de 24 %, pas 27 %.",
        ecart="arrondi",
        barres=_b("Hausse du salaire minimum brut, 2016 → 2026", "%",
                  ("France, il annonce", "27", "dit"), ("France", "24,3", "fait"),
                  ("Espagne, il annonce", "86,5", "dit"), ("Espagne", "86,5", "fait"),
                  ("Portugal", "73,6", "fait"), ("Allemagne", "62,3", "fait"))),
    "ECO-02": dict(
        resume="2,6 % en 2025 (10e de l'UE) et 3,7 % en 2024 (5e) : l'Espagne n'est pas en tête.",
        ecart="superlatif",
        barres=_b("Croissance du PIB en 2025", "%",
                  ("Espagne, il annonce", "3,8", "dit"), ("Espagne", "2,6", "fait"), ("Irlande", "8,0", "repere"),
                  ("Pologne", "3,8", "repere"))),
    "ECO-03": dict(
        resume="Environ 5 chômeurs par emploi vacant en 2025 (8,5 en ne comptant que les entreprises de 10 salariés "
               "ou plus).",
        ecart="gonfle",
        barres=_b("Chômeurs par emploi vacant, 2025", "chômeurs",
                  ("Il annonce", "17", "dit"), ("Toutes entreprises", "5,2", "fait"),
                  ("Entreprises de 10 salariés ou plus", "8,5", "fait"))),
    "ECO-04": dict(
        resume="Les CDD font 84 % des déclarations d'embauche hors intérim ; les CDD de moins d'un mois, 69 %.",
        ecart="arrondi",
        barres=_b("Part des embauches en 2025", "%",
                  ("Il annonce", "87", "dit"), ("Tous CDD", "83,7", "fait"), ("CDD de moins d'un mois", "69,3",
                                                                              "fait"))),
    "ECO-05": dict(
        resume="En 2025, la production industrielle reste 3,8 % sous son niveau de 2019."),
    "ECO-06": dict(
        resume="33e sur 190 dans le dernier classement (17 % de tête), un classement arrêté en 2021.",
        ecart="date"),
    "ECO-07": dict(
        resume="Premier de l'UE en nombre (830 en 2024) et en taux d'accidents mortels, avec des pratiques de "
               "déclaration qui diffèrent d'un pays à l'autre.",
        barres=_b("Accidents du travail mortels en 2024", "décès",
                  ("France", "830", "fait"), ("Italie", "482", "repere"))),
    "ECO-08": dict(
        resume="979 décès d'accidents du travail et de maladies professionnelles en 2024, 1 295 avec les trajets.",
        barres=_b("Décès liés au travail reconnus en 2024", "décès",
                  ("Il annonce", "1 000", "dit"), ("Accidents du travail", "764", "fait"),
                  ("Avec les maladies professionnelles", "979", "fait"), ("Avec les trajets", "1 295", "fait"))),
    "ECO-09": dict(
        resume="+34 % depuis mai 2017, +26 % depuis 2021 : juste depuis l'arrivée de Macron, qu'il vise.",
        ecart="contexte",
        barres=_b("Hausse des prix de l'alimentation jusqu'en août 2026", "%",
                  ("Il annonce", "30", "dit"), ("Depuis mai 2017", "34,4", "fait"), ("Depuis janvier 2021", "25,8",
                                                                                     "fait"))),
    "ECO-10": dict(
        resume="Consommation des ménages : 52 % du PIB, 54 % avec les associations ; 55 % est un arrondi vers le haut.",
        ecart="arrondi"),
    "ECO-11": dict(
        resume="L'Allemagne en est déjà à 449 robots pour 10 000 salariés ; l'objectif de 400 est sous son niveau "
               "actuel."),
    "ECO-12": dict(
        resume="Le SMIC net est d'environ 1 441 € en 2026 : 1 700 € net, c'est une hausse d'environ 18 %."),
    # ------------------------------------------------------------------ 07 Santé et hôpital
    "SANTE-01": dict(
        resume="98 198 lits publics en moins de 1999 à 2024, dont une bonne part de lits de long séjour devenus des "
               "places d'Ehpad.",
        ecart="contexte",
        barres=_b("Lits perdus par l'hôpital public en vingt-cinq ans", "lits",
                  ("Il annonce", "80 000", "dit"), ("1999 → 2024", "98 198", "fait"))),
    "SANTE-02": dict(
        resume="18,2 % de la population en zone sous-dense au seuil de la DREES ; 31,7 % avec un seuil plus large.",
        ecart="gonfle",
        barres=_b("Population en zone sous-dense en généralistes, 2024", "%",
                  ("Il annonce", "33", "dit"), ("Seuil de la DREES", "18,2", "fait"),
                  ("Seuil plus large", "31,7", "fait"))),
    "SANTE-03": dict(
        resume="41 % des cancers sont évitables, surtout par le tabac, l'alcool et l'alimentation ; l'environnement "
               "au sens strict en explique 1,7 %.",
        ecart="perimetre",
        barres=_b("Part des cancers évitables", "%",
                  ("Il annonce, par l'environnement", "40", "dit"), ("Tous facteurs", "41", "fait"),
                  ("Environnement au sens large", "9,3", "fait"), ("Pollution, chimie, radon", "1,7", "fait"))),
    # ------------------------------------------------------------------ 08 École et enseignement
    "ECOLE-01": dict(
        resume="37 % d'une génération a un bac technologique ou professionnel, 57 % n'a pas de bac général : 50 % "
               "est entre les deux.",
        ecart="arrondi",
        barres=_b("Part d'une génération en 2025", "%",
                  ("Il annonce", "50", "dit"), ("Bacheliers technologiques et professionnels", "36,9", "fait"),
                  ("Sans baccalauréat général", "56,7", "fait"))),
    "ECOLE-02": dict(
        resume="2,5 millions d'adultes illettrés selon l'Insee, et les hommes sont plus touchés que les femmes.",
        ecart="erreur"),
    # ------------------------------------------------------------------ 09 Retraites et protection sociale
    "RET-01": dict(
        resume="L'âge légal va aujourd'hui de 62 ans et 9 mois à 64 ans, et le taux plein demande jusqu'à 43 ans de "
               "cotisation.",
        barres=_b("Durée de cotisation pour le taux plein", "trimestres",
                  ("Il propose", "160", "dit"), ("Nés à partir de 1966", "172", "fait"))),
    # ------------------------------------------------------------------ 10 Logement et urbanisme
    "LOG-01": dict(
        resume="2,76 millions de demandes fin 2024 selon le ministère : le chiffre est juste, mais ce sont des ménages.",
        ecart="perimetre"),
    "LOG-02": dict(
        resume="350 000 est le nombre de sans-domicile, dont la plupart sont hébergés, pas « à la rue ».",
        ecart="perimetre"),
    "LOG-03": dict(
        resume="98 682 logements sociaux financés en 2024 : l'objectif double le rythme actuel.",
        barres=_b("Logements sociaux financés par an", "logements",
                  ("Il propose", "200 000", "dit"), ("2023", "91 208", "fait"), ("2024", "98 682", "fait"))),
    # ------------------------------------------------------------------ 11 Énergie et nucléaire
    "NRJ-01": dict(
        resume="+144 % de mai 2017 à août 2026, +153 % jusqu'en septembre, contre +27 % pour l'ensemble des prix.",
        barres=_b("Hausse des prix depuis mai 2017", "%",
                  ("Gaz, il annonce", "150", "dit"), ("Gaz, jusqu'en août 2026", "144,4", "fait"),
                  ("Ensemble des prix", "26,7", "repere"))),
    "NRJ-02": dict(
        resume="Pendant les gilets jaunes, le plus haut était 1,57 € ; les 2 € n'ont été dépassés qu'en 2022.",
        ecart="erreur",
        barres=_b("Prix le plus haut d'une semaine, octobre 2018 → mars 2019", "€/l",
                  ("Il annonce", "2", "dit"), ("Gazole", "1,533", "fait"), ("Essence SP95", "1,574", "fait"),
                  ("Gazole, septembre 2026", "2,325", "repere"))),
    "NRJ-03": dict(
        resume="La marge de raffinage du ministère a été multipliée par 7,6 depuis janvier, par 6 depuis février.",
        ecart="contexte",
        barres=_b("Marge brute de raffinage sur Brent", "€/t",
                  ("Janvier 2026", "32", "repere"), ("Février 2026", "41", "repere"), ("Août 2026", "246", "fait"))),
    "NRJ-04": dict(
        resume="1,70 € est bien le prix de février 2026 ; y revenir, c'est baisser le gazole de 27 %.",
        barres=_b("Prix du gazole", "€/l",
                  ("Il propose", "1,70", "dit"), ("Février 2026", "1,672", "fait"), ("Septembre 2026", "2,325",
                                                                                  "fait"))),
    "NRJ-05": dict(
        resume="Les renouvelables font 24 % de la consommation d'énergie ; le nucléaire, 67 % de l'électricité."),
    # ------------------------------------------------------------------ 12 Agriculture
    "AGRI-01": dict(
        resume="Le secteur emploie 691 000 personnes : 500 000 de plus, c'est +72 %.",
        barres=_b("Emploi dans l'agriculture, la sylviculture et la pêche", "milliers",
                  ("2000", "932", "repere"), ("2025", "691", "fait"), ("Avec la mesure", "1 191", "dit"))),
    # ------------------------------------------------------------------ 13 Europe et international
    "EUR-01": dict(
        resume="18,8 % du PIB de la zone euro, 15,8 % de celui de l'UE ; la Grèce pèse 1,6 % et 1,3 %.",
        ecart="perimetre",
        barres=_b("Part dans le PIB de la zone euro, 2025", "%",
                  ("France, il annonce", "18", "dit"), ("France", "18,8", "fait"), ("France, dans l'UE", "15,8", "fait"),
                  ("Grèce", "1,6", "fait"))),
    "EUR-02": dict(
        resume="La dette fédérale américaine atteint 40,09 milliers de milliards de dollars le 16 septembre 2026."),
    "EUR-03": dict(
        resume="La France est à 2,05 % du PIB ; 5 % coûterait environ 88 Md€ de plus par an."),
    # ------------------------------------------------------------------ 14 Institutions, référendum et normes
    "INST-01": dict(
        resume="25 recours au 49.3 de 2017 à fin 2024 selon l'Assemblée ; ceux de 2025 et 2026 ne sont pas encore "
               "décomptés.",
        ecart="inaccessible"),
    "INST-02": dict(
        resume="54,67 % de « non » au référendum du 29 mai 2005.",
        ecart="arrondi"),
    # ------------------------------------------------------------------ 15 Culture, numérique, IA (et espace)
    "CULT-01": dict(
        resume="L'Agence spatiale européenne compte 68 450 objets de plus de 10 cm, pas un million.",
        ecart="gonfle",
        barres=_b("Objets de plus de 10 cm en orbite, 2026", "objets",
                  ("Il annonce", "1 000 000", "dit"), ("Agence spatiale européenne", "68 450", "fait"))),
    # ------------------------------------------------------------------ 17 Inégalités, pauvreté et grandes fortunes
    "INEG-01": dict(
        resume="De 8,89 à 9,82 millions de personnes pauvres entre 2017 et 2024 : 0,93 million de plus.",
        barres=_b("Personnes pauvres en plus, 2017 → 2024", "millions",
                  ("Il annonce", "1", "dit"), ("Insee", "0,93", "fait"))),
    "INEG-02": dict(
        resume="15,4 % : le plus haut depuis 1996, mais le taux était de 17,0 % en 1975.",
        ecart="superlatif",
        barres=_b("Taux de pauvreté", "%",
                  ("1975", "17,0", "repere"), ("1996", "15,3", "repere"), ("2024", "15,4", "fait"))),
    "INEG-03": dict(
        resume="9,82 millions de personnes pauvres en 2024 : ni « plus de 10 millions », ni « 9 millions ».",
        ecart="arrondi"),
    "INEG-04": dict(
        resume="L'Insee estime les bénéficiaires de l'aide alimentaire entre 2 et 4 millions par an.",
        ecart="gonfle",
        barres=_b("Bénéficiaires de l'aide alimentaire sur une année", "millions",
                  ("Il annonce", "8", "dit"), ("Insee, haut de la fourchette", "4", "fait"))),
    "INEG-05": dict(
        resume="Environ 7,9 millions de personnes ne peuvent pas chauffer leur logement : deux fois plus que son "
               "chiffre.",
        ecart="erreur",
        barres=_b("Personnes ne pouvant pas chauffer leur logement, 2025", "millions",
                  ("Il annonce", "4", "dit"), ("Enquête européenne", "7,9", "fait"))),
    "INEG-06": dict(
        resume="Le SMIC net à temps plein dépasse le seuil de pauvreté d'une personne seule d'environ 4,5 %."),
    "INEG-07": dict(
        resume="1 337 € est bien le seuil de pauvreté de 2024 ; le coût de la garantie n'est pas chiffré ici."),
    # ------------------------------------------------------------------ 18 Climat, eau et environnement
    "CLIM-01": dict(
        resume="2023 et 2024 ont battu le record ; 2020 est restée juste sous 2016 et 2025 n'est que troisième.",
        ecart="superlatif",
        barres=_b("Écart de température mondiale à la moyenne 1991-2020", "°C",
                  ("2016", "0,438", "fait"), ("2020", "0,430", "fait"), ("2023", "0,603", "fait"),
                  ("2024", "0,719", "fait"), ("2025", "0,592", "fait"))),
    "CLIM-02": dict(
        resume="−33 % depuis 1990 ; atteindre −65 % en 2033 demande −7 % par an, trois fois le rythme récent.",
        barres=_b("Baisse annuelle des émissions", "% par an",
                  ("Nécessaire de 2024 à 2033", "7,0", "dit"), ("Observée de 2014 à 2024", "2,2", "fait"))),
    "CLIM-03": dict(
        resume="32 % du territoire boisé et mortalité des arbres +125 % : les chiffres de l'IGN."),
    # ------------------------------------------------------------------ 19 Égalité femmes-hommes et discriminations
    "EGAL-01": dict(
        resume="21,8 % d'écart de revenu salarial dans le privé en 2024 ; 14,0 % à temps de travail égal.",
        ecart="contexte",
        barres=_b("Écart de salaire femmes-hommes, secteur privé, 2024", "%",
                  ("Il annonce", "22", "dit"), ("Revenu salarial", "21,8", "fait"),
                  ("À temps de travail égal", "14,0", "fait"))),
    "EGAL-02": dict(
        resume="5e en 2017, 15e sur 49 en 2026 dans le classement d'ILGA-Europe."),
}
