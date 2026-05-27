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
  return precoAtual <= Math.min(...historico) + 0.01;
}
