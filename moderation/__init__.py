"""Modération des commentaires Facebook : à part de l'analyse principale (notes, thèmes).

Demandée par le gestionnaire d'un groupe Facebook de soutien (2026-11-13) : repérer les commentaires à modérer et
ceux qui appellent une réponse. Chaque commentaire Facebook collecté reçoit une catégorie parmi trois :

- insultant : injure ou grossièreté qui vise une personne ou un groupe, menace, appel à la violence, propos haineux
  ou déshumanisant, attaque personnelle méprisante. Une critique dure sans injure n'en est pas une ;
- question : appelle une réponse de l'équipe (vraie question sur le candidat, son programme, le mouvement ; doute
  sincère ; demande d'aide ; affirmation fausse à rectifier). Une question rhétorique n'en est pas une ;
- autre : tout le reste, commentaires positifs compris.

Le modèle est multilingual-e5-base affiné sur les annotations (donnees/moderation/annotations.csv), lues par
Claude, ou par Gemini (PROMPT_GEMINI.md) puis relues par Claude.

Cible d'un insultant (2026-11-14) : L s'il vise David Lisnard, Nouvelle Énergie ou leurs soutiens, A sinon. Donnée
par la lecture (« L: » / « I: ») ; à défaut, cible L/A de l'analyse principale (publication.cibles()). Le modèle de
modération ne la prédit pas : trop peu d'insultes visent Lisnard (16 sur 443).

Mots surveillés (mots_surveilles.txt) : simple filtre du site de modération, hors modèle (site.ecrire_mots()).
Les essais qui ont mené à ce choix (textdetox, zero-shot, Qwen3-4B) sont dans docs/HISTORIQUE.md.

Le classement des nouveaux commentaires suit seul chaque collecte qui ramène du neuf sur Facebook
(collecte/__main__.py) ; annotation et réentraînement se font à la demande (onglet « Modération » de
l'interface, ou « python -m moderation », voir __main__.py et PROCESS.md). Rien ne paraît sur le site ; les
catégories et les commentaires eux-mêmes (texte, auteur, date ; le lien se déduit de la publication, vue
moderation_complete) sont gardés dans la table privée « moderation » de Supabase (publication.py), reliée aux
tables publications, utilisateurs et commentaires (modèle normalisé de web/schema.sql).

Réponses préparées (2026-11-19, reponses.py) : sous chaque commentaire, le site propose des réponses toutes faites,
rangées par thème (ceux de l'analyse) et par objection ; bibliothèque dans moderation/reponses.xlsx et dans Supabase,
modifiable par les modérateurs depuis le site (« python -m moderation reponses » synchronise). Les commentaires sont
rangés par thème par lots lus par Gemini (PROMPT_GEMINI_THEMES.md) ou par Claude.

Mode hors ligne : même règle que l'analyse (analyse/__init__.py), posée ici avant tout import de transformers.
"""
import analyse  # noqa: F401 — pose HF_HUB_OFFLINE=1 si le modèle de départ est déjà sur le disque
