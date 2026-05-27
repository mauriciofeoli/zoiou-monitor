from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from app.api.deps import obter_cliente, obter_usuario_autenticado
from app.schemas.usuario import PreferenciasUpdate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/me", response_model=UsuarioResponse)
async def obter_perfil(
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente),
) -> UsuarioResponse:
    """Retorna os dados e preferências do usuário autenticado."""
    resposta = (
        await db.table("usuarios")
        .select("*")
        .eq("id", usuario["id"])
        .single()
        .execute()
    )
    if not resposta.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    dados = resposta.data
    return UsuarioResponse(
        id=dados["id"],
        email=dados["email"],
        telegram_id=dados.get("telegram_id"),
        whatsapp=dados.get("whatsapp"),
        notif_telegram=dados.get("notif_telegram", False),
        notif_whatsapp=dados.get("notif_whatsapp", False),
        notif_email=dados.get("notif_email", True),
    )


@router.patch("/me/preferencias", response_model=UsuarioResponse)
async def atualizar_preferencias(
    payload: PreferenciasUpdate,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente),
) -> UsuarioResponse:
    """Atualiza as preferências de notificação do usuário."""
    atualizacoes = payload.model_dump(exclude_none=True)
    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    await db.table("usuarios").update(atualizacoes).eq("id", usuario["id"]).execute()

    resposta = (
        await db.table("usuarios")
        .select("*")
        .eq("id", usuario["id"])
        .single()
        .execute()
    )
    dados = resposta.data
    return UsuarioResponse(
        id=dados["id"],
        email=dados["email"],
        telegram_id=dados.get("telegram_id"),
        whatsapp=dados.get("whatsapp"),
        notif_telegram=dados.get("notif_telegram", False),
        notif_whatsapp=dados.get("notif_whatsapp", False),
        notif_email=dados.get("notif_email", True),
    )
