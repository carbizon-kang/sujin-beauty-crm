-- =============================================
-- 수진뷰티 CRM - Supabase 테이블 생성 SQL
-- Supabase → SQL Editor 에 붙여넣고 Run 하세요
-- =============================================

-- 1. 고객 테이블
create table if not exists customers (
  id            bigserial primary key,
  customer_id   text unique not null,
  name          text not null,
  phone         text default '',
  gender        text default '',
  age_group     text default '',
  registered_at text default '',
  memo          text default ''
);

-- 2. 시술이력 테이블
create table if not exists treatments (
  id              bigserial primary key,
  treatment_id    text unique not null,
  customer_id     text not null,
  customer_name   text default '',
  visit_date      text default '',
  treatment_type  text default '',
  product_used    text default '',
  price           integer default 0,
  memo            text default ''
);

-- 3. 시술종류 테이블
create table if not exists treatment_types (
  id         serial primary key,
  type_name  text unique not null,
  sort_order integer default 0
);

-- 4. 기본 시술종류 삽입
insert into treatment_types (type_name, sort_order) values
  ('커트', 1), ('펌', 2), ('염색', 3), ('탈색', 4),
  ('클리닉 트리트먼트', 5), ('두피 관리', 6),
  ('피부 관리 (기본)', 7), ('피부 관리 (스페셜)', 8),
  ('제모', 9), ('눈썹 정리', 10), ('기타', 11)
on conflict (type_name) do nothing;

-- 5. RLS 비활성화 (개인 매장 전용 앱)
alter table customers      disable row level security;
alter table treatments     disable row level security;
alter table treatment_types disable row level security;
