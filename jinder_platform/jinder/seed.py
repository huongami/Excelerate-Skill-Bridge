"""Fill the database with the demo job catalogue and with sample talent profiles (version 2: ICT only).

Data sources (they stay in `jinder_backend_engine/data/synthetic`; all of it is made up, see its README):
  * jobs.json     the 50 job ads of the catalogue. `postedDaysAgo` and `closesInDays` are days from now.
  * talents.json  the 50 sample talent profiles. `updatedDaysAgo` is the age of the last change of the profile.
  * demo.json     the demo employer and the 4 jobs that the demo employer owns.

The old datasets (`australian_*`, `international_candidates_dataset.csv`, `real_resumes_dataset.csv`) are not read any more.

Sample talent profiles cannot sign in. Employers see them only by alias, like every other talent.
Demo accounts are made only when the operator asks for them (`--demo`), with random passwords (AI_Rule Rule 6, item 9).
"""
import json
import logging
import random
import re
import sqlite3
from datetime import timedelta
from typing import Any, Dict, List, Optional

from . import catalogue, config, db, security, store
from .catalogue import money_text, summary_of
from .reference import YEARS
from .translation import translate
from .util import iso, jdump, new_id, now_iso, short_id, utcnow

log = logging.getLogger("jinder.seed")

_CATALOGUE_KEY = "catalogue_seed"
_TALENT_KEY = "sample_talent_seed"
_DEMO_KEY = "demo_seed"
SEED_VERSION = "2"    # a database that was seeded with an older version (the old Australian data) is seeded again


def _read_json(name: str) -> Any:
    path = config.SYNTHETIC_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"The demo data file was not found: {path}. Set JINDER_SYNTHETIC_DIR or JINDER_DATA_DIR.")
    return json.loads(path.read_text(encoding="utf-8"))


# =====================================================================
# Catalogue
# =====================================================================
def _job_row(j: Dict[str, Any], index: int, now, owner_id: Optional[str] = None, company: Optional[str] = None) -> Dict[str, Any]:
    """The columns of one job of the data files. The pay is stored as given, with its unit. The description is stored in full."""
    sal = j["salary"]
    # Jobs with the same age get a few minutes of difference, so that "newest" has a clear order
    posted = now - timedelta(days=int(j["postedDaysAgo"]), minutes=index)
    return {
        "id": "job-" + j["key"], "owner_id": owner_id, "title": j["title"], "company": company or j["company"], "category": j["domain"],
        "location": j["city"], "area": j["area"], "type": j["type"], "anzsco": str(j["occupation"]["code"]), "occupation": j["occupation"]["title"],
        "salary": money_text(sal["min"], sal["max"], sal["unit"]), "salary_min": sal["min"], "salary_max": sal["max"], "salary_unit": sal["unit"],
        "summary": summary_of(j["description"]), "description": j["description"], "posted_at": iso(posted),
        "closes_at": iso(now + timedelta(days=int(j["closesInDays"]))), "created_at": iso(now),
        "level": j["level"], "specialisation": j["specialisation"], "min_years": j["minYears"], "max_years": j["maxYears"],
        "work_mode": j["workMode"], "education_min": j["educationMin"],
        "certs_required": jdump(j["certifications"]["required"]), "certs_preferred": jdump(j["certifications"]["preferred"]),
        "awards_preferred": jdump(j["awards"]["preferred"]),
    }


def _insert_job(conn: sqlite3.Connection, row: Dict[str, Any], skills: List[Dict[str, Any]], target_applicants: Optional[int] = None) -> None:
    row = {**row, "target_applicants": target_applicants}
    conn.execute(f"INSERT OR REPLACE INTO jobs ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})", tuple(row.values()))
    catalogue.save_job_skills(conn, row["id"], [s["name"] for s in skills], [{"name": s["name"], "level": s["level"], "must": s["must"]} for s in skills])


def seed_catalogue(conn: sqlite3.Connection) -> int:
    """Write the catalogue jobs (the 50 jobs of jobs.json). The old catalogue is removed first. Dates are relative to now."""
    old = [r["id"] for r in conn.execute("SELECT id FROM jobs WHERE owner_id IS NULL").fetchall()]
    for jid in old:
        conn.execute("DELETE FROM jobs WHERE id = ?", (jid,))            # the job skills go with it
        conn.execute("DELETE FROM bookmarks WHERE job_id = ?", (jid,))
        conn.execute("DELETE FROM skips WHERE job_id = ?", (jid,))
    now = utcnow()
    jobs = _read_json("jobs.json")["jobs"]
    for i, j in enumerate(jobs):
        _insert_job(conn, _job_row(j, i, now), j["skills"])
    return len(jobs)


def refresh_catalogue_dates(conn: sqlite3.Connection) -> int:
    """Keep the sample catalogue alive: move its dates forward when the newest job is old. Employer jobs do not change."""
    if config.FREEZE_CATALOGUE_DATES:
        return 0
    row = conn.execute("SELECT MAX(posted_at) AS newest FROM jobs WHERE owner_id IS NULL").fetchone()
    from .util import parse_iso
    newest = parse_iso(row["newest"]) if row else None
    if newest is None or utcnow() - newest < timedelta(days=3):
        return 0
    delta = (utcnow() - timedelta(days=1)) - newest
    days = delta.total_seconds() / 86400.0
    conn.execute(
        """UPDATE jobs SET posted_at = strftime('%Y-%m-%dT%H:%M:%S', posted_at, ?) || '.000Z',
                           closes_at = strftime('%Y-%m-%dT%H:%M:%S', closes_at, ?) || '.000Z'
           WHERE owner_id IS NULL""", (f"{days:+.4f} days", f"{days:+.4f} days"))
    return conn.execute("SELECT COUNT(*) FROM jobs WHERE owner_id IS NULL").fetchone()[0]


# =====================================================================
# Sample talent
# =====================================================================
def _years_band(y: float) -> str:
    return store.years_band(y)


def _translation_rows(profile: Dict[str, Any], skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The translated cards of a profile, all accepted. The role cards get their occupation and code from the taxonomy.
    The skill cards get the level and the years of the data. The evidence lines (private) make the evidence of a skill "Strong"."""
    plain = {k: profile.get(k) for k in ("currentRole", "qualification", "studyCountry")}
    plain["skills"] = [s["name"] for s in skills]
    rows = translate(plain, profile.get("evidence", []))["skills"]
    by_name = {s["name"].lower(): s for s in skills}
    for r in rows:
        r["status"] = "accepted"
        if r["source"] == "skill":
            mine = by_name.get(r["mapped"].lower())
            if mine:
                r["level"], r["years"] = mine["level"], mine.get("years")
    return rows


def _sample_profile(t: Dict[str, Any]) -> Dict[str, Any]:
    profile = {
        "qualification": t["qualification"], "fieldOfStudy": t["fieldOfStudy"], "studyCountry": t["studyCountry"],
        "currentRole": [t["currentRole"]], "industry": [t["domain"]], "targetIndustries": t["targetIndustries"],
        "specialisation": t["specialisation"], "level": t["level"], "yearsExperience": t["yearsExperience"],
        "skills": [s["name"] for s in t["skills"]], "targetRole": t["targetRole"], "locations": t["locations"],
        "workModes": t["workModes"], "workTypes": t["workTypes"], "certifications": t["certifications"], "awards": t["awards"],
        "evidence": t["evidence"],
    }
    profile["translation"] = _translation_rows(profile, t["skills"])
    return profile


def _add_sample_talent(conn: sqlite3.Connection, t: Dict[str, Any], index: int, now) -> str:
    uid = new_id()
    alias = t["alias"]
    slug = re.sub(r"[^a-z]+", ".", alias.lower())
    conn.execute(
        "INSERT INTO users (id, role, name, email, company, alias, password_hash, onboarding, is_sample, created_at) "
        "VALUES (?, 'candidate', ?, ?, NULL, ?, ?, 'done', 1, ?)",
        (uid, f"Sample profile {alias}", f"{slug}@sample.jinder.invalid", alias, security.NO_LOGIN, iso(now)))
    # F12: the profiles were changed over the last 60 days, so that "Recently updated" has an order
    changed = now - timedelta(days=float(t["updatedDaysAgo"]), minutes=index)
    store.save_profile(conn, uid, _sample_profile(t), iso(changed))
    return uid


def seed_sample_talent(conn: sqlite3.Connection) -> int:
    """Write the 50 sample talent profiles of talents.json. The old sample talent is removed first."""
    for r in conn.execute("SELECT id FROM users WHERE is_sample = 1").fetchall():
        conn.execute("DELETE FROM users WHERE id = ?", (r["id"],))        # the profile, the translated skills and the applications go with it
    now = utcnow()
    talents = _read_json("talents.json")["talents"]
    for i, t in enumerate(talents):
        _add_sample_talent(conn, t, i, now)
    return len(talents)


# =====================================================================
# Demo accounts (only when the operator asks)
# =====================================================================
DEMO_EMPLOYER = "recruiter@demo.jinder.app"
DEMO_TALENT = "candidate@demo.jinder.app"
_DEMO_ALIAS = "Teal Heron"

# The demo talent: a Mid data analyst who studied in Vietnam and wants to become a data engineer. Her titles are overseas titles, so the
# translation shows the cross-border step. She has 8 skills with levels, one certification and one award. She is a strong fit for data analyst
# jobs, a medium fit for data engineering jobs, and a weak fit for backend and machine learning jobs.
_DEMO_PROFILE = {
    "qualification": ["Bachelor's degree"], "fieldOfStudy": ["Information systems"], "studyCountry": ["Vietnam"],
    "currentRole": ["BI Specialist", "MIS Executive"], "industry": ["Data"], "targetIndustries": ["Data"], "specialisation": "Data analytics",
    "level": "Mid", "yearsExperience": 4.5, "targetRole": ["Data Engineer"], "locations": ["Melbourne", "Sydney"],
    "workModes": ["Hybrid", "Remote"], "workTypes": ["Full-time"],
    "certifications": [{"name": "Microsoft Certified: Power BI Data Analyst Associate", "issuer": "Microsoft", "year": 2024}],
    "awards": [{"name": "Smart City Hackathon Runner-up", "kind": "hackathon", "year": 2023}],
    "evidence": [
        "Built the weekly sales and stock dashboards in Power BI for 6 regional teams, replacing 14 manual spreadsheets.",
        "Wrote SQL queries and Python scripts to clean and join data from 5 source systems before each monthly report.",
        "Designed the report data model (ER diagrams) for the company data warehouse together with two engineers.",
        "Started to load data with Informatica jobs for the finance reports.",
    ],
}
# (the name as the talent wrote it, the level, the years). The names that the taxonomy does not use are translated.
_DEMO_SKILLS = [("SQL", 4, 4.5), ("Python", 3, 2.5), ("Power BI", 4, 3.5), ("spreadsheets", 4, 4.5), ("Data analysis", 4, 4.0),
                ("dashboards", 3, 3.5), ("Informatica", 2, 0.8), ("ER diagrams", 3, 2.0)]


def _demo_talent_profile() -> Dict[str, Any]:
    profile = dict(_DEMO_PROFILE)
    profile["skills"] = [n for n, _, _ in _DEMO_SKILLS]
    rows = translate(profile, profile["evidence"])["skills"]
    typed = {n.lower(): (lvl, yrs) for n, lvl, yrs in _DEMO_SKILLS}
    for r in rows:
        r["status"] = "accepted"
        if r["source"] == "skill":
            # a card can join two typed names ("data cleaning; Data analysis"): it gets the highest level of them
            hits = [typed[o.strip().lower()] for o in r["original"].split(";") if o.strip().lower() in typed]
            if hits:
                r["level"] = max(h[0] for h in hits)
                r["years"] = max(h[1] for h in hits)
    profile["translation"] = rows
    return profile


def _must_coverage(profile: Dict[str, Any], skills: List[Dict[str, Any]]) -> float:
    """How much of the must-have skills of a job a sample talent has (0 to 1): each must-have counts min(1, level / needed level).
    This is a plain data check. It is used only to choose which sample talent applies to which demo job."""
    have = {r["mapped"]: store.effective_level(r) for r in profile["translation"] if r["source"] == "skill"}
    musts = [s for s in skills if s["must"]]
    if not musts:
        return 0.0
    return sum(min(1.0, have.get(s["name"], 0) / s["level"]) for s in musts) / len(musts)


def _wipe_demo(conn: sqlite3.Connection, emp_id: str, tal_id: str) -> None:
    """Remove the old story of the demo accounts (jobs, applications, alerts, activity), and keep the two accounts."""
    for r in conn.execute("SELECT id FROM jobs WHERE owner_id = ?", (emp_id,)).fetchall():
        conn.execute("DELETE FROM applications WHERE job_id = ?", (r["id"],))
        conn.execute("DELETE FROM events WHERE target_type = 'job' AND target_id = ?", (r["id"],))
        conn.execute("DELETE FROM bookmarks WHERE job_id = ?", (r["id"],))
        conn.execute("DELETE FROM skips WHERE job_id = ?", (r["id"],))
        conn.execute("DELETE FROM jobs WHERE id = ?", (r["id"],))
    conn.execute("DELETE FROM applications WHERE candidate_id = ? OR recruiter_id = ?", (tal_id, emp_id))
    for uid in (emp_id, tal_id):
        conn.execute("DELETE FROM notifications WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM email_outbox WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM events WHERE actor_id = ?", (uid,))
        conn.execute("DELETE FROM bookmarks WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM skips WHERE user_id = ?", (uid,))
    conn.execute("DELETE FROM saved_candidates WHERE recruiter_id = ?", (emp_id,))
    conn.execute("DELETE FROM skipped_candidates WHERE recruiter_id = ?", (emp_id,))


def _at(days: float) -> str:
    return iso(utcnow() + timedelta(days=days))


def seed_demo_accounts(conn: sqlite3.Connection) -> Dict[str, str]:
    """Make (or reset) the two demo accounts and a small story: jobs, applications, alerts. Returns { email: password }."""
    from .routes.applications import snapshot_match

    demo = _read_json("demo.json")
    passwords = {DEMO_EMPLOYER: security.make_demo_password(), DEMO_TALENT: security.make_demo_password()}
    emp = store.get_user_by_email(conn, DEMO_EMPLOYER)
    tal = store.get_user_by_email(conn, DEMO_TALENT)
    marker = conn.execute("SELECT value FROM schema_info WHERE key = ?", (_DEMO_KEY,)).fetchone()
    if emp and tal and marker and marker["value"] == SEED_VERSION:
        for email, pw in passwords.items():
            conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (security.hash_password(pw), email))
        conn.execute("DELETE FROM sessions WHERE user_id IN (?, ?)", (emp["id"], tal["id"]))
        return passwords
    company = demo["employer"]["company"]
    if emp and tal:
        # The accounts come from an older seed (the old story with other jobs). Keep the accounts, make the story again.
        emp_id, tal_id = emp["id"], tal["id"]
        _wipe_demo(conn, emp_id, tal_id)
        conn.execute("UPDATE users SET company = ?, name = ? WHERE id = ?", (company, demo["employer"]["name"], emp_id))
        for email, pw in passwords.items():
            conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (security.hash_password(pw), email))
        conn.execute("DELETE FROM sessions WHERE user_id IN (?, ?)", (emp_id, tal_id))
    else:
        emp_id, tal_id = new_id(), new_id()
        conn.execute("INSERT INTO users (id, role, name, email, company, alias, password_hash, onboarding, is_sample, created_at) "
                     "VALUES (?, 'recruiter', ?, ?, ?, NULL, ?, NULL, 0, ?)",
                     (emp_id, demo["employer"]["name"], DEMO_EMPLOYER, company, security.hash_password(passwords[DEMO_EMPLOYER]), _at(-60)))
        conn.execute("INSERT INTO users (id, role, name, email, company, alias, password_hash, onboarding, is_sample, created_at) "
                     "VALUES (?, 'candidate', 'Linh Nguyen', ?, NULL, ?, ?, 'done', 0, ?)",
                     (tal_id, DEMO_TALENT, _DEMO_ALIAS, security.hash_password(passwords[DEMO_TALENT]), _at(-30)))
    store.save_profile(conn, tal_id, _demo_talent_profile())
    conn.execute("INSERT OR REPLACE INTO plans (user_id, plan) VALUES (?, 'basic')", (emp_id,))

    # ----- the 4 jobs of the demo employer -----
    now = utcnow()
    job_ids: Dict[str, str] = {}
    skills_of: Dict[str, List[Dict[str, Any]]] = {}
    for i, j in enumerate(demo["jobs"]):
        row = _job_row(j, i, now, owner_id=emp_id, company=company)
        _insert_job(conn, row, j["skills"], target_applicants=[10, 8, 5, 5][i % 4])
        job_ids[j["key"]] = row["id"]
        skills_of[j["key"]] = j["skills"]

    # ----- who applies: the sample talent with the best must-have coverage for each job (one talent for one job at most) -----
    from .catalogue import find_job
    pool = {r["alias"]: r["id"] for r in conn.execute("SELECT id, alias FROM users WHERE is_sample = 1").fetchall()}
    profiles = {t["alias"]: _sample_profile(t) for t in _read_json("talents.json")["talents"] if t["alias"] in pool}
    used: set = set()

    def best(job_key: str, n: int) -> List[str]:
        ranked = sorted(profiles, key=lambda a: (-_must_coverage(profiles[a], skills_of[job_key]), a))
        pick = [a for a in ranked if a not in used][:n]
        used.update(pick)
        return [pool[a] for a in pick]

    de, be, ml, closed = ("demo-data-engineer-mid", "demo-backend-senior", "demo-ml-engineer-mid", "demo-data-engineer-contract-closed")

    def add_app(job_key: str, cand_id: str, status: str, history: List[tuple], *, note: str = "", slots: Optional[List[tuple]] = None,
                chosen: Optional[str] = None, confirmed: bool = False, shared: bool = False, offer: Optional[str] = None) -> str:
        aid = new_id()
        job = find_job(conn, job_ids[job_key])
        snapshot = store.shared_profile_of(conn, store.get_user(conn, cand_id))
        first, last = history[0][1], history[-1][1]
        conn.execute(
            """INSERT INTO applications (id, job_id, candidate_id, recruiter_id, origin, status, note, snapshot, match_json, chosen_slot_id,
                                         slot_confirmed, identity_shared, offer_text, offer_sent_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'applied', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (aid, job["id"], cand_id, emp_id, status, note, jdump(snapshot), jdump(snapshot_match(job, snapshot)), chosen,
             1 if confirmed else 0, 1 if shared else 0, offer, _at(-24) if offer else None, _at(first), _at(last)))
        for st, days, by, text in history:
            conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, ?, ?, ?, ?)", (aid, st, _at(days), by, text))
        for i, (slot_id, start) in enumerate(slots or []):
            conn.execute("INSERT INTO application_slots (id, application_id, start, position) VALUES (?, ?, ?, ?)", (slot_id, aid, start, i))
        return aid

    # The story: the demo talent is in interview for the data engineer job. One profile waits in review. One waits for an answer.
    # The ML job closes soon and has an application. A finished contract job has an accepted offer.
    slot_times = [(short_id(8), iso((utcnow() + timedelta(days=d + 2)).replace(hour=10 + d, minute=0, second=0, microsecond=0))) for d in (1, 2, 3)]
    de_a, de_b = best(de, 2)
    be_a, be_b = best(be, 2)
    ml_a = best(ml, 1)[0]
    closed_a = best(closed, 1)[0]
    add_app(de, de_a, "review", [("applied", -5, "candidate", ""), ("review", -3, "recruiter", "")])
    add_app(de, tal_id, "interview", [("applied", -5, "candidate", ""), ("review", -4, "recruiter", ""), ("interview", -2, "recruiter", "Offered 3 interview times")],
            slots=slot_times)
    a_wait = add_app(de, de_b, "applied", [("applied", -1, "candidate", "")], note="I build and run data pipelines every day and I like your lakehouse stack.")
    a_be = add_app(be, be_a, "applied", [("applied", -2, "candidate", "")])
    add_app(be, be_b, "review", [("applied", -3, "candidate", ""), ("review", -2, "recruiter", "")])
    a_ml = add_app(ml, ml_a, "applied", [("applied", -6, "candidate", "")])
    add_app(closed, closed_a, "confirmed", [("applied", -35, "candidate", ""), ("review", -33, "recruiter", ""), ("interview", -30, "recruiter", "Offered 2 interview times"),
                                             ("accepted", -25, "recruiter", ""), ("offer", -24, "recruiter", ""), ("confirmed", -22, "candidate", "Accepted the offer")],
            slots=[("past1", _at(-28))], chosen="past1", confirmed=True, shared=True, offer="6-month contract at $900 per day, starting next month.")
    interview_app = conn.execute("SELECT id FROM applications WHERE candidate_id = ?", (tal_id,)).fetchone()["id"]
    alias_of = {v: k for k, v in pool.items()}
    for aid, job_key, cand_id in ((a_wait, de, de_b), (a_be, be, be_a), (a_ml, ml, ml_a)):
        title = next(j["title"] for j in demo["jobs"] if j["key"] == job_key)
        store.notify(conn, emp_id, "new_application", f"New application for {title}", f"{alias_of[cand_id]} applied.", f"/review/{aid}")
    store.notify(conn, tal_id, "interview_slots", f"Interview times for {demo['jobs'][0]['title']}", "Choose a time that works for you.", f"/applications/{interview_app}")
    # Some activity for the charts
    rnd = random.Random(7)
    for key, jid in job_ids.items():
        for kind, n in (("job_appear", 30), ("job_watch", 12), ("job_save", 4)):
            for _ in range(n + rnd.randint(0, 6)):
                conn.execute("INSERT INTO events (type, target_type, target_id, actor_id, at) VALUES (?, 'job', ?, NULL, ?)", (kind, jid, _at(-rnd.random() * 20)))
    conn.execute("INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)", (_DEMO_KEY, SEED_VERSION))
    return passwords


# =====================================================================
# Entry point
# =====================================================================
def _marker(conn: sqlite3.Connection, key: str) -> bool:
    row = conn.execute("SELECT value FROM schema_info WHERE key = ?", (key,)).fetchone()
    return bool(row and row["value"] == SEED_VERSION)


def _set_marker(conn: sqlite3.Connection, key: str) -> None:
    conn.execute("INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)", (key, SEED_VERSION))


def seed_all(conn: sqlite3.Connection) -> Dict[str, int]:
    """Seed what is missing. Safe to run at each start. A database that has the data of an older seed gets the new data. Returns what it wrote."""
    wrote = {"jobs": 0, "talent": 0, "refreshed": 0}
    with db.transaction(conn):
        if not _marker(conn, _CATALOGUE_KEY):
            wrote["jobs"] = seed_catalogue(conn)
            _set_marker(conn, _CATALOGUE_KEY)
        else:
            wrote["refreshed"] = refresh_catalogue_dates(conn)
        if not _marker(conn, _TALENT_KEY):
            wrote["talent"] = seed_sample_talent(conn)
            _set_marker(conn, _TALENT_KEY)
    return wrote
