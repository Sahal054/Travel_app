from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Travelling Salesman API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://roamy:roamy@db:5432/roamy"
    )
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None
    log_level: str = "INFO"

    # Comma-separated origins allowed to call the API
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    media_storage_backend: str = "local"  # "local" or "s3"
    media_local_dir: str = "/tmp/ts_media"

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str = "ap-south-1"
    s3_bucket_name: str | None = None
    s3_prefix: str = "reels"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()