import { describe, expect, it } from "vitest";
import { ehPrecoHistoricoLista, formatarBRL } from "../utils";

describe("ehPrecoHistoricoLista", () => {
  it("retorna true quando preço é menor que o mínimo histórico", () => {
    expect(ehPrecoHistoricoLista(89.9, [100, 90, 95])).toBe(true);
  });

  it("retorna true quando preço é igual ao mínimo histórico", () => {
    expect(ehPrecoHistoricoLista(90.0, [100, 90, 95])).toBe(true);
  });

  it("retorna true dentro da tolerância de R$ 0,01", () => {
    expect(ehPrecoHistoricoLista(90.01, [100, 90, 95])).toBe(true);
  });

  it("retorna false quando preço está acima do mínimo + 0,01", () => {
    expect(ehPrecoHistoricoLista(90.02, [100, 90, 95])).toBe(false);
  });

  it("retorna false para lista de histórico vazia", () => {
    expect(ehPrecoHistoricoLista(100.0, [])).toBe(false);
  });

  it("retorna true com histórico de um único ponto", () => {
    expect(ehPrecoHistoricoLista(99.0, [100.0])).toBe(true);
  });
});

describe("formatarBRL", () => {
  it("formata valor inteiro corretamente", () => {
    expect(formatarBRL(100)).toBe("R$\xa0100,00");
  });

  it("formata valor com centavos corretamente", () => {
    expect(formatarBRL(1850.99)).toBe("R$\xa01.850,99");
  });

  it("formata zero", () => {
    expect(formatarBRL(0)).toBe("R$\xa00,00");
  });

  it("formata valor grande com separador de milhar", () => {
    const resultado = formatarBRL(10000);
    expect(resultado).toContain("10.000");
  });
});
