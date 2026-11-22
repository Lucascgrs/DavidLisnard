"""python -m verification [personne] <commande>

  personne : lisnard (par défaut) ou melenchon (voir verification/commun/personnes.py)

  corpus                     copie les Parquet du parti de la personne depuis le RAG (R2, lecture seule) dans donnees/verification/corpus/
  chercher "<motif>" [n]     passages du corpus qui contiennent le motif (expression régulière), n au plus
  registre <theme>           réécrit affirmations.csv du thème (citations vérifiées dans le corpus)
  telecharger <theme>        refait les téléchargements du thème et remplit son sources.csv
  calculer <theme>           refait les calculs du thème à partir de brut/
  verifier [theme]           contrôles automatiques (catalogue, empreintes, renvois, verdicts)
  synthese                   régénère SYNTHESE.md à partir des resultats et du registre
  site [apercu|deployer]     régénère le site statique (site/) ; apercu l'ouvre en local, deployer le met en ligne

  themes                     catalogue commun des thèmes, et qui est vérifié sur chacun

<theme> = numéro (1) ou nom du dossier (01_dette_depense_fiscalite). Les numéros et les noms de dossier sont les mêmes
pour toutes les personnes (verification/commun/themes.py).
Exemple : python -m verification melenchon calculer 6
"""
import runpy
import sys

from .commun.personnes import PERSONNES, personne


def dossier_theme(nom: str, cle: str | None = None):
    """Dossier des scripts du thème (ses données : <données de la personne>/themes/, même nom)."""
    for d in sorted(personne(cle).scripts.iterdir()):
        if d.is_dir() and (d.name == nom or d.name.split("_")[0] == nom.zfill(2)):
            return d
    raise SystemExit(f"Thème introuvable : {nom}")


def main(args: list[str]) -> None:
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cle = None
    if args and args[0] in PERSONNES:
        cle, args = args[0], args[1:]
    if not args or args[0] in {"-h", "--help", "aide"}:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "corpus":
        from .commun.corpus import telecharger_corpus
        for p in telecharger_corpus(cle):
            print("  ", p.name)
    elif cmd == "chercher":
        from .commun.corpus import chercher
        n = int(args[2]) if len(args) > 2 else 40
        for r in chercher(args[1], limite=n, cle=cle):
            print(f"[{r['date']}] {r['id_corpus']} · {r['type_source']}/{r['sous_type']} · {r['titre']}\n   {r['url_source']}\n"
                  f"   … {r['passage']} …\n")
    elif cmd == "registre":
        d = dossier_theme(args[1], cle)
        runpy.run_path(str(d / "registre.py"), run_name="__main__")
    elif cmd == "telecharger":
        d = dossier_theme(args[1], cle)
        runpy.run_path(str(d / "telecharger.py"), run_name="__main__")
    elif cmd == "calculer":
        d = dossier_theme(args[1], cle)
        runpy.run_path(str(d / "calculs" / "calculer.py"), run_name="__main__")
    elif cmd == "verifier":
        from .controles import verifier
        ok = verifier(args[1] if len(args) > 1 else None, cle)
        sys.exit(0 if ok else 1)
    elif cmd == "synthese":
        from .synthese import ecrire_synthese
        print(ecrire_synthese(cle))
    elif cmd == "site":
        from .site import main as site
        site(args[1:], cle)
    elif cmd == "themes":
        from .commun.themes import tableau
        print(tableau())
    else:
        raise SystemExit(f"Commande inconnue : {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
