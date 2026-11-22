"""Chemins du paquet verification/.

Le code (ce paquet, les scripts de chaque thème : registre.py, telecharger.py, calculs/calculer.py, et le site) est
dans verification/ ; toutes les données sont dans donnees/verification/ : corpus/, registre_affirmations.csv,
SYNTHESE.md et, pour chaque thème, un dossier du même nom que celui de ses scripts (affirmations.csv, position.md,
analyse.md, sources.csv, brut/, calculs/ sauf calculer.py).

Ces constantes sont celles de David Lisnard ; chaque autre candidat a les mêmes dans son sous-dossier
(commun/personnes.py). donnees_de() trouve seul la personne d'un script.
"""
from pathlib import Path

from .personnes import DONNEES_VERIF, RACINE, personne, personne_du_chemin

_L = personne("lisnard")
SCRIPTS = _L.scripts  # scripts de chaque thème
DONNEES = DONNEES_VERIF
CORPUS = _L.corpus
THEMES = _L.themes  # données de chaque thème
REGISTRE = _L.registre
SYNTHESE = _L.synthese


def donnees_de(script: str | Path) -> Path:
    """Dossier de données d'un script de thème : <code>/themes/<thème>[/calculs]/x.py →
    <données>/themes/<thème>[/calculs]/ (créé au besoin), pour la personne du script."""
    p = personne_du_chemin(script)
    dossier = p.themes / Path(script).resolve().parent.relative_to(p.scripts)
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier
