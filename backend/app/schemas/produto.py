from pydantic import BaseModel, HttpUrl


class ProdutoCreate(BaseModel):
    """Payload para adicionar um produto à lista de desejos."""

    url: HttpUrl


class ProdutoResponse(BaseModel):
    """Produto retornado pela API com dados da lista de desejos."""

    id: str
    nome: str
    url: str
    loja: str | None
    imagem: str | None
    preco_atual: float | None
    preco_anterior: float | None
    ativo: bool
    monitorando_ha_dias: int


class ProdutoPatch(BaseModel):
    """Payload para ativar ou desativar o monitoramento."""

    ativo: bool
