"""Copie de travail des commentaires collectés, pour l'analyse.

On ne touche jamais aux fichiers de collecte (donnees/<source>/*.csv) : on les lit et on écrit
donnees/analyse/corpus.csv, une ligne par commentaire, avec :
- cle : « source:commentaire_id », identifiant unique dans toute l'analyse ;
- le contexte utile à la lecture : compte, groupe du compte, titre de la publication, texte du commentaire parent ;
- l'auteur pseudonymisé (empreinte) : ni l'annotation ni le modèle n'ont besoin du nom ;
- texte_cle : empreinte du texte normalisé, pour ne noter qu'une fois les textes identiques (« Bravo ! »).

    python -m analyse.corpus            met à jour donnees/analyse/corpus.csv
"""
import hashlib
import re
import sys
from collections import Counter

from analyse.stockage import CORPUS
from commun.config import DONNEES, perimetre
from commun.fichiers import ecrire_csv, lire_csv
from commun.textes import sans_accents

# Ordre de lecture des sources : il fixe l'ordre des lignes du corpus, et donc le tirage des lots d'annotation.
ORDRE_SOURCES = ["youtube", "instagram", "whatsapp"]
CHAMPS = ["cle", "source", "compte", "groupe", "publication_id", "publication_titre", "publication_lien",
          "publication_date", "date", "type", "parent_cle", "parent_texte", "auteur_h", "likes", "texte", "texte_cle"]
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
    return g


def lire_collecte() -> list[dict]:
    grp = groupes()
    lignes = []
    for source in ORDRE_SOURCES:
        for f in sorted((DONNEES / source).glob("*.csv")):
            lignes += lire_csv(f)
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
            "groupe": "adhérents" if l["source"] == "whatsapp" else grp.get((l["source"], l["compte_source"]), ""),
            "publication_id": l["publication_id"], "publication_titre": nettoyer(l["publication_titre"])[:300],
            "publication_lien": l["publication_lien"], "publication_date": l["publication_date"],
            "date": l["date"], "type": l["type"],
            "parent_cle": f"{l['source']}:{parent}" if parent else "",
            "parent_texte": textes.get((l["source"], parent), "")[:500] if parent else "",
            "auteur_h": hashlib.sha1(f"{l['source']}|{l['auteur_id'] or l['auteur']}".encode()).hexdigest()[:10],
            "likes": l.get("likes", ""), "texte": texte, "texte_cle": cle_texte(texte),
        })
    return corpus


def lire() -> list[dict]:
    return lire_csv(CORPUS)


def mettre_a_jour() -> list[dict]:
    corpus = lire_collecte()
    ecrire_csv(CORPUS, corpus, CHAMPS)
    return corpus


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    c = mettre_a_jour()
    print(f"{len(c)} commentaires → {CORPUS}")
    print(Counter(l["source"] for l in c), f"textes distincts : {len({l['texte_cle'] for l in c})}")
