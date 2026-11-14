"""Publication de la vérification factuelle (paquet verification/) dans le bucket R2 PUBLIC rag-politique-sources.

    python -m cloudflare verification            envoie ce qui a changé, retire du bucket ce qui n'existe plus en local
    python -m cloudflare verification --essai    affiche seulement ce qui serait envoyé ou retiré

Rangement (décidé avec l'utilisateur le 2026-11-14 ; originaux sous ne/ comme les livrets NE) :

    originaux/ne/verification/<thème>/affirmations.csv
    originaux/ne/verification/<thème>/sources.csv
    originaux/ne/verification/<thème>/brut/<source>/<fichier>   fichiers d'origine
    data/programmes/nouvelle-energie/verification/<thème>/...                            contenu de calculs/
    data/programmes/nouvelle-energie/verification/SYNTHESE.md, registre_affirmations.csv

Seules les clés sous ces deux préfixes sont touchées. Le README du bucket reçoit une section balisée
<!-- verification:debut --> … <!-- verification:fin -->.
"""
import hashlib
import mimetypes
from pathlib import Path

from cloudflare.export import client

BUCKET = "rag-politique-sources"  # bucket PUBLIC : publication autorisée par l'utilisateur le 2026-11-14
DATA = "data/programmes/nouvelle-energie/verification"
ORIGINAUX = "originaux/ne/verification"
ANCIENS = ["originaux/programmes/nouvelle-energie/verification"]  # ancien emplacement, vidé à la prochaine publication
VERIF = Path(__file__).resolve().parent.parent / "verification"
TYPES = {".csv": "text/csv; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".json": "application/json",
         ".py": "text/x-python; charset=utf-8", ".html": "text/html; charset=utf-8", ".png": "image/png",
         ".pdf": "application/pdf", ".zip": "application/zip", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         ".ods": "application/vnd.oasis.opendocument.spreadsheet"}


def _fichiers(dossier: Path):
    for f in sorted(dossier.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
            yield f


def plan() -> dict[str, Path]:
    """{clé dans le bucket : fichier local}."""
    p = {}
    for theme in sorted(d for d in (VERIF / "themes").iterdir() if (d / "affirmations.csv").exists()):
        for nom in ("affirmations.csv", "sources.csv"):
            if (theme / nom).exists():
                p[f"{ORIGINAUX}/{theme.name}/{nom}"] = theme / nom
        if (theme / "brut").exists():
            for f in _fichiers(theme / "brut"):
                p[f"{ORIGINAUX}/{theme.name}/brut/{f.relative_to(theme / 'brut').as_posix()}"] = f
        if (theme / "calculs").exists():
            for f in _fichiers(theme / "calculs"):
                p[f"{DATA}/{theme.name}/{f.relative_to(theme / 'calculs').as_posix()}"] = f
    for nom in ("SYNTHESE.md", "registre_affirmations.csv"):
        p[f"{DATA}/{nom}"] = VERIF / nom
    return p


def distants(s3) -> dict[str, str]:
    sortie = {}
    for prefixe in (DATA, ORIGINAUX, *ANCIENS):
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefixe + "/"):
            for o in page.get("Contents", []):
                sortie[o["Key"]] = o["ETag"].strip('"')
    return sortie


def section_readme(p: dict[str, Path]) -> str:
    themes = sorted({k.split("/")[4] for k in p if k.count("/") >= 5})
    lignes = "\n".join(f"| `{t}` |" for t in themes)
    return f"""<!-- verification:debut -->
## Vérification factuelle des affirmations de David Lisnard (`verification/`)

Travail du projet DavidLisnard : les affirmations chiffrées de David Lisnard (Nouvelle Énergie) relevées dans ce
corpus sont confrontées, thème par thème, aux données publiques (Eurostat, Insee, OCDE, FMI, DGFiP, Cour des
comptes…). Verdicts : exact, plutôt exact, trompeur, faux, invérifiable, opinion ou promesse. Les chiffrages
marqués « ESTIMATION » ne sont pas fiables à 100 %.

```
originaux/ne/verification/<thème>/affirmations.csv   citations datées et sourcées (corpus)
originaux/ne/verification/<thème>/sources.csv        catalogue : organisme, adresse, date, sha256
originaux/ne/verification/<thème>/brut/…             fichiers téléchargés, tels quels
data/programmes/nouvelle-energie/verification/<thème>/                        calculs : resultats.csv, METHODE.md, graphiques, script
data/programmes/nouvelle-energie/verification/registre_affirmations.csv       toutes les affirmations et leur verdict
data/programmes/nouvelle-energie/verification/SYNTHESE.md                     tableau des verdicts
```

| Thème |
|---|
{lignes}

Ces fichiers ne sont pas des Parquet : ils ne font pas partie de la configuration `default` du dataset.
<!-- verification:fin -->"""


def maj_readme(s3, p: dict[str, Path], essai: bool, journal=print) -> None:
    texte = s3.get_object(Bucket=BUCKET, Key="README.md")["Body"].read().decode("utf-8")
    section = section_readme(p)
    debut, fin = "<!-- verification:debut -->", "<!-- verification:fin -->"
    if debut in texte and fin in texte:
        neuf = texte[:texte.index(debut)] + section + texte[texte.index(fin) + len(fin):]
    else:
        neuf = texte.rstrip("\n") + "\n\n" + section + "\n"
    if neuf == texte:
        journal("README.md : section vérification déjà à jour")
        return
    journal(f"README.md : section vérification {'à écrire' if essai else 'écrite'}")
    if not essai:
        s3.put_object(Bucket=BUCKET, Key="README.md", Body=neuf.encode("utf-8"), ContentType="text/markdown; charset=utf-8")


def publier(journal=print, essai: bool = False) -> dict:
    s3 = client()
    p = plan()
    dist = distants(s3)
    envoyes, inchanges, retires, octets = 0, 0, 0, 0
    for cle, f in p.items():
        donnees = f.read_bytes()
        md5 = hashlib.md5(donnees).hexdigest()
        if dist.get(cle) == md5:
            inchanges += 1
            continue
        envoyes += 1
        octets += len(donnees)
        if essai:
            continue
        type_ = TYPES.get(f.suffix.lower()) or mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        etag = s3.put_object(Bucket=BUCKET, Key=cle, Body=donnees, ContentType=type_)["ETag"].strip('"')
        if etag != md5:
            raise RuntimeError(f"{cle} : empreinte renvoyée par R2 ({etag}) différente du fichier ({md5})")
    for cle in sorted(set(dist) - set(p)):
        retires += 1
        journal(f"  {'à retirer' if essai else 'retiré'} : {cle}")
        if not essai:
            s3.delete_object(Bucket=BUCKET, Key=cle)
    maj_readme(s3, p, essai, journal)
    r = {"fichiers": len(p), "envoyes": envoyes, "inchanges": inchanges, "retires": retires, "mo": round(octets / 1e6, 1)}
    journal(f"{'Essai' if essai else 'Publication'} {BUCKET} : {r}")
    return r
