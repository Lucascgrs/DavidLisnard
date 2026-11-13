"""Entraînement, mesure et classement du modèle de modération.

Modèle : intfloat/multilingual-e5-base (le même modèle de départ que l'analyse), affiné en entier en trois classes
(autre, insultant, question). Réglages retenus le 2026-11-13 après essais : préfixe « query: », 128 jetons au plus,
4 époques, lots de 16, taux 3e-5 avec 10 % de montée puis décroissance linéaire, poids des classes rares adoucis
(racine de l'inverse de la fréquence), graine 0. Une trentaine de minutes d'entraînement sur le processeur, puis
environ 0,1 s par commentaire pour classer.
"""
import random
import shutil
import time

from commun.fichiers import ecrire_csv, ecrire_json, lire_csv
from commun.taches import verifier_arret, verrou
from commun.textes import maintenant
from moderation import donnees as d

MODELE_DEPART = "intfloat/multilingual-e5-base"
PREFIXE = "query: "
LONGUEUR, LOT, EPOQUES, TAUX = 128, 16, 4, 3e-5


def _torch():
    import torch
    torch.set_num_threads(8)
    return torch


def journal(texte: str) -> None:
    ligne = f"{maintenant()} {texte}"
    print(ligne, flush=True)
    d.DOSSIER.mkdir(parents=True, exist_ok=True)
    with open(d.JOURNAL, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def predire(mod, tok, textes: list[str], arret: bool = True, avancement=None):
    """Probabilités (autre, insultant, question) de chaque texte, par lots de longueurs voisines."""
    torch = _torch()
    ordre = sorted(range(len(textes)), key=lambda i: len(textes[i]))
    P = [None] * len(textes)
    with torch.inference_mode():
        for k in range(0, len(ordre), 32):
            if arret:
                verifier_arret(d.TACHE)
            idx = ordre[k:k + 32]
            enc = tok([PREFIXE + textes[i] for i in idx], truncation=True, max_length=LONGUEUR, padding=True,
                      return_tensors="pt")
            for i, p in zip(idx, torch.softmax(mod(**enc).logits, -1).tolist()):
                P[i] = p
            if avancement:
                avancement(min(k + 32, len(ordre)), len(ordre))
    return P


def mesurer(test: list[dict], P) -> dict:
    """Mesures sur le jeu de test. Le test surreprésente les commentaires que textdetox croyait toxiques : chaque
    annotation porte un poids (1, ou 1327/400 pour le tirage au hasard parmi les autres) qui ramène les parts
    d'alertes justes à ce qu'on verrait sur l'ensemble des commentaires."""
    pred = [d.CATEGORIES[max(range(3), key=lambda k: p[k])] for p in P]
    w = [float(a.get("poids") or 1) for a in test]
    vrai = [a["categorie"] for a in test]
    m = {"n": len(test), "accord": sum(p == v for p, v in zip(pred, vrai)) / max(len(test), 1)}
    for c in ("insultant", "question"):
        tp = sum(wi for wi, p, v in zip(w, pred, vrai) if p == c and v == c)
        alertes = sum(wi for wi, p in zip(w, pred) if p == c)
        reels = sum(wi for wi, v in zip(w, vrai) if v == c)
        m[c] = {"n": sum(v == c for v in vrai), "alertes": sum(p == c for p in pred),
                "justes": tp / alertes if alertes else 0, "trouves": tp / reels if reels else 0}
    return m


def entrainer() -> None:
    """Réentraîne sur toutes les annotations d'entraînement, mesure sur le test, remplace le modèle en service,
    puis reclasse tous les commentaires avec la nouvelle version."""
    torch = _torch()
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    with verrou(d.TACHE, sans_veille=True):
        ann = list(d.lire_annotations().values())
        app = [a for a in ann if a["jeu"] != "test"]
        test = [a for a in ann if a["jeu"] == "test"]
        journal(f"Réentraînement : {len(app)} annotations d'entraînement, {len(test)} de test.")
        torch.manual_seed(0)
        random.seed(0)
        tok = AutoTokenizer.from_pretrained(MODELE_DEPART)
        mod = AutoModelForSequenceClassification.from_pretrained(
            MODELE_DEPART, num_labels=3, id2label=dict(enumerate(d.CATEGORIES)),
            label2id={c: i for i, c in enumerate(d.CATEGORIES)})
        X = [PREFIXE + a["texte"] for a in app]
        y = torch.tensor([d.CATEGORIES.index(a["categorie"]) for a in app])
        cnt = torch.bincount(y, minlength=3).float().clamp(min=1)
        lossf = torch.nn.CrossEntropyLoss(weight=(cnt.sum() / (3 * cnt)) ** 0.5)
        opt = torch.optim.AdamW(mod.parameters(), lr=TAUX, weight_decay=0.01)
        nstep = EPOQUES * ((len(X) + LOT - 1) // LOT)
        sched = torch.optim.lr_scheduler.LambdaLR(
            opt, lambda s: min(1, (s + 1) / (0.1 * nstep)) * max(0, (nstep - s) / nstep))
        t0, step = time.time(), 0
        for ep in range(EPOQUES):
            mod.train()
            idx = sorted(range(len(X)), key=lambda i: len(X[i]) + random.random() * 40)
            lots = [idx[i:i + LOT] for i in range(0, len(idx), LOT)]
            random.shuffle(lots)
            for b in lots:
                verifier_arret(d.TACHE)
                enc = tok([X[i] for i in b], truncation=True, max_length=LONGUEUR, padding=True, return_tensors="pt")
                lossf(mod(**enc).logits, y[b]).backward()
                torch.nn.utils.clip_grad_norm_(mod.parameters(), 1.0)
                opt.step(), sched.step(), opt.zero_grad()
                step += 1
                if step % 50 == 0:
                    journal(f"  époque {ep + 1}/{EPOQUES}, étape {step}/{nstep} ({time.time() - t0:.0f} s)")
                    ecrire_json(d.AVANCEMENT, {"tache": "entraînement", "fait": step, "total": nstep})
        mod.eval()
        mesures = mesurer(test, predire(mod, tok, [a["texte"] for a in test]))
        ancien = d.infos_modele() or {}
        version = f"m{int(ancien.get('version', 'm0')[1:]) + 1}"
        infos = {"version": version, "le": maintenant(), "modele_depart": MODELE_DEPART, "annotations": len(app),
                 "test": len(test), "mesures": mesures,
                 "reglages": {"longueur": LONGUEUR, "lot": LOT, "epoques": EPOQUES, "taux": TAUX},
                 "historique": ancien.get("historique", []) + ([{k: ancien[k] for k in ("version", "le", "mesures")}]
                                                              if ancien else [])}
        tmp = d.MODELE.with_name("moderation_nouveau")
        shutil.rmtree(tmp, ignore_errors=True)
        mod.save_pretrained(tmp)
        tok.save_pretrained(tmp)
        ecrire_json(tmp / "infos.json", infos)
        shutil.rmtree(d.MODELE, ignore_errors=True)
        tmp.rename(d.MODELE)
        journal(f"Modèle {version} en service : accord {mesures['accord']:.0%} sur le test ; insultes "
                f"{mesures['insultant']['justes']:.0%} justes, {mesures['insultant']['trouves']:.0%} trouvées ; "
                f"questions {mesures['question']['justes']:.0%} justes, {mesures['question']['trouves']:.0%} trouvées.")
        _classer(tout=True, mod=mod, tok=tok, version=version)


def classer(tout: bool = False) -> None:
    """Classe les commentaires Facebook qui n'ont pas encore de catégorie de la version en service (tous avec
    tout=True)."""
    with verrou(d.TACHE, sans_veille=True):
        _classer(tout)


def _classer(tout: bool, mod=None, tok=None, version: str | None = None) -> None:
    infos = d.infos_modele()
    if not infos:
        journal("Aucun modèle de modération : lancer d'abord « python -m moderation entrainer ».")
        return
    version = version or infos["version"]
    notes = {} if tout else {k: v for k, v in d.lire_notes().items() if v["version"] == version}
    a_faire = [c for c in d.commentaires() if c["cle"] not in notes]
    if not a_faire:
        journal(f"Classement : rien de nouveau ({len(notes)} commentaires déjà classés par {version}).")
        d.AVANCEMENT.unlink(missing_ok=True)
        return
    journal(f"Classement par {version} : {len(a_faire)} commentaires.")
    if mod is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(d.MODELE)
        mod = AutoModelForSequenceClassification.from_pretrained(d.MODELE).eval()
    garde = {} if tout else {k: v for k, v in d.lire_notes().items() if v["version"] == version}
    t0 = time.time()
    for debut in range(0, len(a_faire), 2000):  # enregistré par tranches : un arrêt garde ce qui est fait
        tranche = a_faire[debut:debut + 2000]
        P = predire(mod, tok, [c["texte"] for c in tranche],
                    avancement=lambda f, t: ecrire_json(d.AVANCEMENT, {"tache": "classement", "fait": debut + f,
                                                                       "total": len(a_faire)}))
        le = maintenant()
        for c, p in zip(tranche, P):
            garde[c["cle"]] = {"cle": c["cle"], "categorie": d.CATEGORIES[max(range(3), key=lambda k: p[k])],
                               "p_autre": f"{p[0]:.3f}", "p_insultant": f"{p[1]:.3f}", "p_question": f"{p[2]:.3f}",
                               "version": version, "classe_le": le}
        ecrire_csv(d.NOTES, garde.values(), d.CHAMPS_NOTES)
        journal(f"  {debut + len(tranche)}/{len(a_faire)} classés ({time.time() - t0:.0f} s)")
    d.AVANCEMENT.unlink(missing_ok=True)
    n = list(garde.values())
    journal(f"Classement terminé : {sum(x['categorie'] == 'insultant' for x in n)} insultants, "
            f"{sum(x['categorie'] == 'question' for x in n)} questions sur {len(n)} commentaires.")
    envoyer()


def envoyer() -> None:
    """Table privée « moderation » de Supabase (moderation/publication.py). Un échec n'annule pas le classement :
    il est noté, et « python -m moderation publier » reprendra ce qui n'est pas parti."""
    from moderation import publication
    try:
        publication.publier(journal=journal)
    except Exception as e:  # noqa: BLE001 — réseau, base en pause…
        journal(f"Envoi à Supabase impossible ({type(e).__name__} : {e}) ; relancer « python -m moderation publier ».")


def remesurer() -> dict:
    """Mesures du modèle en service sur le test actuel (sans réentraîner)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(d.MODELE)
    mod = AutoModelForSequenceClassification.from_pretrained(d.MODELE).eval()
    test = [a for a in lire_csv(d.ANNOTATIONS) if a["jeu"] == "test"]
    return mesurer(test, predire(mod, tok, [a["texte"] for a in test], arret=False))
