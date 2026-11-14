"""Affirmations du thème 7 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 7"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Santé et hôpital"
PS = "24b9759cb8fd9a3e"  # page programme Santé (site Nouvelle Énergie, version de septembre 2026)
LS = "ee63defac3480434"  # Livret Santé 2026
A = [
    dict(id="SANTE-01", id_corpus=PS, date="2026-09-01", priorite=1,
         citation="87 % du territoire manque de médecins",
         autres_versions="« 87 % du territoire est classé en désert médical » (tribune, 26/02/2025) ; « 87% des Français sont confrontés aux déserts médicaux » (19/02/2025) ; « quatre-vingt-sept pour cent du territoire national sont en désert médical » (22/04/2026)",
         grandeur_testee="Part de la population vivant en zone sous-dense (APL de la DREES) ; zonage des ARS"),
    dict(id="SANTE-02", id_corpus=PS, date="2026-09-01", priorite=2,
         citation="Un tiers du personnel hospitalier n’est pas soignant",
         grandeur_testee="Effectifs salariés hospitaliers par profession (DREES)"),
    dict(id="SANTE-03", id_corpus=PS, date="2026-09-01", priorite=1,
         citation="Ce n’est pas une question de moyens – la France dépense plus que ses voisins.",
         autres_versions="« Nous dépensons 12 % du PIB en santé, soit 60 milliards de plus que la moyenne européenne » (réseaux sociaux, 05/2026)",
         grandeur_testee="Dépense courante de santé en % du PIB et par habitant, UE (Eurostat)"),
    dict(id="SANTE-04", id_corpus=LS, date="2026-05-06", priorite=2,
         citation="3,2 médecins pour 1000 habitants (26e rang de l'OCDE), 44 % des médecins âgés de 55 ans et plus, seulement 9,5 nouveaux diplômés pour 100 000 habitants (30e sur 36 pays)",
         grandeur_testee="Médecins en exercice pour 1 000 habitants et diplômés en médecine pour 100 000 habitants (OCDE)"),
    dict(id="SANTE-05", id_corpus=LS, date="2026-05-06", priorite=3,
         citation="22 % des services d'urgences publiques n'ont pas la capacité d'assurer un accueil continu",
         autres_versions="« 23% des urgences hospitalières publiques qui n'assurent plus […] la continuité des soins » (11/06/2026)",
         grandeur_testee="Part des services d'urgences ayant fermé ou régulé l'accès (enquêtes Samu-Urgences de France)", verifiable="partiellement"),
    dict(id="SANTE-06", id_corpus=PS, date="2026-09-01", priorite=3,
         citation="Elle ne produit plus que 30 % des médicaments qu’elle consomme.",
         grandeur_testee="Part de la consommation de médicaments produite en France (LEEM, ANSM)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
