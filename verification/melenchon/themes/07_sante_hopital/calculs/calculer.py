"""Mélenchon, thème 7 — Santé et hôpital : calculs à partir de brut/.

python -m verification melenchon calculer 7   → calculs/resultats.csv
"""
import pandas as pd

from verification.commun import lecture as L
from verification.commun.calculs import Calculs

CIRC = "circ/pr261_cancers_evitables.pdf"
LUS = {
    "evitables": (CIRC, "142 000 cas de cancer (41 %) auraient pu être évités", 41),
    "infectieux": (CIRC, "4 % des nouveaux cas de cancers sont imputables aux agents infectieux", 4),
    "professionnel": (CIRC, "3,6 % aux expositions professionnelles", 3.6),
    "radon": (CIRC, "1,2 % au radon dans l’air intérieur", 1.2),
    "pollution": (CIRC, "0,4 % à la pollution atmosphérique", 0.4),
    "chimique": (CIRC, "0,1 % à une exposition à des substances chimiques dans l’environnement général", 0.1),
}
C = Calculs(__file__, LUS)
B = C.brut


def main():
    C.verifier()
    # SANTE-01 : lits de l'hôpital public
    p = L.eurostat(B / "eurostat/hlth_rs_bds2_fr.json").pivot_table(index="time", columns="owner", values="valeur")
    t = L.eurostat(B / "eurostat/hlth_rs_bds1_fr.json")
    t = t[t.hlthcare.isin(["SOM", "TOTAL"])].pivot_table(index="time", columns="facility", values="valeur",
                                                          aggfunc="max")
    fin = p["PUB"].dropna().index.max()
    debut = str(int(fin) - 25) if str(int(fin) - 25) in p.index else p.index.min()
    C.res("SANTE-01", f"{debut} → {fin}", "Lits supprimés dans les hôpitaux publics", p.loc[debut, "PUB"] - p.loc[fin, "PUB"],
          "lits", fin, "EUROSTAT-LITS-PROPRIETAIRE", "M1", "80 000 lits en vingt-cinq ans",
          f"{p.loc[debut, 'PUB']:.0f} → {p.loc[fin, 'PUB']:.0f} lits", 0)
    C.res("SANTE-01", f"{debut} → {fin}, tous statuts", "Lits de soins de longue durée supprimés (public et privé)",
          t.loc[debut, "HBEDT_LT"] - t.loc[fin, "HBEDT_LT"], "lits", fin, "EUROSTAT-LITS-TYPE", "M1", "",
          f"{t.loc[debut, 'HBEDT_LT']:.0f} → {t.loc[fin, 'HBEDT_LT']:.0f} lits ; lits de soins aigus : "
          f"{t.loc[debut, 'HBEDT_CUR']:.0f} → {t.loc[fin, 'HBEDT_CUR']:.0f}", 0)

    # SANTE-02 : déserts médicaux (même lecture du fichier que pour David Lisnard)
    d = pd.read_excel(B / "drees/APL_medecins_generalistes.xlsx", sheet_name="APL 2024", header=None, skiprows=10)
    d = d.iloc[:, [0, 2, 7]]
    d.columns = ["commune", "apl", "pop"]
    d["apl"], d["pop"] = pd.to_numeric(d["apl"], errors="coerce"), pd.to_numeric(d["pop"], errors="coerce")
    d = d.dropna()
    for seuil, nom in ((2.5, "moins de 2,5 consultations par an et par habitant (zone sous-dense, seuil DREES)"),
                       (3.0, "moins de 3 consultations par an et par habitant"),
                       (4.0, "moins de 4 consultations par an et par habitant (seuil large)")):
        C.res("SANTE-02", f"APL 2024, {nom}", "Part de la population concernée",
              d.loc[d.apl < seuil, "pop"].sum() / d["pop"].sum() * 100, "%", "2024", "DREES-APL-GENERALISTES", "M2",
              "plus d'un tiers de la population", f"part des communes : {(d.apl < seuil).mean() * 100:.1f} %", 1)

    # SANTE-03 : cancers évitables
    env = sum(C.v(k) for k in ("pollution", "chimique", "radon"))
    large = env + C.v("infectieux") + C.v("professionnel")
    C.res("SANTE-03", "2015, adultes de 30 ans et plus", "Cancers évitables, tous facteurs de risque étudiés",
          C.v("evitables"), "%", "2015", "CIRC-CANCERS-EVITABLES-2018", "M3", "40 %",
          "tabac, alcool, alimentation, surpoids en tête", 1)
    C.res("SANTE-03", "pollution de l'air, substances chimiques, radon", "Cancers attribuables à l'environnement au sens "
          "strict", env, "%", "2015", "CIRC-CANCERS-EVITABLES-2018", "M3", "40 % « en agissant sur l'environnement »",
          "", 1)
    C.res("SANTE-03", "avec les infections et les expositions professionnelles", "Cancers attribuables à "
          "l'environnement au sens large", large, "%", "2015", "CIRC-CANCERS-EVITABLES-2018", "M3",
          "40 % « en agissant sur l'environnement »", "sans les rayonnements ultraviolets ni les facteurs liés au mode "
          "de vie", 1)
    C.ecrire()


if __name__ == "__main__":
    main()
