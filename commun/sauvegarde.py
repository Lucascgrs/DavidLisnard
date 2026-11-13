"""Sauvegarde de ce qu'on ne peut pas refaire : donnees/sauvegardes/donnees.zip.

    python -m commun.sauvegarde             fait la sauvegarde
    python -m commun.sauvegarde --voir      ce que contient la sauvegarde actuelle
    python -m commun.sauvegarde --forcer    remplace l'ancienne même si un fichier de collecte a rétréci

Ce qui est copié, dans cet ordre (le plus irremplaçable d'abord) :
1. Instagram : les anciennes publications ne peuvent pas être recollectées ;
2. les autres sources (YouTube, Bluesky, Facebook, X) ;
3. le travail fait à la main : annotations (donnees/analyse/annotation/), corrections de l'interface
   (donnees/analyse/corrections.csv), lecture par thèmes (donnees/critiques/) et annotations de la modération
   (donnees/moderation/annotations.csv et lots/).
Pour chaque source : les CSV bruts, etat.json (ce qui a déjà été lu) et likes.json. Les Excel, la copie de travail,
les vecteurs et les notes du modèle ne sont pas copiés : tout cela se recalcule.

Une seule sauvegarde est gardée. La nouvelle est d'abord écrite dans un fichier temporaire, relue en entier, et ne
remplace l'ancienne qu'ensuite : on ne se retrouve jamais sans sauvegarde, même si l'écriture est coupée.

Garde-fou : les CSV de collecte ne font que grandir. Si l'un d'eux a disparu ou rétréci depuis la dernière sauvegarde,
c'est le signe d'un accident (fichier écrasé ou tronqué) : l'ancienne sauvegarde est gardée, la nouvelle est mise de
côté dans donnees_a_verifier.zip, et le journal le dit. --forcer passe outre.

La sauvegarde se fait seule à la fin de chaque collecte (collecte/__main__.py).
"""
import json
import sys
import time
import zipfile
from pathlib import Path

from commun.config import DONNEES, SOURCES
from commun.taches import DejaEnCours, verrou
from commun.textes import maintenant

DOSSIER = DONNEES / "sauvegardes"
FICHIER = DOSSIER / "donnees.zip"
A_VERIFIER = DOSSIER / "donnees_a_verifier.zip"
CONTENU = "contenu.json"  # dans l'archive : date et taille de chaque fichier
PRIORITE = ("instagram",)
TACHE = "sauvegardes"  # verrou donnees/sauvegardes/EN_COURS


class SauvegardeRefusee(Exception):
    """Un fichier de collecte a rétréci ou disparu : l'ancienne sauvegarde est gardée."""


def fichiers() -> list[tuple[Path, str, bool]]:
    """(fichier, nom dans l'archive, « ne fait que grandir ») de tout ce qui est sauvegardé, dans l'ordre d'écriture."""
    sortie = []
    for source in [s for s in PRIORITE if s in SOURCES] + [s for s in SOURCES if s not in PRIORITE]:
        d = DONNEES / source
        sortie += [(f, f"{source}/{f.name}", True) for f in sorted(d.glob("*.csv"))]
        sortie += [(f, f"{source}/{f.name}", False) for f in (d / "etat.json", d / "likes.json") if f.exists()]
    for dossier in (DONNEES / "analyse" / "annotation", DONNEES / "critiques"):
        sortie += [(f, f.relative_to(DONNEES).as_posix(), False) for f in sorted(dossier.rglob("*"))
                   if f.is_file() and f.suffix != ".tmp" and f.name not in ("EN_COURS", "ARRET")]
    corrections = DONNEES / "analyse" / "corrections.csv"
    if corrections.exists():
        sortie.append((corrections, "analyse/corrections.csv", False))
    # Modération (moderation/) : annotations et lots tirés ; les notes du modèle se recalculent.
    moderation = DONNEES / "moderation"
    if (moderation / "annotations.csv").exists():
        sortie.append((moderation / "annotations.csv", "moderation/annotations.csv", False))
    sortie += [(f, f.relative_to(DONNEES).as_posix(), False) for f in sorted((moderation / "lots").glob("*"))
               if f.is_file()]
    return sortie


def contenu(archive: Path = FICHIER) -> dict | None:
    """La table des matières d'une sauvegarde ({« le », « fichiers »: {nom: {octets, grandit}}}), ou None."""
    try:
        with zipfile.ZipFile(archive) as z:
            return json.loads(z.read(CONTENU).decode("utf-8"))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None


def sauvegarder(journal=print, forcer: bool = False) -> dict:
    """Écrit la nouvelle sauvegarde et remplace l'ancienne. Renvoie {fichier, fichiers, octets, duree_s}."""
    debut = time.time()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    tmp = FICHIER.with_name(FICHIER.name + ".tmp")
    table = {}
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for chemin, nom, grandit in fichiers():
            octets = chemin.read_bytes()  # lu d'un seul coup : la taille notée est celle de ce qui est copié
            z.writestr(nom, octets)
            table[nom] = {"octets": len(octets), "grandit": grandit}
        z.writestr(CONTENU, json.dumps({"le": maintenant(), "fichiers": table}, ensure_ascii=False, indent=1))
    with zipfile.ZipFile(tmp) as z:  # relecture complète : une archive abîmée ne remplace jamais la bonne
        abime = z.testzip()
        if abime or set(z.namelist()) != set(table) | {CONTENU}:
            tmp.unlink(missing_ok=True)
            raise OSError(f"sauvegarde illisible après écriture ({abime or 'fichiers manquants'}) : ancienne gardée")
    avant = (contenu() or {}).get("fichiers", {})
    retrecis = [f"{nom} ({v['octets']} → {table.get(nom, {}).get('octets', 0)} octets)" for nom, v in avant.items()
                if v.get("grandit") and table.get(nom, {}).get("octets", 0) < v["octets"]]
    if retrecis and not forcer:
        tmp.replace(A_VERIFIER)
        raise SauvegardeRefusee("des fichiers de collecte ont rétréci ou disparu depuis la dernière sauvegarde : "
                                + ", ".join(retrecis) + f". L'ancienne sauvegarde est gardée ; la nouvelle est dans "
                                f"{A_VERIFIER.name}. Si c'est voulu : python -m commun.sauvegarde --forcer")
    tmp.replace(FICHIER)
    A_VERIFIER.unlink(missing_ok=True)
    bilan = {"fichier": FICHIER, "fichiers": len(table), "octets": FICHIER.stat().st_size,
             "duree_s": round(time.time() - debut, 1)}
    journal(f"   sauvegarde : {bilan['fichiers']} fichiers, {bilan['octets'] / 1e6:.1f} Mo → "
            f"{FICHIER.relative_to(DONNEES.parent)} ({bilan['duree_s']} s)")
    return bilan


def sauvegarder_sous_verrou(journal=print, forcer: bool = False, attente_s: int = 120) -> dict | None:
    """Une seule sauvegarde à la fois. Si une autre est en cours (plusieurs collectes lancées ensemble), on attend
    sa fin pour refaire la nôtre, qui contient ce que nous venons de collecter."""
    limite = time.time() + attente_s
    while True:
        try:
            with verrou(TACHE):
                return sauvegarder(journal, forcer)
        except DejaEnCours:
            if time.time() > limite:
                journal("   sauvegarde : une autre est en cours depuis trop longtemps, celle-ci est sautée")
                return None
            time.sleep(3)


def voir() -> None:
    c = contenu()
    if not c:
        print("Pas encore de sauvegarde (python -m commun.sauvegarde).")
        return
    print(f"{FICHIER} — {FICHIER.stat().st_size / 1e6:.1f} Mo, faite le {c['le']}, {len(c['fichiers'])} fichiers")
    par_dossier = {}
    for nom, v in c["fichiers"].items():
        morceaux = nom.split("/")
        d = par_dossier.setdefault("/".join(morceaux[:2 if morceaux[0] == "analyse" else 1]), [0, 0])
        d[0] += 1
        d[1] += v["octets"]
    for dossier, (n, octets) in par_dossier.items():
        print(f"  {dossier:<22} {n:>4} fichiers, {octets / 1e6:6.1f} Mo")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--voir" in sys.argv[1:]:
        voir()
    else:
        try:
            sauvegarder_sous_verrou(forcer="--forcer" in sys.argv[1:])
        except SauvegardeRefusee as e:
            sys.exit(f"Sauvegarde refusée : {e}")
