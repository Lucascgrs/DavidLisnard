"""Affirmations du thème 9 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 9"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Retraites et protection sociale"
A = [
    dict(id="RET-01", id_corpus="03c98af3f1e41600", priorite=1,
         citation="Toujours selon l’institut Molinari, « le vrai déséquilibre des retraites est de 2,8 % en 2020, bien au-delà du déficit mis en avant par le COR (0,6 %) »",
         autres_versions="« pour ne pas faire apparaître l’immense déficit des retraites, on impute des cotisations sociales allant jusqu’à 80% du salaire des fonctionnaires » (16/10/2026)",
         grandeur_testee="Solde du système de retraite selon les conventions comptables (Cour des comptes, COR)"),
    dict(id="RET-02", type="mesure", id_corpus="9bd690b50b94ed7b", date="2026-09-01", priorite=1,
         citation="pour atteindre un montant de capitalisation évalué à 116 milliards d’euros, soit environ 40% du montant total des retraites",
         grandeur_testee="Dépenses de retraite (vieillesse et survie) en France (Eurostat)", verifiable="partiellement"),
    dict(id="RET-03", id_corpus="fd30e16db1490020", priorite=2,
         citation="cette personne au SMIC qui cotise 10%, au bout de 40 ans pouvait bénéficier d'un capital de plus de 320 000 euros",
         grandeur_testee="Rendement annuel nécessaire pour atteindre 320 000 € avec 10 % du SMIC pendant 40 ans", verifiable="partiellement"),
    dict(id="RET-04", id_corpus="91fd285cc9204f60", priorite=2,
         citation="le livre cite le rendement moyen de 5,4 % par an des placements de l’Erafp depuis 2006",
         grandeur_testee="Rendement annualisé du régime additionnel de la fonction publique (rapport annuel de l'Erafp)"),
    dict(id="RET-05", id_corpus="6c735fa2b3e701c2", date="2026-06-10", priorite=3,
         citation="En ce jour de grève de la SNCF, rappelons que le montant de son régime spécial des retraites, à 5,5 milliards d’euros, représente à lui seul une grosse moitié de tout le budget de la Justice",
         grandeur_testee="Subvention de l'État au régime de retraite de la SNCF et crédits de la mission Justice (budget de l'État)", verifiable="partiellement"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
