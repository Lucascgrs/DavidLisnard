"""Thème 12 — Agriculture : calculs à partir de brut/.

python -m verification calculer 12   → calculs/resultats.csv, calculs/graphiques/
"""
import csv
import html
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
GRAPHIQUES = ICI / "graphiques"
LUS = {
    "solde_2025": ("douanes/resultats_commerce_exterieur_2025.pdf",
                   "le solde des produits agricoles et alimentaires est passé de +7,7 Md€ à +0,2 Md€ 2025, un point bas historique", 0.2),
    "solde_2019": ("douanes/resultats_commerce_exterieur_2025.pdf", "est passé de +7,7 Md€ à +0,2 Md€", 7.7),
    "academie_1978": ("academie/commerce_exterieur_agroalimentaire.pdf",
                      "En 2025, pour la première fois depuis 1978, le solde agroalimentaire a été déficitaire, si l’on inclut les produits de la mer", 1978),
    "suicide_22_28": ("assemblee/QANR5L14QE102524.pdf", "une surmortalité par suicide comprise entre 22 et 28 % par rapport à la population générale", 28),
    "suicide_msa_2015": ("assemblee/QANR5L15QE23624.pdf", "de l'ordre de 12 % en 2015", 12),
    "suicide_spf": ("spf/BEH_2018_27_2.pdf", "Les résultats publiés, portant sur les années 2007 à 2011, montraient une surmortalité par suicide chez les hommes", 0),
    "pauvrete_exploitants": ("insee/8376591.html", "En 2020, 17,7 % des exploitants vivent sous le seuil de pauvreté monétaire, contre 14,4 % parmi l’ensemble de la population", 17.7),
    "pauvrete_ensemble": ("insee/8376591.html", "contre 14,4 % parmi l’ensemble de la population", 14.4),
}
MER = ["03", "1604", "1605"]


def _texte(f: Path) -> str:
    if f.suffix == ".html":
        t = html.unescape(re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8", errors="replace")))
    else:
        import logging
        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        t = " ".join((p.extract_text() or "") for p in PdfReader(f).pages)
    return re.sub(r"\s+", "", t)


def verifier_documents():
    cache = {}
    for cle, (f, extrait, _) in LUS.items():
        if f not in cache:
            cache[f] = _texte(BRUT / f)
        if re.sub(r"\s+", "", extrait) not in cache[f]:
            raise SystemExit(f"Introuvable : {cle} ({f})")


V = lambda k: LUS[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def commerce():
    c = L.eurostat(BRUT / "eurostat/comext_fr_chapitres_01_24.json")
    ch = c[c["product"].str.len() == 2]
    tot = ch.pivot_table(index="time", columns="flow", values="valeur", aggfunc="sum") / 1e9
    mer = c[c["product"].isin(MER)].pivot_table(index="time", columns="flow", values="valeur", aggfunc="sum") / 1e9
    tab = c[c["product"] == "24"].pivot_table(index="time", columns="flow", values="valeur", aggfunc="sum") / 1e9
    t = pd.DataFrame({"imp": tot["1"], "exp": tot["2"]})
    t["solde"] = t.exp - t.imp
    t["imp_hors_mer"] = tot["1"] - mer["1"]
    t["solde_hors_mer"] = (tot["2"] - mer["2"]) - (tot["1"] - mer["1"])
    t["imp_hors_mer_tabac"] = tot["1"] - mer["1"] - tab["1"]
    return t


def m1(t):
    src = "COMEXT-AGROALIMENTAIRE"
    res("AGRI-01", "Douanes, périmètre officiel", "Solde des produits agricoles et agroalimentaires", V("solde_2025"), "Md€", "2025", "TRESOR-COMMERCE-2025",
        "M1", "déficitaire", f"« point bas historique » ; {V('solde_2019')} Md€ en 2019")
    res("AGRI-01", "chapitres 01 à 24, produits de la mer compris", "Solde commercial", t.solde["2025"], "Md€", "2025", src, "M1", "déficitaire",
        f"premier solde négatif de la série (depuis 2000) ; l'Académie d'agriculture date le précédent de {V('academie_1978'):.0f}")
    res("AGRI-01", "chapitres 01 à 24, hors produits de la mer", "Solde commercial", t.solde_hors_mer["2025"], "Md€", "2025", src, "M1", "déficitaire")


def m2(t):
    src = "COMEXT-AGROALIMENTAIRE"
    for col, nom in [("imp", "chapitres 01 à 24"), ("imp_hors_mer_tabac", "hors produits de la mer et tabac")]:
        res("AGRI-02", f"{nom}, 2022", "Importations agricoles et alimentaires", t[col]["2022"], "Md€", "2022", src, "M2", "63 Md€")
        res("AGRI-02", f"{nom}, 2022 / 2000", "Rapport des importations 2022 / 2000 (euros courants)", t[col]["2022"] / t[col]["2000"], "fois", "2022", src,
            "M2", "« plus du double »", f"2000 : {t[col]['2000']:.1f} Md€")


def m3(t):
    src = "COMEXT-AGROALIMENTAIRE"
    for a, lis in [("2022", "10,4 Md€"), ("2024", "4,9 Md€")]:
        res("AGRI-03", f"{a}, chapitres 01 à 24", "Solde commercial agroalimentaire", t.solde[a], "Md€", a, src, "M1", lis,
            f"hors produits de la mer : {t.solde_hors_mer[a]:.1f} Md€ ; périmètre différent de celui des Douanes")
    res("AGRI-03", "2025 / 2024, chapitres 01 à 24", "Hausse des importations agroalimentaires", (t.imp["2025"] / t.imp["2024"] - 1) * 100, "%", "2025", src,
        "M1", "+8,5 %", f"niveau 2025 : {t.imp['2025']:.1f} Md€ (Lisnard : « plus de 64 milliards », autre périmètre)")


def m4():
    res("AGRI-04", "exploitants, MSA", "Surmortalité par suicide par rapport à la population générale (borne haute)", V("suicide_22_28"), "%", "2011",
        "AN-QE102524-SUICIDE", "M3", "« 7 fois plus » (+600 %)", "fourchette de 22 à 28 % ; soit 1,2 à 1,3 fois le risque moyen")
    res("AGRI-04", "affiliés MSA, 2015", "Risque de suicide supérieur à celui des assurés du régime général", V("suicide_msa_2015"), "%", "2015",
        "AN-QE23624-SUICIDE-MSA", "M3", "« 7 fois plus »", "chiffre de la MSA rapporté dans une question écrite")
    res("AGRI-05", "exploitants, 2020", "Taux de pauvreté monétaire", V("pauvrete_exploitants"), "%", "2020", "INSEE-PAUVRETE-EXPLOITANTS", "M4",
        "« presque 40 % » ; « un sur quatre »", f"ensemble de la population : {V('pauvrete_ensemble')} %")


def m5():
    r = L.eurostat(BRUT / "eurostat/aact_eaa06_fr.json")
    n = r[r.unit == "I_N_1"].pivot_table(index="time", columns="indic_agr", values="valeur")
    src = "EUROSTAT-REVENU-AGRICOLE"
    noms = {"IND_C": "Revenu net d'entreprise agricole total, en termes réels (indicateur C)",
            "IND_B": "Revenu net d'entreprise agricole par actif non salarié, en termes réels (indicateur B)"}
    for ind, nom in noms.items():
        for d, f in [("1994", "2024"), ("1995", "2025")]:
            s = n.loc[str(int(d) + 1):f, ind] / 100
            res("AGRI-06", f"{d} → {f}", nom, (s.prod() - 1) * 100, "%", f, src, "M5", "−40 %", "variations annuelles chaînées")


def m6():
    f = L.eurostat(BRUT / "eurostat/aei_fm_usefert_fr.json").pivot_table(index="time", columns="nutrient", values="valeur")
    for a in ["2018", "2024"]:
        res("AGRI-07", a, "Consommation d'engrais azotés (en azote)", f.N[a] / 1e6, "millions de tonnes", a, "EUROSTAT-ENGRAIS", "M6", "2,2 millions de tonnes")


def graphique(t):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPHIQUES.mkdir(exist_ok=True)
    x = t.index.astype(int)
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    ax.plot(x, t.solde_hors_mer, color="#2a78d6", lw=2)
    ax.plot(x, t.solde, color="#eb6834", lw=2)
    ax.axhline(0, color="#555", lw=1)
    ax.text(2025.3, t.solde_hors_mer.iloc[-1], f"hors produits de la mer\n{t.solde_hors_mer.iloc[-1]:+.1f} Md€", va="center", fontsize=9, color="#333")
    ax.text(2025.3, t.solde.iloc[-1] - 0.6, f"produits de la mer compris\n{t.solde.iloc[-1]:+.1f} Md€", va="center", fontsize=9, color="#333")
    ax.scatter([2025], [V("solde_2025")], color="#1baf7a", zorder=3, s=40)
    ax.annotate(f"Douanes, périmètre officiel : +{V('solde_2025')} Md€", (2025, V("solde_2025")), xytext=(2014.5, 1.6), fontsize=9, color="#333",
                arrowprops=dict(arrowstyle="-", color="#8a8984", lw=0.8))
    ax.set_xlim(1999.5, 2030)
    ax.set_ylim(-3, 16)
    ax.set_xticks(range(2000, 2026, 5))
    ax.set_ylabel("Md€")
    ax.set_title("Solde du commerce agricole et alimentaire de la France", loc="left", fontsize=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    fig.text(0.01, 0.01, "Sources : Eurostat Comext (chapitres 01 à 24 du système harmonisé) ; Douanes / DSECE, résultats 2025.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPHIQUES / "solde_agroalimentaire.png")
    plt.close(fig)


def main():
    verifier_documents()
    t = commerce()
    m1(t)
    m2(t)
    m3(t)
    m4()
    m5()
    m6()
    graphique(t)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
