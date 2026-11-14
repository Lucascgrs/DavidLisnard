"""Thème 2 — Sécurité, justice et narcotrafic : calculs à partir de brut/.

python -m verification calculer 2   → calculs/resultats.csv et calculs/graphiques/
Les chiffres lus dans des PDF sont dans LUS_DANS_LES_PDF (phrase exacte vérifiée dans le PDF avant tout calcul).
"""
import csv
import json
import re
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
BRUT = ICI.parent / "brut"
SORTIE, GRAPH = ICI / "resultats.csv", ICI / "graphiques"

LUS_DANS_LES_PDF = {
    "places_manquantes_oct2025": ("senat/a25-145-6_synthese_penitentiaire.pdf", "s’établit à 22 361", 22361),
    "detenus_oct2025": ("senat/a25-145-6_synthese_penitentiaire.pdf", "le nombre de détenus s’élevait à 84 862", 84862),
    "densite_oct2025": ("senat/a25-145-6_synthese_penitentiaire.pdf", "la densité carcérale globale s’établit à 135,8 %", 135.8),
    "cout_journee_2024": ("senat/a25-145-6_synthese_penitentiaire.pdf", "évalué à 128 euros", 128),
    "cout_plan15000": ("senat/r23-037_synthese_plan15000.pdf", "porte cette estimation à 5,55 milliards d’euros", 5.55),
    "places_brutes_livrees_oct2025": ("senat/a25-145-6_synthese_penitentiaire.pdf", "comportant 7 504 places brutes", 7504),
    "space_mediane_2024": ("conseil_europe/SPACE_I_2024.pdf", "Prison population rate per 100,000 habitants (51 PA) 104.8", 104.8),
    "space_france_2024": ("conseil_europe/SPACE_I_2024.pdf", "France 68 401 997 76 275 111.5", 111.5),
    "space_allemagne_2024": ("conseil_europe/SPACE_I_2024.pdf", "Germany 83 445 000 59 413 71.2", 71.2),
    "exec_immediate_2025": ("justice/RSJ2026_12_1.pdf", "En 2025, 58 % des peines d’emprisonnement ferme", 58),
    "exec_5ans_2025": ("justice/RSJ2026_12_1.pdf", "le taux de mise à exécution à cinq ans est stable, à 90 %", 90),
    "exec_1an_2024": ("justice/RSJ2025_chapitre12.pdf", "57 % au moment du jugement et de 79 % à un an", 79),
    "exec_immediate_2024": ("justice/RSJ2025_chapitre12.pdf", "57 % au moment du jugement", 57),
    "igj_courtes_peines_amenagees_2019": ("justice/IGJ_execution_peines_2022.pdf", "40 % environ des « courtes peines » sont aménagées", 40),
    "igj_exec_immediate_2021": ("justice/IGJ_execution_peines_2022.pdf", "jusque 45 % en 2021", 45),
    "cepej_juges_france_2024": ("conseil_europe/CEPEJ_fiche_France_2024.pdf", "Professional judges 11,6 23,4", 11.6),
    "cepej_juges_mediane_ue_2024": ("conseil_europe/CEPEJ_fiche_France_2024.pdf", "Professional judges 11,6 23,4", 23.4),
    "cepej_procureurs_france_2024": ("conseil_europe/CEPEJ_fiche_France_2024.pdf", "Prosecutors 3,2 11,4", 3.2),
    "cepej_procureurs_mediane_2024": ("conseil_europe/CEPEJ_fiche_France_2024.pdf", "Prosecutors 3,2 11,4", 11.4),
    "narco_ca_minimum": ("senat/r23-588-1_synthese_narcotrafic.pdf", "3,5 milliards d’euros, en fourchette basse", 3.5),
}


def verifier_pdf():
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    cache, manquants = {}, []
    for cle, (f, extrait, _) in LUS_DANS_LES_PDF.items():
        if f not in cache:
            cache[f] = re.sub(r"\s+", "", " ".join((p.extract_text() or "") for p in PdfReader(BRUT / f).pages))
        if re.sub(r"\s+", "", extrait) not in cache[f]:
            manquants.append(f"{cle} ({f} : « {extrait} »)")
    if manquants:
        raise SystemExit("Introuvables dans les PDF :\n  " + "\n  ".join(manquants))


V = lambda k: LUS_DANS_LES_PDF[k][2]
R: list[dict] = []


def res(aff, variante, grandeur, valeur, unite, annee, sources, section, lisnard="", note=""):
    R.append({"affirmation": aff, "variante": variante, "grandeur": grandeur, "valeur": round(float(valeur), 2),
              "unite": unite, "annee": annee, "chiffre_lisnard": lisnard, "sources": sources, "methode": section,
              "note": note})


def delinquance():
    d = pd.read_csv(BRUT / "ssmsi/delinquance_departementale_2016_2025.csv", sep=";")
    n = d.groupby(["indicateur", "annee"]).nombre.sum().unstack()
    n.loc["Violences physiques (total)"] = n.loc["Violences physiques intrafamiliales"] + n.loc["Violences physiques hors cadre familial"]
    evol = lambda ind, a, b: (n.loc[ind, b] / n.loc[ind, a] - 1) * 100
    src = "SSMSI-DELINQUANCE-DEP"
    for ind, lis in [("Violences physiques (total)", "+51 % (2017-2022) ; +63 % en 6 ans"), ("Homicides", "+15 % (2017-2022)"),
                     ("Violences physiques hors cadre familial", ""), ("Violences physiques intrafamiliales", "")]:
        res("SECU-01", f"{ind}, 2017 → 2022", "Hausse des faits enregistrés", evol(ind, 2017, 2022), "%", "2022", src, "M1", lis,
            f"{n.loc[ind, 2017]:.0f} → {n.loc[ind, 2022]:.0f}")
    for ind, lis in [("Violences physiques (total)", "+51 % (programme)"), ("Homicides", "+16 % (programme)"),
                     ("Tentatives d'homicide", "+90 % (programme)"), ("Violences physiques hors cadre familial", "")]:
        res("SECU-01", f"{ind}, 2017 → 2025", "Hausse des faits enregistrés", evol(ind, 2017, 2025), "%", "2025", src, "M1", lis,
            f"{n.loc[ind, 2017]:.0f} → {n.loc[ind, 2025]:.0f}")
    for ind, lis in [("Violences physiques (total)", "+50 % en dix ans"), ("Homicides", "+43 % en dix ans")]:
        res("SECU-01", f"{ind}, 2016 → 2025 (dix ans)", "Hausse des faits enregistrés", evol(ind, 2016, 2025), "%", "2025", src,
            "M1", lis, f"{n.loc[ind, 2016]:.0f} → {n.loc[ind, 2025]:.0f}")
    res("SECU-01", "Homicides, 2017 → 2021", "Hausse des faits enregistrés (déclaration de juillet 2022)", evol("Homicides", 2017, 2021),
        "%", "2021", src, "M1", "+12 % (07/2022)", f"{n.loc['Homicides', 2017]:.0f} → {n.loc['Homicides', 2021]:.0f}")
    vi = n.loc["Violences physiques intrafamiliales"]
    part = (vi[2025] - vi[2017]) / (n.loc["Violences physiques (total)", 2025] - n.loc["Violences physiques (total)", 2017]) * 100
    res("SECU-01", "2017 → 2025", "Part de la hausse des violences physiques due aux violences intrafamiliales", part, "%", "2025",
        src, "M1", "", "hausse en grande partie liée au meilleur signalement des violences conjugales (selon le SSMSI)")
    return n


def prisons():
    for f, src, date in [("dap/statistique_etablissements_01092026.xlsx", "DAP-DETENUS-2026-09", "2026-09"),
                         ("dap/statistique_etablissements_01092025.xlsx", "DAP-DETENUS-2025-09", "2025-09")]:
        t = pd.read_excel(BRUT / f, sheet_name="Tab6", header=None)
        ligne = t[t[0].astype(str).str.contains("Total France")].iloc[0]
        places, detenus = float(ligne[2]), float(ligne[3])
        res("SECU-02", f"France entière, {date}", "Détenus en surnombre (détenus − places opérationnelles)", detenus - places,
            "détenus", date, src, "M2", "20 000 places manquantes ; 30 000 (2025-2026)",
            f"{detenus:.0f} détenus pour {places:.0f} places ; densité {detenus / places * 100:.1f} %")
    res("SECU-02", "Sénat, octobre 2025", "Places manquantes pour ramener la densité à 100 % dans chaque établissement",
        V("places_manquantes_oct2025"), "places", "2025-10", "SENAT-PENITENTIAIRE-PLF2026", "M2", "20 000 / 30 000",
        "compte établissement par établissement : un établissement en sous-occupation ne compense pas une maison d'arrêt saturée")
    res("SECU-02", "Europe (51 administrations), 31/01/2024", "Taux de détention, France, pour 100 000 habitants",
        V("space_france_2024"), "détenus pour 100 000 hab.", "2024", "COE-SPACE-I-2024", "M2", "« sous-taux d'incarcération »",
        f"médiane européenne {V('space_mediane_2024')} ; Allemagne {V('space_allemagne_2024')}")


def peines():
    res("SECU-03", "peines devenues exécutoires, 2024", "Peines d'emprisonnement ferme non exécutées un an après",
        100 - V("exec_1an_2024"), "%", "2024", "RSJ-2025-EXECUTION", "M3", "40 % au bout de six mois")
    res("SECU-03", "2025", "Peines non mises à exécution immédiatement (au jugement)", 100 - V("exec_immediate_2025"), "%", "2025",
        "RSJ-2026-EXECUTION", "M3", "40 % au bout de six mois")
    res("SECU-03", "peines exécutoires en 2020, à cinq ans", "Peines jamais mises à exécution cinq ans après", 100 - V("exec_5ans_2025"),
        "%", "2025", "RSJ-2026-EXECUTION", "M3", "« une condamnation sur deux n'est pas appliquée »")
    res("SECU-03", "IGJ, 2021", "Taux d'exécution immédiate (rapport IGJ de mars 2022)", V("igj_exec_immediate_2021"), "%", "2021",
        "IGJ-EXECUTION-PEINES-2022", "M3", "45 % non exécutées à six mois (2021)", "il était d'environ 30 % de 2017 à 2019")


def justice_europe():
    res("SECU-04", "UE à 27, 2024", "Juges professionnels pour 100 000 habitants (France)", V("cepej_juges_france_2024"),
        "pour 100 000 hab.", "2024", "CEPEJ-FRANCE-2024", "M4", "10,9 ; médiane 17,7", f"médiane UE {V('cepej_juges_mediane_ue_2024')}")
    res("SECU-04", "UE à 27, 2024", "Procureurs pour 100 000 habitants (France)", V("cepej_procureurs_france_2024"),
        "pour 100 000 hab.", "2024", "CEPEJ-FRANCE-2024", "M4", "", f"médiane UE {V('cepej_procureurs_mediane_2024')}")


def polices_municipales():
    communes = pd.DataFrame(json.loads((BRUT / "geo/communes.json").read_text(encoding="utf-8")))
    nb_communes = len(communes)
    d24 = pd.read_excel(BRUT / "interieur/effectifs_police_municipale_2024.ods", sheet_name="Communes", header=None, engine="odf")
    tot = d24[d24[0].astype(str).str.contains("TOTAL NATIONAL")].iloc[0]
    services, agents24 = float(tot[3]), float(tot[6])
    lignes = d24.iloc[8:]
    lignes = lignes[pd.to_numeric(lignes[6], errors="coerce").fillna(0) > 0]
    lignes = lignes[~lignes[0].astype(str).str.contains("TOTAL")]
    avec_agent = len(lignes)
    res("SECU-05", "2024", "Communes ou intercommunalités ayant un service de police municipale / nombre de communes",
        services / nb_communes * 100, "%", "2024", "PM-EFFECTIFS-2024 ; GEO-COMMUNES", "M5", "12 % ; 10 % ; 20 % ; 14 %",
        f"{services:.0f} services sur {nb_communes} communes ; borne haute (un service intercommunal couvre plusieurs communes)")
    res("SECU-05", "2024", "Lignes avec au moins un policier municipal / nombre de communes", avec_agent / nb_communes * 100, "%",
        "2024", "PM-EFFECTIFS-2024 ; GEO-COMMUNES", "M5", "12 %", f"{avec_agent} lignes")
    d14 = pd.read_excel(BRUT / "interieur/effectifs_police_municipale_2014.xlsx", sheet_name="Cadre enquête communes 2014", header=None)
    agents14 = float(d14[d14[0].astype(str).str.strip().str.lower() == "totaux"].iloc[0][2])  # ligne « totaux » du fichier
    res("SECU-05", "2014 → 2024", "Hausse des effectifs de policiers municipaux", (agents24 / agents14 - 1) * 100, "%", "2024",
        "PM-EFFECTIFS-2014 ; PM-EFFECTIFS-2024", "M5", "+35 % / +36 % en dix ans", f"{agents14:.0f} → {agents24:.0f} agents")


def narcotrafic():
    res("SECU-06", "Sénat 2024 (ministre de l'Économie)", "Chiffre d'affaires annuel du narcotrafic, fourchette basse",
        V("narco_ca_minimum"), "Md€", "2024", "SENAT-NARCOTRAFIC-2024", "M6", "3 à 6 Md€ (2024) ; 8 Md€ (2026)")


def mesures():
    cout_place = V("cout_plan15000") * 1e9 / 15000
    res("SECU-07", "plan 15 000 (Sénat, juin 2023)", "Coût d'investissement moyen par place", cout_place / 1e3, "k€ par place", "2023",
        "SENAT-PLAN15000-2023", "M7", "", "ESTIMATION, non fiable à 100 % : coût moyen d'un plan en cours, hors inflation après 2023")
    res("SECU-07", "20 000 places", "Coût d'investissement estimé", 20000 * cout_place / 1e9, "Md€", "2023",
        "SENAT-PLAN15000-2023", "M7", "", "ESTIMATION, non fiable à 100 % : 20 000 × coût moyen du plan 15 000")
    res("SECU-07", "20 000 places occupées", "Coût de fonctionnement annuel estimé", 20000 * V("cout_journee_2024") * 365 / 1e9,
        "Md€ par an", "2024", "SENAT-PENITENTIAIRE-PLF2026", "M7", "",
        "ESTIMATION, non fiable à 100 % : coût moyen d'une journée de détention (128 €) × 365 × 20 000")
    res("SECU-07", "plan 15 000, octobre 2025", "Places brutes livrées depuis 2018", V("places_brutes_livrees_oct2025"), "places",
        "2025", "SENAT-PENITENTIAIRE-PLF2026", "M7", "« elles ne sont toujours pas faites »")


def graphique(n):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAPH.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#b9b8b3", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.labelcolor": "#52514e"})
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
    for ind, nom, coul, dy in [("Violences physiques intrafamiliales", "Violences intrafamiliales", "#eb6834", 0),
                               ("Violences physiques hors cadre familial", "Violences hors cadre familial", "#2a78d6", 0),
                               ("Homicides", "Homicides", "#1baf7a", 0)]:
        s = n.loc[ind] / n.loc[ind, 2017] * 100
        ax.plot(s.index, s.values, color=coul, lw=2, label=nom)
        ax.annotate(f"{nom} {s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(6, dy), textcoords="offset points", va="center",
                    fontsize=9, color="#0b0b0b")
    ax.axhline(100, color="#b9b8b3", lw=0.8)
    ax.set_xlim(2016, 2029)
    ax.set_ylabel("Indice, base 100 en 2017")
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_title("La hausse des violences vient surtout des violences intrafamiliales", loc="left", fontsize=12, color="#0b0b0b")
    fig.text(0.01, 0.01, "Faits enregistrés par la police et la gendarmerie. Source : SSMSI, base départementale (juillet 2026)",
             fontsize=8, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(GRAPH / "violences_2016_2025.png")
    plt.close(fig)


def main():
    verifier_pdf()
    n = delinquance()
    prisons()
    peines()
    justice_europe()
    polices_municipales()
    narcotrafic()
    mesures()
    graphique(n)
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    print(f"{len(R)} résultats → calculs/resultats.csv")


if __name__ == "__main__":
    main()
