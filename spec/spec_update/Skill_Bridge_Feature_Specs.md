# Skill Bridge: Feature Specifications

**Created:** 2026-10-06
**Status:** In Specification (drafts for review)
**Rally:** Not created yet (working titles, no Rally IDs)
**Terminology:** Talent and Employer replace candidate, job seeker, recruiter and HR.

## How to read this document

- Each spec contains only what the team confirmed in the user flow discussion.
- Anything still in discussion is listed under **Backlog (in discussion)** at the end of its feature, and consolidated in section 9.
- **Success Metrics** and **UX Prototype & Design** are deferred for all features, by the team's choice.
- Acceptance Criteria are **starter drafts**. They need the team's review and edits before they count as final.
- Owners and dates in the dependency tables are TBD, with relative timing for the next 2 to 3 days.
- The stack in each Architecture section is an assumption: web client, REST API, relational database, role-based auth, and an LLM API. Confirm what the national round MVP uses.

## Progress overview

| # | Feature | Context | AC | In/Out of Scope | Dependencies | Architecture | Success Metrics | UX |
|---|---|---|---|---|---|---|---|---|
| 1 | Secure Onboarding and Role-Based Access | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 2 | Explainable Cross-Border Skill Translation | Approved | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 3 | Personalised Job Matching and Discovery | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 4 | Transparent Applications and Status Tracking | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 5 | Anonymous Talent Discovery for Employers | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 6 | Streamlined Job Posting and Hiring Pipeline | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |
| 7 | Timely Alerts, Insights and Premium Access | Draft | Draft | Draft | Draft | Draft | Skipped | Skipped |

**Status labels used in the flow**
- Job: Open, Closed.
- Application: Applied, Review, Interview, Accepted or Rejected, Offer, Confirmed.
- Employer-initiated (premium): Contacted, then Interview.

---

# Feature 1: Secure Onboarding and Role-Based Access

## Feature Context

### Problem Statement
Skill Bridge has two very different users, talents and employers, who need one safe way into the platform. Every other feature depends on knowing who the user is and what they are allowed to see. Without role-based access, the anonymity and privacy promises of the product cannot be enforced.

### Overview and Context
- **Why:** This is the foundation. Anonymous employer views, private CVs and per-role pages all rely on it.
- **Who:** Talents (international students and skilled migrants) and employers at Australian SMEs.
- **What:** One login and sign-up for both roles. Talents provide basic information and continue to CV upload. Employers provide their information only, with no CV upload. Talents choose an alias or get an animal-based name. Users get a fixed, hideable left navigation pane and an information edit menu in settings.

### Benefits
- Users reach the right experience immediately after login.
- Talent data stays private, which supports the responsible AI promise.
- A single entry point keeps the build small for a 2 to 3 day sprint.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Sign up:** Given a new visitor, when they sign up and choose talent or employer and provide basic information, then an account is created with that role.
- [ ] **AC2 Login:** Given a registered user, when they log in with valid credentials, then they land on the home page for their role.
- [ ] **AC3 One entry point:** Talents and employers use the same login and sign-up screens.
- [ ] **AC4 Employer sign-up:** Employers provide their information only. There is no CV upload step.
- [ ] **AC5 Talent sign-up:** After sign-up, a talent continues to CV upload (Feature 2).
- [ ] **AC6 Alias:** A talent can enter an alias at sign-up. If they do not, the system assigns an animal-based name. Every alias is unique.
- [ ] **AC7 Role guards:** A talent cannot open employer pages or call employer endpoints, and an employer cannot do the reverse. This is enforced on the server.
- [ ] **AC8 Navigation pane:** A pane on the left stays in place, can be hidden and shown, and gives direct access to the main sections for the user's role. Its open or hidden state persists.
- [ ] **AC9 Settings:** The user can edit their information from the settings menu.
- [ ] **AC10 Logout:** The user can log out, and the session ends.

### Edge cases and errors
- [ ] **AC11:** An email already in use is rejected with a clear message.
- [ ] **AC12:** Invalid credentials show a generic error that does not reveal which field was wrong.
- [ ] **AC13:** A chosen alias that is already taken suggests an available alternative.
- [ ] **AC14:** An expired session redirects to login and returns the user to the page they were on.

### Landing page and demo data
- [ ] **AC15 Landing page:** Given a visitor who is not logged in, when they open the site, then a landing page highlights the Australian market with icons and explains the product, with no "black-box score" wording in the top section.
- [ ] **AC16 Entry points:** The landing page has one entry point for talent and one for employers, each leading to sign-up with the role preselected, plus a login link. A logged-in user goes straight to their home page.
- [ ] **AC17 Demo accounts:** A seed script creates a demo talent, a demo employer on a basic plan and one on a premium plan, extra anonymous talent profiles, and applications at different statuses. It can reset the demo without duplicates. All data is synthetic.

### Non-functional
- [ ] **Security:** Passwords are hashed with a modern algorithm, sessions use secure tokens, and login attempts are rate limited.
- [ ] **Usability:** The navigation pane is keyboard accessible and readable by screen readers (WCAG 2.1 AA).
- [ ] **Reliability:** Role checks run on every protected request, with no reliance on the client.

## 3. In-Scope
- [ ] Sign-up and login for both roles on shared screens
- [ ] Role assignment and role-based routing after login
- [ ] Alias entry at sign-up, or an assigned animal-based name
- [ ] Left navigation pane, fixed and hideable
- [ ] Settings with an information edit menu
- [ ] Logout and session handling
- [ ] Landing page with entry points for talent and employers
- [ ] Demo accounts and seeded data

## 4. Out of Scope
- Company profile and verification (not discussed yet)
- Social or single sign-on login
- Payments and plans (Feature 7)
- CV upload and parsing (Feature 2)
- An admin console

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Database and hosting setup | System | Yes | TBD | Day 1 |
| User and profile data model | Team | Yes | TBD | Day 1 |
| All other features depend on this one | Feature (downstream) | Blocks all | TBD | Day 1 |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** email and password authentication, role stored on the user, session tokens, and role-based access control applied as server middleware.
- **Key components:** auth service, role guard middleware, alias generator, settings endpoints, navigation configuration by role.
- **Integration points:** the user table shared by all features, and the profile data used by Feature 2.

## Backlog (in discussion)
- The final list of sign-up fields.
- Email verification and password reset.
- Delete my data and account deletion.
- Alias rules: wording of assigned names (neutral words rather than personality adjectives) and screening of custom aliases against real names or origin signals.
- Company profile and verification for employers.
- The final navigation items for each role.
- Landing page choices: one page or two, a "how it works" example with a translation, and whether to mention premium pricing.

---

# Feature 2: Explainable Cross-Border Skill Translation

## Feature Context (approved)

### Problem Statement
Australian employers can't recognise skills that arrive in an unfamiliar format, such as a foreign job title, a different industry's vocabulary, or a CV structure local screening tools can't read. 69% of Australian employers report difficulty finding skilled talent (ManpowerGroup, 2024), while 680,582 international students are in Australia (Dept. of Education, 2026). Employers name "identifying transferable skills" and "evaluating international experience" as explicit barriers, so qualified talents are rejected silently with no explanation.

### Overview and Context
- **Why:** The shortage is a translation gap, not a talent gap. This feature is the core engine of Skill Bridge, and every other feature depends on its output.
- **Who:** Primary users are international students and skilled migrants who build their profile. Secondary users are employers, who later read the same confirmed output.
- **What:** The talent uploads a CV, and the AI parses it and pre-fills the profile fields. The talent reviews and edits, and sees their translated profile at this step. The translation design is still in discussion (see backlog).

### Benefits
- Talents see their real capability in local terms and stay in control of what employers see.
- Employers get skills they can verify, not a black-box score.
- Delivers the PRD's two required live demos and the explainability criterion once the translation design is settled.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Upload:** Given a signed-in talent, when they upload a PDF or DOCX CV (proposed limit 10 MB), then the file is stored privately and parsing starts.
- [ ] **AC2 AI pre-fill:** Given a parsed CV, then the AI fills in the information fields, and each pre-filled field is marked "AI-detected".
- [ ] **AC3 Edit:** The talent can edit, add or remove any pre-filled field before saving.
- [ ] **AC4 Translated profile:** After upload and information input, the talent sees their translated profile at this step. Only the translated profile is ever shared with employers, never the original CV.
- [ ] **AC5 Settings:** The talent can edit their information later from the settings menu.
- [ ] **AC6 No invention:** If information is missing from the CV, the field stays empty and flagged.
- [ ] **AC7 No scoring:** The output contains no personality, suitability or overall quality score, and nothing is decided automatically.

### Edge cases and errors
- [ ] **AC8 Bad files:** An unsupported file type or a file over the size limit is rejected with a clear message.
- [ ] **AC9 Parse failure:** If parsing fails or the AI output is invalid, the talent sees an error and can retry or enter details manually, with no data lost.

### Onboarding and profile view
- [ ] **AC10 Linear onboarding:** New talent go through one linear flow: upload CV, review and edit what the AI filled in, done. Editing answers is part of the review step, not a separate flow.
- [ ] **AC11 What employers see:** The talent home page shows a "What employers see" panel with the anonymous profile as employers see it, and invites the talent to complete the profile if it is empty.

### Non-functional (proposed defaults)
- [ ] **Security:** The CV is private to its owner and never returned by any employer endpoint. CV text is not written to logs, and CV content is treated as data, never as instructions to the model.
- [ ] **Performance:** A typical CV is parsed within about 15 seconds, or a progress state is shown.
- [ ] **Usability:** Keyboard navigable and readable by screen readers (WCAG 2.1 AA).

## 3. In-Scope
- [ ] CV upload (PDF and DOCX) with private storage
- [ ] AI parsing and form pre-fill with "AI-detected" markers
- [ ] Talent editing of all pre-filled fields
- [ ] Translated profile shown at the upload and information input step (content to be defined)
- [ ] Manual-entry fallback when parsing fails
- [ ] Editing the information later from settings
- [ ] One linear onboarding flow (upload CV, review and edit, done)
- [ ] A "What employers see" panel on the talent home page

## 4. Out of Scope
- Formal credential verification and visa checking (excluded in the PRD)
- Matching skills to jobs (Feature 3)
- Alias, anonymization and the employer-facing view (Features 1 and 5)
- Behavioural skill evidence and the pre-interview survey (post-hackathon Beta)
- Data-driven transferable skill detection and co-occurrence learning (roadmap)
- Any automatic hire or reject decision

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Accounts and roles (Feature 1) | Feature | Yes | TBD | Day 1 |
| LLM API access for parsing | System | Yes | TBD | Day 1 |
| Private object storage for CVs | System | Yes | TBD | Day 1 |
| Profile data model | Team | Yes | TBD | Day 1 |
| Synthetic or consented sample CVs | Team content | Yes (for the demo) | TBD | Day 1 to 2 |
| Decision on the translation design | Team decision | Blocks the translated profile content only | Team | Discussion tomorrow |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** web client, REST API, relational database, role-based auth, LLM API for parsing.
- **Key components:** upload service (type and size checks, private storage), text extraction (PDF and DOCX), parsing service (structured output validated against a schema, one retry), profile service (stores fields and flags AI-detected values), and a placeholder for the translation service.
- **Integration points:** LLM API, object storage, and the profile data read by Features 3 and 5 (translated profile only).

## Backlog (in discussion)
- Cross-border and cross-industry translation design: how it works, where it shows in the talent and employer views, the two or three demo industry pairs, and the seeded mapping library (20 to 30 pairs).
- Translated skill format: original skill, mapped skill, plain-language reason, and evidence confidence (Limited, Moderate, Strong).
- Library-based versus AI-inferred labelling of mappings.
- Talent accept, edit and remove per translated skill, and which skills reach employers.
- Profile versioning, with submitted applications keeping a snapshot.
- Exact onboarding steps (the current update CV and Edit Answers flow is confusing).
- Later options: OCR for scanned CVs and result caching.

---

# Feature 3: Personalised Job Matching and Discovery

## Feature Context

### Problem Statement
Talents apply blindly and get silent rejections, with no idea which jobs fit them or which skills they are missing. Minh, the talent persona, has no sense of which gaps to close first. Without a clear match, qualified international talents don't find roles where their translated skills count.

### Overview and Context
- **Why:** Matching turns the translated profile into action: which jobs to look at and what is missing.
- **Who:** Talents.
- **What:** The home page recommends open jobs based on skill matching and, if the talent has a target role, by that role. A scannable shortlist and a job detail page show the skill gaps and match. Talents can skip, bookmark and report jobs, and see similar jobs.

### Benefits
- Talents see where they fit and what to close, which addresses the "no explanation" frustration.
- The skip and report actions feed the recommendation improvements later.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Recommendations:** Given a talent with a profile, the home page lists open jobs based on skill match and, if a target role is set, by that role.
- [ ] **AC2 Exclusions:** Closed, skipped and already applied jobs are not shown in the recommendations.
- [ ] **AC3 Shortlist item:** Each job shows the job description, the skill gap or percentage match, and the open and close dates, so the talent can scan quickly.
- [ ] **AC4 Skip:** Skip hides the job from the list, on the shortlist and on the detail page.
- [ ] **AC5 Bookmark:** Bookmark saves the job to the bookmark list, on the shortlist and on the detail page. A bookmark can be removed.
- [ ] **AC6 Report:** Report records a wrong recommendation (for example a sushi chef job for someone seeking data analyst roles), on the shortlist and on the detail page.
- [ ] **AC7 Job detail:** The detail page shows the full job description, the detailed skill match breakdown with the percentage, and which skills are gaps.
- [ ] **AC8 Similar jobs:** The detail page suggests similar jobs.
- [ ] **AC9 Detail actions:** The detail page offers apply, skip, bookmark and report, placed at the bottom right of the page.
- [ ] **AC10 Bookmark list:** The bookmark list shows saved jobs as a shortlist. Clicking one opens the same job detail page as from the recommendations.
- [ ] **AC11 Fair matching:** Matching uses skills only. It never uses the alias, origin or any protected attribute.

### Edge cases and errors
- [ ] **AC12:** A talent without a profile is prompted to complete it, with no empty page.
- [ ] **AC13:** No matching jobs, or every job skipped, shows a helpful empty state.
- [ ] **AC14:** If a job closes while the talent is viewing it, apply is disabled with a clear message.

### Non-functional (proposed defaults)
- [ ] **Performance:** List pages load within about 3 seconds, using cached recommendations.
- [ ] **Usability:** Percentages are shown with text, not only colour (WCAG 2.1 AA).
- [ ] **Reliability:** Skip, bookmark and report actions are repeatable without creating duplicates.

## 3. In-Scope
- [ ] Recommended jobs on the talent home page
- [ ] Job shortlist with description, skill gap or percentage match, and open and close dates
- [ ] Skip (hide), bookmark and report actions
- [ ] Job detail page with a skill match breakdown and skill gaps
- [ ] Similar jobs on the detail page
- [ ] Bookmark list

## 4. Out of Scope
- Moving skipped jobs to the bottom of the list as low priority (a later feature)
- The apply flow and status tracking (Feature 4)
- Posting and managing jobs (Feature 6)
- Learning from outcomes and co-occurrence (roadmap)

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Confirmed translated profile (Feature 2) | Feature | Yes | TBD | Day 1 to 2 |
| Jobs with required skills (Feature 6, or seeded jobs) | Feature or data | Yes | TBD | Day 1 to 2 |
| Matching formula decision | Team decision | Blocks the match values | Team | Discussion tomorrow |
| Accounts and roles (Feature 1) | Feature | Yes | TBD | Day 1 |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** a recommendation endpoint backed by a matching service, with cached results refreshed when the profile or jobs change.
- **Key components:** matching service as a replaceable module, recommendation endpoint with pagination, skip, bookmark and report endpoints, similar jobs endpoint.
- **Integration points:** profile data (Feature 2), job data (Feature 6), tracking events for appear, watch and save (Feature 7).

## Backlog (in discussion)
- The matching and grading formula, and whether the percentage is per skill or an aggregate (the PRD calls for per-skill matching and no single score on the person).
- How a job's required skills are produced (AI-extracted or employer-tagged).
- Moving skipped jobs to the bottom as low priority.
- How "similar jobs" is calculated.
- Review tooling for reports about wrong recommendations.
- Where the target role is set (it depends on the sign-up fields).

---

# Feature 4: Transparent Applications and Status Tracking

## Feature Context

### Problem Statement
Talents like Minh face silent rejection with no explanation, and they cannot see where an application stands. Without visibility and control, applying feels like a black box, and mistakes in their profile go unseen until it is too late.

### Overview and Context
- **Why:** Transparency is a core value of Skill Bridge, and it must hold on the talent's side of the hiring process too.
- **Who:** Talents, with employers driving the status changes.
- **What:** A review step before applying, a success screen that links to tracking, an application list with a status ribbon, a tracking view, an edit window until the employer starts reviewing, and the talent side of the interview, offer and feedback stages.

### Benefits
- Talents always know where each application stands.
- They can catch mistakes before the employer reviews.
- The final feedback stage helps improve the product.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Review before submit:** Applying opens a review step that shows exactly what will be sent: the translated profile only, never the original CV.
- [ ] **AC2 Submit:** Submitting creates an application with status Applied and shows a success screen.
- [ ] **AC3 Success screen:** The success screen prompts the talent to track the status and links to the tracking view.
- [ ] **AC4 Application list:** The application list shows each applied job as a shortlist with its current status as a ribbon in the top right corner.
- [ ] **AC5 Tracking view:** Clicking an applied job opens the tracking view, the same view the success screen links to. It shows the status and the submitted application.
- [ ] **AC6 Edit window:** The talent can edit the application until the employer moves it to Review. After that the server rejects edits with a clear message.
- [ ] **AC7 Status values:** Status follows Applied, Review, Interview, Accepted or Rejected, Offer, Confirmed. Only valid transitions are allowed.
- [ ] **AC8 Interview:** When the employer offers time slots, the talent sees them, picks one and confirms.
- [ ] **AC9 Result:** The talent is notified of the result.
- [ ] **AC10 Offer:** If accepted, the talent sees the offer and accepts or rejects it. A rejected offer ends the application in Rejected.
- [ ] **AC11 Feedback:** After the talent accepts or rejects the offer, or is rejected, a feedback form opens for the employer and for the development team.

### Edge cases and errors
- [ ] **AC12:** Applying twice to the same job is prevented.
- [ ] **AC13:** Applying to a closed job is blocked with a clear message.
- [ ] **AC14:** If the status changes while the talent is editing, the edit is not saved and the talent is told why.
- [ ] **AC15:** If a picked slot is no longer available, the talent is asked to choose another.
- [ ] **AC16 Your activity:** The talent home page shows a "Your activity" component at the top with only active items, and has no KPI cards.

### Non-functional (proposed defaults)
- [ ] **Security:** A talent can only see and edit their own applications.
- [ ] **Reliability:** The application keeps a frozen copy of the translated profile as submitted.
- [ ] **Usability:** Status is shown in text as well as in the ribbon (WCAG 2.1 AA).

## 3. In-Scope
- [ ] Review step and submit
- [ ] Success screen linking to tracking
- [ ] Application list with a status ribbon
- [ ] Tracking view with the submitted application
- [ ] Edit window until the employer moves the application to Review
- [ ] Talent side of interview slot picking, result, offer reply and feedback
- [ ] A "Your activity" component at the top of the talent home page showing only active items

## 4. Out of Scope
- Employer-side status updates and scheduling (Feature 6)
- Notification delivery (Feature 7)
- Employer-initiated contact (premium, Feature 7)
- Messaging between talent and employer

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Job detail with an apply action (Feature 3) | Feature | Yes | TBD | Day 2 |
| Confirmed translated profile (Feature 2) | Feature | Yes | TBD | Day 1 to 2 |
| Employer status updates and slots (Feature 6) | Feature | Yes, for statuses beyond Applied | TBD | Day 2 |
| Notifications (Feature 7) | Feature | No | TBD | Day 3 |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** an application state machine enforced on the server, with every transition logged.
- **Key components:** application service, status history, frozen profile snapshot at submit, edit lock tied to the Review status, interview slot and offer records, feedback records.
- **Integration points:** profile data (Feature 2), job data (Features 3 and 6), notification service (Feature 7).

## Backlog (in discussion)
- Cancelling or withdrawing an application (tentative).
- Where rejected applications are shown (for example a "past jobs" menu).
- What happens when no offered interview slot works, and rescheduling.
- Offers that expire or go unanswered.
- Whether a talent rejected at the result stage skips the offer and goes straight to feedback.
- When feedback to the other party is released (after both submit, or after a timeout).
- The look of the status ribbon (the team said no colour coding for now).

---

# Feature 5: Anonymous Talent Discovery for Employers

## Feature Context

### Problem Statement
Employers like Sarah receive 200 or more applications per role and can't tell which cross-industry or international talents truly fit. Names, origin and other personal details can also cause accidental discrimination. Employers need to see talents by skills only.

### Overview and Context
- **Why:** The product's promise is that a skill is recognised for what it is, regardless of where it was built. Hiding identifying information protects that.
- **Who:** Employers at Australian SMEs.
- **What:** The employer home page shows a shortlist of potential talents by alias. Name, origin, ethnicity, nationality, gender and contact details are hidden. Employers see only the translated profile and the skill match. They can save, report or skip a talent. The basic tier shows the top N talents, and the full list is premium.

### Benefits
- Fairer shortlisting and less accidental discrimination.
- Faster review through a skills-first view.
- A clear monetization path (full list and direct contact).

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Shortlist:** The employer home page shows a shortlist of potential talents.
- [ ] **AC2 Alias only:** Each talent appears under their alias.
- [ ] **AC3 Hidden fields:** Name, origin, ethnicity, nationality, gender and contact details are never shown to employers.
- [ ] **AC4 Translated profile only:** Employers see the translated profile and never the original CV, because it may contain a photo or other identifying details.
- [ ] **AC5 Talent detail:** Clicking a talent opens a detail page, similar to the job detail page, with the talent information and the skill match.
- [ ] **AC6 Actions:** On the shortlist and on the detail page, the employer can save (bookmark), report a wrongly recommended talent, or skip (hide) the talent.
- [ ] **AC7 Top N:** On the basic tier, the employer sees only the top N talents. The full list is available on the premium tier.
- [ ] **AC8 Contact:** Contact details stay hidden. Employers contact talents through the platform, and directly contacting a talent who did not apply is premium.
- [ ] **AC9 Skills only:** The skill match is shown per skill. No person-level score is shown.

### Edge cases and errors
- [ ] **AC10:** No matching talents shows a helpful empty state.
- [ ] **AC11:** A skipped talent is hidden from this employer's shortlist.

### Non-functional (proposed defaults)
- [ ] **Security:** Hidden fields are removed on the server. Employer endpoints never return them, and an automated test checks every employer response for personal fields.
- [ ] **Privacy:** The original CV and contact details are never accessible through any employer endpoint.
- [ ] **Usability:** Keyboard navigable and readable by screen readers (WCAG 2.1 AA).

## 3. In-Scope
- [ ] Employer home shortlist of talents by alias
- [ ] Server-side hiding of personal fields
- [ ] Talent detail with the translated profile and skill match
- [ ] Save, report and skip actions
- [ ] Top N talents on the basic tier

## 4. Out of Scope
- Full talent list, direct contact and comparing two profiles (premium, Feature 7)
- Posting jobs and reviewing applications (Feature 6)
- Creating the translated profile (Feature 2)
- Messaging between employer and talent

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Confirmed translated profiles (Feature 2) | Feature | Yes | TBD | Day 1 to 2 |
| Aliases (Feature 1) | Feature | Yes | TBD | Day 1 |
| Matching service (Feature 3) | Feature | Yes | TBD | Day 2 |
| Premium gating (Feature 7) | Feature | No, for the basic tier | TBD | Day 3 |
| Seeded talent profiles | Team content | Yes (for the demo) | TBD | Day 2 |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** an anonymization layer sits between the database and every employer endpoint and produces an employer-safe view.
- **Key components:** anonymization layer (allowlist of fields), talent shortlist endpoint, talent detail endpoint, save, report and skip endpoints, an automated personal-data test.
- **Integration points:** profile and alias data, the matching service, and the entitlement check (Feature 7).

## Backlog (in discussion)
- The value of N for the top talent list.
- Whether to also hide employer and university names, age and photos.
- When anonymity ends (interviews and offers need real identity), and how the talent's consent is recorded.
- Whether talents opt in to appear in recommendations.
- How talents are ordered in the shortlist.
- How the employer-initiated contact flow works for talents (accept or decline).

---

# Feature 6: Streamlined Job Posting and Hiring Pipeline

## Feature Context

### Problem Statement
Sarah is the sole talent acquisition lead at a 60-person company and handles all screening, interviewing and onboarding herself. She needs one place to post jobs, track applicants against a target, and move talents through the process, without a heavy ATS.

### Overview and Context
- **Why:** The employer is the buyer and the person who feels the skills shortage most. The pipeline keeps the hiring decision with the human.
- **Who:** Employers.
- **What:** Employers post jobs with a target number of applicants and a close date. A job list shows target against current applicants and a close-date badge. Each job opens its applications, where the employer reviews profiles and skill matches, updates statuses, offers interview slots, sends offers and gives feedback. Job edits notify applicants.

### Benefits
- A lightweight workflow SMEs can adopt without new infrastructure.
- Clear visibility of how each job is progressing.
- Every status change is a human decision.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Post a job:** The employer can post a job with a description, a target number of applicants and a close date. The job starts as Open. The employer can also upload a PDF job description, which the AI reads to fill in the form for the employer to review. The basic plan allows up to 50 open jobs at a time (closed jobs do not count), and posting beyond that is blocked with an upgrade prompt.
- [ ] **AC2 My jobs list:** The employer sees all their posted jobs as a shortlist, showing the target against the current number of applicants (for example target 100, current 200) and the close date.
- [ ] **AC3 Close badge:** A green badge shows the job is open, a yellow badge shows less than one week until the close date, and a red badge shows the job is closed or overdue.
- [ ] **AC4 Applications view:** Clicking a job opens its applications and talents.
- [ ] **AC5 Review profiles:** The employer can review a talent's translated profile and skill match, like the talent detail page.
- [ ] **AC6 Status updates:** The employer moves an application through Review, Interview, Accepted or Rejected, Offer and Confirmed. Only valid transitions are allowed.
- [ ] **AC7 Edit lock:** Moving an application to Review locks the talent's ability to edit it.
- [ ] **AC8 Interview slots:** The employer offers time slots, sees the slot the talent picked, and confirms.
- [ ] **AC9 Result and offer:** After the interview the employer confirms the result, and sends an offer to accepted talents.
- [ ] **AC10 Edit a job:** The employer can edit the job description. Any change notifies everyone who has applied.
- [ ] **AC11 Feedback:** At the final stage the employer can give feedback to the talent and to the development team.
- [ ] **AC12 Human decisions:** The system never changes an application status on its own, and never auto-accepts or auto-rejects.

### Edge cases and errors
- [ ] **AC13:** A close date in the past is rejected with a clear message.
- [ ] **AC14:** An invalid status transition is rejected with a clear message.
- [ ] **AC15:** A job with no applicants shows a helpful empty state.

### Non-functional (proposed defaults)
- [ ] **Security:** An employer can only see and manage their own jobs and their applicants.
- [ ] **Reliability:** Every status change is logged with who made it and when.
- [ ] **Usability:** Badge states are shown in text as well as colour (WCAG 2.1 AA).

## 3. In-Scope
- [ ] Posting a job with a target number of applicants and a close date
- [ ] Posting a job from a PDF
- [ ] My jobs list with target against current and the close badge
- [ ] Applications view per job with profile and skill match review
- [ ] Status updates through the full lifecycle
- [ ] Interview slot offers, result, offer and confirmation
- [ ] Editing a job with applicant notification
- [ ] Employer feedback at the final stage

## 4. Out of Scope
- Comparing two profiles (premium, Feature 7)
- Employer-initiated contact and headhunting (premium, Feature 7)
- Notification delivery itself (Feature 7)
- The talent side of applying and tracking (Feature 4)
- Integrations with other hiring systems

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Accounts and roles (Feature 1) | Feature | Yes | TBD | Day 1 |
| Matching service (Feature 3) | Feature | Yes | TBD | Day 2 |
| Applications from talents (Feature 4) | Feature | Yes | TBD | Day 2 |
| Notifications (Feature 7) | Feature | No | TBD | Day 3 |
| Decision on how job skills are produced | Team decision | Blocks the skill match on new jobs | Team | Discussion tomorrow |
| Seeded jobs for the demo | Team content | Yes (for the demo) | TBD | Day 1 to 2 |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** job and application services behind role guards, with the application state machine from Feature 4 and a scheduled job that closes jobs on their close date.
- **Key components:** job service, badge calculation on the server, applications endpoint, status transition service with history, interview slot and offer services, job edit history.
- **Integration points:** the matching service (Feature 3), the anonymization layer (Feature 5), the notification service (Feature 7).

## Backlog (in discussion)
- How a job's required skills are produced (AI-extracted from the description, or tagged by the employer).
- What happens to pending applications when a job closes.
- Whether a major job edit re-runs the skill match for existing applicants.
- Rescheduling interviews when no slot fits, and offers that expire.
- Messaging between employer and talent on the platform.
- Company profile and verification.
- Employer-initiated path (Contacted, then Interview) and its talent accept or decline step.

---

# Feature 7: Timely Alerts, Insights and Premium Access

## Feature Context

### Problem Statement
Without alerts, talents and employers have to keep checking the platform for updates, and without insight into how their jobs or profiles perform, neither side can improve. The team also wants a sustainable model: the core experience stays free and extra capability is paid for.

### Overview and Context
- **Why:** Notifications keep the hiring process moving, tracking data improves the recommendations, and premium access funds the product.
- **Who:** Talents and employers.
- **What:** Notifications for key events, a user tracking system that logs job and profile events, basic charts on the employer home page, and premium gating for the open job limit, the full talent list, direct contact, comparing two profiles, statistics and advanced charts.

### Benefits
- Faster responses on both sides.
- A feedback loop for better recommendations.
- A clear premium path for employers.

## 1. Success Metrics
**Status:** ⏳ Pending (skipped for now)

## 2. User Acceptance Criteria (REQUIRED)
**Status:** 📝 Starter draft, needs team review

### Functional
- [ ] **AC1 Employer alert:** The employer is notified when someone applies to their job.
- [ ] **AC2 Talent email:** The talent is notified by email when an application is accepted or rejected.
- [ ] **AC3 Job edit alert:** Everyone who applied is notified when the job description is edited.
- [ ] **AC4 Event logging:** The system logs job appear, job watch, job save, job apply and job respond, and profile appear, profile watch and profile saved.
- [ ] **AC5 Employer statistics (premium):** Employers see the job events for their own jobs (appear, watch, save, apply, respond).
- [ ] **AC6 Talent statistics (premium):** Talents see their own job apply and job respond events, and the profile appear, watch and saved events for their profile.
- [ ] **AC7 Ignored counts:** The number of skipped jobs and profiles is recorded for improving the AI recommendations, and is not shown to users.
- [ ] **AC8 Basic charts, employer:** The home page shows how many jobs are open, how many jobs reached their applicant target, and how many talents are waiting for a response.
- [ ] **AC9 No KPI cards, talent:** The talent home page has no KPI cards. Active applications appear in the Your activity component (Feature 4).
- [ ] **AC10 Premium gating:** On the basic plan, employers can have up to 50 open jobs at a time, see the top N talents, respond only to talents who applied, and see basic charts. Premium unlocks no job limit (assumed), the full talent list, direct contact (headhunting), comparing two profiles, job statistics, and advanced charts. Talents on premium get personal statistics and advanced charts.
- [ ] **AC11 Server-side check:** Premium access is checked on the server, never only in the interface.
- [ ] **AC12 Upgrade prompt:** A locked feature shows what it is and how to upgrade.

### Edge cases and errors
- [ ] **AC13:** A failed email does not block the action that triggered it, and is retried.
- [ ] **AC14:** Logging an event never slows down or blocks the user action.
- [ ] **AC15:** Charts with no data show a helpful empty state.
- [ ] **AC16 Plan selection:** A plan selection screen compares Basic and Premium and lists exactly which features each plan includes, for employers and for talent. The premium account has a distinct, elegant look that makes the difference visible.

### Non-functional (proposed defaults)
- [ ] **Privacy:** Employers cannot identify which talent performed an event that would break anonymity.
- [ ] **Reliability:** Notifications are sent at most once per event.
- [ ] **Security:** Users only see their own events and charts.

## 3. In-Scope
- [ ] Notifications for new applications, accepted or rejected results, and job edits
- [ ] The user tracking system for job and profile events, with statistics as a premium feature
- [ ] Basic charts on the employer home page
- [ ] Premium gating for the full list, direct contact, comparing two profiles and advanced charts
- [ ] Upgrade prompts for locked features
- [ ] Plan selection screen listing what each plan includes

## 4. Out of Scope
- Real payment processing (to be decided)
- Talent score charts or any scoring of people
- Recruiting analytics shared outside the platform
- The status changes that trigger notifications (Features 4 and 6)

## 5. Dependencies

| Dependency | Type | Blocking? | Owner | ETA |
|---|---|---|---|---|
| Applications and statuses (Features 4 and 6) | Feature | Yes, for notifications and charts | TBD | Day 2 |
| Email sending service | System | Yes, for email | TBD | Day 3 |
| Accounts and roles (Feature 1) | Feature | Yes | TBD | Day 1 |
| Talent shortlist and top N (Feature 5) | Feature | Yes, for gating | TBD | Day 2 |
| Decision on the premium chart list | Team decision | Blocks the advanced charts only | Team | Discussion tomorrow |

## 6. UX Prototype & Design
**Status:** ⏳ Pending (skipped for now)

## 7. Architecture Requirements
**Architect assigned:** TBD
- **Approach:** events trigger notifications through an outbox so a failed email never blocks the main action. Tracking events are written asynchronously.
- **Key components:** notification service with templates, event tracking service, aggregation endpoints for charts, entitlement record per user with a single server-side check.
- **Integration points:** an email service, the application and job services (Features 4 and 6), and the anonymization layer (Feature 5).

## Backlog (in discussion)
- Whether notifications are email only or also in-app.
- The full list of notification types (interview slots, offers, job closing soon, feedback).
- The list of premium charts for each side.
- Whether employers see job events as aggregate counts per job or per talent.
- A notice to users that their activity is tracked, and the retention period.
- Pricing, credits for contacting talents, promoted jobs, and university or training provider licences.
- How premium works in the demo (a toggle, or real payments).
- Guardrails for charts: no talent scoring and no breakdown by nationality, gender or ethnicity.
- Notification settings per user.

---

# 9. Consolidated backlog (in discussion)

## Discuss first (they block several features)
1. **Translation design (Feature 2):** how it works, where it shows, demo industry pairs, mapping library.
2. **Matching formula (Features 3, 5, 6):** per skill versus aggregate percentage, and how it fits the PRD's no-single-score rule.
3. **How jobs get their required skills (Features 3, 6).**
4. **When anonymity ends and how consent is recorded (Feature 5).**
5. **Where rejected applications show up (Feature 4).**

## Product decisions
- Sign-up fields; value of N; top N ordering; opt-in visibility for recommendations.
- Hiding employer and university names, age and photos.
- Cancel or withdraw an application; expiring offers; interview rescheduling.
- Rejected at result: skip the offer and go to feedback?
- Pending applications when a job closes; re-running the match after a job edit.
- Exact onboarding steps and landing page choices (one page or two, a "how it works" example, premium pricing mention).
- Whether Premium has any limit on open jobs (assumed unlimited).
- Employer-initiated contact (premium) and the talent's accept or decline step.

## Platform and trust
- Email verification, password reset, delete my data.
- Company profile and verification.
- Alias wording and screening rules.
- Messaging on the platform.
- Report moderation.
- Notification channels and settings; activity-tracking notice; retention.

## Monetization
- Premium chart list; pricing; credits for contact; promoted jobs; institution licences; demo approach for premium.

## Later (roadmap)
- Moving skipped jobs down the list; OCR for scanned CVs; behavioural evidence and the pre-interview survey; data flywheel and co-occurrence learning; talent pool marketplace.
