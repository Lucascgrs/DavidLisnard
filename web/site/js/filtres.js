// L'état des filtres, partagé par les pages Statistiques et Commentaires : lu et écrit dans l'adresse (liens
// partageables, « voir ces commentaires » d'une page à l'autre), et traduit en filtre pour la base.
import { CRITERES } from "./commun.js";

const COURTS = { tonalite: "ton", forme: "forme", systeme: "sys", idees: "idees", pertinence: "pert" };
export const TOUTES_NOTES = () => Object.fromEntries(CRITERES.map((k) => [k, [0, 20]]));

export function etatVide() {
  return { du: null, au: null, sources: null, groupes: null, comptes: null, type: "tous", cible: null, q: "",
    notes: TOUTES_NOTES(), fiab: "toutes", tri: "recent", exploitables: true };
}

export function lireAdresse() {
  const p = new URL(location.href).searchParams;
  const e = etatVide();
  const liste = (k) => (p.get(k) ? p.get(k).split(",").filter(Boolean) : null);
  e.du = p.get("du"); e.au = p.get("au");
  e.sources = liste("src"); e.groupes = liste("grp");
  e.comptes = p.getAll("compte").length ? p.getAll("compte") : null;
  if (["principal", "reponse"].includes(p.get("type"))) e.type = p.get("type");
  if (["L", "A"].includes(p.get("cible"))) e.cible = p.get("cible");
  e.q = p.get("q") || "";
  for (const k of CRITERES) {
    const m = /^(\d+)-(\d+)$/.exec(p.get(COURTS[k]) || "");
    if (m) e.notes[k] = [Math.min(20, +m[1]), Math.min(20, +m[2])];
  }
  if (["bm", "bonne"].includes(p.get("fiab"))) e.fiab = p.get("fiab");
  if (p.get("tri")) e.tri = p.get("tri");
  if (p.get("expl") === "0") e.exploitables = false;
  return e;
}

/** Paramètres d'adresse ; `pour` = "commentaires" ou "statistiques" (chacune ne garde que ce qu'elle comprend). */
export function versParametres(e, pour) {
  const p = new URLSearchParams();
  if (e.du) p.set("du", e.du);
  if (e.au) p.set("au", e.au);
  if (e.sources) p.set("src", e.sources.join(","));
  if (e.groupes) p.set("grp", e.groupes.join(","));
  for (const c of e.comptes || []) p.append("compte", c);
  if (e.type !== "tous") p.set("type", e.type);
  if (pour === "statistiques") {
    if (!e.exploitables) p.set("expl", "0");
    return p;
  }
  if (e.cible) p.set("cible", e.cible);
  if (e.q) p.set("q", e.q);
  for (const k of CRITERES) if (e.notes[k][0] > 0 || e.notes[k][1] < 20) p.set(COURTS[k], e.notes[k].join("-"));
  if (e.fiab !== "toutes") p.set("fiab", e.fiab);
  if (e.tri !== "recent") p.set("tri", e.tri);
  return p;
}

export function ecrireAdresse(e, pour) {
  const u = new URL(location.href);
  const garde = u.searchParams.get("c");
  u.search = versParametres(e, pour).toString();
  if (garde) u.searchParams.set("c", garde);
  history.replaceState(null, "", u);
}

/** Filtre pour selection(f) / evolution(f) de la base (web/schema.sql). */
export function versBase(e) {
  const f = {};
  if (e.du) f.du = e.du;
  if (e.au) f.au = e.au;
  if (e.sources) f.sources = e.sources;
  if (e.groupes) f.groupes = e.groupes;
  if (e.comptes?.length) f.comptes = e.comptes;
  if (e.type !== "tous") f.reponse = e.type === "reponse";
  if (e.cible) f.cible = e.cible;
  if (e.q.trim()) f.q = e.q.trim();
  for (const k of CRITERES) if (e.notes[k][0] > 0 || e.notes[k][1] < 20) f[k] = e.notes[k];
  if (e.fiab === "bm") f.fiabilites = ["bonne", "moyenne", "corrigée"];
  if (e.fiab === "bonne") f.fiabilites = ["bonne", "corrigée"];
  return f;
}

export const TRIS = {
  recent: ["Plus récents", "date.desc.nullslast"],
  ancien: ["Plus anciens", "date.asc.nullslast"],
  pertinent: ["Plus argumentés", "pertinence.desc"],
  favorable: ["Plus favorables", "tonalite.desc,pertinence.desc"],
  hostile: ["Plus hostiles", "tonalite.asc,pertinence.desc"],
  aime: ["Plus aimés", "likes.desc"],
};
