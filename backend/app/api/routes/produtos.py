import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from supabase import AsyncClient

from app.api.deps import obter_cliente_rls, obter_usuario_autenticado
from app.core.database import obter_cliente as _db_direto
from app.schemas.produto import ProdutoCreate, ProdutoPatch, ProdutoResponse
from app.services.historico import buscar_ultimo_preco, buscar_ultimos_precos, registrar_preco
from app.services.notificacao import despachar_notificacoes
from app.services.scraper import extrair_metadados_produto, extrair_preco, extrair_produto_completo

router = APIRouter(prefix="/produtos", tags=["produtos"])
logger = logging.getLogger(__name__)


async def _notificar_variacao(
    db: AsyncClient,
    produto_id: str,
    nome: str,
    loja: str,
    url: str,
    preco_anterior: float | None,
    preco_novo: float,
) -> None:
    """Despacha notificações se a variação de preço for significativa (> R$ 0,01)."""
    if preco_anterior is not None and abs(preco_novo - preco_anterior) > 0.01:
        await despachar_notificacoes(
            db=db,
            produto_id=produto_id,
            nome=nome,
            loja=loja,
            url=url,
            preco_anterior=preco_anterior,
            preco_atual=preco_novo,
        )


async def _capturar_preco_background(produto_id: str, url: str) -> None:
    """Tenta capturar preço via Playwright após a resposta já ter sido enviada."""
    try:
        db = await _db_direto()
        if await buscar_ultimo_preco(db, produto_id) is not None:
            return
        preco = await extrair_preco(url)
        if preco is not None:
            await registrar_preco(db, produto_id, preco)
            logger.info("Background: R$ %.2f capturado para %s", preco, url)
        else:
            logger.warning("Background: preço não encontrado para %s", url)
    except Exception as exc:
        logger.error("Background preço %s: %s", url, exc)


async def _atualizar_preco_forcado_background(
    produto_id: str, url: str, nome: str, loja: str
) -> None:
    """Captura preço atual; registra e notifica só se o valor mudou mais de R$ 0,01."""
    try:
        db = await _db_direto()
        preco_anterior = await buscar_ultimo_preco(db, produto_id)
        preco = await extrair_preco(url)
        if preco is None:
            logger.warning("BG atualizar-todos: preço não encontrado para %s", url)
            return
        if preco_anterior is not None and abs(preco - preco_anterior) <= 0.01:
            logger.info("BG atualizar-todos: sem variação para %s (R$ %.2f)", url, preco)
            return
        await registrar_preco(db, produto_id, preco)
        logger.info("BG atualizar-todos: R$ %.2f para %s", preco, url)
        await _notificar_variacao(db, produto_id, nome, loja, url, preco_anterior, preco)
    except Exception as exc:
        logger.error("BG atualizar-todos %s: %s", url, exc)


async def _atualizar_metadados_background(
    produto_id: str, url: str, imagem_atual: str | None, loja: str = ""
) -> None:
    """Atualiza nome e imagem quando curl_cffi retornou metadados genéricos."""
    try:
        db = await _db_direto()
        meta = await extrair_metadados_produto(url)
        nome = meta.get("nome", "")
        if nome and nome != url and nome != loja:
            await db.table("produtos").update({
                "nome": nome,
                "imagem": meta.get("imagem") or imagem_atual,
            }).eq("id", produto_id).execute()
            logger.info("Background: metadados atualizados para %s", url)
    except Exception as exc:
        logger.error("Background metadados %s: %s", url, exc)


@router.get("", response_model=list[ProdutoResponse])
async def listar_produtos(
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> list[ProdutoResponse]:
    """Lista todos os produtos ativos e pausados da lista de desejos do usuário."""
    resposta = (
        await db.table("lista_desejos")
        .select("id, ativo, criado_em, produtos(id, nome, url, loja, imagem)")
        .eq("usuario_id", usuario["id"])
        .execute()
    )

    resultado = []
    for item in resposta.data or []:
        produto = item.get("produtos")
        if not produto:
            continue

        preco_atual, preco_anterior, ultima_atualizacao = await buscar_ultimos_precos(db, produto["id"])

        criado_em = datetime.fromisoformat(item["criado_em"].replace("Z", "+00:00"))
        dias_monitorando = (datetime.now(timezone.utc) - criado_em).days

        resultado.append(
            ProdutoResponse(
                id=produto["id"],
                nome=produto["nome"],
                url=produto["url"],
                loja=produto.get("loja"),
                imagem=produto.get("imagem"),
                preco_atual=preco_atual,
                preco_anterior=preco_anterior,
                ativo=item["ativo"],
                monitorando_ha_dias=max(dias_monitorando, 0),
                ultima_atualizacao=ultima_atualizacao,
            )
        )
    return resultado


@router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
async def adicionar_produto(
    payload: ProdutoCreate,
    background_tasks: BackgroundTasks,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> ProdutoResponse:
    """Adiciona um produto à lista de desejos. Responde rápido; preço/metadados
    são completados em background se curl_cffi não conseguir imediatamente."""
    url = str(payload.url)
    db_s = await _db_direto()

    total = await db.table("lista_desejos").select("id", count="exact").eq("usuario_id", usuario["id"]).execute()
    if (total.count or 0) >= 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limite de 20 produtos atingido.",
        )

    existente = await db_s.table("produtos").select("id, nome, url, loja, imagem").eq("url", url).limit(1).execute()

    if existente.data:
        produto_id = existente.data[0]["id"]
        p = existente.data[0]
    else:
        dados = await extrair_produto_completo(url, usar_playwright=False)
        novo = (
            await db_s.table("produtos")
            .insert({
                "url": url,
                "nome": dados["nome"] or url,
                "loja": dados["loja"],
                "imagem": dados["imagem"],
            })
            .execute()
        )
        produto_id = novo.data[0]["id"]
        p = {"id": produto_id, "nome": dados["nome"] or url, "url": url,
             "loja": dados["loja"], "imagem": dados["imagem"]}

        if dados.get("preco") is not None:
            await registrar_preco(db_s, produto_id, dados["preco"])

    await db.table("lista_desejos").upsert(
        {"usuario_id": usuario["id"], "produto_id": produto_id, "ativo": True},
        on_conflict="usuario_id,produto_id",
    ).execute()

    preco_atual = await buscar_ultimo_preco(db, produto_id)

    if preco_atual is None:
        background_tasks.add_task(_capturar_preco_background, produto_id, url)

    loja_p = p.get("loja", "")
    nome_invalido = not p.get("nome") or p["nome"] == url or p["nome"] == loja_p
    if nome_invalido:
        background_tasks.add_task(_atualizar_metadados_background, produto_id, url, p.get("imagem"), loja_p)

    return ProdutoResponse(
        id=p["id"],
        nome=p["nome"],
        url=url,
        loja=p.get("loja"),
        imagem=p.get("imagem"),
        preco_atual=preco_atual,
        preco_anterior=None,
        ativo=True,
        monitorando_ha_dias=0,
        ultima_atualizacao=None,
    )


@router.post("/atualizar-todos")
async def atualizar_todos_agora(
    background_tasks: BackgroundTasks,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> dict[str, int | bool]:
    """Dispara scraping em background para todos os produtos ativos do usuário."""
    lista = (
        await db.table("lista_desejos")
        .select("produto_id")
        .eq("usuario_id", usuario["id"])
        .eq("ativo", True)
        .execute()
    )
    db_s = await _db_direto()
    total = 0
    for item in lista.data or []:
        produto = (
            await db_s.table("produtos")
            .select("url, nome, loja")
            .eq("id", item["produto_id"])
            .single()
            .execute()
        )
        if produto.data:
            background_tasks.add_task(
                _atualizar_preco_forcado_background,
                item["produto_id"],
                produto.data["url"],
                produto.data.get("nome") or "",
                produto.data.get("loja") or "",
            )
            total += 1
    return {"iniciado": True, "total": total}


@router.post("/{produto_id}/atualizar", response_model=ProdutoResponse)
async def atualizar_preco_agora(
    produto_id: str,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> ProdutoResponse:
    """Dispara o scraping imediato de um produto e atualiza nome/imagem se ainda não tiver."""
    db_s = await _db_direto()

    lista = (
        await db.table("lista_desejos")
        .select("ativo")
        .eq("produto_id", produto_id)
        .eq("usuario_id", usuario["id"])
        .limit(1)
        .execute()
    )
    if not lista.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    produto_db = (
        await db_s.table("produtos")
        .select("id, nome, url, loja, imagem")
        .eq("id", produto_id)
        .single()
        .execute()
    )
    p = produto_db.data
    url = p["url"]

    loja_p = p.get("loja", "")
    if not p["nome"] or p["nome"] == url or p["nome"] == loja_p:
        metadados = await extrair_metadados_produto(url)
        novo_nome = metadados.get("nome", "")
        if novo_nome and novo_nome != loja_p:
            await db_s.table("produtos").update({
                "nome": novo_nome,
                "imagem": metadados.get("imagem") or p.get("imagem"),
            }).eq("id", produto_id).execute()
            p["nome"] = novo_nome
            p["imagem"] = metadados.get("imagem") or p.get("imagem")

    preco_novo = await extrair_preco(url)
    if preco_novo is not None:
        await registrar_preco(db_s, produto_id, preco_novo)

    preco_atual, preco_anterior, ultima_atualizacao = await buscar_ultimos_precos(db_s, produto_id)

    if preco_novo is not None:
        await _notificar_variacao(
            db_s, produto_id, p["nome"], p.get("loja") or "", url, preco_anterior, preco_novo
        )

    ativo = lista.data[0]["ativo"]

    return ProdutoResponse(
        id=p["id"],
        nome=p["nome"],
        url=p["url"],
        loja=p.get("loja"),
        imagem=p.get("imagem"),
        preco_atual=preco_atual,
        preco_anterior=preco_anterior,
        ativo=ativo,
        monitorando_ha_dias=0,
        ultima_atualizacao=ultima_atualizacao,
    )


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_produto(
    produto_id: str,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> None:
    """Remove um produto da lista de desejos do usuário."""
    resposta = (
        await db.table("lista_desejos")
        .delete()
        .eq("produto_id", produto_id)
        .eq("usuario_id", usuario["id"])
        .execute()
    )
    if not resposta.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")


@router.patch("/{produto_id}", response_model=ProdutoResponse)
async def atualizar_produto(
    produto_id: str,
    payload: ProdutoPatch,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente_rls),
) -> ProdutoResponse:
    """Ativa ou desativa o monitoramento de um produto."""
    db_s = await _db_direto()

    await db.table("lista_desejos").update({"ativo": payload.ativo}).eq(
        "produto_id", produto_id
    ).eq("usuario_id", usuario["id"]).execute()

    produto_db = (
        await db_s.table("produtos")
        .select("id, nome, url, loja, imagem")
        .eq("id", produto_id)
        .single()
        .execute()
    )
    p = produto_db.data
    preco_atual = await buscar_ultimo_preco(db, produto_id)

    return ProdutoResponse(
        id=p["id"],
        nome=p["nome"],
        url=p["url"],
        loja=p.get("loja"),
        imagem=p.get("imagem"),
        preco_atual=preco_atual,
        preco_anterior=None,
        ativo=payload.ativo,
        monitorando_ha_dias=0,
        ultima_atualizacao=None,
    )
