"""CLI entry point for `make corpus` (docs/SPEC.md #8).

Validates every corpus_src/*.yaml file, embeds and upserts the ones with
reviewed_by set, and prints a summary. Run from the repo root.
"""

import pathlib
import sys

from app.config import get_settings
from app.services.corpus import CorpusSourceError, run_corpus_ingest

CORPUS_SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "corpus_src"


def main() -> int:
    settings = get_settings()
    if not settings.gemini_model_embed:
        print("GEMINI_MODEL_EMBED is not set -- cannot embed corpus items.", file=sys.stderr)
        return 1

    try:
        results = run_corpus_ingest(CORPUS_SRC_DIR, embed_model=settings.gemini_model_embed)
    except CorpusSourceError as exc:
        print(f"Corpus source validation failed: {exc}", file=sys.stderr)
        return 1

    upserted = sum(1 for r in results if r.status == "upserted")
    skipped = sum(1 for r in results if r.status == "skipped_unreviewed")
    print(
        f"Corpus ingest: {upserted} upserted, {skipped} skipped (unreviewed), {len(results)} total."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
