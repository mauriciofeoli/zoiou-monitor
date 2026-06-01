import logging
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from supabase import AsyncClient
from telegram import Bot
from telegram.constants import ParseMode

from app.core.config import configuracoes

logger = logging.getLogger(__name__)


def _formatar_mensagem(
    nome: str,
    loja: str,
    preco_anterior: float,
    preco_atual: float,
    url: str,
    eh_historico: bool,
) -> str:
    """Monta a mensagem de notificação no formato padrão do Zoiou."""
    diferenca = preco_atual - preco_anterior
    percentual = abs(diferenca / preco_anterior * 100) if preco_anterior else 0

    if eh_historico:
        return (
            f"🏆 *PREÇO HISTÓRICO — {nome}*\n"
            f"Menor preço registrado em 12 meses\n"
            f"R$ {preco_atual:,.2f} na {loja}\n"
            f"🔗 [Ver produto]({url})"
        )

    if diferenca < 0:
        return (
            f"📉 *{nome} — {loja}*\n"
            f"De R$ {preco_anterior:,.2f} → R$ {preco_atual:,.2f}\n"
            f"↓ R$ {abs(diferenca):,.2f} a menos ({percentual:.1f}%)\n"
            f"🔗 [Ver produto]({url})"
        )

    return (
        f"📈 *{nome} — {loja}*\n"
        f"De R$ {preco_anterior:,.2f} → R$ {preco_atual:,.2f}\n"
        f"↑ R$ {diferenca:,.2f} a mais ({percentual:.1f}%)\n"
        f"🔗 [Ver produto]({url})"
    )


async def enviar_notificacao_telegram(
    telegram_id: str,
    nome: str,
    loja: str,
    preco_anterior: float,
    preco_atual: float,
    url: str,
    eh_historico: bool = False,
) -> bool:
    """Envia mensagem de variação de preço via Telegram. Retorna True se enviou."""
    if not configuracoes.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado.")
        return False

    mensagem = _formatar_mensagem(nome, loja, preco_anterior, preco_atual, url, eh_historico)
    try:
        bot = Bot(token=configuracoes.telegram_bot_token)
        await bot.send_message(
            chat_id=telegram_id,
            text=mensagem,
            parse_mode=ParseMode.MARKDOWN,
        )
        return True
    except Exception as exc:
        logger.error("Falha ao enviar Telegram para %s: %s", telegram_id, exc)
        return False


async def obter_username_bot() -> str | None:
    """Retorna o username do bot via getMe. Retorna None se falhar."""
    if not configuracoes.telegram_bot_token:
        return None
    try:
        bot = Bot(token=configuracoes.telegram_bot_token)
        me = await bot.get_me()
        return me.username
    except Exception as exc:
        logger.error("Falha ao obter username do bot: %s", exc)
        return None


async def registrar_webhook(backend_url: str, secret: str) -> bool:
    """Registra o webhook do bot no Telegram. Retorna True se bem-sucedido."""
    if not configuracoes.telegram_bot_token:
        return False
    webhook_url = f"{backend_url}/api/telegram/webhook"
    try:
        bot = Bot(token=configuracoes.telegram_bot_token)
        await bot.set_webhook(url=webhook_url, secret_token=secret)
        logger.info("Webhook Telegram registrado: %s", webhook_url)
        return True
    except Exception as exc:
        logger.error("Falha ao registrar webhook: %s", exc)
        return False


async def gerar_token_conexao(db: AsyncClient, usuario_id: str) -> str:
    """Gera token UUID, salva no banco com TTL de 10 min e retorna o token."""
    token = str(uuid.uuid4())
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.table("usuarios").update({
        "telegram_token": token,
        "telegram_token_expira_em": expira_em.isoformat(),
    }).eq("id", usuario_id).execute()
    return token


async def processar_update(db: AsyncClient, update: dict) -> None:
    """Processa update do Telegram: extrai /start TOKEN e conecta o usuário."""
    mensagem = update.get("message") or update.get("my_chat_member")
    if not mensagem:
        return

    texto = mensagem.get("text", "")
    chat_id = str(mensagem.get("chat", {}).get("id", ""))

    if not texto.startswith("/start ") and texto != "/start":
        return

    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        return

    token = partes[1].strip()
    agora = datetime.now(timezone.utc)

    resposta = (
        await db.table("usuarios")
        .select("id")
        .eq("telegram_token", token)
        .gt("telegram_token_expira_em", agora.isoformat())
        .maybe_single()
        .execute()
    )
    if not resposta.data:
        logger.warning("Token Telegram inválido ou expirado: %s", token)
        return

    usuario_id = resposta.data["id"]
    await db.table("usuarios").update({
        "telegram_id": chat_id,
        "notif_telegram": True,
        "telegram_token": None,
        "telegram_token_expira_em": None,
    }).eq("id", usuario_id).execute()

    logger.info("Telegram conectado para usuário %s (chat_id=%s)", usuario_id, chat_id)

    try:
        bot = Bot(token=configuracoes.telegram_bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text="✅ *Zoiou conectado!*\nVocê vai receber alertas de variação de preço aqui.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as exc:
        logger.error("Falha ao enviar confirmação de conexão: %s", exc)
