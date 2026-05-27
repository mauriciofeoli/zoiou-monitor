import { Trophy } from "lucide-react";

export function BadgePrecoHistorico() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-gold/15 px-2.5 py-1 text-xs font-medium text-gold-foreground ring-1 ring-gold/40">
      <Trophy className="h-3.5 w-3.5 text-gold" />
      Preço histórico
    </span>
  );
}
