"""Mélenchon, thème 6 — Économie, travail et entreprises : calculs à partir de brut/.

python -m verification melenchon calculer 6   → calculs/resultats.csv
"""
import json
import re

import pandas as pd

from verification.commun import lecture as L
from verification.commun.calculs import Calculs, texte_de

REPSS = "securite_sociale/REPSS_ATMP_2026.pdf"
IFR = "ifr/robot_density_2025.html"
LUS = {
    "at_mortels_2024": (REPSS, "En 2024, on dénombre 764 accidents du travail mortels", 764),
    "trajet_mortels_2024": (REPSS, "et 316 accidents de trajet mortels", 316),
    "mp_mortelles_2024": (REPSS, "215 MP mortelles sont enregistrés en 2024", 215),
    "malaises": (REPSS, "plus de la moitié de ces décès sont la conséquence de malaises", 0),
    "declaration_heterogene": (REPSS, "des niveaux de déclaration très hétérogènes selon les pays européens", 0),
    "allemagne_robots": (IFR, "Germany ranks third, with 449 units per 10,000 employees", 449),
    "ue_robots": (IFR, "The European Union (EU-27) has a robot density of 231 units", 231),
}
C = Calculs(__file__, LUS)
B = C.brut
EU27 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
        "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}
NOMS = {"FR": "France", "ES": "Espagne", "PT": "Portugal", "DE": "Allemagne", "NL": "Pays-Bas", "BE": "Belgique"}


def main():
    C.verifier()

    # ECO-01 et ECO-12 : salaires minimums
    w = L.eurostat(B / "eurostat/earn_mw_cur_6pays.json").pivot_table(index="time", columns="geo", values="valeur")
    annonce = {"FR": "27 %", "ES": "86,5 %", "PT": "73 %", "DE": "62 %", "NL": "52 %", "BE": "45 %"}
    for g in ["FR", "ES", "PT", "DE", "NL", "BE"]:
        h = (w.loc["2026-S1", g] / w.loc["2016-S1", g] - 1) * 100
        C.res("ECO-01", NOMS[g], "Hausse du salaire minimum mensuel brut, 1er semestre 2016 → 1er semestre 2026", h, "%",
              "2016-2026", "EUROSTAT-SMIC-PAYS", "M1", annonce[g],
              f"{w.loc['2016-S1', g]:.0f} € → {w.loc['2026-S1', g]:.0f} € par mois (Eurostat, sur 12 mois)", 1)
    h15 = (w.loc["2025-S2", "FR"] / w.loc["2015-S2", "FR"] - 1) * 100
    C.res("ECO-01", "France, autre période", "Hausse du SMIC brut, 2e semestre 2015 → 2e semestre 2025", h15, "%",
          "2015-2025", "EUROSTAT-SMIC-PAYS", "M1", "27 %", "", 1)

    # ECO-02 : croissance
    g = L.eurostat(B / "eurostat/croissance_pib_pays.json")
    g = g[g.geo.isin(EU27)]
    for an in ("2024", "2025"):
        x = g[g.time == an].sort_values("valeur", ascending=False).reset_index(drop=True)
        es = x[x.geo == "ES"].iloc[0]
        rang = int(x.index[x.geo == "ES"][0]) + 1
        tete = ", ".join(f"{r.geo} {r.valeur:.1f}" for r in x.head(5).itertuples())
        C.res("ECO-02", f"Espagne, {an}", "Croissance du PIB en volume", es.valeur, "%", an, "EUROSTAT-CROISSANCE", "M2",
              "3,8 %, « le plus fort taux de croissance de toute l'Europe »",
              f"rang {rang} sur {len(x)} pays de l'UE ; en tête : {tete}", 1)

    # ECO-03 : chômeurs par emploi vacant
    v = L.eurostat(B / "eurostat/jvs_q_nace2_fr.json")
    v = v[v.indic_em == "JOBVAC"].pivot_table(index="time", columns="sizeclas", values="valeur")
    u = L.eurostat(B / "eurostat/une_rt_q_fr.json").set_index("time").valeur * 1000
    t = sorted(set(v.index) & set(u.index))[-4:]  # quatre derniers trimestres communs
    vac_tot, vac_10, chom = v.loc[t, "TOTAL"].mean(), v.loc[t, "GE10"].mean(), u.loc[t].mean()
    C.res("ECO-03", f"{t[0]} → {t[-1]}, toutes entreprises", "Chômeurs (BIT) par emploi vacant", chom / vac_tot,
          "chômeurs", t[-1][:4], "EUROSTAT-CHOMEURS; EUROSTAT-EMPLOIS-VACANTS", "M3", "17 chômeurs pour 1 offre",
          f"moyenne de quatre trimestres : {chom:.0f} chômeurs, {vac_tot:.0f} emplois vacants", 1)
    C.res("ECO-03", f"{t[0]} → {t[-1]}, entreprises de 10 salariés ou plus", "Chômeurs (BIT) par emploi vacant",
          chom / vac_10, "chômeurs", t[-1][:4], "EUROSTAT-CHOMEURS; EUROSTAT-EMPLOIS-VACANTS", "M3",
          "17 chômeurs pour 1 offre", f"{vac_10:.0f} emplois vacants dans les entreprises de 10 salariés ou plus", 1)
    C.res("ECO-03", "chômeurs nécessaires", "Chômeurs qu'il faudrait pour 17 par emploi vacant (toutes entreprises)",
          17 * vac_tot / 1e6, "millions", t[-1][:4], "EUROSTAT-EMPLOIS-VACANTS", "M3", "17 chômeurs pour 1 offre",
          f"contre {chom / 1e6:.2f} millions de chômeurs au sens du BIT", 1)

    # ECO-04 : embauches en contrats courts
    d = pd.read_csv(B / "urssaf/dpae_france_na38_2019_2026.csv", sep=";", encoding="utf-8-sig")
    p = d.pivot_table(index="annee", columns="nature_de_contrat", values="dpae_brut", aggfunc="sum")
    for an in (2019, 2024, 2025):
        tot = p.loc[an].sum()
        cdd = p.loc[an, "CDD de moins d'un mois"] + p.loc[an, "CDD de plus d'un mois"]
        C.res("ECO-04", f"{an}, tous CDD", "Part des CDD dans les déclarations d'embauche (hors intérim)", cdd / tot * 100,
              "%", str(an), "URSSAF-DPAE", "M4", "87 %", f"{tot / 1e6:.1f} millions de déclarations", 1)
        C.res("ECO-04", f"{an}, CDD de moins d'un mois", "Part des CDD de moins d'un mois dans les déclarations "
              "d'embauche", p.loc[an, "CDD de moins d'un mois"] / tot * 100, "%", str(an), "URSSAF-DPAE", "M4", "87 %",
              "", 1)

    # ECO-05 : production industrielle
    ip = L.eurostat(B / "eurostat/sts_inpr_a_fr.json").pivot_table(index="time", columns="nace_r2", values="valeur")
    for n, nom in (("B-D", "Industrie (hors construction)"), ("C", "Industrie manufacturière")):
        C.res("ECO-05", nom, "Production industrielle 2025 par rapport à 2019", (ip.loc["2025", n] / ip.loc["2019", n] - 1)
              * 100, "%", "2025", "EUROSTAT-PROD-INDUS", "M5", "pas retrouvé son niveau d'avant Covid-19",
              f"indice 2021 = 100 : {ip.loc['2019', n]} en 2019, {ip.loc['2025', n]} en 2025", 1)

    # ECO-06 : Doing Business
    j = json.loads((B / "banque_mondiale/doing_business_rang_2019.json").read_text(encoding="utf-8"))[1]
    rangs = {r["countryiso3code"]: r["value"] for r in j if r["value"] is not None}
    fr, n = rangs["FRA"], max(rangs.values())
    C.res("ECO-06", "Doing Business 2020 (données 2019)", "Rang de la France", fr, "rang", "2019",
          "BM-DOING-BUSINESS-2019", "M6", "dans les 15 % de pays", f"sur {n} économies classées", 0)
    C.res("ECO-06", "Doing Business 2020 (données 2019)", "Part des pays classés devant ou au même rang", fr / n * 100,
          "%", "2019", "BM-DOING-BUSINESS-2019", "M6", "15 %", "classement arrêté en 2021", 1)

    # ECO-07 : morts au travail en Europe
    a = L.eurostat(B / "eurostat/hsw_n2_02.json")
    a = a[a.geo.isin(EU27)]
    for an in sorted(a.time.unique())[-2:]:
        for unite, grandeur, u_ in (("NR", "Accidents du travail mortels", "décès"),
                                    ("RT_INC", "Taux d'accidents mortels pour 100 000 travailleurs", "pour 100 000")):
            x = a[(a.time == an) & (a.unit == unite)].sort_values("valeur", ascending=False).reset_index(drop=True)
            if x.empty or "FR" not in set(x.geo):
                continue
            rang = int(x.index[x.geo == "FR"][0]) + 1
            suivant = x[x.geo != "FR"].iloc[0]
            C.res("ECO-07", f"France, {an}", grandeur, x[x.geo == "FR"].valeur.iloc[0], u_, an, "EUROSTAT-AT-MORTELS",
                  "M7", "« pays record d'Europe des morts au travail »",
                  f"rang {rang} sur {len(x)} pays de l'UE ; premier autre pays : {suivant.geo} ({suivant.valeur})",
                  2 if unite == "RT_INC" else 0)

    # ECO-08 : 1 000 décès par an
    tot = C.v("at_mortels_2024") + C.v("trajet_mortels_2024") + C.v("mp_mortelles_2024")
    C.res("ECO-08", "2024, accidents du travail seuls", "Décès reconnus après un accident du travail",
          C.v("at_mortels_2024"), "décès", "2024", "REPSS-ATMP-2026", "M8", "1 000 décès par an",
          "plus de la moitié sont des malaises", 0)
    C.res("ECO-08", "2024, accidents du travail et maladies professionnelles",
          "Décès reconnus (accidents du travail + maladies professionnelles)",
          C.v("at_mortels_2024") + C.v("mp_mortelles_2024"), "décès", "2024", "REPSS-ATMP-2026", "M8",
          "1 000 décès par an", "", 0)
    C.res("ECO-08", "2024, avec les accidents de trajet", "Décès reconnus, tous risques professionnels", tot, "décès",
          "2024", "REPSS-ATMP-2026", "M8", "1 000 décès par an", "accidents de trajet : 316", 0)

    # ECO-09 : prix de l'alimentation
    i = L.eurostat(B / "eurostat/prc_hicp_minr_fr.json").pivot_table(index="time", columns="coicop18", values="valeur")
    fin = "2026-08"  # dernier mois connu le jour du discours (12 septembre 2026)
    for debut in ("2017-05", "2021-01", "2022-01"):
        C.res("ECO-09", f"{debut} → {fin}", "Hausse des prix de l'alimentation (IPCH, produits alimentaires et boissons "
              "non alcoolisées)", (i.loc[fin, "CP011"] / i.loc[debut, "CP011"] - 1) * 100, "%", "2026",
              "EUROSTAT-IPCH", "M9", "plus de 30 %",
              f"ensemble des prix sur la même période : {(i.loc[fin, 'TOTAL'] / i.loc[debut, 'TOTAL'] - 1) * 100:.1f} %",
              1)
    C.res("ECO-09", "sur un an, août 2026", "Hausse de l'ensemble des prix sur un an",
          (i.loc[fin, "TOTAL"] / i.loc["2025-08", "TOTAL"] - 1) * 100, "%", "2026", "EUROSTAT-IPCH", "M9", "« 3 % »",
          "", 1)

    # ECO-10 : consommation et salaires dans le PIB
    c = L.eurostat(B / "eurostat/nama_10_gdp_conso_fr.json").pivot_table(index="time", columns="na_item", values="valeur")
    for item, nom in (("P31_S14", "Consommation des ménages"), ("P31_S14_S15", "Consommation des ménages et des "
                                                                             "institutions sans but lucratif"),
                      ("D1", "Rémunération des salariés")):
        C.res("ECO-10", "2025", f"{nom}, en % du PIB", c.loc["2025", item] / c.loc["2025", "B1GQ"] * 100, "% du PIB",
              "2025", "EUROSTAT-PIB-EMPLOIS", "M10", "55 % du PIB", "", 1)

    # ECO-11 : robots
    C.res("ECO-11", "Allemagne, 2024", "Robots industriels pour 10 000 salariés de l'industrie manufacturière",
          C.v("allemagne_robots"), "robots", "2024", "IFR-DENSITE-2025", "M11", "400 robots pour 10 000 salariés",
          f"moyenne de l'UE : {C.v('ue_robots'):.0f}", 0)

    # ECO-12 : SMIC à 1 700 € net
    brut = w.loc["2026-S1", "FR"]
    net = brut * 0.7905
    C.res("ECO-12", "2026", "SMIC mensuel net (estimation : brut Eurostat moins 20,95 % de cotisations salariales)", net,
          "€", "2026", "EUROSTAT-SMIC-PAYS", "M12", "1 700 € net",
          f"ESTIMATION, non fiable à 100 % : SMIC brut {brut:.0f} € ; 1 700 € net = hausse d'environ "
          f"{(1700 / net - 1) * 100:.0f} %", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
