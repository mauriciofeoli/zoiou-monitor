export interface PontoHistorico {
  data: string; // ISO
  preco: number;
}

export interface ProdutoMock {
  id: string;
  nome: string;
  loja: string;
  url: string;
  imagem: string;
  precoAtual: number;
  precoAnterior: number;
  ativo: boolean;
  historico: PontoHistorico[];
}

function gerarHistorico(base: number, dias: number, volatilidade = 0.08): PontoHistorico[] {
  const pontos: PontoHistorico[] = [];
  let preco = base;
  const hoje = new Date();
  for (let i = dias; i >= 0; i--) {
    const d = new Date(hoje);
    d.setDate(hoje.getDate() - i);
    // Suave passeio aleatório determinístico
    const seed = Math.sin(i * 13.37 + base) * 10000;
    const ruido = (seed - Math.floor(seed)) - 0.5;
    preco = Math.max(base * 0.7, preco * (1 + ruido * volatilidade));
    pontos.push({ data: d.toISOString(), preco: Math.round(preco * 100) / 100 });
  }
  return pontos;
}

export const produtosMock: ProdutoMock[] = [
  {
    id: "rtx-4060-ti-kabum",
    nome: "Placa de Vídeo RTX 4060 Ti 8GB",
    loja: "Kabum",
    url: "https://www.kabum.com.br/produto/rtx-4060-ti",
    imagem:
      "https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&w=600&q=80",
    precoAtual: 1850.0,
    precoAnterior: 1920.0,
    ativo: true,
    historico: gerarHistorico(1900, 120),
  },
  {
    id: "kindle-11-amazon",
    nome: "Kindle 11ª Geração 16GB",
    loja: "Amazon",
    url: "https://www.amazon.com.br/kindle-11",
    imagem:
      "https://images.unsplash.com/photo-1592434134753-a70baf7979d5?auto=format&fit=crop&w=600&q=80",
    precoAtual: 499.0,
    precoAnterior: 499.0,
    ativo: true,
    historico: gerarHistorico(520, 200, 0.05),
  },
  {
    id: "airpods-pro-2-magalu",
    nome: "AirPods Pro 2ª Geração USB-C",
    loja: "Magalu",
    url: "https://www.magazineluiza.com.br/airpods-pro-2",
    imagem:
      "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=600&q=80",
    precoAtual: 1990.0,
    precoAnterior: 1799.0,
    ativo: true,
    historico: gerarHistorico(1850, 180, 0.07),
  },
  {
    id: "switch-oled-mercado-livre",
    nome: "Nintendo Switch OLED Branco",
    loja: "Mercado Livre",
    url: "https://www.mercadolivre.com.br/switch-oled",
    imagem:
      "https://images.unsplash.com/photo-1612036782180-6f0822045d23?auto=format&fit=crop&w=600&q=80",
    precoAtual: 2199.0,
    precoAnterior: 2349.0,
    ativo: false,
    historico: gerarHistorico(2300, 250, 0.06),
  },
  {
    id: "monitor-lg-ultragear",
    nome: 'Monitor LG UltraGear 27" 165Hz',
    loja: "Pichau",
    url: "https://www.pichau.com.br/monitor-lg-ultragear",
    imagem:
      "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80",
    precoAtual: 1649.0,
    precoAnterior: 1899.0,
    ativo: true,
    historico: gerarHistorico(1850, 300, 0.09),
  },
  {
    id: "echo-dot-5",
    nome: "Echo Dot 5ª Geração",
    loja: "Amazon",
    url: "https://www.amazon.com.br/echo-dot-5",
    imagem:
      "https://images.unsplash.com/photo-1543512214-318c7553f230?auto=format&fit=crop&w=600&q=80",
    precoAtual: 349.0,
    precoAnterior: 399.0,
    ativo: true,
    historico: gerarHistorico(380, 365, 0.05),
  },
];

// Força o primeiro produto a ter o último ponto = precoAtual
produtosMock.forEach((p) => {
  if (p.historico.length) {
    p.historico[p.historico.length - 1].preco = p.precoAtual;
  }
});

export function getProduto(id: string): ProdutoMock | undefined {
  return produtosMock.find((p) => p.id === id);
}

export function formatarBRL(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function ehPrecoHistorico(produto: ProdutoMock): boolean {
  const min = Math.min(...produto.historico.map((h) => h.preco));
  return produto.precoAtual <= min + 0.01;
}
