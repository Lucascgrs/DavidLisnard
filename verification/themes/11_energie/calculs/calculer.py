"""Thème 11 — Énergie et nucléaire : calculs à partir de brut/.

python -m verification calculer 11   → calculs/resultats.csv, calculs/graphiques/
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
CSPE, ANNEXE = "cre/250710_2025-180_CSPE_2025-2026.pdf", "cre/250710_2025-180_CSPE_2025-2026_Annexe_1.pdf"
# Chiffres lus dans les PDF et pages HTML : (fichier, phrase exacte vérifiée, valeur)
LUS = {
    "accise_menages_2026": ("bofip/BOI-RES-EAT-000240-20251224.html", "30,85 €/MWh pour la catégorie « ménages et assimilés »", 30.85),
    "accise_pme_2026": ("bofip/BOI-RES-EAT-000240-20251224.html", "26,58 €/MWh pour la catégorie « PME »", 26.58),
    "accise_reduits": ("bofip/BOI-RES-EAT-000240-20251224.html", "différents tarifs réduits et nuls d’accise sur l’électricité s’échelonnant de 0 €/MWh à 12 €/MWh", 12),
    "ticfe_2019": ("assemblee/QANR5L15QE16278.pdf", "s'applique un tarif unique de 22,5 €/MWh pour les ménages", 22.5),
    "stromsteuer": ("allemagne/stromstg_3.html", "Die Steuer beträgt 20,50 Euro für eine Megawattstunde", 20.50),
    "stromsteuer_allegement": ("allemagne/stromstg_9b.html", "Die Steuerentlastung beträgt 20 Euro für eine Megawattstunde", 20),
    "cspe_2026": (CSPE, "la CRE procède à l’évaluation annuelle des charges à compenser en 2026, qui s’élèvent à 12,94 Mds€", 12.94),
    "eolien_terrestre_2026": (CSPE, "1. Eolien terrestre -3 422,6 -68,9 929,6 1 300,1", 1300.1),
    "eolien_terrestre_2023": (CSPE, "1. Eolien terrestre -3 422,6", -3422.6),
    "cout_achat_unitaire_2024": (ANNEXE, "Coût d'achat unitaire en 2024 (€/MWh) 218,5 105,3 97,5 178,2", 97.5),
    "cout_achat_unitaire_2026": (ANNEXE, "Coût d'achat unitaire (€/MWh) 232,8 111,1 100,6 184,9", 100.6),
    "colonnes_annexe": (ANNEXE, "Cogénération gaz Hydraulique Eolien à terre Eolien en mer", 0),
    "schiste_france_tcf": ("eia/worldshalegas_overview.pdf", "France 727 137 118 4.7", 137),
    "schiste_pologne_tcf": ("eia/worldshalegas_overview.pdf", "Poland 763 148 65 3.3", 148),
    "dpe_coefficient": ("assemblee/QANR5L17QE9713.pdf", "(coefficient énergie primaire ou CEP) à 1,9, anciennement 2,3", 2.3),
    "ppe_14_reacteurs": ("ppe/PPE_2020.pdf", "14 réacteurs nucléaires seront arrêtés d’ici 2035, dont ceux de la centrale de Fessenheim", 14),
    "sddr_raccordement_mer": ("cre/250918_Consultation_2025-08_SDDR_RTE.pdf", "pour le raccordement de parcs éoliens en mer s’élèvent à 37 Md€ pour les actifs mis en service sur cette période", 37),
    "sddr_apres_2040": ("cre/250918_Consultation_2025-08_SDDR_RTE.pdf", "auxquelles s’ajoutent 10 Md€ pour les raccordements qui seront mis en service à partir de 2040", 10),
}
TCF_EN_MILLIARDS_M3 = 28.316846592  # 1 000 milliards de pieds cubes = 28,3168 milliards de m³ (1 pied³ = 0,0283168 m³)


def _texte(f: Path) -> str:
    if f.suffix == ".html":
        t = html.unescape(re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8", errors="replace")))
    else:
        import logging
        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        t = " ".join((p.extract_text() or "") for p in PdfReader(f).pages)
    return re.sub(r"\s+", "", t.replace("‑", "-"))


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


def m1():
    e = L.eurostat(BRUT / "eurostat/nrg_bal_peh_fr.json").pivot_table(index="time", columns="siec", values="valeur")
    part = e.div(e.TOTAL, axis=0) * 100
    src = "EUROSTAT-PRODUCTION-ELEC"
    res("NRJ-01", "2019", "Part du nucléaire dans la production brute d'électricité", part.N900H["2019"], "%", "2019", src, "M1", "70 %")
    res("NRJ-01", "2020", "Part du nucléaire dans la production brute d'électricité", part.N900H["2020"], "%", "2020", src, "M1", "70 %",
        "année de la tribune (novembre 2020), marquée par la crise sanitaire")
    for a in ["2022", "2024"]:
        res("NRJ-02", a, "Part du nucléaire et des renouvelables dans la production brute d'électricité", part.N900H[a] + part.RA000[a], "%", a, src,
            "M1", "plus de 90 %", f"fossiles : {part.FE[a]:.1f} %")


def m2():
    f = L.fmi(BRUT / "fmi/ngdpd_fra_monde.json").pivot_table(index="time", columns="pays", values="valeur")
    p = L.fmi(BRUT / "fmi/pppsh_fra.json").pivot_table(index="time", columns="pays", values="valeur")
    for a in ["2024", "2025"]:
        res("NRJ-03", f"{a}, aux taux de change courants", "Part de la France dans le PIB mondial", f.FRA[a] / f.WEOWORLD[a] * 100, "%", a,
            "FMI-PIB-DOLLARS", "M2", "2,4 %")
        res("NRJ-03", f"{a}, en parité de pouvoir d'achat", "Part de la France dans le PIB mondial", p.FRA[a], "%", a, "FMI-PIB-PPA-PART", "M2", "2,4 %")
    o = pd.read_csv(BRUT / "owid/owid-co2-data.csv", usecols=["country", "year", "co2", "consumption_co2"])
    o = o[o.country.isin(["France", "World"])].pivot_table(index="year", columns="country", values=["co2", "consumption_co2"])
    for a in [2023, 2025]:
        res("NRJ-03", f"{a}, émissions territoriales", "Part de la France dans les émissions mondiales de CO2 fossile",
            o[("co2", "France")][a] / o[("co2", "World")][a] * 100, "%", str(a), "GCB-OWID-CO2", "M2", "0,7 %")
    res("NRJ-03", "2024, émissions de consommation", "Part de la France dans les émissions mondiales de CO2, importations comprises",
        o[("consumption_co2", "France")][2024] / o[("consumption_co2", "World")][2024] * 100, "%", "2024", "GCB-OWID-CO2", "M2",
        "« il faut rajouter les produits importés »")


def m3():
    g = L.eurostat(BRUT / "eurostat/nama_10_gdp_ue.json")
    g = g[g.geo == "EU27_2020"].set_index("time").valeur
    for d, f in [("1995", "2025"), ("1995", "2024")]:
        res("NRJ-04", f"{d} → {f}", "Croissance du PIB en volume de l'UE à 27", (g[f] / g[d] - 1) * 100, "%", f, "EUROSTAT-PIB-VOLUME", "M3",
            "« 70 % sur 30 ans, un peu plus »", "la série en volume commence en 1995")
    h = L.eurostat(BRUT / "eurostat/env_air_gge_ue.json")
    h = h[h.geo == "EU27_2020"].pivot_table(index="time", columns=["airpol", "src_crf"], values="valeur")
    for d in ["1994", "1990"]:
        res("NRJ-04", f"{d} → 2024", "Évolution des émissions de gaz à effet de serre de l'UE à 27 (hors UTCATF, aviation internationale comprise)",
            (h[("GHG", "TOTX4_MEMO")]["2024"] / h[("GHG", "TOTX4_MEMO")][d] - 1) * 100, "%", "2024", "EUROSTAT-GES", "M3", "-37 %")
    res("NRJ-04", "1994 → 2024", "Évolution des émissions de CO2 de l'UE à 27 (hors UTCATF)",
        (h[("CO2", "TOTX4_MEMO")]["2024"] / h[("CO2", "TOTX4_MEMO")]["1994"] - 1) * 100, "%", "2024", "EUROSTAT-GES", "M3", "-37 %")


def prix_entreprises():
    p = L.eurostat(BRUT / "eurostat/nrg_pc_205_fr.json")
    p = p[p.geo == "FR"].copy()
    p["an"] = p.time.str[:4]
    return p.pivot_table(index="nrg_cons", columns=["tax", "an"], values="valeur") * 1000  # €/kWh → €/MWh


def m4(a):
    src = "EUROSTAT-PRIX-ENTREPRISES"
    noms = {"TOT_KWH": "toutes tranches", "MWH500-1999": "500 à 2 000 MWh/an", "MWH2000-19999": "2 à 20 GWh/an",
            "MWH70000-149999": "70 à 150 GWh/an", "MWH_GE150000": "plus de 150 GWh/an"}
    for b, nom in noms.items():
        res("NRJ-05", f"France, {nom}", "Hausse du prix hors TVA, moyenne 2024 / moyenne 2021", (a.loc[b, ("X_VAT", "2024")] / a.loc[b, ("X_VAT", "2021")] - 1) * 100,
            "%", "2024", src, "M4", "+67 %")
        res("NRJ-05", f"France, {nom}", "Prix de l'électricité hors TVA, moyenne 2024", a.loc[b, ("X_VAT", "2024")], "€/MWh", "2024", src, "M4",
            "165 €/MWh", f"toutes taxes comprises (TVA récupérable comprise) : {a.loc[b, ('I_TAX', '2024')]:.0f} €/MWh")
    eia = pd.read_excel(BRUT / "eia/epa_02_04.xlsx", header=None)
    eia = eia.iloc[4:15].set_axis(["an", "residentiel", "commercial", "industriel", "transport", "total"], axis=1)
    eia["an"] = eia.an.astype(int).astype(str)
    eia = eia.set_index("an").astype(float)
    usd = L.eurostat(BRUT / "eurostat/ert_bil_eur_a_usd.json").set_index("time").valeur
    for sect, nom in [("industriel", "industrie"), ("commercial", "commerce et services")]:
        v = eia.loc["2024", sect] * 10 / usd["2024"]  # cents/kWh → $/MWh → €/MWh
        res("NRJ-05", f"États-Unis, {nom}", "Prix moyen de l'électricité, converti en euros", v, "€/MWh", "2024", "EIA-PRIX-SECTEURS ; EUROSTAT-CHANGE-USD",
            "M4", "73 €/MWh" if sect == "industriel" else "", f"{eia.loc['2024', sect]:.2f} cents de dollar par kWh ; 1 € = {usd['2024']:.4f} $")
    return eia.loc["2024", "industriel"] * 10 / usd["2024"]


def m5():
    res("NRJ-06", "ménages, 1er février 2026", "Tarif de l'accise sur l'électricité (majoration ZNI comprise)", V("accise_menages_2026"), "€/MWh", "2026",
        "BOFIP-ACCISE-2026", "M5", "30,35 €/MWh")
    res("NRJ-06", "ménages, 2026 / 2019", "Hausse de l'accise depuis 2019", (V("accise_menages_2026") / V("ticfe_2019") - 1) * 100, "%", "2026",
        "BOFIP-ACCISE-2026 ; AN-QE16278-TICFE", "M5", "+37 %", f"2019 : {V('ticfe_2019')} €/MWh (TICFE)")
    res("NRJ-06", "Allemagne, ménages", "Taxe sur l'électricité (Stromsteuer), tarif normal", V("stromsteuer"), "€/MWh", "2026", "STROMSTG-3", "M5")
    res("NRJ-06", "Allemagne, industrie manufacturière", "Stromsteuer après allègement", V("stromsteuer") - V("stromsteuer_allegement"), "€/MWh", "2026",
        "STROMSTG-3 ; STROMSTG-9B", "M5", "0,5 €/MWh pour son industrie")
    res("NRJ-06", "France, PME et haute puissance", "Tarif normal de l'accise (majoration ZNI comprise)", V("accise_pme_2026"), "€/MWh", "2026",
        "BOFIP-ACCISE-2026", "M5", "", f"tarifs réduits de 0 à {V('accise_reduits'):.0f} €/MWh pour certaines activités (industrie électro-intensive notamment)")


def m6():
    src = "CRE-CSPE-2026"
    res("NRJ-07", "prévision 2026", "Charges de service public de l'énergie à compenser", V("cspe_2026"), "Md€", "2026", src, "M6", "12,9 Md€")
    res("NRJ-07", "prévision 2026", "Charges de soutien à l'éolien terrestre", V("eolien_terrestre_2026") / 1000, "Md€", "2026", src, "M6", "1,3 Md€",
        f"soit {V('eolien_terrestre_2026') / 1000 / V('cspe_2026') * 100:.0f} % du total")
    res("NRJ-07", "constaté 2023", "Charges de soutien à l'éolien terrestre (négatives : reversement à l'État)", V("eolien_terrestre_2023") / 1000, "Md€",
        "2023", src, "M6", "", "prix de marché supérieurs aux tarifs garantis")
    res("NRJ-07", "obligation d'achat, 2024", "Coût d'achat unitaire de l'éolien terrestre", V("cout_achat_unitaire_2024"), "€/MWh", "2024",
        "CRE-CSPE-2026-ANNEXE1", "M6", "97,5 €/MWh « en 2025 »", f"prévision 2026 : {V('cout_achat_unitaire_2026')} €/MWh")


def m7():
    gz = L.eurostat(BRUT / "eurostat/nrg_cb_gas_fr.json").set_index("time").valeur / 1000  # Mm³ → milliards de m³
    stock = V("schiste_france_tcf") * TCF_EN_MILLIARDS_M3
    res("NRJ-08", "EIA 2013", "Gaz de schiste techniquement récupérable, France", stock, "milliards de m³", "2013", "EIA-GAZ-SCHISTE-2013", "M7",
        "3 879 milliards de m³", f"{V('schiste_france_tcf')} Tcf ; Pologne : {V('schiste_pologne_tcf')} Tcf")
    for a in ["2024", "2019"]:
        res("NRJ-08", f"consommation {a}", "Années de consommation nationale de gaz couvertes", stock / gz[a], "ans", a,
            "EIA-GAZ-SCHISTE-2013 ; EUROSTAT-GAZ", "M7", "95 ans", f"consommation intérieure {a} : {gz[a]:.1f} milliards de m³")


def m8():
    c = V("dpe_coefficient")
    res("NRJ-09", "DPE jusqu'au 31/12/2025", "Coefficient de conversion de l'électricité en énergie primaire", c, "", "2025", "AN-QE9713-DPE", "M8",
        "malus de 230 %", f"soit {(c - 1) * 100:.0f} % de plus que l'énergie finale ; 1,9 depuis le 1er janvier 2026")
    res("NRJ-10", "PPE d'avril 2020", "Réacteurs à arrêter d'ici 2035", V("ppe_14_reacteurs"), "réacteurs", "2020", "PPE-2020", "M8", "quatorze")
    res("NRJ-11", "SDDR 2025, scénario de référence", "Investissements de raccordement des parcs éoliens en mer, mis en service 2025-2039",
        V("sddr_raccordement_mer"), "Md€", "2039", "CRE-CONSULTATION-SDDR", "M8", "37 Md€", f"+ {V('sddr_apres_2040'):.0f} Md€ pour les mises en service à partir de 2040")


def graphique(a, us_industrie):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPHIQUES.mkdir(exist_ok=True)
    ordre = [("MWH_LT20", "< 20 MWh"), ("MWH20-499", "20-500 MWh"), ("MWH500-1999", "0,5-2 GWh"), ("MWH2000-19999", "2-20 GWh"),
             ("MWH20000-69999", "20-70 GWh"), ("MWH70000-149999", "70-150 GWh"), ("MWH_GE150000", "> 150 GWh")]
    vals = [a.loc[b, ("X_VAT", "2024")] for b, _ in ordre]
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    barres = ax.bar([n for _, n in ordre], vals, color="#2a78d6", width=0.6)
    for r, v in zip(barres, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 4, f"{v:.0f}", ha="center", fontsize=9, color="#333")
    moy = a.loc["TOT_KWH", ("X_VAT", "2024")]
    ax.axhline(moy, color="#eb6834", lw=1.5, ls="--")
    ax.text(6.45, moy + 5, f"moyenne française, toutes tranches : {moy:.0f}", ha="right", fontsize=9, color="#333")
    ax.axhline(us_industrie, color="#8a8984", lw=1.5, ls=":")
    ax.text(6.45, 245, f"pointillés gris : industrie américaine, moyenne (EIA) : {us_industrie:.0f}", ha="right", fontsize=9, color="#333")
    ax.set_ylabel("€/MWh, hors TVA")
    ax.set_xlabel("consommation annuelle de l'entreprise")
    ax.set_title("Prix de l'électricité des entreprises françaises en 2024, selon leur consommation", loc="left", fontsize=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    ax.set_axisbelow(True)
    fig.text(0.01, 0.01, "Sources : Eurostat (nrg_pc_205, moyenne des deux semestres) ; EIA, Electric Power Annual, tableau 2.4 ; BCE (taux de change).",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPHIQUES / "prix_electricite_entreprises.png")
    plt.close(fig)


def main():
    verifier_documents()
    m1()
    m2()
    m3()
    a = prix_entreprises()
    us = m4(a)
    m5()
    m6()
    m7()
    m8()
    graphique(a, us)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
