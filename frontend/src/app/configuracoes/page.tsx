"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, CheckCircle2, Loader2, Send, Unlink } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Header } from "@/components/Header";
import { useAuth } from "@/hooks/use-auth";
import {
  atualizarPreferencias,
  iniciarConexaoTelegram,
  obterPerfil,
  removerPushSubscription,
  salvarPushSubscription,
  testarTelegram,
} from "@/lib/api";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "";

function urlBase64ToUint8Array(base64: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const buf = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  return buf;
}

export default function Configuracoes() {
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [conectando, setConectando] = useState(false);
  const [testando, setTestando] = useState(false);
  const [ativandoPush, setAtivandoPush] = useState(false);
  const [pushAtivo, setPushAtivo] = useState(false);
  const [pushSuportado, setPushSuportado] = useState(true);

  useEffect(() => {
    if (!carregandoAuth && !usuario) router.push("/login");
  }, [usuario, carregandoAuth, router]);

  const { data: perfil, isLoading } = useQuery({
    queryKey: ["perfil"],
    queryFn: obterPerfil,
    enabled: !!usuario,
  });

  // Verifica estado atual do push ao carregar
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setPushSuportado(false);
      return;
    }
    navigator.serviceWorker.register("/sw.js").then((reg) => {
      reg.pushManager.getSubscription().then((sub) => {
        setPushAtivo(!!sub);
      });
    });
  }, []);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  async function handleConectarTelegram() {
    setConectando(true);
    try {
      const { url } = await iniciarConexaoTelegram();
      window.open(url, "_blank");

      let tentativas = 0;
      pollingRef.current = setInterval(async () => {
        tentativas++;
        await queryClient.invalidateQueries({ queryKey: ["perfil"] });
        const atualizado = queryClient.getQueryData<typeof perfil>(["perfil"]);
        if (atualizado?.telegramId || tentativas >= 30) {
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
          setConectando(false);
          if (atualizado?.telegramId) toast.success("Telegram conectado!");
        }
      }, 2000);
    } catch {
      toast.error("Não foi possível gerar o link. Tente novamente.");
      setConectando(false);
    }
  }

  async function handleDesconectarTelegram() {
    try {
      await atualizarPreferencias({ notifTelegram: false, telegramId: null });
      await queryClient.invalidateQueries({ queryKey: ["perfil"] });
      toast.success("Telegram desconectado.");
    } catch {
      toast.error("Não foi possível desconectar.");
    }
  }

  async function handleToggleTelegram(ativo: boolean) {
    try {
      await atualizarPreferencias({ notifTelegram: ativo });
      await queryClient.invalidateQueries({ queryKey: ["perfil"] });
    } catch {
      toast.error("Não foi possível salvar.");
    }
  }

  async function handleAtivarPush() {
    setAtivandoPush(true);
    try {
      const permissao = await Notification.requestPermission();
      if (permissao !== "granted") {
        toast.error("Permissão negada. Habilite notificações nas configurações do browser.");
        return;
      }
      const reg = await navigator.serviceWorker.register("/sw.js");
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      });
      await salvarPushSubscription(sub);
      setPushAtivo(true);
      toast.success("Notificações do site ativadas!");
    } catch {
      toast.error("Não foi possível ativar as notificações.");
    } finally {
      setAtivandoPush(false);
    }
  }

  async function handleDesativarPush() {
    try {
      const reg = await navigator.serviceWorker.getRegistration("/sw.js");
      if (reg) {
        const sub = await reg.pushManager.getSubscription();
        if (sub) await sub.unsubscribe();
      }
      await removerPushSubscription();
      setPushAtivo(false);
      toast.success("Notificações do site desativadas.");
    } catch {
      toast.error("Não foi possível desativar.");
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
                      aria-checked={perfil?.notifTelegram}
                      onClick={() => handleToggleTelegram(!perfil?.notifTelegram)}
                      className={[
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors",
                        perfil?.notifTelegram ? "bg-success" : "bg-muted",
                      ].join(" ")}
                    >
                      <span
                        className={[
                          "inline-block h-5 w-5 translate-y-0.5 transform rounded-full bg-background shadow transition-transform",
                          perfil?.notifTelegram ? "translate-x-[22px]" : "translate-x-0.5",
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
                    onClick={handleConectarTelegram}
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
                      onClick={handleDesconectarTelegram}
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

          {/* Push do browser */}
          <div className={["rounded-2xl border border-border bg-card p-5 transition-colors", !pushSuportado ? "opacity-50" : ""].join(" ")}>
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                {pushAtivo ? <Bell className="h-5 w-5" /> : <BellOff className="h-5 w-5" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <h3 className="font-serif text-xl text-ink">Notificações do site</h3>
                    {pushAtivo && (
                      <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-xs text-success">
                        <CheckCircle2 className="h-3 w-3" />
                        Ativo
                      </span>
                    )}
                    {!pushSuportado && (
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                        não suportado
                      </span>
                    )}
                  </div>
                </div>

                <p className="mt-1 text-sm text-muted-foreground">
                  Alertas direto no browser, mesmo com o site fechado.
                </p>

                {pushSuportado && !pushAtivo && (
                  <button
                    type="button"
                    disabled={ativandoPush}
                    onClick={handleAtivarPush}
                    className="mt-3 inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors"
                  >
                    {ativandoPush ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    {ativandoPush ? "Ativando..." : "Ativar notificações"}
                  </button>
                )}

                {pushSuportado && pushAtivo && (
                  <button
                    type="button"
                    onClick={handleDesativarPush}
                    className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:bg-card hover:text-foreground transition-colors"
                  >
                    <BellOff className="h-3.5 w-3.5" />
                    Desativar
                  </button>
                )}
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
            onClick={async () => {
              try {
                await atualizarPreferencias({ notifTelegram: false });
                await queryClient.invalidateQueries({ queryKey: ["perfil"] });
                if (pushAtivo) await handleDesativarPush();
                toast.success("Modo silencioso ativado.");
              } catch {
                toast.error("Não foi possível salvar.");
              }
            }}
            className="rounded-full border border-border bg-background px-4 py-2 text-sm hover:bg-card"
          >
            Ativar
          </button>
        </div>
      </main>
    </div>
  );
}
