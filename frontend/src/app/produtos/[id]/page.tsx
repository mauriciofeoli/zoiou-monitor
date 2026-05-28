"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowDownRight,
  ArrowUpRight,
  ExternalLink,
  Loader2,
  Pause,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Header } from "@/components/Header";
import { GraficoHistorico } from "@/components/GraficoHistorico";
import { BadgePrecoHistorico } from "@/components/BadgePrecoHistorico";
import { useAuth } from "@/hooks/use-auth";
import { atualizarAtivo, atualizarAgora, obterHistorico, removerProduto, listarProdutos } from "@/lib/api";
import { formatarBRL, ehPrecoHistoricoLista } from "@/lib/utils";
import type { Produto } from "@/types";

export default function ProdutoDetalhe() {
  const params = useParams();
  const id = params.id as string;
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [atualizando, setAtualizando] = useState(false);

  useEffect(() => {
    if (!carregandoAuth && !usuario) {
      router.push("/login");
    }
  }, [usuario, carregandoAuth, router]);

  const { data: produtos = [], isLoading: carregandoProdutos } = useQuery({
    queryKey: ["produtos"],
    queryFn: listarProdutos,
    enabled: !!usuario,
    refetchInterval: (query) => {
      const produto = (query.state.data as typeof produtos | undefined)?.find((p) => p.id === id);
      return produto?.precoAtual === null ? 5000 : false;
    },
  });

  const { data: historico, isLoading: carregandoHistorico } = useQuery({
    queryKey: ["historico", id],
    queryFn: () => obterHistorico(id),
    enabled: !!usuario,
  });

  const produto = produtos.find((p) => p.id === id);

  async function handleToggleAtivo() {
    if (!produto) return;
    try {
      await atualizarAtivo(id, !produto.ativo);
      await queryClient.invalidateQueries({ queryKey: ["produtos"] });
      toast.success(produto.ativo ? "Monitoramento pausado." : "Monitoramento retomado.");
    } catch {
      toast.error("Não foi possível atualizar o monitoramento.");
    }
  }

  async function handleAtualizarAgora() {
    setAtualizando(true);
    try {
      const produtoAtualizado = await atualizarAgora(id);
      queryClient.setQueryData(["produtos"], (old: Produto[] | undefined) =>
        old ? old.map((p) => (p.id === id ? produtoAtualizado : p)) : [produtoAtualizado],
      );
      await queryClient.invalidateQueries({ queryKey: ["historico", id] });
      toast.success("Preço atualizado!");
    } catch {
      toast.error("Não foi possível capturar o preço agora. Tente novamente.");
    } finally {
      setAtualizando(false);
    }
  }

  async function handleRemover() {
    if (!confirm(`Remover "${produto?.nome}" da sua lista?`)) return;
    try {
      await removerProduto(id);
      await queryClient.invalidateQueries({ queryKey: ["produtos"] });
      toast.success("Produto removido.");
      router.push("/");
    } catch {
      toast.error("Não foi possível remover o produto.");
    }
  }

  if (carregandoAuth || carregandoProdutos || carregandoHistorico) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!produto) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="mx-auto max-w-3xl px-6 py-24 text-center">
          <p className="font-serif text-5xl text-ink">Produto não encontrado.</p>
          <Link
            href="/"
            className="mt-6 inline-flex items-center gap-1 text-sm text-success hover:underline"
          >
            <ArrowLeft className="h-4 w-4" /> voltar para a lista
          </Link>
        </div>
      </div>
    );
  }

  const precoAtual = produto.precoAtual ?? 0;
  const precoAnterior = produto.precoAnterior ?? precoAtual;
  const delta = precoAtual - precoAnterior;
  const pct = precoAnterior > 0 ? (delta / precoAnterior) * 100 : 0;
  const subiu = delta > 0.01;
  const caiu = delta < -0.01;

  const pontosHistorico = historico?.pontos ?? [];
  const precosHistorico = pontosHistorico.map((p) => p.preco);
  const isPrecoHistorico = ehPrecoHistoricoLista(precoAtual, precosHistorico);

  const minH = historico?.precoMinimo ?? (precosHistorico.length ? Math.min(...precosHistorico) : null);
  const maxH = historico?.precoMaximo ?? (precosHistorico.length ? Math.max(...precosHistorico) : null);
  const medH = historico?.precoMedio;
  const variacao = pct;

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-5xl px-6 py-10">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar
        </Link>

        <div className="grid gap-8 md:grid-cols-[260px_1fr] items-start">
          <div className="overflow-hidden rounded-2xl border border-border bg-card">
            {produto.imagem ? (
              <img
                src={produto.imagem}
                alt={produto.nome}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="aspect-square flex items-center justify-center text-muted-foreground text-sm">
                Sem imagem
              </div>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              {produto.loja && (
                <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium">
                  {produto.loja}
                </span>
              )}
              {isPrecoHistorico && <BadgePrecoHistorico />}
            </div>

            <h1 className="font-serif text-4xl md:text-5xl text-ink leading-tight">
              {produto.nome}
            </h1>

            <div className="mt-6 flex items-end gap-4">
              {produto.precoAtual != null ? (
                <>
                  <div className="font-serif text-6xl text-ink leading-none">
                    {formatarBRL(produto.precoAtual)}
                  </div>
                  {(subiu || caiu) && (
                    <div
                      className={[
                        "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-medium mb-2",
                        caiu && "bg-success/15 text-success ring-1 ring-success/30",
                        subiu && "bg-destructive/15 text-destructive ring-1 ring-destructive/30",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      {caiu ? (
                        <ArrowDownRight className="h-4 w-4" />
                      ) : (
                        <ArrowUpRight className="h-4 w-4" />
                      )}
                      {formatarBRL(Math.abs(delta))} ({pct > 0 ? "+" : ""}
                      {pct.toFixed(1)}%)
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground italic">Aguardando primeira captura...</p>
              )}
            </div>

            {produto.precoAnterior != null && produto.precoAtual != null && (delta > 0.01 || delta < -0.01) && (
              <p className="mt-2 text-sm text-muted-foreground">
                anteriormente{" "}
                <span className="line-through">{formatarBRL(produto.precoAnterior)}</span>
              </p>
            )}

            <div className="mt-6 flex flex-wrap gap-2">
              <a
                href={produto.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:bg-foreground/90"
              >
                Ver na {produto.loja || "loja"} <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <button
                onClick={handleAtualizarAgora}
                disabled={atualizando}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm hover:bg-secondary disabled:opacity-60"
              >
                {atualizando ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {atualizando ? "Capturando..." : "Atualizar agora"}
              </button>
              <button
                onClick={handleToggleAtivo}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm hover:bg-secondary"
              >
                {produto.ativo ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {produto.ativo ? "Pausar" : "Retomar"}
              </button>
              <button
                onClick={handleRemover}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm text-destructive hover:bg-destructive/5"
              >
                <Trash2 className="h-4 w-4" /> Remover
              </button>
            </div>
          </div>
        </div>

        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Mínimo (12m)", valor: minH != null ? formatarBRL(minH) : "—", accent: "text-gold" },
            { label: "Máximo (12m)", valor: maxH != null ? formatarBRL(maxH) : "—" },
            { label: "Média (12m)", valor: medH != null ? formatarBRL(medH) : "—" },
            {
              label: "Variação",
              valor: produto.precoAtual != null ? `${variacao > 0 ? "+" : ""}${variacao.toFixed(1)}%` : "—",
              accent: caiu ? "text-success" : subiu ? "text-destructive" : "",
            },
          ].map((s) => (
            <div key={s.label} className="rounded-2xl border border-border bg-card p-5">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</div>
              <div className={`font-serif text-2xl mt-2 ${s.accent ?? ""}`}>{s.valor}</div>
            </div>
          ))}
        </div>

        <section className="mt-8 rounded-2xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif text-2xl text-ink">Histórico de preços</h2>
            <span className="text-xs text-muted-foreground">
              {pontosHistorico.length} registro{pontosHistorico.length !== 1 ? "s" : ""}
            </span>
          </div>
          <GraficoHistorico dados={pontosHistorico} />
        </section>
      </main>
    </div>
  );
}
