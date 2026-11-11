"""Regénère docs/FONCTIONNEMENT.pdf, le document illustré qui explique comment marche le projet.

    python -m docs                 PDF à jour (chiffres relus dans les données)
    python -m docs --html          écrit aussi docs/FONCTIONNEMENT_rendu.html (pour relire dans un navigateur)

La source modifiable est docs/FONCTIONNEMENT.html : texte, schémas et mise en page. Les {{nom}} y sont remplacés
par les chiffres ci-dessous (chiffres()), relus à chaque génération : nombre de commentaires, annotations, version
du modèle et ses mesures, lecture par thèmes. Le texte, lui, est écrit à la main et doit suivre toute modification de
structure ou de méthode du projet (règle dans CLAUDE.md).

Rendu : Chrome invisible (Playwright), comme les essais du site ; rien ne s'affiche à l'écran.
"""
import csv
import re
import sys
from collections import Counter
from datetime import date, datetime

from commun.config import DOCS, MODELES, perimetre
from commun.fichiers import lire_csv, lire_json

SOURCE = DOCS / "FONCTIONNEMENT.html"
PDF = DOCS / "FONCTIONNEMENT.pdf"
RENDU = DOCS / "FONCTIONNEMENT_rendu.html"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
COUCHES = 12  # couches d'e5-base
NOMS = {"tonalite": "Tonalité", "pertinence": "Pertinence", "systeme": "Système", "idees": "Idées",
        "forme": "Forme"}


def entier(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def decimal(x: float, chiffres: int = 2) -> str:
    return f"{x:.{chiffres}f}".replace(".", ",")


def pourcent(x: float) -> str:
    return f"{round(100 * x)} %"


def jour(texte: str) -> str:
    d = date.fromisoformat(texte[:10])
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]} {d.year}"


def puissance(x: float) -> str:
    """3e-05 → 3·10⁻⁵"""
    m, e = f"{x:e}".split("e")
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return f"{float(m):g}".replace(".", ",") + "·10" + str(int(e)).translate(sup)


def chiffres() -> dict[str, str]:
    from analyse import stockage, versions

    with open(stockage.CORPUS, encoding="utf-8-sig", newline="") as f:
        sources = Counter(l["source"] for l in csv.DictReader(f, delimiter=";"))
    i = versions.infos() or {}
    m = i.get("mesures_test", {})
    vec = m.get("vecteurs_seuls", {})
    reseau = lire_json(MODELES / i.get("reseau", "") / "infos.json", {}) or {}
    constance = lire_json(stockage.CONSTANCE, {}) or {}
    p = perimetre()
    insta = p.get("instagram", {})
    figes = int(reseau.get("figes", 4))
    longueurs = reseau.get("longueurs") or [128, 64, 20]
    from critiques import donnees as critiques
    th_themes = (lire_json(critiques.THEMES, {}) or {}).get("themes", {})
    th_ratt = lire_csv(critiques.RATTACHEMENTS) if critiques.RATTACHEMENTS.exists() else []
    th_lus = lire_csv(critiques.LUS) if critiques.LUS.exists() else []
    th_etat = critiques.resultats()  # sélection d'aujourd'hui et reste à lire
    from commun import sauvegarde
    from commun.config import DONNEES
    doublons = 0
    autres = Counter()
    with open(stockage.CORPUS, encoding="utf-8-sig", newline="") as f:
        for l in csv.DictReader(f, delimiter=";"):
            doublons += bool(l.get("doublon_de"))
    fichier_autres = DONNEES / "youtube" / "autres_chaines.csv"
    if fichier_autres.exists():
        autres = Counter(l["compte_source"] for l in lire_csv(fichier_autres))
    archive = sauvegarde.FICHIER.stat().st_size / 1e6 if sauvegarde.FICHIER.exists() else 0
    minutes = round(reseau.get("duree_min", 0))
    poids = i.get("poids_reseau", {})

    # Barre de répartition des annotations (largeur utile 840, de x = 10 à 850, 2 de jeu entre les blocs).
    app, reg, test = i.get("apprentissage", 0), i.get("reglage", 0), i.get("test", 0)
    total = max(app + reg + test, 1)
    l_app, l_reg = 840 * app / total - 2, 840 * reg / total - 2
    x_reg = 10 + l_app + 2
    x_test = x_reg + l_reg + 2

    couches = "".join(
        f'<rect x="{296 + 20 * k}" y="60" width="16" height="120" rx="3" '
        f'style="fill:var({"--gris" if k < figes else "--s-modele"})"/>' for k in range(COUCHES))

    barres = []
    for c in ("tonalite", "pertinence", "systeme", "idees", "forme"):
        a = (vec.get(c) or {}).get("correlation_rang")
        b = (m.get(c) or {}).get("correlation_rang")
        if a is None or b is None:
            continue
        barres.append(
            f'<div class="barre"><span class="nom">{NOMS[c]}</span><div class="piste">'
            f'<div class="trait t-vec" style="width:{100 * a:.1f}%"><span>{decimal(a)}</span></div>'
            f'<div class="trait t-ens" style="width:{100 * b:.1f}%"><span>{decimal(b)}</span></div></div></div>')

    return {
        "date": jour(date.today().isoformat()),
        "n_total": entier(sum(sources.values())),
        "n_youtube": entier(sources.get("youtube", 0)),
        "n_instagram": entier(sources.get("instagram", 0)),
        "n_whatsapp": entier(sources.get("whatsapp", 0)),
        "n_bluesky": entier(sources.get("bluesky", 0)),
        "bluesky_relire": str(p.get("bluesky", {}).get("relire_si_moins_de_jours", 7)),
        "n_autres_chaines": entier(len(autres)), "n_autres": entier(sum(autres.values())),
        "pages_recherche": str((p.get("youtube", {}).get("recherche") or {}).get("pages_par_lancement", 5)),
        "n_doublons": entier(doublons),
        "part_doublons": decimal(100 * doublons / max(1, sum(sources.values())), 1) + " %",
        "sauvegarde_mo": f"{archive:.0f} Mo" if archive else "à faire",
        "th_selection": entier(th_etat["n_selection"]), "th_a_lire": entier(th_etat["a_lire"]),
        "n_chaines": str(len(p.get("youtube", {}).get("chaines", []))),
        "comptes_instagram": ", ".join(f"@{c}" for c in insta.get("comptes", [])) or "aucun compte",
        "posts_par_lancement": str(insta.get("posts_par_lancement", "")),
        "relire_jours": str(insta.get("relire_si_moins_de_jours", "")),
        "annotations": entier(i.get("annotations", 0)),
        "apprentissage": entier(app), "reglage": entier(reg), "test": entier(test),
        "l_app": f"{l_app:.1f}", "x_reg": f"{x_reg:.1f}", "l_reg": f"{l_reg:.1f}",
        "x_test": f"{x_test:.1f}", "l_test": f"{850 - x_test:.1f}",
        "m_app": f"{10 + l_app / 2:.1f}", "m_reg": f"{min(x_reg + l_reg / 2, 780):.1f}",
        "version": i.get("version", "?"), "reseau": i.get("reseau", "?"),
        "entraine_le": jour(i["le"]) + " à " + datetime.fromisoformat(i["le"]).strftime("%H:%M") if i.get("le") else "?",
        "long_c": str(longueurs[0]), "long_p": str(longueurs[1]), "long_t": str(longueurs[2]),
        "th_lus": entier(len(th_lus)), "th_n": str(len(th_themes)), "th_ratt": entier(len(th_ratt)),
        "th_e": entier(sum(r["sens"] == "E" for r in th_ratt)), "th_c": entier(sum(r["sens"] == "C" for r in th_ratt)),
        "th_d": entier(sum(r["sens"] == "D" for r in th_ratt)),
        "figes": str(figes), "couches_ajustees": str(COUCHES - figes), "couches_svg": couches,
        "epoques": str(reseau.get("epoques", "?")), "lr": puissance(reseau.get("lr", 3e-5)),
        "duree": f"{minutes // 60} h {minutes % 60:02d}" if minutes >= 60 else f"{minutes} min",
        "poids_ton": pourcent(poids.get("tonalite", 0)), "poids_cible": pourcent(poids.get("cible", 0)),
        "barres": "".join(barres),
        "ecart_ton": decimal((m.get("tonalite") or {}).get("ecart_moyen", 0)),
        "cible": pourcent((m.get("cible") or {}).get("exactitude", 0)),
        "constance_n": entier(constance.get("n", 0)),
        "constance_cible": pourcent(constance.get("cible", 0)),
        "constance_ton": decimal((constance.get("ecart") or {}).get("tonalite", 0)),
    }


def remplir(modele: str, valeurs: dict[str, str]) -> str:
    inconnus = sorted(set(re.findall(r"\{\{(\w+)\}\}", modele)) - set(valeurs))
    if inconnus:
        raise SystemExit(f"Valeurs manquantes dans chiffres() : {', '.join(inconnus)}")
    return re.sub(r"\{\{(\w+)\}\}", lambda x: valeurs[x.group(1)], modele)


def generer(html_aussi: bool = False, journal=print) -> None:
    from playwright.sync_api import sync_playwright

    source = re.sub(r"<!--.*?-->", "", SOURCE.read_text(encoding="utf-8"), flags=re.S)  # notes pour qui modifie
    html = remplir(source, chiffres())
    if html_aussi:
        RENDU.write_text(html, encoding="utf-8")
    pied = ('<div style="width:100%;font-size:7pt;color:#8a94a3;font-family:Segoe UI,sans-serif;'
            'padding:0 14mm;display:flex;justify-content:space-between">'
            '<span>Projet DavidLisnard · comment marche l\'analyse</span>'
            '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        page = nav.new_page()
        page.set_content(html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(PDF), format="A4", print_background=True, prefer_css_page_size=True,
                 display_header_footer=True, header_template="<span></span>", footer_template=pied)
        nav.close()
    journal(f"{PDF} regénéré")


if __name__ == "__main__":
    generer("--html" in sys.argv[1:])
