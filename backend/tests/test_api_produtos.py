"""Testes de integração para os endpoints de produtos.

Usa mocks do Supabase para não depender de infraestrutura real em CI.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import obter_cliente_rls
from app.core.security import obter_usuario_autenticado
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def mock_usuario() -> dict:
    return {"id": "user-123", "email": "test@zoiou.com"}


@pytest.fixture()
def mock_produto() -> dict:
    return {
        "id": "prod-abc",
        "nome": "RTX 4060 Ti",
        "url": "https://kabum.com.br/produto/123",
        "loja": "Kabum",
        "imagem": None,
        "preco_atual": 1850.0,
        "preco_anterior": 1920.0,
        "ativo": True,
        "monitorando_ha_dias": 7,
        "ultima_atualizacao": "2025-01-01T03:00:00Z",
    }


class TestListarProdutos:
    def test_sem_token_retorna_401(self, client: TestClient) -> None:
        resp = client.get("/api/produtos")
        assert resp.status_code == 401

    def test_com_token_valido_retorna_200(
        self, client: TestClient, mock_usuario: dict
    ) -> None:
        db_mock = MagicMock()
        db_mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        app.dependency_overrides[obter_usuario_autenticado] = lambda: mock_usuario
        app.dependency_overrides[obter_cliente_rls] = lambda: db_mock

        try:
            resp = client.get(
                "/api/produtos",
                headers={"Authorization": "Bearer token-valido"},
            )
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.clear()


class TestAdicionarProduto:
    def test_sem_token_retorna_401(self, client: TestClient) -> None:
        resp = client.post("/api/produtos", json={"url": "https://kabum.com.br/123"})
        assert resp.status_code == 401

    def test_url_invalida_retorna_422(self, client: TestClient, mock_usuario: dict) -> None:
        app.dependency_overrides[obter_usuario_autenticado] = lambda: mock_usuario
        app.dependency_overrides[obter_cliente_rls] = lambda: MagicMock()

        try:
            resp = client.post(
                "/api/produtos",
                json={"url": "nao-e-uma-url"},
                headers={"Authorization": "Bearer token-valido"},
            )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestRateLimiting:
    def test_alem_do_limite_retorna_429(self, client: TestClient) -> None:
        """Mais de 10 requisições por minuto em POST /api/produtos → 429."""
        respostas = [
            client.post("/api/produtos", json={"url": "https://kabum.com.br/123"})
            for _ in range(12)
        ]
        codigos = [r.status_code for r in respostas]
        assert 429 in codigos, f"Esperava 429 nos últimos requests, got: {codigos}"
