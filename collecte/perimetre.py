"""Modifier le périmètre de collecte (config/perimetre.json) : utilisé par l'interface pour ajouter ou retirer des
chaînes YouTube et des comptes Instagram.

Un compte retiré n'est plus lu, mais ses commentaires déjà collectés restent dans les fichiers.
"""
import json
import re
from datetime import datetime

import requests

from commun.config import FICHIER_PERIMETRE, cles

API_YOUTUBE = "https://www.googleapis.com/youtube/v3/"
REGLES = {"toutes": "toutes les vidéos", "mention": "vidéos qui citent le mot-clé"}
GROUPES = ["officiel", "soutien", "media", "commentateur", "autre"]


def sauver(p: dict) -> None:
    """Réécrit perimetre.json lisiblement (une chaîne YouTube par ligne), avec une copie de l'ancien en .bak."""
    jetons = {}

    def compact(objet):
        cle = f"@@{len(jetons)}@@"
        jetons[cle] = json.dumps(objet, ensure_ascii=False)
        return cle

    copie = json.loads(json.dumps(p))
    copie.setdefault("youtube", {})["chaines"] = [compact(c) for c in copie["youtube"].get("chaines", [])]
    if "instagram" in copie:
        copie["instagram"]["comptes"] = compact(copie["instagram"].get("comptes", []))
    texte = json.dumps(copie, ensure_ascii=False, indent=2)
    for cle, valeur in jetons.items():
        texte = texte.replace(f'"{cle}"', valeur)
    json.loads(texte)  # garde-fou : jamais de fichier invalide
    if FICHIER_PERIMETRE.exists():
        FICHIER_PERIMETRE.with_suffix(".json.bak").write_bytes(FICHIER_PERIMETRE.read_bytes())
    tmp = FICHIER_PERIMETRE.with_suffix(".json.tmp")
    tmp.write_text(texte + "\n", encoding="utf-8", newline="\n")
    tmp.replace(FICHIER_PERIMETRE)


def trouver_chaine(saisie: str) -> tuple[str, str]:
    """Lien, @pseudo ou identifiant d'une chaîne YouTube → (identifiant UC…, nom).
    Coûte 1 unité de quota (100 s'il faut passer par la recherche)."""
    cle = cles().get("youtube", "").strip()
    if not cle:
        raise ValueError("Pas de clé YouTube dans config/cles.json.")
    s = saisie.strip()
    essais = []
    m = re.search(r"(UC[0-9A-Za-z_-]{22})", s)
    if m:
        essais.append({"id": m.group(1)})
    m = re.search(r"youtube\.com/(?:c/|user/)?(@?[^/?#\s]+)", s)
    nom = m.group(1) if m else s
    if nom.startswith("@"):
        essais.append({"forHandle": nom})
    elif not essais:
        essais += [{"forHandle": "@" + nom}, {"forUsername": nom}]
    for params in essais:
        r = requests.get(API_YOUTUBE + "channels", params={"part": "snippet", "key": cle, **params}, timeout=20)
        r.raise_for_status()
        items = r.json().get("items") or []
        if items:
            return items[0]["id"], items[0]["snippet"]["title"]
    r = requests.get(API_YOUTUBE + "search", timeout=20,
                     params={"part": "snippet", "type": "channel", "q": nom.lstrip("@"), "maxResults": 1, "key": cle})
    r.raise_for_status()
    items = r.json().get("items") or []
    if items:
        return items[0]["id"]["channelId"], items[0]["snippet"]["title"]
    raise ValueError(f"Aucune chaîne trouvée pour « {saisie} ».")


def pseudo_instagram(saisie: str) -> str:
    """« https://www.instagram.com/davidlisnard/ » ou « @DavidLisnard » → « davidlisnard »."""
    s = saisie.strip()
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", s)
    s = (m.group(1) if m else s).lstrip("@").strip("/").lower()
    if not re.fullmatch(r"[a-z0-9._]{1,30}", s):
        raise ValueError(f"« {saisie} » n'est pas un pseudo Instagram valable.")
    return s


def debut_instagram(conf: dict) -> float:
    """Horodatage du début de la période Instagram (« depuis »), 0 si la date est illisible."""
    try:
        return datetime.fromisoformat(conf.get("depuis", "2025-01-01")).timestamp()
    except ValueError:
        return 0


def avancement_instagram(conf: dict, etat: dict, pseudo: str) -> dict:
    """Pour un compte suivi : posts listés dans la période, posts lus, liste complète ou non."""
    depuis = debut_instagram(conf)
    liste = etat.get("liste", {}).get(pseudo, {})
    dans = [c for c, v in liste.items() if v.get("date", 0) >= depuis]
    lus = etat.get("posts", {})
    return {"liste": bool(liste), "posts": len(dans), "lus": sum(1 for c in dans if c in lus),
            "jamais_lus": sum(1 for c in dans if c not in lus),
            "complete": bool(etat.get("liste_complete", {}).get(pseudo))}
