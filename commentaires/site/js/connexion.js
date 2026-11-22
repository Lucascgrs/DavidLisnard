// Accès par mot de passe (Supabase Auth, compte partagé des lecteurs, « python -m commentaires motdepasse »).
// Importé en premier par chaque page : tant que la connexion n'est pas faite, la page reste cachée et son script
// attend (await de premier niveau) ; aucune donnée n'est demandée. Sans session, la base ne rend rien (règles de
// commentaires/schema.sql) : ce module n'est qu'une porte d'entrée, la protection est dans la base.
import { SUPABASE_URL, SUPABASE_CLE, EMAIL } from "./config.js";

const STOCK = "analyse:session";

export class NonConnecte extends Error {}

function lire() {
  try { return JSON.parse(localStorage.getItem(STOCK) || "null"); } catch { return null; }
}
function garder(s) { localStorage.setItem(STOCK, JSON.stringify(s)); }
function oublier() {
  localStorage.removeItem(STOCK);
  try { for (const k of Object.keys(sessionStorage)) if (k.startsWith("synthese:")) sessionStorage.removeItem(k); } catch { /* indisponible */ }
}

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

async function connecter(motDePasse) {
  let s;
  try {
    s = await jeton("password", { email: EMAIL, password: motDePasse });
  } catch (e) {
    if (e.status === 400 || e.status === 401) throw new Error("Mot de passe incorrect.");
    if (e.status === 429) throw new Error("Trop d'essais : attendez quelques minutes.");
    throw new Error("Connexion impossible pour le moment. Réessayez dans un instant.");
  }
  if (contenu(s.acces).app_metadata?.role !== "lecteur") throw new Error("Ce compte n'a pas accès au site.");
  garder(s);
}

function deconnecter() {
  const s = lire();
  oublier();
  if (s) {
    fetch(`${SUPABASE_URL}/auth/v1/logout`, { method: "POST", headers: { apikey: SUPABASE_CLE, Authorization: `Bearer ${s.acces}` } })
      .catch(() => {});
  }
}

let enCours = null;
/** Le jeton d'accès de la session, renouvelé s'il va expirer ; NonConnecte s'il n'y a plus de session. */
export async function jetonAcces() {
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

/** La base a refusé la session (mot de passe changé, compte supprimé) : on la retire et on redemande le mot de passe. */
export function sessionRefusee() {
  oublier();
  location.reload();
}

function ecranConnexion() {
  return new Promise((fini) => {
    const forme = document.createElement("main");
    forme.className = "connexion";
    forme.innerHTML = `
      <form class="carte carte-connexion" autocomplete="on">
        <svg width="44" height="44" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" style="fill:var(--texte)"/><path d="M9 21v-4M14 21v-9M19 21v-6M24 21v-11" style="stroke:var(--fond)" stroke-width="3" stroke-linecap="round"/></svg>
        <h1>Lisnard vu par les commentaires</h1>
        <p class="doux">Accès réservé. Entrez le mot de passe du site.</p>
        <label for="mdp">Mot de passe</label>
        <input id="mdp" type="password" autocomplete="current-password" required>
        <button class="bouton plein" type="submit">Entrer</button>
        <p class="erreur" role="alert" hidden></p>
      </form>`;
    document.body.append(forme);
    const champ = forme.querySelector("#mdp");
    const erreur = forme.querySelector(".erreur");
    const bouton = forme.querySelector("button");
    champ.focus();
    forme.querySelector("form").addEventListener("submit", async (ev) => {
      ev.preventDefault();
      bouton.disabled = true;
      erreur.hidden = true;
      try {
        await connecter(champ.value);
        forme.remove();
        fini();
      } catch (e) {
        erreur.textContent = e.message;
        erreur.hidden = false;
        champ.select();
      } finally {
        bouton.disabled = false;
      }
    });
  });
}

function boutonDeconnexion() {
  const nav = document.querySelector(".entete .nav");
  if (!nav) return;
  const b = document.createElement("button");
  b.type = "button";
  b.className = "deconnexion";
  b.textContent = "Se déconnecter";
  b.addEventListener("click", () => { deconnecter(); location.reload(); });
  nav.after(b);
}

// La page attend ici : rien n'est montré ni demandé avant la connexion.
if (!lire()) await ecranConnexion();
document.documentElement.classList.remove("verrouille");
boutonDeconnexion();
