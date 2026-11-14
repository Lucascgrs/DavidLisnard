"""Thème 9 — Retraites et protection sociale : téléchargement des sources brutes.  python -m verification telecharger 9"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("CC-RETRAITES-2025", "Cour des comptes (copie publiée par vie-publique.fr)",
           "Situation financière et perspectives du système de retraites (mission flash, février 2025)", "B",
           "https://www.vie-publique.fr/files/rapport/pdf/297428.pdf", "cour_des_comptes/situation_financiere_retraites_2025.pdf",
           ["RET-01"], licence=LO, outil="curl", date_publication="2025-02-20"),
    Source("ERAFP-RA-2025", "Erafp (Établissement de retraite additionnelle de la fonction publique)", "Rapport annuel 2025", "A",
           "https://media.rafp.fr/s3fs-public/2026-06/RAFP-RA2025-V6_0.pdf", "erafp/RAFP_rapport_annuel_2025.pdf", ["RET-04"],
           outil="curl", date_publication="2026-06"),
    Source("EUROSTAT-PROTSOC-VIEILLESSE", "Eurostat", "Dépenses de protection sociale par fonction : vieillesse et survie (spr_exp_func)", "A",
           EUROSTAT + "spr_exp_func", "eurostat/spr_exp_func_vieillesse_fr.json", ["RET-02"], licence=CCBY,
           params={"geo": "FR", "spfunc": ["OLD", "SURVIVOR", "TOTAL"], "unit": ["MIO_EUR", "PC_GDP"], "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-SMIC", "Eurostat", "Salaire minimum mensuel brut (earn_mw_cur)", "A", EUROSTAT + "earn_mw_cur",
           "eurostat/earn_mw_cur_fr.json", ["RET-03"], licence=CCBY, params={"geo": "FR", "currency": "EUR", "sinceTimePeriod": "2015"}),
    Source("BUDGET-VERT-PLF2026", "Ministère de l'Économie (direction du Budget)", "PLF 2026 — Budget vert : crédits de paiement par programme",
           "A", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/plf-2026-budget-vert/exports/csv",
           "budget/plf2026_budget_vert.csv", ["RET-05"], licence=LO, params={"delimiter": ";"}),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:28} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
