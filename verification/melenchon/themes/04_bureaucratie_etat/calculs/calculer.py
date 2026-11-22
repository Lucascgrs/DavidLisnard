"""Mélenchon, thème 4 — Bureaucratie, normes et réforme de l'État : calculs à partir de brut/.

python -m verification melenchon calculer 4   → calculs/resultats.csv
"""
from verification.commun import lecture as L
from verification.commun.calculs import Calculs

C = Calculs(__file__)
B = C.brut


def main():
    g = L.eurostat(B / "eurostat/gov_10a_main_d1_te_fr.json").pivot_table(index="time", columns=["sector", "na_item"],
                                                                           values="valeur")
    fin = "2024"  # dernière année complète connue le jour du débat (27/08/2026)
    for debut in ("2004", "1995"):
        for s, nom in (("S13", "ensemble des administrations publiques"), ("S1311", "État")):
            C.res("ETAT-01", f"{nom}, {debut} → {fin}", "Évolution de la rémunération des salariés publics",
                  g.loc[fin, (s, "D1PAY")] - g.loc[debut, (s, "D1PAY")], "points de PIB", fin,
                  "EUROSTAT-REMUNERATIONS-DEPENSES", "M1", "−6 points",
                  f"{g.loc[debut, (s, 'D1PAY')]} % → {g.loc[fin, (s, 'D1PAY')]} % du PIB", 1)
            C.res("ETAT-02", f"{nom}, {debut} → {fin}", "Évolution de la dépense publique totale",
                  g.loc[fin, (s, "TE")] - g.loc[debut, (s, "TE")], "points de PIB", fin,
                  "EUROSTAT-REMUNERATIONS-DEPENSES", "M1", "−7 points en 20 ans",
                  f"{g.loc[debut, (s, 'TE')]} % → {g.loc[fin, (s, 'TE')]} % du PIB", 1)
    C.ecrire()


if __name__ == "__main__":
    main()
