"""Fichiers de la modération et lecture des commentaires Facebook.

donnees/moderation/
- annotations.csv : catégorie donnée par Claude à la lecture (cle, categorie, jeu, poids, annote_le, texte). Le jeu
  « test » ne sert qu'à mesurer le modèle ; « poids » ramène ce test à la population (voir mesurer() dans modele.py) ;
- notes.csv : catégorie donnée par le modèle (cle, categorie, p_insultant, p_question, p_autre, version, classe_le) ;
- lots/lot_N.json et lot_N.txt : lots tirés pour l'annotation ;
- journal.log, avancement.json, EN_COURS (verrou de la tâche « moderation »).
modeles/moderation/ : le modèle en service et infos.json (version, mesures sur le test, historique).
"""
import random
import re

from commun.config import DONNEES, MODELES
from commun.fichiers import ecrire_csv, ecrire_json, lire_csv, lire_json
from commun.textes import maintenant

TACHE = "moderation"
DOSSIER = DONNEES / "moderation"
ANNOTATIONS = DOSSIER / "annotations.csv"
NOTES = DOSSIER / "notes.csv"
LOTS = DOSSIER / "lots"
JOURNAL = DOSSIER / "journal.log"
AVANCEMENT = DOSSIER / "avancement.json"
MODELE = MODELES / "moderation"
INFOS = MODELE / "infos.json"

CATEGORIES = ["autre", "insultant", "question"]  # ordre des sorties du modèle
LETTRES = {"I": "insultant", "Q": "question", "A": "autre"}
CHAMPS_ANNOTATIONS = ["cle", "categorie", "jeu", "poids", "annote_le", "texte"]
CHAMPS_NOTES = ["cle", "categorie", "p_insultant", "p_question", "p_autre", "version", "classe_le"]
TAILLE_LOT = 250


def commentaires() -> list[dict]:
    """Les commentaires Facebook collectés (donnees/facebook/*.csv), sans les publications elles-mêmes, sans texte
    vide ni doublon. Chaque ligne reçoit sa clé « facebook:<identifiant> », comme dans le corpus de l'analyse."""
    vus, sortie, publications = set(), [], {}
    for f in sorted((DONNEES / "facebook").glob("*.csv")):
        for l in lire_csv(f):
            cid = l.get("commentaire_id") or ""
            if cid and cid == l.get("publication_id"):
                publications[cid] = l.get("texte") or ""  # la publication elle-même : son texte sert de titre
                continue
            if not cid or not (l.get("texte") or "").strip() or cid in vus:
                continue
            vus.add(cid)
            l["cle"] = f"facebook:{cid}"
            sortie.append(l)
    for l in sortie:  # titre vide dans le CSV (ligne lue avant la publication) : texte de la publication
        if not (l.get("publication_titre") or "").strip():
            l["publication_titre"] = publications.get(l.get("publication_id"), "")
    return sortie


def lire_annotations() -> dict[str, dict]:
    return {l["cle"]: l for l in lire_csv(ANNOTATIONS)}


def lire_notes() -> dict[str, dict]:
    return {l["cle"]: l for l in lire_csv(NOTES)}


def infos_modele() -> dict | None:
    return lire_json(INFOS)


def ajouter_annotations(nouvelles: list[dict]) -> int:
    """Ajoute des annotations ; une clé déjà annotée ne l'est jamais une deuxième fois (elle est ignorée)."""
    a = lire_annotations()
    n = 0
    for l in nouvelles:
        if l["cle"] in a:
            continue
        a[l["cle"]] = {"annote_le": maintenant(), "poids": "", "jeu": "entrainement", **l}
        n += 1
    ecrire_csv(ANNOTATIONS, a.values(), CHAMPS_ANNOTATIONS)
    return n


def etat() -> dict:
    """Chiffres de l'onglet et de « python -m moderation etat »."""
    com = commentaires()
    notes, ann, i = lire_notes(), lire_annotations(), infos_modele() or {}
    v = i.get("version")
    classes = [n for c in com if (n := notes.get(c["cle"])) and n["version"] == v]
    return {"commentaires": len(com), "classes": len(classes), "a_classer": len(com) - len(classes),
            "insultants": sum(n["categorie"] == "insultant" for n in classes),
            "questions": sum(n["categorie"] == "question" for n in classes),
            "annotations": len(ann), "test": sum(a["jeu"] == "test" for a in ann.values()),
            "annotations_par_categorie": {c: sum(a["categorie"] == c for a in ann.values()) for c in CATEGORIES},
            "modele": i}


def afficher_etat() -> None:
    e = etat()
    i = e["modele"]
    print(f"Commentaires Facebook : {e['commentaires']}")
    print(f"Classés par le modèle {i.get('version', '(aucun)')} : {e['classes']} (à classer : {e['a_classer']})"
          f" — insultants {e['insultants']}, questions {e['questions']}")
    pc = e["annotations_par_categorie"]
    print(f"Annotés : {e['annotations']} dont {e['test']} gardés pour le test "
          f"(insultant {pc['insultant']}, question {pc['question']}, autre {pc['autre']})")
    if i:
        m = i["mesures"]
        print(f"Modèle {i['version']} entraîné le {i['le']} : accord {m['accord']:.0%} ; insultes {m['insultant']['justes']:.0%}"
              f" justes, {m['insultant']['trouves']:.0%} trouvées ; questions {m['question']['justes']:.0%} justes, "
              f"{m['question']['trouves']:.0%} trouvées")


# --- Annotation par lots ----------------------------------------------------------------------------------------

MODES = {
    "hasard": "au hasard, pour que les annotations représentent les commentaires",
    "questions": "ceux qui contiennent « ? » ou que le modèle croit être des questions (le point faible du modèle)",
    "insultes": "ceux que le modèle croit insultants (probabilité ≥ 0,2)",
    "doutes": "ceux où le modèle hésite (aucune catégorie au-dessus de 0,7)",
}


def tirer(n: int = TAILLE_LOT, mode: str = "hasard") -> int:
    """Prépare le lot suivant parmi les commentaires jamais annotés, et l'affiche (« numéro|texte »)."""
    if mode not in MODES:
        raise SystemExit(f"Mode inconnu : {mode} (au choix : {', '.join(MODES)})")
    ann, notes = lire_annotations(), lire_notes()
    # Les lots tirés mais pas encore notés réservent leurs commentaires : deux lots tirés à la suite ne se
    # chevauchent pas.
    reserves = {cle for f in LOTS.glob("lot_*.json") for cle in (lire_json(f) or {}).get("commentaires", {}).values()}
    reste = [c for c in commentaires() if c["cle"] not in ann and c["cle"] not in reserves]
    p = lambda c, k: float(notes.get(c["cle"], {}).get(k) or 0)  # noqa: E731
    if mode == "questions":
        reste = [c for c in reste if "?" in c["texte"] or p(c, "p_question") >= .2]
    elif mode == "insultes":
        reste = [c for c in reste if p(c, "p_insultant") >= .2]
    elif mode == "doutes":
        reste = [c for c in reste if c["cle"] in notes and max(p(c, k) for k in ("p_insultant", "p_question", "p_autre")) < .7]
    random.shuffle(reste)
    lot = reste[:n]
    if not lot:
        print("Rien à tirer : aucun commentaire non annoté ne correspond.")
        return 0
    LOTS.mkdir(parents=True, exist_ok=True)
    k = 1 + max([int(m.group(1)) for f in LOTS.glob("lot_*.json") if (m := re.match(r"lot_(\d+)", f.stem))] or [0])
    ecrire_json(LOTS / f"lot_{k}.json", {"mode": mode, "tire_le": maintenant(),
                                          "commentaires": {str(j): c["cle"] for j, c in enumerate(lot, 1)}})
    lignes = [f"{j}|" + c["texte"].replace("\n", " / ")[:400] for j, c in enumerate(lot, 1)]
    (LOTS / f"lot_{k}.txt").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"Lot {k} ({mode}, {len(lot)} commentaires) : {LOTS / f'lot_{k}.txt'}")
    print("Réponse attendue dans un fichier texte : une ligne « I: numéros » (insultants) et une ligne « Q: numéros »"
          " (questions), numéros séparés par des virgules ; tout le reste du lot est « autre ».")
    return k


def noter(k: int, fichier: str, test: bool = False) -> None:
    """Enregistre la lecture du lot k. `fichier` contient « I: 3, 17 » et « Q: 5, 9 » ; le reste du lot est
    « autre ». Avec test=True, le lot rejoint le jeu de test (il ne servira qu'à mesurer)."""
    lot = lire_json(LOTS / f"lot_{k}.json")
    if not lot:
        raise SystemExit(f"Lot {k} introuvable dans {LOTS}")
    numeros = lot["commentaires"]
    choix: dict[str, str] = {}
    for ligne in open(fichier, encoding="utf-8-sig").read().splitlines():
        m = re.match(r"\s*([IQ])\s*:\s*(.*)$", ligne)
        if not m:
            continue
        for x in re.split(r"[,\s]+", m.group(2).strip()):
            if not x:
                continue
            if x not in numeros:
                raise SystemExit(f"Numéro {x} absent du lot {k}")
            if x in choix and choix[x] != LETTRES[m.group(1)]:
                raise SystemExit(f"Numéro {x} donné à deux catégories")
            choix[x] = LETTRES[m.group(1)]
    textes = {c["cle"]: c["texte"] for c in commentaires()}
    nouvelles = [{"cle": cle, "categorie": choix.get(j, "autre"), "jeu": "test" if test else "entrainement",
                  "texte": textes.get(cle, "")} for j, cle in numeros.items()]
    n = ajouter_annotations(nouvelles)
    par = {c: sum(x["categorie"] == c for x in nouvelles) for c in CATEGORIES}
    print(f"Lot {k} : {n} annotations enregistrées ({par['insultant']} insultants, {par['question']} questions, "
          f"{par['autre']} autres){' — jeu de test' if test else ''}.")
