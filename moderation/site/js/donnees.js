// Les données du site, gardées dans le navigateur (IndexedDB) pour ménager la base gratuite :
// - premier passage : tout est téléchargé une fois (≈ 18 pages de 1 000 commentaires) ;
// - ensuite : seules les lignes écrites depuis la dernière fois (colonne maj), les retraits et les marques de suivi
//   sont redemandés ; quand rien n'a changé, chaque requête rend une liste vide en moins d'une milliseconde.
// Filtres, tris et comptages se font ici, sur l'ordinateur du modérateur. Tout est effacé à la déconnexion.
import { rest } from "./api.js";

const VERSION = 1;          // changer quand la forme des données change : tout est retéléchargé
const PAGE = 1000;          // lignes par requête (plafond de l'API Supabase)
const RECHARGER_JOURS = 7;  // filet de sécurité : tout retélécharger au-delà

const enc = encodeURIComponent;

// ── IndexedDB : une seule valeur, l'état complet ───────────────────────────────────────────────────────────
function ouvrir() {
  return new Promise((ok, ko) => {
    const r = indexedDB.open("moderation", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("cache");
    r.onsuccess = () => ok(r.result);
    r.onerror = () => ko(r.error);
  });
}
async function lireCache() {
  try {
    const db = await ouvrir();
    return await new Promise((ok) => {
      const q = db.transaction("cache").objectStore("cache").get("etat");
      q.onsuccess = () => ok(q.result || null);
      q.onerror = () => ok(null);
    });
  } catch { return null; }
}
async function ecrireCache(valeur) {
  try {
    const db = await ouvrir();
    await new Promise((ok) => {
      const t = db.transaction("cache", "readwrite");
      t.objectStore("cache").put(valeur, "etat");
      t.oncomplete = ok;
      t.onerror = ok;
    });
  } catch { /* navigation privée ou stockage plein : on retéléchargera la prochaine fois */ }
}
export function effacerCache() {
  try { indexedDB.deleteDatabase("moderation"); } catch { /* rien à effacer */ }
}

// ── État en mémoire ────────────────────────────────────────────────────────────────────────────────────────
export const etat = {
  lignes: new Map(),   // code → ligne de moderation_lignes
  pubs: new Map(),     // id → publication (moderation_pubs)
  suivi: new Map(),    // code → { etat, par, le }
  curseurs: { maj: null, code: null, retires: null, suivi: null, pub: 0 },
  complet: 0,          // heure du dernier téléchargement complet
  synchro: 0,          // heure de la dernière actualisation
};

/** Lit toutes les pages d'une requête triée, en suivant le curseur rendu par suite(ligne). */
async function pages(construire, suite, avancement) {
  const toutes = [];
  let curseur = null;
  for (;;) {
    const ls = await (await rest(construire(curseur))).json();
    toutes.push(...ls);
    if (avancement) avancement(toutes.length);
    if (ls.length < PAGE) return toutes;
    curseur = suite(ls[ls.length - 1]);
  }
}

async function lignesDepuis(maj, code, avancement) {
  const filtre = (m, c) => (m ? `&or=${enc(`(maj.gt."${m}",and(maj.eq."${m}",code.gt."${c}"))`)}` : "");
  let m = maj, c = code;
  const ls = await pages(
    (cur) => { if (cur) [m, c] = cur; return `moderation_lignes?select=*${filtre(m, c)}&order=maj.asc,code.asc&limit=${PAGE}`; },
    (l) => [l.maj, l.code], avancement);
  for (const l of ls) etat.lignes.set(l.code, l);
  if (ls.length) { etat.curseurs.maj = ls[ls.length - 1].maj; etat.curseurs.code = ls[ls.length - 1].code; }
  return ls.length;
}

async function suiviDepuis(le) {
  let depuis = le;
  const ls = await pages(
    (cur) => { if (cur) depuis = cur; return `moderation_suivi?select=code,etat,par,le${depuis ? `&le=gt.${enc(depuis)}` : ""}&order=le.asc&limit=${PAGE}`; },
    (l) => l.le);
  for (const s of ls) etat.suivi.set(s.code, { etat: s.etat, par: s.par, le: s.le });
  if (ls.length) etat.curseurs.suivi = ls[ls.length - 1].le;
  return ls.length;
}

async function retiresDepuis(le) {
  let depuis = le;
  const ls = await pages(
    (cur) => { if (cur) depuis = cur; return `moderation_retires?select=code,le&le=gt.${enc(depuis)}&order=le.asc&limit=${PAGE}`; },
    (l) => l.le);
  for (const r of ls) etat.lignes.delete(r.code);
  if (ls.length) etat.curseurs.retires = ls[ls.length - 1].le;
  return ls.length;
}

async function pubsDepuis(id) {
  let depuis = id;
  const ls = await pages(
    (cur) => { if (cur) depuis = cur; return `moderation_pubs?select=*&id=gt.${depuis}&order=id.asc&limit=${PAGE}`; },
    (p) => p.id);
  for (const p of ls) etat.pubs.set(p.id, p);
  if (ls.length) etat.curseurs.pub = ls[ls.length - 1].id;
  return ls.length;
}

async function toutTelecharger(avancement) {
  etat.lignes.clear(); etat.pubs.clear(); etat.suivi.clear();
  etat.curseurs = { maj: null, code: null, retires: null, suivi: null, pub: 0 };
  // Les retraits antérieurs ne comptent pas : on part de l'état actuel. Repère pris avant, pour ne rien manquer.
  const dernier = await (await rest("moderation_retires?select=le&order=le.desc&limit=1")).json();
  etat.curseurs.retires = dernier[0]?.le || "1970-01-01T00:00:00Z";
  await pubsDepuis(0);
  await lignesDepuis(null, null, avancement);
  await suiviDepuis(null);
  etat.complet = Date.now();
}

function sauver() {
  ecrireCache({
    version: VERSION, complet: etat.complet, synchro: etat.synchro, curseurs: etat.curseurs,
    lignes: [...etat.lignes.values()], pubs: [...etat.pubs.values()],
    suivi: [...etat.suivi].map(([code, s]) => ({ code, ...s })),
  });
}

/** Au démarrage : ce qui est déjà dans le navigateur (affichage immédiat), sinon rien. */
export async function charger() {
  const c = await lireCache();
  if (!c || c.version !== VERSION) return false;
  etat.lignes = new Map(c.lignes.map((l) => [l.code, l]));
  etat.pubs = new Map(c.pubs.map((p) => [p.id, p]));
  etat.suivi = new Map(c.suivi.map(({ code, ...s }) => [code, s]));
  etat.curseurs = c.curseurs;
  etat.complet = c.complet;
  etat.synchro = c.synchro;
  return true;
}

/** Met à jour depuis la base. seulementSuivi : juste les marques des autres modérateurs (le plus fréquent).
 *  Rend vrai si quelque chose a changé. */
export async function actualiser({ seulementSuivi = false, avancement } = {}) {
  let change = 0;
  if (!etat.complet || Date.now() - etat.complet > RECHARGER_JOURS * 864e5) {
    await toutTelecharger(avancement);
    change = 1;
  } else if (seulementSuivi) {
    change += await suiviDepuis(etat.curseurs.suivi);
  } else {
    change += await pubsDepuis(etat.curseurs.pub);
    change += await lignesDepuis(etat.curseurs.maj, etat.curseurs.code);
    change += await retiresDepuis(etat.curseurs.retires);
    change += await suiviDepuis(etat.curseurs.suivi);
  }
  etat.synchro = Date.now();
  if (change) sauver();
  return change > 0;
}

/** Une marque posée ici : gardée tout de suite, sans attendre la prochaine actualisation. */
export function noterSuivi(code, s) {
  etat.suivi.set(code, s);
  sauver();
}
