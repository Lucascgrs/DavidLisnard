"""Thème 7 — Santé et hôpital : calculs à partir de brut/.

python -m verification calculer 7   → calculs/resultats.csv
"""
import csv
import json
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
UE27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT",
        "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
OCDE38 = ["AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL",
          "IRL", "ISR", "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN",
          "ESP", "SWE", "CHE", "TUR", "GBR", "USA"]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def apl():
    d = pd.read_excel(BRUT / "drees/APL_medecins_generalistes.xlsx", sheet_name="APL 2024", header=None, skiprows=10)
    d = d.iloc[:, [0, 2, 7]]
    d.columns = ["commune", "apl", "pop"]
    d["apl"], d["pop"] = pd.to_numeric(d["apl"], errors="coerce"), pd.to_numeric(d["pop"], errors="coerce")
    d = d.dropna()
    for seuil, nom in [(2.5, "zone sous-dense (seuil DREES, moins de 2,5 consultations par an et par habitant)"),
                       (4.0, "moins de 4 consultations par an et par habitant (seuil large)")]:
        pop = d.loc[d.apl < seuil, "pop"].sum() / d["pop"].sum() * 100
        com = (d.apl < seuil).mean() * 100
        res("SANTE-01", f"APL 2024, {nom}", "Part de la population concernée", pop, "%", "2024", "DREES-APL-GENERALISTES", "M1",
            "87 % du territoire / des Français", f"part des communes concernées : {com:.1f} %")


def personnel():
    e = pd.read_csv(BRUT / "drees/effectifs_salaries_hospitaliers.csv", sep=";")
    x = e[e.annee == e.annee.max()]
    det = x.dropna(subset=["professions_detaillees"]).groupby("professions_detaillees").effectifs.sum()
    total = det.sum()
    admin = det["6 - Filière administrative"]
    autres_ns = det["72 - Autres non soignants"]
    an = str(e.annee.max())
    res("SANTE-02", f"public + privé, {an}", "Part des non-soignants (filière administrative + autres non soignants)", (admin + autres_ns) / total * 100,
        "%", an, "DREES-EFFECTIFS-HOSPITALIERS", "M2", "un tiers", f"{admin + autres_ns:.0f} sur {total:.0f} salariés")
    res("SANTE-02", f"public + privé, {an}", "Part de la seule filière administrative", admin / total * 100, "%", an,
        "DREES-EFFECTIFS-HOSPITALIERS", "M2", "un tiers")


def depense():
    h = L.eurostat(BRUT / "eurostat/hlth_sha11_hf.json")
    an = "2024"  # dernière année renseignée pour la plupart des pays (2025 : 17 pays seulement)
    p = h[(h.time == an) & (h.unit == "PC_GDP")].set_index("geo").valeur
    s = p[p.index.isin(UE27)].sort_values(ascending=False)
    res("SANTE-03", f"UE à 27, {an}", "Dépense courante de santé, % du PIB (France)", p["FR"], "% du PIB", an, "EUROSTAT-DEPENSE-SANTE", "M3",
        "« plus que ses voisins » ; 12 % du PIB", f"rang {list(s.index).index('FR') + 1}/{len(s)} ; Allemagne {p['DE']} % ; 1er {s.index[0]} {s.iloc[0]} % ; UE {p.get('EU27_2020', float('nan'))} %")
    q = h[(h.time == an) & (h.unit == "PPS_HAB")].set_index("geo").valeur
    s2 = q[q.index.isin(UE27)].sort_values(ascending=False)
    res("SANTE-03", f"UE à 27, {an}", "Rang de la France, dépense de santé par habitant (standard de pouvoir d'achat)",
        list(s2.index).index("FR") + 1, "rang", an, "EUROSTAT-DEPENSE-SANTE", "M3", "« plus que ses voisins »",
        f"devant : {', '.join(s2.index[:list(s2.index).index('FR')])}")
    m = h[(h.time == an) & (h.unit == "MIO_EUR")].set_index("geo").valeur
    if "EU27_2020" in p:
        ecart = (p["FR"] - p["EU27_2020"]) / 100 * (m["FR"] / (p["FR"] / 100)) / 1e3
        res("SANTE-03", f"France, {an}", "Dépense en plus de la moyenne de l'UE (écart de % du PIB × PIB)", ecart, "Md€", an,
            "EUROSTAT-DEPENSE-SANTE", "M3", "60 Md€ de plus que la moyenne européenne")


def ocde():
    def series(f):
        j = json.loads((BRUT / f).read_text(encoding="utf-8"))
        return {s["series_code"]: dict(zip(s["period"], s["value"])) for s in j["series"]["docs"]}
    m = series("ocde/medecins.json")
    g = series("ocde/diplomes.json")
    for nom, src, motif, lis in [("Médecins en exercice pour 1 000 habitants", "OCDE-MEDECINS", ".HSE.10P3HB._Z._Z.PHYS._Z.P._Z", "3,2 (26e de l'OCDE)"),
                                 ("Diplômés en médecine pour 100 000 habitants", "OCDE-DIPLOMES", ".HSG.10P5HB._Z._Z.PHYS._Z._Z._Z", "9,5 (30e sur 36)")]:
        base = m if src == "OCDE-MEDECINS" else g
        vals = {}
        for code, ser in base.items():
            if code.endswith(motif) and code.split(".")[0] in OCDE38:
                pts = [(a, v) for a, v in ser.items() if v not in (None, "NA")]
                if pts:
                    vals[code.split(".")[0]] = sorted(pts)[-1]
        if "FRA" not in vals:
            continue
        an_fr, v_fr = vals["FRA"]
        meme = {p: v for p, (a, v) in vals.items() if a == an_fr}
        s = pd.Series(meme).sort_values(ascending=False)
        res("SANTE-04", f"OCDE, {an_fr}", nom, v_fr, "valeur", an_fr, src, "M4", lis,
            f"rang {list(s.index).index('FRA') + 1}/{len(s)} pays ayant une donnée pour {an_fr} ; médiane {s.median():.1f}")


def main():
    apl()
    personnel()
    depense()
    ocde()
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
