// Lecture des données dans Supabase (lecture seule, clé publique). Les filtres sont appliqués par la base :
// fonctions selection(f) et evolution(f) de web/schema.sql.
import { SUPABASE_URL, SUPABASE_CLE } from "./config.js";

const REST = `${SUPABASE_URL}/rest/v1`;
const ENTETES = SUPABASE_CLE.startsWith("sb_")
  ? { apikey: SUPABASE_CLE }
  : { apikey: SUPABASE_CLE, Authorization: `Bearer ${SUPABASE_CLE}` };
// Modèle normalisé (web/schema.sql) : source, compte et groupe se lisent par la publication. remettre() redonne à
// chaque commentaire la forme qu'attendent les pages (cle « source:code », source, compte, groupe, parent).
const CHAMPS = "source:sources(nom),code,date,semaine,reponse,parent,likes,mots,texte,tonalite,forme,systeme,idees,"
  + "pertinence,cible,fiabilite,publications(titre,lien,code,date,comptes(nom,groupe))";

function remettre(c) {
  const source = c.source?.nom;
  const pub = c.publications || {};
  return {
    ...c, source, cle: `${source}:${c.code}`, compte: pub.comptes?.nom, groupe: pub.comptes?.groupe,
    parent: c.parent ? `${source}:${c.parent}` : null,
    publications: { titre: pub.titre, lien: pub.lien, code: pub.code, date: pub.date },
  };
}

async function demander(chemin, { methode = "GET", corps, entetes = {}, signal } = {}) {
  const r = await fetch(`${REST}/${chemin}`, {
    method: methode, signal,
    headers: { ...ENTETES, ...(corps ? { "Content-Type": "application/json" } : {}), ...entetes },
    body: corps ? JSON.stringify(corps) : undefined,
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r;
}

const memoire = new Map();

/** « meta » ou « cube », calculés à la publication (web/export.py). Gardés le temps de la visite. */
export function synthese(nom) {
  if (!memoire.has(nom)) {
    memoire.set(nom, (async () => {
      const cle = `synthese:${nom}`;
      try {
        const garde = JSON.parse(sessionStorage.getItem(cle) || "null");
        if (garde && Date.now() - garde.t < 10 * 60 * 1000) return garde.d;
      } catch { /* stockage indisponible : on relit */ }
      const r = await demander(`syntheses?nom=eq.${nom}&select=donnees`);
      const d = (await r.json())[0]?.donnees;
      if (!d) throw new Error(`synthèse ${nom} absente`);
      try { sessionStorage.setItem(cle, JSON.stringify({ t: Date.now(), d })); } catch { /* trop gros ou interdit */ }
      return d;
    })().catch((e) => { memoire.delete(nom); throw e; }));
  }
  return memoire.get(nom);
}

/** Une page de commentaires de la sélection. tri : « date.desc », « pertinence.desc »… */
export async function selection(filtre, { tri = "date.desc.nullslast", limite = 30, decalage = 0, compter = false, signal } = {}) {
  const ordre = tri.includes("date") ? tri : `${tri},likes.desc,date.desc.nullslast`;
  const r = await demander(`rpc/selection?select=${CHAMPS}&order=${ordre}&limit=${limite}&offset=${decalage}`, {
    methode: "POST", corps: filtre, signal, entetes: compter ? { Prefer: "count=exact" } : {},
  });
  const lignes = (await r.json()).map(remettre);
  const plage = r.headers.get("Content-Range");
  return { lignes, total: plage ? Number(plage.split("/")[1]) : null };
}

export async function evolution(filtre, signal) {
  const r = await demander("rpc/evolution", { methode: "POST", corps: filtre, signal });
  return r.json();
}

export async function commentaire(cle) {
  const r = await demander(`rpc/commentaire?select=${CHAMPS}`, { methode: "POST", corps: { cle } });
  const c = (await r.json())[0];
  return c ? remettre(c) : null;
}
