import asyncio
import json
import logging

from pywebpush import WebPushException, webpush

from app.core.config import configuracoes

logger = logging.getLogger(__name__)


async def enviar_push(
    subscription: dict,
    titulo: str,
    corpo: str,
    url: str,
) -> bool:
    """Envia push notification via Web Push Protocol. Retorna True se enviou."""
    if not configuracoes.vapid_private_key or not configuracoes.vapid_email:
        return False

    payload = json.dumps({"title": titulo, "body": corpo, "url": url})

    def _enviar() -> None:
        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=configuracoes.vapid_private_key,
            vapid_claims={"sub": f"mailto:{configuracoes.vapid_email}"},
        )

    try:
        await asyncio.to_thread(_enviar)
        return True
    except WebPushException as exc:
        logger.error("Falha ao enviar push notification: %s", exc)
        return False
    except Exception as exc:
        logger.error("Erro inesperado no push: %s", exc)
        return False
