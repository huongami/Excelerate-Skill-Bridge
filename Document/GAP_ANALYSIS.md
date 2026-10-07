# Gap analysis: Technical Requirements against the current app

| | |
|---|---|
| Source document | [`sdd/06_TECHNICAL_REQUIREMENTS.md`](sdd/06_TECHNICAL_REQUIREMENTS.md) (read-only) |
| Checked against | `jinder_platform/` (API, database), `jinder_frontend/app/` (web client), `jinder_backend_engine/intelligence_engine/` (formulas) |
| Date | 8 October 2026 |
| Method | Each bullet of the requirements was checked in the code, not in the docs. Paths below are relative to the repository root. `BE` = `jinder_platform/jinder/`, `FE` = `jinder_frontend/app/js/`. |

**Status words**
- **Missing**: the app does not have it.
- **Partial**: the app has part of it, or does it in a different way.
- **Done**: the app meets the requirement.

Items marked `[DISCUSS]` are open questions in the source document. This file says what the app does now. The team must confirm these decisions.

> **Note: these gaps are future enhancements.**
> The current app is the hackathon MVP. The gaps in this file are **not defects of the MVP scope**. They are the backlog of **enhancements for future versions**, and section 9 is the plan to build them.
> One exception: the admin access control in section 1. Fix it before the app runs on a shared computer, a network or in public.

---

## 1. Fix first: the admin routes have no access control

**Severity: critical (privacy).**

The routes `/admin/*` do not check a session or a role (`BE/routes/admin.py`, lines 15, 107, 242). A caller can:
- read every table, including emails, private CV evidence lines, `parses.result`, `cv_files` and the feedback to the team (`GET /admin/table-data`);
- run SQL (`POST /admin/sql`).

`admin.html` calls these routes without a token. `tests/test_admin.py` calls them without a token and expects success.

**Current risk:** low on a laptop, because the server listens on `127.0.0.1` by default (`BE/config.py:56`). **The risk is high** if someone starts the server with `--host 0.0.0.0` or puts it on a network.

**Action:** require an admin role (or turn the routes off outside development) and add a test that a call without a token gets 401.

---

## 2. P0 (critical): missing

| # | Requirement | What is missing | Evidence |
|---|---|---|---|
| 1 | TR-R-05, TR-SYS-06 | The Basic limit of **50 open jobs** and the upgrade prompt. `job_create` has no count check. | `BE/routes/recruiter.py:146-195`, `BE/config.py:71-73` |
| 2 | TR-R-06, TR-SYS-01 | A **scheduled auto-close** at `close_at`, and a stored job status. "Open" is calculated from `closes_at` when a job is read. A closed job can open again if the employer sets a new date. | `BE/catalogue.py:82-84`, `BE/routes/recruiter.py:241-243` |
| 3 | TR-R-02, TR-R-11, §1.3 | **`visibility_opt_in`**: a talent cannot choose to appear (or not) in employer lists. Every talent with a done profile is in the pool. | `BE/store.py:383-410` |
| 4 | TR-SYS-01, TR-JS-12 `[DISCUSS]` | **Withdrawn** status: a talent cannot withdraw an application. | `BE/routes/applications.py:18-26`, `BE/schema.sql:206-207` |
| 5 | TR-SYS-01, TR-JS-14 `[DISCUSS]` | **Expired** offer: no `expires_at`, no Expired state. | `BE/routes/applications.py:24` |
| 6 | §5 Privacy | **Consent recorded on the server** before the CV is processed. There is only a terms check box in the sign-up form. | `FE/views/auth.js:241`, `BE/routes/account.py:224` |
| 7 | §5 Privacy | **Encryption** in transit and at rest. The server uses plain HTTP. SQLite and the uploads are plain files. | `BE/parsing.py:31-41` |
| 8 | TR-JS-05, TR-JS-15 | A **versioned profile save**. The profile is overwritten. Only the application snapshot is frozen. | `BE/store.py:281-305` |
| 9 | TR-JS-05 | An **unsaved-changes warning**. Closing the edit dialog drops the changes with no warning. | `FE/components/onboarding.js:963-969` |
| 10 | TR-JS-05 | **Add a skill** on the translation step. A skill can be added only on the earlier Skills step. | `FE/components/onboarding.js:305-346` |
| 11 | TR-JS-09 | Job detail **actions at the bottom right**. They are in the header under the title. | `FE/views/jobs.js:142-148` |
| 12 | TR-JS-12 | **Optimistic concurrency** on the application edit (no version or If-Match check). | `BE/routes/applications.py:213-222` |
| 13 | TR-JS-02, TR-JS-07, TR-SYS-02 | **Caching**: of parse results by file hash, and of the recommendation list. Each request runs the formulas again (CHANGELOG defect D-3). | `BE/schema.sql:98-109`, `BE/routes/jobs.py:68-80` |
| 14 | §1.3 | An **ExperienceItem** entity (title, description, source country and industry for each role). Roles are a JSON list of names. | `BE/schema.sql` (`profiles.current_role`) |
| 15 | TR-JS-03, TR-JS-04 | **No LLM is used.** CV parsing and skill translation are rule-based (regular expressions and the taxonomy). So these are missing: LLM generalisation for unseen skills with an "inferring" flag, and schema validation with one retry of the AI output. An unknown skill keeps its own name. | `BE/cv_parser.py`, `BE/translation.py:353-355` |

---

## 3. P0 (critical): partial

| Requirement | What is different or not complete | Evidence |
|---|---|---|
| TR-SYS-10 Landing | A signed-in user is not redirected to Home (the page shows "Go to my workspace"). The hero still says "ranked … never a black box", and the preview shows an "86%" match score. The "anonymous talent" promise is not stated. 55 contrast failures are open (CHANGELOG D-2). | `FE/main.js:19`, `FE/views/landing.js:17-30` |
| TR-R-06 My jobs | The badge is yellow only when fewer than 7 days are left. A job with exactly 7 days left is green, but the spec says "7 days or less" is yellow. | `BE/routes/recruiter.py:34-43` (`left < 7`) |
| TR-R-02 Employer home | Talent is not filtered to the employer's open jobs; the list is ranked against one job (the newest open job). The panel shows 3 talents, but N = 5. | `BE/routes/recruiter.py:442-485`, `FE/views/recruiter.js:171-188` |
| TR-R-03 Anonymised view | The leak check removes emails and phone numbers, but not names. Employers do not see the translation reason of each skill. Identity is shared when the talent picks a slot (not at interview confirmation). Consent is a flag plus a history row, with no own timestamp column. | `BE/util.py:199-216`, `BE/store.py:332-375`, `BE/routes/applications.py:241-243` |
| TR-R-04 Talent detail | Skip is only on the list cards, not on the detail page. Report has no "wrongly recommended" reason. | `FE/views/recruiter.js:1192-1193, 1323-1331` |
| TR-R-05 Post a job | Required skills are mandatory (1 to 12), not optional. | `BE/routes/recruiter.py:75-114` |
| TR-JS-09 Job detail | The per-skill list does not show the talent's evidence or the reason, although the API sends `reason`. | `FE/components/status.js:34-50`, `BE/skills.py:206-220` |
| TR-SYS-02 Matching | The evidence for each skill is only a level number. The order also uses non-skill factors (seniority, certifications; in the talent feed also location, salary and saved companies). No protected attribute is used. | `BE/routes/recruiter.py:419`, `BE/engine_bridge.py:341` |
| TR-SYS-03 Notifications | The key events (new application, status change, slots offered, slot confirmed) are in-app only (`email=False`). Only result, offer and rejection send email. The spec says email first. There are no templates and no idempotency key. | `BE/routes/applications.py:162`, `BE/routes/recruiter.py:347, 365, 378` |
| TR-SYS-06 Plan screen | Basic and Premium are two radio options with one-line hints, not side by side. The screen does not list the open-job limit or the statistics per plan. The premium look is a crown, a gold ring and a chip only. No `valid_until`. | `FE/views/settings.js:64-65`, `FE/components/shell.js:141-146` |
| TR-SYS-01 History | `application_history.actor` is a role word, not an actor id. There is no `from_status`. Some extra moves are allowed (Applied, Contacted and Accepted to Rejected). | `BE/schema.sql:226-233` |
| TR-JS-01 Sign-up | Sign-up does not ask for the country of study or work, or the target role (`[DISCUSS]`). | `BE/routes/account.py:26-65` |
| TR-JS-18 Onboarding | 8 steps, not the short linear flow. Progress is saved to the server only when the dialog closes. The step position is not restored. | `FE/components/onboarding.js:23-25, 993-1008` |
| TR-JS-03 Parsing | Employers, dates and responsibilities are not returned as structured items for each role. Responsibilities become free evidence lines. | `BE/cv_parser.py:1784-1816` |
| TR-JS-12 Edit window | Only the note can be edited. | `BE/routes/applications.py:213-222` |
| §5 Privacy page | The text is a placeholder and some statements are wrong (for example, "data stays in your browser"). | `FE/views/legal.js:57, 72` |

---

## 4. P1 (if time allows): missing or partial

| Requirement | Gap |
|---|---|
| TR-JS-01 | Email verification and password reset ("Forgot password?" shows "not available yet"). |
| TR-JS-02 | OCR for scanned PDFs. |
| §5 Security | Virus scanning of uploads. Rate limits on upload and parse endpoints (only sign-in and the password check have limits). |
| TR-JS-13, TR-R-09 | No "no slot fits" path for the talent. The employer cannot reschedule or cancel an interview. No check for the same time across two applications of one employer. |
| TR-JS-14, TR-SYS-08 | Feedback to the other side is shown at once, not after both sides submit or after a timeout. |
| TR-JS-17 | The talent's profile counts (appear, watch, saved) are not shown on any screen, and they are not premium-gated. |
| TR-R-07 | No change history for job edits (only `edited_at`). The match is not computed again when the skills change (`[DISCUSS]`). |
| TR-SYS-03 | No user-level notification settings. No "job closing soon" event. |
| TR-SYS-04 | Reports have no status column and no admin list. No human-review flow. |
| TR-SYS-05 | No in-product notice that activity is tracked. No documented retention period. Events are written synchronously in the request, not async or batched. |
| §5 Responsible AI | No traceable, privacy-safe log of AI inputs and outputs. |
| §5 Performance | No timeout on parsing. |
| §5 Accessibility | Contrast defect D-2 is open. Screen readers were not tested. |
| §5 Testing | The end-to-end browser test needs a running server and Chrome, so it is not in the unit test run. No test that `/admin` needs authentication. |

---

## 5. P2 (roadmap)

| Requirement | Gap |
|---|---|
| TR-R-01 | Company profile and employer verification. |
| TR-R-11 | Employer-initiated contact: the talent has no explicit Accept; the employer moves Contacted to Interview. |
| TR-R-12 | Compare allows 2 to 5 profiles (the spec says 2). It also shows a position (1, 2, 3) for each profile inside each Formula 4 area, which ranks people per area. The spec says "no ranking of the two people". |

---

## 6. Data entities (§1.3) compared with `schema.sql`

| Entity | Status | Difference |
|---|---|---|
| User | Done | Roles are stored as `candidate` and `recruiter`. |
| TalentProfile | Partial | No `visibility_opt_in`. |
| ExperienceItem | Missing | No table. |
| TranslatedSkill | Partial | No `source_item_id`. Confidence is `evidence`; confirmation is `status`. |
| Job | Partial | No `status` column. |
| JobSkill | Done | `must` flag for required or preferred. |
| Application | Done | |
| ApplicationEvent | Partial | No `from_status`, no `actor_id`. |
| InterviewSlot | Partial | `start` only. No `end`, no `status`. |
| Offer | Partial | No table: `offer_text` and `offer_sent_at` on the application. No status, `responded_at` or expiry. |
| Feedback | Done | Different shape: `side`, `to_other`, `to_team`. |
| Bookmark, Skip | Partial | Separate tables for jobs and for talent, not one table with `entity_type`. |
| Report | Partial | No `status`. |
| TrackingEvent | Partial | No `actor_type`, no `metadata`. |
| Notification | Partial | An `email` flag, not a channel. A `read` flag, not `read_at`. No `sent_at`. |
| Entitlement | Partial | The `plans` table has no `valid_until`. |
| SkillMapping | Partial | Rules in code (`BE/translation.py`) and the taxonomy JSON, not a seed table. |

---

## 7. Done

- TR-JS-06 Alias (generator, uniqueness, screening).
- TR-JS-08 Job shortlist with skip, bookmark and report.
- TR-JS-10 Bookmark list.
- TR-JS-11 Apply, review and the frozen snapshot.
- TR-JS-16 Navigation pane (Settings is the user block, not a menu item).
- TR-R-08 Applications view and review.
- TR-R-10 Result, offer and feedback (employer side).
- TR-SYS-07 Charts (no demographic breakdown).
- TR-SYS-09 Role guards and deep links.
- Delete my data, data export, no CV text in logs, text label on the job badge, file type and size checks.
- Tests for the state machine, the anonymised view, the badge and "no personal fields in employer responses".

## 8. Decisions the app made for `[DISCUSS]` items (to confirm)

| Question | Current decision in the app |
|---|---|
| Value of N for the top talent list | 5 |
| Industries in scope | ICT only: Software Engineering, AI & Machine Learning, Data |
| Match wording | Skill coverage per job plus a separate "Fit score" |
| Where rejected applications go | A "Past" tab, labelled "Not selected" |
| When anonymity ends | When the talent picks an interview slot and ticks the consent box |
| Employer and university names | Hidden from employers (certification issuers are shown) |
| Job skills | Both: extracted from the description and edited by the employer |
| Withdraw and offer expiry | Not allowed / not built |
| Re-run the match after a job edit | No; the application keeps its frozen match |


## 9. Enhancement plan (future versions)

The plan puts the gaps into 7 phases. A phase starts when the phase before it is done, except where a line says "can run in parallel". Every phase ends with the tests of that phase passing and the docs updated (`prompt.md`, `DESIGN.md`, `AI_Rule.md`, `jinder_platform/docs/`).

**Size:** S = up to 1 day, M = 2 to 4 days, L = 1 to 2 weeks (for one developer).
**Area:** FE = `jinder_frontend`, BE = `jinder_platform`, ENG = `jinder_backend_engine`.

### Phase 0: Security hardening (before the app runs on a shared computer, a network or in public)

Goal: no personal data can leak through the platform.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| Require an admin role on all `/admin/*` routes, or turn them off outside development. Change `admin.html` to send the token. | §1 | BE, FE | S |
| Add a test: a call to `/admin/*` without a token gets 401; a talent or employer token gets 403. | §1, §4 Testing | BE | S |
| Rate limits on CV upload, job description upload and parse endpoints. | §4 Security | BE | S |

**Done when:** the new tests pass and the full test run ends with `OK`.

### Phase 1: Quick wins (can run in parallel with Phase 0)

Goal: close the small P0 gaps.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| Badge rule: yellow when 7 days or less are left. Update the badge test. | §3 TR-R-06 | BE | S |
| Landing: redirect a signed-in user to Home. Remove "ranked … never a black box" and the "86%" score from the preview. State the "anonymous talent" promise. | §3 TR-SYS-10 | FE | S |
| Basic plan limit of 50 open jobs, with an upgrade prompt on the job form. | §2 #1 | BE, FE | S |
| Job detail: move the actions to the bottom right. Show the evidence and the reason for each skill. | §2 #11, §3 TR-JS-09 | FE | S |
| Employer talent detail: add Skip. Add the report reason "Wrongly recommended". | §3 TR-R-04 | FE, BE | S |
| Employer home: show N = 5 talents, and filter the pool to the employer's open jobs. | §3 TR-R-02 | BE, FE | M |

**Done when:** the browser journeys (`run_tests.py --browser-quick`) pass with the new behaviour.

### Phase 2: Talent trust and privacy

Goal: the talent controls what is shared, and the app records consent.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| `visibility_opt_in` on the profile, a switch in Settings, and the filter in all employer lists. | §2 #3 | BE, FE | M |
| A consent record (what, when, version of the text) before the first CV is processed. | §2 #6 | BE, FE | M |
| Rewrite the privacy page with correct statements. Add the tracking notice and the retention period. | §3 Privacy page, §4 TR-SYS-05 | FE, docs | M |
| Leak check: also remove names (the talent's own name and common name patterns) from shared text. | §3 TR-R-03 | BE | S |
| Show the translation reason of each skill to employers. | §3 TR-R-03 | BE, FE | S |
| A consent timestamp column for "identity shared". | §3 TR-R-03 | BE | S |
| Onboarding: an unsaved-changes warning, and "Add a skill" on the translation step. | §2 #9, #10 | FE | S |

**Decision needed first:** when anonymity ends (`[DISCUSS]`, section 8).

### Phase 3: Hiring workflow

Goal: the full application lifecycle in the spec, with a clear audit trail.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| `application_history`: add `actor_id` and `from_status`. Remove the moves that the spec does not list, or document them. | §3 TR-SYS-01 | BE | M |
| Job status column (Open, Closed), a scheduled auto-close at `close_at`, and no reopen of a closed job. Pending applications stay for the employer. | §2 #2 | BE | M |
| Withdrawn status (talent) and Expired offers (`expires_at`). | §2 #4, #5 | BE, FE | M |
| Interviews: reschedule and cancel (employer), "no slot fits" (talent), and a check for the same time across applications. | §4 TR-JS-13, TR-R-09 | BE, FE | M |
| Feedback is shown to the other side only after both submit, or after a timeout. | §4 TR-SYS-08 | BE, FE | S |
| Job change history, and the rule for re-running the match after a skills change. | §4 TR-R-07 | BE | M |
| Optimistic concurrency on application edits (version or If-Match). | §2 #12 | BE, FE | S |

**Decisions needed first:** withdraw allowed, offer expiry period, feedback timeout, re-run match (`[DISCUSS]`).

### Phase 4: Data model and performance

Goal: the data entities of §1.3, and fast lists with many users.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| `ExperienceItem` table (title, description, source country, source industry). Link translated skills with `source_item_id`. | §2 #14, §6 | BE, ENG | L |
| Versioned profile save. Applications keep their snapshot. | §2 #8 | BE | M |
| Cache the recommendation list and the parse results (by file hash). Clear the cache when the profile or the jobs change. | §2 #13 | BE | M |
| Write tracking events async and in batches. | §4 TR-SYS-05 | BE | S |
| Missing entity fields: InterviewSlot `end`/`status`, an Offer record, Notification `channel`/`read_at`/`sent_at`, Report `status`, Entitlement `valid_until`, TrackingEvent `actor_type`/`metadata`. | §6 | BE | M |

**Done when:** the performance check (`qa_perf.py`) passes with 4 clients (CHANGELOG defect D-3 closed).

### Phase 5: Notifications and Premium

Goal: email first, and a clear difference between the plans.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| Email for the key events (new application, status change, slots offered, slot confirmed), templates per type, and an idempotency key. | §3 TR-SYS-03 | BE | M |
| User-level notification settings, and the "job closing soon" event. | §4 TR-SYS-03 | BE, FE | M |
| Plan screen: Basic and Premium side by side, with every feature and limit. A stronger premium look. | §3 TR-SYS-06 | FE | M |
| Talent profile counts on a screen, gated as a Premium feature. | §4 TR-JS-17 | FE, BE | S |
| Reports: a status column, an admin list, and a human-review flow. | §4 TR-SYS-04 | BE, FE | M |

**Can run in parallel with Phase 4.**

### Phase 6: AI services

Goal: the AI behaviour that the spec assumes, with safe fallbacks.

| Item | Gap ref | Area | Size |
|---|---|---|---|
| An LLM service for CV parsing and skill translation, behind one module. The rule-based code stays as the fallback. Library matches first; mark inferred mappings ("inferring"). Low temperature, cache per item. | §2 #15 | BE, ENG | L |
| Schema validation of the AI output, one retry, then the fallback. Timeouts on every call. | §2 #15, §4 Performance | BE | M |
| Structured roles from the CV (employer, dates, responsibilities) into `ExperienceItem`. | §3 TR-JS-03 | BE | M |
| A privacy-safe log of AI inputs and outputs (no raw CV text), so a wrong mapping can be traced. | §4 Responsible AI | BE | M |
| OCR for scanned PDFs, and virus scanning of uploads. | §4 TR-JS-02, Security | BE | M |

**Depends on:** Phase 4 (`ExperienceItem`). **Rule:** CV text is data, never instructions to the model (AI_Rule Rule 5).

### Phase 7: Production readiness and roadmap (P2)

| Item | Gap ref | Area | Size |
|---|---|---|---|
| HTTPS and encryption at rest (database and uploads), and object storage for CV files. | §2 #7 | BE, ops | L |
| Email verification and password reset. | §4 TR-JS-01 | BE, FE | M |
| Sign-up fields: country of study or work, target role (after the `[DISCUSS]` decision). | §3 TR-JS-01 | FE, BE | S |
| Short linear onboarding with progress saved after each step. | §3 TR-JS-18 | FE, BE | M |
| Accessibility: fix the contrast defects (D-2) and test with a screen reader. | §4 Accessibility | FE | M |
| End-to-end browser test in the automatic test run. | §4 Testing | BE, FE | S |
| Company profile and employer verification. | §5 TR-R-01 | BE, FE | L |
| Compare: decide 2 or up to 5 profiles, and remove the per-area positions. | §5 TR-R-12 | BE, FE | S |
| Employer-initiated contact: an explicit Accept for the talent. | §5 TR-R-11 | BE, FE | S |

### Summary of the plan

| Phase | Theme | Main size |
|---|---|---|
| 0 | Security hardening | S |
| 1 | Quick wins | S to M |
| 2 | Talent trust and privacy | M |
| 3 | Hiring workflow | M |
| 4 | Data model and performance | M to L |
| 5 | Notifications and Premium | M |
| 6 | AI services | L |
| 6 | Production readiness and P2 roadmap | M to L |

Before Phases 2, 3 and 7, the team must confirm the `[DISCUSS]` decisions in section 8.
