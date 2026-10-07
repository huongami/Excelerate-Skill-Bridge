"""The fit score with one decimal, the radar values, and the comparison of jobs and of profiles."""
import json
import math
import unittest
from datetime import datetime, timedelta, timezone

import helpers as H
from test_talent_flow import onboard


def iso_in(days=0):
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class TalentRadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.t = cls.p.sign_up_and_in()
        onboard(cls.p, cls.t)

    def get(self, path):
        return self.api.call("GET", path, token=self.t["token"])

    def test_the_fit_score_has_one_decimal_and_orders_the_jobs(self):
        s, r = self.get("/jobs/recommended?pageSize=20")
        scores = [j["match"]["score"] for j in r["items"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(isinstance(x, float) and 0 <= x <= 100 and round(x, 1) == x for x in scores))
        self.assertGreater(len(set(scores)), len(scores) // 2, "jobs should seldom have the same score")
        self.assertTrue(all(j["match"]["rank"] == math.floor(j["match"]["score"] + 0.5) for j in r["items"]))   # rank is the score as a whole number

    def test_the_job_detail_has_eight_axes(self):
        s, r = self.get("/jobs/recommended?pageSize=1")
        s, d = self.get(f"/jobs/{r['items'][0]['id']}")
        b = d["bridge"]
        self.assertEqual([a["key"] for a in b["axes"]], ["occupation", "skills", "methods", "readiness", "capability", "pay", "location", "freshness"])
        self.assertEqual({a["formula"] for a in b["axes"]}, {"F1", "F2", "F5"})
        for a in b["axes"]:
            self.assertTrue(0 <= a["value"] <= 100 and round(a["value"], 1) == a["value"], a)
        self.assertEqual(b["score"], d["match"]["score"])

    def test_compare_two_to_five_jobs(self):
        s, r = self.get("/jobs/recommended?pageSize=6")
        ids = [j["id"] for j in r["items"]]
        s, c = self.get("/jobs/compare?ids=" + ",".join(ids[:2]))
        self.assertEqual(s, 200)
        self.assertEqual(len(c["jobs"]), 2)
        self.assertEqual(len(c["pairs"]), 1)
        self.assertEqual([a["key"] for a in c["axes"]][:2], ["occupation", "skills"])
        for j in c["jobs"]:
            self.assertEqual(len(j["axes"]), 8)
            self.assertIn("score", j["match"])
            self.assertGreater(j["salaryMidpoint"], 0)
        pair = c["pairs"][0]
        self.assertEqual({pair["a"], pair["b"]}, set(ids[:2]))
        self.assertTrue(0 <= pair["index"] <= 100)
        self.assertEqual([p["key"] for p in pair["parts"]], ["taxonomy", "requirements", "salary", "sector", "place"])
        # every pair: 3 jobs give 3 pairs, 4 give 6, 5 give 10 (version 2: up to 5 jobs)
        for n, pairs in ((3, 3), (4, 6), (5, 10)):
            s, cn = self.get("/jobs/compare?ids=" + ",".join(ids[:n]))
            self.assertEqual((s, len(cn["jobs"]), len(cn["pairs"])), (200, n, pairs))
            self.assertEqual({(p["a"], p["b"]) for p in cn["pairs"]}, {(ids[a], ids[b]) for a in range(n) for b in range(a + 1, n)})

    def test_compare_input_is_checked(self):
        s, r = self.get("/jobs/recommended?pageSize=6")
        ids = [j["id"] for j in r["items"]]
        for query in ("", ids[0], ",".join(ids), f"{ids[0]},{ids[0]}"):    # none, one, six, one twice
            s, e = self.get("/jobs/compare?ids=" + query)
            self.assertEqual((s, e["error"]["fields"]["ids"]), (400, "Choose 2 to 5 jobs to compare."), query)
        s, e = self.get(f"/jobs/compare?ids={ids[0]},nope")
        self.assertEqual(s, 404)

    def test_compare_is_for_talent_only(self):
        e = self.p.sign_up_and_in(role="recruiter")
        self.assertEqual(self.api.call("GET", "/jobs/compare?ids=a,b", token=e["token"])[0], 403)
        self.assertEqual(self.api.call("GET", "/jobs/compare?ids=a,b")[0], 401)


class EmployerRadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_the_radar_of_two_profiles(self):
        e = self.p.sign_up_and_in(role="recruiter")
        s, job = self.api.call("POST", "/recruiter/jobs", {"title": "Data Analyst", "category": "Data", "location": "Sydney", "type": "Full-time",
                                                           "skills": ["SQL", "Power BI", "Microsoft Excel"], "targetApplicants": 2, "closesAt": iso_in(9),
                                                           "description": "Build dashboards, write SQL queries and report on the numbers every week."}, token=e["token"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        s, r = self.api.call("GET", f"/recruiter/candidates?jobId={job['id']}", token=e["token"])
        a, b = r["items"][0]["id"], r["items"][3]["id"]
        # version 2: ids=a,b (2 to 5 ids) and jobId. The radar has one series for each profile.
        s, c = self.api.call("GET", f"/recruiter/compare?ids={a},{b}&jobId={job['id']}", token=e["token"])
        self.assertEqual(s, 200)
        radar = c["radar"]
        self.assertEqual([x["key"] for x in radar["axes"]], ["coverage", "requirement", "seniority", "statutory", "depth", "experience", "transferable", "level", "evidence"])
        self.assertEqual(radar["axes"][3]["label"], "Certification readiness")        # it was "Licence readiness" in version 1
        self.assertEqual([x["id"] for x in radar["series"]], [a, b])
        for series in radar["series"]:
            self.assertEqual(len(series["values"]), 9)
            for v in series["values"]:
                self.assertTrue(0 <= v <= 100)
        self.assertNotIn("total", json.dumps(radar).lower())
        self.assertNotIn("relative_merit", json.dumps(c).lower())
        # the first axis is the per-skill coverage that the table above shows
        self.assertEqual(radar["series"][0]["values"][0], float(r["items"][0]["coverage"]))

    def test_a_job_is_needed_for_the_comparison(self):
        e = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        s, r = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        s, c = self.api.call("GET", f"/recruiter/compare?ids={r['items'][0]['id']},{r['items'][1]['id']}", token=e["token"])
        self.assertEqual((s, c["error"]["fields"]["jobId"]), (400, "Choose one of your jobs."))


if __name__ == "__main__":
    unittest.main()
