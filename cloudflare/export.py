"""Conversion des commentaires en Parquet et envoi vers Cloudflare R2, dans le bucket privé
rag-politique-sources-privees du groupe RAG politique (règles : docs/CLOUDFLARE.md).

Dans le bucket, nos fichiers sont rangés sous data/commentaires/nouvelle-energie/, **un seul fichier par source**,
daté du jour de sa dernière mise à jour : « youtube_2026-11-13.parquet », « instagram_2026-11-13.parquet »…

Chaque export recalcule le fichier complet de chaque source. S'il est identique à celui déjà déposé (même empreinte
du contenu), rien ne part. S'il a changé (nouveaux commentaires, notes refaites, « j'aime »), le nouveau fichier est
déposé, vérifié (empreinte MD5 renvoyée par R2), puis l'ancien est supprimé : jamais deux versions côte à côte.

Les fichiers sont d'abord écrits dans donnees/cloudflare/lots/ ; donnees/cloudflare/etat.json retient, par source,
le fichier préparé et le fichier déposé avec leur empreinte.

Ce qui part : les commentaires notés et sans doublon, comme sur le site (web/export.py), et leurs notes du moment.
Aucun nom de compte d'auteur ne part : la colonne `auteur_id` est un identifiant opaque, le même pour tous les
commentaires d'un même compte, calculé avec une clé secrète locale (AUTEUR_CLE dans config/cloudflare.env) :
impossible de retrouver le compte à partir de l'identifiant, même en essayant des noms.
Le site (Supabase, Vercel) ne dépend en rien de cet export.
"""
import hashlib
import hmac
import json
import secrets
import re
from datetime import datetime
from pathlib import Path

from analyse import stockage
from analyse.criteres import CRITERES
from commun.config import CONFIG, DONNEES, SOURCES, lire_env
from commun.fichiers import ecrire_json, lire_csv, lire_json
from commun.textes import PARIS, maintenant

BUCKET = "rag-politique-sources-privees"  # privé : jamais le bucket public rag-politique-sources
TYPE_SOURCE, PARTI, PERSONNE = "commentaires", "nouvelle-energie", "David Lisnard"
DOSSIER = f"data/{TYPE_SOURCE}/{PARTI}"
LOCAL = DONNEES / "cloudflare"
LOTS = LOCAL / "lots"
ETAT = LOCAL / "etat.json"  # {source: {"prepare": {...}, "depose": {...}}}
FICHIER_ENV = CONFIG / "cloudflare.env"  # clés R2 et AUTEUR_CLE (privé, hors git)

COLONNES = ["id", "type_source", "parti", "personne", "source", "compte", "groupe", "publication_id",
            "publication_titre", "publication_lien", "publication_date", "date", "type", "parent_id",
            "parent_texte", "auteur_id", "likes", "texte", "nb_caracteres", *CRITERES, "cible", "origine_notes",
            "version_modele"]
ENTIERS = {"likes", "nb_caracteres", *CRITERES}


def client():
    """Client S3 de R2 (boto3), avec les clés de config/cloudflare.env."""
    import boto3
    env = lire_env(FICHIER_ENV)
    manque = [k for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if not env.get(k)]
    if manque:
        raise RuntimeError(f"config/cloudflare.env incomplet : {', '.join(manque)} (modèle : cloudflare.exemple.env)")
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"], region_name="auto")


def fichiers_distants(s3=None) -> dict[str, str]:
    """Nos fichiers dans le bucket : {clé: empreinte MD5 (ETag)}."""
    sortie = {}
    for page in (s3 or client()).get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=DOSSIER + "/"):
        for o in page.get("Contents", []):
            sortie[o["Key"]] = o["ETag"].strip('"')
    return sortie


def lire_etat() -> dict:
    return lire_json(ETAT, {}) or {}


def source_du_fichier(nom: str) -> str:
    """« youtube_2026-11-13.parquet » → « youtube »."""
    return re.sub(r"_\d{4}-\d{2}-\d{2}(_\d+)?\.parquet$", "", nom)


def cle_auteurs() -> bytes:
    """Clé secrète des identifiants d'auteur, créée une fois dans config/cloudflare.env. La perdre change tous les
    identifiants (les fichiers sont alors refaits en entier), sans autre conséquence."""
    cle = lire_env(FICHIER_ENV).get("AUTEUR_CLE")
    if not cle:
        cle = secrets.token_hex(32)
        avant = FICHIER_ENV.read_text(encoding="utf-8") if FICHIER_ENV.exists() else ""
        FICHIER_ENV.write_text(avant.rstrip("\n") + ("\n" if avant else "")
                               + "# Clé des identifiants d'auteur envoyés sur Cloudflare R2. Ne jamais la partager.\n"
                               + f"AUTEUR_CLE={cle}\n", encoding="utf-8")
    return cle.encode()


def auteurs() -> dict[str, str]:
    """Identifiant opaque de l'auteur (« u » + 16 caractères), par clé « source:commentaire_id ». Le compte (identifiant
    de plateforme, à défaut nom affiché, comme web/export.py) est lu dans les CSV de collecte (donnees/<source>/) et ne
    sort jamais d'ici : seul part son HMAC avec la clé locale."""
    cle, sortie = cle_auteurs(), {}
    for source in SOURCES:
        for f in sorted((DONNEES / source).glob("*.csv")):
            for l in lire_csv(f):
                compte = (l.get("auteur_id") or l.get("auteur") or "").strip()
                if compte and l.get("commentaire_id"):
                    sortie.setdefault(f"{source}:{l['commentaire_id']}",
                                      "u" + hmac.new(cle, f"{source}|{compte}".encode(), hashlib.sha256).hexdigest()[:16])
    return sortie


def lignes_par_source() -> dict[str, list[dict]]:
    """Par source : tous les commentaires notés et sans doublon, triés par identifiant (contenu stable d'un export
    à l'autre tant que rien ne change)."""
    noms = auteurs()
    tout = lire_csv(stockage.CORPUS)
    notes = stockage.lire_notes(tout)
    garde = {l["cle"]: l.get("doublon_de") or l["cle"] for l in tout}
    par_source = {s: [] for s in SOURCES}
    for l in tout:
        if l["source"] not in par_source or l.get("doublon_de") or l["cle"] not in notes:
            continue
        n = notes[l["cle"]]
        par_source[l["source"]].append({
            "id": l["cle"], "type_source": TYPE_SOURCE, "parti": PARTI, "personne": PERSONNE,
            "source": l["source"], "compte": l["compte"], "groupe": l["groupe"],
            "publication_id": l["publication_id"], "publication_titre": l["publication_titre"],
            "publication_lien": l["publication_lien"], "publication_date": l["publication_date"],
            "date": l["date"], "type": l["type"], "parent_id": garde.get(l["parent_cle"], l["parent_cle"]),
            "parent_texte": l["parent_texte"], "auteur_id": noms.get(l["cle"], ""), "likes": int(l["likes"] or 0),
            "texte": l["texte"], "nb_caracteres": len(l["texte"]), **{c: int(n[c]) for c in CRITERES},
            "cible": n["cible"],
            "origine_notes": {"relue": "annotation", "corrigée": "correction"}.get(n.get("fiabilite"), "modèle"),
            "version_modele": n.get("version") or "",
        })
    return {s: sorted(v, key=lambda x: x["id"]) for s, v in par_source.items() if v}


def empreinte(lignes: list[dict]) -> str:
    h = hashlib.sha256()
    for l in lignes:
        h.update(json.dumps([l[c] for c in COLONNES], ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


def ecrire_lot(chemin: Path, lignes: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq
    schema = pa.schema([(c, pa.int64() if c in ENTIERS else pa.string()) for c in COLONNES])
    table = pa.Table.from_pylist([{c: l[c] for c in COLONNES} for l in lignes], schema=schema)
    tmp = chemin.with_suffix(".tmp")
    pq.write_table(table, tmp, compression="zstd")
    tmp.replace(chemin)


def preparer(journal=print) -> list[str]:
    """Recalcule le fichier de chaque source ; n'écrit que ceux dont le contenu a changé depuis le dernier dépôt
    ou la dernière préparation. Un seul fichier par source dans donnees/cloudflare/lots/."""
    LOTS.mkdir(parents=True, exist_ok=True)
    etat = lire_etat()
    jour = datetime.now(PARIS).strftime("%Y-%m-%d")
    faits = []
    for source, lignes in lignes_par_source().items():
        e = empreinte(lignes)
        s = etat.setdefault(source, {})
        prepare = s.get("prepare") or {}
        if prepare.get("empreinte") == e and (LOTS / prepare.get("fichier", "?")).exists():
            journal(f"   {source} : inchangé ({len(lignes)} commentaires)")
            continue
        nom = f"{source}_{jour}.parquet"
        ecrire_lot(LOTS / nom, lignes)
        for ancien in LOTS.glob(f"{source}_*.parquet"):  # un seul fichier par source, ici aussi
            if ancien.name != nom and source_du_fichier(ancien.name) == source:
                ancien.unlink()
        s["prepare"] = {"fichier": nom, "empreinte": e, "lignes": len(lignes), "le": maintenant()}
        faits.append(nom)
        journal(f"   {nom} : {len(lignes)} commentaires ({'mis à jour' if prepare else 'nouveau'})")
    ecrire_json(ETAT, etat)
    return faits


def envoyer(journal=print, s3=None) -> dict:
    """Pour chaque source dont le fichier préparé diffère de celui du bucket : dépose le nouveau, vérifie son
    empreinte, puis supprime l'ancien (et tout autre fichier de cette source)."""
    s3 = s3 or client()
    distants = fichiers_distants(s3)
    etat = lire_etat()
    envoyes = []
    for source, s in sorted(etat.items()):
        p = s.get("prepare")
        if not p or not (LOTS / p["fichier"]).exists():
            continue
        cible = f"{DOSSIER}/{p['fichier']}"
        anciens = [k for k in distants if source_du_fichier(Path(k).name) == source and k != cible]
        donnees = (LOTS / p["fichier"]).read_bytes()
        md5 = hashlib.md5(donnees).hexdigest()
        if distants.get(cible) == md5 and not anciens:
            if (s.get("depose") or {}).get("empreinte") != p["empreinte"]:
                s["depose"] = {**p, "md5": md5, "depose_le": maintenant()}
            continue
        if distants.get(cible) != md5:
            etag = s3.put_object(Bucket=BUCKET, Key=cible, Body=donnees, ContentType="application/vnd.apache.parquet",
                                 Metadata={"sha256": hashlib.sha256(donnees).hexdigest(),
                                           "lignes": str(p["lignes"])})["ETag"].strip('"')
            if etag != md5:
                raise RuntimeError(f"{cible} : empreinte renvoyée par R2 ({etag}) différente du fichier ({md5})")
        for ancien in anciens:
            s3.delete_object(Bucket=BUCKET, Key=ancien)
        s["depose"] = {**p, "md5": md5, "depose_le": maintenant()}
        envoyes.append(p["fichier"])
        ecrire_json(ETAT, etat)
        journal(f"   {p['fichier']} déposé ({p['lignes']} commentaires)"
                + (f", remplace {', '.join(Path(a).name for a in anciens)}" if anciens else ""))
    ecrire_json(ETAT, etat)
    if not envoyes:
        journal("   rien à envoyer : le bucket est déjà à jour")
    return {"envoyes": envoyes}


def etat() -> dict:
    """Par source : fichier préparé, nombre de commentaires, déposé tel quel ou en attente."""
    lignes = []
    for source, s in sorted(lire_etat().items()):
        p, d = s.get("prepare") or {}, s.get("depose") or {}
        if p:
            lignes.append((source, p["fichier"], p["lignes"], d.get("empreinte") == p["empreinte"]))
    return {"sources": lignes, "exportes": sum(x[2] for x in lignes),
            "en_attente": [x[1] for x in lignes if not x[3]]}
