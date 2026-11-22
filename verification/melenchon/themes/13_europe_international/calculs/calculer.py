"""Mélenchon, thème 13 — Europe et international : calculs à partir de brut/.

python -m verification melenchon calculer 13   → calculs/resultats.csv
"""
import json

from verification.commun import lecture as L
from verification.commun.calculs import Calculs

OTAN = "otan/def_exp_2025.pdf"
LUS = {
    "otan_2025_pib": (OTAN, "France 1.82 1.78 1.79 1.78 1.81 1.82 1.99 1.90 1.87 1.94 2.03 2.05", 2.05),
}
C = Calculs(__file__, LUS)
B = C.brut


def main():
    C.verifier()
    pib = L.eurostat(B / "eurostat/nama_10_gdp_pays_2025.json").set_index("geo").valeur
    for pays, nom, dit in (("FR", "France", "18 %"), ("EL", "Grèce", "2 %")):
        for agg, nom_agg in (("EU27_2020", "l'UE"), ("EA20", "la zone euro")):
            C.res("EUR-01", f"{nom}, 2025", f"Part dans le PIB de {nom_agg}", pib[pays] / pib[agg] * 100, "%", "2025",
                  "EUROSTAT-PIB-PAYS-2025", "M1", dit, "", 1)

    d = json.loads((B / "tresor_us/debt_to_penny_2026.json").read_text(encoding="utf-8"))["data"]
    dette = {r["record_date"]: float(r["tot_pub_debt_out_amt"]) for r in d}
    for jour in ("2026-09-16", "2026-10-10"):
        connu = max(k for k in dette if k <= jour)
        C.res("EUR-02", f"au {connu}", "Dette fédérale totale des États-Unis", dette[connu] / 1e12, "milliers de Md$",
              connu[:4], "TRESOR-US-DETTE", "M2", "40 000 milliards de dollars",
              "dernier jour publié avant la déclaration (dette fédérale, sans les États ni les collectivités)", 2)

    C.res("EUR-03", "France, estimation 2025", "Dépenses de défense (définition OTAN)", C.v("otan_2025_pib"), "% du PIB",
          "2025", "OTAN-DEPENSES-2025", "M3", "refuser les 5 %",
          f"ESTIMATION, non fiable à 100 % : passer à 5 % représenterait environ "
          f"{(5 - C.v('otan_2025_pib')) / 100 * pib['FR'] / 1e3:.0f} Md€ de plus par an au PIB de 2025", 2)
    C.ecrire()


if __name__ == "__main__":
    main()
