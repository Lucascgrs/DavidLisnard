"""Supabase : l'API de gestion (jeton personnel) pour créer la base, l'API REST (clé secrète) pour y écrire."""
import json
import time

import requests

GESTION = "https://api.supabase.com/v1"


class ErreurSupabase(Exception):
    pass


def _verifier(r: requests.Response) -> requests.Response:
    if r.status_code >= 400:
        raise ErreurSupabase(f"{r.request.method} {r.url.split('?')[0]} → {r.status_code} : {r.text[:500]}")
    return r


class Gestion:
    """API de gestion de supabase.com, avec le jeton personnel du compte."""

    def __init__(self, jeton: str):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {jeton}", "User-Agent": "analyse-commentaires/1.0"})

    def appel(self, methode: str, chemin: str, **kw):
        r = _verifier(self.s.request(methode, GESTION + chemin, timeout=120, **kw))
        return r.json() if r.content else None

    def trouver_projet(self) -> dict:
        """Le projet du site : celui dont le nom contient « lisnard », sinon le seul du compte."""
        projets = self.appel("GET", "/projects")
        nommes = [p for p in projets if "lisnard" in p["name"].lower().replace(" ", "")]
        choix = nommes or (projets if len(projets) == 1 else [])
        if len(choix) != 1:
            raise ErreurSupabase(f"projet introuvable parmi : {', '.join(p['name'] for p in projets) or 'aucun'}")
        return choix[0]

    def sql(self, ref: str, requete: str):
        return self.appel("POST", f"/projects/{ref}/database/query", json={"query": requete})

    def cles(self, ref: str) -> tuple[str, str]:
        """(clé publique, clé secrète). Les nouvelles clés (sb_publishable_, sb_secret_) sont préférées aux
        anciennes (anon, service_role) ; une clé secrète est créée s'il n'y en a pas."""
        cles = self.appel("GET", f"/projects/{ref}/api-keys", params={"reveal": "true"})
        par_type = {}
        for c in cles:
            par_type.setdefault(c.get("type") or "", []).append(c)
        if "secret" not in par_type and "publishable" in par_type:
            c = self.appel("POST", f"/projects/{ref}/api-keys", params={"reveal": "true"},
                           json={"type": "secret", "name": "publication_site"})
            par_type["secret"] = [c]
        anciennes = {c["name"]: c["api_key"] for c in par_type.get("legacy", [])}
        publique = (par_type.get("publishable") or [{}])[0].get("api_key") or anciennes.get("anon")
        secrete = (par_type.get("secret") or [{}])[0].get("api_key") or anciennes.get("service_role")
        if not (publique and secrete):
            raise ErreurSupabase("clés de l'API introuvables")
        return publique, secrete

    def attendre_actif(self, ref: str, minutes: int = 10) -> None:
        """Un projet gratuit inactif est mis en pause par Supabase : on le relance et on attend qu'il réponde."""
        fin = time.time() + 60 * minutes
        projet = self.appel("GET", f"/projects/{ref}")
        if projet.get("status") in ("INACTIVE", "PAUSED"):
            self.appel("POST", f"/projects/{ref}/restore")
        while self.appel("GET", f"/projects/{ref}").get("status") != "ACTIVE_HEALTHY":
            if time.time() > fin:
                raise ErreurSupabase("le projet Supabase ne redémarre pas")
            time.sleep(10)


def entetes(cle: str) -> dict:
    """Les nouvelles clés passent seules ; les anciennes (des JWT) aussi en Authorization."""
    h = {"apikey": cle}
    if not cle.startswith(("sb_publishable_", "sb_secret_")):
        h["Authorization"] = f"Bearer {cle}"
    return h


class Base:
    """Écriture dans les tables par l'API REST, avec la clé secrète (seule à pouvoir écrire)."""

    def __init__(self, url: str, cle_secrete: str):
        self.url = url.rstrip("/") + "/rest/v1"
        self.s = requests.Session()
        self.s.headers.update({**entetes(cle_secrete), "Content-Type": "application/json"})

    def _envoi(self, methode: str, table: str, **kw) -> None:
        for essai in range(4):
            try:
                _verifier(self.s.request(methode, f"{self.url}/{table}", timeout=180, **kw))
                return
            except (requests.ConnectionError, requests.Timeout):
                if essai == 3:
                    raise
                time.sleep(5 * (essai + 1))

    def ecrire(self, table: str, lignes: list[dict], conflit: str, paquet: int = 1000, avancement=None) -> None:
        """Ajoute ou remplace les lignes (même clé `conflit` = remplacement)."""
        for i in range(0, len(lignes), paquet):
            morceau = lignes[i:i + paquet]
            self._envoi("POST", table, params={"on_conflict": conflit},
                        headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                        data=json.dumps(morceau, ensure_ascii=False).encode("utf-8"))
            if avancement:
                avancement(min(i + paquet, len(lignes)), len(lignes))

    def supprimer(self, table: str, colonne: str, valeurs: list[str], paquet: int = 100) -> None:
        for i in range(0, len(valeurs), paquet):
            liste = ",".join('"' + v.replace('"', '\\"') + '"' for v in valeurs[i:i + paquet])
            self._envoi("DELETE", table, params={colonne: f"in.({liste})"})
