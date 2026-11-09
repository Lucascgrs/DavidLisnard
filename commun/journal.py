"""Journal des collectes et des analyses : à l'écran et dans donnees/journal.log (que l'interface affiche en direct)."""
import time
from datetime import datetime

from commun.config import DONNEES
from commun.textes import PARIS


class Journal:
    def __init__(self):
        DONNEES.mkdir(exist_ok=True)
        self.fichier = open(DONNEES / "journal.log", "a", encoding="utf-8")
        self.debut = time.time()

    def __call__(self, message: str) -> None:
        ligne = f"{datetime.now(PARIS):%H:%M:%S} {message}"
        print(ligne, flush=True)
        self.fichier.write(ligne + "\n")
        self.fichier.flush()
