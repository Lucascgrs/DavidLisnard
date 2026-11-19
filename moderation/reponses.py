"""Réponses préparées pour les modérateurs, et thèmes des commentaires Facebook (demande du 2026-11-19).

Le gestionnaire du groupe « Cap 2027 avec David Lisnard » veut répondre vite aux commentaires qui appellent une
réponse (« Macron bis », « le RN fera mieux »…) : le site de modération propose, pour chaque commentaire, des
réponses toutes faites, plusieurs par objection et dans des styles différents (chiffres, arguments, courte,
bienveillante, punchline). Deux choses pour y arriver :

1. La bibliothèque des réponses : moderation/reponses.xlsx (feuilles « Réponses » et « Thèmes »), écrite d'abord
   par Claude à partir des synthèses des thèmes (donnees/critiques/themes.json) et des faits vérifiés
   (verification/ : seulement les chiffres jugés exacts ou plutôt exacts, et les mesures présentées comme des
   propositions). Elle est copiée dans les tables reponses et reponses_themes de Supabase, où les modérateurs
   l'enrichissent depuis le site (modifier, ajouter une réponse, ajouter un thème). « python -m moderation
   reponses » synchronise dans les deux sens : ce qui n'a changé que d'un côté passe de l'autre ; si une même ligne a
   changé des deux côtés, la version du site est gardée et celle du fichier est montrée dans le journal. Une ligne
   effacée du fichier est désactivée sur le site (actif = non), jamais supprimée ; le site, lui, ne fait que
   désactiver.

2. Le thème de chaque commentaire : les thèmes sont ceux de l'analyse (T1…T59, lus par Claude dans la sélection),
   plus ceux qu'ajoutent les modérateurs (M-…). Un commentaire déjà rangé par Claude pour les thèmes
   (rattachements.csv, critique ou doute) garde ces thèmes ; les autres, parmi ceux qui appellent une réponse,
   sont rangés par lots, par Gemini (moderation/PROMPT_GEMINI_THEMES.md) ou par Claude : « themes tirer » prépare
   un lot (la liste des thèmes, puis les commentaires), « themes noter K fichier » enregistre la lecture (une ligne
   « numéro: T31 T43 » ou « numéro: - » par commentaire). Ce qui est rangé ne l'est jamais deux fois. Les thèmes
   partent dans la colonne themes de la table moderation (moderation/publication.py).

Fichiers : moderation/reponses.xlsx (la bibliothèque, dans le dépôt), donnees/moderation/reponses_etat.json
(empreintes de la dernière synchronisation), donnees/moderation/themes.csv (cle, themes, lot, par, le) et
donnees/moderation/lots_themes/ (lots tirés, lectures).
"""
import random
import re
import secrets
from pathlib import Path

from commun.fichiers import ecrire_csv, ecrire_json, lire_csv, lire_json
from commun.textes import empreinte, maintenant
from moderation import donnees as d

ICI = Path(__file__).resolve().parent
FICHIER = ICI / "reponses.xlsx"
ETAT = d.DOSSIER / "reponses_etat.json"
CLASSEMENT = d.DOSSIER / "themes.csv"
LOTS = d.DOSSIER / "lots_themes"

# Le groupe que montre le site de modération (même liste que moderation_publications() dans web/schema.sql).
GROUPES = ("Cap 2027 avec David Lisnard",)
STYLES = {"chiffres": "Avec des chiffres", "arguments": "Argumentée", "courte": "Courte",
          "bienveillante": "Bienveillante", "punchline": "Punchline"}
CHAMPS = {
    "themes": ["id", "nom", "famille", "definition", "actif", "par", "maj"],
    "reponses": ["id", "theme", "objection", "style", "titre", "texte", "gif", "sources", "ordre", "actif", "par",
                 "maj"],
}
# Ce qui compte pour savoir si une ligne a changé (ni l'auteur ni la date de la dernière écriture).
CONTENU = {"themes": ["nom", "famille", "definition", "actif"],
           "reponses": ["theme", "objection", "style", "titre", "texte", "gif", "sources", "ordre", "actif"]}
TABLES = {"themes": "reponses_themes", "reponses": "reponses"}
FEUILLES = {"reponses": "Réponses", "themes": "Thèmes"}
ENTETES = {
    "id": "Identifiant", "nom": "Nom", "famille": "Famille", "definition": "Définition", "actif": "Actif",
    "par": "Écrit par", "maj": "Modifié le", "theme": "Thème", "objection": "Objection", "style": "Style",
    "titre": "Titre", "texte": "Texte de la réponse", "gif": "GIF (mot à chercher)", "sources": "Sources",
    "ordre": "Ordre",
}
TAILLE_LOT = 100
MAX_THEMES = 3
CHAMPS_CLASSEMENT = ["cle", "themes", "lot", "par", "le"]


# ── La bibliothèque : fichier Excel ─────────────────────────────────────────────────────────────────────────────

def _normal(genre: str, l: dict) -> dict:
    """Une ligne propre : textes sans espaces autour, actif en booléen, ordre en entier."""
    sortie = {}
    for c in CHAMPS[genre]:
        v = l.get(c)
        if c == "actif":  # vide = actif ; « non », « faux », 0… = retiré
            v = v if isinstance(v, bool) else str(v or "").strip().lower() not in ("non", "false", "0", "faux", "n")
        elif c == "ordre":
            try:
                v = int(float(v)) if v not in (None, "") else 0
            except ValueError:
                v = 0
        else:
            v = "" if v is None else str(v).strip()
        sortie[c] = v
    return sortie


def _empreinte(genre: str, l: dict | None) -> str | None:
    return None if l is None else empreinte(*(l[c] for c in CONTENU[genre]))


def lire_fichier() -> dict[str, dict[str, dict]]:
    """{"themes": {id: ligne}, "reponses": {id: ligne}} ; une ligne sans identifiant en reçoit un (ajout fait à la
    main dans Excel)."""
    sortie = {"themes": {}, "reponses": {}}
    if not FICHIER.exists():
        return sortie
    from openpyxl import load_workbook
    classeur = load_workbook(FICHIER, read_only=True, data_only=True)
    pour_entete = {v: k for k, v in ENTETES.items()}
    for genre, feuille in FEUILLES.items():
        if feuille not in classeur.sheetnames:
            continue
        lignes = list(classeur[feuille].iter_rows(values_only=True))
        if not lignes:
            continue
        cols = [pour_entete.get(str(e or "").strip(), str(e or "").strip()) for e in lignes[0]]
        for valeurs in lignes[1:]:
            brut = dict(zip(cols, valeurs))
            if not any(v not in (None, "") for v in brut.values()):
                continue
            l = _normal(genre, brut)
            if not l["id"]:
                l["id"] = ("R-" if genre == "reponses" else "M-") + secrets.token_hex(4)
            sortie[genre][l["id"]] = l
    classeur.close()
    return sortie


def ecrire_fichier(contenu: dict[str, dict[str, dict]]) -> None:
    """Réécrit le classeur : les réponses par thème puis par ordre, les thèmes par identifiant, et une feuille d'aide."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    noms = {t["id"]: t["nom"] for t in contenu["themes"].values()}
    cle_theme = lambda i: (0, int(i[1:])) if re.fullmatch(r"T\d+", i or "") else (1, i or "")  # noqa: E731
    classeur = Workbook()
    classeur.remove(classeur.active)
    largeurs = {"id": 13, "theme": 8, "objection": 34, "style": 13, "titre": 34, "texte": 90, "gif": 16,
                "sources": 40, "ordre": 7, "actif": 7, "par": 12, "maj": 18, "nom": 36, "famille": 14,
                "definition": 80}
    for genre in ("reponses", "themes"):
        f = classeur.create_sheet(FEUILLES[genre])
        champs = CHAMPS[genre] + (["nom_theme"] if genre == "reponses" else [])
        f.append([ENTETES.get(c, "Nom du thème (lecture seule)") for c in champs])
        if genre == "reponses":
            lignes = sorted(contenu[genre].values(), key=lambda l: (cle_theme(l["theme"]), l["objection"], l["ordre"]))
        else:
            lignes = sorted(contenu[genre].values(), key=lambda l: cle_theme(l["id"]))
        for l in lignes:
            f.append([("oui" if l[c] else "non") if c == "actif" else l[c] if c in l else noms.get(l["theme"], "")
                      for c in champs])
        for i, c in enumerate(champs):
            lettre = f.cell(row=1, column=i + 1).column_letter
            f.column_dimensions[lettre].width = largeurs.get(c, 30)
        for cellule in f[1]:
            cellule.font = Font(bold=True, color="FFFFFF")
            cellule.fill = PatternFill("solid", fgColor="1D3F8F")
        for rang in f.iter_rows(min_row=2):
            for cellule in rang:
                cellule.alignment = Alignment(wrap_text=True, vertical="top")
        f.freeze_panes = "B2"
        f.auto_filter.ref = f.dimensions
        if genre == "reponses":
            liste = DataValidation(type="list", formula1='"' + ",".join(STYLES) + '"', allow_blank=False)
            f.add_data_validation(liste)
            liste.add(f"D2:D{max(len(lignes) + 200, 300)}")
    aide = classeur.create_sheet("Lisez-moi")
    for ligne in [
        "Réponses préparées du site de modération. Ce fichier et la base Supabase se synchronisent dans les deux sens :",
        "python -m moderation reponses (depuis le dossier DavidLisnard).",
        "",
        "- Ajouter une réponse : nouvelle ligne dans « Réponses », identifiant vide (il est donné à la synchronisation).",
        "- Thème : identifiant de la feuille « Thèmes » (T31…, ou M-… pour un thème ajouté par un modérateur).",
        "- Objection : ce à quoi la réponse répond ; les réponses d'une même objection sont regroupées sur le site.",
        "- Style : " + ", ".join(f"{k} ({v})" for k, v in STYLES.items()) + ".",
        "- Retirer une réponse : Actif = non (ou effacer la ligne : elle est alors désactivée sur le site).",
        "- Si une même réponse a été modifiée ici et sur le site, la version du site est gardée.",
        "- Les colonnes « Écrit par », « Modifié le » et « Nom du thème » sont remplies seules.",
        "- Chiffres : n'utiliser que des chiffres sourcés (colonne Sources), à vérifier avant de publier.",
    ]:
        aide.append([ligne])
    aide.column_dimensions["A"].width = 120
    tmp = FICHIER.with_name("reponses_nouveau.xlsx")
    classeur.save(tmp)
    tmp.replace(FICHIER)


def themes_analyse() -> dict[str, dict]:
    """Les thèmes de l'analyse (donnees/critiques/themes.json), au format de la feuille « Thèmes »."""
    from critiques import donnees as cd
    t = lire_json(cd.THEMES, {}) or {}
    return {i: _normal("themes", {"id": i, "nom": v["nom"], "famille": cd.FAMILLES.get(v.get("famille"), ""),
                                  "definition": v.get("definition", ""), "actif": True, "par": "analyse"})
            for i, v in (t.get("themes") or {}).items()}


# ── Synchronisation avec Supabase ─────────────────────────────────────────────────────────────────────────────

def _base():
    from web import acces
    from web.supabase import Base
    if not acces.pret_a_publier():
        raise SystemExit("Supabase n'est pas configuré (config/web.json) : lancer d'abord « python -m web installer ».")
    a = acces.lire()
    return Base(a["supabase_url"], a["supabase_cle_secrete"])


def fusionner(genre: str, fichier: dict, site: dict, avant: dict, journal=print):
    """Fusion à trois voies d'un genre de lignes. Rend (résultat, lignes à écrire sur le site)."""
    resultat, envoyer = {}, []
    for i in sorted(set(fichier) | set(site)):
        f, s, b = fichier.get(i), site.get(i), avant.get(i)
        hf, hs = _empreinte(genre, f), _empreinte(genre, s)
        if f and s:
            if hf == hs or hf == b:          # identiques, ou seul le site a changé
                resultat[i] = s
            elif hs == b:                    # seul le fichier a changé
                resultat[i] = f
                envoyer.append(f)
            else:                            # changé des deux côtés : le site l'emporte
                resultat[i] = s
                journal(f"   conflit sur {i} : la version du site est gardée ; celle du fichier était : "
                        f"{f.get('titre') or f.get('nom')} — {(f.get('texte') or f.get('definition'))[:300]}")
        elif f:                              # nouvelle dans le fichier (ou absente du site) : on l'envoie
            resultat[i] = f
            envoyer.append(f)
        elif b is not None and hs == b and s["actif"]:  # effacée du fichier, inchangée sur le site : désactivée
            s = {**s, "actif": False}
            resultat[i] = s
            envoyer.append(s)
        else:                                # ajoutée ou changée sur le site
            resultat[i] = s
    return resultat, envoyer


def synchroniser(journal=print) -> dict:
    """Fichier ↔ Supabase (voir le début du module). Ajoute aussi au fichier les thèmes de l'analyse qui y manquent."""
    base = _base()
    fichier = lire_fichier()
    for i, t in themes_analyse().items():
        fichier["themes"].setdefault(i, t)
    themes_connus = set(fichier["themes"])
    etat = lire_json(ETAT, {}) or {}
    resultat = {}
    bilan = {}
    for genre in ("themes", "reponses"):
        site = {l["id"]: _normal(genre, l) for l in base.lire(TABLES[genre], "id")}
        if genre == "reponses":
            themes_connus |= set(resultat["themes"])
            for l in fichier[genre].values():
                if l["theme"] not in themes_connus:
                    raise SystemExit(f"Réponse {l['id']} : thème inconnu « {l['theme']} » (feuille Thèmes).")
                if l["style"] not in STYLES:
                    raise SystemExit(f"Réponse {l['id']} : style inconnu « {l['style']} » ({', '.join(STYLES)}).")
                if not (l["objection"] and l["titre"] and l["texte"]):
                    raise SystemExit(f"Réponse {l['id']} : objection, titre et texte sont obligatoires.")
        res, envoyer = fusionner(genre, fichier[genre], site, etat.get(genre, {}), journal)
        if envoyer:
            base.ecrire(TABLES[genre], [{c: (l[c] if l[c] != "" else None) for c in CHAMPS[genre] if c != "maj"}
                                        for l in envoyer], "id")
        envoyes = {l["id"] for l in envoyer}
        recus = sum(1 for i, l in res.items()
                    if i not in envoyes and _empreinte(genre, l) != _empreinte(genre, fichier[genre].get(i)))
        bilan[genre] = {"envoyees": len(envoyer), "recues": recus, "total": len(res),
                        "actives": sum(l["actif"] for l in res.values())}
        resultat[genre] = res
    ecrire_fichier(resultat)
    ecrire_json(ETAT, {**{g: {i: _empreinte(g, l) for i, l in resultat[g].items()} for g in resultat},
                       "le": maintenant()})
    journal(f"Réponses préparées : {bilan['reponses']['actives']} réponses actives sur "
            f"{bilan['themes']['actives']} thèmes ; envoyées au site : {bilan['reponses']['envoyees']} réponses, "
            f"{bilan['themes']['envoyees']} thèmes ; reçues du site : {bilan['reponses']['recues']} réponses, "
            f"{bilan['themes']['recues']} thèmes. Fichier : {FICHIER}")
    return bilan


# ── Thèmes des commentaires ────────────────────────────────────────────────────────────────────────────────────

def themes_actifs() -> dict[str, dict]:
    """Les thèmes proposés à la lecture : ceux du fichier, sinon ceux de l'analyse (avant la 1re synchronisation)."""
    t = lire_fichier()["themes"] or themes_analyse()
    return {i: l for i, l in t.items() if l["actif"]}


def lire_classement() -> dict[str, dict]:
    return {l["cle"]: l for l in lire_csv(CLASSEMENT)}


def themes_lus_par_claude() -> dict[str, list[str]]:
    """Thèmes des critiques et doutes rangés par Claude pour l'analyse (rattachements.csv), par commentaire."""
    from critiques import donnees as cd
    sortie: dict[str, list[str]] = {}
    for r in lire_csv(cd.RATTACHEMENTS):
        if r.get("sens") in ("C", "D") and r["theme"] not in sortie.setdefault(r["cle"], []):
            sortie[r["cle"]].append(r["theme"])
    return {k: v for k, v in sortie.items() if v}


def themes_par_commentaire() -> dict[str, str]:
    """Les thèmes retenus de chaque commentaire Facebook (« T31 T43 ») : la lecture pour les réponses, sinon celle
    de l'analyse. Un commentaire lu sans thème (« - ») n'en a pas."""
    sortie = {k: " ".join(v[:MAX_THEMES]) for k, v in themes_lus_par_claude().items() if k.startswith("facebook:")}
    for cle, l in lire_classement().items():
        if l["themes"]:
            sortie[cle] = l["themes"]
        else:
            sortie.pop(cle, None)
    return sortie


def _tonalite(c: dict) -> float | None:
    try:
        return float(c.get("tonalite") or "")
    except ValueError:
        return None


def a_lire(mode: str = "reponses") -> list[dict]:
    """Les commentaires du groupe à ranger, du plus récent au plus ancien. mode « reponses » : ceux qui appellent
    une réponse (question, ou commentaire négatif sur Lisnard / Nouvelle Énergie, tonalité ≤ 8 sur 20), non
    insultants, d'au moins 5 mots ; mode « tout » : tous les non insultants d'au moins 5 mots."""
    from moderation import publication
    notes, ann, cib = d.lire_notes(), d.lire_annotations(), publication.cibles()
    deja = set(lire_classement()) | set(themes_lus_par_claude())
    reserves = {cle for f in LOTS.glob("lot_*.json") if not (j := lire_json(f) or {}).get("lu_le")
                for cle in j.get("commentaires", {}).values()}
    sortie = []
    for c in d.commentaires():
        if c["compte_source"] not in GROUPES or c["cle"] in deja or c["cle"] in reserves:
            continue
        cat = (ann.get(c["cle"]) or notes.get(c["cle"]) or {}).get("categorie")
        if cat == "insultant" or len(c["texte"].split()) < 5:
            continue
        t = _tonalite(c)
        if mode == "reponses" and not (cat == "question" or (cib.get(c["cle"]) == "L" and t is not None and t <= 8)):
            continue
        sortie.append(c)
    return sorted(sortie, key=lambda c: c.get("date") or "", reverse=True)


def texte_du_lot(lot: list[dict], themes: dict[str, dict]) -> str:
    entete = ["THÈMES (identifiant — nom : définition)"]
    cle_theme = lambda i: (0, int(i[1:])) if re.fullmatch(r"T\d+", i) else (1, i)  # noqa: E731
    for i in sorted(themes, key=cle_theme):
        entete.append(f"{i} — {themes[i]['nom']} : {themes[i]['definition']}")
    return "\n".join(entete) + "\n\nCOMMENTAIRES\n\n" + d.texte_du_lot(lot)


def tirer(n: int = TAILLE_LOT, mode: str = "reponses") -> int:
    """Prépare le lot suivant (les plus récents d'abord) et l'écrit dans lots_themes/lot_K.txt."""
    if mode not in ("reponses", "tout"):
        raise SystemExit("Mode inconnu (au choix : reponses, tout).")
    try:  # les thèmes ajoutés par les modérateurs depuis la dernière fois
        synchroniser(journal=lambda t: None)
    except (SystemExit, Exception) as e:  # noqa: BLE001 — sans réseau, on lit avec les thèmes du fichier
        print(f"(Synchronisation des thèmes impossible : {e} ; thèmes du fichier.)")
    themes = themes_actifs()
    lot = a_lire(mode)[:n]
    if not lot:
        print("Rien à tirer : tous les commentaires de ce mode sont déjà rangés.")
        return 0
    LOTS.mkdir(parents=True, exist_ok=True)
    k = 1 + max([int(m.group(1)) for f in LOTS.glob("lot_*.json") if (m := re.match(r"lot_(\d+)$", f.stem))] or [0])
    ecrire_json(LOTS / f"lot_{k}.json", {"mode": mode, "tire_le": maintenant(), "themes": sorted(themes),
                                         "commentaires": {str(j): c["cle"] for j, c in enumerate(lot, 1)}})
    (LOTS / f"lot_{k}.txt").write_text(texte_du_lot(lot, themes), encoding="utf-8")
    print(f"Lot {k} ({mode}, {len(lot)} commentaires) : {LOTS / f'lot_{k}.txt'}")
    print("Réponse attendue : une ligne par commentaire, « numéro: T31 T43 » (1 à 3 thèmes, le principal d'abord) "
          "ou « numéro: - » s'il n'aborde aucun thème. Puis « python -m moderation themes noter K fichier ».")
    return k


def lire_reponse(fichier: str, numeros: dict, themes: set[str]) -> dict[str, list[str]]:
    """Lit « 12: T31 T43 », « #12 | T5 », « 12: - » (tolère le gras Markdown et les virgules)."""
    choix: dict[str, list[str]] = {}
    for ligne in open(fichier, encoding="utf-8-sig").read().splitlines():
        m = re.match(r"\s*[*_`>-]*\s*#?(\d+)\s*[*_`]*\s*[:|]\s*(.*)$", ligne)
        if not m:
            continue
        j, reste = m.group(1), re.sub(r"[*_`]", " ", m.group(2)).strip()
        if j not in numeros:
            raise SystemExit(f"Numéro {j} absent du lot (ligne « {ligne.strip()} »)")
        if j in choix:
            raise SystemExit(f"Numéro {j} donné deux fois")
        ids = [] if reste.lower() in ("-", "", "aucun", "aucune", "rien", "none") else \
            [x.upper() if re.fullmatch(r"[tT]\d+", x) else x for x in re.split(r"[,;\s]+", reste) if x]
        for x in ids:
            if x not in themes:
                raise SystemExit(f"Thème inconnu « {x} » pour le numéro {j}")
        choix[j] = list(dict.fromkeys(ids))[:MAX_THEMES]
    manquants = [j for j in numeros if j not in choix]
    if manquants:
        raise SystemExit(f"{len(manquants)} numéros sans réponse : {', '.join(manquants[:30])}"
                         f"{'…' if len(manquants) > 30 else ''} (une ligne par commentaire, « - » s'il n'a aucun thème)")
    return choix


def noter(k: int, fichier: str, par: str = "") -> None:
    f_lot = LOTS / f"lot_{k}.json"
    lot = lire_json(f_lot)
    if not lot:
        raise SystemExit(f"Lot {k} introuvable dans {LOTS}")
    if lot.get("lu_le"):
        raise SystemExit(f"Le lot {k} est déjà noté (le {lot['lu_le']}).")
    themes = set(lot.get("themes") or themes_actifs())
    choix = lire_reponse(fichier, lot["commentaires"], themes)
    classement = lire_classement()
    le = maintenant()
    n = 0
    for j, cle in lot["commentaires"].items():
        if cle in classement:
            continue
        classement[cle] = {"cle": cle, "themes": " ".join(choix[j]), "lot": k, "par": par, "le": le}
        n += 1
    ecrire_csv(CLASSEMENT, classement.values(), CHAMPS_CLASSEMENT)
    ecrire_json(f_lot, {**lot, "par": par, "lu_le": le})
    avec = sum(bool(v) for v in choix.values())
    print(f"Lot {k} : {n} commentaires rangés ({avec} avec un thème, {len(choix) - avec} sans){' — lu par ' + par if par else ''}.")


def etat() -> dict:
    fichier = lire_fichier()
    classement = lire_classement()
    lots = {int(m.group(1)): lire_json(f) or {} for f in LOTS.glob("lot_*.json") if (m := re.match(r"lot_(\d+)$", f.stem))}
    return {"reponses": sum(l["actif"] for l in fichier["reponses"].values()),
            "themes_avec_reponses": len({l["theme"] for l in fichier["reponses"].values() if l["actif"]}),
            "themes": sum(l["actif"] for l in fichier["themes"].values()),
            "ranges": len(classement), "avec_theme": sum(bool(l["themes"]) for l in classement.values()),
            "par_claude_analyse": len([k for k in themes_lus_par_claude() if k.startswith("facebook:")]),
            "a_lire": len(a_lire()), "lots_en_attente": sorted(k for k, l in lots.items() if not l.get("lu_le")),
            "synchronise_le": (lire_json(ETAT, {}) or {}).get("le")}


def afficher_etat() -> None:
    e = etat()
    print(f"Réponses préparées : {e['reponses']} actives, sur {e['themes_avec_reponses']} des {e['themes']} thèmes "
          f"(dernière synchronisation : {e['synchronise_le'] or 'jamais'})")
    print(f"Commentaires rangés par thème pour les réponses : {e['ranges']} ({e['avec_theme']} avec un thème), "
          f"plus {e['par_claude_analyse']} déjà lus par Claude pour l'analyse")
    print(f"À ranger (appellent une réponse) : {e['a_lire']}"
          + (f" ; lots tirés pas encore notés : {', '.join(map(str, e['lots_en_attente']))}" if e["lots_en_attente"] else ""))
