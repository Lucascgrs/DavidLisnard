"""Annotation : tirage des commentaires à noter, affichage par lots, enregistrement vérifié des notes.

Les notes suivent docs/GRILLE.md. Une annotation porte sur un texte distinct (texte_cle) vu dans un contexte
(le commentaire « représentant » tiré au sort) : elle vaut pour ce commentaire, et le modèle apprend sur lui.

    python -m analyse.annotation tirer-tour1           prépare les lots du premier tour (fait le 2026-11-08)
    python -m analyse.annotation tirer-actif N          N commentaires où le modèle hésite, ou loin de tout exemple
    python -m analyse.annotation tirer-reponses N       N réponses à lire avec leur parent (ironie, « exactement »…)
    python -m analyse.annotation tirer-visibles N       N commentaires mis en avant (argumentés, notes extrêmes)
    python -m analyse.annotation tirer-suspects         ceux dont le texte contredit la tonalité du modèle
    python -m analyse.annotation tirer-longs N          N commentaires longs (≥ 40 mots), argumentés, toutes sources
    python -m analyse.annotation tirer-hasard N [jeu]   N commentaires au hasard (jeu « test » : agrandit la mesure)
    … tirer-actif N --source facebook                   (et tirer-hasard) : seulement les commentaires d'une source,
                                                        pour une source nouvelle encore peu annotée
    python -m analyse.annotation voir 3 [depuis]        affiche le lot 3 (pour l'annotateur)
    python -m analyse.annotation noter 3 notes.txt      vérifie et enregistre les notes du lot 3
    python -m analyse.annotation etat                   où en est l'annotation

Format d'une ligne de notes : « n cible tonalite forme systeme idees pertinence [# remarque] »,
cible = L (parle de Lisnard, de son mouvement ou s'adresse à lui) ou A (autre chose),
par exemple « 12 L 16 10 10 13 12 # salue la baisse des impôts ».

Pendant une longue série, comparer de temps en temps les moyennes d'un lot récent avec celles des lots 1 à 17 :
sans repère, l'échelle glisse (voir « Garde-fou contre la dérive » dans docs/GRILLE.md).
"""
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

from analyse import stockage
from analyse.corpus import lire
from analyse.criteres import CRITERES
from commun.config import SOURCES
from commun.fichiers import ecrire_csv, lire_csv
from commun.textes import abreger, sans_accents

DOSSIER = stockage.ANNOTATION
LOTS = DOSSIER / "lots"
ANNOTATIONS = DOSSIER / "annotations.csv"
CHAMPS_NOTES = ["cle", "texte_cle", "lot", "jeu", "cible"] + CRITERES + ["remarque", "annotateur", "le"]
TAILLE_LOT = 100
LOTS_CONSTANCE = 900  # lots 900 et suivants : contrôle de constance (renotation à l'aveugle), hors apprentissage

MOTS = {
    "systeme": r"macron|systeme|enarque|\bena\b|elite|establishment|umps|\blr\b|republicains|sarko|\bump\b|meme moule|"
               r"recycl|vieux monde|caste|mondialis|technocrat|droite molle|bourgeois|comme les autres|politicien|"
               r"carriere|\bbis\b|macronie|macroniste|wauquiez|retailleau|philippe|pecresse|fillon|bayrou|centr",
    "forme": r"parle|voix|debit|charism|orateur|eloquen|elocution|endor|robot|monoton|ennuy|lunette|communi|presence|"
             r"articul|bafouill|souri|sympa|\bmou\b|fade|telegeni|posture|s.exprim|discours|calme|pose|clair|"
             r"convainc|prestance|stature|carrure|petit|tete|physique|style|ton\b",
    "idees": r"idee|programme|proposition|mesure|projet|liberal|irrealist|solution|reforme|fiscal|dette|impot|"
             r"retraite|econom|depense|fonctionnaire|smic|immigration|securite|ecolog|nucleaire|entreprise|"
             r"etat\b|charges|bureaucra|decentralis|maire|cannes",
}


def annotations() -> list[dict]:
    return lire_csv(ANNOTATIONS)


def numero_lot(chemin) -> int:
    return int(chemin.stem.split("_")[1])


def deja_tires() -> set[str]:
    return {l["texte_cle"] for f in LOTS.glob("lot_*.csv") for l in lire_csv(f)}


def _representants(corpus):
    """Un commentaire par texte distinct (tiré au hasard parmi ceux qui ont ce texte)."""
    par_texte = defaultdict(list)
    for l in corpus:
        if l["texte"].strip():
            par_texte[l["texte_cle"]].append(l)
    rnd = random.Random(7)
    return {k: rnd.choice(v) for k, v in par_texte.items()}


def _de_la_source(corpus: list[dict], source: str | None) -> list[dict]:
    if source and source not in SOURCES:
        raise SystemExit(f"source inconnue : {source} (possibles : {', '.join(SOURCES)})")
    return [l for l in corpus if l["source"] == source] if source else corpus


def _strate(l):
    if l["source"] == "youtube":
        return "youtube_" + ("media" if l["groupe"] == "media" else "officiel" if l["groupe"] == "officiel"
                             else "autres")
    return l["source"]


def _ecrire_lots(choisis: list[dict], premier: int):
    random.Random(premier).shuffle(choisis)  # test et entraînement mélangés : l'annotateur ne sait pas lequel
    n = premier
    for i in range(0, len(choisis), TAILLE_LOT):
        ecrire_csv(LOTS / f"lot_{n:03d}.csv", _numerote(choisis[i:i + TAILLE_LOT]),
                   ["n", "cle", "texte_cle", "jeu", "motif"])
        n += 1
    return n - premier


def _numerote(lignes):
    for i, l in enumerate(lignes, 1):
        l["n"] = i
    return lignes


def tirer_tour1():
    if list(LOTS.glob("lot_*.csv")):
        raise SystemExit("Le premier tour est déjà tiré.")
    reps = _representants(lire())
    rnd = random.Random(2026)
    par_strate = defaultdict(list)
    for k, l in reps.items():
        par_strate[_strate(l)].append(l)
    quotas = {"youtube_officiel": 260, "youtube_media": 300, "youtube_autres": 150, "instagram": 260}
    choisis, pris = [], set()
    # 1. Au hasard dans chaque strate, en sur-représentant un peu les textes longs (la moitié tirée parmi > 80 car.)
    for s, q in quotas.items():
        pool = par_strate[s]
        longs = [l for l in pool if len(l["texte"]) > 80]
        tirage = rnd.sample(longs, min(len(longs), q // 2))
        reste = [l for l in pool if l["texte_cle"] not in {t["texte_cle"] for t in tirage}]
        tirage += rnd.sample(reste, min(len(reste), q - len(tirage)))
        for l in tirage:
            choisis.append({"cle": l["cle"], "texte_cle": l["texte_cle"], "jeu": "", "motif": f"hasard:{s}"})
            pris.add(l["texte_cle"])
    # Échantillon de test : 300 tirés parmi ceux-là, jamais vus à l'entraînement.
    hasard = [c for c in choisis]
    for c in rnd.sample(hasard, 300):
        c["jeu"] = "test"
    for c in hasard:
        c["jeu"] = c["jeu"] or "entrainement"
    # 2. Ciblés sur les reproches rares (mots-clés), hors YouTube « autres » déjà bien couvert.
    for critere, n in (("systeme", 220), ("forme", 220), ("idees", 180)):
        motif = re.compile(MOTS[critere])
        pool = [l for k, l in reps.items() if k not in pris and 25 < len(l["texte"]) < 1500
                and motif.search(sans_accents(l["texte"]))]
        for l in rnd.sample(pool, min(n, len(pool))):
            choisis.append({"cle": l["cle"], "texte_cle": l["texte_cle"], "jeu": "entrainement",
                            "motif": f"mots:{critere}"})
            pris.add(l["texte_cle"])
    nb = _ecrire_lots(choisis, 1)
    print(f"{len(choisis)} commentaires en {nb} lots ; test : 300 ; motifs : {Counter(c['motif'] for c in choisis)}")


def tirer(cles_texte: list[str], motif: str, jeu: str = "entrainement"):
    """Ajoute des lots pour ces textes (tours d'apprentissage actif)."""
    reps = _representants(lire())
    numeros = [x for x in map(numero_lot, LOTS.glob("lot_*.csv")) if x < LOTS_CONSTANCE]
    premier = max(numeros, default=0) + 1
    choisis = [{"cle": reps[k]["cle"], "texte_cle": k, "jeu": jeu, "motif": motif}
               for k in cles_texte if k in reps]
    nb = _ecrire_lots(choisis, premier)
    print(f"{len(choisis)} commentaires en {nb} lots (à partir du lot {premier})")


def tirer_actif(n: int, source: str | None = None):
    """Tour d'apprentissage actif : n commentaires choisis par le modèle actuel.
    - la moitié là où ses deux méthodes divergent le plus (il hésite) ;
    - un quart parmi les plus éloignés de tout ce qui a déjà été annoté ;
    - un quart parmi ceux qu'il croit porteurs d'un reproche fort (forme, système, idées), pour les cas rares.
    source : seulement les commentaires de cette source (représentant pris dans cette source)."""
    import numpy as np
    from analyse.modele import Entrees, charger
    modele, _ = charger()
    entrees = Entrees()
    deja = deja_tires()
    reps = _representants(_de_la_source(entrees.corpus, source))
    cands = [l for k, l in reps.items() if k not in deja and k in entrees.textes.index and len(l["texte"]) > 15]
    p = modele.predire(entrees.matrice(cands))
    rnd = random.Random(len(deja))
    pris: list[str] = []

    def prendre(ordre, combien):
        for i in ordre:
            k = cands[i]["texte_cle"]
            if k not in pris:
                pris.append(k)
                combien -= 1
                if combien <= 0:
                    break

    prendre(np.argsort(-p["ecart"]), n // 2)
    prendre(np.argsort(p["proximite"]), n // 4)
    reproche = np.minimum(np.minimum(p["forme"], p["systeme"]), p["idees"])
    forts = np.where(reproche <= 7)[0]
    prendre(rnd.sample(list(forts), len(forts)), n - len(pris))
    tirer(pris, "actif")


IRONIE = (r"😂|🤣|😅|😆|🙄|🤡|mdr|lol|ptdr|\bbien sur\b|quel courage|\.\.\.|…|!!|\?!|bravo|genial|magnifique|"
          r"sauveur|\bmessie\b|grand homme|\bwaouh?\b|\bouah\b|evidemment|tellement|on y croit|c.est sur|hein|\"|«")


def tirer_reponses(n: int):
    """Réponses à lire avec leur parent : la moitié avec des indices d'ironie, l'autre au hasard parmi les réponses
    dont le parent parle de Lisnard (selon le modèle actuel)."""
    corpus = lire()
    scores = stockage.lire_scores()
    deja = deja_tires()
    reps = _representants(corpus)
    rnd = random.Random(len(deja) + 1)
    cands = [l for k, l in reps.items() if k not in deja and l["type"] == "réponse" and l["parent_texte"]
             and 3 <= len(l["texte"]) < 1200]
    parent_l = [l for l in cands if float(scores.get(l["parent_cle"], {}).get("p_autre", 1) or 1) < 0.5
                or re.search(r"lisnard", sans_accents(l["parent_texte"]))]
    ironiques = [l for l in parent_l if re.search(IRONIE, sans_accents(l["texte"]))]
    pris = rnd.sample(ironiques, min(len(ironiques), n // 2))
    vus = {l["texte_cle"] for l in pris}
    reste = [l for l in parent_l if l["texte_cle"] not in vus]
    pris += rnd.sample(reste, min(len(reste), n - len(pris)))
    print(f"{len(cands)} réponses candidates, {len(parent_l)} sous un parent sur Lisnard, {len(ironiques)} avec indices")
    tirer([l["texte_cle"] for l in pris], "reponses")


def tirer_visibles(n: int):
    """Les commentaires que le site et l'interface mettent en avant, pas encore relus : ceux que le modèle juge
    argumentés (pertinence ≥ 12), sur Lisnard, avec une note extrême (tonalité ≤ 6 ou ≥ 14, reproche ≤ 6 ou éloge
    ≥ 16). Ce sont eux qui sortent en tête des « Soutiens argumentés », des « Critiques argumentées » et des tris : une
    erreur inversée s'y voit tout de suite. Les plus argumentés d'abord. Le commentaire tiré est celui-là même (avec
    son parent), pas une autre copie du texte."""
    corpus = lire()
    scores = stockage.lire_scores()
    deja = deja_tires() | {a["texte_cle"] for a in annotations()}
    cands = {}
    for l in corpus:
        s = scores.get(l["cle"])
        if not s or l["source"] not in SOURCES or s["cible"] != "L" or l["texte_cle"] in deja:
            continue
        x = {c: int(s[c]) for c in CRITERES}
        if x["pertinence"] < 12:
            continue
        extreme = (x["tonalite"] <= 6 or x["tonalite"] >= 14
                   or any(x[c] <= 6 or x[c] >= 16 for c in ("forme", "systeme", "idees")))
        if extreme and (l["texte_cle"] not in cands or x["pertinence"] > cands[l["texte_cle"]][0]):
            cands[l["texte_cle"]] = (x["pertinence"], abs(x["tonalite"] - 10), l)
    ordre = sorted(cands.values(), key=lambda v: (-v[0], -v[1]))[:n]
    choisis = [{"cle": l["cle"], "texte_cle": l["texte_cle"], "jeu": "entrainement", "motif": "visible"}
               for _, _, l in ordre]
    numeros = [x for x in map(numero_lot, LOTS.glob("lot_*.csv")) if x < LOTS_CONSTANCE]
    premier = max(numeros, default=0) + 1
    nb = _ecrire_lots(choisis, premier)
    print(f"{len(cands)} candidats ; {len(choisis)} commentaires en {nb} lots (à partir du lot {premier})")


# Marques de critique dans un commentaire noté favorable, ou d'éloge dans un commentaire noté hostile : là où le
# modèle se trompe de sens (« … la conséquence est la destruction du public : c'est ça, un programme d'austérité ! »
# noté 15). Beaucoup de faux suspects (un soutien qui critique les autres), d'où la relecture.
CRITIQUE = (r"austerit|detrui|destruct|demantel|casser? (le|les|la|des)|cadeaux? (fiscaux|aux)|ultra.?riches|"
            r"plus riches|inegalit|bla.?bla|baratin|clone|macron bis|lr bis|charlatan|menteur|guignol|escroc|"
            r"imposteur|vendu|pantin|poulain|aucune (chance|credibilit|confiance)|jamais (je ne|voter)|"
            r"ne votera[is]? (jamais|pas)|non merci|surtout pas|ridicule|risible|pathetique|demago|populis|hors.?sol|"
            r"deconnect|mepris|arrogan|honte|catastroph|desastre|prive payant|precarit|anti.?social|"
            r"liberalisme sauvage|ultra.?liberal|neoliberal|thatcher|milei du pauvre|medef|bourges?\b|nantis|"
            r"sbires|recycl|meme moule|droite molle")
ELOGE = (r"bravo|merci (monsieur|mr|m\.|david)|je voterai pour (lui|vous)|lisnard president|notre (futur )?president|"
         r"soutien total|tout mon soutien|enfin un|le seul (qui|candidat)|excellent|formidable|j.adhere|continuez|"
         r"courage a vous")


def tirer_suspects():
    """Les commentaires sur Lisnard, assez pertinents pour être vus (≥ 10), dont le texte contredit la tonalité
    donnée par le modèle : favorable mais avec plus de marques de critique que d'éloge, ou l'inverse. Les plus
    contradictoires d'abord."""
    corpus = lire()
    scores = stockage.lire_scores()
    deja = deja_tires() | {a["texte_cle"] for a in annotations()}
    critique, eloge = re.compile(CRITIQUE), re.compile(ELOGE)
    cands = {}
    for l in corpus:
        s = scores.get(l["cle"])
        if (not s or l["source"] not in SOURCES or s["cible"] != "L" or l["texte_cle"] in deja
                or int(s["pertinence"]) < 10):
            continue
        t, ton = sans_accents(l["texte"]), int(s["tonalite"])
        nc, ne = len(critique.findall(t)), len(eloge.findall(t))
        force = nc - ne if ton >= 14 else ne - nc if ton <= 6 else 0
        if force > 0 and (ton >= 14 and nc or ton <= 6 and ne):
            cands.setdefault(l["texte_cle"], (force, l))
    ordre = sorted(cands.values(), key=lambda v: -v[0])
    choisis = [{"cle": l["cle"], "texte_cle": l["texte_cle"], "jeu": "entrainement", "motif": "visible"}
               for _, l in ordre]
    numeros = [x for x in map(numero_lot, LOTS.glob("lot_*.csv")) if x < LOTS_CONSTANCE]
    premier = max(numeros, default=0) + 1
    nb = _ecrire_lots(choisis, premier)
    print(f"{len(choisis)} suspects en {nb} lots (à partir du lot {premier})")


MOTS_LONG = 40
# Facebook (groupes de soutiens, ajouté le 2026-11-12) : une part à lui, prise sur YouTube et Instagram. X (ajouté le
# 2026-11-13) : 10 %, pris de même sur YouTube et Instagram.
PART_SOURCES = {"youtube": 0.35, "instagram": 0.28, "bluesky": 0.12, "facebook": 0.15, "x": 0.10}


def tirer_longs(n: int):
    """Commentaires longs (au moins 40 mots) pas encore annotés, ceux qui apprennent le plus au modèle et que la
    lecture par thèmes utilise. 90 % parmi ceux que le modèle juge sur Lisnard et argumentés (pertinence ≥ 10), 10 %
    parmi les autres longs (hors sujet, disputes) pour qu'il apprenne aussi à les reconnaître. Réparti entre les
    sources (PART_SOURCES, le reste reporté sur les autres si une source manque) et, dans chaque source, en tournant
    entre les comptes pour ne pas tout prendre sous les mêmes vidéos."""
    corpus = lire()
    scores = stockage.lire_scores()
    deja = deja_tires() | {a["texte_cle"] for a in annotations()}
    rnd = random.Random(len(deja) + 3)
    vus, cands = set(), defaultdict(lambda: defaultdict(list))
    for l in corpus:
        k = l["texte_cle"]
        if k in deja or k in vus or l.get("doublon_de") or len(l["texte"].split()) < MOTS_LONG or len(l["texte"]) > 4000:
            continue
        vus.add(k)
        s = scores.get(l["cle"])
        fort = bool(s) and s["cible"] == "L" and int(s["pertinence"]) >= 10
        cands[fort][l["source"]].append(l)

    def repartir(pool, combien):
        voulu = {src: round(combien * PART_SOURCES.get(src, 0)) for src in pool}
        manque = sum(max(0, v - len(pool[src])) for src, v in voulu.items())
        for src in sorted(pool, key=lambda x: -len(pool[x])):  # le manque d'une source va aux plus fournies
            libre = len(pool[src]) - voulu[src]
            if manque and libre > 0:
                plus = min(libre, manque)
                voulu[src] += plus
                manque -= plus
        pris = []
        for src, v in voulu.items():
            par_compte = defaultdict(list)
            for l in pool[src]:
                par_compte[l["compte"]].append(l)
            files = [rnd.sample(x, len(x)) for x in par_compte.values()]
            rnd.shuffle(files)
            pris_src = []
            while len(pris_src) < min(v, len(pool[src])):
                for f in files:
                    if f and len(pris_src) < v:
                        pris_src.append(f.pop())
            pris += pris_src
        return pris

    forts = repartir(cands[True], round(0.9 * n))
    autres = repartir(cands[False], n - len(forts))
    choisis = [{"cle": l["cle"], "texte_cle": l["texte_cle"], "jeu": "entrainement", "motif": "long"}
               for l in forts + autres]
    numeros = [x for x in map(numero_lot, LOTS.glob("lot_*.csv")) if x < LOTS_CONSTANCE]
    premier = max(numeros, default=0) + 1
    nb = _ecrire_lots(choisis, premier)
    print(f"{len(choisis)} longs en {nb} lots (à partir du lot {premier}) ; "
          f"{Counter(l['source'] for l in forts + autres)}")


def tirer_hasard(n: int, jeu: str, source: str | None = None):
    """n commentaires au hasard (jeu « test » : agrandit l'échantillon de mesure), d'une seule source si demandé."""
    deja = deja_tires()
    reps = _representants(_de_la_source(lire(), source))
    rnd = random.Random(len(deja) + 2)
    pool = [k for k in reps if k not in deja]
    tirer(rnd.sample(pool, n), f"hasard:{jeu}", jeu)


def voir(numero: int, depuis: int = 1):
    lot = lire_csv(LOTS / f"lot_{numero:03d}.csv")
    corpus = {l["cle"]: l for l in lire()}
    for item in lot[depuis - 1:]:
        l = corpus[item["cle"]]
        compte = l["compte"].replace("Nouvelle Énergie", "NE")[:22]
        ligne = f"{item['n']}. [{l['source'][:2]}|{compte}|{l['type'][:3]}]"
        if l["publication_titre"] and l["source"] == "youtube":
            ligne += f" T:{abreger(l['publication_titre'], 80)}"
        elif l["publication_titre"]:
            ligne += f" P:{abreger(l['publication_titre'], 60)}"
        if l["parent_texte"]:
            ligne += "\n   ↳ répond à : " + abreger(l["parent_texte"], 450)
        ligne += f"\n   » {abreger(l['texte'], 1500 if item.get('motif') in ('visible', 'long') else 600)}"
        print(ligne)


NOTE = re.compile(r"^\s*(\d+)\s+([LA])\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(?:#\s*(.*))?$")


def noter(numero: int, fichier: str, annotateur="claude"):
    lot = {int(l["n"]): l for l in lire_csv(LOTS / f"lot_{numero:03d}.csv")}
    nouvelles, erreurs = {}, []
    with open(fichier, encoding="utf-8") as h:
        for ligne in h:
            if not ligne.strip() or ligne.lstrip().startswith("//"):
                continue
            m = NOTE.match(ligne)
            if not m:
                erreurs.append(f"illisible : {ligne.strip()}")
                continue
            n, cible, *notes, remarque = m.groups()
            n, notes = int(n), [int(x) for x in notes]
            if n not in lot:
                erreurs.append(f"n° {n} absent du lot")
            elif any(not 0 <= x <= 20 for x in notes):
                erreurs.append(f"n° {n} : note hors de 0-20")
            elif cible == "A" and notes[:4] != [10, 10, 10, 10]:
                erreurs.append(f"n° {n} : cible A, la tonalité et les reproches doivent valoir 10")
            else:
                nouvelles[n] = (cible, notes, remarque or "")
    manquants = sorted(set(lot) - set(nouvelles))
    if manquants:
        erreurs.append(f"manquants : {manquants}")
    if erreurs:
        raise SystemExit("Lot non enregistré :\n  " + "\n  ".join(erreurs))
    toutes = [a for a in annotations() if not (a["lot"] == str(numero) and a["annotateur"] == annotateur)]
    le = datetime.now().isoformat(timespec="seconds")
    for n, (cible, notes, remarque) in sorted(nouvelles.items()):
        item = lot[n]
        toutes.append({"cle": item["cle"], "texte_cle": item["texte_cle"], "lot": numero, "jeu": item["jeu"],
                       "cible": cible, **dict(zip(CRITERES, notes)), "remarque": remarque,
                       "annotateur": annotateur, "le": le})
    ecrire_csv(ANNOTATIONS, toutes, CHAMPS_NOTES)
    print(f"lot {numero} enregistré : {len(nouvelles)} notes ; total {len(toutes)}")


def etat():
    a = annotations()
    lots = sorted(LOTS.glob("lot_*.csv"))
    faits = {int(x["lot"]) for x in a}
    print(f"{len(a)} annotations ; lots tirés {len(lots)} ; lots faits {sorted(faits)}")
    print("à faire :", [n for n in map(numero_lot, lots) if n not in faits and n < LOTS_CONSTANCE])
    if a:
        print(Counter(x["jeu"] for x in a), Counter(x["cible"] for x in a))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, *args = sys.argv[1:] or [""]
    source = None
    if "--source" in args:
        i = args.index("--source")
        source = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    if cmd == "tirer-tour1":
        tirer_tour1()
    elif cmd == "tirer-actif":
        tirer_actif(int(args[0]) if args else 500, source)
    elif cmd == "tirer-reponses":
        tirer_reponses(int(args[0]))
    elif cmd == "tirer-suspects":
        tirer_suspects()
    elif cmd == "tirer-longs":
        tirer_longs(int(args[0]))
    elif cmd == "tirer-visibles":
        tirer_visibles(int(args[0]))
    elif cmd == "tirer-hasard":
        tirer_hasard(int(args[0]), args[1] if len(args) > 1 else "entrainement", source)
    elif cmd == "voir":
        voir(int(args[0]), int(args[1]) if len(args) > 1 else 1)
    elif cmd == "noter":
        noter(int(args[0]), args[1])
    elif cmd == "etat":
        etat()
    else:
        raise SystemExit(__doc__)
