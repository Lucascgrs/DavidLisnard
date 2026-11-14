"""Repérage des phrases candidates pour le registre : affirmations chiffrées et mesures proposées.

Un thème = une liste d'expressions régulières (mots du thème). Une phrase est candidate si elle contient un mot du
thème ET (un nombre, ou une formule de proposition). Le résultat est à relire à la main : il sert à ne rien
oublier, pas à décider.
"""
import csv
import re
from pathlib import Path

from .corpus import charger

NOMBRE = re.compile(r"\d[\d  .,]*\s?(%|pour ?cent|milliards?|millions?|Md€|M€|€|points?|fois|ans|places)|"
                    r"\b(premier|premi[eè]re|dernier|champion|record|plus (?:élevé|lourd|faible)|le plus)\b", re.I)
MESURE = re.compile(r"\b(je propose|nous proposons|il faut|je veux|nous voulons|supprimer|créer|instaurer|"
                    r"baisser|réduire|plafonner|interdire|rétablir|inscrire|abaisser|doubler|diviser)\b", re.I)
PHRASE = re.compile(r"(?<=[.!?…»])\s+(?=[A-ZÀ-Ý«\"“])")


def phrases(texte: str):
    for p in PHRASE.split(re.sub(r"\s+", " ", texte or "")):
        if 30 <= len(p) <= 700:
            yield p.strip()


def extraire(mots: list[str], sortie: Path, df=None) -> int:
    """Écrit dans `sortie` (CSV) les phrases candidates du thème, avec leur origine. Renvoie leur nombre."""
    df = charger() if df is None else df
    rx = re.compile("|".join(mots), re.I)
    vus, lignes = set(), []
    for _, l in df.iterrows():
        for p in phrases(l["texte"]):
            if not rx.search(p):
                continue
            chiffre, mesure = bool(NOMBRE.search(p)), bool(MESURE.search(p))
            if not (chiffre or mesure):
                continue
            cle = re.sub(r"\W+", "", p.lower())[:160]
            if cle in vus:
                continue
            vus.add(cle)
            lignes.append({"id_corpus": l["id"], "type_source": l["type_source"], "sous_type": l["sous_type"],
                           "date": l["date"], "titre": l["titre"], "url_source": l["url_source"],
                           "chiffre": int(chiffre), "mesure": int(mesure), "phrase": p})
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]) if lignes else ["phrase"])
        w.writeheader()
        w.writerows(lignes)
    return len(lignes)
