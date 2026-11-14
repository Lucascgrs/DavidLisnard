"""Fenêtre de suivi d'un affinage en cours, sans l'interrompre.

    python -m suivi                 branche la sonde sur l'entraînement lancé (si besoin) et ouvre la fenêtre
    python -m suivi --image a.png   enregistre une image de la fenêtre, sans rien ouvrir (contrôle)

La sonde (suivi/sonde.py) est injectée dans le processus d'entraînement par sys.remote_exec (Python 3.14) : elle
lit les variables de la boucle d'affinage sans les modifier et les écrit dans %TEMP%/lisnard_suivi.json.
La fenêtre ne fait que lire ce fichier : la fermer ne touche pas à l'entraînement.
"""
import argparse
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SORTIE = Path(tempfile.gettempdir()) / "lisnard_suivi.json"
SONDE = Path(__file__).with_name("sonde.py").resolve()
L, H = 1400, 860
FOND, PANNEAU, LIGNE = (20, 22, 28), (29, 32, 41), (52, 56, 70)
TEXTE, DISCRET, ACCENT = (232, 232, 238), (140, 144, 160), (122, 162, 247)
VERT, ORANGE, ROUGE, BLEU = (95, 211, 141), (240, 170, 80), (230, 103, 103), (35, 159, 192)
POLICES = "C:/Windows/Fonts/"
SORTIES_TETE = ["cible", "tonalité", "pertinence", "forme −", "forme =", "forme +", "système −", "système =",
                "système +", "idées −", "idées =", "idées +"]
CLASSE = ["−", "=", "+"]


def police(taille, gras=False):
    nom = "seguisb.ttf" if gras else "segoeui.ttf"
    try:
        return ImageFont.truetype(POLICES + nom, taille)
    except OSError:
        return ImageFont.load_default()


F = {k: police(t, g) for k, (t, g) in {"titre": (24, True), "grand": (18, True), "moyen": (15, False),
                                         "moyen_g": (15, True), "petit": (13, False), "mini": (11, False)}.items()}


# --- branchement -------------------------------------------------------------------------------------------------

def trouver_entrainement():
    import psutil
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        cmd = " ".join(p.info["cmdline"] or [])
        if "python" in (p.info["name"] or "").lower() and ("analyse.ensemble" in cmd or "analyse.affinage" in cmd):
            if p.info["pid"] != os.getpid():
                return p.info["pid"]
    return None


def lire_etat():
    for _ in range(3):
        try:
            return json.loads(SORTIE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            time.sleep(0.05)
    return None


def brancher():
    pid = trouver_entrainement()
    if pid is None:
        print("Aucun entraînement en cours (python -m analyse.ensemble / analyse.affinage).")
        return None
    e = lire_etat()
    if e and e.get("pid") == pid and time.time() - e.get("maj", 0) < 15:
        print(f"Sonde déjà branchée sur l'entraînement {pid}.")
        return pid
    print(f"Branchement de la sonde sur l'entraînement {pid} (sans l'interrompre)…")
    sys.remote_exec(pid, str(SONDE))
    for _ in range(120):  # la sonde s'exécute au prochain point sûr du processus
        e = lire_etat()
        if e and e.get("pid") == pid and time.time() - e.get("maj", 0) < 5:
            print("Sonde branchée.")
            return pid
        time.sleep(0.5)
    print("La sonde ne répond pas encore : la fenêtre s'ouvre quand même et attendra ses données.")
    return pid


# --- dessin ------------------------------------------------------------------------------------------------------

def tronquer(texte, fnt, largeur):
    texte = " ".join(str(texte).split())
    if fnt.getlength(texte) <= largeur:
        return texte
    while texte and fnt.getlength(texte + "…") > largeur:
        texte = texte[:-1]
    return texte + "…"


def melange(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def carte_divergente(m, echelle):
    """Écart négatif en bleu, positif en rouge, nul sur le fond du panneau."""
    v = np.clip(m / max(echelle, 1e-12), -1, 1)[..., None]
    base = np.array(PANNEAU, float)
    rgb = np.where(v < 0, base + (np.array(BLEU) * 1.15 - base) * -v, base + (np.array(ROUGE) * 1.1 - base) * v)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def duree(s):
    if s is None or s < 0 or math.isinf(s) or math.isnan(s):
        return "—"
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def fr(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


class Rendu:
    """Dessine l'état de la sonde ; garde des valeurs affichées qui glissent vers les vraies (animation douce)."""

    def __init__(self):
        self.zoom = None
        self.tete = None
        self.derive = None
        self.echelle_zoom = None
        self.lot_vu, self.t_lot = None, 0.0

    def glisser(self, ancien, cible, k=0.18):
        if cible is None:
            return ancien
        cible = np.asarray(cible, float)
        if ancien is None or ancien.shape != cible.shape:
            return cible.copy()
        return ancien + (cible - ancien) * k

    def image(self, e, t=None):
        t = time.time() if t is None else t
        im = Image.new("RGB", (L, H), FOND)
        d = ImageDraw.Draw(im)
        if not e:
            d.text((40, 40), "En attente des données de la sonde…", font=F["titre"], fill=TEXTE)
            return im
        self.entete(d, e, t)
        self.commentaires(d, e, t)
        self.courbe(d, e)
        self.poids(im, d, e)
        self.couches(d, e)
        if e.get("erreur"):
            d.rectangle((0, H - 22, L, H), fill=(70, 30, 30))
            d.text((10, H - 20), tronquer("Sonde : " + e["erreur"].strip().splitlines()[-1], F["mini"], L - 20),
                   font=F["mini"], fill=TEXTE)
        return im

    # En-tête : époques, barre de progression, temps
    def entete(self, d, e, t):
        pas, total = e.get("pas") or 0, e.get("pas_total") or 1
        vieux = t - e.get("maj", 0) > 10
        phase = "la sonde ne répond plus (entraînement fini ?)" if vieux else e.get("phase", "")
        d.text((30, 18), f"Affinage {e.get('nom') or ''}", font=F["titre"], fill=TEXTE)
        d.text((30, 54), phase, font=F["moyen"], fill=ORANGE if vieux else ACCENT)
        # époques
        n, ep = e.get("epoques") or 0, e.get("epoque") or 0
        x0 = 330
        d.text((x0, 22), "époques", font=F["mini"], fill=DISCRET)
        for k in range(n):
            cx, cy = x0 + 8 + k * 30, 52
            if k + 1 < ep:
                d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=VERT)
            elif k + 1 == ep:
                r = 9 + 2.5 * (0.5 + 0.5 * math.sin(t * 4))
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ACCENT, width=2)
                d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=ACCENT)
            else:
                d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=LIGNE, width=2)
            d.text((cx, cy), str(k + 1), font=F["mini"], fill=FOND if k + 1 <= ep else DISCRET, anchor="mm")
        # barre
        bx0, bx1, by = 520, 1000, 44
        d.rounded_rectangle((bx0, by, bx1, by + 16), 8, fill=PANNEAU)
        frac = min(1.0, pas / total)
        if frac > 0:
            fin = bx0 + (bx1 - bx0) * frac
            d.rounded_rectangle((bx0, by, max(bx0 + 16, fin), by + 16), 8, fill=ACCENT)
            lueur = bx0 + ((t * 120) % max(1, fin - bx0))  # reflet qui court sur la partie faite
            if min(fin - 4, lueur + 30) > lueur:
                d.rectangle((lueur, by + 3, min(fin - 4, lueur + 30), by + 13),
                            fill=melange(ACCENT, (255, 255, 255), .35))
        d.text((bx0, 20), f"pas {pas:,} / {total:,}".replace(",", " ") + f"   ({fr(100 * frac)} %)",
               font=F["moyen"], fill=TEXTE)
        # temps
        pertes = e.get("pertes") or []
        if len(pertes) >= 6:
            recents = pertes[-60:]
            s_pas = (recents[-1][2] - recents[0][2]) / max(1, recents[-1][0] - recents[0][0])
        elif e.get("t0") and pas:
            s_pas = (t - e["t0"]) / pas
        else:
            s_pas = None
        ecoule = t - e["t0"] if e.get("t0") else None
        reste = (total - pas) * s_pas if s_pas else None
        lignes = [f"écoulé {duree(ecoule)}", f"reste ≈ {duree(reste)}",
                  f"{fr(s_pas)} s par pas de 16" if s_pas else "", f"taux {e['lr']:.1e}" if e.get("lr") else ""]
        for k, s in enumerate(lignes):
            d.text((1040 + (k // 2) * 175, 18 + (k % 2) * 26), s, font=F["moyen"], fill=TEXTE if k < 2 else DISCRET)

    # Colonne gauche : le lot que le réseau vient de lire
    def commentaires(self, d, e, t):
        x0, y0, x1, y1 = 20, 100, 700, H - 30
        d.rounded_rectangle((x0, y0, x1, y1), 12, fill=PANNEAU)
        lot = e.get("lot_predit") or {}
        cour = e.get("lot_courant") or {}
        d.text((x0 + 18, y0 + 12), "Ce que le réseau vient de lire", font=F["grand"], fill=TEXTE)
        d.text((x0 + 18, y0 + 38), "note de Claude  ○      prédiction du réseau  ●      (pertinence sur 0-20)",
               font=F["mini"], fill=DISCRET)
        if cour.get("pas") is not None and cour.get("pas") == e.get("pas") and cour.get("pas") != lot.get("pas"):
            a = 0.5 + 0.5 * math.sin(t * 6)
            d.ellipse((x1 - 190, y0 + 20, x1 - 180, y0 + 30), fill=melange(PANNEAU, ACCENT, a))
            d.text((x1 - 172, y0 + 16), "lot suivant en lecture…", font=F["petit"], fill=DISCRET)
        if lot.get("pas") != self.lot_vu:
            self.lot_vu, self.t_lot = lot.get("pas"), t
        cartes = lot.get("commentaires") or []
        y, h = y0 + 62, 42
        for k, c in enumerate(cartes[:16]):
            apparition = min(1.0, max(0.0, (t - self.t_lot - k * 0.06) / 0.25))
            if apparition <= 0:
                break
            p = c.get("predit") or {}
            note = c.get("note") or [10] * 5
            ecart = abs(p.get("pertinence", note[4]) - note[4])
            couleur = VERT if ecart <= 2.5 else ORANGE if ecart <= 5 else ROUGE
            yy = y + k * h + (1 - apparition) * 12
            fond = melange(FOND, PANNEAU, 0.35)
            d.rounded_rectangle((x0 + 12, yy, x1 - 12, yy + h - 5), 7, fill=melange(PANNEAU, fond, apparition))
            d.rectangle((x0 + 12, yy + 4, x0 + 15, yy + h - 9), fill=melange(PANNEAU, couleur, apparition))
            src = str(c.get("source", ""))[:9]
            d.text((x0 + 24, yy + 3), src, font=F["mini"], fill=DISCRET)
            d.text((x0 + 92, yy + 1), tronquer(c.get("texte", ""), F["petit"], 340), font=F["petit"],
                   fill=melange(PANNEAU, TEXTE, apparition))
            if p:
                cible = "autre sujet" if p["autre"] > 0.5 else "parle de Lisnard"
                vrai = "autre sujet" if c.get("cible") == 1 else "parle de Lisnard"
                rep = " ".join(f"{n}{CLASSE[p['reproches'][j]]}" for j, n in enumerate(("F", "S", "I")))
                detail = (f"ton {fr(note[0], 0)}→{fr(p['tonalite'])}   {rep}   "
                          f"{cible}{'' if cible == vrai else ' (Claude : ' + vrai + ')'}")
                d.text((x0 + 92, yy + 19), tronquer(detail, F["mini"], 340), font=F["mini"], fill=DISCRET)
                # jauge de pertinence
                gx0, gx1, gy = x1 - 220, x1 - 30, yy + 18
                d.line((gx0, gy, gx1, gy), fill=LIGNE, width=3)
                for v in (0, 10, 20):
                    gx = gx0 + (gx1 - gx0) * v / 20
                    d.line((gx, gy - 4, gx, gy + 4), fill=LIGNE)
                xv = gx0 + (gx1 - gx0) * np.clip(note[4], 0, 20) / 20
                xp = gx0 + (gx1 - gx0) * np.clip(p["pertinence"], 0, 20) / 20
                d.line((xv, gy, xp, gy), fill=couleur, width=3)
                d.ellipse((xv - 7, gy - 7, xv + 7, gy + 7), outline=TEXTE, width=2)
                d.ellipse((xp - 5, gy - 5, xp + 5, gy + 5), fill=couleur)
                d.text((gx1 + 6, gy), fr(p["pertinence"], 0), font=F["mini"], fill=couleur, anchor="lm")
        if not cartes:
            d.text((x0 + 18, y0 + 80), "Le premier lot arrive…", font=F["moyen"], fill=DISCRET)

    # Courbe de la perte
    def courbe(self, d, e):
        x0, y0, x1, y1 = 720, 100, L - 20, 370
        d.rounded_rectangle((x0, y0, x1, y1), 12, fill=PANNEAU)
        d.text((x0 + 18, y0 + 12), "Erreur du réseau (perte) à chaque pas", font=F["grand"], fill=TEXTE)
        pertes = e.get("pertes") or []
        if len(pertes) < 3:
            d.text((x0 + 18, y0 + 50), "Les premiers pas arrivent (un toutes les 4 à 5 s)…", font=F["moyen"],
                   fill=DISCRET)
            return
        p = np.array([q[:2] for q in pertes], float)
        gx0, gy0, gx1, gy1 = x0 + 50, y0 + 50, x1 - 20, y1 - 30
        bas, haut = np.percentile(p[:, 1], 1), np.percentile(p[:, 1], 99)
        haut = haut + (haut - bas) * 0.1 + 1e-6
        a, b = p[0, 0], max(p[-1, 0], p[0, 0] + 1)

        def pt(s, v):
            return gx0 + (gx1 - gx0) * (s - a) / (b - a), gy1 - (gy1 - gy0) * (np.clip(v, bas, haut) - bas) / (haut - bas)

        for k in range(5):
            v = bas + (haut - bas) * k / 4
            yy = pt(a, v)[1]
            d.line((gx0, yy, gx1, yy), fill=LIGNE)
            d.text((gx0 - 8, yy), fr(v, 2), font=F["mini"], fill=DISCRET, anchor="rm")
        for s, v in p:
            x, y = pt(s, v)
            d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=melange(PANNEAU, ACCENT, .45))
        n = min(25, max(1, len(p) // 3))
        moy = np.convolve(p[:, 1], np.ones(n) / n, mode="valid")
        d.line([pt(s, v) for s, v in zip(p[n - 1:, 0], moy)], fill=VERT, width=3)
        d.text((gx0, gy1 + 8), f"pas {int(a)}", font=F["mini"], fill=DISCRET)
        d.text((gx1, gy1 + 8), f"pas {int(b)}", font=F["mini"], fill=DISCRET, anchor="ra")
        d.text((x1 - 20, y0 + 16), f"moyenne sur {n} pas : {fr(moy[-1], 3)}", font=F["moyen"], fill=VERT, anchor="ra")
        d.text(((gx0 + gx1) / 2, gy1 + 8), f"suivie depuis le branchement de la sonde", font=F["mini"],
               fill=DISCRET, anchor="ma")

    # Poids : zoom sur 1 600 poids de la dernière couche + tête de sortie
    def poids(self, im, d, e):
        x0, y0, x1, y1 = 720, 385, L - 20, 655
        d.rounded_rectangle((x0, y0, x1, y1), 12, fill=PANNEAU)
        d.text((x0 + 18, y0 + 10), "Les poids qui bougent", font=F["grand"], fill=TEXTE)
        z = e.get("zoom")
        self.zoom = self.glisser(self.zoom, z and z["ecart"])
        self.tete = self.glisser(self.tete, e.get("tete"))
        if self.zoom is not None:
            ech = float(np.percentile(np.abs(self.zoom), 98)) or 1e-6
            self.echelle_zoom = ech if self.echelle_zoom is None else self.echelle_zoom * 0.95 + ech * 0.05
            carte = carte_divergente(self.zoom, self.echelle_zoom).resize((200, 200), Image.NEAREST)
            im.paste(carte, (x0 + 20, y0 + 44))
            d.text((x0 + 20, y0 + 248), f"40 × 40 poids de la couche {z['couche']} : écart au e5 de départ",
                   font=F["mini"], fill=DISCRET)
            d.text((x1 - 20, y0 + 16), f"bleu : a baissé · rouge : a monté (échelle ± {self.echelle_zoom:.0e})",
                   font=F["mini"], fill=DISCRET, anchor="ra")
        if self.tete is not None:
            ech = float(np.percentile(np.abs(self.tete), 98)) or 1e-6
            carte = carte_divergente(self.tete, ech).resize((96 * 3, 12 * 17), Image.NEAREST)
            tx = x0 + 340
            im.paste(carte, (tx, y0 + 44))
            for k, n in enumerate(SORTIES_TETE):
                d.text((tx - 8, y0 + 44 + k * 17 + 8), n, font=F["mini"], fill=DISCRET, anchor="rm")
            d.text((tx, y0 + 248), "tête de sortie : 96 premiers poids de chaque note prédite", font=F["mini"],
                   fill=DISCRET)
        if self.zoom is None and self.tete is None:
            d.text((x0 + 18, y0 + 50), "Lecture des poids…", font=F["moyen"], fill=DISCRET)

    # Dérive de chaque couche depuis le modèle de départ
    def couches(self, d, e):
        x0, y0, x1, y1 = 720, 670, L - 20, H - 30
        d.rounded_rectangle((x0, y0, x1, y1), 12, fill=PANNEAU)
        d.text((x0 + 18, y0 + 10), "Combien chaque couche a changé depuis e5", font=F["grand"], fill=TEXTE)
        self.derive = self.glisser(self.derive, e.get("derive"))
        if self.derive is None:
            return
        n, figees = len(self.derive), e.get("figees", 0)
        haut = max(0.05, float(self.derive.max()) * 1.15)
        bx0, bx1, by0, by1 = x0 + 30, x1 - 30, y0 + 50, y1 - 26
        lb = (bx1 - bx0) / n
        for k, v in enumerate(self.derive):
            bx = bx0 + k * lb
            hh = (by1 - by0) * v / haut
            coul = LIGNE if k < figees else melange(ACCENT, VERT, k / max(1, n - 1))
            d.rounded_rectangle((bx + 6, by1 - max(2, hh), bx + lb - 6, by1), 4, fill=coul)
            d.text((bx + lb / 2, by1 + 4), str(k + 1), font=F["mini"], fill=DISCRET, anchor="ma")
            etiquette = "figée" if k < figees else f"{fr(v, 2)} %"
            d.text((bx + lb / 2, by1 - max(2, hh) - 3), etiquette, font=F["mini"], fill=DISCRET, anchor="ms")


def fenetre():
    import tkinter as tk
    from PIL import ImageTk
    racine = tk.Tk()
    racine.title("Suivi de l'affinage — DavidLisnard")
    racine.configure(bg="#14161c")
    etiquette = tk.Label(racine, bg="#14161c", bd=0)
    etiquette.pack(fill="both", expand=True)
    rendu = Rendu()
    etat = {"e": None, "lu": 0.0}

    def tic():
        if time.time() - etat["lu"] > 0.5:
            etat["e"] = lire_etat() or etat["e"]
            etat["lu"] = time.time()
        im = rendu.image(etat["e"])
        w, h = max(200, etiquette.winfo_width()), max(200, etiquette.winfo_height())
        if (w, h) != (L, H) and w > 1:
            r = min(w / L, h / H)
            im = im.resize((int(L * r), int(H * r)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(im)
        etiquette.configure(image=photo)
        etiquette.image = photo
        racine.after(80, tic)

    racine.geometry(f"{L}x{H}")
    tic()
    racine.mainloop()


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--image", help="enregistre une image de la fenêtre au lieu de l'ouvrir")
    a.add_argument("--sans-brancher", action="store_true", help="ne pas injecter la sonde")
    x = a.parse_args()
    if not x.sans_brancher:
        brancher()
    if x.image:
        r = Rendu()
        e = lire_etat()
        r.image(e)  # premier passage : les valeurs glissantes partent des vraies
        r.image(e, time.time() + 5).save(x.image)
        print(f"image enregistrée : {x.image}")
    else:
        fenetre()


if __name__ == "__main__":
    if sys.stdout is not None:  # pythonw (Suivi.bat) n'a pas de console
        sys.stdout.reconfigure(encoding="utf-8")
    main()
