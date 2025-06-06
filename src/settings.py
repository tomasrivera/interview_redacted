from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    mongo_url: str = "mongodb://user:pass@localhost:27017"
    mongo_db_name: str = "flights"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_username: str | None = None
    redis_password: str | None = None

    celery_broker: str = "redis://localhost:6379"
    celery_result_backend: str = "redis://localhost:6379"


settings = Settings()
