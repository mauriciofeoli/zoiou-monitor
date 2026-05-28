import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import historico, produtos, usuarios
from app.core.config import configuracoes
from app.scheduler.jobs import iniciar_scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(name)s — %(message)s")

app = FastAPI(title="Zoiou API", version="1.0.0", docs_url="/docs")

_origens_dev = ["http://localhost:3000", "http://localhost:3001"]
_origens = _origens_dev if configuracoes.ambiente == "development" else [configuracoes.frontend_url]

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


@app.exception_handler(Exception)
async def handler_generico(request: Request, exc: Exception) -> JSONResponse:
    """Retorna erro 500 sem expor detalhes internos ao cliente."""
    logging.error("Erro não tratado: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": {"code": "ERRO_INTERNO", "message": "Erro interno."}},
    )


@app.on_event("startup")
async def startup() -> None:
    iniciar_scheduler()


@app.on_event("shutdown")
async def shutdown() -> None:
    from app.scheduler.jobs import scheduler
    if scheduler.running:
        scheduler.shutdown()


@app.get("/health")
async def health() -> dict:
    """Endpoint de saúde para Railway."""
    return {"status": "ok"}
