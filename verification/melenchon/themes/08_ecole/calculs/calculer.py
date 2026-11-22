"""Mélenchon, thème 8 — École et enseignement : calculs à partir de brut/.

python -m verification melenchon calculer 8   → calculs/resultats.csv
"""
from verification.commun.calculs import Calculs

NI, IP = "depp/NI_26-05_bac_2025.pdf", "insee/IP1426_competences_ecrit.html"
LUS = {
    "bac_general": (NI, "La proportion de bacheliers dans une génération est de 80,1 % : 43,3 % dans la voie générale",
                    43.3),
    "bac_techno": (NI, "15,9 % dans la voie technologique", 15.9),
    "bac_pro": (NI, "21,0 % dans la voie professionnelle", 21.0),
    "bac_total": (NI, "80,1 % d’une génération est diplômée du baccalauréat", 80.1),
    "illettres": (IP, "Deux millions et demi d’adultes en situation d’illettrisme", 2.5),
    "ecrit_hommes": (IP, "la proportion d’hommes qui éprouvent des difficultés est plus forte que celle des femmes "
                     "(17 % et 15 %)", 17),
    "ecrit_femmes": (IP, "(17 % et 15 %)", 15),
}
C = Calculs(__file__, LUS)


def main():
    C.verifier()
    tp = C.v("bac_techno") + C.v("bac_pro")
    C.res("ECOLE-01", "session 2025", "Bacheliers technologiques et professionnels, en % d'une génération", tp, "%",
          "2025", "DEPP-NI-26-05-BAC", "M1", "50 %", f"technologique {C.v('bac_techno')} %, professionnel "
          f"{C.v('bac_pro')} %", 1)
    C.res("ECOLE-01", "session 2025", "Part d'une génération sans baccalauréat général", 100 - C.v("bac_general"), "%",
          "2025", "DEPP-NI-26-05-BAC", "M1", "50 %",
          f"dont {100 - C.v('bac_total'):.1f} % sans baccalauréat",
          1)
    hommes, femmes = C.v("ecrit_hommes"), C.v("ecrit_femmes")
    C.res("ECOLE-02", "2011, 18-65 ans", "Adultes en situation d'illettrisme", C.v("illettres"), "millions", "2011",
          "INSEE-IP1426-ECRIT", "M2", "près de 4 millions", "dernière enquête nationale de l'Insee", 1)
    C.res("ECOLE-02", "2011, 18-65 ans", "Part des femmes parmi les adultes en difficulté à l'écrit (estimation, à "
          "effectifs égaux d'hommes et de femmes)", femmes / (hommes + femmes) * 100, "%", "2011", "INSEE-IP1426-ECRIT",
          "M2", "six sur dix sont des femmes",
          f"ESTIMATION, non fiable à 100 % : {hommes:.0f} % des hommes et {femmes:.0f} % des femmes en difficulté", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
