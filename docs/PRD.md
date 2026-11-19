# CareTrace — Healthcare Compliance & Inspection Readiness Copilot

**Product Requirements Document (PRD) — v0.1 | Discovery draft | November 19, 2026**  
**Working name:** CareTrace (unverified; not a trademark clearance)  
**Status:** Concept hypothesis, not a validated business or selected final product.

## 1. Executive summary
CareTrace is a proposed AI-assisted workspace for Ontario long-term-care (LTC) teams preparing for inspections. It turns authoritative regulations, public inspection findings, and an organization's approved policies into traceable obligation maps, policy-coverage reviews, and evidence checklists. Unlike a generic PDF chatbot, it helps teams move from **"What does the rule say?"** to **"What should we review, who should check it, and which source supports that request?"**

**Initial wedge:** inspection-readiness analysis for infection prevention and control (IPAC) policies and supporting documentation. Broader cross-Act analysis is a subsequent hypothesis, not an MVP promise.

**Product principle:** the software suggests, links, compares, and documents. A qualified person makes compliance determinations.

## 2. Problem and opportunity
- Relevant rules and inspection findings are spread across legislation, regulations, public reports, and internal policy documents.
- A team can find a regulatory clause yet still struggle to connect it to a particular policy and the evidence an inspector may request.
- Generic LLM answers may cite irrelevant passages, omit obligations, or use outdated text.
- Existing vendors already offer broad healthcare compliance workflows. The hypothesis to test is whether a **narrow, source-verifiable inspection-readiness workflow** produces value that users cannot get easily from general-purpose search or existing tools.

These are **hypotheses requiring interviews**, not claims of measured customer pain or willingness to pay.

## 3. Target customer and users
**Initial buyer hypothesis:** a small or mid-sized Ontario LTC operator or the administrator of a single home.

**Primary user:** Director of Care, quality/compliance lead, or designated policy owner.

**Secondary users:** clinical educator, IPAC lead, administrator, and internal auditor.

**Job to be done:** "Before an inspection, help me verify which documented requirements apply to our IPAC program, where our policies address them, where evidence is missing, and what needs human review."

## 4. Proposed value proposition
**For Ontario LTC compliance teams, CareTrace creates an inspection preparation workspace grounded in versioned, direct-source evidence instead of presenting an unverified answer from uploaded PDFs.**

Potential differentiated value to validate:
1. Regulation-to-policy-to-evidence traceability.
2. Explanations linked to exact sections and document versions.
3. Public inspection findings used as examples of historically cited issues—not as proof that another facility has the same problem.
4. Explicit review states, uncertainty, and a human-approved export.

## 5. Core workflow
1. User selects an IPAC topic and a review date.
2. System retrieves in-scope requirements from a curated, versioned regulatory library.
3. User uploads an approved *de-identified* policy or uses a synthetic example.
4. System links each requirement to potentially matching policy passages and relevant public inspection examples.
5. System assigns a provisional **coverage status**: `addressed in document`, `partially addressed`, `no supporting passage found`, or `needs review`. These are *document coverage labels*, not legal compliance judgments.
6. Reviewer checks citations, corrects mappings, records evidence needed, and assigns follow-up work.
7. System generates a versioned, reviewer-approved inspection-readiness packet with source references and an audit trail.

## 6. MVP scope and acceptance criteria

### P0 — Required for initial demo
**F1. Authoritative source library**
- Ingest the *Fixing Long-Term Care Act, 2021*, Ontario Regulation 246/22, and a curated set of publicly available inspection reports relevant to the selected IPAC workflow.
- Preserve source URL, title, section/paragraph, as-of date, version, ingestion timestamp, and content checksum.
- **Accept:** reviewer can open every source directly and identify the text/version used.

**F2. Cited, topic-bounded search**
- Search using a mixture of keyword and embedding retrieval with reranking.
- Return answers with exact source passages, jurisdiction, and date; abstain when the evidence is insufficient.
- **Accept:** test questions show direct supporting passages; no unsupported universal claim of completeness or compliance.

**F3. Requirement-to-policy comparison**
- Extract candidate obligations into structured fields: `obligation_id`, `source`, `actor`, `action`, `condition`, `frequency`, `effective_date`, and `review_status`.
- Link obligations to uploaded policy excerpts and mark ambiguous or absent matches for human review.
- **Accept:** every flagged gap shows which obligation was checked and what text was searched; reviewer can override the status with a reason.

**F4. Inspection evidence checklist and export**
- Draft a checklist of documentation to gather, with source-backed rationale and editable owner/status fields.
- Export Markdown or PDF only after human approval; capture approver, time, and source versions.
- **Accept:** downloaded result distinguishes verified sources, AI suggestions, reviewer decisions, and unresolved items.

### P1 — After validation
- Monitor changes to in-scope legislation and show section-level differences and impacted policies.
- Cross-reference selected obligations against the Occupational Health and Safety Act and Employment Standards Act where legal specialists confirm applicability.
- Team assignments, notifications, approvals, and integrations with document storage.
- Multi-home benchmarking based on carefully contextualized public data.

### Out of scope
- Autonomous legal advice or definitive compliance certification.
- Assessing individual residents, clinical decision-making, or admission decisions.
- Ingesting identifiable patient/resident health records during MVP.
- Automatic regulatory filings, policy changes, or actions without approval.
- Supporting all Canadian jurisdictions or expanding to banking/insurance in v0.1.

## 7. Functional and safety requirements
- **Provenance:** clickable citations to sections, not just PDF filenames.
- **Temporal accuracy:** answer using the regulatory version applicable to the selected date; flag uncertain effective dates.
- **Grounding:** if retrieved evidence does not support a claim, show "insufficient evidence" rather than infer.
- **Privacy:** public and synthetic/de-identified data only for demo. Real client policies require authorization, access controls, retention rules, and security review. An operational deployment involving personal health information requires a separate PHIPA-informed privacy/security assessment.
- **Security:** authenticated access, tenant separation for production, encrypted storage/transport, least privilege, logs, and deletion controls.
- **Human oversight:** no automated compliance conclusion or external submission.
- **Auditability:** versioned source corpus, model/prompt version, retrieved passages, outputs, and reviewer changes.

## 8. Technical architecture (informed by supplied RAG diagram)
**Ingestion:** official statutes/regulations + public inspection reports + authorized policies → parsing/OCR only if necessary → layout-aware chunks → metadata/version tagging → obligation extraction → indexing.

**Retrieval:** question or policy clause → query interpretation → hybrid lexical + semantic retrieval → reranking → source/date/jurisdiction checks → citation-qualified context.

**Output:** LLM drafts obligation map, comparison, and checklist → deterministic validation of source IDs and quote spans → human reviewer → auditable export.

**Possible stack (proposed, not mandatory):**
- Frontend: Next.js + TypeScript.
- API and ingestion: Python + FastAPI; background jobs.
- Storage: PostgreSQL for structured obligations and approvals, object storage for originals.
- Retrieval: pgvector for semantic search plus OpenSearch for BM25; simpler PostgreSQL full-text can substitute during a small prototype.
- AI: embedding model, optional reranker, LLM with schema-constrained responses.
- Deployment: containerized application with secrets management, monitoring, and explicit data policies.

**Why not only vector RAG?** Exact statute numbers, dates, negations, exceptions, and thresholds can be missed by similarity search. Structured obligation extraction and keyword/metadata filters are first-class parts of the design.

## 9. Example user stories
- **As a quality lead,** I want to ask which IPAC obligations relate to a particular policy and see exact current citations, so I can review them confidently.
- **As a Director of Care,** I want a list of policy clauses with missing or ambiguous support, so I can request clarification from the right person.
- **As an internal reviewer,** I want examples from published inspection findings with direct links, so I can understand what inspectors have previously documented without assuming those findings predict my home's risk.
- **As an administrator,** I want an approved, time-stamped evidence checklist, so I can keep an inspection preparation record.

## 10. Success metrics and evaluation plan
**Prototype test corpus:** 30–50 curated legal/regulatory excerpts, 20–40 public inspection findings, and 3–5 synthetic or explicitly permitted de-identified policies. These are planning targets, not data already acquired.

**Evaluation set:** at least 50 expert-checked questions, including ambiguous, outdated, cross-reference, and unanswerable cases.

**Proposed quality gates (to refine with domain reviewers):**
- ≥95% of factual citations open to the correct supporting passage and version.
- ≥90% recall of in-scope obligations on a bounded, expert-annotated test set.
- Zero unqualified statements that the facility is "fully compliant" or that all obligations were found.
- 100% of final gap exports require recorded human approval.

**User value validation:** interview 8–12 people in LTC quality/compliance roles; observe at least 3 current inspection-preparation workflows; test a prototype with at least 3 reviewers. Measure time to prepare a narrowly defined checklist versus the user's existing process, correction rate, trust, and whether someone would adopt or pay for it. Do not assume time savings before testing.

## 11. Delivery plan (illustrative, not a commitment)
- **Stage 1 — Discovery:** interviews, workflow map, source/legal scoping, competitor teardown.
- **Stage 2 — Corpus and evaluation:** authoritative ingestion, section-level versioning, annotated questions.
- **Stage 3 — Retrieval prototype:** hybrid search, citation viewer, abstention behavior.
- **Stage 4 — Workflow prototype:** policy comparison, review labels, editable evidence checklist.
- **Stage 5 — Validation:** measure precision/recall and workflow value; determine whether to build further, pivot, or stop.

## 12. Primary risks and mitigations
- **Crowded market:** narrow the wedge; validate what current tools fail to do.
- **Incorrect legal interpretation:** requirement extraction is provisional; expert review and direct citations mandatory.
- **Outdated rules:** version registry and as-of dates; flag stale source checks.
- **PDF parsing errors:** retain originals and manually validate sampled extracts.
- **No access to real workflows:** start with public sources and synthetic policies; customer discovery is a gate before commercialization.
- **False sense of inspection readiness:** use coverage/evidence terminology, never certification or risk guarantees.

## 13. Open decisions
1. **Sector:** Ontario long-term care (current hypothesis) or another healthcare segment?
2. **Pain point:** policy comparison, regulatory change impact, or inspection-evidence preparation?
3. **First topic:** IPAC (current hypothesis), staff onboarding/training, or another narrow regulation cluster?
4. **Product objective:** portfolio-quality engineering demonstration, research project, or startup validated for customers?
5. **Data access:** public-only demo, approved organizational policies, or partner pilot?
6. **Business model:** unknown; evaluate paid pilot/subscription only after confirming demand.

## 14. Go / no-go decision
**Proceed** if interviews identify one repeated, costly workflow; reviewers judge source traceability materially useful; a bounded evaluation reaches acceptable quality; and at least one potential user agrees to pilot. **Pivot** if the pain is real but another workflow has stronger urgency or better access to data. **Stop** if existing solutions adequately solve it, users will not share even non-sensitive documents, or safe accuracy cannot be demonstrated.

## 15. Source starting points
- [Fixing Long-Term Care Act, 2021](https://www.ontario.ca/laws/statute/21f39)
- [O. Reg. 246/22](https://www.ontario.ca/laws/regulation/220246)
- [Ontario LTC inspection reports](https://publicreports.mltc.gov.on.ca/)
- [Ontario Information and Privacy Commissioner: Health privacy guidance](https://www.ipc.on.ca/en/health-privacy-ontario/general-resources-for-health-information-custodians)
- [exacare ai — Admissions](https://www.exacare.com/admissions)
- [CHeCS](https://checs.ca/)
- [Riskophia](https://www.riskophia.ca/)

**Important:** This draft is product planning, not legal advice. Regulatory and competitive facts should be re-verified at implementation time; real-world scope and market demand remain unvalidated.
