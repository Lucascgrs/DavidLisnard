"""Mise en ligne des pages de web/site/ sur Vercel, par son API (pas besoin de Node ni de la commande vercel)."""
import time
from pathlib import Path

import requests

API = "https://api.vercel.com"
PROJET = "analyse-commentaires-lisnard"


class ErreurVercel(Exception):
    pass


class Vercel:
    def __init__(self, jeton: str):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {jeton}"})
        self.params = {}
        equipe = self.appel("GET", "/v2/user").get("user", {}).get("defaultTeamId")
        if equipe:  # comptes récents : tout appartient à l'équipe personnelle
            self.params = {"teamId": equipe}

    def appel(self, methode: str, chemin: str, params=None, **kw):
        r = self.s.request(methode, API + chemin, params={**self.params, **(params or {})}, timeout=120, **kw)
        if r.status_code >= 400:
            raise ErreurVercel(f"{methode} {chemin} → {r.status_code} : {r.text[:500]}")
        return r.json() if r.content else None

    def deployer(self, dossier: Path, journal=print, projet: str = PROJET) -> str:
        """Envoie tous les fichiers du dossier en production et attend que le site réponde. Rend son adresse.
        projet : nom du projet Vercel (créé au premier envoi) ; le site de modération a le sien."""
        fichiers = [{"file": p.relative_to(dossier).as_posix(), "data": p.read_text(encoding="utf-8")}
                    for p in sorted(dossier.rglob("*")) if p.is_file()]
        d = self.appel("POST", "/v13/deployments", params={"skipAutoDetectionConfirmation": "1"}, json={
            "name": projet, "files": fichiers, "target": "production",
            "projectSettings": {"framework": None, "buildCommand": None, "installCommand": None,
                                "outputDirectory": None}})
        journal(f"   {len(fichiers)} fichiers envoyés, construction…")
        fin = time.time() + 300
        while d.get("readyState") not in ("READY", "ERROR", "CANCELED"):
            if time.time() > fin:
                raise ErreurVercel("la mise en ligne ne se termine pas")
            time.sleep(3)
            d = self.appel("GET", f"/v13/deployments/{d['id']}")
        if d["readyState"] != "READY":
            raise ErreurVercel(f"mise en ligne en échec : {d.get('errorMessage') or d['readyState']}")
        # Pas d'écran de connexion Vercel devant les pages : le site public est ouvert à tous, celui de modération
        # a sa propre connexion (Supabase Auth).
        self.appel("PATCH", f"/v9/projects/{projet}", json={"ssoProtection": None, "passwordProtection": None})
        infos = self.appel("GET", f"/v9/projects/{projet}")
        domaines = [a["domain"] for a in infos.get("alias", []) if a.get("domain", "").endswith(".vercel.app")]
        domaines += [x for x in d.get("alias", []) if x.endswith(".vercel.app")]
        return "https://" + (min(domaines, key=len) if domaines else d["url"])
