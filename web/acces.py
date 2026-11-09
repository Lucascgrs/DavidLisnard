"""Accès aux services du site, gardés dans config/web.json (privé, hors git).

L'utilisateur y colle deux jetons une fois pour toutes :
- vercel_jeton : vercel.com → Account Settings → Tokens ;
- supabase_jeton : supabase.com/dashboard/account/tokens.
« python -m web installer » complète le reste (projet Supabase, adresse, clés, adresse du site).
"""
from commun.config import CONFIG
from commun.fichiers import ecrire_json, lire_json

FICHIER = CONFIG / "web.json"


class AccesManquant(Exception):
    pass


def lire() -> dict:
    return lire_json(FICHIER, {}) or {}


def sauver(**valeurs) -> None:
    ecrire_json(FICHIER, {**lire(), **valeurs})


def exiger(*noms: str) -> dict:
    acces = lire()
    manquants = [n for n in noms if not acces.get(n)]
    if manquants:
        raise AccesManquant(f"{', '.join(manquants)} manquant dans {FICHIER} (voir web/acces.py)")
    return acces


def pret_a_publier() -> bool:
    """Vrai quand l'installation est faite : la publication automatique après la collecte peut avoir lieu."""
    a = lire()
    return bool(a.get("supabase_url") and a.get("supabase_cle_secrete"))
