# Operation & Demo Walkthrough

This guide details the step-by-step walkthrough script for evaluating the **Jinder Platform** during hackathon judging and live demonstrations.

---

## 1. Persona 1: The International Talent (Candidate Flow)

1. **Sign In:**
   - Navigate to `http://localhost:8095/#/auth`.
   - Log in with `candidate@demo.jinder.app` / `password123`.
2. **Landing & Feed:**
   - The Home Dashboard calculates personalized matches using **Formula F-05 (FRS)**.
   - Note the **Fit Score badge** on each job card (e.g., *94% Fit*, *82% Fit*).
3. **Exploring a Job & Gap Analysis:**
   - Click on any job card to open the Job Details drawer.
   - Observe **Matched Skills** (green badges) and **Gaps to Close** (amber badges).
   - Review **"Your Path to This Job"**: Shows estimated remediation time (e.g., *"1.5 months to close learnable tools"*) and recommended Australian certifications.
4. **Applying:**
   - Click *"Apply Anonymously"*. The application is saved in SQLite and the candidate's personal identity is masked.
5. **Job Comparison (Compare Free):**
   - Select 2 to 5 jobs and open the **Compare** drawer (`#/compare`).
   - View the side-by-side competency matrix, salary ranges, and proximity indices (**Formula F-03**).

---

## 2. Persona 2: The Australian Employer (Recruiter Flow)

1. **Sign In:**
   - Log in with `recruiter@demo.jinder.app` / `password123`.
2. **Reviewing Requisitions:**
   - View posted jobs under `#/recruiter`.
   - Select a job (e.g., *"Senior Backend Engineer"*).
3. **Reviewing Talent Pool & Wildlife Aliases:**
   - Notice the candidate cards:
     - No candidate names, photos, or personal emails are displayed (**Zero-PII**).
     - Candidates are represented by unique wildlife names (e.g., *"Silver Koala"*, *"Azure Platypus"*).
   - Candidates are ranked via **Formula F-06 (TSS)**.
4. **Side-by-Side Talent Comparison (Premium Feature):**
   - Check the compare checkboxes for 2 to 5 candidates.
   - Click *"Compare Candidates"* to enter the multi-candidate evaluation matrix.
   - Compare per-skill proficiency levels (1 to 5), years of verified experience, and certifications without demographic bias.
5. **Actioning Candidates:**
   - Shortlist or invite a candidate to interview.
   - Only upon candidate acceptance are interview scheduling links revealed.

---

## 3. Interactive Portals & Administrative Telemetry Walkthrough

### 3.1 Canonical Mathematical Engine Deck (`Presentation/formulas_presentation.html`)
1. **Launch:** Open `Presentation/formulas_presentation.html` in your browser.
2. **Executive Overview (100vh Single-Screen):**
   - Review all 6 canonical formulas (F-01 through F-06) displayed simultaneously in a balanced 3×2 grid with zero vertical page scrolling.
3. **Interactive Simulation:**
   - Use the **Parameter Simulation Workbench** on the left panel with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`).
   - Drag sliders (e.g., Mandatory Weight, Statutory Beta, Recency Decay) to observe immediate real-time recalculation of match percentages.
   - Inspect the KaTeX variable definitions and step-by-step worked numerical examples.

### 3.2 Admin Control Center & Data Flow Telemetry (`Presentation/admin.html`)
1. **Launch:** Open `Presentation/admin.html` (or `http://localhost:8095/admin.html` when the server is active).
2. **Overview & System Health:**
   - Inspect live SQLite WAL performance telemetry (WAL size, active pages, cache hits) and verified entity counts (**51 Talents**, **1 Demo Employer**, 54 Job Requisitions).
3. **Interactive 5-Stage Data Flow Pipeline:**
   - Click on each pipeline stage (Ingestion $\to$ Taxonomy Translation $\to$ Mathematical Engine $\to$ SQLite WAL $\to$ Shortlist Delivery) to inspect latency SLAs, sample payload records, and throughput metrics.
4. **22 Tables Relational Explorer & Safe SQL Runner:**
   - Switch to the **Database Explorer** tab to browse schemas, paginate through tables, and filter records.
   - Execute read-only SQL queries in the built-in terminal with safety checks and tabular result formatting.

