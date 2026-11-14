# Déposer nos données sur Cloudflare R2

Où le projet DavidLisnard dépose ses commentaires pour le groupe RAG politique, et comment. Le stockage du groupe est
sur Cloudflare R2 (stockage de fichiers compatible S3), en vue d'une API qui servira toutes les données.

## Les buckets

- `rag-politique-sources` : les textes publics sur la présidentielle 2027 (programmes, discours, entretiens,
  tribunes, articles, réseaux sociaux des responsables, communication des partis, débats, rapports de la Cour des
  comptes).
- `rag-politique-sources-privees` : ce qui ne doit pas être diffusé (extraits du livre de David Lisnard, et nos
  commentaires du public).

Les deux sont privés : l'accès public de Cloudflare (adresse `r2.dev`) est désactivé, on n'y lit et n'écrit qu'avec
des clés.

## Règles de rangement

1. **Arborescence** : `data/<type de source>/<parti>/<fichier>.parquet`. Les PDF d'origine, s'il y en a, vont dans
   `originaux/<source>/` ; les données, elles, sont toujours en texte dans les Parquet.
2. **Noms de dossiers** en minuscules, sans accents ni espaces.
3. **Format Parquet uniquement** pour les données.
4. Partis déjà utilisés : `nouvelle-energie`, `lfi`, `rn`, `plusieurs-partis`, `cour-des-comptes`.
5. Ce qui est protégé par le droit d'auteur, ou ce qui touche des personnes privées, va dans le bucket privé.

## Ce que dépose ce projet

Les commentaires du public forment le type de source **`commentaires`**, dans le bucket
**`rag-politique-sources-privees`** uniquement :

```
data/commentaires/nouvelle-energie/<source>_<AAAA-MM-JJ>.parquet
```

- **Un seul fichier par source**, daté de sa dernière mise à jour : `youtube_2026-11-13.parquet`,
  `instagram_2026-11-13.parquet`, `bluesky_…`, `facebook_…`, `x_…`. Il contient tous les commentaires de la source.
- **Quand une source change** (nouveaux commentaires, notes refaites, « j'aime »), son fichier est recalculé en entier,
  déposé, vérifié (l'empreinte MD5 renvoyée par R2 doit être celle du fichier), puis l'ancien est supprimé. Jamais
  deux fichiers presque identiques côte à côte. Une source inchangée (même empreinte du contenu) ne repart pas.
- Ce qui part : les commentaires notés et sans doublon (comme sur le site), le texte, la publication à laquelle ils
  répondent, le commentaire parent, les « j'aime », les cinq notes et la cible, telles qu'à la date du fichier.
- **Aucun nom de compte d'auteur.** La colonne `auteur_id` (« u » + 16 caractères) est un HMAC-SHA256 de
  « source|identifiant de plateforme » avec une clé secrète locale, `AUTEUR_CLE` dans `config/cloudflare.env`
  (créée au premier export, à ne jamais partager). Le même compte a toujours le même identifiant, ce qui permet de
  regrouper ses commentaires, mais on ne peut pas remonter au compte, même en essayant des noms. Perdre la clé change
  tous les identifiants (les fichiers sont alors refaits), rien de plus. Les colonnes `compte` et `groupe` restent :
  ce sont les pages, chaînes et groupes publics suivis, pas des personnes.
- Le site (Supabase, Vercel, `python -m web`) ne change pas et ne dépend pas de cet export.

Lire nos fichiers (Python, boto3 + pyarrow) :

```python
import boto3, io, pyarrow.parquet as pq
s3 = boto3.client("s3", endpoint_url="https://<account id>.r2.cloudflarestorage.com",
                  aws_access_key_id="…", aws_secret_access_key="…", region_name="auto")
cle = "data/commentaires/nouvelle-energie/youtube_2026-11-13.parquet"
table = pq.read_table(io.BytesIO(s3.get_object(Bucket="rag-politique-sources-privees", Key=cle)["Body"].read()))
```

## Lancer l'export

```
python -m cloudflare              refait le fichier de chaque source, envoie ceux qui ont changé
python -m cloudflare preparer     seulement les Parquet, dans donnees/cloudflare/lots/
python -m cloudflare envoyer      seulement l'envoi des fichiers préparés qui diffèrent du bucket
python -m cloudflare etat         par source : fichier, commentaires, déposé ou en attente
```

- Automatique : après chaque collecte qui ramène du neuf (`python -m collecte`, après la publication du site).
- Depuis l'interface : bouton **Export Cloudflare** en haut de la fenêtre (le suivi s'affiche dans le journal).
- Clés : `config/cloudflare.env` (privé, hors git ; modèle `config/cloudflare.exemple.env`) : `R2_ENDPOINT`,
  `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` pour R2, `CF_API_TOKEN` et `CF_ACCOUNT_ID` pour l'API Cloudflare, et
  `AUTEUR_CLE`.
- `donnees/cloudflare/lots/` garde le dernier fichier de chaque source ; `etat.json` retient, par source, le fichier
  préparé et le fichier déposé (empreinte du contenu, MD5). Si ce dossier est perdu, l'export suivant refait les
  fichiers et remplace ceux du bucket : toujours un seul fichier par source.
