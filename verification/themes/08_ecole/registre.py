"""Affirmations du thème 8 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 8"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "École et enseignement"
A = [
    dict(id="ECOLE-01", id_corpus="2520764a2c94d9dc", priorite=1,
         citation="On est les derniers au classement PISA dans l'Europe",
         autres_versions="« la France sera non plus dernière au classement PISA de l’éducation » (24/01/2025) ; « Le classement PISA, qui nous voit dégrader chaque année, être devenus les cancres de l'Europe » (29/08/2026) ; « le bonnet d’âne hexagonal à chaque classement éducatif international » (19/07/2024)",
         grandeur_testee="Score moyen en mathématiques à PISA 2022, pays de l'UE (OCDE)"),
    dict(id="ECOLE-02", id_corpus="a00d58e9451169bb", priorite=1,
         citation="On dépense 40 % de plus dans l'éducation qu'il y a vingt-cinq ans.",
         autres_versions="« On n'a jamais autant eu de moyens dans l'Éducation nationale » (07/10/2026)",
         grandeur_testee="Dépense publique d'éducation (COFOG 09), euros courants et constants, 2000 → 2025"),
    dict(id="ECOLE-03", id_corpus="47c9cb9b0072c5a9", priorite=2,
         citation="Ça ne coûte pas 60 milliards le primaire, le collège et le lycée, moi j'arrive à 30.",
         grandeur_testee="Crédits de la mission Enseignement scolaire (budget de l'État)", verifiable="partiellement"),
    dict(id="ECOLE-04", type="mesure", id_corpus="0621ce12a92face7", date="2026-09-01", priorite=2,
         citation="l’ instauration du chèque-éducation comme cela a fonctionné dans les pays qui l’ont mis en place",
         grandeur_testee="Effets du libre choix et des chèques-éducation (recherche)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
