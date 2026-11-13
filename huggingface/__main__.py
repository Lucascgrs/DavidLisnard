"""Export des commentaires vers le dataset Hugging Face privé rag-politique/politique-sources-privees (docs/HUGGINGFACE.md).

    python -m huggingface              refait le fichier de chaque source, envoie ceux qui ont changé
    python -m huggingface preparer     seulement les fichiers Parquet, dans donnees/huggingface/lots/
    python -m huggingface envoyer      seulement l'envoi des fichiers préparés qui diffèrent du dataset
    python -m huggingface etat         par source : fichier, commentaires, déposé ou en attente

Jeton : HF_TOKEN dans config/huggingface.env, sinon celui de « hf auth login ». Relancé seul après chaque collecte
qui ramène du neuf (collecte/__main__.py) et par le bouton « Exporter vers Hugging Face » de l'interface.
"""
import argparse
import os
import sys

# analyse/__init__.py met Hugging Face hors ligne (modèles lus sur le disque) ; l'export, lui, doit joindre le
# dataset. À poser avant tout import de huggingface_hub, qui lit ce réglage une fois pour toutes.
os.environ["HF_HUB_OFFLINE"] = "0"

from commun.journal import Journal
from commun.taches import DejaEnCours, verrou
from huggingface import export


def exporter(journal) -> dict:
    """Préparation puis envoi, sous le verrou « huggingface » (une seule écriture à la fois)."""
    with verrou("huggingface"):
        journal(f"### Export vers Hugging Face ({export.DEPOT}/{export.DOSSIER_HF})")
        hf = export.api()
        export.preparer(journal)
        r = export.envoyer(journal, hf)
        journal("### Export vers Hugging Face terminé")
        return r


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m huggingface", description=__doc__,
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
            with verrou("huggingface"):
                (export.preparer if args.action == "preparer" else export.envoyer)(journal)
    except DejaEnCours as e:
        sys.exit(f"Export déjà en cours (processus {e.pid}) : attendre sa fin.")


if __name__ == "__main__":
    main()
