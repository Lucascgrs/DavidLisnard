// Page « Le projet » : chiffres du corpus, l'essentiel en une phrase, qualité mesurée du modèle.
import { TITRES, EXPLOITABLE, BAS, HAUT, el, nombre, pc, sur20, decimal, moisLong, messageErreur } from "./commun.js";
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

  $("grands-chiffres").replaceChildren(...[
    [nombre(meta.commentaires), "commentaires analysés", `dont ${nombre(meta.reponses)} réponses à d'autres commentaires`],
    [nombre(meta.publications), "vidéos et posts", `${nombre(meta.par_source.youtube)} commentaires YouTube, ${nombre(meta.par_source.instagram)} Instagram`],
    [String(meta.comptes.length), "comptes suivis", "les siens, ceux de son mouvement, des médias et des commentateurs"],
    [nombre(m.annotations), "exemples annotés", "pour entraîner le modèle et mesurer ses erreurs"],
  ].map(([v, nom, legende]) => el("div", { class: "chiffre" }, el("div", { class: "valeur" }, v), el("div", { class: "nom" }, nom), el("div", { class: "legende" }, legende))));

  enBref(cube);
  qualite(m);
}

function enBref(cube) {
  const col = Object.fromEntries(cube.colonnes.map((c, i) => [c, i]));
  const t = new Array(cube.colonnes.length).fill(0);
  for (const c of cube.cellules) if (c[4] && !c[3]) for (let j = col.n; j < c.length; j++) t[j] += c[j];
  const n = t[col.n], fav = t[col.haut_tonalite] / n, hos = t[col.bas_tonalite] / n, ton = t[col.tonalite] / n;
  const reproches = { forme: "sa forme (manière de parler, communication)", systeme: "être un homme du « système »", idees: "ses idées" };
  const [critere, part] = Object.keys(reproches).map((k) => [k, t[col[`bas_${k}`]] / n]).sort((a, b) => b[1] - a[1])[0];
  $("en-bref").replaceChildren(
    el("p", { class: "surtitre" }, "En bref"),
    el("p", { class: "phrase" }, `Sur les ${nombre(n)} commentaires qui parlent vraiment de lui, `, el("b", {}, pc(fav)), " lui sont favorables et ",
      el("b", {}, pc(hos)), ` hostiles. Tonalité moyenne : ${sur20(ton)} sur 20. Le reproche précis le plus fréquent porte sur ${reproches[critere]} (${pc(part)} des commentaires).`),
    el("div", { class: "repartition" },
      el("div", { class: "bas", style: { flex: `${hos} 1 0` } }, pc(hos)),
      el("div", { class: "milieu", style: { flex: `${1 - hos - fav} 1 0` } }, pc(1 - hos - fav)),
      el("div", { class: "haut", style: { flex: `${fav} 1 0` } }, pc(fav))),
    el("div", { class: "legende-rep" }, el("span", { style: { "--c": "var(--bas)" } }, `hostiles (tonalité ≤ ${BAS})`),
      el("span", { style: { "--c": "var(--milieu)" } }, "neutres ou mitigés"), el("span", { style: { "--c": "var(--haut)" } }, `favorables (≥ ${HAUT})`)),
    el("p", { class: "doux petit", style: { margin: "16px 0 0" } }, `Tous comptes et toutes périodes confondus, commentaires exploitables seulement (pertinence ≥ ${EXPLOITABLE}). `,
      el("a", { href: "statistiques.html" }, "Le détail par semaine, par compte et par critère →")));
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
  if (m.correlation.tonalite) phrases.push(`Ses notes de tonalité suivent de près celles de référence (corrélation de rang ${decimal(m.correlation.tonalite)} ; ${decimal(m.correlation.pertinence)} pour la pertinence).`);
  if (m.cible) phrases.push(`Il dit juste dans ${pc(m.cible)} des cas si le commentaire parle de lui ou d'autre chose.`);
  if (r.systeme) phrases.push(`Sur le reproche « système », il en retrouve ${pc(r.systeme.rappel)}, et ${pc(r.systeme.precision)} de ceux qu'il signale sont justes. Les reproches de forme, rares, sont les plus difficiles (${pc(r.forme?.rappel)} retrouvés).`);
  $("qualite-intro").textContent = `Mesuré sur ${nombre(m.test)} commentaires qu'il n'avait jamais vus, en comparant ses notes aux notes de référence (modèle ${m.version}, ${m.langue || "modèle de langue affiné"}).`;
  $("qualite").replaceChildren(
    el("div", { class: "tete" }, el("h3", {}, "De combien il se trompe, en moyenne"),
      el("p", {}, "La barre montre l'écart moyen entre sa note et la note de référence, sur 20 : plus elle est courte, mieux c'est. Le trait noir marque l'écart de l'annotateur avec lui-même quand il renote les mêmes commentaires, la limite qu'un modèle peut espérer atteindre. Pour la forme, le système et les idées, l'écart paraît faible parce que la plupart des commentaires n'en parlent pas.")),
    el("div", { class: "qualite" }, ...lignes),
    el("p", { class: "doux", style: { margin: "18px 0 0" } }, phrases.join(" ")));
}
