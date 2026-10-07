# Jinder: how to run the latest version

This package has four folders. Keep them side by side. Do not move or rename them.

| Folder | What it has |
|---|---|
| `jinder_platform` | The server (REST API), the database code, the sample data loader and the tests. **Start here.** |
| `jinder_frontend` | The frontend (`app/`), the design system (`Docs/DESIGN.md`), the rules for AI assistants (`AI_Rule.md`), the build prompt and API contract (`prompt.md`) and the product specifications |
| `jinder_backend_engine` | The six formulas (`intelligence_engine/`), the taxonomy (`data/reference/ict_taxonomy.json`) and the synthetic data (`data/synthetic/`) |
| `spec` | Copies of the feature specifications (not needed to run) |

**All data is synthetic.** The demo covers three domains only: Software Engineering, AI & Machine Learning and Data.
The platform reads the 50 jobs, the 50 sample talent profiles and the 4 demo employer jobs from `jinder_backend_engine/data/synthetic`.
It reads the one list of names (skills, roles, certifications, award kinds, levels, cities) from the taxonomy `jinder_backend_engine/data/reference/ict_taxonomy.json`.
The old Australian datasets in `jinder_backend_engine/data` are **not used** any more. They are still there. Do not use them.

## Run it

You need **Python 3.9 or later** (the package was tested on Python 3.12). No other software and no `pip install`.

1. Open a terminal in the folder `jinder_platform`.
2. Run `python start.py --demo`.
3. Write down the two demo passwords that the terminal shows. They show only one time.
4. Open `http://localhost:8095/` in a browser.

The two demo accounts are:

| Account | Email | What it has |
|---|---|---|
| Employer (Alex Morgan, company Bluebushworks) | `recruiter@demo.jinder.app` | 4 jobs (a Data Engineer, a Senior Backend Engineer, a Machine Learning Engineer that closes in 4 days, and a closed Contract Data Engineer), applications from sample talent, alerts |
| Talent (alias Teal Heron) | `candidate@demo.jinder.app` | A Mid data analyst who studied in Vietnam and wants to be a Data Engineer. 8 skills with levels, one certification, one award. She is in the interview step for the Data Engineer job |

Run `python start.py` (without `--demo`) the next time. The database stays in `jinder_platform/var`.
To start again from nothing, run `python start.py --reset-db`.

> **Important: restart the old server, and know what happens to your old data.**
> 1. If a server from an older version still runs on port 8095, stop it. It keeps the old code in its memory. Then start `python start.py` again.
> 2. At the **first start of this version**, an old database (schema version 1) is **saved as `jinder.db.v1.bak`** in `jinder_platform/var` (and the folder `uploads` as `uploads.v1.bak`). A new database is made with the new data. **Nothing is deleted.**
> 3. The old accounts are in the backup, not in the new database. Create a new account, or start with `--demo`.
> 4. To go back: stop the server, delete the new `jinder.db` (and `-wal`, `-shm`), and rename the backup files to the old names (see `jinder_platform/docs/DATABASE.md`).

On Windows, you can also double-click `jinder_platform\start.bat`.

## Check that it works

Run `python run_tests.py` in `jinder_platform`. It runs **729 tests in about 75 seconds** and must end with `OK`.

Browser tests need Chrome or Edge:

1. Run `python run_tests.py --browser` to also run all browser tests: **7 stages, about 1,055 checks, about 12 minutes**. Each stage starts its own platform in a temporary folder on port 8197 and prints each step. A table at the end shows each stage.
   Run `python run_tests.py --browser-quick` for only the two journeys (about 2 minutes). Add `--formulas` to also run the 32 self-checks of the formulas.
2. Run one of the browser checks for one part of the frontend, for example `python tests/browser/check_fe_talent.py`.
   Each check starts its own platform in a temporary folder and stops it at the end. It does not use your database or the port 8095.

| Browser check | Part | Port |
|---|---|---|
| `tests/browser/check_fe_core.py` | Shared components, menu, user block, Settings plan card | 8120 |
| `tests/browser/check_fe_talent.py` | Talent lists, job detail, "Your path to this job", onboarding | 8130 |
| `tests/browser/check_fe_employer.py` | Employer lists, job form, job overview, talent cards | 8140 |
| `tests/browser/check_fe_compare.py` | The Compare page for both roles | 8150 |
| `tests/browser/check_mock_ict.py` | The browser-only mock (`?mock=1`): ICT data only | 8170 |

Add `--shots <folder>` to write screenshots.
The QA scripts `tests/browser/qa_acceptance.py`, `qa_a11y.py`, `qa_perf.py` and `qa_xss.py` are not part of `run_tests.py`. See `jinder_platform/README.md` (section "Tests").
The result of the last full check (QA) is in `jinder_platform/docs/CHANGELOG_V2.md`, with the open defects and the known limits.

## Read more

- `jinder_platform/README.md`: what the product does, the settings, the folders
- `jinder_platform/docs/`: the database, the formulas in the product, the API notes, and `CHANGELOG_V2.md` (what changed in version 2 and the known limits)
- `jinder_frontend/prompt.md`: the API contract between the frontend and the backend, and how to build the frontend
- `jinder_backend_engine/data/reference/README_taxonomy.md` and `jinder_backend_engine/data/synthetic/README.md`: the taxonomy and the synthetic data

> **Warning:** The server uses plain HTTP and the demo switch for Premium. Use it on your own computer.
> Do not put it on the internet without HTTPS and the settings in `jinder_platform/README.md`.
