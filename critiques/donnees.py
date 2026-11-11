"""Les fichiers des thèmes, dans donnees/critiques/, et tout ce qui les lit ou les écrit.

- themes.json : la liste des thèmes ({id: nom, famille, définition, lot de création, synthèses par sens}),
  les anciens identifiants absorbés par une fusion (alias) et le journal des fusions ;
- rattachements.csv : une ligne par (texte, thème, sens) avec la phrase courte qui dit ce que le commentaire en dit ;
- lus.csv : les textes lus, même ceux qui n'abordent aucun thème (pour ne jamais les relire) ;
- lots/lot_NNN.csv : les commentaires de chaque lot ; notes/lot_NNN.txt : la lecture de Claude telle qu'écrite.

Un texte n'est lu qu'une fois, même s'il a été posté plusieurs fois : la clé « copie » ignore les mentions
« @pseudo » du début (un même texte collé en réponse à des dizaines de personnes reste un seul texte), la casse,
les accents, la ponctuation et ce qui suit les 300 premiers caractères (un même texte
légèrement retouché à la fin, collé plusieurs fois, reste un seul texte). On lit son représentant (le plus pertinent) et les comptages se font en textes
distincts, et aussi en auteurs distincts (empreinte anonyme auteur_h). Un texte lu reste rangé même si sa note change
ensuite et qu'il sortirait de la sélection.
"""
import hashlib
import re
from collections import Counter, defaultdict
from datetime import datetime

from analyse import stockage
from commun.config import DONNEES
from commun.fichiers import ecrire_csv, ecrire_json, lire_csv, lire_json
from commun.textes import abreger, sans_accents

DOSSIER = DONNEES / "critiques"
THEMES = DOSSIER / "themes.json"
RATTACHEMENTS = DOSSIER / "rattachements.csv"
LUS = DOSSIER / "lus.csv"
LOTS = DOSSIER / "lots"
NOTES = DOSSIER / "notes"

CHAMPS_RATT = ["cle", "copie", "theme", "sens", "resume", "lot", "le"]
CHAMPS_LUS = ["cle", "copie", "lot", "le"]
TAILLE_LOT = 100

# La sélection (choix de l'utilisateur, 2026-11-11)
PERTINENCE_MIN = 12
MOTS_MIN = 20
FIABILITES = {"bonne", "moyenne", "corrigée", "relue"}

SENS = {"E": "éloge", "C": "critique", "D": "doute ou question"}
# Sur quoi porte un thème. Les noms affichés disent le sujet en clair (retour d'un lecteur du site, 2026-11-11 :
# « Famille », « Toutes » et « Forme » ne se comprenaient pas) ; les clés, elles, ne changent pas.
FAMILLES = {"idees": "Ses idées", "forme": "Sa façon de s'exprimer", "positionnement": "Son positionnement politique",
            "personne": "Sa personne et son bilan", "strategie": "Sa stratégie et sa campagne",
            "autre": "Autres sujets"}


def maintenant() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normaliser(nom: str) -> str:
    return " ".join(sans_accents(nom).lower().replace("’", "'").split())


def mots(texte: str) -> int:
    return len(texte.split())


INVISIBLES = re.compile("[​-‏⁠﻿]")
MENTIONS = re.compile(r"^(?:\s*@[\w.\-]+[\s,:;]*)+")


def copie(texte: str) -> str:
    """Clé d'un texte pour repérer ses copies (voir l'en-tête du module)."""
    t = MENTIONS.sub("", INVISIBLES.sub("", texte or ""))
    t = " ".join(re.sub(r"[^\w]+", " ", sans_accents(t).lower()).split())
    return hashlib.sha1(t[:300].encode("utf-8")).hexdigest()[:16]  # le début suffit : variantes retouchées à la fin


# ---------------------------------------------------------------------------------------------- lecture / écriture

def lire_themes() -> dict:
    d = lire_json(THEMES, None) or {}
    d.setdefault("themes", {})
    d.setdefault("alias", {})
    d.setdefault("fusions", [])
    d.setdefault("prochain", 1)
    return d


def ecrire_themes(d: dict) -> None:
    d["maj"] = maintenant()
    ecrire_json(THEMES, d)


def rattachements() -> list[dict]:
    return lire_csv(RATTACHEMENTS)


def lus() -> list[dict]:
    return lire_csv(LUS)


def resoudre(d: dict, ident: str) -> str | None:
    """Identifiant courant d'un thème (suit les fusions)."""
    vus = set()
    while ident in d["alias"] and ident not in vus:
        vus.add(ident)
        ident = d["alias"][ident]
    return ident if ident in d["themes"] else None


# ---------------------------------------------------------------------------------------------- sélection et lots

def selection(corpus: list[dict] | None = None, notes: dict | None = None) -> dict[str, dict]:
    """Textes retenus : {copie: commentaire représentant (le plus pertinent, puis le plus ancien)}."""
    corpus = corpus if corpus is not None else lire_csv(stockage.CORPUS)
    notes = notes if notes is not None else stockage.lire_notes(corpus)
    choix = {}
    for l in corpus:
        s = notes.get(l["cle"])
        if not s or s["cible"] != "L" or int(s["pertinence"]) < PERTINENCE_MIN or mots(l["texte"]) < MOTS_MIN:
            continue
        if l.get("doublon_de"):  # même auteur, même texte, même source : seul le premier publié compte
            continue
        if (s.get("fiabilite") or "") not in FIABILITES:
            continue
        rang = (-int(s["pertinence"]), l["date"] or "9")
        k = copie(l["texte"])
        if k not in choix or rang < choix[k][0]:
            choix[k] = (rang, {**l, "_pertinence": int(s["pertinence"])})
    return {k: v[1] for k, v in choix.items()}


def numero_lot(chemin) -> int:
    return int(chemin.stem.split("_")[1])


def lots_existants() -> list[int]:
    return sorted(numero_lot(p) for p in LOTS.glob("lot_*.csv")) if LOTS.exists() else []


def tirer(n: int = TAILLE_LOT) -> int | None:
    """Prépare le prochain lot : n textes sélectionnés pas encore lus ni déjà tirés, les plus argumentés d'abord."""
    deja = {l["copie"] for l in lus()}
    for k in lots_existants():
        deja |= {l["copie"] for l in lire_csv(LOTS / f"lot_{k:03d}.csv")}
    choix = [l for k, l in selection().items() if k not in deja]
    if not choix:
        print("Rien de nouveau à lire : tous les commentaires sélectionnés ont été lus.")
        return None
    choix.sort(key=lambda l: (-l["_pertinence"], -mots(l["texte"]), l["cle"]))
    numero = (lots_existants() or [0])[-1] + 1
    lignes = [{"n": i + 1, "cle": l["cle"], "copie": copie(l["texte"])} for i, l in enumerate(choix[:n])]
    ecrire_csv(LOTS / f"lot_{numero:03d}.csv", lignes, ["n", "cle", "copie"])
    print(f"Lot {numero} : {len(lignes)} commentaires ({len(choix) - len(lignes)} restent à tirer).")
    return numero


def ligne_theme(t: dict, comptes: Counter) -> str:
    c = " ".join(f"{comptes[(t['id'], s)]}{s}" for s in SENS if comptes[(t["id"], s)])
    return f"{t['id']} {t['nom']} [{t['famille']}] {c}".rstrip()


def comptes_par_theme() -> Counter:
    return Counter((r["theme"], r["sens"]) for r in rattachements())


def liste(definitions: bool = True) -> None:
    d = lire_themes()
    comptes = comptes_par_theme()
    par_famille = defaultdict(list)
    for t in d["themes"].values():
        par_famille[t["famille"]].append(t)
    for f, nom in FAMILLES.items():
        if not par_famille[f]:
            continue
        print(f"== {nom}")
        for t in sorted(par_famille[f], key=lambda t: int(t["id"][1:])):
            print("  " + ligne_theme(t, comptes) + (f" :: {t['definition']}" if definitions else ""))


def voir(numero: int, depuis: int = 1, themes: bool = True) -> None:
    lot = lire_csv(LOTS / f"lot_{numero:03d}.csv")
    corpus = {l["cle"]: l for l in lire_csv(stockage.CORPUS)}
    if themes:
        liste(definitions=False)
        print()
    for item in lot[depuis - 1:]:
        l = corpus[item["cle"]]
        compte = l["compte"].replace("Nouvelle Énergie", "NE")[:22]
        ligne = f"{item['n']}. [{l['source'][:2]}|{compte}|{l['date'][:10]}]"
        if l["publication_titre"]:
            ligne += f" T:{abreger(l['publication_titre'], 70)}"
        if l["parent_texte"]:
            ligne += "\n   ↳ répond à : " + abreger(l["parent_texte"], 350)
        ligne += f"\n   » {abreger(l['texte'], 1800)}"
        print(ligne)


# ---------------------------------------------------------------------------------------------- enregistrement

DECLARATION = re.compile(r"^\+\s*(.+?)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*$")
RATTACHEMENT = re.compile(r"^(\d+)\s*\|\s*(.+?)\s*\|\s*([ECD])\s*\|\s*(.+?)\s*$")
AUCUN = re.compile(r"^(\d+)\s*\|\s*-\s*$")


def noter(numero: int, fichier: str) -> None:
    """Vérifie puis enregistre la lecture d'un lot. Rien n'est écrit s'il y a une erreur.

    Lignes du fichier :
        + Nom du thème | famille | définition d'une ligne      (déclare un thème nouveau)
        12 | T5 | C | phrase courte                           (le commentaire 12 critique le thème T5)
        12 | Nom du thème | E | phrase courte                 (par le nom, d'un thème existant ou déclaré)
        13 | -                                                (lu, n'aborde aucun thème)
    """
    lot = {int(l["n"]): l for l in lire_csv(LOTS / f"lot_{numero:03d}.csv")}
    if not lot:
        raise SystemExit(f"Lot {numero} introuvable.")
    d = lire_themes()
    par_nom = {normaliser(t["nom"]): i for i, t in d["themes"].items()}
    declares, liens, vides, erreurs = {}, [], set(), []
    texte = open(fichier, encoding="utf-8").read()
    for brut in texte.splitlines():
        ligne = brut.strip()
        if not ligne or ligne.startswith("//"):
            continue
        if m := DECLARATION.match(ligne):
            nom, famille, definition = m.groups()
            if famille not in FAMILLES:
                erreurs.append(f"famille inconnue « {famille} » : {ligne}")
            elif normaliser(nom) in par_nom or normaliser(nom) in declares:
                erreurs.append(f"thème déjà existant ou déclaré deux fois : {nom}")
            else:
                declares[normaliser(nom)] = {"nom": nom, "famille": famille, "definition": definition}
        elif m := AUCUN.match(ligne):
            vides.add(int(m.group(1)))
        elif m := RATTACHEMENT.match(ligne):
            liens.append((int(m.group(1)), m.group(2), m.group(3), m.group(4), ligne))
        else:
            erreurs.append(f"illisible : {ligne}")
    resolus, utilises = [], set()
    for n, ref, sens, resume, ligne in liens:
        if n not in lot:
            erreurs.append(f"numéro hors du lot : {ligne}")
            continue
        if re.fullmatch(r"T\d+", ref):
            ident = resoudre(d, ref)
            if not ident:
                erreurs.append(f"thème inconnu {ref} : {ligne}")
                continue
            resolus.append((n, ident, sens, resume))
        elif normaliser(ref) in par_nom:
            resolus.append((n, par_nom[normaliser(ref)], sens, resume))
        elif normaliser(ref) in declares:
            utilises.add(normaliser(ref))
            resolus.append((n, "+" + normaliser(ref), sens, resume))
        else:
            erreurs.append(f"thème ni existant ni déclaré « {ref} » : {ligne}")
        if len(resume) > 220:
            erreurs.append(f"phrase trop longue ({len(resume)} caractères) : {ligne}")
    vus = {n for n, *_ in resolus} | vides
    manquants = sorted(set(lot) - vus)
    if manquants:
        erreurs.append(f"commentaires sans lecture : {manquants}")
    for k in set(declares) - utilises:
        erreurs.append(f"thème déclaré mais jamais utilisé : {declares[k]['nom']}")
    if erreurs:
        print("Rien n'a été enregistré :")
        for e in erreurs:
            print("  - " + e)
        raise SystemExit(1)

    # Relecture d'un lot déjà enregistré : on retire d'abord ce qu'il avait apporté.
    anciens = [r for r in rattachements() if r["lot"] == str(numero)]
    ratt = [r for r in rattachements() if r["lot"] != str(numero)]
    deja_lus = [r for r in lus() if r["lot"] != str(numero)]
    if anciens:
        restants = {r["theme"] for r in ratt}
        for i in [i for i, t in d["themes"].items() if t.get("cree") == numero and i not in restants]:
            del d["themes"][i]
    nouveaux = {}
    for k, t in declares.items():
        ident = f"T{d['prochain']}"
        d["prochain"] += 1
        d["themes"][ident] = {"id": ident, **t, "cree": numero, "synthese": {}}
        nouveaux[k] = ident
    le = maintenant()
    vus_liens = set()
    for n, ident, sens, resume in resolus:
        ident = nouveaux[ident[1:]] if ident.startswith("+") else ident
        item = lot[n]
        if (item["copie"], ident, sens) in vus_liens:
            continue
        vus_liens.add((item["copie"], ident, sens))
        ratt.append({"cle": item["cle"], "copie": item["copie"], "theme": ident, "sens": sens,
                     "resume": resume, "lot": numero, "le": le})
    for n, item in lot.items():
        deja_lus.append({"cle": item["cle"], "copie": item["copie"], "lot": numero, "le": le})
    ecrire_csv(RATTACHEMENTS, ratt, CHAMPS_RATT)
    ecrire_csv(LUS, deja_lus, CHAMPS_LUS)
    ecrire_themes(d)
    NOTES.mkdir(parents=True, exist_ok=True)
    (NOTES / f"lot_{numero:03d}.txt").write_text(texte, encoding="utf-8")
    sens = Counter(s for _, _, s, _ in resolus)
    print(f"Lot {numero} enregistré : {len(vus_liens)} rattachements ({', '.join(f'{v} {k}' for k, v in sens.items())}), "
          f"{len(nouveaux)} thèmes nouveaux, {len(vides)} sans thème. {len(d['themes'])} thèmes en tout.")


# ---------------------------------------------------------------------------------------------- fusion et synthèses

FUSION = re.compile(r"^((?:T\d+\s+)+)>\s*(.+?)\s*$")
RENOMMAGE = re.compile(r"^(T\d+)\s*=\s*(.+?)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*$")


def fusionner(fichier: str) -> None:
    """Applique des fusions et des renommages. Lignes :
        T10 T12 > Nouveau nom | famille | définition     (T12 rejoint T10, qui prend ce nom)
        T11 > T3                                         (T11 rejoint T3, qui garde son nom)
        T3 = Nom | famille | définition                  (renomme ou redéfinit T3)
    """
    d = lire_themes()
    ops, erreurs = [], []
    for brut in open(fichier, encoding="utf-8").read().splitlines():
        ligne = brut.strip()
        if not ligne or ligne.startswith("//"):
            continue
        if m := RENOMMAGE.match(ligne):
            ident, nom, famille, definition = m.groups()
            ops.append(("renommer", [ident], (nom, famille, definition), ligne))
        elif m := FUSION.match(ligne):
            ids = m.group(1).split()
            cible = m.group(2)
            if re.fullmatch(r"T\d+", cible):
                ops.append(("fusion", [cible] + ids, None, ligne))  # la cible garde son nom
            else:
                morceaux = [x.strip() for x in cible.split("|")]
                if len(morceaux) != 3:
                    erreurs.append(f"attendu « nom | famille | définition » : {ligne}")
                    continue
                ops.append(("fusion", ids, tuple(morceaux), ligne))
        else:
            erreurs.append(f"illisible : {ligne}")
    for _, ids, nouveau, ligne in ops:
        for i in ids:
            if not resoudre(d, i):
                erreurs.append(f"thème inconnu {i} : {ligne}")
        if nouveau and nouveau[1] not in FAMILLES:
            erreurs.append(f"famille inconnue : {ligne}")
    if erreurs:
        print("Rien n'a été appliqué :")
        for e in erreurs:
            print("  - " + e)
        raise SystemExit(1)
    ratt = rattachements()
    le = maintenant()
    for genre, ids, nouveau, ligne in ops:
        ids = [resoudre(d, i) for i in ids]
        garde, absorbes = ids[0], [i for i in ids[1:] if i != ids[0]]
        avant = {i: d["themes"][i]["nom"] for i in ids}
        if nouveau:
            t = d["themes"][garde]
            t["nom"], t["famille"], t["definition"] = nouveau
        for i in absorbes:
            d["alias"][i] = garde
            del d["themes"][i]
        if absorbes:
            for r in ratt:
                if r["theme"] in absorbes:
                    r["theme"] = garde
        d["fusions"].append({"le": le, "genre": genre, "garde": garde, "absorbes": absorbes, "anciens_noms": avant,
                             "nom": d["themes"][garde]["nom"]})
    # Un texte présent deux fois dans le même thème avec le même sens n'est gardé qu'une fois.
    vus, garde_ratt = set(), []
    for r in ratt:
        k = (r["copie"], r["theme"], r["sens"])
        if k not in vus:
            vus.add(k)
            garde_ratt.append(r)
    noms = Counter(normaliser(t["nom"]) for t in d["themes"].values())
    doubles = [n for n, c in noms.items() if c > 1]
    if doubles:
        raise SystemExit(f"Deux thèmes porteraient le même nom : {doubles}. Rien n'a été appliqué.")
    ecrire_csv(RATTACHEMENTS, garde_ratt, CHAMPS_RATT)
    ecrire_themes(d)
    print(f"{len(ops)} opérations appliquées ; {len(d['themes'])} thèmes, {len(garde_ratt)} rattachements "
          f"({len(ratt) - len(garde_ratt)} doublons retirés).")


def proches(n: int = 60) -> None:
    """Paires de thèmes candidates à la fusion : sens du nom et de la définition, et textes en commun."""
    import numpy as np
    from analyse.vecteurs import modele_langue
    d = lire_themes()
    ids = list(d["themes"])
    if len(ids) < 2:
        return
    textes = [f"query: {d['themes'][i]['nom']}. {d['themes'][i]['definition']}" for i in ids]
    v = modele_langue().encode(textes, normalize_embeddings=True, batch_size=64)
    sim = v @ v.T
    par_theme = defaultdict(set)
    for r in rattachements():
        par_theme[r["theme"]].add(r["copie"])
    paires = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            ea, eb = par_theme[ids[a]], par_theme[ids[b]]
            commun = len(ea & eb) / max(1, min(len(ea), len(eb)))
            paires.append((float(sim[a, b]) + 0.3 * commun, float(sim[a, b]), commun, ids[a], ids[b]))
    paires.sort(reverse=True)
    comptes = comptes_par_theme()
    for score, s, commun, a, b in paires[:n]:
        print(f"{score:.3f} (sens {s:.3f}, commun {commun:.2f})\n   {ligne_theme(d['themes'][a], comptes)}"
              f"\n   {ligne_theme(d['themes'][b], comptes)}")


SYNTHESE = re.compile(r"^(T\d+)\s+([ECD])\s*\|\s*(.+?)\s*$")


def syntheses(fichier: str) -> None:
    """Enregistre les synthèses rédigées : « T5 C | ce que disent les critiques de ce thème »."""
    d = lire_themes()
    n, erreurs = 0, []
    for brut in open(fichier, encoding="utf-8").read().splitlines():
        ligne = brut.strip()
        if not ligne or ligne.startswith("//"):
            continue
        m = SYNTHESE.match(ligne)
        if not m or not resoudre(d, m.group(1)):
            erreurs.append(ligne)
            continue
        d["themes"][resoudre(d, m.group(1))].setdefault("synthese", {})[m.group(2)] = m.group(3)
        n += 1
    if erreurs:
        print("Lignes ignorées :", *erreurs, sep="\n  ")
    ecrire_themes(d)
    print(f"{n} synthèses enregistrées.")


# ---------------------------------------------------------------------------------------------- résultats

def resultats(corpus: list[dict] | None = None) -> dict:
    """Tout ce qu'affichent l'interface et le site : thèmes, comptes par sens et par mois, rattachements."""
    d = lire_themes()
    corpus = corpus if corpus is not None else lire_csv(stockage.CORPUS)
    par_cle = {l["cle"]: l for l in corpus}
    themes = {}
    for i, t in d["themes"].items():
        themes[i] = {**t, "n": {s: 0 for s in SENS}, "mois": defaultdict(lambda: {s: 0 for s in SENS}),
                     "liens": [], "_auteurs": {s: set() for s in SENS}}
    for r in rattachements():
        t = themes.get(r["theme"])
        l = par_cle.get(r["cle"])
        if l and l.get("doublon_de"):  # lu avant la règle des doublons : on montre le commentaire gardé à sa place
            l = par_cle.get(l["doublon_de"], l)
        if not t or not l:
            continue
        t["n"][r["sens"]] += 1
        t["_auteurs"][r["sens"]].add(l.get("auteur_h") or r["cle"])
        if l["date"]:
            t["mois"][l["date"][:7]][r["sens"]] += 1
        t["liens"].append({"cle": l["cle"], "sens": r["sens"], "resume": r["resume"], "date": l["date"][:10],
                           "source": l["source"], "compte": l["compte"], "texte": l["texte"],
                           "auteur_h": l.get("auteur_h", "")})
    for t in themes.values():
        t["total"] = sum(t["n"].values())
        t["auteurs"] = {s: len(a) for s, a in t.pop("_auteurs").items()}
        t["mois"] = dict(sorted(t["mois"].items()))
        t["liens"].sort(key=lambda x: x["date"], reverse=True)
    sel = selection(corpus)
    lu = {l["copie"] for l in lus()}
    return {"themes": themes, "n_lus": len(lu), "n_selection": len(sel), "a_lire": len(set(sel) - lu),
            "n_rattachements": sum(t["total"] for t in themes.values()), "maj": d.get("maj"),
            "fusions": len(d["fusions"])}


def etat() -> None:
    r = resultats()
    n = Counter()
    for t in r["themes"].values():
        n.update(t["n"])
    print(f"{r['n_lus']} textes lus ; {r['n_selection']} sélectionnés aujourd'hui, {r['a_lire']} à lire ; "
          f"{len(r['themes'])} thèmes ; {r['n_rattachements']} rattachements "
          f"({', '.join(f'{n[s]} × {SENS[s]}' for s in SENS)}) ; {r['fusions']} fusions.")
