"""Petits outils sur les textes et les dates."""
import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
_DEBUT_FORMULE = ("=", "+", "-", "@")


def maintenant() -> str:
    """« 2026-11-09 14:31:46 », heure de Paris."""
    return datetime.now(PARIS).strftime("%Y-%m-%d %H:%M:%S")


def date_paris(valeur) -> str:
    """ISO 8601 (« 2026-11-07T10:00:00Z »), horodatage Unix ou datetime → « 2026-11-07 11:00:00 » heure de Paris."""
    if valeur in (None, ""):
        return ""
    if isinstance(valeur, (int, float)):
        d = datetime.fromtimestamp(valeur, tz=timezone.utc)
    elif isinstance(valeur, datetime):
        d = valeur if valeur.tzinfo else valeur.replace(tzinfo=PARIS)
    else:
        d = datetime.fromisoformat(str(valeur).replace("Z", "+00:00"))
        if not d.tzinfo:
            d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(PARIS).strftime("%Y-%m-%d %H:%M:%S")


def sans_accents(texte: str) -> str:
    """En minuscules et sans accents : « Énergie » → « energie »."""
    return "".join(c for c in unicodedata.normalize("NFD", texte or "") if unicodedata.category(c) != "Mn").lower()


def contient(texte: str, mot: str) -> bool:
    return sans_accents(mot) in sans_accents(texte)


def nom_fichier(nom: str) -> str:
    """« Public Sénat » → « public_senat »."""
    return re.sub(r"[^a-z0-9]+", "_", sans_accents(nom)).strip("_") or "sans_nom"


def empreinte(*morceaux) -> str:
    """Identifiant stable quand la plateforme n'en donne pas."""
    return hashlib.sha1("\x1f".join(str(m) for m in morceaux).encode("utf-8")).hexdigest()[:16]


def pour_excel(texte):
    """Excel prendrait « =… », « -… », « +… » ou « @… » pour une formule : on les fait précéder d'une espace."""
    return " " + texte if isinstance(texte, str) and texte.startswith(_DEBUT_FORMULE) else texte


def abreger(texte: str, n: int) -> str:
    """Espaces normalisées, coupé à n caractères avec « … »."""
    t = " ".join((texte or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"
