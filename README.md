# Jinder — Autonomous Capability Alignment Platform

> **Live Platform Repository & Source Code**  
> For complete instructions on how to start and test the platform, see [**`START_HERE.md`**](START_HERE.md).

---

## 🚀 Quick Start

You only need **Python 3.9+** (tested on Python 3.12). No external dependencies or `pip install` required.

```bash
cd jinder_platform
python3 start.py --demo
```
- Open **`http://localhost:8095/`** in your browser.
- Write down the demo passwords printed in the terminal:
  - **Employer:** `recruiter@demo.jinder.app`
  - **Talent:** `candidate@demo.jinder.app`

### Run Autonomous Tests
```bash
cd jinder_platform
python3 run_tests.py
```
*(Runs all 729 unit & integration tests in ~24s with full `OK` status).*

---

## 📁 Repository Structure

The repository is organized according to the required submission standard:

```
Excelerate-Skill-Bridge/
│
├── AI Rule/                   # 🛡️ AI Boundaries, Capabilities & 10 Core Governance Rules
├── Skill/                     # ⚡ AI Skills (Extraction, Gap Analysis, Formulas, Zero-PII)
├── SDD/                       # 📋 Software Design Description (PRD, Specs, User Flows, Stories)
├── Prompt/                    # 💬 Prompt Engineering Principles, System Prompts & API Contract
├── Readme/                    # 📖 Master Documentation Guides & Demo Walkthroughs
├── Presentation/              # 🎨 Interactive Project Presentation & Mathematical Formula Decks
├── Data/                      # 📊 Verified Synthetic Benchmarks & Australian Legal Provenance
├── Document/                  # 📐 Architecture Details (Frontend, Backend, Data, Formulas, AI Test Plan)
│
├── jinder_platform/           # 🚀 The Running Platform Backend & SQLite Database
├── jinder_frontend/           # 🎨 Client Web Application (HTML/CSS/JS)
├── jinder_backend_engine/     # 📐 Intelligence Engine (Formulas F-01 to F-06)
└── old_version/               # 📦 Archived Legacy Files & Historical Prototypes
```

---

## 📐 The 6 Core Mathematical Formulas

Located in `jinder_backend_engine/intelligence_engine/`:

1. **F-01 (SMF):** Candidate vs ANZSCO Skill Match Model.
2. **F-02 (GSI & JRS):** Skill Gap Severity & Job Readiness Score (distinguishes statutory blockers from learnable tools).
3. **F-03 (JPI):** Job Proximity Index & Multi-Job Distance Matrix.
4. **F-04 (RMS):** Candidate Benchmarking & Relative Merit Score (Zero-PII).
5. **F-05 (FRS):** Job Seeker Feed Ranking Score + Behavioral Affinity Loop.
6. **F-06 (TSS):** Recruiter Talent Search Score + Wildlife Animal Aliases.

For interactive equation sliders and ASD-STE100 technical documentation, open:
[`jinder_backend_engine/formulas_presentation.html`](jinder_backend_engine/formulas_presentation.html) in your browser.
