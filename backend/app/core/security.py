from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient

from app.core.database import obter_cliente

bearer_scheme = HTTPBearer()


async def obter_usuario_autenticado(
    credenciais: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncClient = Depends(obter_cliente),
) -> dict:
    """Valida o JWT do Supabase e retorna os dados do usuário."""
    token = credenciais.credentials
    try:
        resposta = await db.auth.get_user(token)
        if resposta.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado.",
            )
        usuario = {"id": resposta.user.id, "email": resposta.user.email}
        # Garante que o usuário existe na tabela pública (handles signup antes da migration)
        await db.table("usuarios").upsert(
            {"id": usuario["id"], "email": usuario["email"]},
            on_conflict="id",
        ).execute()
        return usuario
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
        )
