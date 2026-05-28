from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from supabase import AsyncClient, acreate_client

from app.core.config import configuracoes
from app.core.database import obter_cliente
from app.core.security import bearer_scheme, obter_usuario_autenticado


async def obter_cliente_rls(
    credenciais: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AsyncClient:
    """Cria cliente Supabase com JWT do usuário — RLS é aplicado pelo banco."""
    cliente = await acreate_client(
        configuracoes.supabase_url,
        configuracoes.supabase_anon_key,
    )
    cliente.postgrest.auth(credenciais.credentials)
    return cliente


__all__ = ["obter_cliente", "obter_cliente_rls", "obter_usuario_autenticado", "Depends", "AsyncClient"]
