"""Thème 2 — Sécurité, justice et narcotrafic : téléchargement des sources brutes.

python -m verification telecharger 2        (ajouter --forcer pour tout retélécharger)
"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
LO, CCBY = "Licence ouverte Etalab 2.0", "CC BY 4.0"
DG = "https://static.data.gouv.fr/resources/"
SSMSI = DG + "bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales/"
DAP = DG + "statistique-mensuelle-de-la-population-ecrouee-et-detenue-en-france/"
PM = DG + "police-municipale-effectifs-par-commune/"
PARL = "Documents parlementaires, réutilisation libre"

SOURCES = [
    Source("SSMSI-DELINQUANCE-DEP", "Ministère de l'Intérieur (SSMSI)",
           "Base départementale de la délinquance enregistrée par la police et la gendarmerie, 2016-2025 (édition juillet 2026)",
           "A", SSMSI + "20260709-120038/donnee-dep-data.gouv-2025-geographie2026-produit-le2026-06-25.csv",
           "ssmsi/delinquance_departementale_2016_2025.csv", ["SECU-01", "SECU-07"], licence=LO,
           date_publication="2026-07-09"),
    Source("SSMSI-DOCUMENTATION", "Ministère de l'Intérieur (SSMSI)", "Documentation des bases statistiques de la délinquance (juillet 2026)",
           "A", SSMSI + "20260709-120136/fichier-metadonnees-data-gouv-geographie-delinquance-juillet2026.pdf",
           "ssmsi/documentation_bases_delinquance.pdf", ["SECU-01"], licence=LO),
    Source("DAP-DETENUS-2026-09", "Ministère de la Justice (direction de l'administration pénitentiaire)",
           "Statistique mensuelle de la population détenue et écrouée, situation au 1er septembre 2026", "A",
           DAP + "20261013-162028/statistique-etablissements-01092026.xlsx", "dap/statistique_etablissements_01092026.xlsx",
           ["SECU-02"], licence=LO),
    Source("DAP-DETENUS-2025-09", "Ministère de la Justice (direction de l'administration pénitentiaire)",
           "Statistique mensuelle de la population détenue et écrouée, situation au 1er septembre 2025", "A",
           DAP + "20261011-161011/statistique-etablissements-personnes-ecrouees-01092025.xlsx",
           "dap/statistique_etablissements_01092025.xlsx", ["SECU-02"], licence=LO),
    Source("SENAT-PENITENTIAIRE-PLF2026", "Sénat (commission des lois)",
           "Avis sur le PLF 2026, administration pénitentiaire : synthèse (détenus, densité, places)", "B",
           "https://www.senat.fr/rap/a25-145-6/a25-145-6-syn.pdf", "senat/a25-145-6_synthese_penitentiaire.pdf",
           ["SECU-02", "SECU-09"], licence=PARL, date_publication="2025-11"),
    Source("COE-SPACE-I-2024", "Conseil de l'Europe (SPACE I, Université de Lausanne)",
           "Statistiques pénales annuelles du Conseil de l'Europe, SPACE I 2024 (prisons au 31 janvier 2024)", "A",
           "https://wp.unil.ch/space/files/2025/09/250924_rapport-space-i-2024.pdf", "conseil_europe/SPACE_I_2024.pdf",
           ["SECU-02"], date_publication="2025-09-24", licence="Conseil de l'Europe, citation requise"),
    Source("IGJ-EXECUTION-PEINES-2022", "Inspection générale de la justice",
           "Exécution des peines d'emprisonnement ferme, rapport n° 022-22 (mars 2022)", "B",
           "https://www.vie-publique.fr/files/rapport/pdf/301357.pdf", "justice/IGJ_execution_peines_2022.pdf", ["SECU-03"],
           licence=LO, date_publication="2022-03"),
    Source("RSJ-2025-EXECUTION", "Ministère de la Justice (SDSE)",
           "Références statistiques justice, édition 2025, chapitre 12 : exécution et application des peines", "A",
           "https://www.justice.gouv.fr/sites/default/files/2026-01/RSJ2025%20chapitre%2012.pdf",
           "justice/RSJ2025_chapitre12.pdf", ["SECU-03"], licence=LO),
    Source("RSJ-2026-EXECUTION", "Ministère de la Justice (SDSE)",
           "Références statistiques justice, édition 2026, fiche 12.1 : mise à exécution des peines d'emprisonnement ferme",
           "A", "https://www.justice.gouv.fr/sites/default/files/2026-07/RSJ2026%2012_1.pdf",
           "justice/RSJ2026_12_1.pdf", ["SECU-03"], licence=LO),
    Source("CEPEJ-FRANCE-2024", "Conseil de l'Europe (CEPEJ), étude pour la Commission européenne",
           "Systèmes judiciaires des États membres de l'UE, fiche pays France (données 2024)", "A",
           "https://rm.coe.int/france-country-fiche/48802c1521", "conseil_europe/CEPEJ_fiche_France_2024.pdf", ["SECU-04"],
           licence="Conseil de l'Europe, citation requise"),
    Source("PM-EFFECTIFS-2024", "Ministère de l'Intérieur", "Effectifs de police municipale par commune, 2024", "A",
           PM + "20260212-085753/enquete-stats-pm-2024.ods", "interieur/effectifs_police_municipale_2024.ods", ["SECU-05"],
           licence=LO),
    Source("PM-EFFECTIFS-2014", "Ministère de l'Intérieur", "Effectifs de police municipale par commune, 2014", "A",
           PM + "20150817-171722/PM_enquete_2014_communes_ASVP.xlsx", "interieur/effectifs_police_municipale_2014.xlsx",
           ["SECU-05"], licence=LO),
    Source("GEO-COMMUNES", "État (API Découpage administratif, geo.api.gouv.fr, données Insee/IGN)",
           "Liste des communes françaises (code, nom, population)", "A", "https://geo.api.gouv.fr/communes",
           "geo/communes.json", ["SECU-05"], licence=LO, params={"fields": "code,nom,population", "format": "json"}),
    Source("SENAT-NARCOTRAFIC-2024", "Sénat (commission d'enquête)",
           "Rapport n° 588 (2023-2024) sur l'impact du narcotrafic en France : l'essentiel", "B",
           "https://www.senat.fr/rap/r23-588-1/r23-588-1-syn.pdf", "senat/r23-588-1_synthese_narcotrafic.pdf", ["SECU-06"],
           licence=PARL, date_publication="2024-05"),
    Source("AN-QE-12391-PRISONS", "Assemblée nationale (question écrite et réponse du ministère)",
           "Question écrite n° 12391 (16e législature) sur le coût du plan 15 000 places", "B",
           "https://questions.assemblee-nationale.fr/dyn/16/questions/QANR5L16QE12391.pdf", "assemblee/QE12391_plan_15000.pdf",
           ["SECU-09"], licence=PARL),
    Source("SENAT-PLAN15000-2023", "Sénat (commission des finances)",
           "Rapport d'information n° 37 (2023-2024) sur le plan 15 000 places et les centres éducatifs fermés : l'essentiel",
           "B", "https://www.senat.fr/rap/r23-037/r23-037-syn.pdf", "senat/r23-037_synthese_plan15000.pdf", ["SECU-07"],
           licence=PARL, date_publication="2023-10"),
    Source("CC-2002-461-DC", "Conseil constitutionnel", "Décision n° 2002-461 DC du 29 août 2002 (justice des mineurs)", "A",
           "https://www.conseil-constitutionnel.fr/decision/2002/2002461DC.htm", "conseil_constitutionnel/2002-461-DC.html",
           ["SECU-10"], licence=LO),
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
