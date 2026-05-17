-- Supabase SQL 에디터에서 실행하세요

create table if not exists companies (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  product_info  text not null default '',
  brand_direction text not null default '',
  target        text not null default '',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table if not exists references (
  id          uuid primary key default gen_random_uuid(),
  company_id  uuid references companies(id) on delete set null,
  title       text not null,
  content     text not null,
  source      text not null default 'upload', -- 'upload' | 'extracted' | 'generated'
  created_at  timestamptz not null default now()
);

-- updated_at 자동 갱신 트리거
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists companies_updated_at on companies;
create trigger companies_updated_at
  before update on companies
  for each row execute function update_updated_at();

-- RLS 비활성화 (팀 내부 도구용 — 필요 시 활성화)
alter table companies disable row level security;
alter table references disable row level security;
