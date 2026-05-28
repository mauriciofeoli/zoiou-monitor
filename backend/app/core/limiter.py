from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request, status

# { ip: [timestamps] } — em memória, reseta ao reiniciar (aceitável para single-instance)
_contagens: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int, janela_segundos: int = 60):
    """Dependência FastAPI para rate limiting por IP."""
    async def verificar(request: Request) -> None:
        ip = (request.client.host if request.client else "unknown")
        agora = monotonic()
        corte = agora - janela_segundos

        timestamps = _contagens[ip]
        # Remove registros fora da janela
        _contagens[ip] = [t for t in timestamps if t > corte]

        if len(_contagens[ip]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Tente novamente em instantes.",
            )

        _contagens[ip].append(agora)

    return verificar
