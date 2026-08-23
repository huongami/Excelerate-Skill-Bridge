# Skill Bridge

Skill Bridge makes international and cross-industry experience visible to Australian employers. It translates a candidate's existing experience into recognisable skills, explains every mapping, highlights honest gaps, and keeps every hiring decision with a human recruiter.

## Hackathon deliverable

The repository now provides two presentation paths:

- [Static three-screen demo](app/demo.html) - one self-contained HTML file with hardcoded illustrative personas, no server, build step, network dependency, database, or live AI call.
- [Workflow diagram](pitch/diagrams/workflow.png) and [data-model diagram](pitch/diagrams/data-model.png) - pitch-ready PNGs generated reproducibly by [generate.py](pitch/diagrams/generate.py).
- [Coded Next.js app](app/page.tsx) - the same flow through thin API routes, domain functions, Zod contracts, append-only decisions, and a guarded AI gateway. It defaults to deterministic demo mode.
- [Architecture specification](Docs/ARCHITECTURE.md) - the implemented structure plus the full Raw -> Reference -> Silver -> Gold production path.

Open [app/demo.html](app/demo.html) directly in a browser and use **Next** or the top navigation to move through:

1. Candidate CV and profile review
2. Translated skills and honest gaps
3. Recruiter job match and human decision log

To run the coded app:

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

Open `http://localhost:3000`. Keep `SKILL_BRIDGE_DEMO_MODE=true` for a deterministic, API-key-free demo. Run `pnpm test`, `pnpm lint`, and `pnpm build` before presenting.

## Why this problem matters

Australia hosts 680,582 international students, while 69% of employers report difficulty finding skilled talent. The problem is not simply talent scarcity: overseas job titles, cross-industry experience, and non-standard CV formats make genuine capability difficult for local recruiters and applicant-tracking systems to recognise. Skill Bridge addresses that translation gap without reducing a person to an opaque score. See [PRD §1-3](Docs/Skill_Bridge_PRD.md) and [challenge brief: The Problem](Docs/Topic_challenge.md#the-problem).

## Solution direction

The candidate reviews a structured profile, sees their experience translated into Australian-market skill language with evidence, and receives neutral gap guidance. A recruiter then compares those already-translated skills with a specific job description using per-skill match levels and explanations. The recruiter alone chooses **Shortlist**, **Needs more info**, or **Not a fit**; the product never auto-accepts or auto-rejects.

## Judging-criteria alignment

Attendance is handled by the team and is not claimed by the repository.

| Criterion | Weight | Evidence in this repository |
| --- | ---: | --- |
| Problem and User Understanding | 12% | The problem, root cause, target users, and evidence are defined in [PRD §1-4](Docs/Skill_Bridge_PRD.md) and reflected in the two-sided demo personas. |
| Solution Quality and Innovation | 12% | Cross-border and cross-industry translation, explainable skill evidence, honest gaps, and skill-level matching implement [US-2, US-3, US-5, and US-6](Docs/Skill-Bridge-User-Stories.md). |
| Prototype and Technical Execution | 28% | The [static demo](app/demo.html) covers all three screens without stage-risk dependencies, while the coded app implements the screen/API/domain boundaries. [ARCHITECTURE §0-3](Docs/ARCHITECTURE.md) maps every function, contract, artifact, schema, and pipeline layer. |
| Evaluation, Limitations and Future Development | 16% | [ARCHITECTURE §4](Docs/ARCHITECTURE.md) defines Zero-AI-Trust verification, golden-set/adversarial/e2e tests, and retest triggers; [§5](Docs/ARCHITECTURE.md#5-limitations-roadmap-and-open-items) records limitations, database triggers, and open decisions. |
| Pitch and Live Demonstration | 8% | [Demo instructions](app/README.md), deterministic personas, and a three-step narrative support a smooth live walkthrough grounded in [PRD §2.3](Docs/Skill_Bridge_PRD.md). |
| Creativity (Video/Pitch Presentation) | 4% | Reproducible [workflow and data-model visuals](pitch/diagrams/README.md), consistent Skill Bridge styling, explainability copy, and the two-sided story provide pitch-ready visual anchors. |

## Deliberate scope decisions

- No database, authentication, or production personal data. Live LLM mode is optional and must not be used for the stage-safe path.
- No overall candidate score and no automated hiring decision.
- Static demo data is synthetic and baked into `app/demo.html`.
- The coded app remains one process/deploy with `frontend/`, `backend/`, and `infra/` concern boundaries. Framework routes are thin wrappers; frontend code calls backend logic only through HTTP API contracts.
- Default presentation mode is local from the presenter's machine. A public deployment must not combine serverless functions with in-memory session state.

## Repository map

See [Docs/REPO_GUIDE.md](Docs/REPO_GUIDE.md) for the full tree, ownership, build order, and unresolved questions. [Docs/PROMPTS.md](Docs/PROMPTS.md) is the current repo-generation and runtime prompt source of truth.
