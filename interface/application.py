"""La fenêtre principale : en-tête, onglets, barre de messages et boucles de rafraîchissement.

Deux boucles tournent pendant que la fenêtre est ouverte :
- toutes les 1,5 s : journal en direct, état des collectes et de l'analyse en cours ;
- toutes les 20 s : comptage des commentaires collectés (dans un fil à part : quelques dixièmes de seconde).
Les fils d'arrière-plan ne touchent jamais aux composants : ils déposent leurs résultats dans `a_faire`, que la
boucle principale applique.
"""
import queue
import threading
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import messagebox, ttk

from collecte.depot import compter_par_source
from commun.config import DONNEES
from commun.taches import ERREURS
from interface.onglet_analyse import PageAnalyse
from interface.onglet_moderation import PageModeration
from interface.onglet_themes import PageThemes
from interface.onglets_collecte import (PageBluesky, PageFacebook, PageInstagram, PagePlanification, PageTableau, PageX,
                                        PageYoutube, tout_lancer)
from interface.theme import COULEURS, appliquer_theme, ouvrir, police

JOURNAL = DONNEES / "journal.log"


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Collecte des commentaires — David Lisnard")
        self.configure(bg=COULEURS["fond"])
        self.geometry("1280x860")
        self.minsize(860, 600)
        appliquer_theme(self)
        self.comptes = None  # résultat de compter_par_source(), rafraîchi toutes les 20 s
        self.a_faire = queue.Queue()
        self._position_journal = None
        self._comptage_en_cours = False

        entete = tk.Frame(self, bg=COULEURS["fond"], padx=20, pady=14)
        entete.pack(fill="x")
        titres = tk.Frame(entete, bg=COULEURS["fond"])
        titres.pack(side="left")
        tk.Label(titres, text="Commentaires sur David Lisnard", font=police(20, True, True), bg=COULEURS["fond"],
                 fg=COULEURS["texte"]).pack(anchor="w")
        tk.Label(titres, text="Collecte automatique (YouTube, Bluesky, Instagram, Facebook, X), analyse des avis et thèmes",
                 font=police(10), bg=COULEURS["fond"], fg=COULEURS["doux"]).pack(anchor="w")
        ttk.Button(entete, text="Dernier bilan", command=lambda: ouvrir(DONNEES / "bilan.md")).pack(side="right")
        ttk.Button(entete, text="Dossier des données", command=lambda: ouvrir(DONNEES)).pack(side="right", padx=6)
        ttk.Button(entete, text="Sauvegarder", command=self.sauvegarder).pack(side="right")
        ttk.Button(entete, text="Export Hugging Face", command=self.exporter_hf).pack(side="right", padx=6)
        ttk.Button(entete, text="Tout lancer", style="Accent.TButton",
                   command=lambda: tout_lancer(self)).pack(side="right", padx=6)

        self.barre = tk.Label(self, text="", bg=COULEURS["fond"], fg=COULEURS["en_cours"], anchor="w", padx=20)
        self.barre.pack(side="bottom", fill="x", pady=(0, 6))
        self.onglets = ttk.Notebook(self)
        self.onglets.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.tableau = PageTableau(self, self.onglets)
        self.pages_comptes = [PageYoutube(self, self.onglets), PageBluesky(self, self.onglets),
                             PageInstagram(self, self.onglets), PageFacebook(self, self.onglets),
                             PageX(self, self.onglets)]
        PagePlanification(self, self.onglets)
        self.analyse = PageAnalyse(self, self.onglets)
        self.themes = PageThemes(self, self.onglets)
        self.moderation = PageModeration(self, self.onglets)  # à part de l'analyse : groupes Facebook (moderation/)

        self._boucle_rapide()
        self._boucle_comptage()

    def report_callback_exception(self, exc, val, tb):
        """Sans console (pythonw), une erreur passerait inaperçue : on la note et on l'affiche."""
        try:
            with open(ERREURS, "a", encoding="utf-8") as f:
                f.write(f"--- {datetime.now():%Y-%m-%d %H:%M:%S}\n{''.join(traceback.format_exception(exc, val, tb))}")
        except OSError:
            pass
        messagebox.showerror("Erreur", f"{exc.__name__} : {val}\n\nDétail dans donnees/erreurs_interface.log")

    def sauvegarder(self):
        """Sauvegarde unique des données qu'on ne peut pas refaire (aussi faite à la fin de chaque collecte)."""
        from commun import sauvegarde
        from commun.taches import lancer_en_fond
        lancer_en_fond(["-m", "commun.sauvegarde"], sortie=DONNEES / "journal.log")
        c = sauvegarde.contenu()
        self.message("Sauvegarde lancée : donnees/sauvegardes/donnees.zip"
                     + (f" (la précédente date du {c['le'][:16]})." if c else "."))

    def exporter_hf(self):
        """Fichier de chaque source qui a changé → dataset rag-politique/politique-sources (python -m huggingface,
        docs/HUGGINGFACE.md). Aussi fait seul après chaque collecte qui ramène du neuf."""
        from commun.taches import en_cours, lancer_en_fond
        if en_cours("huggingface"):
            return self.message("Un export vers Hugging Face est déjà en cours : voir le journal.")
        if not messagebox.askyesno("Exporter vers Hugging Face",
                                   "Mettre à jour dans le dataset public rag-politique/politique-sources le "
                                   "fichier de chaque source qui a changé (commentaires notés, avec le nom de "
                                   "leurs auteurs) ? L'ancien fichier de ces sources est remplacé."):
            return
        lancer_en_fond(["-m", "huggingface"], env={"HF_HUB_OFFLINE": "0"})
        self.message("Export vers Hugging Face lancé : suivi dans le journal du tableau de bord.")

    def message(self, texte: str):
        """Message passager en bas de la fenêtre (6 secondes)."""
        self.barre.config(text=texte)
        self.after(6000, lambda: self.barre.config(text="") if self.barre.cget("text") == texte else None)

    def journal_texte(self, texte: str):
        self.tableau.ecrire_journal(texte)

    def apres_action(self):
        """État des cartes du tableau de bord, juste après un lancement ou un arrêt."""
        self.tableau.maj(self.comptes)

    def _lire_journal(self):
        """Ajoute au journal en direct les lignes complètes écrites depuis la dernière lecture."""
        if not JOURNAL.exists():
            return
        taille = JOURNAL.stat().st_size
        if self._position_journal is None:  # à l'ouverture : les 150 dernières lignes
            with open(JOURNAL, "rb") as f:
                f.seek(max(0, taille - 30000))
                lignes = f.read().decode("utf-8", errors="replace").splitlines()[-150:]
            self.journal_texte("\n".join(lignes))
            self._position_journal = taille
            return
        if taille < self._position_journal:
            self._position_journal = 0
        if taille > self._position_journal:
            with open(JOURNAL, "rb") as f:
                f.seek(self._position_journal)
                bloc = f.read()
            fin = bloc.rfind(b"\n") + 1
            if fin:
                self.journal_texte(bloc[:fin].decode("utf-8", errors="replace"))
                self._position_journal += fin

    def _boucle_rapide(self):
        try:
            while not self.a_faire.empty():
                self.a_faire.get_nowait()()
            self._lire_journal()
            self.apres_action()
            self.analyse.boucle()
            self.moderation.boucle()
        finally:
            self.after(1500, self._boucle_rapide)

    def _boucle_comptage(self):
        if not self._comptage_en_cours:
            self._comptage_en_cours = True

            def travail():
                try:
                    r = compter_par_source()
                    self.a_faire.put(lambda: self._comptes_prets(r))
                finally:
                    self._comptage_en_cours = False

            threading.Thread(target=travail, daemon=True).start()
        self.after(20000, self._boucle_comptage)

    def _comptes_prets(self, comptes):
        self.comptes = comptes
        self.apres_action()
        for page in self.pages_comptes:
            page.remplir()
