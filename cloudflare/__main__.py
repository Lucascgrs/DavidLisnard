"""Export des commentaires vers le bucket R2 privé rag-politique-sources-privees (docs/CLOUDFLARE.md).

    python -m cloudflare              refait le fichier de chaque source, envoie ceux qui ont changé
    python -m cloudflare preparer     seulement les fichiers Parquet, dans donnees/cloudflare/lots/
    python -m cloudflare envoyer      seulement l'envoi des fichiers préparés qui diffèrent du bucket
    python -m cloudflare etat         par source : fichier, commentaires, déposé ou en attente

Clés : R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY et R2_ENDPOINT dans config/cloudflare.env. Relancé seul après chaque
collecte qui ramène du neuf (collecte/__main__.py) et par le bouton « Export Cloudflare » de l'interface.
"""
import argparse
import sys

from cloudflare import export
from commun.journal import Journal
from commun.taches import DejaEnCours, verrou


def exporter(journal) -> dict:
    """Préparation puis envoi, sous le verrou « cloudflare » (une seule écriture à la fois)."""
    with verrou("cloudflare"):
        journal(f"### Export vers Cloudflare R2 ({export.BUCKET}/{export.DOSSIER})")
        export.preparer(journal)
        r = export.envoyer(journal)
        journal("### Export vers Cloudflare R2 terminé")
        return r


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m cloudflare", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", nargs="?", default="tout", choices=["tout", "preparer", "envoyer", "etat"])
    args = ap.parse_args()
    if args.action == "etat":
        e = export.etat()
        for source, nom, n, depose in e["sources"]:
            print(f"{nom:40} {n:>7} {'déposé, à jour' if depose else 'EN ATTENTE'}")
        print(f"Commentaires dans les fichiers : {e['exportes']} ; fichiers en attente d'envoi : {len(e['en_attente'])}")
        return
    journal = Journal()
    try:
        if args.action == "tout":
            exporter(journal)
        else:
            with verrou("cloudflare"):
                (export.preparer if args.action == "preparer" else export.envoyer)(journal)
    except DejaEnCours as e:
        sys.exit(f"Export déjà en cours (processus {e.pid}) : attendre sa fin.")


if __name__ == "__main__":
    main()
