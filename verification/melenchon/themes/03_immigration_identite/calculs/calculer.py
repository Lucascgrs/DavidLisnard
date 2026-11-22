"""Mélenchon, thème 3 — Immigration, islamisme et identité : calculs à partir de brut/.

python -m verification melenchon calculer 3   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

SP = "droit/service_public_F295_nationalite.html"
LUS = {
    "a_18": (SP, "Si vous êtes né en France de parents étrangers , vous obtenez la nationalité française à l'âge de "
             "18 ans", 18),
    "a_16": (SP, "vous pouvez demander la nationalité française par déclaration dès l'âge de 16 ans", 16),
    "a_13": (SP, "Avoir 13 ans ou 14 ans ou 15 ans", 13),
    "residence": (SP, "pendant une période continue ou discontinue de 5 ans ou plus depuis l'âge de 11 ans", 5),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("IMMI-01", "de plein droit", "Âge d'acquisition automatique de la nationalité", C.v("a_18"), "ans", "2026",
          "SP-NATIONALITE-NE-EN-FRANCE", "M1", "18 ans", "si résidence en France d'au moins 5 ans depuis 11 ans", 0)
    C.res("IMMI-01", "par déclaration de l'enfant", "Âge minimal d'une demande par l'enfant", C.v("a_16"), "ans",
          "2026", "SP-NATIONALITE-NE-EN-FRANCE", "M1", "16 ans", "", 0)
    C.res("IMMI-01", "par déclaration des parents", "Âge minimal d'une demande faite par les parents", C.v("a_13"),
          "ans", "2026", "SP-NATIONALITE-NE-EN-FRANCE", "M1", "", "résidence d'au moins 5 ans depuis 8 ans", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
