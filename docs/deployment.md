# Deploy

O Zoiou usa Railway (backend) e Vercel (frontend). Ambos deployam automaticamente a cada push na branch `master`.

---

## Backend - Railway

### Deploy em um clique

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template)

### Manual

1. Crie uma conta em [railway.app](https://railway.app)
2. Novo projeto → Deploy from GitHub repo → selecione este repositório
3. Configure o **Root Directory** como `backend`
4. Configure o **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Adicione as variáveis de ambiente (veja abaixo)
6. Clique em Deploy

### Variáveis de ambiente (Railway)

| Variável | Obrigatória | Descrição |
|---------|------------|-----------|
| `SUPABASE_URL` | ✅ | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | ✅ | Chave de serviço (Project Settings → API) |
| `SUPABASE_ANON_KEY` | ✅ | Chave anon pública |
| `SECRET_KEY` | ✅ | String aleatória - `openssl rand -hex 32` |
| `FRONTEND_URL` | ✅ | URL do frontend em produção (ex: `https://www.zoiou.com`) |
| `FRONTEND_URLS_EXTRAS` | - | URLs adicionais separadas por vírgula |
| `AMBIENTE` | ✅ | `production` |
| `TELEGRAM_BOT_TOKEN` | - | Token do bot (crie em @BotFather) |
| `TELEGRAM_WEBHOOK_SECRET` | - | String aleatória para validar webhooks |
| `BACKEND_URL` | - | URL pública do backend (para registrar webhook Telegram) |
| `RESEND_API_KEY` | - | API key do Resend (notificações por email) |

---

## Frontend - Vercel

### Deploy em um clique

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/mauriciofeoli/zoiou-monitor)

### Manual

1. Crie uma conta em [vercel.com](https://vercel.com)
2. New Project → Import Git Repository → selecione este repositório
3. Configure o **Root Directory** como `frontend`
4. Adicione as variáveis de ambiente (veja abaixo)
5. Deploy

### Variáveis de ambiente (Vercel)

| Variável | Descrição |
|---------|-----------|
| `NEXT_PUBLIC_API_URL` | URL do backend Railway (ex: `https://zoiou-monitor-production.up.railway.app`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Mesmo valor do backend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Mesmo valor do backend |

---

## Supabase

1. Crie um projeto em [supabase.com](https://supabase.com)
2. Execute as migrations em **SQL Editor** (veja `docs/database-schema.md`)
3. Em **Authentication → URL Configuration**:
   - Site URL: `https://www.seudominio.com`
   - Redirect URLs: `https://www.seudominio.com/**`
4. Copie a **URL**, **anon key** e **service key** para as variáveis de ambiente

---

## Domínio customizado

### Vercel
Settings → Domains → Add Domain → siga as instruções de DNS

### Railway
Settings → Networking → Custom Domain → adicione o domínio e configure o CNAME

### CORS
Após configurar o domínio customizado, atualize no Railway:
```
FRONTEND_URL=https://www.seudominio.com
FRONTEND_URLS_EXTRAS=https://seudominio.com,https://seu-projeto.vercel.app
```

---

## CI/CD

GitHub Actions roda automaticamente em todo PR e push para `master`:

- `backend-test` - pytest
- `backend-lint` - ruff
- `frontend-typecheck` - tsc
- `frontend-lint` - eslint

Configure os secrets no GitHub em **Settings → Secrets → Actions**:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`
