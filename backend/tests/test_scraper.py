import pytest

from app.services.scraper import parsear_preco


def test_parsear_preco_virgula() -> None:
    assert parsear_preco("R$ 1.850,99") == 1850.99


def test_parsear_preco_sem_centavos() -> None:
    assert parsear_preco("R$ 499") == 499.0


def test_parsear_preco_espaco_unicode() -> None:
    assert parsear_preco("R$\xa01.234,56") == 1234.56


def test_parsear_preco_sem_simbolo() -> None:
    assert parsear_preco("2.199,00") == 2199.0


def test_parsear_preco_invalido() -> None:
    with pytest.raises(ValueError):
        parsear_preco("sem preço")
