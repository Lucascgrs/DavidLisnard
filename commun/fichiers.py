"""Lecture et écriture des fichiers de données.

Les CSV du projet sont séparés par des points-virgules et encodés en UTF-8 avec BOM, pour qu'Excel les ouvre
correctement. Toute réécriture complète passe par un fichier temporaire : un fichier à moitié écrit ne remplace
jamais le bon.
"""
import csv
import json
from pathlib import Path

csv.field_size_limit(10**8)  # certains commentaires et légendes dépassent la limite par défaut (128 ko)


def lire_json(chemin: Path, defaut=None):
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return defaut


def ecrire_json(chemin: Path, contenu, indent: int = 1) -> None:
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    tmp.write_text(json.dumps(contenu, ensure_ascii=False, indent=indent), encoding="utf-8")
    tmp.replace(chemin)


def lire_csv(chemin: Path) -> list[dict]:
    """Toutes les lignes d'un CSV du projet ; liste vide si le fichier n'existe pas."""
    chemin = Path(chemin)
    if not chemin.exists():
        return []
    with open(chemin, encoding="utf-8-sig", newline="") as h:
        return list(csv.DictReader(h, delimiter=";"))


def lire_csv_par_cle(chemin: Path, cle: str = "cle") -> dict[str, dict]:
    return {ligne[cle]: ligne for ligne in lire_csv(chemin)}


def ecrire_csv(chemin: Path, lignes, champs: list[str]) -> None:
    """Réécrit le CSV en entier ; les clés absentes de `champs` sont ignorées."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as h:
        w = csv.DictWriter(h, champs, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)
    tmp.replace(chemin)


def compter_lignes_csv(chemin: Path) -> int:
    """Nombre de lignes de données (l'en-tête n'est pas compté ; un texte sur plusieurs lignes compte pour une)."""
    with open(chemin, encoding="utf-8-sig", newline="") as h:
        return max(0, sum(1 for _ in csv.reader(h, delimiter=";")) - 1)
