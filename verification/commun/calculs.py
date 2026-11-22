"""Outils communs des calculs/calculer.py (thèmes écrits après ceux de David Lisnard, qui ont chacun leur copie).

    C = Calculs(__file__, LUS)         LUS = {clé: (fichier relatif à brut/, phrase exacte, valeur)}
    C.verifier()                        chaque phrase doit figurer dans son fichier (PDF, HTML, texte), sinon arrêt
    C.v("cle")                          la valeur recopiée
    C.res(...)                          une ligne de resultats.csv
    C.ecrire()                          écrit calculs/resultats.csv

Les chiffres lus dans un document sont recopiés une seule fois (LUS), avec la phrase qui les contient : le script
vérifie qu'elle est bien dans le fichier téléchargé avant de calculer. Colonnes de resultats.csv : affirmation,
variante, grandeur, valeur, unite, annee, chiffre_annonce (ce que dit la personne), sources, methode, note.
"""
import csv
import html
import re
from pathlib import Path

from .chemins import donnees_de

COLONNES = ["affirmation", "variante", "grandeur", "valeur", "unite", "annee", "chiffre_annonce", "sources", "methode",
            "note"]


def compact(t: str) -> str:
    """Texte sans espaces ni variantes typographiques, pour comparer une phrase recopiée au document."""
    t = html.unescape(t)
    for a, b in (("’", "'"), ("‘", "'"), ("«", '"'), ("»", '"'), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-"),
                 ("­", ""), ("ﬁ", "fi"), ("ﬂ", "fl")):
        t = t.replace(a, b)
    return re.sub(r"\s+", "", t)


def texte_de(chemin: Path) -> str:
    """Texte d'un fichier téléchargé : PDF (pypdf), HTML (balises retirées), sinon texte brut."""
    suffixe = chemin.suffix.lower()
    if suffixe == ".pdf":
        import logging
        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        return " ".join((p.extract_text() or "") for p in PdfReader(chemin).pages)
    brut = chemin.read_bytes().decode("utf-8", errors="replace")
    if suffixe in (".html", ".htm") or brut.lstrip().startswith("<"):
        brut = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", brut)
        brut = re.sub(r"<[^>]+>", " ", brut)
    return brut


class Calculs:
    def __init__(self, script: str, lus: dict | None = None):
        self.ici = donnees_de(script)                   # .../themes/<thème>/calculs/
        self.brut = self.ici.parent / "brut"
        self.sortie = self.ici / "resultats.csv"
        self.lus = lus or {}
        self.lignes: list[dict] = []
        self._textes: dict = {}

    def texte(self, fichier: str) -> str:
        if fichier not in self._textes:
            self._textes[fichier] = compact(texte_de(self.brut / fichier))
        return self._textes[fichier]

    def verifier(self) -> None:
        manquants = [f"{k} ({f})" for k, (f, phrase, _) in self.lus.items() if compact(phrase) not in self.texte(f)]
        if manquants:
            raise SystemExit("Introuvable dans le document : " + ", ".join(manquants))

    def v(self, cle: str) -> float:
        return self.lus[cle][2]

    def res(self, aff, variante, grandeur, valeur, unite, annee, sources, section, annonce="", note="",
            decimales: int = 2) -> None:
        self.lignes.append({"affirmation": aff, "variante": variante, "grandeur": grandeur,
                            "valeur": round(float(valeur), decimales), "unite": unite, "annee": annee,
                            "chiffre_annonce": annonce, "sources": sources, "methode": section, "note": note})

    def ecrire(self) -> None:
        with open(self.sortie, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLONNES)
            w.writeheader()
            w.writerows(self.lignes)
        print(f"{len(self.lignes)} résultats → {self.sortie.relative_to(self.ici.parent.parent.parent)}")

    def graphique(self, nom: str):
        """Chemin d'un graphique (calculs/graphiques/nom), dossier créé."""
        d = self.ici / "graphiques"
        d.mkdir(exist_ok=True)
        return d / nom
