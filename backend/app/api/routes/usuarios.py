from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from app.api.deps import obter_cliente_rls, obter_usuario_autenticado
from app.schemas.usuario import PreferenciasUpdate, UsuarioResponse
from app.services.telegram import enviar_notificacao_telegram, gerar_token_conexao, obter_username_bot

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/me", response_model=UsuarioResponse)
async def obter_perfil(
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> UsuarioResponse:
    """Retorna os dados e preferências do usuário autenticado."""
    resposta = (
        await db.table("usuarios")
        .select("*")
        .eq("id", usuario["id"])
        .maybe_single()
        .execute()
    )
    if not resposta.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    dados = resposta.data
    return UsuarioResponse(
        id=dados["id"],
        email=dados["email"],
        telegram_id=dados.get("telegram_id"),
        notif_telegram=dados.get("notif_telegram", False),
        notif_email=dados.get("notif_email", True),
    )


@router.patch("/me/preferencias", response_model=UsuarioResponse)
async def atualizar_preferencias(
    payload: PreferenciasUpdate,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
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
        notif_telegram=dados.get("notif_telegram", False),
        notif_email=dados.get("notif_email", True),
    )


@router.post("/me/telegram/testar", status_code=status.HTTP_200_OK)
async def testar_notificacao_telegram(
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> dict[str, str]:
    """Envia uma mensagem de teste via Telegram para o usuário autenticado."""
    resposta = (
        await db.table("usuarios")
        .select("telegram_id, notif_telegram")
        .eq("id", usuario["id"])
        .maybe_single()
        .execute()
    )
    dados = resposta.data or {}
    telegram_id = dados.get("telegram_id")

    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="telegram_id não configurado.",
        )

    ok = await enviar_notificacao_telegram(
        telegram_id=telegram_id,
        nome="Produto Teste",
        loja="Zoiou",
        preco_anterior=199.90,
        preco_atual=149.90,
        url="https://zoiou-monitor.pages.dev",
        eh_historico=False,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao enviar mensagem. Verifique o TELEGRAM_BOT_TOKEN e o telegram_id.",
        )
    return {"status": "enviado"}


@router.post("/me/telegram/conectar", status_code=status.HTTP_200_OK)
async def iniciar_conexao_telegram(
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> dict[str, str]:
    """Gera deep link para conectar Telegram via /start TOKEN."""
    username = await obter_username_bot()
    if not username:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot Telegram não configurado.",
        )
    token = await gerar_token_conexao(db, usuario["id"])
    return {"url": f"https://t.me/{username}?start={token}"}
