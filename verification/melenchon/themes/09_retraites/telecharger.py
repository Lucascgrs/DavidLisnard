"""Mélenchon, thème 9 — Retraites et protection sociale : téléchargement des sources brutes.

python -m verification melenchon telecharger 9        (ajouter --forcer pour tout retélécharger)
"""
import sys

from verification.commun.chemins import donnees_de
from verification.commun.sources import Source, executer

ICI = donnees_de(__file__)
BRUT, CATALOGUE = ICI / "brut", ICI / "sources.csv"
SP, LO = "https://www.service-public.fr/particuliers/vosdroits/", "Licence ouverte Etalab 2.0"

SOURCES = [
    Source("SP-AGE-RETRAITE", "Service-public.fr (direction de l'information légale et administrative)",
           "À partir de quel âge un salarié peut-il partir en retraite ? (F14043)", "A", SP + "F14043",
           "droit/service_public_F14043_age_retraite.html", ["RET-01"], licence=LO, outil="curl"),
    Source("SP-TRIMESTRES-TAUX-PLEIN", "Service-public.fr (direction de l'information légale et administrative)",
           "Combien de trimestres un salarié doit-il avoir pour bénéficier d'une retraite à taux plein ? (F35063)", "A",
           SP + "F35063", "droit/service_public_F35063_trimestres.html", ["RET-01"], licence=LO, outil="curl"),
]

if __name__ == "__main__":
    executer(SOURCES, BRUT, CATALOGUE, forcer="--forcer" in sys.argv)
