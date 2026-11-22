"""Mélenchon, thème 13 — Europe et international : téléchargement des sources brutes.

python -m verification melenchon telecharger 13        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"

REPRISES = [
    ("EUROSTAT-PIB-PAYS-2025", "01_dette_depense_fiscalite", ["EUR-01", "EUR-03"], "melenchon"),
    ("OTAN-DEPENSES-2025", "13_europe_international", ["EUR-03"]),
]
SOURCES = [
    Source("TRESOR-US-DETTE", "Département du Trésor des États-Unis (Fiscal Data)",
           "Debt to the Penny : dette fédérale totale, quotidienne, depuis septembre 2026", "A",
           "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny",
           "tresor_us/debt_to_penny_2026.json", ["EUR-02"], licence="Domaine public (États-Unis)",
           params={"filter": "record_date:gte:2026-09-01", "sort": "record_date", "page[size]": "200",
                   "fields": "record_date,tot_pub_debt_out_amt,debt_held_public_amt"}),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
