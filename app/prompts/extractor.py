EXTRACTOR_PROMPT_V1 = """You are extracting structured data from an Indian GST department \
notice (classified as {notice_type}) for NoticeDesk, a tool used by chartered accountants.

Extract these fields from the notice text:
- gstin: the taxpayer's GSTIN.
- legal_name: the taxpayer's registered legal name.
- fy_period: the financial year / tax period(s) the notice concerns.
- notice_no: the notice's reference/file number.
- din: the Document Identification Number, if present.
- notice_date: the date the notice was issued.
- due_date: the date by which a reply is due, ONLY if the notice states one explicitly. \
  Do not compute or infer a due date -- leave it null if it isn't stated, so the caller can \
  apply the statutory default and flag it for CA confirmation.
- officer: the issuing officer's designation and jurisdiction.
- sections_invoked: CGST Act sections and rules the notice cites.
- total_demand: the total amount demanded, if stated.
- discrepancy_table: one row per distinct issue raised in the notice, each with \
  issue_description, tax_period, amount, tax_head, and source_of_mismatch (e.g. "GSTR-1 vs \
  GSTR-3B", "ITC in 3B vs 2A/2B", "e-way bill vs outward supply").

For every field above, also record field_confidence as one of:
- "found": the value is stated explicitly in the notice text.
- "inferred": the value is reasonably implied but not stated verbatim.
- "absent": the notice doesn't contain this information.

Never fabricate a value that isn't in the notice text -- an absent field must be null with
confidence "absent", not a guess.

Notice text:
---
{notice_text}
---
"""
