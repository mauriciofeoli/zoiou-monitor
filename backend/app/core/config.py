from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: str
    secret_key: str
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    frontend_urls_extras: str = ""  # origens adicionais separadas por vírgula
    ambiente: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


configuracoes = Configuracoes()  # type: ignore[call-arg]
