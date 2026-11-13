"""Ce que le site publie, calculé depuis donnees/analyse/ (corpus.csv + scores.csv + corrections.csv).

- les commentaires notés de YouTube, d'Instagram, de Bluesky, des groupes Facebook publics et de X, sans auteur ni doublon (même auteur, même texte,
  même source : analyse/corpus.py) ;
- les publications (vidéos, posts) auxquelles ils répondent, pour le lien vers l'original ;
- « meta » : chiffres du projet, comptes suivis, qualité du modèle (page Le projet, listes de filtres) ;
- « cube » : les comptages par semaine × compte × type × cible × exploitable, d'où la page Statistiques recalcule
  tout instantanément, quels que soient les filtres. Chaque comptage existe deux fois : une voix par commentaire,
  et pondéré par les « j'aime » (colonnes « p_… » : un commentaire pèse 1 + ses « j'aime », lui-même et ceux qui
  l'approuvent) ;
- « themes » : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens (python -m
  critiques), recomptés sur les seules sources publiées, sans auteur (page Thèmes). Chaque critique ou doute porte
  sa catégorie (« cat », de 1 à 5 : critiques.CATEGORIES), que la page propose en filtre.
"""
from collections import defaultdict
from datetime import date, timedelta

from analyse import stockage, versions
from analyse.criteres import CRITERES, REPROCHES
from commun.config import DONNEES
from commun.fichiers import lire_csv, lire_json
from commun.textes import maintenant

SOURCES_PUBLIEES = ("youtube", "instagram", "bluesky", "facebook", "x")
PERTINENCE_EXPLOITABLE = 5  # en dessous : ironie indécidable, émojis seuls, hors sujet (docs/GRILLE.md)
BAS, HAUT, ARGUMENTE = 6, 14, 12  # critique ou reproche ≤ 6, éloge ≥ 14, avis argumenté : pertinence ≥ 12
GROUPES = {"officiel": "Ses comptes", "media": "Médias", "commentateur": "Commentateurs",
           "soutien": "Chaînes et groupes de soutien", "autre": "Autres comptes"}


def lundi(texte_date: str) -> str:
    """Lundi de la semaine d'une date « AAAA-MM-JJ… » (heure de Paris)."""
    d = date.fromisoformat(texte_date[:10])
    return (d - timedelta(days=d.weekday())).isoformat()


def debut_des_semaines(derniere: str) -> str:
    """Premier lundi détaillé sur le site : celui de la semaine du 1er janvier de l'année précédant la dernière
    donnée. Les semaines plus anciennes, clairsemées, sont regroupées en une seule case « avant »."""
    return lundi(f"{int(derniere[:4]) - 1}-01-01")


def charger() -> tuple[list[dict], dict[str, dict]]:
    """Commentaires publiables (une ligne par commentaire noté) et publications, au format des tables du site."""
    tout = lire_csv(stockage.CORPUS)
    notes = stockage.lire_notes(tout)  # corrections à la main, puis notes relues par Claude, puis modèle
    # Les doublons (même auteur, même texte, même source : analyse/corpus.py) ne sont pas publiés.
    garde = {l["cle"]: l.get("doublon_de") or l["cle"] for l in tout}
    corpus = [l for l in tout if l["source"] in SOURCES_PUBLIEES and l["cle"] in notes and not l.get("doublon_de")]
    publies = {l["cle"] for l in corpus}
    commentaires, publications = [], {}
    for l in corpus:
        s = notes[l["cle"]]
        pub = f"{l['source']}:{l['publication_id']}"
        if pub not in publications:
            publications[pub] = {"id": pub, "source": l["source"], "code": l["publication_id"],
                                 "compte": l["compte"], "titre": l["publication_titre"][:600] or None,
                                 "lien": l["publication_lien"] or None, "date": l["publication_date"][:19] or None}
        elif not publications[pub]["titre"] and l["publication_titre"]:
            # Bluesky, Facebook, X : le message de tête (le post) n'a pas de titre (son texte est le commentaire),
            # ses réponses l'ont.
            publications[pub]["titre"] = l["publication_titre"][:600]
        parent = garde.get(l["parent_cle"], "")  # une réponse à un doublon est rattachée au commentaire gardé
        commentaires.append({
            "cle": l["cle"], "source": l["source"], "compte": l["compte"], "groupe": l["groupe"],
            "publication": pub, "date": l["date"][:19] or None, "semaine": lundi(l["date"]) if l["date"] else None,
            "reponse": l["type"] != "principal",
            "parent": parent if parent in publies else None,
            "likes": int(l["likes"] or 0), "texte": l["texte"],
            **{c: int(s[c]) for c in CRITERES}, "cible": s["cible"],
            "fiabilite": s.get("fiabilite") or None,
        })
    return commentaires, publications


def cube(commentaires: list[dict]) -> dict:
    """Comptages agrégés. Chaque cellule : [semaine, compte, réponse, autre, exploitable, puis un bloc de mesures
    (n, sommes des 5 notes, pour tonalité, forme, système, idées : nombre ≤ 6 et nombre ≥ 14, nombre d'argumentés),
    puis le même bloc pondéré par les « j'aime » (colonnes « p_… », poids = 1 + j'aime)]."""
    derniere = max(c["semaine"] for c in commentaires if c["semaine"])
    debut = debut_des_semaines(derniere)
    semaines = ["avant"]
    d = date.fromisoformat(debut)
    while d.isoformat() <= derniere:
        semaines.append(d.isoformat())
        d += timedelta(days=7)
    index_semaine = {s: i for i, s in enumerate(semaines)}
    comptes = sorted({(c["compte"], c["source"], c["groupe"]) for c in commentaires},
                     key=lambda x: (x[1], x[0].lower()))
    index_compte = {x[0]: i for i, x in enumerate(comptes)}
    mesures = ("tonalite", *REPROCHES)
    bloc = 1 + len(CRITERES) + 2 * len(mesures) + 1
    cellules = defaultdict(lambda: [0] * (2 * bloc))
    for c in commentaires:
        s = c["semaine"]
        if not s:
            continue
        cle = (index_semaine.get(s, 0) if s >= debut else 0, index_compte[c["compte"]], int(c["reponse"]),
               int(c["cible"] == "A"), int(c["pertinence"] >= PERTINENCE_EXPLOITABLE))
        x = cellules[cle]
        for debut_bloc, poids in ((0, 1), (bloc, 1 + c["likes"])):
            x[debut_bloc] += poids
            for k, critere in enumerate(CRITERES):
                x[debut_bloc + 1 + k] += poids * c[critere]
            for k, critere in enumerate(mesures):
                x[debut_bloc + 1 + len(CRITERES) + 2 * k] += poids * (c[critere] <= BAS)
                x[debut_bloc + 2 + len(CRITERES) + 2 * k] += poids * (c[critere] >= HAUT)
            x[debut_bloc + bloc - 1] += poids * (c["pertinence"] >= ARGUMENTE)
    noms = ["n", *CRITERES, *[f"{q}_{c}" for c in mesures for q in ("bas", "haut")], "argumentes"]
    return {"semaines": semaines,
            "comptes": [{"nom": n, "source": s, "groupe": g} for n, s, g in comptes],
            "colonnes": ["semaine", "compte", "reponse", "autre", "exploitable", *noms, *[f"p_{n}" for n in noms]],
            "cellules": [[*k, *v] for k, v in sorted(cellules.items())]}


TEXTE_THEME = 400  # caractères du commentaire montrés sous chaque résumé


def themes() -> dict | None:
    """Thèmes de la lecture des commentaires (donnees/critiques/), comptés sur YouTube et Instagram seulement."""
    from critiques import donnees as critiques
    r = critiques.resultats()
    if not r["n_rattachements"]:
        return None
    sortie = []
    anonymes = {}  # auteur -> numéro sans signification, pour compter les auteurs distincts sur une période choisie
    for i, t in r["themes"].items():
        liens = [l for l in t["liens"] if l["source"] in SOURCES_PUBLIEES]  # déjà sans doublon (critiques.resultats)
        if not liens:
            continue
        n = {s: sum(l["sens"] == s for l in liens) for s in critiques.SENS}
        auteurs = {s: len({l["auteur_h"] or l["cle"] for l in liens if l["sens"] == s}) for s in critiques.SENS}
        mois = defaultdict(lambda: {s: 0 for s in critiques.SENS})
        for l in liens:
            if l["date"]:
                mois[l["date"][:7]][l["sens"]] += 1
        sortie.append({"id": i, "nom": t["nom"], "famille": t.get("famille", "autre"),
                       "definition": t.get("definition", ""), "synthese": t.get("synthese", {}),
                       "n": n, "auteurs": auteurs, "mois": dict(sorted(mois.items())),
                       "liens": [{"cle": l["cle"], "sens": l["sens"], "resume": l["resume"], "date": l["date"],
                                  **({"cat": l["categorie"]} if l["categorie"] else {}),
                                  "a": anonymes.setdefault(l["auteur_h"] or l["cle"], len(anonymes)),
                                  "source": l["source"], "compte": l["compte"],
                                  "texte": l["texte"][:TEXTE_THEME] + ("…" if len(l["texte"]) > TEXTE_THEME else "")}
                                 for l in liens]})
    return {"mis_a_jour": maintenant(), "maj_lecture": r.get("maj"), "familles": critiques.FAMILLES,
            "sens": critiques.SENS, "categories": critiques.CATEGORIES,
            "definitions_categories": critiques.DEFINITIONS_CATEGORIES, "n_lus": r["n_lus"], "n_selection": r["n_selection"], "a_lire": r["a_lire"],
            "regles": {"pertinence_min": critiques.PERTINENCE_MIN, "mots_min": critiques.MOTS_MIN},
            "themes": sortie}


def derniere_collecte() -> str | None:
    """Date du dernier lancement de collecte d'une source publiée (« 2026-11-11 22:17:27 », heure de Paris)."""
    dates = [((lire_json(DONNEES / s / "etat.json", {}) or {}).get("dernier") or {}).get("le") for s in SOURCES_PUBLIEES]
    return max((d for d in dates if d), default=None)


def meta(commentaires: list[dict], publications: dict) -> dict:
    """Chiffres du projet et qualité du modèle en service, pour la page « Le projet » et l'en-tête de chaque page
    (date de mise à jour des données, version du modèle)."""
    i = versions.infos() or {}
    m = i.get("mesures_test", {})
    par_compte = defaultdict(int)
    for c in commentaires:
        par_compte[(c["compte"], c["source"], c["groupe"])] += 1
    dates = sorted(c["date"] for c in commentaires if c["date"])
    constance = (lire_json(stockage.CONSTANCE, {}) or {}).get("ecart", {})
    return {
        "mis_a_jour": maintenant(),              # cette publication
        "derniere_collecte": derniere_collecte(),  # dernier passage de la collecte sur une source publiée
        "sources": list(SOURCES_PUBLIEES),
        "commentaires": len(commentaires),
        "reponses": sum(c["reponse"] for c in commentaires),
        "publications": len(publications),
        "par_source": {s: sum(1 for c in commentaires if c["source"] == s) for s in SOURCES_PUBLIEES},
        "premiere_date": dates[0], "derniere_date": dates[-1],
        "debut_par_source": {s: min((c["date"] for c in commentaires if c["source"] == s and c["date"]), default=None)
                             for s in SOURCES_PUBLIEES},
        "comptes": [{"nom": n, "source": s, "groupe": g, "n": k}
                    for (n, s, g), k in sorted(par_compte.items(), key=lambda x: -x[1])],
        "groupes": GROUPES,
        "modele": {
            "version": i.get("version"), "le": i.get("le"), "annotations": i.get("annotations"),
            "test": i.get("test"), "langue": i.get("modele_langue"),
            "correlation": {c: round(m[c]["correlation_rang"], 3) for c in CRITERES
                            if m.get(c, {}).get("correlation_rang") is not None},
            "ecart": {c: round(m[c]["ecart_moyen"], 2) for c in CRITERES if c in m},
            "constance": {c: round(v, 2) for c, v in constance.items()},
            "cible": round(m.get("cible", {}).get("exactitude", 0), 3),
            "reproches": {c: {"rappel": round(m[c].get("reproche_rappel") or 0, 2),
                              "precision": round(m[c].get("reproche_precision") or 0, 2),
                              "n": m[c].get("reproche_n")} for c in REPROCHES if c in m},
        },
    }
