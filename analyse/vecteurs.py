"""Vecteurs de sens des textes (modèle multilingue intfloat/multilingual-e5-base, sur le processeur).

Un vecteur par texte distinct (texte_cle du corpus) et par titre de publication distinct. Calculés une seule fois :
les lancements suivants ne calculent que les nouveaux. Rangés dans donnees/analyse/vecteurs/ :
    <nom>.npy (float16, normalisés) + <nom>.cles (une clé par ligne, même ordre)
"""
import hashlib
import time

import numpy as np

from analyse.stockage import VECTEURS

MODELE_LANGUE = "intfloat/multilingual-e5-base"
DIMENSION = 768
LONGUEUR_MAX = 256  # jetons ; au-delà, la fin du commentaire est ignorée par le modèle
_modele = None


def modele_langue():
    global _modele
    if _modele is None:
        from sentence_transformers import SentenceTransformer
        _modele = SentenceTransformer(MODELE_LANGUE, device="cpu")
        _modele.max_seq_length = LONGUEUR_MAX
    return _modele


def cle_titre(titre: str) -> str:
    return hashlib.sha1(titre.encode("utf-8")).hexdigest()[:16]


class Magasin:
    """Les vecteurs d'un type de texte (« textes » ou « titres »), indexés par clé."""

    def __init__(self, nom: str):
        self.npy = VECTEURS / f"{nom}.npy"
        self.fcles = VECTEURS / f"{nom}.cles"
        if self.npy.exists():
            self.v = np.load(self.npy)
            self.cles = self.fcles.read_text(encoding="utf-8").split("\n")[:len(self.v)]
        else:
            self.v, self.cles = np.zeros((0, DIMENSION), np.float16), []
        self.index = {c: i for i, c in enumerate(self.cles)}

    def manquants(self, textes: dict[str, str]) -> dict[str, str]:
        return {c: t for c, t in textes.items() if c not in self.index}

    def ajouter(self, cles: list[str], v: np.ndarray):
        self.v = np.vstack([self.v, v.astype(np.float16)])
        for c in cles:
            self.index[c] = len(self.cles)
            self.cles.append(c)

    def sauver(self):
        VECTEURS.mkdir(parents=True, exist_ok=True)
        np.save(self.npy.with_suffix(".tmp.npy"), self.v)
        self.fcles.with_suffix(".tmp").write_text("\n".join(self.cles), encoding="utf-8")
        self.npy.with_suffix(".tmp.npy").replace(self.npy)
        self.fcles.with_suffix(".tmp").replace(self.fcles)

    def matrice(self, cles: list[str]) -> np.ndarray:
        """Vecteurs dans l'ordre demandé ; zéros pour une clé vide ou inconnue."""
        out = np.zeros((len(cles), self.v.shape[1]), np.float32)
        for i, c in enumerate(cles):
            j = self.index.get(c)
            if j is not None:
                out[i] = self.v[j]
        return out


def calculer(magasin: Magasin, textes: dict[str, str], journal=print, verifier_arret=lambda: None,
             avancement=lambda fait, total: None, lot=2048) -> int:
    """Calcule et enregistre les vecteurs des textes absents du magasin. Renvoie leur nombre."""
    a_faire = magasin.manquants(textes)
    if not a_faire:
        return 0
    m = modele_langue()
    # Du plus court au plus long : les lots de longueur proche vont beaucoup plus vite.
    cles = sorted(a_faire, key=lambda c: len(a_faire[c]))
    debut, fait = time.time(), 0
    for i in range(0, len(cles), lot):
        verifier_arret()
        morceau = cles[i:i + lot]
        v = m.encode([f"query: {a_faire[c] or '(vide)'}" for c in morceau], batch_size=64,
                     normalize_embeddings=True, show_progress_bar=False)
        magasin.ajouter(morceau, v)
        fait += len(morceau)
        avancement(fait, len(cles))
        if (i // lot) % 5 == 4 or fait == len(cles):
            magasin.sauver()
            journal(f"    vecteurs : {fait}/{len(cles)} ({time.time() - debut:.0f} s)")
    magasin.sauver()
    return fait
