# NoticeDesk — Full Specification
**Version 1.0 · July 15, 2026 · Owner: Aman Kumar Maurya**

Referenced from `CLAUDE.md`. Decision points marked `[DECISION-n]` are Aman's to confirm; do not resolve them silently.

## §1. Mission and market context (for README + hackathon narrative)

**One-liner:** The GST department uses AI to issue notices at machine scale — 4.2 lakh+ a year against 1.4 crore GSTINs. NoticeDesk gives the 1 lakh small CA firms of India an AI litigation workspace to answer back: every notice summarized in 30 seconds, every deadline tracked, every draft grounded in verifiable law.

**Market facts to use (verified July 2026; keep phrasing conservative):**
- 4.2 lakh+ departmental notices in a recent fiscal year; GSTN risk analytics auto-flag return mismatches, so notice volume is structurally rising.
- A mid-size firm handles 200–400 notices/year at 4–8 CA-hours each; industry chatter: ~1 in 3 firms missed a reply deadline in the past year; a missed deadline can become an ex-parte confirmed demand (real cases: ₹12–18 lakh demands from clerical mismatches).
- GSTAT (GST Appellate Tribunal) operationalized Sept 2025; ~4.8 lakh backlog appeals, ₹1 lakh crore+ in dispute; backlog filing deadline extended to July 31, 2026; orders from April 1, 2026 onward carry rolling 3-month appeal windows. Hearings will run for years → sustained litigation workload.
- Buyers: ~1.61 lakh CAs in practice across ~1 lakh firms (73k sole proprietors, 27k partnerships) + tens of thousands of GST practitioners/tax advocates.

**Competitive positioning (be explicit in README):** pay-per-draft tools exist at ₹199–299/notice (GST Notice AI, GST Reply AI) and credit plans (Quick Litigate ₹2,999/yr), plus GSTGuard (₹999/mo) and enterprise suites (IRIS, PwC Navigate). NoticeDesk differentiates on: (1) firm-level workspace — all clients/notices/deadlines in one board vs one-document-at-a-time tools; (2) **verifiable citation pack** — every authority clickable to the exact stored text, zero model-memory citations; (3) WhatsApp-native intake/reminders for tier-2/3 practice reality; (4) lifecycle: notice → reply → order → appeal in one case file, timed to the GSTAT era. Drafting is a feature; the workspace is the product.

**Judging criteria mapping:**
| Criterion | Answer |
|---|---|
| Business Viability | Firm subscriptions (₹1,499–2,999/mo) + per-draft entry pricing; free deadline board as acquisition hook; Razorpay/bank evidence; costs ≈ credits → clean margins |
| AI-Native Operations | AI classifies, extracts, schedules, decides reminder cadence, drafts, verifies citations, runs support/onboarding/marketing; humans do professional review + sales; all runs logged/dashboarded |
| Category Impact | Category: **Professional Services** (fallback: Small Business Services — `[DECISION-1]`). Story: solo practitioners in small cities get large-firm litigation infrastructure; SMEs get affordable, faster defense against machine-generated demands |

## §2. Actors and top-level flows

- **CA / firm partner** (buyer): owns clients, reviews and signs drafts, pays.
- **Firm staff** (article assistants/juniors): upload notices, fill questionnaires, prep evidence.
- **Aman (operator):** onboarding, corpus curation approvals, escalations, sales.
- (Clients of the firm are NOT users in MVP — the CA is our user. `[DECISION-2]` if a business-direct tier is ever added.)

**Flow 1 — New notice:** upload PDF/image (web) or forward to firm's NoticeDesk WhatsApp → OCR if needed → classify + extract → **summary card** (type, GSTIN, period, sections, demand table, officer, due date) → deadline auto-added to firm board with T-7/T-3/T-1 WhatsApp reminders. Free tier ends here — this alone beats spreadsheets.

**Flow 2 — Draft reply (paid):** open case → dynamic questionnaire (3–8 case-specific questions Gemini generates from the notice's actual discrepancies) → optional evidence uploads (returns extracts, reconciliation Excel, invoice lists) → drafting agent produces sectioned reply (facts → point-wise rebuttal per discrepancy → legal grounds with corpus citations → prayer) → **verify pane**: citations listed, each expandable to exact quoted text + source; unsupported points show `[CA to insert authority]` → CA edits in rich editor, regenerates per section → export DOCX/PDF on firm letterhead → status → `reply_filed` (manual portal filing by CA).

**Flow 3 — Lifecycle tracking:** reply_filed → outcome recorded (dropped / order passed) → if adverse order: appeal window countdown (3 months) auto-created + appeal checklist (pre-deposit calculator: 10% of disputed tax; Phase-2 drafting of grounds of appeal `[DECISION-3]`).

**Flow 4 — Firm ops:** weekly digest to partner (open notices, approaching deadlines, drafts pending review); monthly usage/billing summary.

## §3. Data model (Firestore)

**`firms/{firm_id}`**: name, city, plan (free|solo|firm), seats, letterhead asset ref, wa_number (firm's registered WhatsApp for intake), member_emails[], razorpay_customer_ref, created_at.
**`users/{uid}`**: firm_id, role (partner|staff|operator), email, phone.
**`clients/{client_id}`**: firm_id, trade_name, gstin(s)[], contact, notes. (Client records are thin — we are not a books system.)
**`cases/{case_id}`**: firm_id, client_id, notice_type (ASMT-10|DRC-01A|DRC-01|other), fy_period, sections_invoked[], demand_amount, officer, din, notice_date, due_date, status (new|in_prep|draft_ready|reply_filed|dropped|order_passed|appeal_window|closed), appeal_due_date?, assigned_uid, source (web|whatsapp), created_at.
**`cases/{id}/documents/{doc_id}`**: kind (notice|evidence|export), storage_ref, ocr_used, pages, uploaded_by, ts.
**`cases/{id}/extraction`**: single doc — full structured extraction JSON + per-field confidence + `discrepancy_table[]` (issue, period, amount, tax_head).
**`cases/{id}/qa/{q_id}`**: question, answer, answered_by, ts.
**`cases/{id}/drafts/{draft_id}`**: version, sections[] ({heading, body, citation_ids[]}), unsupported_points[], created_by_run, editor_state, exported_refs[].
**`corpus/{item_id}`**: type (act_section|rule|circular|instruction|notification|case_law), citation_string, source_url, effective_dates, verbatim_text (the quotable holding/para), summary, issue_tags[], embedding, added_by, reviewed_by, version. **Immutable once reviewed; edits create new version.**
**`corpus_chunks/{chunk_id}`**: corpus_item_id, chunk_text, embedding (for retrieval; citations always resolve to parent item).
**`agent_runs/{run_id}`**: agent, firm_id?, case_id?, trigger, input_digest (≤300 chars, PII-minimized), decision, reasoning_digest, output_digest, model, tokens_in/out, latency_ms, status (ok|error|fallback), ts.
**`payments/{id}`**: firm_id, amount_inr, usd_equiv, razorpay_ref, kind (draft_credit|subscription|setup), period, related_party: bool, notes, ts.
**`metrics_daily/{date}`**: notices_ingested, summaries_generated, drafts_generated, drafts_exported, deadlines_tracked, reminders_sent, active_firms, revenue_inr, agent_runs_total, avg_summary_latency_ms.
**`kb_gaps/{id}`**: point needing authority, case_id, issue_tag, status (open|corpus_added|rejected) — feeds corpus curation queue.

## §4. Repository layout

```
noticedesk/
├── CLAUDE.md · PROGRESS.md · README.md · LICENSE · Makefile · Dockerfile · .env.example
├── app/
│   ├── main.py · config.py · deps.py
│   ├── routers/ (auth.py, cases.py, drafts.py, corpus_admin.py, whatsapp.py,
│   │             razorpay.py, tasks.py, evidence.py)
│   ├── services/ (gemini.py, firestore.py, ocr.py, storage.py, rag.py,
│   │              wa_client.py, deadlines.py, exporter.py, logging_runs.py)
│   ├── agents/ (classifier.py, extractor.py, questioner.py, drafter.py,
│   │            citation_verifier.py, reminder.py, support.py, marketing.py,
│   │            digest.py, billing.py)
│   ├── prompts/ · models/
├── webapp/src/pages/ (Login, Board, CaseDetail, DraftEditor, Clients,
│                      CorpusAdmin, Evidence, Settings, Billing)
├── corpus_src/            # raw curated legal texts (yaml/md per item) — reviewed by human
├── scripts/ (corpus_ingest.py, eval_notices.py, seed_demo.py,
│             onboard_firm.py, export_evidence.py)
├── evals/golden_notices/  # anonymized real notices + expected extraction JSONs
└── tests/
```

## §5. Ingestion & extraction pipeline

1. **Intake:** web upload (PDF/JPG/PNG, ≤25 MB) or WhatsApp media forwarded to firm's NoticeDesk number (map sender → firm; unknown sender → onboarding reply). Store original in Cloud Storage.
2. **OCR routing:** try native PDF text; if text density below threshold or image input → Document AI OCR. Record `ocr_used`.
3. **Classifier agent** (FAST, temp 0, JSON schema): notice_type ∈ {ASMT-10, DRC-01A, DRC-01, other} + confidence. `other` → summary-only mode, flag "unsupported type for drafting (yet)"; still track deadline.
4. **Extractor agent** (FAST, JSON schema): gstin, legal_name, fy/period, notice_no, din, notice_date, **due_date**, officer designation/jurisdiction, sections_invoked[], total_demand, discrepancy_table[] (issue_description, tax_period, amount, tax_head, source_of_mismatch). Per-field `found|inferred|absent` confidence. Absent due_date → compute per statutory default for the notice type AND flag for CA confirmation (never silently guess a deadline).
5. **Summary card** rendered ≤30s p50 from upload. Deadline written to board + reminder schedule (T-7/T-3/T-1, quiet hours 21:00–09:00 IST).
6. `log_agent_run` for every step.

## §6. Questionnaire & evidence

**Questioner agent** (SMART, JSON): input = extraction + notice text; output = 3–8 case-specific questions, each tied to a discrepancy row, each with answer_type (yes_no|text|number|file_request) and why_it_matters one-liner. Examples it should produce for an ITC-mismatch DRC-01: "Were tax invoices held for the ₹X ITC from supplier {name}?"; "Was payment to supplier within 180 days (Rule 37)?"; "Did the ITC reflect in GSTR-2A/2B for the period?". Staff answers; files attach to case. No generic forms — questions must reference actual amounts/suppliers/periods from the notice.

## §7. Drafting engine (the trust product)

1. **Issue tagging:** map each discrepancy row → issue_tags (e.g., `itc_2a_3b_mismatch`, `supplier_retro_cancellation`, `rule_36_4`, `eway_discrepancy`, `rcm_liability`, `s73_vs_s74_intent`). Tags drive corpus retrieval.
2. **Retrieval:** per issue_tag + notice facts → Firestore vector search over corpus_chunks (top-k per issue, k=6) → assemble candidate authority set (parent corpus items, deduped).
3. **Drafter agent** (SMART; one call per section, not one giant call): sections = Facts; Point-wise reply per discrepancy; Legal grounds; Prayer. Hard prompt rules: cite only provided corpus items by `[[cite:ITEM_ID]]` markers; if no provided authority supports a point, write the argument factually and insert `[[gap:description]]`; formal representation register (English; Hindi UI labels fine, drafts English `[DECISION-4]`); never concede liability; never fabricate figures — pull only from extraction + QA answers.
4. **Citation verifier agent** (FAST, deterministic checks + model assist): every `[[cite:x]]` exists in corpus AND the drafted proposition is consistent with stored verbatim_text (model returns supported|unsupported|partial per citation). Unsupported → auto-replace with `[[gap]]` + log. **Zero unverified citations reach the editor.**
5. **Renderer:** `[[cite:x]]` → formatted citation string + expandable quote panel in UI; `[[gap:x]]` → highlighted `[CA to insert authority]`. Export to DOCX/PDF on letterhead (gaps rendered as visible placeholders so nothing unsupported ships silently).
6. Per-section regenerate; full edit history on drafts.

## §8. Legal corpus subsystem (moat; human + machine)

- **Scope for MVP (supports the 3 notice types):** CGST Act ss. 16, 17, 31, 35–39, 50, 61, 73, 74, 74A, 75, 107, 112, 122–126, 128A; CGST Rules 36, 37, 86A, 88C/88D, 142; ~25–40 key CBIC circulars/instructions (incl. 183/15/2022, 193/05/2023, 170/02/2022, 224/18/2024); ~60–120 curated case-law holdings for the MVP issue tags (public-domain judgment texts; store the holding para verbatim + neutral citation + source URL).
- **Pipeline:** `corpus_src/*.yaml` (id, type, citation_string, source_url, effective_dates, verbatim_text, summary, issue_tags) → `make corpus` validates schema, embeds, upserts. **Every item requires `reviewed_by` (Aman or CA advisor) before it becomes retrievable.**
- **Growth loop:** `kb_gaps` from drafting → weekly curation session → corpus grows where real cases demand. This compounding, human-reviewed corpus is the defensibility story vs prompt-wrapper competitors — say so in README.
- Statutory text/notifications: public domain. Keep source_url for every item; do not bulk-copy paid databases (Taxmann/SCC etc.).

## §9. AI-native operations layer (hackathon-critical, same pattern as AdmitAgent)

- **Reminder agent:** scheduler-driven; per deadline decides channel/copy/skip (e.g., skip T-3 if reply already filed) — decisions logged with reasoning.
- **Support agent:** on NoticeDesk's own WhatsApp + webapp bubble; RAG over `docs/help/*.md`; escalates billing/account changes to Aman.
- **Onboarding agent:** after signup, personalized sequence (email/WhatsApp) based on firm's first actions; nudges first notice upload.
- **Marketing agent:** weekly — drafts LinkedIn/Telegram posts + a "GST Notice Trends" snippet from anonymized aggregate metrics_daily (e.g., "41% of notices on NoticeDesk this week were 2A/3B mismatches") — never client-identifiable, never invented numbers; human approves before posting (`content_pieces` queue).
- **Digest agent:** Mon 09:00 IST partner digest (open cases, deadlines ≤7d, drafts awaiting review, usage).
- **Billing agent:** Razorpay webhook → payments upsert (related_party flag), credit ledger update, receipts; monthly P&L rollup.
- All runs → `agent_runs`; **Evidence page**: totals by agent, last-100 decision stream, autonomy metrics, latency, revenue with related-party split; `GET /api/evidence/export.csv` + `scripts/export_evidence.py`. `is_demo` data excluded from all evidence.

## §10. Pricing & monetization (`[DECISION-5]` — confirm numbers)

- **Free forever:** deadline board + summaries for up to N active cases (N=10) + WhatsApp reminders. (Acquisition hook; costs pennies.)
- **Per-draft entry:** ₹199/draft credit (market anchor) — impulse tier, Razorpay link.
- **Solo plan:** ₹1,499/mo — unlimited summaries, 15 drafts, 1 seat.
- **Firm plan:** ₹2,999/mo — unlimited summaries, 40 drafts, 5 seats, letterhead exports, priority support.
- Launch offer (July): 50% off first month for first 25 firms; disclosed as marketing spend if any referral fees paid.

## §11. Webapp

- **Auth:** Firebase Auth (Google sign-in + email link), firm allowlist; roles partner/staff; strict firm-scoped Firestore access via API layer (no client-side Firestore).
- **Board:** cases by status columns + deadline urgency badges (overdue/≤3d/≤7d); filters client/type/assignee.
- **Case detail:** summary card, documents, questionnaire, draft versions, timeline of agent + human actions.
- **Draft editor:** section-wise rich text, citation chips (click → quote + source link), gap highlights, regenerate-section, export.
- **Corpus admin (operator-only):** review queue, item editor, version history.
- **Evidence / Settings / Billing** pages per §9–10.
- Dense, fast, desktop-first (CA at a desk with documents); board usable on mobile.

## §12. API surface (summary)

`POST /api/cases` (upload) · `GET /api/cases?filters` · `GET /api/cases/{id}` · `POST /api/cases/{id}/questionnaire` · `POST /api/cases/{id}/qa` · `POST /api/cases/{id}/draft` · `POST /api/drafts/{id}/regenerate_section` · `POST /api/drafts/{id}/export` · `POST /api/cases/{id}/status` · `GET/POST /api/corpus` (operator) · `GET/POST /webhooks/whatsapp` · `POST /webhooks/razorpay` · `POST /tasks/{reminders,digest,weekly-marketing}` (OIDC) · `GET /api/evidence/*` · `GET /healthz`. All `/api/*` Firebase-auth'd + firm-scoped.

## §13. Security, privacy, compliance posture

- Secret Manager: GEMINI_API_KEY, WA_*, RAZORPAY_WEBHOOK_SECRET, FIREBASE_*. Least-privilege service account. OIDC on task endpoints. Rate-limit uploads/webhooks.
- Encryption in transit everywhere; Cloud Storage/Firestore encryption at rest (default) — state plainly, don't overclaim.
- Retention: originals + drafts kept while account active; deletion API on request; auto-purge free-tier inactive firms after 12 months (`[DECISION-6]`).
- Positioning language (marketing + app footer): "Drafting assistance for tax professionals. Every output is reviewed and signed by the practitioner. NoticeDesk is not a law firm and does not provide legal advice." Never market "no CA needed."
- ICAI ethics note: our referral/affiliate mechanics must not put CAs in violation of solicitation norms — pay referral fees to the firm as service discounts, not cash-for-clients (`[DECISION-7]` review with CA advisor).

## §14. Testing & evals (deploy gates)

- **Golden set:** ≥15 anonymized real notices (collect via CA network; strip identifiers) with expected extraction JSONs. Gate: ≥90% field accuracy on found fields; 100% on due_date-or-flag behavior.
- **Citation verifier tests:** invented-ID rejected; mismatched-proposition downgraded; gap rendering correct; zero unverified citations in export path.
- **Deadline math:** notice-type defaults, T-reminder scheduling, quiet hours, overdue transitions.
- Webhook signature tests (WhatsApp, Razorpay); firm-isolation access tests (user A cannot read firm B); OCR routing fallback; JSON-parse fallbacks (malformed model output → safe degrade + `status=fallback` run).
- `make eval` runs golden set + citation suite; CI blocks deploy on failure.

## §15. Phased build plan (dates assume start Jul 16; submit Aug 15)

**Phase 0 — Scaffold (Jul 16–17):** repo, CI, Cloud Run healthz, auth skeleton, Firestore wiring. *Accept:* deployed healthz; CI green.
**Phase 1 — Summary card + board (Jul 18–23):** intake (web), OCR routing, classifier+extractor, summary card, deadline board, WhatsApp reminders, corpus pipeline + first 40 corpus items (acts/rules/core circulars). *Accept:* 10 golden notices → correct cards ≤30s p50; deadlines on board; reminder fires on test case; eval gate live. **Launch free tier to CA groups end of Phase 1 — distribution starts before drafting exists.**
**Phase 2 — Drafting + payments (Jul 24–31):** questionnaire, drafter, citation verifier, editor, DOCX/PDF export, Razorpay credits/subscriptions. *Accept:* end-to-end paid draft on a real ASMT-10 and a real DRC-01 with zero unverified citations; a stranger can pay and export unassisted.
**Phase 3 — Ops layer + evidence (Aug 1–5):** support/onboarding/marketing/digest/billing agents, Evidence page + exports, help docs, WhatsApp intake channel. *Accept:* all agents visible with live counts; digest arrives Monday; payment appears in P&L with related-party flag.
**Phase 4 — Hardening + sell (Aug 5–12, interleaved with Aman selling daily):** onboarding polish, appeal-window tracking on adverse orders, bug triage, seed_demo for video, feature freeze Aug 12.
**Phase 5 — Submission (Aug 12–14):** README for judges, evidence bundle, 3-min video (real notice → card → draft → verify pane → board → evidence dashboard), 500–1000-word narrative. **Submit Aug 15.**

## §16. GTM (owner: Aman; product must support it)

Free deadline board is the hook: "Forward any GST notice to this WhatsApp number, get a summary + every deadline tracked, free." Channels: large CA/GST-practitioner Telegram & WhatsApp groups, LinkedIn DMs to practitioners posting about notices, CAclubindia/Taxguru comment presence, physical visits to Varanasi/Jaunpur firms, one webinar with a known CA if bookable. Conversion: free board → first paid draft (₹199) → plan. Targets: 100 free firms, 15–30 arms-length paying by Aug 14. Testimonials with explicit consent flag.

## §17. Non-goals (MVP — refuse scope creep)

GST portal login/scraping or auto-filing; income-tax notices (Phase-2 roadmap only); GSTAT appeal *drafting* (window July 31 too near; track appeal deadlines only — `[DECISION-3]`); books/reconciliation engine (accept CA's Excel as evidence, don't compute reconciliations yet); Tally/Zoho integrations; mobile apps; business-direct (non-CA) tier; multi-language drafts.

## §18. Risks & mitigations

- **Invented citations = product death** → citation-lock architecture + verifier + eval gate + visible gaps. This is the #1 engineering priority.
- **Crowded wedge (₹199 tools)** → never compete on draft price alone; lead with board/deadlines/verify-pack; README states differentiation explicitly for judges.
- **Notice format variance (scans, photos, regional formats)** → Document AI + confidence flags + human-confirm on low-confidence due dates; collect failures into golden set weekly.
- **CA trust/liability optics** → professional-in-the-loop language everywhere; verify pane front and center; advisor CA reviews corpus.
- **Corpus quality bottleneck** → start narrow (3 notice types, ~12 issue tags done well) rather than broad and shallow.
- **Ex-parte stakes on our reminders** → reminders are assistive; UI disclaimer that statutory deadlines are the CA's responsibility; never suppress a reminder without logged reason.

## §19. Post-hackathon growth path (README "future scope")

Income-tax notices (143(1)/148/154/CP-equivalents) on the same engine → appeal drafting + GSTAT hearing-prep packs (case-law compilations, grounds, chronology builders) riding the 4.8-lakh-case tribunal decade → GSP-partnership auto-fetch of notices from GSTN → Tally/Zoho evidence pulls → firm analytics ("your exposure by issue type") → the litigation OS for India's 1 lakh small tax practices. TAM sanity: 5,000 firms × ₹2.4k/mo ≈ ₹14.4 Cr ARR before income-tax expansion.

## §20. Open decisions for Aman (`[DECISION-n]` — confirm before Phase 2)

1. Hackathon category: Professional Services vs Small Business Services.
2. Business-direct tier (SMEs without a CA): out for MVP — confirm.
3. Appeal drafting: track-only for MVP — confirm.
4. Draft language: English-only drafts (UI bilingual) — confirm.
5. Pricing table §10 — confirm numbers.
6. Data retention policy — confirm.
7. Referral mechanics vs ICAI solicitation norms — review with CA advisor.
8. Product name: "NoticeDesk" is a working name — confirm or rename before domain/branding.
9. **Track decision: does NoticeDesk replace AdmitAgent for the hackathon, run parallel (rules allow multiple substantially-different submissions), or wait post-hackathon?** — this gates everything above.
