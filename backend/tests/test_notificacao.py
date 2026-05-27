from unittest.mock import AsyncMock, patch

import pytest

from app.services.telegram import _formatar_mensagem


def test_mensagem_queda_preco() -> None:
    msg = _formatar_mensagem(
        nome="RTX 4060 Ti",
        loja="Kabum",
        preco_anterior=1920.0,
        preco_atual=1850.0,
        url="https://kabum.com.br/produto/123",
        eh_historico=False,
    )
    assert "📉" in msg
    assert "1.920,00" in msg or "1920" in msg
    assert "1.850,00" in msg or "1850" in msg
    assert "Kabum" in msg


def test_mensagem_alta_preco() -> None:
    msg = _formatar_mensagem(
        nome="RTX 4060 Ti",
        loja="Kabum",
        preco_anterior=1850.0,
        preco_atual=1920.0,
        url="https://kabum.com.br/produto/123",
        eh_historico=False,
    )
    assert "📈" in msg


def test_mensagem_preco_historico() -> None:
    msg = _formatar_mensagem(
        nome="RTX 4060 Ti",
        loja="Kabum",
        preco_anterior=1780.0,
        preco_atual=1690.0,
        url="https://kabum.com.br/produto/123",
        eh_historico=True,
    )
    assert "🏆" in msg
    assert "PREÇO HISTÓRICO" in msg
