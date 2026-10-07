# Skill Bridge: Technical Requirements

Derived from the Skill Bridge User Flow Specification. Futura Remix Hackathon, international round.

**Terminology:** Talent and Employer replace candidate, job seeker, recruiter and HR throughout. Requirement IDs such as TR-JS and TR-R keep their original prefixes for traceability.

## How to read this document

**Priority**
- **P0**: demo-critical, build in the next two to three days.
- **P1**: build if time allows, otherwise mock with seeded data.
- **P2**: roadmap, show on slides only.

**Assumptions** (I do not know the stack deployed in the national round, so adjust anything that conflicts)
- Web application with a REST API and a relational database.
- An LLM API handles CV parsing, skill translation, and reasoning text.
- Object storage holds uploaded CVs. An email service sends notifications.
- Demo data is synthetic or consented, as the PRD requires.

`[DISCUSS]` marks requirements blocked by an open question from the user flow spec.

---

## 1. System overview

### 1.1 Components

| Component | Responsibility |
|---|---|
| Web client | Talent and employer interfaces, left navigation pane, charts |
| API service | Auth, profiles, jobs, applications, lifecycle, entitlements, reports |
| AI service | CV parsing, skill translation, job skill extraction, match reasoning |
| Matching service | Per-skill match between a translated profile and a job |
| Anonymization layer | Produces employer-safe talent views, no personal data leaves it |
| Notification service | Email now, in-app later, triggered by lifecycle events |
| Event tracking | Logs job and profile events, builds aggregates for charts |
| Database | Users, profiles, skills, jobs, applications, events, reports, feedback |
| Object storage | Original CV files, accessible only to the owning talent |

### 1.2 Core design constraints (from the PRD)
- Matching is per skill, with a plain-language reason. No single score on a person.
- The system never auto-accepts or auto-rejects. Every status change on an application is a human action.
- Employers never receive personal identifiers or the original CV.
- Every AI output shows its reasoning: source skill, mapped skill, why.

### 1.3 Key data entities

| Entity | Main fields |
|---|---|
| User | id, role (talent or employer), email, password hash, created_at |
| TalentProfile | user_id, alias, target_role, visibility_opt_in, personal info (private) |
| ExperienceItem | profile_id, original_title, original_description, source_country, source_industry |
| TranslatedSkill | profile_id, source_item_id, original_skill, mapped_skill, reason, confidence_level, user_confirmed |
| Job | id, employer_id, title, description, required_skills, target_applicants, open_at, close_at, status |
| JobSkill | job_id, skill, required or preferred |
| Application | id, job_id, talent_id, status, origin (applied or contacted), submitted_snapshot, timestamps |
| ApplicationEvent | application_id, from_status, to_status, actor_id, timestamp |
| InterviewSlot | application_id, start, end, status (offered, picked, confirmed, declined) |
| Offer | application_id, status (sent, accepted, rejected, expired), sent_at, responded_at |
| Feedback | application_id, from_user_id, to (user or dev team), body, created_at |
| Bookmark | user_id, entity_type (job or talent), entity_id |
| Skip | user_id, entity_type, entity_id |
| Report | reporter_id, entity_type, entity_id, reason, status |
| TrackingEvent | actor_id, actor_type, event_type, entity_type, entity_id, timestamp, metadata |
| Notification | user_id, type, payload, channel, sent_at, read_at |
| Entitlement | user_id, plan (basic or premium), valid_until |
| SkillMapping | source_skill, source_context, target_skill, rationale (seed library) |

---

## 2. Talent requirements

### TR-JS-01: Authentication and sign-up (P0)
Covers: log in or sign up.

- Email and password sign-up and login. Role is chosen at sign-up (talent or employer) and stored on the user.
- Password hashing with a modern algorithm, session via secure token, logout.
- Email verification and password reset. (P1)
- Sign-up collects basic information. `[DISCUSS]` Final field list. Until decided, collect name, email, country of study or work, and target role (optional).
- Talent sign-up lets the user enter an alias, or generates one if left blank (see TR-JS-03).
- The same login screen serves both roles. Routing after login depends on role.

### TR-JS-02: CV upload (P0)
Covers: upload CV.

- Accept PDF and DOCX. Maximum file size 10 MB. Reject other types with a clear message.
- Store the original file in object storage, private to the owner, never exposed to employer endpoints.
- Extract text from the file. Handle non-standard international formats and translated documents (PRD accessibility requirement). For scanned PDFs, use OCR. (P1)
- Show progress while parsing and a clear error with a retry or manual-entry fallback if parsing fails.
- Parsing must finish within about 15 seconds for a typical CV, or show an asynchronous progress state.
- For the demo, use a small set of pre-checked sample CVs to protect against live failures. Cache parse results by file hash.

### TR-JS-03: AI parsing and pre-fill (P0)
Covers: AI pre-fills the information fields.

- Extract from the CV: roles, employers, dates, responsibilities, education, and skills.
- Return structured JSON that matches the profile schema. Validate with a schema check and retry once if invalid.
- Pre-fill the edit form with the parsed values.
- Mark each pre-filled field as AI-detected so the user knows to check it.
- Never invent experience. If a field is not found, leave it empty.
- No personal data should be sent to the LLM beyond what the CV contains, and prompts must not log raw CV text in application logs.

### TR-JS-04: Cross-border and cross-industry skill translation (P0) `[DISCUSS]`
Covers: the core engine, shown at CV upload and in the edit step.

- Input: parsed experience items. Output: for each, a list of translated skills.
- Each translated skill carries: original skill or duty, mapped skill (Australian market equivalent), the reason in plain language, and an evidence confidence level (Limited, Moderate, Strong).
- Two translation types must be supported:
  - Cross-border: overseas job titles and duties mapped to local equivalents.
  - Cross-industry: skills mapped where the underlying competency matches (for example Product Owner to Marketing Executive, Business Analyst to Data Analyst).
- Use a seeded mapping library of 20 to 30 skill pairs for the demo, plus LLM generalization for unseen cases. The LLM must prefer a library match when one exists, and say when it is inferring.
- Output must be deterministic enough to demo: set temperature low and cache results per experience item.
- Must not produce a personality, suitability, or overall quality score. Confidence describes the strength of evidence only.
- `[DISCUSS]` Which two or three industry pairs to demo, and the mapping library content.

### TR-JS-05: Edit profile and confirm translation (P0)
Covers: talent reviews and edits the AI output.

- Editable form for all parsed fields and each translated skill (original, mapped, reason).
- The talent can accept, edit, remove, or add a skill. Track `user_confirmed` per skill.
- Only confirmed or edited skills appear in the employer-facing translated profile.
- Save is explicit and versioned, so the profile snapshot used in an application is fixed at submit time (see TR-JS-11).
- Validation on required fields, and unsaved-changes warning.
- Editing information later is available from settings (see TR-JS-15).

### TR-JS-06: Alias (P0)
- Talent may set an alias at sign-up. Otherwise the system generates one from a list of animal names with a neutral modifier, such as a colour (not personality adjectives such as "indecisive").
- Alias is unique across the platform.
- Custom aliases are screened: reject anything resembling a real name, contact detail, or origin signal. Use a blocklist plus a simple check against the talent's own name.
- Alias is the only identifier employers ever see.

### TR-JS-07: Home page and recommendations (P0)
Covers: recommended jobs based on skill match and target role.

- Endpoint returns a ranked list of open jobs for the talent.
- Ranking inputs: per-skill match (TR-SYS-02) and, if set, target role similarity.
- Exclude closed jobs, skipped jobs, and jobs already applied to.
- Pagination, and a cached recommendation list refreshed when the profile or jobs change.
- A **Your activity** component at the top showing only active items (applications in progress). There are no KPI cards.
- A **What employers see** panel showing the talent's anonymous profile as employers see it, read from the same projection as TR-R-03.
- Links to the bookmark list, application list, and settings.
- Log a `job_appear` event when a job is shown (see TR-SYS-05).
- `[DISCUSS]` The matching and grading formula. Skipped jobs moving to the bottom as low priority is a later feature (P2).

### TR-JS-08: Job shortlist and actions (P0)
Covers: scannable list with skip, bookmark, report.

- Each item shows: job description summary, match summary and skill gaps, open date, and close date.
- **Skip**: stores a Skip record and hides the job. Hidden jobs are excluded from recommendations (P0). Undo is not required.
- **Bookmark**: stores a Bookmark record, appears in the bookmark list.
- **Report**: stores a Report with an optional reason for a wrong recommendation. Reports are stored for later improvement of ranking (P1 for review tooling).
- Actions are idempotent and update the UI without a full page reload.
- Log `job_save` and skip events.

### TR-JS-09: Job detail (P0)
- Full job description and the detailed skill breakdown from the matching service: for each required skill, status (match, partial, gap), the talent evidence, and the reason.
- An aggregate match percentage may be shown as a summary of required-skill coverage, never as a score on the person. `[DISCUSS]` Final wording and formula.
- Similar jobs list (P1): based on shared required skills or title similarity.
- Actions: apply, skip, bookmark, report, placed at the bottom right of the page.
- Log `job_watch` when the page is opened.

### TR-JS-10: Bookmark list (P0)
- List of bookmarked jobs with the same card layout as the shortlist.
- Clicking opens the job detail page.
- Remove bookmark supported.

### TR-JS-11: Apply and review (P0)
Covers: review step, submit, success screen.

- Review screen renders exactly the payload that will be sent: the translated profile only. The original CV and personal identifiers are excluded.
- On submit, create an Application with status Applied and a frozen snapshot of the translated profile (`submitted_snapshot`).
- Prevent duplicate applications to the same job.
- Reject applications to closed jobs.
- Success screen links to the status tracking view.
- Triggers: notification to the employer, `job_apply` event.

### TR-JS-12: Application list and status tracking (P0)
- Application list shows each applied job with a status ribbon in the top right corner.
- Status values follow the state machine in TR-SYS-01.
- Status tracking view shows status history from ApplicationEvent, the submitted application, and the next action required.
- The same tracking view is reachable from the success screen and the application list.
- **Edit window**: the talent may edit the application until status moves to Review. After that, edits are rejected by the server with a clear message. Use optimistic concurrency so a status change during editing is detected.
- **Cancel**: `[DISCUSS]` Whether to allow withdrawal. If allowed, add a Withdrawn status and notify the employer.
- `[DISCUSS]` Where rejected applications appear (for example a "past jobs" view). Until decided, show them in the application list with a Rejected status.

### TR-JS-13: Interview scheduling, talent side (P1)
- Talent sees offered time slots and picks one. The server marks the slot picked, then confirmed when the employer confirms (or confirmed immediately, to be decided).
- Prevent double booking of the same slot.
- Notification to the employer when a slot is picked.
- `[DISCUSS]` No slot fits: allow a decline with a reschedule request.
- Store times in UTC and display in the user's time zone.

### TR-JS-14: Result, offer, and feedback, talent side (P1)
- Talent is notified of the result by email.
- If accepted, an Offer appears. The talent accepts or rejects. A rejected offer sets the application to Rejected.
- `[DISCUSS]` Offer expiry: add `expires_at` and an automatic Expired state if decided.
- Feedback form at the final stage, with two targets: the employer (exchanged) and the development team (collected).
- Feedback to the employer is delivered only after both sides have submitted, or after a timeout. `[DISCUSS]`

### TR-JS-15: Settings and information edit (P0)
- Edit personal information, alias (subject to uniqueness and screening), target role, and the profile fields.
- Changes to translated skills create a new profile version. Existing applications keep their frozen snapshot.
- Delete account and personal data (P1). Deleting removes the CV file and personal fields, and anonymizes events.

### TR-JS-16: Navigation pane (P0)
- Persistent left navigation pane with sections: home, bookmarks, applications, settings, and notifications.
- Can be collapsed and expanded. The state persists across sessions and pages.
- Keyboard accessible, with proper labels for screen readers.

### TR-JS-17: Talent profile statistics, premium (P1)
- This is a **premium** feature, checked by TR-SYS-06. A talent sees their own apply and respond events.
- Talent sees profile appear, profile watch, and profile saved counts, so they can judge profile strength.
- Counts are aggregates. They do not reveal which employer viewed the profile.

---

## 3. Employer requirements

### TR-R-01: Account (P0)
- Same login and sign-up as the talent, role set to employer.
- Collects employer information only. No CV upload.
- Company profile and verification so talents can trust postings. (P2)

### TR-R-02: Employer home page (P0)
- Top N talent shortlist for the employer, drawn from talents who opted in to visibility and match the employer's open jobs. `[DISCUSS]` The value of N.
- Basic charts: jobs open, jobs that reached their target, talents awaiting response (see TR-SYS-07).
- Basic tier shows the top N only. Premium shows the full list (TR-SYS-06).

### TR-R-03: Anonymized talent view (P0)
Covers: masking of personal information.

- All employer-facing talent endpoints go through the anonymization layer. Do not rely on the client to hide fields.
- Hidden: name, origin, ethnicity, nationality, gender, contact details, photo, age or date of birth, and the original CV.
- Shown: alias, translated role title, translated skills with reasons, per-skill match against the employer's job.
- `[DISCUSS]` Whether to also hide employer and university names, since they can reveal origin.
- The translated profile text is checked for leaked identifiers (names, emails, phone numbers) before display. Use pattern checks and strip matches.
- Add an automated test that asserts no personal field appears in any employer API response.
- `[DISCUSS]` When anonymity ends. If unmasking happens at interview confirmation, record the talent's consent and the unmask timestamp.

### TR-R-04: Talent detail and actions (P0)
- Shows the translated profile and per-skill match against a selected job.
- Actions: bookmark (save talent), report (wrongly recommended talent), skip (hide the talent).
- Same implementation pattern as the talent side actions, with entity type talent.
- Log `profile_watch`, `profile_saved`, and skip events.
- The match view must not show a single score on the person. It shows per-skill results with reasons.

### TR-R-05: Post a job (P0)
- Form fields: title, description, target number of applicants, close date, and optional required skills.
- Job skill extraction: AI reads the description and proposes required and preferred skills, which the employer can edit. `[DISCUSS]` AI-extracted, employer-tagged, or both.
- Validation: close date in the future, target a positive integer.
- **Post from PDF:** the employer can upload a PDF job description (type and size checks, as for CVs). The text is extracted by reusing the CV extraction code, and the AI fills in the title, description and required skills. The employer reviews and edits before posting. If extraction fails, the employer fills the form manually.
- **Open job limit:** the basic plan allows up to 50 jobs with status Open at a time. Posting another is blocked with an upgrade prompt. Closed jobs do not count. Premium has no limit (assumed).
- Job status is Open on publish.

### TR-R-06: My jobs list (P0)
- Lists the employer's jobs with target against current applicant count (for example target 100, current 200).
- Close-date badge calculated server-side from `close_at`:
  - Green: open and more than 7 days to close.
  - Yellow: open and 7 days or less to close.
  - Red: closed or overdue.
- Clicking a job opens its applications.
- Jobs auto-close at `close_at` through a scheduled job. `[DISCUSS]` Pending applications at close must be kept for the employer to decide, with no automatic rejection.

### TR-R-07: Edit a job (P1)
- Employer can edit the description, skills, target, and close date.
- Any edit sends a notification to everyone who has applied.
- Keep a change history with timestamps.
- `[DISCUSS]` Whether a major change, such as the required skills, re-runs the match for existing applicants. If yes, mark applicants' match as recomputed and keep the previous result.

### TR-R-08: Applications view and review (P0)
- Lists the applications for a job with the talent alias, match summary, and current status.
- Opening an application shows the frozen translated profile snapshot and per-skill match.
- Employer moves the status. Moving from Applied to Review locks the talent's edit window.
- Every status change writes an ApplicationEvent and sends a notification to the talent.
- No automatic status change is ever made by the system.

### TR-R-09: Interview scheduling, employer side (P1)
- Employer offers one or more time slots for an application.
- Employer sees the slot the talent picked and confirms.
- Reschedule and cancel supported. `[DISCUSS]` No slot fits.
- Notifications on slot offered, picked, and changed.

### TR-R-10: Result, offer, and feedback, employer side (P1)
- Employer sets the result to Accepted or Rejected after the interview.
- If accepted, the employer sends an offer. The talent's reply updates the status.
- Feedback form at the final stage, with the same two targets as the talent side.

### TR-R-11: Employer-initiated contact, premium (P2)
- Premium employers contact a talent found in the recommendation panel.
- Creates an Application with origin `contacted` and status Contacted. The talent can accept or decline. `[DISCUSS]`
- On accept, the application moves directly to Interview, skipping Applied and Review.
- Talents control whether they appear in recommendations (`visibility_opt_in`).
- Contact goes through the platform. Contact details stay hidden.

### TR-R-12: Compare two profiles, premium (P2)
- Side-by-side view of two translated profiles against the same job.
- Per-skill comparison only. No combined score and no ranking of the two people.

---

## 4. Cross-cutting system requirements

### TR-SYS-01: Application status state machine (P0)

| From | Allowed next |
|---|---|
| Applied | Review, Withdrawn `[DISCUSS]` |
| Review | Interview, Rejected |
| Interview | Accepted, Rejected |
| Accepted | Offer |
| Offer | Confirmed, Rejected (offer rejected), Expired `[DISCUSS]` |
| Contacted (premium) | Interview, Declined |
| Confirmed, Rejected | Feedback is open; no further status changes |

- Transitions are enforced on the server. Invalid transitions return an error.
- Each transition records the actor and timestamp in ApplicationEvent.
- Only the employer moves an application forward, except the talent's offer reply, withdrawal, and slot pick.
- Job status: Open to Closed only.

### TR-SYS-02: Matching service (P0) `[DISCUSS]`
- Input: a translated talent profile and a job's required skills.
- Output per required skill: status (match, partial, gap), the talent's evidence, and a plain-language reason.
- Output summary: the number of required skills covered and the list of gaps. A percentage may be derived as covered divided by required, as a placeholder until the formula is decided.
- No weighting by anything other than skills. No use of alias, country, or any protected attribute.
- Deterministic for the same input, and fast enough to rank a talent's recommendations (target under 2 seconds for a page of results, using caching).
- The formula is a separate module so it can be replaced without changing the API.

### TR-SYS-03: Notification service (P0 for the key events, P1 for the rest)
- Events trigger notifications through an outbox table, so a failed email does not block the main action.
- Email channel first. In-app notifications later. `[DISCUSS]`
- Key events (demo scope): new application (to employer), status change (to talent), interview slots offered, slot confirmed.
- Other events: result, offer, job edited (to applicants), job closing soon, feedback received.
- Templates per type, idempotent sends, retry with backoff, and user-level notification settings. (P1)

### TR-SYS-04: Report handling (P1)
- Reports from both sides share one table and one API.
- Minimum viable: store reports and show an admin list. Used later to evaluate and improve ranking.

### TR-SYS-05: User tracking system (P1)
- Log these events: `job_appear`, `job_watch`, `job_save`, `job_apply`, `job_respond`, `profile_appear`, `profile_watch`, `profile_saved`, plus skip events for jobs and profiles.
- Log asynchronously, batched, and never block the user action.
- Visibility (a premium feature, gated by TR-SYS-06):
  - Employer sees job event counts for their own jobs. `[DISCUSS]` Aggregate counts, not per-talent detail, to protect anonymity.
  - Talent sees their own apply and respond events and their profile counts.
  - Skip counts are internal only, used to improve recommendations.
- Show an in-product notice that activity is tracked. `[DISCUSS]`
- Retention period defined and documented.

### TR-SYS-06: Entitlements and premium gating (P0 as a mock)
- An Entitlement record per user with plan basic or premium.
- A single server-side check decides: top N versus full talent list, direct contact, compare two profiles, and premium charts.
- For the demo, premium is a toggle with an upgrade prompt. No real payments.
- The same check enforces the basic limit of 50 open jobs per employer.
- **Plan selection screen:** shows Basic and Premium side by side and lists exactly which features each plan includes (open job limit, top N versus full list, direct contact, compare two profiles, statistics, advanced charts). The premium account has a distinct, elegant look that makes the difference visible (design in the UX step).
- Real billing integration is P2.

### TR-SYS-07: Charts and statistics (P1)
- Aggregation endpoints return chart-ready data.
- Basic charts (employer): open jobs, jobs that reached their target, talents awaiting response.
- The talent home page has no KPI cards. Active applications appear in the Your activity component (TR-JS-07).
- Premium charts (P2): see the ideas in the user flow spec section 6.2.
- Charts show skills and process only. No breakdown by nationality, gender, or ethnicity, even in aggregate.
- For the demo, run charts on seeded data.

### TR-SYS-08: Feedback collection (P1)
- Two targets: the other party and the development team.
- Feedback to the other party is exchanged when both have submitted (or after a timeout). `[DISCUSS]`
- Feedback to the development team is stored with a link to the anonymized application and is visible only to the team.

### TR-SYS-09: Left navigation and routing (P0)
- Role-based route guards. Talents cannot reach employer pages and the other way around.
- Deep links to job detail, application tracking, and talent detail are supported.

### TR-SYS-10: Landing page (P0)
- Public page for visitors who are not logged in, served at the site root. A logged-in user is redirected to their home page.
- The top section highlights the Australian market, with icons, and does not use "black-box score" wording.
- Two entry points (talent and employer) lead to sign-up with the role preselected, plus a login link.
- States the product's promises: explained recommendations, anonymous talent, employers decide.
- Responsive, WCAG 2.1 AA, and fast to load.
- `[DISCUSS]` One page or two, a "how it works" example, and a premium pricing mention.

### TR-SYS-11: Demo accounts and seed data (P0)
- An idempotent seed script creates a demo talent (Minh persona) with a sample CV and translated profile, a demo employer (Sarah persona) with the seeded jobs, 8 to 10 more anonymous talent profiles, and applications at different statuses.
- A basic and a premium employer demo account both exist, to show the limits and the plan screen.
- The script can reset the demo to its starting state. All data is synthetic, and demo logins live in the seed file only.

### TR-JS-18: Linear onboarding (P0)
- One linear flow for new talent: upload CV, review and edit what the AI filled in (including the translated skills), done.
- Editing answers is part of the review step, not a separate flow. Returning users edit from settings.
- Progress is saved between steps, and the user can go back without losing data.
- `[DISCUSS]` Exact steps. This replaces the current confusing onboarding (update CV and Edit Answers).

---

## 5. Non-functional requirements

### Privacy and data protection
- Role-based access control on every endpoint, checked on the server.
- CVs and personal fields are accessible only to the owning talent and system processes.
- Encrypt data in transit and at rest.
- Consent recorded before processing CV data. Delete my data supported (P1).
- Check the platform against applicable privacy law (for example Australia's Privacy Act) before any real data is used. Demo data stays synthetic or consented.
- Do not write CV text, prompts, or personal data to application logs.

### Responsible AI
- Every translated skill and every match shows its reasoning.
- No auto-accept or auto-reject. No overall talent score, personality, or cultural-fit output.
- Evidence confidence describes evidence strength only.
- Log AI inputs and outputs in a privacy-safe way so a wrong mapping can be traced and challenged.
- Human review of reports about wrong recommendations.

### Performance and reliability
- Page loads under 3 seconds on a typical connection for list pages.
- LLM calls have timeouts, retries, and a fallback to manual entry.
- Cache LLM results for the demo path and keep a recorded backup demo.

### Accessibility and inclusion
- CV parsing tolerates non-standard formats and translated documents.
- UI supports keyboard navigation and screen readers. Avoid relying on colour alone (the job badge also needs a text label).
- Plain-language wording throughout.

### Security
- Input validation, file type and size checks, and virus scanning on uploads. (P1)
- Rate limiting on login, upload, and AI endpoints.
- Protect against injection through CV text: treat CV content as data, never as instructions to the model.

### Testing
- Unit tests for the state machine, anonymization layer, and badge logic.
- Test that employer responses contain no personal fields.
- End-to-end test of the demo path with the seeded CVs and jobs.

---

## 6. Suggested build order for the next two to three days

1. **Day 1:** auth and roles, CV upload, AI parsing and translation with the seeded mapping library, edit profile with translated skills.
2. **Day 2:** job posting with skill extraction, matching service with per-skill output, job shortlist and detail, apply and review, anonymized employer talent view, employer status updates.
3. **Day 3:** polish the demo path, seed data, notifications for the key events, premium toggle, backup recording.

Mock or show on slides: interview scheduling beyond a simple version, offer and feedback, tracking system, charts beyond a few seeded ones, billing, and employer-initiated contact.

---

## 7. Open technical decisions

1. Cross-border and cross-industry translation approach, the mapping library, and the demo industry pairs.
2. Matching formula and how the summary percentage is worded.
3. How a job's required skills are produced (AI, employer, or both).
4. When anonymity ends, and how consent is recorded.
5. Whether employer and university names are hidden from employers.
6. Value of N for the top talent list.
7. Whether talents can withdraw, and whether offers expire.
8. Email only, or also in-app notifications.
9. Aggregate versus per-talent job events for employers.
10. Hosting, framework, and database. This document assumes a standard web stack, so confirm what the national round MVP uses.
11. Exact onboarding steps.
12. Landing page content choices (one page or two, a "how it works" example, premium pricing mention).
