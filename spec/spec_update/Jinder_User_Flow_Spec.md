# Jinder: User Flow Specification

Futura Remix Hackathon, international round. Working draft from the team's flow discussion.

**Status key**
- **Decided**: agreed in the flow discussion.
- **To discuss**: open question, marked with `[DISCUSS]`.
- **Premium**: part of the paid tier.
- **Later**: acknowledged but not for the current build.

---

## 1. Overview

Skill Bridge is a two-sided platform. Talents (international students and skilled migrants) get their experience translated into skills an Australian employer recognises. Employers see anonymous, translated profiles matched per skill against their jobs, and make every hiring decision themselves.

The platform has two user types, a talent (job seeker) and an employer (recruiter or HR), who share the same login and sign-up screens.

**Terminology:** the product uses **Talent** and **Employer** consistently in the interface and in all documents, replacing the earlier words candidate, job seeker, recruiter and HR.

**Design principles carried over from the PRD**
- Matching is shown per skill, with a plain-language reason. It is not a single score on the person.
- The tool never auto-accepts or auto-rejects a talent. The employer always decides.
- Employers see talents anonymously, to reduce bias.

---

## 2. Talent flow

### 2.0 Landing page
The first screen for any visitor who is not logged in.
- The top section highlights the Australian market, with icons. The "black-box score" wording is removed from the top section.
- It explains the problem and the product, and gives two clear entry points, one for talent and one for employers, plus a login link.
- A logged-in user goes straight to their home page.
- `[DISCUSS]` One page with two paths or two separate pages, a "how it works" section with a translation example, and whether to mention premium pricing.

### 2.1 Account and profile
1. **Log in or sign up.** New users sign up and provide some basic information. `[DISCUSS]` Which sign-up fields to collect.
2. **Upload CV.** The AI reads the CV and pre-fills the information fields. The cross-border and cross-industry translation happens at this step. `[DISCUSS]` See section 7.1.
3. **Review and edit.** The talent reviews the AI-detected information and the translated skills in the same step, and corrects anything that is wrong. Editing answers is part of this step, not a separate flow. `[DISCUSS]` The current onboarding (update CV, Edit Answers) is confusing. Proposed: one linear flow of upload CV, review and edit, done.
4. **Alias.** The talent can choose an alias at sign-up. If they do not, the platform assigns an animal-based name (for example "yellow llama"). Employers see only the alias.

### 2.2 Home page
- **Your activity** at the top of the page, showing only active items (such as applications in progress). There are no KPI cards.
- **What employers see:** a panel showing the talent's anonymous profile as employers see it. It replaces the old "Your anonymous profile is empty" message.
- Recommended jobs, based on skill matching and, if the talent has set one, their target role.
- Access to the bookmark list, the application list, and the information edit menu in settings.
- Statistics about their own profile (appearances, views, saves) are a premium feature.

### 2.3 Job shortlist
Each job in the recommendation list shows the job description, the skill gap or percentage match, and the open and close dates, so the talent can scan quickly.

Actions on each job:
- **Skip**: hides the job for now. `Later:` move skipped jobs to the bottom as low priority.
- **Bookmark**: saves the job to the bookmark list.
- **Report**: flags a wrong recommendation (for example, a sushi chef job shown to someone seeking data analyst roles). Reports are used to improve the recommendations.

### 2.4 Job detail
Clicking a job opens:
- The full job description.
- The detailed skill match breakdown, including the skill gaps. `[DISCUSS]` Matching formula, see section 7.1.
- Similar jobs.
- Actions: **Apply**, **Skip**, **Bookmark**, **Report**, placed at the bottom right of the page.

### 2.5 Applying
1. **Review.** Before submitting, the talent reviews what will be sent. Only the translated profile goes to the employer. The original CV is not shared, because it may contain a photo or other identifying details.
2. **Submit.**
3. **Success screen.** Prompts the talent to track the application status.

### 2.6 After applying
- **Edit window.** The talent can edit the application form until the employer moves it to Review (or In progress).
- **Cancel.** The talent may be able to withdraw an application. `[DISCUSS]` Tentative.
- **Application list.** A shortlist of applied jobs, each with a brief status shown as a ribbon in the top right corner.
- **Status tracking view.** Opened from the application list or from the success screen. Shows the status and the submitted application.
- **Interview.** The employer offers time slots. The talent picks one and confirms. `[DISCUSS]` What happens if no slot fits.
- **Result and offer.** The talent is notified of the result. If accepted, an offer follows and the talent accepts or rejects it. `[DISCUSS]` Offers that expire unanswered.
- **Feedback.** The final stage, after the talent accepts or rejects the offer or is rejected.

### 2.7 Bookmark list
A shortlist of saved jobs. Clicking one opens the same job detail page as from the recommendation list.

### 2.8 Navigation
A fixed navigation pane on the left that stays in place but can be hidden. It gives direct access to the main sections: home, bookmarks, applications, and settings.

---

## 3. Employer flow

### 3.1 Account
Same login and sign-up as the talent, but employers only provide their information. There is no CV upload.

### 3.2 Home page
- A shortlist of potential talents. The basic tier shows the top N talents. `[DISCUSS]` The value of N.
- Basic charts: how many jobs are open, how many have reached their applicant target, and how many talents are waiting for a response. Advanced charts are premium.

### 3.3 Anonymity rules
Talents are shown by alias. Hidden from employers:
- Name, origin, ethnicity, nationality, gender.
- Contact details. Employers contact talents through the platform.
- The original CV. Employers see only the translated profile.

`[DISCUSS]` Also consider hiding employer and university names, age, and photos. `[DISCUSS]` When anonymity ends, since interviews and offers need real identity.

### 3.4 Talent detail
The translated profile and the skill match. Actions on the shortlist and on the detail page:
- **Bookmark** (save talent).
- **Report** a wrongly recommended talent.
- **Skip** (hide the talent).

### 3.5 Posting and managing jobs
- **Post a job.** The employer sets the target number of applicants and the close date. The employer can also **upload a PDF** of the job description, and the AI reads it and fills in the title, description and required skills for the employer to review before posting. `[DISCUSS]` How the job's required skills are produced: AI-extracted from the description, or tagged by the employer.
- **Job limit:** the basic plan allows up to **50 open jobs at a time**. Closed jobs do not count. Premium has no limit (assumed, to confirm).
- **My jobs list.** Each job shows the target against the current applicant count, for example target 100, current 200. A badge shows the time to close:
  - Green: open.
  - Yellow: less than one week until the close date.
  - Red: closed or overdue.
- **Edit a job.** Any change notifies everyone who has applied. `[DISCUSS]` Whether a major edit should re-run the skill match for existing applicants.
- `[DISCUSS]` What happens to pending applications when a job closes. The tool should not auto-reject.

### 3.6 Reviewing applications
Clicking a posted job opens its applications. The employer can:
- Review each talent's translated profile and skill match.
- Update the application status.
- Offer interview time slots.
- Confirm the result, send an offer, and give feedback.

---

## 4. Shared hiring lifecycle

### 4.1 Job status
**Open**, then **Closed**.

### 4.2 Application status
Applying through a job post:

`Applied` → `Review` → `Interview` → `Accepted` or `Rejected` → `Offer` → `Confirmed`

- If the talent rejects the offer, the application goes to Rejected.
- Feedback is the final stage, whichever way the application ends.
- `[DISCUSS]` Where rejected applications are shown. One idea is a "past jobs" menu.

### 4.3 Employer-initiated path (premium)
When an employer finds a talent through the recommendation panel:

`Contacted` → `Interview` → same flow as above.

Applied and Review are skipped, because the employer has already reviewed the profile.

### 4.4 Feedback
Two kinds, both collected at the final stage:
- **To each other.** The employer and talent give feedback that is exchanged between them.
- **To the development team.** Collected in the backend and used to improve the product.

---

## 5. Notifications

Decided:
- Employer: notified when someone applies to their job.
- Talent: notified by email when an application is accepted or rejected.
- Applicants: notified when a job they applied to is edited.

Suggested for the demo build (not yet confirmed): new application, status change, interview slots offered, slot confirmed.

`[DISCUSS]` Email only, or also in-app notifications.

---

## 6. Data, charts, and monetization

### 6.1 User tracking system
Events logged:
- **Job events:** appear, watch, save, apply, respond.
- **Profile events:** appear, watch, saved.
- **Ignored counts:** skipped jobs and profiles, used internally to improve the AI recommendations.

Visibility:
- **Premium feature:** employers see job events for their own jobs (appear, watch, save, apply, respond). `[DISCUSS]` Aggregate counts per job, not per individual talent, to protect anonymity.
- **Premium feature:** talents see their own apply and respond events, plus profile appear, watch, and saved events, so they can judge how strong their profile is.
- Ignored counts are not shown to users.

`[DISCUSS]` Users should be told their activity is tracked.

### 6.2 Charts

| | Basic | Premium (ideas, not final) |
|---|---|---|
| **Talent** | Your activity component (active applications), no KPI cards | Profile statistics (appearances, views, saves), skill gap ranking, market demand for their skills, match trend |
| **Employer** | Open jobs, jobs that reached their target, talents awaiting a response | Job statistics (appearances, views, saves, applications, responses), time to respond, pipeline drop-off by stage, skills supply versus demand, hidden talent from cross-industry and international backgrounds |

Guardrails: keep charts about skills and process, not about people. Avoid a talent scoring chart. Do not break anonymity with breakdowns by nationality, gender, or ethnicity.

### 6.3 Premium tier

| Feature | Basic | Premium |
|---|---|---|
| Talent recommendations | Top N only | Full list |
| Contacting talents | Respond only to talents who applied to your job | Contact talents directly (headhunting) |
| Comparing profiles | Not available | Compare two profiles side by side |
| Open jobs (employer) | Up to 50 open jobs at a time | No limit (assumed) |
| Statistics | Not available | Employers: job statistics (appearances, views, saves, applications, responses). Talents: profile statistics (appearances, views, saves) and their own activity events |
| Charts | Basic charts | Advanced charts, both sides |

### 6.4 Plan selection screen and premium look
- A plan selection screen compares Basic and Premium and lists exactly which features each plan includes, for employers and for talents.
- The premium account has an elegant interface that shows the difference clearly (for example a premium badge, a distinct accent, and visible premium features instead of only locked ones). Design is done in the UX step.

---

## 7. Open questions

### 7.1 To discuss tomorrow (most important first)
1. **Cross-border and cross-industry translation.** The core engine is missing from the flow so far. Decide how it works, where it appears in the talent and employer views, and which two or three industry pairs to demo live.
2. **Matching formula.** How skill matching and grading is calculated. The percentage match on the shortlist must be reconciled with the PRD rule of per-skill matching and no single score on a person.
3. **How jobs get their required skills.** AI-extracted or employer-tagged.
4. **When anonymity ends.** The point at which a talent's real identity is revealed, ideally with the talent's consent.
5. **Where rejected applications show up.** For example a "past jobs" menu.

### 7.2 Flow gaps
- Sign-up fields and the list of status options.
- The exact onboarding steps (upload CV, review and edit, done).
- The value of N for top talents.
- Whether cancelling an application is allowed.
- A talent who cannot make any offered interview slot, or an employer who needs to reschedule.
- Offers that expire or go unanswered.
- What happens to pending applications when a job closes.
- Whether a major job edit re-runs the skill match.
- Whether a talent rejected at the result stage skips the offer and goes straight to feedback.
- Email only, or also in-app notifications.
- Employer-initiated contact: the talent needs to accept or decline, and an opt-in setting for appearing in recommendations.

### 7.3 Not yet discussed
- Employer-to-talent messaging on the platform.
- Company profile and verification, so talents can trust postings.
- Email verification, password reset, and deleting personal data.
- Moderation of reports (wrong job or talent recommendations).
- How the premium paywall works in the demo, with no real payments needed.
- Empty states, such as a new talent with no matches yet.
- Landing page choices: one page or two, a "how it works" example, and whether to mention premium pricing.

---

## 8. Suggested scope for the next two to three days

Build the core path only, with seeded data:
1. CV upload, AI pre-fill, and edit, with the translation visible (original skill, mapped skill, why).
2. Job shortlist and job detail with per-skill match.
3. Review, apply, and success.
4. Employer's anonymous talent view and status updates.
5. Landing page, demo accounts and seeded data.

Mock or show as slides: premium gates, notifications beyond the key few, charts, the tracking system, and the full interview-to-feedback lifecycle. Put the rest on the roadmap slide.
