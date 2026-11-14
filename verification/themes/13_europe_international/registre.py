"""Affirmations du thème 13 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 13"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Europe et international"
A = [
    dict(id="EUR-01", id_corpus="98b8bc58a8cad628", priorite=1,
         citation="la France vient de passer en richesse par habitant, c'est la première fois dans notre histoire contemporaine, c'est très important, pardonnez-moi de le dire, en dessous de la moyenne européenne.",
         autres_versions="« Depuis 2022, notre PIB par habitant est passé sous la moyenne de l'Union européenne » (Livre noir de la bureaucratie, 2026 ; discours du 22/04/2026)",
         grandeur_testee="PIB par habitant en standards de pouvoir d'achat, indice UE = 100 (Eurostat)"),
    dict(id="EUR-02", id_corpus="971c01539f2d19fe", priorite=2,
         citation="On vient de passer derrière l’Italie en création de richesse par habitant",
         grandeur_testee="PIB par habitant en standards de pouvoir d'achat, France et Italie (Eurostat)"),
    dict(id="EUR-03", id_corpus="5fe642c21296238c", priorite=1,
         citation="on était au 7e rang de création de richesse par habitant il y a 30 ans, qu'on est au 27e rang",
         autres_versions="« Dans les années 80, la France affichait le 11ème PIB par habitant du monde, devant les États-Unis. Quarante ans plus tard, elle est au 24e rang » (Livre noir, 2026) ; « la septième puissance en production de richesse par habitant […] aujourd'hui au vingt-septième rang » (discours, 25/09/2026)",
         grandeur_testee="Rang mondial du PIB par habitant (FMI, en dollars courants et en parité de pouvoir d'achat)"),
    dict(id="EUR-04", id_corpus="36ef214f9db258f7", priorite=2,
         citation="Selon le rapport Draghi, cette seule divergence explique 70 % de l’écart de PIB par habitant entre l’Union européenne et les États-Unis.",
         autres_versions="« La productivité horaire de la zone euro, qui atteignait 98 % de celle des États-Unis en 1995, n'en représentait plus que 82 % en 2019 » (même texte)",
         grandeur_testee="Rapport Draghi (septembre 2024), partie A"),
    dict(id="EUR-05", id_corpus="6622efdfd4caa309", priorite=2,
         citation="Aujourd’hui, la France consacre 57 milliards d’euros à sa défense, soit à peine 2 % de la richesse nationale.",
         autres_versions="« Passer de 2,06 % à 3 % du PIB consacré à la défense […] représente 27 milliards d'€ supplémentaires par an. Atteindre 3,5 %, c'est plus de 40 milliards/an » (X, 03/03/2026)",
         grandeur_testee="Dépenses de défense de la France (OTAN) et PIB (Eurostat)"),
    dict(id="EUR-06", id_corpus="127b429195e1c2ac", priorite=1,
         citation="Le déficit commercial de l’Union européenne avec Pékin a atteint le niveau record de 360 milliards d’euros en 2025.",
         grandeur_testee="Solde commercial de l'UE avec la Chine (Eurostat Comext)"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
