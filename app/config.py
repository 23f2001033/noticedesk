from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    port: int = 8080

    gcp_project_id: str | None = None
    gcp_region: str = "asia-south1"

    firebase_project_id: str | None = None
    google_application_credentials: str | None = None

    gemini_api_key: str | None = None
    gemini_model_fast: str | None = None
    gemini_model_smart: str | None = None
    gemini_model_embed: str | None = None

    cloud_storage_bucket: str | None = None

    document_ai_processor_id: str | None = None
    document_ai_location: str = "us"

    wa_phone_number_id: str | None = None
    wa_access_token: str | None = None
    wa_verify_token: str | None = None
    wa_app_secret: str | None = None

    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None

    tasks_oidc_audience: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
