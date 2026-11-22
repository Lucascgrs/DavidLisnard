// Réponses préparées : panneau latéral ouvert depuis un commentaire (bouton « Réponses »).
// Les réponses sont rangées par thème (ceux de l'analyse, T1…, et ceux qu'ajoutent les modérateurs, M-…), puis par
// objection ; chacune est repliée, on ne voit que son style et son titre. Dépliée : le texte, à copier, ou à copier
// en ouvrant le commentaire sur Facebook (Facebook ne laisse aucun site remplir sa zone de réponse : il reste à
// cliquer sur « Répondre » et coller). Les modérateurs modifient, ajoutent et retirent (jamais de suppression : une
// réponse retirée passe à actif = false) ; tout part dans la base (tables reponses, reponses_themes) et revient dans
// donnees/moderation/reponses.xlsx à la prochaine synchronisation (« python -m moderation reponses »).
import { NonConnecte } from "./api.js";
import { enregistrerReponse, enregistrerTheme, etat } from "./donnees.js";

export const STYLES = {
  chiffres: "Avec des chiffres", arguments: "Argumentée", courte: "Courte", bienveillante: "Bienveillante", punchline: "Punchline",
};
const $ = (id) => document.getElementById(id);
const normal = (s) => (s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const nombreTheme = (id) => { const m = /^T(\d+)$/.exec(id); return m ? [0, Number(m[1]), ""] : [1, 0, id]; };
const parTheme = (a, b) => { const x = nombreTheme(a), y = nombreTheme(b); return x[0] - y[0] || x[1] - y[1] || x[2].localeCompare(y[2]); };
const nouvelId = (prefixe) => `${prefixe}-${(crypto.randomUUID?.() || String(Math.random()).slice(2)).replace(/-/g, "").slice(0, 8)}`;

function el(balise, attrs = {}, ...enfants) {
  const n = document.createElement(balise);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const e of enfants.flat()) if (e != null && e !== false) n.append(e instanceof Node ? e : String(e));
  return n;
}

// ── Lecture ──────────────────────────────────────────────────────────────────────────────────────────────────
export const themesActifs = () => [...etat.themesRep.values()].filter((t) => t.actif).sort((a, b) => parTheme(a.id, b.id));
export const reponsesDu = (theme) => [...etat.reponses.values()].filter((r) => r.actif && r.theme === theme);
export const themesDu = (c) => (c.themes || "").split(/\s+/).filter((t) => t && etat.themesRep.get(t)?.actif);
export function nombreReponses(c) {
  return themesDu(c).reduce((s, t) => s + reponsesDu(t).length, 0);
}
export const nomTheme = (id) => etat.themesRep.get(id)?.nom || id;

/** Les réponses par objection, dans l'ordre (ordre, puis titre). */
function parObjection(liste) {
  const groupes = new Map();
  for (const r of [...liste].sort((a, b) => (a.ordre ?? 0) - (b.ordre ?? 0) || a.titre.localeCompare(b.titre))) {
    const cle = `${r.theme}\u0000${r.objection}`;
    if (!groupes.has(cle)) groupes.set(cle, { theme: r.theme, objection: r.objection, liste: [] });
    groupes.get(cle).liste.push(r);
  }
  return [...groupes.values()];
}

// ── Panneau ──────────────────────────────────────────────────────────────────────────────────────────────────
let p = null;  // { c, theme, recherche, edition, outils }

export function ouvrirReponses(c, outils) {
  const detectes = themesDu(c);
  p = { c, theme: detectes[0] || "", recherche: "", edition: null, outils, ouverts: new Set() };
  $("panneau").hidden = false;
  $("voile").hidden = false;
  document.body.classList.add("panneau-ouvert");
  dessiner();
  $("panneau").querySelector("select, input, button")?.focus();
}
export function fermerReponses() {
  if (!p) return;
  p = null;
  $("panneau").hidden = true;
  $("voile").hidden = true;
  document.body.classList.remove("panneau-ouvert");
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && p && !p.edition) fermerReponses(); });
$("voile")?.addEventListener("click", () => fermerReponses());

const prenomAuteur = (c) => (c.auteur || "").trim().split(/\s+/)[0] || "";
const avecPrenom = () => localStorage.getItem("moderation:avec-prenom") === "1";
function texteACopier(r) {
  const prenom = avecPrenom() ? prenomAuteur(p.c) : "";
  return prenom ? `${prenom}, ${r.texte}` : r.texte;
}
async function copier(texte) {
  try {
    await navigator.clipboard.writeText(texte);
  } catch {
    const zone = el("textarea", { class: "sr" });
    zone.value = texte;
    document.body.append(zone);
    zone.select();
    document.execCommand("copy");
    zone.remove();
  }
}

function dessiner() {
  if (!p) return;
  const { c } = p;
  const detectes = themesDu(c);
  const themes = themesActifs();
  const zone = $("panneau");

  const entete = el("div", { class: "panneau-tete" },
    el("div", {}, el("strong", {}, "Réponses préparées")),
    el("button", { type: "button", class: "lien fermer", "aria-label": "Fermer", onclick: fermerReponses }, "✕"));

  const puces = el("div", { class: "puces-themes" },
    detectes.length
      ? [el("span", { class: "pale" }, "Thèmes détectés :"), ...detectes.map((t) => el("button", {
        type: "button", class: `puce-theme ${t === p.theme && !p.recherche ? "choisi" : ""}`,
        onclick: () => { p.theme = t; p.recherche = ""; dessiner(); },
      }, `${nomTheme(t)} (${reponsesDu(t).length})`))]
      : el("span", { class: "pale" }, "Ce commentaire n'est pas encore rangé dans un thème : choisissez-en un, ou cherchez une réponse."));

  const choix = el("select", { "aria-label": "Thème", onchange: (e) => { p.theme = e.target.value; p.recherche = ""; dessiner(); } },
    el("option", { value: "" }, "— Choisir un thème —"),
    themes.map((t) => el("option", { value: t.id, selected: t.id === p.theme }, `${t.nom} (${reponsesDu(t.id).length})`)));
  const recherche = el("input", { type: "search", placeholder: "Chercher dans toutes les réponses", value: p.recherche });
  recherche.addEventListener("input", () => {
    p.recherche = recherche.value;
    dessinerListe();
  });
  const prenom = el("label", { class: "case" }, el("input", {
    type: "checkbox", checked: avecPrenom(),
    onchange: (e) => localStorage.setItem("moderation:avec-prenom", e.target.checked ? "1" : "0"),
  }), ` Commencer par le prénom de l'auteur${prenomAuteur(c) ? ` (« ${prenomAuteur(c)}, … »)` : ""}`);

  const outilsTheme = el("div", { class: "actions" },
    p.theme && el("button", { type: "button", class: "bouton", onclick: () => editer({ theme: p.theme }) }, "+ Ajouter une réponse"),
    el("button", { type: "button", class: "bouton", onclick: () => editerTheme({}) }, "+ Nouveau thème"),
    p.theme && el("button", { type: "button", class: "lien", onclick: () => editerTheme(etat.themesRep.get(p.theme)) }, "Modifier ce thème"));

  zone.replaceChildren(entete, puces, el("div", { class: "choix-theme" }, choix, recherche), prenom, outilsTheme,
    el("div", { id: "liste-reponses", class: "liste-reponses" }));
  dessinerListe();
}

function dessinerListe() {
  const zone = $("liste-reponses");
  if (!zone) return;
  let liste;
  const mots = normal(p.recherche).split(/\s+/).filter(Boolean);
  if (mots.length) {
    liste = [...etat.reponses.values()].filter((r) => r.actif
      && mots.every((m) => normal(`${r.titre} ${r.texte} ${r.objection} ${nomTheme(r.theme)}`).includes(m)));
  } else {
    liste = p.theme ? reponsesDu(p.theme) : [];
  }
  if (!liste.length) {
    zone.replaceChildren(el("p", { class: "vide-reponses" }, mots.length ? "Aucune réponse ne contient ces mots."
      : p.theme ? "Aucune réponse pour ce thème pour l'instant : ajoutez la première !" : "Choisissez un thème."));
    return;
  }
  zone.replaceChildren(...parObjection(liste).map((g) => el("section", { class: "objection" },
    el("h4", {}, g.objection, mots.length > 0 && el("small", { class: "pale" }, ` · ${nomTheme(g.theme)}`)),
    g.liste.map(carteReponse))));
}

function carteReponse(r) {
  const corps = el("div", { class: "corps-reponse" },
    el("p", { class: "texte-reponse" }, r.texte),
    r.gif && el("p", { class: "gif" }, "GIF suggéré : dans la zone de commentaire, bouton GIF, chercher « ", el("strong", {}, r.gif), " »."),
    r.sources && el("p", { class: "sources pale" }, `Sources : ${r.sources}`),
    el("div", { class: "actions" },
      el("button", { type: "button", class: "bouton principal", onclick: async () => {
        await copier(texteACopier(r));
        p.outils.message("Réponse copiée : collez-la sous le commentaire.");
      } }, "Copier"),
      p.c.lien && el("a", { class: "bouton", href: p.c.lien, target: "_blank", rel: "noopener noreferrer", onclick: () => {
        copier(texteACopier(r));
        p.outils.message("Réponse copiée. Sur Facebook : « Répondre », puis coller.");
      } }, "Copier et ouvrir le commentaire ↗"),
      el("span", { class: "espace" }),
      el("button", { type: "button", class: "lien", onclick: () => editer(r) }, "Modifier"),
      el("button", { type: "button", class: "lien", onclick: () => retirer(r) }, "Retirer")),
    el("p", { class: "signature pale" }, r.par ? `Écrite par ${r.par}` : ""));
  const d = el("details", { class: "reponse", open: p.ouverts.has(r.id) },
    el("summary", {}, el("span", { class: `style s-${r.style}` }, STYLES[r.style] || r.style), " ", r.titre), corps);
  d.addEventListener("toggle", () => { if (d.open) p.ouverts.add(r.id); else p.ouverts.delete(r.id); });
  return d;
}

// ── Écriture ─────────────────────────────────────────────────────────────────────────────────────────────────
function echecEcriture(e) {
  if (e instanceof NonConnecte) return p?.outils.echec(e);
  console.error(e);
  p?.outils.message("Enregistrement impossible, réessayez.");
}

async function retirer(r) {
  if (!confirm(`Retirer la réponse « ${r.titre} » ? Elle ne sera plus proposée (elle reste récupérable dans le fichier Excel).`)) return;
  try {
    await enregistrerReponse({ ...sansMaj(r), actif: false, par: p.outils.prenom() || r.par });
    p.outils.message("Réponse retirée.");
    p.outils.apres();
    dessiner();
  } catch (e) { echecEcriture(e); }
}
const sansMaj = ({ maj, ...reste }) => reste;  // la base date elle-même chaque écriture

function formulaire(titre, champs, enregistrer) {
  p.edition = true;
  const zone = $("panneau");
  const form = el("form", { class: "edition" }, el("h3", {}, titre), champs,
    el("div", { class: "actions" },
      el("button", { type: "submit", class: "bouton principal" }, "Enregistrer"),
      el("button", { type: "button", class: "bouton", onclick: () => { p.edition = null; dessiner(); } }, "Annuler")));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const b = ev.submitter;
    b.disabled = true;
    try {
      await enregistrer(new FormData(form));
      p.edition = null;
      p.outils.apres();
      dessiner();
    } catch (e) { b.disabled = false; echecEcriture(e); }
  });
  zone.replaceChildren(form);
  form.querySelector("input, textarea, select")?.focus();
}
const champ = (libelle, controle, aide) => el("label", { class: "champ" }, el("span", {}, libelle, aide && el("small", { class: "pale" }, ` ${aide}`)), controle);

function editer(r) {
  const nouvelle = !r.id;
  const theme = r.theme || p.theme;
  const objections = [...new Set(reponsesDu(theme).map((x) => x.objection))];
  const liste = el("datalist", { id: "objections-connues" }, objections.map((o) => el("option", { value: o })));
  formulaire(nouvelle ? `Nouvelle réponse · ${nomTheme(theme)}` : "Modifier la réponse", [
    champ("Thème", el("select", { name: "theme", required: true },
      themesActifs().map((t) => el("option", { value: t.id, selected: t.id === theme }, t.nom)))),
    champ("Objection", el("input", { name: "objection", required: true, list: "objections-connues", value: r.objection || objections[0] || "", maxlength: 200 }),
      "ce à quoi elle répond, ex. « C'est un Macron bis »"), liste,
    champ("Style", el("select", { name: "style" }, Object.entries(STYLES).map(([k, v]) => el("option", { value: k, selected: k === (r.style || "arguments") }, v)))),
    champ("Titre", el("input", { name: "titre", required: true, value: r.titre || "", maxlength: 120 }), "court, visible replié"),
    champ("Texte de la réponse", el("textarea", { name: "texte", required: true, rows: 8 }, r.texte || "")),
    champ("GIF", el("input", { name: "gif", value: r.gif || "", maxlength: 60 }), "facultatif : mot à chercher dans les GIF de Facebook"),
    champ("Sources", el("textarea", { name: "sources", rows: 2 }, r.sources || ""), "d'où viennent les chiffres"),
  ], async (d) => {
    const theme2 = d.get("theme"), objection = d.get("objection").trim();
    const ordre = nouvelle || theme2 !== r.theme || objection !== r.objection
      ? Math.max(-1, ...reponsesDu(theme2).filter((x) => x.objection === objection).map((x) => x.ordre ?? 0)) + 1 : r.ordre ?? 0;
    const ligne = {
      ...(nouvelle ? {} : sansMaj(r)), id: r.id || nouvelId("R"), theme: theme2, objection, style: d.get("style"),
      titre: d.get("titre").trim(), texte: d.get("texte").trim(), gif: d.get("gif").trim() || null,
      sources: d.get("sources").trim() || null, ordre, actif: true, par: p.outils.prenom() || "modérateur",
    };
    await enregistrerReponse(ligne);
    p.theme = theme2;
    p.recherche = "";
    p.ouverts.add(ligne.id);
    p.outils.message(nouvelle ? "Réponse ajoutée : tous les modérateurs la voient." : "Réponse modifiée.");
  });
}

function editerTheme(t) {
  const nouveau = !t?.id;
  formulaire(nouveau ? "Nouveau thème" : `Modifier le thème · ${t.nom}`, [
    champ("Nom", el("input", { name: "nom", required: true, value: t?.nom || "", maxlength: 80 }), "ex. « Retraites des fonctionnaires »"),
    champ("Définition", el("textarea", { name: "definition", rows: 3 }, t?.definition || ""), "ce que regroupe ce thème (sert aussi à ranger les commentaires)"),
  ], async (d) => {
    const ligne = {
      ...(nouveau ? { famille: "Ajouté par les modérateurs" } : sansMaj(t)), id: t?.id || nouvelId("M"),
      nom: d.get("nom").trim(), definition: d.get("definition").trim() || null, actif: true, par: p.outils.prenom() || "modérateur",
    };
    await enregistrerTheme(ligne);
    p.theme = ligne.id;
    p.recherche = "";
    p.outils.message(nouveau ? "Thème ajouté : ajoutez-y une première réponse." : "Thème modifié.");
  });
}
