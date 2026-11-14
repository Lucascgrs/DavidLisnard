"""Sonde injectée dans un entraînement déjà lancé (sys.remote_exec de Python 3.14), sans l'interrompre.

Elle démarre un fil d'exécution discret qui lit, sans rien modifier, les variables locales de
analyse.affinage.entrainer (lot en cours, sorties du réseau, perte, poids) et les écrit toutes les demi-secondes
dans un fichier JSON du dossier temporaire, que lit la fenêtre (python -m suivi).
Tout est protégé : une erreur de la sonde est écrite dans le fichier, jamais renvoyée à l'entraînement.
"""


def _demarrer():
    import json
    import math
    import os
    import sys
    import tempfile
    import threading
    import time
    import traceback

    VERSION = 2
    if getattr(sys, "_suivi_lisnard", None) == VERSION:  # déjà branchée : ne pas lancer deux fils
        return
    sys._suivi_lisnard = VERSION  # un fil d'une autre version s'arrête de lui-même (voir boucle)
    for t in threading.enumerate():  # fil de la première version, qui ne savait pas s'arrêter : le rendre muet
        if t.name == "suivi_lisnard":
            try:
                f = sys._current_frames().get(t.ident)
                while f is not None and f.f_code.co_name != "boucle":
                    f = f.f_back
                if f is not None and "ecrire" in f.f_code.co_freevars:
                    f.f_locals["ecrire"] = lambda *a: None
            except Exception:
                pass

    SORTIE = os.path.join(tempfile.gettempdir(), "lisnard_suivi.json")
    COUCHE_ZOOM, COTE_ZOOM = 11, 40  # carré de 40 × 40 poids de la dernière couche, affiché en direct
    SUFFIXES = ("attention.self.query.weight", "attention.self.value.weight", "attention.output.dense.weight")

    def cadre_entrainement():
        principal = threading.main_thread().ident
        f = sys._current_frames().get(principal)
        pile = []
        while f is not None:
            pile.append(f.f_code.co_name)
            code = f.f_code  # pas_total sert dans une lambda : variable de cellule, pas locale
            if code.co_name == "entrainer" and "pas_total" in code.co_varnames + code.co_cellvars:
                return f, pile
            f = f.f_back
        return None, pile

    def fichier_e5():
        try:
            from analyse import MODELE_LANGUE
            from huggingface_hub import try_to_load_from_cache
            p = try_to_load_from_cache(MODELE_LANGUE, "model.safetensors")
            return p if isinstance(p, str) else None
        except Exception:
            return None

    def boucle():
        import numpy as np
        import torch

        etat = {"pid": os.getpid(), "debut_sonde": time.time(), "pertes": [], "derive_temps": [],
                "lots": [], "erreur": None}
        dernier_pas, dernier_out, dernier_idx = None, None, None
        ref, ref_zoom, couches, t_poids = None, None, None, 0.0
        vu = False

        while getattr(sys, "_suivi_lisnard", None) == VERSION:
            try:
                f, pile = cadre_entrainement()
                if f is None:
                    etat["phase"] = ("modèle combiné" if "construire" in pile else
                                     "terminé" if vu else "en attente de l'affinage")
                    etat["maj"] = time.time()
                    ecrire(etat)
                    time.sleep(1.0)
                    continue
                vu = True
                loc = f.f_locals
                pas, pas_total = loc.get("pas"), loc.get("pas_total")
                ep, epoques = loc.get("ep"), loc.get("epoques")
                lignes, notes, cibles = loc.get("lignes"), loc.get("notes"), loc.get("cibles")
                etat.update(nom=loc.get("nom"), pas=pas, pas_total=pas_total,
                            epoque=None if ep is None else ep + 1, epoques=epoques,
                            t0=loc.get("t0"), n_app=len(loc.get("app", [])),
                            historique=loc.get("historique"),
                            phase="évaluation sur le jeu de réglage" if "predire_brut" in pile else "apprentissage")
                opt = loc.get("opt")
                if opt is not None:
                    etat["lr"] = float(opt.param_groups[0]["lr"])

                # Lot qui vient d'être lu : sorties du réseau (out) et commentaires (idx)
                idx, out = loc.get("idx"), loc.get("out")
                if idx is not None and idx is not dernier_idx and lignes is not None:
                    dernier_idx = idx
                    etat["lot_courant"] = {"pas": pas, "commentaires": [decrire(lignes, notes, cibles, int(i))
                                                                       for i in idx]}
                if out is not None and out is not dernier_out and idx is not None and len(idx) == out.shape[0]:
                    dernier_out = out
                    o = out.detach().float().numpy().copy()
                    lot = [decrire(lignes, notes, cibles, int(i)) for i in idx]
                    for k, c in enumerate(lot):
                        c["predit"] = {
                            "autre": float(1 / (1 + math.exp(-o[k, 0]))),
                            "tonalite": float(o[k, 1] * 5 + 10),
                            "pertinence": float(o[k, 2] * 5 + 10),
                            "reproches": [int(np.argmax(o[k, 3 + 3 * j:6 + 3 * j])) for j in range(3)],
                        }
                    etat["lot_predit"] = {"pas": pas, "commentaires": lot}

                if pas is not None and pas != dernier_pas:
                    perte = loc.get("perte")
                    if dernier_pas is not None and perte is not None:
                        etat["pertes"].append([pas, float(perte.detach().item()), time.time()])
                        etat["pertes"] = etat["pertes"][-6000:]
                    dernier_pas = pas

                # Poids : toutes les 3 s, écart au modèle e5 de départ
                reseau = loc.get("reseau")
                if reseau is not None and time.time() - t_poids > 3.0:
                    t_poids = time.time()
                    with torch.no_grad():
                        params = dict(reseau.base.named_parameters())
                        if ref is None:
                            ref, couches = charger_ref(params)
                        derive = []
                        for n in range(couches):
                            tot, ecart = 0.0, 0.0
                            for s in SUFFIXES:
                                k = f"encoder.layer.{n}.{s}"
                                if k in ref and k in params:
                                    w = params[k].detach()
                                    ecart += float((w - ref[k]).pow(2).sum())
                                    tot += float(ref[k].pow(2).sum())
                            derive.append(math.sqrt(ecart / tot) * 100 if tot else 0.0)
                        etat["derive"] = derive
                        etat["figees"] = sum(1 for n in range(couches)
                                             if not params[f"encoder.layer.{n}.{SUFFIXES[0]}"].requires_grad)
                        etat["derive_temps"].append([pas, derive])
                        etat["derive_temps"] = etat["derive_temps"][-400:]
                        k = f"encoder.layer.{COUCHE_ZOOM}.{SUFFIXES[0]}"
                        if k in ref:
                            w = params[k].detach()[:COTE_ZOOM, :COTE_ZOOM]
                            etat["zoom"] = {"couche": COUCHE_ZOOM + 1,
                                            "ecart": (w - ref[k][:COTE_ZOOM, :COTE_ZOOM]).numpy().round(6).tolist()}
                        tete = reseau.tete.weight.detach()[:, :96]
                        etat["tete"] = tete.numpy().round(4).tolist()
                        etat["ref_source"] = ref.get("__source__", "")

                etat["maj"] = time.time()
                etat["erreur"] = None
                ecrire(etat)
            except Exception:
                etat["erreur"] = traceback.format_exc()[-2000:]
                try:
                    ecrire(etat)
                except Exception:
                    pass
            time.sleep(0.5)

    def charger_ref(params):
        import torch
        ref, chemin = {}, fichier_e5()
        couches = 1 + max(int(k.split(".")[2]) for k in params if k.startswith("encoder.layer."))
        voulues = {f"encoder.layer.{n}.{s}" for n in range(couches) for s in SUFFIXES  # couches figées : écart nul
                   if params[f"encoder.layer.{n}.{s}"].requires_grad}
        if chemin:
            from safetensors import safe_open
            with safe_open(chemin, "pt") as f:
                for k in f.keys():
                    court = k.split("roberta.", 1)[-1]
                    if court in voulues:
                        ref[court] = f.get_tensor(k).float()
            ref["__source__"] = "e5 de départ"
        if not ref or len(ref) < len(voulues):  # repli : photographie des poids au branchement de la sonde
            ref = {k: params[k].detach().clone().float() for k in voulues if k in params}
            ref["__source__"] = "branchement de la sonde"
        return ref, couches

    def decrire(lignes, notes, cibles, i):
        l = lignes[i]
        return {"texte": str(l.get("texte", ""))[:400], "source": l.get("source", ""),
                "type": l.get("type", ""),
                "note": [float(x) for x in notes[i]] if notes is not None else None,
                "cible": int(cibles[i]) if cibles is not None else None}

    def ecrire(etat):
        tmp = SORTIE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(etat, fh, ensure_ascii=False)
        os.replace(tmp, SORTIE)

    threading.Thread(target=boucle, name="suivi_lisnard", daemon=True).start()


_demarrer()
