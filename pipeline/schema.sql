-- ============================================================
-- JEE PYQ Question Bank — Supabase / Postgres schema
-- Content is stored as LaTeX-in-Markdown strings, NOT as docx/md files.
-- ============================================================

create extension if not exists "pgcrypto";
create extension if not exists vector;      -- for semantic search / dedup later

-- ---------- taxonomy ----------

create table subjects (
  id          smallserial primary key,
  name        text not null unique          -- 'Physics'
);

create table units (
  id          smallserial primary key,
  subject_id  smallint not null references subjects(id),
  name        text not null,                -- 'Mechanics 1'
  sort_order  smallint not null
);

create table chapters (
  id          smallserial primary key,
  unit_id     smallint not null references units(id),
  chapter_no  smallint not null,            -- 1..32, matches the answer key
  name        text not null,                -- 'Rotational Motion'
  -- ground truth from the book's own answer key; used to validate ingestion
  expected_question_count smallint,
  unique (chapter_no)
);

create table topics (
  id          serial primary key,
  chapter_id  smallint not null references chapters(id),
  name        text not null,                -- 'Fundamentals of Vectors'
  sort_order  smallint,
  unique (chapter_id, name)
);

-- ---------- questions ----------

create type question_tier as enum ('concept_builder', 'must_do', 'advanced');
create type question_format as enum ('mcq', 'numerical', 'match_list', 'assertion_reason', 'statement');
create type exam_shift as enum ('morning', 'evening');

create table questions (
  id              uuid primary key default gen_random_uuid(),
  chapter_id      smallint not null references chapters(id),
  topic_id        int references topics(id),

  -- Q-number within the chapter. This is the join key to the answer key.
  q_no            smallint not null,
  tier            question_tier not null,
  format          question_format not null,

  -- Body as Markdown with inline LaTeX ($...$ / $$...$$).
  -- Figures referenced inline as [[fig:p008_x192]] placeholders.
  body            text not null,

  -- answer: exactly one of these is populated
  correct_option  smallint check (correct_option between 1 and 4),
  numerical_answer text,

  -- provenance / filtering
  exam_date       date,                     -- 27 Aug 2021
  exam_shift      exam_shift,               -- (M) / (E)
  exam_year       smallint generated always as (extract(year from exam_date)::smallint) stored,

  out_of_syllabus boolean not null default false,  -- the '*' marker
  good_to_solve   boolean not null default false,  -- the '^' marker

  -- traceability back to the PDF, so you can always re-verify
  source_page     smallint not null,
  source_bbox     jsonb,

  -- QA
  extraction_confidence real,               -- from the VLM pass
  review_status   text not null default 'unreviewed',   -- unreviewed|auto_ok|flagged|human_ok

  embedding       vector(768),              -- optional: semantic search / duplicate detection
  created_at      timestamptz not null default now(),

  unique (chapter_id, q_no)
);

create index on questions (chapter_id, tier);
create index on questions (exam_year, exam_shift);
create index on questions (topic_id);
create index on questions (review_status) where review_status <> 'human_ok';

-- ---------- options ----------
-- Separate table because options can themselves be images
-- (e.g. Match-the-List questions where List II items are diagrams).

create table question_options (
  id            uuid primary key default gen_random_uuid(),
  question_id   uuid not null references questions(id) on delete cascade,
  option_index  smallint not null check (option_index between 1 and 4),
  body          text,                       -- LaTeX/Markdown, may be null if pure image
  unique (question_id, option_index)
);

-- ---------- figures ----------

create type figure_role as enum ('question_body', 'option', 'match_list_item');

create table figures (
  id            uuid primary key default gen_random_uuid(),
  figure_key    text not null unique,       -- 'p008_x192' — stable, from the PDF xref
  storage_path  text not null,              -- 'pyq/physics/figures/p008_x192.png'
  public_url    text,
  px_width      int,
  px_height     int,
  bytes         int,
  checksum      text,                       -- sha256, for dedup across books
  source_page   smallint not null,
  source_bbox   jsonb not null,
  alt_text      text                        -- VLM-generated, for accessibility + search
);

-- A figure attaches to a question OR to a specific option.
create table figure_links (
  figure_id     uuid not null references figures(id) on delete cascade,
  question_id   uuid not null references questions(id) on delete cascade,
  option_id     uuid references question_options(id) on delete cascade,
  role          figure_role not null,
  sort_order    smallint default 0,
  primary key (figure_id, question_id, coalesce(option_id, '00000000-0000-0000-0000-000000000000'::uuid))
);

-- ---------- ingestion audit ----------

create table ingestion_runs (
  id            uuid primary key default gen_random_uuid(),
  source_file   text not null,
  model_used    text,
  pages_processed int,
  questions_written int,
  figures_written int,
  cost_usd      numeric(10,4),
  started_at    timestamptz default now(),
  finished_at   timestamptz,
  notes         jsonb
);

-- ---------- validation view ----------
-- Compare what you ingested against the book's own answer key.
-- Any row where actual <> expected means the parse dropped or duplicated questions.

create view v_ingestion_check as
select
  c.chapter_no,
  c.name,
  c.expected_question_count as expected,
  count(q.id)               as actual,
  count(q.id) filter (where q.correct_option is null
                        and q.numerical_answer is null) as missing_answer,
  count(q.id) filter (where q.review_status = 'flagged') as flagged,
  c.expected_question_count - count(q.id) as delta
from chapters c
left join questions q on q.chapter_id = c.id
group by c.id, c.chapter_no, c.name, c.expected_question_count
order by c.chapter_no;
