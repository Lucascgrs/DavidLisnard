"""Mélenchon, thème 7 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 7
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("07")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="SANTE-01", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="En vingt-cinq ans, l’hôpital public a perdu 80 000 lits, des centaines de maternités et de services "
                  "d’urgence.",
         grandeur_testee="Lits d'hôpital des établissements publics, 1999 → 2024 (Eurostat, DREES)"),
    dict(id="SANTE-02", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="6 millions de personnes n’ont pas de médecin traitant et plus d’un tiers de la population vit dans un "
                  "désert médical.",
         grandeur_testee="Population des communes sous-denses en médecins généralistes (APL de la DREES, 2024)"),
    dict(id="SANTE-03", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Ainsi, 40 % des cancers sont évitables en agissant sur l’environnement.",
         grandeur_testee="Cancers attribuables aux facteurs de risque, dont environnementaux (CIRC, 2018)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
