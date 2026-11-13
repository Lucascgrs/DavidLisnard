// Connexion (Supabase Auth, compte partagé des modérateurs) et lecture de la base avec la session ouverte.
// Sans session, aucune requête n'est faite ; avec une session sans le rôle « moderateur », la base ne rend rien
// (règles de web/schema.sql).
import { SUPABASE_URL, SUPABASE_CLE, EMAIL } from "./config.js";

const STOCK = "moderation:session";

export class NonConnecte extends Error {}

function lire() {
  try { return JSON.parse(localStorage.getItem(STOCK) || "null"); } catch { return null; }
}
function garder(s) { localStorage.setItem(STOCK, JSON.stringify(s)); }
function oublier() { localStorage.removeItem(STOCK); }

/** Le contenu du jeton (sans vérification : c'est la base qui vérifie). */
function contenu(jwt) {
  try {
    const b = jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(escape(atob(b))));
  } catch { return {}; }
}

async function jeton(type, corps) {
  const r = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=${type}`, {
    method: "POST", headers: { apikey: SUPABASE_CLE, "Content-Type": "application/json" }, body: JSON.stringify(corps),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) {
    const e = new Error(d.error_description || d.msg || d.message || `erreur ${r.status}`);
    e.status = r.status;
    throw e;
  }
  return { acces: d.access_token, renouv: d.refresh_token, expire: (d.expires_at ? d.expires_at * 1000 : Date.now() + d.expires_in * 1000) };
}

export function connecte() { return !!lire(); }

export async function connecter(motDePasse) {
  let s;
  try {
    s = await jeton("password", { email: EMAIL, password: motDePasse });
  } catch (e) {
    if (e.status === 400 || e.status === 401) throw new Error("Mot de passe incorrect.");
    if (e.status === 429) throw new Error("Trop d'essais : attendez quelques minutes.");
    throw new Error("Connexion impossible pour le moment. Réessayez dans un instant.");
  }
  if (contenu(s.acces).app_metadata?.role !== "moderateur") throw new Error("Ce compte n'a pas accès à la modération.");
  garder(s);
}

export function deconnecter() {
  const s = lire();
  oublier();
  if (s) {
    fetch(`${SUPABASE_URL}/auth/v1/logout`, { method: "POST", headers: { apikey: SUPABASE_CLE, Authorization: `Bearer ${s.acces}` } })
      .catch(() => {});
  }
}

let enCours = null;
async function acces() {
  const s = lire();
  if (!s) throw new NonConnecte();
  if (Date.now() < s.expire - 60_000) return s.acces;
  enCours ??= jeton("refresh_token", { refresh_token: s.renouv })
    .then((n) => { garder(n); return n.acces; })
    .catch((e) => {
      if (e.status >= 400 && e.status < 500) { oublier(); throw new NonConnecte(); }
      throw e;
    })
    .finally(() => { enCours = null; });
  return enCours;
}

/** Une requête à l'API de la base (PostgREST). chemin : « moderation_site?select=*… ». */
export async function rest(chemin, { methode = "GET", corps, entetes = {} } = {}) {
  const jet = await acces();
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${chemin}`, {
    method: methode,
    headers: { apikey: SUPABASE_CLE, Authorization: `Bearer ${jet}`, ...(corps ? { "Content-Type": "application/json" } : {}), ...entetes },
    body: corps ? JSON.stringify(corps) : undefined,
  });
  if (r.status === 401 || r.status === 403) { oublier(); throw new NonConnecte(); }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r;
}

/** Pose une marque de suivi ; rend l'heure d'enregistrement donnée par la base. */
export async function suivre(cle, etat, par) {
  const r = await rest("rpc/suivre", { methode: "POST", corps: { _cle: cle, _etat: etat, _par: par || null } });
  return r.json();
}
