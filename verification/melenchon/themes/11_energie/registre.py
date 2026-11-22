"""Mélenchon, thème 11 — affirmations relevées dans le corpus → affirmations.csv.

python -m verification melenchon registre 11
"""
from verification.commun.chemins import donnees_de
from verification.commun.registre import ecrire
from verification.commun.themes import intitule

THEME = intitule("11")
PROG, AEC = "90fffc92f061e353", "programme L'Avenir en commun (LFI, 2026)"
YT = "prises-de-parole-melenchon:youtube:"
A = [
    dict(id="NRJ-01", id_corpus=YT + "80bBtk2lTiI:11", priorite=1,
         citation="Depuis Macron, le gaz a augmenté de 150%, pas de 3%.",
         grandeur_testee="Indice des prix du gaz (IPCH), mai 2017 → août 2026"),
    dict(id="NRJ-02", id_corpus=YT + "YQg-98xoxao:9", priorite=2,
         citation="Parce que, au moment des gilets jaunes, on dépassait les 2 euros une fois de temps en temps, et ça "
                  "montait vers 2 euros le litre.",
         grandeur_testee="Prix à la pompe du gazole et de l'essence en France, octobre 2018 → mars 2019"),
    dict(id="NRJ-03", id_corpus=YT + "NSuEVHfqUk4:15", priorite=1,
         citation="Les marges, c'est 7 fois et demie ce qu'elles étaient au début de la guerre.",
         autres_versions="« leur marge a été multipliée par 7,5 sur la raffinerie » (Politico, 24/09/2026) ; « les "
                         "marges des raffineurs ont été multipliées par quatre » (Fête de l'Humanité, 12/09/2026)",
         grandeur_testee="Marge brute de raffinage sur Brent (DGEC), avant la guerre contre l'Iran et en 2026"),
    dict(id="NRJ-04", type="mesure", id_corpus=YT + "YQg-98xoxao:13", priorite=1,
         citation="Donc le premier objectif c'est de ramener le prix à 1,70 en bloquant les prix.",
         autres_versions="« on pourrait les obliger à revenir au prix d'avant la crise à 1,70 € » (LCI, 16/11/2026)",
         grandeur_testee="Prix à la pompe avant la crise et en septembre 2026 (DGEC)", verifiable="partiellement"),
    dict(id="NRJ-05", type="mesure", id_corpus=PROG, date="2026", support=AEC, priorite=2,
         citation="Atteindre le 100 % d’énergies renouvelables au plus tard en 2060, en commençant par organiser la "
                  "sortie des énergies fossiles avant 2050",
         autres_versions="« Planifier la fermeture progressive des centrales nucléaires existantes en ne prolongeant pas "
                         "au-delà de 60 ans leur durée de vie et arrêter le programme de nouveau nucléaire (EPR2) » "
                         "(programme)",
         grandeur_testee="Part des renouvelables dans la consommation d'énergie et part du nucléaire dans l'électricité",
         verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(donnees_de(__file__) / "affirmations.csv", THEME, A), "affirmations")
