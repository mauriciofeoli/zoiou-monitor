"use client";

import { ArrowDownRight, Eye, Loader2, Trophy } from "lucide-react";
import { ZoiouWordmark } from "@/components/ZoiouWordmark";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/lib/supabase";

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

      {/* Coluna esquerda — Landing */}
      <div className="flex flex-col border-b border-border md:border-b-0 md:border-r md:w-[55%] px-10 py-10 md:px-16 md:py-16">
        <div className="flex items-baseline gap-0.5">
          <ZoiouWordmark size={22} className="text-ink" />
          <span className="text-success font-bold text-xl leading-none">.</span>
        </div>

        <div className="flex flex-col justify-center flex-1 py-8 md:py-0 md:mt-20">
          <h1 className="font-serif text-4xl md:text-5xl text-ink leading-tight mb-4">
            Fique de zoio<br />no preço.
          </h1>
          <p className="text-muted-foreground text-base md:text-lg mb-10 max-w-sm">
            Cadastre o produto. A gente monitora.<br className="hidden md:block" />
            Você compra na hora certa.
          </p>

          <ul className="flex flex-col gap-5">
            <li className="flex items-start gap-3">
              <Eye className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
              <span className="text-sm text-foreground">Monitora qualquer loja</span>
            </li>
            <li className="flex items-start gap-3">
              <ArrowDownRight className="h-5 w-5 text-success mt-0.5 shrink-0" />
              <span className="text-sm text-foreground">Avisa quando o preço cai</span>
            </li>
            <li className="flex items-start gap-3">
              <Trophy className="h-5 w-5 mt-0.5 shrink-0" style={{ color: "var(--gold)" }} />
              <span className="text-sm text-foreground">Detecta o menor preço em 12 meses</span>
            </li>
          </ul>
        </div>

        <p className="text-xs text-muted-foreground pt-8">gratuito · sem anúncios</p>
      </div>

      {/* Coluna direita — Login (inalterado) */}
      <div className="flex items-center justify-center md:w-[45%] px-6 py-12">
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
              onClick={() => {
                setModo(modo === "entrar" ? "cadastrar" : "entrar");
                setErro("");
              }}
              className="text-foreground underline underline-offset-2 hover:text-success transition-colors"
            >
              {modo === "entrar" ? "Criar conta" : "Entrar"}
            </button>
          </p>
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
