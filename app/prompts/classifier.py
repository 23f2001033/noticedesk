CLASSIFIER_PROMPT_V1 = """You are classifying an Indian GST department notice for NoticeDesk, \
a tool used by chartered accountants.

Read the notice text below and classify it into exactly one of these types:
- "ASMT-10": scrutiny notice under Section 61 pointing out discrepancies in a return.
- "DRC-01A": pre-show-cause intimation of tax ascertained as payable (Rule 142(1A)).
- "DRC-01": formal show cause notice under Section 73 or 74.
- "other": any GST notice that doesn't match the above (e.g. DRC-07, appellate orders, \
  audit memos, recovery notices).

Base the classification only on what's in the notice text -- form numbers, section \
citations, and the notice's own language are the strongest signals. If truly ambiguous, \
prefer "other" and reflect your uncertainty in a lower confidence score rather than \
guessing a specific type.

Respond with the notice_type and a confidence score between 0.0 and 1.0.

Notice text:
---
{notice_text}
---
"""
