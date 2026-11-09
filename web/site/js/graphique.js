// Graphique d'évolution : courbes (un seul axe) et, dessous, le nombre de commentaires de chaque période.
// Survol : ligne verticale, points et info-bulle ; les courbes sont nommées au bout, à droite.
import { el, nombre } from "./commun.js";

const SVG = "http://www.w3.org/2000/svg";
const s = (tag, attrs = {}) => {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
};

/**
 * options : points [{ n, valeurs: { cle: nombre|null } }], series [{ cle, nom, couleur }], yMax, yPas,
 * formatY(v), etiquetteX(i) → texte ou null (graduation), titreBulle(i), hauteur.
 */
export function evolution(conteneur, o) {
  const racine = el("div", { class: "graphique" });
  const bulle = el("div", { class: "info-bulle", role: "status" });
  conteneur.replaceChildren(
    el("div", { class: "legende-graph" }, ...o.series.map((x) => el("span", { style: { "--c": x.couleur } }, x.nom))),
    racine,
  );
  const dessiner = () => {
    const L = Math.max(280, racine.clientWidth);
    const H = o.hauteur || 250, HV = 64, M = { g: 44, d: 78, h: 10, b: 26 };
    const n = o.points.length;
    const lx = L - M.g - M.d, ly = H - M.h - M.b;
    const pasX = n > 1 ? lx / (n - 1) : 0;
    const x = (i) => M.g + (n > 1 ? i * pasX : lx / 2);
    const y = (v) => M.h + ly * (1 - v / o.yMax);
    const svg = s("svg", { viewBox: `0 0 ${L} ${H}`, height: H, role: "img", "aria-label": o.description || "évolution" });
    const grille = s("g", { class: "grille" }), axe = s("g", { class: "axe" });
    for (let v = 0; v <= o.yMax + 1e-9; v += o.yPas) {
      grille.append(s("line", { x1: M.g, x2: L - M.d, y1: y(v), y2: y(v), class: v === 0 ? "zero" : "" }));
      const t = s("text", { x: M.g - 8, y: y(v) + 4, "text-anchor": "end" });
      t.textContent = o.formatY(v);
      axe.append(t);
    }
    let dernierX = -Infinity;
    for (let i = 0; i < n; i++) {
      const etiquette = o.etiquetteX(i);
      if (!etiquette || x(i) - dernierX < 56) continue;
      dernierX = x(i);
      const t = s("text", { x: x(i), y: H - 6, "text-anchor": i === 0 && n > 1 ? "start" : "middle" });
      t.textContent = etiquette;
      axe.append(t);
    }
    svg.append(grille, axe);
    if (o.repere != null) {
      const g = s("g", { class: "reperes" });
      g.append(s("line", { x1: M.g, x2: L - M.d, y1: y(o.repere), y2: y(o.repere) }));
      svg.append(g);
    }
    const etiquettes = [];
    for (const serie of o.series) {
      let d = "", leve = true, dernier = null;
      o.points.forEach((p, i) => {
        const v = p.valeurs[serie.cle];
        if (v == null) { leve = true; return; }
        d += `${leve ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
        leve = false;
        dernier = i;
      });
      const courbe = s("path", { d, class: "courbe" });
      courbe.style.stroke = serie.couleur;
      svg.append(courbe);
      // Points isolés (sans voisin) : un petit rond, sinon ils seraient invisibles.
      o.points.forEach((p, i) => {
        const v = p.valeurs[serie.cle];
        if (v != null && o.points[i - 1]?.valeurs[serie.cle] == null && o.points[i + 1]?.valeurs[serie.cle] == null)
          svg.append(Object.assign(s("circle", { cx: x(i), cy: y(v), r: 3 }), { style: `fill:${serie.couleur}` }));
      });
      if (dernier != null) etiquettes.push({ serie, y: y(o.points[dernier].valeurs[serie.cle]), v: o.points[dernier].valeurs[serie.cle] });
    }
    etiquettes.sort((p, q) => p.y - q.y);
    for (let i = 1; i < etiquettes.length; i++) etiquettes[i].y = Math.max(etiquettes[i].y, etiquettes[i - 1].y + 16);
    for (const e of etiquettes) {
      const t = s("text", { x: L - M.d + 8, y: e.y + 4, class: "etiquette-serie", fill: "currentColor" });
      t.textContent = `${e.serie.nom} ${o.formatY(e.v, true)}`;
      t.style.color = "var(--doux)";
      svg.append(t);
    }
    const guide = s("line", { y1: M.h, y2: H - M.b, stroke: "var(--pale)", "stroke-width": 1, visibility: "hidden" });
    svg.append(guide);
    const marques = o.series.map((x) => {
      const c = s("circle", { r: 4.5, class: "point", visibility: "hidden" });
      c.style.fill = x.couleur;
      svg.append(c);
      return c;
    });

    // Volume : barres du nombre de commentaires, même axe des x, sa propre échelle.
    const vol = s("svg", { viewBox: `0 0 ${L} ${HV}`, height: HV, "aria-hidden": "true" });
    const nMax = Math.max(1, ...o.points.map((p) => p.n));
    const lb = Math.max(1, Math.min(18, (n > 1 ? pasX : lx) * 0.7));
    const barres = o.points.map((p, i) => {
      const h = p.n ? Math.max(1.5, (HV - 18) * p.n / nMax) : 0;
      const r = s("rect", { x: x(i) - lb / 2, y: HV - 2 - h, width: lb, height: h, rx: Math.min(3, lb / 2), class: "barre" });
      vol.append(r);
      return r;
    });
    const tv = s("text", { x: M.g - 8, y: 12, "text-anchor": "end", class: "axe" });
    tv.textContent = nombre(nMax);
    tv.style.fill = "var(--pale)"; tv.style.fontSize = "11.5px";
    vol.append(tv);
    vol.append(s("line", { x1: M.g, x2: L - M.d, y1: HV - 1.5, y2: HV - 1.5, stroke: "var(--bord-fort)" }));

    let survol = -1;
    const montrer = (clientX) => {
      const r = svg.getBoundingClientRect();
      const px = ((clientX - r.left) / r.width) * L;
      const i = Math.max(0, Math.min(n - 1, Math.round(n > 1 ? (px - M.g) / pasX : 0)));
      if (i === survol) return;
      if (survol >= 0) barres[survol]?.classList.remove("survol");
      survol = i;
      barres[i]?.classList.add("survol");
      guide.setAttribute("x1", x(i)); guide.setAttribute("x2", x(i)); guide.setAttribute("visibility", "visible");
      o.series.forEach((serie, k) => {
        const v = o.points[i].valeurs[serie.cle];
        marques[k].setAttribute("visibility", v == null ? "hidden" : "visible");
        if (v != null) { marques[k].setAttribute("cx", x(i)); marques[k].setAttribute("cy", y(v)); }
      });
      const p = o.points[i];
      bulle.replaceChildren(el("div", { class: "t" }, o.titreBulle(i)),
        ...o.series.map((serie) => el("div", { class: "l" }, el("span", {}, el("i", { style: { "--c": serie.couleur } }), serie.nom),
          el("b", {}, p.valeurs[serie.cle] == null ? "trop peu" : o.formatY(p.valeurs[serie.cle], true)))),
        ...(o.lignesBulle ? o.lignesBulle(i) : []).map(([k, v]) => el("div", { class: "l" }, el("span", {}, k), el("b", {}, v))),
        el("div", { class: "l" }, el("span", {}, "commentaires"), el("b", {}, nombre(p.n))));
      bulle.classList.add("visible");
      const largeur = racine.clientWidth, xp = (x(i) / L) * largeur;
      bulle.style.left = `${Math.min(largeur - bulle.offsetWidth - 4, Math.max(4, xp + 14 + bulle.offsetWidth > largeur ? xp - bulle.offsetWidth - 14 : xp + 14))}px`;
      bulle.style.top = "8px";
    };
    const cacher = () => {
      bulle.classList.remove("visible");
      guide.setAttribute("visibility", "hidden");
      marques.forEach((m) => m.setAttribute("visibility", "hidden"));
      if (survol >= 0) barres[survol]?.classList.remove("survol");
      survol = -1;
    };
    for (const cible of [svg, vol]) {
      cible.addEventListener("pointermove", (e) => montrer(e.clientX));
      cible.addEventListener("pointerleave", cacher);
    }
    racine.replaceChildren(svg, el("div", { class: "sous-titre-graph" }, o.titreVolume || "Nombre de commentaires"), vol, bulle);
  };
  dessiner();
  let largeur = racine.clientWidth;
  conteneur._observateur?.disconnect();
  const ro = conteneur._observateur = new ResizeObserver(() => { if (Math.abs(racine.clientWidth - largeur) > 4) { largeur = racine.clientWidth; dessiner(); } });
  ro.observe(racine);
}
