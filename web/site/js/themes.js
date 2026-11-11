// Page Thèmes : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens (synthèse « themes »,
// écrite par python -m web publier depuis la lecture de python -m critiques). Un thème ouvert montre sa définition,
// les synthèses par sens, l'évolution par mois et les commentaires, chacun avec son résumé.
import { SOURCES, el, nombre, dateCourte, moisCourt, debounce, segments, messageErreur } from "./commun.js";
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
const sansAccents = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

let D;
const vue = { famille: "toutes", sens: "tous", q: "", tri: "nombre", theme: null, montres: PAR_PAGE };

demarrer();

async function demarrer() {
  let meta;
  try {
    [meta, D] = await Promise.all([synthese("meta"), synthese("themes")]);
  } catch (e) {
    return messageErreur($("filtres"), e);
  }
  remplirPied(meta);
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
  if (["nombre", "auteurs", "nom"].includes(p.get("tri"))) vue.tri = p.get("tri");
  vue.q = p.get("q") || "";
  vue.theme = p.get("t");
}
function ecrireAdresse() {
  const p = new URLSearchParams(new URL(location.href).searchParams);
  for (const k of ["famille", "sens", "tri", "q", "t"]) p.delete(k);
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
  const sens = segments([["tous", "Tous les avis"], ...Object.entries(SENS)], vue.sens, (v) => { vue.sens = v; changer(); }, "Type d'avis");
  const tri = segments([["nombre", "Nombre de commentaires"], ["auteurs", "Nombre d'auteurs"], ["nom", "Ordre alphabétique"]], vue.tri,
    (v) => { vue.tri = v; changer(); }, "Classement");
  const champ = el("input", { type: "search", placeholder: "retraites, Cannes, Macron…", "aria-label": "Chercher un thème", value: vue.q });
  champ.addEventListener("input", debounce(() => { vue.q = champ.value.trim(); changer(); }, 250));
  $("filtres").replaceChildren(el("div", { class: "barre-filtres-themes" },
    el("div", {}, el("span", { class: "etiquette" }, "Afficher les thèmes qui portent sur"), familles.element),
    el("div", {}, el("span", { class: "etiquette" }, "Type d'avis"), sens.element),
    el("div", {}, el("span", { class: "etiquette" }, "Classer les thèmes par"), tri.element),
    el("div", {}, el("span", { class: "etiquette" }, "Chercher un thème"), el("div", { class: "recherche" },
      el("span", { html: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>' }), champ))));
}

function changer() {
  vue.montres = PAR_PAGE;
  calculer();
}

// ---------- Calculs ----------

const compte = (t) => (vue.sens === "tous" ? t.n.E + t.n.C + t.n.D : t.n[vue.sens]);
const auteurs = (t) => (vue.sens === "tous" ? t.auteurs.E + t.auteurs.C + t.auteurs.D : t.auteurs[vue.sens]);

function choisir() {
  const q = sansAccents(vue.q);
  const ts = D.themes.filter((t) => (vue.famille === "toutes" || t.famille === vue.famille) && compte(t) > 0
    && (!q || sansAccents(`${t.nom} ${t.definition}`).includes(q)));
  const cle = { nombre: compte, auteurs, nom: null }[vue.tri];
  return ts.sort((a, b) => (cle ? cle(b) - cle(a) : a.nom.localeCompare(b.nom, "fr")));
}

function calculer() {
  const ts = choisir();
  if (!ts.some((t) => t.id === vue.theme)) vue.theme = ts[0]?.id || null;
  ecrireAdresse();
  chiffres();
  liste(ts);
  fiche();
}

function chiffres() {
  const n = { E: 0, C: 0, D: 0 };
  for (const t of D.themes) for (const s in n) n[s] += t.n[s];
  const total = n.E + n.C + n.D;
  const tuiles = [
    ["Commentaires lus", nombre(D.n_lus), `${D.a_lire ? `${nombre(D.a_lire)} encore à lire` : "tous les retenus d'aujourd'hui le sont"}, toutes sources ; ${D.themes.length} thèmes`],
    ...Object.keys(SENS).map((s) => [SENS[s], nombre(n[s]), `${Math.round((100 * n[s]) / total)} % des rattachements`, COULEUR[s]]),
  ];
  $("chiffres").replaceChildren(...tuiles.map(([nom, valeur, legende, couleur]) => el("div", { class: "chiffre" },
    el("div", { class: "nom" }, couleur ? el("span", { class: "pastille", style: { background: couleur } }) : null, nom),
    el("div", { class: "valeur" }, valeur), el("div", { class: "legende" }, legende))));
}

function barre(t) {
  const tot = t.n.E + t.n.C + t.n.D;
  return el("div", { class: "barre-sens", "aria-hidden": "true" },
    ...Object.keys(SENS).map((s) => el("i", { style: { width: `${(100 * t.n[s]) / tot}%`, background: COULEUR[s] } })));
}

function liste(ts) {
  const lignes = ts.map((t) => el("button", { type: "button", class: "ligne-theme", "aria-pressed": String(t.id === vue.theme),
    onclick: () => { vue.theme = t.id; vue.montres = PAR_PAGE; calculer(); if (innerWidth < 1020) $("theme").scrollIntoView({ behavior: "smooth" }); } },
    el("span", { class: "nom-theme" }, t.nom),
    el("span", { class: "doux petit" }, `${nombre(compte(t))} · ${nombre(auteurs(t))} auteurs`),
    barre(t)));
  $("liste-themes").replaceChildren(el("div", { class: "tete" }, el("h2", {}, `${ts.length} thèmes`),
    el("p", {}, `${vue.sens === "tous" ? "Bleu : éloges, rouge : critiques, jaune : doutes ou questions."
      : `Classés selon le nombre de ${COURT[vue.sens]}.`} Cliquer sur un thème pour lire ce qu'on en dit.`)),
    ...(lignes.length ? lignes : [el("p", { class: "doux" }, "Aucun thème ne correspond.")]));
}

function fiche() {
  const t = D.themes.find((x) => x.id === vue.theme);
  if (!t) return $("theme").replaceChildren();
  const sensMontres = vue.sens === "tous" ? Object.keys(SENS) : [vue.sens];
  const resumes = sensMontres.filter((s) => t.synthese[s]).map((s) => el("div", { class: "synthese-sens" },
    el("h3", {}, el("span", { class: "pastille", style: { background: COULEUR[s] } }), `${SENS[s]} · ${nombre(t.n[s])}`,
      el("span", { class: "doux petit" }, ` (${nombre(t.auteurs[s])} auteurs)`)),
    el("p", {}, t.synthese[s])));
  const liens = t.liens.filter((l) => vue.sens === "tous" || l.sens === vue.sens);
  const cartes = liens.slice(0, vue.montres).map((l) => el("article", { class: "resume-theme" },
    el("p", { class: "resume" }, el("span", { class: "pastille", style: { background: COULEUR[l.sens] }, title: SENS[l.sens] }), l.resume),
    el("p", { class: "doux petit extrait" }, l.texte),
    el("p", { class: "pale petit" }, `${dateCourte(l.date)} · ${l.compte} · ${SOURCES[l.source] || l.source} · `,
      el("button", { type: "button", class: "lien", onclick: () => ouvrir(l.cle) }, "voir le commentaire"))));
  const plus = liens.length > vue.montres ? el("button", { type: "button", class: "bouton", onclick: () => { vue.montres += PAR_PAGE; fiche(); } },
    `Voir ${Math.min(PAR_PAGE, liens.length - vue.montres)} de plus (${nombre(liens.length - vue.montres)} restants)`) : null;
  $("theme").replaceChildren(
    el("div", { class: "tete" }, el("p", { class: "surtitre" }, sujet(t.famille)), el("h2", {}, t.nom), el("p", {}, t.definition)),
    mois(t), ...resumes,
    el("h3", { class: "titre-liens" }, `Les commentaires (${nombre(liens.length)})`),
    el("div", { class: "liste-commentaires" }, ...cartes), plus);
}

function mois(t) {
  const ms = Object.entries(t.mois).slice(-12);
  if (ms.length < 2) return el("div");
  const max = Math.max(...ms.map(([, v]) => v.E + v.C + v.D));
  return el("div", { class: "mois-theme", "aria-label": "Rattachements par mois" },
    ...ms.map(([m, v]) => el("div", { class: "colonne-mois", title: `${moisCourt(`${m}-01`, true)} : ${v.E} éloges, ${v.C} critiques, ${v.D} doutes` },
      el("div", { class: "pile" }, ...["D", "C", "E"].map((s) => el("i", { style: { height: `${(100 * v[s]) / max}%`, background: COULEUR[s] } }))),
      el("span", { class: "pale petit" }, moisCourt(`${m}-01`)))));
}
