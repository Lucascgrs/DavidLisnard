"""Thème 8 — École et enseignement : calculs à partir de brut/.

python -m verification calculer 8   → calculs/resultats.csv
"""
import csv
import json
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
UE = {"Austria": "AUT", "Belgium": "BEL", "Bulgaria": "BGR", "Croatia": "HRV", "Cyprus": "CYP", "Czech Republic": "CZE",
      "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN",
      "Ireland": "IRL", "Italy": "ITA", "Latvia": "LVA", "Lithuania": "LTU", "Malta": "MLT", "Netherlands": "NLD", "Poland": "POL",
      "Portugal": "PRT", "Romania": "ROU", "Slovak Republic": "SVK", "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE"}
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def pisa():
    from pypdf import PdfReader
    t = "\n" + "\n".join((p.extract_text() or "") for p in PdfReader(BRUT / "ocde/PISA2022_tableau_I.2.1_MEXT.pdf").pages)
    scores = {}
    for pays in UE:
        m = re.search(r"\n" + re.escape(pays) + r" (\d{3})\n", t) or re.search(r"\n(\d{3}) " + re.escape(pays) + r"[\* \n]", t)
        if m:
            scores[pays] = int(m.group(1))
    s = pd.Series(scores).sort_values(ascending=False)
    rang = list(s.index).index("France") + 1
    res("ECOLE-01", "PISA 2022, mathématiques, pays de l'UE participants", "Score moyen de la France", s["France"], "points", "2022",
        "OCDE-PISA-2022-MEXT", "M1", "« derniers au classement PISA dans l'Europe »",
        f"rang {rang}/{len(s)} ; derrière la France : {', '.join(s.index[rang:])} ; moyenne OCDE 472")
    wb = json.loads((BRUT / "banque_mondiale/LO.PISA.MAT.json").read_text(encoding="utf-8"))[1]
    fr = {x["date"]: x["value"] for x in wb if x["countryiso3code"] == "FRA" and x["value"] is not None}
    res("ECOLE-01", "PISA 2018 → 2022, mathématiques", "Variation du score de la France", s["France"] - fr["2018"], "points", "2022",
        "BM-PISA-2000-2018 ; OCDE-PISA-2022-MEXT", "M1", "« nous voit dégrader chaque année »",
        f"2018 : {fr['2018']:.0f} ; 2003 : {fr.get('2003', float('nan')):.0f} (série Banque mondiale)")


def depense():
    c = L.eurostat(BRUT / "eurostat/gov_10a_exp_education_fr.json")
    e = c[(c.cofog99 == "GF09") & (c.unit == "MIO_EUR")].set_index("time").valeur
    d = L.eurostat(BRUT / "eurostat/nama_10_gdp_deflateur_fr.json")
    defl = d[d.unit == "PD15_EUR"].set_index("time").valeur
    for debut in ("2000", "2001"):
        fin = "2024"
        nom = (e[fin] / e[debut] - 1) * 100
        reel = (e[fin] / defl[fin]) / (e[debut] / defl[debut]) * 100 - 100
        res("ECOLE-02", f"{debut} → {fin}, euros courants", "Hausse de la dépense publique d'éducation", nom, "%", fin,
            "EUROSTAT-COFOG-EDUCATION", "M2", "+40 % en vingt-cinq ans", f"{e[debut] / 1e3:.1f} → {e[fin] / 1e3:.1f} Md€")
        res("ECOLE-02", f"{debut} → {fin}, euros constants (déflateur du PIB)", "Hausse de la dépense publique d'éducation", reel, "%", fin,
            "EUROSTAT-COFOG-EDUCATION ; EUROSTAT-PRIX-PIB", "M2", "+40 % en vingt-cinq ans")
    p = c[(c.cofog99 == "GF09") & (c.unit == "PC_GDP")].set_index("time").valeur
    res("ECOLE-02", "2000 → 2024", "Dépense publique d'éducation, % du PIB", p["2024"], "% du PIB", "2024", "EUROSTAT-COFOG-EDUCATION", "M2", "",
        f"{p['2000']} % en 2000")
    el = L.eurostat(BRUT / "eurostat/educ_uoe_enra01_fr.json").pivot_table(index="time", columns="isced11", values="valeur")
    tot = el[["ED1", "ED2", "ED3"]].sum(axis=1)
    res("ECOLE-02", "2013 → 2024", "Évolution du nombre d'élèves (primaire, collège, lycée)", (tot["2024"] / tot["2013"] - 1) * 100, "%",
        "2024", "EUROSTAT-ELEVES", "M2", "", "le nombre d'élèves est stable : la hausse de la dépense n'est pas due à un afflux d'élèves")


def budget():
    v = pd.read_csv(BRUT / "budget/plf2026_budget_vert.csv", sep=";")
    v = v[(v.type_depense == "Crédits budgétaires") & (v["mission"] == "Enseignement scolaire")]
    m = v["lfi_2025_cp_ou_prevision_2025_si_depense_fiscale"].sum() / 1e9
    res("ECOLE-03", "LFI 2025, hors pensions", "Crédits de la mission Enseignement scolaire", m, "Md€", "2025", "BUDGET-VERT-PLF2026", "M3",
        "« pas 60 milliards […] moi j'arrive à 30 »", "dont l'essentiel en salaires d'enseignants")


def main():
    pisa()
    depense()
    budget()
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
