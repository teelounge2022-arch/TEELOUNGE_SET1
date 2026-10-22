-- TEE LOUNGE AI 업무실 · 재고 지도 테이블
-- Supabase 대시보드 > SQL Editor 에 붙여넣고 한 번 실행하세요. 여러 번 실행해도 괜찮아요.

create table if not exists public.stock_items (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 80),
  color text not null default '',
  size text not null default '',
  qty integer not null default 0 check (qty >= 0),
  unit text not null,                       -- 선반 코드 (예: 3-B)
  level integer not null default 1 check (level >= 1),  -- 단 (1 = 맨 아래)
  note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.stock_items enable row level security;

-- 주의: 아래 정책은 사이트 주소를 아는 사람 누구나 재고를 보고 고칠 수 있게 해요.
-- 로그인을 붙이면 "to anon, authenticated" 를 "to authenticated" 로 바꾸세요.
drop policy if exists "stock_items read" on public.stock_items;
drop policy if exists "stock_items insert" on public.stock_items;
drop policy if exists "stock_items update" on public.stock_items;
drop policy if exists "stock_items delete" on public.stock_items;
create policy "stock_items read" on public.stock_items for select to anon, authenticated using (true);
create policy "stock_items insert" on public.stock_items for insert to anon, authenticated with check (true);
create policy "stock_items update" on public.stock_items for update to anon, authenticated using (true) with check (true);
create policy "stock_items delete" on public.stock_items for delete to anon, authenticated using (true);

-- 다른 사람이 고친 재고가 바로 보이게 Realtime 에 등록해요
do $$
begin
  alter publication supabase_realtime add table public.stock_items;
exception when duplicate_object then null;
end $$;
