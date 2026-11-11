// Page Statistiques : tout est recalculé dans le navigateur à partir du « cube » (comptages par semaine, compte,
// type, cible), donc instantanément ; seuls les exemples sont demandés à la base.
// Deux vues : une voix par commentaire (colonnes n, tonalite…), ou pondérée par les « j'aime » (colonnes p_n,
// p_tonalite… : un commentaire pèse 1 + ses « j'aime »). K(nom) rend la colonne de la vue choisie ; les seuils
// « assez de commentaires » se comptent toujours en commentaires (col.n).
import { SOURCES, GROUPES, TITRES, REPROCHES, EXPLOITABLE, BAS, HAUT, el, nombre, pc, sur20, dateCourte, moisCourt, moisLong,
  finDeSemaine, debounce, puces, segments, interrupteur, messageErreur } from "./commun.js";
import { synthese, selection } from "./donnees.js";
import { curseur } from "./curseur.js";
import { evolution as graphique } from "./graphique.js";
import { carte, ouvrirDepuisAdresse } from "./fiche.js";
import { lireAdresse, ecrireAdresse, versParametres, versBase, etatVide } from "./filtres.js";
import { remplirPied } from "./pied.js";

const $ = (id) => document.getElementById(id);
const MIN_PAR_PERIODE = 30; // une semaine de quelques commentaires donnerait des parts au hasard
const MESURES = ["tonalite", ...REPROCHES];
const COULEURS = { bas: "var(--bas)", haut: "var(--haut)", accent: "var(--accent)" };

const K = (nom) => col[(etat.poids && col.p_n != null ? "p_" : "") + nom];
let cube, col, S, etat, periode, vue = { critere: "tonalite", mode: "parts", pas: "auto", exemple: "critiques", tousComptes: false };

demarrer();

async function demarrer() {
  let meta;
  try {
    [meta, cube] = await Promise.all([synthese("meta"), synthese("cube")]);
  } catch (e) {
    return messageErreur($("filtres"), e);
  }
  remplirPied(meta);
  col = Object.fromEntries(cube.colonnes.map((c, i) => [c, i]));
  S = cube.semaines;
  etat = lireAdresse();
  periode = [indiceDu(etat.du), indiceAu(etat.au)];
  construireFiltres();
  calculer();
  chargerExemples();
  ouvrirDepuisAdresse();
}

// ---------- Période ----------

function indiceDu(du) {
  if (!du) return 0;
  const i = S.findIndex((s, k) => k > 0 && s >= du);
  return i < 0 ? S.length - 1 : i;
}
function indiceAu(au) {
  if (!au) return S.length - 1;
  for (let k = S.length - 1; k > 0; k--) if (S[k] <= au) return k;
  return 1;
}
const libelleDebut = (i) => (i === 0 ? "Depuis le début" : `du ${dateCourte(S[i])}`);
const libelleFin = (i) => (i === S.length - 1 ? "à aujourd'hui" : `au ${dateCourte(finDeSemaine(S[i]))}`);

function changer() {
  etat.du = periode[0] === 0 ? null : S[periode[0]];
  etat.au = periode[1] === S.length - 1 ? null : S[periode[1]];
  ecrireAdresse(etat, "statistiques");
  calculer();
  chargerExemplesPlusTard();
}

// ---------- Filtres ----------

let curseurPeriode, zoneCompte;
function construireFiltres() {
  const histo = new Array(S.length).fill(0);
  for (const c of cube.cellules) histo[c[0]] += c[col.n];
  curseurPeriode = curseur({
    min: 0, max: S.length - 1, valeurs: periode, histo, etiquette: "Période",
    format: (i) => (i === 0 ? "le début" : dateCourte(S[i])),
    plage: (a, b) => [libelleDebut(a), libelleFin(b)],
    oninput: (v) => { periode = v; calculer(); },
    onchange: (v) => { periode = v; changer(); },
  });
  const dernier = S.length - 1;
  const raccourcis = el("div", { class: "raccourcis" }, ...[["4 dernières semaines", 4], ["3 mois", 13], ["6 mois", 26], ["1 an", 52], ["Tout", null]].map(([t, n]) =>
    el("button", { type: "button", class: "puce-choix", onclick: () => {
      periode = n ? [Math.max(1, dernier - n + 1), dernier] : [0, dernier];
      curseurPeriode.fixer(periode);
      changer();
    } }, t)));

  const parSource = {}, parGroupe = {};
  for (const c of cube.cellules) {
    const k = cube.comptes[c[1]];
    parSource[k.source] = (parSource[k.source] || 0) + c[col.n];
    parGroupe[k.groupe] = (parGroupe[k.groupe] || 0) + c[col.n];
  }
  const sources = puces(Object.entries(SOURCES).map(([k, v]) => [k, v, parSource[k]]), etat.sources || Object.keys(SOURCES), (v) => {
    etat.sources = v.length === Object.keys(SOURCES).length ? null : v; changer();
  });
  const groupes = puces(Object.entries(GROUPES).map(([k, v]) => [k, v, parGroupe[k]]), etat.groupes || Object.keys(GROUPES), (v) => {
    etat.groupes = v.length === Object.keys(GROUPES).length ? null : v; changer();
  });
  const type = segments([["tous", "Tous"], ["principal", "Commentaires"], ["reponse", "Réponses"]], etat.type, (v) => { etat.type = v; changer(); }, "Type");
  const expl = interrupteur("Écarter les commentaires inexploitables", etat.exploitables, (v) => { etat.exploitables = v; changer(); });
  const poids = interrupteur("Pondérer par les « j'aime »", etat.poids, (v) => { etat.poids = v; changer(); });
  zoneCompte = el("div");
  $("filtres").replaceChildren(el("div", { class: "barre-filtres" },
    el("div", { class: "periode" }, el("span", { class: "etiquette" }, "Période"), curseurPeriode.element, raccourcis),
    el("div", {}, el("span", { class: "etiquette" }, "Sources"), sources.element),
    el("div", {}, el("span", { class: "etiquette" }, "Comptes"), groupes.element),
    el("div", { class: "filtres-ligne" },
      el("div", {}, el("span", { class: "etiquette" }, "Type"), type.element),
      el("div", {}, el("span", { class: "etiquette" }, "Exploitables"), expl.element,
        el("p", { class: "aide" }, "Sans émojis seuls, hors-sujet ni ironie impossible à trancher.")),
      col.p_n != null ? el("div", {}, el("span", { class: "etiquette" }, "Poids"), poids.element,
        el("p", { class: "aide" }, "Chaque commentaire pèse 1 + ses « j'aime ».")) : null),
    zoneCompte));
  majCompte();
}

function majCompte() {
  zoneCompte.replaceChildren(...(etat.comptes?.length ? [el("div", { class: "filtres-actifs", style: { marginBottom: 0 } },
    el("button", { type: "button", onclick: () => { etat.comptes = null; majCompte(); changer(); } }, `Compte : ${etat.comptes.join(", ")}`))] : []));
}

// ---------- Calculs ----------

function choisir() {
  const [i0, i1] = periode;
  const src = new Set(etat.sources || Object.keys(SOURCES)), grp = new Set(etat.groupes || Object.keys(GROUPES));
  const cpt = etat.comptes?.length ? new Set(etat.comptes) : null;
  const tous = cube.cellules.filter((c) => {
    if (c[0] < i0 || c[0] > i1) return false;
    const k = cube.comptes[c[1]];
    if (!src.has(k.source) || !grp.has(k.groupe) || (cpt && !cpt.has(k.nom))) return false;
    return etat.type === "tous" || (etat.type === "reponse") === Boolean(c[2]);
  });
  const base = etat.exploitables ? tous.filter((c) => c[4]) : tous;
  return { tous, base, sur: base.filter((c) => !c[3]) };
}

function somme(cellules) {
  const t = new Array(cube.colonnes.length).fill(0);
  for (const c of cellules) for (let j = col.n; j < c.length; j++) t[j] += c[j];
  return t;
}

function calculer() {
  const { tous, base, sur } = choisir();
  const T = somme(tous), B = somme(base), L = somme(sur);
  chiffres(T, B, L);
  perception(L);
  evolution(sur, base);
  comptes(sur);
}

// ---------- Chiffres clés ----------

function chiffres(T, B, L) {
  const n = col.n, p = K("n");
  const ton = L[p] ? L[K("tonalite")] / L[p] : null;
  const mention = etat.poids ? ", pondéré par les « j'aime »" : "";
  const verdict = ton == null ? "" : ton >= 12 ? "plutôt favorable" : ton <= 8 ? "plutôt hostile" : "partagée";
  const tuiles = [
    ["Commentaires analysés", nombre(B[n]), etat.exploitables ? `exploitables sur ${nombre(T[n])}` : "dans la sélection"],
    ["Parlent de lui", pc(B[n] ? L[n] / B[n] : null), `${nombre(L[n])} commentaires`],
    ["Tonalité moyenne", ton == null ? "—" : `${sur20(ton)} /20`, verdict ? `envers lui : ${verdict}${mention}` : ""],
    ["Favorables", pc(L[p] ? L[K("haut_tonalite")] / L[p] : null), `tonalité de ${HAUT} ou plus${mention}`, "var(--haut)"],
    ["Hostiles", pc(L[p] ? L[K("bas_tonalite")] / L[p] : null), `tonalité de ${BAS} ou moins${mention}`, "var(--bas)"],
    ["Argumentés", pc(B[p] ? B[K("argumentes")] / B[p] : null), `donnent au moins une raison${mention}`],
  ];
  $("chiffres").replaceChildren(...tuiles.map(([nom, valeur, legende, couleur]) => el("div", { class: "chiffre" },
    el("div", { class: "nom" }, couleur ? el("span", { class: "pastille", style: { background: couleur } }) : null, nom),
    el("div", { class: "valeur" }, valeur), el("div", { class: "legende" }, legende))));
}

// ---------- Perception ----------

function repartition(bas, haut, fine) {
  const milieu = Math.max(0, 1 - bas - haut);
  const part = (x, classe, texte) => el("div", { class: classe, style: { flex: `${x} 1 0` }, title: texte }, !fine && x >= 0.07 ? pc(x) : "");
  return el("div", { class: `repartition${fine ? " fine" : ""}` },
    bas > 0 ? part(bas, "bas", `critiques ${pc(bas)}`) : null,
    milieu > 0 ? part(milieu, "milieu", `non évoqué ou neutre ${pc(milieu)}`) : null,
    haut > 0 ? part(haut, "haut", `éloges ${pc(haut)}`) : null);
}

function perception(L) {
  const n = L[col.n], p = L[K("n")];
  const lignes = {
    tonalite: "hostile · neutre · favorable",
    forme: "élocution, charisme, communication",
    systeme: "proche de Macron, de l'establishment… ou hors système",
    idees: "son programme, ses positions",
  };
  const grille = el("div", { class: "perception" });
  for (const k of MESURES) {
    const bas = p ? L[K(`bas_${k}`)] / p : 0, haut = p ? L[K(`haut_${k}`)] / p : 0;
    grille.append(
      el("div", { class: "nom" }, el("h3", {}, TITRES[k]), el("p", {}, lignes[k])),
      repartition(bas, haut),
      el("div", { class: "resume" }, el("span", { class: "badge bas" }, `${pc(bas)} ${k === "tonalite" ? "hostiles" : "reproches"}`),
        el("span", { class: "badge haut" }, `${pc(haut)} ${k === "tonalite" ? "favorables" : "éloges"}`)));
  }
  $("perception").replaceChildren(
    el("div", { class: "tete" }, el("h2", {}, "Ce qu'on lui reproche, ce qu'on salue"),
      el("p", {}, `Sur les ${nombre(n)} commentaires qui parlent de lui${etat.poids ? ", pondérés par les « j'aime »" : ""}. En gris : ceux qui n'en disent rien.`)),
    grille,
    el("div", { class: "legende-rep" }, el("span", { style: { "--c": "var(--bas)" } }, `critique ou reproche (note ≤ ${BAS})`),
      el("span", { style: { "--c": "var(--milieu)" } }, "neutre ou pas évoqué"), el("span", { style: { "--c": "var(--haut)" } }, `éloge (note ≥ ${HAUT})`)));
}

// ---------- Évolution ----------

let zoneGraph, outils;
function evolution(sur, base) {
  if (!zoneGraph) {
    zoneGraph = el("div");
    const criteres = segments(Object.entries(TITRES), vue.critere, (v) => { vue.critere = v; calculer(); }, "Critère");
    const mode = segments([["parts", "Critiques et éloges"], ["moyenne", "Note moyenne"]], vue.mode, (v) => { vue.mode = v; calculer(); }, "Mesure");
    const pas = segments([["auto", "Auto"], ["semaine", "Semaines"], ["mois", "Mois"]], vue.pas, (v) => { vue.pas = v; calculer(); }, "Pas");
    outils = el("div", { class: "graph-outils" }, criteres.element, el("div", { class: "puces" }, mode.element, pas.element));
    $("evolution").replaceChildren(el("div", { class: "tete" }, el("h2", {}, "Évolution"),
      el("p", { id: "evolution-aide" })), outils, zoneGraph);
  }
  const k = vue.critere;
  const i0 = Math.max(1, periode[0]), i1 = periode[1];
  const pas = vue.pas === "auto" ? (i1 - i0 > 30 ? "mois" : "semaine") : vue.pas;
  const cle = (i) => (pas === "mois" ? S[i].slice(0, 7) : S[i]);
  const ordre = [], seaux = new Map();
  for (let i = i0; i <= i1; i++) if (!seaux.has(cle(i))) { seaux.set(cle(i), { debut: S[i], sur: [], base: [] }); ordre.push(cle(i)); }
  for (const c of k === "pertinence" ? base : sur) {
    if (c[0] < i0 || c[0] > i1) continue;
    seaux.get(cle(c[0]))[k === "pertinence" ? "base" : "sur"].push(c);
  }
  const points = ordre.map((q) => {
    const x = seaux.get(q), t = somme(k === "pertinence" ? x.base : x.sur), n = t[col.n], p = t[K("n")];
    const assez = n >= MIN_PAR_PERIODE;
    const valeurs = {};
    if (vue.mode === "moyenne") valeurs.moy = assez ? t[K(k)] / p : null;
    else if (k === "pertinence") valeurs.arg = assez ? (100 * t[K("argumentes")]) / p : null;
    else {
      valeurs.bas = assez ? (100 * t[K(`bas_${k}`)]) / p : null;
      valeurs.haut = assez ? (100 * t[K(`haut_${k}`)]) / p : null;
    }
    return { n, valeurs, debut: x.debut, moyenne: p ? t[K(k)] / p : null };
  });
  const series = vue.mode === "moyenne" ? [{ cle: "moy", nom: `${TITRES[k]} moyenne`, couleur: COULEURS.accent }]
    : k === "pertinence" ? [{ cle: "arg", nom: "argumentés", couleur: COULEURS.accent }]
    : [{ cle: "haut", nom: k === "tonalite" ? "favorables" : "éloges", couleur: COULEURS.haut },
       { cle: "bas", nom: k === "tonalite" ? "hostiles" : "reproches", couleur: COULEURS.bas }];
  const max = Math.max(0, ...points.flatMap((p) => Object.values(p.valeurs).filter((v) => v != null)));
  const [yMax, yPas] = vue.mode === "moyenne" ? [20, 5] : echelle(max);
  $("evolution-aide").textContent = (vue.mode === "moyenne"
    ? `Note moyenne de ${TITRES[k].toLowerCase()} sur 20, `
    : k === "pertinence" ? "Part des commentaires qui donnent au moins une raison, "
    : `Part des commentaires ${k === "tonalite" ? "favorables et hostiles" : `qui font un éloge ou un reproche sur ${TITRES[k].toLowerCase()}`}, `)
    + `par ${pas}${etat.poids ? ", pondérée par les « j'aime »" : ""}.`;
  if (!points.length) { zoneGraph.replaceChildren(el("p", { class: "vide" }, "Aucune période dans la sélection.")); return; }
  graphique(zoneGraph, {
    points, series, yMax, yPas, repere: vue.mode === "moyenne" ? 10 : null,
    formatY: (v, precis) => (vue.mode === "moyenne" ? (precis ? sur20(v) : String(v)) : `${precis ? Math.round(v) : v} %`),
    etiquetteX: (i) => {
      const d = points[i].debut, avant = points[i - 1]?.debut;
      if (pas === "mois") return moisCourt(d, i === 0 || d.slice(5, 7) === "01");
      if (avant && avant.slice(0, 7) === d.slice(0, 7)) return null;
      return moisCourt(d, i === 0 || d.slice(5, 7) === "01");
    },
    titreBulle: (i) => (pas === "mois" ? moisLong(points[i].debut) : `Semaine du ${dateCourte(points[i].debut)}`),
    lignesBulle: (i) => (vue.mode === "parts" && points[i].moyenne != null ? [[`${TITRES[k].toLowerCase()} moyenne`, `${sur20(points[i].moyenne)}/20`]] : []),
    description: `Évolution de ${TITRES[k].toLowerCase()} par ${pas}`,
  });
}

function echelle(max) {
  for (const pas of [2, 5, 10, 20, 25]) if (max <= pas * 5) return [Math.max(pas * Math.ceil((max * 1.08) / pas), pas * 2), pas];
  return [100, 25];
}

// ---------- Par compte ----------

function comptes(sur) {
  const par = new Map();
  for (const c of sur) {
    const x = par.get(c[1]) || new Array(cube.colonnes.length).fill(0);
    for (let j = col.n; j < c.length; j++) x[j] += c[j];
    par.set(c[1], x);
  }
  const lignes = [...par.entries()].filter(([, t]) => t[col.n] >= 10).sort((a, b) => b[1][col.n] - a[1][col.n]);
  const montrees = vue.tousComptes ? lignes : lignes.slice(0, 10);
  const grille = el("div", { class: "comptes" },
    el("div", { class: "entete-col" }, "Compte"), el("div", { class: "entete-col n" }, "Comment."),
    el("div", { class: "entete-col col-rep" }, "Hostiles · neutres · favorables"), el("div", { class: "entete-col moy" }, "Ton"));
  for (const [i, t] of montrees) {
    const k = cube.comptes[i], n = t[col.n], p = t[K("n")];
    const choisi = etat.comptes?.length === 1 && etat.comptes[0] === k.nom;
    grille.append(
      el("button", { type: "button", class: "nom-compte", title: choisi ? "Retirer ce filtre" : `Ne garder que ${k.nom}`, onclick: () => {
        etat.comptes = choisi ? null : [k.nom]; majCompte(); changer();
      } }, el("span", {}, k.nom), el("span", { class: "source-mini" }, `${SOURCES[k.source] || k.source} · ${GROUPES[k.groupe] || "Autres comptes"}`)),
      el("div", { class: "n" }, nombre(n)),
      el("div", { class: "col-rep" }, repartition(t[K("bas_tonalite")] / p, t[K("haut_tonalite")] / p, true)),
      el("div", { class: "moy", title: "tonalité moyenne sur 20" }, sur20(t[K("tonalite")] / p)));
  }
  $("comptes").replaceChildren(
    el("div", { class: "tete" }, el("h2", {}, "Selon le compte"),
      el("p", {}, "Ses propres comptes attirent surtout ses soutiens. Cliquer sur un compte pour ne garder que lui.")),
    lignes.length ? grille : el("p", { class: "vide" }, "Aucun compte dans la sélection."),
    lignes.length > 10 ? el("button", { type: "button", class: "bouton discret", style: { marginTop: "14px" }, onclick: () => { vue.tousComptes = !vue.tousComptes; comptes(choisir().sur); } },
      vue.tousComptes ? "Afficher moins" : `Afficher les ${lignes.length} comptes`) : null);
}

// ---------- Exemples ----------

const EXEMPLES = {
  critiques: ["Critiques argumentées", { tonalite: [0, BAS] }, "pertinent", "Les avis hostiles les plus argumentés."],
  soutiens: ["Soutiens argumentés", { tonalite: [HAUT, 20] }, "pertinent", "Les avis favorables les plus argumentés."],
  forme: ["Reproches : forme", { forme: [0, BAS] }, "forme", "Sur sa manière de parler et sa communication."],
  systeme: ["Reproches : système", { systeme: [0, BAS] }, "systeme", "Ceux qui le voient comme un homme du système."],
  idees: ["Reproches : idées", { idees: [0, BAS] }, "idees", "Les rejets de son programme ou de ses positions."],
};
const TRIS_EXEMPLES = { pertinent: "pertinence.desc", forme: "forme.asc,pertinence.desc", systeme: "systeme.asc,pertinence.desc", idees: "idees.asc,pertinence.desc" };

let zoneExemples, aideExemples, lienExemples, controleur;
function etatExemple() {
  const [, notes, tri] = EXEMPLES[vue.exemple];
  const e = { ...etatVide(), du: etat.du, au: etat.au, sources: etat.sources, groupes: etat.groupes, comptes: etat.comptes, type: etat.type, cible: "L" };
  e.notes = { ...e.notes, ...notes };
  if (etat.exploitables) e.notes.pertinence = [EXPLOITABLE, 20];
  e.tri = "pertinent";
  return { e, tri: TRIS_EXEMPLES[tri] };
}

async function chargerExemples() {
  if (!zoneExemples) {
    zoneExemples = el("div", { class: "exemples" });
    aideExemples = el("p", { class: "doux petit", style: { margin: "14px 0" } });
    lienExemples = el("a", { class: "bouton", style: { marginTop: "16px" } }, "Voir tous ces commentaires →");
    const onglets = segments(Object.entries(EXEMPLES).map(([k, v]) => [k, v[0]]), vue.exemple, (v) => { vue.exemple = v; chargerExemples(); }, "Exemples");
    $("exemples").replaceChildren(el("div", { class: "tete" }, el("h2", {}, "Exemples"),
      el("p", {}, "Cliquer sur un commentaire pour voir ses notes et la vidéo.")),
      onglets.element, aideExemples, zoneExemples, lienExemples);
  }
  aideExemples.textContent = EXEMPLES[vue.exemple][3];
  const { e, tri } = etatExemple();
  lienExemples.href = `commentaires.html?${versParametres(e, "commentaires")}`;
  controleur?.abort();
  controleur = new AbortController();
  zoneExemples.style.opacity = ".5";
  try {
    // Des internautes collent le même texte sous plusieurs posts : on n'en montre qu'un exemplaire.
    const vus = new Set(), lignes = [];
    for (const c of (await selection(versBase(e), { tri, limite: 40, signal: controleur.signal })).lignes) {
      const cle = c.texte.toLowerCase().replace(/^(@\S+\s*)+/, "").replace(/\W+/g, " ").trim().slice(0, 120);
      if (!vus.has(cle) && lignes.length < 6) { vus.add(cle); lignes.push(c); }
    }
    zoneExemples.replaceChildren(...(lignes.length ? lignes.map((c) => carte(c, { critere: EXEMPLES[vue.exemple][2] === "pertinent" ? "pertinence" : EXEMPLES[vue.exemple][2] }))
      : [el("p", { class: "vide" }, "Aucun commentaire de ce genre dans la sélection.")]));
  } catch (err) {
    if (err.name !== "AbortError") messageErreur(zoneExemples, err);
  }
  zoneExemples.style.opacity = "";
}
const chargerExemplesPlusTard = debounce(chargerExemples, 350);
