from datetime import datetime

from pydantic import BaseModel


class PontoHistorico(BaseModel):
    """Registro de preço em um momento específico."""

    preco: float
    capturado_em: datetime


class HistoricoResponse(BaseModel):
    """Histórico completo de preços de um produto."""

    produto_id: str
    pontos: list[PontoHistorico]
    preco_minimo: float | None
    preco_maximo: float | None
    preco_medio: float | None
