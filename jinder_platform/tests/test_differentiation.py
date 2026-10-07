"""Differentiation tests (V2_PLAN.md, section 9): the 50 synthetic jobs and the 50 synthetic talents must give scores that differ.

The test uses ONLY the engine functions. It does not import platform modules. A small helper in this file builds the engine
dictionaries from the JSON files in `jinder_backend_engine/data/synthetic`.

The product score of a talent for a job (the same as the platform: 0.55 fit + 0.45 FRS, with no behaviour data):

    fit     = 01 evaluate_job_fit(talent, job)["fit"]                       (0 to 100, one decimal)
    FRS     = 05 rank_job_feed_for_candidate(talent, all 50 jobs)           (feed_ranking_score, one decimal, with the employer diversity penalty)
    score   = round(0.55 x fit + 0.45 x FRS, 1)

The employer order of a talent for a job:

    order   = round(0.6 x coverage + 0.4 x TSS, 1)
    coverage = 06 compute_talent_search_score(...)["skill_coverage"]       (0 to 100, level-aware skill coverage)
    TSS      = 06 compute_talent_search_score(...)["talent_search_score"]  (shared profile only)

The checks:
  1. For each talent: the top 20 jobs have at least 18 different scores (one decimal).
  2. For each talent: best minus worst score is 30 points or more.
  3. For each talent: none of the 8 radar axes of "How this job fits you" has the same value for all 50 jobs.
  4. For each job: the order of the 50 talents has at most 2 exact ties in the top 10.
  5. Near-twin jobs (same specialisation and level, nearly the same skills) never get the same score for a talent.
  6. A job ladder (the same specialisation at several levels) is ordered by level fit around the level of the talent.
  7. A bridge talent (the target role is in another specialisation) can reach jobs of the target area.

If the data files do not exist, the tests are skipped with a message.
Run:  python -m unittest test_differentiation     (from the tests folder)     or     python test_differentiation.py   (prints the numbers)
"""
import importlib.util
import json
import os
import statistics
import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("JINDER_ENGINE_DIR") or Path(__file__).resolve().parents[2] / "jinder_backend_engine" / "intelligence_engine")
DATA_DIR = Path(os.environ.get("JINDER_SYNTHETIC_DIR") or ENGINE_DIR.parent / "data" / "synthetic")
JOBS_FILE, TALENTS_FILE = DATA_DIR / "jobs.json", DATA_DIR / "talents.json"
FIT_WEIGHT, FRS_WEIGHT = 0.55, 0.45
ORDER_COVERAGE_WEIGHT, ORDER_TSS_WEIGHT = 0.6, 0.4
TOP = 20
MIN_DISTINCT_TOP = 18
MIN_SPREAD = 30.0
MAX_TOP10_TIES = 2
AXES = ["occupation", "skills", "methods", "readiness", "capability", "pay", "location", "freshness"]

_FILES = {"f1": "01_skill_matching_model.py", "f2": "02_skill_gap_analysis.py", "f3": "03_job_to_job_comparison.py",
          "f4": "04_candidate_benchmarking.py", "f5": "05_job_seeker_ranking_feed.py", "f6": "06_recruiter_candidate_ranking.py"}
_modules = {}


def load(key):
    if key not in _modules:
        spec = importlib.util.spec_from_file_location("diff_engine_" + key, str(ENGINE_DIR / _FILES[key]))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _modules[key] = module
    return _modules[key]


# ---------------------------------------------------------------------
# A small builder: JSON of the synthetic files -> the dictionaries of the engine (V2_PLAN.md, section 6)
# ---------------------------------------------------------------------
def job_dict(j):
    sal = j.get("salary") or {}
    occ = j.get("occupation") or {}
    certs = j.get("certifications") or {}
    return {
        "id": j.get("key") or j.get("id"), "title": j["title"], "company": j["company"], "category": j["domain"], "specialisation": j.get("specialisation"),
        "level": j.get("level"), "min_years": j.get("minYears"), "max_years": j.get("maxYears"),
        "city": j.get("city"), "location": j.get("area") or j.get("city"), "work_mode": j.get("workMode"), "type": j.get("type"),
        "anzsco_code": occ.get("code", ""), "anzsco_title": occ.get("title", ""),
        "salary_min": sal.get("min"), "salary_max": sal.get("max"), "salary_unit": sal.get("unit"),
        "required_skills": [{"name": s["name"], "level": s["level"], "must": s["must"]} for s in j.get("skills") or []],
        "requirements": [s["name"] for s in j.get("skills") or []],
        "certifications_required": list(certs.get("required") or []), "certifications_preferred": list(certs.get("preferred") or []),
        "awards_preferred": list((j.get("awards") or {}).get("preferred") or []), "education_min": j.get("educationMin"),
        "days_old": j.get("postedDaysAgo"), "description": j.get("description", ""),
    }


EDUCATION_ORDER = ("doctor", "phd", "master", "bachelor", "diploma", "certificate")


def talent_dict(t, index):
    quals = t.get("qualification") or []
    best = ""
    for word in EDUCATION_ORDER:                       # the highest qualification
        found = [q for q in quals if word in str(q).lower()]
        if found:
            best = found[0]
            break
    locations = list(t.get("locations") or [])
    return {
        "id": t.get("alias") or "talent-%d" % index, "alias": t.get("alias"), "current_title": t.get("currentRole"), "level": t.get("level"),
        "years_experience": t.get("yearsExperience"), "domain": t.get("domain"), "specialisation": t.get("specialisation"),
        "target_roles": list(t.get("targetRole") or []), "highest_education": best or (quals[0] if quals else ""),
        "field_of_study": list(t.get("fieldOfStudy") or []),
        "skills": [{"name": s["name"], "skill_name": s["name"], "level": s.get("level"), "years": s.get("years"), "last_used_year": s.get("lastUsedYear")}
                   for s in t.get("skills") or []],
        "certifications": list(t.get("certifications") or []), "awards": list(t.get("awards") or []),
        "preferred_location": locations[0] if locations else "", "locations": locations,
        "work_modes": list(t.get("workModes") or []), "work_types": list(t.get("workTypes") or []),
        # no cv_raw_text and no evidence lines: this is the shared profile, and the talent screens need nothing more
    }


def load_data():
    jobs = [job_dict(j) for j in json.loads(JOBS_FILE.read_text(encoding="utf-8"))["jobs"]]
    talents = [talent_dict(t, i) for i, t in enumerate(json.loads(TALENTS_FILE.read_text(encoding="utf-8"))["talents"])]
    return jobs, talents


def near_twins(jobs):
    """Pairs of jobs with the same specialisation and level, and a skill-name overlap (Jaccard) of 0.75 or more."""
    out = []
    for i in range(len(jobs)):
        for k in range(i + 1, len(jobs)):
            a, b = jobs[i], jobs[k]
            if a["specialisation"] != b["specialisation"] or a["level"] != b["level"]:
                continue
            sa, sb = {s["name"] for s in a["required_skills"]}, {s["name"] for s in b["required_skills"]}
            if len(sa & sb) / float(len(sa | sb)) >= 0.75:
                out.append((a["id"], b["id"]))
    return out


def role_specs():
    """Which specialisations each role title fits (the table of the talent checker). None if the checker is not there."""
    path = DATA_DIR / "validate_talents.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("diff_validate_talents", str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.ROLE_SPECS
    except Exception:  # noqa: BLE001 - the table is only a help for one test
        return None


DATA_OK = JOBS_FILE.is_file() and TALENTS_FILE.is_file()
SKIP_MESSAGE = "The synthetic data files do not exist yet: %s and %s. Write them first (Data agents), then run this test again." % (JOBS_FILE, TALENTS_FILE)


@unittest.skipUnless(DATA_OK, SKIP_MESSAGE)
class DifferentiationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f1, cls.f2, cls.f5, cls.f6 = load("f1"), load("f2"), load("f5"), load("f6")
        cls.jobs, cls.talents = load_data()
        cls.job_ids = [j["id"] for j in cls.jobs]
        assert len(cls.jobs) == 50 and len(cls.talents) == 50, "expected 50 jobs and 50 talents"
        cls.scores = {}        # talent id -> {job id -> product score}
        cls.fits = {}          # talent id -> {job id -> fit result}
        cls.axes = {}          # talent id -> {axis -> [value for each job]}
        for t in cls.talents:
            feed = cls.f5.rank_job_feed_for_candidate(t, cls.jobs, top_limit=len(cls.jobs))["top_feed"]
            frs = {x["job_id"]: x for x in feed}
            per_job, fit_by_job = {}, {}
            axes = {a: [] for a in AXES}
            for j in cls.jobs:
                fit = cls.f1.evaluate_job_fit(t, j)
                per_job[j["id"]] = round(FIT_WEIGHT * fit["fit"] + FRS_WEIGHT * frs[j["id"]]["feed_ranking_score"], 1)
                fit_by_job[j["id"]] = fit
                m = cls.f1.evaluate_skill_match(t, j)["sub_metrics"]
                g = cls.f2.evaluate_skill_gaps(t, j)
                f5 = frs[j["id"]]["sub_metrics"]
                values = {"occupation": m["s_tree_taxonomy"], "skills": m["s_direct_competency"], "methods": m["s_trans_methodology"],
                          "readiness": g["job_readiness_score"], "capability": f5["s_cap_capability"], "pay": f5["s_wage_upside"],
                          "location": f5["s_loc_location"], "freshness": f5["s_rec_recency"]}
                for a in AXES:
                    axes[a].append(round(values[a], 1))
            cls.scores[t["id"]] = per_job
            cls.fits[t["id"]] = fit_by_job
            cls.axes[t["id"]] = axes
        cls.orders = {}        # job id -> {talent id -> order value}
        for j in cls.jobs:
            row = {}
            for t in cls.talents:
                r = cls.f6.compute_talent_search_score(t, j)
                row[t["id"]] = round(ORDER_COVERAGE_WEIGHT * r["skill_coverage"] + ORDER_TSS_WEIGHT * r["talent_search_score"], 1)
            cls.orders[j["id"]] = row

    # ----- the numbers (used by the tests and by the report) -----
    @classmethod
    def numbers(cls):
        distinct = {tid: len(set(sorted(s.values(), reverse=True)[:TOP])) for tid, s in cls.scores.items()}
        spread = {tid: max(s.values()) - min(s.values()) for tid, s in cls.scores.items()}
        ties = {}
        for jid, row in cls.orders.items():
            top = sorted(row.values(), reverse=True)[:10]
            ties[jid] = len(top) - len(set(top))
        return distinct, spread, ties

    def test_top_20_scores_are_different(self):
        distinct, _, _ = self.numbers()
        bad = {tid: n for tid, n in distinct.items() if n < MIN_DISTINCT_TOP}
        self.assertFalse(bad, "Talents with fewer than %d different scores in the top %d: %s" % (MIN_DISTINCT_TOP, TOP, bad))

    def test_best_minus_worst_is_30_points_or_more(self):
        _, spread, _ = self.numbers()
        bad = {tid: round(v, 1) for tid, v in spread.items() if v < MIN_SPREAD}
        self.assertFalse(bad, "Talents with a spread below %.0f points: %s" % (MIN_SPREAD, bad))

    def test_no_radar_axis_is_the_same_for_all_jobs(self):
        bad = []
        for tid, axes in self.axes.items():
            for a, values in axes.items():
                if len(set(values)) < 2:
                    bad.append((tid, a, values[0]))
        self.assertFalse(bad, "Axes with the same value for all 50 jobs: %s" % bad)

    def test_the_employer_order_has_at_most_2_ties_in_the_top_10(self):
        _, _, ties = self.numbers()
        bad = {jid: n for jid, n in ties.items() if n > MAX_TOP10_TIES}
        self.assertFalse(bad, "Jobs with more than %d exact ties in the top 10 of the talent order: %s" % (MAX_TOP10_TIES, bad))

    def test_all_scores_are_between_0_and_100(self):
        for tid, s in self.scores.items():
            self.assertTrue(all(0.0 <= v <= 100.0 for v in s.values()), tid)
        for jid, row in self.orders.items():
            self.assertTrue(all(0.0 <= v <= 100.0 for v in row.values()), jid)
        for tid, axes in self.axes.items():
            for a, values in axes.items():
                self.assertTrue(all(0.0 <= v <= 100.0 for v in values), (tid, a))

    def test_near_twin_jobs_never_get_the_same_score(self):
        twins = near_twins(self.jobs)
        self.assertTrue(twins, "the data has no near-twin pair")
        same = [(tid, a, b, s[a]) for tid, s in self.scores.items() for a, b in twins if s[a] == s[b]]
        self.assertFalse(same, "Near-twin jobs with the same score for a talent: %s" % same[:10])
        # the two fit numbers are different too, not only the rounded product
        for tid, fits in self.fits.items():
            for a, b in twins:
                self.assertNotEqual(fits[a]["fit_exact"], fits[b]["fit_exact"], (tid, a, b))

    def test_a_job_ladder_is_ordered_by_level_fit_around_the_level_of_the_talent(self):
        by_spec = {}
        for j in self.jobs:
            by_spec.setdefault(j["specialisation"], []).append(j)
        tax = load("f1").C.get_taxonomy()
        ladders = {s: js for s, js in by_spec.items() if len({j["level"] for j in js}) >= 3}
        self.assertTrue(ladders, "the data has no job ladder (one specialisation at 3 or more levels)")
        checked = 0
        for t in self.talents:
            rank = tax.level_rank(t["level"])
            for spec, js in ladders.items():
                rows = sorted(((tax.level_rank(j["level"]), self.fits[t["id"]][j["id"]]["parts"]["level"]) for j in js))
                for (r1, p1), (r2, p2) in zip(rows, rows[1:]):
                    if r1 == r2:
                        self.assertEqual(p1, p2)
                    elif r2 <= rank:           # both rungs are at or below the talent: the nearer rung fits better
                        self.assertLess(p1, p2, (t["id"], spec, r1, r2))
                    elif r1 >= rank:           # both rungs are at or above the talent: the nearer rung fits better
                        self.assertGreater(p1, p2, (t["id"], spec, r1, r2))
                    checked += 1
        self.assertGreater(checked, 100)

    def test_the_rung_of_the_talent_is_usually_the_best_rung_of_a_ladder(self):
        """For a talent in a ladder specialisation, the job at the level of the talent scores higher than a job 2 or more levels away (same specialisation)."""
        tax = load("f1").C.get_taxonomy()
        wins = total = 0
        for t in self.talents:
            rank = tax.level_rank(t["level"])
            same = [j for j in self.jobs if j["specialisation"] == t["specialisation"]]
            near = [j for j in same if abs(tax.level_rank(j["level"]) - rank) == 0]
            far = [j for j in same if abs(tax.level_rank(j["level"]) - rank) >= 2]
            if near and far:
                total += 1
                wins += max(self.scores[t["id"]][j["id"]] for j in near) > max(self.scores[t["id"]][j["id"]] for j in far)
        self.assertGreater(total, 10)
        self.assertGreaterEqual(wins / float(total), 0.8, "the rung of the talent wins in only %d of %d cases" % (wins, total))

    def test_a_bridge_talent_can_reach_jobs_of_the_target_area(self):
        specs = role_specs()
        if not specs:
            self.skipTest("the role table of validate_talents.py is not available")
        raw = json.loads(TALENTS_FILE.read_text(encoding="utf-8"))["talents"]
        bridge, reachable = 0, 0
        problems = []
        for t, r in zip(self.talents, raw):
            target = set()
            for role in r.get("targetRole") or []:
                target |= specs.get(role, set())
            if not target or r["specialisation"] in target:
                continue
            bridge += 1
            area = [j for j in self.jobs if j["specialisation"] in target]
            ranked = sorted(self.jobs, key=lambda j: (-self.scores[t["id"]][j["id"]], j["id"]))
            top = {j["id"] for j in ranked[:TOP]}
            hits = [j["id"] for j in area if j["id"] in top]
            if len(hits) >= 1:
                reachable += 1
            else:
                problems.append((t["alias"], r["specialisation"], sorted(target)))
            # the path to the best job of the target area exists and has a finite time
            best = max(area, key=lambda j: self.scores[t["id"]][j["id"]])
            path = self.f2.evaluate_path(t, best)
            self.assertTrue(path["axes"])
            self.assertGreaterEqual(path["summary"]["monthsToClose"], 0.0)
        self.assertGreaterEqual(bridge, 5, "the data has fewer than 5 bridge talents")
        self.assertFalse(problems, "Bridge talents with no target-area job in the top %d: %s" % (TOP, problems))


def report():
    """Print the numbers of the differentiation (for the report of the agent)."""
    DifferentiationTests.setUpClass()
    distinct, spread, ties = DifferentiationTests.numbers()
    d = list(distinct.values())
    s = list(spread.values())
    t = list(ties.values())
    print("Top-%d distinct scores (1 decimal): min %d, mean %.2f, talents below %d: %d of %d" % (TOP, min(d), statistics.mean(d), MIN_DISTINCT_TOP,
                                                                                               sum(1 for x in d if x < MIN_DISTINCT_TOP), len(d)))
    print("Best minus worst: min %.1f, mean %.1f, max %.1f" % (min(s), statistics.mean(s), max(s)))
    print("Exact ties in the top 10 of the talent order (per job): max %d, mean %.2f, jobs above %d: %d of %d" % (max(t), statistics.mean(t), MAX_TOP10_TIES,
                                                                                                                sum(1 for x in t if x > MAX_TOP10_TIES), len(t)))
    twins = near_twins(DifferentiationTests.jobs)
    gaps = [abs(sc[a] - sc[b]) for sc in DifferentiationTests.scores.values() for a, b in twins]
    print("Near-twin pairs: %d. Smallest score difference for a talent: %.1f, median %.1f" % (len(twins), min(gaps), statistics.median(gaps)))
    const = sum(1 for axes in DifferentiationTests.axes.values() for v in axes.values() if len(set(v)) < 2)
    print("Radar axes with the same value for all jobs: %d of %d" % (const, len(AXES) * len(DifferentiationTests.talents)))


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        unittest.main()
