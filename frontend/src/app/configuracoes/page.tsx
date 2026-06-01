"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, MessageCircle, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Header } from "@/components/Header";
import { useAuth } from "@/hooks/use-auth";
import { atualizarPreferencias, obterPerfil, testarTelegram } from "@/lib/api";

interface Canal {
  id: "telegram";
  nome: string;
  descricao: string;
  icone: React.ComponentType<{ className?: string }>;
  placeholder: string;
}

const canais: Canal[] = [
  {
    id: "telegram",
    nome: "Telegram",
    descricao: "Mensagens instantâneas com link direto para a loja.",
    icone: Send,
    placeholder: "@seu_usuario ou ID numérico",
  },
];

export default function Configuracoes() {
  const { usuario, carregando: carregandoAuth } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [salvando, setSalvando] = useState(false);
  const [testando, setTestando] = useState(false);

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

  const [ativos, setAtivos] = useState<Record<Canal["id"], boolean>>({
    telegram: false,
  });
  const [valores, setValores] = useState<Record<Canal["id"], string>>({
    telegram: "",
  });

  useEffect(() => {
    if (perfil) {
      setAtivos({ telegram: perfil.notifTelegram });
      setValores({ telegram: perfil.telegramId ?? "" });
    }
  }, [perfil, usuario]);

  async function handleSalvar() {
    setSalvando(true);
    try {
      await atualizarPreferencias({
        notifTelegram: ativos.telegram,
        telegramId: ativos.telegram ? valores.telegram || null : null,
      });
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
          {canais.map((canal) => {
            const Icon = canal.icone;
            const ativo = ativos[canal.id];
            return (
              <div
                key={canal.id}
                className="rounded-2xl border border-border bg-card p-5 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="font-serif text-xl text-ink">{canal.nome}</h3>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={ativo}
                        onClick={() => setAtivos((a) => ({ ...a, [canal.id]: !a[canal.id] }))}
                        className={[
                          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors",
                          ativo ? "bg-success" : "bg-muted",
                        ].join(" ")}
                      >
                        <span
                          className={[
                            "inline-block h-5 w-5 translate-y-0.5 transform rounded-full bg-background shadow transition-transform",
                            ativo ? "translate-x-[22px]" : "translate-x-0.5",
                          ].join(" ")}
                        />
                      </button>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{canal.descricao}</p>
                    {ativo && (
                      <div className="mt-3 flex gap-2">
                        <input
                          value={valores[canal.id]}
                          onChange={(e) => setValores((v) => ({ ...v, [canal.id]: e.target.value }))}
                          placeholder={canal.placeholder}
                          className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                        {valores[canal.id] && (
                          <button
                            type="button"
                            disabled={testando}
                            onClick={async () => {
                              setTestando(true);
                              try {
                                await testarTelegram();
                                toast.success("Mensagem de teste enviada!");
                              } catch {
                                toast.error("Falha ao enviar. Verifique o ID e tente novamente.");
                              } finally {
                                setTestando(false);
                              }
                            }}
                            className="shrink-0 rounded-lg border border-border bg-background px-3 py-2 text-sm hover:bg-card disabled:opacity-60 transition-colors"
                          >
                            {testando ? <Loader2 className="h-4 w-4 animate-spin" /> : "Testar"}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

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
            onClick={() => setAtivos({ telegram: false })}
            className="rounded-full border border-border bg-background px-4 py-2 text-sm hover:bg-card"
          >
            Ativar
          </button>
        </div>

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
      </main>
    </div>
  );
}
