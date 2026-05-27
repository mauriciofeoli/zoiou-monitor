from supabase import AsyncClient, acreate_client

from app.core.config import configuracoes

_cliente: AsyncClient | None = None


async def obter_cliente() -> AsyncClient:
    """Retorna o cliente Supabase singleton (service role)."""
    global _cliente
    if _cliente is None:
        _cliente = await acreate_client(
            configuracoes.supabase_url,
            configuracoes.supabase_service_key,
        )
    return _cliente
