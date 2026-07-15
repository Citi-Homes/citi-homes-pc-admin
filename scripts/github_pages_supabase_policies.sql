-- Citi Homes Administration Portal - secure GitHub Pages access rules
-- Run this in Supabase SQL Editor for project xcddssirxwhywvhspica.
--
-- Before running:
-- 1. Create the admin login user in Supabase Authentication > Users.
-- 2. Replace umer@citihomes.ae below if you want a different admin email.

create table if not exists public.admin_portal_users (
    auth_user_id uuid primary key references auth.users(id) on delete cascade,
    email text unique not null,
    role text not null default 'Admin',
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

alter table public.admin_portal_users enable row level security;

grant usage on schema public to authenticated;
grant select on table public.admin_portal_users to authenticated;

drop policy if exists "admin_portal_users_self_read" on public.admin_portal_users;
create policy "admin_portal_users_self_read" on public.admin_portal_users
for select to authenticated
using (auth_user_id = auth.uid() and is_active = true);

insert into public.admin_portal_users (auth_user_id, email, role, is_active)
select id, email, 'Super User', true
from auth.users
where lower(email) = lower('umer@citihomes.ae')
on conflict (auth_user_id)
do update set email = excluded.email, role = 'Super User', is_active = true;

insert into public.admin_portal_users (auth_user_id, email, role, is_active)
select id, email, 'Viewer', true
from auth.users
where lower(email) = lower('test@citihomes.ae')
on conflict (auth_user_id)
do update set email = excluded.email, role = 'Viewer', is_active = true;

grant select, insert, update, delete on table public.employees to authenticated;
grant select, insert, update, delete on table public.recruitment to authenticated;
grant select, insert, update, delete on table public.interview_evaluation to authenticated;
grant select, insert, update, delete on table public.joining_checklist to authenticated;
grant select, insert, update, delete on table public.attendance to authenticated;
grant select, insert, update, delete on table public.leave_management to authenticated;
grant select, insert, update, delete on table public.documents to authenticated;
grant select, insert, update, delete on table public.pantry to authenticated;
grant select, insert, update, delete on table public.utilities to authenticated;
grant select, insert, update, delete on table public.inventory to authenticated;
grant select, insert, update, delete on table public.vendors to authenticated;
grant select, insert, update, delete on table public.tasks to authenticated;
grant usage, select on all sequences in schema public to authenticated;

alter table public.employees enable row level security;
alter table public.recruitment enable row level security;
alter table public.interview_evaluation enable row level security;
alter table public.joining_checklist enable row level security;
alter table public.attendance enable row level security;
alter table public.leave_management enable row level security;
alter table public.documents enable row level security;
alter table public.pantry enable row level security;
alter table public.utilities enable row level security;
alter table public.inventory enable row level security;
alter table public.vendors enable row level security;
alter table public.tasks enable row level security;

drop policy if exists "admin_portal_allowed_users" on public.employees;
create policy "admin_portal_allowed_users" on public.employees
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.recruitment;
create policy "admin_portal_allowed_users" on public.recruitment
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.interview_evaluation;
create policy "admin_portal_allowed_users" on public.interview_evaluation
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.joining_checklist;
create policy "admin_portal_allowed_users" on public.joining_checklist
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.attendance;
create policy "admin_portal_allowed_users" on public.attendance
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.leave_management;
create policy "admin_portal_allowed_users" on public.leave_management
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.documents;
create policy "admin_portal_allowed_users" on public.documents
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.pantry;
create policy "admin_portal_allowed_users" on public.pantry
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.utilities;
create policy "admin_portal_allowed_users" on public.utilities
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.inventory;
create policy "admin_portal_allowed_users" on public.inventory
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.vendors;
create policy "admin_portal_allowed_users" on public.vendors
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

drop policy if exists "admin_portal_allowed_users" on public.tasks;
create policy "admin_portal_allowed_users" on public.tasks
for all to authenticated
using (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true))
with check (exists (select 1 from public.admin_portal_users u where u.auth_user_id = auth.uid() and u.is_active = true));

create or replace function public.admin_portal_has_role(allowed_roles text[])
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.admin_portal_users u
    where u.auth_user_id = auth.uid()
      and u.is_active = true
      and u.role = any(allowed_roles)
  );
$$;

grant execute on function public.admin_portal_has_role(text[]) to authenticated;

do $$
declare
  portal_table text;
  portal_tables text[] := array[
    'employees',
    'recruitment',
    'interview_evaluation',
    'joining_checklist',
    'attendance',
    'leave_management',
    'documents',
    'pantry',
    'utilities',
    'inventory',
    'vendors',
    'tasks'
  ];
begin
  foreach portal_table in array portal_tables loop
    execute format('drop policy if exists "admin_portal_allowed_users" on public.%I', portal_table);
    execute format('drop policy if exists "admin_portal_read" on public.%I', portal_table);
    execute format('drop policy if exists "admin_portal_insert" on public.%I', portal_table);
    execute format('drop policy if exists "admin_portal_update" on public.%I', portal_table);
    execute format('drop policy if exists "admin_portal_delete" on public.%I', portal_table);

    execute format(
      'create policy "admin_portal_read" on public.%I for select to authenticated using (public.admin_portal_has_role(array[''Viewer'', ''Admin'', ''Super User'']))',
      portal_table
    );

    execute format(
      'create policy "admin_portal_insert" on public.%I for insert to authenticated with check (public.admin_portal_has_role(array[''Admin'', ''Super User'']))',
      portal_table
    );

    execute format(
      'create policy "admin_portal_update" on public.%I for update to authenticated using (public.admin_portal_has_role(array[''Admin'', ''Super User''])) with check (public.admin_portal_has_role(array[''Admin'', ''Super User'']))',
      portal_table
    );

    execute format(
      'create policy "admin_portal_delete" on public.%I for delete to authenticated using (public.admin_portal_has_role(array[''Admin'', ''Super User'']))',
      portal_table
    );
  end loop;
end $$;
