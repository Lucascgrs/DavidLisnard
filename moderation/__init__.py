"""Modération des commentaires Facebook : à part de l'analyse principale (notes, thèmes).

Demandée par le gestionnaire d'un groupe Facebook de soutien (2026-11-13) : repérer les commentaires à modérer et
ceux qui appellent une réponse. Chaque commentaire Facebook collecté reçoit une catégorie parmi trois :

- insultant : injure ou grossièreté qui vise une personne ou un groupe, menace, appel à la violence, propos haineux
  ou déshumanisant, attaque personnelle méprisante. Une critique dure sans injure n'en est pas une ;
- question : appelle une réponse de l'équipe (vraie question sur le candidat, son programme, le mouvement ; doute
  sincère ; demande d'aide ; affirmation fausse à rectifier). Une question rhétorique n'en est pas une ;
- autre : tout le reste, commentaires positifs compris.

Le modèle est multilingual-e5-base affiné sur les annotations de Claude (donnees/moderation/annotations.csv).
Les essais qui ont mené à ce choix (textdetox, zero-shot, Qwen3-4B) sont dans docs/HISTORIQUE.md.

Le classement des nouveaux commentaires suit seul chaque collecte qui ramène du neuf sur Facebook
(collecte/__main__.py) ; annotation et réentraînement se font à la demande (onglet « Modération » de
l'interface, ou « python -m moderation », voir __main__.py et PROCESS.md). Rien ne paraît sur le site ; les
catégories et les commentaires eux-mêmes (texte, auteur, date ; le lien se déduit de la publication, vue
moderation_complete) sont gardés dans la table privée « moderation » de Supabase (publication.py), reliée aux
tables publications, utilisateurs et commentaires (modèle normalisé de web/schema.sql).

Mode hors ligne : même règle que l'analyse (analyse/__init__.py), posée ici avant tout import de transformers.
"""
import analyse  # noqa: F401 — pose HF_HUB_OFFLINE=1 si le modèle de départ est déjà sur le disque
