"""Lecture des programmes et enregistrement des mesures.

    python -m proximite lire <candidat> [page]       texte à lire, par pages d'environ 30 000 caractères
    python -m proximite noter <candidat> <fichier>   enregistre les mesures relevées (format ci-dessous)
    python -m proximite relire <candidat>            remet tous les documents du candidat « à lire »
    python -m proximite etat                         documents à lire, mesures par candidat

La lecture est faite par Claude, en entier : le code ne choisit aucun passage. « lire » montre tout le texte des
documents à lire (nouveaux ou modifiés), paragraphes reconstitués (les PDF coupent chaque ligne), sans les liens, les
numéros de page ni les paragraphes déjà vus dans un autre document du candidat (menus, pieds de page répétés).

Format du fichier de « noter » (une mesure par ligne, rédigée court et fidèlement, dans les mots du programme) :

    ## programme-securite.txt          le document d'où viennent les mesures qui suivent
    O1 +2 | Un état d'urgence narco dans les zones les plus touchées
    E1 -3 | Rétablir l'ISF
    H1 | Instaurer le référendum d'initiative citoyenne      (hors axes : pas de note)

Chaque document cité par « ## » est marqué lu (même sans mesure : il n'en contenait pas). Les mesures s'ajoutent à
donnees/proximite/mesures/<candidat>.csv ; celles d'un document relu après modification remplacent les anciennes.
"""
import re
from collections import Counter

from commun.fichiers import ecrire_csv, lire_csv
from commun.textes import maintenant

from . import DOCUMENTS, MESURES, TEXTES
from .axes import NOTE_MAX, NOTE_MIN, SOUS_THEMES, axe_de
from .collecte import CHAMPS_DOCS, a_lire

CHAMPS = ["id", "candidat", "document", "sous_theme", "axe", "note", "mesure", "note_le"]
TAILLE_PAGE = 30000

BRUIT = re.compile(r"https?://|www\.\w|^\[page \d+\]$|^\d{1,3}$|^(sources?|notes?)\s*:|^©", re.I)

# ---------------------------------------------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------------------------------------------

def paragraphes(texte: str) -> list[str]:
    """Paragraphes d'un texte extrait : les lignes coupées (PDF) sont recollées ; une ligne vide, une puce, une fin de
    phrase suivie d'une majuscule ou un titre court terminent un paragraphe."""
    sortie, courant = [], []

    def clore():
        if courant:
            sortie.append(" ".join(courant))
            courant.clear()

    for ligne in texte.splitlines():
        l = ligne.strip()
        if not l or BRUIT.search(l):
            clore()
            continue
        puce = bool(re.match(r"^(•|[-–]\s|\d{1,2}[.)]\s)", l))
        if puce or (courant and re.search(r"[.!?:;»]$", courant[-1]) and re.match(r"^[A-ZÀ-Ý«\d]", l)):
            clore()
        courant.append(l)
        if len(l) < 60 and not re.search(r"[,a-zà-ÿ’'-]$", l) and not puce:
            clore()
    clore()
    return [re.sub(r"-\s(?=[a-zà-ÿ])", "", " ".join(p.split())) for p in sortie]


def lecture(candidat: str) -> list[tuple[str, str]]:
    """(document, paragraphe) des documents à lire du candidat : tout le texte, sans rien choisir, seulement sans les
    paragraphes déjà vus dans un autre document du même candidat (menus, pieds de page répétés)."""
    docs = [d for d in a_lire() if d["candidat"] == candidat]
    vus, sortie = set(), []
    for d in docs:
        sortie.append((d["fichier"], ""))
        for p in paragraphes((TEXTES / d["fichier"]).read_text(encoding="utf-8")):
            if p not in vus:
                vus.add(p)
                sortie.append((d["fichier"], p))
    return sortie


def lire(candidat: str, page: int = 1) -> None:
    pages, courante, taille = [], [], 0
    for doc, p in lecture(candidat):
        bloc = f"\n## {doc}" if not p else p
        if taille + len(bloc) > TAILLE_PAGE and courante:
            pages.append(courante)
            courante, taille = [], 0
        courante.append(bloc)
        taille += len(bloc) + 1
    if courante:
        pages.append(courante)
    if not pages:
        print(f"Rien à lire pour {candidat}.")
        return
    print(f"[{candidat} · page {page}/{len(pages)}]")
    print("\n".join(pages[page - 1]))


# ---------------------------------------------------------------------------------------------------------------
# Enregistrement
# ---------------------------------------------------------------------------------------------------------------

RX_MESURE = re.compile(r"^([EOSH]\d)\s*([+-]?\d)?\s*\|\s*(.+)$")


def lire_fichier_notes(texte: str) -> tuple[list[str], list[dict]]:
    docs, mesures, doc, erreurs = [], [], None, []
    for n, ligne in enumerate(texte.splitlines(), 1):
        l = ligne.strip()
        if not l or l.startswith("#") and not l.startswith("## "):
            continue
        if l.startswith("## "):
            doc = l[3:].strip()
            docs.append(doc)
            continue
        m = RX_MESURE.match(l)
        if not m or doc is None:
            erreurs.append(f"ligne {n} illisible : {l[:80]}")
            continue
        code, note, texte_m = m.group(1), m.group(2), m.group(3).strip()
        if code not in SOUS_THEMES:
            erreurs.append(f"ligne {n} : sous-thème inconnu {code}")
            continue
        if axe_de(code) is None and note:
            erreurs.append(f"ligne {n} : {code} est hors axes, pas de note")
            continue
        if axe_de(code) and (note is None or not NOTE_MIN <= int(note) <= NOTE_MAX):
            erreurs.append(f"ligne {n} : note manquante ou hors de {NOTE_MIN}..{NOTE_MAX}")
            continue
        mesures.append({"document": doc, "sous_theme": code, "axe": axe_de(code) or "",
                        "note": str(int(note)) if note else "", "mesure": texte_m})
    if erreurs:
        raise SystemExit("Fichier refusé, rien n'est enregistré :\n  " + "\n  ".join(erreurs))
    return docs, mesures


def noter(candidat: str, chemin: str) -> None:
    from pathlib import Path
    docs_lus, nouvelles = lire_fichier_notes(Path(chemin).read_text(encoding="utf-8"))
    documents = lire_csv(DOCUMENTS)
    connus = {d["fichier"] for d in documents if d["candidat"] == candidat}
    inconnus = [d for d in docs_lus if d not in connus]
    if inconnus:
        raise SystemExit(f"Documents inconnus pour {candidat} : {', '.join(inconnus)}")
    fichier = MESURES / f"{candidat}.csv"
    anciennes = lire_csv(fichier)
    # Un document relu (modifié depuis sa lecture) remplace ses anciennes mesures. Un fichier de notes couvre donc
    # tout ce qui a été lu d'un document : on l'enregistre en une fois.
    remplaces = set(docs_lus) & {m["document"] for m in anciennes}
    gardees = [m for m in anciennes if m["document"] not in remplaces]
    numero = max((int(m["id"].split("-")[-1]) for m in anciennes), default=0)
    date = maintenant()
    for m in nouvelles:
        numero += 1
        m.update(id=f"{candidat}-{numero:04d}", candidat=candidat, note_le=date)
    ecrire_csv(fichier, gardees + nouvelles, CHAMPS)
    for d in documents:
        if d["candidat"] == candidat and d["fichier"] in docs_lus:
            d["lu_le"], d["empreinte_lue"] = date, d["empreinte"]
    ecrire_csv(DOCUMENTS, documents, CHAMPS_DOCS)
    print(f"{candidat} : {len(nouvelles)} mesures enregistrées, {len(docs_lus)} document(s) marqué(s) lu(s)"
          + (f", {len(remplaces)} relu(s) remplacé(s)" if remplaces else ""))


def relire(candidat: str) -> None:
    """Remet « à lire » tous les documents du candidat ; « noter » remplacera ensuite ses mesures document par
    document."""
    documents = lire_csv(DOCUMENTS)
    n = 0
    for d in documents:
        if d["candidat"] == candidat:
            d["lu_le"], d["empreinte_lue"] = "", ""
            n += 1
    ecrire_csv(DOCUMENTS, documents, CHAMPS_DOCS)
    print(f"{candidat} : {n} document(s) à relire")


def marquer_lu(candidat: str, fichier: str | None = None) -> None:
    documents = lire_csv(DOCUMENTS)
    for d in documents:
        if d["candidat"] == candidat and (fichier is None or d["fichier"] == fichier):
            d["lu_le"], d["empreinte_lue"] = maintenant(), d["empreinte"]
    ecrire_csv(DOCUMENTS, documents, CHAMPS_DOCS)


def toutes() -> list[dict]:
    return [m for f in sorted(MESURES.glob("*.csv")) for m in lire_csv(f)]


def etat() -> None:
    restant = Counter(d["candidat"] for d in a_lire())
    par = Counter(m["candidat"] for m in toutes())
    docs = Counter(d["candidat"] for d in lire_csv(DOCUMENTS))
    print(f"{'candidat':<22} {'documents':>9} {'à lire':>7} {'mesures':>8}")
    for c in sorted(docs):
        print(f"{c:<22} {docs[c]:>9} {restant[c]:>7} {par[c]:>8}")
