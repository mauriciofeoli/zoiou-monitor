from datetime import datetime, timedelta, timezone

from supabase import AsyncClient


async def buscar_historico_produto(
    db: AsyncClient,
    produto_id: str,
    dias: int = 365,
) -> list[dict]:
    """Retorna os registros de preço dos últimos N dias de um produto."""
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    resposta = (
        await db.table("historico_precos")
        .select("preco, capturado_em")
        .eq("produto_id", produto_id)
        .gte("capturado_em", limite.isoformat())
        .order("capturado_em", desc=False)
        .execute()
    )
    return resposta.data or []


async def registrar_preco(
    db: AsyncClient,
    produto_id: str,
    preco: float,
) -> None:
    """Insere um novo registro de preço no histórico."""
    await db.table("historico_precos").insert(
        {"produto_id": produto_id, "preco": preco}
    ).execute()


async def buscar_ultimo_preco(
    db: AsyncClient,
    produto_id: str,
) -> float | None:
    """Retorna o último preço registrado de um produto."""
    resposta = (
        await db.table("historico_precos")
        .select("preco")
        .eq("produto_id", produto_id)
        .order("capturado_em", desc=True)
        .limit(1)
        .execute()
    )
    if resposta.data:
        return float(resposta.data[0]["preco"])
    return None


async def buscar_ultimos_precos(
    db: AsyncClient,
    produto_id: str,
) -> tuple[float | None, float | None, str | None]:
    """Retorna (preco_atual, preco_anterior, ultima_atualizacao) — os dois últimos registros."""
    resposta = (
        await db.table("historico_precos")
        .select("preco, capturado_em")
        .eq("produto_id", produto_id)
        .order("capturado_em", desc=True)
        .limit(2)
        .execute()
    )
    dados = resposta.data or []
    preco_atual = float(dados[0]["preco"]) if dados else None
    preco_anterior = float(dados[1]["preco"]) if len(dados) >= 2 else None
    ultima_atualizacao = dados[0]["capturado_em"] if dados else None
    return preco_atual, preco_anterior, ultima_atualizacao


def eh_preco_historico(preco_atual: float, historico: list[float]) -> bool:
    """Verifica se o preço atual é o menor dos últimos 365 dias."""
    if not historico:
        return False
    return preco_atual <= min(historico) + 0.01


def calcular_estatisticas(
    historico: list[dict],
) -> tuple[float | None, float | None, float | None]:
    """Retorna (mínimo, máximo, média) dos preços do histórico."""
    if not historico:
        return None, None, None
    precos = [float(p["preco"]) for p in historico]
    return min(precos), max(precos), round(sum(precos) / len(precos), 2)


async def limpar_historico_antigo(db: AsyncClient) -> int:
    """Remove registros com mais de 365 dias. Retorna a quantidade deletada."""
    limite = datetime.now(timezone.utc) - timedelta(days=365)
    resposta = (
        await db.table("historico_precos")
        .delete()
        .lt("capturado_em", limite.isoformat())
        .execute()
    )
    return len(resposta.data or [])
