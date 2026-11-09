"""Notation du corpus : chaque commentaire reçoit ses 5 notes (0-20), sa cible et une fiabilité.

Étapes : mise à jour de la copie de travail (donnees/analyse/corpus.csv), calcul des vecteurs manquants, notes par
le modèle en service. Résultat : donnees/analyse/scores.csv (une ligne par commentaire). Les notes produites par
une ancienne version du modèle sont remplacées quand le commentaire est renoté.
"""
import time

from analyse import corpus as cp
from analyse import stockage
from analyse.criteres import CRITERES
from commun.taches import verifier_arret
from commun.textes import maintenant

NOM = "analyse"  # nom de la tâche (verrou donnees/analyse/EN_COURS, arrêt donnees/analyse/ARRET)
TAILLE_MORCEAU = 5000  # notes enregistrées tous les 5 000 commentaires : un arrêt ne perd presque rien


def analyser(sources=None, du=None, au=None, refaire=False, journal=print) -> dict:
    """Note les commentaires choisis qui ne le sont pas encore par la version en service (tous si refaire)."""
    from analyse.modele import Entrees, charger
    debut = time.time()
    try:
        modele, infos = charger()
    except FileNotFoundError:
        raise SystemExit("Le modèle n'est pas encore entraîné (python -m analyse.ensemble tout).")
    version = infos["version"]
    stockage.avancement("copie des commentaires")
    journal("  mise à jour de la copie de travail des commentaires")
    corpus = cp.mettre_a_jour()
    choix = [l for l in corpus if (not sources or l["source"] in sources)
             and (not du or l["date"][:10] >= du) and (not au or l["date"][:10] <= au)]
    scores = stockage.lire_scores()
    a_noter = [l for l in choix if refaire or scores.get(l["cle"], {}).get("version") != version]
    journal(f"  {len(choix)} commentaires dans la sélection, {len(a_noter)} à noter par le modèle {version}")
    if not a_noter:
        stockage.avancement("terminé", 0, 0, version=version)
        return {"notes": 0, "selection": len(choix), "version": version}
    entrees = Entrees(corpus)
    entrees.completer_vecteurs(a_noter, journal, verifier_arret=lambda: verifier_arret(NOM),
                               avancement=stockage.avancement)
    le = maintenant()
    fait = 0
    for i in range(0, len(a_noter), TAILLE_MORCEAU):
        verifier_arret(NOM)
        morceau = a_noter[i:i + TAILLE_MORCEAU]
        p = modele.predire_lignes(morceau, entrees, avancement=lambda f, t, d, i=i: stockage.avancement(
            "notes (lecture fine)", i + f, len(a_noter), version=version))
        fiab = modele.fiabilite(p)
        for k, l in enumerate(morceau):
            scores[l["cle"]] = {"cle": l["cle"], "version": version,
                                **{c: int(round(float(p[c][k]))) for c in CRITERES},
                                "cible": "A" if p["p_autre"][k] > 0.5 else "L",
                                "p_autre": f"{p['p_autre'][k]:.2f}", "fiabilite": fiab[k], "le": le}
        fait += len(morceau)
        stockage.ecrire_scores(scores)
        stockage.avancement("notes", fait, len(a_noter), version=version)
        journal(f"    {fait}/{len(a_noter)} notés")
    stockage.avancement("terminé", fait, len(a_noter), version=version, duree_s=round(time.time() - debut))
    return {"notes": fait, "selection": len(choix), "version": version}
