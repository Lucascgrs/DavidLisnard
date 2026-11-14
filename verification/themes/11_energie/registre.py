"""Affirmations du thème 11 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 11"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Énergie et nucléaire"
A = [
    dict(id="NRJ-01", id_corpus="00201ec474bcaaf9", priorite=2,
         citation="le nucléaire, qui en France produit encore 70 % de notre électricité",
         grandeur_testee="Part du nucléaire dans la production d'électricité (Eurostat)"),
    dict(id="NRJ-02", id_corpus="1cd9653671ac54bb", priorite=2,
         citation="Réformer le DPE en supprimant les indicateurs d’énergie primaire qui pénalisent le chauffage électrique dans un pays à plus de 90 % d’électricité décarbonée.",
         grandeur_testee="Part nucléaire + renouvelables dans la production d'électricité (Eurostat)"),
    dict(id="NRJ-03", id_corpus="6e2b70813bb3145e", priorite=1,
         citation="On sait bien que la France représente à peu près, elle doit représenter 2,4% du PIB mondial et qu'on représente 0,7% des émissions carbone, il faut rajouter les produits importés là-dedans.",
         grandeur_testee="Part de la France dans le PIB mondial (FMI) et dans les émissions de CO2 (Global Carbon Budget)"),
    dict(id="NRJ-04", id_corpus="6e2b70813bb3145e", priorite=2,
         citation="si on prend les 30 dernières années de l'Union européenne, on a une progression du PIB qui doit être de 70% sur 30 ans, un peu plus. Et on a eu une baisse des émissions de carbone de 37%.",
         grandeur_testee="PIB en volume et émissions de gaz à effet de serre de l'UE à 27 (Eurostat)"),
    dict(id="NRJ-05", id_corpus="36ef214f9db258f7", priorite=1,
         citation="Entre 2021 et 2024, le prix de l’électricité pour les entreprises a augmenté de 67 % malgré les aides, et le prix industriel final atteint 165 €/MWh contre 73 €/MWh aux États-Unis.",
         grandeur_testee="Prix de l'électricité des entreprises (Eurostat) et prix industriel américain (EIA)"),
    dict(id="NRJ-06", id_corpus="c7beed9ec77d50a2", priorite=2,
         citation="une accise sur l’électricité à 30,35 euros/MWh pour les ménages, en hausse de 37 % depuis 2019, quand l’Allemagne l’a ramenée à 0,5 euro/MWh pour son industrie.",
         grandeur_testee="Tarifs de l'accise sur l'électricité (BOFiP, Assemblée nationale) et de la Stromsteuer (loi allemande)"),
    dict(id="NRJ-07", id_corpus="2c9c93dc6dc43b31", priorite=2,
         citation="La Commission de régulation de l'énergie prévoit 1,3 milliard d'euros de charges de soutien à l'éolien terrestre seul en 2026, sur un total de 12,9 milliards d'euros de charges de service public de l'énergie.",
         autres_versions="« Le coût de rachat moyen du parc éolien terrestre existant s'établit à 97,5 €/MWh en 2025, soit 37 euros au-dessus du prix de marché » (même article)",
         grandeur_testee="Charges de service public de l'énergie (CRE, délibération 2025-180)"),
    dict(id="NRJ-08", id_corpus="bae9e369da70f247", date="2026-04-23", priorite=2,
         citation="L'Agence internationale de l'énergie évalue notre potentiel techniquement récupérable en gaz de schiste à 3 879 milliards de m³, le deuxième d'Europe, l'équivalent de 95 ans de consommation nationale.",
         grandeur_testee="Ressources de gaz de schiste (EIA 2013) et consommation de gaz (Eurostat)"),
    dict(id="NRJ-09", id_corpus="859f15de1de9c6c1", priorite=3,
         citation="les DPE appliquent un malus injustifié de 230 % à l’électricité",
         grandeur_testee="Coefficient de conversion de l'électricité en énergie primaire du DPE"),
    dict(id="NRJ-10", id_corpus="7fb92e900b9f2b78", priorite=3,
         citation="Emmanuel Macron a commis là une faute majeure, en démantelant Fessenheim et en programmant la fermeture de quatorze réacteurs lors de son premier mandat, avant de rétropédaler en 2022.",
         grandeur_testee="Programmation pluriannuelle de l'énergie 2019-2028 (décret d'avril 2020)"),
    dict(id="NRJ-11", id_corpus="6e2b70813bb3145e", priorite=2,
         citation="sur de l'éolien en mer qui rien que pour le raccordement va coûter 37 milliards d'euros",
         grandeur_testee="Investissements de raccordement en mer du schéma décennal de RTE (SDDR 2025)"),
    dict(id="NRJ-12", type="mesure", id_corpus="c44b52e96a1a4f70", priorite=3,
         citation="Arrêter le plan de démantèlement, prolonger les réacteurs jusqu’à soixante ans par des investissements de maintenance et de sûreté, engager une première série de six EPR, déployer des mini-réacteurs pour renouveler le parc de première génération",
         grandeur_testee="Mesure (programme nucléaire)", verifiable="non"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
