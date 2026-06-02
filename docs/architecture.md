# Arquitetura

## Visão geral

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser / Cliente                        │
│              Next.js 15 + React 19 (Vercel)                 │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS + JWT (Supabase Auth)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI (Railway)                         │
│                                                             │
│  /api/produtos   /api/usuarios   /api/historico             │
│         │                │               │                  │
│    RateLimiter      Auth Middleware   CORS Middleware        │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
     ┌───────▼────────┐          ┌────────▼────────┐
     │   Supabase DB  │          │    Scraper       │
     │  (PostgreSQL)  │          │  curl_cffi       │
     │                │          │    → Playwright  │
     │  • produtos    │          │    (fallback)    │
     │  • lista_desejos│         └────────┬─────────┘
     │  • historico_  │                   │
     │    precos      │          ┌────────▼─────────┐
     │  • usuarios    │          │  Telegram Bot API │
     └────────────────┘          └──────────────────┘
```

## Dois clientes Supabase

Este é o padrão mais crítico da arquitetura. O backend usa **dois clientes Supabase distintos** para propósitos diferentes:

| Cliente | Como obter | Quando usar |
|---------|-----------|------------|
| **Service key** | `await _db_direto()` em `database.py` | Leitura/escrita em `produtos` e `historico_precos`. Bypassa RLS — necessário porque essas tabelas são compartilhadas entre usuários. **Obrigatório em `despachar_notificacoes`** |
| **RLS client** | `Depends(obter_cliente_rls)` em `deps.py` | Leitura/escrita em `lista_desejos` e `usuarios`. O banco valida `auth.uid() = usuario_id` automaticamente |

> **Regra crítica:** Nunca passe o cliente RLS para `despachar_notificacoes`. A query em `lista_desejos` retornaria apenas o usuário atual, não todos que monitoram o produto.

## Fluxo de notificação

```
Scheduler (cron 03:00 BRT)
  └── jobs.py: monitora_todos_produtos()
        └── Para cada produto ativo:
              extrair_preco(url)                    ← scraper
                └── registrar_preco(db_s, ...)     ← service key
                      └── _notificar_variacao(...)
                            └── despachar_notificacoes(db_s, ...)
                                  ├── busca lista_desejos (todos os usuários)
                                  ├── eh_preco_historico(preco, historico_12m)
                                  ├── enviar_notificacao_telegram(...)  se notif_telegram=True
                                  └── enviar_notificacao_email(...)     se notif_email=True
```

**Condição de envio:** `preco_novo is not None` AND `abs(preco_novo - preco_anterior) > 0.01`

## Scraping

O scraper usa dois paths em cascata:

1. **curl_cffi** (primário, síncrono) — emula fingerprint de browser, mais rápido
2. **Playwright** (fallback, assíncrono em background) — headless Chromium, para páginas que exigem JS

O fallback é acionado quando curl_cffi retorna preço `None`.

## Rate limiting

Implementado como middleware Starlette (`backend/app/core/limiter.py`):

| Endpoint | Limite |
|---------|--------|
| `POST /api/produtos` | 10/min por IP |
| `POST /api/produtos/atualizar-todos` | 2/min por IP |
| `POST /api/produtos/{id}/atualizar` | 6/min por IP |

## Autenticação

O frontend usa Supabase Auth diretamente. O JWT gerado pelo Supabase é enviado no header `Authorization: Bearer <token>` para o backend. O backend valida o token com `supabase.auth.get_user(token)` — sem segredo compartilhado, sem revalidação manual de claims.
