import pytest

from app.services.ocr import UnsupportedDocumentTypeError, _has_sufficient_text_density, route_ocr


def test_has_sufficient_text_density_true() -> None:
    assert _has_sufficient_text_density("x" * 500, 2) is True


def test_has_sufficient_text_density_false() -> None:
    assert _has_sufficient_text_density("short", 3) is False


def test_has_sufficient_text_density_zero_pages() -> None:
    assert _has_sufficient_text_density("", 0) is False


def test_route_ocr_uses_native_text_when_density_sufficient(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ocr._extract_native_pdf_text", lambda file_bytes: ("plenty " * 100, 1)
    )

    def fail_if_called(**kwargs):
        raise AssertionError("Document AI should not be called when text density is sufficient")

    monkeypatch.setattr("app.services.ocr.run_document_ai_ocr", fail_if_called)

    result = route_ocr(file_bytes=b"pdf-bytes", mime_type="application/pdf")

    assert result.ocr_used is False
    assert result.pages == 1
    assert "plenty" in result.text


def test_route_ocr_falls_back_to_document_ai_when_density_low(monkeypatch) -> None:
    monkeypatch.setattr("app.services.ocr._extract_native_pdf_text", lambda file_bytes: ("", 3))
    monkeypatch.setattr(
        "app.services.ocr.run_document_ai_ocr", lambda **kwargs: "ocr extracted text"
    )

    result = route_ocr(file_bytes=b"scanned-pdf-bytes", mime_type="application/pdf")

    assert result.ocr_used is True
    assert result.pages == 3
    assert result.text == "ocr extracted text"


def test_route_ocr_routes_images_directly_to_document_ai(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ocr.run_document_ai_ocr", lambda **kwargs: "ocr text from image"
    )

    result = route_ocr(file_bytes=b"image-bytes", mime_type="image/png")

    assert result.ocr_used is True
    assert result.pages == 1
    assert result.text == "ocr text from image"


def test_route_ocr_raises_for_unsupported_mime_type() -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        route_ocr(file_bytes=b"data", mime_type="application/msword")
