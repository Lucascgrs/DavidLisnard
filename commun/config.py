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

# Sources collectées, dans l'ordre de passage : YouTube et Bluesky (API, sans fenêtre), WhatsApp (plein écran), puis
# Instagram (navigateur, le plus lent). Reddit et TikTok ne sont pas collectés : voir README.md.
SOURCES = {"youtube": "YouTube", "bluesky": "Bluesky", "whatsapp": "WhatsApp", "instagram": "Instagram"}


def perimetre() -> dict:
    return lire_json(FICHIER_PERIMETRE, {})


def cles() -> dict:
    return lire_json(FICHIER_CLES, {})
