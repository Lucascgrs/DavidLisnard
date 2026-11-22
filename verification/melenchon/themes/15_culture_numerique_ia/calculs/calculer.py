"""Mélenchon, thème 15 — Culture, numérique et intelligence artificielle (et espace) : calculs à partir de brut/.

python -m verification melenchon calculer 15   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

ESA = "esa/space_environment_report_2026.pdf"
LUS = {
    "plus_10cm": (ESA, "68,450 space objects greater than 10 cm (including approximately 11,300 active payloads)", 68450),
    "de_1_a_10cm": (ESA, "1.5 million space debris objects from 1 cm to 10 cm", 1.5e6),
    "de_1mm_a_1cm": (ESA, "230 million space debris objects from 1 mm to 1 cm", 230e6),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("CULT-01", "1er février 2026", "Objets en orbite de plus de 10 cm (modèle MASTER)", C.v("plus_10cm"), "objets",
          "2026", "ESA-ENVIRONNEMENT-SPATIAL-2026", "M1", "un million (puis « 10 millions »)",
          f"dont environ 11 300 satellites actifs ; il annonce {1e6 / C.v('plus_10cm'):.0f} fois plus", 0)
    C.res("CULT-01", "1er février 2026", "Débris de 1 à 10 cm", C.v("de_1_a_10cm") / 1e6, "millions", "2026",
          "ESA-ENVIRONNEMENT-SPATIAL-2026", "M1", "", "", 1)
    C.res("CULT-01", "1er février 2026", "Débris de 1 mm à 1 cm", C.v("de_1mm_a_1cm") / 1e6, "millions", "2026",
          "ESA-ENVIRONNEMENT-SPATIAL-2026", "M1", "128 millions « de moins d'un centimètre »", "", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
