"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, RefreshCw, Search } from "lucide-react";
import { ZoiouWordmark } from "@/components/ZoiouWordmark";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { CardProduto } from "@/components/CardProduto";
import { AdicionarProdutoModal } from "@/components/AdicionarProdutoModal";
import { useAuth } from "@/hooks/use-auth";
import { atualizarTodos, listarProdutos } from "@/lib/api";
import { cn, formatarBRL } from "@/lib/utils";

const COOLDOWN_MS = 3 * 60 * 1000;
const STORAGE_KEY = "zoiou_atualizar_todos_ts";

export default function Dashboard() {
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [busca, setBusca] = useState("");
  const [modalAberto, setModalAberto] = useState(false);
  const [atualizandoTodos, setAtualizandoTodos] = useState(false);
  const [cooldownRestante, setCooldownRestante] = useState(0);

  useEffect(() => {
    const ts = Number(localStorage.getItem(STORAGE_KEY)) || 0;
    const restante = Math.max(0, COOLDOWN_MS - (Date.now() - ts));
    if (restante > 0) setCooldownRestante(Math.ceil(restante / 1000));
  }, []);

  useEffect(() => {
    if (cooldownRestante <= 0) return;
    const id = setInterval(() => {
      setCooldownRestante((s) => (s <= 1 ? 0 : s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [cooldownRestante]);

  async function handleAtualizarTodos() {
    if (atualizandoTodos || cooldownRestante > 0) return;
    setAtualizandoTodos(true);
    try {
      await atualizarTodos();
      localStorage.setItem(STORAGE_KEY, String(Date.now()));
      setCooldownRestante(Math.ceil(COOLDOWN_MS / 1000));
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["produtos"] }), 4000);
    } finally {
      setAtualizandoTodos(false);
    }
  }

  useEffect(() => {
    if (!carregandoAuth && !usuario) {
      router.push("/login");
    }
  }, [usuario, carregandoAuth, router]);

  const { data: produtos = [], isLoading } = useQuery({
    queryKey: ["produtos"],
    queryFn: listarProdutos,
    enabled: !!usuario,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.some((p) => p.precoAtual === null) ? 5000 : false;
    },
  });

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    const lista = q
      ? produtos.filter(
          (p) => p.nome.toLowerCase().includes(q) || (p.loja ?? "").toLowerCase().includes(q),
        )
      : [...produtos];

    return lista.sort((a, b) => {
      // Pausados sempre no fundo
      if (a.ativo !== b.ativo) return a.ativo ? -1 : 1;

      // Sem preço no fundo (acima dos pausados)
      const semPrecoA = a.precoAtual === null;
      const semPrecoB = b.precoAtual === null;
      if (semPrecoA !== semPrecoB) return semPrecoA ? 1 : -1;

      const deltaA = (a.precoAtual ?? 0) - (a.precoAnterior ?? a.precoAtual ?? 0);
      const deltaB = (b.precoAtual ?? 0) - (b.precoAnterior ?? b.precoAtual ?? 0);
      const pctA = a.precoAnterior ? (deltaA / a.precoAnterior) * 100 : 0;
      const pctB = b.precoAnterior ? (deltaB / b.precoAnterior) * 100 : 0;

      // 0 = queda, 1 = estável, 2 = alta
      const catA = deltaA < -0.01 ? 0 : deltaA > 0.01 ? 2 : 1;
      const catB = deltaB < -0.01 ? 0 : deltaB > 0.01 ? 2 : 1;

      if (catA !== catB) return catA - catB;

      // Dentro de quedas: maior desconto percentual primeiro
      if (catA === 0) return pctA - pctB;

      return 0;
    });
  }, [busca, produtos]);

  const ativos = produtos.filter((p) => p.ativo);
  const lojas = new Set(produtos.map((p) => p.loja).filter(Boolean));
  const economia = produtos.reduce(
    (acc, p) =>
      acc + Math.max(0, (p.precoAnterior ?? p.precoAtual ?? 0) - (p.precoAtual ?? 0)),
    0,
  );

  if (carregandoAuth || (!usuario && !carregandoAuth)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-6xl px-6 py-12">
        <section className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-10">
          <div className="max-w-2xl">
            <p className="text-sm uppercase tracking-[0.18em] text-muted-foreground mb-3">
              Sua lista de desejos
            </p>
            <h1 className="font-serif text-xl md:text-2xl text-ink leading-snug">
              De olho em{" "}
              <span className="text-success">{ativos.length}</span>{" "}
              produto{ativos.length !== 1 ? "s" : ""} de{" "}
              <span>{lojas.size}</span>{" "}
              loja{lojas.size !== 1 ? "s" : ""}.
            </h1>
            {economia > 0 && (
              <p className="mt-4 text-muted-foreground max-w-md">
                Você já economizou{" "}
                <span className="text-foreground font-medium">{formatarBRL(economia)}</span> desde
                que começou a monitorar.
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            {produtos.length > 0 && (
              <button
                type="button"
                onClick={handleAtualizarTodos}
                disabled={atualizandoTodos || cooldownRestante > 0}
                className="inline-flex items-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-medium hover:bg-card transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={cn("h-4 w-4", atualizandoTodos && "animate-spin")} />
                {atualizandoTodos
                  ? "Atualizando..."
                  : cooldownRestante > 0
                  ? `Atualizar todos (${Math.floor(cooldownRestante / 60)}:${String(cooldownRestante % 60).padStart(2, "0")})`
                  : "Atualizar todos"}
              </button>
            )}
            <button
              type="button"
              onClick={() => setModalAberto(true)}
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background hover:bg-foreground/90 transition-colors shadow-sm"
            >
              <Plus className="h-4 w-4" /> Adicionar produto
            </button>
          </div>
        </section>

        {produtos.length > 0 && (
          <div className="relative mb-8">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nome ou loja..."
              className="w-full rounded-full border border-border bg-card pl-11 pr-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : filtrados.length === 0 && produtos.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-16 text-center">
            <p className="font-serif text-2xl text-ink mb-2">Sua lista está vazia.</p>
            <p className="text-sm text-muted-foreground mb-6">
              Adicione a URL de um produto para começar a monitorar.
            </p>
            <button
              type="button"
              onClick={() => setModalAberto(true)}
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background hover:bg-foreground/90"
            >
              <Plus className="h-4 w-4" /> Adicionar produto
            </button>
          </div>
        ) : filtrados.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-16 text-center">
            <p className="font-serif text-2xl text-ink mb-2">Nada por aqui.</p>
            <p className="text-sm text-muted-foreground">
              Tente outro termo ou adicione um novo produto.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtrados.map((p) => (
              <CardProduto key={p.id} produto={p} />
            ))}
          </div>
        )}
      </main>

      <footer className="border-t border-border mt-16">
        <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p className="flex items-center gap-1">
            <ZoiouWordmark size={16} className="text-foreground" />
            <span className="text-success font-bold">.</span>
            <span>· seu olho nos preços</span>
          </p>
          <div className="flex items-center gap-4">
            <a
              href="https://discord.gg/ASDrPymTfH"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-foreground transition-colors"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057c.002.022.015.043.032.054a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
              </svg>
              Discord
            </a>
            <a
              href="https://t.me/zoioumonitor"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-foreground transition-colors"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
              </svg>
              Telegram
            </a>
          </div>
        </div>
      </footer>

      <AdicionarProdutoModal aberto={modalAberto} fechar={() => setModalAberto(false)} />
    </div>
  );
}
