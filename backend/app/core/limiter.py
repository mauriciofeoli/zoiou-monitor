import re
from collections import defaultdict
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

# POST /api/produtos → 10/min
# POST /api/produtos/{id}/atualizar → 6/min
_REGRAS: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"^/api/produtos$"), "POST", 10),
    (re.compile(r"^/api/produtos/[^/]+/atualizar$"), "POST", 6),
]

_contagens: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, janela_segundos: int = 60) -> None:
        super().__init__(app)
        self.janela = janela_segundos

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path
        method = request.method

        for padrao, metodo, limite in _REGRAS:
            if method == metodo and padrao.match(path):
                ip = (
                    request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                    or (request.client.host if request.client else "unknown")
                )
                agora = monotonic()
                corte = agora - self.janela
                bucket = _contagens[path][ip]
                bucket[:] = [t for t in bucket if t > corte]
                if len(bucket) >= limite:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Muitas requisições. Tente novamente em instantes."},
                    )
                bucket.append(agora)
                break

        return await call_next(request)
