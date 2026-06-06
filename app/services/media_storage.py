import os
import shutil
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class MediaStorage(Protocol):
    def store_file(self, source_path: Path, destination_key: str) -> str:
        ...


class LocalMediaStorage(MediaStorage):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.media_local_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store_file(self, source_path: Path, destination_key: str) -> str:
        # Create subdirectories if the key has them
        dest_path = self.base_dir / destination_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        return str(dest_path.absolute())


class S3MediaStorage(MediaStorage):
    def __init__(self):
        import boto3 # Type error safe if backend is local and no boto3 is installed
        self.bucket = settings.s3_bucket_name
        self.prefix = settings.s3_prefix
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token,
            region_name=settings.aws_region,
        )

    def store_file(self, source_path: Path, destination_key: str) -> str:
        if not self.bucket:
            raise ValueError("S3_BUCKET_NAME is not configured")
            
        full_key = f"{self.prefix}/{destination_key}".strip("/")
        
        self.client.upload_file(
            Filename=str(source_path),
            Bucket=self.bucket,
            Key=full_key,
        )
        # Return an S3 URI that we can store in the DB
        return f"s3://{self.bucket}/{full_key}"


def get_media_storage() -> MediaStorage:
    if settings.media_storage_backend.lower() == "s3":
        return S3MediaStorage()
    return LocalMediaStorage()