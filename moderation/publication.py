"""Envoi des catégories de modération dans la table privée « moderation » de Supabase (web/schema.sql).

Incrémental, comme la publication du site : donnees/moderation/publie.json garde l'empreinte de chaque ligne déjà
envoyée ; seules les lignes nouvelles ou changées partent. Rien n'est envoyé au site lui-même : la table n'a aucune
règle de lecture publique.

Modèle normalisé : une ligne porte la classification (probabilités du modèle, version, annotation) et des numéros
vers publications et utilisateurs (table privée des auteurs). Le commentaire lui-même (publication, auteur, date,
texte, parent) n'est écrit que s'il n'est pas déjà dans la table commentaires du site ; la vue moderation_complete
le reprend de l'une ou de l'autre, avec la catégorie retenue (annotation, sinon modèle) et le lien direct. Les
comptes, publications et auteurs Facebook qui manquent encore y sont ajoutés, sans toucher à ceux du site.
"""
import json

from commun.fichiers import ecrire_json, lire_json
from commun.textes import empreinte
from moderation import donnees as d

ETAT = d.DOSSIER / "publie.json"
MODELE = 2  # modèle normalisé de web/schema.sql (2026-11-13) ; un état d'un autre modèle fait tout renvoyer


def _sur_le_site() -> dict[str, str | None]:
    """Commentaires Facebook déjà dans la table commentaires (d'après l'état de « python -m web publier ») → leur
    parent tel que publié (clé, ou None)."""
    from web import export
    from web import publication as web
    etat = lire_json(web.ETAT, {}) or {}
    if etat.get("modele") != web.MODELE:
        return {}
    envoyes = etat.get("commentaires", {})
    commentaires, _ = export.charger()
    return {c["cle"]: c["parent"] for c in commentaires if c["source"] == "facebook" and c["cle"] in envoyes}


def lignes(num, sur_le_site: dict) -> list[dict]:
    """Une ligne par commentaire classé ou annoté, au format de la table moderation."""
    notes, ann = d.lire_notes(), d.lire_annotations()
    com = {c["cle"]: c for c in d.commentaires()}
    sortie = []
    for cle in sorted(set(notes) | set(ann)):
        n, a, c = notes.get(cle), ann.get(cle), com.get(cle)
        f = lambda k: float(n[k]) if n and n.get(k) else None  # noqa: E731
        ligne = {"source": num.source("facebook"), "code": cle.split(":", 1)[1],
                 "p_insultant": f("p_insultant"), "p_question": f("p_question"), "p_autre": f("p_autre"),
                 "version": n["version"] if n else None, "annotation": a["categorie"] if a else None,
                 "classe_le": n["classe_le"] if n else None,
                 "publication": None, "utilisateur": None, "parent": None, "date": None, "texte": None}
        if c:
            parent = f"facebook:{c['parent_id']}" if c.get("parent_id") else None
            if cle in sur_le_site:  # le reste vient de la table commentaires ; le vrai parent seulement s'il diffère
                if parent != sur_le_site[cle]:
                    ligne["parent"] = c["parent_id"] or None
            else:
                ident = (c.get("auteur_id") or c.get("auteur") or "").strip()
                ligne.update({
                    "publication": num.publication("facebook", c.get("compte_source"), c["publication_id"])
                    if c.get("publication_id") and c.get("compte_source") else None,
                    "utilisateur": num.utilisateur("facebook", ident) if ident else None,
                    "parent": c.get("parent_id") or None, "date": (c.get("date") or "")[:19] or None,
                    "texte": c.get("texte") or None})
        sortie.append(ligne)
    return sortie


def references(cles: set[str]) -> tuple[dict, dict, dict]:
    """Comptes, publications et auteurs Facebook des commentaires `cles`, au format de web.publication.relier()."""
    from analyse.corpus import GROUPE_PAR_DEFAUT, groupes
    grp = groupes()
    comptes, publications, utilisateurs = {}, {}, {}
    for c in d.commentaires():
        if c["cle"] not in cles:
            continue
        compte, pid = c.get("compte_source"), c.get("publication_id")
        if compte and pid:
            comptes[("facebook", compte)] = grp.get(("facebook", compte), GROUPE_PAR_DEFAUT)
            p = publications.setdefault(("facebook", compte, pid), {
                "titre": None, "lien": c.get("publication_lien") or None,
                "date": (c.get("publication_date") or "")[:19] or None})
            if not p["titre"] and c.get("publication_titre"):
                p["titre"] = c["publication_titre"][:600]
        ident = (c.get("auteur_id") or c.get("auteur") or "").strip()
        if ident:
            utilisateurs[("facebook", ident)] = (c.get("auteur") or "").strip()
    return comptes, publications, utilisateurs


def publier(tout: bool = False, journal=print) -> int:
    """Envoie ce qui a changé ; rend le nombre de lignes envoyées. Sans accès Supabase configuré, ne fait rien."""
    from web import acces
    from web.publication import relier
    from web.supabase import Base
    if not acces.pret_a_publier():
        journal("Supabase n'est pas configuré (config/web.json) : rien n'est envoyé.")
        return 0
    a = acces.lire()
    base = Base(a["supabase_url"], a["supabase_cle_secrete"])
    etat = {} if tout else (lire_json(ETAT, {}) or {})
    if etat.get("modele") != MODELE:
        etat = {}
    avant = etat.get("lignes", {})
    sur_le_site = _sur_le_site()
    a_classer = set(d.lire_notes()) | set(d.lire_annotations())
    # Les clés étrangères exigent comptes, publications et auteurs d'abord ; ceux du site ne sont pas modifiés.
    comptes, publications, utilisateurs = references(a_classer - set(sur_le_site))
    num = relier(base, comptes, publications, utilisateurs, etat=None, journal=journal)
    tout_ = lignes(num, sur_le_site)
    maintenant = {l["code"]: empreinte(json.dumps(l, ensure_ascii=False, sort_keys=True)) for l in tout_}
    a_envoyer = [l for l in tout_ if avant.get(l["code"]) != maintenant[l["code"]]]
    retires = sorted(set(avant) - set(maintenant))
    if retires:
        base.supprimer("moderation", "code", retires, filtre={"source": f"eq.{num.source('facebook')}"})
    if a_envoyer:
        base.ecrire("moderation", a_envoyer, "source,code")
    ecrire_json(ETAT, {"modele": MODELE, "lignes": maintenant}, indent=None)
    journal(f"Supabase (table privée moderation) : {len(a_envoyer)} lignes envoyées, {len(retires)} retirées, "
            f"{len(tout_)} au total ({len(sur_le_site)} commentaires Facebook déjà sur le site, texte non recopié).")
    return len(a_envoyer)
