"""Ce que le site publie, calculé depuis donnees/analyse/ (corpus.csv + scores.csv + corrections.csv).

- les commentaires notés de YouTube et d'Instagram, sans auteur. WhatsApp n'est jamais publié : c'est une
  discussion privée d'adhérents, pas un espace public ;
- les publications (vidéos, posts) auxquelles ils répondent, pour le lien vers l'original ;
- « meta » : chiffres du projet, comptes suivis, qualité du modèle (page Le projet, listes de filtres) ;
- « cube » : les comptages par semaine × compte × type × cible × exploitable, d'où la page Statistiques recalcule
  tout instantanément, quels que soient les filtres.
"""
from collections import defaultdict
from datetime import date, timedelta

from analyse import stockage, versions
from analyse.criteres import CRITERES, REPROCHES
from commun.fichiers import lire_csv, lire_json
from commun.textes import maintenant

SOURCES_PUBLIEES = ("youtube", "instagram")
PERTINENCE_EXPLOITABLE = 5  # en dessous : ironie indécidable, émojis seuls, hors sujet (docs/GRILLE.md)
BAS, HAUT, ARGUMENTE = 6, 14, 12  # critique ou reproche ≤ 6, éloge ≥ 14, avis argumenté : pertinence ≥ 12
GROUPES = {"officiel": "Ses comptes", "media": "Médias", "commentateur": "Commentateurs",
           "soutien": "Chaînes de soutien"}


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
    notes = stockage.lire_scores()
    notes.update(stockage.lire_corrections())  # les corrections faites à la main priment
    corpus = [l for l in lire_csv(stockage.CORPUS) if l["source"] in SOURCES_PUBLIEES and l["cle"] in notes]
    publies = {l["cle"] for l in corpus}
    commentaires, publications = [], {}
    for l in corpus:
        s = notes[l["cle"]]
        pub = f"{l['source']}:{l['publication_id']}"
        if pub not in publications:
            publications[pub] = {"id": pub, "source": l["source"], "code": l["publication_id"],
                                 "compte": l["compte"], "titre": l["publication_titre"][:600] or None,
                                 "lien": l["publication_lien"] or None, "date": l["publication_date"][:19] or None}
        commentaires.append({
            "cle": l["cle"], "source": l["source"], "compte": l["compte"], "groupe": l["groupe"],
            "publication": pub, "date": l["date"][:19] or None, "semaine": lundi(l["date"]) if l["date"] else None,
            "reponse": l["type"] != "principal",
            "parent": l["parent_cle"] if l["parent_cle"] in publies else None,
            "likes": int(l["likes"] or 0), "texte": l["texte"],
            **{c: int(s[c]) for c in CRITERES}, "cible": s["cible"],
            "fiabilite": "corrigée" if "version" not in s else s.get("fiabilite") or None,
        })
    return commentaires, publications


def cube(commentaires: list[dict]) -> dict:
    """Comptages agrégés. Chaque cellule : [semaine, compte, réponse, autre, exploitable, n, sommes des 5 notes,
    puis pour tonalité, forme, système, idées : nombre ≤ 6 et nombre ≥ 14, puis nombre d'argumentés]."""
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
    cellules = defaultdict(lambda: [0] * (1 + len(CRITERES) + 2 * len(mesures) + 1))
    for c in commentaires:
        s = c["semaine"]
        if not s:
            continue
        cle = (index_semaine.get(s, 0) if s >= debut else 0, index_compte[c["compte"]], int(c["reponse"]),
               int(c["cible"] == "A"), int(c["pertinence"] >= PERTINENCE_EXPLOITABLE))
        x = cellules[cle]
        x[0] += 1
        for k, critere in enumerate(CRITERES):
            x[1 + k] += c[critere]
        for k, critere in enumerate(mesures):
            x[1 + len(CRITERES) + 2 * k] += c[critere] <= BAS
            x[2 + len(CRITERES) + 2 * k] += c[critere] >= HAUT
        x[-1] += c["pertinence"] >= ARGUMENTE
    return {"semaines": semaines,
            "comptes": [{"nom": n, "source": s, "groupe": g} for n, s, g in comptes],
            "colonnes": ["semaine", "compte", "reponse", "autre", "exploitable", "n", *CRITERES,
                         *[f"{q}_{c}" for c in mesures for q in ("bas", "haut")], "argumentes"],
            "cellules": [[*k, *v] for k, v in sorted(cellules.items())]}


def meta(commentaires: list[dict], publications: dict) -> dict:
    """Chiffres du projet et qualité du modèle en service, pour la page « Le projet »."""
    i = versions.infos() or {}
    m = i.get("mesures_test", {})
    par_compte = defaultdict(int)
    for c in commentaires:
        par_compte[(c["compte"], c["source"], c["groupe"])] += 1
    dates = sorted(c["date"] for c in commentaires if c["date"])
    constance = (lire_json(stockage.CONSTANCE, {}) or {}).get("ecart", {})
    return {
        "mis_a_jour": maintenant(),
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
