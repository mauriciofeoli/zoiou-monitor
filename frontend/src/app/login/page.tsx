"use client";

import { ArrowDownRight, ArrowUpRight, Loader2, Minus, Trophy } from "lucide-react";
import { ZoiouWordmark } from "@/components/ZoiouWordmark";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/lib/supabase";

const MOCK_PRODUTOS = [
  {
    nome: "Placa de Vídeo RTX 4070 Super | Kabum",
    loja: "kabum.com.br",
    preco: "R$ 3.199",
    anterior: "R$ 3.699",
    badge: "queda" as const,
    pct: "-13,5%",
    cor: "bg-muted",
  },
  {
    nome: "SSD Samsung 870 EVO 1TB | Terabyte",
    loja: "terabyteshop.com.br",
    preco: "R$ 289",
    anterior: null,
    badge: "historico" as const,
    pct: null,
    cor: "bg-muted",
  },
  {
    nome: "Monitor LG 27\" IPS 144Hz | Pichau",
    loja: "pichau.com.br",
    preco: "R$ 1.799",
    anterior: "R$ 1.750",
    badge: "alta" as const,
    pct: "+2,8%",
    cor: "bg-muted",
  },
];

function PreviewChip({ badge, pct }: { badge: "queda" | "alta" | "historico" | "estavel"; pct: string | null }) {
  if (badge === "historico") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-gold/15 ring-1 ring-gold/30" style={{ color: "var(--gold)" }}>
        <Trophy className="h-3 w-3" />Preço histórico
      </span>
    );
  }
  if (badge === "queda") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-success/15 text-success ring-1 ring-success/30">
        <ArrowDownRight className="h-3 w-3" />{pct}
      </span>
    );
  }
  if (badge === "alta") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-destructive/15 text-destructive ring-1 ring-destructive/30">
        <ArrowUpRight className="h-3 w-3" />{pct}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-muted text-muted-foreground ring-1 ring-border">
      <Minus className="h-3 w-3" />estável
    </span>
  );
}

export default function Login() {
  const { usuario, carregando } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [modo, setModo] = useState<"entrar" | "cadastrar">("entrar");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!carregando && usuario) {
      router.push("/");
    }
  }, [usuario, carregando, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      if (modo === "entrar") {
        const { error } = await supabase.auth.signInWithPassword({ email, password: senha });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({ email, password: senha });
        if (error) throw error;
      }
      router.push("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao autenticar.";
      setErro(traduzirErroSupabase(msg));
    } finally {
      setEnviando(false);
    }
  }

  if (carregando) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col md:flex-row">

      {/* Coluna direita — Login — order-1 mobile (aparece primeiro) */}
      <div className="order-1 md:order-2 flex items-center justify-center md:w-1/2 px-6 py-12 border-b border-border/40 md:border-b-0">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center gap-2">
            <span className="flex items-baseline gap-0.5">
              <ZoiouWordmark size={32} className="text-ink" />
              <span className="text-success font-bold text-3xl leading-none">.</span>
            </span>
            <p className="text-sm text-muted-foreground">seu olho nos preços</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                E-mail
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="voce@exemplo.com"
                className="w-full rounded-xl border border-border bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label htmlFor="senha" className="block text-sm font-medium text-foreground mb-1.5">
                Senha
              </label>
              <input
                id="senha"
                type="password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="••••••••"
                minLength={6}
                className="w-full rounded-xl border border-border bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {erro && (
              <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {erro}
              </p>
            )}

            <button
              type="submit"
              disabled={enviando}
              className="w-full rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
            >
              {enviando && <Loader2 className="h-4 w-4 animate-spin" />}
              {modo === "entrar" ? "Entrar" : "Criar conta"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            {modo === "entrar" ? "Não tem conta?" : "Já tem conta?"}{" "}
            <button
              type="button"
              onClick={() => { setModo(modo === "entrar" ? "cadastrar" : "entrar"); setErro(""); }}
              className="text-foreground underline underline-offset-2 hover:text-success transition-colors"
            >
              {modo === "entrar" ? "Criar conta" : "Entrar"}
            </button>
          </p>
        </div>
      </div>

      {/* Coluna esquerda — Preview — order-2 mobile (aparece depois) */}
      <div className="order-2 md:order-1 flex flex-col md:w-1/2 bg-muted/50 border-r border-border/40 overflow-hidden">
        {/* mini header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 bg-background/60 backdrop-blur">
          <div className="flex items-baseline gap-0.5">
            <ZoiouWordmark size={16} className="text-ink" />
            <span className="text-success font-bold text-sm leading-none">.</span>
          </div>
          <span className="text-xs text-muted-foreground uppercase tracking-widest">Sua lista de desejos</span>
        </div>

        {/* cards mock */}
        <div className="flex flex-col gap-3 p-6 flex-1">
          {MOCK_PRODUTOS.map((p, i) => (
            <div
              key={i}
              className="rounded-2xl border border-border bg-card p-4 flex items-start gap-4"
            >
              <div className="h-14 w-14 rounded-xl bg-muted shrink-0 flex items-center justify-center">
                <span className="text-xl">📦</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-muted-foreground mb-0.5">{p.loja}</p>
                <p className="text-sm font-medium text-foreground leading-snug line-clamp-1 mb-2">{p.nome}</p>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-serif text-lg text-ink leading-none">{p.preco}</span>
                  {p.anterior && (
                    <span className="text-xs text-muted-foreground line-through">{p.anterior}</span>
                  )}
                  <PreviewChip badge={p.badge} pct={p.pct} />
                </div>
              </div>
            </div>
          ))}

          {/* mensagem de economia */}
          <p className="text-xs text-muted-foreground text-center pt-2">
            Você já economizou <span className="text-foreground font-medium">R$ 500</span> desde que começou a monitorar.
          </p>
        </div>

        <div className="px-6 py-4 border-t border-border/40 text-center">
          <p className="text-xs text-muted-foreground">gratuito · sem anúncios · sem afiliados</p>
        </div>
      </div>

    </div>
  );
}

function traduzirErroSupabase(msg: string): string {
  if (msg.includes("Invalid login credentials")) return "E-mail ou senha incorretos.";
  if (msg.includes("Email not confirmed")) return "Confirme seu e-mail antes de entrar.";
  if (msg.includes("User already registered")) return "E-mail já cadastrado. Tente entrar.";
  if (msg.includes("Password should be at least")) return "A senha deve ter pelo menos 6 caracteres.";
  return msg;
}
