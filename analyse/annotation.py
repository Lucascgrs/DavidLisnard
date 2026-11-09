"""Annotation : tirage des commentaires à noter, affichage par lots, enregistrement vérifié des notes.

Les notes suivent docs/GRILLE.md. Une annotation porte sur un texte distinct (texte_cle) vu dans un contexte
(le commentaire « représentant » tiré au sort) : elle vaut pour ce commentaire, et le modèle apprend sur lui.

    python -m analyse.annotation tirer-tour1           prépare les lots du premier tour (fait le 2026-11-08)
    python -m analyse.annotation tirer-actif N          N commentaires où le modèle hésite, ou loin de tout exemple
    python -m analyse.annotation tirer-reponses N       N réponses à lire avec leur parent (ironie, « exactement »…)
    python -m analyse.annotation tirer-hasard N [jeu]   N commentaires au hasard (jeu « test » : agrandit la mesure)
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
    quotas = {"youtube_officiel": 260, "youtube_media": 300, "youtube_autres": 150, "instagram": 260, "whatsapp": 60}
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


def tirer_actif(n: int):
    """Tour d'apprentissage actif : n commentaires choisis par le modèle actuel.
    - la moitié là où ses deux méthodes divergent le plus (il hésite) ;
    - un quart parmi les plus éloignés de tout ce qui a déjà été annoté ;
    - un quart parmi ceux qu'il croit porteurs d'un reproche fort (forme, système, idées), pour les cas rares."""
    import numpy as np
    from analyse.modele import Entrees, charger
    modele, _ = charger()
    entrees = Entrees()
    deja = deja_tires()
    reps = _representants(entrees.corpus)
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


def tirer_hasard(n: int, jeu: str):
    """n commentaires au hasard (jeu « test » : agrandit l'échantillon de mesure)."""
    deja = deja_tires()
    reps = _representants(lire())
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
        ligne += f"\n   » {abreger(l['texte'], 600)}"
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
    if cmd == "tirer-tour1":
        tirer_tour1()
    elif cmd == "tirer-actif":
        tirer_actif(int(args[0]) if args else 500)
    elif cmd == "tirer-reponses":
        tirer_reponses(int(args[0]))
    elif cmd == "tirer-hasard":
        tirer_hasard(int(args[0]), args[1] if len(args) > 1 else "entrainement")
    elif cmd == "voir":
        voir(int(args[0]), int(args[1]) if len(args) > 1 else 1)
    elif cmd == "noter":
        noter(int(args[0]), args[1])
    elif cmd == "etat":
        etat()
    else:
        raise SystemExit(__doc__)
