# Jinder - Intelligence Engine, Data and Prototype Backend

This folder has the six formulas of the Jinder engine (version 2), the reference taxonomy, the synthetic sample data, the math documents, and the earlier prototype backend.

> **The product runs from [`../jinder_platform`](../jinder_platform/README.md).**
> It serves the frontend, a REST API and a SQLite database. It calls the six formulas in [`intelligence_engine/`](intelligence_engine/).
> This folder is the home of the formulas and of the datasets.
> The API server in `backend/server.py` (port 8095) is the earlier prototype. Do not start it at the same time as the platform: both use port 8095 by default.

---

## 1. Version 2 in short

The product covers three domains only: **Software Engineering**, **AI & Machine Learning** and **Data**.
A talent and a job have a level (Intern, Junior, Mid, Senior, Lead, Principal), exact years, skill levels (1 to 5), certifications, awards and a work mode.
The formulas use these facts. Every score is a smooth function, so two different jobs or talents seldom have the same score.

| Formula | File | Gives |
| :--- | :--- | :--- |
| F-01 | `01_skill_matching_model.py` | The skill match (SMF) and the product **fit** (0 to 100, one decimal) with a per-skill breakdown |
| F-02 | `02_skill_gap_analysis.py` | Gap items and strength items, readiness, months to close, and the `path` of "Your path to this job" |
| F-03 | `03_job_to_job_comparison.py` | The job proximity index (symmetric), `annual_salary(min, max, unit)` |
| F-04 | `04_candidate_benchmarking.py` | The merit dimensions of a profile (never a total for the employer) |
| F-05 | `05_job_seeker_ranking_feed.py` | The feed score (capability, wage upside, location, recency, employer diversity) |
| F-06 | `06_recruiter_candidate_ranking.py` | The talent search score (the shared profile only) |
| helper | `engine_common.py` | The taxonomy index, the input cleaners and the smooth functions. **It must stay in the same folder as the six files.** The formula files, `run_verification.py` and the legacy `backend/scores.py` need it |

The product score is `0.55 x fit + 0.45 x FRS`. The employer order is `0.6 x coverage + 0.4 x TSS`.
The equations, the symbols, the ranges and a worked example for each formula are in [`docs/02_FORMULAS_MATHEMATICAL_SPEC.md`](docs/02_FORMULAS_MATHEMATICAL_SPEC.md) and in the `0N_*.md` files of `intelligence_engine/`.

---

## 2. Quick start

### 2.1 Run the verification

```bash
python run_verification.py
```

The script runs the self-check of each file, checks the properties of the formulas, and runs the differentiation checks on `data/synthetic`.
It prints `PASS` or `FAIL` for each check. The exit code is 0 if all checks pass.

### 2.2 Run the tests of the platform

```bash
cd ../jinder_platform
python run_tests.py
```

The tests `tests/test_formulas.py` (properties of the formulas) and `tests/test_differentiation.py` (50 jobs and 50 talents) use only the engine files.

### 2.3 Call a formula

```python
import importlib.util

spec = importlib.util.spec_from_file_location("f1", "intelligence_engine/01_skill_matching_model.py")
f1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f1)

talent = {"level": "Mid", "years_experience": 4, "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}]}
job = {"title": "Data Engineer", "category": "Data", "level": "Mid", "min_years": 2, "max_years": 5,
       "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True}]}
print(f1.evaluate_job_fit(talent, job)["fit"])
```

The file names start with a digit, so load the files by path. A formula file loads the other files that it needs by itself.

### 2.4 Start the prototype backend (optional)

```bash
python start_server.py
```

This starts the earlier prototype on `http://localhost:8095`. It uses `backend/scores.py`, which calls the same formulas.

---

## 3. Directory structure

```
jinder_backend_engine/
|
|-- README.md                          This file
|-- run_verification.py                Checks of the formulas (PASS or FAIL)
|-- start_server.py                    Launcher of the prototype backend
|-- requirements.txt                   Python 3.9 or later, standard library only
|
|-- intelligence_engine/               The six formulas
|   |-- engine_common.py               Taxonomy index, input cleaners, smooth functions
|   |-- 01_skill_matching_model.py     + 01_SKILL_MATCHING_MODEL.md
|   |-- 02_skill_gap_analysis.py       + 02_SKILL_GAP_ANALYSIS.md
|   |-- 03_job_to_job_comparison.py    + 03_JOB_TO_JOB_COMPARISON.md
|   |-- 04_candidate_benchmarking.py   + 04_CANDIDATE_BENCHMARKING.md
|   |-- 05_job_seeker_ranking_feed.py  + 05_JOB_SEEKER_RANKING_FEED.md
|   |-- 06_recruiter_candidate_ranking.py + 06_RECRUITER_CANDIDATE_RANKING.md
|   |-- MASTER_PLAN.md                 Architecture and rules
|   `-- formulas_presentation.html     Interactive canonical formula deck (Version 2, 100vh, gradient sliders, ASD-STE100)
|
|-- data/
|   |-- reference/                     ict_taxonomy.json (the one list of names), validate_taxonomy.py, README_taxonomy.md
|   |-- synthetic/                     jobs.json (50), talents.json (50), demo.json, checkers
|   `-- australian_*.json, *.csv       Data of the prototype (version 1)
|
|-- docs/
|   |-- 02_FORMULAS_MATHEMATICAL_SPEC.md   The equations of all formulas (short form)
|   |-- 04_DATA_AND_SCORING_SPEC.md        The data, the wiring and the charts
|   `-- 01_*, 03_*                         Documents of the prototype
|
`-- backend/                           The earlier prototype (REST API, SQLite)
```

---

## 4. Rules for every change of a formula

1. Keep the file names, the main function names and the main result keys. Add new keys. Do not remove a key that a caller uses.
2. Make each score a smooth function. Do not add a fixed step that decides a score alone.
3. Do not read a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo.
4. Formulas 4 and 6 read the shared profile only. They do not read the CV text.
5. Change the code and the math documents in the same task. The equations and the worked examples must agree with the code.
6. Run `python run_verification.py` and the tests of the platform.

---

## 5. Taxonomy and sample data

- `data/reference/ict_taxonomy.json` is the one list of names. Run `python data/reference/validate_taxonomy.py` after each change.
  The engine reads this file itself. If it is missing, the engine uses simple defaults and still runs. The names and the aliases are matched in any case.
- `data/synthetic/` has 50 jobs and 50 talents that are made up. There is no real person, no real employer and no real job ad.
  Run `python data/synthetic/validate_jobs.py` and `python data/synthetic/validate_talents.py` after each change.
- The pay of a job has a unit: `year`, `day` or `hour`. The engine changes it to a yearly pay (day x 220 working days, hour x 1950 hours).

---

## 6. Demo data caveat

These values are demo assumptions. They are not statistics and not official data: the pay benchmarks (Software Engineering 130000, AI & Machine Learning 150000, Data 125000 AUD per year for a Mid level),
the pay step of +22% for each level, the 220 working days for a day rate, the assumed credit for a method or soft skill that a talent did not list, and the weights of the fit and of the feed.
The taxonomy (`monthsToLearn`, `rarity`, `prepMonths`) is a list that people made by hand. See `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 9.

---

## 7. Sharing

Send this folder as it is. The engine needs only Python 3.9 or later and no other package.
