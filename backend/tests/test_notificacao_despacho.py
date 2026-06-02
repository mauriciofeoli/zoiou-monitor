"""Testes do fluxo de despacho de notificações."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notificacao import despachar_notificacoes


def _make_db(usuarios: list[dict]) -> MagicMock:
    """Cria um mock de AsyncClient com lista de usuários configurada."""
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=usuarios)
    )
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    return db


@pytest.mark.asyncio
async def test_envia_telegram_quando_configurado() -> None:
    usuarios = [
        {
            "usuario_id": "u1",
            "usuarios": {
                "email": "a@zoiou.com",
                "telegram_id": "123456",
                "notif_telegram": True,
                "notif_email": False,
            },
        }
    ]
    db = _make_db(usuarios)

    with patch("app.services.notificacao.enviar_notificacao_telegram") as mock_tg, \
         patch("app.services.notificacao.buscar_historico_produto", return_value=[]):
        await despachar_notificacoes(
            db=db,
            produto_id="prod-1",
            nome="Produto X",
            loja="Kabum",
            url="https://kabum.com.br/1",
            preco_anterior=100.0,
            preco_atual=90.0,
        )
        mock_tg.assert_called_once()


@pytest.mark.asyncio
async def test_nao_envia_telegram_quando_desativado() -> None:
    usuarios = [
        {
            "usuario_id": "u1",
            "usuarios": {
                "email": "a@zoiou.com",
                "telegram_id": "123456",
                "notif_telegram": False,
                "notif_email": False,
            },
        }
    ]
    db = _make_db(usuarios)

    with patch("app.services.notificacao.enviar_notificacao_telegram") as mock_tg, \
         patch("app.services.notificacao.buscar_historico_produto", return_value=[]):
        await despachar_notificacoes(
            db=db,
            produto_id="prod-1",
            nome="Produto X",
            loja="Kabum",
            url="https://kabum.com.br/1",
            preco_anterior=100.0,
            preco_atual=90.0,
        )
        mock_tg.assert_not_called()


@pytest.mark.asyncio
async def test_nao_envia_sem_telegram_id() -> None:
    usuarios = [
        {
            "usuario_id": "u1",
            "usuarios": {
                "email": "a@zoiou.com",
                "telegram_id": None,
                "notif_telegram": True,
                "notif_email": False,
            },
        }
    ]
    db = _make_db(usuarios)

    with patch("app.services.notificacao.enviar_notificacao_telegram") as mock_tg, \
         patch("app.services.notificacao.buscar_historico_produto", return_value=[]):
        await despachar_notificacoes(
            db=db,
            produto_id="prod-1",
            nome="Produto X",
            loja="Kabum",
            url="https://kabum.com.br/1",
            preco_anterior=100.0,
            preco_atual=90.0,
        )
        mock_tg.assert_not_called()


@pytest.mark.asyncio
async def test_badge_historico_quando_preco_minimo() -> None:
    """Badge de mínimo histórico é enviado quando preço bate o menor dos últimos 12m."""
    usuarios = [
        {
            "usuario_id": "u1",
            "usuarios": {
                "email": "a@zoiou.com",
                "telegram_id": "123456",
                "notif_telegram": True,
                "notif_email": False,
            },
        }
    ]
    db = _make_db(usuarios)
    historico = [{"preco": "100.0"}, {"preco": "90.0"}, {"preco": "95.0"}]

    with patch("app.services.notificacao.enviar_notificacao_telegram") as mock_tg, \
         patch("app.services.notificacao.buscar_historico_produto", return_value=historico):
        await despachar_notificacoes(
            db=db,
            produto_id="prod-1",
            nome="Produto X",
            loja="Kabum",
            url="https://kabum.com.br/1",
            preco_anterior=100.0,
            preco_atual=89.0,  # abaixo do mínimo histórico (90.0)
        )
        call_kwargs = mock_tg.call_args.kwargs
        assert call_kwargs["eh_historico"] is True
