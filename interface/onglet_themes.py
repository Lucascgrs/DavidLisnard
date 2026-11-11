"""Onglet « Thèmes » : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens.

Les thèmes et les rattachements viennent de donnees/critiques/ (lecture faite commentaire par commentaire par Claude,
« python -m critiques », voir critiques/__init__.py). Un commentaire peut être rattaché à plusieurs thèmes, chacun
avec son sens : éloge, critique, ou doute ou question. Les comptes sont donnés en rattachements et en auteurs
distincts.
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
             "ou doute ou question. Les copies d'un même texte ne comptent qu'une fois. Mise à jour à la demande "
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
        self.etat.config(text=f"{nombre(r['n_lus'])} commentaires lus · {nombre(r['n_selection'])} retenus aujourd'hui, "
                              f"{nombre(r['a_lire'])} à lire · {len(r['themes'])} thèmes · "
                              f"{nombre(r['n_rattachements'])} rattachements : {nombre(n['E'])} éloges, "
                              f"{nombre(n['C'])} critiques, {nombre(n['D'])} doutes ou questions.")
        self.afficher()

    # --- Affichage -------------------------------------------------------------------------------------------

    def themes_filtres(self) -> list[tuple[str, dict]]:
        if not self.res:
            return []
        fam = self.v_famille.get()
        q = donnees.normaliser(self.v_q.get())
        sens = self.v_sens.get()
        out = []
        for i, t in self.res["themes"].items():
            if fam != TOUS_LES_THEMES and donnees.FAMILLES.get(t.get("famille"), AUTRES) != fam:
                continue
            if q and q not in donnees.normaliser(t["nom"] + " " + t.get("definition", "")):
                continue
            if sens != "tous" and not t["n"][sens]:
                continue
            out.append((i, t))
        return out

    def valeur(self, t: dict, col: str):
        sens = self.v_sens.get()
        if col in SENS:
            return t["n"][col]
        if col == "auteurs":
            return t["auteurs"][sens] if sens != "tous" else sum(t["auteurs"].values())
        if col == "total":
            return t["n"][sens] if sens != "tous" else t["total"]
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
        for i, t in lignes:
            self.table.insert("", "end", iid=i, values=(t["nom"], self.valeur(t, "famille"), t["n"]["E"],
                                                        t["n"]["C"], t["n"]["D"], self.valeur(t, "auteurs")))
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
        sens = self.v_sens.get()
        w = self.t
        w.delete("1.0", "end")
        w.insert("end", t["nom"] + "\n", "titre")
        w.insert("end", f"{self.valeur(t, 'famille')} · {t.get('definition', '')}\n", "doux")
        w.insert("end", " · ".join(f"{SENS[s]} : {t['n'][s]} ({t['auteurs'][s]} auteurs)" for s in SENS) + "\n",
                 "doux")
        mois = t.get("mois", {})
        if mois:
            w.insert("end", "Par mois : " + ", ".join(
                f"{m[5:]}/{m[2:4]} {v['E']}·{v['C']}·{v['D']}" for m, v in list(mois.items())[-8:])
                + "  (éloges·critiques·doutes)\n", "doux")
        for s in SENS:
            if sens not in ("tous", s):
                continue
            txt = t.get("synthese", {}).get(s)
            if txt:
                w.insert("end", f"{SENS[s]}\n", ("inter", s))
                w.insert("end", txt + "\n")
        liens = [l for l in t["liens"] if sens in ("tous", l["sens"])]
        w.insert("end", f"Commentaires ({len(liens)}{', les ' + str(MAX_LIENS) + ' plus récents' if len(liens) > MAX_LIENS else ''})\n",
                 "inter")
        for l in liens[:MAX_LIENS]:
            w.insert("end", f"● ", l["sens"])
            w.insert("end", f"{l['resume']}  ")
            w.insert("end", f"{l['date']} · {l['source']}\n", "doux")
            w.insert("end", (l["texte"][:600] + ("…" if len(l["texte"]) > 600 else "")) + "\n", "texte")
        w.see("1.0")
