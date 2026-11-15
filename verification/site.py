"""Site public de la vérification : une page par thème, écrite en dur (python -m verification site).

    python -m verification site            régénère les pages dans verification/site/
    python -m verification site apercu     régénère, puis ouvre les pages en local (http://localhost:8010)
    python -m verification site deployer   régénère, puis met en ligne sur Vercel (projet « verification-lisnard »)

Le site est entièrement statique : aucune base de données, aucun appel réseau. Toutes les données sont écrites dans
les pages HTML au moment de la génération, à partir des fichiers de themes/<thème>/ :

- position.md        → « Ce qu'il dit »
- affirmations.csv   → citation exacte, date, support, adresse, autres formulations
- analyse.md         → verdict de chaque affirmation et explication, conclusion du thème (« En bref »)
- calculs/METHODE.md, calculs/resultats.csv, sources.csv → « Le calcul » et « Les sources », repliés
- calculs/graphiques/*.png → copiés dans site/graphiques/
- conclusions.py     → conclusion en une phrase, type d'écart (l'étiquette affichée) et petit graphique
                       « annoncé / mesuré »

Pages : index.html (les thèmes) et une page par thème. affirmations.html et methode.html ont été retirées
(redirigées vers l'accueil par vercel.json).

Écrits à la main dans site/ : css/style.css, js/site.js, favicon.svg, vercel.json, robots.txt. Tout le reste
(*.html, graphiques/) est régénéré à chaque lancement : ne pas le modifier à la main.
"""
import csv
import functools
import html
import http.server
import re
import shutil
import webbrowser
from collections import Counter
from pathlib import Path

from .commun.chemins import RACINE, THEMES
from .conclusions import ACCROCHES, ECARTS, FIGURES, LECTURE
from .controles import ECHELLE

SITE = RACINE / "site"
GRAPHIQUES = SITE / "graphiques"
PROJET_VERCEL = "verification-lisnard"
TITRE_SITE = "Lisnard à l'épreuve des chiffres"

ESP = "\u00a0"   # espace insécable
FINE = "\u202f"  # espace fine insécable (milliers)

# Le site n'affiche pas le verdict d'analyse.md (« faux », « trompeur »…) mais une étiquette qui dit la nature de
# l'écart (« Superlatif », « Chiffre grossi »…), colorée selon sa famille : à quel point la phrase s'éloigne des
# chiffres. Famille → (nom, signe, définition). Le signe et le mot doublent la couleur : rien ne se lit à la couleur
# seule.
FAMILLES = {
    "exact": ("Exact", "✓", "Confirmé par les données publiques."),
    "proche": ("Proche", "≈", "Le bon ordre de grandeur ; un arrondi, une date ou un détail diffère."),
    "nuancer": ("À nuancer", "!", "Le chiffre existe, mais la phrase lui fait dire plus qu'il ne dit."),
    "inexact": ("Inexact", "✕", "Les données publiques donnent un chiffre nettement différent."),
    "inverifiable": ("Invérifiable", "?", "Aucune source publique accessible ne permet de trancher."),
    "promesse": ("Opinion ou promesse", "◆", "Un choix politique ou une mesure à venir : seuls les faits et les "
                                             "ordres de grandeur qui l'entourent sont vérifiés."),
}
# Verdict d'analyse.md → famille. Un superlatif, un arrondi ou un chiffre daté ne descend jamais sous « À nuancer » :
# la phrase reste vraie sur le fond.
FAMILLE_DU_VERDICT = {"exact": "exact", "plutôt exact": "proche", "trompeur": "nuancer", "faux": "inexact",
                      "invérifiable": "inverifiable", "opinion ou promesse": "promesse"}
ECARTS_DOUX = {"superlatif", "arrondi", "date"}


def etiquette(a: dict) -> tuple[str, str, str]:
    """(famille, étiquette affichée, définition) d'une affirmation."""
    famille = FAMILLE_DU_VERDICT[a["verdict"]]
    ecart = LECTURE[a["id"]].get("ecart")
    if famille == "promesse":
        return famille, "Promesse" if a["type"] == "mesure" else "Opinion", FAMILLES[famille][2]
    if famille == "inexact" and ecart in ECARTS_DOUX:
        famille = "nuancer"
    if not ecart:
        return famille, ("Plutôt exact" if a["verdict"] == "plutôt exact" else FAMILLES[famille][0]), \
            FAMILLES[famille][2]
    nom, definition = ECARTS[ecart]
    if ecart == "source" and famille == "inverifiable":
        nom = "Sans source"
    return famille, nom, definition
NIVEAUX = {
    "A": "Statistique publique (Insee, Eurostat, OCDE, ministères…)",
    "B": "Contrôle et évaluation (Cour des comptes, Sénat, Assemblée…)",
    "C": "Recherche",
    "D": "Think tank ou partie prenante : sert à retrouver l'origine d'un chiffre, jamais d'arbitre",
    "E": "Presse",
}
ROLES = {"dit": "Ce qu'il annonce", "fait": "Données publiques", "repere": "Point de comparaison"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
        "décembre"]
RX_ID = re.compile(r"^[A-Z]+-\d+$")
RX_RENVOI = re.compile(r"\s*\[(M\d+)\]")


class Erreur(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------------
# Texte : typographie française, Markdown réduit à ce qu'emploient les fichiers des thèmes
# ---------------------------------------------------------------------------------------------------------------

def typo(s: str) -> str:
    """Espaces insécables : guillemets, ponctuation double, unités, milliers."""
    s = s.replace("« ", "«" + ESP).replace(" »", ESP + "»")
    s = re.sub(r" ([;:!?%€$])", ESP + r"\1", s)
    s = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", FINE, s)
    s = re.sub(r"(?<=\d) (?=(?:Md|M€|Mds|milliards?|millions?|points?|fois|ans?\b|GWh|MWh|TWh|kWh|GW\b|Tcf|habitants))",
               ESP, s)
    return s


def echapper(s: str) -> str:
    return html.escape(s, quote=True)


class Rendu:
    """Markdown → HTML. `etiquettes` : {id d'affirmation: (famille, étiquette, définition)}, pour transformer
    `DETTE-01` en renvoi coloré vers l'affirmation."""

    def __init__(self, etiquettes: dict | None = None, sans_renvois: bool = False, numeros: dict | None = None):
        self.etiquettes = etiquettes or {}
        self.numeros = numeros or {}  # {id: numéro de la carte de l'affirmation dans la page}
        self.sans_renvois = sans_renvois  # retire les [M3] (analyse.md) : le calcul est montré à part

    def renvoi(self, c: str) -> str:
        famille, nom, _ = self.etiquettes[c]
        n = self.numeros.get(c)
        numero = f"<b>{n}</b>" if n else ""
        titre = f"Affirmation {n} : {nom}" if n else nom
        return (f'<a class="renvoi f-{famille}" href="#{c}" title="{echapper(titre)}">'
                f'<i aria-hidden="true">{FAMILLES[famille][1]}</i>{numero}{echapper(nom)}</a>')

    def code(self, c: str) -> str:
        if RX_ID.match(c) and c in self.etiquettes:
            return self.renvoi(c)
        return f"<code>{echapper(c)}</code>"

    def ligne(self, t: str) -> str:
        """Texte courant : gras, code, renvois."""
        codes: list[str] = []

        def garder(m):
            codes.append(self.code(m.group(1)))
            return f"\x00{len(codes) - 1}\x00"

        t = re.sub(r"`([^`]+)`", garder, t)
        if self.sans_renvois:
            t = RX_RENVOI.sub("", t)
        t = echapper(typo(t))
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t).strip()

    def liste(self, lignes: list[str]) -> str:
        """Liste à puces ou numérotée, imbriquée selon le retrait. Les lignes sans puce prolongent l'élément."""
        elements: list[list] = []  # [retrait, numérotée, texte]
        for l in lignes:
            m = re.match(r"^(\s*)([-*]|\d+\.) (.*)$", l)
            if m:
                texte = re.sub(r"^\[[ xX]\] ", "", m.group(3))
                elements.append([len(m.group(1)), m.group(2)[0].isdigit(), texte])
            elif elements:
                elements[-1][2] += " " + l.strip()

        def construire(i: int, retrait: int) -> tuple[str, int]:
            balise = "ol" if elements[i][1] else "ul"
            out = [f"<{balise}>"]
            while i < len(elements) and elements[i][0] >= retrait:
                if elements[i][0] > retrait:  # sous-liste de l'élément précédent
                    sous, i = construire(i, elements[i][0])
                    out[-1] = out[-1].removesuffix("</li>") + sous + "</li>"
                    continue
                out.append(f"<li>{self.ligne(elements[i][2])}</li>")
                i += 1
            return "".join(out) + f"</{balise}>", i

        return construire(0, elements[0][0])[0] if elements else ""

    def tableau(self, lignes: list[str]) -> str:
        rangs = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lignes]
        rangs = [r for r in rangs if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
        tete, corps = rangs[0], rangs[1:]
        out = ['<div class="defile"><table><thead><tr>']
        out += [f"<th>{self.ligne(c)}</th>" for c in tete]
        out.append("</tr></thead><tbody>")
        for r in corps:
            out.append("<tr>" + "".join(f"<td>{self.ligne(c)}</td>" for c in r) + "</tr>")
        return "".join(out) + "</tbody></table></div>"

    def cartes(self, lignes: list[str]) -> str:
        """Une liste de premier niveau en grille de cartes : « **Titre** : texte » donne une carte titrée ; les
        renvois `DETTE-01` sont sortis du texte et placés en bas de la carte."""
        puce = re.compile(r"^(\s*)([-*]|\d+\.) ")
        retrait = len(puce.match(lignes[0]).group(1))
        groupes: list[list[str]] = []
        for l in lignes:
            m = puce.match(l)
            if m and len(m.group(1)) == retrait:
                groupes.append([l[m.end():]])
            elif groupes:
                groupes[-1].append(l)

        def nettoyer(s: str) -> str:
            s = re.sub(r"\s*\((?:\s*`[A-Z]+-\d+`\s*,?)+\)|`[A-Z]+-\d+`", "", s)
            return re.sub(r"\s+([.,)])", r"\1", s).rstrip()

        out = ['<div class="cartes-dit">']
        for g in groupes:
            k = next((n for n, x in enumerate(g) if n and puce.match(x)), len(g))
            texte = nettoyer(" ".join(x.strip() for x in g[:k]))
            sous = [nettoyer(x) for x in g[k:]]
            ids = [i for i in dict.fromkeys(re.findall(r"`([A-Z]+-\d+)`", " ".join(g))) if i in self.etiquettes]
            m = re.match(r"^\*\*(.+?)\*\*\s*:?\s*(.*)$", texte)
            titre, corps = (m.group(1), m.group(2)) if m else ("", texte)
            if titre:
                corps = re.sub(r"^[,:;]\s*", "", corps)
                corps = corps[:1].upper() + corps[1:]
            out.append('<div class="carte-dit">' + (f"<h4>{self.ligne(titre)}</h4>" if titre else "")
                       + (f"<p>{self.ligne(corps)}</p>" if corps else "") + (self.liste(sous) if sous else "")
                       + (f'<p class="carte-renvois">{"".join(self.renvoi(i) for i in ids)}</p>' if ids else "")
                       + "</div>")
        return "".join(out) + "</div>"

    def blocs(self, md: str, niveau_titre: int = 4, cartes: bool = False) -> str:
        lignes, out, i = md.split("\n"), [], 0
        est_liste = lambda l: re.match(r"^\s*([-*]|\d+\.) ", l)
        while i < len(lignes):
            l = lignes[i]
            if not l.strip() or l.strip() == "---":
                i += 1
            elif l.startswith("```"):
                j = i + 1
                while j < len(lignes) and not lignes[j].startswith("```"):
                    j += 1
                corps = "\n".join(lignes[i + 1:j])
                corps = formule(corps) if l.strip() == "```latex" else corps
                out.append(f'<p class="formule">{echapper(typo(corps))}</p>')
                i = j + 1
            elif l.startswith("#"):
                out.append(f"<h{niveau_titre}>{self.ligne(l.lstrip('#').strip())}</h{niveau_titre}>")
                i += 1
            elif l.startswith("|"):
                j = i
                while j < len(lignes) and lignes[j].startswith("|"):
                    j += 1
                out.append(self.tableau(lignes[i:j]))
                i = j
            elif est_liste(l):
                j = i
                while j < len(lignes) and lignes[j].strip() and (est_liste(lignes[j]) or lignes[j].startswith(" ")):
                    j += 1
                out.append(self.cartes(lignes[i:j]) if cartes else self.liste(lignes[i:j]))
                i = j
            elif l.startswith("!["):
                i += 1  # les graphiques sont placés par FIGURES (conclusions.py)
            else:
                j = i
                while (j < len(lignes) and lignes[j].strip() and not est_liste(lignes[j])
                       and not lignes[j].startswith(("|", "#", "```", "!["))):
                    j += 1
                out.append(f"<p>{self.ligne(' '.join(x.strip() for x in lignes[i:j]))}</p>")
                i = j
        return "\n".join(out)


def formule(tex: str) -> str:
    """Les quelques formules LaTeX de METHODE.md, en texte lisible (fractions sur une ligne)."""
    t = tex.strip()
    for _ in range(4):
        t = re.sub(r"\\text\{([^{}]*)\}", r"\1", t)
        t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1) / (\2)", t)
        t = re.sub(r"[_^]\{([^{}]*)\}", lambda m: (" " if m.group(0)[0] == "_" else "^") + m.group(1), t)
    for a, b in [(r"\times", "×"), (r"\left", ""), (r"\right", ""), (r"\Delta", "Δ"), (r"\to", "→"), (r"\quad", "  "),
                 (r"\,", FINE), (r"\_", "_"), ("{,}", ","), ("_", " ")]:
        t = t.replace(a, b)
    return re.sub(r" {2,}", "  ", t).strip()


def date_fr(d: str) -> str:
    """2024-08-30 → 30 août 2024 ; 2026-04 → avril 2026 ; vide ou « nan » → chaîne vide."""
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", (d or "").strip())
    if not m:
        return ""
    jour = "" if not m.group(3) else ("1er " if m.group(3) == "01" else f"{int(m.group(3))} ")
    return f"{jour}{MOIS[int(m.group(2)) - 1]} {m.group(1)}"


def nombre_fr(v: str) -> str:
    """58.4 → 58,4 ; 3482000 → 3 482 000 ; -103 → −103. Laisse tel quel ce qui n'est pas un nombre."""
    v = v.strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", v):
        return v
    ent, _, dec = v.lstrip("-").partition(".")
    if len(ent) > 3:
        ent = re.sub(r"(?<=\d)(?=(\d{3})+$)", FINE, ent)
    return ("−" if v.startswith("-") else "") + ent + ("," + dec if dec else "")


def valeur_barre(v: str) -> float:
    return float(v.replace(" ", "").replace(FINE, "").replace(ESP, "").replace(",", "."))


def lire_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------------------------------------------
# Lecture d'un thème
# ---------------------------------------------------------------------------------------------------------------

def categorie(verdict_brut: str) -> str:
    brut = verdict_brut.strip().lower()
    for e in sorted(ECHELLE, key=len, reverse=True):
        if brut.startswith(e):
            return e
    raise Erreur(f"verdict hors échelle : « {verdict_brut} »")


def sections(md: str) -> tuple[str, list[tuple[str, str]]]:
    """Texte avant le premier « ## », puis [(titre, corps)] pour chaque « ## »."""
    morceaux = re.split(r"(?m)^## (.+)$", md)
    return morceaux[0], [(morceaux[i].strip(), morceaux[i + 1].strip("\n")) for i in range(1, len(morceaux), 2)]


def lire_analyse(d: Path) -> dict:
    avant, secs = sections((d / "analyse.md").read_text(encoding="utf-8"))
    m = re.search(r"\*\*En bref\.\*\*\s*(.*?)(?=^\| Verdict|\Z)", avant, re.S | re.M)
    if not m:
        raise Erreur(f"{d.name} : pas de « En bref » dans analyse.md")
    out = {"bref": m.group(1).strip(), "affirmations": {}, "reste": ""}
    for titre, corps in secs:
        mt = re.match(r"([A-Z]+-\d+) — (.*)$", titre, re.S)
        if not mt:
            if titre.startswith("Ce qui reste"):
                out["reste"] = corps
            continue
        premier, _, suite = corps.partition("\n\n")
        premier = " ".join(x.strip() for x in premier.split("\n"))
        mv = re.match(r"\*\*Verdict : (.+?)\*\*\s*(.*)$", premier, re.S)
        if not mv:
            raise Erreur(f"{d.name} : {mt.group(1)} sans ligne « Verdict » dans analyse.md")
        phrase, reste = mv.group(1).strip().rstrip("."), mv.group(2)
        mc = re.search(r"Confiance : (.+?)\.(?=\s|$)", reste)
        confiance = mc.group(1).strip() if mc else ""
        note = (reste[:mc.start()] + reste[mc.end():]) if mc else reste
        out["affirmations"][mt.group(1)] = {
            "titre": mt.group(2).strip(), "verdict": categorie(phrase), "phrase": phrase[0].upper() + phrase[1:],
            "confiance": confiance, "note": RX_RENVOI.sub("", note).strip(), "corps": suite,
            "renvois": RX_RENVOI.findall(corps), "brut": titre + "\n" + corps}
    return out


def lire_methode(d: Path) -> dict:
    avant, secs = sections((d / "calculs" / "METHODE.md").read_text(encoding="utf-8"))
    avant = re.sub(r"(?m)^# .*$", "", avant)
    avant = "\n\n".join(p for p in re.split(r"\n\s*\n", avant)
                        if p.strip() and p.strip() != "---" and not p.strip().startswith("Tous les résultats"))
    out = {"conventions": avant.strip(), "sections": {}, "autres": []}
    for titre, corps in secs:
        m = re.match(r"(M\d+) — (.*)$", titre)
        if m:
            out["sections"][m.group(1)] = (re.sub(r"\s*\(`[^)]*`\)", "", m.group(2)).strip(), corps)
        else:
            out["autres"].append((titre, corps))
    return out


def lire_theme(d: Path) -> dict:
    numero = d.name.split("_")[0]
    lignes = lire_csv(d / "affirmations.csv")
    analyse, methode = lire_analyse(d), lire_methode(d)
    resultats, sources = lire_csv(d / "calculs" / "resultats.csv"), lire_csv(d / "sources.csv")
    _, position = sections((d / "position.md").read_text(encoding="utf-8"))
    affirmations = []
    for l in lignes:
        a = analyse["affirmations"].get(l["id"])
        if not a:
            raise Erreur(f"{d.name} : {l['id']} absent de analyse.md")
        res = [r for r in resultats if r["affirmation"] == l["id"]]
        renvois = list(dict.fromkeys(a["renvois"] + [r["methode"] for r in res if r["methode"]]))
        affirmations.append({
            **a, "id": l["id"], "type": l["type"], "citation": l["citation"].strip(), "date": date_fr(l["date"]),
            "support": l["support"].strip(), "url": l["url_source"].strip(),
            "versions": [v.strip() for v in re.split(r" ; (?=«)", l["autres_versions"]) if v.strip()],
            "resultats": res, "methodes": [(m, *methode["sections"][m]) for m in renvois if m in methode["sections"]],
            "sources": [s for s in sources if l["id"] in s["affirmations"].split()]})
    return {"numero": numero, "dossier": d, "page": d.name.replace("_", "-") + ".html", "nom": lignes[0]["theme"],
            "affirmations": affirmations, "position": position, "bref": analyse["bref"], "reste": analyse["reste"],
            "methode": methode, "sources": sources,
            "telecharge": max((s["date_telechargement"] for s in sources if s["date_telechargement"]), default="")}


def controler(themes: list[dict]) -> None:
    """Arrête la génération si conclusions.py ne correspond plus aux fichiers des thèmes."""
    err = []
    connus = {a["id"]: (t, a) for t in themes for a in t["affirmations"]}
    err += [f"conclusions.py : pas d'entrée pour {i}" for i in connus if i not in LECTURE]
    err += [f"conclusions.py : {i} n'existe dans aucun thème" for i in LECTURE if i not in connus]
    err += [f"conclusions.py : pas d'accroche pour le thème {t['numero']}" for t in themes
            if t["numero"] not in ACCROCHES]
    for i, lec in LECTURE.items():
        if i not in connus:
            continue
        t, a = connus[i]
        if lec.get("ecart") and lec["ecart"] not in ECARTS:
            err.append(f"conclusions.py : {i}, type d'écart inconnu « {lec['ecart']} »")
        if a["verdict"] in ("trompeur", "faux", "invérifiable") and not lec.get("ecart"):
            err.append(f"conclusions.py : {i} ({a['verdict']}) n'a pas de type d'écart, qui sert d'étiquette")
        texte = re.sub(r"\s+", " ", a["brut"].replace(ESP, " ").replace(FINE, " "))
        for nom, valeur, role in (lec.get("barres") or {}).get("lignes", ()):
            if role not in ROLES:
                err.append(f"conclusions.py : {i}, rôle inconnu « {role} »")
            elif role != "dit" and not re.search(rf"(?<![\d,.]){re.escape(valeur)}(?!\d)(?!,\d)", texte):
                err.append(f"conclusions.py : {i}, la valeur {valeur} (« {nom} ») ne figure pas dans analyse.md")
    for i, (fichier, _) in FIGURES.items():
        if i not in connus:
            err.append(f"conclusions.py : FIGURES cite {i}, qui n'existe pas")
        elif not (connus[i][0]["dossier"] / "calculs" / "graphiques" / fichier).exists():
            err.append(f"conclusions.py : graphique introuvable pour {i} ({fichier})")
    if err:
        raise Erreur("\n".join(err))


# ---------------------------------------------------------------------------------------------------------------
# Morceaux de page
# ---------------------------------------------------------------------------------------------------------------

def pastille(famille: str, nom: str, definition: str = "") -> str:
    signe = FAMILLES[famille][1]
    titre = f' title="{echapper(typo(definition))}"' if definition else ""
    return f'<span class="pastille f-{famille}"{titre}><i aria-hidden="true">{signe}</i>{echapper(nom)}</span>'


def bande_familles(compte: Counter, grande: bool = False) -> str:
    """Barre segmentée (un tout, découpé en parts) et sa légende chiffrée, par famille d'étiquettes."""
    total = sum(compte.values())
    parts, legende = [], []
    for f, (nom, signe, definition) in FAMILLES.items():
        n = compte.get(f, 0)
        if not n:
            continue
        pct = round(100 * n / total)
        dans = f"<b>{n}</b>" if grande and n / total >= 0.05 else ""
        parts.append(f'<span class="f-{f}" style="flex-grow:{n}" title="{nom} : {n} sur {total} ({pct}{ESP}%)">'
                     f"{dans}</span>")
        legende.append(f'<li title="{echapper(typo(definition))}"><span class="cle f-{f}"><i aria-hidden="true">'
                       f"{signe}</i></span>{nom} <b>{n}</b></li>")
    resume = ", ".join(f"{compte[f]} {FAMILLES[f][0].lower()}" for f in FAMILLES if compte.get(f))
    return (f'<div class="verdicts{" grande" if grande else ""}"><div class="bande" role="img" '
            f'aria-label="{echapper(resume)}">{"".join(parts)}</div><ul class="cles">{"".join(legende)}</ul></div>')


def barres(spec: dict) -> str:
    """Petit graphique horizontal : ce qu'il annonce (orange) face aux données (bleu) et aux repères (gris)."""
    unite = spec["unite"]
    court = unite if len(unite) <= 6 else unite.split()[0]
    titre = spec["titre"] + (f" ({unite})" if unite and unite != court else "")
    maxi = max(valeur_barre(v) for _, v, _ in spec["lignes"])
    roles = list(dict.fromkeys(r for _, _, r in spec["lignes"]))
    out = [f'<figure class="barres"><figcaption>{echapper(typo(titre))}</figcaption>']
    if len(roles) > 1:
        out.append('<ul class="cles">' + "".join(f'<li><span class="cle b-{r}"></span>{ROLES[r]}</li>'
                                                 for r in ROLES if r in roles) + "</ul>")
    out.append('<div class="lignes">')
    for nom, v, role in spec["lignes"]:
        affiche = typo(f"{v} {court}".strip())
        part = 0 if maxi <= 0 else max(valeur_barre(v) / maxi, 0.004)
        out.append(f'<div class="ligne" title="{echapper(typo(nom))} : {echapper(affiche)} ({ROLES[role].lower()})">'
                   f'<span class="nom">{echapper(typo(nom))}</span>'
                   f'<span class="piste"><span class="barre b-{role}" style="--p:{part:.4f}"></span>'
                   f'<span class="val">{echapper(affiche)}</span></span></div>')
    return "".join(out) + "</div></figure>"


def image(theme: dict, fichier: str, legende: str) -> str:
    nom = f"{theme['numero']}_{fichier}"
    return (f'<figure class="image"><img src="graphiques/{nom}" alt="{echapper(legende)}" decoding="async" '
            f'width="1350" height="720"><figcaption>{echapper(typo(legende))}</figcaption></figure>')


def tableau_resultats(res: list[dict]) -> str:
    dits = list(dict.fromkeys(r["chiffre_lisnard"].strip() for r in res if r["chiffre_lisnard"].strip()))
    out = []
    if dits:
        out.append(f'<p class="dit"><b>Ce qu\'il dit :</b> {echapper(typo(" · ".join(dits)))}</p>')
    out.append('<div class="defile"><table class="resultats"><thead><tr><th>Mesure</th><th>Cas</th>'
               '<th class="num">Valeur</th><th>Remarque</th></tr></thead><tbody>')
    for r in res:
        unite = r["unite"].strip()
        valeur = nombre_fr(r["valeur"]) + (ESP + unite if unite else "")
        out.append(f'<tr><td>{echapper(typo(r["grandeur"]))}</td><td>{echapper(typo(r["variante"]))}</td>'
                   f'<td class="num">{echapper(valeur)}</td><td>{echapper(typo(r["note"]))}</td></tr>')
    return "".join(out) + "</tbody></table></div>"


def liste_sources(sources: list[dict]) -> str:
    out = ['<ul class="sources">']
    for s in sorted(sources, key=lambda s: (s["niveau"], s["organisme"])):
        n = s["niveau"].strip()[:1] or "?"
        titre = echapper(typo(s["titre"]))
        lien = f'<a href="{echapper(s["url"])}" rel="noopener noreferrer">{titre}</a>' if s["url"] else titre
        jour = "/".join(reversed(s["date_telechargement"].split("-")))
        out.append(f'<li><span class="niveau n-{n}" title="Niveau {n} : {echapper(NIVEAUX.get(n, ""))}">{n}</span>'
                   f'<span><b>{echapper(typo(s["organisme"]))}</b> · {lien}'
                   f'<small> · relevé le {jour} · <code>{echapper(s["id_source"])}</code></small></span></li>')
    return "".join(out) + "</ul>"


def legende_niveaux(niveaux: Counter) -> str:
    return ('<p class="pale niveaux-legende">' + " · ".join(
        f'<span class="niveau n-{k}">{k}</span> {echapper(typo(v.split(" : ")[0]))}'
        for k, v in NIVEAUX.items() if niveaux.get(k)) + "</p>")


def carte_affirmation(theme: dict, a: dict, rendu: Rendu, numero: int) -> str:
    lec = LECTURE[a["id"]]
    famille, nom, definition = etiquette(a)
    out = [f'<details class="aff f-{famille}" id="{a["id"]}" data-famille="{famille}"><summary>'
           f'<span class="aff-numero">{numero}</span>{pastille(famille, nom, definition)}'
           f'<span class="aff-tete"><span class="aff-titre">{rendu.ligne(a["titre"])}</span>'
           f'<span class="aff-resume">{rendu.ligne(lec["resume"])}</span></span>'
           f'<span class="aff-chevron" aria-hidden="true"></span></summary><div class="aff-corps">']

    ou = ", ".join(x for x in (a["support"], a["date"]) if x)
    lien = (f' · <a href="{echapper(a["url"])}" rel="noopener noreferrer">voir la source</a>' if a["url"] else "")
    nature = "La mesure, mot pour mot" if a["type"] == "mesure" else "La phrase exacte"
    out.append(f'<figure class="citation"><figcaption>{nature}</figcaption><blockquote>«{ESP}'
               f'{echapper(typo(a["citation"]))}{ESP}»</blockquote><p class="ou">David Lisnard, {echapper(typo(ou))}'
               f'{lien}</p></figure>')

    details = [f"<span>{FAMILLES[famille][0]}</span>"]
    if a["confiance"]:
        details.append(f'<span>Confiance{ESP}: {echapper(typo(a["confiance"]))}</span>')
    out.append(f'<div class="verdict f-{famille}"><p class="phrase"><i aria-hidden="true">{FAMILLES[famille][1]}</i>'
               f'{echapper(nom)}</p><p class="definition">{echapper(typo(definition))}</p>'
               f'<p class="precisions">{" ".join(details)}</p></div>')

    if lec.get("barres"):
        out.append(barres(lec["barres"]))
    if a["corps"].strip():
        out.append(f'<div class="pourquoi"><h4>Pourquoi</h4>{rendu.blocs(a["corps"])}</div>')
    if a["id"] in FIGURES:
        out.append(image(theme, *FIGURES[a["id"]]))

    if a["versions"]:
        n = len(a["versions"])
        out.append(f'<details class="annexe"><summary>Ses autres formulations ({n})</summary><ul>'
                   + "".join(f"<li>{echapper(typo(v))}</li>" for v in a["versions"]) + "</ul></details>")
    if a["methodes"] or a["resultats"]:
        calcul = "".join(f'<h5>{echapper(typo(titre))}</h5>{Rendu().blocs(corps, 5)}' for _, titre, corps in a["methodes"])
        if a["resultats"]:
            calcul += "<h5>Résultats du calcul</h5>" + tableau_resultats(a["resultats"])
        out.append(f'<details class="annexe"><summary>Le calcul</summary>{calcul}</details>')
    if a["sources"]:
        out.append(f'<details class="annexe"><summary>Les sources ({len(a["sources"])})</summary>'
                   f'{liste_sources(a["sources"])}</details>')
    return "".join(out) + "</div></details>"


# ---------------------------------------------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------------------------------------------

def page(titre: str, description: str, corps: str) -> str:
    complet = titre if titre == TITRE_SITE else f"{titre} · {TITRE_SITE}"
    return f"""<!doctype html>
<!-- Page générée par « python -m verification site » : ne pas modifier à la main. -->
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{echapper(complet)}</title>
<meta name="description" content="{echapper(description)}">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="entete"><div class="large">
<a class="marque" href="index.html"><svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="currentColor"/><path d="M8 17l5 5 11-12" fill="none" stroke="var(--fond)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg><span>{TITRE_SITE}</span></a>
</div></header>
<main id="contenu">
{corps}
</main>
<footer class="pied"><div class="large">
<span>Vérification des affirmations de David Lisnard et de Nouvelle Énergie à partir de données publiques.</span>
<span>Données figées au {DATE_DONNEES}</span>
</div></footer>
<script src="js/site.js" defer></script>
</body>
</html>
"""


def filtres(compte: Counter, cible: str, extra: str = "") -> str:
    boutons = "".join(
        f'<button type="button" class="filtre f-{f}" data-famille="{f}" aria-pressed="false" '
        f'title="{echapper(typo(definition))}"><i aria-hidden="true">{signe}</i>{nom} <b>{compte[f]}</b></button>'
        for f, (nom, signe, definition) in FAMILLES.items() if compte.get(f))
    return (f'<div class="filtres" data-filtres="{cible}"><span class="filtres-titre">Filtrer</span>{boutons}{extra}'
            f'<span class="filtres-compte" aria-live="polite"></span></div>')


SECTIONS_RETIREES = ("Évolution", "Sources")  # parties de position.md non montrées sur le site


def ce_qu_il_dit(t: dict, rendu: Rendu) -> str:
    """position.md, partie par partie : les listes deviennent des cartes, les tableaux restent des tableaux."""
    out = []
    for titre, corps in t["position"]:
        if titre.startswith(SECTIONS_RETIREES):
            continue
        corps = corps.replace("| Identifiant |", "| Vérifié plus bas |")
        out.append(f'<div class="bloc-dit"><h3>{echapper(typo(titre))}</h3>{rendu.blocs(corps, cartes=True)}</div>')
    return "".join(out)


def page_theme(t: dict, themes: list[dict]) -> str:
    aff = t["affirmations"]
    etiquettes = {a["id"]: etiquette(a) for a in aff}
    numeros = {a["id"]: n for n, a in enumerate(aff, 1)}
    rendu = Rendu(etiquettes, numeros=numeros)
    analyse = Rendu(etiquettes, sans_renvois=True, numeros=numeros)
    compte = Counter(e[0] for e in etiquettes.values())
    niveaux = Counter(s["niveau"].strip()[:1] for s in t["sources"])
    i = themes.index(t)

    premiere = next((a["id"] for a in aff if a["id"] in FIGURES), None)
    annexes = []
    conventions = t["methode"]["conventions"]
    autres = "".join(f"<h4>{Rendu().ligne(x)}</h4>{Rendu().blocs(c)}" for x, c in t["methode"]["autres"])
    if conventions or autres:
        annexes.append(f'<details class="volet"><summary>Conventions de calcul</summary>{Rendu().blocs(conventions)}'
                       f"{autres}</details>")
    annexes.append(f'<details class="volet"><summary>Toutes les sources du thème ({len(t["sources"])})</summary>'
                   f'{legende_niveaux(niveaux)}{liste_sources(t["sources"])}</details>')

    avant = f'<a href="{themes[i - 1]["page"]}">← {echapper(themes[i - 1]["nom"])}</a>' if i else "<span></span>"
    apres = (f'<a href="{themes[i + 1]["page"]}">{echapper(themes[i + 1]["nom"])} →</a>'
             if i + 1 < len(themes) else "<span></span>")
    n_mes = sum(a["type"] == "mesure" for a in aff)
    decompte = (f"{len(aff) - n_mes} affirmation{'s' if len(aff) - n_mes > 1 else ''}"
                + (f" et {n_mes} mesure{'s' if n_mes > 1 else ''}" if n_mes else "")
                + f" · {len(t['sources'])} source{'s' if len(t['sources']) > 1 else ''}")
    corps = f"""<div class="large">
<section class="titre-page">
<p class="surtitre"><a href="index.html">← Tous les thèmes</a> · {int(t["numero"])} sur {len(themes)}</p>
<h1>{echapper(typo(t["nom"]))}</h1>
<p class="accroche">{echapper(typo(ACCROCHES[t["numero"]]))}</p>
{bande_familles(compte, grande=True)}
<p class="decompte">{decompte}</p>
</section>

<section class="partie" id="dit">
<h2><span>1</span>Ce qu'il dit</h2>
<p class="chapo">Ses mots, avant toute vérification. Les étiquettes numérotées renvoient à l'affirmation vérifiée plus bas, sous le même numéro.</p>
{ce_qu_il_dit(t, rendu)}
</section>

<section class="partie" id="chiffres">
<h2><span>2</span>Ce que disent les chiffres</h2>
<p class="chapo">Une carte par affirmation : l'étiquette dit en quoi la phrase s'écarte des chiffres, la ligne en dessous dit pourquoi. Ouvrir une carte pour lire la citation exacte, l'explication, le calcul et les sources.</p>
{filtres(compte, "#liste", '<button type="button" class="tout" data-tout="#liste">Tout ouvrir</button>')}
<div class="liste" id="liste">
{"".join(carte_affirmation(t, a, analyse, n) for n, a in enumerate(aff, 1))}
</div>
</section>

<section class="partie" id="conclusion">
<h2><span>3</span>Conclusion</h2>
<div class="conclusion">
<div class="prose">{analyse.blocs(t["bref"])}</div>
{image(t, *FIGURES[premiere]) if premiere else ""}
</div>
{"".join(annexes)}
</section>

<nav class="voisins" aria-label="Autres thèmes">{avant}{apres}</nav>
</div>"""
    return page(t["nom"], ACCROCHES[t["numero"]], corps)


def page_accueil(themes: list[dict]) -> str:
    tous = [a for t in themes for a in t["affirmations"]]
    compte = Counter(etiquette(a)[0] for a in tous)
    n_sources = sum(len(t["sources"]) for t in themes)
    cartes = []
    for t in themes:
        c = Counter(etiquette(a)[0] for a in t["affirmations"])
        cartes.append(f'<a class="carte" href="{t["page"]}"><span class="numero">{int(t["numero"])}</span>'
                      f'<h3>{echapper(typo(t["nom"]))}</h3><p>{echapper(typo(ACCROCHES[t["numero"]]))}</p>'
                      f'{bande_familles(c).replace("<ul", "<ul hidden", 1)}'
                      f'<span class="carte-pied">{len(t["affirmations"])} affirmations vérifiées</span></a>')
    phrases = [f"<b>{compte[f]}</b> {FAMILLES[f][0].lower()}{'s' if compte[f] > 1 and f in ('exact', 'proche', 'inexact') else ''}"
               for f in FAMILLES if compte.get(f) and f not in ("inverifiable", "promesse")]
    bilan = (", ".join(phrases[:-1]) + " et " + phrases[-1] if len(phrases) > 1 else phrases[0])
    bilan += (f" ; <b>{compte['inverifiable']}</b> ne peuvent pas être vérifiées et <b>{compte['promesse']}</b> sont des "
              "opinions ou des promesses.")
    corps = f"""<div class="large">
<section class="une">
<p class="surtitre">Vérification factuelle · {len(themes)} thèmes</p>
<h1>Ce que dit David Lisnard, à l'épreuve des chiffres</h1>
<p class="accroche">{len(tous)} affirmations et mesures de David Lisnard et de Nouvelle Énergie, confrontées une à une aux données publiques : {n_sources} sources téléchargées, des calculs refaits, une conclusion expliquée.</p>
{bande_familles(compte, grande=True)}
<p class="bilan">{bilan}</p>
</section>

<section class="partie">
<h2>Les {len(themes)} thèmes</h2>
<p class="chapo">Pour chaque thème : ce qu'il dit, ce que disent les chiffres, et la conclusion.</p>
<div class="cartes">{"".join(cartes)}</div>
</section>
</div>"""
    return page(TITRE_SITE, f"{len(tous)} affirmations de David Lisnard et de Nouvelle Énergie vérifiées avec des "
                            "données publiques, thème par thème.", corps)


# ---------------------------------------------------------------------------------------------------------------
# Génération, aperçu, mise en ligne
# ---------------------------------------------------------------------------------------------------------------

DATE_DONNEES = ""


def generer(journal=print) -> list[Path]:
    """Réécrit toutes les pages et recopie les graphiques. Rend la liste des fichiers écrits."""
    global DATE_DONNEES
    themes = [lire_theme(d) for d in sorted(THEMES.iterdir()) if d.is_dir() and (d / "analyse.md").exists()]
    if not themes:
        raise Erreur("aucun thème avec analyse.md")
    controler(themes)
    DATE_DONNEES = date_fr(max(t["telecharge"] for t in themes))

    for ancien in SITE.glob("*.html"):
        ancien.unlink()
    shutil.rmtree(GRAPHIQUES, ignore_errors=True)
    GRAPHIQUES.mkdir(parents=True)
    ecrits = []

    def ecrire(nom: str, contenu: str) -> None:
        (SITE / nom).write_text(contenu, encoding="utf-8", newline="\n")
        ecrits.append(SITE / nom)

    par_id = {a["id"]: t for t in themes for a in t["affirmations"]}
    for i, (fichier, _) in FIGURES.items():
        t = par_id[i]
        cible = GRAPHIQUES / f"{t['numero']}_{fichier}"
        shutil.copyfile(t["dossier"] / "calculs" / "graphiques" / fichier, cible)
        ecrits.append(cible)
    for t in themes:
        ecrire(t["page"], page_theme(t, themes))
    ecrire("index.html", page_accueil(themes))
    n = sum(len(t["affirmations"]) for t in themes)
    journal(f"   {len(themes)} thèmes, {n} affirmations, {len(FIGURES)} graphiques → {SITE.relative_to(RACINE.parent)}"
            f" ({len(ecrits)} fichiers)")
    return ecrits


def apercu(port: int = 8010) -> None:
    generer()
    gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), gestion) as serveur:
        print(f"Aperçu sur http://localhost:{port} (Ctrl+C pour arrêter)")
        webbrowser.open(f"http://localhost:{port}")
        serveur.serve_forever()


def deployer(journal=print) -> str:
    """Régénère puis met en ligne sur Vercel. Le jeton est celui du site public (config/web.json, vercel_jeton)."""
    from web import acces
    from web.vercel import Vercel
    generer(journal)
    a = acces.exiger("vercel_jeton")
    url = Vercel(a["vercel_jeton"]).deployer(SITE, journal, projet=PROJET_VERCEL)
    acces.sauver(verification_url=url)
    journal(f"   en ligne : {url}")
    return url


def main(args: list[str]) -> None:
    action = args[0] if args else "generer"
    try:
        if action == "generer":
            generer()
        elif action == "apercu":
            apercu(int(args[1]) if len(args) > 1 else 8010)
        elif action == "deployer":
            deployer()
        else:
            raise SystemExit(f"Action inconnue : {action}\n{__doc__}")
    except Erreur as e:
        raise SystemExit(f"Génération arrêtée :\n{e}")
