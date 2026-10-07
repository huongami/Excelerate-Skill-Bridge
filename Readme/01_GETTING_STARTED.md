# Getting Started with Jinder

## 1. System Requirements

Jinder is engineered to run with zero heavy external dependencies:
- **Operating System:** macOS, Linux, or Windows (WSL / PowerShell)
- **Runtime:** Python 3.9+ (Tested on Python 3.10, 3.11, 3.12)
- **Dependencies:** **None** (Uses Python Standard Library: `sqlite3`, `http.server`, `json`, `urllib`). No `pip install` required!
- **Browser:** Modern web browser (Chrome, Edge, Firefox, Safari)

---

## 2. Launching the Platform

### Step 1: Navigate to the Platform Directory
```bash
cd jinder_platform
```

### Step 2: Start the Server with Synthetic Demo Data
```bash
python3 start.py --demo
```
*Tip: To run on a custom port, add `--port 8095` (defaults to 8095).*

### Step 3: Access the Web Application
Open your browser and navigate to:
```
http://localhost:8095/
```

### Step 4: Demo Credentials
The `--demo` flag creates pre-seeded accounts:
- **Employer / Recruiter Account:**
  - Email: `recruiter@demo.jinder.app`
  - Password: `password123`
- **Talent / Candidate Account:**
  - Email: `candidate@demo.jinder.app`
  - Password: `password123`

---

## 3. Running the Automated Test Suite

Jinder includes a comprehensive suite of **729 automated tests** covering:
- Mathematical formula correctness (F-01 to F-06)
- Database integrity, SQLite migrations, and foreign key constraints
- API endpoints, rate limiting, and RBAC authorization
- Zero-PII anonymization assertions

To execute all tests:
```bash
cd jinder_platform
python3 run_tests.py
```

**Expected Result:**
```
Ran 729 tests in ~24s
OK
```

---

## 4. Opening the Interactive Presentation & Administrative Portals

The platform includes two zero-build HTML applications built using the Jinder Design System:

### 1. Canonical Mathematical Intelligence Engine (`formulas_presentation.html`)
Interactive presentation of Formulas F-01 to F-06 with ASD-STE100 technical documentation, 100vh single-screen view, and continuous gradient parameter sliders:
```bash
open Presentation/formulas_presentation.html
```

### 2. Admin Control Center & Data Flow Telemetry (`admin.html`)
Real-time SQLite WAL database metrics, 5-stage interactive Data Flow Pipeline, and 22-table relational database explorer:
```bash
open Presentation/admin.html
```
*(Also accessible directly within the frontend app at `http://localhost:8095/admin.html` when the server is running).*

