// Page Thèmes : ce que disent les commentaires argumentés sur lui, rangés par thème et par sens (synthèse « themes »,
// écrite par python -m web publier depuis la lecture de python -m critiques). Un thème ouvert montre sa définition,
// les synthèses par sens, l'évolution par mois et les commentaires, chacun avec son résumé.
// Le filtre « Période » (curseur sur les mois) recompte tout dans le navigateur à partir de la date de chaque
// commentaire rattaché, et compare avec la période de même durée juste avant (évolution affichée dans la liste).
// Sujets, types d'avis et types de critique sont des puces : une ou plusieurs à la fois. Le type de critique ne garde
// que les critiques et les doutes des catégories choisies (champ « cat » de chaque rattachement, de 1 à 5 : opposition
// de principe, demande de précision, objection sur une mesure, doute sur la faisabilité, suggestion) ; les éloges
// n'ont pas de catégorie et sont alors écartés. Tous les comptes suivent.
import "./connexion.js";  // en premier : la page attend le mot de passe
import { SOURCES, el, nombre, dateCourte, moisCourt, moisLong, ajouterJours, debounce, segments, puces, messageErreur } from "./commun.js";
import { curseur } from "./curseur.js";
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
const filtreCat = () => vue.cats !== null;
/** Le rattachement passe-t-il le filtre « Type de critique » ? (un filtre actif écarte les éloges) */
const gardeCat = (l) => !filtreCat() || (l.sens !== "E" && vue.cats.includes(l.cat));
const tousSens = () => vue.sens.length === 3;
const elogesSeuls = () => vue.sens.length === 1 && vue.sens[0] === "E";
const sansAccents = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();


let D, S, BORNES, TOTAL;  // S : comptes de chaque thème sur la période choisie (et la précédente) ; TOTAL : leurs sommes
// familles : null = tous les sujets ; sens : liste (E, C, D) ; cats : null = toutes les catégories ; du, au : mois « AAAA-MM ».
const vue = { familles: null, sens: ["E", "C", "D"], cats: null, q: "", tri: "nombre", theme: null, montres: PAR_PAGE, du: null, au: null };

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
  lireAdresse();
  construireFiltres();
  calculer();
  ouvrirDepuisAdresse();
}

// ---------- Adresse (liens partageables) ----------

function lireAdresse() {
  const p = new URL(location.href).searchParams;
  const liste = (k, permis) => { const v = (p.get(k) || "").split(",").filter((x) => x in permis); return v.length ? v : null; };
  vue.familles = liste("famille", D.familles);
  vue.sens = liste("sens", SENS) || Object.keys(SENS);
  vue.cats = liste("cat", categories());
  if (vue.cats && vue.cats.length === Object.keys(categories()).length) vue.cats = null;
  if (filtreCat() && elogesSeuls()) vue.sens = Object.keys(SENS);
  if (p.get("tri") === "auteurs") vue.tri = "auteurs";
  const mois = listeMois();
  vue.du = mois.includes(p.get("du")) ? p.get("du") : mois[0];
  vue.au = mois.includes(p.get("au")) && p.get("au") >= vue.du ? p.get("au") : mois[mois.length - 1];
  vue.theme = p.get("t");
}
function ecrireAdresse() {
  const p = new URLSearchParams(new URL(location.href).searchParams);
  for (const k of ["famille", "sens", "cat", "tri", "q", "t", "periode", "du", "au"]) p.delete(k);
  if (filtreCat()) p.set("cat", vue.cats.join(","));
  if (bornes()) { p.set("du", vue.du); p.set("au", vue.au); }
  if (vue.familles) p.set("famille", vue.familles.join(","));
  if (!tousSens()) p.set("sens", vue.sens.join(","));
  if (vue.tri !== "nombre") p.set("tri", vue.tri);
  if (vue.q) p.set("q", vue.q);
  if (vue.theme) p.set("t", vue.theme);
  history.replaceState(null, "", `${location.pathname}${p.toString() ? `?${p}` : ""}`);
}

// ---------- Filtres ----------

function construireFiltres() {
  const etiquette = (t) => el("span", { class: "etiquette" }, t);

  // Période : curseur sur les 12 derniers mois (95 % des rattachements en novembre 2026), précédés d'un cran
  // « Depuis le début » qui regroupe tout le reste ; derrière la piste, le nombre de rattachements de chaque cran.
  const tous = listeMois();
  const fenetre = tous.slice(-12), avant = tous.slice(0, -12);
  const crans = avant.length ? [null, ...fenetre] : fenetre;  // null : tout ce qui précède la fenêtre
  const dernier = crans.length - 1;
  const parMois = (m) => D.themes.reduce((n, t) => { const v = t.mois[m]; return n + (v ? v.E + v.C + v.D : 0); }, 0);
  const histo = crans.map((m) => (m ? parMois(m) : avant.reduce((n, x) => n + parMois(x), 0)));
  const cranDe = (m) => Math.max(0, crans.indexOf(m));
  const fixerPeriode = ([i, j]) => {
    vue.du = crans[i] ?? tous[0];
    vue.au = crans[j] ?? avant[avant.length - 1];
  };
  const nomCran = (i) => (crans[i] ? moisLong(`${crans[i]}-01`) : "avant");
  const periode = curseur({
    min: 0, max: Math.max(0, dernier), valeurs: [cranDe(vue.du), crans[0] === null && avant.includes(vue.au) ? 0 : cranDe(vue.au)],
    histo, etiquette: "Période", format: nomCran,
    plage: (i, j) => [i === 0 ? "Depuis le début" : `De ${nomCran(i)}`,
      j === dernier ? "à aujourd'hui" : crans[j] ? `à ${nomCran(j)}` : `à ${moisLong(`${avant[avant.length - 1]}-01`)}`],
    onchange: (v) => { fixerPeriode(v); changer(); },
  });
  const raccourcis = el("div", { class: "raccourcis" }, ...[["3 mois", 3], ["6 mois", 6], ["12 mois", 12], ["Tout", null]].map(([t, n]) =>
    el("button", { type: "button", class: "puce-choix", onclick: () => {
      const v = [n ? Math.max(0, dernier - n + 1) : 0, dernier];
      periode.fixer(v); fixerPeriode(v); changer();
    } }, t)));

  // Sujets : du plus fourni au moins fourni (la base ne garde pas l'ordre des clés).
  const combien = (k) => D.themes.filter((t) => t.famille === k).length;
  const sujets = Object.keys(D.familles).filter(combien).sort((a, b) => combien(b) - combien(a));
  const familles = puces(sujets.map((k) => [k, D.familles[k], combien(k)]), vue.familles || sujets, (v) => {
    vue.familles = v.length === sujets.length ? null : v; changer();
  });

  const pastille = (k) => el("span", { class: "pastille", style: { background: COULEUR[k] } });
  const cles = Object.keys(categories());
  let cat = null;
  const sens = puces(Object.keys(SENS).map((k) => [k, [pastille(k), SENS[k]]]), vue.sens, (v) => {
    vue.sens = Object.keys(SENS).filter((k) => v.includes(k));
    // Un éloge n'a pas de type de critique : n'afficher que les éloges retire ce filtre.
    if (elogesSeuls() && filtreCat()) { vue.cats = null; cat?.fixer(cles); }
    changer();
  });
  cat = cles.length ? puces(Object.entries(categories()), vue.cats || cles, (v) => {
    vue.cats = v.length === cles.length ? null : cles.filter((k) => v.includes(k));
    if (filtreCat() && elogesSeuls()) { vue.sens = ["C", "D"]; sens.fixer(vue.sens); }
    changer();
  }) : null;
  const tri = segments([["nombre", "Nombre de commentaires"], ["auteurs", "Nombre d'auteurs"]], vue.tri,
    (v) => { vue.tri = v; changer(); }, "Classement");

  const colonne = (titre, ...enfants) => el("div", { class: "colonne-filtre" }, etiquette(titre), ...enfants);
  $("filtres").replaceChildren(el("div", { class: "filtres-themes" },
    el("div", { class: "filtre-periode" }, etiquette("Période des commentaires"), periode.element, raccourcis),
    el("div", { class: "colonnes-filtres" },
      colonne("Sujets", familles.element),
      colonne("Type d'avis", sens.element),
      cat ? colonne("Type de critique", cat.element, el("p", { class: "pale petit aide-categorie", id: "aide-categorie" })) : null,
      colonne("Classer les thèmes par", tri.element))));
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

/** Bornes (dates incluses) de la période choisie et de la précédente, de même durée ; null pour toute la période. */
function bornes() {
  const mois = listeMois();
  if (!vue.du || (vue.du === mois[0] && vue.au === mois[mois.length - 1])) return null;
  const du = `${vue.du}-01`, au = ajouterJours(`${moisSuivant(vue.au)}-01`, -1);
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
    const avant = b ? tous.filter((l) => l.date >= b.avantDu && l.date <= b.avantAu && vue.sens.includes(l.sens)).length : null;
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

const compte = (t) => { const s = S.get(t.id); return vue.sens.reduce((n, k) => n + s.n[k], 0); };
const auteurs = (t) => { const s = S.get(t.id); return vue.sens.reduce((n, k) => n + s.auteurs[k], 0); };
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
  const ts = D.themes.filter((t) => (!vue.familles || vue.familles.includes(t.famille)) && compte(t) > 0
    && (!q || sansAccents(`${t.nom} ${t.definition}`).includes(q)));
  const cle = vue.tri === "auteurs" ? auteurs : compte;
  return ts.sort((a, b) => cle(b) - cle(a) || a.nom.localeCompare(b.nom, "fr"));
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

/** Sous le filtre « Type de critique » : ce que veut dire le type choisi, s'il n'y en a qu'un. */
function aideCategorie() {
  const p = $("aide-categorie");
  if (!p) return;
  const seul = vue.cats?.length === 1 ? vue.cats[0] : null;
  const definition = seul && D.definitions_categories?.[seul];
  p.textContent = definition ? `${categories()[seul]} : ${definition}.`
    : filtreCat() ? "Les éloges n'ont pas de type : ils sont écartés tant que ce filtre est actif." : "";
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
    el("p", {}, `${tousSens() ? "Bleu : éloges, rouge : critiques, jaune : doutes ou questions."
      : `Classés selon le nombre de ${vue.sens.map((k) => COURT[k]).join(" et ")}.`}${bornes() ? " La part du thème est comparée à celle de la période de même durée juste avant." : ""} Cliquer sur un thème pour lire ce qu'on en dit.`)),
    ...(lignes.length ? lignes : [el("p", { class: "doux" }, "Aucun thème ne correspond.")]));
}

function fiche() {
  const t = D.themes.find((x) => x.id === vue.theme);
  if (!t) return $("theme").replaceChildren();
  const s = S.get(t.id);
  const b = bornes();
  const sensMontres = vue.sens;
  const resumes = sensMontres.filter((k) => t.synthese[k] && s.n[k]).map((k) => el("div", { class: "synthese-sens" },
    el("h3", {}, el("span", { class: "pastille", style: { background: COULEUR[k] } }), `${SENS[k]} · ${nombre(s.n[k])}`,
      el("span", { class: "doux petit" }, ` (${nombre(s.auteurs[k])} auteurs)`)),
    el("p", {}, t.synthese[k])));
  if ((b || filtreCat()) && resumes.length) resumes.push(el("p", { class: "pale petit" }, filtreCat()
    ? "Ces résumés portent sur toutes les critiques et tous les doutes du thème ; les nombres et les commentaires, sur la catégorie choisie."
    : "Ces résumés portent sur toute la période ; les nombres et les commentaires, sur la période choisie."));
  const liens = s.liens.filter((l) => vue.sens.includes(l.sens));
  // Répartition des critiques et des doutes du thème par catégorie (sur la période choisie, toutes catégories).
  const parCat = {};
  for (const l of t.liens) if (l.cat && (!b || (l.date >= b.du && l.date <= b.au))) parCat[l.cat] = (parCat[l.cat] || 0) + 1;
  const repartition = Object.keys(parCat).length ? el("p", { class: "doux petit repartition-categories" }, "Critiques et doutes : ",
    ...Object.entries(categories()).filter(([k]) => parCat[k]).flatMap(([k, nom], i) => [i ? " · " : "",
      el("button", { type: "button", class: "lien", "aria-pressed": String(vue.cats?.length === 1 && vue.cats[0] === k),
        onclick: () => choisirCategorie(vue.cats?.length === 1 && vue.cats[0] === k ? null : k) },
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

/** Choix d'une catégorie depuis la fiche d'un thème (null : toutes) : même effet que le filtre du haut, reconstruit. */
function choisirCategorie(k) {
  vue.cats = k ? [k] : null;
  if (k && elogesSeuls()) vue.sens = ["C", "D"];
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
