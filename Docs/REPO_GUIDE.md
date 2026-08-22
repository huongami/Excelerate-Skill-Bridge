# Repository Guide

## Build status

The static hackathon demo and reproducible pitch diagrams are built. The live Next.js/LLM pipeline is deliberately specified but not implemented until the four product-data questions below are resolved.

## Folder tree and ownership

```text
.
├── README.md                         # Product direction, demo entry point, rubric map (Product/PO)
├── Docs/
│   ├── Topic_challenge.md            # Official brief and judging rubric; source, do not rewrite (Hackathon organiser)
│   ├── Skill_Bridge_PRD.md           # Team product vision and requirements; source spec (Product/PO)
│   ├── Skill-Bridge-User-Stories.md  # MVP stories and acceptance criteria; source spec (Product/PO)
│   ├── ARCHITECTURE.md               # Acceptance-criteria index; full function, app/API/data, trust-test and roadmap spec (Technical)
│   ├── REPO_GUIDE.md                 # Repo map, ownership, status, open questions (Product + Technical)
│   └── PROMPTS.md                    # Current repo-generation prompt and supporting prompt library (Product + Technical)
├── app/
│   ├── README.md                     # One-line demo instructions (Technical)
│   └── demo.html                     # Self-contained, hardcoded three-screen stage demo (Technical + Design)
├── pitch/
│   └── diagrams/
│       ├── README.md                 # Diagram contents and reproduction command (Design + Technical)
│       ├── assets/                   # Team-approved workflow/data-model source images (Design)
│       ├── generate.py               # Deterministic Pillow source-normalization generator (Technical)
│       ├── workflow.png              # Pitch workflow visual (Design)
│       └── data-model.png            # Pitch data-layer visual (Design)
└── data/
    └── README.md                     # Intentional placeholder and unblock conditions (Technical + Product)
```

The original DOCX/PDF files may remain in `Docs/` as provenance artifacts, but the Markdown files above are the working source documents.

## Next-layer layout (specified, not built)

When the open questions are answered, the live app follows the single-process layout in [ARCHITECTURE §1](ARCHITECTURE.md#1-application-architecture):

```text
app/                    # Next.js screens + thin route wrappers required by the framework
frontend/               # UI components, browser state, typed API client
backend/                # Domain functions, schemas, repositories, one guarded LLM gateway
infra/                  # Environment/deployment adapters and observability
data/                   # Reviewed reference seed JSON and synthetic demo fixtures
tests/                  # unit, integration, golden-set, adversarial, e2e
```

One boundary is non-negotiable: `frontend/` never imports `backend/`. It uses `fetch` against same-origin API routes. Route wrappers may import backend controllers; they contain no business logic.

## Open questions blocking live-pipeline code

1. **Seed mapping set:** Which 20-30 reviewed cross-border/cross-industry skill pairs will seed the demo, and who signs them off?
2. **Target roles and industries:** Which two or three role transitions are clearest to judges (for example Product -> Marketing and Business Analysis -> Data Analysis)?
3. **Reference JD set:** Which real, public, non-personal job ads may be retained as consent-compatible evidence, how many per target role, and on what capture date?
4. **Live UI shape:** What is the simplest per-skill match presentation that clearly avoids an overall candidate score?

These questions do **not** block `app/demo.html`, which uses clearly labelled synthetic illustrative data. They do block real API routes, runtime prompts, and committed seed artifacts because those would otherwise be rewritten.

## Deliberate constraints

- No database for the hackathon. A database becomes necessary for concurrent users, cross-visit persistence, recruiter identity on an append-only decision log, or learning features that aggregate outcomes over time.
- No live AI in the stage demo. Runtime AI belongs to the next-layer app and must pass through the guarded gateway described in ARCHITECTURE.
- No second backend service, CORS setup, auth, or platform migration for hackathon scope.
- Only synthetic or explicitly consented candidate data. Public job ads and taxonomies must retain source URL, publisher, capture date, and human-review status.

## Keeping the scaffold synchronized

Any scope change must update `Docs/PROMPTS.md` first as the single current generation spec, then update every affected file in the same pass. If ARCHITECTURE headings, contracts, or responsibilities change, check README rubric links and this guide's descriptions immediately.
