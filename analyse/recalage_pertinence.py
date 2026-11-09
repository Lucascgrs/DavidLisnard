"""Recalage de la pertinence des annotations des lots 18 à 142 sur la grille (fait le 2026-11-09).

Constat : à partir du lot 18, la pertinence des annotations a glissé vers le bas.
- Moyenne des commentaires visant Lisnard : 8,8 dans les lots 1 à 17, 0,8 dans les lots 131 à 142.
- Un « Bravo » noté 0 au lieu de 8.
Le jeu de test (lots 1 à 17) suit la grille, mais pas les données d'entraînement de ces lots.

Méthode :
1. tirer : échantillon de ces annotations, à renoter à l'aveugle (l'ancienne note n'est pas affichée) ;
2. voir : affichage ;
3. noter : une ligne « n pertinence » par commentaire ;
4. appliquer : on ajuste la correspondance (ancienne note, lot, longueur du texte, tonalité, reproches) vers la note
   de la grille, on mesure son erreur par validation croisée, puis on réécrit les pertinences. Les commentaires de
   l'échantillon reçoivent leur note renotée.

L'ancienne note est toujours lue dans annotations_avant_recalage.csv (copie faite au premier « appliquer ») :
relancer « appliquer » redonne exactement le même résultat, et les lots postérieurs au 142 ne sont jamais touchés.
Bilan : donnees/analyse/annotation/recalage/bilan.json.

    python -m analyse.recalage_pertinence tirer 400
    python -m analyse.recalage_pertinence voir [de] [à]
    python -m analyse.recalage_pertinence noter fichier.txt
    python -m analyse.recalage_pertinence appliquer
"""
import json
import math
import random
import re
import shutil
import sys

from analyse.annotation import ANNOTATIONS, DOSSIER
from analyse.corpus import lire
from commun.fichiers import ecrire_csv, lire_csv
from commun.textes import abreger

RECAL = DOSSIER / "recalage"
ECHANTILLON = RECAL / "echantillon.csv"
NOTES = RECAL / "notes.csv"
COPIE = DOSSIER / "annotations_avant_recalage.csv"
LOTS_DERIVES = range(18, 143)  # lots 18 à 142


def _derives(lignes):
    return [l for l in lignes if int(l["lot"]) in LOTS_DERIVES and l["jeu"] == "entrainement"]


def _anciennes_notes() -> dict[str, int]:
    """Pertinence d'origine de chaque annotation (avant tout recalage)."""
    return {l["cle"]: int(l["pertinence"]) for l in lire_csv(COPIE if COPIE.exists() else ANNOTATIONS)}


def tirer(n: int, graine: int = 0):
    lignes = _derives(lire_csv(ANNOTATIONS))
    anciennes = _anciennes_notes()
    rnd = random.Random(graine)
    hauts = [l for l in lignes if anciennes[l["cle"]] >= 5]
    n_haut = min(len(hauts), int(0.3 * n))
    choix = rnd.sample(hauts, n_haut)
    pris = {l["cle"] for l in choix}
    reste = [l for l in lignes if l["cle"] not in pris]
    choix += rnd.sample(reste, n - n_haut)
    rnd.shuffle(choix)
    ecrire_csv(ECHANTILLON, [{"n": i + 1, "cle": l["cle"]} for i, l in enumerate(choix)], ["n", "cle"])
    print(f"{len(choix)} commentaires tirés ({n_haut} parmi les anciennes notes ≥ 5)")


def voir(depuis: int = 1, jusqu_a: int = 10**9):
    corpus = {l["cle"]: l for l in lire()}
    for item in lire_csv(ECHANTILLON):
        if not depuis <= int(item["n"]) <= jusqu_a:
            continue
        l = corpus[item["cle"]]
        ligne = f"{item['n']}. [{l['source'][:2]}|{l['type'][:3]}]"
        if l["publication_titre"]:
            ligne += f" {abreger(l['publication_titre'], 70)}"
        if l["parent_texte"]:
            ligne += "\n   ↳ " + abreger(l["parent_texte"], 300)
        ligne += f"\n   » {abreger(l['texte'], 500)}"
        print(ligne)


LIGNE = re.compile(r"^\s*(\d+)\s+(\d+)\s*(?:#.*)?$")


def noter(fichier: str):
    ech = {int(l["n"]): l["cle"] for l in lire_csv(ECHANTILLON)}
    deja = {l["cle"]: l for l in lire_csv(NOTES)}
    vus = 0
    for brut in open(fichier, encoding="utf-8"):
        if not brut.strip():
            continue
        m = LIGNE.match(brut)
        if not m:
            raise SystemExit(f"ligne illisible : {brut!r}")
        n, p = int(m[1]), int(m[2])
        if n not in ech or not 0 <= p <= 20:
            raise SystemExit(f"ligne hors échantillon ou note hors 0-20 : {brut!r}")
        deja[ech[n]] = {"cle": ech[n], "pertinence": p}
        vus += 1
    ecrire_csv(NOTES, list(deja.values()), ["cle", "pertinence"])
    print(f"{vus} notes enregistrées ; {len(deja)} au total sur {len(ech)}")


def _traits(a, pertinence: int, texte: str) -> list[float]:
    ton = int(a["tonalite"])
    repro = sum(int(a[c]) != 10 for c in ("forme", "systeme", "idees"))
    long_ = math.log1p(len(texte or ""))
    est_l = float(a["cible"] == "L")
    lot = int(a["lot"])
    p = pertinence
    return [p, p * p, est_l, est_l * p, long_, est_l * long_, abs(ton - 10) / 10, repro, lot / 100, lot * p / 1000]


def appliquer():
    import numpy as np
    from scipy.stats import spearmanr
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import cross_val_predict
    corpus = {l["cle"]: l["texte"] for l in lire()}
    annot = lire_csv(ANNOTATIONS)
    par_cle = {a["cle"]: a for a in annot}
    anciennes = _anciennes_notes()
    notes = {l["cle"]: int(l["pertinence"]) for l in lire_csv(NOTES)}
    cles = [c for c in notes if c in par_cle]
    X = np.array([_traits(par_cle[c], anciennes[c], corpus.get(c, "")) for c in cles])
    y = np.array([notes[c] for c in cles], float)
    modele = Ridge(alpha=1.0)
    pred = np.clip(cross_val_predict(modele, X, y, cv=5), 0, 20)
    ancien = np.array([anciennes[c] for c in cles], float)
    bilan = {"echantillon": len(cles),
             "ecart_ancienne_note": float(np.mean(np.abs(ancien - y))),
             "ecart_recalage_validation_croisee": float(np.mean(np.abs(pred - y))),
             "rho_ancienne": float(spearmanr(ancien, y).statistic),
             "rho_recalage": float(spearmanr(pred, y).statistic),
             "moyenne_renotee": float(y.mean()), "moyenne_ancienne": float(ancien.mean())}
    print(json.dumps(bilan, ensure_ascii=False, indent=1))
    modele.fit(X, y)
    if not COPIE.exists():
        shutil.copy2(ANNOTATIONS, COPIE)
    changes = 0
    for a in _derives(annot):
        if a["cle"] in notes:
            nouv = notes[a["cle"]]
        else:
            x = np.array([_traits(a, anciennes[a["cle"]], corpus.get(a["cle"], ""))])
            nouv = int(round(float(np.clip(modele.predict(x)[0], 0, 20))))
        if a["cible"] == "A":
            nouv = min(nouv, 4)
        if str(nouv) != a["pertinence"]:
            a["pertinence"] = str(nouv)
            changes += 1
    ecrire_csv(ANNOTATIONS, annot, list(annot[0].keys()))
    bilan["annotations_modifiees"] = changes
    (RECAL / "bilan.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{changes} pertinences réécrites ; ancienne version dans {COPIE.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, *args = sys.argv[1:] or [""]
    if cmd == "tirer":
        tirer(int(args[0]))
    elif cmd == "voir":
        voir(*(int(x) for x in args[:2]))
    elif cmd == "noter":
        noter(args[0])
    elif cmd == "appliquer":
        appliquer()
    else:
        raise SystemExit(__doc__)
