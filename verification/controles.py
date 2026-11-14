"""Contrôles automatiques de la vérification (python -m verification verifier [theme]).

Pour chaque thème :
1. chaque fichier de brut/ est inscrit dans sources.csv, et son empreinte SHA-256 correspond ;
2. chaque ligne de sources.csv pointe vers un fichier présent ;
3. chaque ligne de calculs/resultats.csv cite des id_source qui existent et une section de METHODE.md qui existe ;
4. chaque affirmation de affirmations.csv a un verdict dans analyse.md, pris dans l'échelle commune ;
5. chaque mesure chiffrée marquée ESTIMATION dans resultats.csv est signalée comme estimation dans analyse.md.
"""
import csv
import re
from pathlib import Path

from .commun.chemins import THEMES
from .commun.sources import sha256

ECHELLE = ["exact", "plutôt exact", "trompeur", "faux", "invérifiable", "opinion ou promesse"]
RX_VERDICT = re.compile(r"^## ([A-Z]+-\d+)\b.*?\n\n\*\*Verdict : ([^.*]+)", re.M | re.S)


def verdicts(analyse: Path) -> dict[str, str]:
    """{id: verdict} lus dans analyse.md (ligne « **Verdict : … » sous chaque titre « ## ID »)."""
    out = {}
    texte = analyse.read_text(encoding="utf-8")
    for bloc in re.split(r"(?m)^## ", texte)[1:]:
        m = re.match(r"([A-Z]+-\d+)\b", bloc)
        v = re.search(r"\*\*Verdict : ([^.*;,]+)", bloc)
        if m and v:
            brut = v.group(1).strip().lower()
            out[m.group(1)] = next((e for e in sorted(ECHELLE, key=len, reverse=True) if brut.startswith(e)), brut)
    return out


def lire_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verifier_theme(d: Path) -> list[str]:
    err = []
    cat_p, brut = d / "sources.csv", d / "brut"
    if not cat_p.exists():
        return [f"{d.name} : pas de sources.csv"]
    cat = {l["id_source"]: l for l in lire_csv(cat_p)}
    inscrits = {l["fichier"] for l in cat.values()}
    for f in brut.rglob("*"):
        if f.is_file():
            rel = "brut/" + f.relative_to(brut).as_posix()
            if rel not in inscrits:
                err.append(f"{d.name} : {rel} absent de sources.csv")
    for l in cat.values():
        f = d / l["fichier"]
        if not f.exists():
            err.append(f"{d.name} : {l['id_source']} → fichier manquant {l['fichier']}")
        elif sha256(f) != l["sha256"]:
            err.append(f"{d.name} : {l['id_source']} → empreinte différente (fichier modifié depuis le téléchargement)")
    res_p, meth_p = d / "calculs/resultats.csv", d / "calculs/METHODE.md"
    sections = set(re.findall(r"^## (M\d+)\b", meth_p.read_text(encoding="utf-8"), re.M)) if meth_p.exists() else set()
    estimations = set()
    if res_p.exists():
        for i, l in enumerate(lire_csv(res_p), 2):
            for s in re.split(r"\s*;\s*", l["sources"]):
                if s and s not in cat:
                    err.append(f"{d.name} : resultats.csv ligne {i} cite une source inconnue {s}")
            if l["methode"] not in sections:
                err.append(f"{d.name} : resultats.csv ligne {i} renvoie à une section absente ({l['methode']})")
            if "ESTIMATION" in l.get("note", ""):
                estimations.add(l["affirmation"])
    aff_p, an_p = d / "affirmations.csv", d / "analyse.md"
    if aff_p.exists() and an_p.exists():
        v = verdicts(an_p)
        texte = an_p.read_text(encoding="utf-8")
        for l in lire_csv(aff_p):
            if l["id"] not in v:
                err.append(f"{d.name} : {l['id']} sans verdict dans analyse.md")
            elif v[l["id"]] not in ECHELLE:
                err.append(f"{d.name} : {l['id']} verdict hors échelle « {v[l['id']]} »")
        for a in estimations:
            bloc = re.search(rf"^## {a}\b(.*?)(?=^## |\Z)", texte, re.M | re.S)
            if not bloc or "estimation" not in bloc.group(1).lower():
                err.append(f"{d.name} : {a} contient des estimations non signalées comme telles dans analyse.md")
    elif aff_p.exists():
        err.append(f"{d.name} : analyse.md manquant")
    return err


def verifier(theme: str | None = None) -> bool:
    dossiers = [d for d in sorted(THEMES.iterdir()) if d.is_dir()]
    if theme:
        dossiers = [d for d in dossiers if d.name == theme or d.name.split("_")[0] == theme.zfill(2)]
    erreurs = []
    for d in dossiers:
        e = verifier_theme(d)
        print(f"{d.name} : {'OK' if not e else f'{len(e)} problème(s)'}")
        erreurs += e
    for e in erreurs:
        print("  -", e)
    return not erreurs
