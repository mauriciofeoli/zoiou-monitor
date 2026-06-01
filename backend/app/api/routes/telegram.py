import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import configuracoes
from app.core.database import obter_cliente as _db_direto
from app.services.telegram import processar_update

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook_telegram(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """Recebe updates do Telegram e processa a conexão via deep link."""
    if not configuracoes.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    if x_telegram_bot_api_secret_token != configuracoes.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    update = await request.json()
    db = await _db_direto()
    await processar_update(db, update)
    return {"ok": True}
