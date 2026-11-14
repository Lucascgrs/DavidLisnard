"""Thème 16 — Cannes, bilan municipal : calculs à partir de brut/.

python -m verification calculer 16   → calculs/resultats.csv, calculs/graphiques/
"""
import csv
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
GRAPHIQUES = ICI / "graphiques"
CHAMPS = ["dette", "caf", "cafn", "charge", "prod", "dgf", "perso", "tfb", "tfnb", "tth"]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def comptes() -> pd.DataFrame:
    lignes = []
    for f in sorted((BRUT / "dgfip").glob("comptes_cannes_*.json")):
        for x in json.loads(f.read_text(encoding="utf-8"))["results"]:
            lignes.append({"an": int(x["an"]), **{k: x.get(k) for k in CHAMPS}})
    d = pd.DataFrame(lignes).drop_duplicates("an").set_index("an").sort_index()
    for k in ["dette", "caf", "cafn", "charge", "prod", "dgf", "perso"]:
        d[k] = d[k] / 1000  # milliers d'euros → millions d'euros
    return d


MILLESIMES = ["2008", "20090", "2010", "2011-2015", "2016", "2017", "2018", "2019-2020", "2021", "2022", "2023-2024", "2025"]
SRC = " ; ".join(f"DGFIP-COMPTES-CANNES-{m}" for m in MILLESIMES)


def m1(d):
    for fin, lis in [(2023, "-65,5 M€ prévu fin 2023"), (2024, "-71,5 M€"), (2025, "-77,5 M€ (dont -1 M€ prévu en 2025)")]:
        res("CAN-01", f"fin 2013 → fin {fin}", "Baisse de l'encours de dette du budget principal", d.dette[fin] - d.dette[2013], "M€", str(fin), SRC, "M1", lis,
            f"encours : {d.dette[2013]:.1f} M€ fin 2013, {d.dette[fin]:.1f} M€ fin {fin}")
    res("CAN-01", "fin 2001 → fin 2008", "Hausse de l'encours de dette (mandats précédents)", d.dette[2008] - d.dette[2001], "M€", "2008", SRC, "M1", "",
        f"de {d.dette[2001]:.1f} à {d.dette[2008]:.1f} M€ (sommet)")
    res("CAN-01", "fin 2025", "Capacité de désendettement (encours / CAF brute)", d.dette[2025] / d.caf[2025], "années", "2025", SRC, "M1",
        "« très en-deçà du seuil d'alerte »", "seuil d'alerte usuel : 12 ans")


def m2(d):
    for a in [2012, 2013, 2014, 2024, 2025]:
        res("CAN-02", str(a), "CAF nette (épargne nette) du budget principal", d.cafn[a], "M€", str(a), SRC, "M2",
            "5,48 M€ en 2014, 55,92 M€ en 2024" if a in (2014, 2024) else "")
    res("CAN-02", "2024 / 2014", "Rapport des CAF nettes", d.cafn[2024] / d.cafn[2014], "fois", "2024", SRC, "M2", "« multiplication par dix »")
    res("CAN-02", "moyenne 2023-2025 / moyenne 2011-2013", "Rapport des CAF nettes moyennes sur trois ans", d.cafn.loc[2023:2025].mean() / d.cafn.loc[2011:2013].mean(),
        "fois", "2025", SRC, "M2", "", "évite de dépendre d'une année creuse ou d'un pic")


def m3(d):
    for col, nom in [("tfb", "taxe foncière sur le bâti"), ("tfnb", "taxe foncière sur le non-bâti"), ("tth", "taxe d'habitation")]:
        s = d[col]
        res("CAN-03", f"{nom}, 2014-2024", "Nombre de valeurs différentes du taux communal de 2014 à 2024", s.loc[2014:2024].nunique(), "valeurs", "2024", SRC, "M3",
            "stabilité pendant 11 ans", "2 valeurs pour le foncier bâti : 17,50 % puis 28,12 % en 2021, transfert du taux départemental (réforme de la taxe d'habitation)" if col == "tfb" else "")
        res("CAN-03", f"{nom}, 2025 / 2024", "Évolution du taux communal", (s[2025] / s[2024] - 1) * 100, "%", "2025", SRC, "M3", "-3,6 %",
            f"{s[2024]} % → {s[2025]} %")


def m4(d):
    for deb, fin in [(2014, 2023), (2014, 2022), (2013, 2023), (2014, 2024)]:
        res("CAN-04", f"{deb} → {fin}", "Évolution des charges de fonctionnement du budget principal", d.charge[fin] - d.charge[deb], "M€", str(fin), SRC, "M4",
            "-65,9 M€ depuis 2014", f"{d.charge[deb]:.1f} → {d.charge[fin]:.1f} M€ (euros courants)")


def m5():
    z = zipfile.ZipFile(BRUT / "insee/base-cc-filosofi-2021-geo2024_csv.zip")
    lire = lambda n: pd.read_csv(io.BytesIO(z.read(n)), sep=";", dtype=str)
    nombre = lambda v: float(str(v).replace(",", "."))  # valeurs « 21,0 » ; certaines cellules sont masquées (secret statistique)
    com = lire("cc_filosofi_2021_COM.csv").set_index("CODGEO")
    met = lire("cc_filosofi_2021_METRO.csv")
    res("CAN-05", "Cannes, 2021", "Taux de pauvreté (seuil à 60 % du niveau de vie médian)", nombre(com.loc["06029", "TP6021"]), "%", "2021", "INSEE-FILOSOFI-2021", "M5", "21 %")
    res("CAN-05", "France métropolitaine, 2021", "Taux de pauvreté (seuil à 60 % du niveau de vie médian)", nombre(met.TP6021.iloc[0]), "%", "2021", "INSEE-FILOSOFI-2021", "M5",
        "14 %", "même source et même méthode (Filosofi)")


def m6(d):
    perte13 = (d.dgf[2013] - d.dgf.loc[2014:2022]).sum()
    perte14 = (d.dgf[2014] - d.dgf.loc[2015:2022]).sum()
    res("CAN-06", "DGF, base 2013, cumul 2014-2022", "Baisse cumulée de la DGF par rapport à 2013", perte13, "M€", "2022", SRC, "M6", "139 M€ depuis 2014",
        "ESTIMATION, non fiable à 100 % : la chute de 2014 (−16,8 M€, −36 %) suggère un changement de périmètre l'année de création de la communauté d'agglomération (non vérifié)")
    res("CAN-06", "DGF, base 2014, cumul 2015-2022", "Baisse cumulée de la DGF par rapport à 2014", perte14, "M€", "2022", SRC, "M6", "139 M€ depuis 2014",
        "ESTIMATION, non fiable à 100 % : DGF seule, sans les autres prélèvements (péréquation, FPIC) que Lisnard inclut peut-être")


def graphique(d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPHIQUES.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    ax.plot(d.index, d.dette, color="#2a78d6", lw=2)
    ax.axvline(2014, color="#8a8984", lw=1, ls=":")
    ax.text(2014.2, 330, "David Lisnard maire\n(avril 2014)", fontsize=9, color="#555", va="top")
    for a in [2000, 2008, 2013, 2025]:
        ax.annotate(f"{d.dette[a]:.0f} M€", (a, d.dette[a]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color="#333")
    ax.set_ylim(0, 340)
    ax.set_ylabel("M€")
    ax.set_title("Encours de la dette de la ville de Cannes au 31 décembre (budget principal)", loc="left", fontsize=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    fig.text(0.01, 0.01, "Source : DGFiP, comptes individuels des communes (data.economie.gouv.fr).", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPHIQUES / "dette_cannes.png")
    plt.close(fig)


def main():
    d = comptes()
    m1(d)
    m2(d)
    m3(d)
    m4(d)
    m5()
    m6(d)
    graphique(d)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
