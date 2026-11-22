-- Base Supabase du site. Rejouable sans risque : « python -m commentaires installer » l'exécute à chaque fois.
-- Rien n'est lisible sans connexion (rôle anon) : le site public se lit avec le mot de passe défini par
-- « python -m commentaires motdepasse » (compte partagé de rôle « lecteur »), et ne peut que lire ; seuls
-- « python -m commentaires publier » et « python -m moderation publier » écrivent, avec la clé secrète.
--
-- Modèle normalisé (2026-11-13) : chaque donnée n'est écrite qu'une fois, les tables se rejoignent par des clés
-- entières.
--
--   sources ─┬─ comptes ── publications ─┬─ commentaires (notes du site) ── parent : commentaires
--            ├─ utilisateurs (privée) ───┤
--            └───────────────────────────┴─ moderation (privée) ── commentaires (texte, auteur… pris là s'il y est)
--
-- Une source, un compte suivi, une publication, un auteur ne sont écrits qu'une fois ; un commentaire ne porte que
-- ses propres données et des numéros. La semaine et la taille en mots sont calculées par la base.

create extension if not exists unaccent with schema extensions;

-- Recherche en français sans tenir compte des accents ni des terminaisons (« énergie » trouve « energies »).
do $$ begin
  if not exists (select 1 from pg_ts_config where cfgname = 'fr') then
    create text search configuration public.fr (copy = pg_catalog.french);
    alter text search configuration public.fr
      alter mapping for hword, hword_part, word with extensions.unaccent, french_stem;
  end if;
end $$;

-- Passage de l'ancien modèle (clés en texte « youtube:<id> », source, compte et groupe recopiés sur chaque
-- commentaire) au modèle normalisé : les anciennes tables sont mises de côté, intactes, dans le schéma « ancien »
-- (invisible du site), puis tout est renvoyé (« python -m commentaires publier » et « python -m moderation publier » le
-- détectent seuls). Une fois le nouveau modèle vérifié : « drop schema ancien cascade; » libère la place.
do $$ begin
  if exists (select 1 from information_schema.columns
             where table_schema = 'public' and table_name = 'publications' and column_name = 'id'
               and data_type = 'text') then
    create schema if not exists ancien;
    revoke all on schema ancien from public, anon, authenticated;
    drop view if exists public.moderation_complete;
    drop function if exists public.evolution(jsonb);
    drop function if exists public.selection(jsonb);
    alter table public.moderation set schema ancien;
    alter table public.commentaires set schema ancien;
    alter table public.publications set schema ancien;
  end if;
end $$;

-- Les plateformes. Numéros fixes, écrits ici : le site et la publication les relisent dans la table.
create table if not exists sources (
  id   smallint primary key,
  nom  text not null unique
);
insert into sources (id, nom) values (1, 'youtube'), (2, 'instagram'), (3, 'bluesky'), (4, 'facebook'), (5, 'x')
on conflict (id) do nothing;

-- Les comptes suivis (chaînes, comptes, groupes Facebook, « Recherche YouTube »…) et leur groupe.
create table if not exists comptes (
  id      smallint generated always as identity primary key,
  source  smallint not null references sources (id),
  nom     text not null,
  groupe  text not null check (groupe in ('officiel', 'media', 'commentateur', 'soutien', 'autre')),
  unique (source, nom)
);

-- Les vidéos et posts sous lesquels on commente. La source se lit dans le compte.
create table if not exists publications (
  id      integer generated always as identity primary key,
  compte  smallint not null references comptes (id),
  code    text not null,           -- identifiant sur la plateforme (vidéo YouTube, code du post Instagram…)
  titre   text,
  lien    text,
  date    timestamp,
  unique (compte, code)
);

-- Les auteurs des commentaires. PRIVÉE (aucune règle de lecture) : le site ne montre aucun auteur ; le public ne
-- voit dans les commentaires qu'un numéro sans signification.
create table if not exists utilisateurs (
  id           integer generated always as identity primary key,
  source       smallint not null references sources (id),
  identifiant  text not null,      -- identifiant sur la plateforme, à défaut le nom affiché
  nom          text,               -- nom affiché, seulement s'il diffère de l'identifiant
  unique (source, identifiant)
);

-- Les commentaires notés, publiés sur le site.
create table if not exists commentaires (
  source       smallint not null references sources (id),
  code         text not null,      -- identifiant du commentaire sur la plateforme (« did/rkey » pour Bluesky)
  publication  integer not null references publications (id),
  utilisateur  integer references utilisateurs (id),
  parent       text,               -- code du commentaire publié auquel il répond (même source)
  date         timestamp,
  semaine      date generated always as (date_trunc('week', date)::date) stored,  -- lundi de la semaine
  reponse      boolean not null,
  likes        integer not null default 0,
  texte        text not null,
  mots         integer generated always as
                 (coalesce(array_length(regexp_split_to_array(btrim(texte), '\s+'), 1), 0)) stored,
  tonalite     smallint not null,
  forme        smallint not null,
  systeme      smallint not null,
  idees        smallint not null,
  pertinence   smallint not null,
  cible        char(1) not null,   -- L : parle de Lisnard ; A : d'autre chose
  fiabilite    text check (fiabilite in ('bonne', 'moyenne', 'faible', 'relue')),
  primary key (source, code),
  foreign key (source, parent) references commentaires (source, code) on delete set null (parent)
);

create index if not exists commentaires_date on commentaires (date desc nulls last);
-- Toutes les colonnes des filtres sauf le texte : evolution() et les comptages se lisent dans cet index au lieu de
-- la table (sinon, cache froid, on dépasse le délai du public). Compte et groupe passent par la publication.
create index if not exists commentaires_resume on commentaires (semaine) include
  (source, publication, fiabilite, reponse, cible, tonalite, forme, systeme, idees, pertinence);
create index if not exists commentaires_pertinence on commentaires (pertinence desc);
create index if not exists commentaires_likes on commentaires (likes desc);
create index if not exists commentaires_mots on commentaires (mots desc);
create index if not exists commentaires_publication on commentaires (publication);
create index if not exists commentaires_utilisateur on commentaires (utilisateur);
create index if not exists commentaires_parent on commentaires (source, parent) where parent is not null;
-- Recherche plein texte sur un index d'expression : rien n'est stocké en plus du texte dans la table.
create index if not exists commentaires_recherche on commentaires
  using gin (to_tsvector('public.fr'::regconfig, texte));

-- Données calculées en bloc : « meta » (chiffres du projet), « cube » (comptages par semaine), « themes ».
create table if not exists syntheses (
  nom     text primary key,
  donnees jsonb not null,
  maj     timestamptz not null default now()
);

-- Modération des commentaires Facebook (moderation/, à part du site) : écrite par « python -m moderation publier ».
-- PRIVÉE : sécurité par ligne active et aucune règle de lecture, donc ni le public (anon) ni le site ne la voient.
-- Le commentaire lui-même (publication, auteur, date, texte) n'y est écrit que s'il n'est pas déjà dans
-- commentaires (un commentaire Facebook est classé avant d'être noté et publié) : la vue moderation_complete le
-- prend dans l'une ou l'autre. Catégorie retenue et origine se déduisent (annotation, sinon modèle), la catégorie
-- du modèle aussi (la plus probable).
create table if not exists moderation (
  source       smallint not null references sources (id),
  code         text not null,      -- identifiant Facebook du commentaire
  publication  integer references publications (id),
  utilisateur  integer references utilisateurs (id),
  parent       text,               -- code du commentaire auquel il répond, s'il diffère de celui de commentaires
  date         timestamp,
  texte        text,
  p_insultant  real,
  p_question   real,
  p_autre      real,
  version      text,               -- version du modèle de modération (m1, m2…)
  annotation   text check (annotation is null or annotation in ('insultant', 'question', 'autre')),
  classe_le    timestamp,
  primary key (source, code)
);
create index if not exists moderation_publication on moderation (publication);
-- « Qui est visé » (cible L/A, 2026-11-14) retiré de la modération le 2026-11-19 : les vues qui le lisaient sont
-- supprimées d'abord (recréées plus bas), puis les deux colonnes.
drop view if exists moderation_complete, moderation_lignes;
alter table moderation drop column if exists cible, drop column if exists annotation_cible;

alter table sources enable row level security;
alter table comptes enable row level security;
alter table publications enable row level security;
alter table utilisateurs enable row level security;
alter table commentaires enable row level security;
alter table syntheses enable row level security;
alter table moderation enable row level security;
drop policy if exists lecture on sources;
drop policy if exists lecture on comptes;
drop policy if exists lecture on publications;
drop policy if exists lecture on commentaires;
drop policy if exists lecture on syntheses;

-- Accès par mot de passe (2026-11-14) : on se connecte par Supabase Auth au compte partagé des lecteurs
-- (« python -m commentaires motdepasse », adresse fixe, rôle app_metadata.role = « lecteur » que seule la clé secrète peut
-- écrire ; inscriptions fermées). Le compte des modérateurs lit aussi ces tables (ses vues les rejoignent). Le compte
-- doit encore exister : changer le mot de passe (compte recréé) coupe aussitôt les sessions ouvertes.
create or replace function public.peut_lire()
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') in ('lecteur', 'moderateur')
     and exists (select 1 from auth.users u where u.id = auth.uid())
$$;
revoke execute on function public.peut_lire() from public, anon;
grant execute on function public.peut_lire() to authenticated;
create policy lecture on sources for select to authenticated using ((select public.peut_lire()));
create policy lecture on comptes for select to authenticated using ((select public.peut_lire()));
create policy lecture on publications for select to authenticated using ((select public.peut_lire()));
-- commentaires : la règle ne vérifie que la connexion (seuls les deux comptes partagés existent, inscriptions et
-- connexions anonymes fermées) ; le compte est vérifié par selection() et commentaire(), par où passe le site. Une
-- règle qui appelle peut_lire() interdirait à PostgreSQL d'utiliser l'index de la recherche plein texte (l'opérateur
-- @@ n'est pas « leakproof ») : 6 s au lieu de 0,1 s, mesuré le 2026-11-14.
create policy lecture on commentaires for select to authenticated using (true);
create policy lecture on syntheses for select to authenticated using ((select public.peut_lire()));
revoke all on sources, comptes, publications, commentaires, syntheses from anon;
revoke insert, update, delete, truncate on sources, comptes, publications, commentaires, syntheses
  from authenticated;
grant select on sources, comptes, publications, commentaires, syntheses to authenticated;
revoke all on utilisateurs, moderation from anon, authenticated;
alter role anon set statement_timeout = '8s';  -- 3 s par défaut : trop court quand la base sort de veille
alter role authenticated set statement_timeout = '8s';  -- le site public se lit maintenant sous ce rôle

-- Tout ce qu'il faut à un administrateur, en une ligne : catégorie, texte, auteur, publication et lien direct vers
-- le commentaire (lien de la publication + comment_id, et reply_comment_id pour une réponse). security_invoker :
-- la vue applique les droits de celui qui la lit, donc reste aussi privée que la table.
create or replace view moderation_complete with (security_invoker = true) as
with m as (
  select m.source, m.code,
         coalesce(m.publication, c.publication) as publication,
         coalesce(m.utilisateur, c.utilisateur) as utilisateur,
         coalesce(m.parent, c.parent) as parent,
         coalesce(m.date, c.date) as date,
         coalesce(m.texte, c.texte) as texte,
         case when m.p_autre is null then null
              when m.p_autre >= m.p_insultant and m.p_autre >= m.p_question then 'autre'
              when m.p_insultant >= m.p_question then 'insultant' else 'question' end as modele,
         m.p_insultant, m.p_question, m.p_autre, m.version, m.annotation, m.classe_le
  from public.moderation m
  left join public.commentaires c on c.source = m.source and c.code = m.code
)
select s.nom || ':' || m.code as cle,
       coalesce(m.annotation, m.modele) as categorie,
       case when m.annotation is not null then 'annotation' else 'modele' end as origine,
       m.modele, m.p_insultant, m.p_question, m.p_autre, m.version, m.annotation, m.classe_le,
       m.date, m.texte, coalesce(u.nom, u.identifiant) as auteur, u.identifiant as auteur_id,
       case when m.parent is null then null else s.nom || ':' || m.parent end as parent,
       p.titre as publication_titre, p.lien as publication_lien,
       case when p.lien is null then null
            when m.parent is null then p.lien || '?comment_id=' || m.code
            else p.lien || '?comment_id=' || m.parent || '&reply_comment_id=' || m.code end as lien,
       m.publication as publication_id
from m
join public.sources s on s.id = m.source
left join public.publications p on p.id = m.publication
left join public.utilisateurs u on u.id = m.utilisateur;
revoke all on moderation_complete from anon, authenticated;

-- ── Site de modération (moderation/site/, « python -m moderation site … ») ──────────────────────────────────────
-- Réservé aux modérateurs : on se connecte par Supabase Auth avec le mot de passe défini par
-- « python -m moderation motdepasse ». Ce compte porte app_metadata.role = « moderateur », que seule la clé
-- secrète peut écrire ; les inscriptions sont fermées. Toute personne non connectée (anon), ou connectée sans ce
-- rôle, ne voit rien : les règles ci-dessous s'appliquent aux tables, et les vues (security_invoker) en héritent.
--
-- Économie de la base (offre gratuite) : le navigateur de chaque modérateur télécharge tout une fois, le garde
-- (IndexedDB), puis ne demande que ce qui a changé depuis (colonne maj, retraits, suivi). Filtres, tris et
-- comptages se font chez lui : la base ne fait que des lectures par index, presque toujours vides.

-- Le compte doit encore exister : changer le mot de passe (compte recréé) coupe aussitôt les sessions ouvertes,
-- sans attendre la fin de validité de leur jeton.
create or replace function public.est_moderateur()
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'moderateur'
     and exists (select 1 from auth.users u where u.id = auth.uid())
$$;
revoke execute on function public.est_moderateur() from public, anon;
grant execute on function public.est_moderateur() to authenticated;

-- Date de la dernière écriture de chaque ligne de moderation (ajout ou changement), et liste des lignes retirées :
-- ce que le site redemande à chaque actualisation.
alter table moderation add column if not exists maj timestamptz not null default clock_timestamp();
create index if not exists moderation_maj on moderation (maj, code);
create or replace function public.moderation_dater()
returns trigger language plpgsql as $$
begin
  new.maj := clock_timestamp();
  return new;
end $$;
drop trigger if exists dater on moderation;
create trigger dater before update on moderation for each row execute function public.moderation_dater();

create table if not exists moderation_retires (
  code  text primary key,
  le    timestamptz not null default clock_timestamp()
);
create index if not exists moderation_retires_le on moderation_retires (le);
alter table moderation_retires enable row level security;
create or replace function public.moderation_retirer()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.moderation_retires (code) values (old.code)
  on conflict (code) do update set le = clock_timestamp();
  return old;
end $$;
drop trigger if exists retirer on moderation;
create trigger retirer after delete on moderation for each row execute function public.moderation_retirer();
-- Un commentaire retiré puis remis n'est plus « retiré ».
create or replace function public.moderation_remettre()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  delete from public.moderation_retires where code = new.code;
  return new;
end $$;
drop trigger if exists remettre on moderation;
create trigger remettre after insert on moderation for each row execute function public.moderation_remettre();

-- Suivi des modérateurs. « a_traiter » est écrit aussi (au lieu d'effacer la ligne), pour que les autres
-- navigateurs voient qu'une marque a été retirée. Écrit depuis le site seulement : rien ne l'efface au reclassement.
create table if not exists moderation_suivi (
  source  smallint not null references sources (id),
  code    text not null,
  etat    text not null,
  par     text,                     -- prénom donné à la connexion (le compte est partagé)
  le      timestamptz not null default clock_timestamp(),
  primary key (source, code)
);
alter table moderation_suivi drop constraint if exists moderation_suivi_etat_check;
alter table moderation_suivi add constraint moderation_suivi_etat_check
  check (etat in ('a_traiter', 'traite', 'sans_suite'));
create index if not exists moderation_suivi_le on moderation_suivi (le);
alter table moderation_suivi enable row level security;

drop policy if exists moderateurs on moderation;
drop policy if exists moderateurs on utilisateurs;
drop policy if exists moderateurs on moderation_suivi;
drop policy if exists moderateurs on moderation_retires;
-- Publications que voient les modérateurs : celles de tous les groupes Facebook de la base (2026-11-22 ; de 2026-11-14
-- à 2026-11-22, un seul groupe). Le site choisit ensuite les groupes à montrer, « Cap 2027 avec David Lisnard » par défaut.
create or replace function public.moderation_publications()
returns setof integer
language sql stable
as $$
  select p.id from public.publications p join public.comptes k on k.id = p.compte
  where k.source = (select id from public.sources where nom = 'facebook')
$$;
revoke execute on function public.moderation_publications() from public, anon;
grant execute on function public.moderation_publications() to authenticated;
create policy moderateurs on moderation for select to authenticated using (
  (select public.est_moderateur())
  and coalesce(publication, (select c.publication from public.commentaires c
                             where c.source = moderation.source and c.code = moderation.code))
      in (select public.moderation_publications()));
create policy moderateurs on utilisateurs for select to authenticated using ((select public.est_moderateur()));
create policy moderateurs on moderation_retires for select to authenticated using ((select public.est_moderateur()));
create policy moderateurs on moderation_suivi for all to authenticated
  using ((select public.est_moderateur())) with check ((select public.est_moderateur()));
grant select on moderation, utilisateurs, moderation_retires to authenticated;
grant select, insert, update on moderation_suivi to authenticated;
revoke all on moderation_suivi, moderation_retires from anon;
revoke delete on moderation_suivi from authenticated;

-- Vues de la première version du site (tout calculé par la base à chaque recherche) : remplacées.
drop view if exists moderation_bilan, moderation_auteurs, moderation_publications, moderation_site;

-- Thèmes du commentaire (« T31 T43 ») : ceux de la lecture pour les réponses préparées (moderation/reponses.py).
alter table moderation add column if not exists themes text;

-- Les commentaires, sous forme compacte : la publication (titre, lien, groupe) est envoyée à part, une seule fois.
create or replace view moderation_lignes with (security_invoker = true) as
select m.code,
       coalesce(m.annotation, case when m.p_autre is null then null
              when m.p_autre >= m.p_insultant and m.p_autre >= m.p_question then 'autre'
              when m.p_insultant >= m.p_question then 'insultant' else 'question' end) as categorie,
       m.annotation is not null as verifie,
       m.p_insultant as pi, m.p_question as pq, m.p_autre as pa,
       coalesce(m.publication, c.publication) as publication,
       coalesce(m.parent, c.parent) as parent,
       coalesce(m.date, c.date) as date,
       coalesce(m.texte, c.texte) as texte,
       coalesce(u.nom, u.identifiant) as auteur, u.identifiant as auteur_id,
       m.maj,
       m.themes  -- thèmes du commentaire, pour les réponses préparées (2026-11-19)
from public.moderation m
left join public.commentaires c on c.source = m.source and c.code = m.code
left join public.utilisateurs u on u.id = coalesce(m.utilisateur, c.utilisateur);

-- Les publications Facebook : titre, lien, groupe et chemin du groupe dans l'adresse (fiche de membre).
create or replace view moderation_pubs with (security_invoker = true) as
select p.id, p.titre, p.lien, p.date, k.nom as groupe, substring(p.lien from '/groups/([^/]+)/') as chemin
from public.publications p
join public.comptes k on k.id = p.compte
where k.source = (select id from public.sources where nom = 'facebook')
  and p.id in (select public.moderation_publications())
  and (select public.est_moderateur());

revoke all on moderation_lignes, moderation_pubs from anon;
grant select on moderation_complete, moderation_lignes, moderation_pubs to authenticated;

-- Marquer un commentaire : « traite », « sans_suite », ou « a_traiter » (retire la marque). Rend l'heure
-- d'enregistrement.
drop function if exists public.suivre(text, text, text);
create function public.suivre(_cle text, _etat text, _par text default null)
returns timestamptz
language plpgsql
as $$
declare
  src smallint := (select id from public.sources where nom = split_part(_cle, ':', 1));
  cod text := substr(_cle, strpos(_cle, ':') + 1);
  quand timestamptz := clock_timestamp();
begin
  if not public.est_moderateur() then
    raise exception 'réservé aux modérateurs' using errcode = '42501';
  end if;
  insert into public.moderation_suivi (source, code, etat, par, le)
  values (src, cod, coalesce(_etat, 'a_traiter'), nullif(_par, ''), quand)
  on conflict (source, code) do update set etat = excluded.etat, par = excluded.par, le = excluded.le;
  return quand;
end $$;
revoke execute on function public.suivre(text, text, text) from public, anon;
grant execute on function public.suivre(text, text, text) to authenticated;

-- La sélection de la page Commentaires, définie une seule fois. Le filtre (jsonb, corps de la requête) peut contenir :
--   du, au (lundis, AAAA-MM-JJ ; du absent = depuis le début), sources, groupes, comptes (listes de noms),
--   reponse (true/false), cible ('L'/'A'), fiabilites (liste), q (mots cherchés),
--   tonalite, forme, systeme, idees, pertinence ([min, max] de 0 à 20), mots_min (taille minimale en mots).
-- Paramètre unique et sans nom : l'API passe alors le corps tel quel ($1), comme une constante de la requête. Avec un
-- paramètre nommé, elle le passe comme une valeur par ligne, et les sous-requêtes des sources et des comptes sont
-- refaites pour chaque commentaire (plus de 8 s). Fonction SQL simple et stable, sans « set search_path » (qui
-- empêcherait PostgreSQL de l'intégrer à la requête, donc d'utiliser les index) : les noms sont écrits en entier.
drop function if exists selection(jsonb);
create function selection(jsonb)
returns setof commentaires
language sql stable
as $$
  select c.* from public.commentaires c
  where (select public.peut_lire())
    and ($1->>'du' is null or c.semaine >= ($1->>'du')::date)
    and ($1->>'au' is null or c.semaine <= ($1->>'au')::date)
    and ($1->'sources' is null or c.source in (select s.id from public.sources s where $1->'sources' ? s.nom))
    and (($1->'groupes' is null and $1->'comptes' is null)
         or c.publication in (select p.id from public.publications p join public.comptes k on k.id = p.compte
                              where ($1->'groupes' is null or $1->'groupes' ? k.groupe)
                                and ($1->'comptes' is null or $1->'comptes' ? k.nom)))
    and ($1->'fiabilites' is null or $1->'fiabilites' ? c.fiabilite)
    and ($1->>'reponse' is null or c.reponse = ($1->>'reponse')::boolean)
    and ($1->>'cible' is null or c.cible = $1->>'cible')
    and c.tonalite between coalesce(($1->'tonalite'->>0)::int, 0) and coalesce(($1->'tonalite'->>1)::int, 20)
    and c.forme between coalesce(($1->'forme'->>0)::int, 0) and coalesce(($1->'forme'->>1)::int, 20)
    and c.systeme between coalesce(($1->'systeme'->>0)::int, 0) and coalesce(($1->'systeme'->>1)::int, 20)
    and c.idees between coalesce(($1->'idees'->>0)::int, 0) and coalesce(($1->'idees'->>1)::int, 20)
    and c.pertinence between coalesce(($1->'pertinence'->>0)::int, 0) and coalesce(($1->'pertinence'->>1)::int, 20)
    and ($1->>'mots_min' is null or c.mots >= ($1->>'mots_min')::int)
    and (coalesce($1->>'q', '') = ''
         or to_tsvector('public.fr'::regconfig, c.texte) @@ websearch_to_tsquery('public.fr'::regconfig, $1->>'q'))
$$;

-- Un commentaire par sa clé « source:code » (adresse partageable du site, commentaire parent).
create or replace function commentaire(cle text)
returns setof commentaires
language sql stable
as $$
  select c.* from public.commentaires c
  where (select public.peut_lire())
    and c.source = (select s.id from public.sources s where s.nom = split_part(cle, ':', 1))
    and c.code = substr(cle, strpos(cle, ':') + 1)
$$;

-- Évolution de la sélection, semaine par semaine : nombre, moyennes, parts de critiques et d'éloges.
drop function if exists evolution(jsonb);
create function evolution(jsonb)
returns table (semaine date, n bigint, tonalite numeric, forme numeric, systeme numeric, idees numeric,
               pertinence numeric, bas_tonalite bigint, haut_tonalite bigint)
language sql stable
as $$
  select s.semaine, count(*), round(avg(s.tonalite), 2), round(avg(s.forme), 2), round(avg(s.systeme), 2),
         round(avg(s.idees), 2), round(avg(s.pertinence), 2),
         count(*) filter (where s.tonalite <= 6), count(*) filter (where s.tonalite >= 14)
  from public.selection($1) s
  where s.semaine is not null
  group by s.semaine
  order by s.semaine
$$;

-- Numéros internes déjà attribués, pour la publication (clé secrète seulement) : la publication relie ses lignes
-- par ces numéros sans les recalculer.
create or replace function correspondances()
returns jsonb
language sql stable
as $$
  select jsonb_build_object(
    'sources', (select coalesce(jsonb_object_agg(nom, id), '{}') from public.sources),
    'comptes', (select coalesce(jsonb_object_agg(source || '|' || nom, id), '{}') from public.comptes),
    'publications', (select coalesce(jsonb_object_agg(compte || '|' || code, id), '{}') from public.publications),
    'utilisateurs', (select coalesce(jsonb_object_agg(source || '|' || identifiant, id), '{}')
                     from public.utilisateurs))
$$;

-- ── Réponses préparées pour les modérateurs (2026-11-19, moderation/reponses.py) ───────────────────────────────
-- Thèmes de la réponse (ceux de l'analyse, T1…, et ceux qu'ajoutent les modérateurs, M-…) et réponses toutes faites,
-- plusieurs par objection, dans des styles différents. Le fichier donnees/moderation/reponses.xlsx et ces tables se
-- synchronisent dans les deux sens (« python -m moderation reponses ») : ce qu'un modérateur écrit sur le site est
-- gardé. Le site lit, ajoute et modifie (compte des modérateurs seulement), sans jamais supprimer : une réponse
-- retirée passe à actif = false. Les thèmes de chaque commentaire sont dans moderation.themes (plus haut).
create table if not exists reponses_themes (
  id          text primary key,
  nom         text not null,
  famille     text,
  definition  text,
  actif       boolean not null default true,
  par         text,                      -- « Claude », « analyse », ou le prénom du modérateur
  maj         timestamptz not null default clock_timestamp()
);
create table if not exists reponses (
  id          text primary key,
  theme       text not null references reponses_themes (id) on update cascade,
  objection   text not null,             -- ce à quoi elle répond (« C'est un Macron bis »)
  style       text not null,             -- chiffres, arguments, courte, bienveillante, punchline…
  titre       text not null,
  texte       text not null,
  gif         text,                      -- mot à chercher dans les GIF de Facebook (réponses humoristiques)
  sources     text,                      -- d'où viennent les chiffres, pour vérifier avant de publier
  ordre       integer not null default 0,
  actif       boolean not null default true,
  par         text,
  maj         timestamptz not null default clock_timestamp()
);
create index if not exists reponses_theme on reponses (theme);
create or replace function public.reponses_dater()
returns trigger language plpgsql as $$
begin
  new.maj := clock_timestamp();
  return new;
end $$;
drop trigger if exists dater on reponses_themes;
create trigger dater before update on reponses_themes for each row execute function public.reponses_dater();
drop trigger if exists dater on reponses;
create trigger dater before update on reponses for each row execute function public.reponses_dater();
alter table reponses_themes enable row level security;
alter table reponses enable row level security;
drop policy if exists moderateurs on reponses_themes;
drop policy if exists moderateurs on reponses;
create policy moderateurs on reponses_themes for all to authenticated
  using ((select public.est_moderateur())) with check ((select public.est_moderateur()));
create policy moderateurs on reponses for all to authenticated
  using ((select public.est_moderateur())) with check ((select public.est_moderateur()));
revoke all on reponses_themes, reponses from anon;
revoke delete, truncate on reponses_themes, reponses from authenticated;
grant select, insert, update on reponses_themes, reponses to authenticated;

revoke execute on function selection(jsonb), evolution(jsonb), commentaire(text) from public, anon;
grant execute on function selection(jsonb), evolution(jsonb), commentaire(text) to authenticated;
revoke execute on function correspondances() from public, anon, authenticated;
grant execute on function correspondances() to service_role;

notify pgrst, 'reload schema';
notify pgrst, 'reload config';
