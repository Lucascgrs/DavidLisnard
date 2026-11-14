"""Thème 9 — Retraites et protection sociale : calculs à partir de brut/.

python -m verification calculer 9   → calculs/resultats.csv
"""
import csv
import re
from pathlib import Path

import pandas as pd

from verification.commun import lecture as L

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
CC = "cour_des_comptes/situation_financiere_retraites_2025.pdf"
LUS_DANS_LES_PDF = {
    "deficit_2025": (CC, "Dès 2025, le déficit tous régimes, tel que calculé par la Cour, devrait atteindre 6,6 Md€", 6.6),
    "solde_2025_avec_complementaires": (CC, "serait de - 0,6 Md€ seulement", -0.6),
    "depenses_2023": (CC, "le système de retraites est présenté, en 2023, à 388,4 Md€ de dépenses", 388.4),
    "conventions": (CC, "Il existe, dès lors, autant de formules de calcul que de conventions comptables", 0),
    "sans_effet_solde": (CC, "Des conventions de présentation sans effet sur le solde des finances publiques", 0),
    "taux_civils_2025": (CC, "celui pour les fonctionnaires civils est de 78,28 % depuis le 1er janvier 2025", 78.28),
    "taux_militaires": (CC, "Le taux de cotisation employeurs pour les militaires est de 126,07 %", 126.07),
    "part_pib_2022": (CC, "à hauteur de 14,4 % de son PIB en 2022", 14.4),
    "erafp_tri": ("erafp/RAFP_rapport_annuel_2025.pdf", "Le TRI global depuis 2006 s’élève à 4,7 % à fin 2025, en hausse par rapport à son niveau de fin 2024 (4,3 %)", 4.7),
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


def main():
    verifier_pdf()
    src = "CC-RETRAITES-2025"
    res("RET-01", "Cour des comptes, prévision 2025", "Déficit du système de retraite, tous régimes", -V("deficit_2025"), "Md€", "2025", src, "M1",
        "2,8 % du PIB (« vrai déséquilibre », 2020) contre 0,6 % (COR)",
        f"{V('solde_2025_avec_complementaires')} Md€ en comptant les produits financiers des régimes complémentaires ; soit environ 0,2 % du PIB")
    res("RET-01", "régime des fonctionnaires de l'État", "Taux de cotisation employeur de l'État, fonctionnaires civils", V("taux_civils_2025"), "%", "2025",
        src, "M1", "« jusqu'à 80 % du salaire des fonctionnaires »", f"militaires : {V('taux_militaires')} %")
    res("RET-02", "2023", "Dépenses du système de retraite (Cour des comptes)", V("depenses_2023"), "Md€", "2023", src, "M2",
        "116 Md€ = 40 % du montant total des retraites", f"116 Md€ représentent {116 / V('depenses_2023') * 100:.1f} % de ce total")
    s = L.eurostat(BRUT / "eurostat/spr_exp_func_vieillesse_fr.json").pivot_table(index="time", columns=["spfunc", "unit"], values="valeur")
    res("RET-02", "2024", "Dépenses de protection sociale « vieillesse » (Eurostat)", s[("OLD", "MIO_EUR")]["2024"] / 1e3, "Md€", "2024",
        "EUROSTAT-PROTSOC-VIEILLESSE", "M2", "", f"116 Md€ en représentent {116 / (s[('OLD', 'MIO_EUR')]['2024'] / 1e3) * 100:.1f} %")
    res("RET-02", "cohérence interne", "Total des retraites implicite dans « 116 Md€ = 40 % »", 116 / 0.4, "Md€", "", src, "M2", "",
        "ESTIMATION, non fiable à 100 % : 290 Md€, nettement en dessous des dépenses réelles (378 à 388 Md€)")
    w = L.eurostat(BRUT / "eurostat/earn_mw_cur_fr.json").set_index("time").valeur
    versement = 0.10 * w["2025-S2"] * 12
    from scipy.optimize import brentq
    vf = lambda r: versement * ((1 + r) ** 40 - 1) / r
    r = brentq(lambda r: vf(r) - 320000, 0.001, 0.2)
    res("RET-03", "SMIC brut 2025, 10 % épargnés pendant 40 ans", "Rendement annuel nécessaire pour atteindre 320 000 €", r * 100, "% par an",
        "2025", "EUROSTAT-SMIC", "M3", "plus de 320 000 €",
        f"ESTIMATION, non fiable à 100 % : versement de {versement:.0f} € par an, sans hausse du SMIC ni frais ; à 4,7 % par an (rendement de l'Erafp) : {vf(0.047):.0f} €")
    res("RET-03", "320 000 € dans 40 ans, inflation de 2 % par an", "Valeur en euros d'aujourd'hui", 320000 / 1.02 ** 40, "€", "2025",
        "EUROSTAT-SMIC", "M3", "plus de 320 000 €", "ESTIMATION, non fiable à 100 % : inflation supposée de 2 % par an (cible de la BCE)")
    res("RET-04", "Erafp, 2006 → 2025", "Taux de rendement interne annualisé depuis 2006", V("erafp_tri"), "% par an", "2025", "ERAFP-RA-2025",
        "M4", "5,4 % par an depuis 2006", "4,3 % à fin 2024 ; rendement nominal (inflation non déduite)")
    v = pd.read_csv(BRUT / "budget/plf2026_budget_vert.csv", sep=";")
    v = v[v.type_depense == "Crédits budgétaires"]
    sncf = v[v.action_si_credit_budgetaire.astype(str).str.contains("personnel de la SNCF")]["lfi_2025_cp_ou_prevision_2025_si_depense_fiscale"].sum() / 1e9
    justice = v[v["mission"] == "Justice"]["lfi_2025_cp_ou_prevision_2025_si_depense_fiscale"].sum() / 1e9
    res("RET-05", "LFI 2025", "Subvention de l'État au régime de retraite de la SNCF", sncf, "Md€", "2025", "BUDGET-VERT-PLF2026", "M5",
        "5,5 Md€, « une grosse moitié du budget de la Justice »", f"soit {sncf / justice * 100:.0f} % des crédits de la Justice ({justice:.2f} Md€, hors pensions)")
    res("RET-05", "LFI 2025", "5,5 Md€ / crédits de la Justice", 5.5 / justice * 100, "%", "2025", "BUDGET-VERT-PLF2026", "M5",
        "« une grosse moitié »", "5,5 Md€ = pensions totales du régime, financées aussi par les cotisations (montant non vérifié ici)")
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
