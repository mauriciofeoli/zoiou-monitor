"""Testes de autenticação e autorização."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestAutenticacao:
    def test_sem_authorization_header_retorna_401(self, client: TestClient) -> None:
        resp = client.get("/api/produtos")
        assert resp.status_code == 401

    def test_token_malformado_retorna_401(self, client: TestClient) -> None:
        resp = client.get("/api/produtos", headers={"Authorization": "NaoBearer abc"})
        assert resp.status_code == 401

    def test_bearer_vazio_retorna_401(self, client: TestClient) -> None:
        resp = client.get("/api/produtos", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401

    def test_token_invalido_supabase_retorna_401(self, client: TestClient) -> None:
        with patch("app.core.security.obter_usuario_autenticado") as mock_auth:
            mock_auth.side_effect = Exception("JWT expired")
            resp = client.get(
                "/api/produtos",
                headers={"Authorization": "Bearer token-expirado"},
            )
            assert resp.status_code == 401

    def test_health_nao_requer_auth(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
