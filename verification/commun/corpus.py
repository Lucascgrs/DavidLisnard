"""Corpus du RAG (bucket R2 public du groupe, `rag-politique-sources`) : téléchargement en lecture seule et recherche.

Les Parquet sont copiés tels quels dans le dossier corpus/ de la personne (donnees/verification/corpus/ pour David
Lisnard, donnees/verification/<clé>/corpus/ pour les autres) ; on ne les modifie jamais. Seuls les textes du parti de
la personne sont copiés (data/<type>/<parti>/…, voir commun/personnes.py).

Dans les transcriptions de vidéos découpées par locuteur (colonne `parle_personne`), seuls les passages où parle la
personne sont gardés à la lecture : les questions des journalistes et les autres orateurs ne sont jamais cités.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .personnes import personne as fiche

BUCKET = "rag-politique-sources"


def client():
    """Client S3 de R2, avec les clés du projet (config/cloudflare.env), en lecture seule ici."""
    from commun.cloudflare.export import client as client_r2
    return client_r2()


def telecharger_corpus(cle: str | None = None) -> list[Path]:
    """Copie dans corpus/ tous les Parquet du parti de la personne (bucket public), et note leur origine."""
    p = fiche(cle)
    CORPUS = p.corpus
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
            cle_r2 = o["Key"]
            morceaux = cle_r2.split("/")  # data/<type>/<parti>/<lot>.parquet (pas les sous-dossiers déposés par la vérification)
            if len(morceaux) != 4 or morceaux[2] not in p.partis_r2 or not cle_r2.endswith(".parquet"):
                continue
            type_source = morceaux[1]
            # un seul lot par type chez Nouvelle Énergie (nom d'origine) ; plusieurs lots par type ailleurs
            lot = Path(morceaux[-1]).stem
            local = CORPUS / (f"{type_source}.parquet" if p.cle == "lisnard" else f"{type_source}__{lot}.parquet")
            octets = s3.get_object(Bucket=BUCKET, Key=cle_r2)["Body"].read()
            local.write_bytes(octets)
            inventaire.append({"fichier": local.name, "cle_r2": cle_r2, "bucket": BUCKET, "octets": len(octets),
                               "sha256": hashlib.sha256(octets).hexdigest(),
                               "telecharge_le": datetime.now().isoformat(timespec="seconds")})
            faits.append(local)
        if not rep.get("IsTruncated"):
            break
        jeton = rep["NextContinuationToken"]
    (CORPUS / "inventaire.json").write_text(json.dumps(inventaire, ensure_ascii=False, indent=2), encoding="utf-8")
    return faits


_CACHE: dict = {}


def charger(cle: str | None = None):
    """Toutes les lignes du corpus de la personne dans un seul DataFrame (colonne `type_source`), sans les passages
    où parle quelqu'un d'autre."""
    import pandas as pd
    p = fiche(cle)
    if p.cle in _CACHE:
        return _CACHE[p.cle]
    morceaux = [pd.read_parquet(f) for f in sorted(p.corpus.glob("*.parquet"))]
    if not morceaux:
        commande = "corpus" if p.cle == "lisnard" else f"{p.cle} corpus"
        raise RuntimeError(f"{p.corpus} est vide : lancer d'abord `python -m verification {commande}`")
    df = pd.concat(morceaux, ignore_index=True)
    if "parle_personne" in df:
        df = df[df["parle_personne"].isna() | (df["parle_personne"] == True)].reset_index(drop=True)  # noqa: E712
    _CACHE[p.cle] = df
    return df


def chercher(motif: str, contexte: int = 220, df=None, limite: int | None = None, cle: str | None = None) -> list[dict]:
    """Passages du corpus qui contiennent `motif` (expression régulière, sans casse), avec leur origine."""
    df = charger(cle) if df is None else df
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
