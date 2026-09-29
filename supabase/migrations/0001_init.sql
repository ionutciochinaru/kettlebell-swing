-- Workout sessions: one row per completed session, payload is the app's SessionLog.
create table public.sessions (
  id text not null,
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  started_at timestamptz not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  primary key (user_id, id)
);
create index sessions_user_started on public.sessions (user_id, started_at desc);

-- Settings, owned bells, progression and custom workouts (last write wins).
create table public.user_state (
  user_id uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.sessions enable row level security;
alter table public.user_state enable row level security;

create policy "Own sessions" on public.sessions
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy "Own state" on public.user_state
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
