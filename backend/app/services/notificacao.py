import logging

from supabase import AsyncClient

from app.services.email import enviar_notificacao_email
from app.services.historico import buscar_historico_produto, eh_preco_historico
from app.services.telegram import enviar_notificacao_telegram

logger = logging.getLogger(__name__)


async def _buscar_usuarios_do_produto(
    db: AsyncClient,
    produto_id: str,
) -> list[dict]:
    """Retorna usuários com o produto ativo na lista de desejos."""
    resposta = (
        await db.table("lista_desejos")
        .select("usuario_id, usuarios(email, telegram_id, notif_email, notif_telegram)")
        .eq("produto_id", produto_id)
        .eq("ativo", True)
        .execute()
    )
    return resposta.data or []


async def despachar_notificacoes(
    db: AsyncClient,
    produto_id: str,
    nome: str,
    loja: str,
    url: str,
    preco_anterior: float,
    preco_atual: float,
) -> None:
    """Envia notificações de variação de preço para todos os usuários do produto."""
    historico = await buscar_historico_produto(db, produto_id)
    precos = [float(p["preco"]) for p in historico]
    historico_minimo = eh_preco_historico(preco_atual, precos)

    usuarios = await _buscar_usuarios_do_produto(db, produto_id)

    for item in usuarios:
        usuario = item.get("usuarios", {})
        if not usuario:
            continue

        if usuario.get("notif_email") and usuario.get("email"):
            await enviar_notificacao_email(
                destinatario=usuario["email"],
                nome=nome,
                loja=loja or "",
                preco_anterior=preco_anterior,
                preco_atual=preco_atual,
                url=url,
                eh_historico=historico_minimo,
            )

        if usuario.get("notif_telegram") and usuario.get("telegram_id"):
            await enviar_notificacao_telegram(
                telegram_id=usuario["telegram_id"],
                nome=nome,
                loja=loja or "",
                preco_anterior=preco_anterior,
                preco_atual=preco_atual,
                url=url,
                eh_historico=historico_minimo,
            )
