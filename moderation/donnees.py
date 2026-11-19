"""Fichiers de la modération et lecture des commentaires Facebook.

Les commentaires et leur classement par le modèle sont dans la table centrale donnees/analyse/corpus.csv (lignes
Facebook ; colonnes mod_categorie, mod_p_insultant, mod_p_question, mod_p_autre, mod_version, mod_le :
analyse/corpus.py). Le texte n'est recopié nulle part ailleurs.

donnees/moderation/
- annotations.csv : catégorie donnée à la lecture (cle, categorie, cible, jeu, poids, annote_le, par). Le jeu
  « test » ne sert qu'à mesurer le modèle ; « poids » ramène ce test à la population (voir mesurer() dans modele.py) ;
  « cible » (insultants seulement) : L si l'insulte vise David Lisnard, Nouvelle Énergie ou leurs soutiens, A sinon ;
  « par » : qui a lu (vide = Claude ; « gemini » = lu par Gemini, pas encore relu ; « gemini+claude » = relu) ;
- lots/lot_N.json et lot_N.txt : lots tirés pour l'annotation ;
- journal.log, avancement.json, EN_COURS (verrou de la tâche « moderation »).
modeles/moderation/ : le modèle en service et infos.json (version, mesures sur le test, historique).
"""
import random
import re

from analyse import corpus as cp
from commun.config import DONNEES, MODELES
from commun.fichiers import ecrire_csv, ecrire_json, lire_csv, lire_json
from commun.textes import maintenant

TACHE = "moderation"
DOSSIER = DONNEES / "moderation"
ANNOTATIONS = DOSSIER / "annotations.csv"
LOTS = DOSSIER / "lots"
JOURNAL = DOSSIER / "journal.log"
AVANCEMENT = DOSSIER / "avancement.json"
MODELE = MODELES / "moderation"
INFOS = MODELE / "infos.json"

CATEGORIES = ["autre", "insultant", "question"]  # ordre des sorties du modèle
# Lettres des réponses de lecture : L = insultant visant Lisnard / Nouvelle Énergie, I = insultant visant autre chose,
# Q = question ; tout le reste du lot est « autre ».
LETTRES = {"L": ("insultant", "L"), "I": ("insultant", "A"), "Q": ("question", "")}
CHAMPS_ANNOTATIONS = ["cle", "categorie", "cible", "jeu", "poids", "annote_le", "par"]
# Classement du modèle tel que le lit le reste du code → colonne du corpus.
EN_COLONNE = {"categorie": "mod_categorie", "p_insultant": "mod_p_insultant", "p_question": "mod_p_question",
              "p_autre": "mod_p_autre", "version": "mod_version", "classe_le": "mod_le"}
TAILLE_LOT = 250


def commentaires() -> list[dict]:
    """Les commentaires Facebook du corpus, sans les publications elles-mêmes ni texte vide (doublons compris : chacun
    est modéré). Chaque ligne garde les noms de la collecte qu'utilisent l'onglet et la table « moderation »
    (compte_source, commentaire_id, parent_id, auteur, auteur_id), le texte du commentaire auquel elle répond, et pour
    titre, quand la ligne n'en a pas, le texte de la publication."""
    lignes = [l for l in cp.lire() if l["source"] == "facebook"]
    publications = {l["publication_id"]: l["texte"] for l in lignes if l["cle"] == f"facebook:{l['publication_id']}"}
    noms = cp.auteurs(["facebook"])
    sortie = []
    for l in lignes:
        cid = l["cle"].split(":", 1)[1]
        if cid == l["publication_id"] or not l["texte"].strip():
            continue
        ident, nom = noms.get(l["cle"], ("", ""))
        sortie.append({**l, "compte_source": l["compte"], "commentaire_id": cid,
                       "parent_id": l["parent_cle"].split(":", 1)[1] if l["parent_cle"] else "",
                       "auteur_id": ident, "auteur": nom,
                       "publication_titre": l["publication_titre"] or publications.get(l["publication_id"], "")})
    return sortie


def lire_annotations() -> dict[str, dict]:
    return {l["cle"]: l for l in lire_csv(ANNOTATIONS)}


def lire_notes() -> dict[str, dict]:
    """Le classement du modèle, par clé : {cle, categorie, p_insultant, p_question, p_autre, version, classe_le}."""
    champs = list(EN_COLONNE.values())
    retour = {v: k for k, v in EN_COLONNE.items()}
    return {cle: {"cle": cle, **{retour[c]: v for c, v in l.items()}} for cle, l in cp.lire_colonnes(champs).items()}


def enregistrer_notes(notes: dict[str, dict]) -> int:
    """Écrit dans le corpus le classement de ces commentaires ({cle: {categorie, p_…, version, classe_le}})."""
    return cp.enregistrer({k: {EN_COLONNE[c]: v for c, v in n.items() if c in EN_COLONNE} for k, n in notes.items()},
                          list(EN_COLONNE.values()))


def textes() -> dict[str, str]:
    """Texte de chaque commentaire Facebook, par clé (les annotations n'en gardent pas de copie)."""
    return {l["cle"]: l["texte"] for l in commentaires()}


def infos_modele() -> dict | None:
    return lire_json(INFOS)


def ajouter_annotations(nouvelles: list[dict], remplacer: bool = False) -> int:
    """Ajoute des annotations ; une clé déjà annotée ne l'est jamais une deuxième fois (elle est ignorée), sauf
    remplacer=True : relecture d'un lot lu par Gemini (le jeu et le poids d'origine sont gardés)."""
    a = lire_annotations()
    n = 0
    for l in nouvelles:
        if l["cle"] in a and not remplacer:
            continue
        avant = a.get(l["cle"], {})
        a[l["cle"]] = {"annote_le": maintenant(), "poids": avant.get("poids", ""),
                       "jeu": avant.get("jeu", "entrainement"), **l}
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
            "a_relire": sorted(k for k, l in lots_lus().items() if l.get("par") == "gemini"),
            "par": {p or "claude": sum((a.get("par") or "") == p for a in ann.values())
                    for p in sorted({a.get("par") or "" for a in ann.values()})},
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
    print("Lus par : " + ", ".join(f"{p} {n}" for p, n in e["par"].items()))
    if e["a_relire"]:
        print(f"Lots lus par Gemini à relire par Claude : {', '.join(map(str, e['a_relire']))}"
              " (python -m moderation relire K lecture.txt)")
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
    (LOTS / f"lot_{k}.txt").write_text(texte_du_lot(lot), encoding="utf-8")
    print(f"Lot {k} ({mode}, {len(lot)} commentaires) : {LOTS / f'lot_{k}.txt'}")
    print("Réponse attendue dans un fichier texte : une ligne « L: numéros » (insultes visant Lisnard / Nouvelle "
          "Énergie), « I: numéros » (autres insultes) et « Q: numéros » (questions) ; le reste est « autre ». "
          "Pour Gemini : moderation/PROMPT_GEMINI.md, puis « noter K fichier --par gemini ».")
    return k


def _court(t: str, n: int) -> str:
    t = " ".join((t or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def texte_du_lot(lot: list[dict]) -> str:
    """Un bloc par commentaire : son numéro, la publication et, pour une réponse, le commentaire auquel il répond
    (le contexte, pour savoir qui est visé), puis le commentaire lui-même, seul à classer."""
    blocs = []
    for j, c in enumerate(lot, 1):
        b = [f"#{j}", f"Publication : {_court(c.get('publication_titre'), 200) or '(sans texte : photo, vidéo ou lien)'}"]
        if c.get("parent_texte"):
            b.append(f"En réponse à : {_court(c['parent_texte'], 250)}")
        b.append(f"COMMENTAIRE : {_court(c['texte'], 600)}")
        blocs.append("\n".join(b))
    return "\n\n".join(blocs) + "\n"


def lots_lus() -> dict[int, dict]:
    """Les lots tirés, par numéro (le fichier json : mode, commentaires, et « par » une fois lus)."""
    sortie = {}
    for f in LOTS.glob("lot_*.json"):
        if m := re.match(r"lot_(\d+)$", f.stem):
            sortie[int(m.group(1))] = lire_json(f) or {}
    return sortie


def lire_reponse(fichier: str, numeros: dict) -> dict[str, tuple[str, str]]:
    """Lit « L: 3, 17 », « I: 4 », « Q: 5, 9 » (une ligne par lettre ; tolère le gras Markdown, « #12 », les
    espaces et les autres lignes de Gemini). Rend numéro → (catégorie, cible)."""
    choix: dict[str, tuple[str, str]] = {}
    for ligne in open(fichier, encoding="utf-8-sig").read().splitlines():
        m = re.match(r"\s*[*_`>-]*\s*([LIQ])\s*[*_`]*\s*:\s*[*_`]*(.*)$", ligne)
        if not m:
            continue
        reste = re.sub(r"[*_`#.]", " ", m.group(2)).strip()
        if reste.lower() in ("", "aucun", "aucune", "rien", "néant", "none", "-"):
            continue
        for x in re.split(r"[,;\s]+", reste):
            if not x:
                continue
            if x not in numeros:
                raise SystemExit(f"Numéro {x!r} absent du lot (ligne « {ligne.strip()} »)")
            if x in choix and choix[x] != LETTRES[m.group(1)]:
                raise SystemExit(f"Numéro {x} donné à deux catégories")
            choix[x] = LETTRES[m.group(1)]
    return choix


def noter(k: int, fichier: str, test: bool = False, par: str = "", relire: bool = False) -> None:
    """Enregistre la lecture du lot k. `fichier` contient « L: … », « I: … » et « Q: … » ; le reste du lot est
    « autre ». Avec test=True, le lot rejoint le jeu de test (il ne servira qu'à mesurer). par="gemini" : lu par
    Gemini, à relire. relire=True : relecture par Claude d'un lot lu par Gemini ; remplace ses annotations et dit
    combien Gemini en avait jugé autrement."""
    f_lot = LOTS / f"lot_{k}.json"
    lot = lire_json(f_lot)
    if not lot:
        raise SystemExit(f"Lot {k} introuvable dans {LOTS}")
    if relire and lot.get("par") != "gemini":
        raise SystemExit(f"Le lot {k} n'a pas été lu par Gemini (par : {lot.get('par') or 'Claude'}).")
    if not relire and lot.get("lu_le"):
        raise SystemExit(f"Le lot {k} est déjà noté (le {lot['lu_le']}) ; une relecture passe par « relire ».")
    numeros = lot["commentaires"]
    choix = lire_reponse(fichier, numeros)
    avant = lire_annotations()
    qui = "gemini+claude" if relire else par
    nouvelles = []
    for j, cle in numeros.items():
        cat, cible = choix.get(j, ("autre", ""))
        jeu = avant.get(cle, {}).get("jeu", "entrainement") if relire else ("test" if test else "entrainement")
        nouvelles.append({"cle": cle, "categorie": cat, "cible": cible, "jeu": jeu, "par": qui})
    ecarts = [x for x in nouvelles if (a := avant.get(x["cle"])) and (a["categorie"], a.get("cible", "")) !=
              (x["categorie"], x["cible"])]
    n = ajouter_annotations(nouvelles, remplacer=relire)
    ecrire_json(f_lot, {**lot, "par": qui, "lu_le": maintenant()})
    nb = {c: sum(x["categorie"] == c for x in nouvelles) for c in CATEGORIES}
    vises = sum(x["cible"] == "L" for x in nouvelles)
    print(f"Lot {k} : {n} annotations enregistrées ({nb['insultant']} insultants dont {vises} visant Lisnard / "
          f"Nouvelle Énergie, {nb['question']} questions, {nb['autre']} autres){' — jeu de test' if test else ''}"
          f"{' — lu par ' + qui if qui else ''}.")
    if relire:
        print(f"Relecture : {len(ecarts)} corrections sur {len(nouvelles)} "
              f"({1 - len(ecarts) / max(len(nouvelles), 1):.0%} d'accord avec Gemini).")

