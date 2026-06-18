from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./production.db"
    api_base_url: str = "http://89.252.189.91:8983"
    api_key: str = ""
    sync_max_retries: int = 3
    sync_retry_delay_seconds: float = 2.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
