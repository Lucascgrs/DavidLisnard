"""Modération des commentaires Facebook (à part de l'analyse ; voir moderation/__init__.py et PROCESS.md).

    python -m moderation etat                     combien de commentaires, classés, annotés ; mesures du modèle
    python -m moderation classer                  classe les commentaires qui n'ont pas encore de catégorie
    python -m moderation classer --tout           reclasse tout avec le modèle en service
    python -m moderation tirer [N] [mode]         prépare un lot à annoter (250 par défaut) ; modes : hasard,
                                                  questions, insultes, doutes
    python -m moderation noter K lecture.txt      enregistre la lecture du lot K (« L: 3 » insultes visant Lisnard
                                                  ou Nouvelle Énergie, « I: 17 » autres insultes, « Q: 5, 9 »
                                                  questions ; le reste est « autre ») ; --test pour le jeu de
                                                  test ; --par gemini si c'est Gemini qui a lu (PROMPT_GEMINI.md)
    python -m moderation relire K lecture.txt     relecture par Claude d'un lot lu par Gemini : remplace ses
                                                  annotations et donne le taux d'accord
    python -m moderation entrainer                réentraîne (≈ 30 min), mesure, puis reclasse tout (≈ 30 min)
    python -m moderation publier [--tout]         envoie ce qui a changé dans la table privée « moderation » de
                                                  Supabase (aussi fait seul après classer, noter et entrainer)
    python -m moderation reponses                 synchronise les réponses préparées : moderation/reponses.xlsx ↔
                                                  Supabase (ce que les modérateurs écrivent sur le site est gardé)
    python -m moderation themes etat              réponses préparées, commentaires rangés par thème, reste à ranger
    python -m moderation themes tirer [N] [mode]  prépare un lot à ranger par thème (100 par défaut, les plus récents
                                                  d'abord) ; modes : reponses (ceux qui appellent une réponse), tout
    python -m moderation themes noter K fichier   enregistre la lecture du lot K (« 12: T31 T43 » ou « 12: - ») ;
                                                  --par gemini si c'est Gemini qui a lu (PROMPT_GEMINI_THEMES.md)
    python -m moderation motdepasse               choisit le mot de passe du site de modération (le demande deux
                                                  fois) ; ferme les sessions ouvertes avec l'ancien
    python -m moderation site deployer            met en ligne le site de modération (moderation/site/)
    python -m moderation site apercu              ouvre le site en local (http://localhost:8001)

Les annotations sont faites par Claude, ou par Gemini puis relues par Claude, à la demande de l'utilisateur. Ce qui est annoté ne l'est
jamais deux fois. Le réentraînement se lance aussi depuis l'onglet « Modération » de l'interface.
"""
import sys

from commun.taches import ArretDemande, DejaEnCours


def cmd_site(argv) -> bool:
    """Commandes du site de modération : sans charger le modèle."""
    from moderation import site
    if argv[0] == "motdepasse":
        site.definir_mot_de_passe(site.demander_mot_de_passe())
    elif argv[0] == "site" and argv[1:2] in (["deployer"], ["apercu"]):
        site.deployer() if argv[1] == "deployer" else site.apercu()
    else:
        return False
    return True


def cmd_reponses(argv) -> None:
    """Réponses préparées et thèmes des commentaires (moderation/reponses.py) : sans charger le modèle."""
    from moderation import modele, reponses
    args = argv[2:]
    if argv[0] == "reponses":
        reponses.synchroniser()
    elif argv[1:2] == ["etat"]:
        reponses.afficher_etat()
    elif argv[1:2] == ["tirer"]:
        nombres = [a for a in args if a.isdigit()]
        modes = [a for a in args if not a.isdigit()]
        reponses.tirer(int(nombres[0]) if nombres else reponses.TAILLE_LOT, modes[0] if modes else "reponses")
    elif argv[1:2] == ["noter"] and len(args) >= 2:
        reponses.noter(int(args[0]), args[1], par=args[args.index("--par") + 1] if "--par" in args else "")
        modele.envoyer()  # les thèmes partent dans la table moderation de Supabase
    else:
        raise SystemExit(f"Commande inconnue : {' '.join(argv)}\n{__doc__}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help", "aide"):
        print(__doc__)
        return
    if cmd_site(argv):
        return
    if argv[0] in ("reponses", "themes"):
        cmd_reponses(argv)
        return
    from moderation import donnees, modele
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "etat":
            donnees.afficher_etat()
        elif cmd == "classer":
            modele.classer(tout="--tout" in args)
        elif cmd == "tirer":
            nombres = [a for a in args if a.isdigit()]
            modes = [a for a in args if not a.isdigit()]
            donnees.tirer(int(nombres[0]) if nombres else donnees.TAILLE_LOT, modes[0] if modes else "hasard")
        elif cmd == "noter":
            par = args[args.index("--par") + 1] if "--par" in args else ""
            donnees.noter(int(args[0]), args[1], test="--test" in args, par=par)
            modele.envoyer()  # l'annotation remplace la catégorie du modèle dans la table Supabase
        elif cmd == "relire":
            donnees.noter(int(args[0]), args[1], relire=True)
            modele.envoyer()  # l'annotation remplace la catégorie du modèle dans la table Supabase
        elif cmd == "publier":
            from moderation import publication
            publication.publier(tout="--tout" in args, journal=modele.journal)
        elif cmd == "entrainer":
            modele.entrainer()
        else:
            raise SystemExit(f"Commande inconnue : {cmd}\n{__doc__}")
    except DejaEnCours as e:
        raise SystemExit(f"Modération déjà en cours (processus {e.pid}) : attendre sa fin.")
    except ArretDemande:
        modele.journal("Arrêté à la demande ; ce qui est fait est gardé.")


if __name__ == "__main__":
    main(sys.argv[1:])
