"""Thème 3 — Immigration, islamisme et identité : téléchargement des sources brutes.

python -m verification telecharger 3
Le site statistique de la direction générale des étrangers en France (DGEF) refuse les téléchargements automatiques :
les titres de séjour et les éloignements viennent d'Eurostat, qui reprend les données transmises par la France.
"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
LO, CCBY, PARL = "Licence ouverte Etalab 2.0", "CC BY 4.0", "Documents parlementaires, réutilisation libre"

SOURCES = [
    Source("EUROSTAT-PREMIERS-TITRES", "Eurostat (données transmises par le ministère de l'Intérieur)",
           "Premiers titres de séjour délivrés à des ressortissants de pays tiers, par motif (migr_resfirst)", "A",
           EUROSTAT + "migr_resfirst", "eurostat/migr_resfirst.json", ["IMMI-01", "IMMI-02"], licence=CCBY,
           params={"citizen": "TOTAL", "duration": "TOTAL", "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-OQTF", "Eurostat", "Ressortissants de pays tiers ayant reçu l'ordre de quitter le territoire (migr_eiord)", "A",
           EUROSTAT + "migr_eiord", "eurostat/migr_eiord.json", ["IMMI-03"], licence=CCBY,
           params={"citizen": "TOTAL", "age": "TOTAL", "sex": "T", "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-RETOURS", "Eurostat", "Ressortissants de pays tiers renvoyés à la suite d'un ordre de quitter le territoire (migr_eirtn)",
           "A", EUROSTAT + "migr_eirtn", "eurostat/migr_eirtn.json", ["IMMI-03"], licence=CCBY,
           params={"citizen": "TOTAL", "age": "TOTAL", "sex": "T", "c_dest": "TOTAL", "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-NAISSANCES", "Eurostat (données Insee)", "Naissances vivantes, France (demo_gind)", "A",
           EUROSTAT + "demo_gind", "eurostat/demo_gind_fr.json", ["IMMI-06"], licence=CCBY,
           params={"geo": "FR", "indic_de": "LBIRTH", "sinceTimePeriod": "1998"}),
    Source("INSEE-NAISSANCES-NATIONALITE", "Insee (état civil)",
           "Naissances selon la nationalité et le pays de naissance des parents, 1998-2025", "A",
           "https://www.insee.fr/fr/statistiques/fichier/2381382/demo-naiss-natio-pays-2.xlsx",
           "insee/demo-naiss-natio-pays-2.xlsx", ["IMMI-06"], licence=LO),
    Source("CC-IMMIGRATION-IRREGULIERE-2024", "Cour des comptes",
           "La politique de lutte contre l'immigration irrégulière (rapport public thématique, janvier 2024)", "B",
           "https://www.ccomptes.fr/sites/default/files/2024-02/20240104_Politique-lutte-contre-immigration-irreguliere.pdf",
           "cour_des_comptes/20240104_lutte_immigration_irreguliere.pdf", ["IMMI-03"], licence=LO, outil="curl",
           date_publication="2024-01-04"),
    Source("SENAT-SANTE-PLF2026", "Sénat (commission des finances)", "Note de présentation de la mission Santé, PLF 2026 (aide médicale de l'État)",
           "B", "https://www.senat.fr/fileadmin/cru-1762483659/Commissions/Finances/2025-2026/PLF_2026/NP/Sante_PLF_2026_NP.pdf",
           "senat/Sante_PLF_2026_NP.pdf", ["IMMI-04"], licence=PARL, outil="curl", date_publication="2025-11"),
    Source("IFOP-ISLAM-2025", "Ifop (sondage)",
           "État des lieux du rapport à l'islam et à l'islamisme des musulmans de France (novembre 2025), présentation des résultats",
           "D", "https://www.ifop.com/wp-content/uploads/2025/11/info-1.pdf", "ifop/ifop_islam_islamisme_2025.pdf", ["IMMI-05"],
           outil="curl", date_publication="2025-11-18",
           note="Sondage commercial : on vérifie la citation et la méthode, pas une mesure statistique publique."),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:30} {s.fichier}")
        except Exception as e:
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
