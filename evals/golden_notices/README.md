# Golden notices

Anonymized real GST notices with expected extraction results, used to gate
extraction quality (docs/SPEC.md §14: ≥15 notices, ≥90% field accuracy on
found fields, 100% on due-date-or-flag behavior).

This folder is intentionally empty except for this README. Collecting real
notices is Aman's work (via his CA network, per §16 GTM) — stripped of
identifying details before they land here. There's no synthetic substitute
worth building: the entire point of this gate is catching extraction
failures against real notice formats/wording, which can't be faked
convincingly enough to be a meaningful test.

## Schema

One `.json` file per notice, validated against `GoldenCase` in
`app/services/eval_notices.py`:

```json
{
  "id": "golden-001",
  "notice_type": "ASMT-10",
  "notice_text": "... anonymized notice text, GSTIN/names/amounts kept but identifying info stripped ...",
  "expected_extraction": {
    "gstin": "27ABCDE1234F1Z5",
    "legal_name": "Example Traders",
    "fy_period": "2024-25",
    "due_date": "2026-08-15",
    "total_demand": 125000
  }
}
```

`expected_extraction` only needs the fields you want scored — omit any
field the notice doesn't state. Omit `due_date` entirely (or set it to
`null`) for a notice that genuinely doesn't state one; the gate then checks
that the extractor correctly flags it absent rather than guessing.

## Running

```bash
make eval   # runs scripts/eval_notices.py
```

Wired into CI already (`.github/workflows/ci.yml`) — passes trivially with
zero golden notices, and starts actually gating the moment real ones land
here.
