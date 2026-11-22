// Date de mise à jour des données et version du modèle (synthèse « meta »), en haut et en bas de chaque page.
import { dateLongue } from "./commun.js";

/** « 2026-11-11 22:17:27 » → « 11 novembre 2026 à 22 h 17 ». */
function dateHeure(s) {
  if (!s) return "";
  const heure = s.length >= 16 ? ` à ${Number(s.slice(11, 13))} h ${s.slice(14, 16)}` : "";
  return `${dateLongue(s)}${heure}`;
}

export function remplirPied(meta) {
  if (!meta) return;
  const m = meta.modele || {};
  const collecte = meta.derniere_collecte || meta.mis_a_jour;
  const haut = document.getElementById("maj-haut");
  if (haut) {
    // Une seule phrase en texte simple : deux pastilles côte à côte se lisaient comme un choix entre deux versions.
    const version = (m.version || "").replace(/^v/, "");
    haut.textContent = `Mis à jour le ${dateHeure(collecte)}${version ? ` · notes calculées par la version ${version} du modèle` : ""}`;
    haut.hidden = false;
  }
  const bas = document.getElementById("maj");
  if (bas) bas.textContent = `Données du ${dateLongue(collecte)} · modèle ${m.version || ""}`;
}
