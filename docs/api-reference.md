# API Reference

Base URL: `https://zoiou-monitor-production.up.railway.app`

Todos os endpoints (exceto `/health`) exigem o header:
```
Authorization: Bearer <supabase_jwt>
```

---

## Produtos

### Listar produtos monitorados

```http
GET /api/produtos
```

Retorna a lista de desejos do usuário autenticado com preços atuais.

**Response 200**
```json
[
  {
    "id": "uuid",
    "nome": "RTX 4060 Ti 8GB",
    "url": "https://kabum.com.br/produto/123",
    "loja": "Kabum",
    "imagem": "https://cdn.kabum.com.br/...",
    "preco_atual": 1850.99,
    "preco_anterior": 1920.00,
    "ativo": true,
    "monitorando_ha_dias": 14,
    "ultima_atualizacao": "2025-01-15T03:00:00Z"
  }
]
```

---

### Adicionar produto

```http
POST /api/produtos
Content-Type: application/json

{ "url": "https://kabum.com.br/produto/123" }
```

Adiciona um produto à lista de desejos. Se a URL já existir no sistema (outro usuário monitorando), reaproveita o produto existente. Faz scraping imediato do preço.

**Limite:** 10 requisições/minuto por IP · 20 produtos por usuário

**Response 201** — produto criado  
**Response 200** — produto já existia, adicionado à lista  
**Response 409** — usuário já tem esse produto na lista  
**Response 422** — URL inválida  
**Response 429** — rate limit excedido

---

### Remover produto

```http
DELETE /api/produtos/{id}
```

Remove o produto da lista de desejos do usuário. Não deleta o produto global nem o histórico de preços.

**Response 204** — removido  
**Response 404** — produto não encontrado na lista do usuário

---

### Ativar/pausar monitoramento

```http
PATCH /api/produtos/{id}
Content-Type: application/json

{ "ativo": false }
```

**Response 200** — produto atualizado

---

### Atualizar preço agora

```http
POST /api/produtos/{id}/atualizar
```

Dispara scraping imediato e retorna o produto com preço atualizado.

**Limite:** 6 requisições/minuto por IP

**Response 200** — produto com preço atualizado  
**Response 503** — scraping falhou (preço não encontrado)

---

### Atualizar todos em background

```http
POST /api/produtos/atualizar-todos
```

Dispara scraping em background para todos os produtos ativos do usuário. Retorna imediatamente.

**Limite:** 2 requisições/minuto por IP

**Response 200**
```json
{ "iniciado": true, "total": 5 }
```

---

### Histórico de preços

```http
GET /api/produtos/{id}/historico
```

**Response 200**
```json
{
  "produto_id": "uuid",
  "pontos": [
    { "capturado_em": "2025-01-01T03:00:00Z", "preco": 1920.00 },
    { "capturado_em": "2025-01-02T03:00:00Z", "preco": 1850.99 }
  ],
  "preco_minimo": 1780.00,
  "preco_maximo": 2100.00,
  "preco_medio": 1920.50
}
```

---

## Usuários

### Perfil do usuário

```http
GET /api/usuarios/me
```

**Response 200**
```json
{
  "id": "uuid",
  "email": "usuario@email.com",
  "telegram_id": "123456789",
  "notif_telegram": true,
  "notif_email": false
}
```

---

### Atualizar preferências

```http
PATCH /api/usuarios/me/preferencias
Content-Type: application/json

{
  "notif_telegram": true,
  "telegram_id": "123456789",
  "notif_email": false
}
```

Todos os campos são opcionais. Envie apenas o que deseja alterar.

**Response 200** — preferências atualizadas

---

### Conectar Telegram

```http
POST /api/usuarios/me/telegram/conectar
```

Gera um link deep link do Telegram para o usuário abrir e vincular sua conta.

**Response 200**
```json
{ "url": "https://t.me/ZoiouBot?start=token_unico" }
```

---

### Testar notificação Telegram

```http
POST /api/usuarios/me/telegram/testar
```

Envia uma mensagem de teste para o Telegram do usuário.

**Response 204** — mensagem enviada  
**Response 400** — Telegram não configurado

---

## Sistema

### Health check

```http
GET /health
```

**Response 200**
```json
{ "status": "ok" }
```

---

## Erros

Todos os erros seguem o formato:

```json
{
  "data": null,
  "error": {
    "code": "CODIGO_ERRO",
    "message": "Descrição legível"
  }
}
```

| Código HTTP | Quando |
|------------|--------|
| 400 | Requisição inválida |
| 401 | Sem token ou token inválido/expirado |
| 403 | Sem permissão para o recurso |
| 404 | Recurso não encontrado |
| 409 | Conflito (ex: produto duplicado) |
| 422 | Dados de entrada inválidos |
| 429 | Rate limit excedido |
| 500 | Erro interno |
| 503 | Serviço externo indisponível (scraping) |
