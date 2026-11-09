"""Sous-onglet « Synthèse », sur la sélection filtrée de l'onglet Commentaires : chiffres clés, perception
(critiques · non évoqué · éloges), évolution par mois, comparaison des sources, exemples."""
import tkinter as tk
from collections import defaultdict
from tkinter import ttk

from analyse.criteres import TITRES
from commun.config import SOURCES
from interface.theme import COULEURS, PARTS, Chiffre, Repartition, carte, defilant, nombre, police, puce, ton_note

PERTINENCE_EXPLOITABLE = 5  # en dessous : ironie indécidable, émojis seuls, hors sujet
MOIS_MIN = 30  # un mois de quelques commentaires donnerait des parts au hasard
NOMS_MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def pc(n, total) -> str:
    return f"{100 * n / total:.0f} %" if total else "—"


def parts(lignes, critere) -> tuple[float, float]:
    """Part des notes ≤ 6 (critique, reproche) et ≥ 14 (éloge)."""
    return (sum(1 for l in lignes if l[critere] <= 6) / len(lignes),
            sum(1 for l in lignes if l[critere] >= 14) / len(lignes))


class OngletSynthese:
    def __init__(self, page, sous: ttk.Notebook):
        self.page = page
        self.selection: list[dict] = []
        C = COULEURS
        f = tk.Frame(sous, bg=C["fond"])
        sous.add(f, text="Synthèse")
        haut = tk.Frame(f, bg=C["fond"], padx=14, pady=10)
        haut.pack(fill="x")
        self.resume = tk.Label(haut, text="", font=police(10), bg=C["fond"], fg=C["doux"], anchor="w")
        self.resume.pack(side="left")
        self.v_exploitables = tk.BooleanVar(value=True)
        ttk.Checkbutton(haut, text="Écarter les commentaires inexploitables (pertinence < 5 : ironie indécidable, "
                        "émojis seuls, hors sujet)", variable=self.v_exploitables,
                        command=lambda: self.afficher(self.selection)).pack(side="right")
        ext, self.corps = defilant(f)
        ext.pack(fill="both", expand=True)

    def afficher(self, selection: list[dict]):
        self.selection = selection
        for w in self.corps.winfo_children():
            w.destroy()
        notes = [l for l in selection if l["_note"]]
        ecarter = self.v_exploitables.get()
        base = [l for l in notes if l["pertinence"] >= PERTINENCE_EXPLOITABLE] if ecarter else notes
        texte = f"Sur la sélection de l'onglet Commentaires : {nombre(len(selection))} commentaires, " \
                f"{nombre(len(notes))} analysés"
        if ecarter and notes:
            texte += f", dont {nombre(len(base))} exploitables"
        self.resume.config(text=texte)
        if not base:
            ext, _ = carte(self.corps, "Rien à résumer", "Le modèle n'a pas encore analysé cette sélection, ou les "
                           "filtres ne laissent aucun commentaire noté.")
            ext.pack(fill="x", padx=14, pady=6)
            return
        sur = [l for l in base if l["cible"] != "A"]
        self._chiffres(base, sur, len(selection))
        if sur:
            self._perception(sur)
            self._evolution_et_sources(sur)
            self._exemples(sur)

    def _chiffres(self, base, sur, n):
        C = COULEURS
        ligne = tk.Frame(self.corps, bg=C["fond"])
        ligne.pack(fill="x", padx=14, pady=(2, 8))
        ton = sum(l["tonalite"] for l in sur) / len(sur) if sur else None
        verdict = "—" if ton is None else "plutôt favorable" if ton >= 12 else "plutôt hostile" if ton <= 8 else "partagée"
        fav, host = sum(1 for l in sur if l["tonalite"] >= 14), sum(1 for l in sur if l["tonalite"] <= 6)
        argu = sum(1 for l in base if l["pertinence"] >= 12)
        chiffres = [
            ("Commentaires analysés", nombre(len(base)), f"sur {nombre(n)} dans la sélection", None),
            ("Parlent de Lisnard", pc(len(sur), len(base)), f"{nombre(len(sur))} commentaires", C["accent"]),
            ("Tonalité moyenne", "—" if ton is None else f"{ton:.1f}".replace(".", ",") + " /20", verdict,
             None if ton is None else C["vert"] if ton >= 12 else C["rouge"] if ton <= 8 else C["texte"]),
            ("Favorables", pc(fav, len(sur)), "tonalité de 14 ou plus", C["vert"]),
            ("Hostiles", pc(host, len(sur)), "tonalité de 6 ou moins", C["rouge"]),
            ("Argumentés", pc(argu, len(base)), "donnent au moins une raison (pertinence ≥ 12)", C["texte"]),
        ]
        for i, (titre, valeur, legende, couleur) in enumerate(chiffres):
            Chiffre(ligne, titre, valeur, legende, couleur).cadre.grid(row=0, column=i, sticky="nsew",
                                                                     padx=(0 if i == 0 else 10, 0))
            ligne.columnconfigure(i, weight=1, uniform="chiffres")

    def _perception(self, sur):
        C = COULEURS
        ext, inner = carte(self.corps, "Comment il est perçu",
                           "Part des commentaires qui parlent de lui. En rouge, les critiques ou reproches (note ≤ 6) ; "
                           "en gris, le sujet n'est pas abordé ; en vert, les éloges (note ≥ 14).")
        ext.pack(fill="x", padx=14, pady=6)
        grille = tk.Frame(inner, bg=C["carte"])
        grille.pack(fill="x")
        grille.columnconfigure(1, weight=1)
        grille.columnconfigure(0, minsize=230)
        lignes = [("tonalite", "hostile · neutre · favorable"), ("forme", "élocution, charisme, communication"),
                  ("systeme", "trop proche de Macron, de l'establishment"), ("idees", "son programme, ses positions")]
        for r, (c, explication) in enumerate(lignes):
            bas, haut = parts(sur, c)
            milieu = max(0.0, 1 - bas - haut)
            etiquette = tk.Frame(grille, bg=C["carte"])
            etiquette.grid(row=r, column=0, sticky="w", pady=7, padx=(0, 16))
            tk.Label(etiquette, text=TITRES[c], font=police(11, True), bg=C["carte"], fg=C["texte"]).pack(anchor="w")
            tk.Label(etiquette, text=explication, font=police(8), bg=C["carte"], fg=C["doux"]).pack(anchor="w")
            Repartition(grille, [(bas, PARTS["bas"], f"{100 * bas:.0f} %"),
                                 (milieu, PARTS["milieu"], f"{100 * milieu:.0f} %" if milieu > .12 else ""),
                                 (haut, PARTS["haut"], f"{100 * haut:.0f} %")], hauteur=26).grid(
                row=r, column=1, sticky="ew", pady=7)
            resume = tk.Frame(grille, bg=C["carte"])
            resume.grid(row=r, column=2, sticky="e", padx=(16, 0))
            puce(resume, f"{100 * bas:.0f} % critiques", "rouge").pack(side="left", padx=2)
            puce(resume, f"{100 * haut:.0f} % éloges", "vert").pack(side="left", padx=2)

    def _evolution_et_sources(self, sur):
        C = COULEURS
        rang = tk.Frame(self.corps, bg=C["fond"])
        rang.pack(fill="x", padx=14, pady=6)
        rang.columnconfigure(0, weight=3, uniform="rang")
        rang.columnconfigure(1, weight=2, uniform="rang")
        ext, inner = carte(rang, "Évolution par mois", "Part des commentaires favorables et hostiles ; en fond, le "
                           "nombre de commentaires du mois.")
        ext.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._graphique(inner, sur)
        ext, inner = carte(rang, "Par source", "Tonalité moyenne et répartition hostile · neutre · favorable.")
        ext.grid(row=0, column=1, sticky="nsew")
        par = defaultdict(list)
        for l in sur:
            par[l["source"]].append(l)
        for s, ls in sorted(par.items(), key=lambda x: -len(x[1])):
            bloc = tk.Frame(inner, bg=C["carte"])
            bloc.pack(fill="x", pady=8)
            tete = tk.Frame(bloc, bg=C["carte"])
            tete.pack(fill="x")
            tk.Label(tete, text=SOURCES.get(s, s), font=police(11, True), bg=C["carte"], fg=C["texte"]).pack(side="left")
            tk.Label(tete, text=f"{nombre(len(ls))} commentaires", font=police(9), bg=C["carte"], fg=C["doux"]).pack(
                side="left", padx=8)
            m = sum(l["tonalite"] for l in ls) / len(ls)
            puce(tete, f"{m:.1f} /20".replace(".", ","), "vert" if m >= 12 else "rouge" if m <= 8 else "neutre").pack(
                side="right")
            b, h = parts(ls, "tonalite")
            Repartition(bloc, [(b, PARTS["bas"], f"{100 * b:.0f} %"), (max(0, 1 - b - h), PARTS["milieu"], ""),
                               (h, PARTS["haut"], f"{100 * h:.0f} %")], hauteur=18).pack(fill="x", pady=(4, 0))
            tk.Label(bloc, text=f"reproche « système » : {100 * parts(ls, 'systeme')[0]:.0f} %", font=police(8),
                     bg=C["carte"], fg=C["doux"]).pack(anchor="w")

    def _graphique(self, parent, sur):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        from interface.theme import style_graphiques
        style_graphiques()
        par_mois = defaultdict(list)
        for l in sur:
            if l["date"]:
                par_mois[l["date"][:7]].append(l)
        mois = [m for m in sorted(par_mois) if len(par_mois[m]) >= MOIS_MIN][-18:]
        if not mois:
            return
        fig = Figure(figsize=(6.6, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        ax2 = ax.twinx()
        x = range(len(mois))
        ax2.bar(x, [len(par_mois[m]) for m in mois], color=COULEURS["accent_pale"], width=0.7, zorder=0)
        ax2.set_yticks([])
        ax2.spines[:].set_visible(False)
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
        fav = [100 * parts(par_mois[m], "tonalite")[1] for m in mois]
        hos = [100 * parts(par_mois[m], "tonalite")[0] for m in mois]
        ax.plot(x, fav, color=PARTS["haut"], lw=2.2, marker="o", ms=4, label="favorables")
        ax.plot(x, hos, color=PARTS["bas"], lw=2.2, marker="o", ms=4, label="hostiles")
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
        ax.set_xticks(list(x))
        ax.set_xticklabels([f"{NOMS_MOIS[int(m[5:7]) - 1]}\n{m[2:4]}" if m[5:7] == "01" or i == 0
                            else NOMS_MOIS[int(m[5:7]) - 1] for i, m in enumerate(mois)], fontsize=8)
        ax.legend(loc="upper left", ncol=2, fontsize=8)
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=parent).get_tk_widget().pack(fill="both", expand=True)

    def _exemples(self, sur):
        C = COULEURS
        ext, inner = carte(self.corps, "Exemples", "Les reproches les plus forts sur chaque critère, puis les avis les "
                           "plus argumentés de chaque bord. Le détail de chacun est dans l'onglet Commentaires.")
        ext.pack(fill="x", padx=14, pady=(6, 14))
        colonnes = tk.Frame(inner, bg=C["carte"])
        colonnes.pack(fill="x")
        groupes = [(f"Reproches : {TITRES[c].lower()}",
                    sorted((l for l in sur if l[c] <= 6), key=lambda l, c=c: (l[c], -l["pertinence"]))[:3], c)
                   for c in ("forme", "systeme", "idees")]
        groupes += [("Critiques les plus argumentées",
                     sorted((l for l in sur if l["tonalite"] <= 6), key=lambda l: -l["pertinence"])[:3], "pertinence"),
                    ("Soutiens les plus argumentés",
                     sorted((l for l in sur if l["tonalite"] >= 14), key=lambda l: -l["pertinence"])[:3], "pertinence")]
        for i, (titre, exemples, c) in enumerate(groupes):
            col = tk.Frame(colonnes, bg=C["carte"])
            col.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0, 14), pady=(0, 10))
            colonnes.columnconfigure(i % 3, weight=1, uniform="ex")
            tk.Label(col, text=titre, font=police(10, True), bg=C["carte"], fg=C["texte"]).pack(anchor="w")
            if not exemples:
                tk.Label(col, text="Aucun dans la sélection.", font=police(9), bg=C["carte"], fg=C["pale"]).pack(
                    anchor="w")
            for l in exemples:
                bloc = tk.Frame(col, bg=C["gris_pale"], padx=10, pady=8)
                bloc.pack(fill="x", pady=4)
                tete = tk.Frame(bloc, bg=C["gris_pale"])
                tete.pack(fill="x")
                puce(tete, f"{TITRES[c]} {l[c]}", ton_note(c, l[c])).pack(side="left")
                tk.Label(tete, text=f"{SOURCES.get(l['source'], '')} · {l['date'][:10]}", font=police(8),
                         bg=C["gris_pale"], fg=C["doux"]).pack(side="right")
                t = " ".join(l["texte"].split())
                tk.Label(bloc, text=t if len(t) < 260 else t[:259] + "…", font=police(9), bg=C["gris_pale"],
                         fg=C["texte"], justify="left", anchor="w", wraplength=330).pack(fill="x", pady=(4, 0))
