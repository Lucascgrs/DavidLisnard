"""Thème 15 — Culture, numérique et intelligence artificielle : téléchargement des sources brutes.  python -m verification telecharger 15"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

SOURCES = [
    Source("DRAGHI-2024-A", "Commission européenne (rapport de M. Draghi)", "The future of European competitiveness, partie A (septembre 2024)", "A",
           "https://commission.europa.eu/document/download/97e481fd-2dc3-412d-be4c-f152a8232961_en?filename=The%20future%20of%20European%20competitiveness%20_%20A%20competitiveness%20strategy%20for%20Europe.pdf",
           "commission/draghi_partie_A.pdf", ["NUM-01"], licence="réutilisation autorisée (décision 2011/833/UE)", outil="curl"),
    Source("STANFORD-AI-INDEX-2026", "Stanford University, Institute for Human-Centered AI", "AI Index Report 2026, page de synthèse (le rapport complet fait 42 Mo)", "B",
           "https://hai.stanford.edu/ai-index/2026-ai-index-report", "stanford/ai_index_2026.html", ["NUM-02"], outil="curl",
           note="Données d'investissement de Quid, reprises par le rapport"),
    Source("BCG-SIA-2021", "Boston Consulting Group et Semiconductor Industry Association", "Strengthening the Global Semiconductor Supply Chain in an Uncertain Era (avril 2021)", "C",
           "https://www.semiconductors.org/wp-content/uploads/2021/05/BCG-x-SIA-Strengthening-the-Global-Semiconductor-Value-Chain-April-2021_1.pdf",
           "bcg_sia/semiconductor_supply_chain_2021.pdf", ["NUM-04"], outil="curl",
           note="Étude d'un cabinet de conseil pour l'association professionnelle américaine : pas de statistique publique équivalente"),
    Source("INSEE-TEF-2021-CULTURE", "Insee (Tableaux de l'économie française 2021, fiche 4.5, d'après le DEPS du ministère de la Culture)",
           "Accès à la culture : dépenses culturelles publiques par habitant et par région (données 2018)", "A",
           "https://www.insee.fr/fr/statistiques/fichier/5039867/FET2021-11.pdf", "insee/FET2021-11.pdf", ["CULT-01"], licence="Licence ouverte Etalab 2.0", outil="curl"),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:26} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
