"""Apparence de l'interface : thème Windows 11 (sv_ttk), couleurs, polices et petits composants graphiques.

Composants :
- carte(parent, titre) : un panneau blanc à bord fin, avec un titre ;
- Chiffre : un chiffre clé (petit titre, grand nombre coloré, légende) ;
- Repartition : une barre horizontale découpée en parts colorées (reproche · non évoqué · éloge, par exemple) ;
- puce(parent, texte, ton) : une étiquette colorée (note, verdict) ;
- defilant(parent) : un cadre qui défile à la molette ;
- note(parent, texte) : un paragraphe d'explication en gris ;
- style_graphiques() : réglages matplotlib accordés au thème ;
- nombre(n), ouvrir(chemin) : « 151 480 », ouvrir un fichier ou un dossier avec l'application de Windows.
"""
import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk

COULEURS = {
    "fond": "#fafafa", "carte": "#ffffff", "texte": "#1c1c1c", "doux": "#616161", "pale": "#9e9e9e",
    "bord": "#e5e5e5", "accent": "#005fb8", "accent_pale": "#e6f0fa",
    "rouge": "#d13438", "rouge_pale": "#fde7e9", "vert": "#107c10", "vert_pale": "#dff6dd",
    "orange": "#c25e00", "orange_pale": "#fff4ce", "gris": "#d6d6d6", "gris_pale": "#f0f0f0",
    # États des collectes (tableau de bord)
    "en_cours": "#107c10", "arret": "#c25e00", "probleme": "#d13438", "pret": "#616161",
}
# Parts des barres : reproche / hostile, non évoqué / neutre, éloge / favorable
PARTS = {"bas": "#e5484d", "milieu": "#dcdcdc", "haut": "#30a46c"}

POLICE = "Segoe UI Variable Text"
POLICE_TITRE = "Segoe UI Variable Display"


def police(taille=10, gras=False, titre=False):
    nom = POLICE_TITRE if titre else POLICE
    if not gras:
        return (nom, taille)
    if nom == "Segoe UI":
        return ("Segoe UI Semibold", taille)
    return (nom + (" Semib" if titre else " Semibold"), taille)


def appliquer_theme(racine: tk.Tk):
    """Thème Windows 11 clair ; repli sur le thème « vista » si sv_ttk manque."""
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    try:
        import sv_ttk
        sv_ttk.set_theme("light", racine)
    except Exception:
        s = ttk.Style(racine)
        if "vista" in s.theme_names():
            s.theme_use("vista")
    import tkinter.font as tkfont
    if POLICE not in tkfont.families(racine):
        globals().update(POLICE="Segoe UI", POLICE_TITRE="Segoe UI")
    racine.option_add("*Font", police(10))
    s = ttk.Style(racine)
    s.configure("Treeview", rowheight=30, font=police(10))
    s.configure("Treeview.Heading", font=police(10, True))
    s.configure("TNotebook.Tab", padding=(16, 6))
    s.configure("Titre.TLabel", font=police(18, True, True))
    return s


def carte(parent, titre: str | None = None, sous_titre: str | None = None, pad=16):
    """Panneau blanc à bord fin. Retourne (cadre extérieur, cadre intérieur où placer le contenu)."""
    C = COULEURS
    ext = tk.Frame(parent, bg=C["carte"], highlightthickness=1, highlightbackground=C["bord"])
    inner = tk.Frame(ext, bg=C["carte"], padx=pad, pady=pad - 4)
    inner.pack(fill="both", expand=True)
    if titre:
        tk.Label(inner, text=titre, font=police(12, True, True), bg=C["carte"], fg=C["texte"],
                 anchor="w").pack(fill="x")
    if sous_titre:
        tk.Label(inner, text=sous_titre, font=police(9), bg=C["carte"], fg=C["doux"], anchor="w",
                 justify="left", wraplength=900).pack(fill="x", pady=(0, 8))
    elif titre:
        tk.Frame(inner, bg=C["carte"], height=6).pack()
    return ext, inner


class Chiffre:
    """Chiffre clé : petit titre gris, grand nombre, légende."""

    def __init__(self, parent, titre: str, valeur: str, legende: str = "", couleur: str | None = None):
        C = COULEURS
        self.cadre, inner = carte(parent, pad=14)
        tk.Label(inner, text=titre.upper(), font=police(8, True), bg=C["carte"], fg=C["doux"],
                 anchor="w").pack(fill="x")
        self.valeur = tk.Label(inner, text=valeur, font=police(24, True, True), bg=C["carte"],
                               fg=couleur or C["texte"], anchor="w")
        self.valeur.pack(fill="x")
        self.legende = tk.Label(inner, text=legende, font=police(9), bg=C["carte"], fg=C["doux"], anchor="w",
                                justify="left", wraplength=220)
        self.legende.pack(fill="x")


class Repartition(tk.Canvas):
    """Barre horizontale en parts : [(part 0-1, couleur, texte), …], redessinée à chaque changement de taille."""

    def __init__(self, parent, parts, hauteur=22, bg=None):
        super().__init__(parent, height=hauteur, bg=bg or COULEURS["carte"], highlightthickness=0)
        self.parts, self.h = parts, hauteur
        self.bind("<Configure>", lambda e: self.dessiner())

    def dessiner(self):
        self.delete("all")
        w = max(1, self.winfo_width())
        x = 0.0
        total = sum(p for p, _, _ in self.parts) or 1
        for i, (p, couleur, texte) in enumerate(self.parts):
            larg = w * p / total
            if larg <= 0:
                continue
            self.create_rectangle(x, 0, x + larg, self.h, fill=couleur, outline=self["bg"], width=1)
            if texte and larg > 34:
                clair = couleur in (PARTS["milieu"], COULEURS["gris"], COULEURS["gris_pale"])
                self.create_text(x + larg / 2, self.h / 2, text=texte, font=police(8, True),
                                 fill=COULEURS["texte"] if clair else "#ffffff")
            x += larg


class Jauge(tk.Canvas):
    """Piste 0-max avec une barre remplie et la valeur écrite au bout (pour les pourcentages, les écarts…)."""

    def __init__(self, parent, valeur: float, maximum: float, couleur: str, texte: str = "", hauteur=14,
                 repere: float | None = None, bg=None):
        super().__init__(parent, height=hauteur, bg=bg or COULEURS["carte"], highlightthickness=0)
        self.v, self.m, self.c, self.t, self.h, self.r = valeur, maximum, couleur, texte, hauteur, repere
        self.bind("<Configure>", lambda e: self.dessiner())

    def dessiner(self):
        self.delete("all")
        w = max(1, self.winfo_width() - 56)
        self.create_rectangle(0, 3, w, self.h - 3, fill=COULEURS["gris_pale"], outline="")
        part = max(0.0, min(1.0, self.v / self.m)) if self.m else 0
        self.create_rectangle(0, 3, w * part, self.h - 3, fill=self.c, outline="")
        if self.r is not None:
            xr = w * max(0.0, min(1.0, self.r / self.m))
            self.create_line(xr, 0, xr, self.h, fill=COULEURS["texte"], width=2)
        self.create_text(w + 8, self.h / 2, text=self.t, anchor="w", font=police(9, True), fill=COULEURS["texte"])


def puce(parent, texte: str, ton: str = "neutre", bg=None):
    """Étiquette colorée. ton : rouge, orange, vert, accent ou neutre."""
    C = COULEURS
    fond, encre = {"rouge": (C["rouge_pale"], C["rouge"]), "orange": (C["orange_pale"], C["orange"]),
                   "vert": (C["vert_pale"], C["vert"]), "accent": (C["accent_pale"], C["accent"]),
                   "neutre": (C["gris_pale"], C["doux"])}[ton]
    return tk.Label(parent, text=texte, font=police(9, True), bg=fond, fg=encre, padx=8, pady=1)


def ton_note(critere: str, note) -> str:
    """Couleur d'une note : rouge si hostile ou reproche, vert si favorable ou éloge."""
    if note is None:
        return "neutre"
    if critere == "pertinence":
        return "vert" if note >= 12 else "orange" if note >= 5 else "neutre"
    return "rouge" if note <= 6 else "vert" if note >= 14 else "neutre"


def defilant(parent, bg=None):
    """Cadre défilant verticalement (molette quand la souris est dessus). Retourne (extérieur, intérieur)."""
    bg = bg or COULEURS["fond"]
    ext = tk.Frame(parent, bg=bg)
    toile = tk.Canvas(ext, bg=bg, highlightthickness=0)
    barre = ttk.Scrollbar(ext, command=toile.yview)
    inner = tk.Frame(toile, bg=bg)
    fenetre = toile.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: toile.configure(scrollregion=toile.bbox("all")))
    toile.bind("<Configure>", lambda e: toile.itemconfigure(fenetre, width=e.width))
    toile.configure(yscrollcommand=barre.set)
    barre.pack(side="right", fill="y")
    toile.pack(side="left", fill="both", expand=True)

    def molette(e):
        w = toile.winfo_containing(e.x_root, e.y_root)
        while w is not None and w is not toile:
            w = w.master
        if w is toile:
            toile.yview_scroll(-e.delta // 120, "units")

    toile.bind_all("<MouseWheel>", molette, add="+")
    inner.toile = toile
    return ext, inner


def note(parent, texte: str, bg=None, largeur=900):
    """Paragraphe d'explication en gris, sous un titre ou en haut d'un onglet."""
    lab = tk.Label(parent, text=texte, bg=bg or COULEURS["fond"], fg=COULEURS["doux"], justify="left", anchor="w",
                   wraplength=largeur, font=police(9))
    lab.pack(fill="x", pady=(0, 8))
    return lab


def nombre(n) -> str:
    """151480 → « 151 480 »."""
    return f"{n:,}".replace(",", " ")


def ouvrir(chemin: Path) -> bool:
    """Ouvre un fichier ou un dossier avec l'application de Windows ; False s'il n'existe pas."""
    if Path(chemin).exists():
        os.startfile(chemin)
        return True
    return False


def style_graphiques():
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": COULEURS["bord"],
        "axes.labelcolor": COULEURS["doux"], "axes.titlesize": 10, "axes.titleweight": "bold",
        "axes.titlecolor": COULEURS["texte"], "axes.titlelocation": "left", "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": "#eeeeee", "grid.linewidth": 0.8,
        "xtick.color": COULEURS["doux"], "ytick.color": COULEURS["doux"], "xtick.major.size": 0,
        "ytick.major.size": 0, "legend.frameon": False, "figure.facecolor": COULEURS["carte"],
        "axes.facecolor": COULEURS["carte"]})
