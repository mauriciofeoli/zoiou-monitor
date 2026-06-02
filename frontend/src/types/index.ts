export interface PontoHistorico {
  data: string; // ISO date string
  preco: number;
}

export interface Produto {
  id: string;
  nome: string;
  url: string;
  loja: string;
  imagem: string;
  precoAtual: number | null;
  precoAnterior: number | null;
  ativo: boolean;
  monitorandoHaDias: number;
  ultimaAtualizacao: string | null;
}

export interface HistoricoProduto {
  produtoId: string;
  pontos: PontoHistorico[];
  precoMinimo: number | null;
  precoMaximo: number | null;
  precoMedio: number | null;
}

export interface Usuario {
  id: string;
  email: string;
  telegramId: string | null;
  notifTelegram: boolean;
}

export interface PreferenciasUpdate {
  telegramId?: string | null;
  notifTelegram?: boolean;
}
