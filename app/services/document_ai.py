from functools import lru_cache

from google.cloud import documentai

from app.config import get_settings


@lru_cache
def _get_client() -> documentai.DocumentProcessorServiceClient:
    return documentai.DocumentProcessorServiceClient()


def run_document_ai_ocr(*, file_bytes: bytes, mime_type: str) -> str:
    """Runs the configured Document AI OCR processor, returns extracted text.

    NOTE: not yet smoke-tested against a live processor -- no GCP project or
    provisioned processor yet (see PROGRESS.md). Written from current
    understanding of the google-cloud-documentai SDK surface.
    """
    settings = get_settings()
    if not settings.gcp_project_id or not settings.document_ai_processor_id:
        raise RuntimeError("GCP_PROJECT_ID and DOCUMENT_AI_PROCESSOR_ID must both be configured")

    client = _get_client()
    name = client.processor_path(
        settings.gcp_project_id, settings.document_ai_location, settings.document_ai_processor_id
    )
    raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    return result.document.text
