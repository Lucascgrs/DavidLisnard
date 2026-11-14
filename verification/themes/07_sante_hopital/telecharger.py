"""Thème 7 — Santé et hôpital : téléchargement des sources brutes.  python -m verification telecharger 7"""
import sys
from pathlib import Path

from verification.commun.sources import Source, inscrire, telecharger

ICI = Path(__file__).resolve().parent
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
DREES = "https://data.drees.solidarites-sante.gouv.fr/api/explore/v2.1/catalog/datasets/"
CCBY, LO = "CC BY 4.0", "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("DREES-APL-GENERALISTES", "DREES", "Accessibilité potentielle localisée (APL) aux médecins généralistes, par commune", "A",
           DREES + "530_l-accessibilite-potentielle-localisee-apl/attachments/indicateur_d_apl_aux_medecins_generalistes_xlsx",
           "drees/APL_medecins_generalistes.xlsx", ["SANTE-01"], licence=LO),
    Source("DREES-APL-LISEZMOI", "DREES", "APL : notice (méthode, seuils de sous-densité)", "A",
           DREES + "530_l-accessibilite-potentielle-localisee-apl/attachments/apl_lisez_moi_pdf", "drees/APL_lisez_moi.pdf",
           ["SANTE-01"], licence=LO),
    Source("DREES-EFFECTIFS-HOSPITALIERS", "DREES (SAE puis DSN)", "Effectifs salariés hospitaliers par profession et secteur, séries longues", "A",
           DREES + "effectifs-salaries-hospitaliers-series-longues/exports/csv", "drees/effectifs_salaries_hospitaliers.csv", ["SANTE-02"],
           licence=LO, params={"delimiter": ";"}),
    Source("EUROSTAT-DEPENSE-SANTE", "Eurostat (comptes de la santé)", "Dépense courante de santé, % du PIB, euros par habitant (hlth_sha11_hf)", "A",
           EUROSTAT + "hlth_sha11_hf", "eurostat/hlth_sha11_hf.json", ["SANTE-03"], licence=CCBY,
           params={"icha11_hf": "TOT_HF", "unit": ["PC_GDP", "EUR_HAB", "PPS_HAB", "MIO_EUR"], "sinceTimePeriod": "2019"}),
    Source("OCDE-MEDECINS", "OCDE (statistiques de la santé, diffusées par DBnomics)", "Médecins (DSD_HEALTH_EMP_REAC@DF_PHYS)", "A",
           "https://api.db.nomics.world/v22/series/OECD/DSD_HEALTH_EMP_REAC@DF_PHYS", "ocde/medecins.json", ["SANTE-04"], licence=CCBY,
           params={"observations": "1", "limit": "1000"}),
    Source("OCDE-DIPLOMES", "OCDE (statistiques de la santé, diffusées par DBnomics)", "Diplômés des professions de santé (DSD_HEALTH_REAC_EMP@DF_GRAD)",
           "A", "https://api.db.nomics.world/v22/series/OECD/DSD_HEALTH_REAC_EMP@DF_GRAD", "ocde/diplomes.json", ["SANTE-04"],
           licence=CCBY, params={"observations": "1", "limit": "1000"}),
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
