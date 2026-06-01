"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, MessageCircle, Send, Unlink } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Header } from "@/components/Header";
import { useAuth } from "@/hooks/use-auth";
import { atualizarPreferencias, iniciarConexaoTelegram, obterPerfil, testarTelegram } from "@/lib/api";

export default function Configuracoes() {
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [salvando, setSalvando] = useState(false);
  const [conectando, setConectando] = useState(false);
  const [testando, setTestando] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!carregandoAuth && !usuario) {
      router.push("/login");
    }
  }, [usuario, carregandoAuth, router]);

  const { data: perfil, isLoading } = useQuery({
    queryKey: ["perfil"],
    queryFn: obterPerfil,
    enabled: !!usuario,
  });

  const [notifAtiva, setNotifAtiva] = useState(false);

  useEffect(() => {
    if (perfil) {
      setNotifAtiva(perfil.notifTelegram);
    }
  }, [perfil]);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  async function handleConectar() {
    setConectando(true);
    try {
      const { url } = await iniciarConexaoTelegram();
      window.open(url, "_blank");

      // polling: detecta quando telegram_id aparecer no perfil
      let tentativas = 0;
      pollingRef.current = setInterval(async () => {
        tentativas++;
        await queryClient.invalidateQueries({ queryKey: ["perfil"] });
        const atualizado = queryClient.getQueryData<typeof perfil>(["perfil"]);
        if (atualizado?.telegramId || tentativas >= 30) {
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
          setConectando(false);
          if (atualizado?.telegramId) {
            toast.success("Telegram conectado!");
          }
        }
      }, 2000);
    } catch {
      toast.error("Não foi possível gerar o link. Tente novamente.");
      setConectando(false);
    }
  }

  async function handleDesconectar() {
    try {
      await atualizarPreferencias({ notifTelegram: false, telegramId: null });
      await queryClient.invalidateQueries({ queryKey: ["perfil"] });
      toast.success("Telegram desconectado.");
    } catch {
      toast.error("Não foi possível desconectar.");
    }
  }

  async function handleToggleNotif(ativo: boolean) {
    setNotifAtiva(ativo);
    try {
      await atualizarPreferencias({ notifTelegram: ativo });
      await queryClient.invalidateQueries({ queryKey: ["perfil"] });
    } catch {
      setNotifAtiva(!ativo);
      toast.error("Não foi possível salvar.");
    }
  }

  async function handleSalvar() {
    setSalvando(true);
    try {
      await atualizarPreferencias({ notifTelegram: notifAtiva });
      await queryClient.invalidateQueries({ queryKey: ["perfil"] });
      toast.success("Preferências salvas!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Não foi possível salvar as preferências.";
      toast.error(msg);
    } finally {
      setSalvando(false);
    }
  }

  if (carregandoAuth || isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  const telegramConectado = !!perfil?.telegramId;

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-sm uppercase tracking-[0.18em] text-muted-foreground mb-3">
          Preferências
        </p>
        <h1 className="font-serif text-5xl text-ink leading-tight">
          Como você quer ser avisado?
        </h1>
        <p className="mt-3 text-muted-foreground max-w-xl">
          Sem spam. A gente só te avisa quando o preço realmente muda — ou quando algo bate o
          mínimo histórico dos últimos 12 meses.
        </p>

        <div className="mt-10 space-y-3">
          {/* Telegram */}
          <div className="rounded-2xl border border-border bg-card p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                <Send className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <h3 className="font-serif text-xl text-ink">Telegram</h3>
                    {telegramConectado && (
                      <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-xs text-success">
                        <CheckCircle2 className="h-3 w-3" />
                        Conectado
                      </span>
                    )}
                  </div>
                  {telegramConectado && (
                    <button
                      type="button"
                      role="switch"
                      aria-checked={notifAtiva}
                      onClick={() => handleToggleNotif(!notifAtiva)}
                      className={[
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors",
                        notifAtiva ? "bg-success" : "bg-muted",
                      ].join(" ")}
                    >
                      <span
                        className={[
                          "inline-block h-5 w-5 translate-y-0.5 transform rounded-full bg-background shadow transition-transform",
                          notifAtiva ? "translate-x-[22px]" : "translate-x-0.5",
                        ].join(" ")}
                      />
                    </button>
                  )}
                </div>

                <p className="mt-1 text-sm text-muted-foreground">
                  Mensagens instantâneas com link direto para a loja.
                </p>

                {!telegramConectado && (
                  <button
                    type="button"
                    disabled={conectando}
                    onClick={handleConectar}
                    className="mt-3 inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors"
                  >
                    {conectando ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Aguardando conexão...
                      </>
                    ) : (
                      "Conectar Telegram"
                    )}
                  </button>
                )}

                {telegramConectado && (
                  <div className="mt-3 flex items-center gap-2">
                    <button
                      type="button"
                      disabled={testando}
                      onClick={async () => {
                        setTestando(true);
                        try {
                          await testarTelegram();
                          toast.success("Mensagem de teste enviada!");
                        } catch {
                          toast.error("Falha ao enviar. Tente reconectar.");
                        } finally {
                          setTestando(false);
                        }
                      }}
                      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-sm hover:bg-card disabled:opacity-60 transition-colors"
                    >
                      {testando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                      Testar
                    </button>
                    <button
                      type="button"
                      onClick={handleDesconectar}
                      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:bg-card hover:text-foreground transition-colors"
                    >
                      <Unlink className="h-3.5 w-3.5" />
                      Desconectar
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* WhatsApp — em breve */}
          <div className="rounded-2xl border border-border bg-card p-5 opacity-50 cursor-not-allowed">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                <MessageCircle className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-serif text-xl text-ink">WhatsApp</h3>
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">em breve</span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">Alertas no seu número, sem precisar abrir o app.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between rounded-2xl bg-secondary p-5">
          <div>
            <p className="font-medium text-foreground">Modo silencioso</p>
            <p className="text-sm text-muted-foreground">
              Consultar tudo só pelo dashboard, sem notificações.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleToggleNotif(false)}
            className="rounded-full border border-border bg-background px-4 py-2 text-sm hover:bg-card"
          >
            Ativar
          </button>
        </div>

        {telegramConectado && (
          <div className="mt-8 flex justify-end">
            <button
              onClick={handleSalvar}
              disabled={salvando}
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-6 py-3 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors"
            >
              {salvando && <Loader2 className="h-4 w-4 animate-spin" />}
              {salvando ? "Salvando..." : "Salvar preferências"}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
