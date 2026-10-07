"""Differentiation through the PLATFORM path (V2_PLAN.md, section 9).

`tests/test_differentiation.py` checks the formulas with the data files. This file checks the same promises through the code of the platform:
the dictionaries of the bridge, `TalentContext.rank_all`, the order of the employer list and the detail of a job.

For each of the 50 sample talents (and the demo talent) over all open jobs, the list sorted by `match.score`:
  * at least 18 different scores in the top 20 (the plan said 19: the lead relaxed it to 18)
  * best minus worst at least 30 points
  * no radar axis has the same value for all jobs
  * the score of a job in the list is the score on the page of the job
and, over the 50 sample talents, for each job: at most 2 exact ties in the top 10 of the order of the employer.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import helpers as H
from jinder import catalogue, config, db, engine_bridge as eb, seed, store
from jinder.routes import recruiter
from jinder.routes.jobs import talent_context

SAMPLE = 6          # how many jobs get a page-detail check for each talent


class PlatformDifferentiationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp(prefix="jinder-diff-"))
        path = cls.folder / "jinder.db"
        db.init_db(path, cls.folder / "uploads")
        cls.conn = db.connect(path)
        seed.seed_all(cls.conn)
        with db.transaction(cls.conn):
            seed.seed_demo_accounts(cls.conn)
        cls.jobs = catalogue.load_jobs(cls.conn)
        cls.open_jobs = [j for j in cls.jobs if catalogue.is_open(j)]
        cls.users = cls.conn.execute("SELECT * FROM users WHERE role = 'candidate' AND onboarding = 'done' ORDER BY alias").fetchall()
        cls.contexts = {u["alias"]: talent_context(cls.conn, u, cls.jobs) for u in cls.users}
        cls.ranked = {alias: ctx.rank_all(cls.open_jobs) for alias, ctx in cls.contexts.items()}

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        shutil.rmtree(cls.folder, True)

    def test_the_data_is_the_data_of_the_plan(self):
        self.assertEqual(len(self.users), 51)                      # 50 sample talents and the demo talent
        self.assertEqual(sum(1 for j in self.open_jobs if j["ownerId"] is None), 50)
        self.assertEqual(len(self.open_jobs), 53)                  # and the 3 open jobs of the demo employer

    def test_top_20_has_at_least_18_different_scores(self):
        for alias, pairs in self.ranked.items():
            top = sorted((m["score"] for _, m in pairs), reverse=True)[:20]
            self.assertGreaterEqual(len(set(top)), 18, alias)
            self.assertTrue(all(round(x, 1) == x and 0 <= x <= 100 for x in top))

    def test_the_best_job_is_far_from_the_worst(self):
        spreads = []
        for alias, pairs in self.ranked.items():
            scores = [m["score"] for _, m in pairs]
            spreads.append(max(scores) - min(scores))
            self.assertGreaterEqual(max(scores) - min(scores), 30, alias)
        self.assertGreaterEqual(min(spreads), 30)

    def test_no_radar_axis_is_the_same_for_all_jobs(self):
        # the 8 axes of "How this job fits you", for all the open jobs of each talent
        for alias, ctx in self.contexts.items():
            by_axis = {}
            for j in self.open_jobs:
                for a in catalogue.fit_axes_for(ctx, j):
                    by_axis.setdefault(a["key"], set()).add(a["value"])
            self.assertEqual(len(by_axis), 8, alias)
            for key, values in by_axis.items():
                self.assertGreater(len(values), 1, (alias, key))

    def test_the_score_in_the_list_is_the_score_on_the_page(self):
        for alias in sorted(self.contexts)[:8] + ["Teal Heron"]:
            ranked = sorted(self.ranked[alias], key=lambda p: -p[1]["score"])
            pick = ranked[:2] + ranked[len(ranked) // 2: len(ranked) // 2 + 2] + ranked[-2:]
            user = next(u for u in self.users if u["alias"] == alias)
            for job, match in pick:
                # a new context for the page: the talent opens the page of one job. Its score must be the score of the list.
                detail = catalogue.job_detail(talent_context(self.conn, user, self.jobs), self.jobs, job["id"])
                self.assertEqual(detail["match"]["score"], match["score"], (alias, job["id"]))
                self.assertEqual(detail["bridge"]["score"], match["score"])
                self.assertEqual(detail["match"]["coverage"], match["coverage"])

    def test_the_score_does_not_change_when_the_talent_skips_or_applies_to_other_jobs(self):
        # the lists remove the jobs that the talent skipped or applied to AFTER the ranking: the other scores stay the same
        alias = "Teal Heron"
        before = {j["id"]: m["score"] for j, m in self.ranked[alias]}
        pool = catalogue.recommended_pairs(self.contexts[alias], self.jobs, {self.open_jobs[0]["id"], self.open_jobs[1]["id"]})
        for j, m in pool:
            self.assertEqual(m["score"], before[j["id"]])

    def test_the_employer_order_has_at_most_2_exact_ties_in_the_top_10(self):
        c = self.conn
        pool = store.candidate_pool(c)
        worst = 0
        for job in self.open_jobs:
            jd = eb.prepare_job(eb.job_dict(job))
            values = []
            for cand in pool:
                if cand["alias"] == "Teal Heron":
                    continue
                ts = eb.talent_score(recruiter._shared_candidate(cand), jd)
                values.append((-round(ts["order_value"], 1), cand["id"]))
            top = [v for v, _ in sorted(values)[:10]]
            ties = len(top) - len(set(top))
            worst = max(worst, ties)
            self.assertLessEqual(ties, 2, job["id"])
        self.assertLessEqual(worst, 2)

    def test_the_employer_list_orders_by_the_engine_and_shows_no_score(self):
        owner = self.conn.execute("SELECT * FROM users WHERE email = ?", (seed.DEMO_EMPLOYER,)).fetchone()
        job = next(j for j in self.jobs if j["ownerId"] == owner["id"] and j["id"] == "job-demo-data-engineer-mid")
        jd = eb.prepare_job(eb.job_dict(job))
        pool = [c for c in store.candidate_pool(self.conn) if c["alias"] != "Teal Heron"]
        cards = [recruiter._card(self.conn, owner, c, job, set(), {}, jd) for c in pool]
        orders = [o for _, o in cards]
        self.assertTrue(any(o > 0 for o in orders))
        for card, _ in cards:
            self.assertEqual(set(card) & {"score", "order", "tss", "orderValue", "talent_search_score"}, set())
            self.assertTrue(card["coverage"] is None or 0 <= card["coverage"] <= 100)
        best = max(cards, key=lambda t: t[1])[0]
        # the best order has a high cover of the must-have skills: the platform used the engine, not a count of words
        self.assertGreaterEqual(best["coverage"], 60)


class EngineDictionaryPrivacyTests(unittest.TestCase):
    """The dictionaries that go into the formulas have no personal data and no private key (AI_Rule Rule 5, items 3, 8 and 9)."""

    # the keys that a skill, a certification or an award may have. "name" is the name of the skill or of the certification, never of a person.
    ITEM_KEYS = {"skill_name", "name", "skill_type", "level", "years", "issuer", "year", "kind"}
    BANNED_KEYS = ("name", "email", "origin", "country", "nationality", "visa", "gender", "age", "birth", "phone", "photo", "study", "evidence")

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.c = cls.p.conn()
        cls.demo = cls.c.execute("SELECT * FROM users WHERE email = ?", (seed.DEMO_TALENT,)).fetchone()
        cls.jobs = catalogue.load_jobs(cls.c)

    def keys_of(self, value, found=None):
        found = set() if found is None else found
        if isinstance(value, dict):
            for k, v in value.items():
                found.add(str(k).lower())
                self.keys_of(v, found)
        elif isinstance(value, (list, tuple)):
            for v in value:
                self.keys_of(v, found)
        return found

    def test_the_dictionary_of_a_talent_has_no_private_key(self):
        tctx = talent_context(self.c, self.demo, self.jobs)
        cand = tctx.engine_candidate
        for word in self.BANNED_KEYS:
            self.assertFalse([k for k in cand if word == k or k.startswith(word + "_")], word)        # the keys of the dictionary
        self.assertLessEqual(self.keys_of(cand["skills"]) | self.keys_of(cand["certifications"]) | self.keys_of(cand["awards"]), self.ITEM_KEYS)
        text = json.dumps(cand)
        for secret in ("Vietnam", "Linh", "Nguyen", "@", "candidate@demo"):
            self.assertNotIn(secret, text)

    def test_the_dictionary_for_an_employer_has_no_cv_no_evidence_no_private_key(self):
        for cand in store.candidate_pool(self.c):
            d = eb.shared_candidate_dict(cand["shared"], cand["id"])
            self.assertNotIn("cv_raw_text", d)
            text = json.dumps(d)
            for word in ("name", "email", "origin", "country", "nationality", "visa", "gender", "birth", "phone", "photo", "evidence", "study"):
                self.assertFalse([k for k in d if k == word or k.startswith(word + "_")], (cand["alias"], word))
            self.assertLessEqual(self.keys_of(d["skills"]) | self.keys_of(d["certifications"]) | self.keys_of(d["awards"]), self.ITEM_KEYS)
            for line in cand["profile"]["evidence"]:
                self.assertNotIn(line[:30], text)
            for country in cand["profile"]["studyCountry"]:
                self.assertNotIn(country, text)
            prepared = eb.prepare_candidate(d, shared_only=True)
            self.assertEqual(prepared["alias"], cand["alias"])

    def test_the_employer_dictionary_changes_when_only_the_shared_profile_changes(self):
        cand = next(c for c in store.candidate_pool(self.c) if c["alias"] != "Teal Heron")
        base = eb.shared_candidate_dict(cand["shared"], cand["id"])
        private = json.loads(json.dumps(cand["profile"]))
        private["evidence"] = ["A secret line"]
        private["studyCountry"] = ["Nowhere"]
        same = eb.candidate_dict(private, [r for r in private["translation"] if store.is_shared(r)], cand["alias"], cand["id"], None, private=False)
        self.assertEqual(json.dumps(same, sort_keys=True), json.dumps(base, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
