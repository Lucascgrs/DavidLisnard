"""Mélenchon, thème 2 — Sécurité, justice et narcotrafic : calculs à partir de brut/.

python -m verification melenchon calculer 2   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

OFDT = "ofdt/drogues_addictions_chiffres_cles_2025.pdf"
LUS = {
    "tabac": (OFDT, "23,1 % des 18-75 ans ont un usage quotidien de tabac", 23.1),
    "cannabis": (OFDT, "dont 1,4 M dont 900 000 usagers quotidiens", 900000),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("SECU-01", "18-75 ans, 2023", "Usage quotidien de tabac", C.v("tabac"), "%", "2023", "OFDT-CHIFFRES-CLES-2025",
          "M1", "23,1 %", "", 1)
    C.res("SECU-01", "adultes", "Usagers quotidiens de cannabis", C.v("cannabis"), "personnes", "2023",
          "OFDT-CHIFFRES-CLES-2025", "M1", "900 000", "", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
