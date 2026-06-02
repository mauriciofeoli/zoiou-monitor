# Desenvolvimento local

Guia completo para rodar o Zoiou na sua máquina.

## Pré-requisitos

- Python 3.12+
- Node.js 20+ e Bun
- Conta no [Supabase](https://supabase.com) (gratuito)
- Git

## Setup em 5 passos

### 1. Clone o repositório

```bash
git clone https://github.com/mauriciofeoli/zoiou-monitor.git
cd zoiou-monitor
```

### 2. Configure o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com)
2. Vá em **SQL Editor** e execute o schema em `docs/database-schema.md`
3. Anote a **URL**, **anon key** e **service key** (Project Settings → API)

### 3. Configure o backend

```bash
cd backend
cp .env.example .env
```

Edite `.env` com suas credenciais:
```
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...
SUPABASE_ANON_KEY=eyJ...
SECRET_KEY=qualquer-string-aleatoria-para-dev
FRONTEND_URL=http://localhost:3000
AMBIENTE=development
```

Instale as dependências e rode:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 4. Configure o frontend

```bash
cd frontend
cp .env.local.example .env.local
```

Edite `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

Instale e rode:
```bash
bun install
bun run dev
# → http://localhost:3000
```

### 5. Acesse a aplicação

Abra [http://localhost:3000](http://localhost:3000), crie uma conta e comece a monitorar.

---

## Rodando os testes

```bash
# Backend
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing -v

# Frontend (typecheck)
cd frontend
npx tsc --noEmit

# Frontend (lint)
bun run lint
```

---

## Telegram (opcional)

Para testar notificações Telegram localmente:

1. Crie um bot em [@BotFather](https://t.me/BotFather) e copie o token
2. Adicione no `.env`: `TELEGRAM_BOT_TOKEN=seu_token`
3. Para webhooks, use [ngrok](https://ngrok.com) para expor o localhost:
   ```bash
   ngrok http 8000
   # Copie a URL https e adicione em BACKEND_URL
   ```

---

## Estrutura de pastas

```
zoiou/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/         # produtos.py, historico.py, usuarios.py, telegram.py
│   │   ├── core/
│   │   │   ├── config.py       # variáveis de ambiente (Pydantic Settings)
│   │   │   ├── database.py     # cliente Supabase service key
│   │   │   ├── deps.py         # dependências FastAPI (auth, RLS client)
│   │   │   ├── limiter.py      # rate limiting por IP
│   │   │   └── security.py     # validação JWT Supabase
│   │   ├── services/
│   │   │   ├── scraper.py      # curl_cffi + Playwright fallback
│   │   │   ├── historico.py    # registrar/buscar preços
│   │   │   ├── notificacao.py  # despachar notificações
│   │   │   └── telegram.py     # envio via Bot API
│   │   ├── scheduler/
│   │   │   └── jobs.py         # cron 03:00 BRT
│   │   └── main.py             # app FastAPI, CORS, middleware
│   ├── tests/
│   │   ├── features/           # BDD .feature files
│   │   ├── test_scraper.py
│   │   ├── test_historico.py
│   │   ├── test_notificacao.py
│   │   ├── test_notificacao_despacho.py
│   │   ├── test_api_produtos.py
│   │   └── test_auth.py
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router
│       │   ├── page.tsx        # Dashboard
│       │   ├── login/
│       │   ├── produtos/[id]/
│       │   └── configuracoes/
│       ├── components/         # CardProduto, Header, GraficoHistorico...
│       ├── hooks/              # use-auth.tsx
│       ├── lib/
│       │   ├── api/index.ts    # todas as chamadas ao backend
│       │   ├── supabase.ts
│       │   └── utils.ts
│       └── types/index.ts
│
├── docs/                       # documentação técnica
├── .github/                    # CI
├── CLAUDE.md                   # mapa para agentes de IA
├── BUSINESS_RULES.md
├── DESIGN_SYSTEM.md
└── LICENSE
```

---

## Dúvidas?

Entre em contato pelo email feoli.maa@gmail.com.
