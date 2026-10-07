"""The seed of version 2: 50 jobs, 50 sample talent profiles and the demo accounts, from the synthetic data files."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import helpers as H
from jinder import catalogue, config, db, engine_bridge as eb, reference, seed, security, store

DATA = Path(config.SYNTHETIC_DIR)
JOBS = json.loads((DATA / "jobs.json").read_text(encoding="utf-8"))["jobs"]
TALENTS = json.loads((DATA / "talents.json").read_text(encoding="utf-8"))["talents"]
DEMO = json.loads((DATA / "demo.json").read_text(encoding="utf-8"))


def fresh_db(demo=False):
    """A new database in its own folder, with the seed. Returns (connection, folder)."""
    folder = Path(tempfile.mkdtemp(prefix="jinder-seed-"))
    path = folder / "jinder.db"
    db.init_db(path, folder / "uploads")
    conn = db.connect(path)
    seed.seed_all(conn)
    if demo:
        with db.transaction(conn):
            seed.seed_demo_accounts(conn)
    return conn, folder


def days_ago(text: str) -> float:
    return (datetime.now(timezone.utc) - datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)).total_seconds() / 86400.0


class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn, cls.folder = fresh_db()
        cls.jobs = {j["id"]: j for j in catalogue.load_jobs(cls.conn) if j["ownerId"] is None}

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        shutil.rmtree(cls.folder, True)

    def test_there_are_50_jobs_from_the_data_file(self):
        self.assertEqual(len(self.jobs), 50)
        self.assertEqual(set(self.jobs), {"job-" + j["key"] for j in JOBS})
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM jobs WHERE owner_id IS NOT NULL").fetchone()[0], 0)

    def test_every_job_has_all_the_facts(self):
        for src in JOBS:
            j = self.jobs["job-" + src["key"]]
            self.assertEqual((j["title"], j["company"], j["category"], j["specialisation"], j["level"], j["type"], j["workMode"]),
                             (src["title"], src["company"], src["domain"], src["specialisation"], src["level"], src["type"], src["workMode"]))
            self.assertEqual((j["location"], j["area"], j["minYears"], j["maxYears"], j["educationMin"]), (src["city"], src["area"], src["minYears"], src["maxYears"], src["educationMin"]))
            self.assertEqual((j["anzsco"], j["occupation"]), (str(src["occupation"]["code"]), src["occupation"]["title"]))
            self.assertEqual(j["skillRequirements"], [{"name": s["name"], "level": s["level"], "must": s["must"]} for s in src["skills"]])
            self.assertEqual(j["skills"], [s["name"] for s in src["skills"]])
            self.assertEqual(j["certifications"], src["certifications"])
            self.assertEqual(j["awards"], src["awards"])

    def test_the_description_is_complete(self):
        for src in JOBS:
            j = self.jobs["job-" + src["key"]]
            self.assertEqual(j["description"], src["description"], src["key"])      # as in the file: with the line breaks, never flattened or cut
            self.assertIn("\n", j["description"])
            self.assertNotIn("…", j["description"])
            headings = re.findall(r"^## (.+)$", j["description"], re.M)
            self.assertGreaterEqual(len(headings), 6, src["key"])
            self.assertEqual(headings[0], "About the role")
            self.assertIn("How we hire", headings)
            self.assertTrue(1200 <= len(j["description"]) <= 3500, (src["key"], len(j["description"])))

    def test_the_summary_is_the_first_sentences_of_about_the_role(self):
        for src in JOBS:
            j = self.jobs["job-" + src["key"]]
            about = re.search(r"## About the role\n\n(.+?)\n\n", src["description"], re.S).group(1)
            self.assertLessEqual(len(j["summary"]), 200)
            self.assertNotIn("#", j["summary"])
            self.assertTrue(about.startswith(j["summary"].rstrip("…")), src["key"])
            self.assertTrue(j["summary"][-1] in ".!?…")
            if not j["summary"].endswith("…"):                   # whole sentences: the next sentence did not fit
                rest = about[len(j["summary"]):].strip()
                self.assertTrue(rest == "" or len(j["summary"] + " " + re.split(r"(?<=[.!?])\s", rest)[0]) > 200, src["key"])

    def test_the_pay_is_stored_as_given_with_its_unit_and_shown_as_text(self):
        units = {"year": 0, "day": 0}
        for src in JOBS:
            j = self.jobs["job-" + src["key"]]
            sal = src["salary"]
            units[sal["unit"]] += 1
            self.assertEqual((j["salaryMin"], j["salaryMax"], j["salaryUnit"]), (sal["min"], sal["max"], sal["unit"]))
            expected = f"${sal['min']:,.0f} – ${sal['max']:,.0f} per {sal['unit']}"
            self.assertEqual(j["salary"], expected)
        self.assertEqual(units, {"year": 44, "day": 6})
        day = next(j for j in self.jobs.values() if j["salaryUnit"] == "day")
        self.assertRegex(day["salary"], r"^\$\d{1,3}(,\d{3})? – \$\d{1,3}(,\d{3})? per day$")

    def test_the_engine_gets_the_pay_as_given_and_changes_it_once(self):
        f3 = eb._load("f3")
        for j in self.jobs.values():
            d = eb.job_dict(j)
            self.assertEqual((d["salary_min"], d["salary_max"], d["salary_unit"]), (j["salaryMin"], j["salaryMax"], j["salaryUnit"]))   # not converted by the platform
            mid = (j["salaryMin"] + j["salaryMax"]) / 2.0
            expected = mid * (220.0 if j["salaryUnit"] == "day" else 1950.0 if j["salaryUnit"] == "hour" else 1.0)
            self.assertAlmostEqual(f3.get_job_salary_midpoint(d), expected, delta=1.0, msg=j["id"])
            self.assertAlmostEqual(eb.salary_midpoint(d), round(expected), delta=1)

    def test_the_dates_are_from_now(self):
        for src in JOBS:
            j = self.jobs["job-" + src["key"]]
            posted = days_ago(j["postedAt"])
            self.assertAlmostEqual(posted, src["postedDaysAgo"], delta=0.2, msg=src["key"])
            closes = -days_ago(j["closesAt"])
            self.assertAlmostEqual(closes, src["closesInDays"], delta=0.2, msg=src["key"])
            self.assertTrue(catalogue.is_open(j))
        newest = min(days_ago(j["postedAt"]) for j in self.jobs.values())
        self.assertLess(abs(newest - 1.0), 0.2)                       # the newest job is about 1 day old

    def test_old_dates_move_forward_and_a_new_start_is_safe(self):
        old = (datetime.now(timezone.utc) - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        conn, folder = fresh_db()
        try:
            conn.execute("UPDATE jobs SET posted_at = ?, closes_at = ? WHERE owner_id IS NULL", (old, old))
            self.assertEqual(seed.seed_all(conn), {"jobs": 0, "talent": 0, "refreshed": 50})
            newest = min(days_ago(j["postedAt"]) for j in catalogue.load_jobs(conn))
            self.assertLess(abs(newest - 1.0), 0.2)
        finally:
            conn.close()
            shutil.rmtree(folder, True)

    def test_the_catalogue_has_no_company_that_is_a_known_brand(self):
        companies = {j["company"] for j in self.jobs.values()}
        self.assertEqual(len(companies), 30)
        for c in companies:
            self.assertNotRegex(c, r"(?i)google|microsoft|amazon|atlassian|canva|commonwealth|telstra|woolworths|seek|linkedin|apple|meta\b")


class SampleTalentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn, cls.folder = fresh_db()
        cls.pool = {c["alias"]: c for c in store.candidate_pool(cls.conn)}

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        shutil.rmtree(cls.folder, True)

    def test_there_are_50_sample_profiles_that_cannot_sign_in(self):
        rows = self.conn.execute("SELECT * FROM users WHERE is_sample = 1").fetchall()
        self.assertEqual(len(rows), 50)
        self.assertEqual({r["alias"] for r in rows}, {t["alias"] for t in TALENTS})
        self.assertEqual(len({r["alias"].lower() for r in rows}), 50)
        for r in rows:
            self.assertEqual((r["password_hash"], r["onboarding"], r["role"]), (security.NO_LOGIN, "done", "candidate"))
            self.assertFalse(security.verify_password("anything at all", r["password_hash"]))
            self.assertTrue(r["email"].endswith("@sample.jinder.invalid"))

    def test_each_profile_has_the_facts_of_the_data_file(self):
        for t in TALENTS:
            c = self.pool[t["alias"]]
            p, shared = c["profile"], c["shared"]
            self.assertEqual((p["level"], p["yearsExperience"], p["specialisation"], p["industry"]), (t["level"], t["yearsExperience"], t["specialisation"], [t["domain"]]))
            self.assertEqual(p["years"], store.years_band(t["yearsExperience"]))
            self.assertEqual((p["locations"], p["workModes"], p["workTypes"], p["targetRole"]), (t["locations"], t["workModes"], t["workTypes"], t["targetRole"]))
            self.assertEqual(p["certifications"], [{"name": x["name"], "issuer": x["issuer"], "year": x["year"]} for x in t["certifications"]])
            self.assertEqual(p["awards"], [{"name": x["name"], "kind": x["kind"], "year": x["year"]} for x in t["awards"]])
            self.assertEqual(p["evidence"], t["evidence"])                    # private
            levels = {x["name"]: (x["level"], x["years"]) for x in t["skills"]}
            self.assertEqual({s["name"]: (s["level"], s["years"]) for s in shared["skillLevels"]}, {k: (v[0], v[1]) for k, v in levels.items()})
            self.assertEqual(shared["skills"], [x["name"] for x in t["skills"]])
            self.assertTrue(shared["roles"], t["alias"])                       # the role has its occupation: the shared profile has `roles`
            self.assertEqual(shared["roles"][0]["anzsco"], str(taxonomy_code(t["currentRole"])))
            self.assertTrue(all(c_["status"] == "accepted" for c_ in p["translation"]))

    def test_the_private_data_is_not_in_the_shared_profile(self):
        for t in TALENTS:
            text = json.dumps(self.pool[t["alias"]]["shared"])
            for line in t["evidence"]:
                self.assertNotIn(line, text)
            for country in t["studyCountry"]:
                self.assertNotIn(country, text)

    def test_the_profiles_were_changed_over_the_last_60_days(self):
        ages = sorted(days_ago(c["updated_at"]) for c in self.pool.values())
        self.assertLess(ages[0], 1.0)
        self.assertGreater(ages[-1], 55.0)
        self.assertLess(ages[-1], 61.0)
        self.assertGreaterEqual(len({int(a) for a in ages}), 45)             # spread, not all on the same day
        by_alias = {t["alias"]: t["updatedDaysAgo"] for t in TALENTS}
        for alias, c in self.pool.items():
            self.assertAlmostEqual(days_ago(c["updated_at"]), by_alias[alias], delta=0.1, msg=alias)

    def test_the_sample_talent_uses_taxonomy_names_only(self):
        t = __import__("jinder.taxonomy", fromlist=["get"]).get()
        for c in self.pool.values():
            for s in c["shared"]["skills"]:
                self.assertIsNotNone(t.skill(s), s)
            for x in c["shared"]["certifications"]:
                self.assertIn(x["name"], t.certification_names)
            for a in c["shared"]["awards"]:
                self.assertIn(a["kind"], t.award_kinds)


def taxonomy_code(role: str) -> str:
    from jinder import taxonomy
    return str(taxonomy.get().occupation_of_role(role)["code"]) if taxonomy.get().role_title(role) else ""


class SeedRunTests(unittest.TestCase):
    def test_the_seed_can_run_again(self):
        conn, folder = fresh_db()
        try:
            self.assertEqual(seed.seed_all(conn), {"jobs": 0, "talent": 0, "refreshed": 0})
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 50)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users WHERE is_sample = 1").fetchone()[0], 50)
            with db.transaction(conn):
                first = seed.seed_demo_accounts(conn)
            with db.transaction(conn):
                second = seed.seed_demo_accounts(conn)            # the second run only makes new passwords
            self.assertEqual(set(first), set(second))
            self.assertNotEqual(first, second)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 54)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0], 7)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], 52)
        finally:
            conn.close()
            shutil.rmtree(folder, True)

    def test_a_database_with_the_old_data_gets_the_new_data(self):
        conn, folder = fresh_db()
        try:
            # the old seed: an Australian job of another field, a sample profile, the markers of version 1, and a bookmark of the old job
            now = "2026-10-01T00:00:00.000Z"
            conn.execute("INSERT INTO jobs (id, owner_id, title, company, category, location, area, type, summary, description, posted_at, closes_at, created_at) "
                         "VALUES ('job-5906848725', NULL, 'Registered Nurse', 'Old Care', 'Healthcare & Nursing', 'Perth', 'Perth WA', 'Full-time', 's', 'd', ?, ?, ?)", (now, now, now))
            conn.execute("INSERT INTO job_skills (job_id, position, skill) VALUES ('job-5906848725', 0, 'Patient care')")
            conn.execute("INSERT INTO users (id, role, name, email, alias, password_hash, onboarding, is_sample, created_at) "
                         "VALUES ('old-sample', 'candidate', 'Sample profile Old Fox', 'old.fox@sample.jinder.invalid', 'Old Fox', '!', 'done', 1, ?)", (now,))
            conn.execute("INSERT INTO users (id, role, name, email, alias, password_hash, onboarding, is_sample, created_at) "
                         "VALUES ('real-user', 'candidate', 'Real User', 'real@example.test', 'Real Wolf', '!', 'done', 0, ?)", (now,))
            conn.execute("INSERT INTO bookmarks (user_id, job_id, created_at) VALUES ('real-user', 'job-5906848725', ?)", (now,))
            conn.execute("UPDATE schema_info SET value = '1' WHERE key IN ('catalogue_seed', 'sample_talent_seed')")
            self.assertEqual(seed.seed_all(conn), {"jobs": 50, "talent": 50, "refreshed": 0})
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM jobs WHERE owner_id IS NULL").fetchone()[0], 50)
            self.assertIsNone(conn.execute("SELECT 1 FROM jobs WHERE id = 'job-5906848725'").fetchone())
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM job_skills WHERE job_id = 'job-5906848725'").fetchone()[0], 0)
            self.assertIsNone(conn.execute("SELECT 1 FROM users WHERE id = 'old-sample'").fetchone())
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users WHERE is_sample = 1").fetchone()[0], 50)
            self.assertIsNotNone(conn.execute("SELECT 1 FROM users WHERE id = 'real-user'").fetchone())          # a real account stays
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM bookmarks WHERE job_id = 'job-5906848725'").fetchone()[0], 0)
        finally:
            conn.close()
            shutil.rmtree(folder, True)

    def test_the_demo_story_of_an_older_seed_is_made_again(self):
        conn, folder = fresh_db(demo=True)
        try:
            emp = store.get_user_by_email(conn, seed.DEMO_EMPLOYER)
            old_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            self.assertEqual(old_apps, 7)
            # an old database: the demo accounts have the old jobs
            conn.execute("DELETE FROM schema_info WHERE key = 'demo_seed'")
            conn.execute("UPDATE jobs SET title = 'Operations Coordinator' WHERE owner_id = ? AND id LIKE '%mid'", (emp["id"],))
            with db.transaction(conn):
                seed.seed_demo_accounts(conn)
            titles = {r["title"] for r in conn.execute("SELECT title FROM jobs WHERE owner_id = ?", (emp["id"],)).fetchall()}
            self.assertEqual(titles, {j["title"] for j in DEMO["jobs"]})
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0], 7)
            self.assertEqual(store.get_user_by_email(conn, seed.DEMO_EMPLOYER)["id"], emp["id"])      # the same account
        finally:
            conn.close()
            shutil.rmtree(folder, True)

    def test_a_new_start_with_demo_and_reset_db_comes_up_clean(self):
        folder = Path(tempfile.mkdtemp(prefix="jinder-start-"))
        try:
            env = {**os.environ, "JINDER_VAR_DIR": str(folder), "JINDER_FAST_TEST_HASH": "1"}
            for key in ("JINDER_DB_PATH", "JINDER_UPLOAD_DIR"):
                env.pop(key, None)
            code = ("import sys; sys.path.insert(0, %r)\nfrom jinder import app\ninfo = app.prepare(demo=True, reset=True)\n"
                    "print(info['seeded'], len(info['demo']), info['migrated'])\n" % str(H.ROOT))
            done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, env=env, cwd=str(folder))
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(done.stdout.strip(), "{'jobs': 50, 'talent': 50, 'refreshed': 0} 2 None")
        finally:
            shutil.rmtree(folder, True)


class DemoAccountTests(unittest.TestCase):
    """The demo accounts of the test server (made by Platform.get with demo=True)."""

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.emp = cls.p.login_demo(seed.DEMO_EMPLOYER)
        cls.tal = cls.p.login_demo(seed.DEMO_TALENT)

    def test_the_demo_employer_has_the_4_jobs_of_the_demo_file(self):
        s, r = self.api.call("GET", "/recruiter/jobs", token=self.emp["token"])
        self.assertEqual(s, 200)
        self.assertEqual(r["page"]["total"], 4)
        by_title = {j["title"]: j for j in r["items"]}
        self.assertEqual(set(by_title), {j["title"] for j in DEMO["jobs"]})
        self.assertEqual(self.emp["user"]["name"], "Alex Morgan")
        self.assertEqual(self.emp["user"]["company"], DEMO["employer"]["company"])
        badges = {j["id"]: j["badge"] for j in r["items"]}
        self.assertEqual(badges["job-demo-data-engineer-contract-closed"], "closed")
        self.assertEqual(badges["job-demo-ml-engineer-mid"], "closing")                   # closes in 4 days
        self.assertEqual(badges["job-demo-data-engineer-mid"], "open")
        closed = next(j for j in r["items"] if j["id"] == "job-demo-data-engineer-contract-closed")
        src = next(j for j in DEMO["jobs"] if j["key"] == "demo-data-engineer-contract-closed")
        self.assertEqual((closed["level"], closed["type"], closed["salary"].endswith("per " + src["salary"]["unit"])), ("Mid", "Contract", True))

    def test_the_demo_talent_tells_a_story(self):
        me = self.tal["user"]
        self.assertEqual((me["alias"], me["name"]), ("Teal Heron", "Linh Nguyen"))
        p = me["profile"]
        self.assertEqual((p["level"], p["yearsExperience"], p["studyCountry"], p["targetRole"], p["specialisation"]), ("Mid", 4.5, ["Vietnam"], ["Data Engineer"], "Data analytics"))
        skills = [c for c in p["translation"] if c["source"] == "skill"]
        self.assertEqual(len(skills), 8)
        self.assertTrue(all(1 <= c["level"] <= 5 and c["status"] == "accepted" for c in skills))
        self.assertEqual(len(p["certifications"]), 1)
        self.assertEqual(len(p["awards"]), 1)
        role = next(c for c in p["translation"] if c["source"] == "role")
        self.assertEqual((role["kind"], role["mapped"], role["anzsco"], role["original"]), ("cross-border", "Data Analyst", "224114", "BI Specialist; MIS Executive"))
        # the overseas words of skills were translated to the names of the taxonomy
        originals = {c["mapped"]: c["original"] for c in skills}
        self.assertEqual((originals["Microsoft Excel"], originals["ETL and ELT pipelines"], originals["Data modelling"]), ("spreadsheets", "Informatica", "ER diagrams"))

    def test_the_demo_talent_has_strong_medium_and_weak_jobs(self):
        s, r = self.api.call("GET", "/jobs?pageSize=50", token=self.tal["token"])
        scores = [j["match"]["score"] for j in r["items"]]
        self.assertGreaterEqual(max(scores), 70)                         # a strong job
        self.assertTrue(any(50 <= x < 65 for x in scores))               # a medium job
        self.assertLessEqual(min(scores), 40)                            # a weak job
        s, rec = self.api.call("GET", "/jobs/recommended?pageSize=5", token=self.tal["token"])
        self.assertEqual(len(rec["items"]), 5)
        self.assertTrue(all(j["match"]["score"] >= 45 for j in rec["items"]))
        self.assertTrue({"Data Analyst", "Data Engineer"} & {j["occupation"] for j in rec["items"]})   # the jobs of her target and her own field lead

    def test_the_story_has_applications_in_every_state(self):
        s, mine = self.api.call("GET", "/applications", token=self.tal["token"])
        self.assertEqual([(a["status"], a["needsAction"]) for a in mine["items"]], [("interview", True)])
        s, det = self.api.call("GET", f"/applications/{mine['items'][0]['id']}", token=self.tal["token"])
        self.assertEqual(len(det["slots"]), 3)
        s, apps = self.api.call("GET", "/recruiter/jobs/job-demo-data-engineer-mid/applications", token=self.emp["token"])
        self.assertEqual({a["status"] for a in apps["items"]}, {"applied", "review", "interview"})
        self.assertEqual(apps["page"]["total"], 3)
        for jid, count in (("job-demo-backend-senior", 2), ("job-demo-ml-engineer-mid", 1), ("job-demo-data-engineer-contract-closed", 1)):
            s, apps = self.api.call("GET", f"/recruiter/jobs/{jid}/applications", token=self.emp["token"])
            self.assertEqual(apps["page"]["total"], count, jid)
        s, st = self.api.call("GET", "/stats", token=self.emp["token"])
        self.assertEqual(st["basic"]["totalJobs"], 4)
        self.assertGreater(st["basic"]["awaitingResponse"], 0)
        s, n = self.api.call("GET", "/notifications", token=self.emp["token"])
        self.assertTrue(n["items"] and n["items"][0]["type"] == "new_application")
        s, n = self.api.call("GET", "/notifications", token=self.tal["token"])
        self.assertEqual(n["items"][0]["type"], "interview_slots")

    def test_the_applicants_are_the_samples_with_the_best_cover_of_the_must_have_skills(self):
        c = self.p.conn()
        pool = {x["id"]: x for x in store.candidate_pool(c)}
        src = {j["key"]: j for j in DEMO["jobs"]}
        checked = 0
        for key in ("demo-data-engineer-mid", "demo-backend-senior", "demo-ml-engineer-mid", "demo-data-engineer-contract-closed"):
            rows = c.execute("SELECT candidate_id FROM applications WHERE job_id = ?", ("job-" + key,)).fetchall()
            ids = [r["candidate_id"] for r in rows if pool[r["candidate_id"]]["alias"] != "Teal Heron"]
            for cid in ids:
                cover = seed._must_coverage(pool[cid]["profile"], src[key]["skills"])
                everyone = sorted((seed._must_coverage(x["profile"], src[key]["skills"]) for x in pool.values() if x["alias"] != "Teal Heron"), reverse=True)
                self.assertGreaterEqual(cover, everyone[7], (key, cover))      # among the 8 best of all the sample profiles
                self.assertGreater(cover, 0.5, key)
                checked += 1
        self.assertEqual(checked, 6)

    def test_the_demo_employer_sees_no_private_data_of_the_applicants(self):
        s, apps = self.api.call("GET", "/recruiter/jobs/job-demo-backend-senior/applications", token=self.emp["token"])
        blob = json.dumps(apps)
        for t in TALENTS:
            for line in t["evidence"]:
                self.assertNotIn(line[:40], blob)
            self.assertNotIn("sample.jinder.invalid", blob)


if __name__ == "__main__":
    unittest.main()
