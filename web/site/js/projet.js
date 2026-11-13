// Page « Le projet » : chiffres du corpus, l'essentiel en une phrase, qualité mesurée du modèle.
import { TITRES, BAS, HAUT, el, nombre, pc, decimal, moisLong, messageErreur } from "./commun.js";
import { synthese } from "./donnees.js";
import { remplirPied } from "./pied.js";

const $ = (id) => document.getElementById(id);

demarrer();

async function demarrer() {
  let meta, cube;
  try {
    [meta, cube] = await Promise.all([synthese("meta"), synthese("cube")]);
  } catch (e) {
    messageErreur($("en-bref"), e);
    $("qualite").replaceChildren();
    return;
  }
  remplirPied(meta);
  const m = meta.modele;
  $("chapo-n").textContent = nombre(meta.commentaires);
  $("n-annotations").textContent = nombre(m.annotations);
  const medias = meta.comptes.filter((c) => c.groupe === "media" || c.groupe === "commentateur").length;
  $("n-comptes").textContent = String(medias);
  if (meta.debut_par_source?.instagram) $("debut-instagram").textContent = moisLong(meta.debut_par_source.instagram);
  if (m.cible) $("erreur-sujet").textContent = `${Math.round(100 * (1 - m.cible))} %`;

  // Comptes du groupe « autre » : chaînes YouTube trouvées par la recherche (Bluesky et la recherche sur X ne sont qu'un seul compte chacun).
  const groupesFb = meta.comptes.filter((c) => c.source === "facebook").length;
  const autres = meta.comptes.filter((c) => c.groupe === "autre" && c.source === "youtube").length;
  $("grands-chiffres").replaceChildren(...[
    [nombre(meta.commentaires), "commentaires analysés", `dont ${nombre(meta.reponses)} réponses à d'autres commentaires`],
    [nombre(meta.publications), "vidéos et posts", `${nombre(meta.par_source.youtube)} commentaires YouTube, ${nombre(meta.par_source.instagram)} Instagram${meta.par_source.bluesky ? `, ${nombre(meta.par_source.bluesky)} Bluesky` : ""}${meta.par_source.facebook ? `, ${nombre(meta.par_source.facebook)} Facebook` : ""}${meta.par_source.x ? `, ${nombre(meta.par_source.x)} X` : ""}`],
    [String(meta.comptes.filter((c) => c.groupe !== "autre").length), "comptes suivis", autres
      ? `ses comptes, son mouvement, des médias${groupesFb ? `, ${groupesFb} groupes Facebook` : ""} ; plus ${autres} autres chaînes, Bluesky et la recherche sur X`
      : `ses comptes, son mouvement, des médias${groupesFb ? `, ${groupesFb} groupes Facebook` : ""}`],
    [nombre(m.annotations), "exemples annotés", "pour entraîner le modèle"],
  ].map(([v, nom, legende]) => el("div", { class: "chiffre" }, el("div", { class: "valeur" }, v), el("div", { class: "nom" }, nom), el("div", { class: "legende" }, legende))));

  enBref(cube);
  qualite(m);
}

function enBref(cube) {
  const col = Object.fromEntries(cube.colonnes.map((c, i) => [c, i]));
  const t = new Array(cube.colonnes.length).fill(0);
  for (const c of cube.cellules) if (c[4] && !c[3]) for (let j = col.n; j < c.length; j++) t[j] += c[j];
  const n = t[col.n], fav = t[col.haut_tonalite] / n, hos = t[col.bas_tonalite] / n;
  const reproches = { forme: "sa forme (manière de parler, communication)", systeme: "être un homme du « système »", idees: "ses idées" };
  const [critere, part] = Object.keys(reproches).map((k) => [k, t[col[`bas_${k}`]] / n]).sort((a, b) => b[1] - a[1])[0];
  $("en-bref").replaceChildren(
    el("p", { class: "surtitre" }, "En bref"),
    el("p", { class: "phrase" }, `Sur les ${nombre(n)} commentaires qui parlent vraiment de lui, `, el("b", {}, pc(fav)), " lui sont favorables et ",
      el("b", {}, pc(hos)), ` hostiles. Le reproche le plus fréquent porte sur ${reproches[critere]} (${pc(part)}).`),
    el("div", { class: "repartition" },
      el("div", { class: "bas", style: { flex: `${hos} 1 0` } }, pc(hos)),
      el("div", { class: "milieu", style: { flex: `${1 - hos - fav} 1 0` } }, pc(1 - hos - fav)),
      el("div", { class: "haut", style: { flex: `${fav} 1 0` } }, pc(fav))),
    el("div", { class: "legende-rep" }, el("span", { style: { "--c": "var(--bas)" } }, `hostiles (tonalité ≤ ${BAS})`),
      el("span", { style: { "--c": "var(--milieu)" } }, "neutres ou mitigés"), el("span", { style: { "--c": "var(--haut)" } }, `favorables (≥ ${HAUT})`)),
    el("p", { class: "doux petit", style: { margin: "16px 0 0" } }, "Toutes sources et toutes périodes. ",
      el("a", { href: "statistiques.html" }, "Le détail par semaine et par compte →")));
}

function qualite(m) {
  const lignes = [];
  for (const k of ["tonalite", "pertinence", "idees", "systeme", "forme"]) {
    if (m.ecart[k] == null) continue;
    const constance = m.constance?.[k];
    lignes.push(
      el("div", {}, el("b", {}, TITRES[k])),
      el("div", { class: "jauge", title: "écart moyen, en points sur 20 (plus court = mieux)" },
        el("div", { style: { width: `${Math.min(100, (100 * m.ecart[k]) / 4)}%` } }),
        constance != null ? el("span", { class: "repere", style: { left: `${Math.min(100, (100 * constance) / 4)}%` }, title: "écart de l'annotateur avec lui-même" }) : null),
      el("div", { class: "val" }, el("b", {}, `${decimal(m.ecart[k], 1)} pt`), " d'écart moyen"));
  }
  const r = m.reproches || {};
  const phrases = [];
  if (m.cible) phrases.push(`Il dit juste dans ${pc(m.cible)} des cas si le commentaire parle de lui ou d'autre chose.`);
  if (r.systeme) phrases.push(`Il repère ${pc(r.systeme.rappel)} des reproches « système ».`);
  $("qualite-intro").textContent = `Mesuré sur ${nombre(m.test)} commentaires qu'il n'avait jamais vus.`;
  $("qualite").replaceChildren(
    el("div", { class: "tete" }, el("h3", {}, "De combien il se trompe, en moyenne"),
      el("p", {}, "Écart moyen avec la note de référence, en points sur 20 : plus la barre est courte, mieux c'est. Le trait marque la limite atteignable.")),
    el("div", { class: "qualite" }, ...lignes),
    el("p", { class: "doux", style: { margin: "18px 0 0" } }, phrases.join(" ")));
}
