import logging

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
