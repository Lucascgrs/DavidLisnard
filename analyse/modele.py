"""Le modèle à vecteurs, et ce que partagent tous les modèles : entrées, jeu annoté, étalonnage, fiabilité, chargement.

Entrées d'un commentaire :
- son vecteur de sens (e5), celui du commentaire auquel il répond et celui du titre de la publication ;
- quelques indicateurs simples : source, groupe du compte, réponse ou non, longueur, mentions (Lisnard, Macron…).

Par critère, deux modèles (l'un sur le texte seul, l'autre avec le parent et le titre), dont on fait la moyenne ;
leur écart sert à la fiabilité :
- tonalité et pertinence : régression ridge ;
- forme, système et idées : régression logistique en 3 classes (reproche, non évoqué, éloge) ;
- cible (L / A) : régression logistique.
Règle appliquée après coup : si le commentaire ne parle pas de Lisnard (probabilité de A > 0,6), la tonalité et
les trois reproches valent 10.

Seul, ce modèle a été la version v1 à v3. Depuis v4, il est combiné au réseau affiné (analyse/ensemble.py).
Les modèles enregistrés (modeles/vN/modele.joblib) contiennent des objets de ce module : ne pas renommer le
module, ni les classes, ni leurs attributs, sans quoi ils ne se rechargent plus.
"""
import re

import joblib
import numpy as np

from analyse import corpus, stockage, versions
from analyse.criteres import CRITERES, REPROCHES, SEUIL_A
from analyse.vecteurs import DIMENSION, Magasin, calculer, cle_titre
from commun.config import MODELES
from commun.fichiers import lire_csv, lire_json
from commun.textes import sans_accents

# L'ordre de ces listes fixe les colonnes des indicateurs : le changer fausserait les modèles déjà entraînés.
SOURCES = ["youtube", "instagram", "whatsapp"]
GROUPES = ["officiel", "media", "commentateur", "soutien", "adhérents", "autre"]
MOTIFS = {
    "lisnard": r"lisnard|lisnar|lienard|isnard|david|\bdl\b|nouvelle energie",
    "macron": r"macron|macroni",
    "systeme": r"systeme|elite|enarque|caste|\blr\b|ump|sarko|recycl|bourgeois",
    "forme": r"charism|parle|orateur|discours|voix|clair|calme|endor|debit|com\b|communication",
    "idees": r"programme|idee|proposition|mesure|projet|liberal",
    "rire": r"😂|🤣|mdr|lol|ptdr",
    "bravo": r"bravo|👏|merci|soutien|go\b|vive",
}
CLASSES = [6.5, 13.5]  # limites des 3 classes des reproches : ≤ 6, 7 à 13, ≥ 14
MOYENNES_PAR_DEFAUT = (3.0, 10.0, 16.0)


def indicateurs(l: dict) -> list[float]:
    t = sans_accents(l["texte"])
    v = [float(l["source"] == s) for s in SOURCES]
    g = l["groupe"] if l["groupe"] in GROUPES else "autre"
    v += [float(g == x) for x in GROUPES]
    v += [float(l["type"] == "réponse"), np.log1p(len(l["texte"])) / 7, float(bool(l["parent_texte"])),
          float(bool(l["publication_titre"]))]
    v += [float(bool(re.search(m, t))) for m in MOTIFS.values()]
    return v


class Entrees:
    """Construit la matrice d'entrée pour une liste de commentaires du corpus."""

    def __init__(self, lignes_corpus: list[dict] | None = None):
        self.corpus = lignes_corpus if lignes_corpus is not None else corpus.lire()
        self.par_cle = {l["cle"]: l for l in self.corpus}
        self.textes = Magasin("textes")
        self.titres = Magasin("titres")

    def completer_vecteurs(self, lignes: list[dict], journal=print, verifier_arret=lambda: None,
                           avancement=lambda etape, fait, total: None) -> int:
        """Calcule les vecteurs qui manquent pour ces commentaires : leur texte, celui de leur parent, leur titre."""
        besoin = {l["texte_cle"] for l in lignes}
        besoin |= {self.par_cle[l["parent_cle"]]["texte_cle"] for l in lignes if l["parent_cle"] in self.par_cle}
        textes = {l["texte_cle"]: l["texte"] for l in self.corpus if l["texte_cle"] in besoin}
        titres = {cle_titre(l["publication_titre"]): l["publication_titre"] for l in lignes if l["publication_titre"]}
        n = len(self.textes.manquants(textes)) + len(self.titres.manquants(titres))
        if n:
            journal(f"  calcul de {n} vecteurs de sens")
            for nom, magasin, dico in (("textes", self.textes, textes), ("titres", self.titres, titres)):
                calculer(magasin, dico, journal, verifier_arret=verifier_arret, lot=1024,
                         avancement=lambda f, t, nom=nom: avancement(f"vecteurs ({nom})", f, t))
        return n

    def matrice(self, lignes: list[dict]) -> np.ndarray:
        e = self.textes.matrice([l["texte_cle"] for l in lignes])
        parents = [self.par_cle.get(l["parent_cle"], {}).get("texte_cle", "") if l["parent_cle"] else ""
                   for l in lignes]
        p = self.textes.matrice(parents)
        t = self.titres.matrice([cle_titre(l["publication_titre"]) if l["publication_titre"] else "" for l in lignes])
        ind = np.array([indicateurs(l) for l in lignes], np.float32)
        return np.hstack([e, 0.5 * p, 0.5 * t, ind]).astype(np.float32)


def jeu_annote(entrees: Entrees):
    """Annotations de Claude avec leur commentaire : (lignes, cibles 0/1, notes n × 5, jeu de chaque annotation).
    Les corrections faites dans l'interface remplacent l'annotation du même commentaire (et gardent son jeu)."""
    from analyse.annotation import annotations
    toutes = {a["cle"]: a for a in annotations()}
    for c in lire_csv(stockage.CORRECTIONS):
        toutes[c["cle"]] = {**c, "jeu": toutes.get(c["cle"], {}).get("jeu", "entrainement")}
    lignes, cibles, notes, jeux = [], [], [], []
    for a in toutes.values():
        l = entrees.par_cle.get(a["cle"])
        if l is None:
            continue
        lignes.append(l)
        cibles.append(1 if a["cible"] == "A" else 0)
        notes.append([int(a[c]) for c in CRITERES])
        jeux.append(a["jeu"])
    return lignes, np.array(cibles), np.array(notes, np.float32), np.array(jeux)


def etalonner(brutes_triees: np.ndarray, vraies_triees: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Replace chaque note p selon son rang parmi des notes brutes de référence, sur la répartition des vraies notes.
    Les modèles resserrent leurs notes autour de la moyenne : sans cela, la synthèse sous-estimerait toutes les
    parts (0,6 % de tonalités ≤ 6 prédites contre 21 % dans les annotations)."""
    rang = np.searchsorted(brutes_triees, p, side="left") / max(1, len(brutes_triees) - 1)
    return np.interp(np.clip(rang, 0, 1), np.linspace(0, 1, len(vraies_triees)), vraies_triees)


def score_fiabilite(p: dict) -> np.ndarray:
    """Mesuré sur le test : le signal qui prédit le mieux les erreurs est la netteté de la cible (L ou A sans
    hésitation), puis l'accord des deux modèles. La proximité d'un exemple annoté, elle, ne prédit rien."""
    nette = np.abs(p["p_autre"] - 0.5) * 2
    return (2 * nette + np.clip(1 - p["ecart"] / 3, 0, 1)) / 3


def classer_fiabilite(score: np.ndarray, seuils) -> np.ndarray:
    bas, haut = seuils
    return np.where(score >= haut, "bonne", np.where(score >= bas, "moyenne", "faible"))


class Modele:
    seuils_fiabilite = (0.33, 0.66)

    def __init__(self):
        self.cible = None
        self.regresseurs: dict[str, list] = {}
        self.references = None  # vecteurs des textes annotés (proximité, pour le tirage des lots)
        self.moyennes = {}
        self.infos = {}

    # Deux jeux d'entrées, chacun normalisé (sans normalisation, les indicateurs 0/1 écrasent les vecteurs, dont les
    # composantes valent ~0,03) : A = texte + indicateurs, B = texte + parent + titre + indicateurs.
    @staticmethod
    def _jeux(X):
        return {"A": np.hstack([X[:, :DIMENSION], X[:, 3 * DIMENSION:]]), "B": X}

    def entrainer(self, X: np.ndarray, cibles: np.ndarray, notes: np.ndarray, journal=print):
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        def logistique():
            return make_pipeline(StandardScaler(), LogisticRegression(C=0.003, max_iter=3000, class_weight="balanced"))

        jeux = self._jeux(X)
        self.cible = [logistique().fit(Z, cibles) for Z in jeux.values()]
        self.moyennes = {}
        for j, c in enumerate(CRITERES):
            y = notes[:, j]
            if c in REPROCHES:
                # Reproches et éloges sont rares : classement en 3 classes à poids équilibrés, puis note = moyenne
                # des notes de chaque classe pondérée par sa probabilité.
                k = np.digitize(y, CLASSES)
                self.moyennes[c] = np.array([y[k == i].mean() if (k == i).any() else MOYENNES_PAR_DEFAUT[i]
                                             for i in range(3)])
                self.regresseurs[c] = [logistique().fit(Z, k) for Z in jeux.values()]
            else:
                self.regresseurs[c] = [make_pipeline(StandardScaler(), Ridge(alpha=3000)).fit(Z, y)
                                       for Z in jeux.values()]
            journal(f"    {c} : appris")
        self.references = X[:, :DIMENSION] / (np.linalg.norm(X[:, :DIMENSION], axis=1, keepdims=True) + 1e-9)
        self._etalonner(X, cibles, notes)

    def _etalonner(self, X, cibles, notes):
        """Étalonnage par rang (voir etalonner), sur des prédictions hors échantillon (validation croisée)."""
        from sklearn.base import clone
        from sklearn.model_selection import KFold
        brutes = {c: np.zeros(len(X)) for c in CRITERES}
        for app, val in KFold(5, shuffle=True, random_state=0).split(X):
            jeux_a, jeux_v = list(self._jeux(X[app]).values()), list(self._jeux(X[val]).values())
            for j, c in enumerate(CRITERES):
                y = notes[app, j]
                cible = np.digitize(y, CLASSES) if c in self.moyennes else y
                ms = [clone(m).fit(Z, cible) for m, Z in zip(self.regresseurs[c], jeux_a)]
                brutes[c][val] = np.mean([self._note(c, m, Z) for m, Z in zip(ms, jeux_v)], axis=0)
        self.etalonnage = {}
        for j, c in enumerate(CRITERES):
            # Pour la tonalité et les reproches, seuls les commentaires sur Lisnard (les autres valent 10 par règle).
            garde = cibles == 0 if c != "pertinence" else np.ones(len(X), bool)
            self.etalonnage[c] = (np.sort(brutes[c][garde]), np.sort(notes[garde, j]))

    def _etalonne(self, c, p):
        if not getattr(self, "etalonnage", None):  # versions entraînées avant l'étalonnage
            return p
        return etalonner(*self.etalonnage[c], p)

    def _note(self, c, m, Z):
        if c in self.moyennes:
            proba = np.zeros((len(Z), 3))
            proba[:, m.classes_] = m.predict_proba(Z)
            return proba @ self.moyennes[c]
        return m.predict(Z)

    def predire(self, X: np.ndarray, lot=20000) -> dict[str, np.ndarray]:
        sortie = {c: [] for c in CRITERES}
        sortie.update(p_autre=[], ecart=[], proximite=[])
        for i in range(0, len(X), lot):
            x = X[i:i + lot]
            jeux = list(self._jeux(x).values())
            pa = np.mean([m.predict_proba(Z)[:, 1] for m, Z in zip(self.cible, jeux)], axis=0)
            ecarts = []
            for c in CRITERES:
                preds = np.array([self._note(c, m, Z) for m, Z in zip(self.regresseurs[c], jeux)])
                p = np.clip(self._etalonne(c, preds.mean(axis=0)), 0, 20)
                if c != "pertinence":
                    p = np.where(pa > SEUIL_A, 10.0, p)
                sortie[c].append(p)
                ecarts.append(np.abs(preds[0] - preds[1]))
            v = x[:, :DIMENSION] / (np.linalg.norm(x[:, :DIMENSION], axis=1, keepdims=True) + 1e-9)
            sortie["proximite"].append((v @ self.references.T).max(axis=1))
            sortie["ecart"].append(np.mean(ecarts, axis=0))
            sortie["p_autre"].append(pa)
        return {k: np.concatenate(v) for k, v in sortie.items()}

    def predire_lignes(self, lignes: list[dict], entrees: Entrees, avancement=None) -> dict[str, np.ndarray]:
        return self.predire(entrees.matrice(lignes))

    @staticmethod
    def score_fiabilite(p: dict) -> np.ndarray:
        return score_fiabilite(p)

    def fiabilite(self, p: dict) -> np.ndarray:
        return classer_fiabilite(score_fiabilite(p), self.seuils_fiabilite)


def charger(version: str | None = None) -> tuple[Modele, dict]:
    """Le modèle d'une version (par défaut celle en service) et ses infos."""
    version = version or versions.derniere_version()
    if not version:
        raise FileNotFoundError("Aucun modèle entraîné")
    d = MODELES / version
    return joblib.load(d / "modele.joblib"), lire_json(d / "infos.json")
