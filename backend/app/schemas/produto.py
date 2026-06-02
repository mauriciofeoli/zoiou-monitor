import ipaddress

from pydantic import BaseModel, HttpUrl, field_validator


class ProdutoCreate(BaseModel):
    """Payload para adicionar um produto à lista de desejos."""

    url: HttpUrl

    @field_validator("url")
    @classmethod
    def bloquear_url_privada(cls, v: HttpUrl) -> HttpUrl:
        host = v.host or ""
        if host.lower() in {"localhost", "0.0.0.0"}:
            raise ValueError("URL inválida.")
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                raise ValueError("URL inválida.")
        except ValueError as exc:
            if "URL inválida" in str(exc):
                raise
        return v


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
    ultima_atualizacao: str | None


class ProdutoPatch(BaseModel):
    """Payload para ativar ou desativar o monitoramento."""

    ativo: bool
