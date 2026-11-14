"""Thème 3 — Immigration, islamisme et identité : calculs à partir de brut/.

python -m verification calculer 3   → calculs/resultats.csv et calculs/graphiques/
"""
import csv
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE, GRAPH = ICI / "resultats.csv", ICI / "graphiques"
UE27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT",
        "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]

LUS_DANS_LES_PDF = {
    "cc_oqtf_10pc": ("cour_des_comptes/20240104_lutte_immigration_irreguliere.pdf",
                     "seule une petite minorité – autour de 10 % – des obligations de quitter le territoire français sont exécutées", 10),
    "cc_oqtf_2022": ("cour_des_comptes/20240104_lutte_immigration_irreguliere.pdf", "dont 134 280 obligations de quitter le territoire", 134280),
    "ame_depense_reelle_2024": ("senat/Sante_PLF_2026_NP.pdf", "s’élèvent en 2024 à 1 387 millions d’euros", 1387),
    "ame_droit_commun_2024": ("senat/Sante_PLF_2026_NP.pdf", "dont 1 256 millions d’euros pour l ’AME de droit commun", 1256),
    "ame_beneficiaires_fin2024": ("senat/Sante_PLF_2026_NP.pdf", "fin 202 4, 465 208 bénéficiaires", 465208),
    "ame_credits_2026": ("senat/Sante_PLF_2026_NP.pdf", "à hauteur de 1,216 milliard d’euros en AE et en CP", 1216),
    "ame_hausse_10ans": ("senat/Sante_PLF_2026_NP.pdf", "Une progression de 7 0 % des dépenses réelles d ’AME en dix ans", 70),
    "ifop_38": ("ifop/ifop_islam_islamisme_2025.pdf",
                "38% des Français musulmans approuvent tout ou partie des positions islamistes, soit deux fois plus que ceux qui partageaient des positions intégristes en 1998 (19%)", 38),
    "ifop_echantillon": ("ifop/ifop_islam_islamisme_2025.pdf", "échantillon de 1 005 personnes de religion musulmane", 1005),
}


def verifier_pdf():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache, manquants = {}, []
    for cle, (f, extrait, _) in LUS_DANS_LES_PDF.items():
        if f not in cache:
            cache[f] = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
        if re.sub(r"\s+", "", extrait) not in cache[f]:
            manquants.append(f"{cle} ({f})")
    if manquants:
        raise SystemExit("Introuvables dans les PDF :\n  " + "\n  ".join(manquants))


V = lambda k: LUS_DANS_LES_PDF[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def titres():
    p = L.eurostat(BRUT / "eurostat/migr_resfirst.json")
    f = p[p.geo == "FR"].pivot_table(index="time", columns="reason", values="valeur")
    for an in ["2022", "2023", "2024", "2025"]:
        t = f.loc[an]
        res("IMMI-01", f"France, {an}", "Premiers titres de séjour délivrés (ressortissants de pays tiers)", t["TOTAL"], "titres", an,
            "EUROSTAT-PREMIERS-TITRES", "M1", "400 000 ; « 500 000 entrées annuelles légales »")
        res("IMMI-01", f"France, {an}", "Part des premiers titres délivrés pour un motif professionnel", t["EMP"] / t["TOTAL"] * 100, "%",
            an, "EUROSTAT-PREMIERS-TITRES", "M1", "13 % (août 2026) ; 17 % (fin août et septembre 2026)",
            f"famille {t['FAM'] / t['TOTAL'] * 100:.1f} % ; études {t['EDUC'] / t['TOTAL'] * 100:.1f} % ; autres motifs (dont humanitaire) {t['OTH'] / t['TOTAL'] * 100:.1f} %")
    return f


def division_par_huit(f):
    t = f.loc["2025"]
    res("IMMI-02", "2025 divisé par 8", "Premiers titres restants", t["TOTAL"] / 8, "titres", "2025", "EUROSTAT-PREMIERS-TITRES", "M2",
        "diviser par huit ; 80 000 entrées par an",
        "ESTIMATION, non fiable à 100 % : à motifs constants ; 80 000 correspond à une division par 4,7")
    res("IMMI-02", "2025", "Titres familiaux + humanitaires et autres (motifs en grande partie fondés sur le droit)",
        t["FAM"] + t["OTH"], "titres", "2025", "EUROSTAT-PREMIERS-TITRES", "M2", "",
        "à comparer à l'objectif de 47 000 à 80 000 : supposerait de réduire aussi des titres que le droit européen et la CEDH encadrent")


def oqtf():
    o = L.eurostat(BRUT / "eurostat/migr_eiord.json").pivot_table(index="time", columns="geo", values="valeur")
    r = L.eurostat(BRUT / "eurostat/migr_eirtn.json").pivot_table(index="time", columns="geo", values="valeur")
    for an in ["2022", "2023", "2024", "2025"]:
        fr = r.loc[an, "FR"] / o.loc[an, "FR"] * 100
        ue = r.loc[an, "EU27_2020"] / o.loc[an, "EU27_2020"] * 100
        hors_fr = (r.loc[an, "EU27_2020"] - r.loc[an, "FR"]) / (o.loc[an, "EU27_2020"] - o.loc[an, "FR"]) * 100
        res("IMMI-03", f"{an}", "Renvois / ordres de quitter le territoire, France", fr, "%", an, "EUROSTAT-OQTF ; EUROSTAT-RETOURS",
            "M3", "« autour de 10 % » ; 95 % non exécutées",
            f"UE à 27 : {ue:.1f} % ; UE hors France : {hors_fr:.1f} % ; écart avec l'UE hors France {hors_fr - fr:.1f} points")
    res("IMMI-03", "Cour des comptes, 2022", "OQTF exécutées (estimation de la Cour)", V("cc_oqtf_10pc"), "%", "2022",
        "CC-IMMIGRATION-IRREGULIERE-2024", "M3", "« autour de 10 % »", f"{V('cc_oqtf_2022')} OQTF prononcées en 2022")


def ame():
    res("IMMI-04", "2024", "Dépenses réelles d'aide médicale de l'État (droit commun + soins urgents)", V("ame_depense_reelle_2024") / 1e3,
        "Md€", "2024", "SENAT-SANTE-PLF2026", "M4", "près d'1,4 Md€", f"dont droit commun {V('ame_droit_commun_2024')} M€")
    res("IMMI-04", "fin 2024", "Bénéficiaires de l'AME de droit commun", V("ame_beneficiaires_fin2024"), "personnes", "2024",
        "SENAT-SANTE-PLF2026", "M4", "près de 500 000", "461 833 au 31 mars 2025")
    res("IMMI-04", "2014 → 2024", "Hausse des dépenses réelles d'AME en dix ans", V("ame_hausse_10ans"), "%", "2024", "SENAT-SANTE-PLF2026",
        "M4", "« deux fois plus qu'il y a 15 ans » (bénéficiaires)")
    res("IMMI-04", "suppression", "Économie brute maximale si l'AME de droit commun disparaît sans compensation",
        V("ame_droit_commun_2024"), "M€", "2024", "SENAT-SANTE-PLF2026", "M4", "700 M€ d'économies (programme)",
        "ESTIMATION, non fiable à 100 % : borne haute ; le remplacement par une aide d'urgence et le report de soins vers l'hôpital réduisent l'économie nette")


def ifop():
    res("IMMI-05", "Ifop, août-septembre 2025", "Musulmans approuvant « tout ou partie » des positions islamistes", V("ifop_38"), "%", "2025",
        "IFOP-ISLAM-2025", "M5", "38 % (contre 19 % il y a trente ans)",
        f"échantillon de {V('ifop_echantillon')} musulmans : marge d'erreur d'environ ±3 points ; le 19 % de 1998 mesurait des « positions intégristes », question différente")


def naissances():
    d = pd.read_excel(BRUT / "insee/demo-naiss-natio-pays-2.xlsx", sheet_name="Figure 1", header=None)
    annees = [int(str(int(a))[:4]) for a in d.iloc[2, 1:]]
    lig = lambda texte: pd.Series(pd.to_numeric(d[d[0].astype(str).str.strip() == texte].iloc[0, 1:]).values, index=annees)
    fr2, mixte, etr2 = lig("Les deux parents français"), lig("Un parent français, un parent étranger"), lig("Les deux parents étrangers")
    au_moins_un = mixte + etr2
    for a, b in [(1998, 2018), (2002, 2022), (2003, 2023)]:
        res("IMMI-06", f"{a} → {b}", "Naissances de deux parents français", (fr2[b] / fr2[a] - 1) * 100, "%", str(b),
            "INSEE-NAISSANCES-NATIONALITE", "M6", "-13,7 % en vingt ans", f"{fr2[a]:.0f} → {fr2[b]:.0f}")
        res("IMMI-06", f"{a} → {b}", "Naissances d'au moins un parent étranger", (au_moins_un[b] / au_moins_un[a] - 1) * 100, "%",
            str(b), "INSEE-NAISSANCES-NATIONALITE", "M6", "+63 % en vingt ans", f"{au_moins_un[a]:.0f} → {au_moins_un[b]:.0f}")
    total = (fr2 + au_moins_un)
    res("IMMI-06", "2025", "Part des naissances d'au moins un parent étranger", au_moins_un[2025] / total[2025] * 100, "%", "2025",
        "INSEE-NAISSANCES-NATIONALITE", "M6", "", "série rompue en 2023 : le « second parent » peut être une femme")
    b = L.eurostat(BRUT / "eurostat/demo_gind_fr.json").set_index("time").valeur
    res("IMMI-06", "2010 → 2025", "Baisse du nombre de naissances", (1 - b["2025"] / b["2010"]) * 100, "%", "2025", "EUROSTAT-NAISSANCES",
        "M6", "« près de 25 % de naissances en moins qu'en 2010 »", f"{b['2010']:.0f} → {b['2025']:.0f}")
    return fr2, au_moins_un


def graphique(f):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPH.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#b9b8b3", "xtick.color": "#52514e", "ytick.color": "#52514e"})
    ans = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
    motifs = [("FAM", "Famille", "#2a78d6"), ("EDUC", "Études", "#eb6834"), ("EMP", "Travail", "#1baf7a"),
              ("OTH", "Humanitaire et autres", "#eda100")]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
    bas = pd.Series(0.0, index=ans)
    for code, nom, coul in motifs:
        v = f.loc[ans, code] / 1e3
        ax.bar(ans, v, bottom=bas, color=coul, label=nom, width=0.66, edgecolor="white", linewidth=1)
        bas += v
    for a in ans:
        ax.text(a, bas[a] + 4, f"{f.loc[a, 'EMP'] / f.loc[a, 'TOTAL'] * 100:.0f} % travail", ha="center", fontsize=8, color="#0b0b0b")
    ax.set_ylabel("Premiers titres de séjour (milliers)")
    ax.legend(frameon=False, ncol=4, loc="upper left", fontsize=8.5)
    ax.set_ylim(0, 430)
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Premiers titres de séjour en France par motif", loc="left", fontsize=12, color="#0b0b0b")
    fig.text(0.01, 0.01, "Ressortissants de pays tiers, titres d'au moins 3 mois. Source : Eurostat, migr_resfirst", fontsize=8,
             color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPH / "premiers_titres_motifs.png")
    plt.close(fig)


def main():
    verifier_pdf()
    f = titres()
    division_par_huit(f)
    oqtf()
    ame()
    ifop()
    naissances()
    graphique(f)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
