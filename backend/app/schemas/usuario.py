from pydantic import BaseModel


class UsuarioResponse(BaseModel):
    """Dados do usuário autenticado."""

    id: str
    email: str
    telegram_id: str | None
    whatsapp: str | None
    notif_telegram: bool
    notif_whatsapp: bool
    notif_email: bool


class PreferenciasUpdate(BaseModel):
    """Payload para atualizar preferências de notificação."""

    telegram_id: str | None = None
    whatsapp: str | None = None
    notif_telegram: bool | None = None
    notif_whatsapp: bool | None = None
    notif_email: bool | None = None
