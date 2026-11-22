"""Comptes partagés de Supabase Auth, qui ouvrent les sites par un mot de passe (site public et site de modération).

Chaque site a un seul compte, d'adresse fixe (on ne tape que le mot de passe), qui porte app_metadata.role : seule la
clé secrète peut l'écrire, et les inscriptions sont fermées. Les règles de la base (commentaires/schema.sql) lisent ce rôle.
Changer le mot de passe recrée le compte : les sessions ouvertes avec l'ancien sont aussitôt fermées (les fonctions
peut_lire() et est_moderateur() vérifient que le compte existe encore).
"""
import getpass

import requests

from commentaires import acces
from commentaires.supabase import Gestion, _verifier, entetes

LONGUEUR_MIN = 10


def _acces() -> dict:
    return acces.exiger("supabase_url", "supabase_cle_secrete", "supabase_jeton", "supabase_projet")


def fermer_inscriptions(journal=print) -> None:
    """Personne ne peut se créer un compte, même anonyme : il n'y a que les comptes partagés. La règle de lecture de
    la table commentaires (commentaires/schema.sql) compte dessus."""
    a = _acces()
    g = Gestion(a["supabase_jeton"])
    chemin = f"/projects/{a['supabase_projet']}/config/auth"
    config = g.appel("GET", chemin)
    if not config.get("disable_signup") or config.get("external_anonymous_users_enabled"):
        g.appel("PATCH", chemin, json={"disable_signup": True, "external_anonymous_users_enabled": False})
        journal("   inscriptions et connexions anonymes fermées sur Supabase Auth")


def _admin(methode: str, chemin: str, **kw):
    a = _acces()
    r = _verifier(requests.request(methode, a["supabase_url"] + "/auth/v1/admin" + chemin,
                                   headers={**entetes(a["supabase_cle_secrete"]), "Content-Type": "application/json"},
                                   timeout=60, **kw))
    return r.json() if r.content else None


def definir_mot_de_passe(email: str, role: str, mot_de_passe: str, journal=print) -> None:
    """(Re)crée le compte `email` (rôle `role`) avec ce mot de passe ; ferme toutes les sessions de l'ancien."""
    if len(mot_de_passe) < LONGUEUR_MIN:
        raise ValueError(f"mot de passe trop court ({LONGUEUR_MIN} caractères au moins)")
    fermer_inscriptions(journal)
    page = 1
    while True:
        users = (_admin("GET", "/users", params={"page": page, "per_page": 200}) or {}).get("users", [])
        for u in users:
            if (u.get("email") or "").lower() == email:
                _admin("DELETE", f"/users/{u['id']}")
                journal("   ancien compte supprimé : les sessions ouvertes sont fermées")
        if len(users) < 200:
            break
        page += 1
    _admin("POST", "/users", json={"email": email, "password": mot_de_passe, "email_confirm": True,
                                   "app_metadata": {"role": role}})
    journal("   compte créé avec le nouveau mot de passe")


def demander_mot_de_passe(qui: str) -> str:
    while True:
        m1 = getpass.getpass(f"Nouveau mot de passe {qui} ({LONGUEUR_MIN} caractères au moins) : ")
        if len(m1) < LONGUEUR_MIN:
            print("Trop court.")
            continue
        if getpass.getpass("Le retaper : ") != m1:
            print("Les deux saisies diffèrent.")
            continue
        return m1
