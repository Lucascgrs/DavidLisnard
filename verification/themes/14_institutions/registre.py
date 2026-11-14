"""Affirmations du thème 14 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 14"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Institutions, référendum et normes"
A = [
    dict(id="INS-01", id_corpus="18ed78fabe6b5932", priorite=1,
         citation="lors du précédent mandat, 42 maires ont démissionné par mois en France, soit quatre fois plus qu'il y a 20 ans.",
         grandeur_testee="Démissions de maires par mois et par an (ministère de l'Intérieur, étude AMF-Cevipof)"),
    dict(id="INS-02", id_corpus="1cd9653671ac54bb", priorite=1,
         citation="Au total, la France est aujourd’hui régie par 95 838 articles de lois et 258 385 articles de décrets. 73% de plus qu’il y a 20 ans.",
         autres_versions="« Le Journal officiel atteignait 69 549 pages en 2024, contre 33 997 en 2004 » (même document) ; « 1700 décrets qui sont publiés en moyenne […] 88 codes, […] 50 000 textes non codés » (06/01/2021)",
         grandeur_testee="Indicateurs de suivi de l'activité normative (Secrétariat général du Gouvernement)"),
    dict(id="INS-03", id_corpus="96de6b24d5f8e977", priorite=3,
         citation="Le 28 septembre 1958, le peuple français approuva la Constitution par référendum, à près de 83 % des suffrages.",
         autres_versions="« En 1962, par référendum encore, il décida l'élection du Président de la République au suffrage universel direct, à 62 % » (même discours)",
         grandeur_testee="Résultats officiels des référendums de 1958 et 1962"),
    dict(id="INS-04", type="mesure", id_corpus="96de6b24d5f8e977", priorite=2,
         citation="Nous y mettrons fin en révisant l’article 55 de la constitution.",
         autres_versions="« l'extension du champ du référendum (modif art 11) » (X, avril 2025) ; « moratoire sur les normes » (CNews, 28/10/2026)",
         grandeur_testee="Mesure (révision constitutionnelle)", verifiable="non"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
