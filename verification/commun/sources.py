"""Téléchargements tracés : chaque fichier brut est enregistré tel quel dans brut/<organisme>/ et inscrit dans le
catalogue sources.csv du thème (organisme, titre, niveau, adresse, requête, dates, empreinte, licence, affirmations).

Niveaux : A statistique publique · B contrôle et évaluation · C recherche · D think tank ou partie prenante ·
E presse ou fact-checker.
"""
import csv
import hashlib
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests

COLONNES = ["id_source", "organisme", "titre", "niveau", "url", "requete_api", "date_publication",
            "date_telechargement", "fichier", "sha256", "licence", "affirmations", "note"]
ENTETES = {"User-Agent": "Mozilla/5.0 (verification-factuelle; usage non commercial)"}


@dataclass
class Source:
    id_source: str
    organisme: str
    titre: str
    niveau: str
    url: str
    fichier: str                 # chemin relatif à brut/, par ex. "eurostat/gov_10a_main.json"
    affirmations: list[str]
    date_publication: str = ""
    licence: str = ""
    requete_api: str = ""
    note: str = ""
    params: dict = field(default_factory=dict)
    entetes: dict | None = None   # None : en-têtes par défaut ; {} : ceux de requests
    outil: str = "requests"       # "curl" : passe par curl (magasin de certificats de Windows)


def sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def telecharger(src: Source, brut: Path, forcer: bool = False, essais: int = 4) -> Path:
    """Télécharge `src.url` dans brut/`src.fichier` (sans retouche). Garde le fichier s'il existe déjà."""
    cible = brut / src.fichier
    if cible.exists() and not forcer:
        return cible
    cible.parent.mkdir(parents=True, exist_ok=True)
    if src.outil == "curl":
        import subprocess
        url = src.url + ("?" + "&".join(f"{k}={v}" for k, v in src.params.items()) if src.params else "")
        r = subprocess.run(["curl", "-sSL", "-f", "-A", ENTETES["User-Agent"], "-o", str(cible), url], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"{src.id_source} : échec curl ({r.stderr.decode(errors='ignore').strip()})")
        return cible
    derniere = None
    for i in range(essais):
        try:
            r = requests.get(src.url, params=src.params or None,
                             headers=ENTETES if src.entetes is None else src.entetes, timeout=180)
            r.raise_for_status()
            cible.write_bytes(r.content)
            return cible
        except requests.RequestException as e:
            derniere = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{src.id_source} : échec du téléchargement ({derniere})")


def lire_catalogue(chemin: Path) -> dict[str, dict]:
    if not chemin.exists():
        return {}
    with open(chemin, encoding="utf-8", newline="") as f:
        return {l["id_source"]: l for l in csv.DictReader(f)}


def inscrire(src: Source, brut: Path, catalogue: Path, date_telechargement: str | None = None) -> None:
    """Ajoute ou met à jour la ligne de `src` dans sources.csv, avec l'empreinte du fichier présent."""
    lignes = lire_catalogue(catalogue)
    fichier = brut / src.fichier
    ancienne = lignes.get(src.id_source, {})
    empreinte = sha256(fichier)
    jour = date_telechargement or (ancienne.get("date_telechargement") if ancienne.get("sha256") == empreinte
                                   else None) or date.today().isoformat()
    requete = src.requete_api or (src.url + ("?" + "&".join(f"{k}={v}" for k, v in src.params.items())
                                             if src.params else ""))
    lignes[src.id_source] = {
        "id_source": src.id_source, "organisme": src.organisme, "titre": src.titre, "niveau": src.niveau,
        "url": src.url, "requete_api": requete, "date_publication": src.date_publication,
        "date_telechargement": jour, "fichier": "brut/" + src.fichier, "sha256": empreinte,
        "licence": src.licence, "affirmations": " ".join(src.affirmations), "note": src.note}
    with open(catalogue, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for k in sorted(lignes):
            w.writerow(lignes[k])


def inscrire_manuel(id_source: str, organisme: str, titre: str, niveau: str, url: str, fichier: str,
                    affirmations: list[str], brut: Path, catalogue: Path, **autres) -> None:
    """Pour un fichier déjà posé dans brut/ (téléchargé à la main ou par navigateur)."""
    inscrire(Source(id_source, organisme, titre, niveau, url, fichier, affirmations, **autres), brut, catalogue)
