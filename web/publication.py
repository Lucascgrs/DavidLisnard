"""Installer la base, y publier les données, mettre les pages en ligne.

La base suit un modèle normalisé (web/schema.sql) : sources, comptes, publications et utilisateurs ne sont écrits
qu'une fois, les commentaires ne portent que leurs propres données et des numéros. Les fichiers locaux
(corpus.csv, notes…) ne changent pas : la publication les traduit dans ce modèle.

La publication est incrémentale : donnees/web/publie.json garde l'empreinte de chaque ligne déjà envoyée, et seules
les lignes nouvelles ou changées partent (après une collecte : quelques secondes). --tout renvoie tout ; un état
d'un modèle antérieur aussi.
"""
import json
from pathlib import Path

from analyse.criteres import CRITERES
from commun.config import DONNEES
from commun.fichiers import ecrire_json, lire_json
from commun.textes import empreinte
from web import acces, export
from web.supabase import Base, Gestion
from web.vercel import Vercel

ICI = Path(__file__).resolve().parent
SITE = ICI / "site"
SCHEMA = ICI / "schema.sql"
ETAT = DONNEES / "web" / "publie.json"
CONFIG_JS = SITE / "js" / "config.js"
MODELE = 2  # modèle normalisé de schema.sql (2026-11-13) ; un état d'un autre modèle fait tout renvoyer


def installer(journal=print) -> None:
    """Crée ou met à jour la base (schema.sql), relève l'adresse et les clés, écrit la configuration des pages."""
    a = acces.exiger("supabase_jeton")
    g = Gestion(a["supabase_jeton"])
    projet = g.trouver_projet()
    ref = projet["id"]
    journal(f"   projet Supabase « {projet['name']} » ({ref}, {projet.get('region')})")
    g.attendre_actif(ref)
    g.sql(ref, SCHEMA.read_text(encoding="utf-8"))
    journal("   base créée ou mise à jour (schema.sql)")
    publique, secrete = g.cles(ref)
    url = f"https://{ref}.supabase.co"
    acces.sauver(supabase_projet=ref, supabase_url=url, supabase_cle_publique=publique, supabase_cle_secrete=secrete)
    ecrire_config_js(url, publique)
    journal(f"   adresse et clés enregistrées ; {CONFIG_JS.relative_to(ICI.parent)} écrit")


def ecrire_config_js(url: str, cle_publique: str) -> None:
    """La clé publique ne permet que de lire (règles de la base) : elle peut figurer dans les pages."""
    CONFIG_JS.write_text("// Écrit par « python -m web installer ». Clé publique : lecture seule.\n"
                         f"export const SUPABASE_URL = {json.dumps(url)};\n"
                         f"export const SUPABASE_CLE = {json.dumps(cle_publique)};\n", encoding="utf-8")


def _empreintes(lignes: list[dict], cle) -> dict[str, str]:
    return {cle(l): empreinte(json.dumps(l, ensure_ascii=False, sort_keys=True)) for l in lignes}


def _avancement(table: str, journal):
    return lambda f, n: journal(f"      {table} {f}/{n}") if f % 20000 == 0 or f == n else None


def _envoyer(base: Base, table: str, lignes: list[dict], conflit: str, cle, existants: dict, etat: dict | None,
             journal) -> bool:
    """Envoie les lignes absentes de la base (`existants`, clé → numéro) et, avec un état, celles qui ont changé
    depuis le dernier envoi. Sans état (modération), une ligne déjà présente n'est pas modifiée. Rend True si quelque
    chose est parti."""
    if etat is None:
        a_envoyer = [l for l in lignes if cle(l) not in existants]
    else:
        avant, maintenant = etat.get(table, {}), _empreintes(lignes, cle)
        a_envoyer = [l for l in lignes if cle(l) not in existants or avant.get(cle(l)) != maintenant[cle(l)]]
    if a_envoyer:
        journal(f"   {table} : {len(a_envoyer)} à envoyer")
        base.ecrire(table, a_envoyer, conflit, ignorer=etat is None, avancement=_avancement(table, journal))
    if etat is not None:
        etat[table] = maintenant
    return bool(a_envoyer)


class Numeros:
    """Numéros internes de la base (fonction correspondances() de schema.sql), par clés lisibles."""

    def __init__(self, brut: dict):
        self.brut = brut
        self.sources = brut["sources"]

    def source(self, nom: str) -> int:
        return self.sources[nom]

    def compte(self, source: str, nom: str) -> int:
        return self.brut["comptes"][f"{self.source(source)}|{nom}"]

    def publication(self, source: str, compte: str, code: str) -> int:
        return self.brut["publications"][f"{self.compte(source, compte)}|{code}"]

    def utilisateur(self, source: str, identifiant: str) -> int:
        return self.brut["utilisateurs"][f"{self.source(source)}|{identifiant}"]


def relier(base: Base, comptes: dict, publications: dict, utilisateurs: dict, etat: dict | None = None,
           journal=print) -> Numeros:
    """Écrit les tables de référence et rend leurs numéros internes.

    comptes : {(source, nom): groupe} ; publications : {(source, compte, code): {titre, lien, date}} ;
    utilisateurs : {(source, identifiant): nom affiché}. Avec `etat` (web publier), les lignes changées sont mises à
    jour et leurs empreintes notées dans etat ; sans (modération), seules les absentes sont ajoutées."""
    ids = base.appeler("correspondances")
    src = ids["sources"]
    lignes = [{"source": src[s], "nom": n, "groupe": g} for (s, n), g in sorted(comptes.items())]
    if _envoyer(base, "comptes", lignes, "source,nom", lambda l: f"{l['source']}|{l['nom']}", ids["comptes"],
                etat, journal):
        ids = base.appeler("correspondances")
    lignes = [{"source": src[s], "identifiant": i, "nom": n if n and n != i else None}
              for (s, i), n in sorted(utilisateurs.items())]
    envoye = _envoyer(base, "utilisateurs", lignes, "source,identifiant",
                      lambda l: f"{l['source']}|{l['identifiant']}", ids["utilisateurs"], etat, journal)
    lignes = [{"compte": ids["comptes"][f"{src[s]}|{c}"], "code": code, **p}
              for (s, c, code), p in sorted(publications.items())]
    envoye |= _envoyer(base, "publications", lignes, "compte,code", lambda l: f"{l['compte']}|{l['code']}",
                       ids["publications"], etat, journal)
    return Numeros(base.appeler("correspondances") if envoye else ids)


def ordre_des_parents(lignes: list[dict]) -> list[dict]:
    """Les commentaires dans un ordre où chaque parent précède ses réponses (clé étrangère parent → commentaire)."""
    par_cle = {(l["source"], l["code"]): l for l in lignes}
    prof: dict = {}

    def profondeur(k, n=0):
        if k not in prof:
            l = par_cle.get(k)
            prof[k] = 0 if not l or not l["parent"] or n > 200 else 1 + profondeur((l["source"], l["parent"]), n + 1)
        return prof[k]
    return sorted(lignes, key=lambda l: profondeur((l["source"], l["code"])))


def publier(tout: bool = False, journal=print) -> dict:
    """Envoie à Supabase ce qui a changé depuis la dernière publication. Rend le bilan."""
    a = acces.exiger("supabase_url", "supabase_cle_secrete")
    base = Base(a["supabase_url"], a["supabase_cle_secrete"])
    etat = {} if tout else (lire_json(ETAT, {}) or {})
    if etat.get("modele") != MODELE:  # premier envoi, --tout ou état de l'ancien modèle : tout repart
        etat = {"modele": MODELE}
    commentaires, publications = export.charger()
    auteurs = export.auteurs()  # clé du commentaire → (identifiant, nom affiché), lus dans les fichiers collectés
    num = relier(base,
                 comptes={(c["source"], c["compte"]): c["groupe"] for c in commentaires},
                 publications={(p["source"], p["compte"], p["code"]): {"titre": p["titre"], "lien": p["lien"],
                                                                       "date": p["date"]}
                               for p in publications.values()},
                 utilisateurs={(c["source"], u[0]): u[1] for c in commentaires if (u := auteurs.get(c["cle"]))},
                 etat=etat, journal=journal)
    ecrire_json(ETAT, etat, indent=None)

    # Retirés du corpus depuis la dernière fois (rare) : supprimés d'abord, l'état n'est réécrit qu'ensuite.
    retires = sorted(set(etat.get("commentaires", {})) - {c["cle"] for c in commentaires})
    par_source: dict[str, list[str]] = {}
    for cle in retires:
        s, code = cle.split(":", 1)
        par_source.setdefault(s, []).append(code)
    for s, codes in par_source.items():
        base.supprimer("commentaires", "code", codes, filtre={"source": f"eq.{num.source(s)}"})

    lignes = {}
    for c in commentaires:
        p = publications[c["publication"]]
        u = auteurs.get(c["cle"])
        lignes[c["cle"]] = {
            "source": num.source(c["source"]), "code": c["cle"].split(":", 1)[1],
            "publication": num.publication(p["source"], p["compte"], p["code"]),
            "utilisateur": num.utilisateur(c["source"], u[0]) if u else None,
            "parent": c["parent"].split(":", 1)[1] if c["parent"] else None,
            "date": c["date"], "reponse": c["reponse"], "likes": c["likes"], "texte": c["texte"],
            **{k: c[k] for k in CRITERES}, "cible": c["cible"], "fiabilite": c["fiabilite"]}
    avant = etat.get("commentaires", {})
    maintenant = {cle: empreinte(json.dumps(l, ensure_ascii=False, sort_keys=True)) for cle, l in lignes.items()}
    a_envoyer = ordre_des_parents([l for cle, l in lignes.items() if avant.get(cle) != maintenant[cle]])
    if a_envoyer:
        journal(f"   commentaires : {len(a_envoyer)} à envoyer")
        base.ecrire("commentaires", a_envoyer, "source,code", avancement=_avancement("commentaires", journal))
    etat["commentaires"] = maintenant
    ecrire_json(ETAT, etat, indent=None)

    syntheses = [{"nom": "meta", "donnees": export.meta(commentaires, publications)},
                 {"nom": "cube", "donnees": export.cube(commentaires)}]
    lecture = export.themes()
    if lecture:
        syntheses.append({"nom": "themes", "donnees": lecture})
    base.ecrire("syntheses", syntheses, "nom", paquet=1)  # une par envoi : ensemble, elles dépassent le délai de la base
    bilan = {"commentaires": len(a_envoyer), "retires": len(retires), "publications": len(publications)}
    journal(f"   publié : {bilan['commentaires']} commentaires nouveaux ou changés, {bilan['retires']} retirés "
            f"({len(commentaires)} en ligne, {len(publications)} publications) ; statistiques recalculées"
            + (f" ; {len(lecture['themes'])} thèmes" if lecture else ""))
    return bilan


def deployer(journal=print) -> str:
    a = acces.exiger("vercel_jeton")
    if not CONFIG_JS.exists() or "supabase.co" not in CONFIG_JS.read_text(encoding="utf-8"):
        raise acces.AccesManquant("lancer d'abord « python -m web installer » (js/config.js ne pointe pas vers Supabase)")
    url = Vercel(a["vercel_jeton"]).deployer(SITE, journal)
    acces.sauver(site_url=url)
    journal(f"   en ligne : {url}")
    return url
