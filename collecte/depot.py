"""Dépôt d'une source : format des lignes, ajout sans doublon, état de la collecte, Excel et bilan.

Une ligne = un commentaire (ou un message WhatsApp). Les fichiers ne font que grandir : une ligne déjà enregistrée
n'est jamais réécrite ni supprimée.
"""
import csv
import re
from pathlib import Path

from commun.config import DONNEES, SOURCES
from commun.fichiers import compter_lignes_csv, ecrire_json, lire_json
from commun.taches import ArretDemande, arret_demande
from commun.textes import maintenant, nom_fichier, pour_excel

COLONNES = [
    "source", "compte_source",
    "publication_id", "publication_titre", "publication_lien", "publication_date",
    "commentaire_id", "type", "parent_id",
    "auteur", "auteur_id", "date", "date_exacte",
    "texte", "likes", "collecte_le",
]
PRINCIPAL, REPONSE = "principal", "réponse"
LIGNES_MAX_EXCEL = 1_048_000  # limite d'Excel ; les CSV, eux, restent complets
_CARACTERES_INTERDITS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")  # refusés par Excel


class SourceImpossible(Exception):
    """La source ne peut pas être collectée maintenant (blocage, quota, application absente…).
    Le message est écrit tel quel dans le bilan."""


class Depot:
    """Le dossier donnees/<source>/ : un CSV par compte suivi, l'état de la collecte (etat.json), l'Excel
    récapitulatif."""

    def __init__(self, source: str):
        self.source = source
        self.dossier = DONNEES / source
        self.dossier.mkdir(parents=True, exist_ok=True)
        self.fichier_etat = self.dossier / "etat.json"
        self.etat = lire_json(self.fichier_etat, {})
        self._ids: dict[str, set] = {}          # fichier → identifiants déjà enregistrés
        self._reponses: dict[str, dict] = {}    # fichier → {parent_id: nombre de réponses connues}
        self.nouveaux = 0
        self.par_compte: dict[str, int] = {}

    def verifier_arret(self) -> None:
        """À appeler entre deux éléments (vidéo, post, écran de messages)."""
        if arret_demande(self.source):
            raise ArretDemande()

    def csv_de(self, compte_source: str) -> Path:
        return self.dossier / f"{nom_fichier(compte_source)}.csv"

    def _charger(self, chemin: Path) -> None:
        if str(chemin) in self._ids:
            return
        ids, rep = set(), {}
        if chemin.exists():
            with open(chemin, encoding="utf-8-sig", newline="") as f:
                for ligne in csv.DictReader(f, delimiter=";"):
                    ids.add(ligne["commentaire_id"])
                    if ligne.get("parent_id"):
                        rep[ligne["parent_id"]] = rep.get(ligne["parent_id"], 0) + 1
        self._ids[str(chemin)], self._reponses[str(chemin)] = ids, rep

    def connus(self, compte_source: str) -> set:
        chemin = self.csv_de(compte_source)
        self._charger(chemin)
        return self._ids[str(chemin)]

    def reponses_connues(self, compte_source: str, parent_id: str) -> int:
        chemin = self.csv_de(compte_source)
        self._charger(chemin)
        return self._reponses[str(chemin)].get(parent_id, 0)

    def ajouter(self, compte_source: str, lignes: list[dict]) -> int:
        """Ajoute en fin de fichier les lignes dont l'identifiant est nouveau. Renvoie leur nombre."""
        chemin = self.csv_de(compte_source)
        self._charger(chemin)
        ids, rep = self._ids[str(chemin)], self._reponses[str(chemin)]
        a_ecrire = []
        collecte = maintenant()
        for l in lignes:
            cid = str(l["commentaire_id"])
            if cid in ids:
                continue
            ids.add(cid)
            if l.get("parent_id"):
                rep[l["parent_id"]] = rep.get(l["parent_id"], 0) + 1
            ligne = {c: l.get(c, "") for c in COLONNES}
            ligne.update(source=self.source, compte_source=compte_source, commentaire_id=cid, collecte_le=collecte)
            for c in ("texte", "publication_titre"):
                ligne[c] = pour_excel(ligne[c])
            a_ecrire.append(ligne)
        if a_ecrire:
            nouveau = not chemin.exists()
            with open(chemin, "a", encoding="utf-8-sig" if nouveau else "utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLONNES, delimiter=";")
                if nouveau:
                    w.writeheader()
                w.writerows(a_ecrire)
        self.nouveaux += len(a_ecrire)
        self.par_compte[compte_source] = self.par_compte.get(compte_source, 0) + len(a_ecrire)
        return len(a_ecrire)

    def sauver_etat(self) -> None:
        ecrire_json(self.fichier_etat, self.etat)

    def total(self) -> int:
        return sum(compter_lignes_csv(c) for c in self.dossier.glob("*.csv"))

    def excel(self) -> Path | None:
        """<source>_tout.xlsx : tous les CSV de la source, une feuille. Recréé à chaque lancement."""
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter

        fichiers = sorted(self.dossier.glob("*.csv"))
        if not fichiers:
            return None
        classeur = Workbook(write_only=True)
        feuille = classeur.create_sheet(self.source)
        largeurs = {"texte": 90, "publication_titre": 45, "compte_source": 25, "auteur": 22,
                    "publication_lien": 30, "date": 19, "publication_date": 19, "collecte_le": 19}
        for i, c in enumerate(COLONNES, 1):
            feuille.column_dimensions[get_column_letter(i)].width = largeurs.get(c, 14)
        feuille.freeze_panes = "A2"
        feuille.append(COLONNES)
        n = 0
        for chemin in fichiers:
            with open(chemin, encoding="utf-8-sig", newline="") as f:
                for ligne in csv.DictReader(f, delimiter=";"):
                    if n >= LIGNES_MAX_EXCEL:
                        break
                    valeurs = []
                    for c in COLONNES:
                        v = _CARACTERES_INTERDITS.sub("", ligne.get(c, "") or "")[:32_000]
                        if c == "likes" and v.isdigit():
                            v = int(v)
                        elif v.startswith("="):  # openpyxl en ferait une formule
                            v = " " + v
                        valeurs.append(v)
                    feuille.append(valeurs)
                    n += 1
        sortie = self.dossier / f"{self.source}_tout.xlsx"
        tmp = sortie.with_name(sortie.stem + "_tmp.xlsx")
        classeur.save(tmp)
        try:
            tmp.replace(sortie)
        except PermissionError:  # le fichier est ouvert dans Excel
            sortie = tmp
        return sortie


def compter_par_source() -> dict:
    """{source: {"total": n, "par_fichier": {nom du CSV: n}}} pour l'interface (lecture complète des CSV)."""
    sortie = {}
    for source in SOURCES:
        par_fichier = {}
        for chemin in sorted((DONNEES / source).glob("*.csv")):
            try:
                par_fichier[chemin.stem] = compter_lignes_csv(chemin)
            except OSError:
                pass
        sortie[source] = {"total": sum(par_fichier.values()), "par_fichier": par_fichier}
    return sortie


def ecrire_bilan(resultats: list[dict]) -> Path:
    """donnees/bilan.md : le dernier lancement, source par source, ajouté aussi à donnees/historique.md."""
    lignes = [f"# Collecte du {maintenant()}", "",
              "| Source | Résultat | Nouveaux commentaires | Total enregistré | Durée |",
              "|---|---|---|---|---|"]
    for r in resultats:
        lignes.append(f"| {r['source']} | {r['statut']} | {r.get('nouveaux', 0)} | {r.get('total', '')} "
                      f"| {r.get('duree', '')} |")
    for r in resultats:
        lignes += ["", f"## {r['source']}", "", f"Résultat : {r['statut']}"]
        if r.get("message"):
            lignes += ["", r["message"]]
        if r.get("par_compte"):
            lignes += ["", "| Compte | Nouveaux |", "|---|---|"]
            lignes += [f"| {k} | {v} |" for k, v in sorted(r["par_compte"].items(), key=lambda x: -x[1]) if v]
        if r.get("details"):
            lignes += [""] + [f"- {d}" for d in r["details"]]
    texte = "\n".join(lignes) + "\n"
    DONNEES.mkdir(exist_ok=True)
    (DONNEES / "bilan.md").write_text(texte, encoding="utf-8")
    with open(DONNEES / "historique.md", "a", encoding="utf-8") as f:
        f.write(texte + "\n")
    return DONNEES / "bilan.md"
