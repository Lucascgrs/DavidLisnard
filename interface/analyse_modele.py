"""Sous-onglet « Modèle » : version en service, qualité mesurée sur le jeu de test, apport du réseau affiné,
reproches retrouvés, fiabilité ; réentraînement et option « analyser après chaque collecte »."""
import tkinter as tk
from tkinter import messagebox, ttk

from analyse import stockage
from analyse.criteres import CRITERES, EXPLICATIONS, REPROCHES, TITRES
from commun.config import DOCS
from commun.fichiers import lire_csv, lire_json
from commun.taches import en_cours, lancer_en_fond
from interface.theme import COULEURS, PARTS, Chiffre, Jauge, carte, defilant, nombre, ouvrir, police, puce


def verdict(critere: str, mesure: dict) -> tuple[str, str]:
    """Verdict lisible : corrélation pour la tonalité et la pertinence, équilibre entre reproches retrouvés et
    reproches justes pour les trois autres."""
    if critere in ("tonalite", "pertinence"):
        r = mesure.get("correlation_rang") or 0
        return ("Très bon", "vert") if r >= .75 else ("Bon", "vert") if r >= .6 else \
            ("Moyen", "orange") if r >= .45 else ("Faible", "rouge")
    rappel, precision = mesure.get("reproche_rappel") or 0, mesure.get("reproche_precision") or 0
    f1 = 2 * rappel * precision / (rappel + precision) if rappel + precision else 0
    return ("Bon", "vert") if f1 >= .6 else ("Moyen", "orange") if f1 >= .4 else ("Faible", "rouge")


class OngletModele:
    def __init__(self, page, sous: ttk.Notebook):
        self.page = page
        self.app = page.app
        C = COULEURS
        f = tk.Frame(sous, bg=C["fond"])
        sous.add(f, text="Modèle")
        ext, self.corps = defilant(f)
        ext.pack(fill="both", expand=True)
        b = tk.Frame(f, bg=C["fond"], padx=14, pady=10)
        b.pack(fill="x")
        ttk.Button(b, text="Rapport détaillé", command=lambda: ouvrir(stockage.RAPPORT)).pack(side="left")
        ttk.Button(b, text="Grille d'annotation", command=lambda: ouvrir(DOCS / "GRILLE.md")).pack(side="left", padx=6)
        ttk.Button(b, text="Réentraîner le modèle", command=self.reentrainer).pack(side="left")
        ttk.Button(b, text="Mettre à jour le site", command=self.publier).pack(side="left", padx=6)
        self.v_auto = tk.BooleanVar(value=stockage.reglages()["apres_collecte"])
        ttk.Checkbutton(b, text="Analyser automatiquement les nouveaux commentaires après chaque collecte",
                        variable=self.v_auto, command=lambda: stockage.sauver_reglages(
                            apres_collecte=self.v_auto.get())).pack(side="right")

    def reentrainer(self):
        if en_cours("analyse"):
            messagebox.showinfo("Modèle", "Une analyse est en cours : attendre sa fin.")
            return
        if not messagebox.askyesno("Réentraîner le modèle", "Le réentraînement complet (affinage du modèle de langue "
                                   "puis combinaison) prend 3 à 4 heures et occupe le processeur. Le lancer "
                                   "maintenant ?"):
            return
        lancer_en_fond(["-u", "-m", "analyse.ensemble", "tout"], sortie=stockage.JOURNAL_REENTRAINEMENT,
                       env={"HF_HUB_OFFLINE": "1"})
        self.app.message("Réentraînement lancé (3 à 4 heures, suivi dans donnees/analyse/reentrainement.log). La "
                         "nouvelle version sera utilisée à la prochaine analyse.")

    def publier(self):
        from web import acces
        if not acces.pret_a_publier():
            messagebox.showinfo("Site", "Le site n'est pas encore installé : lancer « python -m web tout » une fois.")
            return
        if en_cours("web"):
            self.app.message("Une publication du site est déjà en cours.")
            return
        lancer_en_fond(["-u", "-m", "web", "publier"], sortie=stockage.ANALYSE / "publication_site.log")
        site = acces.lire().get("site_url", "le site")
        self.app.message(f"Publication lancée : notes et statistiques à jour sur {site} d'ici une minute.")

    def _vider(self):
        for w in self.corps.winfo_children():
            w.destroy()

    def afficher(self):
        self._vider()
        i = self.page.infos_modele
        if not i:
            ext, _ = carte(self.corps, "Le modèle n'est pas encore entraîné",
                           "Les notes s'afficheront dès qu'il le sera ; aucune note n'est inventée en attendant.")
            ext.pack(fill="x", padx=14, pady=10)
            return
        m = i["mesures_test"]
        self._chiffres(i, m)
        self._qualite(m, (lire_json(stockage.CONSTANCE, {}) or {}).get("ecart", {}))
        if "vecteurs_seuls" in m:
            self._apport(m)
        self._reproches(m)
        self._fiabilite(m)

    def _grille(self, inner, colonne_large: int) -> tk.Frame:
        grille = tk.Frame(inner, bg=COULEURS["carte"])
        grille.pack(fill="x")
        grille.columnconfigure(colonne_large, weight=1)
        grille.columnconfigure(0, minsize=230)
        return grille

    def _chiffres(self, i, m):
        C = COULEURS
        ligne = tk.Frame(self.corps, bg=C["fond"])
        ligne.pack(fill="x", padx=14, pady=(12, 8))
        chiffres = [("Modèle en service", i["version"], f"entraîné le {i['le'][8:10]}/{i['le'][5:7]} à {i['le'][11:16]}",
                     C["accent"]),
                    ("Commentaires annotés", nombre(i["annotations"]), f"dont {i['test']} gardés pour mesurer", None),
                    ("Cible juste", f"{100 * m['cible']['exactitude']:.0f} %",
                     "parle-t-il de Lisnard ou d'autre chose ?", None),
                    ("Corrections", str(len(lire_csv(stockage.CORRECTIONS))),
                     "faites dans l'interface, reprises au prochain entraînement", None)]
        for k, (titre, valeur, legende, couleur) in enumerate(chiffres):
            Chiffre(ligne, titre, valeur, legende, couleur).cadre.grid(row=0, column=k, sticky="nsew",
                                                                     padx=(0 if k == 0 else 10, 0))
            ligne.columnconfigure(k, weight=1, uniform="chiffres")

    def _qualite(self, m, constance):
        C = COULEURS
        ext, inner = carte(self.corps, "Qualité des notes",
                           "Mesurée sur des commentaires que le modèle n'a jamais vus. La barre montre de combien de "
                           "points (sur 20) il se trompe en moyenne : plus elle est courte, mieux c'est. Le trait noir "
                           "marque l'écart de l'annotateur lui-même quand il renote les mêmes commentaires, la limite "
                           "qu'un modèle peut espérer atteindre.")
        ext.pack(fill="x", padx=14, pady=6)
        grille = self._grille(inner, 1)
        for r, c in enumerate(CRITERES):
            x = m[c]
            texte_verdict, ton = verdict(c, x)
            etiquette = tk.Frame(grille, bg=C["carte"])
            etiquette.grid(row=r, column=0, sticky="w", pady=7, padx=(0, 16))
            tk.Label(etiquette, text=TITRES[c], font=police(11, True), bg=C["carte"], fg=C["texte"]).pack(anchor="w")
            tk.Label(etiquette, text=EXPLICATIONS[c], font=police(8), bg=C["carte"], fg=C["doux"], wraplength=220,
                     justify="left").pack(anchor="w")
            couleur = {"vert": PARTS["haut"], "orange": "#f0a30a", "rouge": PARTS["bas"]}[ton]
            Jauge(grille, x["ecart_moyen"], 5, couleur, f"{x['ecart_moyen']:.1f} pt".replace(".", ","), hauteur=18,
                  repere=constance.get(c)).grid(row=r, column=1, sticky="ew", pady=7)
            fin = tk.Frame(grille, bg=C["carte"])
            fin.grid(row=r, column=2, sticky="e", padx=(16, 0))
            puce(fin, texte_verdict, ton).pack(side="left")
            if x.get("correlation_rang") is not None:
                tk.Label(fin, text=f"corrélation {x['correlation_rang']:.2f}".replace(".", ","), font=police(8),
                         bg=C["carte"], fg=C["doux"], width=15).pack(side="left", padx=(8, 0))

    def _apport(self, m):
        C = COULEURS
        v = m["vecteurs_seuls"]
        ext, inner = carte(self.corps, "Ce qu'apporte la lecture fine",
                           "Le modèle en service combine deux méthodes : un modèle de langue réentraîné sur les "
                           "annotations, qui lit chaque commentaire avec celui auquel il répond (ironie, "
                           "« exactement », « 😂 » sous un autre avis), et l'ancienne méthode par vecteurs. "
                           "Corrélation avec les notes de l'annotateur, sur le même test.")
        ext.pack(fill="x", padx=14, pady=6)
        grille = self._grille(inner, 2)
        rangs = [(TITRES[c], v[c]["correlation_rang"] or 0, m[c]["correlation_rang"] or 0, "{:.2f}")
                 for c in ("tonalite", "pertinence", "idees")]
        rangs.append(("Cible juste", v["cible"], m["cible"]["exactitude"], "{:.0%}"))
        for r, (nom, avant, apres, fmt) in enumerate(rangs):
            tk.Label(grille, text=nom, font=police(11, True), bg=C["carte"], fg=C["texte"]).grid(
                row=2 * r, column=0, rowspan=2, sticky="w", pady=6)
            for k, (libelle, val, couleur) in enumerate((("vecteurs seuls", avant, C["gris"]),
                                                         ("en service", apres, C["accent"]))):
                tk.Label(grille, text=libelle, font=police(9), bg=C["carte"], fg=C["doux"]).grid(
                    row=2 * r + k, column=1, sticky="w", padx=(0, 10))
                Jauge(grille, val, 1, couleur, fmt.format(val).replace(".", ","), hauteur=16).grid(
                    row=2 * r + k, column=2, sticky="ew", pady=2)
        if m.get("reponses"):
            x = m["reponses"]
            tk.Label(inner, text=f"Sur les {x['n']} réponses du test : écart moyen de "
                                 f"{x['ecart_tonalite']:.1f} point sur la tonalité, cible juste à "
                                 f"{100 * x['cible']:.0f} %.".replace(".", ",", 1),
                     font=police(9), bg=C["carte"], fg=C["doux"]).pack(anchor="w", pady=(6, 0))

    def _reproches(self, m):
        C = COULEURS
        ext, inner = carte(self.corps, "Reproches retrouvés",
                           "Sur les commentaires qui reprochent quelque chose (note ≤ 6) : la part que le modèle "
                           "retrouve, et la part juste parmi ceux qu'il signale.")
        ext.pack(fill="x", padx=14, pady=6)
        grille = self._grille(inner, 2)
        for r, c in enumerate(REPROCHES):
            x = m[c]
            tk.Label(grille, text=f"{TITRES[c]}  ({x['reproche_n']} cas)", font=police(11, True), bg=C["carte"],
                     fg=C["texte"]).grid(row=2 * r, column=0, rowspan=2, sticky="w", pady=6)
            for k, (nom, cle) in enumerate((("retrouvés", "reproche_rappel"), ("justes", "reproche_precision"))):
                v = x.get(cle)
                tk.Label(grille, text=nom, font=police(9), bg=C["carte"], fg=C["doux"]).grid(
                    row=2 * r + k, column=1, sticky="w", padx=(0, 10))
                Jauge(grille, 100 * (v or 0), 100, C["accent"], "—" if v is None else f"{100 * v:.0f} %",
                      hauteur=16).grid(row=2 * r + k, column=2, sticky="ew", pady=2)

    def _fiabilite(self, m):
        C = COULEURS
        ext, inner = carte(self.corps, "Fiabilité affichée pour chaque commentaire",
                           "Elle dit surtout si le modèle est sûr que le commentaire parle de Lisnard.")
        ext.pack(fill="x", padx=14, pady=(6, 14))
        for nom, x in m["fiabilite"].items():
            rang = tk.Frame(inner, bg=C["carte"])
            rang.pack(fill="x", pady=3)
            puce(rang, nom, {"bonne": "vert", "moyenne": "orange", "faible": "rouge"}[nom]).pack(side="left")
            tk.Label(rang, text=f"{100 * x['part']:.0f} % des commentaires · cible fausse dans "
                                f"{100 * (x.get('cible_fausse') or 0):.0f} % des cas · écart moyen sur la tonalité "
                                f"{x.get('ecart_tonalite') or 0:.1f} pt".replace(".", ","),
                     font=police(9), bg=C["carte"], fg=C["texte"]).pack(side="left", padx=10)
