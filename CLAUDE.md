# Zoiou — contexto para agentes de IA

> Leia este arquivo inteiro antes de qualquer tarefa. Ele é o mapa do repositório.
> Para lógica de preço, notificação, scraping ou banco — leia também **`BUSINESS_RULES.md`**.

---

## O que é o Zoiou

Monitor de preços pessoal (SaaS gratuito v1). O usuário cola a URL de um produto, o sistema raspa o preço diariamente e notifica via Telegram quando muda. Badge especial quando o preço bate o mínimo histórico dos últimos 12 meses.

Para regras de negócio completas leia **`BUSINESS_RULES.md`**.

---

## Stack em 30 segundos

| O quê | Como |
|-------|------|
| Backend | FastAPI + Python 3.12, em `backend/` |
| Frontend | Next.js 15 + React 19 + Tailwind v4, em `frontend/` |
| Banco | Supabase — PostgreSQL + Auth + RLS |
| Scraping | curl_cffi (path síncrono) → Playwright (fallback, background) |
| Notificações | Telegram Bot API |
| Deploy | Railway (backend) · Vercel (frontend) |
| URLs prod | `www.zoiou.com` (frontend) · `zoiou-monitor-production.up.railway.app` (backend) |

---

## Arquivos-chave — navegue por aqui primeiro

### Backend
| Arquivo | O que faz |
|---------|-----------|
| `backend/app/api/routes/produtos.py` | CRUD da lista de desejos + scraping imediato + atualizar-todos |
| `backend/app/api/routes/historico.py` | Histórico de preços por produto |
| `backend/app/api/routes/usuarios.py` | Perfil e preferências de notificação |
| `backend/app/api/routes/telegram.py` | Webhook do bot Telegram + conectar/testar |
| `backend/app/api/deps.py` | `obter_usuario_autenticado`, `obter_cliente_rls` |
| `backend/app/core/database.py` | `obter_cliente()` → service key (bypassa RLS) |
| `backend/app/core/limiter.py` | Rate limiting por IP (middleware Starlette) |
| `backend/app/services/scraper.py` | `extrair_preco`, `extrair_produto_completo`, `extrair_metadados_produto` |
| `backend/app/services/notificacao.py` | `despachar_notificacoes` — envia Telegram para todos os usuários do produto |
| `backend/app/services/historico.py` | `registrar_preco`, `buscar_ultimo_preco`, `buscar_ultimos_precos` |
| `backend/app/scheduler/jobs.py` | Cron 03:00 BRT — monitora todos os produtos ativos |

### Frontend
| Arquivo | O que faz |
|---------|-----------|
| `frontend/src/app/page.tsx` | Dashboard principal — lista de desejos |
| `frontend/src/app/login/page.tsx` | Login / cadastro (Supabase Auth) |
| `frontend/src/app/produtos/[id]/page.tsx` | Detalhe do produto + gráfico |
| `frontend/src/app/configuracoes/page.tsx` | Preferências de notificação |
| `frontend/src/lib/api/index.ts` | Todas as chamadas ao backend (token JWT automático) |
| `frontend/src/hooks/use-auth.tsx` | `AuthProvider` + `useAuth` hook |
| `frontend/src/components/ZoiouWordmark.tsx` | Logo SVG (wordmark + EyeMark) |
| `frontend/src/app/globals.css` | Tokens de cor oklch, dark mode, tipografia |

---

## Padrão crítico: dois clientes Supabase

Este é o ponto de maior risco de bug no backend. Sempre pergunte qual cliente usar:

| Cliente | Variável | Quando usar |
|---------|----------|-------------|
| **Service key** | `db_s = await _db_direto()` | Leitura/escrita em `produtos` e `historico_precos` (tabelas compartilhadas, sem RLS de inserção para anon). **Sempre use para `despachar_notificacoes`** — o service key encontra todos os usuários do produto. |
| **RLS (anon + JWT)** | `db: AsyncClient = Depends(obter_cliente_rls)` | Leitura/escrita em `lista_desejos` e `usuarios` — o banco valida `auth.uid() = usuario_id`. |

**Nunca** passe o cliente RLS para `despachar_notificacoes` — a query em `lista_desejos` retornaria só o usuário atual, não todos que monitoram o produto.

---

## Fluxo de notificação

```
extrair_preco(url)
  → registrar_preco(db_s, produto_id, preco_novo)   ← service key
    → _notificar_variacao(db_s, ...)                 ← service key
      → despachar_notificacoes(db_s, ...)            ← service key
        → busca lista_desejos (todos os usuários)
        → envia Telegram se notif_telegram=True e telegram_id preenchido
```

Notificação só sai quando `preco_novo is not None` (scraping bem-sucedido) e `abs(preco_novo - preco_anterior) > 0.01`.

---

## Convenções — siga sempre

### Python (backend)
- **PEP 8** sem exceções. Type hints em todas as funções.
- Nomes em **snake_case português** (`buscar_preco`, `registrar_preco`).
- Máx. 50 linhas por função, 300 por arquivo.
- Nunca `except Exception` genérico.
- Docstring curta em toda função pública.

### TypeScript (frontend)
- **strict mode**. Nunca `any`, use `unknown`.
- `interface` ou `type` explícito em toda prop de componente.
- Nomes de componentes em **PascalCase**, funções/variáveis em **camelCase**.
- Sem `console.log` em produção.

### Commits (Conventional Commits)
```
feat:     nova funcionalidade
fix:      correção de bug
chore:    limpeza, dependências, configuração
refactor: reestruturação sem mudança de comportamento
docs:     apenas documentação
test:     adicionar ou corrigir testes
style:    formatação, sem mudança de lógica
```

---

## Banco de dados — tabelas principais

```sql
produtos          -- produto compartilhado (URL única)
lista_desejos     -- relação usuário ↔ produto (ativo/pausado)
historico_precos  -- série temporal de preços por produto
usuarios          -- metadados além do Supabase Auth (telegram_id, notif_*)
```

RLS ativo em todas as tabelas. `historico_precos` e `produtos` → service key para escrita. `lista_desejos` e `usuarios` → cliente RLS.

---

## API — endpoints

```
GET    /api/produtos                        lista desejos do usuário
POST   /api/produtos                        adiciona produto
DELETE /api/produtos/{id}                   remove da lista
PATCH  /api/produtos/{id}                   ativa/pausa monitoramento
POST   /api/produtos/atualizar-todos        scraping em background para todos ativos
POST   /api/produtos/{id}/atualizar         scraping imediato de um produto
GET    /api/produtos/{id}/historico         histórico de preços
GET    /api/usuarios/me                     perfil do usuário
PATCH  /api/usuarios/me/preferencias        salva preferências de notificação
POST   /api/usuarios/me/telegram/conectar   gera link de conexão Telegram
POST   /api/usuarios/me/telegram/testar     envia mensagem de teste Telegram
GET    /health                              health check
```

---

## Estrutura de documentação e CI

```
docs/
  architecture.md       diagrama, dois clientes Supabase, fluxo de notificação
  api-reference.md      todos os endpoints com request/response
  database-schema.md    tabelas, colunas, RLS policies
  deployment.md         Railway + Vercel + Supabase + domínio customizado
  local-development.md  setup detalhado para dev local

.github/
  workflows/ci.yml                pytest + ruff + tsc + eslint em todo push

LICENSE                 MIT
```

---

## Rodar localmente

```bash
# Backend
cd backend && uvicorn app.main:app --reload   # porta 8000

# Frontend
cd frontend && bun run dev                    # porta 3000
```

---

## Design system

Para qualquer mudança visual leia **`DESIGN_SYSTEM.md`** — tokens, componentes, tipografia, ícones e regras de voz derivados do código real.

Princípios visuais resumidos:
- **Cor:** oklch, neutros quentes. Verde = queda de preço. Vermelho = alta. Dourado = preço histórico.
- **Tipo:** Inter em todo lugar. `font-serif` no código = Inter 700 com tracking −0.025em (alias histórico).
- **Cards:** `rounded-2xl`, sem sombra em repouso, lift no hover.
- **Botões:** pill (`rounded-full`). Primário = ink sólido. Secundário = borda fina.
- **Logo:** wordmark SVG `z·👁·|·👁·u` — componente `ZoiouWordmark` em `components/ZoiouWordmark.tsx`.
