-- MuseBridge production schema.
-- Applied to Supabase project yvrwrgbokvzcmjjatqfx (MuseBridge).

create table if not exists public.bridges (
  id uuid primary key default gen_random_uuid(),
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.bridge_members (
  bridge_id uuid not null references public.bridges(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner','partner')),
  created_at timestamptz not null default now(),
  primary key (bridge_id, user_id)
);

create table if not exists public.consents (
  id uuid primary key default gen_random_uuid(),
  bridge_id uuid not null references public.bridges(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  scope text not null,
  active boolean not null default true,
  updated_at timestamptz not null default now(),
  unique (bridge_id, owner_id, scope)
);

create table if not exists public.bridge_messages (
  id uuid primary key default gen_random_uuid(),
  bridge_id uuid not null references public.bridges(id) on delete cascade,
  sender_id uuid not null references auth.users(id) on delete cascade,
  recipient_id uuid not null references auth.users(id) on delete cascade,
  body text not null check (length(body) between 1 and 10000),
  scope text not null,
  status text not null default 'draft' check (status in ('draft','approved','delivered','rejected')),
  approved_at timestamptz,
  delivered_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.bridge_agreements (
  id uuid primary key default gen_random_uuid(),
  bridge_id uuid not null references public.bridges(id) on delete cascade,
  text text not null check (length(text) between 1 and 10000),
  status text not null default 'pending' check (status in ('pending','approved','rejected','cancelled')),
  created_at timestamptz not null default now()
);

create table if not exists public.agreement_approvals (
  agreement_id uuid not null references public.bridge_agreements(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  approved_at timestamptz not null default now(),
  primary key (agreement_id, user_id)
);

create table if not exists public.bridge_audit (
  id bigint generated always as identity primary key,
  bridge_id uuid not null references public.bridges(id) on delete cascade,
  actor_id uuid references auth.users(id) on delete set null,
  action text not null,
  target_id uuid,
  created_at timestamptz not null default now()
);

alter table public.bridges enable row level security;
alter table public.bridge_members enable row level security;
alter table public.consents enable row level security;
alter table public.bridge_messages enable row level security;
alter table public.bridge_agreements enable row level security;
alter table public.agreement_approvals enable row level security;
alter table public.bridge_audit enable row level security;

create or replace function public.is_bridge_member(target_bridge uuid)
returns boolean language sql stable security invoker set search_path = public
as $$ select exists (select 1 from public.bridge_members where bridge_id = target_bridge and user_id = (select auth.uid())); $$;

-- PostgreSQL does not support CREATE POLICY IF NOT EXISTS. Drop/recreate keeps
-- this migration rerunnable while preserving explicit policy definitions.
drop policy if exists bridge_members_self_read on public.bridge_members;
create policy bridge_members_self_read on public.bridge_members for select to authenticated
  using (user_id = (select auth.uid()));
drop policy if exists bridges_member_read on public.bridges;
create policy bridges_member_read on public.bridges for select to authenticated
  using (public.is_bridge_member(id));
drop policy if exists consents_owner_manage on public.consents;
create policy consents_owner_manage on public.consents for all to authenticated
  using (public.is_bridge_member(bridge_id) and owner_id = (select auth.uid()))
  with check (public.is_bridge_member(bridge_id) and owner_id = (select auth.uid()));
drop policy if exists messages_member_read on public.bridge_messages;
create policy messages_member_read on public.bridge_messages for select to authenticated
  using (public.is_bridge_member(bridge_id));
drop policy if exists messages_sender_insert on public.bridge_messages;
create policy messages_sender_insert on public.bridge_messages for insert to authenticated
  with check (public.is_bridge_member(bridge_id) and sender_id = (select auth.uid()));
drop policy if exists messages_sender_update on public.bridge_messages;
create policy messages_sender_update on public.bridge_messages for update to authenticated
  using (sender_id = (select auth.uid())) with check (sender_id = (select auth.uid()));
drop policy if exists agreements_member_read on public.bridge_agreements;
create policy agreements_member_read on public.bridge_agreements for select to authenticated
  using (public.is_bridge_member(bridge_id));
drop policy if exists agreements_member_create on public.bridge_agreements;
create policy agreements_member_create on public.bridge_agreements for insert to authenticated
  with check (public.is_bridge_member(bridge_id));
drop policy if exists approvals_member_read on public.agreement_approvals;
create policy approvals_member_read on public.agreement_approvals for select to authenticated
  using (exists (select 1 from public.bridge_agreements a where a.id = agreement_id and public.is_bridge_member(a.bridge_id)));
drop policy if exists approvals_own_insert on public.agreement_approvals;
create policy approvals_own_insert on public.agreement_approvals for insert to authenticated
  with check ((select auth.uid()) = user_id and exists (select 1 from public.bridge_agreements a where a.id = agreement_id and public.is_bridge_member(a.bridge_id)));
drop policy if exists audit_member_read on public.bridge_audit;
create policy audit_member_read on public.bridge_audit for select to authenticated
  using (public.is_bridge_member(bridge_id));
