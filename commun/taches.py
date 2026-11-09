"""Coordination des tâches longues (collecte d'une source, analyse) entre le terminal, l'interface et la
planification.

Chaque tâche a un nom (« youtube », « analyse »…) et un dossier donnees/<nom>/ où elle dépose :
- EN_COURS : le verrou, avec le numéro du processus. Une même tâche n'est jamais lancée deux fois en même temps ;
- ARRET : la demande d'arrêt propre. La tâche la voit entre deux éléments, garde ce qui est fait et s'arrête.
"""
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

from commun.config import DONNEES, RACINE
from commun.fichiers import ecrire_json, lire_json
from commun.textes import maintenant

PYTHON = str(Path(sys.executable).with_name("python.exe"))  # python.exe, même si l'interface tourne sous pythonw
SANS_FENETRE = 0x08000000  # CREATE_NO_WINDOW
ERREURS = DONNEES / "erreurs_interface.log"


class ArretDemande(Exception):
    """Un arrêt a été demandé (fichier ARRET) : on s'arrête proprement entre deux éléments ; ce qui est déjà
    enregistré est gardé et la suite reprendra au prochain lancement."""


class DejaEnCours(Exception):
    def __init__(self, nom: str, pid: int | None):
        super().__init__(f"{nom} : déjà en cours (processus {pid})")
        self.pid = pid


def fichier_arret(nom: str) -> Path:
    return DONNEES / nom / "ARRET"


def fichier_verrou(nom: str) -> Path:
    return DONNEES / nom / "EN_COURS"


def en_cours(nom: str) -> int | None:
    """Numéro du processus qui exécute cette tâche en ce moment, ou None."""
    import psutil
    infos = lire_json(fichier_verrou(nom))
    if not infos:
        return None
    try:
        p = psutil.Process(infos["pid"])
        # Le numéro seul ne suffit pas : Windows le redonne à un autre processus après la fin du premier.
        if p.is_running() and abs(p.create_time() - infos.get("cree", 0)) < 2:
            return infos["pid"]
    except (psutil.Error, KeyError, TypeError):
        pass
    return None


def depuis(nom: str) -> str:
    """Heure de début de la tâche en cours (« 2026-11-09 13:01:19 »), ou ""."""
    return (lire_json(fichier_verrou(nom)) or {}).get("depuis", "")


def arret_demande(nom: str) -> bool:
    return fichier_arret(nom).exists()


def demander_arret(nom: str, motif: str = "arrêt demandé depuis l'interface") -> None:
    fichier_arret(nom).parent.mkdir(parents=True, exist_ok=True)
    fichier_arret(nom).write_text(motif, encoding="utf-8")


def verifier_arret(nom: str) -> None:
    if arret_demande(nom):
        raise ArretDemande()


def pas_de_veille(actif: bool) -> None:
    """Empêche Windows de mettre le PC en veille pendant une tâche (l'écran peut s'éteindre). Une veille au
    milieu d'une lecture Instagram l'a bloquée 17 heures le 2026-11-08."""
    if sys.platform == "win32":
        import ctypes
        es_continuous, es_system_required = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | (es_system_required if actif else 0))


@contextmanager
def verrou(nom: str, sans_veille: bool = False):
    """Exécute le bloc en tant que tâche `nom`. Lève DejaEnCours si elle tourne déjà ailleurs."""
    import psutil
    if en_cours(nom):
        raise DejaEnCours(nom, en_cours(nom))
    moi = psutil.Process(os.getpid())
    ecrire_json(fichier_verrou(nom), {"pid": moi.pid, "cree": moi.create_time(), "depuis": maintenant()})
    fichier_arret(nom).unlink(missing_ok=True)
    if sans_veille:
        pas_de_veille(True)
    try:
        yield
    finally:
        if sans_veille:
            pas_de_veille(False)
        if (lire_json(fichier_verrou(nom)) or {}).get("pid") == os.getpid():
            fichier_verrou(nom).unlink(missing_ok=True)
        fichier_arret(nom).unlink(missing_ok=True)


def lancer_en_fond(arguments: list[str], sortie: Path | None = None, env: dict | None = None) -> None:
    """Lance « python <arguments> » depuis la racine du projet, sans fenêtre, détaché de l'interface : la tâche
    continue si l'on ferme la fenêtre. Les erreurs vont dans donnees/erreurs_interface.log."""
    DONNEES.mkdir(exist_ok=True)
    erreurs = open(ERREURS, "a", encoding="utf-8")
    vers = open(sortie, "a", encoding="utf-8") if sortie else subprocess.DEVNULL
    subprocess.Popen([PYTHON, *arguments], cwd=RACINE, stdin=subprocess.DEVNULL, stdout=vers, stderr=erreurs,
                     creationflags=SANS_FENETRE,
                     env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", **(env or {})))


def arreter_de_force(nom: str) -> None:
    """Tue le processus de la tâche et ses enfants (navigateur…), puis retire le verrou."""
    import psutil
    pid = en_cours(nom)
    if pid:
        try:
            p = psutil.Process(pid)
            for enfant in p.children(recursive=True):
                try:
                    enfant.kill()
                except psutil.Error:
                    pass
            p.kill()
        except psutil.Error:
            pass
    fichier_verrou(nom).unlink(missing_ok=True)
    fichier_arret(nom).unlink(missing_ok=True)
