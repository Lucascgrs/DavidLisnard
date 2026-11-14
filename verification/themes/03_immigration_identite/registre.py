"""Affirmations du thème 3 (citations relevées dans le corpus) → affirmations.csv.  python -m verification registre 3"""
from pathlib import Path

from verification.commun.registre import ecrire

THEME = "Immigration, islamisme et identité"
P = "01248e4dc513596d"  # page programme Immigration (site Nouvelle Énergie, sans date ; version de septembre 2026)
A = [
    dict(id="IMMI-01", id_corpus="8ca17e14d81e76af", priorite=1,
         citation="L’immigration de travail a été remplacée par une immigration de peuplement : seuls 13 % des nouveaux titres de séjour sont délivrés pour travailler.",
         autres_versions="« Savez-vous, le pourcentage de nouveaux titres de séjour sur ces quatre cent mille personnes pour des gens qui sont venus bosser ? 17 % » (29/08/2026) ; « 400 000 titres de séjour supplémentaires. 17% seulement pour le travail » (09/09/2026) ; « l’immigration est devenue une immigration de peuplement, avec 500 000 entrées annuelles légales » (03/07/2026)",
         grandeur_testee="Premiers titres de séjour par motif (Eurostat, données du ministère de l'Intérieur)"),
    dict(id="IMMI-02", type="mesure", id_corpus=P, date="2026-09-01", priorite=1,
         citation="Diviser par huit la délivrance de titres de séjour",
         autres_versions="« un objectif de 80 000 entrées par an, visas étudiants compris » (28/10/2026)",
         grandeur_testee="Nombre de titres après division ; composition par motif", verifiable="partiellement"),
    dict(id="IMMI-03", id_corpus="ac30c7a2afa35a11", priorite=1,
         citation="Cette faillite, nous la constatons depuis plusieurs années au travers du taux d’exécution des OQTF, inférieur de plus de 35 points à la moyenne européenne",
         autres_versions="« seule une petite minorité – autour de 10 % – » (même texte, citant la Cour des comptes) ; « 95 % des expulsions décidées n’ont jamais lieu » (Sud Radio, 2023, repris en 2026) ; « plus de 90 % des déboutés du droit d’asile […] ne soient pas expulsés » (08/03/2021)",
         grandeur_testee="Ressortissants renvoyés / ressortissants ayant reçu l'ordre de quitter le territoire, France et UE (Eurostat)"),
    dict(id="IMMI-04", id_corpus="a0f53f821eea41ab", priorite=1,
         citation="Nous supprimerons l’Aide médicale d’État, qui coûte près d’1,4 milliard par an pour près de 500 000 bénéficiaires, soit deux fois plus qu’il y a 15 ans.",
         autres_versions="programme : « Supprimer l’Aide Médicale d’État (AME) et la remplacer par une aide d’urgence : 700 millions d’euros d’économies »",
         grandeur_testee="Dépenses et bénéficiaires de l'AME (Sénat, PLF 2026)"),
    dict(id="IMMI-05", id_corpus="4878c9f90e8afa2c", priorite=2,
         citation="Selon le dernier sondage IFOP de novembre 2025, 38 % des musulmans de France approuvent désormais tout ou partie des positions islamistes, contre 19 % il y a trente ans.",
         grandeur_testee="Résultat publié par l'Ifop, méthode et comparabilité dans le temps"),
    dict(id="IMMI-06", id_corpus="0d24f6cdeaa224bf", priorite=2,
         citation="en vingt ans, le nombre de naissances d’enfants dont les deux parents sont Français a diminué de 13,7 % quand le nombre de naissances d’enfants dont au moins un des deux parents est étranger a augmenté de 63 %",
         autres_versions="« nous n’avons jamais fait aussi peu d’enfants – près de 25% de naissances en moins qu’en 2010 ! » (03/07/2026)",
         grandeur_testee="Naissances selon la nationalité des parents (Insee, état civil)"),
]

if __name__ == "__main__":
    print(ecrire(Path(__file__).resolve().parent / "affirmations.csv", THEME, A), "affirmations")
