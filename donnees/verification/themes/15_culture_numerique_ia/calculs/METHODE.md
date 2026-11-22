# Méthode des calculs — thème 15, Culture, numérique et intelligence artificielle

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les PDF et pages HTML sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le
14/11/2026.

## M1 — Grandes entreprises européennes (`NUM-01`)

- Entrée : `DRAGHI-2024-A` : « there is no EU company with a market capitalisation over EUR 100 billion that has
  been set up from scratch in the last fifty years, while all six US companies with a valuation above EUR 1
  trillion have been created in this period ». Aucun calcul.

## M2 — Investissement privé dans l'IA (`NUM-02`)

- Entrée : `STANFORD-AI-INDEX-2026` (page de synthèse du rapport 2026) : 285,9 Md$ aux États-Unis en 2025, 12,4 Md$
  en Chine et 20,92 Md$ en Europe.
- Calcul : 285,9 / 12,4.
- Limite : seul l'investissement privé est compté. Le rapport précise que cela sous-estime probablement la dépense
  chinoise, financée en partie par des fonds publics d'orientation.

## M3 — Semi-conducteurs avancés (`NUM-04`)

- Entrée : `BCG-SIA-2021` : en 2019, toute la capacité de production sous 10 nanomètres est en Corée du Sud (8 %) et
  à Taïwan (92 %). Aucun calcul.
- Limites :
  - source professionnelle (un cabinet de conseil et l'association américaine des fabricants) ;
  - données de 2019, alors que la capacité aux États-Unis et au Japon progresse depuis.

## M4 — Dépenses du ministère de la Culture par habitant (`CULT-01`)

- Entrée : `INSEE-TEF-2021-CULTURE` (Insee, d'après le DEPS du ministère de la Culture, données 2018) :
  - 196 € par habitant en Île-de-France ;
  - 21 € par habitant en moyenne hors Île-de-France ;
  - plus de 3,5 Md€ au total.
- Calcul : 196 / 21, comparé à 801 / 24.
- Limite : le chiffre « par habitant parisien » n'existe pas dans la statistique publique, qui publie par région.
