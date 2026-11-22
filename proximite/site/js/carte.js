/* Carte des candidats, en SVG, sans bibliothèque. Deux vues qui se lisent sans manipulation :
   1. Axe par axe : une ligne de -3 à +3 par axe, chaque candidat placé dessus avec son nom ;
   2. Deux axes à la fois : un plan dont on choisit les deux axes, quatre quarts nommés.
   Les noms sont placés sans se chevaucher (étages au-dessus et au-dessous de la ligne, positions autour du point). */
(function () {
  "use strict";

  const MAX = 3;
  const NS = "http://www.w3.org/2000/svg";
  const POLICE = "13px system-ui, -apple-system, 'Segoe UI', sans-serif";
  const POLICE_GRAS = "600 " + POLICE;

  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const signe = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1);
  function svg(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v != null) e.setAttribute(k, v);
    if (parent) parent.append(e);
    return e;
  }
  function texte(parent, x, y, txt, attrs) { const t = svg("text", { x, y, ...attrs }, parent); t.textContent = txt; return t; }
  const mesureur = document.createElement("canvas").getContext("2d");
  function largeur(txt, gras) { mesureur.font = gras ? POLICE_GRAS : POLICE; return mesureur.measureText(txt).width; }

  // --- Bulle et survol communs ---------------------------------------------------------------------------------
  class Survol {
    constructor(bulle, axes, auClic) { this.bulle = bulle; this.axes = axes; this.auClic = auClic; }
    brancher(g, p, cadre) {
      g.style.cursor = "pointer";
      g.addEventListener("mouseenter", e => this.montrer(p, e, cadre));
      g.addEventListener("mousemove", e => this.placer(e, cadre));
      g.addEventListener("mouseleave", () => this.cacher(cadre));
      g.addEventListener("click", () => this.auClic(p.slug));
      g.setAttribute("tabindex", "0"); g.setAttribute("role", "button"); g.setAttribute("aria-label", "Mesures de " + p.nom);
      g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this.auClic(p.slug); } });
    }
    montrer(p, e, cadre) {
      const b = this.bulle; b.replaceChildren();
      const titre = document.createElement("b"); titre.textContent = p.nom; b.append(titre);
      if (p.reference) { const r = document.createElement("i"); r.textContent = "Programme de 2017, pour comparaison"; b.append(r); }
      for (const a of ["E", "O", "S"]) {
        const l = document.createElement("div"), n = document.createElement("span"), v = document.createElement("span");
        n.textContent = this.axes[a].nom; v.textContent = p.connu[a] ? signe(p.pos[a]) : "pas de mesure";
        l.append(n, v); b.append(l);
      }
      b.hidden = false; this.placer(e, cadre);
      cadre.querySelectorAll("[data-slug]").forEach(x => x.classList.toggle("eteint", x.dataset.slug !== p.slug));
    }
    placer(e, cadre) {
      const r = cadre.getBoundingClientRect(), b = this.bulle;
      let x = e.clientX - r.left + 14, y = e.clientY - r.top + 14;
      if (x + b.offsetWidth > r.width - 4) x = e.clientX - r.left - b.offsetWidth - 14;
      if (y + b.offsetHeight > r.height - 4) y = e.clientY - r.top - b.offsetHeight - 14;
      b.style.left = Math.max(4, x) + "px"; b.style.top = Math.max(4, y) + "px";
    }
    cacher(cadre) { this.bulle.hidden = true; cadre.querySelectorAll(".eteint").forEach(x => x.classList.remove("eteint")); }
  }

  function point(g, x, y, p, r) {
    if (p.reference) {
      svg("circle", { cx: x, cy: y, r: r, fill: css("--surface"), stroke: p.couleur, "stroke-width": 3, "stroke-dasharray": "3 2" }, g);
    } else {
      svg("circle", { cx: x, cy: y, r: r, fill: p.couleur, stroke: css("--surface"), "stroke-width": 2 }, g);
    }
  }

  // --- 1. Axe par axe ------------------------------------------------------------------------------------------
  function axeParAxe(zone, points, axes, survol) {
    zone.replaceChildren();
    const W = Math.max(320, zone.clientWidth), m = W < 560 ? 16 : 34;
    const X = v => m + (v + MAX) / (2 * MAX) * (W - 2 * m);
    for (const a of ["E", "O", "S"]) {
      const ax = axes[a], bloc = document.createElement("div"); bloc.className = "axe-ligne";
      const tete = document.createElement("div"); tete.className = "axe-tete";
      const nom = document.createElement("h3"); nom.textContent = ax.nom;
      const poles = document.createElement("div"); poles.className = "poles";
      const g1 = document.createElement("span"), g2 = document.createElement("span");
      g1.className = "pole moins"; g1.textContent = "← " + ax.moins; g2.className = "pole plus"; g2.textContent = ax.plus + " →";
      poles.append(g1, g2); tete.append(nom, poles); bloc.append(tete);

      // Étages des noms : au-dessus (0, 1, 2…) puis au-dessous, en alternance, le plus près possible de la ligne.
      const ps = points.filter(p => p.connu[a]).sort((p, q) => p.pos[a] - q.pos[a]);
      const etages = [];  // etages[i] = liste d'intervalles [g, d] occupés
      const ordre = i => (i % 2 === 0 ? 1 : -1) * (Math.floor(i / 2) + 1); // +1, -1, +2, -2…  (+ : au-dessus)
      const places = ps.map(p => {
        const x = X(p.pos[a]), w = largeur(p.court, true) + 10;
        let g = Math.min(Math.max(x - w / 2, 2), W - w - 2);
        for (let i = 0; ; i++) {
          etages[i] = etages[i] || [];
          if (etages[i].every(([a1, b1]) => g + w < a1 || g > b1)) { etages[i].push([g, g + w]); return { p, x, g, w, niveau: ordre(i) }; }
        }
      });
      const haut = Math.max(1, ...places.map(q => q.niveau)), bas = Math.max(0, ...places.map(q => -q.niveau));
      const PAS = 19, y0 = 14 + haut * PAS + 6, H = y0 + 12 + bas * PAS + 30;
      const s = svg("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: "axe-svg", role: "img",
        "aria-label": `${ax.nom} : position de chaque candidat de -3 à +3` }, bloc);

      // Fond rouge → bleu, graduations
      const def = svg("defs", {}, s), lg = svg("linearGradient", { id: "degrade-" + a }, def);
      svg("stop", { offset: "0%", "stop-color": css("--moins"), "stop-opacity": .9 }, lg);
      svg("stop", { offset: "50%", "stop-color": css("--milieu"), "stop-opacity": 1 }, lg);
      svg("stop", { offset: "100%", "stop-color": css("--plus"), "stop-opacity": .9 }, lg);
      svg("rect", { x: X(-MAX), y: y0 - 3, width: X(MAX) - X(-MAX), height: 6, rx: 3, fill: `url(#degrade-${a})` }, s);
      for (let v = -MAX; v <= MAX; v++) {
        svg("line", { x1: X(v), x2: X(v), y1: y0 + 5, y2: y0 + (v === 0 ? 14 : 9), stroke: css("--muet"), "stroke-width": v === 0 ? 2 : 1 }, s);
        texte(s, X(v), H - 6, (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v), { "text-anchor": "middle", class: "graduation" });
      }
      for (const q of places) {
        const g = svg("g", { "data-slug": q.p.slug, class: "candidat" }, s);
        const yl = q.niveau > 0 ? y0 - 12 - (q.niveau - 1) * PAS : y0 + 24 + (-q.niveau - 1) * PAS;
        const yLien = q.niveau > 0 ? yl + 4 : yl - 13;
        svg("line", { x1: q.x, x2: Math.min(Math.max(q.x, q.g + 4), q.g + q.w - 4), y1: y0, y2: yLien, stroke: q.p.couleur, "stroke-width": 1.2, opacity: .7 }, g);
        const fond = svg("rect", { x: q.g, y: yl - 13, width: q.w, height: 17, rx: 4, fill: css("--surface"), class: "fond-nom" }, g);
        fond.setAttribute("stroke", q.p.couleur); fond.setAttribute("stroke-opacity", .45);
        if (q.p.reference) fond.setAttribute("stroke-dasharray", "3 2");
        texte(g, q.g + q.w / 2, yl, q.p.court, { "text-anchor": "middle", class: "nom-point" });
        point(g, q.x, y0, q.p, 7);
        survol.brancher(g, q.p, zone.parentElement);
      }
      const absents = points.filter(p => !p.connu[a]);
      if (absents.length) {
        const n = document.createElement("p"); n.className = "aide";
        n.textContent = "Sans mesure sur cet axe, donc non placé : " + absents.map(p => p.nom).join(", ") + ".";
        bloc.append(n);
      }
      zone.append(bloc);
    }
  }

  // --- 2. Deux axes à la fois ----------------------------------------------------------------------------------
  function plan(zone, points, axes, survol, ax, ay) {
    zone.replaceChildren();
    const W = Math.max(320, zone.clientWidth), etroit = W < 560;
    const H = Math.round(Math.min(W * (etroit ? 1 : 0.62), 640));
    const mg = etroit ? 14 : 30, mh = 34, mb = etroit ? 52 : 34;
    const X = v => mg + (v + MAX) / (2 * MAX) * (W - 2 * mg);
    const Y = v => mh + (MAX - v) / (2 * MAX) * (H - mh - mb);
    const s = svg("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: "plan-svg", role: "img",
      "aria-label": `Plan : ${axes[ax].nom} en horizontal, ${axes[ay].nom} en vertical` }, zone);

    // Quarts : teinte légère, nom du quart dans son coin
    const quarts = [[1, 1], [-1, 1], [-1, -1], [1, -1]];
    for (const [sx, sy] of quarts) {
      const x1 = sx < 0 ? X(-MAX) : X(0), y1 = sy > 0 ? Y(MAX) : Y(0);
      svg("rect", { x: x1, y: y1, width: X(MAX) - X(0), height: Y(0) - Y(MAX), fill: css("--lavis"), opacity: (sx + sy === 0) ? .5 : 1 }, s);
      if (etroit) continue;  // sur un petit écran, les noms des quarts se chevaucheraient
      const nx = sx < 0 ? axes[ax].moins : axes[ax].plus, ny = sy < 0 ? axes[ay].moins : axes[ay].plus;
      const tx = sx < 0 ? X(-MAX) + 8 : X(MAX) - 8, ty = sy > 0 ? Y(MAX) + 16 : Y(-MAX) - 22;
      texte(s, tx, ty, nx, { "text-anchor": sx < 0 ? "start" : "end", class: "quart" });
      texte(s, tx, ty + 14, "+ " + ny.toLowerCase(), { "text-anchor": sx < 0 ? "start" : "end", class: "quart" });
    }
    for (let v = -MAX; v <= MAX; v++) {
      svg("line", { x1: X(v), x2: X(v), y1: Y(MAX), y2: Y(-MAX), stroke: css(v === 0 ? "--axe" : "--grille"), "stroke-width": v === 0 ? 1.6 : 1 }, s);
      svg("line", { x1: X(-MAX), x2: X(MAX), y1: Y(v), y2: Y(v), stroke: css(v === 0 ? "--axe" : "--grille"), "stroke-width": v === 0 ? 1.6 : 1 }, s);
    }
    // Pôles des axes : horizontal sous le plan (sur deux lignes sur un petit écran), vertical en haut et en bas
    const lx = texte(s, X(-MAX), etroit ? H - 28 : H - 10, "← " + axes[ax].moins, { class: "pole-svg" });
    const rx = texte(s, X(MAX), H - 10, axes[ax].plus + " →", { class: "pole-svg", "text-anchor": "end" });
    if (!etroit) texte(s, X(0), H - 10, "horizontal : " + axes[ax].nom, { class: "nom-axe-svg", "text-anchor": "middle" });
    const ty = texte(s, etroit ? X(-MAX) : X(0) + 8, 22, "↑ " + axes[ay].plus + (etroit ? "" : "   (vertical : " + axes[ay].nom + ")"), { class: "pole-svg" });
    const by = texte(s, etroit ? X(-MAX) + 6 : X(0) + 8, Y(-MAX) - 8, "↓ " + axes[ay].moins, { class: "pole-svg" });
    for (const [t, c] of [[lx, "--moins"], [rx, "--plus"], [ty, "--plus"], [by, "--moins"]]) t.style.fill = css(c);

    // Points, puis noms placés autour sans chevauchement
    const ps = points.filter(p => p.connu[ax] && p.connu[ay]);
    const boites = ps.map(p => { const x = X(p.pos[ax]), y = Y(p.pos[ay]); return [x - 8, y - 8, x + 8, y + 8]; });
    const libre = b => b[0] >= 2 && b[2] <= W - 2 && b[1] >= 2 && b[3] <= H - 2 &&
      boites.every(o => b[2] < o[0] || b[0] > o[2] || b[3] < o[1] || b[1] > o[3]);
    const couche = svg("g", {}, s);
    const ordre = ps.map((p, i) => i).sort((i, j) => ps[i].pos[ax] - ps[j].pos[ax]);
    for (const i of ordre) {
      const p = ps[i], x = X(p.pos[ax]), y = Y(p.pos[ay]), w = largeur(p.court, true) + 8, h = 17;
      let choix = null;
      for (const d of [12, 22, 34, 48, 64]) {
        const essais = [[d, -h / 2], [-d - w, -h / 2], [-w / 2, -d - h + 4], [-w / 2, d - 4], [d * .7, -d * .7 - h], [-d * .7 - w, -d * .7 - h], [d * .7, d * .7], [-d * .7 - w, d * .7]];
        for (const [dx, dy] of essais) {
          const b = [x + dx, y + dy, x + dx + w, y + dy + h];
          if (libre(b)) { choix = b; break; }
        }
        if (choix) break;
      }
      if (!choix) choix = [x + 10, y - h / 2, x + 10 + w, y + h / 2];
      boites.push(choix);
      const g = svg("g", { "data-slug": p.slug, class: "candidat" }, couche);
      const cx = Math.min(Math.max(x, choix[0]), choix[2]), cy = Math.min(Math.max(y, choix[1]), choix[3]);
      if (Math.hypot(cx - x, cy - y) > 14) svg("line", { x1: x, y1: y, x2: cx, y2: cy, stroke: p.couleur, "stroke-width": 1.2, opacity: .7 }, g);
      const fond = svg("rect", { x: choix[0], y: choix[1], width: w, height: h, rx: 4, fill: css("--surface"), class: "fond-nom" }, g);
      fond.setAttribute("stroke", p.couleur); fond.setAttribute("stroke-opacity", .45);
      if (p.reference) fond.setAttribute("stroke-dasharray", "3 2");
      texte(g, choix[0] + w / 2, choix[1] + 13, p.court, { "text-anchor": "middle", class: "nom-point" });
      point(g, x, y, p, 8);
      survol.brancher(g, p, zone.parentElement);
    }
    const absents = points.filter(p => !(p.connu[ax] && p.connu[ay]));
    if (absents.length) {
      const n = document.createElement("p"); n.className = "aide";
      n.textContent = "Non placés (sans mesure sur l'un de ces axes) : " + absents.map(p => p.nom).join(", ") + ".";
      zone.append(n);
    }
  }

  class Carte {
    constructor(zoneAxes, zonePlan, bulle, points, axes, auClic) {
      this.zoneAxes = zoneAxes; this.zonePlan = zonePlan; this.points = points; this.axes = axes;
      this.survol = new Survol(bulle, axes, auClic); this.paire = ["E", "O"];
      let l = 0;
      new ResizeObserver(() => { if (Math.abs(zoneAxes.clientWidth - l) > 4) { l = zoneAxes.clientWidth; this.dessiner(); } }).observe(zoneAxes);
    }
    changerPaire(x, y) { this.paire = [x, y]; plan(this.zonePlan, this.points, this.axes, this.survol, x, y); }
    dessiner() {
      axeParAxe(this.zoneAxes, this.points, this.axes, this.survol);
      plan(this.zonePlan, this.points, this.axes, this.survol, ...this.paire);
    }
  }

  window.Carte = Carte;
})();
