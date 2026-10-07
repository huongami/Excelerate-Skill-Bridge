# Skill Bridge 2.0 — Product Rebuild Specification Pack

Source of truth for the full rebuild requested in [`app/prompt/prompt.md`](../prompt/prompt.md).
Visual source of truth: [`app/skills/desgin/design.md`](../skills/desgin/design.md).

> Every agent MUST read this file first, then the files listed for its role in `07_TASK_BREAKDOWN.md`.

## 1. Files in this pack

| File | Purpose | Primary readers |
| :--- | :--- | :--- |
| `00_README.md` | Index, rules of engagement, glossary | All agents |
| `01_REQUIREMENTS_TRACEABILITY.md` | Every sentence of the prompt → requirement ID → spec section → task → test | Lead, QA |
| `02_PRODUCT_SPEC.md` | Roles, flows, screens, functional behaviour (seeker + HR) | Frontend, Backend, QA |
| `03_DESIGN_SYSTEM_SPEC.md` | Design tokens, components, motion, a11y, UI/UX Pro Max skill usage | Design-system, Frontend |
| `04_DATA_AND_SCORING_SPEC.md` | Database schema, seeding from `data/`, formula wiring, behavioural ranking, chart maths | Data, Backend |
| `05_API_SPEC.md` | REST contract between Next.js UI and Python product API | Backend, Frontend |
| `06_CONTENT_SPEC.md` | Full Terms & Conditions text, Privacy notice, microcopy, empty/error states | Frontend, Content |
| `07_TASK_BREAKDOWN.md` | Agents, tasks, dependencies, Definition of Done | All agents |
| `08_QA_ACCEPTANCE.md` | End-to-end scenarios and acceptance checklists | QA, Lead |
| `09_DECISIONS_AND_OPEN_QUESTIONS.md` | Gap-filling decisions taken where the prompt is silent; open questions | Lead, user |

## 2. Rules of engagement (mandatory for every agent)

1. **No invention.** Build only what is in this pack. If something is not specified, stop and raise it to the Lead (record it in `09_DECISIONS_AND_OPEN_QUESTIONS.md` § Open Questions). Do not guess.
2. **No omission.** Every requirement ID (`REQ-*`) in `01_REQUIREMENTS_TRACEABILITY.md` must be implemented and tested. A task is not done if any linked `REQ-*` fails its acceptance test.
3. **Formulas are fixed.** Scores come only from the six formulas in `intelligence_engine/` (Formula 1–6). Do not re-implement, re-weight, or approximate them in the UI. The only permitted engine changes are listed in `04_DATA_AND_SCORING_SPEC.md` § 5.3 (parameterisation, no weight changes).
4. **Data is real.** All jobs, employers, and candidates come from `data/`. No lorem ipsum, no placeholder people, no fake companies. Missing values are handled by the rules in `04_DATA_AND_SCORING_SPEC.md` § 4, and the UI must label derived values.
5. **Language.** All UI copy, code identifiers, comments, and documentation are in **English** (Australian spelling: "organisation", "licence" (noun), "optimise").
6. **Design.** All UI follows `03_DESIGN_SYSTEM_SPEC.md`. No ad-hoc colours, fonts, radii, or shadows. No emoji used as icons (use Lucide).
7. **Behaviour, not decoration.** Every button listed in the spec has a persisted server-side effect and a visible UI result. A button that only shows a toast is a defect.
8. **Traceability in commits/PRs.** Each change references its task ID (`T-xx`) and requirement IDs (`REQ-*`).

## 3. Target architecture (summary)

```
┌──────────────────────────────┐        HTTP/JSON        ┌───────────────────────────────────┐
│  Next.js 15 (App Router)     │  ───────────────────▶   │  Product API (Python 3, stdlib +   │
│  React 19 + Tailwind CSS v4  │   /api/* rewrite        │  sqlite3)  port 8095               │
│  Lucide React, Recharts      │  ◀───────────────────   │  imports intelligence_engine/*.py  │
│  port 3000                   │                          │  SQLite: product_api/var/app.db    │
└──────────────────────────────┘                          └───────────────────────────────────┘
                                                                     ▲
                                                                     │ seed (one-off, idempotent)
                                                          data/australian_jobs.json (461 jobs)
                                                          data/australian_jobs_dataset.csv (dates)
                                                          data/australian_candidates.json (320 CVs)
```

- New frontend code lives in `app/` (routes) and `frontend/` (components, state, API client). Old screens are replaced, not patched.
- New backend lives in `product_api/` (new folder). The existing `enterprise_pipeline/` and `intelligence_engine/` are reused, not modified except as allowed in `04` § 5.3.

## 4. Glossary

| Term | Meaning |
| :--- | :--- |
| Seeker | Job seeker account (role `seeker`). |
| HR | Employer / recruiter account (role `hr`). |
| Alias | Public display name chosen by the seeker. HR sees only the alias, never the legal name. |
| SMF | Formula 1 — Skill Match vs ANZSCO, 0–100. Displayed as "ANZSCO match %". |
| GSI / JRS | Formula 2 — Gap Severity Index (0–100, higher = bigger gap) / Job Readiness Score = 100 − GSI. |
| JPI | Formula 3 — Job Proximity Index between two jobs, 0–100. |
| RMS / Δ | Formula 4 — Relative Merit Score of a candidate / head-to-head delta. |
| FRS | Formula 5 — Feed Ranking Score of a job for a seeker. Displayed as the job "Overall score". |
| FRS★ | FRS after the behavioural adjustment in `04` § 6 (saves, applies, ignores). Feed order uses FRS★. |
| TSS | Formula 6 — Talent Search Score of a candidate for a job. Displayed as the candidate "Overall score". |
| AI field | Any value produced by CV/JD extraction. Shown with an "AI" badge until the user confirms or edits it. |
