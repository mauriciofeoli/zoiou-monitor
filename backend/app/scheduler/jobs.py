import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import obter_cliente
from app.services.historico import (
    buscar_ultimo_preco,
    limpar_historico_antigo,
    registrar_preco,
)
from app.services.notificacao import despachar_notificacoes
from app.services.scraper import extrair_preco

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


async def monitorar_todos_produtos() -> None:
    """Verifica o preço de todos os produtos ativos e notifica em caso de mudança."""
    db = await obter_cliente()

    resposta = (
        await db.table("lista_desejos")
        .select("produto_id, produtos(id, nome, url, loja)")
        .eq("ativo", True)
        .execute()
    )
    itens = resposta.data or []
    produto_ids_vistos: set[str] = set()

    for item in itens:
        produto = item.get("produtos")
        if not produto:
            continue

        produto_id = produto["id"]
        if produto_id in produto_ids_vistos:
            continue
        produto_ids_vistos.add(produto_id)

        url = produto["url"]
        nome = produto["nome"]
        loja = produto.get("loja", "")

        preco_novo = await extrair_preco(url)
        if preco_novo is None:
            logger.warning("Scraping falhou para %s (%s)", nome, url)
            continue

        preco_anterior = await buscar_ultimo_preco(db, produto_id)
        await registrar_preco(db, produto_id, preco_novo)

        if preco_anterior is None:
            logger.info("Primeiro preço registrado para %s: R$ %.2f", nome, preco_novo)
            continue

        if abs(preco_novo - preco_anterior) <= 0.01:
            continue

        logger.info(
            "Variação em %s: R$ %.2f → R$ %.2f",
            nome,
            preco_anterior,
            preco_novo,
        )
        await despachar_notificacoes(
            db=db,
            produto_id=produto_id,
            nome=nome,
            loja=loja,
            url=url,
            preco_anterior=preco_anterior,
            preco_atual=preco_novo,
        )


async def _limpar_historico() -> None:
    """Remove registros de histórico com mais de 365 dias."""
    db = await obter_cliente()
    deletados = await limpar_historico_antigo(db)
    logger.info("Limpeza de histórico: %d registros deletados.", deletados)


def iniciar_scheduler() -> None:
    """Registra os jobs e inicia o scheduler."""
    scheduler.add_job(
        monitorar_todos_produtos,
        trigger=CronTrigger(hour=3, minute=0, timezone="America/Sao_Paulo"),
        id="monitorar_produtos",
        replace_existing=True,
    )
    scheduler.add_job(
        _limpar_historico,
        trigger=CronTrigger(day_of_week="sun", hour=4, timezone="America/Sao_Paulo"),
        id="limpar_historico",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado.")
