# 02 — Product Specification (Functional)

Status: Approved for build · Owner: Lead agent · Source: `app/prompt/prompt.md`
Requirement IDs (`REQ-*`) are defined in `01_REQUIREMENTS_TRACEABILITY.md`. This file describes **how** each requirement behaves.

---

## 1. Product overview

Skill Bridge is a two-sided recruitment platform for the Australian labour market. It translates an international candidate's CV into ANZSCO-aligned skills, ranks jobs for the seeker, ranks applicants for the employer, and runs the full application lifecycle from "Submitted" to "Hired".

The product has **three components** (REQ-G04):

| # | Component | Route prefix | Auth |
| :--- | :--- | :--- | :--- |
| C1 | Landing page + authentication (sign in / sign up / Google) | `/`, `/signin`, `/signup/*`, `/oauth/*` | Public |
| C2 | Seeker application | `/seeker/*` | Role `seeker` |
| C3 | HR application | `/hr/*` | Role `hr` |

Route guards: a signed-out user who opens `/seeker/*` or `/hr/*` is redirected to `/signin?next=<path>`. A seeker who opens `/hr/*` (or the reverse) is redirected to their own home with toast "That area is for {other role} accounts."

---

## 2. C1 — Landing page (REQ-L01, REQ-L02)

Route `/`. Signed-in users are redirected to their role home (`/seeker` or `/hr`).

### 2.1 Sections (top to bottom)

| # | Section | Content (copy in `06_CONTENT_SPEC.md` § 3) | Design notes (`03` § 6) |
| :--- | :--- | :--- | :--- |
| 1 | Floating pill nav | Logo, anchors (How it works, For job seekers, For employers, FAQ), buttons **Sign in** (ghost) and **Get started** (primary) | Sticky `top-4`, glass |
| 2 | Hero | H1, sub-copy, CTAs **I'm looking for work** → `/signup/seeker`, **I'm hiring** → `/signup/hr`; live stats strip | 2 blurred blobs, rotated image frame |
| 3 | Live platform stats | 4 numbers pulled from `GET /api/public/stats`: live jobs, employers, candidates, ANZSCO occupations covered | `grid-cols-2 md:grid-cols-4`, numbers scale on hover |
| 4 | How it works (seeker) | 4 steps: Upload CV → Review AI-extracted skills → Get ranked jobs with ANZSCO match → Apply and track | Curved dashed SVG connector |
| 5 | For employers | 3 feature cards: Upload JD → Ranked applicants (Overall score) → Compare candidates on a radar | Asymmetric card radii |
| 6 | How we score | Plain-English summary of Overall score, ANZSCO match, Skill gap, with link "Read the scoring method" → opens `/intelligence_engine/formulas_presentation.html` in new tab | Sand section background |
| 7 | FAQ | 6 questions (accordion `details/summary`) | Chevron rotates |
| 8 | Final CTA | Two buttons as in Hero | Moss section |
| 9 | Footer | Links: Terms and Conditions (opens T&C modal), Privacy notice (opens modal), © year | — |

Stats MUST be live counts from the database, never hard-coded.

---

## 3. C1 — Authentication

### 3.1 Sign in `/signin` (REQ-L02)

- Fields: Email, Password. Button **Sign in**. Button **Continue with Google** (§ 3.4).
- Link "New here? Create an account" → `/signup`.
- Errors: wrong credentials → inline "Email or password is incorrect." (never reveal which one). 5 failed attempts in 10 min for one email → "Too many attempts. Try again in 10 minutes." (HTTP 429).
- **Demo accounts panel** (collapsible, below the form): lists the demo accounts from `04` § 4.6 with role, name/company, and a **Use this account** button that fills and submits the form. Label: "Demo accounts (seeded from real platform data)".
- On success: redirect to `next` param if same-role, else role home.

### 3.2 Role choice `/signup`

Two large cards: **I'm looking for work** (→ `/signup/seeker`) and **I'm hiring** (→ `/signup/hr`).

### 3.3 Seeker sign-up `/signup/seeker` (REQ-A01, A02, A03, A04, A05, A07)

Stepper with 4 steps. Progress persists in `sessionStorage` so refresh does not lose data.

**Step 1 — Choose a method**
- Option A (primary card): **Upload your CV** — drop zone. Accepts `.pdf`, `.docx`, `.txt`; max 5 MB; one file. Validation errors inline: "Only PDF, DOCX or TXT files are accepted." / "File is larger than 5 MB."
- Option B (secondary): **Continue with Google instead** → § 3.4 (T&C tick still required, see Step 4 rule).
- Link "Already have an account? Sign in".

**Step 2 — Scanning** (after upload)
- `POST /api/cv/scan` (multipart). UI shows an animated organic progress blob with the stage list: "Reading file" → "Extracting text" → "Finding personal details" → "Mapping skills to ANZSCO" → "Done". Stages advance from the server response `stages[]` (no fake timers longer than the real request; minimum display 1.2 s for readability).
- Failure (unreadable/empty text) → error card "We could not read text from this file. Try a DOCX or TXT version, or continue with Google and upload later." with buttons **Try another file** and **Continue with Google**.

**Step 3 — Review what we found** (REQ-A02, REQ-A07, REQ-S22)
Two editable panels. Every field produced by extraction carries an **AI** badge (sand) with tooltip "Extracted by AI from your CV — please check." Editing a field changes the badge to **Edited** (moss); clicking **Confirm** without editing changes it to **Confirmed**.

- *Personal details*: Full legal name, Email (pre-filled if found), Phone (optional), Country of origin, Current/most recent job title, Years of experience (number, 0–50, step 0.5), Highest education, Preferred work location in Australia (select: Sydney, Melbourne, Brisbane, Gold Coast, Perth, Adelaide, Canberra, Hobart, Darwin, Remote — default from CV if found, else Sydney).
- *Target occupation*: ANZSCO code + title (select from the ANZSCO list in `04` § 5.2), pre-selected by extraction; shows "Why this occupation" (matched keywords).
- *Skills*: chips grouped **Direct skills**, **Transferable skills**. Each chip: label, type, evidence quote (expand on click), actions Edit / Remove. **+ Add skill** input with autocomplete from the ANZSCO core-skill vocabulary (free text allowed).
- *Known gaps* (from CV, e.g. missing registration): list, editable, user can add.
- *Experience timeline*: roles (title, employer, country, start, end) extracted; editable rows; add/remove.
- Validation: name, title, years, ANZSCO code required; at least 1 skill.

**Step 4 — Create your account**
- Fields: Email (required, unique), Password (min 10 chars, ≥1 letter and ≥1 number; strength meter), Confirm password.
- **Alias** (REQ-A07): required, 3–24 chars, letters/numbers/space/hyphen, unique (live check `GET /api/aliases/check?alias=`). Helper: "Employers see this name instead of your real name." Button **Suggest** generates `"{Adjective} {Noun}"` from a fixed list (06 § 5).
- Checkbox **I agree to the [Terms and Conditions] and acknowledge the [Privacy notice]** (REQ-A03). Links open modals (REQ-A04, § 3.6). Submit button disabled until ticked; if user tries to submit via keyboard, show inline error "Please accept the Terms and Conditions to continue."
- **Create account** → `POST /api/auth/signup/seeker` with profile + skills + alias + `termsVersion`. On success → `/seeker` with welcome toast "Welcome, {alias}. Your matches are ready."

### 3.4 Google sign-in — protocol-only implementation (REQ-A05)

No real Google credentials are used. Implement the **OAuth 2.0 Authorization Code flow with PKCE + OpenID Connect** against a **local mock Google authorization server** hosted by the Product API, so the protocol is real and swappable for Google later by changing config only.

Sequence:
1. Front-end requires the T&C checkbox to be ticked on the screen where the Google button is pressed (sign-up screens). On `/signin` no tick is required for existing accounts; if Google returns an unknown email, the user is sent to `/signup/google-complete` where the T&C tick + alias + role choice are required before the account is created.
2. Front-end generates `state` (32 random bytes, base64url), `nonce`, `code_verifier` (43–128 chars) and `code_challenge = BASE64URL(SHA256(code_verifier))`, stores them in `sessionStorage`, and redirects to `GET {OAUTH_AUTHORIZE_URL}?response_type=code&client_id=skillbridge-web&redirect_uri={APP}/oauth/google/callback&scope=openid%20email%20profile&state=..&nonce=..&code_challenge=..&code_challenge_method=S256&prompt=select_account`.
3. Mock authorize page (`/mock-google/authorize`, served by the API, styled neutrally with a "Simulated Google sign-in (demo)" banner) shows an account chooser: the seeded demo Google identities (§ 04 4.6) + "Use another account" (enter name + email). Selecting returns `302 redirect_uri?code=..&state=..`.
4. `/oauth/google/callback` (Next page) verifies `state` equals stored value (else error screen "Sign-in was interrupted. Please try again."), then calls `POST /api/auth/google/exchange {code, code_verifier, redirect_uri, nonce, intent: "signin"|"signup", role}`.
5. API validates code (single use, 60 s expiry), PKCE, issues an `id_token` (JWT HS256 signed with `MOCK_GOOGLE_SECRET`, claims `iss, aud, sub, email, email_verified, name, nonce, iat, exp`), validates it exactly as it would a Google token (iss, aud, exp, nonce), then: existing user with that `google_sub` or email → session; new user → pending registration token → `/signup/google-complete`.
6. `/signup/google-complete`: role (pre-set from intent), alias (seeker) or company name + job title (HR), T&C tick required → create account with `auth_provider = "google"`, no password, no CV/JD.
7. Result for seeker: `/seeker` shows the **No CV state** (§ 4.2). Result for HR: `/hr` shows the **No JD state** (§ 5.2) (REQ-A06, REQ-H02).

Config keys (`.env`): `OAUTH_AUTHORIZE_URL`, `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `MOCK_GOOGLE_SECRET`. Swapping to real Google = change URLs/client id and replace HS256 validation with Google JWKS (RS256) — document this in `product_api/README.md`.

### 3.5 HR sign-up `/signup/hr` (REQ-H01, REQ-H02, REQ-A03)

**Step 1 — About you**: Full name, Work email, Job title, Company name (autocomplete from existing employers in DB; picking an existing employer links the account to that employer's seeded jobs only if it is an unclaimed seeded employer — see `04` § 4.5), Password + confirm, T&C checkbox (required). Or **Continue with Google**.

**Step 2 — Add your first job description (optional)**: upload `.pdf/.docx/.txt` (5 MB) **or** paste text, then **Scan JD**. Or **Skip for now** → account created, lands on No JD state.

**Step 3 — Review the job** (REQ-H08): AI-extracted fields with AI badges, all editable: Job title, Company, Location (city + state), Employment type (Full-time, Part-time, Contract, Casual), Salary min / max (AUD) + period (Annual / Hourly), Category (8 categories), ANZSCO code + title, Required years of experience, Key requirements (list), Responsibilities (list), Description (rich text: paragraphs + bullets only), Listing duration (14 / 30 / 45 / 60 days, default 30). **Publish job** → `POST /api/hr/jobs` → `/hr`.

### 3.6 Terms and Conditions modal (REQ-A04)

- Opens from every T&C link (sign-up forms, Google-complete page, footer). Title "Terms and Conditions", version + effective date, scrollable body with section headings and a sticky mini table of contents. Full text: `06_CONTENT_SPEC.md` § 1.
- Buttons: **Close** (ghost) and **I agree** (primary). **I agree** ticks the originating checkbox and closes the modal. **I agree** is enabled only after the user has scrolled to the end of the text (progress bar at top shows read %).
- Accessible: `role="dialog"`, `aria-modal="true"`, focus trap, Esc closes, focus returns to the link.
- Privacy notice modal: same component, text in `06` § 2, only a **Close** button.
- Acceptance is stored server-side: `terms_version`, `terms_accepted_at`, `privacy_version`.

### 3.7 Session

HTTP-only, `SameSite=Lax` cookie `sb_session` (opaque random token, 7-day expiry, server-side sessions table). **Sign out** in the sidebar account menu deletes the session.

---

## 4. C2 — Seeker application

### 4.1 Layout shell (REQ-S19 … REQ-S24)

Left sidebar (fixed, 280 px desktop; collapsible to 76 px icon rail; off-canvas drawer below `md`):

| Order | Item | Behaviour |
| :--- | :--- | :--- |
| 1 | Logo | → `/seeker` |
| 2 | **Account** (avatar circle with initials of alias) | Opens Account menu: *Personal details* (`/seeker/account/profile`), *My CV* (`/seeker/account/cv`), *Skills* (`/seeker/account/skills`), *Sign out* |
| 3 | **Jobs for you** | `/seeker` (home feed) |
| 4 | **Saved jobs** + count badge | `/seeker/saved` (REQ-S23) |
| 5 | **Applications** + count of active applications | `/seeker/applications` (REQ-S24) |
| 6 | **Compare jobs** + count of jobs in tray | `/seeker/compare` (REQ-S27) |
| 7 | **Hidden jobs** | `/seeker/hidden` — jobs the seeker ignored or reported, with **Restore** |
| 8 | Profile completeness ring (bottom) | % of profile fields confirmed by user; click → first unconfirmed field |

Mini lists (REQ-S23/S24): under "Saved jobs" and "Applications" the sidebar shows up to 3 most recent items (title + company / title + status pill) when expanded; "View all" link.

### 4.2 No CV state (REQ-A06)

If the seeker has no CV/profile skills (Google sign-up without CV): home shows a centred organic card: title "Add your CV to see jobs matched to you", sub-copy, a large circular **+** button (64 px, moss, label "Upload CV" below, `aria-label="Upload CV"`). Clicking opens the **CV upload drawer** that runs § 3.3 Steps 1–3 inline (scan + review) and saves to the profile. The search bar and job list are **not shown** until a CV is processed. Sidebar items Saved/Applications/Compare are visible but show empty states.

### 4.3 Home feed `/seeker` (REQ-S01 … REQ-S08, REQ-S15, REQ-S16)

**Search bar** (REQ-S01), top of page, pill input, placeholder "Search job title, company, skill or location". Debounced 300 ms; Enter submits; clear (×) button. Query is matched (case-insensitive, all terms must match) against title, company, description, requirements, location, category, ANZSCO title. Optional filter chips under the bar: **Category** (multi), **City** (multi), **Posted within** (Any, 7 days, 14 days, 30 days). The query and filters only **filter**; ordering is always FRS★ (REQ-S15). URL reflects state (`?q=&cat=&city=&within=`).

**Header line**: "{N} jobs ranked for you" + info icon tooltip "Ranked by Overall score, adjusted by the jobs you save, apply to and hide."

**Job list** (REQ-S02): ordered by FRS★ descending (ties: newer `posted_at` first, then job id). Excludes jobs the seeker ignored, reported, applied to (applied jobs live in Applications), expired/closed jobs, and jobs under global review (`04` § 6.4). Infinite scroll, 20 per page, skeleton cards while loading.

**Job card** (REQ-S03 … REQ-S07, S13, S14) — collapsed card, whole card clickable (except buttons):

| Element | Source | Format |
| :--- | :--- | :--- |
| Title, company, city | job | Title in Fraunces 600 |
| **Overall score** (REQ-S03) | FRS★ | Circular gauge 0–100, integer, label "Overall" |
| **Short description** (REQ-S04) | `job.short_description` (`04` § 4.4) | ≤ 160 chars, 2-line clamp |
| **ANZSCO match** (REQ-S05) | SMF vs job ANZSCO code | "82% ANZSCO match" + bar; tooltip shows ANZSCO code + title |
| **Skill gap** (REQ-S06) | GSI → level | Pill: **Low gap** (GSI < 20, moss) / **Moderate gap** (20–44.9, clay) / **High gap** (≥ 45, burnt sienna); plus "{n} gaps · ~{T} months to close" |
| **Posted** (REQ-S07) | `posted_at` | Relative: "Posted today", "Posted 1 day ago", "Posted 13 days ago", ≥ 60 days → "Posted 2 months ago". Tooltip with exact date (dd MMM yyyy). Derived dates show "(estimated)" in the tooltip. |
| Salary | job salary | "$120k–$130k a year" / "$40 an hour" / "Salary not listed" |
| **Save** (REQ-S13) | toggle | Bookmark icon button, `aria-pressed` |
| **Report** (REQ-S14) | dialog | Flag icon button |
| **Compare** | toggle | "Compare" checkbox-chip, adds to compare tray (max 4) |

Every job surface (feed card, saved list row, compare column, job detail, hidden list) shows **Save** and **Report** (REQ-S13, REQ-S14).

Impression logging: when a card is ≥ 50% visible for ≥ 1 s, the client batches `POST /api/events/impressions` (deduped per seeker/job/day server-side) — feeds the HR "Appearances" metric (REQ-H05).

### 4.4 Save behaviour (REQ-S13, REQ-S16, REQ-S23)

- Click Save → optimistic toggle to filled bookmark + toast "Saved to your list" with **Undo** (6 s). Server: `PUT /api/seeker/saved/{jobId}` → insert `saved_jobs`, log event `save`. Unsave → `DELETE` + event `unsave`.
- Saved jobs stay in the feed (with filled icon) and appear in `/seeker/saved` (newest first) and the sidebar mini list; count badge updates instantly.
- Saving changes ranking (REQ-S16): feed re-ranks on next fetch using `04` § 6. After a save the client re-fetches page 1 silently and animates reordering (FLIP, 300 ms) but never moves the card the user just interacted with out of view.
- Saved list row: title, company, Overall, ANZSCO match, gap pill, posted, status ("Open" / "Expired" / "Closed by employer" — expired saved jobs remain listed, greyed, Apply disabled), buttons Apply, Remove (unsave), Report, Compare.

### 4.5 Report behaviour (REQ-S14)

- Click Report → dialog "Report this job". Reason (radio, required): *Job details are wrong or misleading*, *ANZSCO occupation or match looks wrong*, *Job is no longer available*, *Duplicate listing*, *Scam or suspicious*, *Discriminatory content*, *Other*. Details textarea (required for *Other* and *ANZSCO…*, max 500 chars). Checkbox "Also hide this job from my feed" (default on).
- Submit → `POST /api/jobs/{id}/reports`. One open report per seeker per job (second attempt shows "You already reported this job on {date}."). Toast "Thanks — our team and the employer will review it."
- Effects: if hide = on → job removed from this seeker's feed (listed in Hidden jobs with reason "Reported"). Server rules in `04` § 6.4 (threshold auto-hide, HR notification, HR resolution). Seeker sees report status in Hidden jobs: *Open*, *Resolved – job corrected*, *Resolved – no change*.

### 4.6 Job detail `/seeker/jobs/{id}` (REQ-S08 … REQ-S12, REQ-S17, REQ-S18)

Opens as a full page (deep-linkable) with a back link that restores feed scroll position. Records a `view` event (unique per seeker/job) for HR metrics.

Layout (desktop two columns 7/5; mobile stacked):

Left column:
1. Header: title, company, city, employment type, salary, posted (relative + exact), ANZSCO code/title chip, listing source link ("Original listing").
2. **Score summary row**: Overall (FRS★), ANZSCO match (SMF), Job readiness (JRS), Skill gap level.
3. **Chart A — ANZSCO match over time** (REQ-S09): line chart, x = months from today (0 … ceil(T_bridge), min 6), y = projected SMF % (0–100). Definition in `04` § 7.1. Reference line at 85% labelled "Direct alignment". Tooltip per point: month, match %, gaps closed by then.
4. **Chart B — Skill gap over time** (REQ-S10): line chart, x as Chart A, y = projected GSI (0–100, lower is better), area fill below the line; second line JRS optional toggle. Definition in `04` § 7.2. Horizontal bands for Low/Moderate/High.
5. **Explanation** (REQ-S11), plain English, generated from formula outputs (template in `06` § 4):
   - "Why this score": FRS sub-scores — Capability, Salary, Location, Freshness — each as a labelled bar with one sentence.
   - "How you match ANZSCO {code} {title}": SMF sub-metrics (Taxonomy, Direct skills, Transferable, Experience multiplier) + lists **Matched skills** and **Missing core skills**.
   - "Your gaps": table from Formula 2 — Gap, Category (Statutory licence / Core discipline / Tool / Local standard), Severity points, Estimated months, "Blocker" flag for statutory items; total bridge duration; readiness tier text.
   - "What would raise your score": up to 3 actions = the gaps with the highest severity points per month.
6. Job description and requirements (full).

Right column (sticky): action panel with **Apply** (primary), **Ignore** (outline), **Save**, **Report**, **Add to compare**; mini "Similar jobs" (top 3 by JPI ≥ 50 with this job, excluding hidden/applied) each with Save/Report.

**Apply** (REQ-S12, REQ-S17): opens Apply dialog:
- Shows what will be sent: alias, current title, years, ANZSCO occupation, skills (confirmed + edited only; unconfirmed AI skills listed with a warning "Not yet confirmed — confirm before applying?" and link to Skills page), CV file name, gaps (seeker may toggle "Share my known gaps with the employer", default on).
- Optional message to employer (max 1,000 chars).
- Consent checkbox (required): "I agree to share this application with {company} under the Terms and Conditions."
- **Send application** → `POST /api/applications`. Server snapshots scores (FRS, SMF, GSI, JRS, TSS for this job) and profile, creates application `submitted`, immediately transitions to `cv_scanning` (system), then after the scan job completes (≤ 5 s, async) to `under_review`… see pipeline `04` § 8. Success screen: "Application sent to {company}" + mini timeline + **View application** / **Back to jobs**. Job leaves the feed and appears in Applications.
- Disabled cases: job expired/closed ("This job is no longer accepting applications"), already applied ("Applied on {date}" + link).

**Ignore** (REQ-S12, REQ-S18): immediate, no dialog. Job removed from feed (card collapses with 300 ms animation), toast "Job hidden. We'll show fewer jobs like this." + **Undo** (8 s). Server `PUT /api/seeker/ignored/{id}` + event `ignore`; affects ranking (`04` § 6). From detail page, Ignore returns to the feed. Restorable later from Hidden jobs (**Restore** → `DELETE` + event `unignore`).

### 4.7 Applications `/seeker/applications` (REQ-S24, REQ-S25, REQ-S26)

- Tabs: **Active** (not terminal), **Closed** (hired, rejected, withdrawn, job closed). Sorted by last status change desc.
- Row (collapsed) (REQ-S25): job title, company, status pill (colour per status, `03` § 5.9), "Updated {relative}". Click → expands (accordion) or on mobile opens a sheet.
- Expanded (REQ-S26): **Timeline bar** — horizontal stepper on desktop, vertical on mobile, with all checkpoints of `04` § 8.1 in order: *Submitted → CV scanning → Under review → Shortlisted → Interview → Final assessment → Offer → Hired*. Completed checkpoints filled moss with date/time; current checkpoint pulses softly (respect `prefers-reduced-motion`); future checkpoints outlined. Terminal *Rejected* or *Withdrawn* renders as a burnt-sienna/grey node after the last reached checkpoint with remaining steps faded. Each node tooltip: date, actor ("Skill Bridge", "Employer"), and the note from the employer if shared. Interview node shows interview date/time/mode when HR scheduled it.
- Also shown: score snapshot at time of applying vs current, message sent, **Withdraw application** (allowed until *Offer*; confirm dialog; sets `withdrawn`).
- Offer stage: seeker sees **Accept offer** / **Decline offer**. Accept → `hired` (job counted as hired in HR dashboard; other active applications unaffected). Decline → `withdrawn` with note "Offer declined".

### 4.8 Compare jobs `/seeker/compare` (REQ-S27)

- Compare tray: floating pill at bottom showing selected jobs (2–4), **Compare now** enabled at ≥ 2. Selection persisted server-side (`compare_items`) so it survives reloads.
- Page: **Radar ("spider web") chart** with all selected jobs overlaid as translucent polygons (fill opacity 0.18, stroke 2 px, colours from `03` § 2.6 chart palette, legend with toggles). Axes (all 0–100, same scale), defined in `04` § 7.3: *ANZSCO match*, *Job readiness*, *Salary*, *Location fit*, *Freshness*, *Overall*.
- Below: comparison table (columns = jobs): every axis value, salary text, city, posted, gaps count + bridge months, statutory blocker yes/no; best value per row highlighted.
- Pairwise **Job similarity** matrix (Formula 3 JPI) with tier label and salary delta.
- Each column header has Save, Report, Apply, Remove from compare.
- Entry points: "Compare" chip on cards, detail page button, Saved list.

### 4.9 Account pages (REQ-S19 … REQ-S22)

- **Personal details** `/seeker/account/profile` (REQ-S19): edit all personal fields of § 3.3 Step 3 + alias (uniqueness check) + email (re-auth with password if provider = password) + preferred location. Change password (password accounts). Save → recompute scores (feed cache invalidated). Delete account (confirm by typing alias) → soft-delete, applications withdrawn.
- **My CV** `/seeker/account/cv` (REQ-S20): current file (name, size, uploaded date, **Download**, **Preview text**); **Replace CV** runs scan → **diff review** screen: for every field and skill shows *Current* vs *New from CV* with per-row choice Keep / Use new; nothing is overwritten without confirmation. Upload history (last 5 versions).
- **Skills** `/seeker/account/skills` (REQ-S21, REQ-S22): table of skills with columns Skill, Type (Direct/Transferable), Evidence, Source (*AI* / *You*), Status (*AI – unconfirmed* / *Confirmed* / *Edited* / *Added by you*), actions Confirm, Edit, Remove, Restore. Filter "Show unconfirmed AI skills". Bulk **Confirm all**. Edits are stored as corrections (`field_corrections`) and preserved across CV re-scans. Target ANZSCO occupation editable here. Known gaps editable here (add/remove, mark "Resolved" with optional evidence → removed from gap calculation). Banner shows "Your match scores update when you save." After save, show "Scores updated" with how many feed jobs changed by ≥ 5 points.

### 4.10 Hidden jobs `/seeker/hidden`

List of ignored and reported jobs: reason (Ignored / Reported – {reason} – {report status}), date, **Restore** (removes ignore; for reported jobs restores visibility for this seeker only), Save, Report (disabled if already reported).

---

## 5. C3 — HR application

### 5.1 Layout shell (REQ-H06 … REQ-H10)

Left sidebar (same component as seeker, HR colourway = clay accents):

| Order | Item | Behaviour |
| :--- | :--- | :--- |
| 1 | Logo | → `/hr` |
| 2 | **Account** avatar | Menu: *Personal details* (`/hr/account/profile`), *Company* (`/hr/account/company`), *Sign out* |
| 3 | **Dashboard** | `/hr` |
| 4 | **Jobs** + active count | `/hr/jobs` (REQ-H04) — includes JD editing (REQ-H07, H08) |
| 5 | **+ Post a job** | `/hr/jobs/new` |
| 6 | **Candidates** section (REQ-H09, H10) | Inline sidebar list (see § 5.6) + link "Open candidate board" → `/hr/candidates` |
| 7 | **Compare candidates** + tray count | `/hr/compare` (REQ-H11) |
| 8 | **Reports** + open count | `/hr/reports` — seeker reports on this employer's jobs |

### 5.2 No JD state (REQ-H02)

If the HR account has 0 jobs: home shows centred card "Post your first job to start receiving ranked candidates" with circular **+** button labelled "Add job description" → JD upload/paste drawer (§ 3.5 Steps 2–3). Dashboard metrics hidden until ≥ 1 job exists.

### 5.3 Dashboard `/hr` (REQ-H03)

Metric cards (exact definitions in `04` § 9), for all jobs owned by this HR account's employer:

| Card | Definition |
| :--- | :--- |
| **Total jobs** | All jobs ever posted (any status) |
| **Active** | `status = active` and `expires_at > now` |
| **Expired** | `expires_at ≤ now` or `status = expired` (excludes manually closed) |
| **Hired** | Applications with status `hired` |
| **Rejected** | Applications with status `rejected` |

Each card is clickable: jobs cards → `/hr/jobs?status=…`; Hired/Rejected → `/hr/candidates?status=…`.
Below the cards (supporting, read-only): "Pipeline" bar showing count per application status across all jobs; "Needs attention" list: applications in `under_review` > 3 days, open reports, jobs expiring in ≤ 3 days (with **Extend 30 days** button).

### 5.4 Jobs list `/hr/jobs` (REQ-H04, REQ-H05)

Tabs: All / Active / Expired / Closed / Under review (reported). Search by title. Sorted by `posted_at` desc.

Job row — collapsed (REQ-H05):
- **Job title**, **company name**
- **Description** — short description (≤ 160 chars)
- **Posted** — relative time (+ exact tooltip); expiry "Expires in 12 days" / "Expired 3 days ago"
- **Appearances** (impressions), **Views**, **Applicants** — numbers with icons and tooltips explaining each (`04` § 9)
- Status pill.

Click → expands: full description, requirements, metrics sparkline (last 30 days, impressions/views/applies per day), applicant breakdown by status, top 3 applicants by TSS, buttons **Edit JD**, **View applicants** (→ `/hr/candidates?job={id}`), **Close job** (confirm; stops applications; status `closed`; active applicants receive status note), **Extend** (+30 days), **Reopen** (for closed/expired, sets new `expires_at`).

### 5.5 Edit JD `/hr/jobs/{id}/edit` (REQ-H07, REQ-H08)

Same form as § 3.5 Step 3. AI-extracted fields keep AI badges until confirmed/edited; each AI field shows the source excerpt from the JD on hover. **Re-upload JD** runs scan → diff review (Keep / Use new) like the seeker CV diff. Saving recalculates TSS for all applicants and invalidates seeker feeds containing the job. Change history panel (who, when, field, old → new). If the job was auto-hidden by reports, saving shows "Mark reports as resolved?" (see § 5.8).

### 5.6 Candidates — sidebar list and board (REQ-H09, REQ-H10, REQ-H12)

Scope: seekers who **applied** to any job of this employer. Filter: Job (default "All jobs"), Status. Ranked by TSS for the applied job (desc). A candidate who applied to several jobs appears once per application.

**Collapsed item** (REQ-H09, REQ-H10) — both in the sidebar (compact) and on `/hr/candidates` (full width):
- **Alias** (never legal name), **title** (current job title), **experience** ("8 yrs"), **ANZSCO match %** (SMF for the applied job's ANZSCO code), **skill gap** level pill + GSI, **Overall** (TSS gauge), **status** pill, applied job title (board only).

**Expanded** (click; accordion; only one expanded at a time in the sidebar, many on the board):
- Origin country, education, target ANZSCO occupation, preferred location
- Skills (confirmed/edited/added; AI-unconfirmed shown with "AI" badge so HR knows it is unverified) with evidence quotes
- Formula 6 breakdown: Requisition fit, Seniority parity, Evidence rigour, Regulatory readiness, Data compliance — bars + one-line explanations
- Formula 2 gaps table (category, months, blocker)
- Seeker message, shared gaps
- Application timeline (same component as seeker, HR view)
- CV: **View CV text (PII-redacted)** — email, phone, legal name, street address redacted (`04` § 10)
- **Status actions** (only valid next transitions from `04` § 8.2): e.g. **Shortlist**, **Schedule interview** (date, time, mode: Video/Phone/On-site, location/link, note), **Move to final assessment**, **Make offer** (salary, start date, note), **Reject** (reason select + optional note to candidate; "Share note with candidate" toggle). Each action writes `application_events` and is reflected in the seeker's timeline immediately.
- **Add to compare** toggle.

### 5.7 Compare candidates `/hr/compare` (REQ-H11)

- Tray as seeker compare; 2–4 candidates; candidates must be applicants to the **same job** (selector at top "Compare for job: …"; adding a candidate for a different job prompts to switch).
- **Radar chart** overlaying each candidate's polygon (same visual rules as § 4.8). Axes (0–100) defined in `04` § 7.4 — *skills and experience*: *ANZSCO match*, *Skill depth*, *Experience*, *Seniority fit*, *Evidence*, *Transferable skills*, *Regulatory readiness*.
- Table: all axis values, years, TSS, RMS, GSI, gaps, status; best per row highlighted.
- Head-to-head (exactly 2 selected): Formula 4 Δ with verdict text from the engine.
- Each column: alias, status, quick actions (Shortlist / Reject / Open profile).

### 5.8 Reports `/hr/reports`

List of reports on this employer's jobs: job, reason, details, date, count of reporters for that job, status. Actions: **Edit job** (→ edit page), **Resolve – job corrected**, **Resolve – no change** (requires a note visible to reporters). Resolving un-hides an auto-hidden job (`04` § 6.4).

### 5.9 Account pages (REQ-H06)

- **Personal details**: full name, job title, email (re-auth), phone, password change, sign out of all sessions.
- **Company**: company name (display), website, about (used in job detail "About the employer"), logo initials colour. Changing company name updates all its jobs' displayed company.

---

## 6. Cross-cutting behaviour

- **Optimistic UI** for save/ignore/compare with rollback + error toast "Couldn't save that. Check your connection and try again."
- **Loading**: skeletons matching card shapes; never a blank screen > 300 ms.
- **Empty states**: every list has illustrated empty state copy (`06` § 3.6).
- **Toasts**: bottom-centre, auto-dismiss 6 s, pause on hover, Undo where specified.
- **Responsive**: 375, 768, 1024, 1440 px verified (REQ-G02, `03` § 9).
- **Accessibility**: WCAG 2.2 AA; keyboard operable; charts have a "View data as table" toggle.
- **Performance**: feed page 1 API ≤ 800 ms p95 on the seeded DB (461 jobs); scores cached per (seeker revision, job revision).
- **Two-tab demo**: a seeker and an HR user signed in in two browsers see each other's changes on refresh; seeker Applications and HR Candidates poll every 15 s while visible.
