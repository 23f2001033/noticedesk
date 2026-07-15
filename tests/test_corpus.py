from pathlib import Path

import pytest

from app.models.corpus import CorpusItem, CorpusItemType
from app.services.corpus import (
    CorpusSourceError,
    CorpusSourceRecord,
    chunk_verbatim_text,
    ingest_corpus_item,
    load_corpus_source_records,
    parse_corpus_source_file,
)

# NOTE: all "verbatim_text" / "citation_string" values below are obviously
# fictional test fixtures -- not real CGST law. See corpus_src/README.md.
FIXTURE_YAML = """\
id: test-fixture-001
type: act_section
citation_string: "Test Fixture Act, s. 1"
source_url: "https://example.invalid/test-fixture-act"
verbatim_text: "Placeholder text for testing the corpus pipeline only; not real law."
summary: "Test fixture item."
issue_tags: ["test_tag"]
added_by: "test-harness"
"""


def _write_fixture(tmp_path: Path, content: str, name: str = "test-fixture-001.yaml") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_corpus_source_file_valid(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path, FIXTURE_YAML)

    record = parse_corpus_source_file(path)

    assert record.item_id == "test-fixture-001"
    assert record.item.type == CorpusItemType.ACT_SECTION
    assert record.item.reviewed_by is None


def test_parse_corpus_source_file_missing_id(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path, "type: act_section\ncitation_string: x\n", name="bad.yaml")

    with pytest.raises(CorpusSourceError):
        parse_corpus_source_file(path)


def test_parse_corpus_source_file_invalid_schema(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path, "id: bad-1\ntype: not_a_real_type\n", name="bad2.yaml")

    with pytest.raises(CorpusSourceError):
        parse_corpus_source_file(path)


def test_load_corpus_source_records_reads_all_files_sorted(tmp_path: Path) -> None:
    _write_fixture(tmp_path, FIXTURE_YAML.replace("test-fixture-001", "b-item"), name="b.yaml")
    _write_fixture(tmp_path, FIXTURE_YAML.replace("test-fixture-001", "a-item"), name="a.yaml")

    records = load_corpus_source_records(tmp_path)

    assert [r.item_id for r in records] == ["a-item", "b-item"]


def test_chunk_verbatim_text_short_text_single_chunk() -> None:
    assert chunk_verbatim_text("short text") == ["short text"]


def test_chunk_verbatim_text_empty_text() -> None:
    assert chunk_verbatim_text("") == []


def test_chunk_verbatim_text_splits_long_text_with_overlap() -> None:
    text = "x" * 2500

    chunks = chunk_verbatim_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 3
    assert all(len(c) <= 1000 for c in chunks)
    assert chunks[0][-100:] == chunks[1][:100]


def _make_record(
    item_id: str = "test-fixture-001", reviewed_by: str | None = None
) -> CorpusSourceRecord:
    item = CorpusItem(
        type=CorpusItemType.ACT_SECTION,
        citation_string="Test Fixture Act, s. 1",
        source_url="https://example.invalid/test-fixture-act",
        verbatim_text="Placeholder statutory text for tests only, not real law.",
        summary="Test fixture.",
        issue_tags=["test_tag"],
        added_by="test-harness",
        reviewed_by=reviewed_by,
    )
    return CorpusSourceRecord(item_id=item_id, item=item, source_path=Path("fake.yaml"))


def test_ingest_corpus_item_skips_unreviewed(monkeypatch, fake_firestore_recorder) -> None:
    monkeypatch.setattr("app.services.corpus.get_firestore_client", lambda: fake_firestore_recorder)

    def fail_if_called(**kwargs):
        raise AssertionError("should not embed an unreviewed item")

    monkeypatch.setattr("app.services.corpus.embed_text", fail_if_called)

    result = ingest_corpus_item(_make_record(reviewed_by=None), embed_model="test-embed-model")

    assert result.status == "skipped_unreviewed"
    assert result.chunks_written == 0
    collections_written = {c for c, _ in fake_firestore_recorder.writes}
    assert collections_written == {"corpus"}


def test_ingest_corpus_item_embeds_and_upserts_reviewed(
    monkeypatch, fake_firestore_recorder
) -> None:
    monkeypatch.setattr("app.services.corpus.get_firestore_client", lambda: fake_firestore_recorder)
    monkeypatch.setattr("app.services.corpus.embed_text", lambda **kwargs: [0.1, 0.2, 0.3])

    result = ingest_corpus_item(_make_record(reviewed_by="aman"), embed_model="test-embed-model")

    assert result.status == "upserted"
    assert result.chunks_written == 1
    collections_written = [c for c, _ in fake_firestore_recorder.writes]
    assert collections_written.count("corpus") == 1
    assert collections_written.count("corpus_chunks") == 1
