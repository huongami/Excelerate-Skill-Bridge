# Skill Bridge: User Stories (full set, every story broken down)

**Created:** 2026-10-06
**Terminology:** Talent and Employer replace candidate, job seeker, recruiter and HR.
**Source:** The confirmed feature specs and user flow (no Rally data available)
**Stories:** 50 stories, split into 117 sub-stories (3 stories of 1 point are not split further)
**Total effort:** 132 story points (about 44 developer-days by the rubric)
**Demo slice:** 78 story points (about 26 developer-days)

This file merges the earlier user stories and story breakdown into one. Every story is now broken into sub-stories with their own acceptance criteria, tasks and effort. The eight stories that were broken down earlier keep their technical sub-stories, and the others are split into delivery slices of about 1 point each.

## How to read this document

**IDs:** `F<feature>-S<story>` for a story, and a letter for a sub-story, for example F3-S2b is the second sub-story of story 2 in Feature 3.

**Priority**
- **High:** needed for the demo loop (sign up, CV, jobs, apply, anonymous view, status updates).
- **Medium:** important, and it extends the loop.
- **Low:** deferrable.

**Effort scale (story points):** 1 = under 2 hours, 2 = half a day, 3 = about 1 day, 5 = 2 to 3 days, 8 = about 1 week.

**Standard Definition of Done (applies to every story and sub-story)**
- [ ] Code written and reviewed
- [ ] Unit tests added and passing, with integration tests where applicable
- [ ] Deployed to the test environment
- [ ] Acceptance criteria verified
- [ ] No blocking bugs

Each story lists only what it adds to this checklist.

**Story and sub-story roles.** The story holds the whole-story acceptance criteria, priority, dependencies and open decisions. Each sub-story is one deliverable slice with its own acceptance criteria and a task checklist. Sub-stories inherit the story's priority, demo slice and decisions unless they state otherwise.

**Decisions still open.** Stories that depend on a backlog item name it as "Decision" and give the default to build with until the team decides. Defaults are assumptions, not agreed decisions.

**Estimates** assume AI-assisted building and a team working in parallel. Confirm them against your team size and stack.

## Summary

| Feature | Stories | Sub-stories | Points | Demo slice points |
|---|---|---|---|---|
| 1. Secure Onboarding and Role-Based Access | 8 | 15 | 16 | 12 |
| 2. Explainable Cross-Border Skill Translation | 7 | 16 | 18 | 16 |
| 3. Personalised Job Matching and Discovery | 7 | 16 | 19 | 16 |
| 4. Transparent Applications and Status Tracking | 8 | 19 | 20 | 12 |
| 5. Anonymous Talent Discovery for Employers | 5 | 9 | 11 | 8 |
| 6. Streamlined Job Posting and Hiring Pipeline | 7 | 21 | 24 | 14 |
| 7. Timely Alerts, Insights and Premium Access | 8 | 21 | 24 | 0 |
| **Total** | **50** | **117** | **132** | **78** |

Sub-stories counts exclude the 3 stories of 1 point that are not split (F1-S2, F3-S6 and F5-S5). They carry a task checklist instead.

---

# Feature 1: Secure Onboarding and Role-Based Access

### F1-S1: Role-Based Sign-up

**As a** new visitor, **I want** to sign up as a talent or an employer, **so that** I get the experience built for my role.

**Acceptance criteria (whole story)**
- Given a new visitor, when they sign up as a talent or employer with basic information, then an account with that role is created.
- Given a talent sign-up, when it completes, then the talent continues to CV upload (F2-S1).
- Given an employer sign-up, when it completes, then there is no CV step, and only employer information is collected.
- Given an email already in use or a weak password, when signing up, then the form shows a clear error.

**Definition of Done:** standard, plus passwords stored hashed.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** System: database and hosting. Decision (non-blocking): final sign-up fields. Default: name, email, role.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S1a: Sign-up Form and Validation

**As a** new visitor, **I want** a sign-up form with a role choice, **so that** I can start as a talent or an employer.

**Acceptance criteria**
- Given the form, when the visitor picks talent or employer and enters the basic information, then the form validates it.
- Given an email already in use or a weak password, then a clear error is shown.

**Tasks**
- [ ] Sign-up form with a role selector
- [ ] Validation rules and messages
- [ ] Employer variant without a CV step

**Effort:** 1 pt / XS

#### F1-S1b: Account Creation and Next Step

**As a** new visitor, **I want** my account created securely, **so that** I continue to the right next step.

**Acceptance criteria**
- Given valid input, when submitted, then the account is created with its role and the password is stored hashed.
- Given a talent, then they continue to CV upload. Given an employer, then they go to their home page.

**Tasks**
- [ ] User table with a role field
- [ ] Password hashing
- [ ] Redirect by role

**Effort:** 1 pt / XS

### F1-S2: Alias Assignment

**As a** talent, **I want** to pick an alias or get one automatically, **so that** employers see me without my name.

**Acceptance criteria (whole story)**
- Given a talent at sign-up, when they enter an alias, then it is saved if it is unique.
- Given a blank alias, when sign-up completes, then a unique animal-based alias is assigned.
- Given an alias that is taken, when it is submitted, then an available alternative is suggested.

**Definition of Done:** standard, plus a database uniqueness constraint.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F1-S1. Decision (non-blocking): alias wording and screening rules. Default: neutral words such as colours, and a check against the talent's own name.

**Tasks** (1 point, so not split further)
- [ ] Alias field at sign-up and in settings
- [ ] List of animal names with neutral modifiers
- [ ] Database uniqueness constraint
- [ ] Suggest an alternative on conflict

### F1-S3: Login, Logout and Session

**As a** registered user, **I want** to log in and out securely, **so that** only I can access my account.

**Acceptance criteria (whole story)**
- Given valid credentials, when the user logs in, then they land on the home page for their role.
- Given invalid credentials, when the user logs in, then a generic error is shown that doesn't reveal which field was wrong.
- Given an expired session, when the user opens a page, then they are sent to login and returned to that page afterwards.
- Given the user logs out, then the session ends.

**Definition of Done:** standard, plus login attempts are rate limited.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S1

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S3a: Login and Logout

**As a** registered user, **I want** to log in and out, **so that** only I can use my account.

**Acceptance criteria**
- Given valid credentials, then the user lands on the home page for their role.
- Given invalid credentials, then a generic error is shown. Given logout, then the session ends.

**Tasks**
- [ ] Login endpoint and form
- [ ] Logout
- [ ] Generic error message

**Effort:** 1 pt / XS

#### F1-S3b: Session Expiry and Rate Limiting

**As a** registered user, **I want** my session handled safely, **so that** my account stays protected.

**Acceptance criteria**
- Given an expired session, then the user is sent to login and returned to their page afterwards.
- Given repeated failed attempts, then login is rate limited.

**Tasks**
- [ ] Session token expiry
- [ ] Return-to-page handling
- [ ] Rate limiter on login

**Effort:** 1 pt / XS

### F1-S4: Role-Based Access Guards

**As a** platform owner, **I want** roles enforced on the server, **so that** talents and employers can only reach their own data.

**Acceptance criteria (whole story)**
- Given a talent account, when it requests an employer-only page or endpoint, then the server returns 403, and the same applies in reverse.
- Given a visitor who is not logged in, when they open a protected page, then they are sent to login.
- Given a user, when they request another user's private data, then the server returns 403.

**Definition of Done:** standard, plus tests for both role directions.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S1, F1-S3

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S4a: Server-side Role Guard

**As a** platform owner, **I want** roles enforced on the server, **so that** each role only reaches its own data.

**Acceptance criteria**
- Given a talent account that requests an employer-only endpoint, then the server returns 403, and the reverse also returns 403.
- Given a request for another user's private data, then the server returns 403.

**Tasks**
- [ ] Guard middleware with role and ownership checks
- [ ] Apply it to all protected endpoints

**Effort:** 1 pt / XS

#### F1-S4b: Page Routing Guards and Tests

**As a** platform owner, **I want** protected pages guarded and tested, **so that** nothing leaks through the interface.

**Acceptance criteria**
- Given a visitor who is not logged in, when they open a protected page, then they are sent to login.

**Tasks**
- [ ] Route guards in the client
- [ ] Tests for both role directions
- [ ] Test for the not-logged-in case

**Effort:** 1 pt / XS

### F1-S5: Left Navigation Pane

**As a** logged-in user, **I want** a fixed navigation pane I can hide, **so that** I can reach the main sections quickly.

**Acceptance criteria (whole story)**
- Given a logged-in user, when a page loads, then a navigation pane on the left gives direct access to the main sections for their role.
- Given the pane, when the user hides or shows it, then the state persists across pages and sessions.
- Given a keyboard or screen reader user, then the pane is fully usable (WCAG 2.1 AA).

**Definition of Done:** standard, plus accessibility check on the pane.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F1-S3. Decision (non-blocking): final items per role. Default: talent gets home, bookmarks, applications and settings. Employer gets home, my jobs and settings.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S5a: Navigation Pane Layout

**As a** logged-in user, **I want** a navigation pane on the left, **so that** I can reach the main sections quickly.

**Acceptance criteria**
- Given a logged-in user, when a page loads, then the pane shows the main sections for their role, with the current one highlighted.

**Tasks**
- [ ] Pane component
- [ ] Section list by role
- [ ] Active item highlight

**Effort:** 1 pt / XS

#### F1-S5b: Hide, Show and Accessibility

**As a** logged-in user, **I want** to hide the pane and have it remembered, **so that** I control my screen space.

**Acceptance criteria**
- Given the pane, when the user hides or shows it, then the state persists across pages and sessions.
- Given a keyboard or screen reader user, then the pane is fully usable (WCAG 2.1 AA).

**Tasks**
- [ ] Persist the open or hidden state
- [ ] Focus order and labels
- [ ] Accessibility check

**Effort:** 1 pt / XS

### F1-S6: Settings and Information Edit

**As a** user, **I want** to edit my information in settings, **so that** my details stay correct.

**Acceptance criteria (whole story)**
- Given a logged-in user, when they open settings, then they can edit their information and save.
- Given a talent, when they change their alias, then the same uniqueness rule applies.
- Given invalid values, when saving, then the form shows clear errors and nothing is lost.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F1-S3. Talent profile fields come from F2-S3.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S6a: Settings Page and Information Edit

**As a** user, **I want** to edit my information in settings, **so that** my details stay correct.

**Acceptance criteria**
- Given a logged-in user, when they edit their information and save, then the changes are stored.
- Given invalid values, then clear errors are shown and nothing is lost.

**Tasks**
- [ ] Settings page
- [ ] Form and validation
- [ ] Update endpoint

**Effort:** 1 pt / XS

#### F1-S6b: Alias Edit

**As a** talent, **I want** to change my alias, **so that** I can pick a name I like.

**Acceptance criteria**
- Given a new alias, when saved, then the same uniqueness rule applies. If it is taken, an available alternative is suggested.

**Tasks**
- [ ] Alias field in settings
- [ ] Reuse the uniqueness check
- [ ] Error message

**Effort:** 1 pt / XS

### F1-S7: Demo Accounts and Seeded Data

**As a** presenter, **I want** ready-made accounts and data, **so that** the demo runs smoothly without waiting on live steps.

**Acceptance criteria (whole story)**
- Given the seed script, when it runs, then it creates a demo talent (based on the Minh persona) with a sample CV, a translated profile and an alias, and a demo employer (based on the Sarah persona) with the seeded jobs.
- Given the seed script, then 8 to 10 more anonymous talent profiles are created across 2 to 3 industries, so the employer shortlist is populated.
- Given the seed script, then applications exist at different statuses (Applied, Review, Interview, Accepted), so the status ribbon and tracking view can be shown immediately.
- Given the demo employer, then both a basic and a premium version exist, so the 50-job limit, the top N limit and the plan screen can be shown.
- Given the script runs again, then it resets the demo to its starting state without creating duplicates.
- Given all demo data, then it is synthetic, with no real personal data.

**Definition of Done:** standard, plus demo login details kept in the seed file only, not shown in the interface.
**Priority:** High | **Complexity:** Low | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S1, F2-S4c, F4-S1b, F6-S1c

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S7a: Demo Talent and Employer Accounts

**As a** presenter, **I want** ready-made demo accounts, **so that** I can log in immediately on stage.

**Acceptance criteria**
- Given the seed script, when it runs, then it creates a demo talent (Minh persona) with a sample CV, a translated profile and an alias, and a demo employer (Sarah persona) with the seeded jobs.

**Tasks**
- [ ] Seed data for the two personas
- [ ] Sample CV file
- [ ] Link the employer to the seeded jobs

**Effort:** 1 pt / XS

#### F1-S7b: Extra Talent Profiles and Varied Applications

**As a** presenter, **I want** a populated platform, **so that** lists and statuses are not empty.

**Acceptance criteria**
- Given the seed script, then 8 to 10 more anonymous talent profiles exist across 2 to 3 industries.
- Given the seed script, then applications exist at Applied, Review, Interview and Accepted.

**Tasks**
- [ ] Profile fixtures
- [ ] Application fixtures with status history

**Effort:** 1 pt / XS

#### F1-S7c: Reset and Basic/Premium Employers

**As a** presenter, **I want** to reset the demo and show both plans, **so that** every run starts the same.

**Acceptance criteria**
- Given the demo employer, then a basic and a premium version exist.
- Given the script runs again, then it resets to the starting state without duplicates. All data is synthetic.

**Tasks**
- [ ] Idempotent reset logic
- [ ] Plan flag on employers
- [ ] Keep demo logins in the seed file only

**Effort:** 1 pt / XS

### F1-S8: Landing Page

**As a** first-time visitor, **I want** to understand what Skill Bridge does and choose my path, **so that** I know whether it is for me.

**Acceptance criteria (whole story)**
- Given a visitor who is not logged in, when they open the site, then the landing page explains the problem and the product, and its top section highlights the Australian market and uses icons.
- Given the top section, then it does not use "black-box score" wording.
- Given the page, then it shows the key facts from the PRD: 69% of Australian employers report difficulty finding skilled people (ManpowerGroup, 2024), and 680,582 international students are in Australia (Dept. of Education, 2026).
- Given the page, then there are two clear entry points, one for talent and one for employers, each leading to sign-up with that role preselected, plus a login link.
- Given the page, then it states the product's promises: every recommendation is explained, talent is anonymous to employers, and the employer always makes the final decision.
- Given a logged-in user, when they open the site, then they go straight to their home page.
- Given a small screen, then the page is readable and meets WCAG 2.1 AA.

**Definition of Done:** standard, plus an accessibility check.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S1, F1-S3. Decisions (non-blocking): one page or two, a "how it works" example, and a premium pricing mention. Default: one page with two paths and no pricing.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F1-S8a: Landing Content and Australian Market Hero

**As a** first-time visitor, **I want** a clear explanation of the product, **so that** I know what Skill Bridge does.

**Acceptance criteria**
- Given the landing page, then the top section highlights the Australian market with icons and has no 'black-box score' wording.
- Given the page, then it shows the PRD facts and the product promises.

**Tasks**
- [ ] Hero copy and icons
- [ ] Facts section
- [ ] Promises section

**Effort:** 1 pt / XS

#### F1-S8b: Entry Points and Redirects

**As a** first-time visitor, **I want** an obvious way in for my role, **so that** I can sign up quickly.

**Acceptance criteria**
- Given the page, then one entry point for talent and one for employers lead to sign-up with the role preselected, plus a login link.
- Given a logged-in user, then they go straight to their home page. The page is readable on small screens and meets WCAG 2.1 AA.

**Tasks**
- [ ] Role-preselected sign-up links
- [ ] Redirect logic
- [ ] Responsive and accessibility check

**Effort:** 1 pt / XS

---

# Feature 2: Explainable Cross-Border Skill Translation

### F2-S1: CV Upload and Private Storage

**As a** talent, **I want** to upload my CV, **so that** the platform can build my profile from it.

**Acceptance criteria (whole story)**
- Given a signed-in talent, when they upload a PDF or DOCX of up to 10 MB (proposed limit), then the file is stored privately.
- Given an unsupported type or an oversized file, when it is uploaded, then it is rejected with a clear message.
- Given a stored CV, then only its owner can access it, and no employer endpoint ever returns it.

**Definition of Done:** standard, plus owner-only access verified.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S3. System: private object storage.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S1a: Upload Endpoint with Checks

**As a** talent, **I want** to upload my CV, **so that** the platform can read it.

**Acceptance criteria**
- Given a PDF or DOCX of up to 10 MB (proposed limit), then the upload is accepted.
- Given another type or a larger file, then it is rejected with a clear message.

**Tasks**
- [ ] Upload endpoint
- [ ] Type and size validation
- [ ] Error messages

**Effort:** 1 pt / XS

#### F2-S1b: Private Owner-only Storage

**As a** talent, **I want** my CV kept private, **so that** only I can see it.

**Acceptance criteria**
- Given a stored CV, then only its owner can access it.
- Given any employer endpoint, then the CV is never returned.

**Tasks**
- [ ] Private storage location
- [ ] Owner-checked access
- [ ] Test that employer endpoints never return it

**Effort:** 1 pt / XS

### F2-S2: AI Parsing and Form Pre-fill

**As a** talent, **I want** the AI to fill in my information from my CV, **so that** I don't type it all.

**Acceptance criteria (whole story)**
- Given an uploaded CV, when parsing completes, then the information fields are pre-filled and each is marked "AI-detected".
- Given information missing from the CV, then the field stays empty and flagged, and nothing is invented.
- Given parsing takes time, then a progress state is shown (target about 15 seconds for a typical CV).
- Given the AI output, then it is validated against the profile schema before it is shown.

**Definition of Done:** standard, plus CV text not written to logs and CV content treated as data, never as instructions to the model.
**Priority:** High | **Complexity:** Medium | **Effort:** 4 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S1. System: LLM API. Data: profile schema.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S2a: Extract Text from CV

**As a** talent, **I want** my CV file read into text, **so that** the AI can analyse it.

**Acceptance criteria**
- Given a PDF or DOCX, when it is processed, then the text is extracted in reading order, with sections kept in sequence.
- Given a multi-column or table layout, then the text is still extracted in a readable order (best effort).
- Given a file with no extractable text, such as a scanned image, then it is reported as unreadable and the talent goes to the manual-entry fallback (F2-S5). OCR is out of scope.

**Technical tasks**
- [ ] Choose text extraction libraries for PDF and DOCX
- [ ] Normalise whitespace and remove page headers and footers where possible
- [ ] Test with 3 sample CVs, including one with columns

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S1

#### F2-S2b: Parse Text into a Structured Profile

**As a** talent, **I want** my CV's content organised into profile fields, **so that** I don't have to type it.

**Acceptance criteria**
- Given extracted text, when parsed, then the output contains roles, employers, dates, responsibilities, education and skills, and matches the profile schema.
- Given information not in the CV, then the field is left empty and flagged, and never invented.
- Given invalid output, when parsing runs, then the system retries once, then reports a failure (handled by F2-S5).
- Given CV text that contains instructions (for example "ignore previous instructions"), then it is treated as data and does not change the system's behaviour.

**Technical tasks**
- [ ] Define the JSON schema for the profile
- [ ] Write the parsing prompt with low temperature, and add a timeout
- [ ] Validate the output against the schema, with one retry
- [ ] Make sure CV text is never written to logs

**Definition of Done:** standard, plus a prompt-injection test case.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F2-S2a. System: LLM API. Data: profile schema.

#### F2-S2c: Pre-fill Form with Markers and Progress

**As a** talent, **I want** to see the fields filled in and know which came from the AI, **so that** I know what to check.

**Acceptance criteria**
- Given parsing in progress, then a progress state is shown (target about 15 seconds for a typical CV).
- Given the result, then the form is pre-filled and each AI-filled field is marked "AI-detected".
- Given the talent edits a field, then the marker clears for that field (proposed behaviour).

**Technical tasks**
- [ ] Progress and error states
- [ ] Map the parsed JSON to the form fields
- [ ] Track which fields are AI-detected

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S2b, F2-S3

### F2-S3: Profile Editing

**As a** talent, **I want** to review and correct what the AI detected, **so that** my profile is accurate.

**Acceptance criteria (whole story)**
- Given pre-filled fields, when the talent edits, adds or removes a field and saves, then the changes are stored.
- Given invalid values, when saving, then clear errors are shown.
- Given unsaved changes, when the talent leaves the page, then a warning is shown.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S2

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S3a: Editable Profile Form

**As a** talent, **I want** to edit what the AI detected, **so that** my profile is accurate.

**Acceptance criteria**
- Given pre-filled fields, then the talent can edit, add or remove any of them.
- Given invalid values, then clear errors are shown.

**Tasks**
- [ ] Form sections for roles, education and skills
- [ ] Add and remove rows
- [ ] Validation

**Effort:** 1 pt / XS

#### F2-S3b: Save and Unsaved-changes Warning

**As a** talent, **I want** my changes saved safely, **so that** I don't lose my work.

**Acceptance criteria**
- Given edits, when the talent saves, then the changes are stored.
- Given unsaved changes, when the talent leaves the page, then a warning is shown.

**Tasks**
- [ ] Save endpoint
- [ ] Dirty-state tracking
- [ ] Warning dialog

**Effort:** 1 pt / XS

### F2-S4: Translated Profile at Information Input

**As a** talent, **I want** to see my experience translated into skills an Australian employer recognises, **so that** my real capability is visible.

**Acceptance criteria (whole story)**
- Given a saved profile, when the talent finishes information input, then their translated profile is shown at this step.
- Given the translated profile, then only this version is ever shared with employers, never the original CV.
- Given the output, then it contains no personality, suitability or overall quality score.

**Definition of Done:** standard, plus the output checked on 3 sample CVs.
**Priority:** High | **Complexity:** Medium | **Effort:** 4 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S3. Decision (blocks the translated content only): translation design. Default: reuse the translation engine from the national round MVP.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S4a: Translation Service Wrapper

**As a** talent, **I want** my experience run through the translation engine, **so that** I get skills an Australian employer recognises.

**Acceptance criteria**
- Given a saved profile with experience items, when translation runs, then the national round MVP engine is called and returns translated skills.
- Given an engine error or timeout, then the talent still sees their profile and can retry.
- Given the same input, then the same output is returned (low temperature and caching).

**Technical tasks**
- [ ] Put the existing engine behind one service interface, so the design can change later
- [ ] Store the results per experience item
- [ ] Add caching and a timeout

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F2-S3. Decision (blocks the output format only): translation design. Default: reuse the national MVP engine as is.

#### F2-S4b: Show Translated Profile at Information Input

**As a** talent, **I want** to see my translated profile when I finish entering my information, **so that** I can see how employers will read it.

**Acceptance criteria**
- Given translation is complete, then the translated profile is shown at this step.
- Given the output, then it contains no personality, suitability or overall quality score.
- Given translation is still running or has failed, then a loading or error state is shown.

**Technical tasks**
- [ ] Display component for the translated profile
- [ ] Loading and error states

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4a

#### F2-S4c: Employer-Safe Translated Snapshot

**As a** platform owner, **I want** the translated profile stored apart from the original CV, **so that** employers and applications only ever use the translated version.

**Acceptance criteria**
- Given a saved translated profile, then it is stored as a separate record with no original CV fields.
- Given an application, then this record is what is frozen into the application (F4-S1b).
- Given an employer view, then it reads only this record, through the anonymization layer.

**Technical tasks**
- [ ] Data model for the translated profile and its versions
- [ ] Migration
- [ ] Read access for the application and employer code paths

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4a

### F2-S5: Parse Failure and Manual Entry

**As a** talent, **I want** a fallback when my CV can't be read, **so that** I can still finish my profile.

**Acceptance criteria (whole story)**
- Given an unreadable file or a parsing error, when parsing fails, then the talent sees a clear error with retry or manual entry.
- Given invalid AI output, when parsing runs, then the system retries once, then offers manual entry.
- Given any failure, then no entered data is lost.

**Definition of Done:** standard, plus failure paths tested with a corrupted file.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F2-S2

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S5a: Error and Retry States

**As a** talent, **I want** a clear message when my CV can't be read, **so that** I know what to do.

**Acceptance criteria**
- Given an unreadable file or a parsing error, then an error is shown with a retry option.
- Given invalid AI output, then the system retries once.

**Tasks**
- [ ] Error states
- [ ] Retry action
- [ ] One-retry logic

**Effort:** 1 pt / XS

#### F2-S5b: Manual Entry Fallback

**As a** talent, **I want** to type my details when parsing fails, **so that** I can still finish my profile.

**Acceptance criteria**
- Given a failure, then manual entry is offered.
- Given any failure, then no entered data is lost.

**Tasks**
- [ ] Manual form path
- [ ] Preserve the draft
- [ ] Test with a corrupted file

**Effort:** 1 pt / XS

### F2-S6: Linear Onboarding Flow

**As a** new talent, **I want** one clear path to build my profile, **so that** I am not confused about which step comes next.

**Acceptance criteria (whole story)**
- Given a new talent after sign-up, then onboarding is one linear flow: upload CV, review and edit what the AI filled in (including the translated skills), done.
- Given the review step, then editing answers happens there, not in a separate flow.
- Given any step, when the talent goes back, then the data they entered is kept.
- Given a returning talent, then they edit their profile from settings and do not repeat onboarding.
- Given a talent who leaves partway, when they return, then they resume at the step where they stopped.

**Definition of Done:** standard, plus a walkthrough with a new user shows no dead ends.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S1, F2-S3, F2-S4b. Decision (non-blocking): exact steps. Default: the three steps above.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S6a: Three-step Onboarding Flow

**As a** new talent, **I want** one linear path, **so that** I always know the next step.

**Acceptance criteria**
- Given a new talent after sign-up, then onboarding runs upload CV, review and edit, done.
- Given the review step, then editing answers happens there, not in a separate flow.

**Tasks**
- [ ] Step container with a progress indicator
- [ ] Wire the three steps
- [ ] Remove the separate Edit Answers flow

**Effort:** 1 pt / XS

#### F2-S6b: Saved Progress and Resume

**As a** talent, **I want** to go back or leave and return, **so that** I don't lose data.

**Acceptance criteria**
- Given any step, when the talent goes back, then their data is kept.
- Given a talent who leaves partway, then they resume at that step. A returning talent edits from settings.

**Tasks**
- [ ] Persist the step and the draft
- [ ] Resume logic
- [ ] Link to settings for returning users

**Effort:** 1 pt / XS

### F2-S7: "What Employers See" Panel

**As a** talent, **I want** to see my profile the way employers see it, **so that** I know what is shared.

**Acceptance criteria (whole story)**
- Given a talent with a confirmed profile, when they open their home page, then a "What employers see" panel shows their anonymous profile: alias, translated role and translated skills.
- Given a talent without a confirmed profile, then the panel invites them to complete it. It replaces the old "Your anonymous profile is empty" message.
- Given the panel, then it shows exactly what the anonymization layer returns to employers, from the same source.
- Given a field hidden from employers (name, origin, contact details), then it is not shown in the panel.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S4c, F5-S1a

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F2-S7a: Panel Reading the Employer View

**As a** talent, **I want** to see exactly what employers see, **so that** I know what is shared.

**Acceptance criteria**
- Given a confirmed profile, then the panel shows the alias, translated role and translated skills as the anonymization layer returns them.
- Given a field hidden from employers, then it is not shown.

**Tasks**
- [ ] Use the same projection as employer endpoints
- [ ] Panel component

**Effort:** 1 pt / XS

#### F2-S7b: Empty State

**As a** talent without a confirmed profile, **I want** to be invited to complete it, **so that** the panel isn't a dead end.

**Acceptance criteria**
- Given no confirmed profile, then the panel invites the talent to complete it, replacing the old 'Your anonymous profile is empty' message.

**Tasks**
- [ ] Empty-state copy
- [ ] Link to onboarding

**Effort:** 1 pt / XS

---

# Feature 3: Personalised Job Matching and Discovery

### F3-S1: Per-Skill Matching Service

**As a** talent, **I want** my profile compared to a job skill by skill, **so that** I understand where I fit and where I don't.

**Acceptance criteria (whole story)**
- Given a confirmed translated profile and a job's required skills, when the match runs, then each required skill is returned as a match, partial match or gap, with a plain-language reason.
- Given a match result, then a percentage may be shown as a summary of required-skill coverage, never as a score on the person.
- Given any input, then matching uses skills only and never the alias, origin or any protected attribute.
- Given the same input, then the result is the same.

**Definition of Done:** standard, plus unit tests against the seeded jobs and the matcher built as a replaceable module.
**Priority:** High | **Complexity:** Medium (High if the national MVP matcher cannot be reused) | **Effort:** 5 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S4, F6-S1. Decision (non-blocking): matching formula. Default: the national MVP matcher.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S1a: Normalise Job Required Skills

**As a** talent, **I want** a job's skills described in the same terms as my profile, **so that** the comparison is fair.

**Acceptance criteria**
- Given a job's required skills, then they are stored in the same vocabulary as talent skills.
- Given a skill written differently (for example "MS Excel" and "Excel"), then both map to one skill through a simple alias list.
- Given an unknown skill, then it is kept as typed.

**Technical tasks**
- [ ] Seed a skill vocabulary and alias list for the demo industries
- [ ] Normalisation function
- [ ] Unit tests

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S1. Decision (non-blocking): how job skills are produced. Default: AI-extracted and editable.

#### F3-S1b: Per-Skill Comparison with Reasons

**As a** talent, **I want** each required skill marked as a match, partial match or gap with a reason, **so that** I understand where I fit.

**Acceptance criteria**
- Given a translated profile and a job's required skills, when the match runs, then each required skill is returned as match, partial or gap.
- Given each result, then it includes a plain-language reason that refers to the talent's evidence (original skill and mapped skill).
- Given the same input, then the result is the same.
- Given any input, then the alias, origin and other protected attributes are never used.

**Technical tasks**
- [ ] Reuse the national MVP matcher
- [ ] Define the result contract: skill, status, evidence, reason
- [ ] Unit tests with seeded jobs and sample profiles, including a gap and a partial match

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium (High if the national MVP matcher cannot be reused) | **Effort:** 3 pts / S-M | **Demo slice:** Yes
**Dependencies:** Story: F3-S1a, F2-S4c. Decision (non-blocking): matching formula. Default: the national MVP matcher.

#### F3-S1c: Match Summary and Replaceable Interface

**As a** talent, **I want** a simple summary of my match, **so that** I can scan jobs quickly.

**Acceptance criteria**
- Given per-skill results, then a summary percentage is shown as required skills covered divided by required skills, with the list of gaps.
- Given the matcher, then it sits behind one interface so the formula can change without changing the code that calls it.
- Given a job with no required skills, then no percentage is shown.

**Technical tasks**
- [ ] Summary function
- [ ] Interface and contract
- [ ] Short note on the placeholder formula

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F3-S1b. Decision (non-blocking): per-skill versus aggregate percentage. Default: coverage percentage as a summary only.

### F3-S2: Recommended Jobs on Home

**As a** talent, **I want** a home page of recommended jobs, **so that** I see where to look first.

**Acceptance criteria (whole story)**
- Given a talent with a profile, when they open the home page, then open jobs are listed by skill match and, if a target role is set, by that role.
- Given closed, skipped or already applied jobs, then they are not shown.
- Given no profile, then the talent is prompted to complete it. Given no matches, then a helpful empty state is shown.

**Definition of Done:** standard, plus recommendations cached and refreshed when the profile or jobs change.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F3-S1, F6-S1. Decision (non-blocking): where the target role is set. Default: in settings.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S2a: Ranking Query

**As a** talent, **I want** jobs ranked by fit, **so that** the best ones come first.

**Acceptance criteria**
- Given a talent with a profile, then open jobs are ranked by skill match and, if a target role is set, by that role.

**Tasks**
- [ ] Ranking function using the matcher output
- [ ] Target-role similarity

**Effort:** 1 pt / XS

#### F3-S2b: Exclusions, Pagination and Caching

**As a** talent, **I want** a clean, fast list, **so that** I don't see jobs I can't use.

**Acceptance criteria**
- Given closed, skipped or already applied jobs, then they are excluded.
- Given many jobs, then the list is paginated and cached, and refreshed when the profile or jobs change.

**Tasks**
- [ ] Exclusion filters
- [ ] Pagination
- [ ] Cache and invalidation

**Effort:** 1 pt / XS

#### F3-S2c: Home List and Empty States

**As a** talent, **I want** helpful messages when nothing shows, **so that** I know what to do next.

**Acceptance criteria**
- Given no profile, then the talent is prompted to complete it.
- Given no matches, then a helpful empty state is shown.

**Tasks**
- [ ] List UI
- [ ] Empty states
- [ ] Loading state

**Effort:** 1 pt / XS

### F3-S3: Job Shortlist Cards

**As a** talent, **I want** a scannable shortlist, **so that** I can compare jobs quickly.

**Acceptance criteria (whole story)**
- Given the recommendation list, then each job shows a description summary, the skill gap or percentage match, and the open and close dates.
- Given a job card, then skip, bookmark and report actions are available.
- Given a card, when clicked, then the job detail opens.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F3-S2

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S3a: Card Content

**As a** talent, **I want** each job summarised, **so that** I can compare quickly.

**Acceptance criteria**
- Given the list, then each card shows a description summary, the skill gap or percentage match, and the open and close dates.

**Tasks**
- [ ] Card component
- [ ] Date formatting
- [ ] Match summary display

**Effort:** 1 pt / XS

#### F3-S3b: Card Actions and Navigation

**As a** talent, **I want** to act on a job from the list, **so that** I save time.

**Acceptance criteria**
- Given a card, then skip, bookmark and report are available, and clicking it opens the job detail.
- Given a percentage, then it is also shown as text, not only colour.

**Tasks**
- [ ] Action buttons
- [ ] Click-through to detail
- [ ] Text labels

**Effort:** 1 pt / XS

### F3-S4: Job Detail with Skill Breakdown

**As a** talent, **I want** to see the full job and my skill gaps, **so that** I can decide whether to apply.

**Acceptance criteria (whole story)**
- Given a job, when opened, then the full description and the detailed skill match breakdown are shown, with the percentage and which skills are gaps.
- Given the detail page, then apply, skip, bookmark and report are available, placed at the bottom right of the page.
- Given a job that closes while the talent views it, then apply is disabled with a clear message.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F3-S1

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S4a: Detail Page and Description

**As a** talent, **I want** the full job description, **so that** I can judge the role.

**Acceptance criteria**
- Given a job, when opened, then the full description is shown.

**Tasks**
- [ ] Detail route and endpoint
- [ ] Page layout

**Effort:** 1 pt / XS

#### F3-S4b: Skill Breakdown with Gaps

**As a** talent, **I want** to see my skill gaps, **so that** I know what I'm missing.

**Acceptance criteria**
- Given a job, then the detailed skill match breakdown is shown with the percentage and which skills are gaps.

**Tasks**
- [ ] Breakdown component
- [ ] Gap highlighting
- [ ] Text labels, not only colour

**Effort:** 1 pt / XS

#### F3-S4c: Bottom-right Actions and Closed-job State

**As a** talent, **I want** clear actions in a consistent place, **so that** I can decide quickly.

**Acceptance criteria**
- Given the page, then apply, skip, bookmark and report sit at the bottom right.
- Given a job that closes while viewed, then apply is disabled with a clear message.

**Tasks**
- [ ] Action bar at the bottom right
- [ ] Closed-job check
- [ ] Message

**Effort:** 1 pt / XS

### F3-S5: Skip and Bookmark with Bookmark List

**As a** talent, **I want** to hide jobs I don't want and save ones I do, **so that** my list stays relevant.

**Acceptance criteria (whole story)**
- Given a job, when the talent skips it, then it is hidden from their lists.
- Given a job, when the talent bookmarks it, then it appears in the bookmark list, and bookmarking again does nothing new.
- Given the bookmark list, then it shows saved jobs as a shortlist, and clicking one opens the same job detail page. A bookmark can be removed.
- Given skip or bookmark on the shortlist or the detail page, then the same action applies.

**Definition of Done:** standard, plus actions idempotent.
**Priority:** High | **Complexity:** Low | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F3-S3, F3-S4

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S5a: Skip Action

**As a** talent, **I want** to hide jobs I don't want, **so that** my list stays relevant.

**Acceptance criteria**
- Given a job, when skipped, then it is hidden from the talent's lists. Skipping again changes nothing.

**Tasks**
- [ ] Skip table and endpoint
- [ ] Filter in list queries

**Effort:** 1 pt / XS

#### F3-S5b: Bookmark Action

**As a** talent, **I want** to save jobs, **so that** I can come back to them.

**Acceptance criteria**
- Given a job, when bookmarked, then it is saved. Bookmarking again creates no duplicate, and a bookmark can be removed.

**Tasks**
- [ ] Bookmark table and endpoint
- [ ] Toggle UI

**Effort:** 1 pt / XS

#### F3-S5c: Bookmark List Page

**As a** talent, **I want** a list of my saved jobs, **so that** I can review them.

**Acceptance criteria**
- Given saved jobs, then the page shows them as a shortlist, and clicking one opens the same job detail page.

**Tasks**
- [ ] List page
- [ ] Reuse the job card
- [ ] Empty state

**Effort:** 1 pt / XS

### F3-S6: Report a Wrong Recommendation

**As a** talent, **I want** to report a wrong recommendation, **so that** the platform can improve.

**Acceptance criteria (whole story)**
- Given a job on the shortlist or detail page, when the talent reports it with an optional reason, then a report record is stored.
- Given a report, then the talent sees a confirmation.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** No
**Dependencies:** Story: F3-S3. Review tooling for reports is in the backlog.

**Tasks** (1 point, so not split further)
- [ ] Report table and endpoint
- [ ] Report button on the card and the detail page, with an optional reason
- [ ] Confirmation message

### F3-S7: Similar Jobs Suggestion

**As a** talent, **I want** to see similar jobs, **so that** I can keep exploring.

**Acceptance criteria (whole story)**
- Given a job detail page, then a list of similar open jobs is shown.
- Given no similar jobs, then the section is hidden.

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F3-S4. Decision (non-blocking): how similarity is calculated. Default: shared required skills.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F3-S7a: Similarity Query

**As a** talent, **I want** related jobs found, **so that** I can keep exploring.

**Acceptance criteria**
- Given a job, then similar open jobs are found by shared required skills, excluding the job itself.

**Tasks**
- [ ] Similarity function
- [ ] Result limit

**Effort:** 1 pt / XS

#### F3-S7b: Similar Jobs Section

**As a** talent, **I want** a similar jobs section on the detail page, **so that** I can browse on.

**Acceptance criteria**
- Given similar jobs, then the section is shown. Given none, then it is hidden.

**Tasks**
- [ ] Section component
- [ ] Hide-when-empty behaviour

**Effort:** 1 pt / XS

---

# Feature 4: Transparent Applications and Status Tracking

### F4-S1: Review Step and Submit Application

**As a** talent, **I want** to review what I'm sending before I apply, **so that** I stay in control.

**Acceptance criteria (whole story)**
- Given the apply action, when clicked, then a review step shows exactly what will be sent: the translated profile only, never the original CV.
- Given the review step, when the talent submits, then an application is created with status Applied and a frozen copy of the translated profile.
- Given submit, then a success screen prompts the talent to track the application and links to the tracking view.
- Given a job already applied to or closed, when applying, then the system blocks it with a clear message.

**Definition of Done:** standard, plus the frozen snapshot verified.
**Priority:** High | **Complexity:** Medium | **Effort:** 4 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F2-S4, F3-S4. Data: application table.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S1a: Review Screen

**As a** talent, **I want** to see exactly what I'm sending before I apply, **so that** I stay in control.

**Acceptance criteria**
- Given the apply action, when clicked, then a review step shows the translated profile that will be sent.
- Given the review step, then the original CV is neither shown nor sent.
- Given the talent wants to change something, then they can go back to edit before submitting.

**Technical tasks**
- [ ] Review screen reading the translated snapshot record (F2-S4c)
- [ ] Back to edit navigation

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4c, F3-S4

#### F4-S1b: Submit with Frozen Snapshot and Guards

**As a** talent, **I want** my application recorded exactly as I reviewed it, **so that** nothing changes after I submit.

**Acceptance criteria**
- Given the review step, when the talent submits, then an application is created with status Applied and a frozen copy of the translated profile.
- Given a job the talent already applied to, or a closed job, then the system blocks it with a clear message.
- Given a double click on submit, then only one application is created.

**Technical tasks**
- [ ] Application table with the snapshot stored on it
- [ ] Unique constraint on job and talent
- [ ] Single transaction for the create
- [ ] Tests for duplicate and closed-job cases

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F4-S1a. Data: application table.

#### F4-S1c: Success Screen with Tracking Link

**As a** talent, **I want** confirmation that my application went through, **so that** I know it worked.

**Acceptance criteria**
- Given a successful submit, then a success screen prompts the talent to track the status and links to the tracking view for this application.
- Given a failed submit, then an error is shown, never the success screen.

**Technical tasks**
- [ ] Success screen
- [ ] Link to the tracking view (F4-S3)

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F4-S1b, F4-S3

### F4-S2: Application List with Status Ribbon

**As a** talent, **I want** a list of my applications with their status, **so that** I can see where each one stands.

**Acceptance criteria (whole story)**
- Given a talent's applications, then the list shows each applied job as a shortlist with its current status as a ribbon in the top right corner.
- Given a status, then it is also shown as text, not only in the ribbon.
- Given no applications, then a helpful empty state is shown.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F4-S1. Decision (non-blocking): ribbon look. Default: text labels, no colour coding.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S2a: List Endpoint and Cards

**As a** talent, **I want** a list of my applications, **so that** I can see where each stands.

**Acceptance criteria**
- Given a talent's applications, then the list shows each applied job with its current status, and only their own.

**Tasks**
- [ ] List endpoint
- [ ] Application card
- [ ] Ownership check

**Effort:** 1 pt / XS

#### F4-S2b: Status Ribbon and Empty State

**As a** talent, **I want** the status visible at a glance, **so that** I don't open each one.

**Acceptance criteria**
- Given an application, then its status is shown as a ribbon in the top right corner and also as text.
- Given no applications, then a helpful empty state is shown.

**Tasks**
- [ ] Ribbon component
- [ ] Empty state

**Effort:** 1 pt / XS

### F4-S3: Status Tracking View

**As a** talent, **I want** to see the status and my submitted application, **so that** I know what the employer sees.

**Acceptance criteria (whole story)**
- Given an application, when the talent opens it from the list or the success screen, then the same tracking view shows the current status, the status history and the submitted application.
- Given a talent, then they can only open their own applications.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F4-S1, F4-S2. Decision (non-blocking): cancel or withdraw, which is tentative. Not included in this story.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S3a: History and Submitted Application Display

**As a** talent, **I want** to see my status history and what I submitted, **so that** I know what the employer sees.

**Acceptance criteria**
- Given an application, then the tracking view shows the current status, the status history and the submitted application.

**Tasks**
- [ ] Tracking endpoint
- [ ] History list
- [ ] Snapshot display

**Effort:** 1 pt / XS

#### F4-S3b: Access Control and Entry Points

**As a** talent, **I want** to reach the tracking view easily and safely, **so that** only I can see it.

**Acceptance criteria**
- Given an application, then only its owner can open it, and it opens from both the success screen and the application list.

**Tasks**
- [ ] Ownership check
- [ ] Links from both entry points

**Effort:** 1 pt / XS

### F4-S4: Edit Window Until Review

**As a** talent, **I want** to edit my application until the employer starts reviewing, **so that** I can fix mistakes.

**Acceptance criteria (whole story)**
- Given an application with status Applied, when the talent edits and saves it, then the change is stored.
- Given an application at Review or later, when the talent tries to edit, then the server rejects it with a clear message.
- Given the status changes while the talent is editing, then the save is rejected and the talent is told why.

**Definition of Done:** standard, plus the lock tested on the server.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F4-S1, F6-S4

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S4a: Edit Endpoint with Status Lock

**As a** talent, **I want** to edit until review starts, **so that** I can fix mistakes.

**Acceptance criteria**
- Given an application at Applied, when the talent edits and saves, then the change is stored.
- Given Review or later, then the server rejects the edit with a clear message.

**Tasks**
- [ ] Lock check
- [ ] Edit endpoint
- [ ] Error message

**Effort:** 1 pt / XS

#### F4-S4b: Concurrent Change Handling

**As a** talent, **I want** to be told if the status changed while I edited, **so that** I'm not surprised.

**Acceptance criteria**
- Given the status changes while the talent is editing, then the save is rejected and the talent is told why.

**Tasks**
- [ ] Version field
- [ ] Conflict response
- [ ] UI message
- [ ] Test the race

**Effort:** 1 pt / XS

### F4-S5: Interview Slot Selection

**As a** talent, **I want** to pick an interview time from the employer's slots, **so that** we agree a time.

**Acceptance criteria (whole story)**
- Given the employer has offered slots, when the talent opens the application, then the slots are shown.
- Given the slots, when the talent picks and confirms one, then it is saved and the employer is notified.
- Given a slot taken in the meantime, then the talent is asked to choose another.
- Times are stored in UTC and shown in the user's time zone.

**Definition of Done:** standard, plus double booking prevented.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F4-S3, F6-S5. Decision (non-blocking): what happens when no slot fits. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S5a: Show Offered Slots

**As a** talent, **I want** to see the interview times offered, **so that** I can choose.

**Acceptance criteria**
- Given offered slots, when the talent opens the application, then the slots are shown in their time zone.

**Tasks**
- [ ] Slot list endpoint
- [ ] Display in the tracking view
- [ ] Time zone display

**Effort:** 1 pt / XS

#### F4-S5b: Pick and Confirm

**As a** talent, **I want** to pick and confirm a slot, **so that** we agree a time.

**Acceptance criteria**
- Given the slots, when the talent picks and confirms one, then it is saved and the employer is notified.
- Given one slot, then it cannot be booked twice.

**Tasks**
- [ ] Pick endpoint
- [ ] Uniqueness constraint
- [ ] Notification event

**Effort:** 1 pt / XS

#### F4-S5c: Stale Slot Handling

**As a** talent, **I want** a clear message if my slot is gone, **so that** I can choose another.

**Acceptance criteria**
- Given a slot taken in the meantime, then the talent is asked to choose another. Times are stored in UTC.

**Tasks**
- [ ] Conflict response
- [ ] Re-pick UI
- [ ] UTC storage

**Effort:** 1 pt / XS

### F4-S6: Result and Offer Reply

**As a** talent, **I want** to see my result and answer an offer, **so that** the process finishes clearly.

**Acceptance criteria (whole story)**
- Given the employer sets a result, then the talent sees it in the tracking view and is notified.
- Given an accepted result with an offer, when the talent accepts, then the application moves to Confirmed.
- Given an offer, when the talent rejects it, then the application moves to Rejected.

**Definition of Done:** standard, plus transitions tested.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F4-S3, F6-S6. Decision (non-blocking): offer expiry and where rejected applications are shown. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S6a: Result Display

**As a** talent, **I want** to see my result, **so that** I know the outcome.

**Acceptance criteria**
- Given the employer sets a result, then the talent sees it in the tracking view and is notified.

**Tasks**
- [ ] Result field
- [ ] Display
- [ ] Notification event

**Effort:** 1 pt / XS

#### F4-S6b: Offer View and Accept

**As a** talent, **I want** to see an offer and accept it, **so that** I can confirm the job.

**Acceptance criteria**
- Given an accepted result with an offer, then the offer is shown. When the talent accepts, then the application moves to Confirmed.

**Tasks**
- [ ] Offer view
- [ ] Accept endpoint
- [ ] Status transition

**Effort:** 1 pt / XS

#### F4-S6c: Reject Offer

**As a** talent, **I want** to turn an offer down, **so that** the process closes clearly.

**Acceptance criteria**
- Given an offer, when the talent rejects it, then the application moves to Rejected.

**Tasks**
- [ ] Reject endpoint
- [ ] Status transition
- [ ] Test

**Effort:** 1 pt / XS

### F4-S7: Talent Feedback

**As a** talent, **I want** to give feedback at the end, **so that** the employer and the team learn from my experience.

**Acceptance criteria (whole story)**
- Given an application that has ended (Confirmed or Rejected), then a feedback form is available.
- Given the form, when submitted, then it is stored once per application, with one part for the employer and one for the development team.

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F4-S6. Decision (non-blocking): when feedback is released to the other party. Default: stored only, delivered later.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S7a: Feedback Form

**As a** talent, **I want** a feedback form at the end, **so that** I can share my experience.

**Acceptance criteria**
- Given an application that has ended, then a form is available with one part for the employer and one for the development team.

**Tasks**
- [ ] Form with two parts
- [ ] Access rule

**Effort:** 1 pt / XS

#### F4-S7b: Storage and One-per-application Rule

**As a** platform owner, **I want** feedback stored once per application, **so that** it stays clean.

**Acceptance criteria**
- Given a submitted form, then it is stored once per application and the talent sees a confirmation.

**Tasks**
- [ ] Feedback table
- [ ] Uniqueness constraint
- [ ] Confirmation

**Effort:** 1 pt / XS

### F4-S8: Your Activity on the Talent Home Page

**As a** talent, **I want** to see what is active at the top of my home page, **so that** I know what needs my attention.

**Acceptance criteria (whole story)**
- Given a talent with applications in progress, when they open the home page, then a "Your activity" component at the top shows only active items (for example applications in progress, interviews to confirm and offers to answer).
- Given items that have ended, then they are not shown in this component.
- Given a talent with nothing active, then a helpful empty state links to the recommended jobs.
- Given the home page, then there are no KPI cards.
- Given an item, when clicked, then the tracking view opens (F4-S3).

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F4-S2, F4-S3. Decision (non-blocking): which statuses count as active. Default: Applied, Review, Interview, Accepted, Offer.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F4-S8a: Active Items Query

**As a** talent, **I want** the active items found, **so that** the top of my home page is useful.

**Acceptance criteria**
- Given a talent's applications, then only active ones are returned (Applied, Review, Interview, Accepted, Offer).

**Tasks**
- [ ] Query
- [ ] Active status set kept in configuration

**Effort:** 1 pt / XS

#### F4-S8b: Component and Empty State

**As a** talent, **I want** a Your activity component at the top, **so that** I see what needs me.

**Acceptance criteria**
- Given active items, then the component shows them at the top, and there are no KPI cards.
- Given nothing active, then an empty state links to the recommended jobs. Clicking an item opens the tracking view.

**Tasks**
- [ ] Component
- [ ] Remove the KPI cards
- [ ] Empty state

**Effort:** 1 pt / XS

---

# Feature 5: Anonymous Talent Discovery for Employers

### F5-S1: Anonymization Layer

**As an** employer, **I want** talents shown without identifying details, **so that** I judge on skills alone.

**Acceptance criteria (whole story)**
- Given any employer-facing talent response, then name, origin, ethnicity, nationality, gender and contact details are never included.
- Given any employer endpoint, then the original CV is never returned.
- Given the fields, then an allowlist decides what is returned, not a list of hidden fields.
- Given all employer endpoints, then an automated test confirms no personal field appears.

**Definition of Done:** standard, plus the test runs in the build pipeline.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F1-S2, F2-S4. Decision (non-blocking): whether to also hide employer and university names, age and photos. Default: allowlist excludes them.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F5-S1a: Employer-Safe Talent Projection

**As an** employer, **I want** talents shown without identifying details, **so that** I judge on skills alone.

**Acceptance criteria**
- Given any employer-facing talent response, then it is built from an allowlist: alias, translated role, translated skills and the match.
- Given any employer response, then name, origin, ethnicity, nationality, gender and contact details are never included, and the original CV is never returned.
- Given free text in the translated profile, then emails and phone numbers are removed (proposed pattern check).

**Technical tasks**
- [ ] Projection function used by every employer talent endpoint
- [ ] Pattern check for emails and phone numbers in free text
- [ ] Unit tests

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F1-S2, F2-S4c. Decision (non-blocking): whether to also hide employer and university names, age and photos. Default: not in the allowlist.

#### F5-S1b: Automated Personal-Data Test

**As a** platform owner, **I want** a test that catches personal data leaking to employers, **so that** the anonymity promise is verified.

**Acceptance criteria**
- Given a seeded talent with known personal values, when every employer endpoint is called, then the test fails if any of those values appear in any response.
- Given the build, then this test runs on every build.

**Technical tasks**
- [ ] Seed a talent with known personal values
- [ ] Test that loops over all employer endpoints
- [ ] Add it to the build pipeline

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F5-S1a

### F5-S2: Employer Talent Shortlist

**As an** employer, **I want** a shortlist of potential talents by alias, **so that** I can review people quickly.

**Acceptance criteria (whole story)**
- Given the employer home page, then a shortlist of talents is shown by alias.
- Given the basic tier, then only the top N talents are shown. N is configurable.
- Given a talent the employer skipped, then they don't appear again.
- Given no talents, then a helpful empty state is shown.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F5-S1, F3-S1. Decision (non-blocking): value of N, ordering, and talent opt-in. Default: N = 10, ordered by skill coverage.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F5-S2a: Shortlist Query by Alias

**As an** employer, **I want** potential talent listed by alias, **so that** I review on skills only.

**Acceptance criteria**
- Given the employer home page, then talents are listed by alias, ordered by skill coverage, through the anonymization layer.

**Tasks**
- [ ] Query through the projection
- [ ] Ordering by skill coverage

**Effort:** 1 pt / XS

#### F5-S2b: Top N and Skipped Exclusion

**As an** employer, **I want** a focused list, **so that** I'm not overwhelmed.

**Acceptance criteria**
- Given the basic plan, then only the top N talents are shown, and N is configurable.
- Given a talent the employer skipped, then they do not appear again.

**Tasks**
- [ ] Configurable N
- [ ] Skip exclusion
- [ ] Plan hook for premium

**Effort:** 1 pt / XS

#### F5-S2c: Shortlist UI and Empty State

**As an** employer, **I want** a clear list, **so that** I can scan it quickly.

**Acceptance criteria**
- Given the list, then each talent shows as a card by alias. Given no talents, then a helpful empty state is shown.

**Tasks**
- [ ] List page
- [ ] Card
- [ ] Empty state

**Effort:** 1 pt / XS

### F5-S3: Talent Detail

**As an** employer, **I want** to open a talent and see their translated profile and match, **so that** I can judge fit.

**Acceptance criteria (whole story)**
- Given a talent, when opened, then the detail page shows the translated profile and the per-skill match.
- Given the detail page, then no person-level score is shown.
- Given the detail page, then contact details stay hidden, and contact happens through the platform.

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F5-S1, F5-S2

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F5-S3a: Detail Endpoint through Projection

**As an** employer, **I want** a talent's detail returned safely, **so that** no personal data leaks.

**Acceptance criteria**
- Given a talent, then the endpoint returns only allowlisted fields and the per-skill match.

**Tasks**
- [ ] Endpoint via the projection
- [ ] Call the matcher
- [ ] Hook for the profile watch event

**Effort:** 1 pt / XS

#### F5-S3b: Detail Page

**As an** employer, **I want** to read the translated profile and match, **so that** I can judge fit.

**Acceptance criteria**
- Given the page, then it shows the translated profile and the per-skill match, with no person-level score and contact details hidden.

**Tasks**
- [ ] Page layout
- [ ] Per-skill view
- [ ] No score

**Effort:** 1 pt / XS

### F5-S4: Save and Skip Talent

**As an** employer, **I want** to save talents I like and hide ones I don't, **so that** my shortlist stays useful.

**Acceptance criteria (whole story)**
- Given a talent on the shortlist or detail page, when the employer saves, then the talent is added to their saved list.
- Given a talent, when the employer skips, then they are hidden from this employer's shortlist.
- Given either action, then it can be undone from the saved list or settings. Repeating the action creates no duplicates.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F5-S2, F5-S3

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F5-S4a: Save Talent and Saved List

**As an** employer, **I want** to save talent I like, **so that** I can return to them.

**Acceptance criteria**
- Given a talent on the shortlist or detail page, when saved, then they appear in the saved list with no duplicates.

**Tasks**
- [ ] Save table and endpoint
- [ ] Saved list page

**Effort:** 1 pt / XS

#### F5-S4b: Skip and Undo

**As an** employer, **I want** to hide talent I don't want and undo it, **so that** mistakes can be fixed.

**Acceptance criteria**
- Given a talent, when skipped, then they are hidden from this employer's shortlist. The skip can be undone.

**Tasks**
- [ ] Skip table
- [ ] Filter
- [ ] Undo action

**Effort:** 1 pt / XS

### F5-S5: Report a Wrong Talent

**As an** employer, **I want** to report a wrongly recommended talent, **so that** recommendations improve.

**Acceptance criteria (whole story)**
- Given a talent on the shortlist or detail page, when the employer reports with an optional reason, then a report record is stored.
- Given a report, then the employer sees a confirmation.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** No
**Dependencies:** Story: F5-S2. Review tooling for reports is in the backlog.

**Tasks** (1 point, so not split further)
- [ ] Report table and endpoint
- [ ] Report button on the shortlist and the detail page, with an optional reason
- [ ] Confirmation message

---

# Feature 6: Streamlined Job Posting and Hiring Pipeline

### F6-S1: Post a Job

**As an** employer, **I want** to post a job with a target and a close date, **so that** talents can find and apply to it.

**Acceptance criteria (whole story)**
- Given a signed-in employer, when they post a job with a description, a target number of applicants and a close date, then the job is created as Open.
- Given a close date in the past or a target that isn't a positive number, then the form shows a clear error.
- Given an employer on the basic plan who already has 50 open jobs, when they post another, then it is blocked with an upgrade prompt. Closed jobs do not count, and premium has no limit (assumed).
- Given a posted job, then its required skills are available for matching.

**Definition of Done:** standard, plus 10 to 15 seeded jobs loaded for the demo.
**Priority:** High | **Complexity:** Medium | **Effort:** 6 pts (sum of the sub-stories below) | **Demo slice:** Yes for F6-S1a to S1c, No for F6-S1d
**Dependencies:** Story: F1-S4. System: LLM API (skill extraction). Decision (non-blocking): how job skills are produced. Default: AI-extracted and editable by the employer.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S1a: Post-a-Job Form and Validation

**As an** employer, **I want** to post a job with a target and a close date, **so that** talents can find it.

**Acceptance criteria**
- Given a signed-in employer, when they post a job with a title, description, target number of applicants and close date, then the job is created as Open.
- Given a close date in the past or a target that isn't a positive number, then the form shows a clear error.
- Given an employer on the basic plan who already has 50 open jobs, when they post another, then it is blocked with an upgrade prompt. Closed jobs do not count, and premium has no limit (assumed).

**Technical tasks**
- [ ] Form and validation
- [ ] Job table and create endpoint

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F1-S4

#### F6-S1b: AI Required-Skill Extraction

**As an** employer, **I want** the required skills drawn from my description, **so that** matching works without extra typing.

**Acceptance criteria**
- Given a job description, when the employer saves it, then required skills are proposed.
- Given the proposed skills, then the employer can edit, add or remove them before the job goes live.
- Given extraction fails, then the employer can enter the skills manually.

**Technical tasks**
- [ ] Extraction prompt with a schema and validation
- [ ] Editable skills list
- [ ] Manual fallback

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F6-S1a. System: LLM API. Decision (non-blocking): AI-extracted or employer-tagged. Default: AI-extracted and editable.

#### F6-S1c: Seed Demo Jobs

**As a** team member, **I want** realistic jobs ready for the demo, **so that** recommendations and badges can be shown.

**Acceptance criteria**
- Given the seed script, when it runs, then 10 to 15 synthetic jobs are created across 2 to 3 industries, each with required skills and a target.
- Given the seeded jobs, then close dates vary so the demo shows open, closing within a week, and closed jobs.
- Given the script runs twice, then it creates no duplicates.

**Technical tasks**
- [ ] Seed data file
- [ ] Idempotent seed script

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S1b

#### F6-S1d: Post a Job from a PDF

**As an** employer, **I want** to upload a PDF of a job description, **so that** I don't have to retype it.

**Acceptance criteria**
- Given a signed-in employer, when they upload a PDF job description (type and size checked), then the text is extracted and the AI fills in the title, description and required skills.
- Given the filled form, then the employer reviews and edits it before posting, and nothing is posted automatically.
- Given a PDF that can't be read, then the employer sees a clear error and can fill in the form manually.
- Given a basic employer who already has 50 open jobs, then posting is blocked as in F6-S1a.

**Definition of Done:** standard, plus tested with 2 sample job description PDFs.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** No
**Dependencies:** Story: F6-S1a, F6-S1b. Reuses the text extraction from F2-S2a.

### F6-S2: My Jobs List, Badges and Auto-close

**As an** employer, **I want** to see my jobs against their targets, **so that** I know what needs attention.

**Acceptance criteria (whole story)**
- Given the My jobs list, then each job shows the target against the current applicant count (for example target 100, current 200) and the close date.
- Given a job, then a badge shows green when open, yellow when less than one week remains, and red when closed or overdue, each with a text label.
- Given the close date passes, then the job changes to Closed automatically and its applications are kept.
- Given an employer, then they only see their own jobs.

**Definition of Done:** standard, plus badge logic tested at the one-week boundary.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F6-S1. System: scheduled job. Decision (non-blocking): pending applications at close. Default: kept for the employer to decide, no automatic rejection.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S2a: List with Target vs Current

**As an** employer, **I want** my jobs against their targets, **so that** I see progress.

**Acceptance criteria**
- Given the My jobs list, then each job shows the target against the current applicant count and the close date, for the employer's own jobs only.

**Tasks**
- [ ] List endpoint with counts
- [ ] Ownership check

**Effort:** 1 pt / XS

#### F6-S2b: Badge Logic

**As an** employer, **I want** a clear close-date badge, **so that** I know what needs attention.

**Acceptance criteria**
- Given a job, then the badge is green when open, yellow with less than one week left, and red when closed or overdue, each with a text label.

**Tasks**
- [ ] Badge function
- [ ] Unit tests at the one-week boundary
- [ ] Text label

**Effort:** 1 pt / XS

#### F6-S2c: Auto-close Job

**As an** employer, **I want** jobs to close on their date, **so that** I don't have to.

**Acceptance criteria**
- Given the close date passes, then the job becomes Closed automatically and its applications are kept.

**Tasks**
- [ ] Scheduled job
- [ ] Status change
- [ ] Test

**Effort:** 1 pt / XS

### F6-S3: Applications View and Profile Review

**As an** employer, **I want** to see a job's applicants and review their profiles, **so that** I can decide who to move forward.

**Acceptance criteria (whole story)**
- Given one of their jobs, when the employer opens it, then its applications are listed by alias with the match summary and current status.
- Given an application, when opened, then the employer sees the submitted translated profile and the per-skill match, like the talent detail page.
- Given an employer, then they can only open applications for their own jobs.

**Definition of Done:** standard, plus the anonymization layer applied.
**Priority:** High | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F6-S2, F5-S1, F4-S1

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S3a: Applications List per Job

**As an** employer, **I want** a job's applicants listed, **so that** I can work through them.

**Acceptance criteria**
- Given one of their jobs, then applications are listed by alias with the match summary and current status.

**Tasks**
- [ ] Endpoint
- [ ] List UI

**Effort:** 1 pt / XS

#### F6-S3b: Profile Review with Match

**As an** employer, **I want** to open an applicant, **so that** I can judge them on skills.

**Acceptance criteria**
- Given an application, when opened, then the submitted translated profile and the per-skill match are shown.

**Tasks**
- [ ] Detail view
- [ ] Match display

**Effort:** 1 pt / XS

#### F6-S3c: Ownership and Anonymization

**As an** employer, **I want** only my own jobs' applicants, shown anonymously, **so that** data stays safe.

**Acceptance criteria**
- Given an employer, then they can only open applications for their own jobs, and the anonymization layer is applied.

**Tasks**
- [ ] Ownership check
- [ ] Use the projection
- [ ] Test

**Effort:** 1 pt / XS

### F6-S4: Status Updates and Edit Lock

**As an** employer, **I want** to move applications through the process, **so that** every decision is mine.

**Acceptance criteria (whole story)**
- Given an application, when the employer moves it forward, then only valid transitions are accepted (Applied, Review, Interview, Accepted or Rejected, Offer, Confirmed). Invalid ones return a clear error.
- Given the move to Review, then the talent's edit window locks.
- Given any change, then it is logged with who made it and when.
- Given any application, then the system never changes its status on its own.

**Definition of Done:** standard, plus tests for every valid and invalid transition.
**Priority:** High | **Complexity:** Medium | **Effort:** 4 pts (sum of the sub-stories below) | **Demo slice:** Yes
**Dependencies:** Story: F6-S3. Data: application status history.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S4a: Status Transition Rules and History

**As an** employer, **I want** only valid status moves, **so that** the process stays consistent.

**Acceptance criteria**
- Given an application, when the employer moves it, then only these transitions are accepted: Applied to Review, Review to Interview, Interview to Accepted or Rejected, Accepted to Offer, Offer to Confirmed, and Offer to Rejected when the talent rejects it. Anything else returns a clear error.
- Given any change, then it is logged with who made it and when.
- Given any application, then the system never changes its status on its own.

**Technical tasks**
- [ ] Transition table in one place
- [ ] Status history table
- [ ] Tests for every valid and invalid pair

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F6-S3. Data: application status history.

#### F6-S4b: Edit Lock on Review

**As a** talent, **I want** to know when I can no longer edit, **so that** I'm not surprised.

**Acceptance criteria**
- Given the employer moves an application to Review, then the talent's edit window locks.
- Given a locked application, when the talent tries to edit, then the server rejects it with a clear message (see F4-S4).
- Given an edit already in progress, then it is rejected at save time with an explanation.

**Technical tasks**
- [ ] Lock check on the edit endpoint
- [ ] Version check for edits in progress
- [ ] Test the race case

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S4a, F4-S4

#### F6-S4c: Employer Status Controls

**As an** employer, **I want** clear controls for the next step, **so that** I move talents through quickly and safely.

**Acceptance criteria**
- Given an application in the applications view, then only the allowed next actions are shown.
- Given a Reject action, then the employer confirms before it is applied.
- Given a status change, then the new status is shown immediately.

**Technical tasks**
- [ ] Action buttons driven by the transition table
- [ ] Confirmation for rejection
- [ ] Immediate UI update

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S4a

### F6-S5: Interview Scheduling

**As an** employer, **I want** to offer interview times and see the talent's choice, **so that** we agree a time.

**Acceptance criteria (whole story)**
- Given an application in Interview, when the employer offers one or more time slots, then the talent sees them.
- Given a talent's pick, then the employer sees it and confirms.
- Given a slot already taken, then it can't be offered twice.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F6-S4, F4-S5. Decision (non-blocking): rescheduling when no slot fits. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S5a: Offer Slots

**As an** employer, **I want** to offer interview times, **so that** the talent can choose.

**Acceptance criteria**
- Given an application in Interview, when the employer offers one or more slots, then the talent sees them.

**Tasks**
- [ ] Slot creation form
- [ ] Endpoint
- [ ] Notification event to the talent

**Effort:** 1 pt / XS

#### F6-S5b: See Pick and Confirm

**As an** employer, **I want** to see the pick and confirm it, **so that** the time is agreed.

**Acceptance criteria**
- Given the talent's pick, then the employer sees it and confirms.

**Tasks**
- [ ] Pick display
- [ ] Confirm endpoint

**Effort:** 1 pt / XS

#### F6-S5c: Slot Conflicts and Cancellation

**As an** employer, **I want** slots to stay consistent, **so that** nobody is double booked.

**Acceptance criteria**
- Given a slot already taken, then it cannot be offered twice, and a slot can be cancelled with the talent notified.

**Tasks**
- [ ] Uniqueness
- [ ] Cancel endpoint
- [ ] Notification

**Effort:** 1 pt / XS

### F6-S6: Result, Offer and Employer Feedback

**As an** employer, **I want** to record the result, send an offer and give feedback, **so that** the process closes properly.

**Acceptance criteria (whole story)**
- Given an interview, when the employer sets Accepted or Rejected, then the talent sees the result.
- Given an accepted application, when the employer sends an offer, then the talent can reply. An accepted reply moves it to Confirmed.
- Given an ended application, then a feedback form is available for the talent and for the development team.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F6-S4, F4-S6. Decision (non-blocking): offer expiry. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S6a: Set Result

**As an** employer, **I want** to record the result, **so that** the talent knows the outcome.

**Acceptance criteria**
- Given an interview, when the employer sets Accepted or Rejected, then the talent sees the result.

**Tasks**
- [ ] Result endpoint
- [ ] Status transition
- [ ] Event

**Effort:** 1 pt / XS

#### F6-S6b: Send Offer and See Reply

**As an** employer, **I want** to send an offer and see the reply, **so that** I can confirm the hire.

**Acceptance criteria**
- Given an accepted application, when the employer sends an offer, then the talent can reply. An accepted reply moves it to Confirmed and a rejected one to Rejected.

**Tasks**
- [ ] Offer table
- [ ] Send endpoint
- [ ] Reply handling

**Effort:** 1 pt / XS

#### F6-S6c: Employer Feedback Form

**As an** employer, **I want** to give feedback at the end, **so that** the talent and the team learn from it.

**Acceptance criteria**
- Given an ended application, then a feedback form is available for the talent and for the development team.

**Tasks**
- [ ] Form
- [ ] Reuse the feedback table

**Effort:** 1 pt / XS

### F6-S7: Edit a Job

**As an** employer, **I want** to edit a posted job, **so that** the posting stays accurate.

**Acceptance criteria (whole story)**
- Given one of their jobs, when the employer edits the description, skills, target or close date, then the changes are saved and a change history is kept.
- Given an edit, then a notification event is created for everyone who applied (delivery in F7-S2).
- Given a close date moved forward on a closed job, then the badge updates.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F6-S1. Decision (non-blocking): whether a major edit re-runs the skill match. Default: no re-run.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F6-S7a: Edit Form and History

**As an** employer, **I want** to edit a posted job, **so that** the posting stays accurate.

**Acceptance criteria**
- Given one of their jobs, when the employer edits the description, skills, target or close date, then the changes are saved and a history is kept, and the badge updates.

**Tasks**
- [ ] Edit form
- [ ] History table
- [ ] Badge recalculation

**Effort:** 1 pt / XS

#### F6-S7b: Applicant Notification Event

**As an** employer, **I want** applicants told of changes, **so that** nobody is surprised.

**Acceptance criteria**
- Given a saved edit, then a notification event is created for everyone who applied (delivery in F7-S2).

**Tasks**
- [ ] Event on save
- [ ] Applicants query
- [ ] Hand-off to F7-S2

**Effort:** 1 pt / XS

---

# Feature 7: Timely Alerts, Insights and Premium Access

### F7-S1: Notification Service

**As a** platform owner, **I want** reliable notifications, **so that** users hear about important events.

**Acceptance criteria (whole story)**
- Given an event, then a notification record is created and sent through the email channel with a template for its type.
- Given an email that fails, then it is retried and never blocks the action that triggered it.
- Given one event, then at most one notification is sent.

**Definition of Done:** standard, plus an outbox so failures can be retried.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** System: email sending service. Decision (non-blocking): email only or also in-app. Default: email only.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S1a: Notification Records and Templates

**As a** platform owner, **I want** notifications recorded with templates, **so that** messages are consistent.

**Acceptance criteria**
- Given an event, then a notification record is created with a template for its type.

**Tasks**
- [ ] Notification table
- [ ] Templates
- [ ] Outbox

**Effort:** 1 pt / XS

#### F7-S1b: Email Sending with Retries

**As a** platform owner, **I want** emails sent reliably, **so that** users get them.

**Acceptance criteria**
- Given a notification, then it is sent by email. Given a failure, then it is retried.

**Tasks**
- [ ] Email provider integration
- [ ] Retry with backoff
- [ ] Logging without personal data

**Effort:** 1 pt / XS

#### F7-S1c: Idempotency and Failure Isolation

**As a** platform owner, **I want** each event to notify once and never block, **so that** actions stay fast.

**Acceptance criteria**
- Given one event, then at most one notification is sent. Given a failed email, then the triggering action is not blocked.

**Tasks**
- [ ] Idempotency key
- [ ] Asynchronous dispatch
- [ ] Test the failure path

**Effort:** 1 pt / XS

### F7-S2: Key Event Notifications

**As a** user, **I want** to be told when something important happens, **so that** I don't have to keep checking.

**Acceptance criteria (whole story)**
- Given someone applies to a job, then its employer is notified.
- Given an application is accepted or rejected, then the talent is notified by email.
- Given a job is edited, then everyone who applied is notified.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F7-S1, F4-S1, F6-S4, F6-S7. Decision (non-blocking): the full list of notification types. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S2a: Application and Result Triggers

**As a** user, **I want** to hear about applications and results, **so that** I don't keep checking.

**Acceptance criteria**
- Given someone applies, then the employer is notified. Given an application is accepted or rejected, then the talent is notified by email.

**Tasks**
- [ ] Hook into submit
- [ ] Hook into status change
- [ ] Templates

**Effort:** 1 pt / XS

#### F7-S2b: Job Edit Trigger

**As a** talent, **I want** to be told when a job I applied to changes, **so that** I can react.

**Acceptance criteria**
- Given a job edit, then everyone who applied is notified.

**Tasks**
- [ ] Consume the F6-S7 event
- [ ] Recipient list
- [ ] Template

**Effort:** 1 pt / XS

### F7-S3: Event Tracking Logging

**As a** platform owner, **I want** job and profile events logged, **so that** we can improve recommendations and show users insights.

**Acceptance criteria (whole story)**
- Given user activity, then these events are logged: job appear, watch, save, apply and respond, and profile appear, watch and saved.
- Given a skipped job or profile, then the skip is counted for improving recommendations.
- Given logging, then it never slows down or blocks the user action.

**Definition of Done:** standard, plus events written asynchronously.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F3-S2, F5-S3. Decision (non-blocking): tracking notice and retention period.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S3a: Event Schema and Async Writer

**As a** platform owner, **I want** events written without slowing users down, **so that** tracking is safe.

**Acceptance criteria**
- Given activity, then events are written asynchronously and never block the user action.

**Tasks**
- [ ] Event table
- [ ] Async queue or batch
- [ ] Schema

**Effort:** 1 pt / XS

#### F7-S3b: Job Events

**As a** platform owner, **I want** job events logged, **so that** we can show and use them.

**Acceptance criteria**
- Given activity, then job appear, watch, save, apply and respond are logged.

**Tasks**
- [ ] Instrument the list, detail, bookmark, apply and response paths

**Effort:** 1 pt / XS

#### F7-S3c: Profile Events and Skip Counts

**As a** platform owner, **I want** profile events and skips logged, **so that** recommendations can improve.

**Acceptance criteria**
- Given activity, then profile appear, watch and saved are logged, and skips are counted for internal use only.

**Tasks**
- [ ] Instrument employer views and saves
- [ ] Skip counters
- [ ] Keep skip counts internal

**Effort:** 1 pt / XS

### F7-S4: Event Visibility (Premium)

**As an** employer or talent, **I want** to see how my jobs or profile are performing, **so that** I can act on it.

**Acceptance criteria (whole story)**
- Given an employer, then they see the job events for their own jobs.
- Given a talent, then they see their own apply and respond events, and the profile appear, watch and saved counts for their profile.
- Given skip counts, then they are never shown to users.
- Given a basic plan user, then these statistics are not available and an upgrade prompt is shown.
- Given an employer view, then it doesn't reveal which talent caused an event that would break anonymity.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Medium | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F7-S3, F7-S6. Decision (non-blocking): aggregate or per-talent counts. Default: aggregate counts per job.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S4a: Employer Job Statistics

**As an** employer on Premium, **I want** statistics for my jobs, **so that** I can see how they perform.

**Acceptance criteria**
- Given a premium employer, then they see job events for their own jobs as aggregate counts, with no talent identified.

**Tasks**
- [ ] Aggregation endpoint
- [ ] Anonymity-safe counts
- [ ] Plan check

**Effort:** 1 pt / XS

#### F7-S4b: Talent Profile Statistics

**As a** talent on Premium, **I want** statistics for my profile, **so that** I can judge how strong it is.

**Acceptance criteria**
- Given a premium talent, then they see their own apply and respond events and their profile appear, watch and saved counts.

**Tasks**
- [ ] Endpoint
- [ ] Plan check

**Effort:** 1 pt / XS

#### F7-S4c: Statistics UI and Gating

**As a** user, **I want** the statistics shown clearly, or an upgrade prompt, **so that** I know what I get.

**Acceptance criteria**
- Given a premium user, then the statistics are shown. Given a basic user, then an upgrade prompt is shown instead.

**Tasks**
- [ ] Statistics UI
- [ ] Gating
- [ ] Upgrade prompt

**Effort:** 1 pt / XS

### F7-S5: Basic Charts for Employers

**As an** employer, **I want** simple charts of my jobs on my home page, **so that** I can see what needs attention.

**Acceptance criteria (whole story)**
- Given an employer, then the home page shows how many jobs are open, how many reached their applicant target, and how many talents are waiting for a response.
- Given a talent, then the home page has no KPI cards. Active applications appear in Your activity (F4-S8).
- Given no data, then a helpful empty state is shown. A user only sees their own data.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F6-S2, F7-S3

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S5a: Aggregation Endpoint

**As an** employer, **I want** my job numbers calculated, **so that** the charts are accurate.

**Acceptance criteria**
- Given an employer, then the endpoint returns how many jobs are open, how many reached their target, and how many talents await a response.

**Tasks**
- [ ] Queries
- [ ] Endpoint

**Effort:** 1 pt / XS

#### F7-S5b: Chart UI and Empty State

**As an** employer, **I want** simple charts on my home page, **so that** I see what needs attention.

**Acceptance criteria**
- Given data, then the charts are shown for the employer's own data only. Given none, then a helpful empty state is shown.

**Tasks**
- [ ] Chart components
- [ ] Empty state
- [ ] Ownership

**Effort:** 1 pt / XS

### F7-S6: Entitlements and Upgrade Prompts

**As a** platform owner, **I want** premium access controlled on the server, **so that** paid features stay paid.

**Acceptance criteria (whole story)**
- Given a user, then they have a basic or premium plan.
- Given a locked feature, when a basic user opens it, then the server refuses it and the screen shows what the feature is and how to upgrade.
- Given a premium user, then locked features open normally.
- Given a basic employer with 50 open jobs, when they post another, then the server blocks it and shows an upgrade prompt. Premium employers have no limit (assumed).

**Definition of Done:** standard, plus the check applied on the server for every premium endpoint.
**Priority:** Medium | **Complexity:** Low | **Effort:** 2 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F1-S4. Decision (non-blocking): how premium works in the demo. Default: a toggle, no real payments.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S6a: Plan Record and Server Check

**As a** platform owner, **I want** each user's plan enforced on the server, **so that** premium stays premium.

**Acceptance criteria**
- Given a user, then they have a basic or premium plan, and the server checks it on every premium endpoint.

**Tasks**
- [ ] Plan field
- [ ] Check helper or middleware
- [ ] Apply it to premium endpoints

**Effort:** 1 pt / XS

#### F7-S6b: Upgrade Prompt and 50-job Limit

**As an** employer, **I want** a clear prompt when I hit a limit, **so that** I know how to continue.

**Acceptance criteria**
- Given a locked feature, then a prompt explains it and how to upgrade.
- Given a basic employer with 50 open jobs, when they post another, then it is blocked with an upgrade prompt.

**Tasks**
- [ ] Prompt component
- [ ] Open-job count check
- [ ] Test the limit boundary

**Effort:** 1 pt / XS

### F7-S7: Premium Employer Tools

**As a** premium employer, **I want** the full talent list, direct contact and profile comparison, **so that** I can find and assess talent faster.

**Acceptance criteria (whole story)**
- Given a premium employer, then the shortlist shows the full list instead of the top N.
- Given two talents, when the employer compares them, then a side-by-side per-skill view is shown for the same job, with no combined score and no ranking of the two people.
- Given a talent who didn't apply, when a premium employer contacts them, then contact goes through the platform and contact details stay hidden.
- Given a basic employer, then these actions show an upgrade prompt and respond only to talents who applied to their jobs.

**Definition of Done:** standard, plus access tests for basic and premium users.
**Priority:** Low | **Complexity:** Medium | **Effort:** 6 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S2, F5-S3. Decisions (non-blocking): the talent's accept or decline step for direct contact, and the advanced charts list. Not included.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S7a: Full Talent List

**As a** premium employer, **I want** the full talent list, **so that** I'm not limited to the top N.

**Acceptance criteria**
- Given a premium employer, then the shortlist shows the full list.
- Given a basic employer, then the shortlist shows only the top N, with an upgrade prompt.
- Given any request, then the plan is checked on the server.

**Technical tasks**
- [ ] Plan check in the shortlist endpoint
- [ ] Upgrade prompt

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S2

#### F7-S7b: Compare Two Profiles

**As a** premium employer, **I want** two talents side by side, **so that** I can assess them on their skills.

**Acceptance criteria**
- Given two talents for the same job, when the employer compares them, then a side-by-side per-skill view is shown.
- Given the comparison, then there is no combined score and no ranking of the two people, and both appear by alias.
- Given a basic employer, then the action shows an upgrade prompt.

**Technical tasks**
- [ ] Selection of two talents
- [ ] Comparison view reusing the matcher output
- [ ] Access tests for basic and premium

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Medium | **Effort:** 3 pts / S-M | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S3, F3-S1b

#### F7-S7c: Direct Contact Through the Platform

**As a** premium employer, **I want** to contact a talent who didn't apply, **so that** I can approach strong matches.

**Acceptance criteria**
- Given a premium employer, when they contact a talent, then the request goes through the platform, a Contacted record is created, and contact details stay hidden.
- Given a basic employer, then the action is blocked with an upgrade prompt.
- Given the talent's side (accept or decline and what they see), then it is not part of this story.

**Technical tasks**
- [ ] Contact request record with the Contacted status
- [ ] Plan check on the server

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 2 pts / S | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S3. Decision (blocks the talent side only): how the talent accepts or declines, and whether talents opt in to appear in recommendations.

### F7-S8: Plan Selection Screen

**As an** employer or talent, **I want** to compare Basic and Premium and see exactly what each includes, **so that** I can decide whether to upgrade.

**Acceptance criteria (whole story)**
- Given a logged-in user, when they open the plan selection screen, then Basic and Premium are shown side by side with the features each includes.
- Given an employer, then the list includes: open jobs (up to 50 on Basic, no limit on Premium, assumed), top N versus the full talent list, direct contact, comparing two profiles, job statistics (appearances, views, saves, applications, responses) and advanced charts.
- Given a talent, then the list includes: personal statistics (profile appearances, views, saves and activity) and advanced charts.
- Given a premium account, then the interface looks distinct and elegant (for example a premium badge and accent), so the difference is visible.
- Given the demo, when a plan is chosen, then the demo plan switches, with no real payment.

**Definition of Done:** standard.
**Priority:** Medium | **Complexity:** Low | **Effort:** 3 pts (sum of the sub-stories below) | **Demo slice:** No
**Dependencies:** Story: F7-S6. Decisions (non-blocking): premium design details (UX step) and pricing.

**Sub-stories** (priority, demo slice and decisions are inherited from the story unless stated)

#### F7-S8a: Plan Comparison Content

**As an** employer or talent, **I want** Basic and Premium side by side, **so that** I can compare them.

**Acceptance criteria**
- Given the plan screen, then Basic and Premium are shown with the features each includes, separately for employers and for talent.

**Tasks**
- [ ] Content list
- [ ] Comparison layout

**Effort:** 1 pt / XS

#### F7-S8b: Premium Visual Treatment

**As a** premium user, **I want** my account to look distinct and elegant, **so that** the difference is visible.

**Acceptance criteria**
- Given a premium account, then the interface shows the difference, for example a premium badge and accent.

**Tasks**
- [ ] Badge and accent
- [ ] Premium-only touches
- [ ] Design details follow in the UX step

**Effort:** 1 pt / XS

#### F7-S8c: Demo Plan Switch

**As a** presenter, **I want** to switch plans in the demo, **so that** I can show both.

**Acceptance criteria**
- Given the demo, when a plan is chosen, then the demo plan switches with no real payment.

**Tasks**
- [ ] Plan switch endpoint
- [ ] Demo flag
- [ ] Reset through the seed script

**Effort:** 1 pt / XS

---

# Footer

## Success criteria for the demo build (78 points)
- The full loop works with seeded data: a talent signs up, uploads a sample CV, edits it, sees recommended jobs, and applies.
- An employer sees the applicant anonymously, moves it to Review and then Accepted, and the talent sees the change.
- No employer response contains a personal field, and invalid status changes are rejected.

## Technical prerequisites
- Chosen stack, database and hosting
- LLM API access and private object storage
- The translation engine and matcher from the national round MVP
- 3 or more sample CVs and 10 to 15 seeded jobs (synthetic or consented)
- An email service (for the notification stories)

## Recommended implementation order
1. **Foundation:** F1-S1 to S4, and F1-S8 (landing page)
2. **Talent input:** F2-S1 to S4, and F6-S1 in parallel
3. **Matching:** F3-S1 to S5
4. **Application loop:** F4-S1 to S4, F5-S1 to S3, F6-S2 to S4, then F2-S6 and S7, F4-S8, and F1-S7 (demo accounts)
5. **Extend the loop:** F4-S5 to S7 with F6-S5 and S6, then F3-S6 and S7, F5-S4 and S5, F1-S5 and S6, F2-S5, F6-S7
6. **Insights and premium:** F7-S1 to S8

## Risks
- **Scope:** the demo slice is about 26 developer-days by the rubric. If the team is small, cut F3-S5 (bookmarks), F1-S5 (navigation pane) and F2-S5 first.
- **Open decisions:** the matching formula, the translation design and how job skills are produced are the defaults most likely to change the work.
- **Added scope:** the landing page, demo accounts, linear onboarding, the "What employers see" panel, Your activity and the premium plan screen added 7 stories. They are included in the totals above. The finer split of the earlier 7 stories also adds some overhead.
