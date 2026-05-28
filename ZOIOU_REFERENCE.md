# ZOIOU — Documento de Referência do Projeto

> Este documento é a fonte única de verdade para o desenvolvimento do Zoiou.
> Toda IA, desenvolvedor ou colaborador deve seguir estas instruções à risca.

---

## 1. Visão Geral do Produto

**Zoiou** é um monitor de preços pessoal. O usuário cadastra a URL de um produto em qualquer loja online, e o sistema monitora o preço diariamente, notificando quando há variação.

- **Tipo:** SaaS gratuito (v1)
- **Domínio:** zoiou.com.br
- **Repositório:** github.com/mauriciofeoli/zoiou-monitor
- **Linguagem principal:** Python (backend) + Next.js (frontend)
- **Banco de dados:** Supabase (PostgreSQL + Auth)
- **Deploy:** Railway (backend) + Vercel (frontend)

---

## 2. Stack Técnica

### Backend
| Tecnologia | Versão mínima | Uso |
|---|---|---|
| Python | 3.12+ | Linguagem principal |
| FastAPI | 0.111+ | API REST |
| curl_cffi | 0.7+ | Scraping primário (rápido, sem JS) |
| Playwright | 1.44+ | Scraping fallback (sites com JS) |
| BeautifulSoup4 | 4.12+ | Extração de HTML |
| APScheduler | 3.10+ | Agendamento de tarefas |
| python-telegram-bot | 21+ | Notificações Telegram |
| Resend | 2+ | Notificações por e-mail |
| supabase-py | 2+ | Conexão com banco |
| pydantic | 2+ | Validação de dados |
| python-dotenv | 1+ | Variáveis de ambiente |

### Frontend
| Tecnologia | Versão mínima | Uso |
|---|---|---|
| Next.js | 15+ | Framework web (App Router) |
| React | 19+ | UI |
| TypeScript | 5+ | Tipagem |
| Tailwind CSS | 4+ | Estilização |
| @radix-ui/* | latest | Componentes primitivos de UI |
| @tanstack/react-query | 5+ | Cache e sincronização de dados |
| next-themes | 0.4+ | Dark mode (sistema/claro/escuro) |
| react-hook-form + zod | latest | Formulários com validação |
| Recharts | 2+ | Gráficos de histórico |
| sonner | 2+ | Toasts de notificação |
| @supabase/supabase-js | 2+ | Auth no cliente |

### Infraestrutura
| Serviço | Uso |
|---|---|
| Supabase | PostgreSQL + Auth (JWT) |
| Railway | Deploy do backend Python |
| Vercel | Deploy do frontend Next.js |

---

## 3. Estrutura de Pastas

```
zoiou/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # obter_usuario_autenticado, obter_cliente_rls
│   │   │   └── routes/
│   │   │       ├── produtos.py      # CRUD da lista de desejos + scraping
│   │   │       ├── historico.py     # histórico de preços
│   │   │       └── usuarios.py      # perfil e preferências
│   │   ├── core/
│   │   │   ├── config.py            # configurações e env vars (pydantic-settings)
│   │   │   ├── database.py          # conexão Supabase (service key)
│   │   │   ├── limiter.py           # rate limiting via Starlette middleware
│   │   │   └── security.py          # validação JWT + bearer scheme
│   │   ├── schemas/
│   │   │   ├── produto.py           # ProdutoCreate (+ SSRF validator), ProdutoPatch, ProdutoResponse
│   │   │   ├── historico.py         # HistoricoResponse, PontoHistorico
│   │   │   └── usuario.py           # UsuarioResponse, PreferenciasUpdate (+ Telegram validator)
│   │   ├── services/
│   │   │   ├── scraper.py           # extrair_preco, extrair_produto_completo, extrair_metadados_produto
│   │   │   ├── historico.py         # buscar_ultimo_preco, buscar_ultimos_precos, registrar_preco
│   │   │   ├── notificacao.py       # despacho de notificações (Telegram + e-mail)
│   │   │   ├── telegram.py          # integração Telegram Bot API
│   │   │   └── email.py             # integração Resend (com escape HTML)
│   │   ├── scheduler/
│   │   │   └── jobs.py              # monitorar_todos_produtos (03:00 BRT) + _limpar_historico (dom 04:00)
│   │   └── main.py                  # entry point FastAPI
│   ├── tests/
│   │   ├── test_scraper.py
│   │   ├── test_historico.py
│   │   └── test_notificacao.py
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # RootLayout com suppressHydrationWarning
│   │   │   ├── providers.tsx        # ThemeProvider + QueryClientProvider + AuthProvider
│   │   │   ├── globals.css          # variáveis CSS (light + dark) em oklch
│   │   │   ├── page.tsx             # dashboard principal (lista de desejos)
│   │   │   ├── login/
│   │   │   │   └── page.tsx         # login com Supabase Auth
│   │   │   ├── produtos/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx     # detalhe do produto + gráfico de histórico
│   │   │   └── configuracoes/
│   │   │       └── page.tsx         # preferências de notificação
│   │   ├── components/
│   │   │   ├── ui/                  # componentes Radix UI (shadcn pattern)
│   │   │   ├── Header.tsx           # nav + dark mode toggle (Moon/Sun)
│   │   │   ├── CardProduto.tsx
│   │   │   ├── GraficoHistorico.tsx
│   │   │   ├── BadgePrecoHistorico.tsx
│   │   │   └── AdicionarProdutoModal.tsx
│   │   ├── hooks/
│   │   │   └── use-auth.tsx         # AuthProvider + useAuth (Supabase session)
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   └── index.ts         # chamadas REST ao backend + mapeamento snake→camel
│   │   │   ├── supabase.ts          # createClient (anon key)
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts             # Produto, HistoricoProduto, Usuario, etc.
│   ├── .env.local.example
│   ├── next.config.ts
│   └── package.json
│
├── supabase/
│   └── migrations/
│       └── 001_initial.sql
│
├── ZOIOU_REFERENCE.md
└── README.md
```

---

## 4. Banco de Dados

### Tabelas

```sql
-- Usuários (metadados além do Supabase Auth)
create table usuarios (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  telegram_id text,
  notif_telegram boolean default false,
  notif_email boolean default true,
  criado_em timestamptz default now()
);

-- Produtos monitorados (compartilhados entre usuários)
create table produtos (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  url text unique not null,
  loja text,
  imagem text,
  criado_em timestamptz default now()
);

-- Lista de desejos do usuário (relação N:N com ativo/pausado)
create table lista_desejos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid references usuarios(id) on delete cascade,
  produto_id uuid references produtos(id) on delete cascade,
  ativo boolean default true,
  criado_em timestamptz default now(),
  unique(usuario_id, produto_id)
);

-- Histórico de preços
create table historico_precos (
  id uuid primary key default gen_random_uuid(),
  produto_id uuid references produtos(id) on delete cascade,
  preco numeric(10,2) not null,
  capturado_em timestamptz default now()
);

-- Índices
create index idx_historico_produto_data on historico_precos(produto_id, capturado_em desc);
create index idx_lista_ativo on lista_desejos(ativo) where ativo = true;
```

### Regras de retenção
- Registros com `capturado_em < now() - interval '365 days'` são deletados automaticamente pelo scheduler (domingo 04:00 BRT).
- O histórico só é limpo quando o produto é **removido** da lista pelo usuário — a retenção de 365 dias serve como teto máximo.

---

## 5. Autenticação e Segurança

### Supabase Auth + RLS

O backend usa um padrão de **cliente duplo**:

| Cliente | Chave | Uso |
|---|---|---|
| `obter_cliente_rls` | `SUPABASE_ANON_KEY` + JWT do usuário | Leituras/escritas em `lista_desejos` e `usuarios` — RLS aplicado pelo banco |
| `obter_cliente` (service key) | `SUPABASE_SERVICE_KEY` | Escritas em `produtos` e `historico_precos` (tabelas compartilhadas sem INSERT policy para anon) |

Nunca usar a service key em rotas que aceitam parâmetros controlados pelo usuário sem validação prévia.

### Row Level Security (RLS)

RLS ativo em **todas** as tabelas. Exemplo:

```sql
alter table lista_desejos enable row level security;

create policy "usuario_ve_propria_lista"
  on lista_desejos for select
  using (auth.uid() = usuario_id);

create policy "usuario_gerencia_propria_lista"
  on lista_desejos for all
  using (auth.uid() = usuario_id);
```

### Variáveis de ambiente

```
# backend/.env.example
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_ANON_KEY=
TELEGRAM_BOT_TOKEN=
RESEND_API_KEY=
AMBIENTE=development   # ou production
FRONTEND_URL=          # usado no CORS em produção

# frontend/.env.local.example
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

### Proteções implementadas

- **SSRF**: `ProdutoCreate.bloquear_url_privada` rejeita IPs privados/localhost via `ipaddress.ip_address().is_global`
- **HTML injection**: `email.py` usa `html.escape()` em nome, loja e URL antes de montar o template
- **Rate limiting**: `RateLimitMiddleware` (Starlette BaseHTTPMiddleware) — 10 req/min em `POST /api/produtos`, 6 req/min em `POST /api/produtos/{id}/atualizar`, por IP (`X-Forwarded-For` para Railway)
- **Telegram ID**: `PreferenciasUpdate.validar_telegram_id` aceita apenas `@usuario` ou ID numérico
- **CORS**: aceita apenas o domínio do frontend configurado em `FRONTEND_URL` (produção) ou localhost (desenvolvimento)

---

## 6. Padrões de API

### Endpoints

```
GET    /api/produtos                     # lista produtos da lista de desejos
POST   /api/produtos                     # adiciona produto à lista
DELETE /api/produtos/{id}                # remove produto da lista
PATCH  /api/produtos/{id}                # ativa/desativa monitoramento

POST   /api/produtos/{id}/atualizar      # força scraping imediato
GET    /api/produtos/{id}/historico      # histórico de preços

GET    /api/usuarios/me                  # dados do usuário autenticado
PATCH  /api/usuarios/me/preferencias     # atualiza preferências de notificação

GET    /health                           # health check
```

### Formato de resposta

A API retorna os campos diretos (sem envelope `data/error`) — exceto o handler genérico de 500:

```json
// sucesso: retorna o objeto diretamente
{ "id": "...", "nome": "...", "preco_atual": 1850.00, ... }

// erro 500 (handler genérico)
{ "data": null, "error": { "code": "ERRO_INTERNO", "message": "Erro interno." } }
```

### Códigos HTTP
- `200` — sucesso
- `201` — criado com sucesso
- `204` — deletado com sucesso (sem corpo)
- `400` — erro de validação
- `401` — não autenticado
- `404` — não encontrado
- `422` — entidade não processável (Pydantic)
- `429` — rate limit atingido
- `500` — erro interno (nunca expor detalhes ao cliente)

---

## 7. Regras de Negócio

1. **Sem spam** — só notifica se o preço mudou em relação ao último registro.
2. **Preço histórico** — quando o preço capturado for menor que todos os registros dos últimos 365 dias, marcar como `🏆 Preço histórico`.
3. **Comparação justa** — comparar sempre com o último preço registrado, nunca com a média.
4. **Produto ativo** — scraper só processa produtos com `lista_desejos.ativo = true`.
5. **Retenção de histórico** — máximo 365 dias; limpeza automática semanal. O histórico pertence ao produto, não ao usuário — dura até o produto ser removido da lista ou completar 365 dias.
6. **Produto compartilhado** — a tabela `produtos` é compartilhada. Se dois usuários monitoram a mesma URL, o produto existe uma única vez. A `lista_desejos` é a relação por usuário.
7. **Notificação opcional** — usuário pode desativar Telegram e/ou e-mail e só consultar no dashboard.
8. **Links diretos** — nenhum link deve ser substituído por link de afiliado na v1.

---

## 8. Scraper

### Estratégia em dois estágios

O path síncrono (adição de produto) usa apenas **curl_cffi** — rápido, sem abrir browser. Se não conseguir preço ou metadados, **Playwright** é disparado em background após a resposta.

```python
# Estágio 1 (síncrono, curl_cffi): retorna rápido
dados = await extrair_produto_completo(url, usar_playwright=False)

# Estágio 2 (background, Playwright): preenche o que faltou
background_tasks.add_task(_capturar_preco_background, produto_id, url)
```

### Princípios

- A função de scraping recebe uma URL e retorna `float | None`.
- Nunca misturar lógica de scraping com lógica de negócio.
- Timeout máximo de 15 segundos por request.
- Tratar erros de scraping sem expor stack trace ao usuário.
- Nunca salvar credenciais de loja.

---

## 9. Agendador

- **Monitoramento**: todos os produtos ativos, **03:00 BRT** diariamente.
- **Limpeza**: histórico com mais de 365 dias, **domingo 04:00 BRT**.
- Nunca bloquear o event loop com operações síncronas dentro do scheduler.

```python
scheduler.add_job(
    monitorar_todos_produtos,
    trigger=CronTrigger(hour=3, minute=0, timezone="America/Sao_Paulo"),
)

scheduler.add_job(
    _limpar_historico,
    trigger=CronTrigger(day_of_week="sun", hour=4, timezone="America/Sao_Paulo"),
)
```

---

## 10. Notificações

### Formato da mensagem Telegram

```
📉 *RTX 4060 Ti — Kabum*
De R$ 1.920 → R$ 1.850
↓ R$ 70 a menos (3,6%)
🔗 [Ver produto](https://kabum.com.br/...)
```

```
📈 *RTX 4060 Ti — Kabum*
De R$ 1.850 → R$ 1.920
↑ R$ 70 a mais (3,8%)
🔗 [Ver produto](https://kabum.com.br/...)
```

```
🏆 *PREÇO HISTÓRICO — RTX 4060 Ti*
Menor preço registrado em 12 meses
R$ 1.690 na Kabum
🔗 [Ver produto](https://kabum.com.br/...)
```

### Regras
- Mensagem enviada apenas quando o preço mudou.
- Se o preço bater o mínimo histórico (365 dias), usar o formato especial com `🏆`.
- Nunca enviar stack trace ou mensagem técnica ao usuário.
- Escapar caracteres especiais do Markdown V2 em nome e URL do produto.

---

## 11. Clean Code

### Python

- Seguir **PEP 8** sem exceções.
- Usar **type hints** em todas as funções e métodos.
- Máximo de **50 linhas por função**. Se passar, quebrar em funções menores.
- Máximo de **300 linhas por arquivo**. Se passar, dividir em módulos.
- Nomes de variáveis e funções em **snake_case**, sempre em **português**.
- Nomes de classes em **PascalCase**.
- Toda função pública deve ter **docstring** curta explicando o que faz.
- Nunca usar `except Exception` genérico — capturar exceções específicas.
- Preferir **retorno explícito** a side effects.

```python
# ✅ correto
async def buscar_preco_produto(produto_id: str) -> float | None:
    """Busca o preço atual de um produto pelo seu ID."""
    ...

# ❌ errado
async def getBuscaPreco(id):
    ...
```

### TypeScript / Next.js

- Usar **TypeScript strict mode** sempre.
- Nomes de componentes em **PascalCase**.
- Nomes de funções e variáveis em **camelCase**.
- Toda prop de componente deve ter **interface** ou **type** explícito.
- Nunca usar `any` — usar `unknown` se necessário.
- Preferir **Server Components** por padrão; usar `"use client"` só quando necessário.
- Não deixar `console.log` em produção.

```typescript
// ✅ correto
interface CardProdutoProps {
  nome: string
  precoAtual: number | null
  precoAnterior: number | null
}

export function CardProduto({ nome, precoAtual, precoAnterior }: CardProdutoProps) { ... }

// ❌ errado
export function CardProduto(props: any) { ... }
```

---

## 12. Testes

- Todo service deve ter testes unitários em `tests/`.
- Usar **pytest** com **pytest-asyncio** para testes assíncronos.
- Mockar chamadas externas (Playwright, Supabase, Telegram) nos testes.
- Cobertura mínima: **70%** nas funções de `services/`.

```python
# tests/test_historico.py
async def test_detectar_preco_historico():
    historico = [1920.0, 1850.0, 2100.0, 1780.0]
    preco_atual = 1750.0
    assert eh_preco_historico(preco_atual, historico) is True
```

---

## 13. Git e Versionamento

### Commits (Conventional Commits)
```
feat: adiciona scraper para Kabum
fix: corrige parsing de preço com vírgula
chore: atualiza dependências
docs: atualiza ZOIOU_REFERENCE.md
refactor: separa lógica de notificação em service próprio
test: adiciona testes para service de histórico
```

### Regras
- Todo commit deve ser atômico — uma mudança por commit.
- Nunca commitar arquivos `.env`, `__pycache__`, `.DS_Store`, `venv/`, `.next/`.

---

## 14. Fora do Escopo (v1)

- Links de afiliado
- Canal público de promoções no Telegram
- Comparação automática de preços entre lojas
- Busca automática de produto por nome
- App mobile
- Monetização de qualquer tipo
- Alertas por preço-alvo definido pelo usuário
- Integração com Zoom, Buscapé ou qualquer agregador
- Notificações via WhatsApp

---

*Zoiou · zoiou.com.br · v1.0*
