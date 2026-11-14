"""Thème 1 — Dette, dépense publique et fiscalité : tous les calculs, à partir des seuls fichiers de brut/.

python -m verification calculer 1

Écrit calculs/resultats.csv (une ligne par affirmation et par variante de périmètre) et calculs/graphiques/*.png.
Chaque ligne renvoie à la section de METHODE.md qui explique le calcul. Les chiffres lus dans un PDF (budget de
l'État, rapports) sont recopiés ici dans LUS_DANS_LES_PDF, avec la page ou la phrase d'origine : ils sont la seule
saisie manuelle, et `verifier_pdf()` contrôle qu'ils figurent bien dans le texte du PDF.
"""
import csv
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
GRAPH = ICI / "graphiques"

UE27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU",
        "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
OCDE38 = ["AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL",
          "IRL", "ISR", "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN",
          "ESP", "SWE", "CHE", "TUR", "GBR", "USA"]
ISO3_ISO2_UE = {"AUT": "AT", "BEL": "BE", "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE",
                "GRC": "EL", "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV", "LTU": "LT", "LUX": "LU", "NLD": "NL",
                "POL": "PL", "PRT": "PT", "SVK": "SK", "SVN": "SI", "ESP": "ES", "SWE": "SE"}

# Chiffres lus dans des PDF (fichier, phrase ou tableau exact à retrouver dans le texte, valeur en Md€ sauf mention).
LUS_DANS_LES_PDF = {
    "charge_etat_lfi2025": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "54 207 000 000", 54.207),
    "charge_etat_plf2026": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "58 615 000 000", 58.615),
    "charge_etat_lfi2026": ("senat/NP_EFE_PLF_2027.pdf", "58,0 milliards", 58.0),
    "charge_etat_revise2026": ("senat/NP_EFE_PLF_2027.pdf", "61,6 milliards", 61.6),
    "charge_etat_plf2027": ("senat/NP_EFE_PLF_2027.pdf", "71,9 milliards", 71.9),
    "ens_scolaire_plf2027": ("senat/NP_EFE_PLF_2027.pdf", "65,5 milliards", 65.5),
    "defense_plf2027": ("senat/NP_EFE_PLF_2027.pdf", "63,4 milliards", 63.4),
    "deficit_etat_2024": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "Déficit budgétaire 155,9", 155.9),
    "deficit_etat_2025_revise": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "Déficit budgétaire 155,9 139,0 130,5", 130.5),
    "recettes_etat_2024": ("budget/PLF2026_Voies_et_moyens_tome1.pdf", "Recettes totales de l’État 348,9", 348.9),
    "recettes_etat_2025_revise": ("budget/PLF2026_Voies_et_moyens_tome1.pdf", "Recettes totales de l’État 348,9 370,6 377,0", 377.0),
    "ir_net_lfi2025": ("budget/PLF2026_Voies_et_moyens_tome1.pdf", "Impôt net sur le revenu 88,0 94,5", 94.5),
    "cvae_etat_2025": ("budget/PLF2026_Voies_et_moyens_tome1.pdf", "la prévision s’établit à 4 069 M€", 4.069),
    "niches_nombre_plf2025": ("budget/PLF2025_Voies_et_moyens_tome2.pdf", "s’élève à 474", 474),
    "niches_cout_2025": ("budget/PLF2025_Voies_et_moyens_tome2.pdf", "et 85,1 Md€ en 2025", 85.1),
    "niches_ir_2025": ("budget/PLF2025_Voies_et_moyens_tome2.pdf", "Impôt sur le revenu 38 735 41 762 42 070", 42.07),
    "niches_nombre_plf2026": ("budget/PLF2026_Voies_et_moyens_tome2.pdf", "s’élève à 465", 465),
    "niches_cout_2026": ("budget/PLF2026_Voies_et_moyens_tome2.pdf", "et 88,3 Md€ en 2026", 88.3),
    "amortissement_mlt_2026": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "155,1 151,1 4,0 168,2 166,1 2,1 168,0 166,1 1,9 175,8", 175.8),
    "encours_negociable_fin2024": ("budget/PAP2026_Engagements_financiers_Etat.pdf", "2 145,1 2 277,8 2 430,0 2 601,6", 2601.6),
    "aides_senat_large_2023": ("senat/r24-808-1_synthese.pdf", "atteignent au moins 211 milliards d’euros en 2023", 211),
    "aides_senat_restreint_2023": ("senat/r24-808-1_synthese.pdf", "passe de 211 à 108 milliards", 108),
    "aides_hcsp_2023": ("hcsp/HCSP-2025-NA157-aides-entreprises.pdf", "111,9 milliards", 111.9),
    "aides_hcsp_europeen_2022": ("hcsp/HCSP-2025-NA157-aides-entreprises.pdf", "s’élevaient à 45 milliards d’euros en 2022", 45),
    "aides_igf_2024": ("hcsp/HCSP-2025-NA157-aides-entreprises.pdf", "à 88 milliards", 88),
    "aides_clerse_2019": ("clerse/capitalisme_sous_perfusion_2022.pdf", "à 157 mds", 157),
    "aides_clerse_pib_2000": ("clerse/capitalisme_sous_perfusion_2022.pdf", "passant de 3 % du PIB environ à 6,44 % en 2019", 3.0),
    "po_snf_fipeco_2022_pib": ("fipeco/PO_nets_Entreprises_2022.pdf", "soit 12,6 % du PIB", 12.6),
    "po_snf_nets_fipeco_2022_pib": ("fipeco/PO_nets_Entreprises_2022.pdf", "soit 10,4 % du PIB", 10.4),
    "po_snf_allemagne_2022_pib": ("fipeco/PO_nets_Entreprises_2022.pdf", "Allemagne (9,3 % du PIB)", 9.3),
    "ip_societes_fr_2022_pib": ("fipeco/Impots_production_2022.pdf", "ont représenté 3,3 % du PIB en France en 2022", 3.3),
    "ip_societes_ze_2022_pib": ("fipeco/Impots_production_2022.pdf", "la moyenne était de 1,5 % pour la zone euro", 1.5),
    "c3s_2022": ("fipeco/Impots_production_2022.pdf", "contribution sociale de solidarité des sociétés, pour 4,3 Md€", 4.3),
    "ir_non_imposes_2023_pct": ("dgfip/dgfip_stat_32_2025.pdf", "(45 %)", 55),  # 100 - 45 % imposés
    "ir_d10_part_2023_pct": ("dgfip/dgfip_stat_32_2025.pdf", "contribuant à 76 % de l’impôt net", 76),
}


def texte_pdf(rel: str) -> str:
    from pypdf import PdfReader
    t = " ".join((p.extract_text() or "") for p in PdfReader(BRUT / rel).pages)
    return re.sub(r"\s+", " ", t)


def verifier_pdf() -> list[str]:
    """Contrôle que chaque chiffre recopié d'un PDF y figure bien (à l'espace près)."""
    import logging
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache, manquants = {}, []
    for cle, (fichier, extrait, _) in LUS_DANS_LES_PDF.items():
        if fichier not in cache:
            cache[fichier] = re.sub(r"\s+", "", texte_pdf(fichier)).replace("’", "'")
        if re.sub(r"\s+", "", extrait).replace("’", "'") not in cache[fichier]:
            manquants.append(f"{cle} ({fichier} : « {extrait} »)")
    return manquants


def V(cle: str) -> float:
    return LUS_DANS_LES_PDF[cle][2]


RESULTATS: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    RESULTATS.append({"affirmation": aff, "variante": variante, "grandeur": grandeur,
                      "valeur": (int(valeur) if unite == "rang" else round(float(valeur), 2)), "unite": unite,
                      "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section, "note": note})


def rang(serie: pd.Series, pays: str) -> int:
    s = serie.dropna().sort_values(ascending=False)
    return list(s.index).index(pays) + 1


# ---------------------------------------------------------------------------------------------------------------
def dette_01_depense(main, fmi_dep):
    te = main[(main.na_item == "TE") & (main.unit == "PC_GDP") & main.geo.isin(UE27)]
    for an in ["2022", "2023", "2024", "2025"]:
        s = te[te.time == an].set_index("geo").valeur
        premier = s.idxmax()
        res("DETTE-01", f"UE à 27, {an}", "Dépense publique, % du PIB (France)", s["FR"], "% du PIB", an,
            "EUROSTAT-GOV10A-MAIN", "M1", "58 % (2024) ; 57 % (2026)",
            f"rang de la France : {rang(s, 'FR')}/27 ; 1er : {premier} ({s[premier]} %)")
    f = fmi_dep.set_index(["pays", "time"]).valeur
    for an in ["2023", "2024", "2025"]:
        s = fmi_dep[fmi_dep.time == an].set_index("pays").valeur
        s_ocde = s[s.index.isin(OCDE38)]
        devant = [p for p in s.sort_values(ascending=False).index[:rang(s, "FRA") - 1]]
        res("DETTE-01", f"monde (FMI), {an}", "Rang mondial de la France, dépense publique % du PIB", rang(s, "FRA"),
            "rang", an, "FMI-FM-DEPENSES", "M1", "« champion du monde »",
            f"{len(s)} pays ; devant la France : {', '.join(devant)}")
        res("DETTE-01", f"OCDE (FMI), {an}", "Rang de la France parmi les 38 pays de l'OCDE", rang(s_ocde, "FRA"),
            "rang", an, "FMI-FM-DEPENSES", "M1", "« champion du monde »",
            f"1er : {s_ocde.idxmax()} ({round(s_ocde.max(), 1)} %)")


def dette_02_prelevements(taxag, rev, fmi_rec):
    t = taxag[(taxag.na_item == "D2_D5_D91_D61_M_D995") & (taxag.unit == "PC_GDP")]
    for an in ["2022", "2023", "2024", "2025"]:
        s = t[(t.time == an) & t.geo.isin(UE27)].set_index("geo").valeur
        ea = t[(t.time == an) & (t.geo == "EA20")].valeur.iloc[0]
        res("DETTE-02", f"Eurostat UE à 27, {an}", "Impôts et cotisations sociales, % du PIB (France)", s["FR"],
            "% du PIB", an, "EUROSTAT-TAXAG", "M2", "45,4 % (2022) ; 47 € pour 100 € (2026)",
            f"rang {rang(s, 'FR')}/27 ; 1er : {s.idxmax()} ({s.max()}) ; zone euro {ea}")
    r = rev[(rev.STANDARD_REVENUE == "_T") & (rev.UNIT_MEASURE == "PT_B1GQ") & (rev.SECTOR == "S13")]
    for an in ["2021", "2022", "2023", "2024"]:
        s = r[(r.time == an) & r.REF_AREA.isin(OCDE38)].set_index("REF_AREA").valeur
        res("DETTE-02", f"OCDE, {an}", "Recettes fiscales, % du PIB (France, définition OCDE)", s["FRA"], "% du PIB", an,
            "OCDE-RECETTES-FISCALES", "M2", "« le plus élevé de l'OCDE »",
            f"rang {rang(s, 'FRA')}/{len(s)} ; 1er : {s.idxmax()} ({round(s.max(), 1)})")
    s = fmi_rec[fmi_rec.time == "2025"].set_index("pays").valeur
    res("DETTE-02", "monde (FMI), 2025", "Rang mondial de la France, recettes publiques % du PIB", rang(s, "FRA"),
        "rang", "2025", "FMI-FM-RECETTES", "M2", "« record du monde »",
        "recettes publiques totales (impôts, cotisations et autres recettes), pas seulement les prélèvements")


def dette_03_04_charge(budget_vert, d41q, main, plf2024):
    cols = {"2024": "execution_2024_cp", "2025": "lfi_2025_cp_ou_prevision_2025_si_depense_fiscale",
            "2026": "plf_2026_cp_ou_prevision_2026_si_depense_fiscale"}
    bv = budget_vert[budget_vert.type_depense == "Crédits budgétaires"]
    mission = lambda nom, an: bv[bv["mission"] == nom][cols[an]].sum() / 1e9
    justice26, def26, ens26 = mission("Justice", "2026"), mission("Défense", "2026"), mission("Enseignement scolaire", "2026")
    justice25, ens25, def25 = mission("Justice", "2025"), mission("Enseignement scolaire", "2025"), mission("Défense", "2025")
    q = d41q.set_index("time").valeur
    apu_4t = q[["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]].sum() / 1e3
    d41 = main[(main.na_item == "D41PAY") & (main.unit == "MIO_EUR") & (main.geo == "FR")].set_index("time").valeur
    apu_2024, apu_2025 = d41["2024"] / 1e3, d41["2025"] / 1e3
    for nom, charge, src in [("État, LFI 2026 (comptabilité budgétaire)", V("charge_etat_lfi2026"), "SENAT-EFE-PLF2027"),
                             ("État, prévision révisée 2026", V("charge_etat_revise2026"), "SENAT-EFE-PLF2027"),
                             ("toutes administrations, 4 derniers trimestres connus (T3 2025-T2 2026)", apu_4t,
                              "EUROSTAT-INTERETS-TRIM")]:
        res("DETTE-03", nom, "Charge d'intérêts / crédits de la mission Justice (PLF 2026, hors pensions)",
            charge / justice26, "fois", "2026", f"{src} ; BUDGET-VERT-PLF2026", "M3", "7 fois",
            f"intérêts {charge:.1f} Md€ ; Justice {justice26:.2f} Md€")
    res("DETTE-03", "2024, toutes administrations", "Intérêts payés (comptabilité nationale) / Justice exécutée 2024",
        apu_2024 / mission("Justice", "2024"), "fois", "2024", "EUROSTAT-GOV10A-MAIN ; BUDGET-VERT-PLF2026", "M3",
        "5 fois (juillet 2024)", f"intérêts {apu_2024:.1f} Md€ ; Justice exécutée {mission('Justice', '2024'):.2f} Md€")
    p24 = plf2024[plf2024.type_mission == "BG"]
    charge_plf24 = p24[p24.programme == 117].cp_plf.sum() / 1e9
    res("DETTE-03", "2024, État (PLF 2024)", "Charge de la dette de l'État / Justice exécutée 2024 (hors pensions)",
        charge_plf24 / mission("Justice", "2024"), "fois", "2024", "PLF2024-DESTINATION ; BUDGET-VERT-PLF2026", "M3",
        "5 fois (juillet 2024)", f"charge {charge_plf24:.1f} Md€ ; Justice {mission('Justice', '2024'):.2f} Md€")
    # DETTE-04 : premier poste ?
    res("DETTE-04", "2025, État (LFI)", "Charge de la dette de l'État (programme 117)", V("charge_etat_lfi2025"), "Md€",
        "2025", "PAP2026-ENGAGEMENTS-FIN", "M4", "66 Md€, premier poste",
        f"Enseignement scolaire {ens25:.1f} Md€ ; Défense {def25:.1f} Md€ (hors pensions)")
    res("DETTE-04", "2025, toutes administrations", "Intérêts payés par toutes les administrations", apu_2025, "Md€",
        "2025", "EUROSTAT-GOV10A-MAIN", "M4", "66 Md€",
        "c'est ce périmètre qui donne 66 Md€ : il inclut Sécurité sociale et collectivités")
    res("DETTE-04", "2026, État (révisé)", "Charge de la dette de l'État", V("charge_etat_revise2026"), "Md€", "2026",
        "SENAT-EFE-PLF2027", "M4", "74 / 70 / 77 Md€ en 2026 ; « supérieure au budget des armées »",
        f"Enseignement scolaire {ens26:.1f} Md€ ; Défense {def26:.1f} Md€ (PLF 2026, hors pensions)")
    res("DETTE-04", "2027, État (PLF 2027)", "Charge de la dette de l'État", V("charge_etat_plf2027"), "Md€", "2027",
        "SENAT-EFE-PLF2027", "M4", "premier poste",
        f"Enseignement scolaire {V('ens_scolaire_plf2027')} Md€ ; Défense {V('defense_plf2027')} Md€ : premier poste en 2027")
    res("DETTE-04", "toutes administrations, 4 derniers trimestres", "Intérêts payés (T3 2025-T2 2026)", apu_4t, "Md€",
        "2026", "EUROSTAT-INTERETS-TRIM", "M4", "74 / 77 Md€ en 2026")
    return {"justice26": justice26, "def26": def26, "ens26": ens26, "apu_4t": apu_4t}


def dette_05_06_07_dette(edp, q, gdp):
    qq = q[q.unit == "MIO_EUR"].set_index("time").valeur
    qp = q[q.unit == "PC_GDP"].set_index("time").valeur
    for t, lis in [("2025-Q3", "3 482 Md€, 117,4 % (avril 2026)"), ("2026-Q1", "3 536 Md€ (juillet 2026)"),
                   ("2026-Q2", "3 500 Md€ (septembre 2026)")]:
        res("DETTE-05", t, "Dette publique au sens de Maastricht", qq[t] / 1e3, "Md€", t, "EUROSTAT-DETTE-TRIM", "M5", lis,
            f"{qp[t]} % du PIB")
    a = edp[(edp.unit == "MIO_EUR") & (edp.geo == "FR")].set_index("time").valeur
    p = gdp[gdp.geo == "FR"].set_index("time").valeur
    res("DETTE-06", "2017 → 2024", "Hausse de la dette", (a["2024"] / a["2017"] - 1) * 100, "%", "2024",
        "EUROSTAT-EDP-DETTE", "M6", "+46 %", f"{a['2017'] / 1e3:.0f} → {a['2024'] / 1e3:.0f} Md€ (+{(a['2024'] - a['2017']) / 1e3:.0f} Md€)")
    res("DETTE-06", "2017 → 2024", "Hausse du PIB en valeur", (p["2024"] / p["2017"] - 1) * 100, "%", "2024",
        "EUROSTAT-PIB", "M6", "+27 %")
    for debut, fin in [("2015", "2025"), ("2016", "2025")]:
        gd, gp = a[fin] / a[debut] - 1, p[fin] / p[debut] - 1
        res("DETTE-06", f"{debut} → {fin}", "Croissance de la dette / croissance du PIB (rapport)", gd / gp, "rapport", fin,
            "EUROSTAT-EDP-DETTE ; EUROSTAT-PIB", "M6", "« 40 % plus vite » (soit un rapport de 1,4)",
            f"dette +{gd * 100:.1f} % ; PIB +{gp * 100:.1f} %")
    r = edp[edp.unit == "PC_GDP"].set_index(["geo", "time"]).valeur
    for fin in ["2024", "2025"]:
        d_fr = r[("FR", fin)] - r[("FR", "2017")]
        d_ea = r[("EA20", fin)] - r[("EA20", "2017")]
        ratio_cf = r[("FR", "2017")] + d_ea
        dette_cf = ratio_cf / 100 * p[fin]
        ecart = (a[fin] - dette_cf) / 1e3
        res("DETTE-07", f"2017 → {fin}", "Dette en moins si le ratio avait suivi la zone euro", ecart, "Md€", fin,
            "EUROSTAT-EDP-DETTE ; EUROSTAT-PIB", "M7", "400 Md€",
            f"ratio France {r[('FR', '2017')]} → {r[('FR', fin)]} (+{d_fr:.1f} pt) ; zone euro {r[('EA20', '2017')]} → "
            f"{r[('EA20', fin)]} ({d_ea:+.1f} pt)")
        res("DETTE-07", f"2017 → {fin}", "Baisse des intérêts correspondante (proportionnelle à la dette)",
            ecart * 1e3 / a[fin] * 100, "%", fin, "EUROSTAT-EDP-DETTE", "M7", "« divisées par deux » (-50 %)",
            "approximation haute : à taux moyen inchangé, les intérêts baissent comme l'encours")


def dette_08_detention(bdf):
    s = bdf.set_index("time").valeur
    for t, lis in [("2025-Q1", "54,7 % (novembre 2025)"), ("2025-Q2", ""), ("2025-Q4", "55 % / plus de la moitié (2026)")]:
        res("DETTE-08", t, "Part de la dette négociable de l'État détenue par les non-résidents", s[t], "%", t,
            "BDF-NONRESIDENTS", "M8", lis)
    res("DETTE-08", "2026 (PLF)", "Amortissements de titres à moyen et long terme / encours fin 2024",
        V("amortissement_mlt_2026") / V("encours_negociable_fin2024") * 100, "%", "2026", "PAP2026-ENGAGEMENTS-FIN", "M8",
        "12,5 % du stock refinancé chaque année (1/8)",
        "hors titres courts (BTF), refinancés plusieurs fois par an : le refinancement brut total est bien plus élevé")


def dette_09_deficit(main):
    m = main[main.geo == "FR"].pivot_table(index="time", columns=["na_item", "unit"], values="valeur")
    b9, tr = -m[("B9", "MIO_EUR")]["2024"] / 1e3, m[("TR", "MIO_EUR")]["2024"] / 1e3
    res("DETTE-09", "toutes administrations, 2024", "Déficit public", b9, "Md€", "2024", "EUROSTAT-GOV10A-MAIN", "M9",
        "170 Md€", f"{-m[('B9', 'PC_GDP')]['2024']} % du PIB")
    res("DETTE-09", "toutes administrations, 2024", "Déficit / recettes publiques", b9 / tr * 100, "%", "2024",
        "EUROSTAT-GOV10A-MAIN", "M9", "37,8 %")
    res("DETTE-09", "État seul, 2024", "Déficit budgétaire / recettes nettes de l'État",
        V("deficit_etat_2024") / V("recettes_etat_2024") * 100, "%", "2024",
        "PAP2026-ENGAGEMENTS-FIN ; VM2026-TOME1", "M9", "37,8 %")
    res("DETTE-09", "État seul, 2025 révisé", "Déficit budgétaire / recettes nettes de l'État",
        V("deficit_etat_2025_revise") / V("recettes_etat_2025_revise") * 100, "%", "2025",
        "PAP2026-ENGAGEMENTS-FIN ; VM2026-TOME1", "M9", "37,8 %")
    res("DETTE-09", "toutes administrations, 2025", "Déficit public, % du PIB", -m[("B9", "PC_GDP")]["2025"], "% du PIB",
        "2025", "EUROSTAT-GOV10A-MAIN", "M9", "5,1 %")


def dette_10_social(sfunc, stype, socx):
    for an in ["2022", "2023", "2024"]:
        s = sfunc[(sfunc.time == an) & sfunc.geo.isin(UE27)].set_index("geo").valeur
        res("DETTE-10", f"UE, {an}", "Dépenses de protection sociale, % du PIB (France)", s["FR"], "% du PIB", an,
            "EUROSTAT-PROTSOC-FONC", "M10", "33 % / 34 % / 31 %", f"rang {rang(s, 'FR')}/27 ; 1er {s.idxmax()} ({s.max()})")
    fr = stype[(stype.geo == "FR") & (stype.unit == "MIO_EUR")].pivot_table(index="time", columns="spdeps", values="valeur")
    res("DETTE-10", "France, 2024", "Dépenses de protection sociale, total (prestations + gestion)", fr["TOTAL"]["2024"] / 1e3,
        "Md€", "2024", "EUROSTAT-PROTSOC-TYPE", "M10", "900 à 950 Md€", f"dont prestations {fr['SPR']['2024'] / 1e3:.0f} Md€")
    s = stype[(stype.unit == "PPS_HAB") & (stype.spdeps == "TOTAL") & (stype.time == "2023")]
    s = s[~s.geo.str.startswith(("EU", "EA"))].set_index("geo").valeur
    res("DETTE-10", "Europe (UE + AELE), 2023", "Rang de la France, dépenses sociales par habitant (en standard de pouvoir d'achat)",
        rang(s, "FR"), "rang", "2023", "EUROSTAT-PROTSOC-TYPE", "M10", "« record absolu du monde par rapport à la population »",
        f"devant : {', '.join(s.sort_values(ascending=False).index[:rang(s, 'FR') - 1])}")
    x = socx[(socx.UNIT_MEASURE == "USD_PPP_PS") & (socx.EXPEND_SOURCE == "ES10") & (socx.PRICE_BASE == "V")]
    s = x[x.time == "2021"].set_index("REF_AREA").valeur
    s = s[s.index.isin(OCDE38)]
    res("DETTE-10", "OCDE, 2021", "Rang de la France, dépenses sociales publiques par habitant (dollars PPA)", rang(s, "FRA"),
        "rang", "2021", "OCDE-SOCX", "M10", "« record absolu du monde par rapport à la population »",
        f"devant : {', '.join(s.sort_values(ascending=False).index[:rang(s, 'FRA') - 1])}")
    x = socx[(socx.UNIT_MEASURE == "PT_B1GQ") & (socx.EXPEND_SOURCE == "ES10")]
    s = x[x.time == "2022"].set_index("REF_AREA").valeur
    res("DETTE-10", "OCDE, 2022", "Dépenses sociales publiques, % du PIB (France)", s["FRA"], "% du PIB", "2022", "OCDE-SOCX",
        "M10", "", f"rang {rang(s[s.index.isin(OCDE38)], 'FRA')}/OCDE")


def dette_11_aides():
    for k, var, src in [("aides_hcsp_europeen_2022", "aides d'État au sens européen, 2022", "HCSP-AIDES-2025"),
                        ("aides_igf_2024", "Inspection générale des finances, 2024 (cité par le HCSP)", "HCSP-AIDES-2025"),
                        ("aides_senat_restreint_2023", "Sénat, sens restreint, 2023", "SENAT-AIDES-2025-SYN"),
                        ("aides_hcsp_2023", "Haut-Commissariat au plan, 2023", "HCSP-AIDES-2025"),
                        ("aides_clerse_2019", "Clersé-IRES, 2019", "CLERSE-AIDES-2022"),
                        ("aides_senat_large_2023", "Sénat, sens large, 2023", "SENAT-AIDES-2025-SYN")]:
        res("DETTE-11", var, "Aides publiques aux entreprises", V(k), "Md€", var[-4:], src, "M11", "144 / 145 / 157 Md€")
    res("DETTE-11", "Clersé-IRES, vers 2000", "Aides aux entreprises, % du PIB", V("aides_clerse_pib_2000"), "% du PIB",
        "2000", "CLERSE-AIDES-2022", "M11", "« environ 40 milliards au début des années 2000 »",
        "3 % du PIB de 2000 (≈ 1 480 Md€) ≈ 44 Md€")


def dette_12_13_entreprises(taxag):
    res("DETTE-12", "Fipeco, sociétés non financières, 2022", "Prélèvements sur les sociétés non financières",
        V("po_snf_fipeco_2022_pib"), "% du PIB", "2022", "FIPECO-PO-ENTREPRISES-2022", "M12", "13,2 % (2021)",
        "2e de l'UE derrière la Suède ; Allemagne 9,3 %")
    res("DETTE-12", "Fipeco, nets des aides, 2022", "Prélèvements nets des aides reçues", V("po_snf_nets_fipeco_2022_pib"),
        "% du PIB", "2022", "FIPECO-PO-ENTREPRISES-2022", "M12", "")
    res("DETTE-12", "Écart avec l'Allemagne, 2022", "Écart France - Allemagne", V("po_snf_fipeco_2022_pib") - V("po_snf_allemagne_2022_pib"),
        "point de PIB", "2022", "FIPECO-PO-ENTREPRISES-2022", "M12", "5,9 points avec la zone euro (13,2 - 7,3)")
    d = taxag[(taxag.na_item == "D29") & (taxag.unit == "PC_GDP")]
    for an in ["2024", "2025"]:
        s = d[(d.time == an) & d.geo.isin(UE27)].set_index("geo").valeur
        res("DETTE-13", f"Eurostat, tous payeurs, {an}", "Autres impôts sur la production (D29), % du PIB (France)", s["FR"],
            "% du PIB", an, "EUROSTAT-TAXAG", "M13", "3,6 % ; médiane européenne 1,2 %",
            f"médiane UE à 27 : {s.median():.2f} % ; rang {rang(s, 'FR')}/27 (1re : Suède, où la taxe sur les salaires est classée ici)")
    res("DETTE-13", "Fipeco, sociétés seules, 2022", "Impôts sur la production payés par les sociétés", V("ip_societes_fr_2022_pib"),
        "% du PIB", "2022", "FIPECO-IMPOTS-PRODUCTION-2022", "M13", "3,6 %", f"zone euro {V('ip_societes_ze_2022_pib')} %")


def dette_14_coin(tw):
    s = tw[(tw.MEASURE == "AV_TW") & (tw.HOUSEHOLD_TYPE == "S_C0") & (tw.INCOME_PRINCIPAL == "AW100")]
    for an in ["2022", "2025"]:
        x = s[s.time == an].set_index("REF_AREA").valeur
        pays = x[x.index.isin(OCDE38)]
        res("DETTE-14", f"célibataire au salaire moyen, {an}", "Coin fiscal et social, % du coût du travail (France)", x["FRA"],
            "% du coût salarial", an, "OCDE-IMPOTS-SALAIRES", "M14", "« première marche du podium » ; 47 % contre 35 %",
            f"rang {rang(pays, 'FRA')}/38 (devant : {', '.join(pays.sort_values(ascending=False).index[:rang(pays, 'FRA') - 1])}) ; "
            f"moyenne OCDE {x['OECD_REP']:.1f} % ; moyenne des 22 pays de l'UE membres de l'OCDE {x['EU22OECD']:.1f} %")


def dette_15_16_ir():
    res("DETTE-15", "revenus 2023 (connus en septembre 2025)", "Foyers sans impôt net sur le revenu", V("ir_non_imposes_2023_pct"),
        "% des foyers", "2023", "DGFIP-IR-2023-PDF", "M15", "55 %", "19 millions de foyers imposés sur 41 millions (45 %)")
    res("DETTE-15", "revenus 2023", "Part de l'impôt net payée par les 10 % de foyers les plus aisés", V("ir_d10_part_2023_pct"),
        "%", "2023", "DGFIP-IR-2023-PDF", "M15", "70 %")
    d = pd.read_excel(BRUT / "dgfip/dgfip_stat_41.xlsx", sheet_name="Tableau 4", header=None)
    moy = pd.to_numeric(d.iloc[4:14, 3])
    res("DETTE-15", "revenus 2024 (calcul)", "Part de l'impôt net payée par le dernier dixième", moy.iloc[-1] / moy.sum() * 100,
        "%", "2024", "DGFIP-IR-2024", "M15", "70 %", "les dixièmes ont le même nombre de foyers : part = moyenne D10 / somme des moyennes")
    res("DETTE-16", "PLF 2025", "Nombre de dépenses fiscales", V("niches_nombre_plf2025"), "nombre", "2025", "VM2025-TOME2", "M16", "474")
    res("DETTE-16", "PLF 2025", "Coût des dépenses fiscales", V("niches_cout_2025"), "Md€", "2025", "VM2025-TOME2", "M16", "85 Md€")
    res("DETTE-16", "PLF 2025", "Dépenses fiscales sur l'impôt sur le revenu / IR net attendu (LFI 2025)",
        V("niches_ir_2025") / V("ir_net_lfi2025") * 100, "%", "2025", "VM2025-TOME2 ; VM2026-TOME1", "M16",
        "42 Md€ sur 94, « près de la moitié »", f"{V('niches_ir_2025')} Md€ / {V('ir_net_lfi2025')} Md€")
    res("DETTE-16", "PLF 2026", "Nombre de dépenses fiscales", V("niches_nombre_plf2026"), "nombre", "2026", "VM2026-TOME2", "M16",
        "465 (avril 2026)")


def dette_17_succession(rev, gdp, taxag):
    h = rev[(rev.STANDARD_REVENUE == "T_4300") & (rev.UNIT_MEASURE == "PT_B1GQ") & (rev.SECTOR == "S13")]
    for an in ["2022", "2023", "2024"]:
        montants = {}
        for i3, i2 in ISO3_ISO2_UE.items():
            p = h[(h.REF_AREA == i3) & (h.time == an)].valeur
            v = gdp[(gdp.geo == i2) & (gdp.time == an)].valeur
            if len(p) and len(v) and pd.notna(p.iloc[0]) and pd.notna(v.iloc[0]):
                montants[i2] = p.iloc[0] / 100 * v.iloc[0]
        tot = sum(montants.values())
        res("DETTE-17", f"22 pays de l'UE membres de l'OCDE, {an}", "Part de la France dans les droits de succession et de donation",
            montants["FR"] / tot * 100, "%", an, "OCDE-RECETTES-FISCALES ; EUROSTAT-PIB", "M17", "45 %",
            f"France {montants['FR'] / 1e3:.1f} Md€ sur {tot / 1e3:.1f} Md€ ({len(montants)} pays renseignés)")
    d = taxag[(taxag.na_item == "D91") & (taxag.unit == "MIO_EUR") & (taxag.time == "2024") & taxag.geo.isin(UE27)]
    s = d.set_index("geo").valeur
    res("DETTE-17", "UE à 27, impôts en capital (D91), 2024", "Part de la France dans les impôts en capital de l'UE",
        s["FR"] / s.sum() * 100, "%", "2024", "EUROSTAT-TAXAG", "M17", "45 %",
        "D91 contient aussi d'autres impôts en capital : contrôle d'ordre de grandeur")


def dette_18_carburant():
    f = BRUT / "commission_europeenne/Weekly_Oil_Bulletin_Prices_History.xlsx"

    def lire(feuille):
        d = pd.read_excel(f, sheet_name=feuille, header=None)
        h, d = d.iloc[0], d.iloc[3:].copy()
        idx = pd.to_datetime(d[0], errors="coerce")
        out = {}
        for i, c in h.items():
            if isinstance(c, str) and "_price_" in c and ("euro95" in c or "diesel" in c):
                out[(c.split("_")[0], "essence SP95" if "euro95" in c else "gazole")] = pd.to_numeric(d[i], errors="coerce").values
        return pd.DataFrame(out, index=idx)

    part = (1 - lire("Prices wo taxes") / lire("Prices with taxes")) * 100
    for libelle, sel in [("semaine du 4 mai 2026", part.loc[pd.Timestamp("2026-05-04")]),
                         ("moyenne 2025", part[part.index.year == 2025].mean())]:
        for prod in ["essence SP95", "gazole"]:
            s = sel.xs(prod, level=1).dropna()
            s = s[s.index.isin(UE27 + ["GR"])]
            res("DETTE-18", f"{prod}, {libelle}", "Part des taxes dans le prix à la pompe (France)", s["FR"], "%",
                libelle[-4:], "CE-BULLETIN-PETROLIER", "M18", "60 %, « la plus élevée du monde »",
                f"rang {rang(s, 'FR')}/{len(s)} dans l'UE ; 1er : {s.idxmax()} ({s.max():.1f} %)")


def dette_19_capital():
    is_normal = 25.0 * 1.033  # IS à 25 % + contribution sociale de 3,3 % (au-delà de 763 000 € d'IS) : borne haute
    is_grand = is_normal * 1.412  # + contribution exceptionnelle de 41,2 % de l'IS (chiffre d'affaires ≥ 3 Md€)
    res("DETTE-19", "très grande entreprise (CA ≥ 3 Md€), 2025-2026", "Taux d'IS légal, surtaxes comprises", is_grand, "%", "2026",
        "BOFIP-CONTRIBUTION-EXCEPTIONNELLE ; SP-IMPOT-SOCIETES", "M19", "« dépasse 36 % »")
    for nom, taux_is in [("entreprise ordinaire", is_normal), ("très grande entreprise", is_grand)]:
        for perso, taux_perso in [("flat tax 31,4 %", 31.4), ("flat tax + contribution hauts revenus 4 %", 35.4),
                                  ("plancher de 20 % pour l'impôt (CDHR) + prélèvements sociaux 18,6 %", 38.6)]:
            cumul = 100 - (100 - taux_is) * (100 - taux_perso) / 100
            res("DETTE-19", f"{nom}, {perso}", "Imposition cumulée d'un bénéfice distribué en dividende", cumul, "%", "2026",
                "SP-IMPOT-SOCIETES ; SP-PRELEVEMENTS-SOCIAUX ; SP-CEHR-CDHR ; BOFIP-CONTRIBUTION-EXCEPTIONNELLE", "M19",
                "« excède 60 % »")


def dette_20_21_22_mesures(main, gdp, taxag, sal):
    te = main[(main.na_item == "TE") & (main.unit == "MIO_EUR") & (main.geo == "FR")].set_index("time").valeur
    tp = main[(main.na_item == "TE") & (main.unit == "PC_GDP")]
    p = gdp[gdp.geo == "FR"].set_index("time").valeur
    pib25, dep25 = p["2025"] / 1e3, te["2025"] / 1e3
    s25 = tp[(tp.time == "2025") & tp.geo.isin(UE27)].set_index("geo").valeur
    for eco in [200, 300]:
        apres = s25["FR"] - eco / pib25 * 100
        s2 = s25.copy()
        s2["FR"] = apres
        res("DETTE-20", f"{eco} Md€ d'économies (PIB et dépense 2025)", "Économies en % de la dépense publique", eco / dep25 * 100,
            "%", "2025", "EUROSTAT-GOV10A-MAIN", "M20", "", "ESTIMATION : à PIB inchangé")
        res("DETTE-20", f"{eco} Md€ d'économies (PIB et dépense 2025)", "Économies en points de PIB", eco / pib25 * 100,
            "point de PIB", "2025", "EUROSTAT-GOV10A-MAIN ; EUROSTAT-PIB", "M20", "7 points = 200 Md€ ; 9 points visés",
            "ESTIMATION : à PIB inchangé")
        res("DETTE-20", f"{eco} Md€ d'économies", "Dépense publique après économies, % du PIB (France)", apres, "% du PIB", "2025",
            "EUROSTAT-GOV10A-MAIN ; EUROSTAT-PIB", "M20",
            "« resterait le pays à la dépense la plus élevée d'Europe » (200) ; « au-dessus des Pays-Bas » (300)",
            f"ESTIMATION à PIB inchangé ; rang {rang(s2, 'FR')}/27 ; Pays-Bas {s25['NL']} % ; Finlande {s25['FI']} %")
    nb = sal.set_index("time").valeur
    an = max(nb.index)
    res("DETTE-21", f"salariés {an}", "Gain mensuel moyen si 120 Md€ de cotisations allaient entièrement en salaire net",
        120e9 / (nb[an] * 1e3) / 12, "€ par mois et par salarié", an, "EUROSTAT-SALARIES", "M21", "« presque 400 euros »",
        f"ESTIMATION, non fiable à 100 % : {nb[an] / 1e3:.1f} millions de salariés ; suppose que toute la baisse va au salaire net")
    res("DETTE-21", "première année (60 % de 80 Md€)", "Gain mensuel moyen la première année", 0.6 * 80e9 / (nb[an] * 1e3) / 12,
        "€ par mois et par salarié", an, "EUROSTAT-SALARIES", "M21", "« près de 200 euros » au départ",
        "ESTIMATION, non fiable à 100 % ; même hypothèse")
    res("DETTE-21", "C3S + CVAE", "Rendement de la C3S (2022) et de la CVAE (part État, 2025)", V("c3s_2022") + V("cvae_etat_2025"),
        "Md€", "2025", "FIPECO-IMPOTS-PRODUCTION-2022 ; VM2026-TOME1", "M21", "40 Md€ de baisse des impôts de production",
        "ESTIMATION : la suppression des deux impôts cités coûte environ 8 à 9 Md€, le reste des 40 Md€ n'est pas précisé")
    t = taxag[(taxag.na_item == "D2_D5_D91_D61_M_D995") & (taxag.unit == "PC_GDP")].set_index(["geo", "time"]).valeur
    ecart = t[("FR", "2025")] - t[("EA20", "2025")]
    res("DETTE-22", "Eurostat 2025", "Baisse nécessaire pour atteindre la moyenne de la zone euro", ecart / 100 * pib25 * 1e3 / 1e3,
        "Md€", "2025", "EUROSTAT-TAXAG ; EUROSTAT-PIB", "M22", "100 Md€",
        f"ESTIMATION à PIB inchangé : France {t[('FR', '2025')]} % ; zone euro {t[('EA20', '2025')]} % ; écart {ecart:.1f} points")


# ---------------------------------------------------------------------------------------------------------------
def graphiques(main, charges):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPH.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.edgecolor": "#b9b8b3", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e"})
    # 1. Dépense publique, % du PIB : France, Finlande, moyenne UE
    te = main[(main.na_item == "TE") & (main.unit == "PC_GDP")]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
    for geo, nom, coul, dy in [("FR", "France", "#2a78d6", -7), ("FI", "Finlande", "#eb6834", 7),
                               ("EU27_2020", "Moyenne UE à 27", "#8a8984", 0)]:
        s = te[(te.geo == geo) & (te.time >= "2012")].set_index("time").valeur
        ax.plot(s.index.astype(int), s.values, color=coul, lw=2, label=nom)
        ax.annotate(f"{nom} {s.iloc[-1]:.1f} %", (int(s.index[-1]), s.iloc[-1]), xytext=(6, dy), textcoords="offset points",
                    va="center", color="#0b0b0b", fontsize=9)
    ax.set_xlim(2012, 2028.5)
    ax.set_axisbelow(True)
    ax.set_ylabel("Dépense publique, % du PIB")
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_title("La Finlande dépasse la France depuis 2024", loc="left", fontsize=12, color="#0b0b0b")
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    fig.text(0.01, 0.01, "Source : Eurostat, gov_10a_main (octobre 2026)", fontsize=8, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPH / "depense_publique_ue.png")
    plt.close(fig)
    # 2. Intérêts de la dette et grandes missions de l'État, 2026
    barres = [("Intérêts, toutes administrations\n(4 derniers trimestres connus)", charges["apu_4t"], "#2a78d6"),
              ("Charge de la dette de l'État\n(prévision révisée 2026)", V("charge_etat_revise2026"), "#2a78d6"),
              ("Charge de la dette de l'État\n(loi de finances 2026)", V("charge_etat_lfi2026"), "#2a78d6"),
              ("Enseignement scolaire", charges["ens26"], "#8a8984"), ("Défense", charges["def26"], "#8a8984"),
              ("Justice", charges["justice26"], "#8a8984")]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
    y = range(len(barres))[::-1]
    ax.barh(list(y), [b[1] for b in barres], color=[b[2] for b in barres], height=0.62)
    for yi, b in zip(y, barres):
        ax.text(b[1] + 0.8, yi, f"{b[1]:.1f} Md€", va="center", fontsize=9, color="#0b0b0b")
    ax.set_yticks(list(y), [b[0] for b in barres], fontsize=8.5)
    ax.set_xlabel("Milliards d'euros (missions : PLF 2026, hors pensions)")
    ax.set_xlim(0, 85)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#e4e3df", lw=0.8)
    ax.set_title("Intérêts de la dette et grandes missions de l'État en 2026", loc="left", fontsize=12, color="#0b0b0b")
    fig.text(0.01, 0.01, "Sources : Sénat (note EFE, PLF 2027), Eurostat gov_10q_ggnfa, PLF 2026 (Budget vert)", fontsize=8,
             color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPH / "charge_dette_2026.png")
    plt.close(fig)


def main():
    manquants = verifier_pdf()
    if manquants:
        raise SystemExit("Chiffres introuvables dans les PDF :\n  " + "\n  ".join(manquants))
    eu = lambda f: L.eurostat(BRUT / "eurostat" / f)
    main_ = eu("gov_10a_main.json")
    taxag, gdp = eu("gov_10a_taxag.json"), eu("nama_10_gdp.json")
    rev = L.ocde(BRUT / "ocde/revenue_statistics.csv")
    dette_01_depense(main_, L.fmi(BRUT / "fmi/fiscal_monitor_depenses.json"))
    dette_02_prelevements(taxag, rev, L.fmi(BRUT / "fmi/fiscal_monitor_recettes.json"))
    charges = dette_03_04_charge(pd.read_csv(BRUT / "budget/plf2026_budget_vert.csv", sep=";"),
                                 eu("gov_10q_ggnfa_fr_d41.json"), main_,
                                 pd.read_csv(BRUT / "budget/plf2024_destination.csv", sep=";"))
    dette_05_06_07_dette(eu("gov_10dd_edpt1.json"), eu("gov_10q_ggdebt_fr.json"), gdp)
    dette_08_detention(L.dbnomics(BRUT / "bdf/det_nonresidents.json"))
    dette_09_deficit(main_)
    dette_10_social(eu("spr_exp_func.json"), eu("spr_exp_type.json"), L.ocde(BRUT / "ocde/socx_agg.csv"))
    dette_11_aides()
    dette_12_13_entreprises(taxag)
    dette_14_coin(L.ocde(BRUT / "ocde/taxing_wages.csv"))
    dette_15_16_ir()
    dette_17_succession(rev, gdp, taxag)
    dette_18_carburant()
    dette_19_capital()
    dette_20_21_22_mesures(main_, gdp, taxag, eu("nama_10_a10_e_fr.json"))
    graphiques(main_, charges)
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(RESULTATS[0]))
        w.writeheader()
        w.writerows(RESULTATS)
    print(f"{len(RESULTATS)} résultats → {SORTIE.relative_to(ICI.parent)} ; graphiques dans calculs/graphiques/")


if __name__ == "__main__":
    main()
