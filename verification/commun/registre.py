"""Écriture du fichier affirmations.csv d'un thème : date, support et adresse sont repris du corpus (id_corpus).

Chaque affirmation est un dict : id, type (affirmation / mesure), id_corpus, citation (copiée du corpus), et
facultativement autres_versions, grandeur_testee, verifiable, priorite, date (si le texte du corpus regroupe un mois de
publications, la date précise de la phrase).
"""
import csv
import re
from pathlib import Path

from .corpus import charger

COLONNES = ["id", "theme", "type", "citation", "date", "support", "id_corpus", "url_source", "autres_versions",
            "grandeur_testee", "verifiable", "priorite"]


def _support(l) -> str:
    titre = str(l.get("titre") or "")
    m = re.match(r"(Entretien|Tribune|Discours|FAQ Nouvelle Énergie|Newsletter Nouvelle Énergie)\s*[—-]\s*([^—(]+)", titre)
    if m:
        return f"{m.group(1).lower()}, {m.group(2).strip()}"
    return f"{str(l.get('sous_type') or l.get('type_source')).lower()} : {titre[:90]}"


def ecrire(chemin: Path, theme: str, affirmations: list[dict]) -> int:
    df = charger().set_index("id")
    corpus_texte = {}
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for a in affirmations:
            l = df.loc[a["id_corpus"]]
            texte = re.sub(r"\s+", " ", str(l["texte"]))
            corpus_texte[a["id"]] = texte
            extrait = re.sub(r"\s+", " ", a["citation"]).split("[…]")[0].strip(" «»")[:60]
            if extrait and extrait not in texte:
                raise ValueError(f"{a['id']} : citation introuvable dans {a['id_corpus']} : « {extrait} »")
            url = l.get("url_source")
            w.writerow({"id": a["id"], "theme": theme, "type": a.get("type", "affirmation"), "citation": a["citation"],
                        "date": a.get("date") or l.get("date") or "", "support": a.get("support") or _support(l),
                        "id_corpus": a["id_corpus"], "url_source": "" if url is None or str(url) == "nan" else url,
                        "autres_versions": a.get("autres_versions", ""), "grandeur_testee": a.get("grandeur_testee", ""),
                        "verifiable": a.get("verifiable", "oui"), "priorite": a.get("priorite", 2)})
    return len(affirmations)
