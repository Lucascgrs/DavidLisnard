// Lisnard à l'épreuve des chiffres : filtres, recherche et ouverture des affirmations.
// Aucune donnée n'est chargée : tout est déjà dans la page.

(function () {
  "use strict";

  // Filtres par verdict (plusieurs à la fois), par thème et par mot, sur la liste désignée par data-filtres.
  document.querySelectorAll("[data-filtres]").forEach(function (zone) {
    var liste = document.querySelector(zone.dataset.filtres);
    if (!liste) return;
    var lignes = Array.prototype.slice.call(liste.querySelectorAll("[data-famille]"));
    var boutons = Array.prototype.slice.call(zone.querySelectorAll("button[data-famille]"));
    var theme = zone.querySelector("select");
    var recherche = zone.querySelector("input[type=search]");
    var compte = zone.querySelector(".filtres-compte");
    var vide = document.querySelector(".vide");
    var plat = function (s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); };
    var textes = recherche ? lignes.map(function (l) { return plat(l.textContent); }) : [];

    function appliquer() {
      var choisis = boutons.filter(function (b) { return b.getAttribute("aria-pressed") === "true"; })
        .map(function (b) { return b.dataset.famille; });
      var mot = recherche ? plat(recherche.value.trim()) : "";
      var visibles = 0;
      lignes.forEach(function (l, i) {
        var ok = (!choisis.length || choisis.indexOf(l.dataset.famille) >= 0)
          && (!theme || !theme.value || l.dataset.theme === theme.value)
          && (!mot || textes[i].indexOf(mot) >= 0);
        l.hidden = !ok;
        if (ok) visibles++;
      });
      if (compte) compte.textContent = visibles === lignes.length ? "" : visibles + " sur " + lignes.length;
      if (vide) vide.hidden = visibles > 0;
    }

    boutons.forEach(function (b) {
      b.addEventListener("click", function () {
        b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
        appliquer();
      });
    });
    if (theme) theme.addEventListener("change", appliquer);
    if (recherche) recherche.addEventListener("input", appliquer);
    zone.reinitialiser = function () {
      boutons.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
      appliquer();
    };
  });

  // « Tout ouvrir » / « Tout fermer ».
  document.querySelectorAll("button[data-tout]").forEach(function (bouton) {
    bouton.addEventListener("click", function () {
      var ouvrir = bouton.textContent.indexOf("ouvrir") >= 0;
      document.querySelectorAll(bouton.dataset.tout + " > details:not([hidden])").forEach(function (d) {
        d.open = ouvrir;
      });
      bouton.textContent = ouvrir ? "Tout fermer" : "Tout ouvrir";
    });
  });

  // Une adresse qui se termine par #DETTE-01 ouvre cette affirmation (même si un filtre la cachait).
  function ouvrirAncre() {
    var id = decodeURIComponent(location.hash.slice(1));
    var cible = id && document.getElementById(id);
    if (!cible || cible.tagName !== "DETAILS") return;
    if (cible.hidden) {
      var zone = document.querySelector("[data-filtres]");
      if (zone && zone.reinitialiser) zone.reinitialiser();
    }
    cible.open = true;
    cible.scrollIntoView({ block: "start", behavior: "instant" });
  }
  window.addEventListener("hashchange", ouvrirAncre);
  ouvrirAncre();
})();
