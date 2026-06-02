# zoiou. - seu olho nos preços

[![CI](https://github.com/mauriciofeoli/zoiou-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/mauriciofeoli/zoiou-monitor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)

Monitor de preços pessoal. Cole a URL de qualquer produto, o Zoiou acompanha o preço todo dia e te avisa pelo **Telegram** quando muda - com destaque especial quando bate o menor preço dos últimos 12 meses.

**[zoiou.com](https://www.zoiou.com)** · gratuito · sem anúncios · sem afiliados

---

## Funcionalidades

- **Monitora qualquer loja brasileira** - Kabum, Pichau, Terabyte, Amazon BR, Mercado Livre e mais
- **Notificação por Telegram** quando o preço sobe ou cai
- **Badge 🏆 Preço histórico** quando o produto bate o menor preço dos últimos 12 meses
- **Gráfico de histórico** com área + linha de mínimo histórico
- **Ativar / pausar** monitoramento por produto
- **Dark mode** nativo
- **Rate limiting** e **RLS** - dados de cada usuário isolados no banco

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com) 0.111 + Python 3.12 |
| Frontend | [Next.js](https://nextjs.org) 15 + [React](https://react.dev) 19 + [Tailwind](https://tailwindcss.com) v4 |
| Banco | [Supabase](https://supabase.com) - PostgreSQL + Auth + RLS |
| Scraping | [curl_cffi](https://github.com/lexiforest/curl_cffi) (primário) → [Playwright](https://playwright.dev) (fallback) |
| Notificações | [Telegram Bot API](https://core.telegram.org/bots/api) · WhatsApp (em breve) |
| Deploy backend | [Railway](https://railway.app) |
| Deploy frontend | [Vercel](https://vercel.com) |

---

## Quickstart

### Pré-requisitos
- Python 3.12+, Node.js 20+, [Bun](https://bun.sh)
- Conta no [Supabase](https://supabase.com) (gratuito)

### Backend

```bash
cd backend
cp .env.example .env       # preencha com suas credenciais Supabase
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local   # preencha SUPABASE_URL e SUPABASE_ANON_KEY
bun install
bun run dev
# → http://localhost:3000
```

Veja o guia completo em **[docs/local-development.md](docs/local-development.md)**.

---

## Variáveis de ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Descrição |
|---------|------------|-----------|
| `SUPABASE_URL` | ✅ | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | ✅ | Chave de serviço (bypassa RLS) |
| `SUPABASE_ANON_KEY` | ✅ | Chave anon pública |
| `SECRET_KEY` | ✅ | String aleatória - `openssl rand -hex 32` |
| `FRONTEND_URL` | ✅ | URL do frontend (CORS) |
| `AMBIENTE` | ✅ | `development` ou `production` |
| `TELEGRAM_BOT_TOKEN` | - | Token do bot Telegram |

### Frontend (`frontend/.env.local`)

| Variável | Descrição |
|---------|-----------|
| `NEXT_PUBLIC_API_URL` | URL do backend |
| `NEXT_PUBLIC_SUPABASE_URL` | URL do Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Chave anon |

---

## Arquitetura

```
Browser (Next.js/Vercel)
        │ JWT
        ▼
  FastAPI (Railway)
  ├── Rate limiter
  ├── CORS middleware
  └── Auth (Supabase JWT)
        │
   ┌────┴────┐
   │         │
Supabase   Scraper
   DB    curl_cffi → Playwright
            │
      Telegram Bot API
```

O ponto mais crítico é o uso de **dois clientes Supabase** distintos no backend - service key para tabelas compartilhadas, RLS client para dados do usuário. Leia [docs/architecture.md](docs/architecture.md).

---

## Deploy

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com)

Veja o guia completo em **[docs/deployment.md](docs/deployment.md)**.

---

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/architecture.md](docs/architecture.md) | Diagrama, dois clientes Supabase, fluxo de notificação |
| [docs/api-reference.md](docs/api-reference.md) | Todos os endpoints com request/response |
| [docs/database-schema.md](docs/database-schema.md) | Tabelas, colunas, RLS policies |
| [docs/deployment.md](docs/deployment.md) | Railway, Vercel, Supabase, domínio customizado |
| [docs/local-development.md](docs/local-development.md) | Setup local passo a passo |
| [CLAUDE.md](CLAUDE.md) | Mapa do repositório para agentes de IA |

---

## Rodando os testes

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npx tsc --noEmit
```

---

## Licença

MIT © [Mauricio Feoli](https://github.com/mauriciofeoli)
