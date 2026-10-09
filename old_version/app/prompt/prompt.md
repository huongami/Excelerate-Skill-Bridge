# Product Frontend Specification Prompt

Complete UI rebuild required.

Refresh UI according to the design specification in `skill/design/design.md`.

Use the skill: `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git`

The product consists of 3 core components:

1. **Landing Homepage:** Features product overview and Sign In / Sign Up functionality.

2. **Sign Up Flow:**
   - Supports uploading a CV, followed by scanning/parsing personal details, skills, and experience.
   - Registration requires accepting Terms & Conditions (clicking opens a modal dialog with terms content).
   - If the user does not want to upload a CV during sign up, they can sign in via Google Mail protocol, after which the homepage shows an upload button `+` to add a CV later.
   - Once signed in and a CV is uploaded, the system extracts experience, skills, and anonymous animal alias for display to recruiters.

3. **Job Search & Feed:**
   - Homepage shows a search bar, with the job feed ranked by algorithmic suitability underneath.
   - Each job card displays:
     - Overall match score
     - Short job description
     - Match percentage (% match based on ANZSCO taxonomy)
     - Skill gap level
     - Time posted (e.g. "Posted 13 days ago")
   - Clicking a job card opens full details, line chart for % match, line chart for skill gaps, and breakdown explanation.
   - Action buttons: Apply or Ignore.
   - Additional features per job card: Save to favorites and Report incorrect job (fully implement functional behavior for these buttons).
   - Feed order is decided by the previously implemented priority algorithm, factoring in actions like favoriting or ignoring.
   - Clicking Apply triggers CV submission to HR. Clicking Ignore removes the job from the feed.

4. **Candidate Navigation & Profile:**
   - Left sidebar menu: Account icon to edit personal info, edit CV, update skills, override AI-extracted skills.
   - Saved jobs list and Applied jobs tracking list.
   - Applied jobs list displays: Job title, company, current status (Reviewed, CV Scanning, Interview...).
   - Clicking an applied job displays an interactive timeline progress bar tracking the candidate journey from application to offer.
   - Job comparison tray: Spider/radar chart overlaying shared metrics across compared jobs.

5. **HR / Recruiter Flow:**
   - Recruiter accounts register with a Job Description (JD). If no JD is added during signup, homepage prompts an "Add Job" button.
   - Recruiter homepage shows an overall analytics dashboard (Total jobs, Active jobs, Expired, Hired, Rejected).
   - Job management page lists posted jobs with:
     - Job title, company name, description, date posted
     - Impressions, views, applicants
   - Left sidebar for HR: Account icon to edit profile, edit JD, override AI-extracted requirements.
   - Candidate discovery page:
     - Displays masked alias (Australian wildlife persona), overseas translated title, experience, % match (ANZSCO), skill gap, overall score, and hiring status.
     - Expandable accordion format: clicking expands detailed breakdown.
     - Multi-candidate comparison tray: 5-axis spider/radar chart overlaying skills and experience side-by-side.

6. **Algorithmic Engine & Data Integration:**
   - Job ranking, applicant scoring, and gap evaluation must be driven by the 6 canonical algebraic formulas implemented in this repository.
   - Data is pre-seeded in the `data/` directory, representing realistic user inputs (job seekers and HR). Deliver a functional, seamless end-to-end simulation of the Australian hiring process for both personas.