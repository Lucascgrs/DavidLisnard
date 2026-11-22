"""Mélenchon, thème 12 — Agriculture : calculs à partir de brut/.

python -m verification melenchon calculer 12   → calculs/resultats.csv
"""
from verification.commun import lecture as L
from verification.commun.calculs import Calculs

C = Calculs(__file__)
B = C.brut


def main():
    e = L.eurostat(B / "eurostat/nama_10_a10_e_agriculture_fr.json").pivot_table(index="time", columns="na_item",
                                                                                   values="valeur")
    der = e.index.max()
    C.res("AGRI-01", der, "Emploi dans l'agriculture, la sylviculture et la pêche", e.loc[der, "EMP_DC"], "milliers",
          der, "EUROSTAT-EMPLOI-AGRICOLE", "M1", "500 000 emplois agricoles en plus",
          f"dont {e.loc[der, 'SAL_DC']:.0f} milliers de salariés ; +500 000 = "
          f"+{500 / e.loc[der, 'EMP_DC'] * 100:.0f} %", 0)
    C.res("AGRI-01", f"2000 → {der}", "Emplois perdus dans la branche", e.loc["2000", "EMP_DC"] - e.loc[der, "EMP_DC"],
          "milliers", der, "EUROSTAT-EMPLOI-AGRICOLE", "M1", "", f"{e.loc['2000', 'EMP_DC']:.0f} milliers en 2000", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
