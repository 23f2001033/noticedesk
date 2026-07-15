import time
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiJsonParseError(Exception):
    """Raised when the model's response doesn't parse into the expected schema.

    Callers must treat this as the JSON-parse fallback path (docs/SPEC.md
    #14) -- degrade safely and log status=fallback, never raise to the user.
    """


def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def generate_json(
    *,
    model: str,
    prompt: str,
    response_schema: type[T],
    temperature: float = 0.0,
) -> tuple[T, dict]:
    """Call Gemini with a JSON response schema.

    Returns (parsed_response, usage) where usage has tokens_in/tokens_out/latency_ms.
    Raises GeminiJsonParseError if the response doesn't validate against response_schema.

    NOTE: written against the google-genai SDK surface as currently understood;
    has not been exercised against a live API key (none provisioned yet -- see
    PROGRESS.md). Needs a smoke test against a real GEMINI_API_KEY before Phase 1
    ships to real users. Model IDs are never hardcoded here -- callers pass
    settings.gemini_model_fast/smart, verified against ai.google.dev by Aman.
    """
    client = _get_client()
    started = time.monotonic()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )
    latency_ms = int((time.monotonic() - started) * 1000)

    try:
        parsed = response_schema.model_validate_json(response.text)
    except (ValidationError, ValueError) as exc:
        raise GeminiJsonParseError(str(exc)) from exc

    usage = response.usage_metadata
    return parsed, {
        "tokens_in": getattr(usage, "prompt_token_count", None),
        "tokens_out": getattr(usage, "candidates_token_count", None),
        "latency_ms": latency_ms,
    }


def embed_text(*, model: str, text: str) -> list[float]:
    """Generates an embedding vector for text via the Gemini embedding model
    (docs/SPEC.md #7, #8 -- corpus_chunks retrieval).

    NOTE: same caveat as generate_json -- not yet smoke-tested against a live
    API key.
    """
    client = _get_client()
    response = client.models.embed_content(model=model, contents=text)
    return response.embeddings[0].values
