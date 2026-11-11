-- Base Supabase du site. Rejouable sans risque : « python -m web installer » l'exécute à chaque fois.
-- Le public (rôle anon) ne peut que lire ; seul « python -m web publier » écrit, avec la clé secrète.

create extension if not exists unaccent with schema extensions;

-- Recherche en français sans tenir compte des accents ni des terminaisons (« énergie » trouve « energies »).
do $$ begin
  if not exists (select 1 from pg_ts_config where cfgname = 'fr') then
    create text search configuration public.fr (copy = pg_catalog.french);
    alter text search configuration public.fr
      alter mapping for hword, hword_part, word with extensions.unaccent, french_stem;
  end if;
end $$;

create table if not exists publications (
  id      text primary key,          -- « youtube:<id vidéo> », « instagram:<code du post> », « bluesky:<did/rkey de la tête du fil> »
  source  text not null,
  code    text not null,
  compte  text,
  titre   text,
  lien    text,
  date    timestamp
);

create table if not exists commentaires (
  cle         text primary key,      -- « youtube:<id commentaire> », « instagram:<id commentaire> », « bluesky:<did/rkey> »
  source      text not null,
  compte      text not null,
  groupe      text not null,         -- officiel, media, commentateur, soutien, autre (recherche YouTube, Bluesky)
  publication text references publications (id),
  date        timestamp,
  semaine     date,                  -- lundi de la semaine
  reponse     boolean not null,
  parent      text,                  -- clé du commentaire auquel il répond
  likes       integer not null default 0,
  texte       text not null,
  tonalite    smallint not null,
  forme       smallint not null,
  systeme     smallint not null,
  idees       smallint not null,
  pertinence  smallint not null,
  cible       char(1) not null,      -- L : parle de Lisnard ; A : d'autre chose
  fiabilite   text,
  recherche   tsvector generated always as (to_tsvector('public.fr'::regconfig, texte)) stored
);

-- Taille en mots, calculée par la base (filtre « Taille » et tri « Plus longs » de la page Commentaires).
alter table commentaires add column if not exists mots integer
  generated always as (coalesce(array_length(regexp_split_to_array(btrim(texte), '\s+'), 1), 0)) stored;

create index if not exists commentaires_date on commentaires (date desc nulls last);
create index if not exists commentaires_semaine on commentaires (semaine);
-- Toutes les colonnes des filtres sauf le texte : evolution() et les comptages se lisent dans ces ~10 Mo
-- au lieu des 64 Mo de la table (sinon, cache froid, on dépasse le délai du public).
create index if not exists commentaires_resume on commentaires (semaine) include
  (source, groupe, compte, fiabilite, reponse, cible, tonalite, forme, systeme, idees, pertinence);
create index if not exists commentaires_pertinence on commentaires (pertinence desc);
create index if not exists commentaires_likes on commentaires (likes desc);
create index if not exists commentaires_mots on commentaires (mots desc);
create index if not exists commentaires_publication on commentaires (publication);
create index if not exists commentaires_parent on commentaires (parent);
create index if not exists commentaires_recherche on commentaires using gin (recherche);

-- Données calculées en bloc : « meta » (chiffres du projet) et « cube » (page Statistiques).
create table if not exists syntheses (
  nom     text primary key,
  donnees jsonb not null,
  maj     timestamptz not null default now()
);

alter table publications enable row level security;
alter table commentaires enable row level security;
alter table syntheses enable row level security;
drop policy if exists lecture on publications;
drop policy if exists lecture on commentaires;
drop policy if exists lecture on syntheses;
create policy lecture on publications for select to anon, authenticated using (true);
create policy lecture on commentaires for select to anon, authenticated using (true);
create policy lecture on syntheses for select to anon, authenticated using (true);
revoke insert, update, delete, truncate on publications, commentaires, syntheses from anon, authenticated;
grant select on publications, commentaires, syntheses to anon, authenticated;
alter role anon set statement_timeout = '8s';  -- 3 s par défaut : trop court quand la base sort de veille

-- La sélection de la page Commentaires, définie une seule fois. Le filtre f (jsonb) peut contenir :
--   du, au (lundis, AAAA-MM-JJ ; du absent = depuis le début), sources, groupes, comptes (listes),
--   reponse (true/false), cible ('L'/'A'), fiabilites (liste), q (mots cherchés),
--   tonalite, forme, systeme, idees, pertinence ([min, max] de 0 à 20), mots_min (taille minimale en mots).
-- Fonction SQL simple et stable, sans « set search_path » (qui empêcherait PostgreSQL de l'intégrer à la requête,
-- donc d'utiliser les index) : les noms sont écrits en entier.
create or replace function selection(f jsonb default '{}'::jsonb)
returns setof commentaires
language sql stable
as $$
  select c.* from public.commentaires c
  where (f->>'du' is null or c.semaine >= (f->>'du')::date)
    and (f->>'au' is null or c.semaine <= (f->>'au')::date)
    and (f->'sources' is null or f->'sources' ? c.source)
    and (f->'groupes' is null or f->'groupes' ? c.groupe)
    and (f->'comptes' is null or f->'comptes' ? c.compte)
    and (f->'fiabilites' is null or f->'fiabilites' ? c.fiabilite)
    and (f->>'reponse' is null or c.reponse = (f->>'reponse')::boolean)
    and (f->>'cible' is null or c.cible = f->>'cible')
    and c.tonalite between coalesce((f->'tonalite'->>0)::int, 0) and coalesce((f->'tonalite'->>1)::int, 20)
    and c.forme between coalesce((f->'forme'->>0)::int, 0) and coalesce((f->'forme'->>1)::int, 20)
    and c.systeme between coalesce((f->'systeme'->>0)::int, 0) and coalesce((f->'systeme'->>1)::int, 20)
    and c.idees between coalesce((f->'idees'->>0)::int, 0) and coalesce((f->'idees'->>1)::int, 20)
    and c.pertinence between coalesce((f->'pertinence'->>0)::int, 0) and coalesce((f->'pertinence'->>1)::int, 20)
    and (f->>'mots_min' is null or c.mots >= (f->>'mots_min')::int)
    and (coalesce(f->>'q', '') = '' or c.recherche @@ websearch_to_tsquery('public.fr'::regconfig, f->>'q'))
$$;

-- Évolution de la sélection, semaine par semaine : nombre, moyennes, parts de critiques et d'éloges.
create or replace function evolution(f jsonb default '{}'::jsonb)
returns table (semaine date, n bigint, tonalite numeric, forme numeric, systeme numeric, idees numeric,
               pertinence numeric, bas_tonalite bigint, haut_tonalite bigint)
language sql stable
as $$
  select s.semaine, count(*), round(avg(s.tonalite), 2), round(avg(s.forme), 2), round(avg(s.systeme), 2),
         round(avg(s.idees), 2), round(avg(s.pertinence), 2),
         count(*) filter (where s.tonalite <= 6), count(*) filter (where s.tonalite >= 14)
  from public.selection(f) s
  where s.semaine is not null
  group by s.semaine
  order by s.semaine
$$;

grant execute on function selection(jsonb), evolution(jsonb) to anon, authenticated;

notify pgrst, 'reload schema';
notify pgrst, 'reload config';
