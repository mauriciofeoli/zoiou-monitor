"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2, Plus, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { CardProduto } from "@/components/CardProduto";
import { AdicionarProdutoModal } from "@/components/AdicionarProdutoModal";
import { useAuth } from "@/hooks/use-auth";
import { listarProdutos } from "@/lib/api";
import { formatarBRL } from "@/lib/utils";

export default function Dashboard() {
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const [busca, setBusca] = useState("");
  const [modalAberto, setModalAberto] = useState(false);

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
    if (!q) return produtos;
    return produtos.filter(
      (p) =>
        p.nome.toLowerCase().includes(q) || (p.loja ?? "").toLowerCase().includes(q),
    );
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
              produto{ativos.length !== 1 ? "s" : ""} em{" "}
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

          <button
            type="button"
            onClick={() => setModalAberto(true)}
            className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background hover:bg-foreground/90 transition-colors shadow-sm"
          >
            <Plus className="h-4 w-4" /> Adicionar produto
          </button>
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
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtrados.map((p) => (
              <CardProduto key={p.id} produto={p} />
            ))}
          </div>
        )}
      </main>

      <footer className="border-t border-border mt-16">
        <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <p>
            <span className="font-serif text-base text-foreground">zoiou</span> · seu olho nos
            preços
          </p>
          <p>Sem spam · sem afiliados · sem distrações</p>
        </div>
      </footer>

      <AdicionarProdutoModal aberto={modalAberto} fechar={() => setModalAberto(false)} />
    </div>
  );
}
