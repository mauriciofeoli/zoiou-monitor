# Zoiou — Design System

> Fonte de verdade visual do projeto. Derivado do código real em `frontend/src/`.
> Ao mudar qualquer padrão visual, atualize este documento junto.

---

## 1. Princípio geral

**Minimalismo funcional.** Superfícies brancas separadas por bordas finas, cor reservada quase exclusivamente para significado (direção de preço). Sem sombras decorativas, sem gradientes, sem animações de entrada. Silencioso em repouso, responsivo na interação.

---

## 2. Tokens de cor

Definidos em `frontend/src/app/globals.css` usando **oklch**. Nunca usar hex ou hsl no código — sempre referenciar os tokens.

### Light mode (padrão)
```css
--background:       oklch(1 0 0)           /* branco puro — fundo da página */
--foreground:       oklch(0.25 0.012 85)   /* texto principal — cinza quente escuro */
--ink:              oklch(0.18 0.012 85)   /* títulos e preços — quase preto */
--card:             oklch(1 0 0)           /* fundo de cards — branco */
--muted-foreground: oklch(0.52 0.008 85)  /* legendas, metadados */
--border:           oklch(0.905 0.004 85) /* bordas finas */
--success:          oklch(0.58 0.16 150)  /* verde — queda de preço */
--destructive:      oklch(0.58 0.2 28)    /* vermelho — alta de preço */
--gold:             oklch(0.72 0.14 75)   /* dourado — preço histórico */
```

### Dark mode (classe `.dark` no html)
```css
--background:  oklch(0.18 0 0)   /* ≈ #121212 — fundo base */
--foreground:  oklch(0.83 0 0)
--ink:         oklch(0.93 0 0)
--card:        oklch(0.22 0 0)   /* ≈ #1a1a1a — superfícies elevadas (inputs, cards) */
--border:      oklch(1 0 0 / 10%)
--success:     oklch(0.7 0.16 150)
--destructive: oklch(0.68 0.2 28)
--gold:        oklch(0.78 0.14 75)
--brand:       oklch(0.68 0.2 250)  /* azul — cor primária de destaque */
--brand-foreground: oklch(1 0 0)
```

### Uso semântico das cores
| Cor | Classe Tailwind | Quando usar |
|-----|----------------|-------------|
| Azul (brand) | `text-brand`, `bg-brand`, `ring-brand/40` | CTAs principais (botão Entrar), destaques de headline |
| Verde | `text-success`, `bg-success/15`, `ring-success/30` | Preço caiu, economia, notificação positiva |
| Vermelho | `text-destructive`, `bg-destructive/15`, `ring-destructive/30` | Preço subiu, erro, ação destrutiva |
| Dourado | `text-gold`, `bg-gold/15`, `ring-gold/40` | Preço histórico (mínimo 12 meses) exclusivamente |
| Muted | `text-muted-foreground` | Legendas, metadados, labels, datas |

---

## 3. Tipografia

**Uma única fonte: Inter.** Sem exceções.

| Uso | Classes | Exemplo no código |
|-----|---------|-------------------|
| Títulos / preços | `font-serif text-2xl text-ink` | Headline do dashboard, preço no detalhe |
| Corpo | `text-sm text-foreground` | Nomes de produto, labels de formulário |
| Legenda / meta | `text-xs text-muted-foreground` | "0 dias monitorando", contagem de registros |
| Overline / eyebrow | `text-xs uppercase tracking-wider text-muted-foreground` | Labels dos cards de estatística (Mínimo, Máximo...) |
| Preço grande | `font-serif text-4xl text-ink leading-none` | Preço na página de detalhe |
| Preço médio | `font-serif text-2xl leading-none text-ink` | Preço no card do dashboard |

> **Nota:** `font-serif` no código **não é serif** — é um alias histórico para Inter 700 com `letter-spacing: -0.025em`. Definido em `globals.css`:
> ```css
> .font-serif { font-family: var(--font-sans); font-weight: 700; letter-spacing: -0.025em; }
> ```

---

## 4. Bordas e raios

| Elemento | Classe | Valor |
|----------|--------|-------|
| Cards, modais, imagens | `rounded-2xl` | 16px |
| Inputs de formulário | `rounded-xl` | 12px |
| Botões, badges, chips | `rounded-full` | pill |
| Chips de loja (header do card) | `rounded-full` | pill |

Bordas sempre `border border-border` (1px, token `--border`). Dashed só em estados vazios (`border-dashed`).

---

## 5. Componentes

### Botão primário
```tsx
className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-3 text-sm font-medium text-brand-foreground hover:bg-brand/90 transition-colors"
```
Uso: ação principal da tela (Entrar, Criar conta). Cor: azul brand com texto branco.

### Botão secundário
```tsx
className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm hover:bg-secondary transition-colors"
```
Uso: ações secundárias (Atualizar agora, Pausar, Retomar).

### Botão destrutivo
```tsx
className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm text-destructive hover:bg-destructive/5 transition-colors"
```
Uso: Remover produto. Sempre acompanhar de modal de confirmação.

### Botão desabilitado
Adicionar `disabled:opacity-50 disabled:cursor-not-allowed` em qualquer botão.

---

### Card de produto
```tsx
// Repouso
className="rounded-2xl border border-border bg-card"

// Hover (aplicado no Link wrapper)
className="hover:border-foreground/30 hover:shadow-[0_8px_30px_-12px_rgba(0,0,0,0.15)] transition-all"

// Imagem
className="aspect-[3/2] overflow-hidden bg-muted rounded-t-2xl object-cover transition-transform duration-500 group-hover:scale-105"
```

### Chip de variação de preço
```tsx
// Queda (verde)
className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-success/15 text-success ring-1 ring-success/30"

// Alta (vermelho)
className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-destructive/15 text-destructive ring-1 ring-destructive/30"

// Estável (neutro)
className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-muted text-muted-foreground ring-1 ring-border"
```

### Badge de preço histórico
```tsx
// Componente: frontend/src/components/BadgePrecoHistorico.tsx
className="inline-flex items-center gap-1.5 rounded-full bg-gold/15 px-2.5 py-1 text-xs font-medium text-gold-foreground ring-1 ring-gold/40"
// Ícone: <Trophy className="h-3.5 w-3.5 text-gold" />
```

### Chip de loja (no card)
```tsx
className="absolute top-3 right-3 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium text-foreground ring-1 ring-border"
```

### Input de formulário
```tsx
className="w-full rounded-xl border border-border bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand/40"
```

### Input de busca (pill)
```tsx
className="w-full rounded-full border border-border bg-card pl-11 pr-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
// Ícone Search posicionado: absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground
```

### Card de estatística (detalhe do produto)
```tsx
className="rounded-2xl border border-border bg-card p-5"
// Label: text-xs uppercase tracking-wider text-muted-foreground
// Valor: font-serif text-xl mt-2
```

---

## 6. Layout e espaçamento

| Contexto | Max width | Padding horizontal |
|----------|-----------|-------------------|
| Dashboard | `max-w-6xl` (1152px) | `px-6` |
| Detalhe do produto | `max-w-5xl` (1024px) | `px-6` |
| Login / Configurações | `max-w-sm` (384px) | `px-6` |

**Header:** `sticky top-0 z-40`, `h-16`, `bg-background/80 backdrop-blur`, `border-b border-border/70`.

**Grid de cards:** `grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`

**Espaçamentos dominantes:** 4px base scale — gaps de 8, 12, 16, 24, 32, 48px.

---

## 7. Iconografia

Biblioteca: **Lucide React** (`lucide-react`). Tamanho padrão `h-4 w-4` ou `h-5 w-5`. Stroke 2. Nunca misturar com outra biblioteca.

| Ícone | Uso |
|-------|-----|
| `Plus` | Adicionar produto |
| `Search` | Campo de busca |
| `RefreshCw` | Atualizar preço (anima com `animate-spin` durante loading) |
| `ArrowDownRight` | Preço caiu |
| `ArrowUpRight` | Preço subiu |
| `Minus` | Preço estável |
| `Trophy` | Preço histórico |
| `Pause` / `Play` | Pausar / retomar monitoramento |
| `Trash2` | Remover produto |
| `ExternalLink` | Link para loja externa |
| `ArrowLeft` | Voltar |
| `Settings` | Preferências |
| `Moon` / `Sun` | Toggle dark mode |
| `LogOut` | Sair |
| `Loader2` | Spinner de loading (`animate-spin`) |
| `Eye` | Feature "monitora qualquer loja" na landing |

**Nunca usar emoji como ícone na UI.** Emoji só em mensagens do Telegram (`📉 📈 🏆`).

---

## 8. Logo

Componente: `frontend/src/components/ZoiouWordmark.tsx`

```tsx
// Wordmark completo (header, footer, login)
<ZoiouWordmark size={26} className="text-ink" />
<span className="text-success font-bold text-2xl leading-none">.</span>

// EyeMark — tile com a face (não usado atualmente na UI, reservado para favicon/app icon)
<ZoiouEyeMark size={52} />
```

O wordmark é `z · 👁 · | · 👁 · u` — os dois "o" do nome viram olhos SVG e o "i" vira nariz. O ponto final é sempre verde (`text-success`).

**Favicon:** `frontend/src/app/icon.svg` — face (olhos + nariz) em tile preto, gerado automaticamente pelo Next.js App Router.

---

## 9. Gráfico de histórico

Componente: `frontend/src/components/GraficoHistorico.tsx` — Recharts `AreaChart`.

- Linha: 2px, `stroke="var(--success)"`
- Área: gradiente vertical `success` de 35% → 0% opacidade
- Grid: linhas dashed em `--border`
- Linha de mínimo histórico: dashed em `--gold`
- Tooltip: card `rounded-xl border border-border bg-card`

---

## 10. Estados vazios

```tsx
// Lista vazia
className="rounded-2xl border border-dashed border-border p-16 text-center"
// Título: font-serif text-2xl text-ink mb-2
// Subtítulo: text-sm text-muted-foreground mb-6

// Sem resultados de busca
// Título: "Nada por aqui."
// Subtítulo: "Tente outro termo ou adicione um novo produto."
```

---

## 11. Texto e voz

- Idioma: **português brasileiro** sempre.
- Pessoa: **"você"** direto. Quente mas sem exagero — nunca hypey.
- Wordmark: sempre **minúsculo** (`zoiou`).
- Labels de UI: sentence case (`Adicionar produto`, não `Adicionar Produto`).
- Overlines: MAIÚSCULO com tracking largo (`SUA LISTA DE DESEJOS`).
- Números monetários: `R$ 1.850,00` — ponto nos milhares, vírgula nos decimais.
- Variação: `-3,6%` queda · `+3,8%` alta · `estável` quando flat.
