"""Mélenchon, thème 11 — Énergie et nucléaire : calculs à partir de brut/.

python -m verification melenchon calculer 11   → calculs/resultats.csv
"""
from datetime import datetime

import pandas as pd

from verification.commun import lecture as L
from verification.commun.calculs import Calculs

C = Calculs(__file__)
B = C.brut


def bulletin_france():
    """Prix TTC hebdomadaires en France (€/l), Weekly Oil Bulletin : gazole et essence SP95."""
    d = pd.read_excel(B / "commission_europeenne/Weekly_Oil_Bulletin_Prices_History.xlsx", sheet_name="Prices with taxes",
                      header=None)
    h, d = d.iloc[0], d.iloc[3:]
    out = {}
    for i, c in h.items():
        if isinstance(c, str) and c.startswith("FR_") and "_price_" in c and ("euro95" in c or "diesel" in c):
            out["essence SP95" if "euro95" in c else "gazole"] = pd.to_numeric(d[i], errors="coerce").values / 1000
    df = pd.DataFrame(out, index=pd.to_datetime(d[0], errors="coerce"))
    return df[df.index.notna()].sort_index()


def prix_dgec():
    d = pd.read_excel(B / "dgec/prix_carburants_2020_2026.xlsx", sheet_name="Carburants routiers", header=None)
    d = d[d[0].map(lambda x: isinstance(x, datetime))]
    d.index = pd.DatetimeIndex(d[0])
    fin = next((k for k in range(1, len(d)) if d.index[k] <= d.index[k - 1]), len(d))  # série hebdomadaire seule
    return d.iloc[:fin][[7, 9]].astype(float).rename(columns={7: "gazole", 9: "SP95-E10"})


def main():
    # NRJ-01 : prix du gaz depuis mai 2017
    i = L.eurostat(B / "eurostat/prc_hicp_minr_energie_fr.json").pivot_table(index="time", columns="coicop18",
                                                                              values="valeur")
    for fin in ("2026-08", "2026-09"):
        C.res("NRJ-01", f"mai 2017 → {fin}", "Hausse des prix du gaz pour les ménages (IPCH, poste gaz)",
              (i.loc[fin, "CP0452"] / i.loc["2017-05", "CP0452"] - 1) * 100, "%", fin[:4], "EUROSTAT-IPCH-ENERGIE",
              "M1", "150 %", "août 2026 : dernier mois connu le jour du discours (12/09/2026)" if fin == "2026-08"
              else f"ensemble des prix : {(i.loc[fin, 'TOTAL'] / i.loc['2017-05', 'TOTAL'] - 1) * 100:.1f} %", 1)

    # NRJ-02 : prix pendant les gilets jaunes
    b = bulletin_france()
    gj = b.loc["2018-10-01":"2019-03-31"]
    for prod in ("gazole", "essence SP95"):
        C.res("NRJ-02", f"{prod}, octobre 2018 → mars 2019", "Prix TTC le plus haut d'une semaine, France",
              gj[prod].max(), "€/l", "2018", "CE-BULLETIN-PETROLIER", "M2", "« on dépassait les 2 euros »",
              f"semaine du {gj[prod].idxmax():%d/%m/%Y}", 3)
    avant = b.loc[:"2021-12-31"]
    C.res("NRJ-02", "avant 2022", "Prix TTC le plus haut d'une semaine, France, gazole et essence",
          avant.max().max(), "€/l", "2005-2021", "CE-BULLETIN-PETROLIER", "M2", "« on dépassait les 2 euros »",
          "les 2 € ont été dépassés pour la première fois en 2022", 3)

    # NRJ-03 : marges de raffinage
    m = pd.read_excel(B / "dgec/marge_brute_raffinage_mensuelle.xlsx", header=None)
    m = m[m[0].map(lambda x: isinstance(x, datetime))]
    m.index = pd.DatetimeIndex(m[0]).strftime("%Y-%m")
    eur = m[2].astype(float)
    for fin in ("2026-08", "2026-09"):
        for base in ("2026-01", "2026-02"):
            C.res("NRJ-03", f"{base} → {fin}", "Marge brute de raffinage sur Brent : rapport entre les deux mois",
                  eur[fin] / eur[base], "fois", fin[:4], "DGEC-MARGE-RAFFINAGE", "M3", "7,5 fois",
                  f"{eur[base]:.0f} €/t → {eur[fin]:.0f} €/t", 1)
    C.res("NRJ-03", "moyenne 2025 → août 2026", "Marge brute de raffinage : rapport à la moyenne de 2025",
          eur["2026-08"] / eur[[k for k in eur.index if k.startswith("2025")]].mean(), "fois", "2026",
          "DGEC-MARGE-RAFFINAGE", "M3", "7,5 fois", "", 1)

    # NRJ-04 : 1,70 €, le prix d'avant la crise
    p = prix_dgec()
    hebdo = p[p.index.year >= 2026]
    for prod in ("gazole", "SP95-E10"):
        fev = hebdo.loc["2026-02-01":"2026-02-28", prod].mean()
        sep = hebdo.loc["2026-09-01":"2026-09-30", prod].mean()
        C.res("NRJ-04", f"{prod}, février 2026", "Prix TTC moyen avant la hausse de mars 2026", fev, "€/l", "2026",
              "DGEC-PRIX-CARBURANTS", "M4", "1,70 €, « le prix d'avant la crise »", "", 3)
        C.res("NRJ-04", f"{prod}, septembre 2026", "Prix TTC moyen au moment de la proposition", sep, "€/l", "2026",
              "DGEC-PRIX-CARBURANTS", "M4", "ramener à 1,70 €", f"baisse demandée : {(1.70 / sep - 1) * 100:.0f} %", 3)

    # NRJ-05 : renouvelables et nucléaire
    r = L.eurostat(B / "eurostat/nrg_ind_ren_fr.json").pivot_table(index="time", columns="geo", values="valeur")
    an = r["FR"].dropna().index.max()
    C.res("NRJ-05", f"France, {an}", "Part des renouvelables dans la consommation finale brute d'énergie",
          r.loc[an, "FR"], "%", an, "EUROSTAT-PART-RENOUVELABLES", "M5", "100 % en 2060",
          f"UE : {r.loc[an, 'EU27_2020']:.1f} %", 1)
    e = L.eurostat(B / "eurostat/nrg_bal_peh_fr.json").pivot_table(index="time", columns="siec", values="valeur")
    an = e["TOTAL"].dropna().index.max()
    C.res("NRJ-05", f"France, {an}", "Part du nucléaire dans la production brute d'électricité",
          e.loc[an, "N900H"] / e.loc[an, "TOTAL"] * 100, "%", an, "EUROSTAT-PRODUCTION-ELEC", "M5",
          "fermeture des réacteurs à 60 ans", f"renouvelables : {e.loc[an, 'RA000'] / e.loc[an, 'TOTAL'] * 100:.1f} %", 1)
    C.ecrire()


if __name__ == "__main__":
    main()
