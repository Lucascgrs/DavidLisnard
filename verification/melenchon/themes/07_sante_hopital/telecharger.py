"""Mélenchon, thème 7 — Santé et hôpital : téléchargement des sources brutes.

python -m verification melenchon telecharger 7        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
CCBY = "CC BY 4.0"

REPRISES = [
    ("DREES-APL-GENERALISTES", "07_sante_hopital", ["SANTE-02"]),
    ("DREES-APL-LISEZMOI", "07_sante_hopital", ["SANTE-02"]),
]
SOURCES = [
    Source("EUROSTAT-LITS-PROPRIETAIRE", "Eurostat (statistiques hospitalières de la DREES)",
           "Lits d'hôpital selon le statut de l'établissement, France (hlth_rs_bds2)", "A", EUROSTAT + "hlth_rs_bds2",
           "eurostat/hlth_rs_bds2_fr.json", ["SANTE-01"], licence=CCBY,
           params={"geo": "FR", "unit": "NR", "sinceTimePeriod": "1999"}),
    Source("EUROSTAT-LITS-TYPE", "Eurostat (statistiques hospitalières de la DREES)",
           "Lits d'hôpital selon le type de soins, France (hlth_rs_bds1)", "A", EUROSTAT + "hlth_rs_bds1",
           "eurostat/hlth_rs_bds1_fr.json", ["SANTE-01"], licence=CCBY,
           params={"geo": "FR", "unit": "NR", "sinceTimePeriod": "1999"}),
    Source("CIRC-CANCERS-EVITABLES-2018", "Centre international de recherche sur le cancer (OMS)",
           "Communiqué n° 261 : cas de cancers attribuables au mode de vie et à l'environnement en France (25 juin 2018)",
           "C", "https://www.iarc.who.int/wp-content/uploads/2018/07/pr261_F.pdf", "circ/pr261_cancers_evitables.pdf",
           ["SANTE-03"], outil="curl", date_publication="2018-06-25"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv, reprises=REPRISES)
