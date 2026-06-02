# Contributing to Zoiou

Obrigado pelo interesse em contribuir! Este guia cobre tudo que você precisa para rodar o projeto localmente e enviar mudanças.

## Pré-requisitos

| Ferramenta | Versão mínima | Instalar |
|-----------|--------------|---------|
| Python | 3.12+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| Bun | 1.0+ | `curl -fsSL https://bun.sh/install \| bash` |
| Git | qualquer | [git-scm.com](https://git-scm.com) |

Você também precisará de uma conta no [Supabase](https://supabase.com) para criar um projeto de desenvolvimento.

## Setup local

### 1. Fork e clone

```bash
git clone https://github.com/SEU_USUARIO/zoiou-monitor.git
cd zoiou-monitor
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Preencha as variáveis no .env (veja a seção abaixo)
pip install -r requirements.txt
uvicorn app.main:app --reload
# API disponível em http://localhost:8000
# Docs interativos em http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Preencha NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY
bun install
bun run dev
# App disponível em http://localhost:3000
```

### Variáveis de ambiente

**`backend/.env`** (obrigatórias para dev):

| Variável | Descrição |
|---------|-----------|
| `SUPABASE_URL` | URL do seu projeto Supabase |
| `SUPABASE_SERVICE_KEY` | Chave de serviço (bypassa RLS) — em Project Settings → API |
| `SUPABASE_ANON_KEY` | Chave anon pública — em Project Settings → API |
| `SECRET_KEY` | String aleatória — gere com `openssl rand -hex 32` |
| `FRONTEND_URL` | `http://localhost:3000` para dev |
| `AMBIENTE` | `development` |
| `TELEGRAM_BOT_TOKEN` | Opcional — crie um bot com @BotFather |

**`frontend/.env.local`**:

| Variável | Descrição |
|---------|-----------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |
| `NEXT_PUBLIC_SUPABASE_URL` | Mesmo valor do backend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Mesmo valor do backend |

## Workflow de contribuição

### Branches

```
master      → produção (protegido, só aceita PR)
feat/nome   → nova funcionalidade
fix/nome    → correção de bug
chore/nome  → infra, deps, configuração
docs/nome   → documentação
```

### Passo a passo

```bash
# 1. Crie uma branch a partir da master
git checkout master && git pull
git checkout -b feat/minha-feature

# 2. Desenvolva e teste
pytest backend/tests/ -v          # testes backend
cd frontend && npx tsc --noEmit   # typecheck frontend

# 3. Commit seguindo Conventional Commits
git commit -m "feat: adiciona suporte a WhatsApp"

# 4. Push e abra PR
git push origin feat/minha-feature
```

### Conventional Commits

```
feat:     nova funcionalidade
fix:      correção de bug
chore:    infra, deps, config (sem mudança de comportamento)
refactor: reestruturação sem mudança de comportamento
docs:     apenas documentação
test:     adicionar ou corrigir testes
```

## Rodando os testes

```bash
# Backend
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing

# Frontend (typecheck)
cd frontend
npx tsc --noEmit
bun run lint
```

## Arquitetura em 30 segundos

```
Browser → Next.js (Vercel)
              ↓ JWT
        FastAPI (Railway)
         ↙         ↘
   Supabase DB    Scraper (curl_cffi → Playwright)
         ↓
   Telegram Bot API
```

Leia `CLAUDE.md` para o mapa completo do repositório e `docs/architecture.md` para detalhes.

## Dúvidas?

Abra uma [issue](https://github.com/mauriciofeoli/zoiou-monitor/issues) ou entre no [Discord](https://discord.gg/ASDrPymTfH).
