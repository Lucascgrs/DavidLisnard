"""Thème 6 — Économie, travail et entreprises : calculs à partir de brut/.

python -m verification calculer 6   → calculs/resultats.csv et calculs/graphiques/
"""
import csv
import json
from pathlib import Path

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE, GRAPH = ICI / "resultats.csv", ICI / "graphiques"
UE27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT",
        "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def commerce():
    d = L.eurostat(BRUT / "eurostat/ext_lt_intratrd_fr.json").pivot_table(index="time", columns="indic_et", values="valeur")
    g = L.eurostat(BRUT / "eurostat/nama_10_gdp_biens.json").pivot_table(index="time", columns="na_item", values="valeur")
    for an in ["2022", "2023", "2024", "2025"]:
        res("ECO-01", f"douanes (Eurostat), {an}", "Solde des échanges de biens", d.loc[an, "MIO_BAL_VAL"] / 1e3, "Md€", an,
            "EUROSTAT-COMMERCE-DOUANES", "M1", "114 Md€ (12 mois à juin 2022) ; 100 Md€ « structurel » ; 80 Md€ (2024)",
            "importations valorisées CAF (avec transport et assurance) : déficit plus large que le chiffre français FAB-FAB")
        res("ECO-01", f"comptes nationaux, {an}", "Solde des échanges de biens", (g.loc[an, "P61"] - g.loc[an, "P71"]) / 1e3, "Md€", an,
            "EUROSTAT-COMMERCE-BIENS", "M1", "", f"biens et services : {(g.loc[an, 'P6'] - g.loc[an, 'P7']) / 1e3:.1f} Md€")


def industrie():
    v = L.eurostat(BRUT / "eurostat/nama_10_a10.json")
    pib = L.eurostat(BRUT / "eurostat/nama_10_gdp_pays.json")
    an = "2024"
    t = v[v.time == an].pivot_table(index="geo", columns="nace_r2", values="valeur")
    p = pib[pib.time == an].set_index("geo").valeur
    for geo, nom, lis in [("FR", "France", "10,6 % ; 10,3 % ; moins de 10 %"), ("IT", "Italie", "16 %"), ("ES", "Espagne", "13,6 %"),
                          ("DE", "Allemagne", "19 %"), ("EU27_2020", "UE à 27", "")]:
        res("ECO-02", f"{nom}, {an}", "Industrie manufacturière, % du PIB", t.loc[geo, "C"] / p[geo] * 100, "% du PIB", an,
            "EUROSTAT-VA-BRANCHES ; EUROSTAT-PIB-PAYS", "M2", lis,
            f"{t.loc[geo, 'C'] / t.loc[geo, 'TOTAL'] * 100:.1f} % de la valeur ajoutée ; industrie au sens large (B-E) {t.loc[geo, 'B-E'] / p[geo] * 100:.1f} % du PIB")
    s = (t["C"] / t["TOTAL"])[t.index.isin(UE27)].sort_values()
    res("ECO-02", f"UE à 27, {an}", "Rang de la France du moins au plus industrialisé (part de l'industrie manufacturière)",
        list(s.index).index("FR") + 1, "rang", an, "EUROSTAT-VA-BRANCHES", "M2", "« l'un des pays les moins industrialisés d'Europe »",
        f"devant la France : {', '.join(s.index[:list(s.index).index('FR')])}")
    fr = v[(v.geo == "FR")].pivot_table(index="time", columns="nace_r2", values="valeur")
    res("ECO-02", "France, 2000", "Industrie manufacturière, % de la valeur ajoutée", fr.loc["2000", "C"] / fr.loc["2000", "TOTAL"] * 100, "%",
        "2000", "EUROSTAT-VA-BRANCHES", "M2", "")


def productivite():
    j = json.loads((BRUT / "ocde/pib_par_heure.json").read_text(encoding="utf-8"))
    s = {d["series_code"]: dict(zip(d["period"], d["value"])) for d in j["series"]["docs"]}
    vol = {p: s[f"{p}.A.GDPHRS._T.XDC_H.Q._Z._Z._Z"] for p in ("USA", "EA20", "FRA", "DEU")}
    for p, nom in [("USA", "États-Unis"), ("EA20", "zone euro"), ("FRA", "France"), ("DEU", "Allemagne")]:
        res("ECO-03", f"{nom}, 2010 → 2023", "Hausse du PIB par heure travaillée (volume)", (vol[p]["2023"] / vol[p]["2010"] - 1) * 100, "%",
            "2023", "OCDE-PRODUCTIVITE", "M3", "+22 % aux États-Unis, +5 % en Europe")
    cour = {p: s[f"{p}.A.GDPHRS._T.USD_PPP_H.V._Z._Z._Z"] for p in ("USA", "EA20")}
    for an in ["1995", "2019", "2023"]:
        if cour["EA20"].get(an) and cour["USA"].get(an):
            res("ECO-03", f"{an}, parités de pouvoir d'achat courantes", "Productivité horaire de la zone euro / États-Unis",
                cour["EA20"][an] / cour["USA"][an] * 100, "%", an, "OCDE-PRODUCTIVITE", "M3", "98 % (1995) ; 82 % (2019)")
    return vol


def chomage():
    u = L.eurostat(BRUT / "eurostat/une_rt_a.json")
    j = u[(u.age == "Y15-24")].pivot_table(index="time", columns="geo", values="valeur")
    for an in ["2024", "2025"]:
        res("ECO-04", f"15-24 ans, {an}", "Taux de chômage des jeunes, France", j.loc[an, "FR"], "%", an, "EUROSTAT-CHOMAGE-ANNUEL", "M4",
            "18,8 % ; Allemagne 6,7 % ; zone euro moins de 15 %",
            f"Allemagne {j.loc[an, 'DE']} % ; zone euro (EA21) {j.loc[an, 'EA21']} % ; UE {j.loc[an, 'EU27_2020']} %")
    q = L.eurostat(BRUT / "eurostat/une_rt_q_fr.json").set_index("time").valeur
    res("ECO-04", "1er trimestre 2026", "Taux de chômage, France (corrigé des variations saisonnières, Eurostat)", q["2026-Q1"], "%", "2026",
        "EUROSTAT-CHOMAGE-TRIM", "M4", "8,1 % (Insee)", "l'Insee publie sa propre estimation, légèrement différente")


def recherche():
    r = L.eurostat(BRUT / "eurostat/rd_e_gerdtot.json")
    t = r[r.time == "2023"].pivot_table(index="geo", columns="sectperf", values="valeur")
    for geo, nom, lis in [("FR", "France", "2,2 %"), ("DE", "Allemagne", "3,1 %"), ("US", "États-Unis", "3,5 %")]:
        res("ECO-05", f"{nom}, 2023", "Dépense intérieure de R&D totale, % du PIB", t.loc[geo, "TOTAL"], "% du PIB", "2023", "EUROSTAT-RD", "M5", lis)
        res("ECO-05", f"{nom}, 2023", "R&D exécutée par l'État et l'enseignement supérieur (« recherche publique »), % du PIB",
            t.loc[geo, "GOV"] + t.loc[geo, "HES"], "% du PIB", "2023", "EUROSTAT-RD", "M5", lis, f"entreprises : {t.loc[geo, 'BES']} % du PIB")


def graphique(vol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPH.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#b9b8b3", "xtick.color": "#52514e", "ytick.color": "#52514e"})
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
    ans = [str(a) for a in range(2010, 2025)]
    for p, nom, coul in [("USA", "États-Unis", "#2a78d6"), ("DEU", "Allemagne", "#1baf7a"), ("EA20", "Zone euro", "#8a8984"),
                         ("FRA", "France", "#eb6834")]:
        x = [a for a in ans if vol[p].get(a)]
        y = [vol[p][a] / vol[p]["2010"] * 100 for a in x]
        ax.plot([int(a) for a in x], y, color=coul, lw=2, label=nom)
        ax.annotate(f"{nom} {y[-1]:.0f}", (int(x[-1]), y[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9)
    ax.set_xlim(2010, 2028)
    ax.set_ylabel("PIB par heure travaillée, base 100 en 2010")
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("Productivité horaire depuis 2010 : la France décroche aussi de l'Europe", loc="left", fontsize=12)
    fig.text(0.01, 0.01, "Volume, monnaie nationale. Source : OCDE, base de données de la productivité (via DBnomics)", fontsize=8,
             color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPH / "productivite_2010_2024.png")
    plt.close(fig)


def main():
    commerce()
    industrie()
    vol = productivite()
    chomage()
    recherche()
    graphique(vol)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
