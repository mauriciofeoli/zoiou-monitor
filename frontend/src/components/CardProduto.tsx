import Image from "next/image";
import Link from "next/link";
import { ArrowDownRight, ArrowUpRight, ExternalLink, Minus } from "lucide-react";
import type { Produto } from "@/types";
import { formatarBRL } from "@/lib/utils";
import { BadgePrecoHistorico } from "./BadgePrecoHistorico";

interface CardProdutoProps {
  produto: Produto;
  ehHistorico?: boolean;
}

export function CardProduto({ produto, ehHistorico = false }: CardProdutoProps) {
  const precoAtual = produto.precoAtual ?? 0;
  const precoAnterior = produto.precoAnterior ?? precoAtual;
  const delta = precoAtual - precoAnterior;
  const pct = precoAnterior > 0 ? (delta / precoAnterior) * 100 : 0;
  const subiu = delta > 0.01;
  const caiu = delta < -0.01;
  const estavel = !subiu && !caiu;

  return (
    <Link
      href={`/produtos/${produto.id}`}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:border-foreground/30 hover:shadow-[0_8px_30px_-12px_rgba(0,0,0,0.15)]"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {produto.imagem ? (
          <Image
            src={produto.imagem}
            alt={produto.nome}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
            Sem imagem
          </div>
        )}
        {!produto.ativo && (
          <span className="absolute top-3 left-3 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium text-muted-foreground ring-1 ring-border">
            pausado
          </span>
        )}
        {ehHistorico && produto.ativo && (
          <div className="absolute top-3 left-3">
            <BadgePrecoHistorico />
          </div>
        )}
        {produto.loja && (
          <span className="absolute top-3 right-3 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium text-foreground ring-1 ring-border">
            {produto.loja}
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <h3 className="text-base font-medium leading-snug text-foreground line-clamp-2">
          {produto.nome}
        </h3>

        <div className="flex items-end justify-between gap-3 mt-auto">
          <div>
            {produto.precoAtual != null ? (
              <>
                <div className="font-serif text-3xl leading-none text-ink">
                  {formatarBRL(produto.precoAtual)}
                </div>
                {!estavel && produto.precoAnterior != null && (
                  <div className="mt-1.5 text-xs text-muted-foreground line-through">
                    {formatarBRL(produto.precoAnterior)}
                  </div>
                )}
              </>
            ) : (
              <div className="text-sm text-muted-foreground italic">aguardando captura</div>
            )}
          </div>

          {produto.precoAtual != null && (
            <div
              className={[
                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
                caiu && "bg-success/15 text-success ring-1 ring-success/30",
                subiu && "bg-destructive/15 text-destructive ring-1 ring-destructive/30",
                estavel && "bg-muted text-muted-foreground ring-1 ring-border",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {caiu && <ArrowDownRight className="h-3.5 w-3.5" />}
              {subiu && <ArrowUpRight className="h-3.5 w-3.5" />}
              {estavel && <Minus className="h-3.5 w-3.5" />}
              {estavel ? "estável" : `${pct > 0 ? "+" : ""}${pct.toFixed(1)}%`}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border/60">
          <span>{produto.monitorandoHaDias} dias monitorando</span>
          <span className="inline-flex items-center gap-1 text-foreground/70 group-hover:text-foreground transition-colors">
            ver detalhes <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      </div>
    </Link>
  );
}
