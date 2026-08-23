# Repo-Generation Prompt

Last updated: 2026-08-23.

This is one current prompt, not a request log. Given `Topic_challenge.md`, `Skill_Bridge_PRD.md`, and `Skill-Bridge-User-Stories.md`, it reproduces the repository's current intended state. Treat the brief as the constraint and the two team documents as fixed source specifications; build on them without rewriting them.

**Standing rule:** whenever a new instruction changes what the repository should contain, merge it into this prompt and update every affected scaffold document in the same pass. Do not append dated history. A document that is correct alone but inconsistent with README, REPO_GUIDE, or ARCHITECTURE is a repository bug.

## Current generation specification

### 1. Direction and rubric

Map the solution explicitly to every judging criterion except attendance and cite PRD/user-story sections. Weight documentation effort proportionally: 12% problem understanding, 12% solution quality, 28% prototype/technical execution, 16% evaluation/limitations, 8% pitch, and 4% creativity. Technical execution and evaluation must be the deepest sections.

### 2. Build order

Build idea and demo reliability before engineering depth:

1. Create `app/demo.html`, a self-contained static three-screen demo using hardcoded synthetic personas. It must need no server, build step, database, venue network, or live LLM call.
2. Create pitch-ready `pitch/diagrams/workflow.png` and `data-model.png` from the team-approved originals retained under `pitch/diagrams/assets/`. Preserve the Workflow pixels. Because the approved Data Model JPG is only 600×386 and unreadably soft in a deck, retain it as the visual reference but redraw its exact information structure deterministically with Pillow at 1700×980. Do not use generative image upscaling for text-heavy diagrams, because labels must remain exact.
3. Implement the single-process Next.js scaffold after the static assets, using the static persona, Product Manager role, provisional synthetic mappings, and per-skill card UI as explicit defaults. The homepage selects among Candidate, HR, and Admin demo portals: Candidate owns profile/skills, HR owns JD matching and human decisions, and Admin shows read-only trust/readiness status. These routes are presentation roles, not access control; do not add auth or a database. Keep `SKILL_BRIDGE_DEMO_MODE=true` deterministic and key-free. Real model calls and evaluation claims remain gated on reviewed seed mappings, a dated public JD set, and golden/adversarial validation.

### 3. Application architecture

Specify a single-process, single-deploy application using folder-level `frontend/`, `backend/`, and `infra/` separation. Do not split services, add a second server, or create CORS overhead. Framework-required `app/` screens and route handlers are thin wrappers that import real UI/backend logic.

Enforce: `frontend/` never imports `backend/`; it calls same-origin API routes through `fetch`. Only one backend LLM gateway may import the AI SDK, and every route must pass through it for structured output, validation, bounded retry, and explicit failure.

Name concrete packages and locations: Next.js 15/React 19/TypeScript, Tailwind CSS 4, Zod 4, official `openai` SDK, `mammoth`, `pdf-parse`, Zustand, `jose`, pnpm, Vitest/MSW, and Playwright. Document exact screen/route/function mappings and request/response/error contracts.

State physical storage: static persona data in the HTML; reviewed Reference JSON imported as modules and baked into the production build (seed changes require rebuild/redeploy); non-persisted browser state in Zustand so stale browser IDs cannot outlive process-memory backend records; local-only live-app session state in one process; a signed size-bounded cookie if a public single-session demo is necessary; no database. Default to local presentation. Never deploy process-memory state to stateless serverless functions such as Vercel and assume it will persist. For a public URL, use client-side/signed session state or a single persistent-process host.

No database is intentional for the hackathon. The roadmap trigger is multi-user concurrency, persistence across visits/devices, authenticated recruiter identity on append-only decisions, audit retention, or product learning over many users. At that point use PostgreSQL plus Drizzle ORM, authentication, tenancy, encryption/retention policy, and relational revisions/evidence/events; do not add them now.

### 4. Repository scaffold

Maintain:

- `README.md`: problem, solution, rubric table with source citations, demo entry point, and links.
- `Docs/REPO_GUIDE.md`: full tree, purpose/owner, status, and open questions.
- `Docs/ARCHITECTURE.md`: full functional inventory, code architecture, Raw/Reference/Silver/Gold data design, API contracts/schemas, prompt map, tests, limitations, roadmap, and open items.
- `Docs/PROMPTS.md`: this current generation spec and supporting prompt library.
- `app/demo.html`, the three Next.js screens, thin API route wrappers, and `app/README.md`.
- `pitch/diagrams/` with one-line README, team-approved source assets, normalization generator, and both generated PNGs.
- `frontend/`, `backend/`, `infra/`, and `shared/`: UI, domain/controller, adapter, and dependency-neutral contract code.
- `tests/`: unit/integration tests plus golden-set, adversarial, and e2e homes.
- `data/`: labelled synthetic demo fixtures and provisional Reference JSON, with review gates documented in its README.

### 5. Functional inventory and data model

Audit every acceptance-criteria bullet and maintain a fine-grained coverage index before the full specifications. Specify a backing function and artifact in full: trigger, ordered processing, exact output, and edge cases. Multiple checklist rows may share an orchestration function only when each row's independent trigger/data effect remains explicit and testable. In particular:

- Candidate confirmation/editing changes data and appends provenance; it is not merely a UI action.
- Many-JD frequency aggregation and one-JD candidate semantic matching are distinct functions/prompts.
- Raw reference source text has an explicit extraction/normalization stage before consumption.
- No overall candidate score exists, including hidden aggregate fields.
- Recruiter actions are append-only events and never overwrite earlier actions.
- Image-only/scanned PDFs without extractable text fail explicitly with `OCR_NOT_SUPPORTED`; OCR is an accepted hackathon limitation, never a silent or improvised fallback.

Use Raw (unstructured input) -> Reference (reviewed static seeds) -> Silver (strict structured artifacts; one extraction call per document) -> Gold (UI-ready deterministic joins). After Silver, no LLM reinterprets Raw text. Include a Mermaid transform diagram and JSON Schema for each core Silver/Gold artifact.

Every Raw/Reference item must name who produced it and where it literally came from: team-authored synthetic CV, explicitly consented candidate CV, recruiter-owned JD, dated public postings captured from SEEK/LinkedIn/Indeed/Jora, ANZSCO from the Australian Bureau of Statistics/Jobs and Skills Australia, ESCO from the European Commission, O*NET from the US Department of Labor, or an explicit team decision.

Reference build process: choose roles; retain dataset versions, URLs, licenses, publishers, locations, and capture dates; normalize stable IDs deterministically; use an LLM only to extract structured skills from retained text, compare already-sourced rows, propose mappings, or draft rationales; never trust it to invent a taxonomy row, job posting, requirement, or statistic; require human review/sign-off before any row is committed; compute JD frequencies deterministically.

### 6. Invariants

Check every function, schema, route, UI control, and test against these constraints:

- Rank skills, not people; no single opaque or aggregate candidate score.
- No auto-accept/auto-reject; only recruiter-initiated actions.
- Every AI result provides source -> mapped result -> plain-language reason.
- Only synthetic or explicitly consented personal data.
- Keep the hackathon solution adoptable by an Australian SME: no separate service, database, auth, or infrastructure migration.

### 7. Zero-AI-Trust tests and retesting

Every LLM output is untrusted. Per call, use strict schema validation, resolvable evidence IDs, one bounded repair retry, then an explicit typed failure. Silver schemas structurally forbid aggregate fields and retain edit provenance. Reference rows require source metadata and human signature. Gold uses deterministic joins and append-only events. A human reviews every result before a hiring action.

Use standard test homes:

- `tests/unit/`: Vitest pure functions/schemas, mocked LLM.
- `tests/integration/`: route/session flow, mock only the LLM network boundary.
- `tests/golden-set/`: hand-labelled fixtures and the US-1 80% accuracy bar; real calls, on demand.
- `tests/adversarial/`: inflated claims, unsupported JD requirements, prompt injection, garbled inputs, forced medium matches, invented sources, and auto-reject wording; real calls, on demand.
- `tests/e2e/`: Playwright full US-1-US-7 flow against a running app.

Unit and integration run on every commit. Golden-set, adversarial, and e2e run on demand per the retest matrix. The exact static personas receive a human pre-pitch spot-check and have no test folder. Prompt changes, schema changes, seed changes, and model/version upgrades require the corresponding unit/integration/e2e checks; prompts and model upgrades always rerun golden-set and adversarial suites. Never assume unchanged prompt text behaves the same after a model upgrade.

### 8. Synchronization

After every scope change, merge it into sections 1-7 and update README, REPO_GUIDE, ARCHITECTURE, demo/data, and test descriptions wherever affected. Check links and section citations immediately, especially when ARCHITECTURE headings shift.

## Runtime prompt library

These prompts belong to the implemented live-app boundary, not the static demo. Demo mode uses deterministic fixtures; any enabled model output must use strict schemas through the guarded gateway.

### CV_EXTRACT_V1 — US-1 CV/experience parser

```text
Extract structured career data from a candidate CV or work history. The layout may be non-Western, section order may differ, headings may be non-English, and dates may use non-US formats.

For each role extract title exactly as written, employer, country, start/end date, and responsibility/achievement statements. If a field is missing or ambiguous, output null plus a one-line reason; never guess silently. Do not infer skills. Return only JSON matching the supplied schema, with source excerpts for every extracted value.
```

### JD_EXTRACT_V1 — JD skill extraction

```text
Extract required and strongly preferred skills from one job description. Ignore company, benefits, EEO, and other boilerplate. Normalize casing and wording, but do not infer a skill that is not stated or clearly implied by a listed responsibility. Every skill must include an exact evidence span from the input. Return strict schema-conformant JSON.
```

### SKILL_TRANSLATE_V1 — US-2 translator

```text
Map one already-parsed role (title, country, responsibilities) to Australian-market skill terms using only the supplied reviewed Reference records. For an overseas role, name an explicit AU-equivalent title/function. For a cross-industry move, surface a mapping only when a genuine underlying competency exists and name it. Omit unsupported fragments with a reason. Return source evidence IDs for every mapping. Translate skills; never score the person and never output an aggregate score.
```

### SKILL_EXPLAIN_V1 — US-3 highlighter

```text
Given one translated skill and the original evidence it came from, write one plain-language sentence explaining why it transfers. Name the specific past experience and return its source evidence ID. Do not add experience or capability not present in the supplied evidence.
```

### US-4 frequency aggregation — deterministic, not an LLM prompt

```text
Across a reviewed role's pre-extracted JD Silver records, count document occurrence for each normalized skill, sort descending, and retain source JD IDs. If fewer than five JDs exist, set robustness to "indicative" in the artifact itself. Do not confuse this with matching one candidate to one JD.
```

### US-5 honest gaps — deterministic Gold join

```text
Left-join reviewed expected skills for the target role against the candidate's validated skill profile. List missing skills separately in neutral language. If none remain, output exactly "No major gaps identified". Never present a gap as a penalty or rejection.
```

### SKILL_MATCH_V1 — US-6 one-JD semantic match

```text
Given the candidate's translated skills and justifications plus one JD's extracted requirements, assess each JD skill separately as high, medium, or low. Reuse existing candidate justification and evidence IDs. If there is no matching or related evidence, output low plainly. Return no aggregate field or overall score.
```

### US-6/US-7 match display and human review

```text
Present only per-skill match levels linked to evidence. Never output or imply a total candidate score. Available actions are recruiter initiated: Shortlist, Needs more info, or Not a fit. Never generate auto-approve or auto-reject controls/copy. Append every confirmed action as a new event.
```

## Future vibe-coding stages

### Stage 1 — implemented scaffold

```text
Maintain the implemented single-process Next.js/TypeScript layout in ARCHITECTURE with profile review, translated skills/gaps, and recruiter match/human review. Keep framework routes thin, enforce frontend/backend import boundaries, and use clearly labelled synthetic/provisional data in demo mode. No auth or database.
```

### Stage 2 — runtime wiring

```text
Replace one placeholder function at a time with its named versioned prompt through guardedGenerate(). Validate strict structured output, retry schema repair once, then show explicit failure. Never fabricate fallback values. Add/update unit, integration, golden-set, adversarial, and e2e coverage per the retest table.
```

### Stage 3 — reviewed seed data

```text
Build three synthetic candidate fixtures (cross-border, cross-industry, both), the team-approved target roles, 20-30 reviewed skill mappings per selected scope, and a dated public JD set. Run JD extraction once per document, retain source spans/URLs, require human sign-off, compute frequency deterministically, and commit versioned JSON plus provenance manifests under data/reference/.
```
