from fastapi import Depends
from supabase import AsyncClient

from app.core.database import obter_cliente
from app.core.security import obter_usuario_autenticado

__all__ = ["obter_cliente", "obter_usuario_autenticado", "Depends", "AsyncClient"]
