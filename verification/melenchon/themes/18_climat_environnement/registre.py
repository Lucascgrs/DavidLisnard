"""Mélenchon, thème 18 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 18
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("18")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
A = [
    dict(id="CLIM-01", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="À l’époque, 2016 avait été l’année la plus chaude jamais enregistrée sur terre. Depuis, le record a "
                  "été battu en 2020, 2023, 2024 et 2025.",
         grandeur_testee="Température moyenne mondiale annuelle, 2016-2025 (Copernicus, ERA5)"),
    dict(id="CLIM-02", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Respecter au plus vite les engagements climatiques de la France, relever le niveau de ses ambitions, "
                  "avec une baisse de 65 % des émissions de gaz à effet de serre (GES) d’ici 2033",
         grandeur_testee="Émissions de gaz à effet de serre de la France depuis 1990 (inventaire, Eurostat)",
         verifiable="partiellement"),
    dict(id="CLIM-03", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="La forêt couvre un tiers du territoire hexagonal et environ 85 % des territoires ultramarins. […] La "
                  "mortalité des arbres a augmenté de 125 % en dix ans.",
         grandeur_testee="Taux de boisement et mortalité des arbres (IGN, mémento 2025)"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
