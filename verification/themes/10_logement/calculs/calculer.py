"""Thème 10 — Logement et urbanisme : calculs à partir de brut/.

python -m verification calculer 10   → calculs/resultats.csv, calculs/graphiques/
"""
import csv
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
GRAPHIQUES = ICI / "graphiques"
CREDOC = "credoc/Sou1986-3360.pdf"
LUS_DANS_LES_PDF = {
    "seuil_500k_1971": (CREDOC, "de 400 000 en 1964, de 500 000 en 1971", 500000),
    "pic_1973": (CREDOC, "la mise en chantier de 556 000 logements", 556000),
    "sous_500k_1976": (CREDOC, "en 1976, de 400 000 en 1981 et de 300 000 en 1984", 1976),
}


def verifier_pdf():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache = {}
    for cle, (f, extrait, _) in LUS_DANS_LES_PDF.items():
        if f not in cache:
            cache[f] = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
        if re.sub(r"\s+", "", extrait) not in cache[f]:
            raise SystemExit(f"Introuvable dans le PDF : {cle} ({f})")


V = lambda k: LUS_DANS_LES_PDF[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def logements():
    d = pd.read_csv(BRUT / "sdes/logements_mensuel_national.csv", sep=";")
    d = d[(d.NAT_SERIES == "Brute") & (d.TYPE_LGT == "Tous Logements")].copy()
    d["date"] = pd.to_datetime(dict(year=d.ANNEE, month=d.MOIS, day=1))
    return d.sort_values("date")


def m1(d):
    src = "SDES-LOGEMENTS-MENSUEL"
    an = d.groupby("ANNEE").agg(com=("LOG_COM", "sum"), mois=("MOIS", "count"))
    an = an[an.mois == 12].com
    for a, lis in [(2017, "437 000"), (2021, "345 000"), (2024, "« en dessous de 300 000 »"), (2025, "« en dessous de 300 000 »")]:
        res("LOG-01", str(a), "Logements commencés dans l'année (France hors Mayotte, données estimées)", an[a], "logements", str(a), src, "M1", lis)
    d_avant = d[d.date <= "2025-09-01"].tail(12)
    res("LOG-01", "12 mois jusqu'à 09/2025", "Logements commencés sur les 12 mois connus au moment de l'audition (22/10/2025)",
        d_avant.LOG_COM.sum(), "logements", "2025", src, "M1", "« en dessous de 300 000 »", "données estimées, révisées depuis")
    d12 = d.tail(12)
    fin = d12.date.iloc[-1]
    res("LOG-01", f"12 mois jusqu'à {fin:%m/%Y}", "Logements commencés sur les 12 derniers mois connus", d12.LOG_COM.sum(), "logements",
        f"{fin:%Y}", src, "M1", "« en dessous de 300 000 »")
    res("LOG-01", "plus bas depuis 2002", "Année complète la plus basse de la série", an.min(), "logements", str(an.idxmin()), src, "M1", "",
        "la série estimée commence en 2002")
    res("LOG-01", "1971-1975 (CRÉDOC)", "Logements mis en chantier par an, seuil franchi de 1971 à 1975", V("seuil_500k_1971"), "logements",
        "1974", "CREDOC-1986-CONSTRUCTION", "M1", "« quasiment 500 000 » en 1974",
        f"au-dessus de 500 000 de 1971 à 1975, pic de {V('pic_1973'):.0f} en 1973, repassé sous 500 000 en {V('sous_500k_1976'):.0f}")
    p = L.eurostat(BRUT / "eurostat/demo_gind_population.json").pivot_table(index="time", columns="geo", values="valeur")
    psrc = "EUROSTAT-POPULATION"
    res("LOG-01", "métropole 1974 → métropole 2013", "Hausse de la population (France métropolitaine)", (p.FX["2013"] - p.FX["1974"]) / 1e6,
        "millions", "2013", psrc, "M1", "10 millions de plus", "la série métropolitaine s'arrête en 2013")
    res("LOG-01", "métropole 1974 → France entière 2025", "Hausse de la population", (p.FR["2025"] - p.FX["1974"]) / 1e6, "millions", "2025",
        psrc, "M1", "10 millions de plus", f"inclut les DOM ({(p.FR['2013'] - p.FX['2013']) / 1e6:.1f} million en 2013)")
    res("LOG-01", "1974, au moins 500 000", "Logements commencés pour 1 000 habitants", V("seuil_500k_1971") / p.FX["1974"] * 1000, "‰", "1974",
        f"CREDOC-1986-CONSTRUCTION ; {psrc}", "M1", "", "borne basse : le nombre réel dépasse 500 000")
    res("LOG-01", "2025", "Logements commencés pour 1 000 habitants", an[2025] / p.FR["2025"] * 1000, "‰", "2025", f"{src} ; {psrc}", "M1")
    return an


def m2():
    c = L.eurostat(BRUT / "eurostat/gov_10a_exp_logement.json")
    pc = c[c.unit == "PC_GDP"].pivot_table(index=["geo", "time"], columns="cofog99", values="valeur")
    md = c[c.unit == "MIO_EUR"].pivot_table(index=["geo", "time"], columns="cofog99", values="valeur")
    src = "EUROSTAT-COFOG-LOGEMENT"
    for a in ["2019", "2021", "2024"]:
        for g, nom in [("FR", "France"), ("EU27_2020", "UE à 27")]:
            x = pc.loc[(g, a)]
            res("LOG-02", f"{nom} {a}", "Dépenses publiques de logement (aménagement GF0601 + allocations GF1006)", x.GF0601 + x.GF1006, "% du PIB",
                a, src, "M2", "1,2 % (France) contre 0,5 % (UE)", "somme de deux valeurs arrondies à 0,1 point par Eurostat")
            res("LOG-02", f"{nom} {a}", "Logement et équipements collectifs, au sens large (GF06)", x.GF06, "% du PIB", a, src, "M2", "",
                "inclut eau, éclairage public, développement local")
    fr = md.loc[("FR", "2021")]
    res("LOG-02", "France 2021", "Dépenses publiques de logement (GF0601 + GF1006)", (fr.GF0601 + fr.GF1006) / 1e3, "Md€", "2021", src, "M2",
        "40 milliards d'euros", "hors dépenses fiscales (TVA réduite, dispositifs d'investissement locatif), comptées dans les 40 Md€")
    s = L.eurostat(BRUT / "eurostat/spr_exp_func_logement.json")
    s = s[s.unit == "PC_GDP"].pivot_table(index="time", columns="geo", values="valeur")
    for a in ["2021", "2024"]:
        res("LOG-02", f"{a}, prestations seules", "Prestations sociales de logement, France / UE", s.FR[a], "% du PIB", a, "EUROSTAT-PROTSOC-LOGEMENT",
            "M2", "", f"UE à 27 : {s.EU27_2020[a]:.2f} % ; rapport {s.FR[a] / s.EU27_2020[a]:.1f}")
    return pc


def m3():
    o = L.ocde(BRUT / "ocde/recettes_patrimoine.csv")
    src = "OCDE-RECETTES-IMMOBILIER"
    for a in ["2021", "2023"]:
        p = o[o.time == a].pivot_table(index="REF_AREA", columns="STANDARD_REVENUE", values="valeur")
        for r, nom in [("FRA", "France"), ("OECD_REP", "moyenne OCDE")]:
            x = p.loc[r]
            res("LOG-03", f"{nom} {a}", "Impôts récurrents sur la propriété immobilière (4100) / recettes fiscales totales",
                x.T_4100 / x._T * 100, "%", a, src, "M3", "6 % (France) contre 3,3 % (OCDE)")
            res("LOG-03", f"{nom} {a}", "Impôts 4100 + impôts sur les transactions (4400) / recettes fiscales totales",
                (x.T_4100 + x.T_4400) / x._T * 100, "%", a, src, "M3", "6 % (France) contre 3,3 % (OCDE)",
                "4400 inclut aussi les taxes sur les transactions financières")


def graphique(an):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPHIQUES.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    x = an.index.astype(int)
    ax.plot(x, an.values / 1e3, color="#2a78d6", lw=2)
    ax.axhline(500, color="#eb6834", lw=1.5, ls="--")
    ax.text(2002.2, 508, "1971-1975 : plus de 500 000 par an (pic de 556 000 en 1973, CRÉDOC)", color="#333", fontsize=9)
    ax.axhline(300, color="#8a8984", lw=1, ls=":")
    ax.text(2002.2, 287, "300 000", color="#555", fontsize=9)
    for a in [2017, 2021, 2025]:
        ax.annotate(f"{an[a] / 1e3:.0f} 000", (a, an[a] / 1e3), textcoords="offset points", xytext=(0, 8 if a != 2025 else -16),
                    ha="center", fontsize=9, color="#333")
    ax.set_ylim(0, 600)
    ax.set_ylabel("milliers de logements")
    ax.set_title("Logements commencés par an en France", loc="left", fontsize=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    fig.text(0.01, 0.01, "Sources : SDES (Sitadel, données estimées, France hors Mayotte) ; CRÉDOC, Consommation, 1986.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPHIQUES / "logements_commences.png")
    plt.close(fig)


def main():
    verifier_pdf()
    an = m1(logements())
    m2()
    m3()
    graphique(an)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
