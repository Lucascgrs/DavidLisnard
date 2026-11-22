"""Collecte automatique par le Planificateur de tâches de Windows (tâche « DavidLisnard - collecte des
commentaires »), qui lance Collecter.bat avec les sources choisies. Les réglages choisis dans l'interface sont gardés
dans config/planification.json.
"""
import re
import subprocess

from commun.config import FICHIER_PLANIFICATION, RACINE
from commun.fichiers import ecrire_json, lire_json
from commun.taches import SANS_FENETRE

TACHE = "DavidLisnard - collecte des commentaires"


def reglages() -> dict:
    return lire_json(FICHIER_PLANIFICATION, {}) or {}


def prochaine_execution() -> str | None:
    """Date de la prochaine exécution si la tâche existe (« active » si Windows ne la donne pas), sinon None."""
    r = subprocess.run(["schtasks", "/Query", "/TN", TACHE, "/FO", "LIST", "/V"], capture_output=True,
                       encoding="oem", errors="replace", creationflags=SANS_FENETRE)
    if r.returncode != 0:
        return None
    for ligne in r.stdout.splitlines():
        if re.match(r"\s*(Prochaine exécution|Next Run Time)", ligne, re.I):
            return ligne.split(":", 1)[1].strip()
    return "active"


def activer(sources: list[str], heure: str, toutes_les_h: int) -> None:
    """Chaque jour à `heure` (HH:MM), puis toutes les `toutes_les_h` heures si ce n'est pas 0."""
    commande = f'"{RACINE / "Collecter.bat"}" ' + " ".join(sources)
    cmd = ["schtasks", "/Create", "/F", "/TN", TACHE, "/TR", commande, "/SC", "DAILY", "/ST", heure]
    if toutes_les_h:
        cmd += ["/RI", str(toutes_les_h * 60), "/DU", "23:59"]
    r = subprocess.run(cmd, capture_output=True, encoding="oem", errors="replace", creationflags=SANS_FENETRE)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    ecrire_json(FICHIER_PLANIFICATION, {"sources": sources, "heure": heure, "toutes_les_h": toutes_les_h})


def desactiver() -> None:
    subprocess.run(["schtasks", "/Delete", "/TN", TACHE, "/F"], capture_output=True, creationflags=SANS_FENETRE)
