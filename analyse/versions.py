"""Les modèles enregistrés dans modeles/ :
- vN/ : une version complète, mise en service dès qu'elle existe (modele.joblib + infos.json, mesures comprises) ;
- affineN/ : un réseau affiné (reseau.pt), qui sert à construire une version (analyse/ensemble.py).

La version en service est la plus récente. Ce module ne charge aucun modèle : l'interface s'en sert pour afficher
les infos sans attendre.
"""
import re

from commun.config import MODELES
from commun.fichiers import lire_json


def _numeros(prefixe: str) -> list[int]:
    motif = re.compile(rf"{prefixe}(\d+)")
    return sorted(int(m[1]) for d in MODELES.glob(f"{prefixe}*") if (m := motif.fullmatch(d.name)))


def versions() -> list[str]:
    """Versions utilisables, de la plus ancienne à la plus récente."""
    return [f"v{n}" for n in _numeros("v") if (MODELES / f"v{n}" / "modele.joblib").exists()]


def derniere_version() -> str | None:
    vs = versions()
    return vs[-1] if vs else None


def infos(version: str | None = None) -> dict | None:
    """infos.json d'une version (par défaut celle en service), sans charger le modèle."""
    version = version or derniere_version()
    return lire_json(MODELES / version / "infos.json") if version else None


def prochaine_version() -> str:
    return f"v{max(_numeros('v'), default=0) + 1}"


def prochain_reseau() -> str:
    return f"affine{max(_numeros('affine'), default=0) + 1}"
