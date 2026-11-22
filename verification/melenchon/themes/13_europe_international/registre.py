"""Mélenchon, thème 13 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 13
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("13")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
YT = "prises-de-parole-melenchon:youtube:"
A = [
    dict(id="EUR-01", id_corpus=YT + "5Df-5eY6Xtc:361", priorite=1,
         citation="Nous sommes 18% de l'économie du continent, pas 2% comme les Grecs.",
         grandeur_testee="Part de la France et de la Grèce dans le PIB de l'UE et de la zone euro, 2025 (Eurostat)"),
    dict(id="EUR-02", id_corpus=YT + "R7t9n_z35to:24", priorite=2,
         citation="elle engage la plus grande dette publique du monde, 40 000 milliards de dollars",
         autres_versions="« les Américains, parce que 40 000 milliards de dettes » (10/10/2026)",
         grandeur_testee="Dette fédérale des États-Unis (Trésor américain), septembre-octobre 2026"),
    dict(id="EUR-03", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=1,
         citation="Rejeter le tribut, exigé par les États-Unis, de 5 % du PIB consacré aux dépenses de défense",
         grandeur_testee="Dépenses de défense de la France en % du PIB (OTAN, 2025)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
