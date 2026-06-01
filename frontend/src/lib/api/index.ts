import { supabase } from "@/lib/supabase";
import type {
  HistoricoProduto,
  PontoHistorico,
  PreferenciasUpdate,
  Produto,
  Usuario,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://zoiou-monitor-production.up.railway.app";

async function tokenAtual(): Promise<string> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("Não autenticado.");
  return token;
}

async function get<T>(path: string): Promise<T> {
  const token = await tokenAtual();
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Erro ${res.status}`);
  }
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const token = await tokenAtual();
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b?.error?.message ?? `Erro ${res.status}`);
  }
  return res.json();
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const token = await tokenAtual();
  const res = await fetch(`${API_URL}${path}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b?.error?.message ?? `Erro ${res.status}`);
  }
  return res.json();
}

async function del(path: string): Promise<void> {
  const token = await tokenAtual();
  const res = await fetch(`${API_URL}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 204) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b?.error?.message ?? `Erro ${res.status}`);
  }
}

// Mapeia snake_case da API para camelCase do frontend
function mapearProduto(p: Record<string, unknown>): Produto {
  return {
    id: p.id as string,
    nome: p.nome as string,
    url: p.url as string,
    loja: (p.loja as string) ?? "",
    imagem: (p.imagem as string) ?? "",
    precoAtual: p.preco_atual != null ? Number(p.preco_atual) : null,
    precoAnterior: p.preco_anterior != null ? Number(p.preco_anterior) : null,
    ativo: p.ativo as boolean,
    monitorandoHaDias: (p.monitorando_ha_dias as number) ?? 0,
  };
}

function mapearHistorico(h: Record<string, unknown>): HistoricoProduto {
  const pontos = ((h.pontos as Record<string, unknown>[]) ?? []).map(
    (p): PontoHistorico => ({
      data: p.capturado_em as string,
      preco: Number(p.preco),
    }),
  );
  return {
    produtoId: h.produto_id as string,
    pontos,
    precoMinimo: h.preco_minimo != null ? Number(h.preco_minimo) : null,
    precoMaximo: h.preco_maximo != null ? Number(h.preco_maximo) : null,
    precoMedio: h.preco_medio != null ? Number(h.preco_medio) : null,
  };
}

function mapearUsuario(u: Record<string, unknown>): Usuario {
  return {
    id: u.id as string,
    email: u.email as string,
    telegramId: (u.telegram_id as string | null) ?? null,
    whatsapp: (u.whatsapp as string | null) ?? null,
    notifTelegram: (u.notif_telegram as boolean) ?? false,
    notifWhatsapp: (u.notif_whatsapp as boolean) ?? false,
    notifEmail: (u.notif_email as boolean) ?? true,
  };
}

export async function atualizarAgora(id: string): Promise<Produto> {
  const dado = await post<Record<string, unknown>>(`/api/produtos/${id}/atualizar`, {});
  return mapearProduto(dado);
}

export async function atualizarTodos(): Promise<{ iniciado: boolean; total: number }> {
  return post<{ iniciado: boolean; total: number }>("/api/produtos/atualizar-todos", {});
}

export async function listarProdutos(): Promise<Produto[]> {
  const dados = await get<Record<string, unknown>[]>("/api/produtos");
  return dados.map(mapearProduto);
}

export async function adicionarProduto(url: string): Promise<Produto> {
  const dado = await post<Record<string, unknown>>("/api/produtos", { url });
  return mapearProduto(dado);
}

export async function removerProduto(id: string): Promise<void> {
  await del(`/api/produtos/${id}`);
}

export async function atualizarAtivo(id: string, ativo: boolean): Promise<Produto> {
  const dado = await patch<Record<string, unknown>>(`/api/produtos/${id}`, { ativo });
  return mapearProduto(dado);
}

export async function obterHistorico(produtoId: string): Promise<HistoricoProduto> {
  const dado = await get<Record<string, unknown>>(`/api/produtos/${produtoId}/historico`);
  return mapearHistorico(dado);
}

export async function obterPerfil(): Promise<Usuario> {
  const dado = await get<Record<string, unknown>>("/api/usuarios/me");
  return mapearUsuario(dado);
}

export async function atualizarPreferencias(prefs: PreferenciasUpdate): Promise<Usuario> {
  const payload: Record<string, unknown> = {};
  if (prefs.telegramId !== undefined) payload.telegram_id = prefs.telegramId;
  if (prefs.whatsapp !== undefined) payload.whatsapp = prefs.whatsapp;
  if (prefs.notifTelegram !== undefined) payload.notif_telegram = prefs.notifTelegram;
  if (prefs.notifWhatsapp !== undefined) payload.notif_whatsapp = prefs.notifWhatsapp;
  if (prefs.notifEmail !== undefined) payload.notif_email = prefs.notifEmail;

  const dado = await patch<Record<string, unknown>>("/api/usuarios/me/preferencias", payload);
  return mapearUsuario(dado);
}

export async function testarTelegram(): Promise<void> {
  await post<unknown>("/api/usuarios/me/telegram/testar", {});
}
