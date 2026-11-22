"""Collecte des programmes (python -m proximite collecter).

1. La liste des candidats vient de l'export ouvert de candidats2027.org (https://candidats2027.org/api/export) : nom,
   parti, famille, statut, et pour ceux qui ont publié leur programme, le PDF (copie hébergée par le site) ou la page
   officielle en ligne. Les candidatures terminées (retrait, primaire perdue) sont écartées.
2. Chaque programme est téléchargé : le PDF tel quel, ou la page officielle et, selon la recette du candidat
   (RECETTES), les sous-pages ou les PDF vers lesquels elle renvoie (un programme en chapitres, en thèmes…).
3. Le texte de chaque document est écrit dans donnees/proximite/textes/<candidat>/ et son empreinte notée dans
   documents.csv. Un document déjà lu dont l'empreinte n'a pas changé n'est pas à relire ; un document nouveau ou
   modifié l'est (python -m proximite etat).

Un candidat qui publie un programme apparaît dans l'export : relancer la collecte suffit, sauf si son site demande une
recette (sous-pages à suivre), à ajouter dans RECETTES.

4. Les programmes de référence (REFERENCES) ne viennent pas de l'export : d'anciens programmes, placés sur la carte pour
   comparaison (Emmanuel Macron en 2017). Ils sont collectés, lus et notés comme les autres, selon la même grille.
"""
import re
import time
from urllib.parse import urljoin, urlparse

import requests

from commun.fichiers import ecrire_csv, ecrire_json, lire_csv
from commun.textes import empreinte, maintenant

from . import BRUT, CANDIDATS, DOCUMENTS, TEXTES

EXPORT = "https://candidats2027.org/api/export"
SITE_C2027 = "https://candidats2027.org"
ENTETES = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/130.0 Safari/537.36", "Accept-Language": "fr-FR,fr;q=0.9"}
EN_LICE = {"declare", "primaire-droite"}  # statuts retenus ; « primaire-ps » (perdue), « retire »… sont écartés

# Candidat → expression des liens à suivre depuis sa page de programme (sous-pages ou PDF du programme lui-même).
# Sans recette : la page seule (ou le PDF seul).
RECETTES = {
    "jean-luc-melenchon": r"/programme/livre/[a-z0-9-]+/chapitre\d+$",
    "francois-ruffin": r"^https://nouspresident\.fr/(?!notre-programme|je-rejoins|partagez|mentions|wp-)[a-z0-9-]+/$",
    "edouard-philippe": r"^https://www\.edouardphilippe\.fr/programme/[a-z0-9-]+$",
    "david-lisnard": r"^/notre-programme/[a-z0-9-]+/$",
    "olivier-becht": r"/wp-content/uploads/livre/olivier-becht-projet-france-partie-\d+-[0-9a-f]+\.pdf$",
}
# Pages en ligne dont le PDF de candidats2027.org est préféré (la page n'est qu'un sommaire de liens).
PDF_D_ABORD = {"emmanuel-dubuisson"}

# Programmes de référence, hors de l'export : un ancien programme placé sur la carte pour comparaison. Même lecture, même
# grille ; le site les montre à part (« pour comparaison ») et ajoute l'année au nom.
REFERENCES = [
    {"slug": "emmanuel-macron-2017", "prenom": "Emmanuel", "nom": "Macron", "parti": "En marche !",
     "partiCourt": "EM", "famille": "centre", "statut": "reference", "annee": "2017", "photo": None,
     "programmeTitre": "Programme d'Emmanuel Macron · présidentielle 2017", "programmePublieLe": "2017-03-02",
     "programmePages": None,
     "programmePdf": "https://storage.googleapis.com/en-marche-fr/COMMUNICATION/Programme-Emmanuel-Macron.pdf",
     "programmeSource": None, "programmeEnLigne": None},
]

CHAMPS_DOCS = ["candidat", "url", "fichier", "type", "empreinte", "caracteres", "telecharge_le", "lu_le",
               "empreinte_lue"]


def telecharger(url: str) -> requests.Response:
    for essai in range(4):
        try:
            r = requests.get(url, headers=ENTETES, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if essai == 3:
                raise
            time.sleep(2 * (essai + 1))


def texte_pdf(contenu: bytes) -> str:
    import pymupdf
    with pymupdf.open(stream=contenu, filetype="pdf") as doc:
        pages = [p.get_text("text") for p in doc]
    return nettoyer("\n".join(f"[page {i}]\n{t}" for i, t in enumerate(pages, 1)))


def texte_html(contenu: str) -> str:
    from bs4 import BeautifulSoup
    s = BeautifulSoup(contenu, "lxml")
    for t in s(["script", "style", "noscript", "nav", "header", "footer", "form", "svg", "iframe", "button"]):
        t.decompose()
    for t in s.select("[class*=cookie], [id*=cookie], [class*=consent], [id*=consent], [class*=share], "
                      "[class*=partage]"):
        t.decompose()
    corps = s.find("main") or s.find("article") or s.body or s
    for t in corps.find_all(["li", "h1", "h2", "h3", "h4", "h5", "p", "tr", "br", "div"]):
        t.insert_before("\n")
    for t in corps.find_all(["li"]):
        t.insert_before("• ")
    return nettoyer(corps.get_text(" "))


def nettoyer(t: str) -> str:
    lignes = [re.sub(r"[ \t ]+", " ", l).strip() for l in t.splitlines()]
    sortie, vide = [], False
    for l in lignes:
        if l in {"", "•"}:
            vide = True
            continue
        if vide and sortie:
            sortie.append("")
        sortie.append(l)
        vide = False
    return "\n".join(sortie).strip() + "\n"


def liens(page_html: str, base: str, motif: str) -> list[str]:
    from bs4 import BeautifulSoup
    rx, vus = re.compile(motif), []
    for a in BeautifulSoup(page_html, "lxml").find_all("a", href=True):
        h = a["href"].split("#")[0]
        if rx.search(h):
            u = urljoin(base, h)
            if u not in vus:
                vus.append(u)
    return vus


def nom_document(url: str) -> str:
    p = urlparse(url)
    nom = re.sub(r"[^a-z0-9]+", "-", (p.path.strip("/") or p.netloc).lower()).strip("-")[-90:]
    return nom or "page"


def lire_candidats(journal=print) -> list[dict]:
    export = telecharger(EXPORT).json()
    garder = ("slug", "prenom", "nom", "parti", "partiCourt", "famille", "statut", "photo", "programmeTitre",
              "programmePublieLe", "programmePages", "programmePdf", "programmeSource", "programmeEnLigne")
    tous = [{k: c.get(k) for k in garder} for c in export["candidats"]]
    for c in tous:
        c["en_lice"] = c["statut"] in EN_LICE
        c["programme"] = bool(c["programmePdf"] or c["programmeEnLigne"])
        if c["photo"]:
            c["photo"] = urljoin(SITE_C2027, c["photo"])
        if c["programmePdf"]:
            c["programmePdf"] = urljoin(SITE_C2027, c["programmePdf"])
    references = [{**r, "en_lice": False, "programme": True, "reference": True} for r in REFERENCES]
    ecrire_json(CANDIDATS, {"source": EXPORT, "export_du": export.get("genereLe"), "lu_le": maintenant(),
                            "candidats": [c for c in tous if c["en_lice"]] + references})
    retenus = [c for c in tous if c["en_lice"] and c["programme"]] + references
    journal(f"   {sum(c['en_lice'] for c in tous)} candidatures en lice, {len(retenus) - len(references)} programmes "
            f"publiés (export du {export.get('genereLe', '?')[:10]}), {len(references)} de référence")
    return retenus


def documents_du(c: dict) -> list[tuple[str, str]]:
    """(url, type) des documents du programme d'un candidat."""
    slug, pdf, page = c["slug"], c["programmePdf"], c["programmeEnLigne"]
    if pdf and (not page or slug in PDF_D_ABORD):
        return [(pdf, "pdf")]
    docs = [(page, "html")]
    if slug in RECETTES:
        r = telecharger(page)
        suivis = liens(r.text, page, RECETTES[slug])
        docs += [(u, "pdf" if u.lower().endswith(".pdf") else "html") for u in suivis]
    return docs


def collecter(journal=print, seul: str | None = None) -> None:
    anciens = {(d["candidat"], d["url"]): d for d in lire_csv(DOCUMENTS)}
    lignes = {k: v for k, v in anciens.items() if seul and k[0] != seul}
    for c in lire_candidats(journal):
        if seul and c["slug"] != seul:
            continue
        try:
            docs = documents_du(c)
        except requests.RequestException as e:
            journal(f"   {c['slug']} : page du programme injoignable ({e}) ; documents précédents gardés")
            lignes.update({k: v for k, v in anciens.items() if k[0] == c["slug"]})
            continue
        nouveaux = modifies = 0
        for url, genre in docs:
            try:
                r = telecharger(url)
            except requests.RequestException as e:
                journal(f"   {c['slug']} : {url} injoignable ({e})")
                if (c["slug"], url) in anciens:
                    lignes[(c["slug"], url)] = anciens[(c["slug"], url)]
                continue
            nom = nom_document(url)
            brut = BRUT / c["slug"] / (nom + (".pdf" if genre == "pdf" else ".html"))
            brut.parent.mkdir(parents=True, exist_ok=True)
            brut.write_bytes(r.content)
            texte = texte_pdf(r.content) if genre == "pdf" else texte_html(r.text)
            fichier = TEXTES / c["slug"] / (nom + ".txt")
            fichier.parent.mkdir(parents=True, exist_ok=True)
            fichier.write_text(texte, encoding="utf-8", newline="\n")
            avant = anciens.get((c["slug"], url), {})
            e = empreinte(texte)
            if not avant:
                nouveaux += 1
            elif avant.get("empreinte") != e:
                modifies += 1
            lignes[(c["slug"], url)] = {
                "candidat": c["slug"], "url": url, "fichier": fichier.relative_to(TEXTES).as_posix(), "type": genre,
                "empreinte": e, "caracteres": len(texte), "telecharge_le": maintenant(),
                "lu_le": avant.get("lu_le", ""), "empreinte_lue": avant.get("empreinte_lue", "")}
        journal(f"   {c['slug']} : {len(docs)} document(s), {nouveaux} nouveau(x), {modifies} modifié(s)")
    ecrire_csv(DOCUMENTS, sorted(lignes.values(), key=lambda d: (d["candidat"], d["url"])), CHAMPS_DOCS)


def a_lire() -> list[dict]:
    """Documents jamais lus, ou modifiés depuis leur lecture."""
    return [d for d in lire_csv(DOCUMENTS) if d["empreinte"] != d.get("empreinte_lue")]
