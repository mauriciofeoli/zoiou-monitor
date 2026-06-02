"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { PontoHistorico } from "@/types";
import { formatarBRL } from "@/lib/utils";

interface GraficoHistoricoProps {
  dados: PontoHistorico[];
}

export function GraficoHistorico({ dados }: GraficoHistoricoProps) {
  const data = useMemo(
    () =>
      dados.map((d) => ({
        data: d.data,
        preco: d.preco,
        label: new Date(d.data).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" }),
      })),
    [dados],
  );

  if (!dados.length) {
    return (
      <div className="h-72 w-full flex items-center justify-center text-sm text-muted-foreground">
        Sem dados suficientes para exibir o gráfico.
      </div>
    );
  }

  let min = dados[0].preco;
  let max = dados[0].preco;
  for (let i = 1; i < dados.length; i++) {
    if (dados[i].preco < min) min = dados[i].preco;
    if (dados[i].preco > max) max = dados[i].preco;
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="precoFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-success)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-success)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            stroke="var(--color-muted-foreground)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            minTickGap={32}
          />
          <YAxis
            stroke="var(--color-muted-foreground)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => formatarBRL(v).replace(",00", "")}
            width={72}
            domain={[min * 0.95, max * 1.02]}
          />
          <Tooltip
            cursor={{ stroke: "var(--color-foreground)", strokeOpacity: 0.2 }}
            contentStyle={{
              background: "var(--color-card)",
              border: "1px solid var(--color-border)",
              borderRadius: 12,
              fontSize: 12,
            }}
            labelStyle={{ color: "var(--color-muted-foreground)" }}
            formatter={(value: number) => [formatarBRL(value), "Preço"]}
          />
          <ReferenceLine
            y={min}
            stroke="var(--color-gold)"
            strokeDasharray="4 4"
            label={{
              value: `mínimo ${formatarBRL(min)}`,
              position: "insideBottomRight",
              fill: "var(--color-gold)",
              fontSize: 11,
            }}
          />
          <Area
            type="monotone"
            dataKey="preco"
            stroke="var(--color-success)"
            strokeWidth={2}
            fill="url(#precoFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
