// Page Commentaires : filtres à gauche (tous à cliquer ou à glisser), liste paginée à droite, fiche au clic.
// Les filtres sont appliqués par la base (selection) ; l'adresse garde l'état pour partager une recherche.
import { CRITERES, TITRES, BORNES, SOURCES, GROUPES, BAS, HAUT, ARGUMENTE, EXPLOITABLE, el, nombre, sur20, dateCourte,
  moisCourt, moisLong, finDeSemaine, debounce, puces, segments, messageErreur } from "./commun.js";
import { synthese, selection, evolution as lireEvolution } from "./donnees.js";
import { curseur } from "./curseur.js";
import { evolution as graphique } from "./graphique.js";
import { carte, ouvrirDepuisAdresse } from "./fiche.js";
import { lireAdresse, ecrireAdresse, versBase, etatVide, TRIS, TAILLES } from "./filtres.js";
import { remplirPied } from "./pied.js";

const $ = (id) => document.getElementById(id);
const PAR_PAGE = 30;
const PRESETS = {
  tonalite: [["Hostiles", [0, BAS]], ["Neutres", [BAS + 1, HAUT - 1]], ["Favorables", [HAUT, 20]]],
  pertinence: [["Exploitables", [EXPLOITABLE, 20]], ["Argumentés", [ARGUMENTE, 20]]],
  forme: [["Reproches", [0, BAS]], ["Éloges", [HAUT, 20]]],
  systeme: [["Reproches", [0, BAS]], ["Hors système", [HAUT, 20]]],
  idees: [["Rejet", [0, BAS]], ["Adhésion", [HAUT, 20]]],
};

let meta, cube, S, etat, controles = {};

demarrer();

async function demarrer() {
  try {
    [meta, cube] = await Promise.all([synthese("meta"), synthese("cube")]);
  } catch (e) {
    return messageErreur($("filtres"), e);
  }
  remplirPied(meta);
  S = cube.semaines;
  etat = lireAdresse();
  construireFiltres();
  construireTri();
  $("ouvrir-filtres").addEventListener("click", () => $("filtres").classList.add("ouvert"));
  $("evolution").addEventListener("toggle", () => { if ($("evolution").open) chargerEvolution(); });
  recharger();
  ouvrirDepuisAdresse();
}

// ---------- Filtres ----------

const indiceDu = (du) => { if (!du) return 0; const i = S.findIndex((s, k) => k > 0 && s >= du); return i < 0 ? S.length - 1 : i; };
const indiceAu = (au) => { if (!au) return S.length - 1; for (let k = S.length - 1; k > 0; k--) if (S[k] <= au) return k; return 1; };

function construireFiltres() {
  const bloc = (titre, ...enfants) => el("div", { class: "bloc" }, titre ? el("span", { class: "etiquette" }, titre) : null, ...enfants);

  const champ = el("input", { type: "search", placeholder: "Un mot, une expression…", "aria-label": "Rechercher dans les commentaires", value: etat.q });
  champ.value = etat.q;
  champ.addEventListener("input", debounce(() => { etat.q = champ.value; changer(); }, 450));
  controles.q = champ;

  const histo = new Array(S.length).fill(0);
  for (const c of cube.cellules) histo[c[0]] += c[cube.colonnes.indexOf("n")];
  const dernier = S.length - 1;
  controles.periode = curseur({
    min: 0, max: dernier, valeurs: [indiceDu(etat.du), indiceAu(etat.au)], histo, etiquette: "Période",
    format: (i) => (i === 0 ? "le début" : dateCourte(S[i])),
    plage: (a, b) => [a === 0 ? "Depuis le début" : `du ${dateCourte(S[a])}`, b === dernier ? "à aujourd'hui" : `au ${dateCourte(finDeSemaine(S[b]))}`],
    onchange: ([a, b]) => { etat.du = a === 0 ? null : S[a]; etat.au = b === dernier ? null : S[b]; changer(); },
  });
  const raccourcis = el("div", { class: "raccourcis" }, ...[["4 sem.", 4], ["3 mois", 13], ["1 an", 52], ["Tout", null]].map(([t, n]) =>
    el("button", { type: "button", class: "puce-choix", onclick: () => {
      const v = n ? [Math.max(1, dernier - n + 1), dernier] : [0, dernier];
      controles.periode.fixer(v);
      etat.du = v[0] === 0 ? null : S[v[0]]; etat.au = null;
      changer();
    } }, t)));

  controles.sources = puces(Object.entries(SOURCES).map(([k, v]) => [k, v]), etat.sources || Object.keys(SOURCES), (v) => {
    etat.sources = v.length === Object.keys(SOURCES).length ? null : v; majListeComptes(); changer();
  });
  controles.groupes = puces(Object.entries(GROUPES).map(([k, v]) => [k, v]), etat.groupes || Object.keys(GROUPES), (v) => {
    etat.groupes = v.length === Object.keys(GROUPES).length ? null : v; majListeComptes(); changer();
  });
  controles.listeComptes = el("div", { class: "liste-comptes", role: "group", "aria-label": "Comptes" });
  majListeComptes();

  controles.type = segments([["tous", "Tous"], ["principal", "Commentaires"], ["reponse", "Réponses"]], etat.type, (v) => { etat.type = v; changer(); }, "Type");
  controles.cible = segments([["", "Tous"], ["L", "Parlent de lui"], ["A", "D'autre chose"]], etat.cible || "", (v) => { etat.cible = v || null; changer(); }, "Sujet");
  controles.mots = segments(TAILLES.map(([n, t]) => [String(n), t]), String(etat.mots), (v) => { etat.mots = +v; changer(); }, "Taille");
  controles.fiab = segments([["toutes", "Toutes"], ["bm", "Bonne ou moyenne"], ["bonne", "Bonne"]], etat.fiab, (v) => { etat.fiab = v; changer(); }, "Fiabilité");

  controles.notes = {};
  const notes = CRITERES.map((k) => {
    const valeur = el("span");
    const c = curseur({
      min: 0, max: 20, valeurs: etat.notes[k], degrade: k === "pertinence" ? "pert" : true, etiquette: TITRES[k],
      format: String, plage: () => ["", ""], bornes: [`0 ${BORNES[k][0]}`, `20 ${BORNES[k][2]}`],
      oninput: (v) => { valeur.textContent = texteNote(v); },
      onchange: (v) => { etat.notes[k] = v; valeur.textContent = texteNote(v); changer(); },
    });
    c.element.querySelector(".valeurs").remove();
    valeur.textContent = texteNote(etat.notes[k]);
    controles.notes[k] = { curseur: c, valeur };
    const raccourcis = el("div", { class: "puces", style: { marginTop: "6px" } }, ...PRESETS[k].map(([t, v]) =>
      el("button", { type: "button", class: "puce-choix", style: { padding: "3px 10px", fontSize: "13px" }, onclick: () => {
        const deja = etat.notes[k][0] === v[0] && etat.notes[k][1] === v[1];
        etat.notes[k] = deja ? [0, 20] : [...v];
        c.fixer(etat.notes[k]); valeur.textContent = texteNote(etat.notes[k]); changer();
      } }, t)));
    return el("div", { class: "note-filtre" }, el("div", { class: "titre-note" }, el("span", {}, TITRES[k]), valeur), c.element, raccourcis);
  });

  $("filtres").replaceChildren(
    el("button", { type: "button", class: "bouton discret fermer-filtres", onclick: () => $("filtres").classList.remove("ouvert") }, "Fermer ×"),
    bloc("Recherche", el("div", { class: "recherche" },
      el("span", { html: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>' }), champ),
      el("p", { class: "aide" }, "« entre guillemets » pour une expression exacte, -mot pour l'exclure.")),
    bloc("Période", controles.periode.element, raccourcis),
    bloc("Sources", controles.sources.element),
    bloc("Comptes", controles.groupes.element, controles.listeComptes),
    bloc("Type", controles.type.element),
    bloc("Sujet", controles.cible.element),
    bloc("Taille", controles.mots.element,
      el("p", { class: "aide" }, "Les longs commentaires sont souvent les plus argumentés.")),
    bloc("Notes (de 0 à 20)", ...notes),
    bloc("Fiabilité des notes", controles.fiab.element),
    bloc(null, el("button", { type: "button", class: "bouton", onclick: reinitialiser }, "Tout réinitialiser")));
}

const texteNote = ([a, b]) => (a === 0 && b === 20 ? "toutes" : a === b ? `${a}` : `${a} à ${b}`);

function majListeComptes() {
  const src = new Set(etat.sources || Object.keys(SOURCES)), grp = new Set(etat.groupes || Object.keys(GROUPES));
  const choisis = new Set(etat.comptes || []);
  const visibles = meta.comptes.filter((c) => src.has(c.source) && grp.has(c.groupe));
  controles.listeComptes.replaceChildren(...visibles.map((c) => {
    const box = el("input", { type: "checkbox" });
    box.checked = choisis.has(c.nom);
    box.addEventListener("change", () => {
      const s = new Set(etat.comptes || []);
      box.checked ? s.add(c.nom) : s.delete(c.nom);
      etat.comptes = s.size ? [...s] : null;
      changer();
    });
    return el("label", {}, box, el("span", { title: `${c.nom} · ${SOURCES[c.source]}` }, c.nom), el("span", {}, nombre(c.n)));
  }));
}

function construireTri() {
  const select = $("tri");
  for (const [k, [libelle]] of Object.entries(TRIS)) select.append(el("option", { value: k }, libelle));
  select.value = TRIS[etat.tri] ? etat.tri : "recent";
  select.addEventListener("change", () => { etat.tri = select.value; changer(); });
}

function reinitialiser() {
  etat = etatVide();
  controles.q.value = "";
  controles.periode.fixer([0, S.length - 1]);
  controles.sources.fixer(Object.keys(SOURCES));
  controles.groupes.fixer(Object.keys(GROUPES));
  controles.type.fixer("tous"); controles.cible.fixer(""); controles.fiab.fixer("toutes"); controles.mots.fixer("0");
  for (const k of CRITERES) { controles.notes[k].curseur.fixer([0, 20]); controles.notes[k].valeur.textContent = "toutes"; }
  $("tri").value = "recent";
  majListeComptes();
  changer();
}

/** Pastilles des filtres actifs, chacune retire son filtre au clic. */
function filtresActifs() {
  const p = [];
  const retirer = (f) => () => { f(); synchroniser(); changer(); };
  if (etat.q) p.push([`« ${etat.q} »`, retirer(() => { etat.q = ""; })]);
  if (etat.du || etat.au) p.push([`${etat.du ? `du ${dateCourte(etat.du)}` : "depuis le début"} ${etat.au ? `au ${dateCourte(finDeSemaine(etat.au))}` : "à aujourd'hui"}`, retirer(() => { etat.du = etat.au = null; })]);
  if (etat.sources) p.push([etat.sources.map((s) => SOURCES[s]).join(" + "), retirer(() => { etat.sources = null; })]);
  if (etat.groupes) p.push([etat.groupes.map((g) => GROUPES[g]).join(" + "), retirer(() => { etat.groupes = null; })]);
  for (const c of etat.comptes || []) p.push([c, retirer(() => { etat.comptes = etat.comptes.filter((x) => x !== c); if (!etat.comptes.length) etat.comptes = null; })]);
  if (etat.type !== "tous") p.push([etat.type === "reponse" ? "Réponses" : "Commentaires principaux", retirer(() => { etat.type = "tous"; })]);
  if (etat.cible) p.push([etat.cible === "L" ? "Parlent de lui" : "Parlent d'autre chose", retirer(() => { etat.cible = null; })]);
  for (const k of CRITERES) if (etat.notes[k][0] > 0 || etat.notes[k][1] < 20) p.push([`${TITRES[k]} ${texteNote(etat.notes[k])}`, retirer(() => { etat.notes[k] = [0, 20]; })]);
  if (etat.mots) p.push([`${etat.mots} mots et plus`, retirer(() => { etat.mots = 0; })]);
  if (etat.fiab !== "toutes") p.push([etat.fiab === "bonne" ? "Fiabilité bonne" : "Fiabilité bonne ou moyenne", retirer(() => { etat.fiab = "toutes"; })]);
  $("actifs").replaceChildren(...p.map(([t, f]) => el("button", { type: "button", onclick: f, "aria-label": `Retirer le filtre ${t}` }, t)));
}

/** Remet les contrôles d'accord avec l'état (après le retrait d'une pastille). */
function synchroniser() {
  controles.q.value = etat.q;
  controles.periode.fixer([indiceDu(etat.du), indiceAu(etat.au)]);
  controles.sources.fixer(etat.sources || Object.keys(SOURCES));
  controles.groupes.fixer(etat.groupes || Object.keys(GROUPES));
  controles.type.fixer(etat.type); controles.cible.fixer(etat.cible || ""); controles.fiab.fixer(etat.fiab);
  controles.mots.fixer(String(etat.mots));
  for (const k of CRITERES) { controles.notes[k].curseur.fixer(etat.notes[k]); controles.notes[k].valeur.textContent = texteNote(etat.notes[k]); }
  majListeComptes();
}

// ---------- Résultats ----------

let page = 0, total = null, fini = false, enCours = null, generation = 0;
const observateur = new IntersectionObserver((e) => { if (e[0].isIntersecting) suite(); }, { rootMargin: "600px" });

function changer() {
  ecrireAdresse(etat, "commentaires");
  recharger();
}

function recharger() {
  filtresActifs();
  generation++;
  page = 0; total = null; fini = false;
  enCours?.abort();
  $("liste").style.opacity = ".5";
  $("total").textContent = "Recherche…";
  suite(true);
  if ($("evolution").open) chargerEvolution();
}

async function suite(premiere = false) {
  if (fini || (!premiere && enCours)) return;
  const g = generation;
  enCours = new AbortController();
  const zone = $("suite");
  if (!premiere) zone.replaceChildren(el("div", { class: "chargement" }, "Chargement…"));
  try {
    const { lignes, total: t } = await selection(versBase(etat), {
      tri: TRIS[etat.tri]?.[1] || TRIS.recent[1], limite: PAR_PAGE, decalage: page * PAR_PAGE, compter: page === 0, signal: enCours.signal,
    });
    if (g !== generation) return;
    if (page === 0) {
      total = t;
      $("liste").replaceChildren();
      $("liste").style.opacity = "";
      $("total").textContent = total === 1 ? "1 commentaire" : `${nombre(total ?? 0)} commentaires`;
      if (!lignes.length) $("liste").append(el("div", { class: "vide" }, "Aucun commentaire ne correspond. Élargir la période ou retirer un filtre."));
    }
    $("liste").append(...lignes.map((c) => carte(c, { critere: triCritere() })));
    page++;
    fini = lignes.length < PAR_PAGE;
    zone.replaceChildren(...(fini ? [] : [el("button", { type: "button", class: "bouton", style: { margin: "18px auto", display: "flex" }, onclick: () => suite() }, "Afficher plus")]));
    enCours = null;
    if (!fini) { observateur.disconnect(); observateur.observe(zone); }
  } catch (e) {
    if (e.name === "AbortError") return;
    enCours = null;
    $("liste").style.opacity = "";
    if (page === 0) { $("total").textContent = ""; messageErreur($("liste"), e); } else messageErreur(zone, e);
  }
}

const triCritere = () => ({ favorable: "tonalite", hostile: "tonalite", pertinent: "pertinence" })[etat.tri];

// ---------- Évolution de la sélection ----------

let controleurEvo;
async function chargerEvolution() {
  const zone = $("evolution-graph");
  controleurEvo?.abort();
  controleurEvo = new AbortController();
  zone.style.opacity = ".5";
  let lignes;
  try {
    lignes = await lireEvolution(versBase(etat), controleurEvo.signal);
  } catch (e) {
    if (e.name !== "AbortError") { zone.style.opacity = ""; messageErreur(zone, e); }
    return;
  }
  zone.style.opacity = "";
  const debut = S[1];
  const recentes = lignes.filter((l) => l.semaine >= debut);
  if (!recentes.length) { zone.replaceChildren(el("p", { class: "vide" }, "Rien à tracer depuis " + moisLong(debut) + ".")); return; }
  const parMois = recentes.length > 30;
  const seaux = new Map();
  // Toutes les périodes de la première à la dernière, vides comprises (l'axe des x reste régulier).
  const toutes = [];
  for (let k = S.indexOf(recentes[0].semaine); k >= 1 && k < S.length && S[k] <= recentes.at(-1).semaine; k++) toutes.push(S[k]);
  for (const s of toutes) { const q = parMois ? s.slice(0, 7) : s; if (!seaux.has(q)) seaux.set(q, { debut: s, n: 0, ton: 0, bas: 0, haut: 0 }); }
  for (const l of recentes) {
    const x = seaux.get(parMois ? l.semaine.slice(0, 7) : l.semaine);
    if (!x) continue;
    x.n += l.n; x.ton += l.tonalite * l.n; x.bas += l.bas_tonalite; x.haut += l.haut_tonalite;
  }
  const MIN = 20;
  const points = [...seaux.values()].map((x) => ({ n: x.n, debut: x.debut, moyenne: x.n ? x.ton / x.n : null,
    valeurs: { haut: x.n >= MIN ? (100 * x.haut) / x.n : null, bas: x.n >= MIN ? (100 * x.bas) / x.n : null } }));
  const max = Math.max(10, ...points.flatMap((p) => [p.valeurs.haut, p.valeurs.bas]).filter((v) => v != null));
  const yPas = max > 60 ? 25 : max > 30 ? 10 : 5;
  graphique(zone, {
    points, yPas, yMax: Math.min(100, yPas * Math.ceil((max * 1.08) / yPas)),
    series: [{ cle: "haut", nom: "favorables", couleur: "var(--haut)" }, { cle: "bas", nom: "hostiles", couleur: "var(--bas)" }],
    formatY: (v, precis) => `${precis ? Math.round(v) : v} %`,
    etiquetteX: (i) => {
      const d = points[i].debut, avant = points[i - 1]?.debut;
      if (!parMois && avant && avant.slice(0, 7) === d.slice(0, 7)) return null;
      return moisCourt(d, i === 0 || d.slice(5, 7) === "01");
    },
    titreBulle: (i) => (parMois ? moisLong(points[i].debut) : `Semaine du ${dateCourte(points[i].debut)}`),
    lignesBulle: (i) => (points[i].moyenne != null ? [["tonalité moyenne", `${sur20(points[i].moyenne)}/20`]] : []),
    titreVolume: "Nombre de commentaires de la sélection",
    description: "Évolution de la sélection",
  });
  zone.prepend(el("p", { class: "doux petit", style: { margin: "0 0 12px" } },
    `Part des commentaires de la sélection jugés favorables (tonalité ≥ ${HAUT}) et hostiles (≤ ${BAS}), par ${parMois ? "mois" : "semaine"}, depuis ${moisLong(debut)}.`));
}
