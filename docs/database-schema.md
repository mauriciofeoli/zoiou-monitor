# Database Schema

Banco PostgreSQL gerenciado pelo Supabase com RLS (Row Level Security) ativo em todas as tabelas.

## Tabelas

### `produtos`

Produto compartilhado entre usuários. URL é única — se dois usuários monitoram o mesmo produto, há apenas um registro aqui.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `uuid` PK | Identificador único |
| `url` | `text` UNIQUE | URL do produto (normalizada) |
| `nome` | `text` | Nome extraído pelo scraper |
| `loja` | `text` | Nome da loja (ex: "Kabum") |
| `imagem` | `text` | URL da imagem do produto |
| `created_at` | `timestamptz` | Data de criação |

**RLS:** leitura pública; escrita apenas via service key.

---

### `lista_desejos`

Relação N:N entre usuários e produtos. Cada linha representa um usuário monitorando um produto.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `uuid` PK | |
| `usuario_id` | `uuid` FK → `auth.users` | Usuário dono |
| `produto_id` | `uuid` FK → `produtos` | Produto monitorado |
| `ativo` | `boolean` | Se o monitoramento está ativo |
| `created_at` | `timestamptz` | Data de adição |

**RLS:** usuário só acessa suas próprias linhas (`auth.uid() = usuario_id`).  
**Índice:** `(usuario_id, produto_id)` UNIQUE — impede duplicatas.

---

### `historico_precos`

Série temporal de preços por produto. Registros são inseridos pelo scheduler diário e por atualizações manuais.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `uuid` PK | |
| `produto_id` | `uuid` FK → `produtos` | |
| `preco` | `numeric(12,2)` | Preço capturado |
| `capturado_em` | `timestamptz` | Timestamp da captura (default: now()) |

**RLS:** leitura pública; escrita apenas via service key.  
**Retenção:** registros com mais de 365 dias são limpos pelo scheduler.

---

### `usuarios`

Extensão do Supabase Auth com preferências de notificação. Criada automaticamente no primeiro login via upsert.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `uuid` PK FK → `auth.users` | |
| `email` | `text` | Email do usuário |
| `telegram_id` | `text` | ID do Telegram (opcional) |
| `notif_telegram` | `boolean` | Notificações Telegram ativas |
| `notif_email` | `boolean` | Notificações email ativas |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**RLS:** usuário só acessa e modifica sua própria linha.

---

## Limites de negócio

- Máximo de **20 produtos por usuário** (validado na API antes de inserir em `lista_desejos`)
- Histórico mantido por **365 dias**
- Variação mínima para registrar novo preço: **R$ 0,01**

## Clientes Supabase no backend

```python
# Service key — bypassa RLS
db_s = await _db_direto()   # database.py

# RLS client — respeita auth.uid()
db: AsyncClient = Depends(obter_cliente_rls)   # deps.py
```

Ver `docs/architecture.md` para quando usar cada um.
