"""CLI entry point for `make eval` (docs/SPEC.md #14, deploy gate).

Runs the classifier + extractor pipeline against evals/golden_notices/*.json
and checks the >=90% field-accuracy / 100% due-date-or-flag gates. An empty
golden set passes trivially -- see evals/golden_notices/README.md for why
it's empty right now. Requires GEMINI_API_KEY/GEMINI_MODEL_FAST to be
configured; not meaningful to run until then.
"""

import pathlib
import sys

from app.services.eval_notices import GoldenSourceError, run_eval

GOLDEN_DIR = pathlib.Path(__file__).resolve().parent.parent / "evals" / "golden_notices"


def main() -> int:
    try:
        summary = run_eval(GOLDEN_DIR)
    except GoldenSourceError as exc:
        print(f"Golden notice validation failed: {exc}", file=sys.stderr)
        return 1

    if not summary.results:
        print("No golden notices found in evals/golden_notices/ -- nothing to evaluate yet.")
        return 0

    accuracy = summary.field_accuracy
    due_date_rate = summary.due_date_pass_rate
    print(
        f"Eval: {len(summary.results)} cases, "
        f"field accuracy {accuracy:.0%} (gate >=90%), "
        f"due-date-or-flag {due_date_rate:.0%} (gate 100%)"
    )

    if not summary.passes_gates():
        print("Eval gate FAILED.", file=sys.stderr)
        return 1

    print("Eval gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
