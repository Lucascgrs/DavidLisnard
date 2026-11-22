"""Les personnes vérifiées : une fiche par candidat (corpus, dossiers de scripts et de données, site).

David Lisnard (Nouvelle Énergie), le premier fait, garde ses dossiers d'origine : verification/themes/ et
donnees/verification/. Chaque nouveau candidat a son sous-dossier, du même nom que sa clé : verification/<clé>/
(conclusions.py, themes/) et donnees/verification/<clé>/ (corpus/, themes/, registre_affirmations.csv, SYNTHESE.md).

Le site est commun à tous (verification/site/, « Vérification politique ») : chaque personne y a un dossier du nom de
sa clé, et y apparaît dès qu'elle a un thème terminé.

Les thèmes portent les mêmes numéros et les mêmes noms de dossier pour tous (commun/themes.py) : c'est ce qui permet
de comparer les candidats thème par thème.

python -m verification <clé> <commande>   (sans clé : lisnard)
"""
from dataclasses import dataclass
from pathlib import Path

from commun.config import DONNEES as DONNEES_PROJET

RACINE = Path(__file__).resolve().parent.parent  # le code : verification/
DONNEES_VERIF = DONNEES_PROJET / "verification"


@dataclass(frozen=True)
class Personne:
    cle: str
    nom: str                 # « David Lisnard »
    parti: str               # « Nouvelle Énergie »
    partis_r2: tuple         # dossiers de parti dans le bucket R2 du RAG (data/<type>/<parti>/…)
    code: Path               # verification/ ou verification/<clé>/
    donnees: Path            # donnees/verification/ ou donnees/verification/<clé>/
    titre_site: str          # titre de ses pages sur le site commun
    module_conclusions: str  # module Python de la couche de lecture du site
    nom_court: str = ""      # « Lisnard »

    @property
    def scripts(self) -> Path:
        return self.code / "themes"

    @property
    def themes(self) -> Path:
        return self.donnees / "themes"

    @property
    def corpus(self) -> Path:
        return self.donnees / "corpus"

    @property
    def registre(self) -> Path:
        return self.donnees / "registre_affirmations.csv"

    @property
    def synthese(self) -> Path:
        return self.donnees / "SYNTHESE.md"


PERSONNES = {
    "lisnard": Personne("lisnard", "David Lisnard", "Nouvelle Énergie", ("nouvelle-energie",), RACINE, DONNEES_VERIF,
                        "Lisnard à l'épreuve des chiffres", "verification.conclusions",
                        "Lisnard"),
    "melenchon": Personne("melenchon", "Jean-Luc Mélenchon", "La France insoumise", ("lfi",), RACINE / "melenchon",
                          DONNEES_VERIF / "melenchon", "Mélenchon à l'épreuve des chiffres",
                          "verification.melenchon.conclusions", "Mélenchon"),
}
DEFAUT = "lisnard"


def personne(cle: str | None = None) -> Personne:
    return PERSONNES[cle or DEFAUT]


def personne_du_chemin(chemin: str | Path) -> Personne:
    """La personne dont un script ou un fichier de données fait partie (le dossier le plus précis l'emporte)."""
    p = Path(chemin).resolve()
    trouves = [(len(r.parts), x) for x in PERSONNES.values() for r in (x.scripts, x.themes, x.donnees)
               if p.is_relative_to(r)]
    if not trouves:
        raise ValueError(f"{p} n'appartient à aucune personne de verification/")
    return max(trouves, key=lambda t: t[0])[1]
