"""Thème 14 — Institutions, référendum et normes : calculs à partir de brut/.

python -m verification calculer 14   → calculs/resultats.csv
"""
import csv
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE = ICI / "resultats.csv"
CP = "amf_cevipof/demissions_maires_communique.pdf"
LUS = {
    "par_an_2008_2014": (CP, "le nombre moyen de démissions de maires par an a été multiplié par 4 (129 vs. 417)", 129),
    "par_an_2020": (CP, "multiplié par 4 (129 vs. 417)", 417),
    "total_depuis_2020": (CP, "Avec 2 189 démissions depuis juillet 2020", 2189),
    "par_mois": (CP, "ce sont en moyenne 40 démissions par mois enregistrées", 40),
}


def verifier_documents():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache = {}
    for cle, (f, extrait, _) in LUS.items():
        if f not in cache:
            cache[f] = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
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
    src = "AMF-CEVIPOF-DEMISSIONS-CP"
    res("INS-01", "septembre 2020 - mars 2025", "Démissions de maires par mois", V("par_mois"), "par mois", "2025", src, "M1", "42 par mois")
    mois = (2025 - 2020) * 12 + (3 - 7) + 1  # juillet 2020 à mars 2025 inclus
    res("INS-01", "juillet 2020 - mars 2025", "Démissions de maires par mois (total / nombre de mois)", V("total_depuis_2020") / mois, "par mois", "2025", src,
        "M1", "42 par mois", f"{V('total_depuis_2020')} démissions sur {mois} mois")
    res("INS-01", "mandat 2020 / mandat 2008-2014", "Rapport des démissions annuelles moyennes", V("par_an_2020") / V("par_an_2008_2014"), "fois", "2025", src,
        "M1", "« quatre fois plus qu'il y a 20 ans »", f"{V('par_an_2020')} par an contre {V('par_an_2008_2014')} ; le communiqué arrondit à « multiplié par 4 »")
    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(R[0]))
        wr.writeheader()
        wr.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
