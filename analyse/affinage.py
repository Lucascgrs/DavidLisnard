"""Modèle affiné : le modèle de langue (e5) réentraîné sur les annotations, qui lit ensemble le commentaire, celui
auquel il répond et le titre de la publication.

Le modèle à vecteurs (modele.py) ne voit que des vecteurs calculés séparément pour chaque texte : il ne peut pas saisir une
réponse ironique (« Bravo, quel courage 😂 » sous une critique), car le sens naît de la rencontre des deux textes.
Ici, le modèle de langue lit la paire en une seule passe et ses couches sont ajustées sur les notes de Claude.

Entrée : « query: <source>, <type>. Commentaire : … Il répond à : … Publication : … » (le commentaire d'abord,
pour qu'il ne soit jamais coupé au profit du contexte).
Sortie : cible (L/A), tonalité et pertinence (régression), forme, système et idées (3 classes : reproche, rien,
éloge), comme dans modele.py.

    python -m analyse.affinage entrainer [--epoques 5] [--sortie affineN] [--graine 0] [--lr 3e-5] [--sans-titre]
        [--longueurs 256 128 20]

Apprend sur le jeu « entrainement » (dont 12 % mis de côté pour choisir la meilleure époque) et enregistre dans
modeles/<sortie>/ le réseau et ses sorties sur le réglage et le test, que lit ensuite analyse/ensemble.py.
Environ 3,4 s par pas de 16 commentaires sur le processeur : compter 40 à 45 minutes par époque pour 12 000
annotations. Ne jamais lancer deux entraînements en même temps : ils se ralentissent jusqu'à 9 fois.
"""
import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np

from analyse import versions
from analyse.criteres import CRITERES, REPROCHES
from analyse.modele import CLASSES, MOYENNES_PAR_DEFAUT, Entrees, jeu_annote
from analyse.vecteurs import DIMENSION, MODELE_LANGUE
from commun.config import MODELES
from commun.fichiers import lire_json

LONG_COMMENTAIRE, LONG_PARENT, LONG_TITRE = 256, 128, 20  # jetons gardés au plus pour chaque partie de l'entrée
# (valeurs par défaut ; un réseau entraîné avec d'autres longueurs les garde dans son infos.json, clé « longueurs »)
FIGES = 4  # couches basses gardées telles quelles (plus rapide, et peu de données pour les ajuster)
FILS = max(1, (os.cpu_count() or 8) - 2)  # le processeur presque entier, en laissant la main à l'interface
SORTIES = 12  # 1 cible + tonalité + pertinence + 3 reproches × 3 classes


def _texte_entree(l: dict, parents: dict) -> tuple[str, str, str, str]:
    tete = f"{l['source']}, {'réponse' if l['type'] == 'réponse' else 'commentaire'}"
    parent = parents.get(l["parent_cle"], "") if l["parent_cle"] else (l.get("parent_texte") or "")
    return tete, l["texte"], parent, l["publication_titre"] or ""


class Encodeur:
    def __init__(self, tok, titre: bool = True, longueurs=None):
        self.tok, self.titre = tok, titre
        self.longueurs = tuple(longueurs or (LONG_COMMENTAIRE, LONG_PARENT, LONG_TITRE))

    def __call__(self, tete, texte, parent, titre):
        t = self.tok
        lc, lp, lt = self.longueurs
        ids = t(f"query: {tete}. Commentaire :", add_special_tokens=False)["input_ids"]
        ids += t(texte, add_special_tokens=False, truncation=True, max_length=lc)["input_ids"]
        if parent:
            ids += t(" Il répond à :", add_special_tokens=False)["input_ids"]
            ids += t(parent, add_special_tokens=False, truncation=True, max_length=lp)["input_ids"]
        if titre and self.titre:
            ids += t(" Publication :", add_special_tokens=False)["input_ids"]
            ids += t(titre, add_special_tokens=False, truncation=True, max_length=lt)["input_ids"]
        return [t.cls_token_id] + ids + [t.sep_token_id]


def _reseau():
    import torch
    from transformers import AutoModel

    class Reseau(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.base = AutoModel.from_pretrained(MODELE_LANGUE)
            self.abandon = torch.nn.Dropout(0.1)
            self.tete = torch.nn.Linear(DIMENSION, SORTIES)

        def forward(self, ids, masque):
            h = self.base(input_ids=ids, attention_mask=masque).last_hidden_state
            m = masque.unsqueeze(-1).float()
            v = (h * m).sum(1) / m.sum(1)  # moyenne des jetons, comme e5
            return self.tete(self.abandon(v))

    r = Reseau()
    for p in r.base.embeddings.parameters():
        p.requires_grad = False
    for couche in r.base.encoder.layer[:FIGES]:
        for p in couche.parameters():
            p.requires_grad = False
    return r


def _lots(longueurs, taille, melanger, rnd):
    ordre = np.argsort(longueurs)
    lots = [ordre[i:i + taille] for i in range(0, len(ordre), taille)]
    if melanger:
        rnd.shuffle(lots)
    return lots


def _tenseurs(seqs, pad):
    import torch
    n = max(len(s) for s in seqs)
    ids = torch.full((len(seqs), n), pad, dtype=torch.long)
    masque = torch.zeros((len(seqs), n), dtype=torch.long)
    for i, s in enumerate(seqs):
        ids[i, :len(s)] = torch.tensor(s)
        masque[i, :len(s)] = 1
    return ids, masque


def predire_brut(reseau, seqs, pad, taille=32, avancement=None):
    """Sorties brutes du réseau (n × 12), dans l'ordre des séquences."""
    import torch
    reseau.eval()
    sortie = np.zeros((len(seqs), SORTIES), np.float32)
    lots = _lots(np.array([len(s) for s in seqs]), taille, False, None)
    t0 = time.time()
    with torch.no_grad():
        for k, idx in enumerate(lots):
            ids, masque = _tenseurs([seqs[i] for i in idx], pad)
            sortie[idx] = reseau(ids, masque).numpy()
            if avancement and k % 50 == 0:
                avancement(min(len(seqs), (k + 1) * taille), len(seqs), time.time() - t0)
    return sortie


def decoder(brut: np.ndarray, moyennes: dict) -> dict[str, np.ndarray]:
    """Sorties brutes → probabilité de A et notes non étalonnées."""
    d = {"p_autre": 1 / (1 + np.exp(-brut[:, 0])), "tonalite": 10 + 5 * brut[:, 1], "pertinence": 10 + 5 * brut[:, 2]}
    for j, c in enumerate(REPROCHES):
        z = brut[:, 3 + 3 * j: 6 + 3 * j]
        p = np.exp(z - z.max(1, keepdims=True))
        p /= p.sum(1, keepdims=True)
        d[c] = p @ np.array(moyennes[c])
    return d


def entrainer(epoques=5, nom=None, graine=0, journal=print, lr=3e-5, titre=True, longueurs=None) -> str:
    """Affine le réseau et l'enregistre dans modeles/<nom>/ (par défaut le prochain affineN). Renvoie le nom.
    titre=False : le réseau ne lit pas le titre de la publication (essai du 2026-11-10).
    longueurs=(commentaire, parent, titre) en jetons ; par défaut LONG_COMMENTAIRE, LONG_PARENT, LONG_TITRE."""
    import torch
    from transformers import AutoTokenizer
    nom = nom or versions.prochain_reseau()
    torch.manual_seed(graine)
    torch.set_num_threads(FILS)
    rnd = random.Random(graine)
    entrees = Entrees()
    lignes, cibles, notes, jeux = jeu_annote(entrees)
    parents = {l["cle"]: l["texte"] for l in entrees.corpus}
    tok = AutoTokenizer.from_pretrained(MODELE_LANGUE)
    enc = Encodeur(tok, titre, longueurs)
    seqs = [enc(*_texte_entree(l, parents)) for l in lignes]
    app = np.where(jeux == "entrainement")[0]
    # 12 % de l'entraînement mis de côté : choix de l'époque et étalonnage des notes (le test reste intouché).
    rnd.shuffle(app := list(app))
    n_dev = int(0.12 * len(app))
    dev, app = np.array(sorted(app[:n_dev])), np.array(sorted(app[n_dev:]))
    test = np.where(np.isin(jeux, ["test", "test_rare"]))[0]
    journal(f"  {len(app)} pour apprendre, {len(dev)} pour régler, {len(test)} pour mesurer")

    classes = {c: np.digitize(notes[:, CRITERES.index(c)], CLASSES) for c in REPROCHES}
    moyennes = {}
    for c in REPROCHES:
        y, k = notes[app, CRITERES.index(c)], classes[c][app]
        moyennes[c] = [float(y[k == i].mean()) if (k == i).any() else MOYENNES_PAR_DEFAUT[i] for i in range(3)]
    sur_l = cibles == 0
    poids_classes = {}
    for c in REPROCHES:
        k = classes[c][app][sur_l[app]]
        freq = np.bincount(k, minlength=3) + 1
        poids_classes[c] = torch.tensor((freq.sum() / (3 * freq)) ** 0.7, dtype=torch.float32)
    pos = (cibles[app] == 1).mean()

    reseau = _reseau()
    groupes = [{"params": [p for p in reseau.base.parameters() if p.requires_grad], "lr": lr},
               {"params": reseau.tete.parameters(), "lr": 1e-3}]
    opt = torch.optim.AdamW(groupes, weight_decay=0.01)
    taille = 16
    pas_total = epoques * math.ceil(len(app) / taille)
    prechauffe = int(0.08 * pas_total)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / prechauffe) * max(0.05, 1 - s / pas_total))
    Y = torch.tensor(notes, dtype=torch.float32)
    C = torch.tensor(cibles, dtype=torch.float32)
    K = {c: torch.tensor(classes[c]) for c in REPROCHES}
    L = torch.tensor(sur_l)
    pad = tok.pad_token_id
    longueurs = np.array([len(seqs[i]) for i in app])
    meilleur, etat_meilleur, historique = None, None, []
    t0 = time.time()
    pas = 0
    for ep in range(epoques):
        reseau.train()
        for idx_local in _lots(longueurs + np.array([rnd.random() * 6 for _ in app]), taille, True, rnd):
            idx = app[idx_local]
            ids, masque = _tenseurs([seqs[i] for i in idx], pad)
            out = reseau(ids, masque)
            ti = torch.tensor(idx)
            perte = torch.nn.functional.binary_cross_entropy_with_logits(
                out[:, 0], C[ti], pos_weight=torch.tensor((1 - pos) / pos))
            lm = L[ti]
            if lm.any():
                perte = perte + torch.nn.functional.smooth_l1_loss(out[lm, 1], (Y[ti][lm, 0] - 10) / 5)
                for j, c in enumerate(REPROCHES):
                    perte = perte + 0.7 * torch.nn.functional.cross_entropy(
                        out[lm, 3 + 3 * j: 6 + 3 * j], K[c][ti][lm], weight=poids_classes[c])
            perte = perte + torch.nn.functional.smooth_l1_loss(out[:, 2], (Y[ti][:, 4] - 10) / 5)
            perte.backward()
            torch.nn.utils.clip_grad_norm_(reseau.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            pas += 1
            if pas % 25 == 0:
                journal(f"    époque {ep + 1}, pas {pas}/{pas_total}, perte {perte.item():.3f}, "
                        f"{(time.time() - t0) / 60:.1f} min")
        brut = predire_brut(reseau, [seqs[i] for i in dev], pad)
        score = _score_dev(decoder(brut, moyennes), notes[dev], cibles[dev])
        historique.append(score)
        journal(f"  époque {ep + 1} : réglage {json.dumps(score)}")
        if meilleur is None or score["total"] > meilleur:
            meilleur = score["total"]
            etat_meilleur = {k: v.detach().clone() for k, v in reseau.state_dict().items()}
    reseau.load_state_dict(etat_meilleur)
    d = MODELES / nom
    d.mkdir(parents=True, exist_ok=True)
    torch.save({k: v.half() for k, v in reseau.state_dict().items()}, d / "reseau.pt")
    sorties = {}
    for nom_jeu, idx in (("dev", dev), ("test", test)):
        brut = predire_brut(reseau, [seqs[i] for i in idx], pad)
        sorties[nom_jeu] = {"cles": [lignes[i]["cle"] for i in idx], "brut": brut.tolist()}
    (d / "sorties.json").write_text(json.dumps(sorties), encoding="utf-8")
    (d / "infos.json").write_text(json.dumps({"moyennes": moyennes, "historique": historique, "epoques": epoques,
                                              "lr": lr, "figes": FIGES, "graine": graine, "titre": titre,
                                              "longueurs": list(enc.longueurs),
                                              "duree_min": round((time.time() - t0) / 60, 1)}, indent=1),
                                  encoding="utf-8")
    journal(f"  enregistré dans {d} ({(time.time() - t0) / 60:.0f} min)")
    return nom


def _score_dev(p, notes, cibles):
    from scipy.stats import spearmanr
    l = cibles == 0
    s = {"cible": float(((p["p_autre"] > 0.5) == (cibles == 1)).mean()),
         "ton": float(spearmanr(notes[l, 0], p["tonalite"][l]).statistic),
         "pert": float(spearmanr(notes[:, 4], p["pertinence"]).statistic)}
    for j, c in zip((1, 2, 3), REPROCHES):
        s[c] = float(spearmanr(notes[l, j], p[c][l]).statistic)
    s["total"] = s["cible"] + s["ton"] + s["pert"] + (s["forme"] + s["systeme"] + s["idees"]) / 3
    return {k: round(v, 3) for k, v in s.items()}


def charger_reseau(nom):
    import torch
    from transformers import AutoTokenizer
    reseau = _reseau()
    etat = torch.load(MODELES / nom / "reseau.pt")
    reseau.load_state_dict({k: v.float() for k, v in etat.items()})
    return reseau, AutoTokenizer.from_pretrained(MODELE_LANGUE), lire_json(MODELES / nom / "infos.json")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser(prog="python -m analyse.affinage", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("commande", choices=["entrainer"])
    a.add_argument("--epoques", type=int, default=5)
    a.add_argument("--sortie", default=None, help="nom du dossier dans modeles/ (défaut : le prochain affineN)")
    a.add_argument("--graine", type=int, default=0)
    a.add_argument("--lr", type=float, default=3e-5)
    a.add_argument("--longueurs", type=int, nargs=3, metavar=("COMMENTAIRE", "PARENT", "TITRE"),
                   help="jetons gardés au plus pour chaque partie (défaut 128 64 20)")
    a.add_argument("--sans-titre", action="store_true", help="ne pas donner le titre de la publication au réseau")
    x = a.parse_args()
    entrainer(x.epoques, x.sortie, x.graine, lr=x.lr, titre=not x.sans_titre, longueurs=x.longueurs)
