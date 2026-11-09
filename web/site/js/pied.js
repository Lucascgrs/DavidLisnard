// Pied de page : date des données et version du modèle (synthèse « meta »).
import { dateLongue } from "./commun.js";

export function remplirPied(meta) {
  const e = document.getElementById("maj");
  if (e && meta) e.textContent = `Données du ${dateLongue(meta.mis_a_jour)} · modèle ${meta.modele?.version || ""}`;
}
