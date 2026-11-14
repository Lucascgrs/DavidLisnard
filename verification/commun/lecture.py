"""Lecture des formats bruts (JSON-stat Eurostat, CSV SDMX de l'OCDE, JSON du FMI et de DBnomics) en tableaux plats."""
import itertools
import json
from pathlib import Path

import pandas as pd


def eurostat(chemin: Path) -> pd.DataFrame:
    """JSON-stat 2.0 d'Eurostat → une ligne par observation, une colonne par dimension (codes) + `valeur`."""
    j = json.loads(Path(chemin).read_text(encoding="utf-8"))
    dims, tailles = j["id"], j["size"]
    codes = []
    for d in dims:
        index = j["dimension"][d]["category"]["index"]
        ordre = sorted(index, key=index.get) if isinstance(index, dict) else index
        codes.append(ordre)
    valeurs = j.get("value", {})
    lignes = []
    for pos, combo in enumerate(itertools.product(*codes)):
        v = valeurs.get(str(pos)) if isinstance(valeurs, dict) else valeurs[pos]
        if v is not None:
            lignes.append((*combo, v))
    df = pd.DataFrame(lignes, columns=[*dims, "valeur"])
    if "time" in df:
        df["time"] = df["time"].astype(str)
    return df


def ocde(chemin: Path) -> pd.DataFrame:
    """CSV SDMX de l'OCDE (codes, avec ou sans colonnes de libellés) → dimensions en codes + `time` + `valeur`."""
    df = pd.read_csv(chemin, low_memory=False)
    garder = [c for c in df.columns if c.isupper() and c not in {"STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION",
                                                                 "OBS_VALUE", "TIME_PERIOD", "DATAFLOW"}]
    out = df[garder].copy()
    out["time"] = df["TIME_PERIOD"].astype(str)
    out["valeur"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    return out


def fmi(chemin: Path) -> pd.DataFrame:
    """JSON du datamapper du FMI → colonnes pays, time, valeur."""
    j = json.loads(Path(chemin).read_text(encoding="utf-8"))
    return pd.DataFrame([(p, str(a), v) for pays in j["values"].values() if pays for p, ser in pays.items() if ser for a, v in ser.items()],
                        columns=["pays", "time", "valeur"])


def dbnomics(chemin: Path) -> pd.DataFrame:
    j = json.loads(Path(chemin).read_text(encoding="utf-8"))
    s = j["series"]["docs"][0]
    return pd.DataFrame({"time": s["period"], "valeur": s["value"]})
