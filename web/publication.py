"""Installer la base, y publier les données, mettre les pages en ligne.

La publication est incrémentale : donnees/web/publie.json garde l'empreinte de chaque ligne déjà envoyée, et seules
les lignes nouvelles ou changées partent (après une collecte : quelques secondes). --tout renvoie tout.
"""
import json
from pathlib import Path

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


def _empreintes(lignes: list[dict], cle: str) -> dict[str, str]:
    return {l[cle]: empreinte(json.dumps(l, ensure_ascii=False, sort_keys=True)) for l in lignes}


def publier(tout: bool = False, journal=print) -> dict:
    """Envoie à Supabase ce qui a changé depuis la dernière publication. Rend le bilan."""
    a = acces.exiger("supabase_url", "supabase_cle_secrete")
    base = Base(a["supabase_url"], a["supabase_cle_secrete"])
    etat = {} if tout else (lire_json(ETAT, {}) or {})
    commentaires, publications = export.charger()
    publications = list(publications.values())
    # Retirés du corpus depuis la dernière fois (rare) : supprimés d'abord, l'état n'est réécrit qu'ensuite.
    retires = sorted(set(etat.get("commentaires", {})) - {c["cle"] for c in commentaires})
    if retires:
        base.supprimer("commentaires", "cle", retires)
    bilan = {"retires": len(retires)}
    for table, lignes, cle in (("publications", publications, "id"), ("commentaires", commentaires, "cle")):
        avant = etat.get(table, {})
        maintenant = _empreintes(lignes, cle)
        a_envoyer = [l for l in lignes if avant.get(l[cle]) != maintenant[l[cle]]]
        if a_envoyer:
            journal(f"   {table} : {len(a_envoyer)} à envoyer")
            base.ecrire(table, a_envoyer, cle, avancement=lambda f, n, t=table: journal(
                f"      {t} {f}/{n}") if f % 20000 == 0 or f == n else None)
        bilan[table] = len(a_envoyer)
        etat[table] = maintenant
        ecrire_json(ETAT, etat, indent=None)  # après chaque table : une coupure ne fait pas tout renvoyer
    syntheses = [{"nom": "meta", "donnees": export.meta(commentaires, {p["id"]: p for p in publications})},
                 {"nom": "cube", "donnees": export.cube(commentaires)}]
    lecture = export.themes()
    if lecture:
        syntheses.append({"nom": "themes", "donnees": lecture})
    base.ecrire("syntheses", syntheses, "nom", paquet=1)  # une par envoi : ensemble, elles dépassent le délai de la base
    journal(f"   publié : {bilan['commentaires']} commentaires et {bilan['publications']} publications nouveaux ou "
            f"changés, {bilan['retires']} retirés ; statistiques recalculées"
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
