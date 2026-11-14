"""Corpus du RAG (bucket R2 public du groupe, `rag-politique-sources`) : téléchargement en lecture seule et recherche.

Les Parquet sont copiés tels quels dans verification/corpus/ ; on ne les modifie jamais. Seuls les textes de
Nouvelle Énergie sont utilisés (programmes, discours, entretiens, tribunes, articles, communication du parti,
réseaux sociaux, vidéos, documents).
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .chemins import CORPUS

BUCKET = "rag-politique-sources"
PREFIXE_NE = "nouvelle-energie"


def client():
    """Client S3 de R2, avec les clés du projet (config/cloudflare.env), en lecture seule ici."""
    from cloudflare.export import client as client_r2
    return client_r2()


def telecharger_corpus() -> list[Path]:
    """Copie dans corpus/ tous les Parquet Nouvelle Énergie du bucket public, et note leur origine."""
    s3 = client()
    CORPUS.mkdir(parents=True, exist_ok=True)
    faits, inventaire = [], []
    jeton = None
    while True:
        args = {"Bucket": BUCKET, "Prefix": "data/"}
        if jeton:
            args["ContinuationToken"] = jeton
        rep = s3.list_objects_v2(**args)
        for o in rep.get("Contents", []):
            cle = o["Key"]
            if f"/{PREFIXE_NE}/" not in cle or not cle.endswith(".parquet"):
                continue
            type_source = cle.split("/")[1]
            local = CORPUS / f"{type_source}.parquet"
            octets = s3.get_object(Bucket=BUCKET, Key=cle)["Body"].read()
            local.write_bytes(octets)
            inventaire.append({"fichier": local.name, "cle_r2": cle, "bucket": BUCKET, "octets": len(octets),
                               "sha256": hashlib.sha256(octets).hexdigest(),
                               "telecharge_le": datetime.now().isoformat(timespec="seconds")})
            faits.append(local)
        if not rep.get("IsTruncated"):
            break
        jeton = rep["NextContinuationToken"]
    (CORPUS / "inventaire.json").write_text(json.dumps(inventaire, ensure_ascii=False, indent=2), encoding="utf-8")
    return faits


def charger():
    """Toutes les lignes du corpus Nouvelle Énergie dans un seul DataFrame (colonne `type_source`)."""
    import pandas as pd
    morceaux = [pd.read_parquet(p) for p in sorted(CORPUS.glob("*.parquet"))]
    if not morceaux:
        raise RuntimeError("corpus/ est vide : lancer d'abord `python -m verification corpus`")
    return pd.concat(morceaux, ignore_index=True)


def chercher(motif: str, contexte: int = 220, df=None, limite: int | None = None) -> list[dict]:
    """Passages du corpus qui contiennent `motif` (expression régulière, sans casse), avec leur origine."""
    df = charger() if df is None else df
    rx = re.compile(motif, re.I)
    sortie = []
    for _, ligne in df.iterrows():
        texte = ligne["texte"] or ""
        for m in rx.finditer(texte):
            a, b = max(0, m.start() - contexte), min(len(texte), m.end() + contexte)
            sortie.append({"id_corpus": ligne["id"], "type_source": ligne["type_source"],
                           "sous_type": ligne.get("sous_type"), "date": ligne.get("date"),
                           "titre": ligne.get("titre"), "url_source": ligne.get("url_source"),
                           "passage": re.sub(r"\s+", " ", texte[a:b]).strip()})
            if limite and len(sortie) >= limite:
                return sortie
    return sortie
