"""Mélenchon, thème 9 — Retraites et protection sociale : calculs à partir de brut/.

python -m verification melenchon calculer 9   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

AGE, TRIM = "droit/service_public_F14043_age_retraite.html", "droit/service_public_F35063_trimestres.html"
LUS = {
    "age_1963": (AGE, "Entre le 1 er janvier 1963 et le 31 mars 1965 62 ans et 9 mois", 62.75),
    "age_1969": (AGE, "À partir du 1 er janvier 1969 64 ans", 64),
    "trim_1969": (TRIM, "À partir du 1 er janvier 1969 64 ans 172 (43 ans)", 172),
    "trim_1963": (TRIM, "Entre le 1 er janvier 1963 et le 31 mars 1965 62 ans et 9 mois 170 (42 ans 6 mois)", 170),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("RET-01", "nés de 1963 à mars 1965", "Âge légal de départ aujourd'hui", C.v("age_1963"), "ans", "2026",
          "SP-AGE-RETRAITE", "M1", "62 ans puis 60 ans", "62 ans et 9 mois", 2)
    C.res("RET-01", "nés à partir de 1969", "Âge légal de départ aujourd'hui", C.v("age_1969"), "ans", "2026",
          "SP-AGE-RETRAITE", "M1", "62 ans puis 60 ans", "", 0)
    C.res("RET-01", "nés à partir de 1969", "Trimestres exigés pour le taux plein", C.v("trim_1969"), "trimestres",
          "2026", "SP-TRIMESTRES-TAUX-PLEIN", "M1", "40 annuités (160 trimestres)",
          f"{C.v('trim_1969') - 160:.0f} trimestres de plus que 40 annuités", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
