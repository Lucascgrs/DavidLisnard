"""Mélenchon, thème 17 — Inégalités, pauvreté et grandes fortunes : calculs à partir de brut/.

python -m verification melenchon calculer 17   → calculs/resultats.csv
"""
import re

import pandas as pd

from verification.commun import lecture as L
from verification.commun.calculs import Calculs

LUS = {
    "aide_2_4": ("insee/IP1907_aide_alimentaire.pdf", "on aboutit à une estimation du nombre de bénéficiaires sur une "
                 "année entre 2 et 4 millions de personnes en France métropolitaine", 4),
    "seuil_1337": ("insee/seuils_pauvrete.html", "1 337", 1337),
}
C = Calculs(__file__, LUS)
B = C.brut


def serie_insee(fichier: str) -> pd.Series:
    """Ligne « Seuil à 60 % » d'un tableau Insee (années en colonnes ; une année avec un renvoi = nouvelle série)."""
    d = pd.read_excel(B / fichier, header=None)
    entete = next(i for i in d.index if str(d.iloc[i, 0]).startswith("Seuil de pauvreté"))
    ligne = next(i for i in d.index if str(d.iloc[i, 0]).startswith("Seuil à 60"))
    out = {}
    for j in range(1, d.shape[1]):
        an = str(d.iloc[entete, j]).strip()
        v = d.iloc[ligne, j]
        if pd.notna(v) and an != "nan":
            m = re.match(r"(\d{4})", an)
            cle = m.group(1) + ("" if re.fullmatch(r"\d{4}(\.0)?", an) else " (nouvelle série)")
            out[cle] = float(v)
    return pd.Series(out)


def main():
    C.verifier()
    taux, nb = serie_insee("insee/taux_pauvrete_1975_2024.xlsx"), serie_insee("insee/personnes_pauvres_1975_2024.xlsx")

    # INEG-01 : un million de pauvres en plus depuis 2017
    C.res("INEG-01", "2017 → 2024", "Hausse du nombre de personnes pauvres (seuil à 60 %)",
          (nb["2024"] - nb["2017"]) / 1e3, "millions", "2024", "INSEE-PAUVRETE-NOMBRE", "M1", "un million",
          f"{nb['2017'] / 1e3:.2f} millions en 2017, {nb['2024'] / 1e3:.2f} millions en 2024", 2)

    # INEG-02 : plus de 15 %, un record ?
    C.res("INEG-02", "2024", "Taux de pauvreté (seuil à 60 %)", taux["2024"], "%", "2024", "INSEE-PAUVRETE-TAUX", "M2",
          "plus de 15 %", f"2023 : {taux['2023']} %", 1)
    depuis96 = taux[[k for k in taux.index if int(k[:4]) >= 1996 and k[:4] != "2024" and k[:4] != "2023"]]
    C.res("INEG-02", "1996 → 2022", "Taux de pauvreté le plus élevé avant 2023", depuis96.max(), "%",
          depuis96.idxmax()[:4], "INSEE-PAUVRETE-TAUX", "M2", "« un record jamais enregistré »",
          "série annuelle depuis 1996", 1)
    for an in ("1975", "1979", "1984"):
        C.res("INEG-02", an, "Taux de pauvreté (seuil à 60 %), série rétropolée", taux[an], "%", an,
              "INSEE-PAUVRETE-TAUX", "M2", "« un record jamais enregistré »", "", 1)

    # INEG-03 : 9 ou 10 millions de pauvres
    C.res("INEG-03", "2024", "Personnes pauvres (seuil à 60 %)", nb["2024"] / 1e3, "millions", "2024",
          "INSEE-PAUVRETE-NOMBRE", "M1", "plus de 10 millions ; 9 millions", "", 2)

    # INEG-04 : aide alimentaire
    C.res("INEG-04", "2021", "Bénéficiaires de l'aide alimentaire sur une année, France métropolitaine (haut de la "
          "fourchette)", C.v("aide_2_4"), "millions", "2021", "INSEE-AIDE-ALIMENTAIRE-2022", "M3", "8 millions",
          "fourchette de l'Insee : 2 à 4 millions", 0)

    # INEG-05 : se chauffer
    ch = L.eurostat(B / "eurostat/ilc_mdes01_fr.json").set_index("time").valeur
    pop = L.eurostat(B / "eurostat/demo_gind_fr.json").set_index("time").valeur
    for an in ("2024", "2025"):
        C.res("INEG-05", an, "Personnes ne pouvant pas chauffer convenablement leur logement", ch[an] * pop[an] / 1e8,
              "millions", an, "EUROSTAT-CHAUFFAGE; EUROSTAT-POPULATION", "M4", "4 millions",
              f"{ch[an]} % de la population", 1)

    # INEG-06 : SMIC et seuil de pauvreté
    w = L.eurostat(B / "eurostat/earn_mw_cur_6pays.json")
    w = w[w.geo == "FR"].set_index("time").valeur
    brut24 = (w["2024-S1"] + w["2024-S2"]) / 2
    net24 = brut24 * 0.7905
    C.res("INEG-06", "2024, temps plein", "SMIC net mensuel (estimation) rapporté au seuil de pauvreté d'une personne "
          "seule", (net24 / C.v("seuil_1337") - 1) * 100, "% au-dessus", "2024", "EUROSTAT-SMIC-PAYS; "
          "INSEE-SEUILS-PAUVRETE", "M5", "à peine plus que le seuil",
          f"ESTIMATION, non fiable à 100 % : SMIC net estimé {net24:.0f} €, seuil 1 337 € ; hors prime d'activité", 1)

    # INEG-07 : 1 337 €
    C.res("INEG-07", "2024", "Seuil de pauvreté à 60 % pour une personne seule", C.v("seuil_1337"), "€ par mois",
          "2024", "INSEE-SEUILS-PAUVRETE", "M6", "1 337 €", "dernier seuil publié (juillet 2026)", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
