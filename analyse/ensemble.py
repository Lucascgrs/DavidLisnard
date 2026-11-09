"""Modèle combiné : le réseau affiné (affinage.py, qui lit le commentaire avec celui auquel il répond) et le modèle à
vecteurs (modele.py). C'est la version mise en service.

Pourquoi les deux : le réseau affiné comprend mieux le contexte (réponses, ironie) ; le modèle à vecteurs est plus
stable sur les critères rares. Leur combinaison, réglée sur des commentaires annotés que ni l'un ni l'autre n'a vus
(le jeu « réglage » du réseau), fait mieux que chacun.

    python -m analyse.ensemble tout                 réentraînement complet : affinage puis combinaison (3 à 4 h)
    python -m analyse.ensemble construire affineN   combinaison seule, à partir d'un réseau déjà affiné (25 min)

Les deux modèles sont entraînés sans les commentaires de test : les mesures du rapport sont donc exactement celles
du modèle en service. La nouvelle version (modeles/vN/) est utilisée dès la prochaine analyse.

Remarque : ces commandes passent par le module importé (analyse.ensemble) et non par __main__, sinon la classe
Ensemble serait enregistrée sous le nom « __main__.Ensemble » et le modèle ne se rechargerait plus ailleurs.
"""
import json
import sys
import time
from datetime import datetime

import joblib
import numpy as np

from analyse import versions
from analyse.criteres import CRITERES, SEUIL_A
from analyse.mesures import mesurer, mesures_fiabilite, mesures_test
from analyse.modele import Entrees, Modele, classer_fiabilite, etalonner, jeu_annote, score_fiabilite
from commun.config import MODELES
from commun.fichiers import lire_json


class Ensemble:
    """Moyenne pondérée, critère par critère, des notes du réseau affiné et du modèle à vecteurs, puis étalonnage.
    Enregistré dans modeles/vN/modele.joblib : ne pas renommer ses attributs."""

    def __init__(self, base: Modele, reseau: str, moyennes: dict, poids: dict, ref: dict, seuils_fiabilite):
        self.base, self.reseau, self.moyennes, self.poids, self.ref = base, reseau, moyennes, poids, ref
        self.seuils_fiabilite = seuils_fiabilite
        self._net = None

    # -- réseau affiné --
    def _charger_reseau(self):
        if self._net is None:
            from analyse.affinage import Encodeur, charger_reseau
            net, tok, _ = charger_reseau(self.reseau)
            self._net = (net, tok, Encodeur(tok))
        return self._net

    def sorties_reseau(self, lignes, corpus_par_cle, avancement=None) -> np.ndarray:
        from analyse.affinage import _texte_entree, predire_brut
        net, tok, enc = self._charger_reseau()
        parents = {k: l["texte"] for k, l in corpus_par_cle.items()}
        seqs = [enc(*_texte_entree(l, parents)) for l in lignes]
        return predire_brut(net, seqs, tok.pad_token_id, taille=32, avancement=avancement)

    # -- combinaison --
    def combiner(self, pb: dict, brut: np.ndarray) -> dict:
        """pb : prédictions du modèle à vecteurs ; brut : sorties du réseau. Retourne les notes finales."""
        from analyse.affinage import decoder
        pa = decoder(brut, self.moyennes)
        sortie = {"p_autre": self.poids["cible"] * pa["p_autre"] + (1 - self.poids["cible"]) * pb["p_autre"]}
        reseau_etalonne = {c: etalonner(self.ref["affine"][c], self.ref["vrai"][c], pa[c]) for c in CRITERES}
        for c in CRITERES:
            m = self.poids[c] * reseau_etalonne[c] + (1 - self.poids[c]) * pb[c]
            m = np.clip(etalonner(self.ref["melange"][c], self.ref["vrai"][c], m), 0, 20)
            if c != "pertinence":
                m = np.where(sortie["p_autre"] > SEUIL_A, 10.0, m)
            sortie[c] = m
        sortie["ecart"] = np.mean([np.abs(reseau_etalonne[c] - pb[c]) for c in CRITERES], axis=0)
        sortie["proximite"] = pb["proximite"]
        return sortie

    def predire_lignes(self, lignes, entrees: Entrees, avancement=None) -> dict:
        pb = self.base.predire(entrees.matrice(lignes))
        brut = self.sorties_reseau(lignes, entrees.par_cle, avancement)
        return self.combiner(pb, brut)

    def predire(self, X):
        """Sans le texte (tirage des lots d'annotation) : le modèle à vecteurs seul."""
        return self.base.predire(X)

    @staticmethod
    def score_fiabilite(p: dict) -> np.ndarray:
        return score_fiabilite(p)

    def fiabilite(self, p: dict) -> np.ndarray:
        return classer_fiabilite(score_fiabilite(p), self.seuils_fiabilite)


def _regler(notes_dev, cibles_dev, pa_dev, pb_dev):
    """Sur le jeu « réglage » : étalonnage du réseau, poids du mélange par critère, étalonnage final."""
    from scipy.stats import spearmanr
    ref = {"affine": {}, "vrai": {}, "melange": {}}
    poids = {}
    for j, c in enumerate(CRITERES):
        garde = cibles_dev == 0 if c != "pertinence" else np.ones(len(cibles_dev), bool)
        ref["affine"][c] = np.sort(pa_dev[c][garde])
        ref["vrai"][c] = np.sort(notes_dev[:, j][garde])
        a_et = etalonner(ref["affine"][c], ref["vrai"][c], pa_dev[c])
        meilleur = None
        for w in np.linspace(0, 1, 11):
            m = w * a_et + (1 - w) * pb_dev[c]
            r = spearmanr(notes_dev[:, j][garde], m[garde]).statistic
            if meilleur is None or r > meilleur[0]:
                meilleur = (r, w)
        # Le réglage compte un ou deux milliers de commentaires : on tire le poids vers 0,5 pour ne pas sur-ajuster.
        poids[c] = float(0.5 * meilleur[1] + 0.25)
        m = poids[c] * a_et + (1 - poids[c]) * pb_dev[c]
        ref["melange"][c] = np.sort(m[garde])
    exactitudes = []
    for w in np.linspace(0, 1, 11):
        pa = w * pa_dev["p_autre"] + (1 - w) * pb_dev["p_autre"]
        exactitudes.append((((pa > 0.5) == (cibles_dev == 1)).mean(), w))
    poids["cible"] = float(0.5 * max(exactitudes)[1] + 0.25)
    return ref, poids


def construire(nom_reseau: str, journal=print) -> str:
    """Nouvelle version vN à partir du réseau modeles/<nom_reseau>/ ; renvoie son nom."""
    from analyse.affinage import decoder
    from analyse.mesures import ecrire_rapport
    debut = time.time()
    d_res = MODELES / nom_reseau
    sorties = lire_json(d_res / "sorties.json")
    infos_res = lire_json(d_res / "infos.json")
    entrees = Entrees()
    lignes, cibles, notes, jeux = jeu_annote(entrees)
    entrees.completer_vecteurs(lignes, journal)
    idx = {l["cle"]: i for i, l in enumerate(lignes)}

    def jeu(nom):  # lignes du jeu « dev » ou « test » du réseau encore annotées, et leurs sorties brutes
        garde = [k for k, c in enumerate(sorties[nom]["cles"]) if c in idx]
        return (np.array([idx[sorties[nom]["cles"][k]] for k in garde]),
                np.array(sorties[nom]["brut"])[garde])

    dev, brut_dev = jeu("dev")
    test, brut_test = jeu("test")
    # Le modèle à vecteurs apprend sur le même jeu que le réseau : l'entraînement sans le réglage ni le test.
    exclus = set(dev) | set(test)
    app = np.array([i for i in range(len(lignes)) if i not in exclus and jeux[i] == "entrainement"])
    X = entrees.matrice(lignes)
    journal(f"  modèle à vecteurs : {len(app)} annotations pour apprendre, {len(dev)} pour régler, {len(test)} pour mesurer")
    base = Modele()
    base.entrainer(X[app], cibles[app], notes[app], journal)
    pb_dev, pb_test = base.predire(X[dev]), base.predire(X[test])
    moy = infos_res["moyennes"]
    ref, poids = _regler(notes[dev], cibles[dev], decoder(brut_dev, moy), pb_dev)
    ens = Ensemble(base, nom_reseau, moy, poids, ref, (0.33, 0.66))
    p = ens.combiner(pb_test, brut_test)
    t = jeux[test] == "test"
    # Seuils de fiabilité : tiers du score sur le test (un tiers « faible », un tiers « bonne »).
    ens.seuils_fiabilite = tuple(float(x) for x in np.quantile(score_fiabilite({k: v[t] for k, v in p.items()}),
                                                                 [1 / 3, 2 / 3]))
    mesures = mesures_test(notes[test], cibles[test], jeux[test], [lignes[i] for i in test], p)
    mesures["fiabilite"] = mesures_fiabilite(notes[test][t], cibles[test][t], {k: v[t] for k, v in p.items()},
                                             ens.fiabilite(p)[t])
    # Pour comparer : le modèle à vecteurs seul, sur le même test.
    mesures["vecteurs_seuls"] = {c: mesurer(notes[test][t, j], pb_test[c][t]) for j, c in enumerate(CRITERES)}
    mesures["vecteurs_seuls"]["cible"] = float(((pb_test["p_autre"][t] > 0.5) == (cibles[test][t] == 1)).mean())
    version = versions.prochaine_version()
    d = MODELES / version
    d.mkdir(parents=True)
    infos = {"version": version, "type": "ensemble", "reseau": nom_reseau,
             "le": datetime.now().isoformat(timespec="seconds"), "annotations": int(len(lignes)),
             "apprentissage": int(len(app)), "reglage": int(len(dev)), "test": int(t.sum()),
             "modele_langue": "intfloat/multilingual-e5-base (affiné) + vecteurs e5", "seuil_autre": SEUIL_A,
             "poids_reseau": poids, "mesures_test": mesures, "duree_s": round(time.time() - debut)}
    joblib.dump(ens, d / "modele.joblib", compress=3)
    (d / "infos.json").write_text(json.dumps(infos, ensure_ascii=False, indent=2), encoding="utf-8")
    ecrire_rapport(infos)
    journal(f"  modèle combiné {version} enregistré ; poids du réseau affiné : "
            + ", ".join(f"{k} {v:.2f}" for k, v in poids.items()))
    return version


def tout(journal=print) -> str:
    """Réentraînement complet sur toutes les annotations : nouveau réseau affiné, puis nouveau modèle combiné."""
    from analyse import affinage
    nom = versions.prochain_reseau()
    journal(f"### Affinage du modèle de langue ({nom})")
    affinage.entrainer(5, nom, journal=journal)
    journal("### Modèle combiné")
    return construire(nom, journal)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import analyse.ensemble as module  # voir la remarque en tête du fichier
    if len(sys.argv) > 2 and sys.argv[1] == "construire":
        module.construire(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "tout":
        module.tout()
    else:
        raise SystemExit(__doc__)
