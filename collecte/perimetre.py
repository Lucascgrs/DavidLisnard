"""Modifier le périmètre de collecte (config/perimetre.json) : utilisé par l'interface pour ajouter ou retirer des
chaînes YouTube, des comptes Instagram, Bluesky et X, des groupes et Pages Facebook.

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


def trouver_bluesky(saisie: str) -> dict:
    """« https://bsky.app/profile/x.bsky.social », « @x.bsky.social » ou un did → {handle, did, nom}
    (API publique de Bluesky, sans compte)."""
    s = saisie.strip()
    m = re.search(r"bsky\.app/profile/([^/?#\s]+)", s)
    s = (m.group(1) if m else s).lstrip("@").strip("/")
    if not s:
        raise ValueError("Saisir un pseudo Bluesky (x.bsky.social), un lien de profil ou un did.")
    r = requests.get("https://api.bsky.app/xrpc/app.bsky.actor.getProfile", params={"actor": s}, timeout=30)
    if r.status_code != 200:
        raise ValueError(f"Compte Bluesky « {s} » introuvable (HTTP {r.status_code}).")
    d = r.json()
    return {"handle": d["handle"], "did": d["did"], "nom": d.get("displayName") or d["handle"]}


def trouver_facebook(saisie: str) -> dict:
    """Lien (ou identifiant) d'un groupe ou d'une Page Facebook → {type, id, nom}, en lisant la page une fois avec le
    compte de collecte (sessions/facebook_cookies.json). type : « groupe » ou « page »."""
    import html
    import unicodedata
    from collecte.connexion_facebook import NAVIGATION, lire_cookies
    s = saisie.strip()
    if not s:
        raise ValueError("Coller le lien du groupe ou de la Page Facebook.")
    if not s.startswith("http"):
        s = "https://www.facebook.com/" + s.lstrip("/")
    m = re.search(r"facebook\.com/groups/([^/?#\s]+)", s)
    if m:
        url = f"https://www.facebook.com/groups/{m.group(1)}/"
    else:
        m = re.search(r"facebook\.com/(?:profile\.php\?id=(\d+)|([A-Za-z0-9.\-]+))", s)
        if not m:
            raise ValueError(f"« {saisie} » n'est pas un lien Facebook.")
        url = (f"https://www.facebook.com/profile.php?id={m.group(1)}" if m.group(1)
               else f"https://www.facebook.com/{m.group(2)}")
    cookies = lire_cookies()
    if not cookies:
        raise ValueError("Pas de session Facebook : lancer d'abord « python -m collecte.connexion_facebook ».")
    session = requests.Session()
    session.headers.update(NAVIGATION)
    for c in cookies:
        session.cookies.set(c["name"], c["value"], domain=".facebook.com")
    try:
        t = session.get(url, timeout=60).text
    except requests.RequestException as e:
        raise ValueError(f"Facebook injoignable ({type(e).__name__}).")
    if "/groups/" in url:
        gid = re.search(r'"groupID":"(\d+)"', t)
        if not gid:
            raise ValueError("Groupe introuvable (lien faux, groupe supprimé, ou privé).")
        titre = re.search(r"<title>(.*?)</title>", t, re.S)
        nom = html.unescape(titre.group(1)).strip() if titre else gid.group(1)
        nom = re.sub(r"\s*\|\s*Facebook\s*$", "", nom)
        nom = " ".join("".join(ch for ch in nom if unicodedata.category(ch)[0] != "S"  # émojis, drapeaux
                               and unicodedata.category(ch) != "Mn" or ch.isalpha()).split()) or gid.group(1)
        return {"type": "groupe", "id": gid.group(1), "nom": nom}
    pid = re.search(r'"profile_owner":\{"id":"(\d+)","name":"([^"]*)"', t)
    if not pid:
        raise ValueError("Page ou profil introuvable (lien faux, ou contenu non public).")
    nom = json.loads(f'"{pid.group(2)}"')
    return {"type": "page", "id": pid.group(1), "nom": nom}


def trouver_x(saisie: str) -> dict:
    """« https://x.com/davidlisnard », « @davidlisnard » ou « davidlisnard » → {pseudo, id, nom}, en lisant le profil
    une fois avec le compte de collecte (sessions/x_cookies.json, une requête)."""
    import asyncio
    s = saisie.strip()
    m = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})", s)
    s = (m.group(1) if m else s).lstrip("@").strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", s):
        raise ValueError(f"« {saisie} » n'est pas un pseudo X valable.")
    from collecte.sources import x as source_x

    async def lire():
        api = await source_x._api()
        return await api.user_by_login(s)

    try:
        u = asyncio.run(lire())
    except source_x.SessionMorte:
        raise ValueError("Pas de session X valable : lancer « python -m collecte.connexion_x ».")
    except Exception as e:
        raise ValueError(f"X injoignable ({type(e).__name__} : {e}).")
    if u is None:
        raise ValueError(f"Compte X « @{s} » introuvable.")
    return {"pseudo": u.username, "id": str(u.id), "nom": u.displayname or u.username}
