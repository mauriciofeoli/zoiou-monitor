import pytest

from app.services.historico import calcular_estatisticas, eh_preco_historico


def test_detectar_preco_historico_true() -> None:
    historico = [1920.0, 1850.0, 2100.0, 1780.0]
    assert eh_preco_historico(1750.0, historico) is True


def test_detectar_preco_historico_igual_ao_minimo() -> None:
    historico = [1920.0, 1850.0, 1780.0]
    assert eh_preco_historico(1780.0, historico) is True


def test_detectar_preco_historico_false() -> None:
    historico = [1920.0, 1850.0, 1780.0]
    assert eh_preco_historico(1800.0, historico) is False


def test_detectar_preco_historico_lista_vazia() -> None:
    assert eh_preco_historico(100.0, []) is False


def test_calcular_estatisticas_basico() -> None:
    historico = [
        {"preco": "100.00"},
        {"preco": "200.00"},
        {"preco": "150.00"},
    ]
    minimo, maximo, media = calcular_estatisticas(historico)
    assert minimo == 100.0
    assert maximo == 200.0
    assert media == 150.0


def test_calcular_estatisticas_lista_vazia() -> None:
    assert calcular_estatisticas([]) == (None, None, None)
