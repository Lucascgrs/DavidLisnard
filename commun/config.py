"""Emplacements du projet et fichiers de réglages.

config/ contient les réglages : perimetre.json (ce qui est collecté, modifiable depuis l'interface), cles.json
(clé de l'API YouTube, privée), compte.json (compte Instagram de collecte, privé) et planification.json.
"""
from pathlib import Path

from commun.fichiers import lire_json

RACINE = Path(__file__).resolve().parent.parent
CONFIG = RACINE / "config"
DONNEES = RACINE / "donnees"
MODELES = RACINE / "modeles"
SESSIONS = RACINE / "sessions"
DOCS = RACINE / "docs"

FICHIER_PERIMETRE = CONFIG / "perimetre.json"
FICHIER_CLES = CONFIG / "cles.json"
FICHIER_COMPTE = CONFIG / "compte.json"
FICHIER_PLANIFICATION = CONFIG / "planification.json"
FICHIER_FACEBOOK_ENV = CONFIG / "facebook.env"  # FB_MAIL et FB_MDP du compte Facebook de collecte (privé)
FICHIER_X_ENV = CONFIG / "x.env"  # X_PSEUDO et X_MDP du compte X de collecte (privé)

# Sources collectées, dans l'ordre de passage : YouTube et Bluesky (API, sans fenêtre), Instagram (navigateur), puis
# Facebook (groupes publics, requêtes directes au rythme réglé dans perimetre.json : la plus longue, ajoutée le
# 2026-11-12), et X (recherche interne du site avec le compte de collecte, au rythme réglé dans perimetre.json : ajouté
# le 2026-11-13). Reddit et TikTok ne sont pas collectés, WhatsApp ne l'est plus (2026-11-12) : voir README.md.
SOURCES = {"youtube": "YouTube", "bluesky": "Bluesky", "instagram": "Instagram", "facebook": "Facebook", "x": "X"}


def perimetre() -> dict:
    return lire_json(FICHIER_PERIMETRE, {})


def cles() -> dict:
    return lire_json(FICHIER_CLES, {})


def lire_env(chemin: Path) -> dict:
    """Un fichier « NOM=valeur » par ligne (les lignes vides et celles qui commencent par # sont ignorées)."""
    sortie = {}
    try:
        lignes = Path(chemin).read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return sortie
    for ligne in lignes:
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            nom, valeur = ligne.split("=", 1)
            sortie[nom.strip()] = valeur.strip().strip('"').strip("'")
    return sortie
