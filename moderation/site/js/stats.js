// Onglet Statistiques : évolution des insultants, questions et mots surveillés, et suivi par modérateur.
// Tout se calcule ici sur les données déjà dans le navigateur. Graphiques en SVG faits à la main (pas de
// bibliothèque : la politique de sécurité du site n'autorise que ses propres scripts). Textes posés en textContent.

const NS = "http://www.w3.org/2000/svg";
const JOUR = 864e5;
const nombre = (n) => (n ?? 0).toLocaleString("fr-FR");

function el(balise, attrs = {}, ...enfants) {
  const n = document.createElement(balise);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "style") n.style.cssText = v;  // pas d'attribut style : la politique de sécurité l'interdit
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const e of enfants.flat()) if (e != null && e !== false) n.append(e instanceof Node ? e : String(e));
  return n;
}
function svg(balise, attrs = {}) {
  const n = document.createElementNS(NS, balise);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}

// ── Périodes ─────────────────────────────────────────────────────────────────────────────────────────────────
// Par jour sur 30 jours, par semaine (lundi) au-delà. Les dates sont lues en heure de Paris (celle des modérateurs).
const debutJour = (t) => { const d = new Date(t); d.setHours(0, 0, 0, 0); return d.getTime(); };
const debutSemaine = (t) => { const d = new Date(debutJour(t)); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.getTime(); };
export const PERIODES = {
  "30": { libelle: "30 jours", jours: 30, pas: "jour" },
  "91": { libelle: "3 mois", jours: 91, pas: "semaine" },
  "182": { libelle: "6 mois", jours: 182, pas: "semaine" },
  "": { libelle: "Tout", jours: null, pas: "semaine" },
};
function cases(periode, plusAncien) {
  const p = PERIODES[periode] ?? PERIODES[""];
  const fin = Date.now();
  const debut = p.jours ? fin - (p.jours - 1) * JOUR : plusAncien || fin;
  const depart = p.pas === "jour" ? debutJour(debut) : debutSemaine(debut);
  const liste = [];
  for (let t = depart; t <= fin; ) {
    liste.push(t);
    const d = new Date(t);
    d.setDate(d.getDate() + (p.pas === "jour" ? 1 : 7));
    t = d.getTime();
  }
  const caseDe = (t) => (t < depart ? -1 : p.pas === "jour"
    ? liste.indexOf(debutJour(t)) : liste.indexOf(debutSemaine(t)));
  return { liste, caseDe, pas: p.pas, depart };
}
const etiquette = (t, pas) => new Date(t).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
const titreCase = (t, pas) => pas === "jour"
  ? new Date(t).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })
  : `Semaine du ${new Date(t).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;

// ── Un graphique : lignes (séries comparables) ou barres empilées (parts d'un total) ────────────────────────────
// series : [{ nom, classe, valeurs[] }] ; la classe donne la couleur (css : .serie-<classe>).
function graphique({ titre, sous, cases: cs, series, empile = false, vide }) {
  const L = 760, H = 260, g = 44, d = 12, h = 14, b = 30;
  const n = cs.liste.length;
  const totaux = cs.liste.map((_, i) => series.reduce((s, x) => s + x.valeurs[i], 0));
  const max = Math.max(1, ...(empile ? totaux : series.flatMap((s) => s.valeurs)));
  const pasY = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000].find((p) => max / p <= 5) || Math.ceil(max / 5);
  const haut = Math.ceil(max / pasY) * pasY;
  const x = (i) => g + (n === 1 ? (L - g - d) / 2 : (i * (L - g - d)) / (n - 1));
  const largeurCase = (L - g - d) / Math.max(n, 1);
  const xb = (i) => g + i * largeurCase;
  const y = (v) => H - b - (v / haut) * (H - b - h);

  const s = svg("svg", { viewBox: `0 0 ${L} ${H}`, class: "graphe", role: "img", "aria-label": titre });
  for (let v = 0; v <= haut; v += pasY) {
    s.append(svg("line", { x1: g, x2: L - d, y1: y(v), y2: y(v), class: v ? "grille" : "base" }));
    const t = svg("text", { x: g - 8, y: y(v) + 4, class: "axe", "text-anchor": "end" });
    t.textContent = nombre(v);
    s.append(t);
  }
  const toutes = Math.ceil(n / 8);  // au plus 8 dates sous l'axe
  cs.liste.forEach((t, i) => {
    if (i % toutes) return;
    const e = svg("text", { x: empile ? xb(i) + largeurCase / 2 : x(i), y: H - 10, class: "axe", "text-anchor": "middle" });
    e.textContent = etiquette(t, cs.pas);
    s.append(e);
  });

  if (empile) {
    const lb = Math.max(2, Math.min(28, largeurCase - 2));
    cs.liste.forEach((_, i) => {
      let bas = 0;
      const vis = series.filter((x) => x.valeurs[i] > 0);
      vis.forEach((serie, k) => {
        const v = serie.valeurs[i];
        const y1 = y(bas + v), y0 = y(bas);
        const sommet = k === vis.length - 1;
        const hRect = Math.max(0, y0 - y1 - (sommet ? 0 : 2));  // 2 px d'écart entre segments
        const xr = xb(i) + (largeurCase - lb) / 2;
        const r = Math.min(4, lb / 2, hRect);
        s.append(svg("path", { class: `barre serie-${serie.classe}`, d: sommet
          ? `M${xr},${y0} V${y1 + r} Q${xr},${y1} ${xr + r},${y1} H${xr + lb - r} Q${xr + lb},${y1} ${xr + lb},${y1 + r} V${y0} Z`
          : `M${xr},${y0} V${y0 - hRect} H${xr + lb} V${y0} Z` }));
        bas += v;
      });
    });
  } else {
    for (const serie of series) {
      const pts = serie.valeurs.map((v, i) => `${x(i)},${y(v)}`).join(" ");
      s.append(svg("polyline", { points: pts, class: `ligne serie-${serie.classe}` }));
    }
  }

  // Survol : une bande par case, une info-bulle avec toutes les valeurs.
  const bulle = el("div", { class: "bulle", hidden: true });
  const repere = svg("line", { y1: h, y2: H - b, class: "repere", visibility: "hidden" });
  s.append(repere);
  const points = series.map((serie) => { const c = svg("circle", { r: 4.5, class: `point serie-${serie.classe}`, visibility: "hidden" }); s.append(c); return c; });
  const cadre = el("div", { class: "cadre-graphe" }, s, bulle);
  cs.liste.forEach((t, i) => {
    const zone = svg("rect", { x: empile ? xb(i) : x(i) - largeurCase / 2, y: 0, width: largeurCase, height: H - b, class: "zone" });
    zone.addEventListener("pointerenter", () => {
      const cx = empile ? xb(i) + largeurCase / 2 : x(i);
      repere.setAttribute("x1", cx); repere.setAttribute("x2", cx); repere.setAttribute("visibility", "visible");
      if (!empile) series.forEach((serie, k) => { points[k].setAttribute("cx", cx); points[k].setAttribute("cy", y(serie.valeurs[i])); points[k].setAttribute("visibility", "visible"); });
      const lignes = series.filter((x) => !empile || x.valeurs[i]).map((x) => el("div", { class: "ligne-bulle" },
        el("span", { class: `pastille serie-${x.classe}` }), el("span", {}, x.nom), el("strong", {}, nombre(x.valeurs[i]))));
      bulle.replaceChildren(...[el("div", { class: "titre-bulle" }, titreCase(t, cs.pas)), ...lignes,
        empile && totaux[i] ? el("div", { class: "ligne-bulle total-bulle" }, el("span"), el("span", {}, "Total"), el("strong", {}, nombre(totaux[i]))) : null,
        empile && !totaux[i] ? el("div", { class: "pale" }, "Aucun") : null].filter(Boolean));
      bulle.hidden = false;
      const r = cadre.getBoundingClientRect(), echelle = r.width / L;
      bulle.style.left = `${Math.min(Math.max(cx * echelle + 12, 0), r.width - bulle.offsetWidth - 4)}px`;
      bulle.style.top = "8px";
    });
    zone.addEventListener("pointerleave", () => { bulle.hidden = true; repere.setAttribute("visibility", "hidden"); points.forEach((p) => p.setAttribute("visibility", "hidden")); });
    s.append(zone);
  });

  const legende = series.length > 1 ? el("div", { class: "legende" }, series.map((x) =>
    el("span", {}, el("span", { class: `pastille serie-${x.classe}${empile ? "" : " trait"}` }), `${x.nom} (${nombre(x.valeurs.reduce((a, b) => a + b, 0))})`))) : null;
  // Les chiffres eux-mêmes, en tableau (lecture d'écran, ou pour recopier).
  const tableau = el("details", { class: "chiffres-graphe" }, el("summary", {}, "Voir les chiffres"),
    el("div", { class: "tableau-cadre" }, el("table", { class: "tableau" },
      el("thead", {}, el("tr", {}, el("th", {}, cs.pas === "jour" ? "Jour" : "Semaine du"), series.map((x) => el("th", { class: "n" }, x.nom)), empile ? el("th", { class: "n" }, "Total") : null)),
      el("tbody", {}, [...cs.liste.keys()].reverse().map((i) => el("tr", {},
        el("td", {}, new Date(cs.liste[i]).toLocaleDateString("fr-FR")),
        series.map((x) => el("td", { class: "n" }, nombre(x.valeurs[i]))), empile ? el("td", { class: "n" }, nombre(totaux[i])) : null))))));
  const rien = !totaux.some(Boolean);
  return el("section", { class: "carte bloc-graphe" }, el("h3", {}, titre), sous && el("p", { class: "doux sous-titre" }, sous),
    rien && vide ? el("div", { class: "vide" }, vide) : [legende, cadre, tableau]);
}

function tuile(classe, chiffre, libelle, detail) {
  return el("div", { class: `chiffre-cle ${classe}` }, el("span", { class: "chiffre" }, nombre(chiffre)),
    el("span", { class: "libelle" }, libelle), detail && el("span", { class: "detail" }, detail));
}

/** L'onglet entier. commentaires : objets préparés par app.js ; suivi : Map code → { etat, par, le } ;
 *  reglages : { periode } ; changer(cle, valeur) : nouveau réglage. */
export function vueStats(zone, { commentaires, suivi, reglages, changer }) {
  const segments = (cle, options) => el("div", { class: "segments" }, Object.entries(options).map(([v, lib]) =>
    el("button", { type: "button", "aria-pressed": String(reglages[cle] === v), onclick: () => changer(cle, v) }, lib)));
  const liste = commentaires;
  const plusAncien = liste.reduce((m, c) => (c.t && c.t < m ? c.t : m), Date.now());
  const cs = cases(reglages.periode, plusAncien);
  const zero = () => cs.liste.map(() => 0);

  // 1. Ce que reçoit le groupe : par date du commentaire.
  const ins = zero(), que = zero(), mots = zero(), tous = zero();
  let nIns = 0, nQue = 0, nMots = 0, nTous = 0;
  for (const c of liste) {
    const i = cs.caseDe(c.t);
    if (i < 0) continue;
    nTous++; tous[i]++;
    if (c.categorie === "insultant") { ins[i]++; nIns++; }
    if (c.categorie === "question") { que[i]++; nQue++; }
    if (c.mots.length) { mots[i]++; nMots++; }
  }

  // 2. Le travail des modérateurs : par date de la marque (la dernière posée sur chaque commentaire).
  const codes = new Map(liste.map((c) => [c.code, c]));
  const parQui = new Map();
  let nTraites = 0, nSans = 0;
  for (const [code, s] of suivi) {
    if (!codes.has(code) || s.etat === "a_traiter") continue;
    const qui = (s.par || "").trim() || "(sans prénom)";
    const p = parQui.get(qui) || { qui, traite: 0, sans_suite: 0, semaine: 0, dernier: 0, valeurs: zero(), ins: 0, que: 0 };
    const t = Date.parse(s.le) || 0;
    p[s.etat]++;
    if (s.etat === "traite") {
      nTraites++;
      const c = codes.get(code);
      if (c.categorie === "insultant") p.ins++;
      if (c.categorie === "question") p.que++;
    } else nSans++;
    if (Date.now() - t < 7 * JOUR) p.semaine++;
    if (t > p.dernier) p.dernier = t;
    const i = cs.caseDe(t);
    if (i >= 0 && s.etat === "traite") p.valeurs[i]++;
    parQui.set(qui, p);
  }
  // Couleur attachée à la personne (ordre alphabétique fixe), jamais à son rang : un filtre ne la change pas.
  const noms = [...parQui.keys()].sort((a, b) => a.localeCompare(b, "fr"));
  const COULEURS = 7;
  const personnes = [...parQui.values()].sort((a, b) => b.traite - a.traite || b.sans_suite - a.sans_suite);
  const enSerie = personnes.filter((p) => p.valeurs.some(Boolean));
  const gardes = enSerie.slice(0, COULEURS);
  const autres = enSerie.slice(COULEURS);
  const seriesModo = gardes.sort((a, b) => noms.indexOf(a.qui) - noms.indexOf(b.qui))
    .map((p) => ({ nom: p.qui, classe: `p${(noms.indexOf(p.qui) % COULEURS) + 1}`, valeurs: p.valeurs }));
  if (autres.length) seriesModo.push({ nom: `${autres.length} autres`, classe: "autres", valeurs: cs.liste.map((_, i) => autres.reduce((s, p) => s + p.valeurs[i], 0)) });

  const aTraiter = liste.filter((c) => (c.categorie === "insultant" || c.categorie === "question") && (suivi.get(c.code)?.etat || "a_traiter") === "a_traiter").length;
  const examines = nTraites + nSans;

  zone.replaceChildren(
    el("div", { class: "barre-stats carte" },
      el("div", {}, el("span", { class: "etiquette" }, "Période"), segments("periode", Object.fromEntries(Object.entries(PERIODES).map(([k, p]) => [k, p.libelle]))))),
    el("div", { class: "chiffres-cles" },
      tuile("", nTous, "commentaires sur la période"),
      tuile("insultant", nIns, "insultants", nTous ? `${(100 * nIns / nTous).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} % des commentaires` : ""),
      tuile("question", nQue, "questions", nTous ? `${(100 * nQue / nTous).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} % des commentaires` : ""),
      tuile("mots", nMots, "avec un mot surveillé"),
      tuile("ok", nTraites, "marqués « traité »", `${nombre(nSans)} « sans suite » · ${nombre(aTraiter)} insultants ou questions encore à traiter`)),
    graphique({ titre: "Insultants, questions et mots surveillés", cases: cs,
      sous: `Nombre de commentaires reçus, ${cs.pas === "jour" ? "par jour" : "par semaine"}, selon la catégorie donnée par le modèle (ou vérifiée à la lecture).`,
      series: [{ nom: "Insultants", classe: "insultant", valeurs: ins }, { nom: "Questions", classe: "question", valeurs: que },
        { nom: "Avec un mot surveillé", classe: "mots", valeurs: mots }],
      vide: "Aucun commentaire sur cette période." }),
    graphique({ titre: "Commentaires marqués « traité », par modérateur", cases: cs, empile: true,
      sous: `Date de la marque, ${cs.pas === "jour" ? "par jour" : "par semaine"}. Seule la dernière marque d'un commentaire compte : un commentaire remis « à traiter » sort du décompte.`,
      series: seriesModo, vide: "Aucun commentaire marqué « traité » sur cette période." }),
    el("section", { class: "carte bloc-graphe" }, el("h3", {}, "Bilan par modérateur"),
      el("p", { class: "doux sous-titre" }, `Depuis le début (toutes périodes), ${nombre(examines)} commentaires examinés. Le prénom est celui donné à la connexion.`),
      personnes.length ? el("div", { class: "tableau-cadre" }, el("table", { class: "tableau" },
        el("thead", {}, el("tr", {}, el("th", {}, "Modérateur"), el("th", { class: "n" }, "Traités"), el("th", { class: "n" }, "dont insultants"),
          el("th", { class: "n" }, "dont questions"), el("th", { class: "n" }, "Sans suite"), el("th", { class: "n" }, "Part du travail"),
          el("th", { class: "n" }, "7 derniers jours"), el("th", {}, "Dernière marque"))),
        el("tbody", {}, personnes.map((p) => el("tr", {},
          el("td", {}, el("span", { class: `pastille serie-${noms.indexOf(p.qui) < 0 ? "autres" : gardes.includes(p) ? `p${(noms.indexOf(p.qui) % COULEURS) + 1}` : "autres"}` }), " ", p.qui),
          el("td", { class: "n fort-ok" }, nombre(p.traite)), el("td", { class: "n" }, nombre(p.ins)), el("td", { class: "n" }, nombre(p.que)),
          el("td", { class: "n" }, nombre(p.sans_suite)),
          el("td", { class: "n" }, el("span", { class: "jauge", style: `--part:${examines ? (100 * (p.traite + p.sans_suite)) / examines : 0}%` }),
            ` ${examines ? Math.round((100 * (p.traite + p.sans_suite)) / examines) : 0} %`),
          el("td", { class: "n" }, nombre(p.semaine)),
          el("td", {}, p.dernier ? new Date(p.dernier).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "")))),
        el("tfoot", {}, el("tr", {}, el("td", {}, "Total"), el("td", { class: "n" }, nombre(nTraites)),
          el("td", { class: "n" }, nombre(personnes.reduce((s, p) => s + p.ins, 0))), el("td", { class: "n" }, nombre(personnes.reduce((s, p) => s + p.que, 0))),
          el("td", { class: "n" }, nombre(nSans)), el("td", { class: "n" }, "100 %"), el("td", { class: "n" }, nombre(personnes.reduce((s, p) => s + p.semaine, 0))), el("td")))))
        : el("div", { class: "vide" }, "Aucune marque posée pour l'instant.")),
  );
}
