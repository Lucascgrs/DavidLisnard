"""Thème 15 — Culture, numérique et intelligence artificielle : calculs à partir de brut/.

python -m verification calculer 15   → calculs/resultats.csv
"""
import csv
import html
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
LUS = {
    "draghi_100md": ("commission/draghi_partie_A.pdf",
                     "there is no EU company with a market capitalisation over EUR 100 billion that has been set up from scratch in the last fifty years, while all six US companies with a valuation above EUR 1 trillion have been created in this period", 100),
    "ia_etats_unis": ("stanford/ai_index_2026.html", "U.S. private AI investment reached $285.9 billion in 2025, more than 23 times the $12.4 billion invested in China", 285.9),
    "ia_chine": ("stanford/ai_index_2026.html", "the $12.4 billion invested in China", 12.4),
    "ia_europe": ("stanford/ai_index_2026.html", "Europe ($20.92 billion)", 20.92),
    "taiwan_10nm": ("bcg_sia/semiconductor_supply_chain_2021.pdf", "currently all the world’s capacity below 10 nanometers is located in South Korea (8%) and Taiwan (92%)", 92),
    "culture_idf": ("insee/FET2021-11.pdf", "représente 196 euros par habitant en", 196),
    "culture_hors_idf": ("insee/FET2021-11.pdf", "contre 21 euros par habitant en moyenne hors", 21),
    "culture_total": ("insee/FET2021-11.pdf", "En 2018, les dépenses du ministère de la Culture s’élèvent à plus de 3,5 milliards d’euros", 3.5),
}


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


def main():
    verifier_documents()
    res("NUM-01", "rapport Draghi", "Seuil de capitalisation qu'aucune entreprise de l'UE créée en 50 ans n'atteint", V("draghi_100md"), "Md€", "2024",
        "DRAGHI-2024-A", "M1", "100 milliards d'euros", "« all six US companies with a valuation above EUR 1 trillion have been created in this period »")
    res("NUM-02", "États-Unis, 2025", "Investissement privé dans l'IA", V("ia_etats_unis"), "Md$", "2025", "STANFORD-AI-INDEX-2026", "M2", "près de 286 Md$")
    res("NUM-02", "États-Unis / Chine, 2025", "Rapport des investissements privés dans l'IA", V("ia_etats_unis") / V("ia_chine"), "fois", "2025",
        "STANFORD-AI-INDEX-2026", "M2", "vingt-trois fois", f"Chine : {V('ia_chine')} Md$ ; Europe : {V('ia_europe')} Md$ ; hors fonds publics chinois")
    res("NUM-04", "capacité de production < 10 nm, 2019", "Part de Taïwan", V("taiwan_10nm"), "%", "2019", "BCG-SIA-2021", "M3", "plus de 90 %",
        "le reste (8 %) en Corée du Sud")
    res("CULT-01", "Île-de-France, 2018", "Dépenses du ministère de la Culture par habitant", V("culture_idf"), "€ par habitant", "2018",
        "INSEE-TEF-2021-CULTURE", "M4", "801 € par Parisien")
    res("CULT-01", "hors Île-de-France, 2018", "Dépenses du ministère de la Culture par habitant", V("culture_hors_idf"), "€ par habitant", "2018",
        "INSEE-TEF-2021-CULTURE", "M4", "24 € par habitant de la province")
    res("CULT-01", "rapport Île-de-France / reste, 2018", "Écart de dépense par habitant", V("culture_idf") / V("culture_hors_idf"), "fois", "2018",
        "INSEE-TEF-2021-CULTURE", "M4", f"{801 / 24:.0f} fois (801 / 24)", "les grands établissements nationaux (musées, opéras) sont comptés là où ils se trouvent")
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
