from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Rate limiter por IP em memória. Instâncias são reutilizadas como dependência FastAPI."""

    def __init__(self, max_requests: int, janela_segundos: int = 60) -> None:
        self.max_requests = max_requests
        self.janela_segundos = janela_segundos
        self._contagens: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        agora = monotonic()
        corte = agora - self.janela_segundos

        self._contagens[ip] = [t for t in self._contagens[ip] if t > corte]

        if len(self._contagens[ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Tente novamente em instantes.",
            )

        self._contagens[ip].append(agora)
