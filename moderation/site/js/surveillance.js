// Mots surveillés (liste de moderation/mots_surveilles.txt, écrite dans mots.js au déploiement) : un simple filtre,
// sans lien avec le modèle. Chaque commentaire est découpé en mots ; un mot de la liste est trouvé quand ses mots se
// suivent dans le commentaire. La comparaison ignore majuscules, accents, lettres répétées (« connnard ») et les
// chiffres ou signes qui déguisent une lettre (« c0nnard », « s@lope »). « mot* » : tout mot qui commence ainsi.
import { MOTS } from "./mots.js";

const DEGUISES = { 0: "o", 1: "i", 3: "e", 4: "a", 5: "s", 7: "t", "@": "a", $: "s" };
const MOT = /[\p{L}\p{N}@$]+/gu;

/** Forme comparable d'un mot : sans accents ni majuscules, chiffres déguisés remplacés, lettres répétées réduites. */
export function forme(mot) {
  return mot.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()
    .replace(/[013457@$]/g, (x) => DEGUISES[x]).replace(/(.)\1+/g, "$1");
}

// La liste, préparée une fois : chaque entrée en mots ; « * » final = préfixe sur le dernier mot.
const ENTREES = MOTS.map(({ mot, rubrique }) => {
  const prefixe = mot.endsWith("*");
  const mots = (mot.replace(/\*$/, "").match(MOT) || []).map(forme);
  return { mot: mot.replace(/\*$/, ""), rubrique, mots, prefixe };
}).filter((e) => e.mots.length);
const PAR_PREMIER = new Map();   // premier mot exact → entrées
const PREFIXES = [];             // entrées d'un seul mot en préfixe (cherchées sur chaque mot)
for (const e of ENTREES) {
  if (e.prefixe && e.mots.length === 1) PREFIXES.push(e);
  else {
    if (!PAR_PREMIER.has(e.mots[0])) PAR_PREMIER.set(e.mots[0], []);
    PAR_PREMIER.get(e.mots[0]).push(e);
  }
}
export const RUBRIQUES = [...new Set(ENTREES.map((e) => e.rubrique).filter(Boolean))];
export const NB_MOTS = ENTREES.length;

function correspond(e, toks, i) {
  if (i + e.mots.length > toks.length) return false;
  for (let k = 0; k < e.mots.length; k++) {
    const dernier = k === e.mots.length - 1;
    const t = toks[i + k].f;
    if (dernier && e.prefixe ? !t.startsWith(e.mots[k]) : t !== e.mots[k]) return false;
  }
  return true;
}

/** Les mots surveillés trouvés dans un texte : [{ debut, fin, mot, rubrique }] (positions dans le texte d'origine),
 *  sans chevauchement (le plus long l'emporte). */
export function trouver(texte) {
  if (!texte || !ENTREES.length) return [];
  const toks = [...texte.matchAll(MOT)].map((m) => ({ debut: m.index, fin: m.index + m[0].length, f: forme(m[0]) }));
  const trouves = [];
  for (let i = 0; i < toks.length; i++) {
    let meilleur = null;
    for (const e of PAR_PREMIER.get(toks[i].f) || []) {
      if ((!meilleur || e.mots.length > meilleur.mots.length) && correspond(e, toks, i)) meilleur = e;
    }
    if (!meilleur) for (const e of PREFIXES) if (toks[i].f.startsWith(e.mots[0])) { meilleur = e; break; }
    if (meilleur) {
      const j = i + meilleur.mots.length - 1;
      trouves.push({ debut: toks[i].debut, fin: toks[j].fin, mot: meilleur.mot, rubrique: meilleur.rubrique });
      i = j;
    }
  }
  return trouves;
}

/** Le texte en nœuds DOM, mots trouvés dans <mark> : le texte reste du texte (jamais interprété en HTML). */
export function surligner(texte, trouves) {
  const morceaux = [];
  let pos = 0;
  for (const t of trouves) {
    if (t.debut > pos) morceaux.push(document.createTextNode(texte.slice(pos, t.debut)));
    const m = document.createElement("mark");
    m.textContent = texte.slice(t.debut, t.fin);
    m.title = `Mot surveillé : ${t.mot}${t.rubrique ? ` (${t.rubrique})` : ""}`;
    morceaux.push(m);
    pos = t.fin;
  }
  if (pos < texte.length) morceaux.push(document.createTextNode(texte.slice(pos)));
  return morceaux;
}
