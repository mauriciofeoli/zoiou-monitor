# Zoiou — Regras de Negócio

> Leia este arquivo antes de qualquer tarefa que envolva lógica de preço, notificação, scraping ou banco de dados. Ele define o comportamento esperado do sistema — não improvise fora dele.

---

## 1. Produto e lista de desejos

**O produto é compartilhado, a lista é por usuário.**

- A tabela `produtos` armazena o produto uma única vez, identificado pela URL.
- Se dois usuários cadastram a mesma URL, o registro em `produtos` é o mesmo — não duplica.
- A tabela `lista_desejos` é a relação N:N entre usuário e produto. É aqui que fica o estado `ativo/pausado` por usuário.
- Ao adicionar um produto: verificar se a URL já existe em `produtos` antes de inserir. Se existir, apenas criar a entrada em `lista_desejos`.

**Impacto:** ao alterar preço ou metadados de um produto, todos os usuários que o monitoram são afetados simultaneamente. Nunca deletar um produto da tabela `produtos` ao remover da lista de um usuário — apenas deletar a entrada em `lista_desejos`.

---

## 2. Monitoramento — quem é processado

O scraper (scheduler e endpoints de atualização manual) só processa produtos onde `lista_desejos.ativo = true`.

- Produto pausado (`ativo = false`) → não é raspado, não gera histórico, não gera notificação.
- Produto ativo → processado normalmente.

O scheduler roda **diariamente às 03:00 BRT** e processa todos os produtos ativos de todos os usuários, sem duplicar (um produto monitorado por múltiplos usuários é raspado uma única vez por ciclo).

---

## 3. Registro de preço e histórico

- Todo preço capturado é registrado em `historico_precos` com `capturado_em = now()`.
- **Não há deduplicação automática** — se o scraper rodar duas vezes e o preço for o mesmo, dois registros são criados. A comparação de variação resolve isso (ver regra 4).
- Retenção máxima: **365 dias**. Registros mais antigos são deletados pelo scheduler todo **domingo às 04:00 BRT** (`_limpar_historico`).
- O histórico pertence ao produto, não ao usuário. Dura até o produto ser removido da lista por todos os usuários OU até 365 dias.

---

## 4. Quando notificar

**Regra central: só notifica se o preço mudou de forma significativa.**

```python
abs(preco_novo - preco_anterior) > 0.01  # diferença mínima de R$ 0,01
```

- `preco_anterior` = o registro mais recente em `historico_precos` antes do novo.
- Se a diferença for ≤ R$ 0,01 → sem notificação (mesmo preço, variação de centavo por arredondamento).
- Se o scraping falhar (`preco_novo is None`) → sem notificação. Nunca comparar dois preços históricos para gerar notificação — só notificar quando um novo preço foi de fato capturado e registrado.
- Primeiro registro de um produto (sem histórico anterior) → sem notificação.

**Todos os usuários que têm o produto ativo na lista de desejos são notificados**, não só quem disparou a atualização. Por isso `despachar_notificacoes` sempre recebe o cliente service key — o RLS limitaria ao usuário atual.

---

## 5. Preço histórico (menor preço)

Quando o preço capturado é **menor que todos os registros dos últimos 365 dias**, o produto recebe o tratamento especial de "preço histórico":

- Notificação com formato especial: `🏆 PREÇO HISTÓRICO`
- Badge dourado (`--gold`) no frontend
- A função `eh_preco_historico(preco_atual, lista_de_precos)` em `services/historico.py` faz esse cálculo

**Comparação justa:** sempre comparar com o último preço registrado, nunca com média ou mediana. O histórico é usado apenas para determinar se é o menor preço — a variação é calculada em relação ao registro imediatamente anterior.

---

## 6. Canais de notificação

| Canal | Status | Condição |
|-------|--------|----------|
| Telegram | **Ativo** | `notif_telegram = true` E `telegram_id` preenchido |

- O usuário controla o canal nas preferências (`/configuracoes`).
- Se nenhum canal estiver configurado, o preço ainda é monitorado e salvo — o usuário pode consultar pelo dashboard.
- **Nunca enviar stack trace ou mensagem técnica** ao usuário via Telegram ou qualquer canal.

---

## 7. Scraping — estratégia em dois estágios

**Estágio 1 — path síncrono (adição de produto):**
- Usa apenas `curl_cffi` — rápido, sem abrir browser.
- Se capturar preço e metadados → retorna imediatamente.
- Se não capturar → responde mesmo assim e dispara Playwright em background.

**Estágio 2 — background (Playwright):**
- Roda após a resposta já ter sido enviada ao cliente.
- Preenche preço e metadados que o estágio 1 não conseguiu.
- Timeout máximo: **15 segundos** por request.

**Monitoramento diário (scheduler):**
- Usa `extrair_preco(url)` diretamente — tenta curl_cffi, fallback Playwright.
- Erros de scraping são logados mas não interrompem o ciclo dos outros produtos.

---

## 8. Segurança e validações

- **SSRF:** `ProdutoCreate` valida que a URL não aponta para IPs privados/localhost.
- **Rate limiting:** 10 req/min em `POST /api/produtos`, 2 req/min em `POST /api/produtos/atualizar-todos`, 6 req/min em `POST /api/produtos/{id}/atualizar` — por IP.
- **Telegram ID:** aceita apenas `@usuario` ou ID numérico. Validado no schema.
- **RLS:** ativo em todas as tabelas. Usar service key só quando necessário (ver CLAUDE.md).
- **CORS:** apenas o domínio do frontend configurado em `FRONTEND_URL`.
- Nunca usar service key em rotas que aceitam parâmetros do usuário sem validação prévia.

---

## 9. Fora do escopo (não implementar)

- Links de afiliado (nunca substituir URL original)
- Canal público de promoções no Telegram
- Comparação automática de preços entre lojas
- Busca de produto por nome
- App mobile
- Monetização de qualquer tipo
- Alertas por preço-alvo definido pelo usuário
- Integração com Zoom, Buscapé ou agregadores
- WhatsApp, e-mail ou qualquer canal além do Telegram

---

## 10. Respostas da API

- Retorna campos diretos, sem envelope `data/error` — exceto erros 500.
- `204` em DELETE bem-sucedido (sem corpo).
- Nunca expor stack trace ou detalhe interno em respostas de erro.
- Códigos: `200` sucesso · `201` criado · `204` deletado · `400` validação · `401` não autenticado · `404` não encontrado · `429` rate limit · `500` erro interno.
