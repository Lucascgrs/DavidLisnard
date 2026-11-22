"""Catalogue commun des thèmes : mêmes numéros, mêmes noms de dossier et mêmes intitulés pour toutes les personnes.

C'est la clé de la comparaison entre candidats : le thème 06 de David Lisnard et le thème 06 de Jean-Luc Mélenchon
portent sur le même sujet, dans des dossiers du même nom (verification/<…>/themes/06_economie_travail/,
donnees/verification/<…>/themes/06_economie_travail/). Un sujet qui n'entre dans aucun thème existant reçoit un
nouveau numéro, à la suite (17, 18…), pour toutes les personnes ; une personne n'a pas forcément tous les thèmes
(le bilan municipal de Cannes n'existe que pour David Lisnard).

python -m verification themes   → tableau des thèmes et des personnes vérifiées sur chacun
"""
from .personnes import PERSONNES

# numéro → (dossier, intitulé, ce que couvre le thème)
CATALOGUE = {
    "01": ("01_dette_depense_fiscalite", "Dette, dépense publique et fiscalité",
           "dette et déficit, niveau de dépense, impôts et prélèvements, aides aux entreprises, fiscalité du "
           "patrimoine"),
    "02": ("02_securite_justice", "Sécurité, justice et narcotrafic",
           "délinquance, police, prisons, justice, drogues"),
    "03": ("03_immigration_identite", "Immigration, islamisme et identité",
           "titres de séjour, asile, régularisations, nationalité, laïcité"),
    "04": ("04_bureaucratie_etat", "Bureaucratie, normes et réforme de l'État",
           "organisation de l'État, agences, fonctionnaires, normes, services publics"),
    "05": ("05_decentralisation", "Décentralisation et collectivités",
           "communes, départements, finances locales"),
    "06": ("06_economie_travail", "Économie, travail et entreprises",
           "croissance, emploi, salaires et prix, temps de travail, industrie, profits"),
    "07": ("07_sante_hopital", "Santé et hôpital", "hôpital, médecins, accès aux soins, assurance maladie"),
    "08": ("08_ecole", "École et enseignement",
           "école, enseignants, niveau des élèves, enseignement supérieur, Parcoursup"),
    "09": ("09_retraites", "Retraites et protection sociale", "retraites, assurance chômage, minima sociaux"),
    "10": ("10_logement", "Logement et urbanisme", "construction, loyers, logement social, logements vacants"),
    "11": ("11_energie", "Énergie et nucléaire", "électricité, nucléaire, renouvelables, carburants, prix de l'énergie"),
    "12": ("12_agriculture", "Agriculture", "agriculteurs, revenus, échanges agricoles, alimentation"),
    "13": ("13_europe_international", "Europe et international",
           "Union européenne, défense, guerres, diplomatie, commerce mondial"),
    "14": ("14_institutions", "Institutions, référendum et normes",
           "Constitution, élections, référendum, Parlement, démocratie"),
    "15": ("15_culture_numerique_ia", "Culture, numérique et intelligence artificielle",
           "culture, médias, numérique, intelligence artificielle, espace"),
    "16": ("16_cannes_bilan", "Cannes : bilan municipal", "le bilan de David Lisnard maire de Cannes"),
    # Thèmes ajoutés avec Jean-Luc Mélenchon (novembre 2026)
    "17": ("17_inegalites_pauvrete", "Inégalités, pauvreté et grandes fortunes",
           "pauvreté, inégalités de revenu et de patrimoine, milliardaires, dividendes"),
    "18": ("18_climat_environnement", "Climat, eau et environnement",
           "émissions de gaz à effet de serre, réchauffement, eau, pollutions, biodiversité"),
    "19": ("19_egalite_discriminations", "Égalité femmes-hommes et discriminations",
           "écarts de salaire, violences faites aux femmes, racisme et discriminations"),
}


def intitule(numero_ou_dossier: str) -> str:
    n = numero_ou_dossier.split("_")[0].zfill(2)
    return CATALOGUE[n][1]


def dossier(numero: str | int) -> str:
    return CATALOGUE[str(numero).zfill(2)][0]


def couverture() -> dict[str, list[str]]:
    """{numéro: [clés des personnes qui ont ce thème (affirmations.csv présent)]}."""
    out = {n: [] for n in CATALOGUE}
    for p in PERSONNES.values():
        for n, (d, _, _) in CATALOGUE.items():
            if (p.themes / d / "affirmations.csv").exists():
                out[n].append(p.cle)
    return out


def tableau() -> str:
    cov = couverture()
    cles = list(PERSONNES)
    lignes = ["  ".join(["n° ", f"{'thème':48}"] + [f"{c:10}" for c in cles])]
    for n, (_, nom, _) in CATALOGUE.items():
        lignes.append("  ".join([n + " ", f"{nom:48}"] + [f"{'oui' if c in cov[n] else '—':10}" for c in cles]))
    return "\n".join(lignes)
