"""Version 2, wave 1: pages and sorting on every list, compare of 2 to 5, the new profile and job keys, the Premium benefits.

See docs/V2_PLAN.md (sections 4 and 5) and docs/changes/BE.md.
"""
import json
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import helpers as H
from jinder import catalogue, parsing, reference, store
from jinder.routes.recruiter import _positions
from jinder.util import ApiError, page_params, paginate

# The skills of a talent that these tests make. The tests build the profile themselves: they do not depend on the CV reader.
SKILLS = ["Microsoft Excel", "SQL", "Python", "Power BI", "Data modelling", "Git", "Data visualisation", "Stakeholder management", "Communication"]


def card(i, mapped, source="skill", status="accepted", evidence="Moderate", level=None, **over):
    """One translated skill, as the profile stores it."""
    return {"id": f"card-{i}", "source": source, "original": f"Original {i}", "mapped": mapped, "kind": "direct", "anzsco": "", "occupation": "",
            "reason": "A card made by a test.", "evidence": evidence, "evidenceText": "", "status": status, "level": level, **over}


def make_talent(p, t=None, skills=SKILLS, levels=None, **profile):
    """Give a talent a finished profile (skills, one role, one qualification) and return (talent, saved profile).

    `levels` is a dictionary: skill name -> level (1 to 5). `profile` replaces keys of the profile.
    """
    t = t or p.sign_up_and_in()
    levels = levels or {}
    cards = [card(i, name, level=levels.get(name)) for i, name in enumerate(skills)]
    cards.append(card(90, "Data Analyst", source="role", anzsco="224114", occupation="Data Analyst", original="BI Specialist"))
    cards.append(card(91, "AQF Level 7 (Bachelor degree)", source="qualification", original="Bachelor's degree (overseas)"))
    body = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Information systems"], "studyCountry": ["Vietnam"], "currentRole": ["BI Specialist"],
            "industry": ["Data"], "years": "3–5 years", "skills": list(skills), "targetRole": ["Data Engineer"],
            "targetIndustries": [], "locations": ["Melbourne"], "workTypes": ["Full-time"], "evidence": [], "translation": cards, **profile}
    s, me = p.api.call("PATCH", "/me", {"profile": body, "onboarding": "done"}, token=t["token"])
    assert s == 200, (s, me)
    return t, me["profile"]


def iso_in(days=0):
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def job_body(**over):
    body = {"title": "Data Engineer", "category": "Data", "location": "Sydney", "type": "Full-time",
            "skills": ["Python", "SQL", "Microsoft Excel"], "targetApplicants": 5, "closesAt": iso_in(20),
            "description": "Build and run the services behind our product, and work with the data team every day."}
    body.update(over)
    return body


def long_jd(size):
    """A job description with headings and bullets, exactly `size` characters long."""
    text = "## About the role\nWe build the tools that help people find work.\n## What you will do\n"
    n = 0
    while len(text) < size:
        n += 1
        text += f"- Task number {n}: design, build, test and run one part of the product.\n"
    return text[:size - 1] + "."


# =====================================================================
# The helper for pages and sorting (util.py)
# =====================================================================
class PageHelperTests(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(tuple(page_params({}, ("best", "newest"))), (1, 10, "best"))
        self.assertEqual(tuple(page_params({"sort": ""}, ("newest",))), (1, 10, "newest"))

    def test_page_size_is_set_to_1_to_50(self):
        for given, expected in (("0", 1), ("-4", 1), ("1", 1), ("25", 25), ("50", 50), ("51", 50), ("500", 50), ("abc", 10), ("2.5", 10), ("", 10)):
            self.assertEqual(page_params({"pageSize": given}, ("best",)).page_size, expected, given)

    def test_a_bad_page_is_page_1(self):
        for given, expected in (("0", 1), ("-3", 1), ("abc", 1), ("7", 7)):
            self.assertEqual(page_params({"page": given}, ("best",)).page, expected, given)

    def test_a_bad_sort_is_a_400_for_the_field_sort(self):
        with self.assertRaises(ApiError) as cm:
            page_params({"sort": "oldest"}, ("best", "newest"))
        self.assertEqual((cm.exception.status, cm.exception.code, set(cm.exception.fields)), (400, "VALIDATION_ERROR", {"sort"}))
        self.assertEqual(cm.exception.fields["sort"], "Use one of these: best, newest.")

    def test_the_page_object(self):
        items = list(range(25))
        params = page_params({"pageSize": "10"}, ("best",))
        chunk, page = paginate(items, params)
        self.assertEqual((chunk, page), (list(range(10)), {"page": 1, "pageSize": 10, "total": 25, "totalPages": 3}))
        chunk, page = paginate(items, page_params({"pageSize": "10", "page": "3"}, ("best",)))
        self.assertEqual((chunk, page["page"]), ([20, 21, 22, 23, 24], 3))
        chunk, page = paginate(items, page_params({"pageSize": "10", "page": "99"}, ("best",)))       # above the last page: the last page
        self.assertEqual((chunk, page["page"]), ([20, 21, 22, 23, 24], 3))
        chunk, page = paginate([], params)                                                           # an empty list has one empty page
        self.assertEqual((chunk, page), ([], {"page": 1, "pageSize": 10, "total": 0, "totalPages": 1}))

    def test_a_cap_gives_one_page_and_the_real_total(self):
        chunk, page = paginate(list(range(12)), page_params({"page": "2", "pageSize": "50"}, ("best",)), cap=5)
        self.assertEqual((chunk, page), ([0, 1, 2, 3, 4], {"page": 1, "pageSize": 5, "total": 12, "totalPages": 1}))


class SkillLevelHelperTests(unittest.TestCase):
    def test_the_level_of_a_skill_with_no_level_is_the_level_of_its_evidence(self):
        self.assertEqual(store.effective_level({"level": 5, "evidence": "Limited"}), 5)
        self.assertEqual([store.effective_level({"level": None, "evidence": e}) for e in ("Strong", "Moderate", "Limited")], [4, 3, 2])
        self.assertEqual(store.effective_level({"level": 9, "evidence": "Strong"}), 4)       # not a level: the evidence decides
        self.assertEqual(store.effective_level({}), 3)

    def test_job_requirements_default_to_level_3_and_must(self):
        self.assertEqual(catalogue.requirements_of({"skills": ["A", "B"], "skillRequirements": []}),
                         [{"name": "A", "level": 3, "must": True}, {"name": "B", "level": 3, "must": True}])
        given = [{"name": "A", "level": 5, "must": False}]
        self.assertEqual(catalogue.requirements_of({"skills": ["A"], "skillRequirements": given}), given)


# =====================================================================
# The lists of the talent
# =====================================================================
class TalentListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.t = cls.p.sign_up_and_in()
        make_talent(cls.p, cls.t)

    def get(self, path, token=None):
        return self.api.call("GET", path, token=token or self.t["token"])

    def count_events(self, user_id, kind):
        return self.p.conn().execute("SELECT COUNT(*) FROM events WHERE actor_id = ? AND type = ?", (user_id, kind)).fetchone()[0]

    def test_recommended_page_1_page_2_and_the_last_page(self):
        s, p1 = self.get("/jobs")
        self.assertEqual(s, 200)
        total = p1["page"]["total"]
        self.assertGreater(total, 25)
        self.assertEqual(p1["page"], {"page": 1, "pageSize": 10, "total": total, "totalPages": -(-total // 10)})
        self.assertEqual((p1["sort"], len(p1["items"])), ("best", 10))
        self.assertNotIn("limit", p1)
        s, p2 = self.get("/jobs?page=2")
        self.assertEqual(p2["page"]["page"], 2)
        self.assertFalse({j["id"] for j in p1["items"]} & {j["id"] for j in p2["items"]}, "page 2 has other jobs than page 1")
        last = p1["page"]["totalPages"]
        s, pl = self.get(f"/jobs?page={last}")
        self.assertEqual(len(pl["items"]), total - 10 * (last - 1))
        s, beyond = self.get(f"/jobs?page={last + 5}")
        self.assertEqual(([j["id"] for j in beyond["items"]], beyond["page"]["page"]), ([j["id"] for j in pl["items"]], last))

    def test_the_page_size_is_set_to_1_to_50(self):
        for given, expected in (("500", 50), ("0", 1), ("-1", 1), ("7", 7), ("abc", 10)):
            s, r = self.get(f"/jobs?pageSize={given}")
            self.assertEqual((r["page"]["pageSize"], len(r["items"])), (expected, expected), given)

    def test_the_pages_in_a_row_are_the_list_in_one_piece(self):
        s, whole = self.get("/jobs?pageSize=50")
        ids = [j["id"] for j in whole["items"]]
        pieces = []
        for page in range(1, 6):
            s, r = self.get(f"/jobs?pageSize=10&page={page}")
            pieces += [j["id"] for j in r["items"]]
        self.assertEqual(pieces, ids)                       # the same order each time: the order is stable
        s, again = self.get("/jobs?pageSize=50")
        self.assertEqual([j["id"] for j in again["items"]], ids)

    def test_best_is_in_score_order_and_a_tie_is_broken_by_the_id(self):
        s, r = self.get("/jobs?pageSize=50&sort=best")
        keys = [(-j["match"]["score"], j["id"]) for j in r["items"]]
        self.assertEqual(keys, sorted(keys))

    def test_newest_is_in_date_order_and_a_tie_is_broken_by_the_id(self):
        s, r = self.get("/jobs?pageSize=50&sort=newest")
        self.assertEqual(r["sort"], "newest")
        dates = [j["postedAt"] for j in r["items"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for a, b in zip(r["items"], r["items"][1:]):
            if a["postedAt"] == b["postedAt"]:
                self.assertLess(a["id"], b["id"])

    def test_a_bad_sort_is_a_400_for_the_field_sort_on_every_talent_list(self):
        for path in ("/jobs/recommended?sort=oldest", "/jobs?sort=saved", "/jobs/recommended?sort=saved", "/bookmarks?sort=oldest", "/applications?sort=best2"):
            s, r = self.get(path)
            self.assertEqual((s, r["error"]["code"], list(r["error"]["fields"])), (400, "VALIDATION_ERROR", ["sort"]), path)

    def test_limit_is_gone(self):
        s, r = self.get("/jobs?limit=3")
        self.assertEqual(len(r["items"]), 10)

    def test_the_recommended_list_has_pages_too(self):
        s, r = self.get("/jobs/recommended?pageSize=3")
        total = r["page"]["total"]
        self.assertGreaterEqual(total, 4)                    # the jobs with a match score of 45 or more
        self.assertEqual((len(r["items"]), r["sort"], r["page"]["totalPages"]), (3, "best", -(-total // 3)))
        self.assertTrue(all(j["match"]["recommended"] and j["match"]["score"] >= 45 for j in r["items"]))
        s, last = self.get(f"/jobs/recommended?pageSize=3&page={r['page']['totalPages']}")
        self.assertEqual(len(last["items"]), total - 3 * (r["page"]["totalPages"] - 1))
        scores = [j["match"]["score"] for j in r["items"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_search_has_pages_and_sorts(self):
        s, all_hits = self.get("/jobs?q=engineer&pageSize=50")
        total = all_hits["page"]["total"]
        self.assertGreater(total, 6)
        self.assertEqual(all_hits["total"], total)           # the old key stays
        s, p2 = self.get("/jobs?q=engineer&pageSize=3&page=2")
        self.assertEqual([j["id"] for j in p2["items"]], [j["id"] for j in all_hits["items"][3:6]])
        s, newest = self.get("/jobs?q=engineer&pageSize=50&sort=newest")
        dates = [j["postedAt"] for j in newest["items"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertEqual(newest["page"]["total"], total)

    def test_appear_events_are_for_the_jobs_of_the_page_only(self):
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        uid = t["user"]["id"]
        self.assertEqual(self.count_events(uid, "job_appear"), 0)
        self.get("/jobs?pageSize=3", t["token"])
        self.assertEqual(self.count_events(uid, "job_appear"), 3)
        self.get("/jobs?pageSize=3&page=2", t["token"])
        self.assertEqual(self.count_events(uid, "job_appear"), 6)
        self.get("/jobs?pageSize=4", t["token"])
        self.assertEqual(self.count_events(uid, "job_appear"), 10)
        self.get("/jobs?pageSize=2&sort=bad", t["token"])      # a refused request tracks nothing
        self.assertEqual(self.count_events(uid, "job_appear"), 10)

    def test_bookmarks_pages_and_sorts(self):
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        s, r = self.get("/jobs?pageSize=4", t["token"])
        ids = [j["id"] for j in r["items"]]
        for jid in ids:
            self.assertEqual(self.api.call("PUT", f"/bookmarks/{jid}", token=t["token"])[0], 200)
            time.sleep(0.01)
        s, saved = self.get("/bookmarks", t["token"])
        self.assertEqual(([j["id"] for j in saved["items"]], saved["sort"]), (ids[::-1], "saved"))        # the last saved comes first
        self.assertEqual(saved["page"], {"page": 1, "pageSize": 10, "total": 4, "totalPages": 1})
        s, p2 = self.get("/bookmarks?pageSize=3&page=2", t["token"])
        self.assertEqual(([j["id"] for j in p2["items"]], p2["page"]["totalPages"]), (ids[::-1][3:], 2))
        s, best = self.get("/bookmarks?sort=best", t["token"])
        keys = [(-j["match"]["score"], j["id"]) for j in best["items"]]
        self.assertEqual(keys, sorted(keys))
        s, newest = self.get("/bookmarks?sort=newest", t["token"])
        dates = [j["postedAt"] for j in newest["items"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_applications_pages_and_sorts(self):
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        s, r = self.get("/jobs?pageSize=3", t["token"])
        applied = []
        for j in r["items"]:
            s, a = self.api.call("POST", "/applications", {"jobId": j["id"]}, token=t["token"])
            self.assertEqual(s, 200)
            applied.append(a["id"])
            time.sleep(0.01)
        s, lst = self.get("/applications", t["token"])
        self.assertEqual(([a["id"] for a in lst["items"]], lst["sort"]), (applied[::-1], "updated"))         # the old order stays the default
        self.assertEqual(lst["page"], {"page": 1, "pageSize": 10, "total": 3, "totalPages": 1})
        time.sleep(0.01)
        self.api.call("PATCH", f"/applications/{applied[0]}", {"note": "A new note."}, token=t["token"])      # the first one changed last
        s, lst = self.get("/applications", t["token"])
        self.assertEqual([a["id"] for a in lst["items"]], [applied[0], applied[2], applied[1]])
        s, newest = self.get("/applications?sort=newest", t["token"])
        self.assertEqual([a["id"] for a in newest["items"]], applied[::-1])
        s, best = self.get("/applications?sort=best", t["token"])
        coverage = [a["coverage"] if a["coverage"] is not None else -1 for a in best["items"]]
        self.assertEqual(coverage, sorted(coverage, reverse=True))
        s, p2 = self.get("/applications?pageSize=2&page=2", t["token"])
        self.assertEqual((len(p2["items"]), p2["page"]["total"], p2["page"]["totalPages"]), (1, 3, 2))


# =====================================================================
# The lists of the employer
# =====================================================================
class EmployerListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def employer(self, premium=False):
        e = self.p.sign_up_and_in(role="recruiter", company="Paging Co Pty Ltd")
        if premium:
            self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        return e

    def post_job(self, e, **over):
        s, j = self.api.call("POST", "/recruiter/jobs", job_body(**over), token=e["token"])
        self.assertEqual(s, 200, j)
        return j

    def get(self, e, path):
        return self.api.call("GET", path, token=e["token"])

    def count_events(self, user_id, kind):
        return self.p.conn().execute("SELECT COUNT(*) FROM events WHERE actor_id = ? AND type = ?", (user_id, kind)).fetchone()[0]

    def test_the_jobs_of_an_employer(self):
        e = self.employer()
        ids = []
        for i in range(3):
            ids.append(self.post_job(e, title=f"Backend Engineer {i}")["id"])
            time.sleep(0.01)
        s, r = self.get(e, "/recruiter/jobs?pageSize=2")
        self.assertEqual(([j["id"] for j in r["items"]], r["sort"]), (ids[::-1][:2], "newest"))
        self.assertEqual(r["page"], {"page": 1, "pageSize": 2, "total": 3, "totalPages": 2})
        s, r2 = self.get(e, "/recruiter/jobs?pageSize=2&page=2")
        self.assertEqual([j["id"] for j in r2["items"]], [ids[0]])
        self.assertEqual(self.get(e, "/recruiter/jobs?sort=newest")[0], 200)
        s, bad = self.get(e, "/recruiter/jobs?sort=best")
        self.assertEqual((s, list(bad["error"]["fields"])), (400, ["sort"]))

    def test_the_applications_for_a_job(self):
        e = self.employer()
        job = self.post_job(e)
        applied = []
        for _ in range(3):
            t = self.p.sign_up_and_in()
            make_talent(self.p, t)
            s, a = self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
            applied.append(a["id"])
            time.sleep(0.01)
        s, r = self.get(e, f"/recruiter/jobs/{job['id']}/applications?pageSize=2")
        self.assertEqual(([a["id"] for a in r["items"]], r["sort"]), (applied[::-1][:2], "newest"))
        self.assertEqual((r["page"]["total"], r["page"]["totalPages"], r["job"]["id"]), (3, 2, job["id"]))
        s, r2 = self.get(e, f"/recruiter/jobs/{job['id']}/applications?pageSize=2&page=2")
        self.assertEqual([a["id"] for a in r2["items"]], [applied[0]])
        self.assertEqual(self.get(e, f"/recruiter/jobs/{job['id']}/applications?sort=best")[0], 400)

    def test_a_basic_employer_gets_5_profiles_and_no_pager(self):
        e = self.employer()
        self.post_job(e)
        s, r = self.get(e, "/recruiter/candidates")
        self.assertEqual((len(r["items"]), r["limitedTo"], r["plan"]), (5, 5, "basic"))
        self.assertGreater(r["total"], 50)
        self.assertEqual(r["page"], {"page": 1, "pageSize": 5, "total": r["total"], "totalPages": 1})
        ids = [c["id"] for c in r["items"]]
        # a page number or a page size does not give a Basic employer more profiles
        s, again = self.get(e, "/recruiter/candidates?page=2&pageSize=50")
        self.assertEqual(([c["id"] for c in again["items"]], again["page"]["totalPages"]), (ids, 1))
        s, upd = self.get(e, "/recruiter/candidates?sort=updated")
        self.assertEqual((len(upd["items"]), upd["page"]["total"], upd["limitedTo"]), (5, r["total"], 5))

    def test_a_premium_employer_has_pages_of_profiles(self):
        e = self.employer(premium=True)
        job = self.post_job(e)
        s, p1 = self.get(e, "/recruiter/candidates")
        total = p1["total"]
        self.assertEqual((len(p1["items"]), p1["limitedTo"], p1["sort"]), (10, None, "best"))
        self.assertEqual(p1["page"], {"page": 1, "pageSize": 10, "total": total, "totalPages": -(-total // 10)})
        s, p2 = self.get(e, "/recruiter/candidates?page=2")
        self.assertFalse({c["id"] for c in p1["items"]} & {c["id"] for c in p2["items"]})
        last = p1["page"]["totalPages"]
        s, pl = self.get(e, f"/recruiter/candidates?page={last}")
        self.assertEqual(len(pl["items"]), total - 10 * (last - 1))
        s, big = self.get(e, "/recruiter/candidates?pageSize=500")
        self.assertEqual((len(big["items"]), big["page"]["pageSize"]), (50, 50))
        # the order is the same for each request, and the same with sort=best
        pieces = []
        for page in range(1, 6):
            s, r = self.get(e, f"/recruiter/candidates?pageSize=10&page={page}&sort=best")
            pieces += [c["id"] for c in r["items"]]
        self.assertEqual(pieces, [c["id"] for c in big["items"]])
        s, bad = self.get(e, "/recruiter/candidates?sort=newest")
        self.assertEqual((s, list(bad["error"]["fields"])), (400, ["sort"]))
        self.assertEqual(job["id"], p1["job"]["id"])

    def test_the_profile_that_changed_last_comes_first_with_sort_updated(self):
        e = self.employer(premium=True)
        self.post_job(e)
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)                  # the newest change of a profile
        s, r = self.get(e, "/recruiter/candidates?sort=updated&pageSize=50")
        self.assertEqual(r["sort"], "updated")
        self.assertEqual(r["items"][0]["alias"], t["user"]["alias"])
        dates = [c["updatedAt"] for c in r["items"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for a, b in zip(r["items"], r["items"][1:]):
            if a["updatedAt"] == b["updatedAt"]:
                self.assertLess(a["id"], b["id"])         # a tie is broken by the id

    def test_the_updated_date_is_the_date_of_the_last_save_of_the_profile(self):
        e = self.employer(premium=True)
        self.post_job(e)
        t, profile = make_talent(self.p)
        s, before = self.get(e, f"/recruiter/candidates/{t['user']['id']}")
        time.sleep(0.02)
        self.api.call("PATCH", "/me", {"profile": profile}, token=t["token"])
        s, after = self.get(e, f"/recruiter/candidates/{t['user']['id']}")
        self.assertGreater(after["updatedAt"], before["updatedAt"])

    def test_profile_events_are_for_the_profiles_of_the_page_only(self):
        basic = self.employer()
        self.post_job(basic)
        self.get(basic, "/recruiter/candidates?pageSize=50")
        self.assertEqual(self.count_events(basic["user"]["id"], "profile_appear"), 5)      # Basic: 5 profiles, not 138
        e = self.employer(premium=True)
        self.post_job(e)
        self.get(e, "/recruiter/candidates?pageSize=7")
        self.assertEqual(self.count_events(e["user"]["id"], "profile_appear"), 7)
        self.get(e, "/recruiter/candidates?pageSize=7&page=2")
        self.assertEqual(self.count_events(e["user"]["id"], "profile_appear"), 14)
        self.get(e, "/recruiter/candidates?sort=bad")
        self.assertEqual(self.count_events(e["user"]["id"], "profile_appear"), 14)


# =====================================================================
# Compare of 2 to 5 jobs (talent) and 2 to 5 profiles (employer)
# =====================================================================
class JobCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.t, _ = make_talent(cls.p, levels={"Microsoft Excel": 5})
        e = cls.p.sign_up_and_in(role="recruiter", company="Matrix Co Pty Ltd")
        s, cls.j1 = cls.api.call("POST", "/recruiter/jobs", job_body(title="Data Analyst One", skillRequirements=[
            {"name": "Microsoft Excel", "level": 4, "must": True}, {"name": "Terraform", "level": 2, "must": False}]), token=e["token"])
        s, cls.j2 = cls.api.call("POST", "/recruiter/jobs", job_body(title="Data Analyst Two", skills=["Microsoft Excel", "Docker"]), token=e["token"])

    def test_the_skill_matrix(self):
        s, c = self.api.call("GET", f"/jobs/compare?ids={self.j1['id']},{self.j2['id']}", token=self.t["token"])
        self.assertEqual(s, 200)
        rows = {r["skill"]: r for r in c["skillMatrix"]}
        self.assertEqual(set(rows), {"Microsoft Excel", "Terraform", "Docker"})
        # a job with skill levels gives them. A job without gives level 3 and must=true.
        self.assertEqual(rows["Microsoft Excel"]["byJob"], {self.j1["id"]: {"required": 4, "must": True}, self.j2["id"]: {"required": 3, "must": True}})
        self.assertEqual(rows["Terraform"]["byJob"], {self.j1["id"]: {"required": 2, "must": False}, self.j2["id"]: None})
        self.assertEqual(rows["Docker"]["byJob"], {self.j1["id"]: None, self.j2["id"]: {"required": 3, "must": True}})
        self.assertEqual(rows["Microsoft Excel"]["yours"], 5)     # the level that the talent set
        self.assertIsNone(rows["Terraform"]["yours"])             # the talent does not have this skill
        self.assertEqual([r["skill"] for r in c["skillMatrix"]], ["Microsoft Excel", "Terraform", "Docker"])
        self.assertEqual(len(c["pairs"]), 1)

    def test_a_skill_that_the_talent_typed_without_a_card_counts_as_level_3(self):
        t = self.p.sign_up_and_in()
        s, me = self.api.call("PATCH", "/me", {"profile": {"skills": ["Excel"], "industry": ["Data"]}, "onboarding": "done"}, token=t["token"])
        self.assertEqual((s, me["profile"]["translation"]), (200, []))
        s, c = self.api.call("GET", f"/jobs/compare?ids={self.j1['id']},{self.j2['id']}", token=t["token"])
        self.assertEqual(s, 200)
        rows = {r["skill"]: r for r in c["skillMatrix"]}
        self.assertEqual((rows["Microsoft Excel"]["yours"], rows["Terraform"]["yours"]), (3, None))

    def test_the_levels_of_the_talent_are_from_1_to_5(self):
        s, rec = self.api.call("GET", "/jobs?pageSize=5", token=self.t["token"])
        s, c = self.api.call("GET", "/jobs/compare?ids=" + ",".join(j["id"] for j in rec["items"]), token=self.t["token"])
        self.assertEqual((s, len(c["pairs"])), (200, 10))
        self.assertTrue(c["skillMatrix"])
        for row in c["skillMatrix"]:
            self.assertTrue(row["yours"] is None or 1 <= row["yours"] <= 5)
            self.assertEqual(set(row["byJob"]), {j["id"] for j in rec["items"]})
            for cell in row["byJob"].values():
                self.assertTrue(cell is None or (1 <= cell["required"] <= 5 and isinstance(cell["must"], bool)))

    def test_the_new_keys_are_on_the_job_cards_of_a_comparison(self):
        s, c = self.api.call("GET", f"/jobs/compare?ids={self.j1['id']},{self.j2['id']}", token=self.t["token"])
        first = c["jobs"][0]
        self.assertEqual((first["level"], first["skillRequirements"][0]), ("Mid", {"name": "Microsoft Excel", "level": 4, "must": True}))


class EmployerCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        cls.e = cls.p.sign_up_and_in(role="recruiter", company="Compare Co Pty Ltd")
        cls.api.call("PUT", "/entitlements", {"plan": "premium"}, token=cls.e["token"])
        s, cls.job = cls.api.call("POST", "/recruiter/jobs", job_body(skillRequirements=[
            {"name": "Microsoft Excel", "level": 4, "must": True}, {"name": "Stakeholder management", "level": 3, "must": False},
            {"name": "Terraform", "level": 2, "must": True}]), token=cls.e["token"])
        s, r = cls.api.call("GET", f"/recruiter/candidates?jobId={cls.job['id']}&pageSize=10", token=cls.e["token"])
        cls.ids = [c["id"] for c in r["items"]]

    def get(self, ids, job_id=None, token=None):
        query = f"ids={','.join(ids)}" + (f"&jobId={job_id}" if job_id else "")
        return self.api.call("GET", f"/recruiter/compare?{query}", token=token or self.e["token"])

    def talent(self, levels):
        """A talent with these levels for skills (a dictionary: skill name -> level)."""
        return make_talent(self.p, levels=levels)[0]

    def test_two_to_five_profiles(self):
        axes = None
        for n in (2, 3, 4, 5):
            ids = self.ids[:n]
            s, c = self.get(ids, self.job["id"])
            self.assertEqual(s, 200, c)
            self.assertEqual([x["id"] for x in c["candidates"]], ids)
            self.assertEqual(c["job"], {"id": self.job["id"], "title": self.job["title"], "skills": self.job["skills"]})
            for cand in c["candidates"]:
                self.assertTrue({"id", "alias", "level", "years", "yearsExperience", "roles", "qualifications", "certifications", "awards",
                                 "coverage", "skills", "otherSkills"} <= set(cand))
                self.assertEqual(len(cand["skills"]), len(self.job["skills"]))
            radar = c["radar"]
            axes = [a["key"] for a in radar["axes"]]
            self.assertEqual(axes[0], "coverage")
            self.assertEqual([s["id"] for s in radar["series"]], ids)
            for series in radar["series"]:
                self.assertEqual(len(series["values"]), len(axes))
                self.assertTrue(all(0 <= v <= 100 for v in series["values"]))
            self.assertTrue(c["areas"])
            for area in c["areas"]:
                self.assertEqual([r["id"] for r in area["ranks"]], ids)
                positions = [r["position"] for r in area["ranks"]]
                self.assertTrue(all(isinstance(x, int) and 1 <= x <= n for x in positions))
                self.assertEqual(min(positions), 1)
            self.assertEqual({r["skill"] for r in c["skillMatrix"]}, {"Microsoft Excel", "Stakeholder management", "Terraform"})
            for row in c["skillMatrix"]:
                self.assertEqual(set(row["byCandidate"]), set(ids))
        # the radar follows the coverage that the list shows
        s, lst = self.api.call("GET", f"/recruiter/candidates?jobId={self.job['id']}&pageSize=10", token=self.e["token"])
        by_id = {x["id"]: x["coverage"] for x in lst["items"]}
        s, c = self.get(self.ids[:5], self.job["id"])
        for series in c["radar"]["series"]:
            self.assertEqual(series["values"][0], float(by_id[series["id"]]))

    def test_the_input_is_checked(self):
        for ids in ([], self.ids[:1], self.ids[:6], [self.ids[0], self.ids[0]]):       # none, one, six, one twice
            s, r = self.get(ids, self.job["id"])
            self.assertEqual((s, r["error"]["fields"]), (400, {"ids": "Choose 2 to 5 profiles to compare."}), ids)
        s, r = self.get(self.ids[:2])
        self.assertEqual((s, r["error"]["fields"]), (400, {"jobId": "Choose one of your jobs."}))
        s, r = self.get(self.ids[:2], "job-does-not-exist")
        self.assertEqual(s, 404)
        s, r = self.get([self.ids[0], "nobody"], self.job["id"])
        self.assertEqual((s, r["error"]["message"]), (404, "We can't find one of the profiles."))
        # the old form with a and b is gone
        s, r = self.api.call("GET", f"/recruiter/compare?a={self.ids[0]}&b={self.ids[1]}&jobId={self.job['id']}", token=self.e["token"])
        self.assertEqual((s, list(r["error"]["fields"])), (400, ["ids"]))

    def test_the_job_must_be_yours(self):
        other = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=other["token"])
        s, r = self.get(self.ids[:2], self.job["id"], token=other["token"])
        self.assertEqual((s, r["error"]["code"]), (404, "NOT_FOUND"))

    def test_the_premium_gate(self):
        basic = self.p.sign_up_and_in(role="recruiter")
        s, j = self.api.call("POST", "/recruiter/jobs", job_body(), token=basic["token"])
        s, r = self.get(self.ids[:2], j["id"], token=basic["token"])
        self.assertEqual((s, r["error"]["code"]), (403, "PREMIUM_REQUIRED"))
        s, r = self.get(self.ids[:6], None, token=basic["token"])           # the gate comes before the check of the input
        self.assertEqual((s, r["error"]["code"]), (403, "PREMIUM_REQUIRED"))
        t = self.p.sign_up_and_in()
        self.assertEqual(self.get(self.ids[:2], self.job["id"], token=t["token"])[0], 403)
        self.assertEqual(self.api.call("GET", "/recruiter/compare?ids=a,b&jobId=x")[0], 401)

    def test_the_skill_matrix_of_the_profiles(self):
        a = self.talent({"Microsoft Excel": 5, "Stakeholder management": 1})
        b = self.talent({"Microsoft Excel": 2, "Stakeholder management": 4})
        s, c = self.get([a["user"]["id"], b["user"]["id"]], self.job["id"])
        self.assertEqual(s, 200, c)
        rows = {r["skill"]: r for r in c["skillMatrix"]}
        self.assertEqual((rows["Microsoft Excel"]["required"], rows["Microsoft Excel"]["must"]), (4, True))
        self.assertEqual((rows["Stakeholder management"]["required"], rows["Stakeholder management"]["must"]), (3, False))
        ida, idb = a["user"]["id"], b["user"]["id"]
        self.assertEqual(rows["Microsoft Excel"]["byCandidate"][ida], {"level": 5, "status": "meets"})
        self.assertEqual(rows["Microsoft Excel"]["byCandidate"][idb], {"level": 2, "status": "below"})
        self.assertEqual(rows["Stakeholder management"]["byCandidate"][ida], {"level": 1, "status": "below"})
        self.assertEqual(rows["Stakeholder management"]["byCandidate"][idb], {"level": 4, "status": "meets"})
        self.assertEqual(rows["Terraform"]["byCandidate"][ida], {"level": None, "status": "missing"})
        by = {x["id"]: x for x in c["candidates"]}
        self.assertEqual(by[ida]["alias"], a["user"]["alias"])

    def test_a_related_skill_is_not_a_level(self):
        # the job asks for SQL. The talent has PostgreSQL only (a related skill): the status is "related" and there is no level.
        # A talent with SQL at level 2 is "below". A talent with nothing of it is "missing".
        e = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        s, job = self.api.call("POST", "/recruiter/jobs", job_body(skillRequirements=[{"name": "SQL", "level": 3, "must": True}]), token=e["token"])
        related = make_talent(self.p, skills=["PostgreSQL", "Git"])[0]
        below = make_talent(self.p, skills=["SQL", "Git"], levels={"SQL": 2})[0]
        nothing = make_talent(self.p, skills=["Git", "Communication"])[0]
        ids = [related["user"]["id"], below["user"]["id"], nothing["user"]["id"]]
        s, c = self.api.call("GET", f"/recruiter/compare?ids={','.join(ids)}&jobId={job['id']}", token=e["token"])
        self.assertEqual(s, 200, c)
        cells = c["skillMatrix"][0]["byCandidate"]
        self.assertEqual(cells[ids[0]], {"level": None, "status": "related"})
        self.assertEqual(cells[ids[1]], {"level": 2, "status": "below"})
        self.assertEqual(cells[ids[2]], {"level": None, "status": "missing"})

    def test_the_positions_of_an_area(self):
        self.assertEqual(_positions([80.0, 60.0, 40.0]), [1, 2, 3])
        self.assertEqual(_positions([90.0, 89.0, 70.0]), [1, 1, 3])             # 90 and 89 are in the same band: the next group starts at 3
        self.assertEqual(_positions([50.0, 80.0, 80.0, 10.0]), [3, 1, 1, 4])    # the order of the list does not matter
        self.assertEqual(_positions([70.0, 70.0]), [1, 1])
        self.assertEqual(_positions([55.5]), [1])

    def test_no_total_no_score_no_name(self):
        t = self.p.sign_up_and_in(name="Zelda Quixote", email="zelda.compare@example.test")
        make_talent(self.p, t, studyCountry=["Kenya"])
        s, c = self.get([t["user"]["id"], self.ids[0], self.ids[1]], self.job["id"])
        self.assertEqual(s, 200)
        blob = json.dumps(c)
        for word in ("Zelda", "Quixote", "zelda.compare", "Kenya", "my-cv"):
            self.assertNotIn(word, blob)
        for key in ('"total"', '"score"', '"rank"', '"tss"', '"relative_merit"', '"merit"'):
            self.assertNotIn(key, blob.lower())


# =====================================================================
# The new keys of the talent profile
# =====================================================================
class ProfileV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def talent(self):
        return make_talent(self.p, studyCountry=["Kenya"])

    def save(self, t, profile):
        s, me = self.api.call("PATCH", "/me", {"profile": profile}, token=t["token"])
        self.assertEqual(s, 200, me)
        return me["profile"]

    def test_the_level_must_be_one_of_the_levels(self):
        t, prof = self.talent()
        for given, expected in (("Senior", "Senior"), ("Intern", "Intern"), ("Principal", "Principal"), ("Boss", ""), ("senior", ""), (5, ""), (None, "")):
            self.assertEqual(self.save(t, {**prof, "level": given})["level"], expected, given)

    def test_exact_years_set_the_band(self):
        t, prof = self.talent()
        for given, years, band in ((6.57, 6.6, "6–10 years"), (0, 0, "Less than 1 year"), (0.9, 0.9, "Less than 1 year"), (1, 1, "1–2 years"),
                                   (2.9, 2.9, "1–2 years"), (3, 3, "3–5 years"), (5.9, 5.9, "3–5 years"), (10, 10, "6–10 years"),
                                   (10.1, 10.1, "More than 10 years"), (40, 40, "More than 10 years"), ("7", 7, "6–10 years")):
            p = self.save(t, {**prof, "yearsExperience": given, "years": "3–5 years"})
            self.assertEqual((p["yearsExperience"], p["years"]), (years, band), given)
        # not a valid number: no exact years. The band that was sent stays.
        for bad in (40.01, -1, "abc", True, None, "", [5], {"x": 1}, float("inf"), 10 ** 400):
            p = self.save(t, {**prof, "yearsExperience": bad, "years": "3–5 years"})
            self.assertEqual((p["yearsExperience"], p["years"]), (None, "3–5 years"), bad)

    def test_certifications_are_cleaned(self):
        t, prof = self.talent()
        year = datetime.now(timezone.utc).year
        sent = [
            {"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022},
            {"name": "Mail me at jane@example.test", "issuer": "Call 0412 345 678", "year": 2020},
            {"name": "Old one", "year": 1989}, {"name": "First year", "year": 1990}, {"name": "Next year", "year": year + 1},
            {"name": "Too far", "year": year + 2}, {"name": "Text year", "year": "2021"}, {"name": "No year"},
            "Bare text name", {"name": ""}, {"issuer": "No name"}, {"name": 5}, 7, None, ["x"],
            {"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022},        # a copy
            {"name": "L" * 300},
        ]
        got = self.save(t, {**prof, "certifications": sent})["certifications"]
        by = {c["name"]: c for c in got}
        self.assertEqual(by["Cloud Practitioner"], {"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022})
        self.assertEqual(len([c for c in got if c["name"] == "Cloud Practitioner"]), 1)
        self.assertEqual(by["Mail me at [email removed]"], {"name": "Mail me at [email removed]", "issuer": "Call [phone removed]", "year": 2020})
        self.assertEqual([by[n]["year"] for n in ("Old one", "First year", "Next year", "Too far", "Text year", "No year")], [None, 1990, year + 1, None, 2021, None])
        self.assertEqual(by["Bare text name"], {"name": "Bare text name", "issuer": "", "year": None})
        self.assertEqual(len(by["L" * 120]["name"]), 120)
        self.assertNotIn("", by)
        for c in got:
            self.assertEqual(set(c), {"name", "issuer", "year"})
        text = json.dumps(got)
        self.assertNotIn("jane@example.test", text)
        self.assertNotIn("0412", text)

    def test_at_most_20_certifications_and_20_awards(self):
        t, prof = self.talent()
        p = self.save(t, {**prof, "certifications": [{"name": f"Certificate {i}"} for i in range(30)], "awards": [{"name": f"Award {i}", "kind": "Prize"} for i in range(30)]})
        self.assertEqual((len(p["certifications"]), len(p["awards"])), (20, 20))
        self.assertEqual(p["certifications"][0]["name"], "Certificate 0")

    def test_awards_are_cleaned(self):
        t, prof = self.talent()
        got = self.save(t, {**prof, "awards": [
            {"name": "Engineer of the year, mail a@b.co", "kind": "hackathon", "year": 2023},
            {"name": "Hack night winner", "kind": reference.AWARD_LABELS["open-source"], "year": 1980}, {"name": "No kind"}, "Bare award", {"kind": "no name"}, 5,
            {"name": "Odd kind", "kind": "K" * 100}, {"name": "Made-up kind", "kind": "best-in-the-world"}]})["awards"]
        # the kind is a kind of the taxonomy. The slug or the label is accepted. Any other kind becomes "".
        self.assertEqual(got[0], {"name": "Engineer of the year, mail [email removed]", "kind": "hackathon", "year": 2023})
        self.assertEqual(got[1], {"name": "Hack night winner", "kind": "open-source", "year": None})
        self.assertEqual(got[2], {"name": "No kind", "kind": "", "year": None})
        self.assertEqual((got[3]["name"], len(got)), ("Bare award", 6))
        self.assertEqual([a["kind"] for a in got[4:]], ["", ""])

    def test_a_skill_level_is_1_to_5_or_null(self):
        t, prof = self.talent()
        skills = [r for r in prof["translation"] if r["source"] == "skill"]
        other = [r for r in prof["translation"] if r["source"] != "skill"]
        self.assertGreaterEqual(len(skills), 5)
        self.assertTrue(other, "the CV gives role or qualification rows too")
        given = [4, 1, 5, 6, 0, "4", 3.0, 2.5, True, None]
        for row, level in zip(skills, given):
            row["level"] = level
        for row in other:
            row["level"] = 5            # a role or a qualification has no level
        saved = self.save(t, prof)["translation"]
        by = {r["id"]: r for r in saved}
        self.assertEqual([by[r["id"]]["level"] for r in skills[:len(given)]], [4, 1, 5, None, None, None, 3, None, None, None][:len(skills)])
        self.assertTrue(all(by[r["id"]]["level"] is None for r in other))
        s, me = self.api.call("GET", "/me", token=t["token"])
        self.assertEqual([r["level"] for r in me["profile"]["translation"]], [r["level"] for r in saved])

    def test_the_level_stays_when_the_translation_runs_again(self):
        t = self.p.sign_up_and_in()
        profile = {"skills": ["Excel", "Scheduling"], "currentRole": ["Operations Team Lead"], "qualification": ["Bachelor's degree"]}
        s, first = self.api.call("POST", "/profile/translate", {"profile": profile, "evidence": []}, token=t["token"])
        cards = first["skills"]
        # a new card of a skill has the level of its evidence (rule F8). A card of a role or a qualification has no level.
        self.assertTrue(all(c["level"] == 3 for c in cards if c["source"] == "skill"))
        self.assertTrue(all(c["level"] is None for c in cards if c["source"] != "skill"))
        row = next(c for c in cards if c["source"] == "skill")
        row["level"] = 5
        for c in cards:
            if c["source"] != "skill":
                c["level"] = 4                  # a role or a qualification cannot have a level
        s, tr = self.api.call("POST", "/profile/translate", {"profile": {**profile, "translation": cards}, "evidence": []}, token=t["token"])
        again = {c["id"]: c for c in tr["skills"]}
        self.assertEqual(again[row["id"]]["level"], 5)
        self.assertTrue(all(c["level"] == 3 for c in tr["skills"] if c["id"] != row["id"] and c["source"] == "skill"))
        self.assertTrue(all(c["level"] is None for c in tr["skills"] if c["source"] != "skill"))

    def test_the_shared_profile_has_the_new_keys_and_no_private_key(self):
        t, prof = self.talent()
        skills = [r for r in prof["translation"] if r["source"] == "skill"]
        skills[0]["level"] = 5                                # the talent set it
        skills[1]["level"] = None
        skills[1]["evidence"] = "Strong"                      # no level: the level of the evidence (4)
        skills[2]["level"] = None
        skills[2]["evidence"] = "Limited"                     # 2
        skills[3]["level"] = None
        skills[3]["evidence"] = "Moderate"                    # 3
        skills[4]["status"] = "removed"                       # not shared
        skills[4]["level"] = 5
        saved = self.save(t, {**prof, "level": "Senior", "yearsExperience": 6.6, "certifications": [{"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022}],
                              "awards": [{"name": "Hack night winner", "kind": "Hackathon", "year": 2023}]})
        s, shared = self.api.call("GET", "/me/shared-profile", token=t["token"])
        self.assertEqual(set(shared), {"alias", "roles", "skills", "qualifications", "fieldsOfStudy", "industries", "years", "targetRoles", "locations", "workTypes",
                                       "level", "yearsExperience", "skillLevels", "certifications", "awards", "updatedAt", "workModes", "specialisation"})
        self.assertEqual((shared["level"], shared["yearsExperience"], shared["years"]), ("Senior", 6.5, "6–10 years"))
        self.assertEqual(shared["certifications"], [{"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022}])
        self.assertEqual(shared["awards"], [{"name": "Hack night winner", "kind": "hackathon", "year": 2023}])
        levels = {x["name"]: x["level"] for x in shared["skillLevels"]}
        self.assertEqual([x["name"] for x in shared["skillLevels"]], shared["skills"])
        self.assertEqual((levels[skills[0]["mapped"]], levels[skills[1]["mapped"]], levels[skills[2]["mapped"]], levels[skills[3]["mapped"]]), (5, 4, 2, 3))
        self.assertNotIn(skills[4]["mapped"], levels)         # a removed skill is not shared, and neither is its level
        self.assertTrue(all(isinstance(v, int) and 1 <= v <= 5 for v in levels.values()))
        self.assertRegex(shared["updatedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        # nothing private
        text = json.dumps(shared)
        for secret in ("Kenya", t["user"]["name"], t["email"], "my-cv", "evidence", "studyCountry"):
            self.assertNotIn(secret, text)
        self.assertEqual(saved["yearsExperience"], 6.6)       # the talent sees the exact number

    def test_the_years_of_the_shared_profile_are_rounded_to_half_a_year(self):
        for exact, shown in ((6.2, 6.0), (6.3, 6.5), (6.7, 6.5), (6.8, 7.0), (0, 0), (0.2, 0.0), (0.3, 0.5), (39.9, 40.0), (12, 12)):
            self.assertEqual(store.shared_profile("A", {"yearsExperience": exact, "translation": []})["yearsExperience"], shown, exact)
        self.assertIsNone(store.shared_profile("A", {"translation": []})["yearsExperience"])

    def test_the_employer_sees_the_new_keys_of_a_profile(self):
        t, prof = self.talent()
        self.save(t, {**prof, "level": "Lead", "yearsExperience": 9, "certifications": [{"name": "Cloud Practitioner", "issuer": "Example Cloud", "year": 2022}],
                      "awards": [{"name": "Hack night winner", "kind": "Hackathon", "year": 2023}]})
        e = self.p.sign_up_and_in(role="recruiter")
        self.api.call("POST", "/recruiter/jobs", job_body(), token=e["token"])
        s, d = self.api.call("GET", f"/recruiter/candidates/{t['user']['id']}", token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual((d["level"], d["yearsExperience"]), ("Lead", 9))
        self.assertEqual(d["certifications"][0]["name"], "Cloud Practitioner")
        self.assertEqual(d["awards"][0]["year"], 2023)
        self.assertTrue(d["skillLevels"] and d["updatedAt"])
        text = json.dumps(d)
        for secret in ("Kenya", t["user"]["name"], t["email"], "my-cv"):
            self.assertNotIn(secret, text)
        # a sample profile has all the keys of version 2
        sample = self.p.conn().execute("SELECT id FROM users WHERE is_sample = 1 LIMIT 1").fetchone()["id"]
        s, old = self.api.call("GET", f"/recruiter/candidates/{sample}", token=e["token"])
        self.assertIn(old["level"], reference.LEVELS)
        self.assertGreaterEqual(old["yearsExperience"], 0)
        self.assertTrue(old["skillLevels"] and all(1 <= x["level"] <= 5 for x in old["skillLevels"]))
        self.assertTrue(old["updatedAt"])


class ProfileWithoutNewKeysTests(unittest.TestCase):
    def test_a_profile_without_the_new_keys_is_empty_not_invented(self):
        p = H.Platform.get()
        t = p.sign_up_and_in()
        s, me = p.api.call("PATCH", "/me", {"profile": {"skills": ["SQL"], "industry": ["Technology"]}}, token=t["token"])
        prof = me["profile"]
        self.assertEqual((prof["level"], prof["yearsExperience"], prof["certifications"], prof["awards"]), ("", None, [], []))
        shared = store.shared_profile("Teal Heron", prof)
        self.assertEqual((shared["level"], shared["yearsExperience"], shared["skillLevels"], shared["certifications"], shared["awards"]), (None, None, [], [], []))


# =====================================================================
# The new keys of a job
# =====================================================================
class JobV2Tests(unittest.TestCase):
    NEW = ("level", "specialisation", "minYears", "maxYears", "workMode", "skillRequirements", "certifications", "awards", "educationMin")

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def employer(self):
        return self.p.sign_up_and_in(role="recruiter", company="Jobs Co Pty Ltd")

    def post(self, e, body, expect=200):
        s, r = self.api.call("POST", "/recruiter/jobs", body, token=e["token"])
        self.assertEqual(s, expect, r)
        return r

    def test_the_old_short_body_still_works(self):
        e = self.employer()
        j = self.post(e, job_body())
        self.assertEqual(j["level"], "Mid")              # the default
        for key in ("specialisation", "minYears", "maxYears", "workMode", "educationMin"):
            self.assertIsNone(j[key], key)
        self.assertEqual((j["skillRequirements"], j["certifications"], j["awards"]), ([], {"required": [], "preferred": []}, {"preferred": []}))
        self.assertEqual(j["skills"], ["Python", "SQL", "Microsoft Excel"])
        s, d = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
        self.assertEqual({k: d[k] for k in self.NEW}, {k: j[k] for k in self.NEW})
        self.assertTrue(d["description"] and d["summary"] and d["company"] == "Jobs Co Pty Ltd")

    def test_the_catalogue_jobs_have_all_the_keys_of_version_2(self):
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        catalogue_ids = sorted(r["id"] for r in self.p.conn().execute("SELECT id FROM jobs WHERE owner_id IS NULL").fetchall())
        self.assertEqual(len(catalogue_ids), 50)
        cards = [self.api.call("GET", f"/jobs/{jid}", token=t["token"])[1] for jid in catalogue_ids[::4]]    # the page of 13 jobs of the catalogue
        for j in cards:
            self.assertIn(j["level"], reference.LEVELS)
            self.assertIn(j["workMode"], reference.WORK_MODES)
            self.assertIn(j["specialisation"], reference.ALL_SPECIALISATIONS)
            self.assertIsInstance(j["minYears"], (int, float))
            self.assertTrue(j["skillRequirements"] and all(1 <= x["level"] <= 5 and isinstance(x["must"], bool) for x in j["skillRequirements"]))
            self.assertEqual(j["skills"], [x["name"] for x in j["skillRequirements"]])
            self.assertEqual(set(j["certifications"]), {"required", "preferred"})
            self.assertEqual(set(j["awards"]), {"preferred"})
            self.assertTrue(j["educationMin"])
            self.assertIn(j["salaryUnit"], ("year", "day", "hour"))
        self.assertTrue(all(c["description"].startswith("## About the role") for c in cards))
        s, r = self.api.call("GET", "/jobs?pageSize=50", token=t["token"])             # and the cards of the list
        listed = [j for j in r["items"] if j["id"] in set(catalogue_ids)]
        self.assertGreater(len(listed), 5)
        self.assertTrue(all("description" not in j and j["level"] in reference.LEVELS and j["skillRequirements"] for j in listed))

    def test_the_new_keys_make_a_round_trip(self):
        e = self.employer()
        body = job_body(category="Software Engineering", level="Senior", specialisation="Backend", minYears=5, maxYears=9.5, workMode="Hybrid", educationMin="Bachelor's degree",
                        skillRequirements=[{"name": "Python", "level": 4, "must": True}, {"name": "SQL", "level": 3, "must": True}, {"name": "Microsoft Excel", "level": 2, "must": False}],
                        certifications={"required": ["Cloud Practitioner"], "preferred": ["Data Associate", "Security Basics"]},
                        awards={"preferred": ["Hackathon", "open-source"]}, skills=["ignored"])
        j = self.post(e, body)
        expected = {"level": "Senior", "specialisation": "Backend", "minYears": 5, "maxYears": 9.5, "workMode": "Hybrid", "educationMin": "Bachelor's degree",
                    "skillRequirements": body["skillRequirements"], "certifications": body["certifications"], "awards": {"preferred": ["hackathon", "open-source"]}}
        self.assertEqual({k: j[k] for k in self.NEW}, expected)
        self.assertEqual(j["skills"], ["Python", "SQL", "Microsoft Excel"])           # the names come from skillRequirements
        s, d = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
        self.assertEqual({k: d[k] for k in self.NEW}, expected)
        s, lst = self.api.call("GET", "/recruiter/jobs", token=e["token"])
        self.assertEqual({k: lst["items"][0][k] for k in self.NEW}, expected)
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        s, det = self.api.call("GET", f"/jobs/{j['id']}", token=t["token"])         # the talent sees it on the job detail
        self.assertEqual({k: det[k] for k in self.NEW}, expected)
        s, found = self.api.call("GET", "/jobs?q=Jobs%20Co&pageSize=50", token=t["token"])      # and on the job card
        card = next(c for c in found["items"] if c["id"] == j["id"])
        self.assertEqual({k: card[k] for k in self.NEW}, expected)
        self.assertNotIn("description", card)

    def test_the_new_keys_are_checked(self):
        e = self.employer()
        cases = [
            ({"level": "Boss"}, "level"), ({"level": "mid"}, "level"), ({"level": 3}, "level"),
            ({"workMode": "Space"}, "workMode"), ({"workMode": 4}, "workMode"),
            ({"minYears": 9, "maxYears": 5}, "maxYears"), ({"minYears": -1}, "minYears"), ({"maxYears": 41}, "maxYears"), ({"minYears": "many"}, "minYears"),
            ({"minYears": True}, "minYears"), ({"minYears": 10 ** 400}, "minYears"), ({"maxYears": [3]}, "maxYears"),
            ({"specialisation": 5}, "specialisation"), ({"educationMin": ["x"]}, "educationMin"),
            ({"skillRequirements": "Python"}, "skillRequirements"), ({"skillRequirements": [{"name": "Python", "level": 6}]}, "skillRequirements"),
            ({"skillRequirements": [{"name": "Python", "level": 0}]}, "skillRequirements"), ({"skillRequirements": [{"name": "Python", "level": "4"}]}, "skillRequirements"),
            ({"skillRequirements": [{"name": "Python", "level": 2.5}]}, "skillRequirements"), ({"skillRequirements": [{"level": 3}]}, "skillRequirements"),
            ({"skillRequirements": [{"name": "Python", "level": 3, "must": "yes"}]}, "skillRequirements"),
            ({"skillRequirements": [{"name": f"Skill {i}", "level": 3} for i in range(13)]}, "skillRequirements"),
            ({"certifications": ["x"]}, "certifications"), ({"certifications": {"required": "x"}}, "certifications"),
            ({"certifications": {"required": [f"Certificate {i}" for i in range(11)]}}, "certifications"),
            ({"certifications": {"preferred": [f"Certificate {i}" for i in range(11)]}}, "certifications"),
            ({"awards": ["x"]}, "awards"), ({"awards": {"preferred": [f"Award {i}" for i in range(11)]}}, "awards"),
        ]
        for extra, field in cases:
            s, r = self.api.call("POST", "/recruiter/jobs", job_body(**extra), token=e["token"])
            self.assertEqual((s, field in r["error"]["fields"]), (400, True), extra)
            self.assertEqual(set(r["error"]["fields"]), {field}, extra)

    def test_a_skill_with_no_level_gets_3_and_a_skill_with_no_must_is_required(self):
        e = self.employer()
        j = self.post(e, job_body(skillRequirements=[{"name": "Python"}, {"name": "SQL", "level": 5, "must": False}, {"name": "python", "level": 2}]))
        self.assertEqual(j["skillRequirements"], [{"name": "Python", "level": 3, "must": True}, {"name": "SQL", "level": 5, "must": False}])   # a copy is dropped

    def test_names_of_certifications_and_awards_are_scrubbed_and_limited(self):
        e = self.employer()
        j = self.post(e, job_body(certifications={"required": ["Call 0412 345 678 for the Cloud exam", "x" * 300, "", "Cloud exam, a@b.co", 7]}))
        required = j["certifications"]["required"]
        self.assertEqual(required[0], "Call [phone removed] for the Cloud exam")
        self.assertEqual(len(required[1]), 120)
        self.assertEqual(required[2], "Cloud exam, [email removed]")
        self.assertEqual(len(required), 3)

    def test_award_kinds_of_a_job_are_kinds_of_the_taxonomy(self):
        e = self.employer()
        j = self.post(e, job_body(awards={"preferred": ["hackathon", reference.AWARD_LABELS["patent"], "hackathon"]}))
        self.assertEqual(j["awards"]["preferred"], ["hackathon", "patent"])       # the slug or the label. A copy is dropped
        for bad in (["Prize mail me@x.co"], ["K" * 100], ["best-in-the-world"], ["hackathon", "best-in-the-world"]):
            s, r = self.api.call("POST", "/recruiter/jobs", job_body(awards={"preferred": bad}), token=e["token"])
            self.assertEqual((s, list(r["error"]["fields"])), (400, ["awards"]), bad)

    def test_the_specialisation_is_one_of_the_taxonomy_and_fits_the_domain(self):
        e = self.employer()
        j = self.post(e, job_body(category="Data", specialisation="Data engineering"))
        self.assertEqual(j["specialisation"], "Data engineering")
        for category, spec in (("Data", "Backend"), ("Software Engineering", "Data engineering"), ("Data", "Plumbing"), ("Data", 5)):
            s, r = self.api.call("POST", "/recruiter/jobs", job_body(category=category, specialisation=spec), token=e["token"])
            self.assertEqual((s, list(r["error"]["fields"])), (400, ["specialisation"]), (category, spec))
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"category": "Software Engineering"}, token=e["token"])    # the stored specialisation does not fit the new domain
        self.assertEqual((s, list(r["error"]["fields"])), (400, ["specialisation"]))
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"category": "Software Engineering", "specialisation": "Backend"}, token=e["token"])
        self.assertEqual((s, r["specialisation"], r["category"]), (200, "Backend", "Software Engineering"))

    def test_an_edit(self):
        e = self.employer()
        j = self.post(e, job_body(minYears=3, maxYears=6, level="Mid", workMode="Remote", skillRequirements=[{"name": "Python", "level": 4, "must": True}]))
        url = f"/recruiter/jobs/{j['id']}"

        def patch(body):
            return self.api.call("PATCH", url, body, token=e["token"])

        s, r = patch({"minYears": 7})                                  # more than the stored maxYears
        self.assertEqual((s, list(r["error"]["fields"])), (400, ["maxYears"]))
        s, r = patch({"maxYears": 2})                                  # less than the stored minYears
        self.assertEqual((s, list(r["error"]["fields"])), (400, ["maxYears"]))
        s, r = patch({"minYears": 7, "maxYears": 12, "level": "Lead"})
        self.assertEqual((s, r["minYears"], r["maxYears"], r["level"]), (200, 7, 12, "Lead"))
        s, r = patch({"workMode": None, "specialisation": "Data engineering"})      # null clears a value
        self.assertEqual((r["workMode"], r["specialisation"]), (None, "Data engineering"))
        s, r = patch({"level": None})                                  # a null level is "not sent"
        self.assertEqual(r["level"], "Lead")
        s, r = patch({"certifications": {"required": ["Cloud Practitioner"], "preferred": []}, "awards": {"preferred": ["Hackathon"]}})
        self.assertEqual((r["certifications"], r["awards"]), ({"required": ["Cloud Practitioner"], "preferred": []}, {"preferred": ["hackathon"]}))
        s, r = patch({"skillRequirements": [{"name": "SQL", "level": 2, "must": False}, {"name": "Python", "level": 5, "must": True}]})
        self.assertEqual((r["skills"], [x["level"] for x in r["skillRequirements"]]), (["SQL", "Python"], [2, 5]))
        s, r = patch({"skills": ["Excel", "Python"]})                  # names only: the levels are cleared
        self.assertEqual((r["skills"], r["skillRequirements"]), (["Excel", "Python"], []))
        s, r = patch({"skillRequirements": [{"name": "Excel", "level": 3}]})
        s, r = patch({"skillRequirements": []})                        # an empty list: the skills stay, the levels go
        self.assertEqual((r["skills"], r["skillRequirements"]), (["Excel"], []))
        s, r = patch({"title": "Backend Engineer Two"})                # an edit of other keys keeps the new keys
        self.assertEqual((r["level"], r["minYears"], r["certifications"]["required"], r["awards"]["preferred"]), ("Lead", 7, ["Cloud Practitioner"], ["hackathon"]))
        self.assertEqual(patch({"level": "Boss"})[0], 400)

    def test_nothing_cuts_the_description(self):
        e = self.employer()
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        for size in (1200, 3000, 3500, catalogue.MAX_DESCRIPTION):
            text = long_jd(size)
            self.assertEqual(len(text), size)
            j = self.post(e, job_body(description=text))
            s, mine = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
            self.assertEqual(mine["description"], text, size)
            s, det = self.api.call("GET", f"/jobs/{j['id']}", token=t["token"])
            self.assertEqual(det["description"], text, size)
            self.assertNotIn("…", det["description"])
            self.assertEqual(self.p.conn().execute("SELECT LENGTH(description) FROM jobs WHERE id = ?", (j["id"],)).fetchone()[0], size)
        # an edit keeps the whole text too
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"description": long_jd(3000)}, token=e["token"])
        self.assertEqual(r["description"], long_jd(3000))

    def test_a_text_above_the_limit_is_refused_not_cut(self):
        e = self.employer()
        s, r = self.api.call("POST", "/recruiter/jobs", job_body(description="x" * (catalogue.MAX_DESCRIPTION + 1)), token=e["token"])
        self.assertEqual((s, r["error"]["fields"]), (400, {"description": f"Use {catalogue.MAX_DESCRIPTION} characters or fewer in the description."}))
        j = self.post(e, job_body())
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"description": "x" * (catalogue.MAX_DESCRIPTION + 1)}, token=e["token"])
        self.assertEqual((s, list(r["error"]["fields"])), (400, ["description"]))

    def test_the_summary_is_short_and_has_no_markup(self):
        e = self.employer()
        j = self.post(e, job_body(description=long_jd(3000)))
        s, d = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
        self.assertLessEqual(len(d["summary"]), 200)
        self.assertNotIn("#", d["summary"])
        self.assertTrue(d["summary"].startswith("We build the tools"))
        self.assertLessEqual(len(catalogue.summary_of("word " * 200)), 200)
        self.assertEqual(catalogue.summary_of("## Heading\n- one\n- two"), "one two")
        self.assertEqual(catalogue.summary_of("Short text."), "Short text.")
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        s, det = self.api.call("GET", f"/jobs/{j['id']}", token=t["token"])
        self.assertEqual(det["summary"], d["summary"])

    def test_line_breaks_stay(self):
        e = self.employer()
        text = "## About the role\r\nWe build things for people.\r\n\r\n## What you will do\r\n- Build the product every day\r\n- Test it"
        j = self.post(e, job_body(description=text))
        s, d = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
        self.assertEqual(d["description"], text.replace("\r\n", "\n"))

    def test_the_keys_of_a_job_description_file_are_cleaned(self):
        fields = {"title": "Cloud Engineer", "level": "Senior", "specialisation": "Platform and DevOps", "minYears": 3, "maxYears": 8, "workMode": "Hybrid",
                  "skillRequirements": [{"name": "Python", "level": 4, "must": True}], "certifications": {"required": ["Cloud Practitioner", "a@b.co"], "preferred": []},
                  "awards": {"preferred": ["Hackathon"]}, "educationMin": "Bachelor's degree"}
        self.assertEqual(catalogue.clean_import_fields(fields)["certifications"], {"required": ["Cloud Practitioner", "[email removed]"], "preferred": []})
        clean = catalogue.clean_import_fields({**fields, "level": "Boss", "minYears": "x", "workMode": "Space", "skillRequirements": [{"name": "Python", "level": 9}],
                                               "awards": "none", "unknown": 1})
        self.assertEqual(clean["title"], "Cloud Engineer")
        for key in ("level", "minYears", "workMode", "skillRequirements", "awards"):
            self.assertNotIn(key, clean, key)               # not valid: left out. The employer fills it in.
        self.assertEqual((clean["maxYears"], clean["specialisation"], clean["educationMin"]), (8, "Platform and DevOps", "Bachelor's degree"))
        self.assertEqual(catalogue.clean_import_fields({"skillRequirements": [{"name": "Python", "level": 4, "must": True}]})["skills"], ["Python"])
        # minYears is more than maxYears: the maximum is left out
        clean = catalogue.clean_import_fields({"minYears": 9, "maxYears": 5})
        self.assertEqual((clean.get("minYears"), "maxYears" in clean), (9, False))

    def test_an_uploaded_job_description_passes_the_new_keys_after_a_check(self):
        e = self.employer()
        result = {"fields": {"title": "Cloud Engineer", "category": "Software Engineering", "level": "Lead", "minYears": 4, "maxYears": 2, "workMode": "Hybrid",
                             "skillRequirements": [{"name": "Python", "level": 4, "must": True}], "awards": {"preferred": ["Hackathon"]}},
                  "detected": ["title", "category"], "missing": ["location", "type", "salary", "description"]}
        with mock.patch.object(parsing, "parse_jd", return_value=result):
            s, up = self.api.upload("/recruiter/jobs/import", "jd.docx", H.make_docx(["Cloud Engineer wanted for a long term project in Sydney with the team."]), e["token"])
            for _ in range(100):
                s, res = self.api.call("GET", f"/recruiter/jobs/import/{up['parse']['id']}", token=e["token"])
                if res["status"] != "parsing":
                    break
                time.sleep(0.05)
        self.assertEqual(res["status"], "done")
        f = res["result"]["fields"]
        self.assertEqual((f["level"], f["minYears"], f["workMode"], f["skills"], f["awards"]), ("Lead", 4, "Hybrid", ["Python"], {"preferred": ["hackathon"]}))
        self.assertNotIn("maxYears", f)                    # smaller than minYears: left out
        self.assertEqual(f["skillRequirements"], [{"name": "Python", "level": 4, "must": True}])
        self.assertEqual(res["result"]["missing"], result["missing"])
        self.assertTrue({"level", "minYears", "workMode", "skillRequirements", "awards"} <= set(res["result"]["detected"]))


# =====================================================================
# The Premium benefits (GET /entitlements) and the events behind them
# =====================================================================
class BenefitTests(unittest.TestCase):
    EMPLOYER = [("all_talent", "See every talent profile, not only the top 5"), ("invite", "Invite talent to apply"),
                ("compare", "Compare up to 5 talent profiles"), ("advanced_charts", "Pipeline by stage and interest per job")]
    TALENT = [("skills_to_learn", "Skills to learn next"), ("skill_demand", "Demand for your skills")]

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def ent(self, user):
        s, r = self.api.call("GET", "/entitlements", token=user["token"])
        self.assertEqual(s, 200)
        return r

    def benefit(self, user, key):
        return next(b for b in self.ent(user)["benefits"] if b["key"] == key)

    def events(self, user, kind):
        return self.p.conn().execute("SELECT COUNT(*) FROM events WHERE actor_id = ? AND type = ?", (user["user"]["id"], kind)).fetchone()[0]

    def test_the_benefits_of_a_basic_employer(self):
        e = self.p.sign_up_and_in(role="recruiter")
        ent = self.ent(e)
        self.assertEqual((ent["plan"], ent["crown"], ent["compareMax"], ent["topN"]), ("basic", False, 5, 5))
        self.assertEqual([(b["key"], b["label"]) for b in ent["benefits"]], self.EMPLOYER)
        for b in ent["benefits"]:
            self.assertEqual(set(b), {"key", "label", "description", "available", "used", "usedCount"})
            self.assertEqual((b["available"], b["used"], b["usedCount"]), (False, False, 0))
            self.assertTrue(b["description"])

    def test_the_benefits_of_a_talent(self):
        t = self.p.sign_up_and_in()
        ent = self.ent(t)
        self.assertEqual((ent["plan"], ent["crown"], ent["compareMax"], ent["canCompare"]), ("basic", False, 5, False))
        self.assertEqual([(b["key"], b["label"]) for b in ent["benefits"]], self.TALENT)
        self.assertTrue(all(not b["available"] and not b["used"] for b in ent["benefits"]))

    def test_premium_makes_the_benefits_available_and_shows_the_crown(self):
        e = self.p.sign_up_and_in(role="recruiter")
        s, ent = self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        self.assertEqual((ent["crown"], ent["compareMax"]), (True, 5))
        self.assertTrue(all(b["available"] and not b["used"] for b in ent["benefits"]))
        s, ent = self.api.call("PUT", "/entitlements", {"plan": "basic"}, token=e["token"])
        self.assertEqual((ent["crown"], any(b["available"] for b in ent["benefits"])), (False, False))

    def test_the_employer_benefits_flip_after_an_action(self):
        e = self.p.sign_up_and_in(role="recruiter", company="Benefit Co Pty Ltd")
        s, job = self.api.call("POST", "/recruiter/jobs", job_body(), token=e["token"])
        self.api.call("GET", "/recruiter/candidates?pageSize=50", token=e["token"])
        self.assertFalse(self.benefit(e, "all_talent")["used"], "Basic employers do not use this benefit")
        self.api.call("GET", "/stats", token=e["token"])
        self.assertFalse(self.benefit(e, "advanced_charts")["used"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        # all_talent: a list of MORE than 5 profiles
        self.api.call("GET", "/recruiter/candidates?pageSize=5", token=e["token"])
        self.assertFalse(self.benefit(e, "all_talent")["used"])
        s, r = self.api.call("GET", "/recruiter/candidates?pageSize=6", token=e["token"])
        self.assertEqual(len(r["items"]), 6)
        b = self.benefit(e, "all_talent")
        self.assertEqual((b["used"], b["usedCount"]), (True, 1))
        self.api.call("GET", "/recruiter/candidates", token=e["token"])
        self.assertEqual(self.benefit(e, "all_talent")["usedCount"], 2)
        self.assertEqual(self.events(e, "talent_list_full"), 2)
        ids = [c["id"] for c in r["items"]]
        # compare: a failed request does not count
        self.api.call("GET", f"/recruiter/compare?ids={ids[0]}&jobId={job['id']}", token=e["token"])
        self.assertFalse(self.benefit(e, "compare")["used"])
        s, c = self.api.call("GET", f"/recruiter/compare?ids={ids[0]},{ids[1]}&jobId={job['id']}", token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual((self.benefit(e, "compare")["used"], self.benefit(e, "compare")["usedCount"]), (True, 1))
        # invite: only a real invitation counts
        self.assertFalse(self.benefit(e, "invite")["used"])
        s, r = self.api.call("POST", f"/recruiter/candidates/{ids[2]}/contact", {"jobId": job["id"], "message": "short"}, token=e["token"])
        self.assertEqual(s, 400)
        self.assertFalse(self.benefit(e, "invite")["used"])
        s, r = self.api.call("POST", f"/recruiter/candidates/{ids[2]}/contact", {"jobId": job["id"], "message": "Please apply, we like your skills."}, token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual((self.benefit(e, "invite")["used"], self.benefit(e, "invite")["usedCount"]), (True, 1))
        # advanced charts
        s, st = self.api.call("GET", "/stats", token=e["token"])
        self.assertIsNotNone(st["advanced"])
        self.assertEqual((self.benefit(e, "advanced_charts")["used"], self.benefit(e, "advanced_charts")["usedCount"]), (True, 1))
        for b in self.ent(e)["benefits"]:
            self.assertEqual(b["usedCount"], self.events(e, {"all_talent": "talent_list_full", "invite": "invite", "compare": "compare_view",
                                                             "advanced_charts": "advanced_charts_view"}[b["key"]]))

    def test_a_different_employer_is_not_changed(self):
        a = self.p.sign_up_and_in(role="recruiter")
        b = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=a["token"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=b["token"])
        self.api.call("GET", "/stats", token=a["token"])
        self.assertTrue(self.benefit(a, "advanced_charts")["used"])
        self.assertFalse(self.benefit(b, "advanced_charts")["used"])

    def test_the_talent_benefits_flip_after_the_insights_are_opened(self):
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        self.api.call("GET", "/stats", token=t["token"])                          # Basic: no insights
        self.assertFalse(self.benefit(t, "skills_to_learn")["used"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=t["token"])
        self.assertTrue(all(b["available"] and not b["used"] for b in self.ent(t)["benefits"]))
        s, st = self.api.call("GET", "/stats", token=t["token"])
        self.assertIsNotNone(st["advanced"])
        for key in ("skills_to_learn", "skill_demand"):
            b = self.benefit(t, key)
            self.assertEqual((b["used"], b["usedCount"]), (True, 1), key)
        self.assertEqual(self.events(t, "insights_view"), 1)

    def test_a_talent_without_a_profile_has_no_insights_to_open(self):
        t = self.p.sign_up_and_in()
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=t["token"])
        s, st = self.api.call("GET", "/stats", token=t["token"])
        self.assertIsNone(st["advanced"])
        self.assertFalse(self.benefit(t, "skills_to_learn")["used"])

    def test_nobody_sees_who_did_what(self):
        e = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        s, job = self.api.call("POST", "/recruiter/jobs", job_body(), token=e["token"])
        t = self.p.sign_up_and_in()
        make_talent(self.p, t)
        tid = t["user"]["id"]
        other = self.p.sign_up_and_in()
        make_talent(self.p, other)
        self.api.call("POST", f"/recruiter/candidates/{tid}/contact", {"jobId": job["id"], "message": "Please apply, we like your skills."}, token=e["token"])
        self.api.call("GET", f"/recruiter/compare?ids={tid},{other['user']['id']}&jobId={job['id']}", token=e["token"])
        self.api.call("GET", "/recruiter/candidates?pageSize=10", token=e["token"])
        # the talent sees counts of their own profile only: no compare, no invite, no employer
        s, st = self.api.call("GET", "/stats", token=t["token"])
        self.assertEqual(set(st["basic"]["profile"]), {"appear", "watch", "saved"})
        blob = json.dumps([st, self.ent(t)]).lower()
        for word in ("compare_view", "invite", "talent_list_full", e["user"]["id"], "benefit co"):
            self.assertNotIn(word, blob)
        # the employer sees no event of the talent, and no event of the other employer
        s, est = self.api.call("GET", "/stats", token=e["token"])
        blob = json.dumps(est).lower()
        for word in ("compare_view", "talent_list_full", "insights_view", tid, other["user"]["id"]):
            self.assertNotIn(word, blob)
        # the benefit lists have no ids and no names
        blob = json.dumps(self.ent(e))
        for word in (tid, e["user"]["id"], t["user"]["alias"]):
            self.assertNotIn(word, blob)


if __name__ == "__main__":
    unittest.main()
