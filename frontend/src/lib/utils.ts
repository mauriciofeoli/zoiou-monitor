import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatarBRL(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function ehPrecoHistoricoLista(precoAtual: number, historico: number[]): boolean {
  if (!historico.length) return false;
  let minHistorico = historico[0];
  for (let i = 1; i < historico.length; i++) {
    if (historico[i] < minHistorico) minHistorico = historico[i];
  }
  return precoAtual <= minHistorico + 0.01;
}
