"""Mélenchon, thème 10 — Logement et urbanisme : calculs à partir de brut/.

python -m verification melenchon calculer 10   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

BDT, FPL = "presse/bdt_logements_sociaux_2024.html", "fondation_logement/etre_humain_130.pdf"
LUS = {
    "demandes_2024": (BDT, "Au 31 décembre 2024, quelque 2,76 millions de ménages avaient fait une demande de logement "
                      "social", 2.76),
    "finances_2024": (BDT, "98.682 logements sociaux ont été financés par l’État en 2024", 98682),
    "finances_2023": (BDT, "En 2023, le bilan s’élevait à 91.208 logements", 91208),
    "npnru_2024": (BDT, "dont 13.301 reconstitués dans le cadre du Nouveau Programme national de rénovation urbaine",
                   13301),
    "attente_fpl": (FPL, "2,9 MILLIONS de ménages sont en attente d’un logement social", 2.9),
    "sans_domicile_fpl": (FPL, "350 000 personnes sont sans domicile", 350000),
    "definition": ("insee/definition_sans_domicile.html", "si la nuit précédente elle a eu recours à un service "
                   "d'hébergement ou si elle a dormi dans un lieu non prévu pour l'habitation", 0),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("LOG-01", "fin 2024, ministère", "Ménages demandeurs d'un logement social", C.v("demandes_2024"), "millions",
          "2024", "BDT-LOGEMENTS-SOCIAUX-2024", "M1", "2,8 millions de personnes ; près de 3 millions de ménages",
          "des ménages, pas des personnes", 2)
    C.res("LOG-01", "début 2026, Fondation pour le logement", "Ménages en attente d'un logement social",
          C.v("attente_fpl"), "millions", "2025", "FPL-ETRE-HUMAIN-130", "M1", "2,8 millions", "", 1)
    C.res("LOG-02", "début 2026, Fondation pour le logement", "Personnes sans domicile", C.v("sans_domicile_fpl"),
          "personnes", "2025", "FPL-ETRE-HUMAIN-130; INSEE-DEF-SANS-DOMICILE", "M2", "350 000 « à la rue »",
          "au sens de l'Insee : hébergées par un service d'hébergement ou dormant dans un lieu non prévu pour l'habitation",
          0)
    C.res("LOG-03", "2024", "Logements sociaux financés par l'État", C.v("finances_2024"), "logements", "2024",
          "BDT-LOGEMENTS-SOCIAUX-2024", "M3", "200 000 logements publics par an",
          f"dont {C.v('npnru_2024'):.0f} reconstitués en rénovation urbaine ; 200 000 = "
          f"{200000 / C.v('finances_2024'):.1f} fois le niveau de 2024", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
