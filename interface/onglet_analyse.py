"""Onglet « Analyse » : choisir des commentaires, lancer l'analyse, lire les notes et la synthèse.

Trois sous-onglets :
- Commentaires (analyse_commentaires) : filtres, tableau, détail, correction des notes, export, lancement ;
- Synthèse (analyse_synthese) : chiffres clés, perception, évolution, sources, exemples, sur la sélection filtrée ;
- Modèle (analyse_modele) : version en service, qualité mesurée, réentraînement, analyse après la collecte.

Les notes viennent de donnees/analyse/scores.csv, écrit par « python -m analyse ». L'interface ne note rien
elle-même ; les corrections faites à la main vont dans corrections.csv et priment sur les notes du modèle.
"""
import threading
import tkinter as tk
from tkinter import ttk

from analyse import stockage, versions
from analyse.criteres import CRITERES
from commun.fichiers import lire_csv
from commun.taches import en_cours
from commun.textes import sans_accents
from interface.analyse_commentaires import OngletCommentaires
from interface.analyse_modele import OngletModele
from interface.analyse_synthese import OngletSynthese
from interface.theme import COULEURS

TACHE = "analyse"


def charger_donnees() -> list[dict]:
    """Corpus + notes (les corrections priment), joints par clé. Quelques secondes pour 150 000 lignes : à lancer
    dans un fil à part."""
    lignes = lire_csv(stockage.CORPUS)
    notes = stockage.lire_scores()
    corrections = stockage.lire_corrections()
    for l in lignes:
        s = corrections.get(l["cle"]) or notes.get(l["cle"])
        l["_note"] = bool(s)
        l["_corrige"] = l["cle"] in corrections
        for c in CRITERES:
            l[c] = int(s[c]) if s else None
        l["cible"] = s["cible"] if s else ""
        l["fiabilite"] = ("corrigée" if l["_corrige"] else s.get("fiabilite", "")) if s else ""
        l["_cherche"] = sans_accents(l["texte"])
    return lignes


class PageAnalyse:
    def __init__(self, app, onglets: ttk.Notebook):
        self.app = app
        self.lignes: list[dict] = []
        self.infos_modele = None
        self._chargement = False
        self._etait_en_cours = False
        cadre = tk.Frame(onglets, bg=COULEURS["fond"], padx=10, pady=8)
        onglets.add(cadre, text="Analyse")
        sous = ttk.Notebook(cadre)
        sous.pack(fill="both", expand=True)
        self.commentaires = OngletCommentaires(self, sous)
        self.synthese = OngletSynthese(self, sous)
        self.modele = OngletModele(self, sous)
        self.recharger()

    def recharger(self):
        """Relit corpus et notes en arrière-plan (à l'ouverture, et à la fin de chaque analyse)."""
        if self._chargement:
            return
        self._chargement = True
        self.commentaires.etat.config(text="Chargement des commentaires…")

        def travail():
            try:
                lignes = charger_donnees()
                self.app.a_faire.put(lambda: self._donnees_pretes(lignes))
            finally:
                self._chargement = False

        threading.Thread(target=travail, daemon=True).start()

    def _donnees_pretes(self, lignes):
        self.lignes = lignes
        self.infos_modele = versions.infos()
        self.commentaires.donnees_pretes()
        self.modele.afficher()

    def selection_changee(self, selection: list[dict]):
        self.synthese.afficher(selection)

    def boucle(self):
        """Appelée toutes les 1,5 s : avancement de l'analyse en cours, rechargement quand elle se termine."""
        actif = bool(en_cours(TACHE))
        self.commentaires.montrer_avancement(actif, stockage.lire_avancement())
        if actif:
            self._etait_en_cours = True
        elif self._etait_en_cours:
            self._etait_en_cours = False
            self.recharger()
