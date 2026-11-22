"""Mélenchon, thème 14 — Institutions, référendum et normes : calculs à partir de brut/.

python -m verification melenchon calculer 14   → calculs/resultats.csv
"""
import pandas as pd

from verification.commun.calculs import Calculs

FICHE = "assemblee/fiche_64_responsabilite_gouvernement.pdf"
LUS = {
    "xv_xvi": (FICHE, "à une reprise sous la XVe législature, et à 23 reprises sous la XVI e législature", 24),
    "barnier": (FICHE, "le Premier ministre Michel Barnier a engagé la responsabilité de son Gouvernement, en "
                "application de l’article 49, alinéa 3", 1),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    total = C.v("xv_xvi") + C.v("barnier")
    C.res("INST-01", "juin 2017 → décembre 2024", "Recours à l'article 49, alinéa 3 (décompte de l'Assemblée)", total,
          "recours", "2024", "AN-FICHE-64", "M1", "32 depuis 2017",
          "1 sous la XVe législature, 23 sous la XVIe, 1 (Barnier) sous la XVIIe ; recours de 2025 et 2026 non décomptés "
          "dans la fiche", 0)
    d = pd.read_excel(C.brut / "interieur/referendum_2005.xls", sheet_name="Départements", header=None, skiprows=4)
    d = d[pd.to_numeric(d[2], errors="coerce").notna()]
    oui, non = d[8].astype(float).sum(), d[11].astype(float).sum()
    C.res("INST-02", "29 mai 2005, tous les départements du fichier", "Part du « non » parmi les suffrages exprimés",
          non / (oui + non) * 100, "%", "2005", "INTERIEUR-REFERENDUM-2005", "M2", "55 %",
          f"{non:.0f} non, {oui:.0f} oui", 2)
    C.ecrire()


if __name__ == "__main__":
    main()
