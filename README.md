# zoiou. — seu olho nos preços

Monitor de preços pessoal. Cole a URL de um produto de qualquer loja online, o Zoiou monitora o preço todo dia e te avisa quando muda — com alerta especial quando bate o menor preço dos últimos 12 meses.

**zoiou.com.br** · gratuito · sem anúncios · sem afiliados

---

## Funcionalidades

- Monitora qualquer loja brasileira (Kabum, Pichau, Terabyte, Amazon BR, etc.)
- Notificação por **Telegram** e **e-mail** quando o preço muda
- Badge de **🏆 Preço histórico** quando algo bate o mínimo dos últimos 12 meses
- Dashboard com histórico de preços em gráfico de área
- Ativar / pausar monitoramento por produto
- Dark mode

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI 0.111 + Python 3.12 |
| Frontend | Next.js 15 + React 19 + Tailwind v4 |
| Banco | Supabase (PostgreSQL + Auth + RLS) |
| Scraping | curl_cffi (primário) + Playwright (fallback) |
| Notificações | Telegram Bot API + Resend (e-mail) |
| Deploy backend | Railway |
| Deploy frontend | Vercel |

---

## Rodar localmente

### Backend

```bash
cd backend
cp .env.example .env        # preencher as variáveis
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local   # preencher as variáveis
bun install
bun run dev
# → http://localhost:3000
```

### Variáveis necessárias

**`backend/.env`**
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_ANON_KEY=
SECRET_KEY=
TELEGRAM_BOT_TOKEN=   # opcional
RESEND_API_KEY=        # opcional
FRONTEND_URL=http://localhost:3000
AMBIENTE=development
```

**`frontend/.env.local`**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

---

## Estrutura

```
zoiou/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # produtos, historico, usuarios
│   │   ├── core/           # config, database, limiter, security
│   │   ├── schemas/        # pydantic models
│   │   ├── services/       # scraper, historico, notificacao, telegram, email
│   │   └── scheduler/      # jobs.py — cron 03:00 BRT
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router (page.tsx, login, produtos, configuracoes)
│       ├── components/     # CardProduto, Header, GraficoHistorico, ZoiouWordmark...
│       ├── hooks/          # use-auth.tsx
│       ├── lib/            # api/index.ts, supabase.ts, utils.ts
│       └── types/          # index.ts
└── ZOIOU_REFERENCE.md      # fonte única de verdade do produto
```

---

## Documentação

- **`ZOIOU_REFERENCE.md`** — especificação completa: regras de negócio, stack, banco, API, segurança, clean code
- **`CLAUDE.md`** — instruções para agentes de IA que trabalham neste repositório
