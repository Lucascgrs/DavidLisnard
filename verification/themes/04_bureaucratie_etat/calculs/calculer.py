"""Thème 4 — Bureaucratie, normes et réforme de l'État : calculs à partir de brut/.

python -m verification calculer 4   → calculs/resultats.csv
"""
import csv
import json
import re
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
TOME1 = "senat/r24-807-1_tome1_agences.pdf"

LUS_DANS_LES_PDF = {
    "organismes_publics_nationaux": ("senat/r24-807-1_synthese_agences.pdf", "434 opérateurs, 317 organismes consultatifs, 1 153 organismes publics nationaux", 1153),
    "operateurs_plf2025": (TOME1, "sont inscrits 434 opérateurs de l ’État rémunérant 402 218 emplois sous plafond", 434),
    "etpt_sous_plafond": (TOME1, "Le montant total des emplois sous plafonds des opérateurs est de 402 489 équivalents temps plein travaillés", 402489),
    "etpt_hors_plafond": (TOME1, "le montant des emplois hors plafond est de 77 058 ETPT", 77058),
    "financement_plf2025": (TOME1, "Les financements publics des opérateurs sont de 77,0 milliards d’euros", 77.0),
    "financement_lfi2024": (TOME1, "était de 80,6 milliar ds d’euros en loi de finances pour 2024", 80.6),
    "economie_8pc": (TOME1, "une réduction de 8 % de ces coûts se traduisant par une économie de 2,2 milliards d’euros", 2.2),
    "igf_2012_agences": (TOME1, "2012 IGF : 1 244 agences", 1244),
    "part_enseignement_sup": (TOME1, "plus de la moitié de ces effectifs correspondent aux effectifs des établiss ements d’enseignement supérieur et de recherche", 50),
    "economie_ministre": ("senat/r24-807-1_synthese_agences.pdf", "a chiffré à 2 à 3 milliards d’euros les économies pouvant résulter de la restructuration des agences", 3),
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


def agences():
    S, SS = "SENAT-AGENCES-2025", "SENAT-AGENCES-2025-SYN"
    res("BUR-01", "Sénat 2025", "Organismes publics nationaux recensés", V("organismes_publics_nationaux"), "organismes", "2025", SS, "M1",
        "1 153 / 1 200", f"dont {V('operateurs_plf2025')} opérateurs ; l'IGF en comptait déjà {V('igf_2012_agences')} en 2012")
    jaune = pd.read_csv(BRUT / "budget/plf2026_jaune_operateurs.csv", sep=";", encoding="latin-1")
    res("BUR-01", "PLF 2026", "Lignes de la liste des opérateurs (opérateurs ou catégories)", len(jaune), "lignes", "2026",
        "JAUNE-OPERATEURS-PLF2026", "M1", "418 agences (janvier 2025)", "une ligne peut regrouper une catégorie de plusieurs opérateurs")
    total = V("etpt_sous_plafond") + V("etpt_hors_plafond")
    res("BUR-01", "PLF 2025", "Emplois des opérateurs (sous plafond + hors plafond)", total, "ETPT", "2025", S, "M1",
        "410 000 à 500 000 « recrutés »", "stock d'emplois, pas des recrutements ; plus de la moitié dans l'enseignement supérieur et la recherche")
    res("BUR-01", "PLF 2025 / LFI 2024", "Financements publics des opérateurs", V("financement_plf2025"), "Md€", "2025", S, "M1",
        "83 à 100 Md€ « de fonctionnement »", f"{V('financement_lfi2024')} Md€ en 2024 ; comprend les transferts reversés (France compétences 15,1 Md€…)")
    base = V("economie_8pc") / 0.08
    res("BUR-01", "calcul", "Charges de personnel et de fonctionnement des opérateurs (déduites du scénario du Sénat)", base, "Md€", "2025",
        S, "M1", "100 Md€ de fonctionnement", "2,2 Md€ = 8 % de ces charges ⇒ environ 27,5 Md€")
    return base


def emploi_public():
    j = json.loads((BRUT / "ocde/gov_emploi_public_2025.json").read_text(encoding="utf-8"))
    for s in j["series"]["docs"]:
        code = s["series_code"]
        if ".EMPG.PT_EMP.S13." in code and (".FRA." in code or ".DEU." in code):
            pays = "France" if ".FRA." in code else "Allemagne"
            for an, v in zip(s["period"], s["value"]):
                if an in ("2021", "2022", "2023") and v not in (None, "NA"):
                    res("BUR-03", f"{pays}, {an}", "Emploi des administrations publiques, % de l'emploi total", v, "%", an,
                        "OCDE-EMPLOI-PUBLIC-2025", "M3", "21 % (France) ; 11 % (Allemagne)")


def mesure(base):
    res("BUR-06", "80 Md€ la première année", "Économie demandée / financements publics de tous les opérateurs", 80 / V("financement_plf2025") * 100,
        "%", "2025", "SENAT-AGENCES-2025", "M6", "80 Md€", "ESTIMATION, non fiable à 100 % : rapport des ordres de grandeur")
    res("BUR-06", "8 Md€ (hypothèse basse, novembre 2026)", "Baisse demandée des charges de personnel et de fonctionnement", 8 / base * 100,
        "%", "2025", "SENAT-AGENCES-2025", "M6", "au moins 8 Md€",
        "ESTIMATION, non fiable à 100 % : à comparer au scénario du Sénat (8 %, 2,2 Md€) et à la ministre (2 à 3 Md€)")


def main():
    verifier_pdf()
    base = agences()
    emploi_public()
    mesure(base)
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
