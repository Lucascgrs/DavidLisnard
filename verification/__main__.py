"""python -m verification <commande>

  corpus                     copie les Parquet Nouvelle Énergie du RAG (R2, lecture seule) dans corpus/
  chercher "<motif>" [n]     passages du corpus qui contiennent le motif (expression régulière), n au plus
  registre <theme>           réécrit affirmations.csv du thème (citations vérifiées dans le corpus)
  telecharger <theme>        refait les téléchargements du thème et remplit son sources.csv
  calculer <theme>           refait les calculs du thème à partir de brut/
  verifier [theme]           contrôles automatiques (catalogue, empreintes, renvois, verdicts)
  synthese                   régénère SYNTHESE.md à partir des resultats et du registre

<theme> = numéro (1) ou nom du dossier (01_dette_depense_fiscalite).
"""
import runpy
import sys

from .commun.chemins import THEMES


def dossier_theme(nom: str):
    for d in sorted(THEMES.iterdir()):
        if d.is_dir() and (d.name == nom or d.name.split("_")[0] == nom.zfill(2)):
            return d
    raise SystemExit(f"Thème introuvable : {nom}")


def main(args: list[str]) -> None:
    if not args or args[0] in {"-h", "--help", "aide"}:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "corpus":
        from .commun.corpus import telecharger_corpus
        for p in telecharger_corpus():
            print("  ", p.name)
    elif cmd == "chercher":
        from .commun.corpus import chercher
        n = int(args[2]) if len(args) > 2 else 40
        for r in chercher(args[1], limite=n):
            print(f"[{r['date']}] {r['type_source']}/{r['sous_type']} · {r['titre']}\n   {r['url_source']}\n"
                  f"   … {r['passage']} …\n")
    elif cmd == "registre":
        d = dossier_theme(args[1])
        runpy.run_path(str(d / "registre.py"), run_name="__main__")
    elif cmd == "telecharger":
        d = dossier_theme(args[1])
        runpy.run_path(str(d / "telecharger.py"), run_name="__main__")
    elif cmd == "calculer":
        d = dossier_theme(args[1])
        runpy.run_path(str(d / "calculs" / "calculer.py"), run_name="__main__")
    elif cmd == "verifier":
        from .controles import verifier
        ok = verifier(args[1] if len(args) > 1 else None)
        sys.exit(0 if ok else 1)
    elif cmd == "synthese":
        from .synthese import ecrire_synthese
        print(ecrire_synthese())
    else:
        raise SystemExit(f"Commande inconnue : {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
