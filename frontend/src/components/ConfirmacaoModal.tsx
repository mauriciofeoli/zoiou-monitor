"use client";

import { X } from "lucide-react";

interface ConfirmacaoModalProps {
  aberto: boolean;
  titulo: string;
  mensagem: string;
  textoBotaoConfirmar?: string;
  onConfirmar: () => void;
  onCancelar: () => void;
}

export function ConfirmacaoModal({
  aberto,
  titulo,
  mensagem,
  textoBotaoConfirmar = "Confirmar",
  onConfirmar,
  onCancelar,
}: ConfirmacaoModalProps) {
  if (!aberto) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm px-4"
      onClick={(e) => e.target === e.currentTarget && onCancelar()}
    >
      <div className="w-full max-w-sm rounded-2xl bg-card border border-border shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif text-xl text-ink">{titulo}</h2>
          <button
            type="button"
            onClick={onCancelar}
            className="rounded-full p-1.5 text-muted-foreground hover:bg-secondary transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-6">{mensagem}</p>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onCancelar}
            className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm hover:bg-secondary transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            className="flex-1 rounded-full bg-destructive px-4 py-2.5 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 transition-colors"
          >
            {textoBotaoConfirmar}
          </button>
        </div>
      </div>
    </div>
  );
}
