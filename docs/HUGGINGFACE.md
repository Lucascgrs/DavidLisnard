# Déposer nos données sur Hugging Face

Rappel des règles du groupe RAG politique pour le dataset Hugging Face, et de la façon dont le projet DavidLisnard
y dépose ses commentaires. Relu le 2026-11-13 sur le README des deux datasets ; l'organisation elle-même n'a pas
de page de règles.

## L'organisation et ses datasets

- Organisation : [`rag-politique`](https://huggingface.co/rag-politique) (« RAG politique »), le groupe du dépôt
  GitHub [oeilde-sauron/Sourcing-RAG](https://github.com/oeilde-sauron/Sourcing-RAG).
- [`rag-politique/politique-sources`](https://huggingface.co/datasets/rag-politique/politique-sources), **public** :
  l'archive commune des textes publics sur la présidentielle 2027 (programmes, discours, entretiens, tribunes,
  articles, réseaux sociaux des responsables, communication des partis, débats, rapports de la Cour des comptes). La
  base du RAG (Postgres + pgvector) se reconstruit à partir de ces fichiers.
- [`rag-politique/politique-sources-privees`](https://huggingface.co/datasets/rag-politique/politique-sources-privees),
  **privé**, réservé aux membres : les textes protégés par le droit d'auteur (extraits du livre de David Lisnard),
  avec les mêmes règles que le dataset public.

## Règles du dataset

1. **Arborescence** : `data/<type de source>/<parti>/<fichier>.parquet`. Les PDF d'origine, s'il y en a, vont dans
   `originaux/<source>/` ; les données, elles, sont toujours en texte dans les Parquet.
2. **Un nouveau fichier par lot, daté** : on ajoute des fichiers, on ne réécrit pas un fichier existant.
3. **Noms de dossiers** en minuscules, sans accents ni espaces.
4. **Format Parquet uniquement.**
5. Partis déjà utilisés : `nouvelle-energie`, `lfi`, `rn`, `plusieurs-partis`, `cour-des-comptes`.
6. Ce qui est protégé par le droit d'auteur va dans le dataset privé, pas dans le public.

## Ce que dépose ce projet

Le groupe a accepté (2026-11-13) un type de source de plus, **`commentaires`**, pour les commentaires du public. Ils
vont dans le dataset **privé** `rag-politique/politique-sources-privees`, jamais dans le public (choix de
l'utilisateur du 2026-11-13 ; ce qui y avait été déposé le matin a été retiré et le README public rétabli) :

```
data/commentaires/nouvelle-energie/<source>_<AAAA-MM-JJ>.parquet
```

- **Un seul fichier par source**, daté de sa dernière mise à jour : `youtube_2026-11-13.parquet`,
  `instagram_2026-11-13.parquet`, `bluesky_…`, `facebook_…`, `x_…`. Il contient tous les commentaires de la source.
- **Quand une source change** (nouveaux commentaires, notes refaites, « j'aime »), son fichier est recalculé en entier
  et **remplace l'ancien** dans le même commit : le nouveau est déposé, l'ancien supprimé. Jamais deux fichiers
  presque identiques côte à côte ; l'historique git du dataset garde les versions précédentes. Une source inchangée
  (même empreinte du contenu) ne repart pas.
- C'est un écart assumé à la règle 2 (« on ne réécrit pas un fichier existant ») : nos fichiers sont petits (15 Mo en
  tout) et une version à jour vaut mieux qu'une pile de lots qui se recouvrent.
- Ce qui part : les commentaires notés et sans doublon (comme sur le site), le texte, la publication à laquelle ils
  répondent, le commentaire parent, les « j'aime » et les cinq notes et la cible, telles qu'à la date du fichier.
- **Aucun nom de compte d'auteur.** La colonne `auteur_id` (« u » + 16 caractères) est un HMAC-SHA256 de
  « source|identifiant de plateforme » avec une clé secrète locale, `AUTEUR_CLE` dans `config/huggingface.env`
  (créée au premier export, à ne jamais partager). Le même compte a toujours le même identifiant, ce qui permet de
  regrouper ses commentaires, mais on ne peut pas remonter au compte, même en essayant des noms. Perdre la clé change
  tous les identifiants (les fichiers sont alors refaits), rien de plus. Les colonnes `compte` et `groupe` restent :
  ce sont les pages, chaînes et groupes publics suivis, pas des personnes.
- Le site (Supabase, Vercel, `python -m web`) ne change pas et ne dépend pas de cet export : Hugging Face est une
  sortie en plus.
- Nos colonnes ne sont pas celles des autres types de source. Pour que le dataset reste lisible, le README du dataset
  privé
  déclare nos fichiers dans une configuration à part, **`commentaires`**, et la configuration `default` liste les
  autres dossiers de `data/`. L'export entretient seul ces deux configurations et une courte section du README
  (entre `<!-- commentaires:debut -->` et `<!-- commentaires:fin -->`) ; le reste du README n'est pas touché.

```python
from datasets import load_dataset
load_dataset("rag-politique/politique-sources-privees", "commentaires", split="train")
```

## Lancer l'export

```
python -m huggingface              refait le fichier de chaque source, envoie ceux qui ont changé (un commit)
python -m huggingface preparer     seulement les Parquet, dans donnees/huggingface/lots/
python -m huggingface envoyer      seulement l'envoi des fichiers préparés qui diffèrent du dataset
python -m huggingface etat         par source : fichier, commentaires, déposé ou en attente
```

- Automatique : après chaque collecte qui ramène du neuf (`python -m collecte`, après la publication du site).
- Depuis l'interface : bouton **Export Hugging Face** en haut de la fenêtre (le suivi s'affiche dans le journal).
- Jeton : `HF_TOKEN` dans `config/huggingface.env` (privé, hors git), sinon celui de `hf auth login`. Il doit avoir le
  droit d'écriture sur l'organisation `rag-politique`.
- `donnees/huggingface/lots/` garde le dernier fichier de chaque source ; `etat.json` retient, par source, le
  fichier préparé et le fichier déposé (empreinte du contenu, commit). Si ce dossier est perdu, l'export suivant
  refait les fichiers et remplace ceux du dataset : toujours un seul fichier par source.
