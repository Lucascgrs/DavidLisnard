// Curseur à deux poignées (du… au…, note minimale… maximale), à la souris, au doigt ou au clavier.
import { el } from "./commun.js";

const SVG = "http://www.w3.org/2000/svg";

/**
 * options : min, max, valeurs [a, b], format(v) → texte d'une valeur, plage(a, b) → [texte gauche, texte droite],
 * histo (nombres, un par valeur, affichés derrière la piste), degrade (piste rouge → gris → bleu), bornes [g, d],
 * etiquette (pour les lecteurs d'écran), onchange([a, b]) au lâcher, oninput([a, b]) pendant le glissement.
 */
export function curseur(o) {
  const { min, max } = o;
  let [a, b] = o.valeurs;
  const gauche = el("span"), droite = el("span");
  const element = el("div", { class: `curseur${o.degrade ? " degrade" : ""}${o.degrade === "pert" ? " pert" : ""}` }, el("div", { class: "valeurs" }, gauche, droite));
  let barres = [];
  if (o.histo) {
    const svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("class", "histo");
    svg.setAttribute("viewBox", `-0.5 0 ${o.histo.length} 1`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    const haut = Math.max(1, ...o.histo.map(Math.sqrt));
    barres = o.histo.map((v, i) => {
      const r = document.createElementNS(SVG, "rect");
      const h = v ? Math.max(0.04, Math.sqrt(v) / haut) : 0;
      r.setAttribute("x", i - 0.4); r.setAttribute("width", 0.8);
      r.setAttribute("y", 1 - h); r.setAttribute("height", h);
      svg.append(r);
      return r;
    });
    element.append(svg);
  }
  const plage = el("div", { class: "plage" });
  const masqueG = el("div", { class: "masque", style: { left: 0 } });
  const masqueD = el("div", { class: "masque", style: { right: 0 } });
  const poignees = [0, 1].map((k) => el("button", {
    type: "button", class: "poignee", role: "slider", "aria-valuemin": min, "aria-valuemax": max,
    "aria-label": `${o.etiquette || "valeur"} : ${k ? "maximum" : "minimum"}`,
  }));
  const piste = el("div", { class: "piste" }, el("div", { class: "rail" }, ...(o.degrade ? [masqueG, masqueD] : [])),
    o.degrade ? null : plage, ...poignees);
  element.append(piste);
  if (o.bornes) element.append(el("div", { class: "bornes" }, el("span", {}, o.bornes[0]), el("span", {}, o.bornes[1])));

  const pos = (v) => (max === min ? 0 : (100 * (v - min)) / (max - min));
  function dessiner() {
    const [pa, pb] = [pos(a), pos(b)];
    poignees[0].style.left = `${pa}%`;
    poignees[1].style.left = `${pb}%`;
    plage.style.left = `${pa}%`;
    plage.style.width = `${pb - pa}%`;
    masqueG.style.width = `${pa}%`;
    masqueD.style.width = `${100 - pb}%`;
    const [tg, td] = o.plage ? o.plage(a, b) : [o.format(a), o.format(b)];
    gauche.textContent = tg;
    droite.textContent = td;
    poignees[0].setAttribute("aria-valuenow", a);
    poignees[1].setAttribute("aria-valuenow", b);
    poignees[0].setAttribute("aria-valuetext", o.format(a));
    poignees[1].setAttribute("aria-valuetext", o.format(b));
    barres.forEach((r, i) => r.classList.toggle("dedans", i >= a - min && i <= b - min));
  }

  const valeurDe = (x) => {
    const r = piste.getBoundingClientRect();
    return Math.round(min + Math.min(1, Math.max(0, (x - r.left) / r.width)) * (max - min));
  };
  function placer(k, v) {
    if (k === 0) a = Math.min(Math.max(min, v), b);
    else b = Math.max(Math.min(max, v), a);
    dessiner();
    o.oninput?.([a, b]);
  }
  let actif = null, avant = null;
  piste.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    const v = valeurDe(e.clientX);
    actif = e.target === poignees[0] ? 0 : e.target === poignees[1] ? 1
      : Math.abs(v - a) < Math.abs(v - b) || (Math.abs(v - a) === Math.abs(v - b) && v < a) ? 0 : 1;
    avant = [a, b];
    poignees[actif].classList.add("actif");
    poignees[actif].focus({ preventScroll: true });
    piste.setPointerCapture(e.pointerId);
    placer(actif, v);
    e.preventDefault();
  });
  piste.addEventListener("pointermove", (e) => { if (actif !== null) placer(actif, valeurDe(e.clientX)); });
  const lacher = () => {
    if (actif === null) return;
    poignees[actif].classList.remove("actif");
    actif = null;
    if (avant[0] !== a || avant[1] !== b) o.onchange?.([a, b]);
  };
  piste.addEventListener("pointerup", lacher);
  piste.addEventListener("pointercancel", lacher);
  poignees.forEach((p, k) => p.addEventListener("keydown", (e) => {
    const pas = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -Math.ceil((max - min) / 10), PageUp: Math.ceil((max - min) / 10) }[e.key];
    const v = k ? b : a;
    let nv = pas != null ? v + pas : e.key === "Home" ? min : e.key === "End" ? max : null;
    if (nv == null) return;
    e.preventDefault();
    placer(k, nv);
    o.onchange?.([a, b]);
  }));
  dessiner();
  return {
    element,
    valeurs: () => [a, b],
    fixer([x, y]) { a = x; b = y; dessiner(); },
  };
}
