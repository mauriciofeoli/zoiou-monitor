from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from app.api.deps import obter_cliente, obter_usuario_autenticado
from app.schemas.historico import HistoricoResponse, PontoHistorico
from app.services.historico import buscar_historico_produto, calcular_estatisticas

router = APIRouter(prefix="/produtos", tags=["historico"])


@router.get("/{produto_id}/historico", response_model=HistoricoResponse)
async def obter_historico(
    produto_id: str,
    usuario: dict = Depends(obter_usuario_autenticado),
    db: AsyncClient = Depends(obter_cliente),
) -> HistoricoResponse:
    """Retorna o histórico de preços de um produto da lista do usuário."""
    # Verifica se o produto pertence ao usuário
    lista = (
        await db.table("lista_desejos")
        .select("id")
        .eq("produto_id", produto_id)
        .eq("usuario_id", usuario["id"])
        .limit(1)
        .execute()
    )
    if not lista.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado na sua lista.",
        )

    historico = await buscar_historico_produto(db, produto_id)
    minimo, maximo, media = calcular_estatisticas(historico)

    pontos = [
        PontoHistorico(preco=float(p["preco"]), capturado_em=p["capturado_em"])
        for p in historico
    ]

    return HistoricoResponse(
        produto_id=produto_id,
        pontos=pontos,
        preco_minimo=minimo,
        preco_maximo=maximo,
        preco_medio=media,
    )
