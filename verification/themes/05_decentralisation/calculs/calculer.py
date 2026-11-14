"""Thème 5 — Décentralisation et collectivités : calculs à partir de brut/.

python -m verification calculer 5   → calculs/resultats.csv
"""
import csv
import json
import re
from pathlib import Path

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"

LUS_DANS_LES_PDF = {
    "crfp_communes_2014": ("assemblee/QE50991_contribution_2014_2016.pdf", "la contribution des communes s'est élevée à 558 M€ en 2014", 0.558),
    "crfp_epci_2014": ("assemblee/QE50991_contribution_2014_2016.pdf", "Celle des EPCI a atteint 252 M€ en 2014", 0.252),
    "crfp_bloc_2015_2016": ("assemblee/QE95791_contribution_2017.pdf", "à hauteur de 2 071 millions d'euros par an", 2.071),
    "crfp_bloc_2017": ("assemblee/QE95791_contribution_2017.pdf", "un effort ramené à 1 035,5 millions d'euros", 1.0355),
}


def verifier_pdf():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    for cle, (f, extrait, _) in LUS_DANS_LES_PDF.items():
        t = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
        if re.sub(r"\s+", "", extrait) not in t:
            raise SystemExit(f"Introuvable dans le PDF : {cle} ({f})")


V = lambda k: LUS_DANS_LES_PDF[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def dgf():
    # Baisse annuelle de la DGF du bloc communal par rapport à 2013 (montants cumulés de la contribution)
    baisse = {2014: V("crfp_communes_2014") + V("crfp_epci_2014")}
    baisse[2015] = baisse[2014] + V("crfp_bloc_2015_2016")
    baisse[2016] = baisse[2015] + V("crfp_bloc_2015_2016")
    baisse[2017] = baisse[2016] + V("crfp_bloc_2017")
    for an in range(2018, 2027):
        baisse[an] = baisse[2017]  # la baisse n'a jamais été rendue : DGF stabilisée à son niveau de 2017
    src = "AN-QE-50991 ; AN-QE-95791"
    for fin in (2022, 2025, 2026):
        cumul = sum(v for a, v in baisse.items() if a <= fin)
        res("DEC-01", f"2014 → {fin}, euros courants", "Cumul des baisses de DGF du bloc communal (par rapport à 2013)", cumul, "Md€",
            str(fin), src, "M1", "47 Md€ (2022) ; plus de 80 Md€ (2026)", f"baisse annuelle stabilisée à {baisse[2017]:.2f} Md€ depuis 2017")
    # Perte due à la non-indexation depuis 2018 (estimation)
    lire = lambda f: {r["exer"][:4]: r["total"] / 1e9 for r in json.loads((BRUT / f).read_text(encoding="utf-8"))["results"]}
    com, gfp = lire("ofgl/dgf_communes_par_annee.json"), lire("ofgl/dgf_intercommunalites_par_annee.json")
    prix = L.eurostat(BRUT / "eurostat/prc_hicp_aind_fr.json").set_index("time").valeur
    dgf18 = com["2018"] + gfp["2018"]
    perte = 0.0
    for an in range(2019, 2026):
        a = str(an)
        perte += dgf18 * prix[a] / prix["2018"] - (com[a] + gfp[a])
    res("DEC-01", "2018 → 2025", "DGF du bloc communal (communes + intercommunalités)", com["2025"] + gfp["2025"], "Md€", "2025",
        "OFGL-DGF-COMMUNES ; OFGL-DGF-GFP", "M1", "", f"2018 : {dgf18:.2f} Md€")
    res("DEC-01", "2019 → 2025", "Perte cumulée due à l'absence d'indexation sur les prix (DGF 2018 indexée − DGF réelle)", perte, "Md€",
        "2025", "OFGL-DGF-COMMUNES ; OFGL-DGF-GFP ; EUROSTAT-INFLATION", "M1", "",
        "ESTIMATION, non fiable à 100 % : l'État n'a jamais été tenu d'indexer la DGF ; ce manque à gagner n'est pas un prélèvement au sens strict")
    total = sum(v for a, v in baisse.items() if a <= 2025) + perte
    res("DEC-01", "2014 → 2025, baisses + non-indexation", "Total (méthode proche de celle de l'AMF)", total, "Md€", "2025",
        f"{src} ; OFGL-DGF-COMMUNES ; OFGL-DGF-GFP ; EUROSTAT-INFLATION", "M1", "plus de 80 Md€",
        "ESTIMATION, non fiable à 100 %")


def dette():
    q = L.eurostat(BRUT / "eurostat/gov_10q_ggdebt_fr_secteurs.json")
    p = q[q.unit == "PC_GDP"].pivot_table(index="time", columns="sector", values="valeur")
    m = q[q.unit == "MIO_EUR"].pivot_table(index="time", columns="sector", values="valeur")
    for t in ["2000-Q4", "2005-Q4", "2010-Q4", "2015-Q4", "2020-Q4", "2024-Q4", "2025-Q4", "2026-Q2"]:
        res("DEC-02", t, "Dette des administrations publiques locales, % du PIB", p.loc[t, "S1313"], "% du PIB", t[:4],
            "EUROSTAT-DETTE-LOCALE-TRIM", "M2", "8,9 % ; 9 % stable depuis 30-35 ans")
    for t in ["2024-Q4", "2025-Q4"]:
        res("DEC-02", t, "Part de la dette locale dans la dette publique", m.loc[t, "S1313"] / m.loc[t, "S13"] * 100, "%", t[:4],
            "EUROSTAT-DETTE-LOCALE-TRIM", "M2", "8 % / 9 % (92 % ou 91 % pour l'État et la Sécurité sociale)")


def depenses():
    e = L.eurostat(BRUT / "eurostat/gov_10a_main_secteurs.json")
    g = lambda geo, sec, unit, an="2024": e[(e.geo == geo) & (e.sector == sec) & (e.unit == unit) & (e.time == an)].valeur.sum()
    src = "EUROSTAT-DEPENSES-SECTEURS"
    res("DEC-03", "France, 2024", "Dépense des administrations locales, % du PIB", g("FR", "S1313", "PC_GDP"), "% du PIB", "2024", src, "M3",
        "11 % (moins de 11 %)")
    res("DEC-03", "UE à 27, 2024", "Dépense des administrations locales seules, % du PIB", g("EU27_2020", "S1313", "PC_GDP"), "% du PIB",
        "2024", src, "M3", "« presque 20 % » ; « 18 % chez nos voisins »")
    res("DEC-03", "UE à 27, 2024", "Dépense des administrations locales + États fédérés et régions autonomes, % du PIB",
        g("EU27_2020", "S1313", "PC_GDP") + g("EU27_2020", "S1312", "PC_GDP"), "% du PIB", "2024", src, "M3", "« presque 20 % »")
    res("DEC-03", "France, 2024", "Dépense locale / dépense publique totale", g("FR", "S1313", "MIO_EUR") / g("FR", "S13", "MIO_EUR") * 100,
        "%", "2024", src, "M3", "19 %", "dépenses non consolidées des sous-secteurs rapportées au total consolidé")
    res("DEC-03", "UE à 27, 2024", "Dépense locale seule / dépense publique totale",
        g("EU27_2020", "S1313", "MIO_EUR") / g("EU27_2020", "S13", "MIO_EUR") * 100, "%", "2024", src, "M3", "34 % / 35 %")
    res("DEC-03", "UE à 27, 2024", "Dépense locale + États fédérés / dépense publique totale",
        (g("EU27_2020", "S1313", "MIO_EUR") + g("EU27_2020", "S1312", "MIO_EUR")) / g("EU27_2020", "S13", "MIO_EUR") * 100, "%", "2024",
        src, "M3", "34 % / 35 %")
    for geo, nom in [("DE", "Allemagne"), ("IT", "Italie"), ("ES", "Espagne")]:
        res("DEC-03", f"{nom}, 2024", "Dépense des administrations locales seules, % du PIB", g(geo, "S1313", "PC_GDP"), "% du PIB", "2024",
            src, "M3", "", f"États fédérés / régions autonomes : {g(geo, 'S1312', 'PC_GDP')} % du PIB")


def main():
    verifier_pdf()
    dgf()
    dette()
    depenses()
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
