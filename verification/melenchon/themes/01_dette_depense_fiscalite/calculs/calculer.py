"""Mélenchon, thème 1 — Dette, dépense publique et fiscalité : calculs à partir de brut/.

python -m verification melenchon calculer 1   → calculs/resultats.csv
"""
from verification.commun import lecture as L
from verification.commun.calculs import Calculs

HCSP = "hcsp/HCSP-2025-NA157-aides-entreprises.pdf"
LUS = {
    "aides_211": (HCSP, "La première, à 211 milliards d’euros, retient comme périmètre", 211),
    "aides_108": (HCSP, "La seconde estimation, à 108 milliards, est plus restreinte", 108),
    "auteurs": (HCSP, "par Olivier Rietmann et Fabien Gay, rapport n° 808", 0),
    "is_25": ("droit/service_public_IS.html", "est imposée au taux normal de 25 %", 25),
    "contrib_41": ("droit/bofip_contribution_exceptionnelle.html", "41,2", 41.2),
    "bareme_45": ("droit/service_public_bareme_ir.html", "Plus de 181 917 € 45 %", 45),
}
C = Calculs(__file__, LUS)
B = C.brut
UE27 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
        "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}


def main():
    C.verifier()
    # DETTE-01 : aides aux entreprises
    C.res("DETTE-01", "estimation large, 2023", "Aides publiques aux entreprises (commission d'enquête du Sénat)",
          C.v("aides_211"), "Md€", "2023", "HCSP-AIDES-2025", "M1", "210 milliards",
          "comprend 41 Md€ d'interventions financières de Bpifrance (prêts, garanties) et 75 Md€ d'allégements de "
          "cotisations", 0)
    C.res("DETTE-01", "estimation restreinte, 2023", "Aides publiques aux entreprises (commission d'enquête du Sénat)",
          C.v("aides_108"), "Md€", "2023", "HCSP-AIDES-2025", "M1", "120 milliards",
          "sans Bpifrance et sans 62 Md€ de dépenses fiscales déclassées ou liées à la TVA", 0)

    # DETTE-02 : déficit de l'État
    d = L.eurostat(B / "eurostat/gov_10a_main_b9_fr.json").pivot_table(index="time", columns=["sector", "unit"],
                                                                        values="valeur")
    for an in ("2024", "2025"):
        for s, nom in (("S1311", "État"), ("S13", "Ensemble des administrations publiques")):
            C.res("DETTE-02", f"{nom}, {an}", "Déficit public (comptabilité nationale)", -d.loc[an, (s, "MIO_EUR")] / 1e3,
                  "Md€", an, "EUROSTAT-DEFICITS", "M2", "150 milliards",
                  f"{-d.loc[an, (s, 'PC_GDP')]:.1f} % du PIB", 1)

    # DETTE-03 : patrimoine public
    nf = L.eurostat(B / "eurostat/nama_10_nfa_bs_apu_fr.json").pivot_table(index="time", columns=["sector", "asset10"],
                                                                            values="valeur")
    fi = L.eurostat(B / "eurostat/nasa_10_f_bs_apu_fr.json").pivot_table(index="time", columns=["sector", "finpos"],
                                                                          values="valeur")
    pop = L.eurostat(B / "eurostat/demo_gind_fr.json").set_index("time").valeur
    an = "2025"
    p = pop.get("2026", pop.iloc[-1])
    for s, nom in (("S13", "Ensemble des administrations publiques"), ("S1311", "État")):
        if (s, "N1N") not in nf.columns or (s, "ASS") not in fi.columns:
            print(f"   (pas de bilan complet pour {nom})")
            continue
        actifs = nf.loc[an, (s, "N1N")] + nf.loc[an, (s, "N2N")] + fi.loc[an, (s, "ASS")]
        passifs = fi.loc[an, (s, "LIAB")]
        net = actifs - passifs
        C.res("DETTE-03", f"{nom}, fin {an}", "Patrimoine net (actifs non financiers et financiers moins passifs)",
              net / 1e3, "Md€", an, "EUROSTAT-PATRIMOINE-NF; EUROSTAT-PATRIMOINE-FIN", "M3",
              "patrimoine supérieur à la dette", f"actifs {actifs / 1e3:.0f} Md€, passifs {passifs / 1e3:.0f} Md€", 0)
        C.res("DETTE-03", f"{nom}, fin {an}", "Patrimoine net par habitant", net * 1e6 / p, "€", an,
              "EUROSTAT-PATRIMOINE-NF; EUROSTAT-PATRIMOINE-FIN; EUROSTAT-POPULATION", "M3", "plus de 10 000 €",
              f"population {p / 1e6:.1f} millions", 0)

    # DETTE-04 : pays à plus de 100 % du PIB
    g = L.eurostat(B / "eurostat/gov_10dd_edpt1_pays.json")
    dette = g[(g.na_item == "GD") & g.geo.isin(UE27)]
    pib = L.eurostat(B / "eurostat/nama_10_gdp_pays_2025.json").set_index("geo").valeur
    plus100 = dette[(dette.time == "2025") & (dette.valeur > 100)].sort_values("valeur", ascending=False)
    liste = ", ".join(f"{r.geo} {r.valeur:.1f} %" for r in plus100.itertuples())
    C.res("DETTE-04", "2025", "Pays de l'UE dont la dette dépasse 100 % du PIB", len(plus100), "pays", "2025",
          "EUROSTAT-DETTE-PAYS", "M4", "5 pays", liste, 0)
    poids = pib[list(plus100.geo)].sum()
    for agg, nom in (("EU27_2020", "de l'UE"), ("EA20", "de la zone euro")):
        C.res("DETTE-04", "2025", f"Poids de ces pays dans le PIB {nom}", poids / pib[agg] * 100, "%", "2025",
              "EUROSTAT-DETTE-PAYS; EUROSTAT-PIB-PAYS-2025", "M4", "50 %", "", 1)

    # DETTE-05 : la Grèce
    gr = g[g.geo == "EL"].pivot_table(index="time", columns="na_item", values="valeur")
    for an in ("2008", "2009", "2010", "2025"):
        solde = gr.loc[an, "B9"]
        C.res("DETTE-05", f"Grèce, {an}", "Dette publique", gr.loc[an, "GD"], "% du PIB", an, "EUROSTAT-DETTE-PAYS",
              "M5", "« déficit égal à 110 % du PIB » ; « plus de 130 % » aujourd'hui",
              f"déficit : {-solde:.1f} % du PIB" if solde < 0 else f"excédent : {solde:.1f} % du PIB", 1)

    # DETTE-06 : impôt sur les sociétés
    C.res("DETTE-06", "2026", "Taux normal de l'impôt sur les sociétés", C.v("is_25"), "%", "2026",
          "SP-IMPOT-SOCIETES", "M6", "25 %", "taux réduit de 15 % jusqu'à 42 500 € de bénéfice pour les PME", 0)
    C.res("DETTE-06", "plus de 3 Md€ de chiffre d'affaires", "Contribution exceptionnelle (en % de l'impôt dû)",
          C.v("contrib_41"), "%", "2025", "BOFIP-CONTRIBUTION-EXCEPTIONNELLE", "M6", "25 %",
          f"taux facial d'environ {25 * (1 + C.v('contrib_41') / 100):.1f} % pour ces entreprises", 1)

    # DETTE-07 : barème de l'impôt sur le revenu
    C.res("DETTE-07", "revenus 2025", "Tranches du barème de l'impôt sur le revenu", 5, "tranches", "2026",
          "SP-BAREME-IR", "M7", "5 tranches aujourd'hui", "0 %, 11 %, 30 %, 41 %, 45 %", 0)
    C.ecrire()


if __name__ == "__main__":
    main()
