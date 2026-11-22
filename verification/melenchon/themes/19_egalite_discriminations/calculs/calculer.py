"""Mélenchon, thème 19 — Égalité femmes-hommes et discriminations : calculs à partir de brut/.

python -m verification melenchon calculer 19   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

INSEE = "insee/focus_ecarts_salaire_2024.html"
LUS = {
    "ecart_revenu": (INSEE, "le revenu salarial moyen des femmes est inférieur de 21,8 % à celui des hommes", 21.8),
    "ecart_eqtp": (INSEE, "les femmes gagnent en moyenne 21,8 % de moins en revenu salarial et 14,0 % de moins en "
                   "équivalent temps plein", 14.0),
    "rang_2017": ("ilga/rainbow_europe_map_2017.pdf", "Norway United Kingdom Belgium France Portugal Finland, Denmark", 5),
    "rang_2026": ("ilga/rainbow_map_2026.html", "France retains 15th place in the ranking", 15),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    C.res("EGAL-01", "secteur privé, 2024", "Écart de revenu salarial moyen (femmes par rapport aux hommes)",
          C.v("ecart_revenu"), "%", "2024", "INSEE-FOCUS-ECARTS-SALAIRE-2024", "M1", "22 %",
          f"à temps de travail égal (équivalent temps plein) : {C.v('ecart_eqtp')} %", 1)
    C.res("EGAL-02", "mai 2017", "Rang de la France (droits LGBTI, lois et politiques)", C.v("rang_2017"), "rang",
          "2017", "ILGA-RAINBOW-MAP-2017", "M2", "cinquième", "après Malte, la Norvège, le Royaume-Uni et la Belgique",
          0)
    C.res("EGAL-02", "mai 2026", "Rang de la France (droits LGBTI, lois et politiques)", C.v("rang_2026"), "rang",
          "2026", "ILGA-RAINBOW-MAP-2026", "M2", "quinzième", "sur 49 pays, score de 60 %", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
