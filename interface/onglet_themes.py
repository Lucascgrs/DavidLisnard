"""Onglet « Thèmes » : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens.

Les thèmes et les rattachements viennent de donnees/critiques/ (lecture faite commentaire par commentaire par Claude,
« python -m critiques », voir critiques/__init__.py). Un commentaire peut être rattaché à plusieurs thèmes, chacun
avec son sens : éloge, critique, ou doute ou question. Les comptes sont donnés en rattachements et en auteurs
distincts. Chaque critique ou doute porte aussi une catégorie (donnees.CATEGORIES : opposition de principe, demande
de précision, objection sur une mesure, doute sur la faisabilité, suggestion) ; le filtre « Catégorie » ne garde que
les critiques et doutes de la catégorie choisie, et tous les comptes de l'onglet suivent.
"""
import threading
import tkinter as tk
from tkinter import ttk

from critiques import donnees
from interface.theme import COULEURS, carte, nombre, note, police

SENS = {"E": "Éloges", "C": "Critiques", "D": "Doutes ou questions"}
COULEUR_SENS = {"E": COULEURS["vert"], "C": COULEURS["rouge"], "D": COULEURS["orange"]}
MAX_LIENS = 300
TOUS_LES_THEMES = "Tous les thèmes"  # premier choix du filtre « Thèmes qui portent sur »
AUTRES = donnees.FAMILLES["autre"]
# Filtre « Catégorie » : toutes, tout ce que le programme peut traiter (2 à 5), ou une seule catégorie.
TOUTES_LES_CATEGORIES = "Toutes les catégories"
TRAITABLES = "Tout sauf les oppositions de principe"
CHOIX_CATEGORIES = {TOUTES_LES_CATEGORIES: None, TRAITABLES: {"2", "3", "4", "5"},
                    **{nom: {k} for k, nom in donnees.CATEGORIES.items()}}


class PageThemes:
    def __init__(self, app, onglets: ttk.Notebook):
        self.app = app
        self.res: dict | None = None
        C = COULEURS
        f = tk.Frame(onglets, bg=C["fond"], padx=14, pady=12)
        onglets.add(f, text="Thèmes")

        haut = tk.Frame(f, bg=C["fond"])
        haut.pack(fill="x")
        titres = tk.Frame(haut, bg=C["fond"])
        titres.pack(side="left", fill="x", expand=True)
        tk.Label(titres, text="Ce qu'on dit de lui, thème par thème", font=police(14, True, True), bg=C["fond"],
                 fg=C["texte"]).pack(anchor="w")
        note(titres, "Commentaires qui parlent de lui, pertinents (12 sur 20 ou plus), d'au moins 20 mots, de fiabilité "
             "bonne ou moyenne. Chacun a été lu et rattaché à un ou plusieurs thèmes, avec son sens : éloge, critique, "
             "ou doute ou question ; chaque critique ou doute a aussi une catégorie, selon ce que le programme "
             "peut en faire. Les copies d'un même texte ne comptent qu'une fois. Mise à jour à la demande "
             "(« python -m critiques », voir le document de fonctionnement).", largeur=820)
        ttk.Button(haut, text="Recharger", command=self.recharger).pack(side="right", anchor="n")
        self.etat = tk.Label(f, text="Chargement…", font=police(9), bg=C["fond"], fg=C["doux"], anchor="w")
        self.etat.pack(fill="x")

        filtres = tk.Frame(f, bg=C["fond"])
        filtres.pack(fill="x", pady=(8, 6))
        tk.Label(filtres, text="Thèmes qui portent sur", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(0, 6))
        self.v_famille = tk.StringVar(value=TOUS_LES_THEMES)
        c = ttk.Combobox(filtres, textvariable=self.v_famille, state="readonly", width=24,
                         values=[TOUS_LES_THEMES] + list(donnees.FAMILLES.values()))
        c.pack(side="left")
        c.bind("<<ComboboxSelected>>", lambda _: self.afficher())
        tk.Label(filtres, text="Type d'avis", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(16, 6))
        self.v_sens = tk.StringVar(value="tous")
        for k, t in [("tous", "Tous les avis")] + list(SENS.items()):
            ttk.Radiobutton(filtres, text=t, value=k, variable=self.v_sens,
                            command=self.changer_sens).pack(side="left", padx=(0, 8))
        tk.Label(filtres, text="Chercher", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(16, 6))
        self.v_q = tk.StringVar()
        e = ttk.Entry(filtres, textvariable=self.v_q, width=24)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _: self.afficher())

        filtres2 = tk.Frame(f, bg=C["fond"])
        filtres2.pack(fill="x", pady=(0, 6))
        tk.Label(filtres2, text="Catégorie des critiques et des doutes", bg=C["fond"],
                 fg=C["doux"]).pack(side="left", padx=(0, 6))
        self.v_cat = tk.StringVar(value=TOUTES_LES_CATEGORIES)
        c2 = ttk.Combobox(filtres2, textvariable=self.v_cat, state="readonly", width=34, values=list(CHOIX_CATEGORIES))
        c2.pack(side="left")
        c2.bind("<<ComboboxSelected>>", lambda _: self.changer_sens())
        self.aide_cat = tk.Label(filtres2, text="", font=police(9), bg=C["fond"], fg=C["doux"], anchor="w")
        self.aide_cat.pack(side="left", padx=(10, 0))

        corps = ttk.PanedWindow(f, orient="horizontal")
        corps.pack(fill="both", expand=True)
        gauche = tk.Frame(corps, bg=C["fond"])
        corps.add(gauche, weight=2)
        colonnes = ("nom", "famille", "E", "C", "D", "auteurs")
        entetes = {"nom": "Thème", "famille": "Porte sur", "E": "Éloges", "C": "Critiques", "D": "Doutes",
                   "auteurs": "Auteurs"}
        largeurs = {"nom": 230, "famille": 170, "E": 60, "C": 70, "D": 60, "auteurs": 65}
        self.table = ttk.Treeview(gauche, columns=colonnes, show="headings", selectmode="browse")
        for col in colonnes:
            self.table.heading(col, text=entetes[col], command=lambda col=col: self.trier(col))
            self.table.column(col, width=largeurs[col], stretch=col == "nom",
                              anchor="w" if col in ("nom", "famille") else "e")
        barre = ttk.Scrollbar(gauche, command=self.table.yview)
        self.table.configure(yscrollcommand=barre.set)
        barre.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", lambda _: self.detail())

        ext, inner = carte(corps, None, None, pad=10)
        corps.add(ext, weight=3)
        self.t = tk.Text(inner, wrap="word", font=police(10), bg=C["carte"], fg=C["texte"], relief="flat",
                         padx=6, pady=4)
        b2 = ttk.Scrollbar(inner, command=self.t.yview)
        self.t.configure(yscrollcommand=b2.set)
        b2.pack(side="right", fill="y")
        self.t.pack(side="left", fill="both", expand=True)
        self.t.tag_configure("titre", font=police(13, True, True))
        self.t.tag_configure("doux", foreground=C["doux"], font=police(9))
        self.t.tag_configure("inter", font=police(11, True), spacing1=10, spacing3=2)
        self.t.tag_configure("texte", foreground=C["doux"], font=police(9), lmargin1=16, lmargin2=16, spacing3=6)
        for s, couleur in COULEUR_SENS.items():
            self.t.tag_configure(s, foreground=couleur, font=police(10, True))
        self.tri = ("total", True)
        self.recharger()

    # --- Données ---------------------------------------------------------------------------------------------

    def recharger(self):
        self.etat.config(text="Chargement des thèmes…")

        boite: dict = {}

        def calcul():
            try:
                boite["r"] = donnees.resultats()
            except Exception as e:  # noqa: BLE001 — affiché dans l'onglet
                boite["erreur"] = e

        def attendre():
            if "r" in boite:
                self.charge(boite["r"])
            elif "erreur" in boite:
                self.etat.config(text=f"Lecture impossible : {boite['erreur']}")
            else:
                self.app.after(200, attendre)

        threading.Thread(target=calcul, daemon=True).start()
        self.app.after(200, attendre)

    def charge(self, r: dict):
        self.res = r
        n = {s: sum(t["n"][s] for t in r["themes"].values()) for s in SENS}
        reste = f" · {nombre(r['sans_categorie'])} critiques ou doutes sans catégorie" if r.get("sans_categorie") else ""
        self.etat.config(text=f"{nombre(r['n_lus'])} commentaires lus · {nombre(r['n_selection'])} retenus aujourd'hui, "
                              f"{nombre(r['a_lire'])} à lire · {len(r['themes'])} thèmes · "
                              f"{nombre(r['n_rattachements'])} rattachements : {nombre(n['E'])} éloges, "
                              f"{nombre(n['C'])} critiques, {nombre(n['D'])} doutes ou questions{reste}.")
        self.afficher()

    # --- Affichage -------------------------------------------------------------------------------------------

    def garde(self, lien: dict) -> bool:
        """Le rattachement passe-t-il le filtre « Catégorie » ? (une catégorie choisie écarte les éloges)"""
        cats = CHOIX_CATEGORIES.get(self.v_cat.get())
        return cats is None or (lien["sens"] in donnees.SENS_TRIES and lien["categorie"] in cats)

    def compter(self) -> None:
        """Comptes de chaque thème sous le filtre « Catégorie » : rattachements et auteurs distincts par sens."""
        self.comptes = {}
        for i, t in self.res["themes"].items():
            liens = [l for l in t["liens"] if self.garde(l)]
            self.comptes[i] = {
                "liens": liens, "n": {s: sum(l["sens"] == s for l in liens) for s in SENS},
                "auteurs": {s: len({l["auteur_h"] or l["cle"] for l in liens if l["sens"] == s}) for s in SENS}}

    def themes_filtres(self) -> list[tuple[str, dict]]:
        if not self.res:
            return []
        self.compter()
        fam = self.v_famille.get()
        q = donnees.normaliser(self.v_q.get())
        sens = self.v_sens.get()
        out = []
        for i, t in self.res["themes"].items():
            if fam != TOUS_LES_THEMES and donnees.FAMILLES.get(t.get("famille"), AUTRES) != fam:
                continue
            if q and q not in donnees.normaliser(t["nom"] + " " + t.get("definition", "")):
                continue
            n = self.comptes[i]["n"]
            if not (n[sens] if sens != "tous" else sum(n.values())):
                continue
            out.append((i, t))
        return out

    def valeur(self, t: dict, col: str):
        sens = self.v_sens.get()
        c = self.comptes[t["id"]]
        if col in SENS:
            return c["n"][col]
        if col == "auteurs":
            return c["auteurs"][sens] if sens != "tous" else sum(c["auteurs"].values())
        if col == "total":
            return c["n"][sens] if sens != "tous" else sum(c["n"].values())
        if col == "famille":
            return donnees.FAMILLES.get(t.get("famille"), AUTRES)
        return t["nom"]

    def trier(self, col):
        self.tri = (col, not self.tri[1] if self.tri[0] == col else col not in ("nom", "famille"))
        self.afficher()

    def changer_sens(self):
        self.tri = ("total", True)
        self.afficher()

    def afficher(self):
        choisi = self.table.selection()
        self.table.delete(*self.table.get_children())
        col, inverse = self.tri
        lignes = sorted(self.themes_filtres(), key=lambda x: self.valeur(x[1], col), reverse=inverse)
        cats = CHOIX_CATEGORIES.get(self.v_cat.get())
        if cats is None:
            self.aide_cat.config(text="")
        else:
            total = sum(len(self.comptes[i]["liens"]) for i, _ in lignes)
            definition = donnees.DEFINITIONS_CATEGORIES[next(iter(cats))] if len(cats) == 1 else \
                "demandes de précision, objections, doutes sur la faisabilité et suggestions"
            self.aide_cat.config(text=f"{nombre(total)} critiques ou doutes : {definition}.")
        for i, t in lignes:
            self.table.insert("", "end", iid=i, values=(t["nom"], self.valeur(t, "famille"), self.valeur(t, "E"),
                                                        self.valeur(t, "C"), self.valeur(t, "D"),
                                                        self.valeur(t, "auteurs")))
        if choisi and self.table.exists(choisi[0]):
            self.table.selection_set(choisi[0])
        elif lignes:
            self.table.selection_set(lignes[0][0])
        else:
            self.t.delete("1.0", "end")

    def detail(self):
        sel = self.table.selection()
        if not sel or not self.res:
            return
        t = self.res["themes"][sel[0]]
        c = self.comptes[sel[0]]
        filtre_cat = CHOIX_CATEGORIES.get(self.v_cat.get()) is not None
        sens = self.v_sens.get()
        w = self.t
        w.delete("1.0", "end")
        w.insert("end", t["nom"] + "\n", "titre")
        w.insert("end", f"{self.valeur(t, 'famille')} · {t.get('definition', '')}\n", "doux")
        w.insert("end", " · ".join(f"{SENS[s]} : {c['n'][s]} ({c['auteurs'][s]} auteurs)" for s in SENS
                                   if not filtre_cat or s in donnees.SENS_TRIES) + "\n", "doux")
        par_cat = {k: sum(l["categorie"] == k for l in t["liens"] if l["sens"] in donnees.SENS_TRIES)
                   for k in donnees.CATEGORIES}
        if any(par_cat.values()):
            w.insert("end", "Critiques et doutes par catégorie : " + " · ".join(
                f"{nom} {par_cat[k]}" for k, nom in donnees.CATEGORIES.items()) + "\n", "doux")
        mois = t.get("mois", {})
        if mois and not filtre_cat:
            w.insert("end", "Par mois : " + ", ".join(
                f"{m[5:]}/{m[2:4]} {v['E']}·{v['C']}·{v['D']}" for m, v in list(mois.items())[-8:])
                + "  (éloges·critiques·doutes)\n", "doux")
        for s in SENS:
            if sens not in ("tous", s) or (filtre_cat and s not in donnees.SENS_TRIES):
                continue
            txt = t.get("synthese", {}).get(s)
            if txt:
                w.insert("end", f"{SENS[s]}\n", ("inter", s))
                w.insert("end", txt + "\n")
        if filtre_cat:
            w.insert("end", "Les résumés ci-dessus portent sur toutes les critiques et tous les doutes du thème ; "
                            "les nombres et les commentaires, sur la catégorie choisie.\n", "doux")
        liens = [l for l in c["liens"] if sens in ("tous", l["sens"])]
        w.insert("end", f"Commentaires ({len(liens)}{', les ' + str(MAX_LIENS) + ' plus récents' if len(liens) > MAX_LIENS else ''})\n",
                 "inter")
        for l in liens[:MAX_LIENS]:
            w.insert("end", f"● ", l["sens"])
            w.insert("end", f"{l['resume']}  ")
            cat = donnees.CATEGORIES.get(l["categorie"])
            w.insert("end", f"{cat + ' · ' if cat else ''}{l['date']} · {l['source']}\n", "doux")
            w.insert("end", (l["texte"][:600] + ("…" if len(l["texte"]) > 600 else "")) + "\n", "texte")
        w.see("1.0")
