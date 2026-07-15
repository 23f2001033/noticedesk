import io
from dataclasses import dataclass

from pypdf import PdfReader

from app.services.document_ai import run_document_ai_ocr

PDF_MIME_TYPES = frozenset({"application/pdf"})
IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png"})
MIN_CHARS_PER_PAGE = 200


class UnsupportedDocumentTypeError(ValueError):
    pass


@dataclass
class OcrResult:
    text: str
    ocr_used: bool
    pages: int


def _extract_native_pdf_text(file_bytes: bytes) -> tuple[str, int]:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text), len(reader.pages)


def _has_sufficient_text_density(text: str, page_count: int) -> bool:
    if page_count == 0:
        return False
    return (len(text) / page_count) >= MIN_CHARS_PER_PAGE


def route_ocr(*, file_bytes: bytes, mime_type: str) -> OcrResult:
    """docs/SPEC.md #5 step 2: try native PDF text; fall back to Document AI
    OCR if text density is low or the input is an image."""
    if mime_type in IMAGE_MIME_TYPES:
        text = run_document_ai_ocr(file_bytes=file_bytes, mime_type=mime_type)
        return OcrResult(text=text, ocr_used=True, pages=1)

    if mime_type not in PDF_MIME_TYPES:
        raise UnsupportedDocumentTypeError(f"Unsupported document type: {mime_type!r}")

    native_text, pages = _extract_native_pdf_text(file_bytes)
    if _has_sufficient_text_density(native_text, pages):
        return OcrResult(text=native_text, ocr_used=False, pages=pages)

    ocr_text = run_document_ai_ocr(file_bytes=file_bytes, mime_type=mime_type)
    return OcrResult(text=ocr_text, ocr_used=True, pages=pages)
