"""python -m verification synthese : registre_affirmations.csv (tous thèmes) et SYNTHESE.md (tous les verdicts)."""
import csv
from collections import Counter
from pathlib import Path

from .commun.chemins import REGISTRE, SYNTHESE, THEMES
from .controles import ECHELLE, lire_csv, verdicts


def ecrire_synthese() -> str:
    lignes, par_theme = [], []
    for d in sorted(p for p in THEMES.iterdir() if p.is_dir()):
        aff = d / "affirmations.csv"
        if not aff.exists():
            continue
        v = verdicts(d / "analyse.md") if (d / "analyse.md").exists() else {}
        rows = lire_csv(aff)
        for r in rows:
            r["verdict"] = v.get(r["id"], "en attente")
            r["dossier"] = d.name
        lignes += rows
        par_theme.append((d, rows))
    if not lignes:
        return "Aucun thème avec affirmations.csv"
    champs = list(lignes[0].keys())
    with open(REGISTRE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)
    total = Counter(r["verdict"] for r in lignes)
    md = ["# Synthèse de la vérification des affirmations de David Lisnard", "",
          f"{len(lignes)} affirmations et mesures dans {len(par_theme)} thème(s) terminé(s) ou en cours. Fichier "
          "complet : `registre_affirmations.csv`. Détail et preuves : `themes/<thème>/analyse.md`.", "",
          "| Verdict | Nombre |", "| --- | --- |"]
    md += [f"| {e.capitalize()} | {total.get(e, 0)} |" for e in ECHELLE]
    if total.get("en attente"):
        md.append(f"| En attente | {total['en attente']} |")
    for d, rows in par_theme:
        md += ["", f"## {rows[0]['theme']}", "", f"Analyse : `themes/{d.name}/analyse.md`", "",
               "| Id | Date | Citation | Verdict |", "| --- | --- | --- | --- |"]
        for r in rows:
            cit = r["citation"].replace("|", "/")
            cit = cit if len(cit) <= 140 else cit[:137] + "…"
            md.append(f"| {r['id']} | {r['date']} | « {cit} » | {r['verdict'].capitalize()} |")
    SYNTHESE.write_text("\n".join(md) + "\n", encoding="utf-8")
    return f"{len(lignes)} affirmations → {REGISTRE.name}, {SYNTHESE.name}"
