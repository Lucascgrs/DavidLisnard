"""Sous-onglet « Commentaires » : filtres, tableau par pages de 500 lignes, détail du commentaire sélectionné,
correction des notes, export Excel, lancement et arrêt de l'analyse de la sélection."""
import tkinter as tk
import webbrowser
from collections import Counter
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

from analyse import stockage
from analyse.criteres import COURTS, CRITERES, EXPLICATIONS, TITRES
from commun.config import SOURCES
from commun.taches import demander_arret, en_cours, lancer_en_fond
from commun.textes import pour_excel, sans_accents
from interface.theme import COULEURS, nombre, ouvrir, police, puce, ton_note

TACHE = "analyse"
PAGE = 500
SOURCES_ANALYSE = {"youtube": "YouTube", "instagram": "Instagram", "whatsapp": "WhatsApp"}
COULEURS_LIGNES = {"tres_neg": "#fde7e9", "neg": "#fff4f4", "pos": "#f1faf1", "tres_pos": "#dff6dd",
                   "autre": "#f5f5f5"}
FIABILITES = {"toutes": None, "bonne et moyenne": {"bonne", "moyenne", "corrigée"}, "bonne": {"bonne", "corrigée"}}


def couleur_ligne(l: dict) -> str:
    """Étiquette de couleur d'une ligne selon la tonalité (gris : ne parle pas de Lisnard)."""
    t = l["tonalite"]
    if l["cible"] == "A":
        return "autre"
    if t is None:
        return ""
    return "tres_neg" if t <= 5 else "neg" if t <= 8 else "tres_pos" if t >= 16 else "pos" if t >= 13 else ""


class OngletCommentaires:
    def __init__(self, page, sous: ttk.Notebook):
        self.page = page
        self.app = page.app
        self.selection: list[dict] = []
        self.numero_page = 0
        self.tri = ("date", True)
        self._comptes: list[str] = []
        C = COULEURS
        f = tk.Frame(sous, bg=C["fond"], padx=6, pady=6)
        sous.add(f, text="Commentaires")
        self._filtres(f)
        droite = tk.Frame(f, bg=C["fond"])
        droite.pack(side="left", fill="both", expand=True)
        self._commande(droite)
        self._tableau(droite)
        self._detail(droite)

    # -- construction --------------------------------------------------------------------------------------------

    def _filtres(self, f):
        C = COULEURS
        gauche = tk.Frame(f, bg=C["fond"], width=290)
        gauche.pack(side="left", fill="y", padx=(0, 10))
        gauche.pack_propagate(False)
        toile = tk.Canvas(gauche, bg=C["fond"], highlightthickness=0)
        defile = ttk.Scrollbar(gauche, command=toile.yview)
        filtres = tk.Frame(toile, bg=C["fond"])
        filtres.bind("<Configure>", lambda e: toile.configure(scrollregion=toile.bbox("all")))
        toile.create_window((0, 0), window=filtres, anchor="nw", width=270)
        toile.configure(yscrollcommand=defile.set)
        defile.pack(side="right", fill="y")
        toile.pack(side="left", fill="both", expand=True)
        toile.bind_all("<MouseWheel>", lambda e: toile.yview_scroll(-e.delta // 120, "units")
                       if str(e.widget).startswith(str(gauche)) else None, add="+")

        def titre(t):
            tk.Label(filtres, text=t, font=police(10, True), bg=C["fond"], fg=C["texte"]).pack(anchor="w", pady=(8, 2))

        titre("Sources")
        self.v_sources = {}
        for s, n in SOURCES_ANALYSE.items():
            v = tk.BooleanVar(value=True)
            ttk.Checkbutton(filtres, text=n, variable=v, command=self._remplir_comptes).pack(anchor="w")
            self.v_sources[s] = v
        titre("Comptes (aucun sélectionné = tous)")
        cadre_l = tk.Frame(filtres, bg=C["bord"])
        cadre_l.pack(fill="x")
        self.liste_comptes = tk.Listbox(cadre_l, selectmode="multiple", height=7, exportselection=False,
                                        relief="flat", font=police(9))
        self.liste_comptes.pack(fill="x", padx=1, pady=1)
        titre("Période (date du commentaire)")
        ligne = tk.Frame(filtres, bg=C["fond"])
        ligne.pack(fill="x")
        tk.Label(ligne, text="du", bg=C["fond"]).pack(side="left")
        self.v_du = tk.StringVar()
        ttk.Entry(ligne, textvariable=self.v_du, width=11).pack(side="left", padx=3)
        tk.Label(ligne, text="au", bg=C["fond"]).pack(side="left")
        self.v_au = tk.StringVar()
        ttk.Entry(ligne, textvariable=self.v_au, width=11).pack(side="left", padx=3)
        raccourcis = tk.Frame(filtres, bg=C["fond"])
        raccourcis.pack(fill="x", pady=(3, 0))
        for t, j in (("7 j", 7), ("30 j", 30), ("Année", "an"), ("Tout", None)):
            ttk.Button(raccourcis, text=t, width=6, command=lambda j=j: self._periode(j)).pack(side="left", padx=1)
        titre("Type")
        self.v_type = tk.StringVar(value="tous")
        for v, t in (("tous", "Tous"), ("principal", "Principaux"), ("réponse", "Réponses")):
            ttk.Radiobutton(filtres, text=t, value=v, variable=self.v_type).pack(anchor="w")
        titre("Recherche dans le texte")
        self.v_cherche = tk.StringVar()
        e = ttk.Entry(filtres, textvariable=self.v_cherche)
        e.pack(fill="x")
        e.bind("<Return>", lambda _: self.appliquer())
        titre("Notes (minimum – maximum)")
        self.v_min, self.v_max = {}, {}
        for c in CRITERES:
            ligne = tk.Frame(filtres, bg=C["fond"])
            ligne.pack(fill="x", pady=1)
            tk.Label(ligne, text=TITRES[c], width=10, anchor="w", bg=C["fond"]).pack(side="left")
            self.v_min[c], self.v_max[c] = tk.StringVar(value="0"), tk.StringVar(value="20")
            ttk.Spinbox(ligne, from_=0, to=20, width=4, textvariable=self.v_min[c]).pack(side="left")
            tk.Label(ligne, text="–", bg=C["fond"]).pack(side="left", padx=2)
            ttk.Spinbox(ligne, from_=0, to=20, width=4, textvariable=self.v_max[c]).pack(side="left")
        titre("Autres")
        self.v_sans_autre = tk.BooleanVar(value=False)
        ttk.Checkbutton(filtres, text="Masquer ceux qui ne parlent pas de Lisnard",
                        variable=self.v_sans_autre).pack(anchor="w")
        self.v_fiab = tk.StringVar(value="toutes")
        ligne = tk.Frame(filtres, bg=C["fond"])
        ligne.pack(fill="x", pady=2)
        tk.Label(ligne, text="Fiabilité", bg=C["fond"]).pack(side="left")
        ttk.Combobox(ligne, textvariable=self.v_fiab, state="readonly", width=16, values=list(FIABILITES)).pack(
            side="left", padx=4)
        self.v_etat = tk.StringVar(value="tous")
        for v, t in (("tous", "Analysés ou non"), ("notes", "Analysés seulement"), ("non", "Pas encore analysés")):
            ttk.Radiobutton(filtres, text=t, value=v, variable=self.v_etat).pack(anchor="w")
        boutons = tk.Frame(filtres, bg=C["fond"])
        boutons.pack(fill="x", pady=(10, 2))
        ttk.Button(boutons, text="Appliquer", style="Accent.TButton", command=self.appliquer).pack(side="left")
        ttk.Button(boutons, text="Réinitialiser", command=self.reinitialiser).pack(side="left", padx=4)
        ttk.Button(filtres, text="Exporter la sélection vers Excel", command=self.exporter).pack(fill="x", pady=4)

    def _commande(self, droite):
        C = COULEURS
        self.etat = tk.Label(droite, text="", bg=C["fond"], fg=C["texte"], anchor="w", font=police(10, True))
        self.etat.pack(fill="x")
        commande = tk.Frame(droite, bg=C["fond"])
        commande.pack(fill="x", pady=(4, 6))
        self.b_lancer = ttk.Button(commande, text="Lancer l'analyse de la sélection", style="Accent.TButton",
                                   command=self.lancer)
        self.b_lancer.pack(side="left")
        self.b_arreter = ttk.Button(commande, text="Arrêter", command=self.arreter)
        self.b_arreter.pack(side="left", padx=6)
        self.barre = ttk.Progressbar(commande, length=180, mode="determinate")
        self.barre.pack(side="left", padx=6)
        self.avance = tk.Label(commande, text="", bg=C["fond"], fg=C["doux"])
        self.avance.pack(side="left")

    def _tableau(self, droite):
        C = COULEURS
        colonnes = ["date", "source", "compte", "texte"] + CRITERES + ["cible", "fiabilite"]
        largeurs = {"date": 90, "source": 70, "compte": 120, "texte": 380, "cible": 45, "fiabilite": 70}
        entetes = {"date": "Date", "source": "Source", "compte": "Compte", "texte": "Commentaire",
                   "cible": "Cible", "fiabilite": "Fiabilité", **COURTS}
        cadre = tk.Frame(droite, bg=C["bord"])
        cadre.pack(fill="both", expand=True)
        self.table = ttk.Treeview(cadre, columns=colonnes, show="headings", selectmode="browse")
        for c in colonnes:
            self.table.heading(c, text=entetes[c], command=lambda c=c: self.trier(c))
            self.table.column(c, width=largeurs.get(c, 50), anchor="w" if c in ("texte", "compte") else "center",
                              stretch=c == "texte")
        for etiquette, couleur in COULEURS_LIGNES.items():
            self.table.tag_configure(etiquette, background=couleur)
        barre = ttk.Scrollbar(cadre, command=self.table.yview)
        self.table.config(yscrollcommand=barre.set)
        barre.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self.table.bind("<<TreeviewSelect>>", lambda _: self.detail())
        pages = tk.Frame(droite, bg=C["fond"])
        pages.pack(fill="x", pady=3)
        ttk.Button(pages, text="◀", width=3, command=lambda: self.aller(-1)).pack(side="left")
        self.l_page = tk.Label(pages, text="", bg=C["fond"], fg=C["doux"])
        self.l_page.pack(side="left", padx=6)
        ttk.Button(pages, text="▶", width=3, command=lambda: self.aller(1)).pack(side="left")
        tk.Label(pages, text="Couleur de ligne : tonalité (rouge hostile, vert favorable, gris : ne parle pas de "
                 "Lisnard)", bg=C["fond"], fg=C["doux"], font=police(8)).pack(side="right")

    def _detail(self, droite):
        C = COULEURS
        detail = tk.Frame(droite, bg=C["carte"], highlightbackground=C["bord"], highlightthickness=1)
        detail.pack(fill="x", pady=(6, 0))
        self.puces_detail = tk.Frame(detail, bg=C["carte"], padx=8, pady=6)
        self.puces_detail.pack(fill="x")
        self.t_detail = tk.Text(detail, height=8, wrap="word", relief="flat", font=police(10),
                                bg=C["carte"], fg=C["texte"], state="disabled")
        self.t_detail.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        self.t_detail.tag_configure("gras", font=police(10, True))
        self.t_detail.tag_configure("doux", foreground=C["doux"])
        boutons = tk.Frame(detail, bg=C["carte"])
        boutons.pack(side="right", fill="y", padx=6, pady=6)
        self.b_ouvrir = ttk.Button(boutons, text="Ouvrir l'original", command=self.ouvrir_original)
        self.b_ouvrir.pack(fill="x")
        ttk.Button(boutons, text="Corriger les notes", command=self.corriger).pack(fill="x", pady=4)

    # -- filtres -------------------------------------------------------------------------------------------------

    def donnees_pretes(self):
        self._remplir_comptes()
        self.appliquer()

    def _remplir_comptes(self):
        actives = {s for s, v in self.v_sources.items() if v.get()}
        comptes = Counter(l["compte"] for l in self.page.lignes if l["source"] in actives)
        choisis = {self.liste_comptes.get(i).rsplit("  (", 1)[0] for i in self.liste_comptes.curselection()}
        self.liste_comptes.delete(0, "end")
        self._comptes = []
        for c, n in sorted(comptes.items(), key=lambda x: -x[1]):
            self.liste_comptes.insert("end", f"{c}  ({n})")
            self._comptes.append(c)
            if c in choisis:
                self.liste_comptes.selection_set("end")

    def _periode(self, jours):
        self.v_au.set("")
        if jours is None:
            self.v_du.set("")
        elif jours == "an":
            self.v_du.set(f"{date.today().year}-01-01")
        else:
            self.v_du.set((date.today() - timedelta(days=jours)).isoformat())
        self.appliquer()

    def reinitialiser(self):
        for v in self.v_sources.values():
            v.set(True)
        self.liste_comptes.selection_clear(0, "end")
        for v in (self.v_du, self.v_au, self.v_cherche):
            v.set("")
        self.v_type.set("tous")
        for c in CRITERES:
            self.v_min[c].set("0")
            self.v_max[c].set("20")
        self.v_sans_autre.set(False)
        self.v_fiab.set("toutes")
        self.v_etat.set("tous")
        self._remplir_comptes()
        self.appliquer()

    def _bornes(self) -> dict:
        b = {}
        for c in CRITERES:
            try:
                lo, hi = int(self.v_min[c].get()), int(self.v_max[c].get())
            except ValueError:
                lo, hi = 0, 20
            if (lo, hi) != (0, 20):
                b[c] = (lo, hi)
        return b

    def filtre(self) -> list[dict]:
        sources = {s for s, v in self.v_sources.items() if v.get()}
        comptes = {self._comptes[i] for i in self.liste_comptes.curselection()}
        du, au = self.v_du.get().strip(), self.v_au.get().strip()
        typ, mot = self.v_type.get(), sans_accents(self.v_cherche.get().strip())
        bornes, sans_autre, etat = self._bornes(), self.v_sans_autre.get(), self.v_etat.get()
        ok_fiab = FIABILITES[self.v_fiab.get()]
        sortie = []
        for l in self.page.lignes:
            if l["source"] not in sources or (comptes and l["compte"] not in comptes):
                continue
            d = l["date"][:10]
            if (du and d < du) or (au and d > au) or (typ != "tous" and l["type"] != typ):
                continue
            if mot and mot not in l["_cherche"]:
                continue
            if etat == "notes" and not l["_note"] or etat == "non" and l["_note"]:
                continue
            if l["_note"]:
                if sans_autre and l["cible"] == "A":
                    continue
                if ok_fiab and l["fiabilite"] not in ok_fiab:
                    continue
                if any(not lo <= l[c] <= hi for c, (lo, hi) in bornes.items()):
                    continue
            elif bornes or sans_autre or ok_fiab:
                continue  # un filtre sur les notes écarte ce qui n'est pas noté
            sortie.append(l)
        return sortie

    def appliquer(self):
        self.selection = self.filtre()
        self.numero_page = 0
        self._trier_selection()
        self.afficher()
        self.page.selection_changee(self.selection)

    # -- tableau -------------------------------------------------------------------------------------------------

    def trier(self, colonne):
        desc = not self.tri[1] if self.tri[0] == colonne else colonne == "date" or colonne in CRITERES
        self.tri = (colonne, desc)
        self._trier_selection()
        self.numero_page = 0
        self.afficher()

    def _trier_selection(self):
        col, desc = self.tri
        if col in CRITERES:
            self.selection.sort(key=lambda l: (l[col] is not None, l[col] or 0), reverse=desc)
        else:
            self.selection.sort(key=lambda l: l.get(col) or "", reverse=desc)

    def afficher(self):
        self.table.delete(*self.table.get_children())
        debut = self.numero_page * PAGE
        for i, l in enumerate(self.selection[debut:debut + PAGE]):
            valeurs = [l["date"][:10], SOURCES.get(l["source"], l["source"]), l["compte"][:30],
                       " ".join(l["texte"].split())[:160]]
            valeurs += ["—" if l[c] is None else l[c] for c in CRITERES]
            valeurs += [l["cible"] or "—", l["fiabilite"] or "—"]
            etiquette = couleur_ligne(l)
            self.table.insert("", "end", iid=str(debut + i), values=valeurs, tags=(etiquette,) if etiquette else ())
        n = len(self.selection)
        self.l_page.config(text=f"page {self.numero_page + 1} / {max(1, (n + PAGE - 1) // PAGE)}")
        notes = sum(1 for l in self.selection if l["_note"])
        self.etat.config(text=f"{nombre(n)} commentaires dans la sélection · {nombre(notes)} analysés")
        self._maj_boutons()

    def aller(self, sens):
        pages = max(1, (len(self.selection) + PAGE - 1) // PAGE)
        self.numero_page = min(max(0, self.numero_page + sens), pages - 1)
        self.afficher()

    def _courant(self):
        s = self.table.selection()
        return self.selection[int(s[0])] if s else None

    def detail(self):
        l = self._courant()
        t = self.t_detail
        t.config(state="normal")
        t.delete("1.0", "end")
        if l:
            t.insert("end", f"{l['date']} · {SOURCES.get(l['source'])} · {l['compte']} · {l['type']}\n", "doux")
            if l["publication_titre"]:
                t.insert("end", "Publication : ", "gras")
                t.insert("end", l["publication_titre"][:300] + "\n")
            if l["parent_texte"]:
                t.insert("end", "En réponse à : ", "gras")
                t.insert("end", l["parent_texte"][:400] + "\n")
            t.insert("end", "Commentaire : ", "gras")
            t.insert("end", l["texte"] + "\n")
            if not l["_note"]:
                t.insert("end", "Pas encore analysé.\n", "doux")
        t.config(state="disabled")
        for w in self.puces_detail.winfo_children():
            w.destroy()
        if l and l["_note"]:
            for c in CRITERES:
                puce(self.puces_detail, f"{TITRES[c]} {l[c]}", ton_note(c, l[c])).pack(side="left", padx=(0, 6))
            puce(self.puces_detail, "parle de Lisnard" if l["cible"] != "A" else "parle d'autre chose",
                 "accent" if l["cible"] != "A" else "neutre").pack(side="left", padx=(10, 6))
            puce(self.puces_detail, f"fiabilité {l['fiabilite']}",
                 {"bonne": "vert", "corrigée": "vert", "moyenne": "orange"}.get(l["fiabilite"], "rouge")).pack(side="left")
        self.b_ouvrir.state(["!disabled"] if l and l["publication_lien"] else ["disabled"])

    def ouvrir_original(self):
        l = self._courant()
        if l and l["publication_lien"]:
            webbrowser.open(l["publication_lien"])

    def corriger(self):
        l = self._courant()
        if not l:
            return
        C = COULEURS
        fen = tk.Toplevel(self.app)
        fen.title("Corriger les notes")
        fen.transient(self.app)
        fen.configure(bg=C["fond"], padx=14, pady=10)
        tk.Label(fen, text=" ".join(l["texte"].split())[:300], wraplength=460, justify="left",
                 bg=C["fond"]).pack(anchor="w", pady=(0, 8))
        vs = {}
        for c in CRITERES:
            ligne = tk.Frame(fen, bg=C["fond"])
            ligne.pack(fill="x", pady=1)
            tk.Label(ligne, text=TITRES[c], width=11, anchor="w", bg=C["fond"]).pack(side="left")
            vs[c] = tk.StringVar(value=str(l[c] if l[c] is not None else 10))
            ttk.Spinbox(ligne, from_=0, to=20, width=4, textvariable=vs[c]).pack(side="left")
            tk.Label(ligne, text=EXPLICATIONS[c], bg=C["fond"], fg=C["doux"], font=police(8)).pack(side="left", padx=6)
        v_cible = tk.StringVar(value=l["cible"] or "L")
        ligne = tk.Frame(fen, bg=C["fond"])
        ligne.pack(fill="x", pady=4)
        ttk.Radiobutton(ligne, text="Parle de Lisnard", value="L", variable=v_cible).pack(side="left")
        ttk.Radiobutton(ligne, text="Ne parle pas de Lisnard", value="A", variable=v_cible).pack(side="left", padx=8)

        def enregistrer():
            try:
                notes = {c: int(vs[c].get()) for c in CRITERES}
                if not all(0 <= x <= 20 for x in notes.values()):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Notes", "Les notes sont des entiers de 0 à 20.", parent=fen)
                return
            if v_cible.get() == "A":  # règle de la grille : ne parle pas de lui ⇒ ton et reproches à 10
                notes.update(tonalite=10, forme=10, systeme=10, idees=10)
            stockage.enregistrer_correction(l["cle"], v_cible.get(), notes)
            l.update(notes, cible=v_cible.get(), fiabilite="corrigée", _note=True, _corrige=True)
            fen.destroy()
            self.afficher()
            self.app.message("Correction enregistrée : elle servira au prochain entraînement du modèle.")

        ttk.Button(fen, text="Enregistrer", style="Accent.TButton", command=enregistrer).pack(anchor="e", pady=(8, 0))

    def exporter(self):
        if not self.selection:
            return
        from openpyxl import Workbook
        from openpyxl.styles import Font
        chemin = stockage.EXPORTS / f"analyse_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        wb = Workbook()
        ws = wb.active
        ws.title = "Commentaires"
        ws.append(["date", "source", "compte", "type", "publication_titre", "publication_lien", "texte"]
                  + CRITERES + ["cible", "fiabilite"])
        for c in ws[1]:
            c.font = Font(bold=True)
        for l in self.selection:
            ws.append([l["date"], l["source"], l["compte"], l["type"], l["publication_titre"],
                       l["publication_lien"], pour_excel(l["texte"])]
                      + [l[c] for c in CRITERES] + [l["cible"], l["fiabilite"]])
        ws.freeze_panes = "A2"
        wb.save(chemin)
        ouvrir(chemin)

    # -- lancer / arrêter l'analyse ------------------------------------------------------------------------------

    def lancer(self):
        if en_cours(TACHE):
            return
        if not self.page.infos_modele:
            messagebox.showinfo("Analyse", "Le modèle n'est pas encore entraîné : rien à lancer pour l'instant.")
            return
        args = ["-m", "analyse"]
        sources = [s for s, v in self.v_sources.items() if v.get()]
        if len(sources) < len(SOURCES_ANALYSE):
            args += ["--sources", ",".join(sources)]
        if self.v_du.get().strip():
            args += ["--du", self.v_du.get().strip()]
        if self.v_au.get().strip():
            args += ["--au", self.v_au.get().strip()]
        lancer_en_fond(args)
        self.app.message("Analyse lancée en arrière-plan.")
        self.page._etait_en_cours = True

    def arreter(self):
        if en_cours(TACHE):
            demander_arret(TACHE)
            self.app.message("Arrêt demandé : l'analyse s'arrête à la fin du lot en cours.")

    def _maj_boutons(self, actif: bool | None = None):
        actif = bool(en_cours(TACHE)) if actif is None else actif
        self.b_lancer.state(["disabled"] if actif or not self.page.infos_modele else ["!disabled"])
        self.b_arreter.state(["!disabled"] if actif else ["disabled"])

    def montrer_avancement(self, actif: bool, a: dict):
        if actif:
            total, fait = a.get("total") or 0, a.get("fait") or 0
            self.barre.config(maximum=max(total, 1), value=fait)
            self.avance.config(text=f"{a.get('etape', '…')} {fait}/{total}" if total else a.get("etape", "…"))
        else:
            self.barre.config(value=0)
            if not self.page.infos_modele:
                self.avance.config(text="Le modèle n'est pas encore entraîné.")
            elif a:
                self.avance.config(text=f"Dernière analyse : {a.get('etape')} ({a.get('le', '')[:16]})")
        self._maj_boutons(actif)
