from functools import lru_cache

from google.cloud import storage

from app.config import get_settings


@lru_cache
def get_storage_client() -> storage.Client:
    settings = get_settings()
    return storage.Client(project=settings.gcp_project_id)


def upload_document(*, file_bytes: bytes, destination_path: str, content_type: str) -> str:
    """Uploads to the configured bucket, returns a gs:// storage_ref.

    NOTE: not yet smoke-tested against a live bucket -- no GCP project yet.
    """
    settings = get_settings()
    if not settings.cloud_storage_bucket:
        raise RuntimeError("CLOUD_STORAGE_BUCKET is not configured")

    client = get_storage_client()
    bucket = client.bucket(settings.cloud_storage_bucket)
    blob = bucket.blob(destination_path)
    blob.upload_from_string(file_bytes, content_type=content_type)
    return f"gs://{settings.cloud_storage_bucket}/{destination_path}"
