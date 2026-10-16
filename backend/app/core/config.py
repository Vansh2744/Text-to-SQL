from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://querypilot:querypilot@localhost:5432/querypilot"

    auth_mode: str = "clerk"
    clerk_issuer: str = ""
    clerk_jwks_url: str = ""

    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "" 

    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50
    max_columns: int = 200

    query_timeout_seconds: float = 15
    max_result_rows: int = 1000
    max_concurrent_queries: int = 4
    duckdb_memory_limit: str = "512MB"
    duckdb_threads: int = 2
    sql_retry_limit: int = 1
    rate_limit_per_minute: int = 30

    @model_validator(mode="after")
    def _check_auth(self):
        if self.auth_mode == "dev" and self.app_env == "production":
            raise ValueError("AUTH_MODE=dev is not allowed when APP_ENV=production")
        if self.auth_mode == "clerk" and not (self.clerk_issuer and self.clerk_jwks_url):
            raise ValueError("CLERK_ISSUER and CLERK_JWKS_URL are required when AUTH_MODE=clerk")
        if self.auth_mode not in ("clerk", "dev"):
            raise ValueError("AUTH_MODE must be 'clerk' or 'dev'")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
