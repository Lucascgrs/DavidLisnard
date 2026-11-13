"""Conversion des commentaires en Parquet et envoi vers rag-politique/politique-sources (règles : docs/HUGGINGFACE.md).

Dans le dataset, nos fichiers sont rangés sous data/commentaires/nouvelle-energie/, **un seul fichier par source**,
daté du jour de sa dernière mise à jour : « youtube_2026-11-13.parquet », « instagram_2026-11-13.parquet »…

Chaque export recalcule le fichier complet de chaque source. S'il est identique à celui déjà déposé (même empreinte
du contenu), rien ne part. S'il a changé (nouveaux commentaires, notes refaites, « j'aime »), le nouveau fichier
remplace l'ancien dans le même commit : l'ancien est supprimé, jamais deux versions côte à côte. L'historique git du
dataset garde les versions précédentes.

Les fichiers sont d'abord écrits dans donnees/huggingface/lots/, puis envoyés en un seul commit ;
donnees/huggingface/etat.json retient, par source, le fichier préparé et le fichier déposé avec leur empreinte.

Ce qui part : les commentaires notés et sans doublon, comme sur le site (web/export.py), avec le nom affiché de leur
auteur (choix de l'utilisateur du 2026-11-13 : pas d'anonymisation ; l'identifiant interne de plateforme ne part pas)
et leurs notes du moment. Le site (Supabase, Vercel) ne dépend en rien de cet export.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from analyse import stockage
from analyse.criteres import CRITERES
from commun.config import CONFIG, DONNEES, SOURCES, lire_env
from commun.fichiers import ecrire_json, lire_csv, lire_json
from commun.textes import PARIS, maintenant

DEPOT = "rag-politique/politique-sources"
TYPE_SOURCE, PARTI, PERSONNE = "commentaires", "nouvelle-energie", "David Lisnard"
DOSSIER_HF = f"data/{TYPE_SOURCE}/{PARTI}"
LOCAL = DONNEES / "huggingface"
LOTS = LOCAL / "lots"
ETAT = LOCAL / "etat.json"  # {source: {"prepare": {...}, "depose": {...}}}
FICHIER_ENV = CONFIG / "huggingface.env"  # HF_TOKEN=… (privé, hors git) ; sinon le jeton de « hf auth login »
NOM_CONFIG = "commentaires"  # configuration du dataset qui lit nos fichiers (README, en-tête YAML)

COLONNES = ["id", "type_source", "parti", "personne", "source", "compte", "groupe", "publication_id",
            "publication_titre", "publication_lien", "publication_date", "date", "type", "parent_id",
            "parent_texte", "auteur", "likes", "texte", "nb_caracteres", *CRITERES, "cible", "origine_notes",
            "version_modele"]
ENTIERS = {"likes", "nb_caracteres", *CRITERES}


def jeton() -> str | None:
    return lire_env(FICHIER_ENV).get("HF_TOKEN") or None


def api():
    from huggingface_hub import HfApi
    return HfApi(token=jeton())


def fichiers_distants(hf=None) -> list[str]:
    return (hf or api()).list_repo_files(DEPOT, repo_type="dataset")


def lire_etat() -> dict:
    return lire_json(ETAT, {}) or {}


def source_du_fichier(nom: str) -> str:
    """« youtube_2026-11-13.parquet » → « youtube »."""
    return re.sub(r"_\d{4}-\d{2}-\d{2}(_\d+)?\.parquet$", "", nom)


def auteurs() -> dict[str, str]:
    """Nom affiché de l'auteur, par clé « source:commentaire_id », lu dans les CSV de collecte (donnees/<source>/) :
    le corpus n'en garde qu'une empreinte."""
    sortie = {}
    for source in SOURCES:
        for f in sorted((DONNEES / source).glob("*.csv")):
            for l in lire_csv(f):
                sortie.setdefault(f"{source}:{l['commentaire_id']}", l.get("auteur") or "")
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
            "parent_texte": l["parent_texte"], "auteur": noms.get(l["cle"], ""), "likes": int(l["likes"] or 0),
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
    ou la dernière préparation. Un seul fichier par source dans donnees/huggingface/lots/."""
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


# --- README du dataset : une configuration à part pour nos fichiers -------------------------------------------------

DEBUT_SECTION, FIN_SECTION = "<!-- commentaires:debut -->", "<!-- commentaires:fin -->"
SECTION = f"""{DEBUT_SECTION}
## Commentaires du public (`data/commentaires/`)

Commentaires publics laissés sous les publications de David Lisnard et des comptes qui parlent de lui (YouTube,
Instagram, Bluesky, groupes Facebook publics, X), envoyés par le projet DavidLisnard. Ce n'est pas la parole des
responsables : c'est la réaction du public. Un seul fichier par source
(`data/commentaires/nouvelle-energie/<source>_<AAAA-MM-JJ>.parquet`, daté de sa dernière mise à jour), remplacé en
entier quand il change ; avec le nom affiché de l'auteur (`auteur`), sans doublon. Les notes (`tonalite`, `forme`,
`systeme`, `idees`, `pertinence` sur 20, `cible`) sont celles du projet à la date du fichier.

Leurs colonnes diffèrent des autres fichiers : ils forment la configuration `{NOM_CONFIG}`, à part de `default`.

```python
load_dataset("rag-politique/politique-sources", "{NOM_CONFIG}", split="train")
```
{FIN_SECTION}"""


def readme_mis_a_jour(texte: str, distants: list[str]) -> str:
    """Le README avec la configuration `commentaires` et la section qui la décrit. `default` garde les autres
    dossiers de data/ (sinon nos colonnes, différentes, empêcheraient de charger le dataset)."""
    import yaml
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", texte, re.S)
    if not m:
        raise ValueError("README du dataset sans en-tête YAML : à regarder à la main")
    entete, corps = m.group(1), texte[m.end():]
    meta = yaml.safe_load(entete) or {}
    types = sorted({f.split("/")[1] for f in distants if f.startswith("data/") and f.count("/") >= 2} - {TYPE_SOURCE})
    voulu = [{"config_name": "default", "default": True,
              "data_files": [{"split": "train", "path": [f"data/{t}/**/*.parquet" for t in types]}]},
             {"config_name": NOM_CONFIG,
              "data_files": [{"split": "train", "path": f"{DOSSIER_HF}/*.parquet"}]}]
    autres = [c for c in meta.get("configs", []) if c.get("config_name") not in ("default", NOM_CONFIG)]
    if meta.get("configs") != voulu + autres:
        # Seul le bloc « configs: » est réécrit : le reste de l'en-tête reste tel que ses auteurs l'ont écrit.
        lignes = entete.splitlines()
        debut = next((i for i, x in enumerate(lignes) if x.startswith("configs:")), None)
        if debut is None:
            garde = lignes
        else:
            fin = next((i for i in range(debut + 1, len(lignes)) if lignes[i] and lignes[i][0] not in " -"),
                       len(lignes))
            garde = lignes[:debut] + lignes[fin:]
        bloc = yaml.safe_dump({"configs": voulu + autres}, allow_unicode=True, sort_keys=False).rstrip()
        entete = "\n".join(garde + [bloc])
    if DEBUT_SECTION in corps:
        corps = re.sub(re.escape(DEBUT_SECTION) + ".*?" + re.escape(FIN_SECTION), lambda _: SECTION, corps, flags=re.S)
    else:
        corps = corps.rstrip() + "\n\n" + SECTION + "\n"
    return f"---\n{entete}\n---\n{corps}"


def envoyer(journal=print, hf=None) -> dict:
    """Un seul commit : pour chaque source dont le fichier préparé diffère du fichier déposé, dépose le nouveau et
    supprime l'ancien (et tout autre fichier de cette source) ; met à jour le README s'il le faut."""
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, hf_hub_download
    hf = hf or api()
    distants = fichiers_distants(hf)
    nos_fichiers = [f for f in distants if f.startswith(DOSSIER_HF + "/")]
    etat = lire_etat()
    operations, changees, n = [], [], 0
    for source, s in sorted(etat.items()):
        p, d = s.get("prepare"), s.get("depose") or {}
        if not p or not (LOTS / p["fichier"]).exists():
            continue
        cible = f"{DOSSIER_HF}/{p['fichier']}"
        anciens = [f for f in nos_fichiers if source_du_fichier(Path(f).name) == source and f != cible]
        if d.get("empreinte") == p["empreinte"] and cible in distants and not anciens:
            continue
        operations.append(CommitOperationAdd(cible, str(LOTS / p["fichier"])))
        operations += [CommitOperationDelete(f) for f in anciens]
        changees.append((source, p, anciens))
        n += p["lignes"]
    if not operations:
        journal("   rien à envoyer : le dataset est déjà à jour")
        return {"envoyes": [], "commit": None}
    readme = Path(hf_hub_download(DEPOT, "README.md", repo_type="dataset", token=jeton(),
                                  force_download=True)).read_text(encoding="utf-8")
    nouveau = readme_mis_a_jour(readme, distants + [f"{DOSSIER_HF}/{p['fichier']}" for _, p, _ in changees])
    if nouveau != readme:
        operations.append(CommitOperationAdd("README.md", nouveau.encode("utf-8")))
    r = hf.create_commit(DEPOT, operations, repo_type="dataset",
                         commit_message=f"Commentaires du public (projet DavidLisnard) : "
                                        f"{', '.join(s for s, _, _ in changees)} mis à jour ({n} commentaires)")
    for source, p, anciens in changees:
        etat[source]["depose"] = {**p, "commit": r.oid, "depose_le": maintenant()}
        journal(f"   {p['fichier']} déposé ({p['lignes']} commentaires)"
                + (f", remplace {', '.join(Path(a).name for a in anciens)}" if anciens else ""))
    ecrire_json(ETAT, etat)
    journal(f"   commit {r.oid[:10]}{' (README mis à jour)' if nouveau != readme else ''} — {r.commit_url}")
    return {"envoyes": [p["fichier"] for _, p, _ in changees], "commit": r.oid, "url": r.commit_url}


def etat() -> dict:
    """Par source : fichier préparé, nombre de commentaires, déposé tel quel ou en attente."""
    lignes = []
    for source, s in sorted(lire_etat().items()):
        p, d = s.get("prepare") or {}, s.get("depose") or {}
        if p:
            lignes.append((source, p["fichier"], p["lignes"], d.get("empreinte") == p["empreinte"]))
    return {"sources": lignes, "exportes": sum(x[2] for x in lignes),
            "en_attente": [x[1] for x in lignes if not x[3]]}
