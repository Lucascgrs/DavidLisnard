"""Thème 13 — Europe et international : calculs à partir de brut/.

python -m verification calculer 13   → calculs/resultats.csv, calculs/graphiques/
"""
import csv
import json
import re
from pathlib import Path

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
GRAPHIQUES = ICI / "graphiques"
OTAN = "otan/def_exp_2025.pdf"
LUS = {
    "draghi_70": ("commission/draghi_partie_A.pdf", "Around 70% of the gap in per capita GDP with US at PPP is explained by lower productivity in the EU", 70),
    "draghi_95_1995": ("commission/draghi_partie_A.pdf", "converged from 22% of the US level in 1945 to 95% in 1995", 95),
    "draghi_80": ("commission/draghi_partie_A.pdf", "fallen back below 80% of the US level", 80),
    "otan_2025_meur": (OTAN, "France (Euros) 39,149 39,199 39,950 40,852 42,748 44,206 46,018 47,702 49,567 54,950 59,580 61,780", 61780),
    "otan_2024_meur": (OTAN, "54,950 59,580 61,780", 59580),
    "otan_2025_pib": (OTAN, "France 1.82 1.78 1.79 1.78 1.81 1.82 1.99 1.90 1.87 1.94 2.03 2.05", 2.05),
}


def verifier_documents():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache = {}
    for cle, (f, extrait, _) in LUS.items():
        if f not in cache:
            cache[f] = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
        if re.sub(r"\s+", "", extrait) not in cache[f]:
            raise SystemExit(f"Introuvable : {cle} ({f})")


V = lambda k: LUS[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def m1():
    p = L.eurostat(BRUT / "eurostat/prc_ppp_ind_pib_hab.json").pivot_table(index="time", columns="geo", values="valeur")
    src = "EUROSTAT-PIB-HAB-SPA"
    avant = p.FR.loc[:"2021"]
    res("EUR-01", "1995-2021", "Plus bas indice de la France avant 2022 (UE = 100)", avant.min(), "indice", avant.idxmin(), src, "M1", "",
        "la série commence en 1995")
    for a in ["2022", "2023", "2024"]:
        res("EUR-01", a, "PIB par habitant de la France en SPA (UE = 100)", p.FR[a], "indice", a, src, "M1", "« en dessous de la moyenne européenne »")
        res("EUR-02", a, "PIB par habitant en SPA (UE = 100) : France moins Italie", p.FR[a] - p.IT[a], "points", a, src, "M1",
            "« derrière l'Italie »", f"France {p.FR[a]:.0f}, Italie {p.IT[a]:.0f}")
    return p


def rangs():
    pays = json.loads((BRUT / "fmi/countries.json").read_text(encoding="utf-8"))["countries"]
    pop = L.fmi(BRUT / "fmi/lp.json")
    pop = pop[pop.pays.isin(pays)].pivot_table(index="pays", columns="time", values="valeur")
    out = {}
    for code, fichier in [("dollars", "fmi/ngdpdpc.json"), ("PPA", "fmi/ppppc.json")]:
        d = L.fmi(BRUT / fichier)
        d = d[d.pays.isin(pays)]
        for a in ["1980", "1995", "2024", "2025"]:
            y = d[d.time == a].dropna()
            for filtre in ["tous", "1M"]:
                z = y if filtre == "tous" else y[y.pays.map(lambda c: pop[a].get(c, float("nan")) >= 1)]
                z = z.sort_values("valeur", ascending=False).reset_index(drop=True)
                out[(code, a, filtre)] = (int(z.index[z.pays == "FRA"][0]) + 1, len(z))
    return out


def m2():
    rg = rangs()
    src = "FMI-PIB-HAB-DOLLARS ; FMI-PIB-HAB-PPA ; FMI-POPULATION ; FMI-PAYS"
    for code, nom in [("dollars", "en dollars courants"), ("PPA", "en parité de pouvoir d'achat")]:
        for filtre, fnom in [("tous", "tous pays"), ("1M", "pays de plus d'un million d'habitants")]:
            for a in ["1980", "1995", "2024", "2025"]:
                r, n = rg[(code, a, filtre)]
                res("EUR-03", f"{nom}, {fnom}, {a}", "Rang mondial de la France pour le PIB par habitant", r, "rang", a, src, "M2",
                    "7e il y a 30 ans, 27e aujourd'hui", f"sur {n} pays classés")


def m3():
    res("EUR-04", "rapport Draghi, partie A", "Part de l'écart de PIB par habitant UE / États-Unis (PPA) expliquée par la productivité", V("draghi_70"), "%",
        "2024", "DRAGHI-2024-A", "M3", "70 %", f"productivité du travail de l'UE : {V('draghi_95_1995')} % du niveau américain en 1995, moins de {V('draghi_80')} % aujourd'hui")


def m4():
    g = L.eurostat(BRUT / "eurostat/nama_10_gdp_fr.json").set_index("time").valeur / 1000  # Md€
    res("EUR-05", "OTAN, estimation 2025", "Dépenses de défense de la France (définition OTAN)", V("otan_2025_meur") / 1000, "Md€", "2025", "OTAN-DEPENSES-2025",
        "M4", "57 Md€", f"{V('otan_2025_pib')} % du PIB ; 2024 : {V('otan_2024_meur') / 1000:.1f} Md€")
    res("EUR-05", "57 Md€ / PIB 2025", "Part du PIB", 57 / g["2025"] * 100, "%", "2025", "EUROSTAT-PIB-COURANT", "M4", "« à peine 2 % »")
    for cible, lis in [(3.0, "27 Md€ par an"), (3.5, "plus de 40 Md€ par an")]:
        res("EUR-05", f"de 2,06 % à {cible} % du PIB 2025", "Dépense supplémentaire annuelle", (cible - 2.06) / 100 * g["2025"], "Md€", "2025",
            "EUROSTAT-PIB-COURANT", "M4", lis, f"PIB 2025 : {g['2025']:.0f} Md€")


def m5():
    c = L.eurostat(BRUT / "eurostat/comext_ue_chine.json").pivot_table(index="time", columns="flow", values="valeur") / 1e9
    solde = c["2"] - c["1"]
    src = "COMEXT-UE-CHINE"
    res("EUR-06", "2025", "Solde commercial de l'UE avec la Chine", solde["2025"], "Md€", "2025", src, "M5", "−360 Md€, « record »")
    res("EUR-06", "record de la série", "Solde commercial de l'UE avec la Chine, année la plus déficitaire", solde.min(), "Md€", solde.idxmin(), src, "M5",
        "", "série 2010-2025")
    return solde


def graphique(p):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPHIQUES.mkdir(exist_ok=True)
    x = p.index.astype(int)
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    for geo, nom, coul in [("FR", "France", "#2a78d6"), ("IT", "Italie", "#eb6834"), ("DE", "Allemagne", "#1baf7a"), ("ES", "Espagne", "#eda100")]:
        ax.plot(x, p[geo], color=coul, lw=2)
        ax.text(x[-1] + 0.3, p[geo].iloc[-1] + (1.2 if geo == "FR" else -1.2 if geo == "IT" else 0), f"{nom} {p[geo].iloc[-1]:.0f}", va="center", fontsize=9, color="#333")
    ax.axhline(100, color="#8a8984", lw=1.2, ls="--")
    ax.text(x[0], 101, "moyenne de l'UE à 27 = 100", fontsize=9, color="#555")
    ax.set_xlim(x[0] - 0.5, x[-1] + 4)
    ax.set_ylabel("indice, UE à 27 = 100")
    ax.set_title("PIB par habitant en standards de pouvoir d'achat", loc="left", fontsize=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    fig.text(0.01, 0.01, "Source : Eurostat (prc_ppp_ind).", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPHIQUES / "pib_par_habitant_spa.png")
    plt.close(fig)


def main():
    verifier_documents()
    p = m1()
    m2()
    m3()
    m4()
    m5()
    graphique(p)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
