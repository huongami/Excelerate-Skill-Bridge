"""Wave 4 of the BE agent: the formulas in the platform path, the skill results, the path of a job, the pay unit, the checks of the new values."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

import helpers as H
from jinder import catalogue, engine_bridge as eb, reference, seed, skills, store, translation
from jinder.routes import recruiter
from jinder.routes.jobs import talent_context
from test_v2_infra import card, job_body, make_talent


class SkillResultTests(unittest.TestCase):
    """The per-skill match of a job: the old keys and the new ones. The status words: meets -> match, below -> partial, related -> partial, missing -> gap."""

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.demo = cls.p.login_demo(seed.DEMO_TALENT)

    def test_a_job_card_has_the_skill_results_of_the_formula(self):
        s, r = self.api.call("GET", "/jobs?pageSize=50", token=self.demo["token"])
        seen = set()
        for job in r["items"]:
            m = job["match"]
            self.assertEqual(m["coverage"], round(m["coverage"]))
            for i in m["skills"]:
                self.assertEqual(set(i) - {"via"}, {"name", "status", "fitStatus", "required", "level", "must", "reason"})
                seen.add((i["status"], i["fitStatus"]))
                if i["fitStatus"] == "meets":
                    self.assertTrue(i["level"] >= i["required"])
                if i["fitStatus"] == "below":
                    self.assertTrue(i["level"] < i["required"])
                if i["fitStatus"] in ("related", "missing"):
                    self.assertIsNone(i["level"])
                self.assertIn(i["required"], range(1, 6))
                self.assertIsInstance(i["must"], bool)
            self.assertEqual(m["matchedSkills"], [i["name"] for i in m["skills"] if i["fitStatus"] == "meets"])
            self.assertEqual(m["partialSkills"], [i["name"] for i in m["skills"] if i["status"] == "partial"])
            self.assertEqual(m["gaps"], [i["name"] for i in m["skills"] if i["status"] == "gap"])
        # the four statuses of the formula map to the three old words
        self.assertEqual(seen, {("match", "meets"), ("partial", "below"), ("partial", "related"), ("gap", "missing")})

    def test_the_mapping_function(self):
        rows = [{"name": "A", "status": "meets", "need_level": 3, "have_level": 4, "must": True},
                {"name": "B", "status": "below", "need_level": 4, "have_level": 2, "must": False},
                {"name": "C", "status": "related", "need_level": 3, "have_level": None, "must": True, "related": {"name": "D", "level": 4}},
                {"name": "E", "status": "missing", "need_level": 2, "have_level": None, "must": True}]
        res = skills.results_from_breakdown(rows, 62.5)
        self.assertEqual([(i["status"], i["fitStatus"]) for i in res["items"]], [("match", "meets"), ("partial", "below"), ("partial", "related"), ("gap", "missing")])
        self.assertEqual(res["items"][2]["via"], "D")
        self.assertEqual((res["coverage"], res["matched"], res["partial"]), (63, 1, 2))
        self.assertEqual(skills.results_from_breakdown([], None)["coverage"], None)

    def test_the_match_of_the_employer_list_has_the_levels_of_the_shared_profile(self):
        e = self.p.sign_up_and_in(role="recruiter")
        s, job = self.api.call("POST", "/recruiter/jobs", job_body(skillRequirements=[{"name": "SQL", "level": 4, "must": True}, {"name": "Terraform", "level": 3, "must": False}]), token=e["token"])
        t, _ = make_talent(self.p, levels={"SQL": 2})
        s, d = self.api.call("GET", f"/recruiter/candidates/{t['user']['id']}?jobId={job['id']}", token=e["token"])
        by = {i["name"]: i for i in d["match"]["skills"]}
        self.assertEqual((by["SQL"]["status"], by["SQL"]["fitStatus"], by["SQL"]["level"], by["SQL"]["required"], by["SQL"]["must"]), ("partial", "below", 2, 4, True))
        self.assertEqual((by["Terraform"]["status"], by["Terraform"]["must"]), ("gap", False))
        self.assertEqual((d["matched"], d["partial"], d["total"]), (0, 1, 2))
        self.assertTrue(0 <= d["coverage"] <= 100)


class PathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.demo = cls.p.login_demo(seed.DEMO_TALENT)

    def test_the_path_is_the_answer_of_the_formula(self):
        c = self.p.conn()
        user = store.get_user_by_email(c, seed.DEMO_TALENT)
        jobs = catalogue.load_jobs(c)
        ctx = talent_context(c, user, jobs)
        s, r = self.api.call("GET", "/jobs?pageSize=3", token=self.demo["token"])
        for item in r["items"]:
            s, d = self.api.call("GET", f"/jobs/{item['id']}", token=self.demo["token"])
            job = next(j for j in jobs if j["id"] == item["id"])
            expected = eb.path(ctx.prepared, ctx.analyse(job)["jd"])
            self.assertEqual(d["bridge"]["path"], expected)
            path = d["bridge"]["path"]
            self.assertEqual(set(path), {"axes", "fit", "gaps", "summary"})
            self.assertTrue(path["axes"])
            for a in path["axes"]:
                self.assertEqual(set(a), {"key", "label", "group", "required", "have", "status"})
                self.assertIn(a["status"], ("gap", "fit", "above"))
                self.assertTrue(0 <= a["required"] <= 100 and 0 <= a["have"] <= 100)
            self.assertEqual((path["summary"]["fitCount"], path["summary"]["gapCount"]), (len(path["fit"]), len(path["gaps"])))
            for g in path["gaps"]:
                self.assertIn(g["kind"], ("missing", "below_level", "experience", "level", "certification"))
                self.assertGreaterEqual(g["months"], 0)
            json.dumps(path)

    def test_the_old_keys_stay_and_the_projection_is_gone(self):
        s, r = self.api.call("GET", "/jobs?pageSize=1", token=self.demo["token"])
        s, d = self.api.call("GET", f"/jobs/{r['items'][0]['id']}", token=self.demo["token"])
        b = d["bridge"]
        self.assertEqual(set(b), {"occupation", "readiness", "gaps", "path", "axes", "score"})
        self.assertEqual([a["key"] for a in b["axes"]], ["occupation", "skills", "methods", "readiness", "capability", "pay", "location", "freshness"])
        self.assertEqual(set(b["occupation"]), {"anzsco", "title", "alignment", "tier", "tierCode"})
        self.assertEqual(set(b["readiness"]), {"gapSeverity", "readiness", "months", "tier", "tierCode", "statutoryBlocker"})
        self.assertFalse(b["readiness"]["statutoryBlocker"])
        for g in b["gaps"]:
            self.assertEqual(set(g), {"name", "category", "categoryName", "months", "blocker"})
            self.assertFalse(g["blocker"])
        self.assertFalse(hasattr(eb, "projection"))
        self.assertFalse(hasattr(eb, "OccupationIndex"))
        self.assertFalse(hasattr(recruiter, "_areas"))
        self.assertFalse(hasattr(recruiter, "_order_value"))

    def test_the_talent_who_fits_has_a_short_path(self):
        t, _ = make_talent(self.p, levels={"Python": 5, "SQL": 5, "Git": 5})
        e = self.p.sign_up_and_in(role="recruiter")
        s, job = self.api.call("POST", "/recruiter/jobs", job_body(level="Mid", skillRequirements=[
            {"name": "Python", "level": 3, "must": True}, {"name": "SQL", "level": 3, "must": True}, {"name": "Terraform", "level": 4, "must": True}]), token=e["token"])
        s, d = self.api.call("GET", f"/jobs/{job['id']}", token=t["token"])
        path = d["bridge"]["path"]
        self.assertTrue(any(g["label"] == "Terraform" and g["kind"] == "missing" and g["must"] for g in path["gaps"]))
        self.assertTrue(any(f["label"] in ("Python", "SQL") for f in path["fit"]))
        self.assertGreater(path["summary"]["monthsToClose"], 0)


class PayUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_the_unit_comes_from_the_text(self):
        for text, expected in (("$900 per day", (900.0, 900.0, "day")), ("$800 - $950 a day", (800.0, 950.0, "day")), ("$70 – $90 per hour", (70.0, 90.0, "hour")),
                               ("$120,000 per year", (120000.0, 120000.0, "year")), ("$150,000 – $170,000", (150000.0, 170000.0, "year")),
                               ("$100k to $120k", (100000.0, 120000.0, "year")), ("Market competitive", (None, None, "year")), ("", (None, None, "year")),
                               ("Day rate $850", (850.0, 850.0, "day")), ("$95 an hour", (95.0, 95.0, "hour"))):
            self.assertEqual(catalogue.parse_salary(text), expected, text)
        self.assertEqual(catalogue.money_text(900, 900, "day"), "$900 per day")
        self.assertEqual(catalogue.money_text(150000, 170000, "year"), "$150,000 – $170,000 per year")
        self.assertEqual(catalogue.money_text(None, None, "year"), "Market competitive")

    def test_an_employer_job_stores_the_pay_as_written_with_its_unit(self):
        e = self.p.sign_up_and_in(role="recruiter")
        s, j = self.api.call("POST", "/recruiter/jobs", job_body(salary="$900 per day", type="Contract"), token=e["token"])
        self.assertEqual(s, 200, j)
        row = self.p.conn().execute("SELECT salary, salary_min, salary_max, salary_unit FROM jobs WHERE id = ?", (j["id"],)).fetchone()
        self.assertEqual(tuple(row), ("$900 per day", 900.0, 900.0, "day"))
        t, _ = make_talent(self.p)
        s, d = self.api.call("GET", f"/jobs/{j['id']}", token=t["token"])
        self.assertEqual((d["salary"], d["salaryUnit"]), ("$900 per day", "day"))
        self.assertNotIn("salaryMin", d)                       # the numbers stay on the server
        c = self.p.conn()
        job = catalogue.find_job(c, j["id"])
        dd = eb.job_dict(job)
        self.assertEqual((dd["salary_min"], dd["salary_max"], dd["salary_unit"]), (900.0, 900.0, "day"))
        self.assertAlmostEqual(eb._load("f3").get_job_salary_midpoint(dd), 900 * 220, delta=1)
        # the edit changes the unit with the text
        s, j2 = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"salary": "$130,000 – $150,000 per year"}, token=e["token"])
        row = self.p.conn().execute("SELECT salary_min, salary_max, salary_unit FROM jobs WHERE id = ?", (j["id"],)).fetchone()
        self.assertEqual(tuple(row), (130000.0, 150000.0, "year"))
        s, j3 = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"salary": "   "}, token=e["token"])
        row = self.p.conn().execute("SELECT salary, salary_min, salary_max, salary_unit FROM jobs WHERE id = ?", (j["id"],)).fetchone()
        self.assertEqual(tuple(row), ("Market competitive", None, None, "year"))

    def test_a_day_rate_is_not_a_cheap_job_for_the_formulas(self):
        # a day rate of $900 is a yearly pay of about $198,000. If the platform did not use the unit, the job would look like a pay of $900 a year.
        e = self.p.sign_up_and_in(role="recruiter")
        t, _ = make_talent(self.p)
        s, day = self.api.call("POST", "/recruiter/jobs", job_body(salary="$900 per day", type="Contract", title="Data Engineer"), token=e["token"])
        s, year = self.api.call("POST", "/recruiter/jobs", job_body(salary="$198,000 per year", title="Data Engineer"), token=e["token"])
        c = self.p.conn()
        user = store.get_user(c, t["user"]["id"])
        jobs = catalogue.load_jobs(c)
        ctx = talent_context(c, user, jobs)
        pay = {k: ctx.analyse(next(j for j in jobs if j["id"] == v["id"]))["feed"]["sub_metrics"]["s_wage_upside"] for k, v in (("day", day), ("year", year))}
        self.assertAlmostEqual(pay["day"], pay["year"], delta=0.2)


class NewValueChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def save(self, t, **profile):
        s, me = self.api.call("PATCH", "/me", {"profile": profile}, token=t["token"])
        self.assertEqual(s, 200, me)
        return me["profile"]

    def test_the_domain_the_specialisation_and_the_work_modes_are_checked(self):
        t = self.p.sign_up_and_in()
        p = self.save(t, industry=["Healthcare", "Data", "Retail"], targetIndustries=["Software Engineering", "Education"], specialisation="Backend",
                      workModes=["Hybrid", "Space", "Remote"], locations=["Sydney", "Mars"])
        self.assertEqual((p["industry"], p["targetIndustries"], p["specialisation"], p["workModes"]), (["Data"], ["Software Engineering"], "Backend", ["Hybrid", "Remote"]))
        for bad in ("Plumbing", 5, None, "backend"):
            self.assertEqual(self.save(t, specialisation=bad)["specialisation"], "", bad)

    def test_the_years_of_a_skill_are_kept_and_cleaned(self):
        t, prof = make_talent(self.p)
        rows = prof["translation"]
        skill_rows = [r for r in rows if r["source"] == "skill"]
        given = [3.46, 0, 40, 41, -1, "x", True, None, 2]
        for r, y in zip(skill_rows, given):
            r["years"] = y
        for r in rows:
            if r["source"] != "skill":
                r["years"] = 5
        saved = self.save(t, **prof)["translation"]
        by = {r["id"]: r["years"] for r in saved}
        self.assertEqual([by[r["id"]] for r in skill_rows[:len(given)]], [3.5, 0, 40, None, None, None, None, None, 2][:len(skill_rows)])
        self.assertTrue(all(r["years"] is None for r in saved if r["source"] != "skill"))
        s, shared = self.api.call("GET", "/me/shared-profile", token=t["token"])
        self.assertEqual({x["name"]: x["years"] for x in shared["skillLevels"]}[skill_rows[0]["mapped"]], 3.5)

    def test_a_skill_that_is_a_dictionary_in_the_profile_keeps_its_name(self):
        t = self.p.sign_up_and_in()
        p = self.save(t, skills=[{"name": "SQL", "level": 4}, {"name": "Python"}, "Git", {"level": 3}, 5])
        self.assertEqual(p["skills"], ["SQL", "Python", "Git", "5"])

    def test_the_summary_is_made_of_whole_sentences(self):
        text = "## About the role\n\n" + " ".join(["This is sentence number %d of the text, written to be quite long." % i for i in range(1, 9)])
        s = catalogue.summary_of(text)
        self.assertLessEqual(len(s), 200)
        self.assertTrue(s.endswith("."))
        self.assertTrue(s.startswith("This is sentence number 1"))
        self.assertNotIn("…", s)
        one = catalogue.summary_of("A" * 20 + (" word" * 60) + ". Short.")
        self.assertTrue(one.endswith("…") and len(one) <= 200)

    def test_the_suggestion_of_skills_for_a_job(self):
        e = self.p.sign_up_and_in(role="recruiter")
        s, r = self.api.call("POST", "/recruiter/jobs/suggest-skills", {"title": "Senior Data Engineer, Lakehouse", "description": "You will build Spark and Databricks pipelines in Python.",
                                                                       "category": "Data"}, token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual(r["skills"], [x["name"] for x in r["skillRequirements"]])
        self.assertTrue({"Apache Spark", "Databricks", "Python"} <= set(r["skills"]))
        self.assertTrue(all(x["level"] == 3 and x["must"] is True and x["name"] in reference.SKILL_NAMES for x in r["skillRequirements"]))
        self.assertLessEqual(len(r["skills"]), 10)
        s, r = self.api.call("POST", "/recruiter/jobs/suggest-skills", {"title": "Wizard", "description": "", "category": "AI & Machine Learning"}, token=e["token"])
        self.assertEqual(r["skills"][:3], reference.SKILL_SUGGESTIONS["AI & Machine Learning"][:3])      # no role and no skill in the text: the usual skills of the domain
        s, r = self.api.call("POST", "/recruiter/jobs/suggest-skills", {}, token=e["token"])
        self.assertEqual((s, r["skills"]), (200, []))

    def test_the_occupation_of_an_employer_job_comes_from_the_taxonomy(self):
        e = self.p.sign_up_and_in(role="recruiter")
        for title, category, spec, code in (("Senior Data Engineer, Lakehouse", "Data", None, "262111"), ("Mobile App Wizard", "Software Engineering", "Mobile", "261312"),
                                            ("iOS Developer", "Software Engineering", None, "261312"), ("The Boss", "Data", None, "")):
            body = job_body(title=title, category=category)
            if spec:
                body["specialisation"] = spec
            s, j = self.api.call("POST", "/recruiter/jobs", body, token=e["token"])
            self.assertEqual(s, 200, j)
            row = self.p.conn().execute("SELECT anzsco, occupation FROM jobs WHERE id = ?", (j["id"],)).fetchone()
            self.assertEqual(row["anzsco"], code, title)
            self.assertEqual(bool(row["occupation"]), bool(code), title)


class CompareErrorTests(unittest.TestCase):
    """A refused comparison names the ids that cannot be compared (`missing`, next to `error`), so that the page can mark them."""

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.t, _ = make_talent(cls.p)
        cls.e = cls.p.sign_up_and_in(role="recruiter")
        cls.api.call("PUT", "/entitlements", {"plan": "premium"}, token=cls.e["token"])
        s, cls.job = cls.api.call("POST", "/recruiter/jobs", job_body(), token=cls.e["token"])
        s, r = cls.api.call("GET", "/jobs?pageSize=8", token=cls.t["token"])
        cls.job_ids = [j["id"] for j in r["items"]]
        s, r = cls.api.call("GET", f"/recruiter/candidates?jobId={cls.job['id']}&pageSize=10", token=cls.e["token"])
        cls.cand_ids = [c["id"] for c in r["items"]]

    def test_jobs_that_do_not_exist(self):
        ids = [self.job_ids[0], "job-gone", self.job_ids[1], "job-gone-too"]
        s, r = self.api.call("GET", "/jobs/compare?ids=" + ",".join(ids), token=self.t["token"])
        self.assertEqual(s, 404)
        self.assertEqual(r["missing"], ["job-gone", "job-gone-too"])
        self.assertEqual((r["error"]["code"], r["error"]["message"]), ("NOT_FOUND", "This job does not exist or was removed."))
        self.assertIn("ids", r["error"]["fields"])

    def test_too_many_jobs_name_the_ones_above_the_limit(self):
        ids = self.job_ids[:7]
        s, r = self.api.call("GET", "/jobs/compare?ids=" + ",".join(ids), token=self.t["token"])
        self.assertEqual((s, r["error"]["fields"]["ids"], r["missing"]), (400, "Choose 2 to 5 jobs to compare.", ids[5:]))
        s, r = self.api.call("GET", "/jobs/compare?ids=" + ids[0], token=self.t["token"])
        self.assertEqual((s, r["missing"]), (400, []))

    def test_profiles_that_cannot_be_compared(self):
        ids = [self.cand_ids[0], "nobody", self.cand_ids[1]]
        s, r = self.api.call("GET", f"/recruiter/compare?ids={','.join(ids)}&jobId={self.job['id']}", token=self.e["token"])
        self.assertEqual(s, 404)
        self.assertEqual(r["missing"], ["nobody"])
        self.assertEqual((r["error"]["code"], r["error"]["message"]), ("NOT_FOUND", "We can't find one of the profiles."))
        self.assertIn("ids", r["error"]["fields"])

    def test_too_many_profiles(self):
        ids = self.cand_ids[:7]
        s, r = self.api.call("GET", f"/recruiter/compare?ids={','.join(ids)}&jobId={self.job['id']}", token=self.e["token"])
        self.assertEqual((s, r["error"]["fields"]["ids"], r["missing"]), (400, "Choose 2 to 5 profiles to compare.", ids[5:]))

    def test_a_good_request_has_no_missing_key(self):
        s, r = self.api.call("GET", f"/recruiter/compare?ids={self.cand_ids[0]},{self.cand_ids[1]}&jobId={self.job['id']}", token=self.e["token"])
        self.assertEqual(s, 200)
        self.assertNotIn("missing", r)


class PremiumInsightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_the_insights_use_the_skills_and_the_levels(self):
        t, _ = make_talent(self.p, levels={"Python": 2, "SQL": 5})
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=t["token"])
        s, st = self.api.call("GET", "/stats", token=t["token"])
        adv = st["advanced"]
        self.assertGreater(adv["basis"], 0)
        self.assertTrue(adv["gapRanking"] and adv["demandForYourSkills"])
        for row in adv["gapRanking"]:
            self.assertEqual(set(row), {"skill", "count", "needLevel", "yourLevel", "missing", "below"})
            self.assertEqual(row["count"], row["missing"] + row["below"])
            self.assertIn(row["skill"], reference.SKILL_NAMES)
        for row in adv["demandForYourSkills"]:
            self.assertEqual(set(row), {"skill", "count", "needLevel", "yourLevel"})
            self.assertGreaterEqual(row["yourLevel"], 1)
        counts = [r["count"] for r in adv["gapRanking"]]
        self.assertEqual(counts, sorted(counts, reverse=True))


class HashCostTests(unittest.TestCase):
    """The weak password hash for the tests is never the default."""

    def cost(self, flag):
        env = {k: v for k, v in __import__("os").environ.items() if k != "JINDER_FAST_TEST_HASH"}
        if flag:
            env["JINDER_FAST_TEST_HASH"] = "1"
        code = f"import sys; sys.path.insert(0, {str(H.ROOT)!r}); from jinder import security; print(security._SCRYPT_N, security.hash_password('x').split('$')[1])"
        done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.split()

    def test_the_default_is_the_strong_hash(self):
        self.assertEqual(self.cost(False), ["16384", "16384"])

    def test_only_the_variable_makes_it_fast(self):
        self.assertEqual(self.cost(True), ["16", "16"])

    def test_a_hash_is_checked_with_the_cost_that_it_has(self):
        import base64
        import hashlib
        from jinder import security
        salt = b"0123456789abcdef"
        digest = hashlib.scrypt(b"a password", salt=salt, n=16, r=8, p=1, dklen=32)
        weak = "scrypt$16$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()
        self.assertTrue(security.verify_password("a password", weak))            # the cost is in the stored text: any server can check it
        self.assertFalse(security.verify_password("another password", weak))
        self.assertTrue(security.verify_password("a password", security.hash_password("a password")))


if __name__ == "__main__":
    unittest.main()
