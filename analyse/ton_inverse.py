"""Ton inversé : part des commentaires de test où le modèle se trompe de camp (carte « Ton inversé » du document).

Sur les commentaires de test (jeux « test » et « test_rare ») que Claude a notés comme parlant de Lisnard (cible L),
une inversion est une tonalité de Claude de 6 ou moins (critique) notée 14 ou plus par le modèle (éloge), ou
l'inverse. Les notes du modèle sont celles de donnees/analyse/scores.csv : la mesure suit donc la version qui a noté
le corpus, sans rien recalculer. Mêmes seuils que le rapport du modèle (reproche ≤ 6, éloge ≥ 14).

    python -m analyse.ton_inverse
"""
import sys
from collections import Counter

from analyse import stockage
from commun.fichiers import lire_csv

CRITIQUE, ELOGE = 6, 14
ARGUMENTE = 12  # pertinence à partir de laquelle un commentaire est « argumenté » (même seuil que les thèmes)


def mesurer() -> dict:
    scores = {r["cle"]: r for r in lire_csv(stockage.SCORES)}
    tests = [a for a in lire_csv(stockage.ANNOTATION / "annotations.csv")
             if a["jeu"].startswith("test") and a["cible"] == "L" and a["cle"] in scores]

    def inverse(a):
        claude, modele = int(a["tonalite"]), float(scores[a["cle"]]["tonalite"])
        return (claude <= CRITIQUE and modele >= ELOGE) or (claude >= ELOGE and modele <= CRITIQUE)

    argumentes = [a for a in tests if int(a["pertinence"]) >= ARGUMENTE]
    versions = Counter(scores[a["cle"]]["version"] for a in tests)
    return {"n": sum(map(inverse, tests)), "total": len(tests),
            "n_arg": sum(map(inverse, argumentes)), "total_arg": len(argumentes),
            "version": versions.most_common(1)[0][0] if versions else "?", "versions": dict(versions)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    m = mesurer()
    part = 100 * m["n"] / m["total"] if m["total"] else 0
    print(f"Ton inversé ({m['version']}) : {m['n']} sur {m['total']} commentaires de test qui parlent de lui "
          f"({part:.1f} %) ; {m['n_arg']} sur {m['total_arg']} parmi les argumentés.")
    if len(m["versions"]) > 1:
        print(f"Attention : corpus noté par plusieurs versions {m['versions']} ; finir « python -m analyse » d'abord.")


if __name__ == "__main__":
    main()
