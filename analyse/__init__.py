"""Analyse des commentaires : 5 notes de 0 à 20 et une cible pour chacun, selon docs/GRILLE.md.

Chaîne de traitement :
- corpus : copie de travail des commentaires collectés (auteurs pseudonymisés) ;
- vecteurs : vecteurs de sens des textes (e5 multilingue) ;
- annotation : les commentaires notés à la main par Claude, qui servent d'exemples et de mesure ;
- modele : le modèle à vecteurs et ce que partagent tous les modèles ;
- affinage : le réseau e5 affiné, qui lit chaque commentaire avec son parent et son titre ;
- ensemble : la combinaison des deux, mise en service (modeles/vN/) ;
- mesures : qualité sur le jeu de test et rapport ;
- notation : notes de tout le corpus par le modèle en service (« python -m analyse ») ;
- criteres, stockage, versions : définitions, fichiers de donnees/analyse/, versions enregistrées ;
- recalage_pertinence : correction ponctuelle de la dérive d'annotation du 2026-11-09.

Modèle de langue et mode hors ligne. Le modèle de départ (MODELE_LANGUE) est téléchargé une fois depuis Hugging Face,
puis gardé sur le disque. Tant que cette copie existe, on met HF_HUB_OFFLINE=1 : la bibliothèque la lit directement,
sans demander en ligne à chaque chargement si le modèle a changé (plus rapide, marche sans connexion, plus de message
« You are sending unauthenticated requests to the HF Hub »). Le réglage se lève de lui-même quand il le faut :
- un modèle de départ jamais téléchargé (on change MODELE_LANGUE) n'a pas de copie : le mode hors ligne n'est pas mis,
  et le téléchargement se fait normalement ;
- pour forcer une vérification en ligne : lancer la commande avec la variable HF_HUB_OFFLINE=0
  (PowerShell : « $env:HF_HUB_OFFLINE = "0"; python -m analyse »). Une valeur déjà posée n'est jamais remplacée.
Ce réglage doit être posé avant le premier import de transformers ou de sentence_transformers : c'est pourquoi il
est ici, dans le paquet que tous les modules de l'analyse traversent d'abord.
"""
import os
from pathlib import Path

MODELE_LANGUE = "intfloat/multilingual-e5-base"


def copie_locale(modele: str = MODELE_LANGUE) -> bool:
    """Vrai si ce modèle est déjà dans le cache de Hugging Face de cette machine."""
    cache = os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if not cache:
        cache = Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub"
    return any((Path(cache) / ("models--" + modele.replace("/", "--")) / "snapshots").glob("*/config.json"))


if "HF_HUB_OFFLINE" not in os.environ and copie_locale():
    os.environ["HF_HUB_OFFLINE"] = "1"


def hors_ligne() -> bool:
    """Vrai si les modèles se lisent sur le disque sans rien demander en ligne."""
    return os.environ.get("HF_HUB_OFFLINE", "").strip().upper() in ("1", "ON", "YES", "TRUE")
