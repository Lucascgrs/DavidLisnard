"""Mélenchon, thème 5 — Décentralisation et collectivités : calculs à partir de brut/.

python -m verification melenchon calculer 5   → calculs/resultats.csv
"""
import pandas as pd

from verification.commun.calculs import Calculs

C = Calculs(__file__)
B = C.brut
DATE_DEBAT = pd.Timestamp("2026-08-27")


def main():
    d = pd.read_csv(B / "interieur/rne_maires_2026-11-20.csv", sep=";", dtype=str)
    naissance = pd.to_datetime(d["Date de naissance"], errors="coerce")
    age = (DATE_DEBAT - naissance).dt.days / 365.25
    csp = d["Libellé de la catégorie socio-professionnelle"].fillna("")
    retraite = csp.str.startswith(("Ancien", "Ancienne", "Retraité"))
    n = len(d)
    C.res("DEC-01", "maires en fonction", "Part des maires de 60 ans ou plus", (age >= 60).mean() * 100, "%", "2026",
          "RNE-MAIRES", "M1", "80 % ont la soixantaine et plus", f"{n} maires ; âge au jour du débat (27/08/2026)", 1)
    C.res("DEC-01", "maires en fonction", "Part des maires retraités (catégorie « ancien … »)", retraite.mean() * 100, "%",
          "2026", "RNE-MAIRES", "M1", "80 % sont partis en retraite", "", 1)
    C.res("DEC-01", "maires en fonction", "Part des maires de 60 ans ou plus et retraités",
          ((age >= 60) & retraite).mean() * 100, "%", "2026", "RNE-MAIRES", "M1", "80 %", "", 1)
    C.ecrire()


if __name__ == "__main__":
    main()
