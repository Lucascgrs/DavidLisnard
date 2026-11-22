// Site de modération : connexion, puis quatre vues (commentaires, auteurs, publications, statistiques).
// Les données sont gardées dans le navigateur (donnees.js) : filtres, tris et comptages se font ici, sans requête.
// La base n'est interrogée que pour les nouveautés (au démarrage et au bouton « Actualiser »), pour les marques des
// autres modérateurs (toutes les 10 s, page visible) et pour enregistrer une marque. Tout texte venu de Facebook est posé en textContent, jamais en HTML.
// La base rend les commentaires de tous les groupes Facebook ; le filtre « Groupes » (en haut, pour toutes les vues) choisit
// ceux qui sont montrés, « Cap 2027 avec David Lisnard » par défaut. Seul ce groupe est rangé par thème (réponses préparées).
import { NonConnecte, connecte, connecter, deconnecter, suivre } from "./api.js";
import { actualiser, charger, effacerCache, etat, marquesRecentes, noterSuivi } from "./donnees.js";
import { RUBRIQUES, surligner, trouver } from "./surveillance.js";
import { vueStats } from "./stats.js";
import { fermerReponses, nombreReponses, nomTheme, ouvrirReponses, reponsesDu, themesActifs, themesDu } from "./reponses.js";

const PAGE = 50;                    // cartes affichées à la fois (affichage seulement : tout est déjà là)
const SUIVI_S = 10;                 // marques des autres modérateurs : toutes les 10 s, page visible
// Nouveaux commentaires : à l'ouverture et au bouton « Actualiser » seulement (collecte : quelques fois par jour).
const VUES = ["commentaires", "auteurs", "publications", "stats"];
const $ = (id) => document.getElementById(id);
const CATEGORIES = { insultant: "Insultant", question: "Question", autre: "Autre" };
const SUIVIS = { traite: "Traité", sans_suite: "Sans suite" };
const GROUPE_DEFAUT = "Cap 2027 avec David Lisnard";  // groupe choisi par défaut, le seul rangé par thème (moderation/reponses.py)
const SEP = "|";                    // séparateur des groupes choisis dans l'adresse

// ── Petits outils ────────────────────────────────────────────────────────────────────────────────────────────
function el(balise, attrs = {}, ...enfants) {
  const n = document.createElement(balise);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const e of enfants.flat()) if (e != null && e !== false) n.append(e instanceof Node ? e : String(e));
  return n;
}
const nombre = (n) => (n ?? 0).toLocaleString("fr-FR");
const pourcent = (p) => (p == null ? "" : `${Math.round(p * 100)} %`);
// Les dates de la base sont en temps universel ; celles sans fuseau aussi.
const enDate = (s) => (s ? new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s.replace(" ", "T") + "Z") : null);
function quand(s) {
  const d = typeof s === "number" ? new Date(s) : enDate(s);
  if (!d) return "";
  const min = (Date.now() - d) / 60000;
  if (min < 1) return "à l'instant";
  if (min < 60) return `il y a ${Math.round(min)} min`;
  if (min < 60 * 24) return `il y a ${Math.round(min / 60)} h`;
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: d.getFullYear() === new Date().getFullYear() ? undefined : "numeric" });
}
const dateLongue = (s) => enDate(s)?.toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) ?? "";
const facebook = (url) => (typeof url === "string" && /^https:\/\/(www\.)?facebook\.com\//.test(url) ? url : null);
const profil = (id) => (id ? `https://www.facebook.com/${/^\d+$/.test(id) ? `profile.php?id=${id}` : encodeURIComponent(id)}` : null);
const ficheGroupe = (chemin, id) => (chemin && id ? `https://www.facebook.com/groups/${encodeURIComponent(chemin)}/user/${encodeURIComponent(id)}/` : null);
const raccourci = (t, n) => (t && t.length > n ? t.slice(0, n - 1) + "…" : t);
// Recherche sans accents ni majuscules ; tous les mots doivent y être.
const normal = (s) => (s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const mots = (s) => normal(s).split(/\s+/).filter(Boolean);
const contientTout = (texte, liste) => liste.every((m) => texte.includes(m));
function attendre(fn, ms = 250) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
function message(texte) {
  const m = $("message");
  m.textContent = texte;
  m.hidden = false;
  clearTimeout(message.t);
  message.t = setTimeout(() => { m.hidden = true; }, 3500);
}
function prenom() { return localStorage.getItem("moderation:prenom") || ""; }

// ── Données préparées (recalculées après chaque actualisation) ──────────────────────────────────────────────
let commentaires = [];       // objets prêts à afficher
let auteurs = new Map();     // auteur_id → bilan
let publications = new Map(); // id → bilan
const suiviDe = (c) => etat.suivi.get(c.code)?.etat || "a_traiter";

let parGroupe = [];          // [groupe, nombre de commentaires], du plus gros au plus petit (tous groupes)
const groupesChoisis = () => new Set(f.groupes ? f.groupes.split(SEP) : []);

function preparer() {
  auteurs = new Map();
  publications = new Map();
  commentaires = [];
  const choisis = groupesChoisis();
  const compte = new Map();
  for (const l of etat.lignes.values()) {
    const pub = etat.pubs.get(l.publication) || null;
    if (pub?.groupe) compte.set(pub.groupe, (compte.get(pub.groupe) || 0) + 1);
    if (pub?.groupe && !choisis.has(pub.groupe)) continue;
    const lien = facebook(pub?.lien)
      ? pub.lien + (l.parent ? `?comment_id=${l.parent}&reply_comment_id=${l.code}` : `?comment_id=${l.code}`) : null;
    const c = { ...l, cle: `facebook:${l.code}`, categorie: l.categorie || "autre", pub, lien, t: enDate(l.date)?.getTime() ?? 0,
      mots: trouver(l.texte) };
    // Catégorie vérifiée à la lecture (annotation) : sûre à 100 %, pour l'affichage, les tris et le filtre de certitude.
    if (l.verifie) Object.assign(c, { pi: 0, pq: 0, pa: 0, [{ insultant: "pi", question: "pq", autre: "pa" }[c.categorie]]: 1 });
    commentaires.push(c);
    if (l.auteur_id) {
      const a = auteurs.get(l.auteur_id) || { auteur_id: l.auteur_id, auteur: l.auteur, n: 0, insultants: 0, questions: 0, mots: 0, dernier: 0, groupes: {}, liste: [] };
      a.n++; a.liste.push(c);
      if (c.categorie === "insultant") a.insultants++;
      if (c.categorie === "question") a.questions++;
      if (c.mots.length) a.mots++;
      if (c.t > a.dernier) a.dernier = c.t;
      if (pub?.groupe) a.groupes[pub.groupe] = pub.chemin;
      auteurs.set(l.auteur_id, a);
    }
    if (pub) {
      const p = publications.get(pub.id) || { ...pub, n: 0, insultants: 0, questions: 0, dernier: 0, liste: [] };
      p.n++; p.liste.push(c);
      if (c.categorie === "insultant") p.insultants++;
      if (c.categorie === "question") p.questions++;
      if (c.t > p.dernier) p.dernier = c.t;
      publications.set(pub.id, p);
    }
  }
  for (const c of commentaires) c.a = c.auteur_id ? auteurs.get(c.auteur_id) : null;
  parGroupe = [...compte].sort((a, b) => b[1] - a[1]);
}
const aTraiter = (liste, cats) => liste.reduce((s, c) => s + (cats.includes(c.categorie) && suiviDe(c) === "a_traiter" ? 1 : 0), 0);

// ── État des filtres (gardé dans l'adresse de la page, pour la partager) ─────────────────────────────────────
const DEFAUT = { vue: "commentaires", categorie: "insultant", theme: "", mots: "", rubrique: "", certitude: "", suivi: "a_traiter",
  periode: "", du: "", au: "", texte: "", auteur: "", publication: "", auteur_id: "", auteur_nom: "", publication_id: "",
  publication_nom: "", tri: "date", s_periode: "91", groupes: GROUPE_DEFAUT };
let f = { ...DEFAUT };

function lireAdresse() {
  const p = new URLSearchParams(location.hash.slice(1));
  f = { ...DEFAUT };
  for (const k of Object.keys(DEFAUT)) if (p.has(k)) f[k] = p.get(k);
  if (!VUES.includes(f.vue)) f.vue = DEFAUT.vue;
}
function ecrireAdresse() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) if (v !== DEFAUT[k]) p.set(k, v);
  history.replaceState(null, "", "#" + p.toString());
}

// ── Connexion ────────────────────────────────────────────────────────────────────────────────────────────────
function ecranConnexion(texte) {
  $("ecran-site").hidden = true;
  $("ecran-connexion").hidden = false;
  $("prenom").value = prenom();
  const e = $("erreur-connexion");
  e.hidden = !texte;
  e.textContent = texte || "";
  $("mdp").focus();
}

$("form-connexion").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const bouton = ev.submitter;
  bouton.disabled = true;
  try {
    await connecter($("mdp").value);
    localStorage.setItem("moderation:prenom", $("prenom").value.trim());
    $("mdp").value = "";
    demarrer();
  } catch (e) {
    ecranConnexion(e.message);
  } finally {
    bouton.disabled = false;
  }
});

// Déconnexion : la session et les données gardées dans ce navigateur sont effacées.
$("deconnexion").addEventListener("click", () => {
  deconnecter();
  fermerReponses();
  effacerCache();
  etat.lignes.clear(); etat.pubs.clear(); etat.suivi.clear(); etat.reponses.clear(); etat.themesRep.clear(); etat.complet = 0;
  commentaires = [];
  ecranConnexion();
});

function echec(e) {
  if (e instanceof NonConnecte) return ecranConnexion("Session terminée : entrez de nouveau le mot de passe.");
  console.error(e);
  message("La base ne répond pas pour le moment ; les données affichées sont celles déjà chargées.");
}

// ── Actualisation ────────────────────────────────────────────────────────────────────────────────────────────
let enCours = false, marquesEnCours = false;
async function synchroniser() {
  if (enCours) return;
  enCours = true;
  $("actualiser").disabled = true;
  const premiere = !etat.complet;
  try {
    const change = await actualiser({
      // Reste affiché pendant tout le chargement (majEtatDonnees ne l'efface plus tant qu'il dure).
      avancement: (n) => { $("etat-donnees").textContent = `${premiere ? "Premier chargement" : "Mise à jour"} : ${nombre(n)} commentaires…`; },
    });
    if (change || premiere) { preparer(); afficher({ garderPosition: !premiere }); }
  } catch (e) {
    echec(e);
  } finally {
    enCours = false;
    $("actualiser").disabled = false;
    majEtatDonnees();
  }
}
function majEtatDonnees() {
  if (enCours) return;  // un chargement est en cours : son compteur reste affiché
  $("etat-donnees").textContent = etat.synchro ? `À jour ${quand(etat.synchro)}` : "";
}
$("actualiser").addEventListener("click", () => synchroniser());

// Marques des autres modérateurs : les cartes affichées changent sur place (couleur, « Traité par … ») sans être
// retirées de la liste, pour que rien ne saute sous les yeux de celui qui lit ; la liste se refiltre au prochain
// changement de filtre ou d'onglet. Les compteurs du haut, eux, sont recalculés tout de suite.
async function suivreLesAutres() {
  if (marquesEnCours || enCours || !etat.complet || document.hidden || !connecte() || $("ecran-site").hidden) return;
  marquesEnCours = true;
  try {
    const codes = new Set(await marquesRecentes());
    if (!codes.size) return;
    for (const carte of document.querySelectorAll("article.commentaire")) if (codes.has(carte.dataset.code)) carte.poser?.();
    tuiles();
    if (f.vue === "stats") vueStatistiques();
  } catch (e) {
    if (e instanceof NonConnecte) echec(e); else console.warn(e);  // réseau coupé : on réessaiera dans 10 s
  } finally {
    marquesEnCours = false;
  }
}
setInterval(() => { majEtatDonnees(); suivreLesAutres(); }, SUIVI_S * 1000);
document.addEventListener("visibilitychange", () => suivreLesAutres());

// ── Compteurs du haut ────────────────────────────────────────────────────────────────────────────────────────
function tuiles() {
  const tuile = (classe, chiffre, libelle, regler, icone) => el("button", {
    type: "button", class: `tuile ${classe}`,
    // Un clic garde les autres filtres et ne change que ceux de la tuile.
    onclick: () => { f = { ...f, categorie: "", certitude: "", suivi: "a_traiter", mots: "", rubrique: "", ...regler, vue: "commentaires" }; afficher(); },
  }, el("span", { class: "icone", "aria-hidden": "true" }, icone), el("span", { class: "chiffre" }, nombre(chiffre)), el("span", { class: "libelle" }, libelle));
  // Les chiffres suivent les filtres en cours (groupes, période, thème, recherches, auteur, publication).
  const vus = filtrer({ pourTuiles: true });
  const avecMots = vus.filter((c) => c.mots.length && suiviDe(c) === "a_traiter").length;
  $("tuiles").replaceChildren(
    tuile("insultant", aTraiter(vus, ["insultant"]), "insultants à traiter", { categorie: "insultant" }, "!"),
    tuile("question", aTraiter(vus, ["question"]), "questions à traiter", { categorie: "question" }, "?"),
    tuile("mots", avecMots, "mots surveillés à traiter", { mots: "oui" }, "⚑"),
    tuile("ok", vus.filter((c) => suiviDe(c) === "traite").length, "marqués « traité »", { suivi: "traite" }, "✓"),
  );
}

// ── Filtre des groupes (pour toutes les vues) ────────────────────────────────────────────────────────────────
function listeGroupes() {
  const choisis = groupesChoisis();
  $("f-groupes").replaceChildren(...parGroupe.map(([g, n]) => el("label", {},
    el("input", { type: "checkbox", value: g, checked: choisis.has(g), onchange: (ev) => {
      const s = groupesChoisis();
      if (ev.target.checked) s.add(g); else s.delete(g);
      f.groupes = [...s].join(SEP);
      preparer();
      afficher();
    } }),
    el("span", {}, g), el("span", { class: "n" }, nombre(n)))));
  $("note-groupes").hidden = !parGroupe.length;
}

// ── Menu de l'auteur ─────────────────────────────────────────────────────────────────────────────────────────
function menuAuteur(ancre, { nom, id, groupes }) {
  const m = $("menu");
  const lienMenu = (href, titre, detail) => href && el("a", { href, target: "_blank", rel: "noopener noreferrer", role: "menuitem" },
    titre, " ↗", detail && el("small", {}, detail));
  m.replaceChildren(
    el("div", { class: "entete-menu" }, nom || "Auteur inconnu"),
    lienMenu(profil(id), "Voir son profil Facebook"),
    ...Object.entries(groupes || {}).filter(([, ch]) => ch).map(([g, ch]) =>
      lienMenu(ficheGroupe(ch, id), `Sa fiche dans « ${raccourci(g, 34)} »`, "Administrateurs : « … » → Retirer du groupe, Bloquer, Mettre en sourdine")),
    id && el("button", { type: "button", role: "menuitem", onclick: () => {
      fermerMenu();
      f = { ...DEFAUT, groupes: f.groupes, vue: "commentaires", categorie: "", suivi: "", auteur_id: id, auteur_nom: nom || id };
      afficher();
    } }, "Tous ses commentaires ici"),
    nom && el("button", { type: "button", role: "menuitem", onclick: () => {
      fermerMenu();
      navigator.clipboard?.writeText(nom).then(() => message("Nom copié."), () => {});
    } }, "Copier son nom"),
  );
  m.hidden = false;
  const r = ancre.getBoundingClientRect();
  const largeur = m.offsetWidth;
  m.style.left = `${Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - largeur - 8))}px`;
  m.style.top = `${window.scrollY + r.bottom + 4}px`;
  m.querySelector("a, button")?.focus();
}
function fermerMenu() { $("menu").hidden = true; }
document.addEventListener("click", (e) => { if (!e.target.closest("#menu, .auteur")) fermerMenu(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") fermerMenu(); });

function boutonAuteur(nom, id, groupes) {
  return el("button", { type: "button", class: "auteur", "aria-haspopup": "menu",
    onclick: (ev) => { ev.stopPropagation(); menuAuteur(ev.currentTarget, { nom, id, groupes }); } }, nom || "Auteur inconnu");
}

// Bouton « afficher la suite » commun aux trois vues : la liste est déjà calculée, on n'en montre qu'une partie.
function suite(zone, cible, liste, faire, libelle) {
  let vus = 0;
  const montrer = () => {
    cible.append(...liste.slice(vus, vus + PAGE).map(faire));
    vus = Math.min(vus + PAGE, liste.length);
    zone.replaceChildren(vus < liste.length
      ? el("button", { type: "button", class: "bouton", onclick: montrer }, `${libelle} (${nombre(liste.length - vus)} restants)`)
      : vus > PAGE ? el("span", {}, "Fin de la liste.") : "");
  };
  montrer();
}

// ── Vue Commentaires ─────────────────────────────────────────────────────────────────────────────────────────
// pourTuiles : les compteurs du haut suivent tous les filtres (groupes, période, thème, recherches, auteur,
// publication) sauf ceux que fixe une tuile (catégorie, certitude, suivi, mots surveillés), sans quoi elles se
// videraient l'une l'autre.
function filtrer({ pourTuiles = false } = {}) {
  const du = f.du ? Date.parse(f.du + "T00:00:00Z") : f.periode ? Date.now() - Number(f.periode) * 864e5 : null;
  const au = f.au ? Date.parse(f.au + "T00:00:00Z") + 864e5 : null;
  const mt = mots(f.texte), ma = mots(f.auteur), mp = mots(f.publication);
  const certitude = !pourTuiles && f.categorie && f.certitude ? Number(f.certitude) : null;
  const cleP = { insultant: "pi", question: "pq", autre: "pa" }[f.categorie];
  const liste = commentaires.filter((c) => {
    if (!pourTuiles && f.categorie && c.categorie !== f.categorie) return false;
    if (f.theme === "avec" && !themesDu(c).length) return false;
    if (f.theme && f.theme !== "avec" && !themesDu(c).includes(f.theme)) return false;
    if (!pourTuiles && f.mots && !c.mots.length) return false;
    if (!pourTuiles && f.mots && f.rubrique && !c.mots.some((m) => m.rubrique === f.rubrique)) return false;
    if (certitude != null && !((c[cleP] ?? 0) >= certitude)) return false;
    if (!pourTuiles && f.suivi && suiviDe(c) !== f.suivi) return false;
    if (du != null && c.t < du) return false;
    if (au != null && c.t >= au) return false;
    if (f.auteur_id && c.auteur_id !== f.auteur_id) return false;
    if (f.publication_id && String(c.publication) !== f.publication_id) return false;
    if (mt.length && !contientTout(c.nt ??= normal(c.texte), mt)) return false;
    if (ma.length && !contientTout(c.na ??= normal(c.auteur), ma)) return false;
    if (mp.length && !contientTout(c.pub ? (c.pub.nt ??= normal(c.pub.titre)) : "", mp)) return false;
    return true;
  });
  if (pourTuiles) return liste;
  const tris = {
    date: (a, b) => b.t - a.t,
    ancien: (a, b) => a.t - b.t,
    insultant: (a, b) => (b.pi ?? 0) - (a.pi ?? 0) || b.t - a.t,
    question: (a, b) => (b.pq ?? 0) - (a.pq ?? 0) || b.t - a.t,
    auteurs: (a, b) => (b.a?.insultants ?? 0) - (a.a?.insultants ?? 0) || (b.auteur_id || "").localeCompare(a.auteur_id || "") || b.t - a.t,
  };
  return liste.sort(tris[f.tri] || tris.date);
}

function carteCommentaire(c) {
  const cat = c.categorie;
  const proba = c[{ insultant: "pi", question: "pq", autre: "pa" }[cat]];
  const badge = el("span", { class: `badge ${cat}`, title: c.verifie ? "Catégorie vérifiée à la lecture" : "Catégorie donnée par le modèle" },
    CATEGORIES[cat] || cat, proba != null ? ` · ${pourcent(proba)}` : "");
  const motsTrouves = [...new Map(c.mots.map((m) => [m.mot, m])).values()];

  const infoSuivi = el("span", { class: "suivi-info" });
  const bTraite = el("button", { type: "button", class: "bouton" }, "✓ Traité");
  const bSans = el("button", { type: "button", class: "bouton" }, "Sans suite");
  const carte = el("article", { class: `carte commentaire ${cat}`, "data-code": c.code },
    el("div", { class: "tete" }, badge, boutonAuteur(c.auteur, c.auteur_id, c.a?.groupes ?? (c.pub?.groupe ? { [c.pub.groupe]: c.pub.chemin } : {})),
      el("time", { datetime: c.date, title: dateLongue(c.date) }, quand(c.date)),
      c.parent && el("span", {}, "réponse à un commentaire"),
      groupesChoisis().size > 1 && c.pub?.groupe && el("span", { class: "pale" }, raccourci(c.pub.groupe, 40)),
      themesDu(c).map((t) => el("span", { class: "badge theme", title: "Thème du commentaire (pour les réponses préparées)" }, nomTheme(t)))),
    el("p", { class: "texte" }, ...surligner(c.texte || "", c.mots)),
    motsTrouves.length > 0 && el("div", { class: "mots-trouves" }, el("span", { class: "pale" }, "Mots surveillés :"),
      motsTrouves.map((m) => el("span", { class: "mot", title: m.rubrique || "" }, m.mot, m.rubrique && el("small", {}, ` · ${m.rubrique}`)))),
    el("p", { class: "contexte" }, "Sous la publication : ",
      c.pub?.titre ? `« ${raccourci(c.pub.titre, 160)} »` : "(sans texte)", " ",
      c.pub && !f.publication_id && el("button", { type: "button", class: "lien", onclick: () => {
        f = { ...f, categorie: "", suivi: "", publication_id: String(c.pub.id), publication_nom: raccourci(c.pub.titre || "publication sans texte", 50) };
        afficher();
      } }, "voir tous ses commentaires")),
    el("div", { class: "actions" },
      el("button", { type: "button", class: `bouton reponses ${nombreReponses(c) ? "avec" : ""}`, title: "Réponses toutes faites pour ce commentaire",
        onclick: () => ouvrirReponses(c, { message, echec, prenom, apres: () => afficher({ garderPosition: true }) }) },
      "💬 Réponses", nombreReponses(c) ? ` (${nombreReponses(c)})` : ""),
      c.lien && el("a", { class: "bouton", href: c.lien, target: "_blank", rel: "noopener noreferrer" }, "Ouvrir sur Facebook ↗"),
      facebook(c.pub?.lien) && el("a", { class: "bouton", href: c.pub.lien, target: "_blank", rel: "noopener noreferrer" }, "La publication ↗"),
      el("span", { class: "espace" }), infoSuivi, bTraite, bSans));

  const poser = () => {
    const s = etat.suivi.get(c.code);
    const e = s?.etat || "a_traiter";
    carte.classList.toggle("marque-traite", e === "traite");
    carte.classList.toggle("marque-sans_suite", e === "sans_suite");
    bTraite.className = `bouton ${e === "traite" ? "actif-ok" : ""}`;
    bSans.className = `bouton ${e === "sans_suite" ? "actif-ss" : ""}`;
    bTraite.setAttribute("aria-pressed", e === "traite");
    bSans.setAttribute("aria-pressed", e === "sans_suite");
    infoSuivi.textContent = e === "a_traiter" ? "" : `${SUIVIS[e]}${s.par ? ` par ${s.par}` : ""}${s.le ? `, ${quand(s.le)}` : ""}`;
  };
  const marquer = async (voulu) => {
    const avant = etat.suivi.get(c.code);
    const nouvel = (avant?.etat || "a_traiter") === voulu ? "a_traiter" : voulu;
    etat.suivi.set(c.code, { etat: nouvel, par: prenom(), le: new Date().toISOString() });
    poser();
    try {
      const le = await suivre(c.cle, nouvel, prenom());
      noterSuivi(c.code, { etat: nouvel, par: prenom() || null, le });
      tuiles();
    } catch (e) {
      if (avant) etat.suivi.set(c.code, avant); else etat.suivi.delete(c.code);
      poser();
      if (e instanceof NonConnecte) return echec(e);
      message("Enregistrement impossible, réessayez.");
    }
  };
  bTraite.addEventListener("click", () => marquer("traite"));
  bSans.addEventListener("click", () => marquer("sans_suite"));
  carte.poser = poser;  // appelé quand un autre modérateur marque ce commentaire (suivreLesAutres)
  poser();
  return carte;
}

function puces() {
  const p = [];
  const puce = (texte, retirer) => el("button", { type: "button", class: "puce", title: "Retirer ce filtre", onclick: () => { retirer(); afficher(); } }, texte);
  if (f.auteur_id) p.push(puce(`Auteur : ${f.auteur_nom || f.auteur_id}`, () => { f.auteur_id = ""; f.auteur_nom = ""; }));
  if (f.publication_id) p.push(puce(`Publication : ${f.publication_nom || f.publication_id}`, () => { f.publication_id = ""; f.publication_nom = ""; }));
  $("puces").replaceChildren(...p);
}

function majControles() {
  for (const [id, cle] of [["f-categorie", "categorie"], ["f-mots", "mots"], ["f-suivi", "suivi"], ["f-periode", "periode"]]) {
    for (const b of $(id).querySelectorAll("button")) b.setAttribute("aria-pressed", b.dataset.v === f[cle] && !(cle === "periode" && f.du));
  }
  majFiltreTheme();
  $("bloc-certitude").hidden = !f.categorie;
  $("f-certitude").value = f.certitude;
  $("f-rubrique").hidden = !f.mots || RUBRIQUES.length < 2;
  $("f-rubrique").value = f.rubrique;
  $("f-du").value = f.du; $("f-au").value = f.au;
  for (const [id, cle] of [["f-texte", "texte"], ["f-auteur", "auteur"], ["f-publication", "publication"]]) {
    if (document.activeElement !== $(id)) $(id).value = f[cle];
  }
  $("tri").value = f.tri;
  puces();
}

// Filtre « Thème » : les thèmes qui ont des réponses préparées ou des commentaires rangés.
function majFiltreTheme() {
  const choix = $("f-theme");
  const avant = choix.value;
  choix.replaceChildren(el("option", { value: "" }, "Tous"), el("option", { value: "avec" }, "Rangés dans un thème"),
    ...themesActifs().map((t) => el("option", { value: t.id }, `${t.nom} (${reponsesDu(t.id).length} réponses)`)));
  choix.value = f.theme || "";
  if (choix.value !== (f.theme || "")) choix.value = avant;
}

function vueCommentaires() {
  majControles();
  const liste = filtrer();
  $("total").textContent = `${nombre(liste.length)} commentaire${liste.length > 1 ? "s" : ""}`;
  const zone = $("liste");
  zone.replaceChildren();
  if (!liste.length) {
    zone.append(el("div", { class: "vide carte" }, !etat.complet ? "Chargement…"
      : f.suivi === "a_traiter" && f.categorie ? "Rien à traiter avec ces filtres." : "Aucun commentaire avec ces filtres."));
  }
  suite($("suite"), zone, liste, carteCommentaire, "Afficher les suivants");
}

// ── Vue Auteurs ──────────────────────────────────────────────────────────────────────────────────────────────
function vueAuteurs() {
  const ma = mots($("a-nom").value);
  let liste = [...auteurs.values()].filter((a) => !ma.length || contientTout(a.na ??= normal(a.auteur), ma));
  for (const a of liste) a.a_traiter = aTraiter(a.liste, ["insultant"]);
  const tris = {
    a_traiter: (x, y) => y.a_traiter - x.a_traiter || y.insultants - x.insultants,
    insultants: (x, y) => y.insultants - x.insultants || y.n - x.n,
    mots: (x, y) => y.mots - x.mots || y.insultants - x.insultants,
    questions: (x, y) => y.questions - x.questions || y.n - x.n,
    n: (x, y) => y.n - x.n,
    dernier: (x, y) => y.dernier - x.dernier,
  };
  liste = liste.sort(tris[$("a-tri").value] || tris.a_traiter);
  $("a-total").textContent = `${nombre(liste.length)} auteurs`;
  const corps = $("a-lignes");
  corps.replaceChildren();
  suite($("a-suite"), corps, liste, (a) => el("tr", {},
    el("td", {}, boutonAuteur(a.auteur, a.auteur_id, a.groupes)),
    el("td", { class: `n ${a.insultants ? "fort" : ""}` }, nombre(a.insultants)),
    el("td", { class: "n" }, nombre(a.a_traiter)),
    el("td", { class: `n ${a.mots ? "fort-mots" : ""}` }, nombre(a.mots)),
    el("td", { class: "n" }, nombre(a.questions)),
    el("td", { class: "n" }, nombre(a.n)),
    el("td", { title: a.dernier ? new Date(a.dernier).toLocaleString("fr-FR") : "" }, quand(a.dernier))), "Afficher les suivants");
}

// ── Vue Publications ─────────────────────────────────────────────────────────────────────────────────────────
function vuePublications() {
  const mp = mots($("p-texte").value);
  let liste = [...publications.values()].filter((p) => !mp.length || contientTout(p.nt ??= normal(p.titre), mp));
  for (const p of liste) p.a_traiter = aTraiter(p.liste, ["insultant", "question"]);
  const tris = {
    a_traiter: (x, y) => y.a_traiter - x.a_traiter || y.insultants - x.insultants,
    insultants: (x, y) => y.insultants - x.insultants || y.n - x.n,
    questions: (x, y) => y.questions - x.questions || y.n - x.n,
    n: (x, y) => y.n - x.n,
    dernier: (x, y) => y.dernier - x.dernier,
  };
  liste = liste.sort(tris[$("p-tri").value] || tris.a_traiter);
  $("p-total").textContent = `${nombre(liste.length)} publications`;
  const zone = $("p-lignes");
  zone.replaceChildren();
  suite($("p-suite"), zone, liste, (p) => el("article", { class: "carte publication" },
    el("div", { class: "tete" }, p.date && el("time", { title: dateLongue(p.date) }, `publiée ${quand(p.date)}`),
      el("span", {}, `dernier commentaire ${quand(p.dernier)}`)),
    el("p", { class: "titre-pub" }, p.titre ? raccourci(p.titre, 300) : el("span", { class: "pale" }, "(publication sans texte : photo, vidéo ou lien)")),
    el("div", { class: "chiffres" },
      el("span", { class: `pastille-chiffre insultant ${p.insultants ? "" : "zero"}` }, `${nombre(p.insultants)} insultants`),
      el("span", { class: `pastille-chiffre question ${p.questions ? "" : "zero"}` }, `${nombre(p.questions)} questions`),
      el("span", { class: "pastille-chiffre" }, `${nombre(p.a_traiter)} à traiter`),
      el("span", { class: "pastille-chiffre" }, `${nombre(p.n)} commentaires`)),
    el("div", { class: "actions" },
      facebook(p.lien) && el("a", { class: "bouton", href: p.lien, target: "_blank", rel: "noopener noreferrer" }, "Ouvrir sur Facebook ↗"),
      el("button", { type: "button", class: "bouton", onclick: () => {
        f = { ...DEFAUT, groupes: f.groupes, vue: "commentaires", categorie: "", suivi: "", publication_id: String(p.id),
          publication_nom: raccourci(p.titre || "publication sans texte", 50) };
        afficher();
      } }, "Voir ses commentaires"))), "Afficher les suivantes");
}

// ── Vue Statistiques ─────────────────────────────────────────────────────────────────────────────────────────
function vueStatistiques() {
  vueStats($("vue-stats"), {
    commentaires, suivi: etat.suivi, reglages: { periode: f.s_periode },
    changer: (cle, v) => { f[`s_${cle}`] = v; afficher({ garderPosition: true }); },
  });
}

// ── Navigation ───────────────────────────────────────────────────────────────────────────────────────────────
function afficher({ garderPosition = false } = {}) {
  const y = window.scrollY;
  fermerMenu();
  ecrireAdresse();
  listeGroupes();
  tuiles();
  $("tuiles").hidden = f.vue === "stats";
  for (const b of document.querySelectorAll(".onglets button")) {
    if (b.dataset.vue === f.vue) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  }
  for (const v of VUES) $(`vue-${v}`).hidden = v !== f.vue;
  if (f.vue === "commentaires") vueCommentaires();
  else if (f.vue === "auteurs") vueAuteurs();
  else if (f.vue === "publications") vuePublications();
  else if (f.vue === "stats") vueStatistiques();
  if (garderPosition) window.scrollTo(0, y);
}

for (const b of document.querySelectorAll(".onglets button")) {
  b.addEventListener("click", () => { f.vue = b.dataset.vue; afficher(); window.scrollTo(0, 0); });
}
for (const [id, cle] of [["f-categorie", "categorie"], ["f-mots", "mots"], ["f-suivi", "suivi"], ["f-periode", "periode"]]) {
  $(id).addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    f[cle] = b.dataset.v;
    if (cle === "periode") { f.du = ""; f.au = ""; }
    if (cle === "categorie" && !f.categorie) f.certitude = "";
    if (cle === "mots" && !f.mots) f.rubrique = "";
    afficher();
  });
}
$("f-rubrique").append(...RUBRIQUES.map((r) => el("option", { value: r }, r)));
$("f-rubrique").addEventListener("change", (e) => { f.rubrique = e.target.value; afficher(); });
$("f-certitude").addEventListener("change", (e) => { f.certitude = e.target.value; afficher(); });
$("f-theme").addEventListener("change", (e) => { f.theme = e.target.value; afficher(); });
$("f-du").addEventListener("change", (e) => { f.du = e.target.value; f.periode = ""; afficher(); });
$("f-au").addEventListener("change", (e) => { f.au = e.target.value; f.periode = ""; afficher(); });
for (const [id, cle] of [["f-texte", "texte"], ["f-auteur", "auteur"], ["f-publication", "publication"]]) {
  $(id).addEventListener("input", attendre((e) => { f[cle] = e.target.value; afficher(); }));
}
$("tri").addEventListener("change", (e) => { f.tri = e.target.value; afficher(); });
$("reinitialiser").addEventListener("click", () => { f = { ...DEFAUT, groupes: f.groupes, categorie: "", suivi: "" }; afficher(); });
$("a-nom").addEventListener("input", attendre(vueAuteurs));
$("a-tri").addEventListener("change", vueAuteurs);
$("p-texte").addEventListener("input", attendre(vuePublications));
$("p-tri").addEventListener("change", vuePublications);

// ── Démarrage ────────────────────────────────────────────────────────────────────────────────────────────────
async function demarrer() {
  if (!connecte()) return ecranConnexion();
  $("ecran-connexion").hidden = true;
  $("ecran-site").hidden = false;
  $("qui").textContent = prenom() ? `Connecté : ${prenom()}` : "";
  lireAdresse();
  if (await charger()) { preparer(); afficher(); }  // affichage immédiat depuis le navigateur
  else afficher();
  synchroniser();  // puis seulement les nouveautés
}
demarrer();
