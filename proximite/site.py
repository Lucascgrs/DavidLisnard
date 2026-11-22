"""Site « Proximité des candidats » (python -m proximite site).

    python -m proximite site            régénère proximite/site/donnees.js
    python -m proximite site apercu     régénère, puis ouvre le site en local (http://localhost:8020)
    python -m proximite site deployer   régénère, puis met en ligne sur Vercel (projet « proximite-candidats »)

Le site est statique : une seule page (index.html) et ses scripts, écrits à la main dans proximite/site/ (css/, js/,
favicon.svg, vercel.json, robots.txt). Seul donnees.js est régénéré : les candidats et leurs programmes
(donnees/proximite/candidats.json), les positions et distances (positions.json, « python -m proximite calculer »),
les mesures notées (donnees/proximite/mesures/) et la grille (proximite/axes.py). Les programmes de référence
(REFERENCES de collecte.py, Emmanuel Macron 2017) y sont marqués « reference » : le site les montre à part.
"""
import functools
import http.server
import json
import webbrowser

from commun.fichiers import lire_json

from . import CANDIDATS, POSITIONS, SITE
from .axes import AXES, NOTE_MAX, NOTE_MIN, POLES, SOUS_THEMES
from .mesures import toutes
from .positions import calculer

PROJET_VERCEL = "proximite-candidats"

# Familles de candidatures de candidats2027.org → groupe de couleur sur le site (3 couleurs et un gris : au-delà,
# des points voisins de la carte ne se distinguent plus ; le nom de chaque candidat est toujours écrit à côté).
GROUPES = {"extreme-gauche": "gauche", "gauche": "gauche", "centre": "centre", "droite": "droite",
           "extreme-droite": "droite", "autres": "autres"}


def donnees() -> dict:
    infos = {c["slug"]: c for c in lire_json(CANDIDATS, {}).get("candidats", [])}
    positions = calculer(journal=lambda *_: None)
    par_candidat = {}
    for m in toutes():
        par_candidat.setdefault(m["candidat"], []).append(
            [m["sous_theme"], int(m["note"]) if m["note"] != "" else None, m["mesure"]])
    candidats = []
    for c in positions["candidats"]:
        i = infos.get(c["slug"], {})
        candidats.append({
            **c, "groupe": GROUPES.get(c["famille"], "autres"),
            "court": (i.get("nom") or c["nom"]) + (f" {i['annee']}" if i.get("annee") else ""),
            "annee": i.get("annee") or "",
            "programme": {"titre": i.get("programmeTitre") or "", "pdf": i.get("programmePdf") or "",
                          "source": i.get("programmeSource") or "", "en_ligne": i.get("programmeEnLigne") or "",
                          "pages": i.get("programmePages"), "publie_le": i.get("programmePublieLe") or ""},
            "liste": par_candidat.get(c["slug"], []),
        })
    en_attente = [{"nom": f"{c.get('prenom', '')} {c.get('nom', '')}".strip(), "parti": c.get("parti") or ""}
                  for c in infos.values() if not c.get("programme")]
    return {"genere_le": positions["calcule_le"], "source": "candidats2027.org",
            "export_du": lire_json(CANDIDATS, {}).get("export_du", ""),
            "note_min": NOTE_MIN, "note_max": NOTE_MAX, "distance_max": positions["distance_max"],
            "axes": AXES, "sous_themes": {k: {"axe": a, "nom": n, "moins": POLES.get(k, ("", ""))[0], "plus": POLES.get(k, ("", ""))[1]}
                            for k, (a, n) in SOUS_THEMES.items()},
            "candidats": candidats, "distances": positions["distances"], "en_attente": en_attente}


def generer(journal=print) -> None:
    d = donnees()
    (SITE / "donnees.js").write_text("window.DONNEES = " + json.dumps(d, ensure_ascii=False, separators=(",", ":"))
                                     + ";\n", encoding="utf-8", newline="\n")
    journal(f"   site : {len(d['candidats'])} candidats, {sum(len(c['liste']) for c in d['candidats'])} mesures "
            f"→ proximite/site/donnees.js")


def apercu(port: int = 8020) -> None:
    generer()
    gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), gestion) as serveur:
        print(f"Aperçu sur http://localhost:{port} (Ctrl+C pour arrêter)")
        webbrowser.open(f"http://localhost:{port}")
        serveur.serve_forever()


def deployer(journal=print) -> str:
    """Régénère puis met en ligne sur Vercel, avec le jeton du site public (config/web.json, vercel_jeton)."""
    from commentaires import acces
    from commentaires.vercel import Vercel
    generer(journal)
    a = acces.exiger("vercel_jeton")
    url = Vercel(a["vercel_jeton"]).deployer(SITE, journal, projet=PROJET_VERCEL)
    acces.sauver(proximite_url=url)
    journal(f"   en ligne : {url}")
    return url


def main(args: list[str]) -> None:
    action = args[0] if args else "generer"
    if action == "generer":
        generer()
    elif action == "apercu":
        apercu(int(args[1]) if len(args) > 1 else 8020)
    elif action == "deployer":
        deployer()
    else:
        raise SystemExit(f"Action inconnue : {action}\n{__doc__}")
