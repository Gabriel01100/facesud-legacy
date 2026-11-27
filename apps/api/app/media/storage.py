import re
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings


class MediaStorageError(Exception):
    pass


class MediaStorage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}\.webp$")


def _validate_key(key: str) -> None:
    if not _KEY_PATTERN.fullmatch(key):
        raise MediaStorageError("Invalid media storage key.")


class LocalMediaStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        _validate_key(key)
        path = (self.root / key).resolve()
        if path.parent != self.root:
            raise MediaStorageError("Invalid media storage path.")
        return path

    def put(self, key: str, content: bytes, content_type: str) -> None:
        path = self._path(key)
        temporary = path.with_suffix(".tmp")
        try:
            temporary.write_bytes(content)
            temporary.replace(path)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise MediaStorageError("Media could not be stored.") from exc

    def get(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise MediaStorageError("Media object not found.") from exc
        except OSError as exc:
            raise MediaStorageError("Media could not be read.") from exc

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink(missing_ok=True)
        except OSError as exc:
            raise MediaStorageError("Media could not be deleted.") from exc


class S3MediaStorage:
    def __init__(self):
        if not all((settings.media_s3_bucket, settings.media_s3_access_key_id, settings.media_s3_secret_access_key)):
            raise MediaStorageError("S3 media storage requires a bucket and credentials.")
        self.bucket = settings.media_s3_bucket
        self.client = boto3.client(
            "s3",
            region_name=settings.media_s3_region,
            endpoint_url=settings.media_s3_endpoint_url,
            aws_access_key_id=settings.media_s3_access_key_id,
            aws_secret_access_key=settings.media_s3_secret_access_key,
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    def put(self, key: str, content: bytes, content_type: str) -> None:
        _validate_key(key)
        try:
            self.client.put_object(
                Bucket=self.bucket, Key=key, Body=content, ContentType=content_type,
                ServerSideEncryption="AES256",
            )
        except Exception as exc:
            raise MediaStorageError("Media could not be stored.") from exc

    def get(self, key: str) -> bytes:
        _validate_key(key)
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            raise MediaStorageError("Media object not found.") from exc

    def delete(self, key: str) -> None:
        _validate_key(key)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            raise MediaStorageError("Media could not be deleted.") from exc


_storage: MediaStorage | None = None


def get_media_storage() -> MediaStorage:
    global _storage
    if _storage is None:
        backend = settings.media_storage_backend.strip().lower()
        if backend == "local":
            _storage = LocalMediaStorage(settings.media_storage_path)
        elif backend == "s3":
            _storage = S3MediaStorage()
        else:
            raise MediaStorageError("Unsupported media storage backend.")
    return _storage
