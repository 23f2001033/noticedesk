# Corpus source

Raw curated legal texts, one `.yaml` file per item (docs/SPEC.md §8). This
folder is intentionally empty except for this README — populating it with
real CGST Act sections, rules, circulars, and case-law holdings is Aman's
curation work (or a CA advisor's), not something to generate from a
language model's memory: an incorrect or invented statutory text here would
violate the citation-lock rule in `CLAUDE.md` just as surely as a
model-invented citation in a draft would.

## Schema

Each file's `id` becomes the Firestore `corpus/{id}` document id and the
identifier used in draft citation markers (`[[cite:ID]]`, §7). Validated
against `CorpusItem` in `app/models/corpus.py`.

```yaml
id: cgst-s16                       # stable, unique -- referenced by citations
type: act_section                  # act_section | rule | circular | instruction | notification | case_law
citation_string: "CGST Act, 2017, Section 16"
source_url: "https://..."          # public-domain source; never a paid database
effective_dates: "01-07-2017 onwards"   # optional
verbatim_text: |
  The exact quotable statutory/holding text. This is what gets inserted
  wherever a draft cites this item -- it must be copied verbatim from the
  source, not paraphrased or reconstructed from memory.
summary: "One-line plain-English summary."   # optional
issue_tags:
  - itc_2a_3b_mismatch
added_by: aman                     # who curated this entry
reviewed_by: aman                  # optional -- OMIT until reviewed.
                                    # Absent reviewed_by = validated and
                                    # stored in `corpus` for visibility, but
                                    # never embedded into `corpus_chunks`,
                                    # so it's structurally unusable by the
                                    # drafter's retrieval step until set.
```

## Ingesting

```bash
make corpus   # runs scripts/corpus_ingest.py
```

Validates every file here, embeds + upserts the reviewed ones to Firestore
(`corpus` + `corpus_chunks`). Requires `GEMINI_MODEL_EMBED` and a live GCP
project (see `PROGRESS.md` for current status).

## Known simplification

The spec notes corpus items are "immutable once reviewed; edits create a
new version" — that versioning (detect an existing item, bump `version`,
preserve `reviewed_by` only if `verbatim_text` is unchanged) isn't
implemented yet; every ingest currently just overwrites `version: 1`. Worth
revisiting once real curation and edits actually start happening.
