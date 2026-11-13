// Page Thèmes : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens (synthèse « themes »,
// écrite par python -m web publier depuis la lecture de python -m critiques). Un thème ouvert montre sa définition,
// les synthèses par sens, l'évolution par mois et les commentaires, chacun avec son résumé.
// Le filtre « Période » recompte tout dans le navigateur à partir de la date de chaque commentaire rattaché, et compare
// avec la période de même durée juste avant (évolution affichée dans la liste, tri « En hausse »).
// Le filtre « Catégorie » ne garde que les critiques et les doutes d'une catégorie (champ « cat » de chaque
// rattachement, de 1 à 5 : opposition de principe, demande de précision, objection sur une mesure, doute sur la
// faisabilité, suggestion) ; « traitables » = tout sauf les oppositions de principe. Tous les comptes suivent.
import { SOURCES, el, nombre, dateCourte, moisCourt, moisLong, ajouterJours, debounce, segments, messageErreur } from "./commun.js";
import { synthese } from "./donnees.js";
import { ouvrir, ouvrirDepuisAdresse } from "./fiche.js";
import { remplirPied } from "./pied.js";

const $ = (id) => document.getElementById(id);
const SENS = { E: "Éloges", C: "Critiques", D: "Doutes ou questions" };
// Sur quoi porte un thème, dit en clair (les libellés viennent de critiques/donnees.py ; secours pour une clé inconnue).
const sujet = (k) => D.familles[k] || "Autres sujets";
const COURT = { E: "éloges", C: "critiques", D: "doutes" };
const COULEUR = { E: "var(--haut)", C: "var(--bas)", D: "var(--doute)" };
const PAR_PAGE = 30;
// Catégories d'une critique ou d'un doute : libellés publiés avec les données (critiques/donnees.py).
const categories = () => D.categories || {};
const TRAITABLES = ["2", "3", "4", "5"];
const filtreCat = () => vue.cat !== "toutes";
/** Le rattachement passe-t-il le filtre « Catégorie » ? (une catégorie choisie écarte les éloges) */
const gardeCat = (l) => !filtreCat() || (l.sens !== "E" && (vue.cat === "traitables" ? TRAITABLES.includes(l.cat) : l.cat === vue.cat));
const sansAccents = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

// Périodes proposées : nombre de jours jusqu'au commentaire rattaché le plus récent ; « mois » = mois choisis à la main.
const PERIODES = [["tout", "Depuis le début"], ["365", "12 derniers mois"], ["182", "6 derniers mois"], ["91", "3 derniers mois"],
  ["30", "30 derniers jours"], ["mois", "Choisir les mois"]];

let D, S, BORNES, TOTAL;  // S : comptes de chaque thème sur la période choisie (et la précédente) ; TOTAL : leurs sommes
const vue = { famille: "toutes", sens: "tous", cat: "toutes", q: "", tri: "nombre", theme: null, montres: PAR_PAGE, periode: "tout", du: null, au: null };

demarrer();

async function demarrer() {
  let meta;
  try {
    [meta, D] = await Promise.all([synthese("meta"), synthese("themes")]);
  } catch (e) {
    return messageErreur($("filtres"), e);
  }
  remplirPied(meta);
  const dates = D.themes.flatMap((t) => t.liens.map((l) => l.date)).filter(Boolean).sort();
  BORNES = { premier: dates[0], dernier: dates[dates.length - 1] };
  $("pertinence").textContent = D.regles.pertinence_min;
  $("mots").textContent = D.regles.mots_min;
  lireAdresse();
  construireFiltres();
  calculer();
  ouvrirDepuisAdresse();
}

// ---------- Adresse (liens partageables) ----------

function lireAdresse() {
  const p = new URL(location.href).searchParams;
  if (p.get("famille") in D.familles) vue.famille = p.get("famille");
  if (p.get("sens") in SENS) vue.sens = p.get("sens");
  if (p.get("cat") === "traitables" || p.get("cat") in categories()) vue.cat = p.get("cat");
  if (filtreCat() && vue.sens === "E") vue.sens = "tous";
  if (["nombre", "auteurs", "hausse", "nom"].includes(p.get("tri"))) vue.tri = p.get("tri");
  if (PERIODES.some(([k]) => k === p.get("periode"))) vue.periode = p.get("periode");
  const mois = listeMois();
  vue.du = mois.includes(p.get("du")) ? p.get("du") : mois[Math.max(0, mois.length - 3)];
  vue.au = mois.includes(p.get("au")) && p.get("au") >= vue.du ? p.get("au") : mois[mois.length - 1];
  if (vue.tri === "hausse" && vue.periode === "tout") vue.tri = "nombre";
  vue.q = p.get("q") || "";
  vue.theme = p.get("t");
}
function ecrireAdresse() {
  const p = new URLSearchParams(new URL(location.href).searchParams);
  for (const k of ["famille", "sens", "cat", "tri", "q", "t", "periode", "du", "au"]) p.delete(k);
  if (filtreCat()) p.set("cat", vue.cat);
  if (vue.periode !== "tout") p.set("periode", vue.periode);
  if (vue.periode === "mois") { p.set("du", vue.du); p.set("au", vue.au); }
  if (vue.famille !== "toutes") p.set("famille", vue.famille);
  if (vue.sens !== "tous") p.set("sens", vue.sens);
  if (vue.tri !== "nombre") p.set("tri", vue.tri);
  if (vue.q) p.set("q", vue.q);
  if (vue.theme) p.set("t", vue.theme);
  history.replaceState(null, "", `${location.pathname}${p.toString() ? `?${p}` : ""}`);
}

// ---------- Filtres ----------

function construireFiltres() {
  const combien = (k) => D.themes.filter((t) => t.famille === k).length;
  // Du sujet le plus fourni au moins fourni (la base ne garde pas l'ordre des clés).
  const familles = segments([["toutes", `Tous les thèmes (${D.themes.length})`], ...Object.entries(D.familles)
    .filter(([k]) => combien(k)).sort((a, b) => combien(b[0]) - combien(a[0])).map(([k, nom]) => [k, `${nom} (${combien(k)})`])], vue.famille,
    (v) => { vue.famille = v; changer(); }, "Sujet des thèmes");
  const sens = segments([["tous", "Tous les avis"], ...Object.entries(SENS)], vue.sens, (v) => {
    vue.sens = v;
    if (v === "E" && filtreCat()) { vue.cat = "toutes"; cat?.fixer("toutes"); }  // un éloge n'a pas de catégorie
    changer();
  }, "Type d'avis");
  const cat = Object.keys(categories()).length ? segments([["toutes", "Toutes"], ["traitables", "Tout sauf les oppositions de principe"],
    ...Object.entries(categories())], vue.cat, (v) => {
    vue.cat = v;
    if (v !== "toutes" && vue.sens === "E") { vue.sens = "tous"; sens.fixer("tous"); }
    changer();
  }, "Catégorie des critiques et des doutes") : null;
  const tri = segments([["nombre", "Nombre de commentaires"], ["auteurs", "Nombre d'auteurs"], ["hausse", "En hausse"], ["nom", "Ordre alphabétique"]], vue.tri,
    (v) => { vue.tri = v; changer(); }, "Classement");
  const boutonHausse = tri.element.children[2];
  const montrerHausse = () => { boutonHausse.hidden = vue.periode === "tout"; };
  montrerHausse();
  // Mois choisis à la main : deux listes « du … au … » (si le début passe après la fin, l'autre liste suit).
  const mois = listeMois();
  const choixMois = (valeur, quand) => {
    const s = el("select", { "aria-label": quand }, ...mois.map((m) => el("option", { value: m }, moisLong(`${m}-01`))));
    s.value = valeur;
    return s;
  };
  const du = choixMois(vue.du, "Premier mois"), au = choixMois(vue.au, "Dernier mois");
  du.addEventListener("change", () => { if (du.value > au.value) au.value = du.value; vue.du = du.value; vue.au = au.value; changer(); });
  au.addEventListener("change", () => { if (du.value > au.value) du.value = au.value; vue.du = du.value; vue.au = au.value; changer(); });
  const blocMois = el("div", { class: "choix-mois", hidden: vue.periode !== "mois" }, "du", du, "au", au);
  const periode = segments(PERIODES, vue.periode, (v) => {
    vue.periode = v;
    blocMois.hidden = v !== "mois";
    if (v === "tout" && vue.tri === "hausse") { vue.tri = "nombre"; tri.fixer("nombre"); }
    montrerHausse();
    changer();
  }, "Période");
  const champ = el("input", { type: "search", placeholder: "retraites, Cannes, Macron…", "aria-label": "Chercher un thème", value: vue.q });
  champ.addEventListener("input", debounce(() => { vue.q = champ.value.trim(); changer(); }, 250));
  $("filtres").replaceChildren(el("div", { class: "barre-filtres-themes" },
    el("div", { class: "filtre-periode" }, el("span", { class: "etiquette" }, "Période des commentaires"), periode.element, blocMois),
    el("div", {}, el("span", { class: "etiquette" }, "Afficher les thèmes qui portent sur"), familles.element),
    el("div", {}, el("span", { class: "etiquette" }, "Type d'avis"), sens.element),
    cat ? el("div", {}, el("span", { class: "etiquette" }, "Critiques et doutes : ce que le programme peut en faire"), cat.element,
      el("p", { class: "pale petit aide-categorie", id: "aide-categorie" })) : null,
    el("div", {}, el("span", { class: "etiquette" }, "Classer les thèmes par"), tri.element),
    el("div", {}, el("span", { class: "etiquette" }, "Chercher un thème"), el("div", { class: "recherche" },
      el("span", { html: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>' }), champ))));
}

function changer() {
  vue.montres = PAR_PAGE;
  calculer();
}

// ---------- Calculs ----------

// ---------- Période ----------

const moisSuivant = (m) => { const [a, n] = m.split("-").map(Number); return n === 12 ? `${a + 1}-01` : `${a}-${String(n + 1).padStart(2, "0")}`; };
function listeMois() {
  const mois = [];
  if (BORNES?.premier) for (let m = BORNES.premier.slice(0, 7); m <= BORNES.dernier.slice(0, 7); m = moisSuivant(m)) mois.push(m);
  return mois;
}
const jours = (a, b) => Math.round((Date.parse(`${b}T12:00:00Z`) - Date.parse(`${a}T12:00:00Z`)) / 864e5);

/** Bornes (dates incluses) de la période choisie et de la précédente, de même durée ; null pour « depuis le début ». */
function bornes() {
  if (vue.periode === "tout") return null;
  let du, au;
  if (vue.periode === "mois") { du = `${vue.du}-01`; au = ajouterJours(`${moisSuivant(vue.au)}-01`, -1); }
  else { au = BORNES.dernier; du = ajouterJours(au, 1 - Number(vue.periode)); }
  const duree = jours(du, au) + 1;
  return { du, au, avantDu: ajouterJours(du, -duree), avantAu: ajouterJours(du, -1), avantComplet: ajouterJours(du, -duree) >= BORNES.premier };
}

/** Comptes de chaque thème sur la période : n et auteurs par sens, ses commentaires, et le total de la période d'avant. */
function compterPeriode() {
  const b = bornes();
  S = new Map();
  for (const t of D.themes) {
    const tous = filtreCat() ? t.liens.filter(gardeCat) : t.liens;
    const liens = b ? tous.filter((l) => l.date >= b.du && l.date <= b.au) : tous;
    const n = { E: 0, C: 0, D: 0 }, a = { E: new Set(), C: new Set(), D: new Set() };
    for (const l of liens) { n[l.sens]++; a[l.sens].add(l.a ?? l.cle); }
    const avant = b ? tous.filter((l) => l.date >= b.avantDu && l.date <= b.avantAu && (vue.sens === "tous" || l.sens === vue.sens)).length : null;
    // Par mois : les comptes publiés, ou recomptés sur la catégorie choisie.
    let mois = t.mois;
    if (filtreCat()) {
      mois = {};
      for (const l of tous) if (l.date) (mois[l.date.slice(0, 7)] ??= { E: 0, C: 0, D: 0 })[l.sens]++;
      mois = Object.fromEntries(Object.entries(mois).sort());
    }
    S.set(t.id, { n, auteurs: { E: a.E.size, C: a.C.size, D: a.D.size }, liens, avant, mois });
  }
  TOTAL = { maintenant: 0, avant: 0 };
  for (const t of D.themes) { TOTAL.maintenant += compte(t); TOTAL.avant += S.get(t.id).avant || 0; }
}

const compte = (t) => { const s = S.get(t.id); return vue.sens === "tous" ? s.n.E + s.n.C + s.n.D : s.n[vue.sens]; };
const auteurs = (t) => { const s = S.get(t.id); return vue.sens === "tous" ? s.auteurs.E + s.auteurs.C + s.auteurs.D : s.auteurs[vue.sens]; };
// Évolution : la part du thème parmi les rattachements de la période, comparée à sa part sur la période précédente de
// même durée. On compare des parts, pas des nombres : la collecte des derniers mois est bien plus fournie que l'ancienne.
const part = (t) => (TOTAL.maintenant ? compte(t) / TOTAL.maintenant : 0);
const partAvant = (t) => (TOTAL.avant ? S.get(t.id).avant / TOTAL.avant : 0);
const ecart = (t) => part(t) - partAvant(t);
const pourcent = (x) => `${(100 * x).toFixed(x < 0.1 ? 1 : 0).replace(".", ",")} %`;
function evolution(t) {
  const b = bornes();
  if (!b || !compte(t)) return null;
  const titre = "Part des avis de la période qui portent sur ce thème, et sa part sur la période précédente de même durée";
  if (!b.avantComplet || TOTAL.avant < 30) return el("span", { class: "evol", title: titre.split(",")[0] }, `· ${pourcent(part(t))} des avis`);
  const e = ecart(t), sensible = Math.abs(e) >= 0.005 && Math.abs(e) >= 0.2 * partAvant(t);
  return el("span", { class: `evol ${sensible ? (e > 0 ? "hausse" : "baisse") : ""}`, title: titre },
    `· ${pourcent(part(t))} des avis (${sensible ? (e > 0 ? "en hausse, " : "en baisse, ") : ""}avant ${pourcent(partAvant(t))})`);
}

function choisir() {
  const q = sansAccents(vue.q);
  const ts = D.themes.filter((t) => (vue.famille === "toutes" || t.famille === vue.famille) && compte(t) > 0
    && (!q || sansAccents(`${t.nom} ${t.definition}`).includes(q)));
  const cle = { nombre: compte, auteurs, hausse: ecart, nom: null }[vue.tri];
  return ts.sort((a, b) => (cle ? cle(b) - cle(a) : a.nom.localeCompare(b.nom, "fr")));
}

function calculer() {
  compterPeriode();
  const ts = choisir();
  if (!ts.some((t) => t.id === vue.theme)) vue.theme = ts[0]?.id || null;
  ecrireAdresse();
  chiffres();
  aideCategorie();
  liste(ts);
  fiche();
}

/** Sous le filtre « Catégorie » : ce que veut dire la catégorie choisie. */
function aideCategorie() {
  const p = $("aide-categorie");
  if (!p) return;
  const definition = D.definitions_categories?.[vue.cat];
  p.textContent = vue.cat === "toutes" ? "Chaque critique ou doute est rangé dans une catégorie ; les éloges n'en ont pas."
    : vue.cat === "traitables" ? "Demandes de précision, objections, doutes sur la faisabilité et suggestions : ce à quoi un programme peut répondre."
      : definition ? `${categories()[vue.cat]} : ${definition}.` : "";
}

function chiffres() {
  const n = { E: 0, C: 0, D: 0 };
  for (const t of D.themes) for (const s in n) n[s] += S.get(t.id).n[s];
  const total = n.E + n.C + n.D || 1;
  const b = bornes();
  const cles = new Set();
  if (b || filtreCat()) for (const s of S.values()) for (const l of s.liens) cles.add(l.cle);
  const evoques = D.themes.filter((t) => { const s = S.get(t.id); return s.n.E + s.n.C + s.n.D > 0; }).length;
  const tuiles = [
    filtreCat() ? ["Commentaires de la catégorie", nombre(cles.size), `${b ? `du ${dateCourte(b.du)} au ${dateCourte(b.au)} ; ` : ""}${evoques} thèmes évoqués`]
    : b ? ["Commentaires de la période", nombre(cles.size), `du ${dateCourte(b.du)} au ${dateCourte(b.au)} ; ${evoques} thèmes évoqués`]
      : ["Commentaires lus", nombre(D.n_lus), `${D.a_lire ? `${nombre(D.a_lire)} encore à lire` : "tous les retenus d'aujourd'hui le sont"}, toutes sources ; ${D.themes.length} thèmes`],
    ...Object.keys(SENS).map((s) => [SENS[s], nombre(n[s]), filtreCat() && s === "E" ? "sans catégorie : non comptés ici"
      : `${Math.round((100 * n[s]) / total)} % des rattachements${filtreCat() ? " de la catégorie" : ""}`, COULEUR[s]]),
  ];
  $("chiffres").replaceChildren(...tuiles.map(([nom, valeur, legende, couleur]) => el("div", { class: "chiffre" },
    el("div", { class: "nom" }, couleur ? el("span", { class: "pastille", style: { background: couleur } }) : null, nom),
    el("div", { class: "valeur" }, valeur), el("div", { class: "legende" }, legende))));
}

function barre(t) {
  const n = S.get(t.id).n;
  const tot = n.E + n.C + n.D || 1;
  return el("div", { class: "barre-sens", "aria-hidden": "true" },
    ...Object.keys(SENS).map((s) => el("i", { style: { width: `${(100 * n[s]) / tot}%`, background: COULEUR[s] } })));
}

function liste(ts) {
  const lignes = ts.map((t) => el("button", { type: "button", class: "ligne-theme", "aria-pressed": String(t.id === vue.theme),
    onclick: () => { vue.theme = t.id; vue.montres = PAR_PAGE; calculer(); if (innerWidth < 1020) $("theme").scrollIntoView({ behavior: "smooth" }); } },
    el("span", { class: "nom-theme" }, t.nom),
    el("span", { class: "doux petit" }, `${nombre(compte(t))} · ${nombre(auteurs(t))} auteur${auteurs(t) > 1 ? "s" : ""} `, evolution(t)),
    barre(t)));
  $("liste-themes").replaceChildren(el("div", { class: "tete" }, el("h2", {}, `${ts.length} thèmes`),
    el("p", {}, `${vue.sens === "tous" ? "Bleu : éloges, rouge : critiques, jaune : doutes ou questions."
      : `Classés selon le nombre de ${COURT[vue.sens]}.`}${bornes() ? " La part du thème est comparée à celle de la période de même durée juste avant." : ""} Cliquer sur un thème pour lire ce qu'on en dit.`)),
    ...(lignes.length ? lignes : [el("p", { class: "doux" }, "Aucun thème ne correspond.")]));
}

function fiche() {
  const t = D.themes.find((x) => x.id === vue.theme);
  if (!t) return $("theme").replaceChildren();
  const s = S.get(t.id);
  const b = bornes();
  const sensMontres = vue.sens === "tous" ? Object.keys(SENS) : [vue.sens];
  const resumes = sensMontres.filter((k) => t.synthese[k] && s.n[k]).map((k) => el("div", { class: "synthese-sens" },
    el("h3", {}, el("span", { class: "pastille", style: { background: COULEUR[k] } }), `${SENS[k]} · ${nombre(s.n[k])}`,
      el("span", { class: "doux petit" }, ` (${nombre(s.auteurs[k])} auteurs)`)),
    el("p", {}, t.synthese[k])));
  if ((b || filtreCat()) && resumes.length) resumes.push(el("p", { class: "pale petit" }, filtreCat()
    ? "Ces résumés portent sur toutes les critiques et tous les doutes du thème ; les nombres et les commentaires, sur la catégorie choisie."
    : "Ces résumés portent sur toute la période ; les nombres et les commentaires, sur la période choisie."));
  const liens = s.liens.filter((l) => vue.sens === "tous" || l.sens === vue.sens);
  // Répartition des critiques et des doutes du thème par catégorie (sur la période choisie, toutes catégories).
  const parCat = {};
  for (const l of t.liens) if (l.cat && (!b || (l.date >= b.du && l.date <= b.au))) parCat[l.cat] = (parCat[l.cat] || 0) + 1;
  const repartition = Object.keys(parCat).length ? el("p", { class: "doux petit repartition-categories" }, "Critiques et doutes : ",
    ...Object.entries(categories()).filter(([k]) => parCat[k]).flatMap(([k, nom], i) => [i ? " · " : "",
      el("button", { type: "button", class: "lien", "aria-pressed": String(vue.cat === k), onclick: () => choisirCategorie(vue.cat === k ? "toutes" : k) },
        `${nom.toLowerCase()} ${nombre(parCat[k])}`)])) : null;
  const cartes = liens.slice(0, vue.montres).map((l) => el("article", { class: "resume-theme" },
    el("p", { class: "resume" }, el("span", { class: "pastille", style: { background: COULEUR[l.sens] }, title: SENS[l.sens] }), l.resume),
    el("p", { class: "doux petit extrait" }, l.texte),
    el("p", { class: "pale petit" }, l.cat && categories()[l.cat] ? el("span", { class: "etiquette-categorie" }, categories()[l.cat]) : null,
      `${dateCourte(l.date)} · ${l.compte} · ${SOURCES[l.source] || l.source} · `,
      el("button", { type: "button", class: "lien", onclick: () => ouvrir(l.cle) }, "voir le commentaire"))));
  const plus = liens.length > vue.montres ? el("button", { type: "button", class: "bouton", onclick: () => { vue.montres += PAR_PAGE; fiche(); } },
    `Voir ${Math.min(PAR_PAGE, liens.length - vue.montres)} de plus (${nombre(liens.length - vue.montres)} restants)`) : null;
  $("theme").replaceChildren(
    el("div", { class: "tete" }, el("p", { class: "surtitre" }, sujet(t.famille)), el("h2", {}, t.nom), el("p", {}, t.definition)),
    mois(t), repartition, ...resumes,
    el("h3", { class: "titre-liens" }, `Les commentaires (${nombre(liens.length)})`),
    el("div", { class: "liste-commentaires" }, ...cartes), plus);
}

/** Choix d'une catégorie depuis la fiche d'un thème : même effet que le filtre du haut, qui est reconstruit. */
function choisirCategorie(k) {
  vue.cat = k;
  if (k !== "toutes" && vue.sens === "E") vue.sens = "tous";
  construireFiltres();
  changer();
}

function mois(t) {
  // Depuis le début : les 12 derniers mois ; sinon les mois de la période (24 au plus).
  const b = bornes();
  const ms = Object.entries(S.get(t.id).mois).filter(([m]) => !b || (m >= b.du.slice(0, 7) && m <= b.au.slice(0, 7))).slice(b ? -24 : -12);
  if (ms.length < 2) return el("div");
  const max = Math.max(...ms.map(([, v]) => v.E + v.C + v.D));
  return el("div", { class: "mois-theme", "aria-label": "Rattachements par mois" },
    ...ms.map(([m, v]) => el("div", { class: "colonne-mois", title: `${moisCourt(`${m}-01`, true)} : ${v.E} éloges, ${v.C} critiques, ${v.D} doutes` },
      el("div", { class: "pile" }, ...["D", "C", "E"].map((s) => el("i", { style: { height: `${(100 * v[s]) / max}%`, background: COULEUR[s] } }))),
      el("span", { class: "pale petit" }, moisCourt(`${m}-01`)))));
}
