"""Mélenchon, thème 18 — Climat, eau et environnement : calculs à partir de brut/.

python -m verification melenchon calculer 18   → calculs/resultats.csv
"""
import pandas as pd

from verification.commun import lecture as L
from verification.commun.calculs import Calculs

IGN = "ign/memento_inventaire_forestier_2025.pdf"
LUS = {
    "mortalite_125": (IGN, "la poursuite de la hausse de la mortalité des arbres, qui atteint maintenant +125 % par "
                      "rapport à la décennie précédente", 125),
    "boisement_32": (IGN, "La forêt couvre aujourd’hui 32 % du territoire", 32),
    "outremer": (IGN, "Le taux de boisement dans ces territoires est compris entre 26 % (Mayotte) et 96 % (Guyane)", 0),
}
C = Calculs(__file__, LUS)
B = C.brut


def main():
    C.verifier()
    # CLIM-01 : les records de chaleur
    t = pd.read_csv(B / "copernicus/era5_daily_series_2t_global.csv", comment="#")
    t["date"] = pd.to_datetime(t["date"])
    t = t[t.date.dt.year <= 2025]
    an = t.groupby(t.date.dt.year)["ano_91-20"].mean()
    record = -99.0
    for a in range(1990, 2026):
        if a >= 2015:
            nouveau = an[a] > record
            classement = int((an[an.index < a] > an[a]).sum()) + 1
            C.res("CLIM-01", str(a), "Écart de température mondiale à la moyenne 1991-2020", an[a], "°C", str(a),
                  "C3S-ERA5-TEMPERATURE", "M1", "records en 2016, 2020, 2023, 2024 et 2025",
                  ("nouveau record" if nouveau else f"pas de record : {classement}e année la plus chaude à cette date"),
                  3)
        record = max(record, an[a])

    # CLIM-02 : -65 % d'ici 2033
    g = L.eurostat(B / "eurostat/env_air_gge_ue_fr.json") if (B / "eurostat/env_air_gge_ue_fr.json").exists() else \
        L.eurostat(next((B / "eurostat").glob("env_air_gge*.json")))
    g = g[(g.geo == "FR") & (g.airpol == "GHG") & (g.src_crf == "TOTX4_MEMO")].set_index("time").valeur / 1e3
    der = g.index.max()
    cible = g["1990"] * 0.35
    baisse_faite = (1 - g[der] / g["1990"]) * 100
    rythme_passe = ((g[der] / g[str(int(der) - 10)]) ** (1 / 10) - 1) * 100
    rythme_requis = ((cible / g[der]) ** (1 / (2033 - int(der))) - 1) * 100
    C.res("CLIM-02", f"1990 → {der}", "Baisse des émissions de gaz à effet de serre (hors puits de carbone)",
          baisse_faite, "%", der, "EUROSTAT-GES", "M2", "-65 % d'ici 2033",
          f"{g['1990']:.0f} Mt → {g[der]:.0f} Mt ; cible : {cible:.0f} Mt", 1)
    C.res("CLIM-02", f"{int(der) - 10} → {der}", "Rythme annuel de baisse observé", rythme_passe, "% par an", der,
          "EUROSTAT-GES", "M2", "-65 % d'ici 2033", "", 1)
    C.res("CLIM-02", f"{der} → 2033", "Rythme annuel de baisse nécessaire", rythme_requis, "% par an", "2033",
          "EUROSTAT-GES", "M2", "-65 % d'ici 2033", "ESTIMATION, non fiable à 100 % : baisse supposée régulière, "
          "base 1990, hors puits de carbone", 1)

    # CLIM-03 : forêt
    C.res("CLIM-03", "France hexagonale et Corse", "Taux de boisement", C.v("boisement_32"), "%", "2024",
          "IGN-MEMENTO-2025", "M3", "un tiers du territoire", "17,6 millions d'hectares", 0)
    C.res("CLIM-03", "dernière période par rapport à la décennie précédente", "Hausse de la mortalité des arbres",
          C.v("mortalite_125"), "%", "2024", "IGN-MEMENTO-2025", "M3", "+125 % en dix ans", "", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
