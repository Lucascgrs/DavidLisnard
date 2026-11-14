"""Thème 1 — Dette, dépense publique et fiscalité : téléchargement de toutes les sources brutes.

python -m verification telecharger 1        (ajouter --forcer pour tout retélécharger)

Chaque fichier est enregistré tel quel dans brut/<organisme>/ puis inscrit dans sources.csv (adresse, requête,
date de téléchargement, empreinte SHA-256, affirmations testées). Rien n'est retouché ici : les calculs lisent ces
fichiers dans calculs/calculer.py.
"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
OCDE = "https://sdmx.oecd.org/public/rest/data/"
FMI = "https://www.imf.org/external/datamapper/api/v1/"
DATAECO = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
AN = "https://www.assemblee-nationale.fr/dyn/contenu/visualisation/"
DGFIP = "https://www.impots.gouv.fr/sites/default/files/media/9_statistiques/0_etudes_et_stats/0_publications/dgfip_statistiques/"
LO = "Licence ouverte Etalab 2.0"
CCBY = "CC BY 4.0"

SOURCES = [
    # --- Eurostat : comptes des administrations publiques (UE, comparables entre pays) ---
    Source("EUROSTAT-GOV10A-MAIN", "Eurostat", "Recettes, dépenses et principaux agrégats des administrations publiques (gov_10a_main)",
           "A", EUROSTAT + "gov_10a_main", "eurostat/gov_10a_main.json",
           ["DETTE-01", "DETTE-03", "DETTE-04", "DETTE-09", "DETTE-20"], licence=CCBY,
           params={"sector": "S13", "unit": ["PC_GDP", "MIO_EUR"], "na_item": ["TE", "TR", "B9", "D41PAY"],
                   "sinceTimePeriod": "1995"}),
    Source("EUROSTAT-EDP-DETTE", "Eurostat", "Dette publique au sens de Maastricht (gov_10dd_edpt1)", "A",
           EUROSTAT + "gov_10dd_edpt1", "eurostat/gov_10dd_edpt1.json", ["DETTE-05", "DETTE-06", "DETTE-07"],
           licence=CCBY, params={"sector": "S13", "na_item": "GD", "unit": ["PC_GDP", "MIO_EUR"],
                                 "sinceTimePeriod": "1995"}),
    Source("EUROSTAT-DETTE-TRIM", "Eurostat", "Dette publique trimestrielle (gov_10q_ggdebt)", "A",
           EUROSTAT + "gov_10q_ggdebt", "eurostat/gov_10q_ggdebt_fr.json", ["DETTE-05"], licence=CCBY,
           params={"geo": "FR", "sector": "S13", "na_item": "GD", "unit": ["PC_GDP", "MIO_EUR"],
                   "sinceTimePeriod": "2017-Q1"}),
    Source("EUROSTAT-TAXAG", "Eurostat", "Principaux agrégats fiscaux (gov_10a_taxag)", "A",
           EUROSTAT + "gov_10a_taxag", "eurostat/gov_10a_taxag.json",
           ["DETTE-02", "DETTE-13", "DETTE-17", "DETTE-22"], licence=CCBY,
           params={"sector": "S13_S212", "unit": ["PC_GDP", "MIO_EUR"],
                   "na_item": ["D2_D5_D91_D61_M_D995", "D29", "D91", "D2", "D5", "D61"], "sinceTimePeriod": "2000"}),
    Source("EUROSTAT-PIB", "Eurostat", "PIB aux prix courants (nama_10_gdp)", "A", EUROSTAT + "nama_10_gdp",
           "eurostat/nama_10_gdp.json", ["DETTE-06", "DETTE-07", "DETTE-20", "DETTE-22"], licence=CCBY,
           params={"na_item": "B1GQ", "unit": "CP_MEUR", "sinceTimePeriod": "2000"}),
    Source("EUROSTAT-SALARIES", "Eurostat", "Emploi salarié, comptes nationaux (nama_10_a10_e)", "A",
           EUROSTAT + "nama_10_a10_e", "eurostat/nama_10_a10_e_fr.json", ["DETTE-21"], licence=CCBY,
           params={"geo": "FR", "na_item": "SAL_DC", "unit": "THS_PER", "nace_r2": "TOTAL", "sinceTimePeriod": "2019"}),
    Source("EUROSTAT-PROTSOC-FONC", "Eurostat", "Dépenses de protection sociale par fonction, % du PIB (spr_exp_func)",
           "A", EUROSTAT + "spr_exp_func", "eurostat/spr_exp_func.json", ["DETTE-10"], licence=CCBY,
           params={"spfunc": "TOTAL", "unit": "PC_GDP", "sinceTimePeriod": "2015"}),
    Source("EUROSTAT-PROTSOC-TYPE", "Eurostat", "Dépenses de protection sociale par type, euros et euros par habitant (spr_exp_type)",
           "A", EUROSTAT + "spr_exp_type", "eurostat/spr_exp_type.json", ["DETTE-10"], licence=CCBY,
           params={"spdeps": ["TOTAL", "SPR"], "unit": ["MIO_EUR", "EUR_HAB", "PPS_HAB"], "sinceTimePeriod": "2015"}),
    # --- FMI : comparaison mondiale ---
    Source("FMI-FM-DEPENSES", "FMI", "Fiscal Monitor (octobre 2026) : dépenses des administrations publiques, % du PIB",
           "A", FMI + "G_X_G01_GDP_PT", "fmi/fiscal_monitor_depenses.json", ["DETTE-01"],
           licence="Conditions d'utilisation FMI (réutilisation avec citation)", entetes={}),
    Source("FMI-FM-RECETTES", "FMI", "Fiscal Monitor (octobre 2026) : recettes des administrations publiques, % du PIB",
           "A", FMI + "GGR_G01_GDP_PT", "fmi/fiscal_monitor_recettes.json", ["DETTE-02"],
           licence="Conditions d'utilisation FMI (réutilisation avec citation)", entetes={}),
    # --- OCDE ---
    Source("OCDE-RECETTES-FISCALES", "OCDE", "Statistiques des recettes publiques, pays de l'OCDE (Revenue Statistics)", "A",
           OCDE + "OECD.CTP.TPS,DSD_REV_COMP_OECD@DF_RSOECD,/..S13._T+T_4300+T_1000+T_2000+T_5000._T.PT_B1GQ+XDC.A",
           "ocde/revenue_statistics.csv", ["DETTE-02", "DETTE-17"], licence=CCBY,
           params={"startPeriod": "2000", "format": "csvfilewithlabels"}),
    Source("OCDE-IMPOTS-SALAIRES", "OCDE", "Les impôts sur les salaires (Taxing Wages) : coin fiscal et social", "A",
           OCDE + "OECD.CTP.TPS,DSD_TAX_WAGES_COMP@DF_TW_COMP,/.AV_TW+AV_R_EMPER_SSC+AV_RITEESSC.PT_COS_LB+PT_WG_EARN_G....A",
           "ocde/taxing_wages.csv", ["DETTE-14"], licence=CCBY,
           params={"startPeriod": "2010", "format": "csvfilewithlabels"}),
    Source("OCDE-SOCX", "OCDE", "Base de données des dépenses sociales (SOCX), agrégats", "A",
           OCDE + "OECD.ELS.SPD,DSD_SOCX_AGG@DF_SOCX_AGG,/.A.SOCX.PT_B1GQ+USD_PPP_PS.ES10+ES10_20._T._T.", "ocde/socx_agg.csv", ["DETTE-10"], licence=CCBY,
           params={"startPeriod": "2015", "format": "csvfilewithlabels"}),
    # --- Banque de France (via DBnomics) : détention de la dette ---
    Source("BDF-NONRESIDENTS", "Banque de France (diffusé par DBnomics)",
           "Détention par les non-résidents de la dette négociable de l'État, en % (série trimestrielle)", "A",
           "https://api.db.nomics.world/v22/series/BDF/DET/Q.FR.1315.F33000.M.Z9.8.F", "bdf/det_nonresidents.json",
           ["DETTE-08"], licence="Banque de France, réutilisation libre avec citation", params={"observations": "1"}),
    # --- Budget de l'État ---
    Source("BUDGET-VERT-PLF2026", "Ministère de l'Économie (direction du Budget)",
           "PLF 2026 — Budget vert : crédits de paiement par programme (exécution 2024, LFI 2025, PLF 2026)", "A",
           DATAECO + "plf-2026-budget-vert/exports/csv", "budget/plf2026_budget_vert.csv", ["DETTE-03", "DETTE-04"],
           licence=LO, params={"delimiter": ";"}),
    Source("PLF2025-DESTINATION", "Ministère de l'Économie (direction du Budget)",
           "PLF 2025 — Dépenses 2025 selon la destination (missions, programmes, actions)", "A",
           DATAECO + "plf25-depenses-2025-selon-destination/exports/csv", "budget/plf2025_destination.csv",
           ["DETTE-03", "DETTE-04"], licence=LO, params={"delimiter": ";"}),
    Source("PLF2024-DESTINATION", "Ministère de l'Économie (direction du Budget)",
           "PLF 2024 — Dépenses 2024 selon les nomenclatures de destination et de nature", "A",
           DATAECO + "plf-2024-depenses-2024-selon-nomenclatures-destination-et-nature/exports/csv",
           "budget/plf2024_destination.csv", ["DETTE-03"], licence=LO, params={"delimiter": ";"}),
    Source("PAP2026-ENGAGEMENTS-FIN", "Ministère de l'Économie (annexe au PLF 2026, publiée par l'Assemblée nationale)",
           "PLF 2026 — Projet annuel de performances, mission Engagements financiers de l'État (charge de la dette)", "A",
           AN + "1087975/file/PAP2026_BG_Engagements_financiers_Etat_EB.pdf", "budget/PAP2026_Engagements_financiers_Etat.pdf",
           ["DETTE-03", "DETTE-04", "DETTE-08"], licence=LO),
    Source("VM2026-TOME1", "Ministère de l'Économie (annexe au PLF 2026, publiée par l'Assemblée nationale)",
           "PLF 2026 — Voies et moyens, tome I : évaluation des recettes", "A",
           AN + "1087930/file/PLF%202026%20-%20V%26M%20TI%20-%20Evaluations%20des%20recettes.pdf",
           "budget/PLF2026_Voies_et_moyens_tome1.pdf", ["DETTE-09", "DETTE-16", "DETTE-21"], licence=LO),
    Source("VM2026-TOME2", "Ministère de l'Économie (annexe au PLF 2026, publiée par l'Assemblée nationale)",
           "PLF 2026 — Voies et moyens, tome II : dépenses fiscales", "A",
           "https://www.assemblee-nationale.fr/dyn/dyn/contenu/visualisation/1087933/file/Voies_et_moyens_Tome_2_2026.pdf",
           "budget/PLF2026_Voies_et_moyens_tome2.pdf", ["DETTE-16"], licence=LO),
    # --- DGFiP : impôt sur le revenu ---
    Source("DGFIP-IR-2023", "DGFiP", "DGFiP Statistiques n° 32 (avril 2025) : l'impôt sur les revenus de 2023 (tableaux)", "A",
           DGFIP + "2025/num32_04/dgfip_stat_32_2025.xlsx", "dgfip/dgfip_stat_32_2025.xlsx", ["DETTE-15"], licence=LO),
    Source("DGFIP-IR-2023-PDF", "DGFiP", "DGFiP Statistiques n° 32 (avril 2025) : l'impôt sur les revenus de 2023", "A",
           DGFIP + "2025/num32_04/dgfip_stat_32_2025.pdf", "dgfip/dgfip_stat_32_2025.pdf", ["DETTE-15"], licence=LO),
    Source("DGFIP-IR-2024", "DGFiP", "DGFiP Statistiques n° 41 (novembre 2025) : l'impôt sur le revenu 2024 (tableaux)", "A",
           DGFIP + "2025/num41_11/dgfip_stat_41.xlsx", "dgfip/dgfip_stat_41.xlsx", ["DETTE-15"], licence=LO),
    Source("DGFIP-IR-2024-PDF", "DGFiP", "DGFiP Statistiques n° 41 (novembre 2025) : l'impôt sur le revenu 2024", "A",
           DGFIP + "2025/num41_11/dgfip_stat_41.pdf", "dgfip/dgfip_stat_41.pdf", ["DETTE-15"], licence=LO),
    # --- Aides aux entreprises ---
    Source("SENAT-AIDES-2025", "Sénat", "Rapport n° 808 (2024-2025) de la commission d'enquête sur les aides publiques aux grandes entreprises, tome I",
           "B", "https://www.senat.fr/rap/r24-808-1/r24-808-11.pdf", "senat/r24-808-1_tome1.pdf", ["DETTE-11"],
           date_publication="2025-07-08", licence="Documents parlementaires, réutilisation libre"),
    Source("SENAT-AIDES-2025-SYN", "Sénat", "Rapport n° 808 (2024-2025), synthèse", "B",
           "https://www.senat.fr/rap/r24-808-1/r24-808-1-syn.pdf", "senat/r24-808-1_synthese.pdf", ["DETTE-11"],
           date_publication="2025-07-08", licence="Documents parlementaires, réutilisation libre"),
    Source("HCSP-AIDES-2025", "Haut-Commissariat à la stratégie et au plan",
           "Note d'analyse n° 157 : les aides publiques aux entreprises (juillet 2025)", "B",
           "https://www.strategie-plan.gouv.fr/files/files/Publications/2025/2025-07-17%20-%20NA%20157%20-%20Aides%20aux%20entreprises/HCSP-2025-NA157-Aides-entreprises-17juillet-11h.pdf",
           "hcsp/HCSP-2025-NA157-aides-entreprises.pdf", ["DETTE-11"], date_publication="2025-07-17", licence=LO),
    Source("CLERSE-AIDES-2022", "CLERSÉ (Université de Lille), étude pour l'IRES commandée par la CGT",
           "Un capitalisme sous perfusion : mesure, théories et effets macroéconomiques des aides publiques aux entreprises (2022)",
           "C", "https://equipementcgt.fr/IMG/pdf/fnee-cgcgt_rapport_capitalisme_sous_perfusion.pdf",
           "clerse/capitalisme_sous_perfusion_2022.pdf", ["DETTE-11"], date_publication="2022",
           note="Copie hébergée par une fédération CGT (commanditaire) ; étude universitaire, origine de son chiffre de 157 Md€."),
    # --- Détention de la dette ---
    Source("SENAT-DETENTION-DETTE", "Sénat", "Rapport d'information n° 902 (2024-2025) sur la détention de la dette publique, synthèse", "B",
           "https://www.senat.fr/rap/r24-902/r24-902-syn.pdf", "senat/r24-902_synthese.pdf", ["DETTE-08"],
           date_publication="2025-09", licence="Documents parlementaires, réutilisation libre"),
    # --- Carburants ---
    Source("CE-BULLETIN-PETROLIER", "Commission européenne (DG Énergie)",
           "Weekly Oil Bulletin : historique des prix des carburants avec et sans taxes, depuis 2005", "A",
           "https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx",
           "commission_europeenne/Weekly_Oil_Bulletin_Prices_History.xlsx", ["DETTE-18"], licence=CCBY),
    # --- Ajouts après la première lecture (charge de la dette 2026-2027, niches 2025, fiscalité des entreprises) ---
    Source("EUROSTAT-INTERETS-TRIM", "Eurostat", "Intérêts payés par les administrations publiques, trimestriel (gov_10q_ggnfa, D41PAY)",
           "A", EUROSTAT + "gov_10q_ggnfa", "eurostat/gov_10q_ggnfa_fr_d41.json", ["DETTE-03", "DETTE-04"], licence=CCBY,
           params={"geo": "FR", "sector": "S13", "na_item": "D41PAY", "unit": "MIO_EUR", "s_adj": "NSA",
                   "sinceTimePeriod": "2022-Q1"}),
    Source("SENAT-EFE-PLF2027", "Sénat (commission des finances)",
           "Note de présentation, mission Engagements financiers de l'État, PLF 2027 (charge de la dette LFI 2026, révisé 2026, PLF 2027)",
           "B", "https://www.senat.fr/fileadmin/cru-1792598966/Commissions/Finances/2026-2027/PLF_2027/NP/NP_EFE_PLF_2027.pdf",
           "senat/NP_EFE_PLF_2027.pdf", ["DETTE-03", "DETTE-04"], date_publication="2026-11",
           licence="Documents parlementaires, réutilisation libre"),
    Source("VM2025-TOME2", "Ministère de l'Économie (annexe au PLF 2025)",
           "PLF 2025 — Voies et moyens, tome II : dépenses fiscales", "A",
           "https://www.publicsenat.fr/app/uploads/2025/04/PLF-2025-Voies_et_moyens_Tome_2_Depenses-fiscales-1.pdf",
           "budget/PLF2025_Voies_et_moyens_tome2.pdf", ["DETTE-16"], licence=LO,
           note="Copie de l'annexe officielle hébergée par Public Sénat (le site du ministère ne la propose plus en lien direct)."),
    Source("FIPECO-PO-ENTREPRISES-2022", "Fipeco (François Ecalle, ancien magistrat de la Cour des comptes)",
           "Les prélèvements sur les sociétés non financières et les subventions qu'elles ont reçues en 2022 (06/12/2023)", "C",
           "https://fipeco.fr/pdf/PO%20nets%20Entreprises%202022.pdf", "fipeco/PO_nets_Entreprises_2022.pdf",
           ["DETTE-11", "DETTE-12"], date_publication="2023-12-06"),
    Source("FIPECO-PO-ENTREPRISES-2019", "Fipeco (François Ecalle)",
           "Les prélèvements sur les entreprises et les subventions qu'elles reçoivent (08/12/2022, données 2019)", "C",
           "https://fipeco.fr/pdf/Entreprises.pdf", "fipeco/Entreprises_2019.pdf", ["DETTE-12"], date_publication="2022-12-08"),
    Source("FIPECO-IMPOTS-PRODUCTION-2022", "Fipeco (François Ecalle)", "Les impôts sur la production en 2022 (08/11/2023)", "C",
           "https://fipeco.fr/pdf/Imp%C3%B4ts%20production2022.pdf", "fipeco/Impots_production_2022.pdf",
           ["DETTE-13", "DETTE-21"], date_publication="2023-11-08"),
    Source("IFRAP-148MD", "Fondation iFRAP (think tank libéral)", "Stop aux 148 milliards d'impôts et taxes en trop pour nos entreprises", "D",
           "https://www.ifrap.org/budget-et-fiscalite/stop-aux-148-milliards-dimpots-et-taxes-en-trop-pour-nos-entreprises",
           "ifrap/stop_aux_148_milliards.html", ["DETTE-12"],
           note="Origine probable du « 13,2 % contre 7,3 % » : sert à retrouver la source, pas d'arbitre."),
    Source("BOFIP-CONTRIBUTION-EXCEPTIONNELLE", "DGFiP (Bulletin officiel des finances publiques)",
           "BOI-IS-AUT-60 : contribution exceptionnelle sur les bénéfices des grandes entreprises", "A",
           "https://bofip.impots.gouv.fr/bofip/14609-PGP.html/ACTU-2025-00035", "droit/bofip_contribution_exceptionnelle.html",
           ["DETTE-19"], licence=LO),
    Source("SP-IMPOT-SOCIETES", "Service-public.fr (DILA)", "Impôt sur les sociétés : taux normal et taux réduit", "A",
           "https://entreprendre.service-public.fr/vosdroits/F23575", "droit/service_public_IS.html", ["DETTE-19"], licence=LO),
    Source("SP-PRELEVEMENTS-SOCIAUX", "Service-public.fr (DILA)", "Prélèvements sociaux sur les revenus du patrimoine et de placement (18,6 %, PFU 31,4 %)",
           "A", "https://www.service-public.fr/particuliers/vosdroits/F2329", "droit/service_public_prelevements_sociaux.html",
           ["DETTE-19"], licence=LO),
    Source("SP-CEHR-CDHR", "Service-public.fr (DILA)", "Contribution exceptionnelle et contribution différentielle sur les hauts revenus",
           "A", "https://www.service-public.fr/particuliers/vosdroits/F31130", "droit/service_public_CEHR_CDHR.html",
           ["DETTE-19"], licence=LO),
]


def main(forcer: bool = False) -> None:
    echecs = []
    for s in SOURCES:
        try:
            telecharger(s, BRUT, forcer=forcer)
            inscrire(s, BRUT, CATALOGUE)
            print(f"  ok  {s.id_source:28} {s.fichier}")
        except Exception as e:  # on continue : une source en échec est signalée, pas bloquante
            echecs.append(s.id_source)
            print(f"  ÉCHEC {s.id_source}: {e}")
    print(f"{len(SOURCES) - len(echecs)}/{len(SOURCES)} sources présentes" + (f" ; échecs : {echecs}" if echecs else ""))


if __name__ == "__main__":
    main(forcer="--forcer" in sys.argv)
