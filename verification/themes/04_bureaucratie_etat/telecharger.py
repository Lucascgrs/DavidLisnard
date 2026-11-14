"""Thème 4 — Bureaucratie, normes et réforme de l'État : téléchargement des sources brutes.

python -m verification telecharger 4
Légifrance (statistiques de la norme du Secrétariat général du Gouvernement) refuse les téléchargements
automatiques : la taille des codes n'a pas pu être téléchargée (à déposer à la main dans brut/sgg/).
"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
LO, PARL = "Licence ouverte Etalab 2.0", "Documents parlementaires, réutilisation libre"

SOURCES = [
    Source("SENAT-AGENCES-2025", "Sénat (commission d'enquête)",
           "Rapport n° 807 (2024-2025) sur les missions des agences, opérateurs et organismes consultatifs de l'État, tome I",
           "B", "https://www.senat.fr/rap/r24-807-1/r24-807-11.pdf", "senat/r24-807-1_tome1_agences.pdf", ["BUR-01", "BUR-06"],
           licence=PARL, outil="curl", date_publication="2025-07-01"),
    Source("SENAT-AGENCES-2025-SYN", "Sénat (commission d'enquête)", "Rapport n° 807 (2024-2025) sur les agences de l'État : l'essentiel",
           "B", "https://www.senat.fr/rap/r24-807-1/r24-807-1-syn.pdf", "senat/r24-807-1_synthese_agences.pdf", ["BUR-01", "BUR-06"],
           licence=PARL, outil="curl", date_publication="2025-07-01"),
    Source("JAUNE-OPERATEURS-PLF2026", "Ministère de l'Économie (direction du Budget)",
           "PLF 2026, jaune « Opérateurs de l'État » : liste des opérateurs et catégories", "A",
           "https://static.data.gouv.fr/resources/projet-de-loi-de-finances-pour-2026-plf-2026-jaune-operateurs-de-letat-liste-des-operateurs-et-categories/20260113-145343/plf2026-jauneoperateurs.csv",
           "budget/plf2026_jaune_operateurs.csv", ["BUR-01"], licence=LO),
    Source("OCDE-EMPLOI-PUBLIC-2025", "OCDE (Panorama des administrations publiques 2025, diffusé par DBnomics)",
           "Emploi public et représentation : emploi des administrations publiques en % de l'emploi total", "A",
           "https://api.db.nomics.world/v22/series/OECD/DSD_GOV@DF_GOV_EMPPS_REP_2025", "ocde/gov_emploi_public_2025.json",
           ["BUR-03"], licence="CC BY 4.0", params={"observations": "1", "limit": "1000"}),
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
