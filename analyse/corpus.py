"""La table centrale des commentaires : donnees/analyse/corpus.csv, une ligne par commentaire collecté.

On ne touche jamais aux fichiers de collecte (donnees/<source>/*.csv) : on les lit et on écrit le corpus. Ce qui se
calcule sur un commentaire y est rangé en colonnes, plutôt que dans des fichiers à part qui recopieraient les clés et
les textes. Trois familles de colonnes :

1. Recopiées de la collecte (CHAMPS_COLLECTE), refaites à chaque mise à jour :
- cle : « source:commentaire_id », identifiant unique dans toute l'analyse ;
- le contexte utile à la lecture : compte, groupe du compte, titre de la publication, texte du commentaire parent ;
- l'auteur pseudonymisé (empreinte) : ni l'annotation ni le modèle n'ont besoin du nom ;
- texte_cle : empreinte du texte normalisé, pour ne noter qu'une fois les textes identiques (« Bravo ! ») ;
- likes : les « j'aime » les plus récents connus (donnees/<source>/likes.json, sinon ceux de la première collecte) ;
- doublon_de : pour un doublon, la clé du commentaire gardé à sa place ; vide sinon.
2. Les notes du modèle d'analyse (CHAMPS_NOTES, analyse/notation.py) : note_version, les cinq notes, cible, p_autre,
   fiabilite, note_le. Vides tant que le commentaire n'est pas noté.
3. Le classement du modèle de modération, commentaires Facebook seulement (CHAMPS_MODERATION, moderation/modele.py) :
   mod_categorie, mod_p_insultant, mod_p_question, mod_p_autre, mod_version, mod_le.

Les colonnes 2 et 3 se recalculent avec les modèles ; elles sont gardées d'une mise à jour à l'autre. Le travail fait
à la main (annotations, corrections, thèmes, catégories de modération) n'est pas ici : il reste dans de petits fichiers
reliés par la clé, sans texte recopié, qu'une réécriture du corpus ne peut pas abîmer.

Écritures. Deux tâches écrivent le corpus (notation, modération) : chacune n'écrit que ses colonnes, par enregistrer(),
qui relit le fichier sous un verrou (donnees/analyse/CORPUS_VERROU) juste avant de le réécrire. Deux tâches lancées
ensemble ne s'effacent donc pas.

Doublons. Un doublon est un commentaire au même texte qu'un autre du même auteur dans la même source : le même
compte qui colle « Au top 👌 » sous 164 publications, ou la même phrase 100 fois de suite. « Même texte » veut dire
même texte_cle : la casse, les accents, la ponctuation et les espaces ne comptent pas. On garde le premier publié ;
les suivants restent dans le corpus et sont notés, mais sortent de tout ce qui se compte (synthèse, site, thèmes).
Le même texte écrit par des personnes différentes n'est pas un doublon : 2 232 personnes ont écrit « 👏👏👏 », ce
sont 2 232 voix. Mesure du 2026-11-11 : 9 424 doublons sur 155 044 commentaires (6,1 %).

    python -m analyse.corpus            met à jour donnees/analyse/corpus.csv
"""
import csv
import hashlib
import os
import re
import sys
import time
from collections import Counter
from contextlib import contextmanager

from analyse.criteres import CRITERES
from analyse.stockage import ANALYSE, CORPUS
from commun.config import DONNEES, SOURCES, perimetre
from commun.fichiers import ecrire_csv, lire_csv, lire_json, remplacer
from commun.textes import sans_accents

# Ordre de lecture des sources : il fixe l'ordre des lignes du corpus, et donc le tirage des lots d'annotation.
# Une nouvelle source s'ajoute à la fin, pour ne pas déplacer les lignes des autres. WhatsApp a été retiré le 2026-11-12,
# Facebook (groupes publics) ajouté le même jour, X le 2026-11-13.
ORDRE_SOURCES = ["youtube", "instagram", "bluesky", "facebook", "x"]
CHAMPS_COLLECTE = ["cle", "source", "compte", "groupe", "publication_id", "publication_titre", "publication_lien",
                   "publication_date", "date", "type", "parent_cle", "parent_texte", "auteur_h", "likes", "texte",
                   "texte_cle", "doublon_de"]
CHAMPS_NOTES = ["note_version"] + CRITERES + ["cible", "p_autre", "fiabilite", "note_le"]
CHAMPS_MODERATION = ["mod_categorie", "mod_p_insultant", "mod_p_question", "mod_p_autre", "mod_version", "mod_le"]
CHAMPS_CALCULES = CHAMPS_NOTES + CHAMPS_MODERATION  # gardés quand le corpus est refait depuis la collecte
CHAMPS = CHAMPS_COLLECTE + CHAMPS_CALCULES
VERROU = ANALYSE / "CORPUS_VERROU"
GROUPE_PAR_DEFAUT = "autre"  # chaînes YouTube trouvées par la recherche, comptes retirés du périmètre, Bluesky
LIEN = re.compile(r"https?://\S+|www\.\S+")


def nettoyer(texte: str) -> str:
    """Espaces normalisées, liens remplacés par [lien] ; émojis gardés (ils portent souvent la tonalité)."""
    return " ".join(LIEN.sub("[lien]", (texte or "").lstrip()).split())


def cle_texte(texte: str) -> str:
    t = re.sub(r"[^\w\s]", "", sans_accents(texte)) if re.search(r"\w", texte) else texte
    return hashlib.sha1(" ".join(t.split()).encode("utf-8")).hexdigest()[:16]


def groupes() -> dict[tuple[str, str], str]:
    """(source, compte) → groupe du compte : officiel, soutien, media, commentateur, autre."""
    p = perimetre()
    g = {("youtube", c["nom"]): c.get("groupe", "") for c in p["youtube"]["chaines"]}
    for c in p["instagram"]["comptes"]:
        g[("instagram", f"@{c}")] = "officiel" if c == "davidlisnard" else "autre"
    for c in (p.get("bluesky") or {}).get("comptes", []):  # comptes Bluesky suivis (la recherche reste « autre »)
        g[("bluesky", f"@{c['handle']}")] = c.get("groupe", "autre")
    fb = p.get("facebook") or {}
    for c in fb.get("groupes", []):  # groupes de soutiens : « soutien »
        g[("facebook", c["nom"])] = c.get("groupe", "soutien")
    for c in fb.get("pages", []):  # sa Page officielle : « officiel »
        g[("facebook", c["nom"])] = c.get("groupe", "officiel")
    for c in (p.get("x") or {}).get("comptes", []):  # comptes X suivis (la recherche reste « autre »)
        g[("x", f"@{c['pseudo']}")] = c.get("groupe", "autre")
    return g


def lire_collecte() -> list[dict]:
    grp = groupes()
    lignes = []
    for source in ORDRE_SOURCES:
        likes = lire_json(DONNEES / source / "likes.json", {}) or {}  # « j'aime » relevés depuis (collecte/depot.py)
        for f in sorted((DONNEES / source).glob("*.csv")):
            for l in lire_csv(f):
                if l["commentaire_id"] in likes:
                    l["likes"] = likes[l["commentaire_id"]]
                lignes.append(l)
    textes = {(l["source"], l["commentaire_id"]): nettoyer(l["texte"]) for l in lignes}
    corpus, vues = [], set()
    for l in lignes:
        cle = f"{l['source']}:{l['commentaire_id']}"
        if cle in vues:
            continue
        vues.add(cle)
        texte = nettoyer(l["texte"])
        parent = l.get("parent_id") or ""
        corpus.append({
            "cle": cle, "source": l["source"], "compte": l["compte_source"],
            "groupe": grp.get((l["source"], l["compte_source"]), GROUPE_PAR_DEFAUT),
            "publication_id": l["publication_id"], "publication_titre": nettoyer(l["publication_titre"])[:300],
            "publication_lien": l["publication_lien"], "publication_date": l["publication_date"],
            "date": l["date"], "type": l["type"],
            "parent_cle": f"{l['source']}:{parent}" if parent else "",
            "parent_texte": textes.get((l["source"], parent), "")[:500] if parent else "",
            "auteur_h": hashlib.sha1(f"{l['source']}|{l['auteur_id'] or l['auteur']}".encode()).hexdigest()[:10],
            "likes": l.get("likes", ""), "texte": texte, "texte_cle": cle_texte(texte), "doublon_de": "",
            **dict.fromkeys(CHAMPS_CALCULES, ""),
        })
    marquer_doublons(corpus)
    return corpus


def marquer_doublons(corpus: list[dict]) -> int:
    """Remplit doublon_de (voir l'en-tête du module) : même source, même auteur, même texte ; le premier publié est
    gardé (à date égale ou absente, le premier dans l'ordre du corpus). Renvoie le nombre de doublons."""
    premiers, n = {}, 0
    for l in sorted(corpus, key=lambda l: l["date"] or "9999"):  # tri stable : l'ordre du corpus départage
        if not l["texte"]:
            continue
        k = (l["source"], l["auteur_h"], l["texte_cle"])
        if k in premiers:
            l["doublon_de"] = premiers[k]
            n += 1
        else:
            premiers[k] = l["cle"]
    return n


def auteurs(sources=SOURCES) -> dict[str, tuple[str, str]]:
    """Clé du commentaire → (identifiant de l'auteur, nom affiché), lus dans les fichiers de collecte : le corpus ne
    garde qu'une empreinte (auteur_h). L'identifiant est celui de la plateforme, à défaut le nom (comme auteur_h).
    Seule lecture des noms d'auteurs du projet : le site (table privée utilisateurs), la modération et l'export
    Cloudflare (identifiant opaque) passent tous par ici."""
    sortie = {}
    for source in sources:
        for f in sorted((DONNEES / source).glob("*.csv")):
            for l in lire_csv(f):
                ident = (l.get("auteur_id") or l.get("auteur") or "").strip()
                if ident and l.get("commentaire_id"):
                    sortie.setdefault(f"{source}:{l['commentaire_id']}", (ident, (l.get("auteur") or "").strip()))
    return sortie


def lire() -> list[dict]:
    return lire_csv(CORPUS)


def lire_colonnes(champs: list[str]) -> dict[str, dict]:
    """{cle: {champ: valeur}} des lignes dont le premier des `champs` est rempli, sans garder tout le corpus en
    mémoire."""
    sortie = {}
    if not CORPUS.exists():
        return sortie
    with open(CORPUS, encoding="utf-8-sig", newline="") as h:
        for l in csv.DictReader(h, delimiter=";"):
            if l.get(champs[0]):
                sortie[l["cle"]] = {c: l.get(c) or "" for c in champs}
    return sortie


def _processus_vivant(pid: int) -> bool:
    import psutil
    try:
        return psutil.Process(pid).is_running()
    except psutil.Error:
        return False


@contextmanager
def verrou(attente_s: int = 1800):
    """Une seule écriture du corpus à la fois, entre processus. Un verrou laissé par un processus mort est repris."""
    limite = time.time() + attente_s
    while True:
        try:
            fd = os.open(VERROU, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                pid = int(VERROU.read_text() or 0)
            except (OSError, ValueError):
                pid = 0
            if pid and not _processus_vivant(pid):
                VERROU.unlink(missing_ok=True)
                continue
            if time.time() > limite:
                raise TimeoutError(f"corpus verrouillé par le processus {pid} depuis trop longtemps ({VERROU})")
            time.sleep(0.5)
    try:
        yield
    finally:
        VERROU.unlink(missing_ok=True)


def enregistrer(valeurs: dict[str, dict], champs: list[str]) -> int:
    """Écrit les colonnes `champs` des commentaires de `valeurs` ({cle: {champ: valeur}}), sans toucher aux autres
    colonnes ni aux autres lignes : le fichier est relu et réécrit ligne à ligne, sous verrou. Rend le nombre de
    lignes modifiées."""
    if not valeurs:
        return 0
    n = 0
    with verrou():
        tmp = CORPUS.with_suffix(".tmp")
        with open(CORPUS, encoding="utf-8-sig", newline="") as h, \
                open(tmp, "w", encoding="utf-8-sig", newline="") as s:
            w = csv.DictWriter(s, CHAMPS, delimiter=";", extrasaction="ignore", restval="")
            w.writeheader()
            for l in csv.DictReader(h, delimiter=";"):
                v = valeurs.get(l["cle"])
                if v is not None:
                    l.update({c: v.get(c, "") for c in champs})
                    n += 1
                w.writerow(l)
        remplacer(tmp, CORPUS)
    return n


def manquants(source: str) -> int:
    """Nombre de commentaires de cette source collectés mais pas encore dans le corpus."""
    collectes = {f"{source}:{l['commentaire_id']}" for f in (DONNEES / source).glob("*.csv") for l in lire_csv(f)
                 if l.get("commentaire_id")}
    return len(collectes - set(lire_colonnes(["cle"])))


def mettre_a_jour() -> list[dict]:
    """Refait le corpus depuis la collecte, en gardant les notes et le classement déjà calculés."""
    corpus = lire_collecte()
    with verrou():
        avant = lire_colonnes(["cle"] + CHAMPS_CALCULES)
        for l in corpus:
            if a := avant.get(l["cle"]):
                l.update({c: a[c] for c in CHAMPS_CALCULES})
        ecrire_csv(CORPUS, corpus, CHAMPS)
    return corpus


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    c = mettre_a_jour()
    print(f"{len(c)} commentaires → {CORPUS}")
    print(Counter(l["source"] for l in c), f"textes distincts : {len({l['texte_cle'] for l in c})}",
          f"doublons mis de côté : {sum(1 for l in c if l['doublon_de'])}")
