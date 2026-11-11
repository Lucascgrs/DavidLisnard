// Carte d'un commentaire dans une liste, et sa fiche détaillée (panneau latéral) : texte entier, commentaire
// auquel il répond, les cinq notes expliquées, la vidéo ou le post d'origine.
import { CRITERES, TITRES, SOURCES, GROUPES, BORNES, el, nombre, dateLongue, dateCourte, ton, sens, lienOriginal } from "./commun.js";
import { commentaire as lireCommentaire } from "./donnees.js";

const FIABILITES = {
  bonne: "Fiabilité bonne : le modèle est sûr de lui, notamment qu'il s'agit bien de David Lisnard.",
  moyenne: "Fiabilité moyenne : notes probables, à lire avec un peu de recul.",
  faible: "Fiabilité faible : le modèle hésite, souvent sur le fait que le commentaire parle de lui.",
  "corrigée": "Notes vérifiées à la main.",
  relue: "Notes relues et données une à une par Claude (et non par le modèle).",
};

/** La carte cliquable d'une liste. */
export function carte(c, { critere } = {}) {
  const pub = c.publications || {};
  const notes = (critere ? [critere, ...CRITERES.filter((k) => k !== critere)] : CRITERES).map((k) =>
    el("span", { class: `badge ${c.cible === "A" && k !== "pertinence" ? "neutre" : ton(k, c[k])}`, title: `${TITRES[k]} : ${c[k]}/20, ${sens(k, c[k])}` },
      `${TITRES[k]} ${c[k]}`));
  const b = el("button", { type: "button", class: "commentaire", onclick: () => ouvrir(c) },
    el("div", { class: "haut-c" },
      el("span", { class: "compte" }, c.compte),
      el("span", {}, `${SOURCES[c.source]} · ${dateCourte(c.date)}`),
      pub.titre ? el("span", { class: "titre-pub" }, `· ${pub.titre}`) : null),
    c.reponse ? el("div", { class: "reponse-a" }, "↳ en réponse à un autre commentaire") : null,
    el("div", { class: "texte" }, c.texte),
    el("div", { class: "bas-c" }, ...notes,
      c.cible === "A" ? el("span", { class: "badge neutre", title: "Le commentaire parle d'autre chose : ses notes restent neutres." }, "ne parle pas de lui") : null,
      c.likes ? el("span", { class: "likes" }, `${nombre(c.likes)} j'aime`) : null));
  return b;
}

let fond = null, retourFocus = null;

function fermer() {
  if (!fond) return;
  const f = fond;
  fond = null;
  f.classList.remove("visible");
  setTimeout(() => f.remove(), 180);
  document.body.style.overflow = "";
  const u = new URL(location.href);
  if (u.searchParams.has("c")) { u.searchParams.delete("c"); history.replaceState(null, "", u); }
  retourFocus?.focus?.();
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape") fermer(); });

function echelle(c, k) {
  const neutre = c.cible === "A" && k !== "pertinence";
  return el("div", { class: "echelle" },
    el("div", { class: "nom" }, TITRES[k]),
    el("div", { class: `regle${k === "pertinence" ? " pert" : ""}`, title: `0 ${BORNES[k][0]} · 10 ${BORNES[k][1]} · 20 ${BORNES[k][2]}` },
      el("div", { class: "marque-note", style: { left: `${(100 * c[k]) / 20}%` } })),
    el("div", { class: "valeur-note" }, el("b", {}, `${c[k]}/20`), ` · ${neutre ? "sans objet" : sens(k, c[k])}`));
}

function lecteur(pub) {
  const bouton = el("button", { type: "button", class: "lecteur", "aria-label": "Lire la vidéo" },
    el("img", { src: `https://i.ytimg.com/vi/${pub.code}/hqdefault.jpg`, alt: "", loading: "lazy" }),
    el("span", { class: "jouer", html: '<svg width="22" height="22" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>' }));
  // La vidéo n'est chargée qu'au clic (youtube-nocookie : pas de traceur avant la lecture).
  bouton.addEventListener("click", () => {
    bouton.replaceChildren(el("iframe", {
      src: `https://www.youtube-nocookie.com/embed/${pub.code}?autoplay=1&rel=0`, title: pub.titre || "Vidéo",
      allow: "autoplay; encrypted-media; picture-in-picture; fullscreen", allowfullscreen: true,
    }));
    bouton.style.cursor = "default";
  }, { once: true });
  return bouton;
}

/** Ouvre la fiche d'un commentaire (objet complet, ou clé à relire). */
export async function ouvrir(c) {
  if (typeof c === "string") {
    c = await lireCommentaire(c).catch(() => null);
    if (!c) return;
  }
  fermer();
  retourFocus = document.activeElement;
  const pub = c.publications || {};
  const parent = el("div");
  const boutonFermer = el("button", { type: "button", class: "fermer", "aria-label": "Fermer", onclick: fermer }, "×");
  const panneau = el("div", { class: "fiche", role: "dialog", "aria-modal": "true", "aria-label": "Commentaire" },
    boutonFermer,
    el("p", { class: "meta-c" }, el("b", {}, c.compte), ` · ${SOURCES[c.source]} · ${GROUPES[c.groupe] || ""} · ${dateLongue(c.date)}`,
      c.likes ? ` · ${nombre(c.likes)} j'aime` : "", c.mots ? ` · ${nombre(c.mots)} mots` : ""),
    parent,
    el("p", { class: "texte-complet" }, c.texte),
    el("h3", {}, "Les notes du modèle"),
    c.cible === "A"
      ? el("p", { class: "doux petit" }, "Le modèle estime que ce commentaire parle d'autre chose que de David Lisnard : tonalité, forme, système et idées restent donc neutres (10).")
      : null,
    ...CRITERES.map((k) => echelle(c, k)),
    el("p", { class: "pale petit" }, FIABILITES[c.fiabilite] || ""),
    el("h3", {}, c.source === "youtube" ? "La vidéo" : c.source === "bluesky" ? "Le fil" : "Le post"),
    el("div", { class: "publication" },
      c.source === "youtube" && pub.code ? lecteur(pub) : null,
      el("div", { class: "titre-pub" }, pub.titre || (c.source === "bluesky" ? "Ce message ouvre le fil." : "(sans titre)")),
      el("div", { class: "pale petit" }, `${c.compte}${pub.date ? ` · publié le ${dateLongue(pub.date)}` : ""}`),
      el("div", { class: "actions" },
        el("a", { class: "bouton plein", href: lienOriginal(c), target: "_blank", rel: "noopener" },
          c.source === "youtube" ? "Voir le commentaire sur YouTube" : c.source === "bluesky" ? "Voir le message sur Bluesky" : "Ouvrir le post sur Instagram"),
        c.source === "bluesky" && pub.lien && pub.lien !== lienOriginal(c) ? el("a", { class: "bouton", href: pub.lien, target: "_blank", rel: "noopener" }, "Début du fil") : null,
        c.source === "youtube" && pub.lien ? el("a", { class: "bouton", href: pub.lien, target: "_blank", rel: "noopener" }, "Vidéo sur YouTube") : null)),
  );
  fond = el("div", { class: "fiche-fond", onclick: (e) => { if (e.target === fond) fermer(); } }, panneau);
  document.body.append(fond);
  document.body.style.overflow = "hidden";
  requestAnimationFrame(() => fond?.classList.add("visible"));
  boutonFermer.focus({ preventScroll: true });
  const u = new URL(location.href);
  u.searchParams.set("c", c.cle);
  history.replaceState(null, "", u);
  if (c.parent) {
    const p = await lireCommentaire(c.parent).catch(() => null);
    if (p) parent.replaceChildren(el("div", { class: "parent" }, el("div", { class: "reponse-a" }, `En réponse à ce commentaire (${dateCourte(p.date)}) :`), p.texte));
  } else if (c.reponse) {
    parent.replaceChildren(el("div", { class: "parent pale" }, "En réponse à un commentaire qui n'est pas dans le corpus."));
  }
}

/** Ouvre la fiche demandée dans l'adresse (?c=…), pour les liens partagés. */
export function ouvrirDepuisAdresse() {
  const cle = new URL(location.href).searchParams.get("c");
  if (cle) ouvrir(cle);
}
