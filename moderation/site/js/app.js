// Site de modération : connexion, puis trois vues (commentaires, auteurs, publications).
// Les données sont gardées dans le navigateur (donnees.js) : filtres, tris et comptages se font ici, sans requête.
// La base n'est interrogée que pour les nouveautés (au démarrage, puis de temps en temps si la page est ouverte)
// et pour enregistrer une marque. Tout texte venu de Facebook est posé en textContent, jamais en HTML.
import { NonConnecte, connecte, connecter, deconnecter, suivre } from "./api.js";
import { actualiser, charger, effacerCache, etat, noterSuivi } from "./donnees.js";

const PAGE = 50;                    // cartes affichées à la fois (affichage seulement : tout est déjà là)
const SUIVI_MIN = 3;                // marques des autres modérateurs : toutes les 3 min, page visible
const TOUT_MIN = 15;                // nouveaux commentaires : toutes les 15 min, page visible (collecte : quelques fois par jour)
const $ = (id) => document.getElementById(id);
const CATEGORIES = { insultant: "Insultant", question: "Question", autre: "Autre" };
const SUIVIS = { traite: "Traité", sans_suite: "Sans suite" };

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

function preparer() {
  auteurs = new Map();
  publications = new Map();
  commentaires = [];
  for (const l of etat.lignes.values()) {
    const pub = etat.pubs.get(l.publication) || null;
    const lien = facebook(pub?.lien)
      ? pub.lien + (l.parent ? `?comment_id=${l.parent}&reply_comment_id=${l.code}` : `?comment_id=${l.code}`) : null;
    const c = { ...l, cle: `facebook:${l.code}`, categorie: l.categorie || "autre", pub, lien, t: enDate(l.date)?.getTime() ?? 0 };
    commentaires.push(c);
    if (l.auteur_id) {
      const a = auteurs.get(l.auteur_id) || { auteur_id: l.auteur_id, auteur: l.auteur, n: 0, insultants: 0, questions: 0, dernier: 0, groupes: {}, liste: [] };
      a.n++; a.liste.push(c);
      if (c.categorie === "insultant") a.insultants++;
      if (c.categorie === "question") a.questions++;
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
}
const aTraiter = (liste, cats) => liste.reduce((s, c) => s + (cats.includes(c.categorie) && suiviDe(c) === "a_traiter" ? 1 : 0), 0);

// ── État des filtres (gardé dans l'adresse de la page, pour la partager) ─────────────────────────────────────
const DEFAUT = { vue: "commentaires", categorie: "insultant", certitude: "", suivi: "a_traiter", periode: "", du: "", au: "",
  groupes: [], texte: "", auteur: "", publication: "", auteur_id: "", auteur_nom: "", publication_id: "", publication_nom: "",
  tri: "date" };
let f = { ...DEFAUT };

function lireAdresse() {
  const p = new URLSearchParams(location.hash.slice(1));
  f = { ...DEFAUT };
  for (const k of Object.keys(DEFAUT)) {
    if (!p.has(k)) continue;
    f[k] = k === "groupes" ? p.getAll(k) : p.get(k);
  }
}
function ecrireAdresse() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) {
    if (k === "groupes") v.forEach((g) => p.append(k, g));
    else if (v !== DEFAUT[k]) p.set(k, v);
  }
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
  effacerCache();
  etat.lignes.clear(); etat.pubs.clear(); etat.suivi.clear(); etat.complet = 0;
  commentaires = [];
  ecranConnexion();
});

function echec(e) {
  if (e instanceof NonConnecte) return ecranConnexion("Session terminée : entrez de nouveau le mot de passe.");
  console.error(e);
  message("La base ne répond pas pour le moment ; les données affichées sont celles déjà chargées.");
}

// ── Actualisation ────────────────────────────────────────────────────────────────────────────────────────────
let derniereComplete = 0, enCours = false;
async function synchroniser({ seulementSuivi = false } = {}) {
  if (enCours) return;
  enCours = true;
  $("actualiser").disabled = true;
  const premiere = !etat.complet;
  try {
    const change = await actualiser({
      seulementSuivi,
      avancement: premiere ? (n) => { $("etat-donnees").textContent = `Premier chargement : ${nombre(n)} commentaires…`; } : null,
    });
    if (!seulementSuivi) derniereComplete = Date.now();
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
  $("etat-donnees").textContent = etat.synchro ? `À jour ${quand(etat.synchro)}` : "";
}
$("actualiser").addEventListener("click", () => synchroniser());
setInterval(() => {
  majEtatDonnees();
  if (document.hidden || !connecte() || $("ecran-site").hidden) return;
  if (Date.now() - derniereComplete > TOUT_MIN * 60000) synchroniser();
  else if (Date.now() - etat.synchro > SUIVI_MIN * 60000) synchroniser({ seulementSuivi: true });
}, 30_000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && connecte() && !$("ecran-site").hidden && Date.now() - etat.synchro > SUIVI_MIN * 60000) {
    synchroniser({ seulementSuivi: Date.now() - derniereComplete < TOUT_MIN * 60000 });
  }
});

// ── Compteurs du haut et liste des groupes ───────────────────────────────────────────────────────────────────
function tuiles() {
  const tuile = (classe, chiffre, libelle, regler) => el("button", {
    type: "button", class: `tuile ${classe}`,
    onclick: () => { f = { ...DEFAUT, ...regler, vue: "commentaires" }; afficher(); },
  }, el("span", { class: "chiffre" }, nombre(chiffre)), el("span", { class: "libelle" }, libelle));
  $("tuiles").replaceChildren(
    tuile("insultant", aTraiter(commentaires, ["insultant"]), "insultants à traiter", { categorie: "insultant" }),
    tuile("question", aTraiter(commentaires, ["question"]), "questions à traiter", { categorie: "question" }),
    tuile("ok", commentaires.filter((c) => suiviDe(c) === "traite").length, "marqués « traité »", { categorie: "", suivi: "traite" }),
    tuile("", commentaires.length, "commentaires en tout", { categorie: "", suivi: "" }),
  );
  const dernier = commentaires.reduce((m, c) => Math.max(m, c.t), 0);
  $("aide-maj").textContent = dernier ? `Commentaire le plus récent : ${dateLongue(new Date(dernier).toISOString())}.` : "";
}

function listeGroupes() {
  const parGroupe = new Map();
  for (const c of commentaires) if (c.pub?.groupe) parGroupe.set(c.pub.groupe, (parGroupe.get(c.pub.groupe) || 0) + 1);
  const groupes = [...parGroupe].sort((a, b) => b[1] - a[1]);
  $("f-groupes").replaceChildren(...groupes.map(([g, n]) => el("label", {},
    el("input", { type: "checkbox", value: g, checked: f.groupes.includes(g),
      onchange: (ev) => { f.groupes = ev.target.checked ? [...f.groupes, g] : f.groupes.filter((x) => x !== g); afficher(); } }),
    el("span", {}, g), el("span", { class: "n" }, nombre(n)))));
  const choisi = $("p-groupe").value;
  $("p-groupe").replaceChildren(el("option", { value: "" }, "Tous les groupes"), ...groupes.map(([g]) => el("option", { value: g }, g)));
  $("p-groupe").value = choisi;
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
      f = { ...DEFAUT, vue: "commentaires", categorie: "", suivi: "", auteur_id: id, auteur_nom: nom || id };
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
function filtrer() {
  const du = f.du ? Date.parse(f.du + "T00:00:00Z") : f.periode ? Date.now() - Number(f.periode) * 864e5 : null;
  const au = f.au ? Date.parse(f.au + "T00:00:00Z") + 864e5 : null;
  const groupes = f.groupes.length ? new Set(f.groupes) : null;
  const mt = mots(f.texte), ma = mots(f.auteur), mp = mots(f.publication);
  const certitude = f.categorie && f.certitude ? Number(f.certitude) : null;
  const cleP = { insultant: "pi", question: "pq", autre: "pa" }[f.categorie];
  const liste = commentaires.filter((c) => {
    if (f.categorie && c.categorie !== f.categorie) return false;
    if (certitude != null && !c.verifie && !((c[cleP] ?? 0) >= certitude)) return false;
    if (f.suivi && suiviDe(c) !== f.suivi) return false;
    if (du != null && c.t < du) return false;
    if (au != null && c.t >= au) return false;
    if (groupes && !groupes.has(c.pub?.groupe)) return false;
    if (f.auteur_id && c.auteur_id !== f.auteur_id) return false;
    if (f.publication_id && String(c.publication) !== f.publication_id) return false;
    if (mt.length && !contientTout(c.nt ??= normal(c.texte), mt)) return false;
    if (ma.length && !contientTout(c.na ??= normal(c.auteur), ma)) return false;
    if (mp.length && !contientTout(c.pub ? (c.pub.nt ??= normal(c.pub.titre)) : "", mp)) return false;
    return true;
  });
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
    CATEGORIES[cat] || cat, c.verifie ? " · vérifié" : proba != null ? ` · ${pourcent(proba)}` : "");
  const a = c.a;
  const recidive = a && a.insultants >= 2
    ? el("span", { class: "recidive", title: "Commentaires insultants de cet auteur, sur tous ses commentaires" }, `${a.insultants} insultants sur ${a.n}`)
    : a && a.n > 1 ? el("span", {}, `${a.n} commentaires`) : null;
  const groupes = c.pub?.groupe ? { [c.pub.groupe]: c.pub.chemin } : {};

  const infoSuivi = el("span", { class: "suivi-info" });
  const bTraite = el("button", { type: "button", class: "bouton" }, "✓ Traité");
  const bSans = el("button", { type: "button", class: "bouton" }, "Sans suite");
  const carte = el("article", { class: `carte commentaire ${cat}` },
    el("div", { class: "tete" }, badge, boutonAuteur(c.auteur, c.auteur_id, groupes), recidive,
      c.pub?.groupe && el("span", {}, c.pub.groupe), el("time", { datetime: c.date, title: dateLongue(c.date) }, quand(c.date)),
      c.parent && el("span", {}, "réponse à un commentaire")),
    el("p", { class: "texte" }, c.texte || ""),
    el("p", { class: "contexte" }, "Sous la publication : ",
      c.pub?.titre ? `« ${raccourci(c.pub.titre, 160)} »` : "(sans texte)", " ",
      c.pub && !f.publication_id && el("button", { type: "button", class: "lien", onclick: () => {
        f = { ...f, categorie: "", suivi: "", publication_id: String(c.pub.id), publication_nom: raccourci(c.pub.titre || "publication sans texte", 50) };
        afficher();
      } }, "voir tous ses commentaires")),
    el("div", { class: "actions" },
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
  for (const [id, cle] of [["f-categorie", "categorie"], ["f-suivi", "suivi"], ["f-periode", "periode"]]) {
    for (const b of $(id).querySelectorAll("button")) b.setAttribute("aria-pressed", b.dataset.v === f[cle] && !(cle === "periode" && f.du));
  }
  $("bloc-certitude").hidden = !f.categorie;
  $("f-certitude").value = f.certitude;
  $("f-du").value = f.du; $("f-au").value = f.au;
  for (const [id, cle] of [["f-texte", "texte"], ["f-auteur", "auteur"], ["f-publication", "publication"]]) {
    if (document.activeElement !== $(id)) $(id).value = f[cle];
  }
  $("tri").value = f.tri;
  for (const c of $("f-groupes").querySelectorAll("input")) c.checked = f.groupes.includes(c.value);
  puces();
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
    el("td", { class: "n" }, nombre(a.questions)),
    el("td", { class: "n" }, nombre(a.n)),
    el("td", { title: a.dernier ? new Date(a.dernier).toLocaleString("fr-FR") : "" }, quand(a.dernier)),
    el("td", {}, Object.keys(a.groupes).join(" · "))), "Afficher les suivants");
}

// ── Vue Publications ─────────────────────────────────────────────────────────────────────────────────────────
function vuePublications() {
  const mp = mots($("p-texte").value), groupe = $("p-groupe").value;
  let liste = [...publications.values()].filter((p) => (!groupe || p.groupe === groupe) && (!mp.length || contientTout(p.nt ??= normal(p.titre), mp)));
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
    el("div", { class: "tete" }, p.groupe && el("span", {}, p.groupe), p.date && el("time", { title: dateLongue(p.date) }, `publiée ${quand(p.date)}`),
      el("span", {}, `dernier commentaire ${quand(p.dernier)}`)),
    el("p", { class: "titre-pub" }, p.titre ? raccourci(p.titre, 300) : el("span", { class: "pale" }, "(publication sans texte : photo, vidéo ou lien)")),
    el("div", { class: "chiffres" },
      el("span", { class: p.insultants ? "fort" : "" }, `${nombre(p.insultants)} insultants`),
      el("span", {}, `${nombre(p.questions)} questions`),
      el("span", {}, `${nombre(p.a_traiter)} à traiter`),
      el("span", {}, `${nombre(p.n)} commentaires`)),
    el("div", { class: "actions" },
      facebook(p.lien) && el("a", { class: "bouton", href: p.lien, target: "_blank", rel: "noopener noreferrer" }, "Ouvrir sur Facebook ↗"),
      el("button", { type: "button", class: "bouton", onclick: () => {
        f = { ...DEFAUT, vue: "commentaires", categorie: "", suivi: "", publication_id: String(p.id),
          publication_nom: raccourci(p.titre || "publication sans texte", 50) };
        afficher();
      } }, "Voir ses commentaires"))), "Afficher les suivantes");
}

// ── Navigation ───────────────────────────────────────────────────────────────────────────────────────────────
function afficher({ garderPosition = false } = {}) {
  const y = window.scrollY;
  fermerMenu();
  ecrireAdresse();
  tuiles();
  listeGroupes();
  for (const b of document.querySelectorAll(".onglets button")) {
    if (b.dataset.vue === f.vue) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  }
  for (const v of ["commentaires", "auteurs", "publications", "aide"]) $(`vue-${v}`).hidden = v !== f.vue;
  if (f.vue === "commentaires") vueCommentaires();
  else if (f.vue === "auteurs") vueAuteurs();
  else if (f.vue === "publications") vuePublications();
  if (garderPosition) window.scrollTo(0, y);
}

for (const b of document.querySelectorAll(".onglets button")) {
  b.addEventListener("click", () => { f.vue = b.dataset.vue; afficher(); window.scrollTo(0, 0); });
}
for (const [id, cle] of [["f-categorie", "categorie"], ["f-suivi", "suivi"], ["f-periode", "periode"]]) {
  $(id).addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    f[cle] = b.dataset.v;
    if (cle === "periode") { f.du = ""; f.au = ""; }
    if (cle === "categorie" && !f.categorie) f.certitude = "";
    afficher();
  });
}
$("f-certitude").addEventListener("change", (e) => { f.certitude = e.target.value; afficher(); });
$("f-du").addEventListener("change", (e) => { f.du = e.target.value; f.periode = ""; afficher(); });
$("f-au").addEventListener("change", (e) => { f.au = e.target.value; f.periode = ""; afficher(); });
for (const [id, cle] of [["f-texte", "texte"], ["f-auteur", "auteur"], ["f-publication", "publication"]]) {
  $(id).addEventListener("input", attendre((e) => { f[cle] = e.target.value; afficher(); }));
}
$("tri").addEventListener("change", (e) => { f.tri = e.target.value; afficher(); });
$("reinitialiser").addEventListener("click", () => { f = { ...DEFAUT, categorie: "", suivi: "" }; afficher(); });
$("a-nom").addEventListener("input", attendre(vueAuteurs));
$("a-tri").addEventListener("change", vueAuteurs);
$("p-texte").addEventListener("input", attendre(vuePublications));
for (const id of ["p-groupe", "p-tri"]) $(id).addEventListener("change", vuePublications);

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
