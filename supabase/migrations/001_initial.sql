-- ============================================================
-- Zoiou — Migration inicial
-- ============================================================

-- Usuários (espelho da tabela auth.users do Supabase)
create table if not exists usuarios (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  telegram_id text,
  whatsapp text,
  notif_telegram boolean default false,
  notif_whatsapp boolean default false,
  notif_email boolean default true,
  criado_em timestamptz default now()
);

-- Produtos monitorados
create table if not exists produtos (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  url text not null,
  loja text,
  imagem text,
  criado_em timestamptz default now()
);

-- Lista de desejos do usuário
create table if not exists lista_desejos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references usuarios(id) on delete cascade,
  produto_id uuid not null references produtos(id) on delete cascade,
  ativo boolean default true,
  criado_em timestamptz default now(),
  unique(usuario_id, produto_id)
);

-- Histórico de preços
create table if not exists historico_precos (
  id uuid primary key default gen_random_uuid(),
  produto_id uuid not null references produtos(id) on delete cascade,
  preco numeric(10, 2) not null,
  capturado_em timestamptz default now()
);

-- ============================================================
-- Índices
-- ============================================================

create index if not exists idx_historico_produto_data
  on historico_precos(produto_id, capturado_em desc);

create index if not exists idx_lista_ativo
  on lista_desejos(ativo) where ativo = true;

-- ============================================================
-- Row Level Security
-- ============================================================

alter table usuarios enable row level security;
alter table produtos enable row level security;
alter table lista_desejos enable row level security;
alter table historico_precos enable row level security;

-- Usuários só leem e editam o próprio perfil
create policy "usuario_ve_proprio_perfil"
  on usuarios for select
  using (auth.uid() = id);

create policy "usuario_atualiza_proprio_perfil"
  on usuarios for update
  using (auth.uid() = id);

create policy "usuario_insere_proprio_perfil"
  on usuarios for insert
  with check (auth.uid() = id);

-- Lista de desejos: usuário só acessa a própria lista
create policy "usuario_ve_propria_lista"
  on lista_desejos for select
  using (auth.uid() = usuario_id);

create policy "usuario_insere_propria_lista"
  on lista_desejos for insert
  with check (auth.uid() = usuario_id);

create policy "usuario_atualiza_propria_lista"
  on lista_desejos for update
  using (auth.uid() = usuario_id);

create policy "usuario_deleta_propria_lista"
  on lista_desejos for delete
  using (auth.uid() = usuario_id);

-- Produtos: leitura pública, escrita apenas pelo service role
create policy "qualquer_um_ve_produtos"
  on produtos for select
  using (true);

-- Histórico: usuário só vê histórico de produtos da sua lista
create policy "usuario_ve_historico_da_sua_lista"
  on historico_precos for select
  using (
    exists (
      select 1 from lista_desejos ld
      where ld.produto_id = historico_precos.produto_id
        and ld.usuario_id = auth.uid()
    )
  );

-- ============================================================
-- Trigger: criar perfil de usuário automaticamente no signup
-- ============================================================

create or replace function criar_usuario_no_signup()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.usuarios (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute function criar_usuario_no_signup();

-- ============================================================
-- Limpeza automática: histórico com mais de 365 dias
-- ============================================================

create or replace function limpar_historico_antigo()
returns void
language plpgsql
as $$
begin
  delete from historico_precos
  where capturado_em < now() - interval '365 days';
end;
$$;
