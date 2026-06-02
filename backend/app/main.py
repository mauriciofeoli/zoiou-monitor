import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import historico, produtos, telegram, usuarios
from app.core.config import configuracoes
from app.core.limiter import RateLimitMiddleware
from app.scheduler.jobs import iniciar_scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(name)s — %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    iniciar_scheduler()
    if configuracoes.telegram_bot_token and configuracoes.telegram_webhook_secret:
        from app.services.telegram import registrar_webhook
        await registrar_webhook(configuracoes.backend_url, configuracoes.telegram_webhook_secret)
    yield
    from app.scheduler.jobs import scheduler
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="Zoiou API", version="1.0.0", docs_url="/docs", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)

_origens_dev = ["http://localhost:3000", "http://localhost:3001"]
_extras = [u.strip() for u in configuracoes.frontend_urls_extras.split(",") if u.strip()]
_origens_prod = [u for u in [configuracoes.frontend_url, *_extras] if u and not u.startswith("http://localhost")]
_origens = [*_origens_dev, *_origens_prod] if configuracoes.ambiente == "development" else _origens_prod or _origens_dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(produtos.router, prefix="/api")
app.include_router(historico.router, prefix="/api")
app.include_router(usuarios.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")


@app.exception_handler(Exception)
async def handler_generico(request: Request, exc: Exception) -> JSONResponse:
    """Retorna erro 500 sem expor detalhes internos ao cliente."""
    logging.error("Erro não tratado: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": {"code": "ERRO_INTERNO", "message": "Erro interno."}},
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
