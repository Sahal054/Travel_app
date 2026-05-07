from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Roamy API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://roamy:roamy@db:5432/roamy"
    )
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    media_storage_backend: str = "local"  # "local" or "s3"
    media_local_dir: str = "/tmp/roamy_media"

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str = "ap-south-1"
    s3_bucket_name: str | None = None
    s3_prefix: str = "reels"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()