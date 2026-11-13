"""Onglets de la collecte : tableau de bord (une carte par source), un onglet par source (YouTube, Bluesky, Instagram,
Facebook, X : ce qui est suivi et les réglages, écrits dans config/perimetre.json) et planification.

Lancer une collecte = « python -m collecte <source> » en arrière-plan : elle continue si l'on ferme la fenêtre, et
l'interface la retrouve à la réouverture (verrou donnees/<source>/EN_COURS), y compris si elle a été lancée ailleurs
(planification, terminal). Arrêter = demander un arrêt propre entre deux éléments (fichier donnees/<source>/ARRET) ;
« Forcer l'arrêt » tue le processus si l'arrêt propre tarde.
"""
import re
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from collecte import perimetre as pm
from collecte import planification
from commun.config import DONNEES, SOURCES, perimetre
from commun.fichiers import lire_json
from commun.taches import arret_demande, arreter_de_force, demander_arret, depuis, en_cours, lancer_en_fond
from commun.textes import date_paris, nom_fichier
from interface.theme import COULEURS, defilant, nombre, note, ouvrir, police


def lancer_collecte(source: str, reessayer: bool = False) -> None:
    lancer_en_fond(["-m", "collecte"] + (["--reessayer"] if reessayer else []) + [source])


def forcer_arret(source: str) -> None:
    arreter_de_force(source)


def etat_source(source: str) -> dict:
    return lire_json(DONNEES / source / "etat.json", {}) or {}


def tout_lancer(app) -> None:
    lances = [SOURCES[s] for s, c in app.tableau.cartes.items() if not en_cours(s) and not c.abandonnee]
    for s, c in app.tableau.cartes.items():
        if not en_cours(s) and not c.abandonnee:
            lancer_collecte(s)
    app.message(f"Lancé : {', '.join(lances)}" if lances else "Rien à lancer (tout est déjà en cours).")
    app.apres_action()


def _page(onglets, titre: str) -> tk.Frame:
    f = tk.Frame(onglets, bg=COULEURS["fond"], padx=14, pady=12)
    onglets.add(f, text=titre)
    return f


# --- Tableau de bord -------------------------------------------------------------------------------------------------

class Carte:
    """Le cadre d'une source sur le tableau de bord : état, total, dernier lancement, boutons."""

    def __init__(self, app, parent, source: str):
        self.app, self.source = app, source
        C = COULEURS
        self.cadre = tk.Frame(parent, bg=C["carte"], highlightthickness=1, highlightbackground=C["bord"],
                              padx=18, pady=14)
        haut = tk.Frame(self.cadre, bg=C["carte"])
        haut.pack(fill="x")
        tk.Label(haut, text=SOURCES[source], font=police(15, True, True), bg=C["carte"], fg=C["texte"]).pack(
            side="left")
        self.pastille = tk.Label(haut, text="", font=police(9, True), bg=C["gris_pale"], padx=10, pady=2)
        self.pastille.pack(side="left", padx=12)
        self.total = tk.Label(haut, text="", font=police(15, True, True), bg=C["carte"], fg=C["accent"])
        self.total.pack(side="right")
        self.infos = tk.Label(self.cadre, text="", font=police(9), bg=C["carte"], fg=C["doux"], justify="left",
                              anchor="w", wraplength=820)
        self.infos.pack(fill="x", pady=(4, 8))
        bas = tk.Frame(self.cadre, bg=C["carte"])
        bas.pack(fill="x")
        self.b_lancer = ttk.Button(bas, text="Lancer la collecte", style="Accent.TButton", command=self.lancer)
        self.b_lancer.pack(side="left")
        self.b_arreter = ttk.Button(bas, text="Arrêter", command=self.arreter)
        self.b_arreter.pack(side="left", padx=6)
        self.b_forcer = ttk.Button(bas, text="Forcer l'arrêt", command=self.forcer)
        ttk.Button(bas, text="Dossier", command=lambda: ouvrir(DONNEES / source)).pack(side="right")
        ttk.Button(bas, text="Ouvrir l'Excel", command=self.excel).pack(side="right", padx=6)
        self.abandonnee = False

    def lancer(self):
        if en_cours(self.source):
            return
        lancer_collecte(self.source, reessayer=self.abandonnee)
        self.app.journal_texte(f"--- {SOURCES[self.source]} : collecte lancée depuis l'interface")
        self.app.apres_action()

    def arreter(self):
        if en_cours(self.source):
            demander_arret(self.source)
            self.app.journal_texte(f"--- {SOURCES[self.source]} : arrêt demandé (fin de l'élément en cours)")
            self.app.apres_action()

    def forcer(self):
        if messagebox.askyesno("Forcer l'arrêt", f"Arrêter {SOURCES[self.source]} tout de suite ?\n\nCe qui est "
                               "déjà enregistré est gardé ; l'élément en cours de lecture sera relu au prochain "
                               "lancement."):
            threading.Thread(target=forcer_arret, args=(self.source,), daemon=True).start()
            self.app.journal_texte(f"--- {SOURCES[self.source]} : arrêt forcé")
            self.app.after(1500, self.app.apres_action)

    def excel(self):
        if not ouvrir(DONNEES / self.source / f"{self.source}_tout.xlsx"):
            messagebox.showinfo("Excel", "Pas encore de fichier Excel pour cette source.")

    def maj(self, comptes: dict | None):
        C = COULEURS
        etat = etat_source(self.source)
        pid = en_cours(self.source)
        arret = arret_demande(self.source)
        self.abandonnee = bool(etat.get("abandon")) and not pid
        if pid and arret:
            texte, couleur, fond = "Arrêt demandé…", C["arret"], C["orange_pale"]
        elif pid:
            texte, couleur, fond = f"Collecte en cours (depuis {depuis(self.source)[11:16]})", C["en_cours"], C["vert_pale"]
        elif self.abandonnee:
            texte, couleur, fond = "Abandonnée", C["probleme"], C["rouge_pale"]
        else:
            texte, couleur, fond = "Prête", C["pret"], C["gris_pale"]
        self.pastille.config(text="● " + texte, fg=couleur, bg=fond)
        self.b_lancer.config(text="Réessayer" if self.abandonnee else "Lancer la collecte",
                             state="disabled" if pid else "normal")
        self.b_arreter.config(state="normal" if pid and not arret else "disabled")
        if pid and arret:
            self.b_forcer.pack(side="left")
        else:
            self.b_forcer.pack_forget()
        if comptes is not None:
            unite = "messages" if self.source == "bluesky" else "commentaires"
            self.total.config(text=f"{nombre(comptes[self.source]['total'])} {unite}")
        lignes = []
        d = etat.get("dernier")
        if d:
            lignes.append(f"Dernier lancement : {d['le'][:16]} — {d['statut']}, {d['nouveaux']} nouveaux, {d['duree']}")
            if d.get("message") and d["statut"] != "ok":
                lignes.append(d["message"][:300])
        if self.abandonnee:
            lignes.append(etat["abandon"])
        lignes += self.details(etat)
        self.infos.config(text="\n".join(lignes))

    def details(self, etat: dict) -> list[str]:
        p = perimetre()
        if self.source == "youtube":
            r, er = p.get("youtube", {}).get("recherche") or {}, etat.get("recherche") or {}
            ailleurs = ("" if not r.get("active") else
                        f" Recherche « {p.get('mot_cle', 'Lisnard')} » au-delà des chaînes suivies : "
                        f"{len(er.get('videos', []))} vidéos, arriéré "
                        + ("terminé." if er.get("complet") else f"remonté jusqu'au {(er.get('arriere') or '…')[:10]}."))
            return [f"{len(p.get('youtube', {}).get('chaines', []))} chaînes suivies, "
                    f"{len(etat.get('videos', {}))} vidéos lues. Quota gratuit : environ 4 lancements par jour."
                    + ailleurs]
        if self.source == "bluesky":
            er = etat.get("recherche") or {}
            return [f"Messages publics qui citent « {p.get('mot_cle', 'Lisnard')} » et leurs réponses, par l'API "
                    "ouverte de Bluesky (sans compte). Arriéré "
                    + ("terminé." if er.get("complet") else f"remonté jusqu'au {(er.get('arriere') or '…')[:10]}.")
                    + (f" Plus {len(p['bluesky']['comptes'])} compte(s) suivi(s) en entier (onglet Bluesky)."
                       if (p.get("bluesky") or {}).get("comptes") else "")]
        if self.source == "instagram":
            conf = p.get("instagram", {})
            sortie = []
            for pseudo in conf.get("comptes", []):
                a = pm.avancement_instagram(conf, etat, pseudo)
                sortie.append(f"@{pseudo} : {a['posts']} posts{'' if a['complete'] else ' (liste en cours)'}, "
                              f"{a['jamais_lus']} jamais lus, {conf.get('posts_par_lancement', 20)} lus par lancement")
            return sortie or ["Aucun compte suivi : en ajouter dans l'onglet Instagram."]
        if self.source == "facebook":
            conf, sortie = p.get("facebook", {}), []
            for g in conf.get("groupes", []) + conf.get("pages", []):
                e = (etat.get("groupes") or {}).get(str(g["id"]), {})
                f = e.get("frontiere") or {}
                arriere = ("terminé" if e.get("complet") else
                           f"remonté jusqu'au {date_paris(f['date'])[:10]}" if f.get("date") else "pas commencé")
                sortie.append(f"{g['nom']} : arriéré {arriere} (jusqu'au {conf.get('depuis', '?')})")
            jour = etat.get("jour") or {}
            sortie.append(f"Groupes publics et Page officielle lus avec le compte de collecte, sans navigateur : "
                          f"{jour.get('requetes', 0) if jour.get('date') == datetime.now().strftime('%Y-%m-%d') else 0}"
                          f" requêtes aujourd'hui sur {conf.get('requetes_par_jour', 6000)}, "
                          f"{conf.get('minutes_par_lancement', 120)} min au plus par lancement.")
            if etat.get("repos_jusqua"):
                sortie.append(f"Au repos jusqu'au {etat['repos_jusqua'].replace('T', ' ')[:16]} (Facebook a freiné).")
            return sortie or ["Aucun groupe ni Page suivis : en ajouter dans l'onglet Facebook."]
        if self.source == "x":
            from collecte.sources.x import date_de
            conf, sortie = p.get("x", {}), []
            req = etat.get("requetes") or {}
            for c in conf.get("comptes", []) + ([None] if conf.get("recherche", True) else []):
                e = req.get(f"@{c['pseudo']}" if c else "recherche", {})
                arriere = ("terminé" if e.get("complet") else
                           f"remonté jusqu'au {date_de(e['bas']):%Y-%m-%d}" if e.get("bas") else "pas commencé")
                nom = f"@{c['pseudo']}" if c else f"Recherche « {p.get('mot_cle', 'Lisnard')} »"
                sortie.append(f"{nom} : arriéré {arriere} (jusqu'au {conf.get('depuis', '?')})")
            jour = etat.get("jour") or {}
            sortie.append(f"Posts et réponses lus avec le compte de collecte, sans navigateur : "
                          f"{jour.get('requetes', 0) if jour.get('date') == datetime.now().strftime('%Y-%m-%d') else 0}"
                          f" requêtes aujourd'hui sur {conf.get('requetes_par_jour', 3000)}, au plus "
                          f"{conf.get('recherches_par_quart_heure', 40)} par quart d'heure et "
                          f"{conf.get('minutes_par_lancement', 120)} min par lancement.")
            if etat.get("repos_jusqua"):
                sortie.append(f"Au repos jusqu'au {etat['repos_jusqua'].replace('T', ' ')[:16]} (X a freiné).")
            return sortie
        return []


class PageTableau:
    def __init__(self, app, onglets):
        f = _page(onglets, "Tableau de bord")
        self.cartes = {}
        # Cinq sources ne tiennent plus en hauteur (2026-11-13, avec X) : les cartes défilent, le journal reste en bas.
        bas = tk.Frame(f, bg=COULEURS["fond"])
        bas.pack(side="bottom", fill="x", pady=(6, 0))
        ext, cartes = defilant(f)
        ext.pack(fill="both", expand=True)
        for source in SOURCES:
            c = Carte(app, cartes, source)
            c.cadre.pack(fill="x", pady=(0, 10), padx=(0, 6))
            self.cartes[source] = c
        tk.Label(bas, text="Journal en direct", font=police(10, True), bg=COULEURS["fond"],
                 fg=COULEURS["texte"]).pack(anchor="w")
        cadre = tk.Frame(bas, bg=COULEURS["bord"])
        cadre.pack(fill="x")
        self.journal = tk.Text(cadre, height=8, font=("Cascadia Mono", 9), wrap="word", relief="flat",
                               bg=COULEURS["carte"], fg=COULEURS["doux"], state="disabled", padx=10, pady=8)
        barre = ttk.Scrollbar(cadre, command=self.journal.yview)
        self.journal.config(yscrollcommand=barre.set)
        barre.pack(side="right", fill="y")
        self.journal.pack(side="left", fill="both", expand=True, padx=1, pady=1)

    def ecrire_journal(self, texte: str, lignes_max: int = 3000):
        bas = self.journal.yview()[1] > 0.98  # on ne fait défiler que si l'on était déjà en bas
        self.journal.config(state="normal")
        self.journal.insert("end", texte.rstrip("\n") + "\n")
        n = int(self.journal.index("end-1c").split(".")[0])
        if n > lignes_max:
            self.journal.delete("1.0", f"{n - lignes_max}.0")
        self.journal.config(state="disabled")
        if bas:
            self.journal.see("end")

    def maj(self, comptes):
        for c in self.cartes.values():
            c.maj(comptes)


# --- YouTube ---------------------------------------------------------------------------------------------------------

class PageYoutube:
    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "YouTube")
        fond = COULEURS["fond"]
        note(f, "Les chaînes suivies. « Toutes les vidéos » : chaînes de David Lisnard et de ses soutiens. "
                "« Vidéos qui citent le mot-clé » : médias et commentateurs, seules les vidéos dont le titre "
                "ou la description contient le mot-clé sont prises. Retirer une chaîne arrête son suivi ; ses "
                "commentaires déjà collectés restent dans les fichiers. Les changements comptent dès le "
                "prochain lancement. « Chercher aussi ailleurs » : la recherche du mot-clé dans tout YouTube "
                "ramène les vidéos des autres chaînes (dernière ligne du tableau, environ 100 unités de quota "
                "par page de 50 vidéos).")
        reglages = tk.Frame(f, bg=fond)
        reglages.pack(fill="x", pady=(0, 8))
        tk.Label(reglages, text="Mot-clé :", bg=fond).pack(side="left")
        self.v_mot = tk.StringVar(value=perimetre().get("mot_cle", "Lisnard"))
        ttk.Entry(reglages, textvariable=self.v_mot, width=18).pack(side="left", padx=(4, 16))
        tk.Label(reglages, text="Relire une vidéo de moins de (jours) :", bg=fond).pack(side="left")
        self.v_jours = tk.StringVar(value=str(perimetre().get("youtube", {}).get("relire_si_moins_de_jours", 30)))
        ttk.Spinbox(reglages, from_=0, to=365, textvariable=self.v_jours, width=5).pack(side="left", padx=4)
        self.v_ailleurs = tk.BooleanVar(value=bool((perimetre().get("youtube", {}).get("recherche") or {}).get(
            "active")))
        ttk.Checkbutton(reglages, text="Chercher aussi ailleurs que sur les chaînes suivies",
                        variable=self.v_ailleurs).pack(side="left", padx=(16, 0))
        ttk.Button(reglages, text="Enregistrer", command=self.sauver_reglages).pack(side="left", padx=10)

        cadre = tk.Frame(f, bg=fond)
        cadre.pack(fill="both", expand=True)
        self.table = ttk.Treeview(cadre, columns=("nom", "regle", "groupe", "id", "commentaires"), show="headings",
                                  selectmode="extended")
        for c, titre, larg in [("nom", "Chaîne", 260), ("regle", "Vidéos prises", 210), ("groupe", "Groupe", 110),
                               ("id", "Identifiant", 220), ("commentaires", "Commentaires", 110)]:
            self.table.heading(c, text=titre)
            self.table.column(c, width=larg, anchor="e" if c == "commentaires" else "w")
        sb = ttk.Scrollbar(cadre, command=self.table.yview)
        self.table.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)

        ajout = tk.LabelFrame(f, text=" Ajouter une chaîne ", bg=fond, padx=10, pady=8)
        ajout.pack(fill="x", pady=(10, 0))
        tk.Label(ajout, text="Lien, @pseudo ou identifiant :", bg=fond).grid(row=0, column=0, sticky="w")
        self.v_saisie = tk.StringVar()
        e = ttk.Entry(ajout, textvariable=self.v_saisie, width=42)
        e.grid(row=0, column=1, padx=6, sticky="we")
        e.bind("<Return>", lambda _: self.ajouter())
        self.v_regle = tk.StringVar(value=pm.REGLES["mention"])
        ttk.Combobox(ajout, textvariable=self.v_regle, values=list(pm.REGLES.values()), state="readonly",
                     width=26).grid(row=0, column=2, padx=6)
        self.v_groupe = tk.StringVar(value="media")
        ttk.Combobox(ajout, textvariable=self.v_groupe, values=pm.GROUPES, width=13).grid(row=0, column=3, padx=6)
        ttk.Button(ajout, text="Ajouter", style="Accent.TButton", command=self.ajouter).grid(row=0, column=4, padx=6)
        ajout.columnconfigure(1, weight=1)

        actions = tk.Frame(f, bg=fond)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Retirer la sélection", command=self.retirer).pack(side="left")
        ttk.Button(actions, text="Changer la règle de la sélection", command=self.changer_regle).pack(
            side="left", padx=6)
        self.remplir()

    def remplir(self):
        selection = set(self.table.selection())
        self.table.delete(*self.table.get_children())
        par_fichier = (self.app.comptes or {}).get("youtube", {}).get("par_fichier", {})
        for c in perimetre().get("youtube", {}).get("chaines", []):
            n = par_fichier.get(nom_fichier(c["nom"]))
            self.table.insert("", "end", iid=c["id"], values=(
                c["nom"], pm.REGLES.get(c["regle"], c["regle"]), c.get("groupe", ""), c["id"],
                "" if n is None else nombre(n)))
        n = par_fichier.get("autres_chaines")  # collecte/sources/youtube.py, FICHIER_RECHERCHE
        if n is not None or self.v_ailleurs.get():
            self.table.insert("", "end", iid="autres_chaines", values=(
                "Autres chaînes (trouvées par la recherche)", pm.REGLES["mention"], "autre", "",
                "" if n is None else nombre(n)))
        for iid in selection:
            if self.table.exists(iid):
                self.table.selection_add(iid)

    def sauver_reglages(self):
        try:
            jours = int(self.v_jours.get())
        except ValueError:
            messagebox.showerror("YouTube", "Le nombre de jours doit être un nombre entier.")
            return
        mot = self.v_mot.get().strip()
        if not mot:
            messagebox.showerror("YouTube", "Le mot-clé ne peut pas être vide.")
            return
        p = perimetre()
        p["mot_cle"] = mot
        p.setdefault("youtube", {})["relire_si_moins_de_jours"] = jours
        p["youtube"]["recherche"] = {"depuis": "2025-01-01", "pages_par_lancement": 5,
                                     **(p["youtube"].get("recherche") or {}), "active": self.v_ailleurs.get()}
        pm.sauver(p)
        self.app.message("Réglages YouTube enregistrés.")

    def ajouter(self):
        saisie = self.v_saisie.get().strip()
        if not saisie:
            return
        self.app.config(cursor="watch")
        self.app.update_idletasks()
        try:
            cid, nom = pm.trouver_chaine(saisie)
        except Exception as e:
            messagebox.showerror("Ajouter une chaîne", str(e))
            return
        finally:
            self.app.config(cursor="")
        p = perimetre()
        chaines = p.setdefault("youtube", {}).setdefault("chaines", [])
        if any(c["id"] == cid for c in chaines):
            messagebox.showinfo("Ajouter une chaîne", f"« {nom} » est déjà suivie.")
            return
        if any(nom_fichier(c["nom"]) == nom_fichier(nom) for c in chaines):
            nom = f"{nom} ({cid[-6:]})"  # deux chaînes du même nom : fichiers séparés
        regle = next(k for k, v in pm.REGLES.items() if v == self.v_regle.get())
        if not messagebox.askyesno("Ajouter une chaîne", f"Suivre « {nom} » ({cid}) ?\n\nVidéos prises : "
                                   f"{pm.REGLES[regle]}."):
            return
        chaines.append({"nom": nom, "id": cid, "regle": regle, "groupe": self.v_groupe.get().strip() or "autre"})
        pm.sauver(p)
        self.v_saisie.set("")
        self.remplir()
        self.app.message(f"Chaîne ajoutée : {nom}. Elle sera lue au prochain lancement de YouTube.")

    def retirer(self):
        ids = [i for i in self.table.selection() if i != "autres_chaines"]
        if not ids:
            return
        p = perimetre()
        noms = [c["nom"] for c in p["youtube"]["chaines"] if c["id"] in ids]
        if not messagebox.askyesno("Retirer", "Ne plus suivre :\n\n" + "\n".join(noms) +
                                   "\n\nLes commentaires déjà collectés restent dans les fichiers."):
            return
        p["youtube"]["chaines"] = [c for c in p["youtube"]["chaines"] if c["id"] not in ids]
        pm.sauver(p)
        self.remplir()
        self.app.message(f"{len(noms)} chaîne(s) retirée(s).")

    def changer_regle(self):
        ids = self.table.selection()
        if not ids:
            return
        p = perimetre()
        for c in p["youtube"]["chaines"]:
            if c["id"] in ids:
                c["regle"] = "mention" if c["regle"] == "toutes" else "toutes"
        pm.sauver(p)
        self.remplir()
        self.app.message("Règle changée.")


# --- Instagram -------------------------------------------------------------------------------------------------------

class PageInstagram:
    REGLAGES = [("depuis", "Posts publiés depuis le (AAAA-MM-JJ)", "2025-01-01"),
                ("posts_par_lancement", "Posts lus au plus par lancement", 50),
                ("relire_si_moins_de_jours", "Relire un post de moins de (jours)", 21),
                ("abandon_si_10_posts_depassent_minutes", "Abandon si 10 posts dépassent (minutes)", 30)]

    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "Instagram")
        fond = COULEURS["fond"]
        note(f, "Les comptes dont on lit les posts. Les posts jamais lus passent d'abord (du plus récent au plus "
                "ancien) ; ensuite, seuls les posts récents qui ont gagné des commentaires sont relus. Lu avec le "
                "compte dédié (sessions/cookies_web.json). La source s'arrête d'elle-même si Instagram bloque.")
        reglages = tk.LabelFrame(f, text=" Réglages ", bg=fond, padx=10, pady=8)
        reglages.pack(fill="x", pady=(0, 10))
        conf = perimetre().get("instagram", {})
        self.v = {}
        for i, (cle, texte, defaut) in enumerate(self.REGLAGES):
            tk.Label(reglages, text=texte + " :", bg=fond).grid(row=i // 2, column=(i % 2) * 2, sticky="w", pady=2)
            v = tk.StringVar(value=str(conf.get(cle, defaut)))
            ttk.Entry(reglages, textvariable=v, width=12).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w",
                                                              padx=(6, 24), pady=2)
            self.v[cle] = v
        ttk.Button(reglages, text="Enregistrer", command=self.sauver_reglages).grid(row=0, column=4, rowspan=2, padx=8)

        cadre = tk.Frame(f, bg=fond)
        cadre.pack(fill="both", expand=True)
        self.table = ttk.Treeview(cadre, columns=("compte", "posts", "lus", "commentaires"), show="headings")
        for c, titre, larg in [("compte", "Compte", 260), ("posts", "Posts dans la période", 170),
                               ("lus", "Posts lus", 120), ("commentaires", "Commentaires", 120)]:
            self.table.heading(c, text=titre)
            self.table.column(c, width=larg, anchor="w" if c == "compte" else "e")
        self.table.pack(fill="both", expand=True)

        ajout = tk.Frame(f, bg=fond)
        ajout.pack(fill="x", pady=(10, 0))
        tk.Label(ajout, text="Pseudo ou lien du compte :", bg=fond).pack(side="left")
        self.v_saisie = tk.StringVar()
        e = ttk.Entry(ajout, textvariable=self.v_saisie, width=36)
        e.pack(side="left", padx=6)
        e.bind("<Return>", lambda _: self.ajouter())
        ttk.Button(ajout, text="Ajouter", style="Accent.TButton", command=self.ajouter).pack(side="left")
        ttk.Button(ajout, text="Retirer la sélection", command=self.retirer).pack(side="left", padx=12)
        self.remplir()

    def remplir(self):
        conf = perimetre().get("instagram", {})
        etat = etat_source("instagram")
        par_fichier = (self.app.comptes or {}).get("instagram", {}).get("par_fichier", {})
        self.table.delete(*self.table.get_children())
        for pseudo in conf.get("comptes", []):
            a = pm.avancement_instagram(conf, etat, pseudo)
            n = par_fichier.get(nom_fichier(f"@{pseudo}"))
            self.table.insert("", "end", iid=pseudo, values=(
                f"@{pseudo}", a["posts"] if a["liste"] else "pas encore listé", a["lus"],
                "" if n is None else nombre(n)))

    def sauver_reglages(self):
        from datetime import datetime
        p = perimetre()
        conf = p.setdefault("instagram", {})
        try:
            datetime.fromisoformat(self.v["depuis"].get().strip())
            valeurs = {k: int(v.get()) for k, v in self.v.items() if k != "depuis"}
        except ValueError:
            messagebox.showerror("Instagram", "Date au format AAAA-MM-JJ et nombres entiers attendus.")
            return
        conf["depuis"] = self.v["depuis"].get().strip()
        conf.update(valeurs)
        pm.sauver(p)
        self.remplir()
        self.app.message("Réglages Instagram enregistrés (pris en compte au prochain lancement).")

    def ajouter(self):
        try:
            pseudo = pm.pseudo_instagram(self.v_saisie.get())
        except ValueError as e:
            messagebox.showerror("Instagram", str(e))
            return
        p = perimetre()
        comptes = p.setdefault("instagram", {}).setdefault("comptes", [])
        if pseudo in comptes:
            messagebox.showinfo("Instagram", f"@{pseudo} est déjà suivi.")
            return
        comptes.append(pseudo)
        pm.sauver(p)
        self.v_saisie.set("")
        self.remplir()
        self.app.message(f"@{pseudo} ajouté : ses posts seront listés au prochain lancement d'Instagram.")

    def retirer(self):
        sel = self.table.selection()
        if not sel or not messagebox.askyesno(
                "Retirer", "Ne plus suivre : " + ", ".join("@" + s for s in sel) +
                " ?\n\nLes commentaires déjà collectés restent dans les fichiers."):
            return
        p = perimetre()
        p["instagram"]["comptes"] = [c for c in p["instagram"]["comptes"] if c not in sel]
        pm.sauver(p)
        self.remplir()


# --- Réglages communs aux onglets Bluesky, Facebook et X ----------------------------------------------------------------

def _reglages(page, f, source: str, reglages: list[tuple[str, str, object]]):
    """Cadre « Réglages » : une case par réglage (clé de perimetre.json, libellé, valeur par défaut)."""
    fond = COULEURS["fond"]
    cadre = tk.LabelFrame(f, text=" Réglages ", bg=fond, padx=10, pady=8)
    cadre.pack(fill="x", pady=(0, 10))
    conf = perimetre().get(source, {})
    page.v = {}
    for i, (cle, texte, defaut) in enumerate(reglages):
        tk.Label(cadre, text=texte + " :", bg=fond).grid(row=i // 2, column=(i % 2) * 2, sticky="w", pady=2)
        v = tk.StringVar(value=str(conf.get(cle, defaut)))
        ttk.Entry(cadre, textvariable=v, width=12).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w",
                                                        padx=(6, 24), pady=2)
        page.v[cle] = v
    ttk.Button(cadre, text="Enregistrer", command=page.sauver_reglages).grid(row=0, column=4, rowspan=2, padx=8)


def _sauver_reglages(page, source: str, titre: str) -> bool:
    try:
        datetime.fromisoformat(page.v["depuis"].get().strip())
        valeurs = {k: int(v.get()) for k, v in page.v.items() if k != "depuis"}
    except ValueError:
        messagebox.showerror(titre, "Date au format AAAA-MM-JJ et nombres entiers attendus.")
        return False
    if any(n < 0 for n in valeurs.values()):
        messagebox.showerror(titre, "Les nombres doivent être positifs.")
        return False
    p = perimetre()
    conf = p.setdefault(source, {})
    conf["depuis"] = page.v["depuis"].get().strip()
    conf.update(valeurs)
    pm.sauver(p)
    page.remplir()
    page.app.message(f"Réglages {titre} enregistrés (pris en compte au prochain lancement).")
    return True


def _table(f, colonnes: list[tuple[str, str, int]], gauche=("nom",)) -> ttk.Treeview:
    cadre = tk.Frame(f, bg=COULEURS["fond"])
    cadre.pack(fill="both", expand=True)
    table = ttk.Treeview(cadre, columns=[c for c, _, _ in colonnes], show="headings", selectmode="extended",
                         height=6)  # hauteur demandée : la table s'étire, mais laisse leur place aux boutons dessous
    for c, titre, larg in colonnes:
        table.heading(c, text=titre)
        table.column(c, width=larg, anchor="w" if c in gauche else "e")
    sb = ttk.Scrollbar(cadre, command=table.yview)
    table.config(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)
    return table


def _ajout(page, f, titre: str, libelle: str, groupe_defaut: str):
    """Cadre d'ajout (saisie, groupe, bouton) et boutons d'action sous la table."""
    fond = COULEURS["fond"]
    ajout = tk.LabelFrame(f, text=f" {titre} ", bg=fond, padx=10, pady=8)
    ajout.pack(fill="x", pady=(10, 0))
    tk.Label(ajout, text=libelle, bg=fond).grid(row=0, column=0, sticky="w")
    page.v_saisie = tk.StringVar()
    e = ttk.Entry(ajout, textvariable=page.v_saisie, width=48)
    e.grid(row=0, column=1, padx=6, sticky="we")
    e.bind("<Return>", lambda _: page.ajouter())
    tk.Label(ajout, text="Groupe :", bg=fond).grid(row=0, column=2, padx=(10, 0))
    page.v_groupe = tk.StringVar(value=groupe_defaut)
    ttk.Combobox(ajout, textvariable=page.v_groupe, values=pm.GROUPES, width=13).grid(row=0, column=3, padx=6)
    ttk.Button(ajout, text="Ajouter", style="Accent.TButton", command=page.ajouter).grid(row=0, column=4, padx=6)
    ajout.columnconfigure(1, weight=1)
    actions = tk.Frame(f, bg=fond)
    actions.pack(fill="x", pady=(8, 0))
    ttk.Button(actions, text="Retirer la sélection", command=page.retirer).pack(side="left")
    ttk.Button(actions, text="Donner le groupe choisi à la sélection", command=page.changer_groupe).pack(
        side="left", padx=6)


def _garder_selection(table, avant):
    for iid in avant:
        if table.exists(iid):
            table.selection_add(iid)


def _arriere(e: dict, date: str | None) -> str:
    if e.get("complet"):
        return "terminé"
    return f"jusqu'au {date_paris(date)[:10]}" if date else "pas commencé"


# --- Bluesky ---------------------------------------------------------------------------------------------------------

class PageBluesky:
    REGLAGES = [("depuis", "Messages publiés depuis le (AAAA-MM-JJ)", "2025-01-01"),
                ("pages_par_lancement", "Pages de 100 messages au plus par lancement", 60),
                ("relire_si_moins_de_jours", "Relire un message de moins de (jours)", 7)]

    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "Bluesky")
        note(f, "Deux façons de prendre des messages, par l'API ouverte de Bluesky (sans compte). La recherche : "
                "tous les messages publics qui citent le mot-clé (réglé dans l'onglet YouTube), et leurs réponses. "
                "Les comptes suivis : tous les messages publiés par ces comptes, qu'ils citent le mot-clé ou non, "
                "et toutes leurs réponses (un fichier par compte). Retirer un compte arrête son suivi ; ses messages "
                "déjà collectés restent dans les fichiers. Les changements comptent dès le prochain lancement.")
        _reglages(self, f, "bluesky", self.REGLAGES)
        self.table = _table(f, [("nom", "Compte", 300), ("pseudo", "Pseudo", 220), ("groupe", "Groupe", 110),
                                ("arriere", "Arriéré", 150), ("messages", "Messages", 110)],
                            gauche=("nom", "pseudo", "groupe"))
        _ajout(self, f, "Suivre un compte", "Pseudo (x.bsky.social) ou lien du profil :", "autre")
        self.remplir()

    def remplir(self):
        avant = set(self.table.selection())
        self.table.delete(*self.table.get_children())
        p = perimetre()
        conf, etat = p.get("bluesky", {}), etat_source("bluesky")
        par_fichier = (self.app.comptes or {}).get("bluesky", {}).get("par_fichier", {})
        mot = p.get("mot_cle", "Lisnard")
        n = par_fichier.get(nom_fichier(f"Recherche « {mot} »"))  # collecte/sources/bluesky.py, nom_compte
        er = etat.get("recherche") or {}
        self.table.insert("", "end", iid="recherche", values=(
            f"Recherche « {mot} » (tout Bluesky)", "", "autre", _arriere(er, er.get("arriere")),
            "" if n is None else nombre(n)))
        for c in conf.get("comptes", []):
            n = par_fichier.get(nom_fichier(f"@{c['handle']}"))  # collecte/sources/bluesky.py, nom_compte_suivi
            e = (etat.get("comptes") or {}).get(c["did"], {})
            self.table.insert("", "end", iid=c["did"], values=(
                c.get("nom") or c["handle"], f"@{c['handle']}", c.get("groupe", "autre"),
                _arriere(e, e.get("arriere")), "" if n is None else nombre(n)))
        _garder_selection(self.table, avant)

    def sauver_reglages(self):
        _sauver_reglages(self, "bluesky", "Bluesky")

    def ajouter(self):
        if not self.v_saisie.get().strip():
            return
        self.app.config(cursor="watch")
        self.app.update_idletasks()
        try:
            c = pm.trouver_bluesky(self.v_saisie.get())
        except Exception as e:
            messagebox.showerror("Bluesky", str(e))
            return
        finally:
            self.app.config(cursor="")
        p = perimetre()
        conf = p.setdefault("bluesky", {})
        comptes = conf.setdefault("comptes", [])
        if any(x["did"] == c["did"] for x in comptes):
            messagebox.showinfo("Bluesky", f"@{c['handle']} est déjà suivi.")
            return
        if not messagebox.askyesno("Bluesky", f"Suivre « {c['nom']} » (@{c['handle']}) ?\n\nTous ses messages depuis "
                                   f"le {conf.get('depuis', '2025-01-01')} et leurs réponses seront pris."):
            return
        comptes.append({**c, "groupe": self.v_groupe.get().strip() or "autre"})
        pm.sauver(p)
        self.v_saisie.set("")
        self.remplir()
        self.app.message(f"@{c['handle']} ajouté : ses messages seront lus au prochain lancement de Bluesky.")

    def retirer(self):
        ids = [i for i in self.table.selection() if i != "recherche"]
        if not ids:
            if self.table.selection():
                messagebox.showinfo("Bluesky", "La recherche du mot-clé ne se retire pas : décocher Bluesky dans "
                                    "la planification pour ne plus rien collecter.")
            return
        p = perimetre()
        noms = [f"@{c['handle']}" for c in p["bluesky"]["comptes"] if c["did"] in ids]
        if not messagebox.askyesno("Retirer", "Ne plus suivre :\n\n" + "\n".join(noms) +
                                   "\n\nLes messages déjà collectés restent dans les fichiers."):
            return
        p["bluesky"]["comptes"] = [c for c in p["bluesky"]["comptes"] if c["did"] not in ids]
        pm.sauver(p)
        self.remplir()
        self.app.message(f"{len(noms)} compte(s) Bluesky retiré(s).")

    def changer_groupe(self):
        ids = [i for i in self.table.selection() if i != "recherche"]
        if not ids:
            return
        p = perimetre()
        for c in p["bluesky"]["comptes"]:
            if c["did"] in ids:
                c["groupe"] = self.v_groupe.get().strip() or "autre"
        pm.sauver(p)
        self.remplir()
        self.app.message(f"Groupe « {self.v_groupe.get()} » donné à la sélection (compté à la prochaine analyse).")


# --- Facebook --------------------------------------------------------------------------------------------------------

class PageFacebook:
    REGLAGES = [("depuis", "Posts publiés depuis le (AAAA-MM-JJ)", "2026-07-31"),
                ("relire_si_moins_de_jours", "Relire un post de moins de (jours)", 7),
                ("minutes_par_lancement", "Durée au plus d'un lancement (minutes)", 120),
                ("requetes_par_jour", "Requêtes au plus par jour", 6000)]

    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "Facebook")
        note(f, "Les groupes publics et les Pages dont on lit les posts et tous les commentaires, avec le compte de "
                "collecte (config/facebook.env), sans navigateur. À chaque lancement, le récent de chaque groupe "
                "passe d'abord, puis l'arriéré remonte jusqu'à la date « depuis ». Ajouter : coller le lien du "
                "groupe ou de la Page (l'identifiant et le nom sont lus sur Facebook). Un groupe privé n'est pas "
                "pris : son contenu n'est pas public. Retirer arrête le suivi ; les commentaires déjà collectés "
                "restent dans les fichiers. Rythme prudent pour ne pas faire bloquer le compte : pauses entre les "
                "requêtes, et 3 h de repos si Facebook freine.")
        _reglages(self, f, "facebook", self.REGLAGES)
        self.table = _table(f, [("nom", "Groupe ou Page", 320), ("type", "Type", 80), ("groupe", "Groupe", 100),
                                ("id", "Identifiant", 150), ("arriere", "Arriéré", 150),
                                ("commentaires", "Commentaires", 110)], gauche=("nom", "type", "groupe", "id"))
        _ajout(self, f, "Ajouter un groupe ou une Page", "Lien du groupe ou de la Page :", "soutien")
        self.remplir()

    @staticmethod
    def _tous(conf: dict) -> list[tuple[str, dict]]:
        return [("groupes", g) for g in conf.get("groupes", [])] + [("pages", g) for g in conf.get("pages", [])]

    def remplir(self):
        avant = set(self.table.selection())
        self.table.delete(*self.table.get_children())
        conf, etat = perimetre().get("facebook", {}), etat_source("facebook")
        par_fichier = (self.app.comptes or {}).get("facebook", {}).get("par_fichier", {})
        for rubrique, g in self._tous(conf):
            e = (etat.get("groupes") or {}).get(str(g["id"]), {})
            n = par_fichier.get(nom_fichier(g["nom"]))
            self.table.insert("", "end", iid=str(g["id"]), values=(
                g["nom"], "groupe" if rubrique == "groupes" else "Page", g.get("groupe", ""), g["id"],
                _arriere(e, (e.get("frontiere") or {}).get("date")), "" if n is None else nombre(n)))
        _garder_selection(self.table, avant)

    def sauver_reglages(self):
        _sauver_reglages(self, "facebook", "Facebook")

    def ajouter(self):
        if not self.v_saisie.get().strip():
            return
        self.app.config(cursor="watch")
        self.app.update_idletasks()
        try:
            t = pm.trouver_facebook(self.v_saisie.get())
        except Exception as e:
            messagebox.showerror("Facebook", str(e))
            return
        finally:
            self.app.config(cursor="")
        p = perimetre()
        conf = p.setdefault("facebook", {})
        if any(str(g["id"]) == t["id"] for _, g in self._tous(conf)):
            messagebox.showinfo("Facebook", f"« {t['nom']} » est déjà suivi.")
            return
        nom = t["nom"]
        if any(nom_fichier(g["nom"]) == nom_fichier(nom) for _, g in self._tous(conf)):
            nom = f"{nom} ({t['id'][-6:]})"  # deux suivis du même nom : fichiers séparés
        genre = "le groupe" if t["type"] == "groupe" else "la Page"
        if not messagebox.askyesno("Facebook", f"Suivre {genre} « {nom} » ({t['id']}) ?\n\nSes posts depuis le "
                                   f"{conf.get('depuis', '2026-07-31')} et tous leurs commentaires seront lus."):
            return
        rubrique = "groupes" if t["type"] == "groupe" else "pages"
        conf.setdefault(rubrique, []).append({"nom": nom, "id": t["id"], "groupe": self.v_groupe.get().strip()
                                              or ("soutien" if rubrique == "groupes" else "officiel")})
        pm.sauver(p)
        self.v_saisie.set("")
        self.remplir()
        self.app.message(f"« {nom} » ajouté : lu au prochain lancement de Facebook.")

    def retirer(self):
        ids = set(self.table.selection())
        if not ids:
            return
        p = perimetre()
        conf = p["facebook"]
        noms = [g["nom"] for _, g in self._tous(conf) if str(g["id"]) in ids]
        if not messagebox.askyesno("Retirer", "Ne plus suivre :\n\n" + "\n".join(noms) +
                                   "\n\nLes commentaires déjà collectés restent dans les fichiers."):
            return
        for rubrique in ("groupes", "pages"):
            conf[rubrique] = [g for g in conf.get(rubrique, []) if str(g["id"]) not in ids]
        pm.sauver(p)
        self.remplir()
        self.app.message(f"{len(noms)} groupe(s) ou Page(s) retiré(s).")

    def changer_groupe(self):
        ids = set(self.table.selection())
        if not ids:
            return
        p = perimetre()
        for _, g in self._tous(p["facebook"]):
            if str(g["id"]) in ids:
                g["groupe"] = self.v_groupe.get().strip() or "autre"
        pm.sauver(p)
        self.remplir()
        self.app.message(f"Groupe « {self.v_groupe.get()} » donné à la sélection (compté à la prochaine analyse).")


# --- X ---------------------------------------------------------------------------------------------------------------

class PageX:
    REGLAGES = [("depuis", "Posts publiés depuis le (AAAA-MM-JJ)", "2026-07-31"),
                ("relire_si_moins_de_jours", "Relire un post suivi de moins de (jours)", 7),
                ("attendre_reponses_jours", "Lire les réponses d'un post cité au bout de (jours)", 2),
                ("minutes_par_lancement", "Durée au plus d'un lancement (minutes)", 120),
                ("requetes_par_jour", "Requêtes au plus par jour", 3000),
                ("recherches_par_quart_heure", "Recherches au plus par quart d'heure (X : 50)", 40)]

    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "X")
        note(f, "Deux façons de prendre des posts sur X (anciennement Twitter), avec le compte de collecte "
                "(config/x.env), sans navigateur. Les comptes suivis : tous leurs posts (ni republications, ni "
                "réponses à d'autres), qu'ils citent le mot-clé ou non, et toutes les réponses dessous (un fichier "
                "par compte). La recherche : les posts des autres comptes qui citent le mot-clé (réglé dans l'onglet "
                "YouTube) et toutes leurs réponses, lues quand le post a quelques jours. Ajouter : le pseudo ou le "
                "lien du profil. Retirer arrête le suivi ; les commentaires déjà collectés restent dans les "
                "fichiers. Rythme prudent pour ne pas faire suspendre le compte : sous la limite de X, pauses entre "
                "les requêtes, et 3 h de repos si X freine.")
        _reglages(self, f, "x", self.REGLAGES)
        self.table = _table(f, [("nom", "Compte", 300), ("pseudo", "Pseudo", 200), ("groupe", "Groupe", 110),
                                ("arriere", "Arriéré", 150), ("commentaires", "Commentaires", 110)],
                            gauche=("nom", "pseudo", "groupe"))
        _ajout(self, f, "Suivre un compte", "Pseudo X (@pseudo) ou lien du profil :", "soutien")
        self.remplir()

    @staticmethod
    def _arriere(e: dict) -> str:
        from collecte.sources.x import date_de
        if e.get("complet"):
            return "terminé"
        return f"jusqu'au {date_de(e['bas']):%Y-%m-%d}" if e.get("bas") else "pas commencé"

    def remplir(self):
        avant = set(self.table.selection())
        self.table.delete(*self.table.get_children())
        p = perimetre()
        conf, etat = p.get("x", {}), etat_source("x")
        req = etat.get("requetes") or {}
        par_fichier = (self.app.comptes or {}).get("x", {}).get("par_fichier", {})
        mot = p.get("mot_cle", "Lisnard")
        if conf.get("recherche", True):
            n = par_fichier.get(nom_fichier(f"Recherche « {mot} »"))  # collecte/sources/x.py, nom_recherche
            self.table.insert("", "end", iid="recherche", values=(
                f"Recherche « {mot} » (tout X)", "", "autre", self._arriere(req.get("recherche", {})),
                "" if n is None else nombre(n)))
        for c in conf.get("comptes", []):
            n = par_fichier.get(nom_fichier(f"@{c['pseudo']}"))  # collecte/sources/x.py, nom_compte_suivi
            self.table.insert("", "end", iid=c["pseudo"], values=(
                c.get("nom") or c["pseudo"], f"@{c['pseudo']}", c.get("groupe", "autre"),
                self._arriere(req.get(f"@{c['pseudo']}", {})), "" if n is None else nombre(n)))
        _garder_selection(self.table, avant)

    def sauver_reglages(self):
        _sauver_reglages(self, "x", "X")

    def ajouter(self):
        if not self.v_saisie.get().strip():
            return
        self.app.config(cursor="watch")
        self.app.update_idletasks()
        try:
            c = pm.trouver_x(self.v_saisie.get())
        except Exception as e:
            messagebox.showerror("X", str(e))
            return
        finally:
            self.app.config(cursor="")
        p = perimetre()
        conf = p.setdefault("x", {})
        comptes = conf.setdefault("comptes", [])
        if any(x["pseudo"].lower() == c["pseudo"].lower() for x in comptes):
            messagebox.showinfo("X", f"@{c['pseudo']} est déjà suivi.")
            return
        if not messagebox.askyesno("X", f"Suivre « {c['nom']} » (@{c['pseudo']}) ?\n\nTous ses posts depuis le "
                                   f"{conf.get('depuis', '2026-07-31')} et leurs réponses seront pris."):
            return
        comptes.append({**c, "groupe": self.v_groupe.get().strip() or "soutien"})
        pm.sauver(p)
        self.v_saisie.set("")
        self.remplir()
        self.app.message(f"@{c['pseudo']} ajouté : ses posts seront lus au prochain lancement de X.")

    def retirer(self):
        ids = [i for i in self.table.selection() if i != "recherche"]
        if not ids:
            if self.table.selection():
                messagebox.showinfo("X", "La recherche du mot-clé ne se retire pas : décocher X dans la "
                                    "planification pour ne plus rien collecter.")
            return
        p = perimetre()
        noms = [f"@{c['pseudo']}" for c in p["x"]["comptes"] if c["pseudo"] in ids]
        if not messagebox.askyesno("Retirer", "Ne plus suivre :\n\n" + "\n".join(noms) +
                                   "\n\nLes commentaires déjà collectés restent dans les fichiers."):
            return
        p["x"]["comptes"] = [c for c in p["x"]["comptes"] if c["pseudo"] not in ids]
        pm.sauver(p)
        self.remplir()
        self.app.message(f"{len(noms)} compte(s) X retiré(s).")

    def changer_groupe(self):
        ids = [i for i in self.table.selection() if i != "recherche"]
        if not ids:
            return
        p = perimetre()
        for c in p["x"]["comptes"]:
            if c["pseudo"] in ids:
                c["groupe"] = self.v_groupe.get().strip() or "autre"
        pm.sauver(p)
        self.remplir()
        self.app.message(f"Groupe « {self.v_groupe.get()} » donné à la sélection (compté à la prochaine analyse).")


# --- Planification ---------------------------------------------------------------------------------------------------

class PagePlanification:
    def __init__(self, app, onglets):
        self.app = app
        f = _page(onglets, "Planification")
        fond = COULEURS["fond"]
        note(f, "Collecte automatique par le Planificateur de tâches de Windows, tant que la session est ouverte "
                "(Instagram a besoin de l'écran). Une fenêtre de console s'ouvre pendant la collecte. "
                "Une source déjà en cours n'est pas lancée une deuxième fois.")
        planif = planification.reglages()
        cadre = tk.Frame(f, bg=fond)
        cadre.pack(fill="x")
        tk.Label(cadre, text="Sources :", bg=fond).grid(row=0, column=0, sticky="w", pady=4)
        self.v_sources = {}
        for i, (source, nom) in enumerate(SOURCES.items()):
            v = tk.BooleanVar(value=source in planif.get("sources", list(SOURCES)))
            ttk.Checkbutton(cadre, text=nom, variable=v).grid(row=0, column=1 + i, sticky="w", padx=6)
            self.v_sources[source] = v
        tk.Label(cadre, text="Chaque jour à (HH:MM) :", bg=fond).grid(row=1, column=0, sticky="w", pady=4)
        self.v_heure = tk.StringVar(value=planif.get("heure", "08:00"))
        ttk.Entry(cadre, textvariable=self.v_heure, width=8).grid(row=1, column=1, sticky="w", padx=6)
        tk.Label(cadre, text="puis toutes les (heures, 0 = une fois par jour) :", bg=fond).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4)
        self.v_toutes = tk.StringVar(value=str(planif.get("toutes_les_h", 0)))
        ttk.Spinbox(cadre, from_=0, to=12, textvariable=self.v_toutes, width=5).grid(row=2, column=2, sticky="w")
        boutons = tk.Frame(f, bg=fond)
        boutons.pack(fill="x", pady=12)
        ttk.Button(boutons, text="Activer / mettre à jour", style="Accent.TButton", command=self.activer).pack(
            side="left")
        ttk.Button(boutons, text="Désactiver", command=self.desactiver).pack(side="left", padx=8)
        self.resume = tk.Label(f, text="", bg=fond, fg=COULEURS["texte"], anchor="w", justify="left")
        self.resume.pack(fill="x")
        self.maj()

    def maj(self):
        def travail():  # schtasks met une ou deux secondes à répondre : hors de la boucle principale
            prochaine = planification.prochaine_execution()
            planif = planification.reglages()
            if prochaine:
                texte = (f"Planification active : {', '.join(SOURCES[s] for s in planif.get('sources', []))}, "
                         f"chaque jour à {planif.get('heure', '?')}"
                         + (f" puis toutes les {planif['toutes_les_h']} h" if planif.get("toutes_les_h") else "")
                         + f".\nProchaine exécution : {prochaine}")
            else:
                texte = "Pas de collecte automatique."
            self.app.a_faire.put(lambda: self.resume.config(text=texte))
        threading.Thread(target=travail, daemon=True).start()

    def activer(self):
        sources = [s for s, v in self.v_sources.items() if v.get()]
        heure = self.v_heure.get().strip()
        if not sources:
            messagebox.showerror("Planification", "Choisir au moins une source.")
            return
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", heure):
            messagebox.showerror("Planification", "Heure au format HH:MM, par exemple 08:00.")
            return
        try:
            planification.activer(sources, heure, int(self.v_toutes.get()))
        except ValueError:
            messagebox.showerror("Planification", "Le nombre d'heures doit être un entier.")
            return
        except RuntimeError as e:
            messagebox.showerror("Planification", f"Windows a refusé la tâche :\n{e}")
            return
        self.maj()
        self.app.message("Collecte automatique activée.")

    def desactiver(self):
        planification.desactiver()
        self.maj()
        self.app.message("Collecte automatique désactivée.")
