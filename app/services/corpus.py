from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.models.corpus import CorpusChunk, CorpusItem
from app.services.firestore import get_firestore_client
from app.services.gemini import embed_text

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


class CorpusSourceError(ValueError):
    """A corpus_src/*.yaml file failed to parse or validate."""


@dataclass
class CorpusSourceRecord:
    item_id: str
    item: CorpusItem
    source_path: Path


@dataclass
class IngestResult:
    item_id: str
    status: str  # "upserted" | "skipped_unreviewed"
    chunks_written: int


def parse_corpus_source_file(path: Path) -> CorpusSourceRecord:
    """docs/SPEC.md #8: corpus_src/*.yaml -- id, type, citation_string,
    source_url, effective_dates, verbatim_text, summary, issue_tags, plus
    added_by (who curated it) and an optional reviewed_by (who approved it;
    absent = not yet retrievable)."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "id" not in raw:
        raise CorpusSourceError(f"{path}: missing required 'id' field")

    item_id = raw.pop("id")
    try:
        item = CorpusItem(**raw)
    except ValidationError as exc:
        raise CorpusSourceError(f"{path}: {exc}") from exc

    return CorpusSourceRecord(item_id=item_id, item=item, source_path=path)


def load_corpus_source_records(corpus_src_dir: Path) -> list[CorpusSourceRecord]:
    return [parse_corpus_source_file(p) for p in sorted(corpus_src_dir.glob("*.yaml"))]


def chunk_verbatim_text(
    text: str, *, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Fixed-size sliding-window chunking for corpus_chunks embeddings (§7 step 2).

    Simple by design -- no real corpus content exists yet to tune this
    against (see PROGRESS.md); revisit once real curated items exist.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    step = chunk_size - overlap
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += step
    return chunks


def ingest_corpus_item(record: CorpusSourceRecord, *, embed_model: str) -> IngestResult:
    """docs/SPEC.md #8: validate -> embed -> upsert.

    Items without reviewed_by are written to `corpus` (for admin/review
    visibility) but never to `corpus_chunks` -- structurally unretrievable
    by the drafter's vector search until reviewed, per "Every item requires
    reviewed_by ... before it becomes retrievable."
    """
    db = get_firestore_client()
    db.collection("corpus").document(record.item_id).set(record.item.model_dump(mode="json"))

    if not record.item.reviewed_by:
        return IngestResult(item_id=record.item_id, status="skipped_unreviewed", chunks_written=0)

    chunks = chunk_verbatim_text(record.item.verbatim_text)
    for i, chunk_text in enumerate(chunks):
        embedding = embed_text(model=embed_model, text=chunk_text)
        chunk = CorpusChunk(
            corpus_item_id=record.item_id, chunk_text=chunk_text, embedding=embedding
        )
        db.collection("corpus_chunks").document(f"{record.item_id}__{i}").set(
            chunk.model_dump(mode="json")
        )

    return IngestResult(item_id=record.item_id, status="upserted", chunks_written=len(chunks))


def run_corpus_ingest(corpus_src_dir: Path, *, embed_model: str) -> list[IngestResult]:
    records = load_corpus_source_records(corpus_src_dir)
    return [ingest_corpus_item(record, embed_model=embed_model) for record in records]
