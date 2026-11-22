# Méthode des calculs — Mélenchon, thème 8, École et enseignement

Résultats produits par `calculer.py` à partir de `brut/` (catalogue `sources.csv`), dans `resultats.csv`. Les
chiffres lus dans les documents sont dans `LUS`, avec la phrase exacte vérifiée. Données téléchargées le 20/11/2026.

## M1 — Les filières d'une génération (`ECOLE-01`)

- Entrée : `DEPP-NI-26-05-BAC` (proportion de bacheliers dans une génération en 2025 : 80,1 %, dont 43,3 % généraux,
  15,9 % technologiques, 21,0 % professionnels).
- Calculs : technologique + professionnel ; 100 − général (part d'une génération sans baccalauréat général).

## M2 — L'illettrisme (`ECOLE-02`) — ESTIMATION

- Entrée : `INSEE-IP1426-ECRIT` (2,5 millions d'adultes de 18 à 65 ans en situation d'illettrisme ; 17 % des hommes et
  15 % des femmes en difficulté à l'écrit, enquête 2011).
- Calcul : part des femmes parmi les personnes en difficulté = 15 / (17 + 15), en supposant autant d'hommes que de
  femmes de 18 à 65 ans. **Estimation, non fiable à 100 %.**
