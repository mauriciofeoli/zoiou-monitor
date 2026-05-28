# ZOIOU — Documento de Referência do Projeto

> Este documento é a fonte única de verdade para o desenvolvimento do Zoiou.
> Toda IA, desenvolvedor ou colaborador deve seguir estas instruções à risca.

---

## 1. Visão Geral do Produto

**Zoiou** é um monitor de preços pessoal. O usuário cadastra a URL de um produto em qualquer loja online, e o sistema monitora o preço diariamente, notificando quando há variação.

- **Tipo:** SaaS gratuito (v1)
- **Domínio:** zoiou.com.br
- **Linguagem principal:** Python (backend) + Next.js (frontend)
- **Banco de dados:** Supabase (PostgreSQL)
- **Deploy:** Railway

---

## 2. Stack Técnica

### Backend
| Tecnologia | Versão mínima | Uso |
|---|---|---|
| Python | 3.12+ | Linguagem principal |
| FastAPI | 0.111+ | API REST |
| Playwright | 1.44+ | Scraping com renderização JS |
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
| Next.js | 14+ | Framework web (App Router) |
| TypeScript | 5+ | Tipagem |
| Tailwind CSS | 3+ | Estilização |
| shadcn/ui | latest | Componentes de UI |
| Recharts | 2+ | Gráficos de histórico |

### Infraestrutura
| Serviço | Uso |
|---|---|
| Supabase | PostgreSQL + Auth |
| Railway | Deploy do backend Python |
| Vercel | Deploy do frontend Next.js |

---

## 3. Estrutura de Pastas

```
zoiou/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── produtos.py
│   │   │   │   ├── historico.py
│   │   │   │   └── usuarios.py
│   │   │   └── deps.py              # dependências compartilhadas
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # configurações e env vars
│   │   │   ├── security.py          # autenticação e tokens
│   │   │   └── database.py          # conexão com Supabase
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── produto.py
│   │   │   ├── historico.py
│   │   │   └── usuario.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── produto.py
│   │   │   ├── historico.py
│   │   │   └── usuario.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py           # lógica de scraping
│   │   │   ├── notificacao.py       # despacho de notificações
│   │   │   ├── telegram.py          # integração Telegram
│   │   │   ├── email.py             # integração Resend
│   │   │   └── historico.py         # lógica de histórico e comparação
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   └── jobs.py              # tarefas agendadas
│   │   └── main.py                  # entry point FastAPI
│   ├── tests/
│   │   ├── __init__.py
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
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx             # dashboard principal
│   │   │   ├── produtos/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx     # detalhe do produto
│   │   │   └── configuracoes/
│   │   │       └── page.tsx         # preferências de notificação
│   │   ├── components/
│   │   │   ├── ui/                  # componentes shadcn
│   │   │   ├── ListaDesejos.tsx
│   │   │   ├── GraficoHistorico.tsx
│   │   │   ├── CardProduto.tsx
│   │   │   └── BadgePrecoHistorico.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # chamadas para o backend
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts
│   ├── .env.local.example
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── supabase/
│   └── migrations/
│       └── 001_initial.sql
│
└── README.md
```

---

## 4. Banco de Dados

### Tabelas

```sql
-- Usuários
create table usuarios (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  telegram_id text,
  whatsapp text,
  notif_telegram boolean default false,
  notif_whatsapp boolean default false,
  notif_email boolean default true,
  criado_em timestamptz default now()
);

-- Produtos monitorados
create table produtos (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  url text not null,
  loja text,
  criado_em timestamptz default now()
);

-- Lista de desejos do usuário
create table lista_desejos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid references usuarios(id) on delete cascade,
  produto_id uuid references produtos(id) on delete cascade,
  ativo boolean default true,
  criado_em timestamptz default now(),
  unique(usuario_id, produto_id)
);

-- Histórico de preços (máximo 365 dias)
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
- Registros com `capturado_em < now() - interval '365 days'` devem ser deletados automaticamente.
- Usar uma função agendada no Supabase ou no scheduler do backend para isso.

---

## 5. Regras de Negócio

1. **Sem spam** — só notifica se o preço mudou em relação ao último registro.
2. **Preço histórico** — quando o preço capturado for menor que todos os registros dos últimos 365 dias, marcar como `🏆 Preço histórico`.
3. **Comparação justa** — comparar sempre com o último preço registrado, nunca com a média.
4. **Produto ativo** — scraper só processa produtos com `lista_desejos.ativo = true`.
5. **Histórico máximo** — deletar registros com mais de 365 dias automaticamente.
6. **Notificação opcional** — usuário pode optar por não receber notificação nenhuma e só consultar no dashboard.
7. **Links diretos** — nenhum link deve ser substituído por link de afiliado na v1.

---

## 6. Clean Code

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
- Nunca comentar código morto — deletar.

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
  precoAtual: number
  precoAnterior: number
}

export function CardProduto({ nome, precoAtual, precoAnterior }: CardProdutoProps) {
  ...
}

// ❌ errado
export function CardProduto(props: any) {
  ...
}
```

---

## 7. Segurança

### Variáveis de ambiente
- **Nunca** commitar `.env` no repositório.
- Sempre manter `.env.example` atualizado com todas as chaves necessárias (sem valores).
- Usar `python-dotenv` no backend e variáveis de ambiente do Vercel/Railway no deploy.

```
# .env.example
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
TELEGRAM_BOT_TOKEN=
RESEND_API_KEY=
SECRET_KEY=
```

### Autenticação
- Usar **Supabase Auth** para autenticação de usuários.
- Tokens JWT validados em toda rota protegida da API.
- Nunca expor a `SUPABASE_SERVICE_KEY` no frontend — usar apenas a `SUPABASE_ANON_KEY` com Row Level Security (RLS) ativado.

### Row Level Security (RLS)
- Ativar RLS em **todas** as tabelas do Supabase.
- Usuário só pode ler e escrever seus próprios dados.

```sql
-- Exemplo: usuário só vê sua própria lista
alter table lista_desejos enable row level security;

create policy "usuario_ve_propria_lista"
  on lista_desejos for select
  using (auth.uid() = usuario_id);
```

### API
- Todas as rotas que modificam dados exigem autenticação.
- Validar e sanitizar toda entrada com **Pydantic** no backend.
- Rate limiting nas rotas de scraping para evitar abuso.
- CORS configurado para aceitar apenas o domínio do frontend.

### Scraping
- Nunca salvar credenciais de loja.
- User-agent rotacionado para evitar bloqueio.
- Timeout máximo de 15 segundos por request de scraping.
- Tratar erros de scraping sem expor stack trace ao usuário.

---

## 8. Padrões de API

### Convenções REST

```
GET    /api/produtos              # lista produtos da lista de desejos
POST   /api/produtos              # adiciona produto à lista
DELETE /api/produtos/{id}         # remove produto da lista
PATCH  /api/produtos/{id}         # ativa/desativa monitoramento

GET    /api/produtos/{id}/historico  # histórico de preços de um produto
GET    /api/usuarios/me              # dados do usuário autenticado
PATCH  /api/usuarios/me/preferencias # atualiza preferências de notificação
```

### Formato de resposta

```json
{
  "data": { ... },
  "error": null
}
```

```json
{
  "data": null,
  "error": {
    "code": "PRODUTO_NAO_ENCONTRADO",
    "message": "Produto não encontrado."
  }
}
```

### Códigos HTTP
- `200` — sucesso
- `201` — criado com sucesso
- `400` — erro de validação
- `401` — não autenticado
- `403` — sem permissão
- `404` — não encontrado
- `422` — entidade não processável
- `500` — erro interno (nunca expor detalhes ao cliente)

---

## 9. Scraper

### Princípios
- Cada loja tem seu próprio extrator de preço isolado em uma função.
- A função de scraping recebe uma URL e retorna um `float | None`.
- Nunca misturar lógica de scraping com lógica de negócio.
- Usar Playwright para sites com JavaScript e `httpx + BeautifulSoup4` para sites estáticos.

### Estrutura do scraper

```python
async def extrair_preco(url: str) -> float | None:
    """Extrai o preço de um produto a partir da URL da loja."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            preco_texto = await page.locator(".preco-atual").inner_text()
            return parsear_preco(preco_texto)
    except Exception as e:
        logger.error(f"Erro ao extrair preço de {url}: {e}")
        return None

def parsear_preco(texto: str) -> float:
    """Converte string de preço para float."""
    limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(limpo)
```

---

## 10. Agendador

- Rodar o ciclo de monitoramento **uma vez por dia**, de madrugada (ex: 03:00 BRT).
- O job de limpeza de histórico roda **uma vez por semana**.
- Nunca bloquear o event loop com operações síncronas dentro do scheduler.

```python
scheduler.add_job(
    monitorar_todos_produtos,
    trigger="cron",
    hour=3,
    minute=0,
    timezone="America/Sao_Paulo"
)

scheduler.add_job(
    limpar_historico_antigo,
    trigger="cron",
    day_of_week="sun",
    hour=4,
    timezone="America/Sao_Paulo"
)
```

---

## 11. Notificações

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
- Se o preço bater o mínimo histórico, usar o formato especial com `🏆`.
- Nunca enviar stack trace ou mensagem técnica ao usuário.

---

## 12. Testes

- Todo service deve ter testes unitários correspondentes em `tests/`.
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

### Branches
- `main` — produção, sempre estável
- `develop` — integração de features
- `feature/nome-da-feature` — desenvolvimento de funcionalidade
- `fix/nome-do-bug` — correção de bug

### Commits (Conventional Commits)
```
feat: adiciona scraper para Kabum
fix: corrige parsing de preço com vírgula
chore: atualiza dependências
docs: atualiza README com instruções de setup
refactor: separa lógica de notificação em service próprio
test: adiciona testes para service de histórico
```

### Regras
- Nunca fazer commit direto em `main`.
- Todo commit deve ser atômico — uma mudança por commit.
- Nunca commitar arquivos `.env`, `__pycache__`, `.DS_Store`.

---

## 14. .gitignore

```
# Python
__pycache__/
*.py[cod]
*.pyo
.env
.venv/
venv/
dist/
build/
*.egg-info/

# Node
node_modules/
.next/
.env.local
.env.production

# Sistema
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

---

## 15. Fora do Escopo (v1)

As funcionalidades abaixo **não devem ser implementadas** na v1:

- Links de afiliado
- Canal público de promoções no Telegram
- Comparação automática de preços entre lojas
- Busca automática de produto por nome
- App mobile
- Monetização de qualquer tipo
- Alertas por preço-alvo definido pelo usuário
- Integração com Zoom, Buscapé ou qualquer agregador

---

*Zoiou · zoiou.com.br · v1.0*
