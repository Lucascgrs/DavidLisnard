(function () {
  "use strict";
  const D = window.DONNEES;
  const AXES = ["E", "O", "S"];
  const ST = D.sous_themes;
  const GROUPES = { gauche: "Gauche", centre: "Centre", droite: "Droite et extrême droite", autres: "Autres, sans étiquette" };
  const $ = s => document.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const signe = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1);
  const fr = n => n.toLocaleString("fr-FR");

  // Candidats rangés de l'intervention au libéralisme (axe économique) ; ceux sans aucune position à la fin.
  const sansAxe = c => AXES.every(a => !c.axes[a].connu);
  const C = [...D.candidats].sort((a, b) => (sansAxe(a) - sansAxe(b)) || (a.axes.E.position - b.axes.E.position));
  const parSlug = Object.fromEntries(C.map(c => [c.slug, c]));
  const placés = C.filter(c => !sansAxe(c));

  function initiales(nom) { return nom.split(/[\s-]+/).filter(Boolean).map(m => m[0]).slice(0, 2).join("").toUpperCase(); }
  function couleurGroupe(g) { return css("--" + g); }

  // Couleurs des cases : divergent rouge (−) / gris / bleu (+) ; séquentiel bleu pour la proximité.
  function hex(h) { h = h.replace("#", ""); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); }
  function melange(a, b, t) { const x = hex(a), y = hex(b); return "rgb(" + x.map((v, i) => Math.round(v + (y[i] - v) * t)).join(",") + ")"; }
  function teinteNote(v) {
    const t = Math.min(1, Math.abs(v) / 2);
    return { fond: melange(css("--milieu"), css(v < 0 ? "--moins" : "--plus"), t), clair: t > 0.55 };
  }
  function teinteProche(d100) {
    const t = 1 - Math.min(1, d100 / 50);
    return { fond: melange(css("--milieu"), css("--plus"), t), clair: t > 0.55 };
  }
  function peindre(td, teinte) { td.style.background = teinte.fond; td.style.color = teinte.clair ? "#fff" : ""; }

  // --- En-tête et pied -----------------------------------------------------------------------------------------
  const date = (D.genere_le || "").slice(0, 10).split("-").reverse().join("/");
  $("#pied").textContent = `Premier essai, à refaire quand tous les programmes seront publiés. Liste des candidats et des programmes : ${D.source} (export du ${(D.export_du || "").slice(0, 10).split("-").reverse().join("/")}). Mesures relevées et notées le ${date}.`;

  // --- Cartouches ----------------------------------------------------------------------------------------------
  function lienProgramme(c) {
    const p = c.programme;
    return p.source || p.en_ligne || p.pdf;
  }
  function miniAxes(c) {
    const bloc = el("div", "mini-axes");
    for (const a of AXES) {
      const ax = c.axes[a], ligne = el("div", "mini-axe");
      ligne.append(el("span", null, D.axes[a].nom.split(" ")[0]));
      const piste = el("div", "mini-piste");
      if (ax.connu) {
        const pt = el("span", "mini-point");
        pt.style.left = (50 + ax.position / D.note_max * 50) + "%";
        pt.style.background = couleurGroupe(c.groupe);
        piste.append(pt);
      }
      ligne.append(piste, el("span", "mini-valeur" + (ax.connu ? "" : " inconnu"), ax.connu ? signe(ax.position) : "—"));
      bloc.append(ligne);
    }
    return bloc;
  }
  function cartouches() {
    const zone = $("#cartouches");
    const refs = C.filter(c => c.reference);
    let zoneRef = null;
    if (refs.length) {
      const titre = el("h3", "sous-section", "Pour comparaison");
      const note = el("p", "aide", "Un ancien programme, lu et noté selon la même grille, pour situer les candidats de 2027 par rapport à lui.");
      zoneRef = el("div", "cartouches");
      zone.after(titre, note, zoneRef);
    }
    for (const c of C) {
      const carte = el("article", "cartouche");
      carte.tabIndex = 0; carte.setAttribute("role", "button"); carte.setAttribute("aria-label", "Mesures de " + c.nom);
      const tete = el("div", "cartouche-tete");
      const pastille = el("span", "pastille " + c.groupe, initiales(c.nom));
      pastille.style.background = couleurGroupe(c.groupe);
      const id = el("div");
      id.append(el("div", "cartouche-nom", c.nom), el("div", "cartouche-parti", c.parti || "Sans étiquette"));
      tete.append(pastille, id);
      const titre = el("div", "cartouche-titre", c.programme.titre || "Programme en ligne");
      const pied = el("div", "cartouche-pied");
      pied.append(el("span", null, `${fr(c.mesures)} mesures`));
      const lien = lienProgramme(c);
      if (lien) {
        const a = el("a", "lien-programme", (c.programme.pdf && !c.programme.en_ligne ? "PDF" : "Programme") + " ↗");
        a.href = lien; a.target = "_blank"; a.rel = "noopener";
        a.addEventListener("click", e => e.stopPropagation());
        pied.append(a);
      }
      carte.append(tete, titre, miniAxes(c), pied);
      carte.addEventListener("click", () => ouvrir(c.slug));
      carte.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ouvrir(c.slug); } });
      if (c.reference) carte.classList.add("reference");
      (c.reference ? zoneRef : zone).append(carte);
    }
    const att = $("#attente");
    $("#attente-titre").textContent = `Sans programme publié (${D.en_attente.length})`;
    for (const c of D.en_attente.sort((a, b) => a.nom.localeCompare(b.nom, "fr"))) {
      att.append(el("li", null, c.parti ? `${c.nom} · ${c.parti}` : c.nom));
    }
  }

  // --- Carte ---------------------------------------------------------------------------------------------------
  let carte;
  function cartePositions() {
    const leg = $("#legende");
    const groupesPresents = Object.keys(GROUPES).filter(g => placés.some(c => c.groupe === g && !c.reference));
    for (const g of groupesPresents) {
      const s = el("span"), i = el("i"); i.style.background = couleurGroupe(g); s.append(i, GROUPES[g]); leg.append(s);
    }
    if (placés.some(c => c.reference)) {
      const s = el("span"), i = el("i", "anneau"); s.append(i, "Programme de 2017, pour comparaison"); leg.append(s);
    }
    const points = () => placés.map(c => ({
      slug: c.slug, nom: c.nom, court: c.court || c.nom, reference: c.reference, couleur: couleurGroupe(c.groupe),
      pos: Object.fromEntries(AXES.map(a => [a, c.axes[a].position])),
      connu: Object.fromEntries(AXES.map(a => [a, c.axes[a].connu])),
    }));
    carte = new window.Carte($("#axes-ligne"), $("#plan"), $("#bulle"), points(), D.axes, ouvrir);
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { carte.points = points(); carte.dessiner(); });
    const boutons = document.querySelectorAll("#paires [data-paire]");
    boutons.forEach(b => b.addEventListener("click", () => {
      boutons.forEach(x => x.classList.toggle("actif", x === b));
      carte.changerPaire(b.dataset.paire[0], b.dataset.paire[1]);
    }));
    carte.dessiner();
  }

  // --- Clés de lecture : deux bornes en gras et en couleur, les cases intermédiaires --------------------------
  function cle(zone, gauche, droite, cases) {
    zone.replaceChildren();
    const g = el("div", "borne moins"), d = el("div", "borne plus");
    g.append(el("b", null, gauche[0]), el("span", null, gauche[1]));
    d.append(el("b", null, droite[0]), el("span", null, droite[1]));
    const echelle = el("div", "echelle");
    for (const [txt, teinte] of cases) { const c = el("span", null, txt); peindre(c, teinte); echelle.append(c); }
    zone.append(g, echelle, d);
  }

  // --- Distances -----------------------------------------------------------------------------------------------
  function boutonNom(c) { const b = el("button", null, c.nom); b.type = "button"; b.addEventListener("click", () => ouvrir(c.slug)); return b; }
  // Distance sur 100 : sur tous les axes (euclidienne, 100 = coins opposés du cube), ou sur un seul (écart des
  // positions, 100 = l'un à −3 et l'autre à +3). Sur un seul axe, un candidat sans mesure sur cet axe n'a pas de distance.
  let axeDistances = "tout";
  function distance100(a, b, axe) {
    if (axe === "tout") return Math.round(D.distances[a.slug][b.slug] / D.distance_max * 100);
    if (!a.axes[axe].connu || !b.axes[axe].connu) return null;
    return Math.round(Math.abs(a.axes[axe].position - b.axes[axe].position) / (D.note_max - D.note_min) * 100);
  }
  function matrice() {
    const onglets = $("#distances-axes"), t = $("#matrice");
    if (!onglets.children.length) {
      for (const [k, nom] of [["tout", "Tous les thèmes"], ...AXES.map(a => [a, D.axes[a].nom])]) {
        const b = el("button", k === axeDistances ? "actif" : null, nom); b.type = "button";
        b.addEventListener("click", () => {
          axeDistances = k; onglets.querySelectorAll("button").forEach(x => x.classList.toggle("actif", x === b)); matrice();
        });
        onglets.append(b);
      }
      // Survol : la ligne et la colonne de la case sont soulignées
      t.addEventListener("mouseover", e => {
        const td = e.target.closest("td, th.col"); if (!td) return;
        const j = td.dataset.col;
        t.querySelectorAll(".croise").forEach(x => x.classList.remove("croise"));
        t.querySelectorAll(`[data-col="${j}"]`).forEach(x => x.classList.add("croise"));
        const tr = td.closest("tr"); if (tr && tr.parentElement.tagName === "TBODY") tr.querySelector("th").classList.add("croise");
      });
      t.addEventListener("mouseleave", () => t.querySelectorAll(".croise").forEach(x => x.classList.remove("croise")));
    }
    const axe = axeDistances;
    // Seule l'échelle des teintes, sans les deux encadrés des bornes
    const echelle = el("div", "echelle");
    for (const v of [0, 10, 20, 30, 40, 50]) { const c = el("span", null, String(v)); peindre(c, teinteProche(v)); echelle.append(c); }
    $("#cle-distances").replaceChildren(echelle);
    t.replaceChildren();
    const thead = el("thead"), tr = el("tr");
    tr.append(el("th", "nom"));
    placés.forEach((c, j) => {
      const th = el("th", "col" + (c.reference ? " ref" : ""), c.court || c.nom); th.dataset.col = j; th.title = c.nom;
      tr.append(th);
    });
    thead.append(tr); t.append(thead);
    const corps = el("tbody");
    for (const a of placés) {
      const ligne = el("tr"), th = el("th", "nom" + (a.reference ? " ref" : "")); th.append(boutonNom(a)); ligne.append(th);
      placés.forEach((b, j) => {
        const d100 = a === b ? null : distance100(a, b, axe);
        const td = el("td", a === b ? "soi" : d100 == null ? "vide" : null, a === b ? "·" : d100 == null ? "—" : String(d100));
        td.dataset.col = j;
        if (d100 != null) { peindre(td, teinteProche(d100)); td.title = `${a.nom} – ${b.nom} : ${d100} / 100`; }
        else if (a !== b) td.title = "Pas de mesure sur cet axe";
        ligne.append(td);
      });
      corps.append(ligne);
    }
    t.append(corps);
  }

  // --- Notes par thème : un axe à la fois ----------------------------------------------------------------------
  let axeNotes = "E";
  function tableauNotes() {
    const onglets = $("#notes-axes");
    if (!onglets.children.length) {
      for (const a of AXES) {
        const b = el("button", a === axeNotes ? "actif" : null, D.axes[a].nom); b.type = "button";
        b.addEventListener("click", () => {
          axeNotes = a; onglets.querySelectorAll("button").forEach(x => x.classList.toggle("actif", x === b)); tableauNotes();
        });
        onglets.append(b);
      }
    }
    const a = axeNotes, ax = D.axes[a];
    cle($("#cle-notes"), ["−3", ax.moins], ["+3", ax.plus],
      [-3, -2, -1, 0, 1, 2, 3].map(v => [(v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v), teinteNote(v)]));
    const t = $("#tableau-notes"); t.replaceChildren();
    const codes = Object.keys(ST).filter(k => ST[k].axe === a);
    const thead = el("thead"), l = el("tr");
    l.append(el("th", "nom"), el("th", "sous-th total", "Position sur l'axe"));
    for (const k of codes) {
      // Nom du sous-thème, puis ce que veut dire une note vers −3 (rouge) ou vers +3 (bleu)
      const th = el("th", "sous-th"), sens = el("div", "sens");
      sens.append(el("span", "moins", "−3 " + ST[k].moins), el("span", "plus", "+3 " + ST[k].plus));
      th.append(el("div", "st-nom", ST[k].nom), sens);
      l.append(th);
    }
    thead.append(l); t.append(thead);
    const corps = el("tbody");
    const ordre = [...C].sort((x, y) => (!x.axes[a].connu - !y.axes[a].connu) || (x.axes[a].position - y.axes[a].position));
    for (const c of ordre) {
      const ligne = el("tr"), th = el("th", "nom" + (c.reference ? " ref" : "")); th.append(boutonNom(c)); ligne.append(th);
      const axc = c.axes[a], td = el("td", "axe-total");
      if (axc.connu) { td.textContent = signe(axc.position); peindre(td, teinteNote(axc.position)); }
      else { td.textContent = "—"; td.classList.add("vide"); }
      ligne.append(td);
      for (const k of codes) {
        const s = c.sous_themes[k], cell = el("td");
        if (s && s.note != null) { cell.textContent = signe(s.note); peindre(cell, teinteNote(s.note)); }
        else { cell.textContent = "—"; cell.classList.add("vide"); }
        cell.title = `${c.nom} · ${ST[k].nom}`;
        ligne.append(cell);
      }
      corps.append(ligne);
    }
    t.append(corps);
  }

  // --- Fiche d'un candidat -------------------------------------------------------------------------------------
  const fiche = $("#fiche");
  let courant = null, filtreAxe = "tout";
  function ouvrir(slug) {
    const c = parSlug[slug]; if (!c) return;
    courant = c; filtreAxe = "tout"; $("#fiche-recherche").value = "";
    $("#fiche-nom").textContent = c.nom;
    const p = $("#fiche-parti"); p.replaceChildren(c.parti || "Sans étiquette", ` · ${fr(c.mesures)} mesures`);
    const lien = lienProgramme(c);
    if (lien) { const a = el("a", null, (c.programme.titre || "Le programme") + " ↗"); a.href = lien; a.target = "_blank"; a.rel = "noopener"; p.append(a); }
    const axes = $("#fiche-axes"); axes.replaceChildren();
    for (const a of AXES) {
      const ax = c.axes[a], bloc = el("div", "fiche-axe"), h = el("h3");
      h.append(D.axes[a].nom, el("span", null, ax.connu ? signe(ax.position) : "pas de mesure"));
      bloc.append(h);
      for (const k of Object.keys(ST).filter(k => ST[k].axe === a)) {
        const s = c.sous_themes[k]; if (!s || s.note == null) continue;
        const ligne = el("div", "barre-st"), piste = el("div", "piste"), r = el("div", "remplissage");
        const w = Math.abs(s.note) / D.note_max * 50;
        r.style.left = (s.note < 0 ? 50 - w : 50) + "%"; r.style.width = w + "%";
        r.style.background = css(s.note < 0 ? "--moins" : "--plus");
        piste.append(r);
        ligne.append(el("span", null, ST[k].nom), piste, el("span", "v", signe(s.note)));
        ligne.title = `${s.mesures} mesures`;
        bloc.append(ligne);
      }
      axes.append(bloc);
    }
    const onglets = $("#fiche-onglets"); onglets.replaceChildren();
    for (const [k, nom] of [["tout", "Tout"], ...AXES.map(a => [a, D.axes[a].nom]), ["H", "Hors axes"]]) {
      const n = c.liste.filter(m => k === "tout" || (k === "H" ? !ST[m[0]].axe : ST[m[0]].axe === k)).length;
      if (!n && k !== "tout") continue;
      const b = el("button", k === "tout" ? "actif" : null, `${nom} (${n})`); b.type = "button";
      b.addEventListener("click", () => { filtreAxe = k; onglets.querySelectorAll("button").forEach(x => x.classList.toggle("actif", x === b)); listeMesures(); });
      onglets.append(b);
    }
    listeMesures();
    if (!fiche.open) fiche.showModal();
    fiche.scrollTop = 0;
  }
  function listeMesures() {
    const c = courant, zone = $("#fiche-mesures"), q = $("#fiche-recherche").value.trim().toLowerCase();
    zone.replaceChildren();
    let total = 0;
    for (const k of Object.keys(ST)) {
      if (filtreAxe !== "tout" && (filtreAxe === "H" ? ST[k].axe : ST[k].axe !== filtreAxe)) continue;
      const ms = c.liste.filter(m => m[0] === k && (!q || m[2].toLowerCase().includes(q)));
      if (!ms.length) continue;
      total += ms.length;
      const g = el("div", "groupe-st"), h = el("h4");
      const s = c.sous_themes[k];
      h.append((ST[k].axe ? D.axes[ST[k].axe].nom + " · " : "") + ST[k].nom,
        el("span", null, s && s.note != null ? `moyenne ${signe(s.note)} · ${ms.length} mesure${ms.length > 1 ? "s" : ""}` : `${ms.length} mesure${ms.length > 1 ? "s" : ""}`));
      g.append(h);
      for (const [, note, texte] of ms.sort((a, b) => (a[1] ?? 0) - (b[1] ?? 0))) {
        const ligne = el("div", "mesure");
        const puce = el("span", "puce-note" + (note == null ? " hors" : ""), note == null ? "·" : (note > 0 ? "+" : note < 0 ? "−" : "") + Math.abs(note));
        if (note != null) peindre(puce, note === 0 ? { fond: css("--milieu"), clair: false } : teinteNote(note * 2 / 3));
        ligne.append(puce, el("span", null, texte));
        g.append(ligne);
      }
      zone.append(g);
    }
    if (!total) zone.append(el("p", "rien", "Aucune mesure."));
  }
  $("#fiche-recherche").addEventListener("input", listeMesures);
  $("#fiche-fermer").addEventListener("click", () => fiche.close());
  fiche.addEventListener("click", e => { if (e.target === fiche) fiche.close(); });

  cartouches(); cartePositions(); matrice(); tableauNotes();
})();
