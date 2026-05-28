import re

from pydantic import BaseModel, field_validator


class UsuarioResponse(BaseModel):
    """Dados do usuário autenticado."""

    id: str
    email: str
    telegram_id: str | None
    notif_telegram: bool
    notif_email: bool


class PreferenciasUpdate(BaseModel):
    """Payload para atualizar preferências de notificação."""

    telegram_id: str | None = None
    notif_telegram: bool | None = None
    notif_email: bool | None = None

    @field_validator("telegram_id")
    @classmethod
    def validar_telegram_id(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if re.match(r"^-?\d+$", v):
            return v
        if re.match(r"^@[A-Za-z0-9_]{4,32}$", v):
            return v
        raise ValueError("telegram_id inválido. Use @usuario ou ID numérico.")
