// Définitions et petits outils communs aux trois pages.

export const CRITERES = ["tonalite", "forme", "systeme", "idees", "pertinence"];
export const REPROCHES = ["forme", "systeme", "idees"];
export const TITRES = { tonalite: "Tonalité", forme: "Forme", systeme: "Système", idees: "Idées", pertinence: "Pertinence" };
export const EXPLICATIONS = {
  tonalite: "hostile, neutre ou favorable envers lui",
  forme: "élocution, charisme, communication",
  systeme: "perçu comme proche de Macron, de l'establishment, ou hors système",
  idees: "son programme, ses positions",
  pertinence: "ce que le commentaire apprend : avis argumenté ou simple réaction",
};
export const BORNES = {
  tonalite: ["hostile", "neutre", "très favorable"],
  forme: ["reproche fort", "non évoquée", "éloge fort"],
  systeme: ["« système »", "non évoqué", "hors système"],
  idees: ["rejet", "non évoquées", "adhésion"],
  pertinence: ["n'apporte rien", "avis sans argument", "argumenté"],
};
export const SOURCES = { youtube: "YouTube", instagram: "Instagram" };
export const GROUPES = { officiel: "Ses comptes", media: "Médias", commentateur: "Commentateurs", soutien: "Chaînes de soutien" };
export const BAS = 6, HAUT = 14, ARGUMENTE = 12, EXPLOITABLE = 5;

const FR = new Intl.NumberFormat("fr-FR");
export const nombre = (n) => FR.format(Math.round(n));
export const pc = (x) => (x == null || !isFinite(x) ? "—" : `${Math.round(100 * x)} %`);
export const sur20 = (x) => (x == null || !isFinite(x) ? "—" : `${x.toFixed(1).replace(".", ",")}`);
export const decimal = (x, n = 2) => x.toFixed(n).replace(".", ",");

const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
const jour = (s) => { const [a, m, j] = s.slice(0, 10).split("-").map(Number); return { a, m, j }; };
export const dateLongue = (s) => { if (!s) return ""; const { a, m, j } = jour(s); return `${j === 1 ? "1er" : j} ${MOIS[m - 1]} ${a}`; };
export const dateCourte = (s) => { if (!s) return ""; const { a, m, j } = jour(s); return `${j} ${MOIS_COURTS[m - 1]} ${a}`; };
export const moisCourt = (s, avecAnnee) => { const { a, m } = jour(s); return avecAnnee ? `${MOIS_COURTS[m - 1]} ${a}` : MOIS_COURTS[m - 1]; };
export const moisLong = (s) => { const { a, m } = jour(s); return `${MOIS[m - 1]} ${a}`; };
export function ajouterJours(s, n) {
  const d = new Date(`${s.slice(0, 10)}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
export const finDeSemaine = (lundi) => ajouterJours(lundi, 6);

/** Couleur d'une note : « bas » (critique, reproche), « haut » (éloge), « neutre ». */
export function ton(critere, note) {
  if (critere === "pertinence") return note >= ARGUMENTE ? "accent" : "neutre";
  return note <= BAS ? "bas" : note >= HAUT ? "haut" : "neutre";
}

/** Ce que veut dire une note, en quelques mots (docs/GRILLE.md). */
export function sens(critere, note) {
  if (critere === "tonalite")
    return note <= 2 ? "haine, insulte" : note <= 4 ? "rejet net" : note <= 6 ? "critique" : note <= 8 ? "réservé"
      : note <= 11 ? "neutre ou mitigé" : note <= 15 ? "approbation" : note <= 18 ? "soutien clair" : "enthousiaste";
  if (critere === "pertinence")
    return note <= 1 ? "sans rapport" : note <= 3 ? "hors sujet" : note <= 6 ? "réaction minimale" : note <= 10 ? "avis sans argument"
      : note <= 14 ? "avis avec une raison" : note <= 18 ? "avis argumenté" : "argumentation riche";
  const quoi = { forme: ["sa forme", "sa forme"], systeme: ["« système »", "hors système"], idees: ["ses idées", "ses idées"] }[critere];
  return note <= 3 ? `reproche fort : ${quoi[0]}` : note <= 6 ? `reproche : ${quoi[0]}` : note <= 8 ? "légère réserve"
    : note <= 12 ? "pas évoqué" : note <= 16 ? (critere === "systeme" ? "perçu hors système" : `éloge : ${quoi[1]}`)
    : (critere === "systeme" ? "nettement hors système" : `éloge fort : ${quoi[1]}`);
}

/** Lien vers le commentaire sur la plateforme d'origine (YouTube le met en avant en haut des commentaires). */
export function lienOriginal(c) {
  const id = c.cle.split(":")[1];
  const pub = c.publications || {};
  if (c.source === "youtube") return `https://www.youtube.com/watch?v=${pub.code}&lc=${id}`;
  return pub.lien || `https://www.instagram.com/p/${pub.code}/`;
}

/** Fabrique un élément : el("div", { class: "x", onclick }, enfant, "texte"…). */
export function el(tag, attrs = {}, ...enfants) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "style" && typeof v === "object") for (const [p, w] of Object.entries(v)) e.style.setProperty(p.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`), w);
    else if (k === "html") e.innerHTML = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const x of enfants.flat()) if (x != null && x !== false) e.append(x.nodeType ? x : String(x));
  return e;
}

export function debounce(f, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => f(...a), ms); };
}

/** Rangée de boutons à bascule (puces) ; rend { element, valeurs() }. */
export function puces(options, choisies, onchange) {
  const element = el("div", { class: "puces" });
  const actives = new Set(choisies);
  for (const [v, libelle, n] of options) {
    const b = el("button", { type: "button", class: "puce-choix", "aria-pressed": String(actives.has(v)) }, libelle,
      n != null ? el("span", { class: "compte-n" }, nombre(n)) : null);
    b.addEventListener("click", () => {
      if (actives.has(v)) { if (actives.size > 1) actives.delete(v); } else actives.add(v);
      for (const [i, [w]] of options.entries()) element.children[i].setAttribute("aria-pressed", String(actives.has(w)));
      onchange([...actives]);
    });
    element.append(b);
  }
  return { element, valeurs: () => [...actives], fixer(vs) { actives.clear(); vs.forEach((v) => actives.add(v)); for (const [i, [w]] of options.entries()) element.children[i].setAttribute("aria-pressed", String(actives.has(w))); } };
}

/** Choix unique en segments ; rend { element, valeur(), fixer(v) }. */
export function segments(options, choisie, onchange, etiquette) {
  const element = el("div", { class: "segments", role: "group", "aria-label": etiquette || null });
  let courante = choisie;
  const maj = () => [...element.children].forEach((b, i) => b.setAttribute("aria-pressed", String(options[i][0] === courante)));
  for (const [v, libelle] of options) {
    element.append(el("button", { type: "button", onclick: () => { if (courante !== v) { courante = v; maj(); onchange(v); } } }, libelle));
  }
  maj();
  return { element, valeur: () => courante, fixer(v) { courante = v; maj(); } };
}

export function interrupteur(libelle, coche, onchange) {
  const input = el("input", { type: "checkbox", role: "switch" });
  input.checked = coche;
  input.addEventListener("change", () => onchange(input.checked));
  return { element: el("label", { class: "interrupteur" }, input, libelle), input };
}

export function messageErreur(conteneur, e) {
  console.error(e);
  conteneur.replaceChildren(el("div", { class: "erreur" },
    "Les données n'ont pas pu être chargées. Réessayer dans un instant ; si cela persiste, la base est peut-être en pause."));
}
