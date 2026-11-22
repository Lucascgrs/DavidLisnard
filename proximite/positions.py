"""Des mesures aux positions (python -m proximite calculer) ; méthode : docs/GRILLE_PROXIMITE.md.

1. Note d'un sous-thème : moyenne des notes de ses mesures.
2. Position sur un axe : moyenne des notes des sous-thèmes de l'axe où le candidat a au moins une mesure (chaque
   sous-thème pèse autant, quel que soit le nombre de mesures).
3. Sans mesure sur un axe : position 0, signalée (« connu » faux).
4. Distance : euclidienne dans l'espace des trois axes ; aussi ramenée sur 100 (100 = deux coins opposés du cube).
"""
import math
from collections import defaultdict

from commun.fichiers import ecrire_json, lire_json
from commun.textes import maintenant

from . import CANDIDATS, POSITIONS
from .axes import AXES, NOTE_MAX, NOTE_MIN, SOUS_THEMES
from .mesures import toutes

DISTANCE_MAX = math.sqrt(len(AXES)) * (NOTE_MAX - NOTE_MIN)


def moyenne(valeurs):
    return sum(valeurs) / len(valeurs) if valeurs else None


def calculer(journal=print) -> dict:
    infos = {c["slug"]: c for c in lire_json(CANDIDATS, {}).get("candidats", [])}
    par_candidat = defaultdict(list)
    for m in toutes():
        par_candidat[m["candidat"]].append(m)

    candidats = []
    for slug, mesures in sorted(par_candidat.items()):
        notes_st = defaultdict(list)
        compte_st = defaultdict(int)
        for m in mesures:
            compte_st[m["sous_theme"]] += 1
            if m["note"] != "":
                notes_st[m["sous_theme"]].append(int(m["note"]))
        sous_themes = {code: {"note": round(moyenne(v), 2), "mesures": compte_st[code]}
                       for code, v in notes_st.items()}
        for code in compte_st:
            sous_themes.setdefault(code, {"note": None, "mesures": compte_st[code]})
        axes = {}
        for a in AXES:
            notes = [sous_themes[c]["note"] for c, (axe, _) in SOUS_THEMES.items()
                     if axe == a and c in sous_themes and sous_themes[c]["note"] is not None]
            axes[a] = {"position": round(moyenne(notes), 2) if notes else 0.0, "connu": bool(notes),
                       "sous_themes": len(notes),
                       "mesures": sum(sous_themes[c]["mesures"] for c, (axe, _) in SOUS_THEMES.items()
                                      if axe == a and c in sous_themes)}
        i = infos.get(slug, {})
        nom = f"{i.get('prenom', '')} {i.get('nom', slug)}".strip() + (f" ({i['annee']})" if i.get("annee") else "")
        candidats.append({"slug": slug, "nom": nom, "reference": bool(i.get("reference")),
                          "parti": i.get("parti") or "", "parti_court": i.get("partiCourt") or "",
                          "famille": i.get("famille") or "", "mesures": len(mesures),
                          "axes": axes, "sous_themes": sous_themes})

    distances = {}
    for a in candidats:
        for b in candidats:
            d = math.sqrt(sum((a["axes"][k]["position"] - b["axes"][k]["position"]) ** 2 for k in AXES))
            distances.setdefault(a["slug"], {})[b["slug"]] = round(d, 2)

    resultat = {"calcule_le": maintenant(), "distance_max": round(DISTANCE_MAX, 2), "candidats": candidats,
                "distances": distances}
    ecrire_json(POSITIONS, resultat)
    for c in candidats:
        pos = "  ".join(f"{k} {c['axes'][k]['position']:+.2f}{'' if c['axes'][k]['connu'] else '?'}" for k in AXES)
        journal(f"   {c['slug']:<22} {c['mesures']:>5} mesures   {pos}")
    return resultat
