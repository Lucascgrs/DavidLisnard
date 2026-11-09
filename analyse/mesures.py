"""Mesure de la qualité d'un modèle sur le jeu de test, et rapport donnees/analyse/RAPPORT_MODELE.md.

Deux jeux de mesure, tirés une fois pour toutes et jamais appris :
- « test » : 500 commentaires tirés au hasard, pour toutes les mesures d'ensemble ;
- « test_rare » : 120 commentaires choisis pour leurs mots de reproche, ajoutés au précédent seulement pour mesurer
  les reproches et les éloges, trop rares au hasard.
"""
import numpy as np

from analyse import stockage
from analyse.criteres import CRITERES, REPROCHES
from analyse.modele import SOURCES

FIABILITES = ("bonne", "moyenne", "faible")


def mesurer(vrai: np.ndarray, pred: np.ndarray, critere: str = "") -> dict:
    """Écart moyen et corrélation de rang ; pour un critère de reproche, rappel et précision des reproches (note ≤ 6)
    et des éloges (note ≥ 14)."""
    from scipy.stats import spearmanr
    m = {"ecart_moyen": float(np.mean(np.abs(vrai - pred))),
         "correlation_rang": float(spearmanr(vrai, pred).statistic) if np.std(vrai) > 0 else None}
    if critere in REPROCHES:
        for nom, masque_v, masque_p in (("reproche", vrai <= 6, pred <= 7), ("eloge", vrai >= 14, pred >= 13)):
            n = int(masque_v.sum())
            m[f"{nom}_n"] = n
            m[f"{nom}_rappel"] = float((masque_v & masque_p).sum() / n) if n else None
            m[f"{nom}_precision"] = float((masque_v & masque_p).sum() / masque_p.sum()) if masque_p.sum() else None
    return m


def mesures_test(notes, cibles, jeux, lignes, p) -> dict:
    """Toutes les mesures, sur « test » (+ « test_rare » pour les reproches). p : prédictions sur ces lignes."""
    test = jeux == "test"
    mesures = {}
    for j, c in enumerate(CRITERES):
        mesures[c] = mesurer(notes[test, j], p[c][test])
        if c in REPROCHES:
            mesures[c].update({k: v for k, v in mesurer(notes[:, j], p[c], c).items()
                               if k.split("_")[0] in ("reproche", "eloge")})
    vrai_a, pred_a = cibles[test] == 1, p["p_autre"][test] > 0.5
    # Fidélité des parts (ce que lit la synthèse), sur les commentaires de test qui parlent de Lisnard.
    sur = cibles[test] == 0
    mesures["parts"] = {c: {"reel_bas": float((notes[test, j][sur] <= 6).mean()),
                            "predit_bas": float((p[c][test][sur] <= 6).mean()),
                            "reel_haut": float((notes[test, j][sur] >= 14).mean()),
                            "predit_haut": float((p[c][test][sur] >= 14).mean())} for j, c in enumerate(CRITERES)}
    mesures["cible"] = {"exactitude": float((vrai_a == pred_a).mean()), "part_A_reelle": float(vrai_a.mean())}
    src = np.array([l["source"] for l in lignes])[test]
    ecart_ton = np.abs(notes[test, 0] - p["tonalite"][test])
    ecart_pert = np.abs(notes[test, 4] - p["pertinence"][test])
    mesures["par_source"] = {s: {"n": int((src == s).sum()), "ecart_tonalite": float(np.mean(ecart_ton[src == s])),
                                 "ecart_pertinence": float(np.mean(ecart_pert[src == s]))}
                             for s in SOURCES if (src == s).any()}
    # Réponses : celles dont le sens dépend du commentaire parent.
    rep = np.array([l["type"] == "réponse" for l in lignes])[test]
    if rep.any():
        mesures["reponses"] = {"n": int(rep.sum()), "ecart_tonalite": float(np.mean(ecart_ton[rep])),
                               "cible": float((vrai_a == pred_a)[rep].mean())}
    return mesures


def mesures_fiabilite(notes, cibles, p, fiab) -> dict:
    """Par niveau de fiabilité : part des commentaires, cible fausse, écart sur la tonalité (sur le test seul)."""
    fausse = (cibles == 1) != (p["p_autre"] > 0.5)
    ecart = np.abs(notes[:, 0] - p["tonalite"])
    return {f: {"part": float((fiab == f).mean()),
                "ecart_tonalite": float(np.mean(ecart[fiab == f])) if (fiab == f).any() else None,
                "cible_fausse": float(np.mean(fausse[fiab == f])) if (fiab == f).any() else None}
            for f in FIABILITES}


def _f(x, pct=False):
    if x is None:
        return "—"
    return f"{100 * x:.0f} %" if pct else f"{x:.2f}"


def ecrire_rapport(infos: dict) -> None:
    m = infos["mesures_test"]
    seuls = m.get("vecteurs_seuls", {})
    lignes = [f"# Rapport du modèle {infos['version']}", "",
              f"Entraîné le {infos['le'][:16].replace('T', ' ')} sur {infos['annotations']} commentaires annotés "
              f"({infos['apprentissage']} pour apprendre, {infos.get('reglage', 0)} pour régler, {infos['test']} mis "
              "de côté pour mesurer). Les mesures ci-dessous portent sur ces commentaires de test, que le modèle n'a "
              "pas vus.", ""]
    if infos.get("reseau"):
        lignes += [f"Réseau affiné : {infos['reseau']}. Poids du réseau dans le mélange : "
                   + ", ".join(f"{k} {v:.2f}" for k, v in infos.get("poids_reseau", {}).items()) + ".", ""]
    lignes += ["## Notes", "",
               "| Critère | Écart moyen (sur 20) | Corrélation de rang | Vecteurs seuls (corrélation) |",
               "|---|---|---|---|"]
    for c in CRITERES:
        lignes.append(f"| {c} | {_f(m[c]['ecart_moyen'])} | {_f(m[c]['correlation_rang'])} | "
                      f"{_f(seuls.get(c, {}).get('correlation_rang'))} |")
    lignes += ["", "## Reproches et éloges (critères 2 à 4)", "",
               "Un « reproche » est une note de 6 ou moins, un « éloge » une note de 14 ou plus. Le rappel dit quelle "
               "part de ces cas le modèle retrouve, la précision quelle part de ce qu'il signale est juste.", "",
               "| Critère | Reproches (n) | Rappel | Précision | Éloges (n) | Rappel | Précision |",
               "|---|---|---|---|---|---|---|"]
    for c in REPROCHES:
        x = m[c]
        lignes.append(f"| {c} | {x['reproche_n']} | {_f(x['reproche_rappel'], 1)} | {_f(x['reproche_precision'], 1)} | "
                      f"{x['eloge_n']} | {_f(x['eloge_rappel'], 1)} | {_f(x['eloge_precision'], 1)} |")
    lignes += ["", "## Parts (ce que lit la synthèse)", "",
               "Sur les commentaires de test qui parlent de Lisnard : part des notes ≤ 6 et ≥ 14, réelle et prédite.",
               "", "| Critère | ≤ 6 réel | ≤ 6 prédit | ≥ 14 réel | ≥ 14 prédit |", "|---|---|---|---|---|"]
    for c in CRITERES:
        x = m["parts"][c]
        lignes.append(f"| {c} | {_f(x['reel_bas'], 1)} | {_f(x['predit_bas'], 1)} | {_f(x['reel_haut'], 1)} | "
                      f"{_f(x['predit_haut'], 1)} |")
    lignes += ["", "## Cible", "",
               f"Exactitude (le commentaire parle-t-il de Lisnard ?) : {_f(m['cible']['exactitude'], 1)}"
               + (f" (vecteurs seuls : {_f(seuls['cible'], 1)})" if "cible" in seuls else "") + "."]
    if m.get("reponses"):
        x = m["reponses"]
        lignes += ["", f"Sur les {x['n']} réponses du test : écart moyen de {_f(x['ecart_tonalite'])} sur la "
                       f"tonalité, cible juste à {_f(x['cible'], 1)}."]
    lignes += ["", "## Fiabilité", "",
               "Elle dit surtout si la cible est sûre : les notes elles-mêmes ne sont pas beaucoup plus justes quand "
               "la fiabilité est bonne.", "",
               "| Fiabilité | Part des commentaires | Cible fausse | Écart moyen sur la tonalité |", "|---|---|---|---|"]
    for f, x in m["fiabilite"].items():
        lignes.append(f"| {f} | {_f(x['part'], 1)} | {_f(x.get('cible_fausse'), 1)} | {_f(x['ecart_tonalite'])} |")
    lignes += ["", "## Par source", "", "| Source | n | Écart tonalité | Écart pertinence |", "|---|---|---|---|"]
    for s, x in m["par_source"].items():
        lignes.append(f"| {s} | {x['n']} | {_f(x['ecart_tonalite'])} | {_f(x['ecart_pertinence'])} |")
    stockage.RAPPORT.write_text("\n".join(lignes) + "\n", encoding="utf-8")
