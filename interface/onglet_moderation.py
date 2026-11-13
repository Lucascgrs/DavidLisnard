"""Onglet « Modération » : commentaires Facebook à modérer (insultants) ou qui appellent une réponse (questions).

À part de l'analyse principale (voir moderation/__init__.py). Les catégories viennent de donnees/moderation/notes.csv,
écrit par « python -m moderation classer » ; quand un commentaire a été annoté par Claude, c'est l'annotation qui
est affichée (repérée « annoté »). Rien n'est publié sur le site : cet onglet montre les auteurs et les liens. Les catégories (sans les auteurs) vont
aussi dans la table privée « moderation » de Supabase, que le site ne peut pas lire (moderation/publication.py).
"""
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from commun.fichiers import lire_json
from commun.taches import demander_arret, en_cours, lancer_en_fond
from commun.textes import sans_accents
from interface.theme import COULEURS, Chiffre, carte, nombre, note, ouvrir, police
from moderation import donnees as d

NOMS = {"insultant": "À modérer", "question": "Question", "autre": "Autre"}
CHOIX = {"À modérer (insultants)": "insultant", "Questions": "question", "Autres": "autre", "Tous": None}
MAX_LIGNES = 2000


def charger() -> dict:
    """Commentaires Facebook joints à leur catégorie (annotation, sinon modèle). Quelques secondes : fil à part."""
    notes, ann, e = d.lire_notes(), d.lire_annotations(), d.etat()
    lignes = []
    for c in d.commentaires():
        n, a = notes.get(c["cle"]), ann.get(c["cle"])
        cat = a["categorie"] if a else n["categorie"] if n else ""
        p = {k: float(n[f"p_{k}"]) for k in d.CATEGORIES} if n else {}
        lignes.append({**c, "_cat": cat, "_annote": bool(a), "_p": p, "_sur": p.get(cat, 1.0 if a else 0.0),
                       "_cherche": sans_accents(f"{c['texte']} {c.get('auteur', '')} {c.get('publication_titre', '')}")})
    return {"lignes": lignes, "etat": e}


class PageModeration:
    def __init__(self, app, onglets: ttk.Notebook):
        self.app = app
        self.res: dict | None = None
        self._chargement = False
        self._etait_en_cours = False
        C = COULEURS
        f = tk.Frame(onglets, bg=C["fond"], padx=14, pady=12)
        onglets.add(f, text="Modération")

        haut = tk.Frame(f, bg=C["fond"])
        haut.pack(fill="x")
        titres = tk.Frame(haut, bg=C["fond"])
        titres.pack(side="left", fill="x", expand=True)
        tk.Label(titres, text="Modération des commentaires Facebook", font=police(14, True, True), bg=C["fond"],
                 fg=C["texte"]).pack(anchor="w")
        note(titres, "À part de l'analyse : chaque commentaire Facebook collecté est classé par un modèle entraîné sur "
             "les annotations de Claude. « À modérer » : injure, menace, propos haineux, attaque personnelle "
             "méprisante (une critique dure sans injure n'en est pas). « Question » : appelle une réponse de l'équipe. "
             "« Autre » : tout le reste, commentaires positifs compris. Les nouveaux sont classés seuls à la fin de chaque "
             "collecte qui ramène du Facebook. Le modèle se trompe parfois : relire avant "
             "de supprimer ou de bannir. Double-clic sur un commentaire : ouvre la publication.", largeur=860)
        boutons = tk.Frame(haut, bg=C["fond"])
        boutons.pack(side="right", anchor="n")
        ttk.Button(boutons, text="Classer les nouveaux", style="Accent.TButton", command=self.classer).pack(fill="x")
        ttk.Button(boutons, text="Réentraîner le modèle", command=self.reentrainer).pack(fill="x", pady=4)
        ligne_b = tk.Frame(boutons, bg=C["fond"])
        ligne_b.pack(fill="x")
        ttk.Button(ligne_b, text="Journal", command=lambda: ouvrir(d.JOURNAL)).pack(side="left")
        ttk.Button(ligne_b, text="Arrêter", command=self.arreter).pack(side="left", padx=4)
        ttk.Button(ligne_b, text="Recharger", command=self.recharger).pack(side="left")

        chiffres = tk.Frame(f, bg=C["fond"])
        chiffres.pack(fill="x", pady=(4, 6))
        self.c_total = Chiffre(chiffres, "Commentaires Facebook", "…", "collectés dans les groupes et la page suivis")
        self.c_classes = Chiffre(chiffres, "Traités par le modèle", "…", "")
        self.c_annotes = Chiffre(chiffres, "Annotés par Claude", "…", "")
        self.c_signales = Chiffre(chiffres, "Signalés", "…", "", C["rouge"])
        for k, c in enumerate((self.c_total, self.c_classes, self.c_annotes, self.c_signales)):
            c.cadre.grid(row=0, column=k, sticky="nsew", padx=(0 if k == 0 else 10, 0))
            chiffres.columnconfigure(k, weight=1, uniform="chiffres")
        self.etat = tk.Label(f, text="Chargement…", font=police(9), bg=C["fond"], fg=C["doux"], anchor="w",
                             justify="left", wraplength=1150)
        self.etat.pack(fill="x")

        filtres = tk.Frame(f, bg=C["fond"])
        filtres.pack(fill="x", pady=(8, 6))
        tk.Label(filtres, text="Catégorie", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(0, 6))
        self.v_cat = tk.StringVar(value=next(iter(CHOIX)))
        c = ttk.Combobox(filtres, textvariable=self.v_cat, state="readonly", width=22, values=list(CHOIX))
        c.pack(side="left")
        c.bind("<<ComboboxSelected>>", lambda _: self.afficher())
        tk.Label(filtres, text="Groupe ou page", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(16, 6))
        self.v_groupe = tk.StringVar(value="Tous")
        self.c_groupe = ttk.Combobox(filtres, textvariable=self.v_groupe, state="readonly", width=34, values=["Tous"])
        self.c_groupe.pack(side="left")
        self.c_groupe.bind("<<ComboboxSelected>>", lambda _: self.afficher())
        tk.Label(filtres, text="Chercher", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(16, 6))
        self.v_q = tk.StringVar()
        e = ttk.Entry(filtres, textvariable=self.v_q, width=24)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _: self.afficher())
        self.v_tri = tk.StringVar(value="sur")
        tk.Label(filtres, text="Trier par", bg=C["fond"], fg=C["doux"]).pack(side="left", padx=(16, 6))
        for v, t in (("sur", "sûreté"), ("date", "date")):
            ttk.Radiobutton(filtres, text=t, value=v, variable=self.v_tri, command=self.afficher).pack(side="left",
                                                                                                    padx=(0, 6))

        corps = ttk.PanedWindow(f, orient="vertical")
        corps.pack(fill="both", expand=True)
        haut_t = tk.Frame(corps, bg=C["fond"])
        corps.add(haut_t, weight=3)
        colonnes = ("date", "categorie", "sur", "auteur", "groupe", "publication", "texte")
        entetes = {"date": "Date", "categorie": "Catégorie", "sur": "Sûreté", "auteur": "Auteur",
                   "groupe": "Groupe ou page", "publication": "Publication", "texte": "Commentaire"}
        largeurs = {"date": 120, "categorie": 120, "sur": 60, "auteur": 150, "groupe": 170, "publication": 220,
                    "texte": 420}
        self.table = ttk.Treeview(haut_t, columns=colonnes, show="headings", selectmode="browse")
        for col in colonnes:
            self.table.heading(col, text=entetes[col])
            self.table.column(col, width=largeurs[col], stretch=col == "texte", anchor="e" if col == "sur" else "w")
        b = ttk.Scrollbar(haut_t, command=self.table.yview)
        self.table.configure(yscrollcommand=b.set)
        b.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", lambda _: self.detail())
        self.table.bind("<Double-1>", lambda _: self.ouvrir_lien())
        self.table.tag_configure("insultant", foreground=C["rouge"])
        self.table.tag_configure("question", foreground=C["orange"])

        ext, inner = carte(corps, None, None, pad=10)
        corps.add(ext, weight=2)
        bas = tk.Frame(inner, bg=C["carte"])
        bas.pack(side="bottom", fill="x", pady=(6, 0))
        self.b_lien = ttk.Button(bas, text="Ouvrir la publication", command=self.ouvrir_lien, state="disabled")
        self.b_lien.pack(side="left")
        self.b_copier = ttk.Button(bas, text="Copier le lien", command=self.copier_lien, state="disabled")
        self.b_copier.pack(side="left", padx=6)
        self.t = tk.Text(inner, wrap="word", font=police(10), bg=C["carte"], fg=C["texte"], relief="flat", padx=6,
                         pady=4, height=8)
        self.t.pack(fill="both", expand=True)
        self.t.tag_configure("titre", font=police(11, True))
        self.t.tag_configure("doux", foreground=C["doux"], font=police(9))
        self.t.tag_configure("insultant", foreground=C["rouge"], font=police(10, True))
        self.t.tag_configure("question", foreground=C["orange"], font=police(10, True))
        self.t.tag_configure("autre", foreground=C["doux"], font=police(10, True))
        self.choisi: dict | None = None
        self.index: dict[str, dict] = {}
        self.recharger()

    # --- Données ---------------------------------------------------------------------------------------------

    def recharger(self):
        if self._chargement:
            return
        self._chargement = True
        self.etat.config(text="Chargement des commentaires Facebook…")

        def travail():
            try:
                r = charger()
                self.app.a_faire.put(lambda: self.charge(r))
            except Exception as e:  # noqa: BLE001 — affiché dans l'onglet
                self.app.a_faire.put(lambda: self.etat.config(text=f"Lecture impossible : {e}"))
            finally:
                self._chargement = False

        threading.Thread(target=travail, daemon=True).start()

    def charge(self, r: dict):
        self.res = r
        e, i = r["etat"], r["etat"]["modele"] or {}
        self.c_total.valeur.config(text=nombre(e["commentaires"]))
        self.c_classes.valeur.config(text=nombre(e["classes"]))
        self.c_classes.legende.config(text=f"modèle {i.get('version', '—')} · {nombre(e['a_classer'])} à classer")
        self.c_annotes.valeur.config(text=nombre(e["annotations"]))
        pc = e["annotations_par_categorie"]
        self.c_annotes.legende.config(text=f"dont {nombre(e['test'])} gardés pour mesurer · {pc['insultant']} "
                                           f"insultants, {pc['question']} questions")
        self.c_signales.valeur.config(text=nombre(e["insultants"]))
        self.c_signales.legende.config(text=f"à modérer · et {nombre(e['questions'])} questions")
        if i:
            m = i["mesures"]
            self.etat.config(text=(
                f"Modèle {i['version']} ({i['modele_depart']} affiné), entraîné le {i['le'][8:10]}/{i['le'][5:7]} sur "
                f"{nombre(i['annotations'])} annotations. Sur les {m['n']} commentaires du test, jamais vus : "
                f"d'accord avec Claude {m['accord']:.0%} du temps ; parmi les « à modérer » signalés, "
                f"{m['insultant']['justes']:.0%} le sont vraiment, et {m['insultant']['trouves']:.0%} des vrais sont "
                f"trouvés ; questions : {m['question']['justes']:.0%} justes, {m['question']['trouves']:.0%} trouvées "
                f"(le point faible : annoter des questions l'améliore).").replace("%", " %"))
        else:
            self.etat.config(text="Aucun modèle de modération : lancer « python -m moderation entrainer ».")
        groupes = sorted({l.get("compte_source", "") for l in r["lignes"]} - {""})
        self.c_groupe.config(values=["Tous"] + groupes)
        self.afficher()

    # --- Affichage -------------------------------------------------------------------------------------------

    def afficher(self):
        if not self.res:
            return
        cat = CHOIX[self.v_cat.get()]
        g = self.v_groupe.get()
        q = sans_accents(self.v_q.get().strip())
        lignes = [l for l in self.res["lignes"] if (cat is None or l["_cat"] == cat)
                  and (g == "Tous" or l.get("compte_source") == g) and (not q or q in l["_cherche"])]
        if self.v_tri.get() == "date":
            lignes.sort(key=lambda l: l.get("date") or "", reverse=True)
        else:
            lignes.sort(key=lambda l: (l["_sur"], l.get("date") or ""), reverse=True)
        self.table.delete(*self.table.get_children())
        self.index = {}
        for k, l in enumerate(lignes[:MAX_LIGNES]):
            iid = str(k)
            self.index[iid] = l
            nom = NOMS.get(l["_cat"], "non classé") + (" · annoté" if l["_annote"] else "")
            sur = f"{100 * l['_sur']:.0f} %" if l["_p"] else "—"
            pub = (l.get("publication_titre") or "").replace("\n", " ")[:90]
            self.table.insert("", "end", iid=iid, tags=(l["_cat"],), values=(
                (l.get("date") or "")[:16], nom, sur, l.get("auteur", ""), l.get("compte_source", ""), pub,
                l["texte"].replace("\n", " ")[:300]))
        n = len(lignes)
        self.app.message(f"{nombre(n)} commentaires" + (f", les {MAX_LIGNES} premiers affichés" if n > MAX_LIGNES
                                                         else "") + " dans l'onglet Modération.")
        if lignes:
            self.table.selection_set("0")
        else:
            self.t.delete("1.0", "end")

    def detail(self):
        sel = self.table.selection()
        if not sel or sel[0] not in self.index:
            return
        l = self.choisi = self.index[sel[0]]
        w = self.t
        w.delete("1.0", "end")
        w.insert("end", NOMS.get(l["_cat"], "Non classé"), l["_cat"] or "autre")
        if l["_annote"]:
            w.insert("end", "  (annoté par Claude)", "doux")
        if l["_p"]:
            w.insert("end", "   modèle : " + " · ".join(f"{NOMS[k].lower()} {100 * l['_p'][k]:.0f} %"
                                                       for k in ("insultant", "question", "autre")), "doux")
        w.insert("end", "\n")
        w.insert("end", f"{l.get('auteur', '')}", "titre")
        w.insert("end", f"  ·  {(l.get('date') or '')[:16]}  ·  {l.get('compte_source', '')}  ·  "
                        f"{l.get('type', '')}  ·  {l.get('likes') or 0} j'aime\n", "doux")
        w.insert("end", l["texte"] + "\n\n")
        titre = (l.get("publication_titre") or "").strip()
        w.insert("end", "Sous la publication : ", "doux")
        w.insert("end", (titre[:500] + ("…" if len(titre) > 500 else "")) if titre else "(sans texte)")
        w.insert("end", f"\n{l.get('publication_lien', '')}\n", "doux")
        etat = "normal" if l.get("publication_lien") else "disabled"
        self.b_lien.config(state=etat)
        self.b_copier.config(state=etat)

    def ouvrir_lien(self):
        if self.choisi and self.choisi.get("publication_lien"):
            webbrowser.open(self.choisi["publication_lien"])

    def copier_lien(self):
        if self.choisi and self.choisi.get("publication_lien"):
            self.app.clipboard_clear()
            self.app.clipboard_append(self.choisi["publication_lien"])
            self.app.message("Lien de la publication copié.")

    # --- Tâches ----------------------------------------------------------------------------------------------

    def classer(self):
        if en_cours(d.TACHE):
            return self.app.message("La modération tourne déjà : voir le journal.")
        lancer_en_fond(["-u", "-m", "moderation", "classer"], sortie=d.JOURNAL)
        self.app.message("Classement des nouveaux commentaires Facebook lancé (quelques secondes à quelques minutes).")

    def reentrainer(self):
        if en_cours(d.TACHE):
            return messagebox.showinfo("Modération", "La modération tourne déjà : attendre sa fin.")
        if en_cours("analyse"):
            return messagebox.showinfo("Modération", "Une analyse est en cours : un seul calcul lourd à la fois, "
                                                     "attendre sa fin.")
        e = (self.res or {}).get("etat") or {}
        i = e.get("modele") or {}
        nouvelles = e.get("annotations", 0) - e.get("test", 0) - i.get("annotations", 0)
        if not messagebox.askyesno(
                "Réentraîner le modèle de modération",
                f"{nombre(max(nouvelles, 0))} annotations nouvelles depuis le modèle {i.get('version', '')}. "
                "Le réentraînement prend une trentaine de minutes, puis tous les commentaires sont reclassés "
                "(encore une demi-heure environ). Le processeur est occupé pendant ce temps. Lancer maintenant ?"):
            return
        lancer_en_fond(["-u", "-m", "moderation", "entrainer"], sortie=d.JOURNAL)
        self.app.message("Réentraînement lancé : suivi dans le journal de la modération.")

    def arreter(self):
        if en_cours(d.TACHE):
            demander_arret(d.TACHE)
            self.app.message("Arrêt demandé : la tâche s'arrête après le lot en cours (ce qui est fait est gardé).")

    def boucle(self):
        """Appelée toutes les 1,5 s par la fenêtre : avancement, rechargement quand la tâche se termine."""
        if en_cours(d.TACHE):
            self._etait_en_cours = True
            a = lire_json(d.AVANCEMENT) or {}
            if a:
                self.c_classes.legende.config(text=f"en cours : {a['tache']} {nombre(a['fait'])}/{nombre(a['total'])}")
        elif self._etait_en_cours:
            self._etait_en_cours = False
            self.recharger()
