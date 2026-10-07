"""The six formulas of the Jinder engine (version 2): their properties.

These tests load the formula files from `jinder_backend_engine/intelligence_engine` by path, the same way as the platform bridge.
They do not start the platform and they do not import platform modules, so they stay valid when the bridge changes.

What they check (V2_PLAN.md, sections 6 and 9):
  bounds from 0 to 100, continuity, monotonic effects of level, years and skill level, partial credit for a level gap,
  certifications and awards, Remote locations, determinism, symmetry of Formula 3, the old dictionary shapes,
  a run without the taxonomy file, and that no private field is read.
"""
import importlib.util
import json
import os
import re
import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("JINDER_ENGINE_DIR") or Path(__file__).resolve().parents[2] / "jinder_backend_engine" / "intelligence_engine")
_FILES = {"f1": "01_skill_matching_model.py", "f2": "02_skill_gap_analysis.py", "f3": "03_job_to_job_comparison.py",
          "f4": "04_candidate_benchmarking.py", "f5": "05_job_seeker_ranking_feed.py", "f6": "06_recruiter_candidate_ranking.py"}
_modules = {}


def load(key):
    """Load one formula file by its path (the file names start with a digit, so `import` cannot load them)."""
    if key not in _modules:
        spec = importlib.util.spec_from_file_location("test_engine_" + key, str(ENGINE_DIR / _FILES[key]))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _modules[key] = module
    return _modules[key]


def common():
    load("f1")
    return sys.modules["jinder_engine_common"]


# ---------------------------------------------------------------------
# Fixtures: one talent and one job, with every version 2 key
# ---------------------------------------------------------------------
def talent(**kw):
    base = {"id": "t1", "alias": "Test Talent", "level": "Mid", "years_experience": 4.0, "domain": "Data", "specialisation": "Data engineering",
            "current_title": "Data Engineer", "target_roles": ["Data Engineer"], "highest_education": "Bachelor's degree",
            "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 4}, {"name": "Apache Spark", "level": 3}],
            "certifications": [], "awards": [], "preferred_location": "Sydney", "locations": ["Sydney"], "work_modes": ["Hybrid"],
            "work_types": ["Full-time"]}
    base.update(kw)
    return base


def job(**kw):
    base = {"id": "j1", "title": "Data Engineer", "company": "Test Co", "category": "Data", "specialisation": "Data engineering", "level": "Mid",
            "min_years": 2, "max_years": 5, "city": "Sydney", "location": "Sydney", "work_mode": "Hybrid", "type": "Full-time", "anzsco_code": "262111",
            "salary_min": 120000, "salary_max": 140000, "education_min": "Bachelor's degree", "days_old": 5,
            "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True},
                                {"name": "Apache Spark", "level": 3, "must": False}],
            "certifications_required": [], "certifications_preferred": [], "awards_preferred": []}
    base.update(kw)
    return base


def with_skill(t, name, level):
    out = dict(t)
    out["skills"] = [s for s in t["skills"] if s["name"] != name] + ([{"name": name, "level": level}] if level else [])
    return out


class EngineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f1, cls.f2, cls.f3, cls.f4, cls.f5, cls.f6 = (load(k) for k in ("f1", "f2", "f3", "f4", "f5", "f6"))
        cls.C = common()
        cls.C.set_taxonomy(None)          # the real taxonomy file
        cls.tax = cls.C.get_taxonomy()

    def fit(self, t, j):
        return self.f1.evaluate_job_fit(t, j)["fit"]

    def assertBounded(self, value, msg=""):
        self.assertTrue(0.0 <= value <= 100.0, f"{msg} {value}")


# =====================================================================
# Loading and the taxonomy
# =====================================================================
class LoadTests(EngineTestCase):
    def test_all_formula_files_load_and_have_the_old_names(self):
        for key, names in {"f1": ["evaluate_skill_match", "evaluate_job_fit", "calculate_experience_multiplier"],
                           "f2": ["evaluate_skill_gaps", "evaluate_path"],
                           "f3": ["compare_two_jobs", "compare_multiple_jobs", "get_job_salary_midpoint"],
                           "f4": ["calculate_candidate_merit_score", "compare_two_candidates", "rank_candidate_cohort"],
                           "f5": ["compute_feed_job_score", "rank_job_feed_for_candidate"],
                           "f6": ["compute_talent_search_score", "rank_candidates_for_job_requisition"]}.items():
            for name in names:
                self.assertTrue(callable(getattr(load(key), name, None)), f"{key}.{name}")

    def test_the_taxonomy_is_loaded_from_the_engine_folder(self):
        self.assertTrue(self.tax.loaded, "ict_taxonomy.json was not found next to the engine")
        self.assertGreaterEqual(len(self.tax.skills), 100)
        self.assertEqual(self.tax.level_names, ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"])

    def test_names_and_aliases_are_case_insensitive(self):
        for text in ("Python", "python", "PYTHON", " pyThon ", "py", "Python3"):
            self.assertEqual(self.tax.canon_skill_name(text), "Python", text)
        self.assertEqual(self.tax.canon_skill_name("ci/cd"), self.tax.canon_skill_name("CI CD"))
        self.assertIsNone(self.tax.canon_skill_name("zzz not a skill"))
        name, entry = self.tax.canon_cert("snowpro core certification")
        self.assertTrue(entry)
        self.assertEqual(self.tax.canon_cert("SnowPro Core Certification")[0], name)


# =====================================================================
# Formula 1
# =====================================================================
class Formula1Tests(EngineTestCase):
    def test_skill_credit_is_smooth_and_has_a_small_bonus_above_the_level(self):
        f1 = self.f1
        values = [f1.skill_credit(h / 10.0, 3.0) for h in range(0, 51)]
        self.assertEqual(values, sorted(values), "credit must not fall when the level rises")
        self.assertAlmostEqual(f1.skill_credit(3.0, 3.0), 1.0, places=9)
        self.assertLess(f1.skill_credit(2.0, 3.0), 1.0)
        self.assertGreater(f1.skill_credit(5.0, 3.0), 1.0)
        self.assertLessEqual(max(values), 1.0 + f1.SURPLUS_CREDIT + 1e-9)
        self.assertLess(max(abs(b - a) for a, b in zip(values, values[1:])), 0.12, "no jump between two close levels")

    def test_the_fit_is_between_0_and_100_with_one_decimal(self):
        for t in (talent(), talent(skills=[], years_experience=0, level="Intern"), talent(level="Principal", years_experience=30)):
            for j in (job(), job(required_skills=[]), job(level="Principal", min_years=10, max_years=20), job(city="Perth", work_mode="Onsite")):
                r = self.f1.evaluate_job_fit(t, j)
                self.assertBounded(r["fit"])
                self.assertEqual(round(r["fit"], 1), r["fit"])
                for key, v in r["parts"].items():
                    if v is not None:
                        self.assertBounded(v, key)
                m = self.f1.evaluate_skill_match(t, j)
                self.assertBounded(m["overall_score"])
                for v in m["sub_metrics"].values():
                    if v is not None and v is not m["sub_metrics"]["phi_experience_multiplier"]:
                        self.assertTrue(0.0 <= v <= 100.0)

    def test_a_better_match_has_a_higher_fit(self):
        weak = talent(skills=[{"name": "SQL", "level": 2}])
        mid = talent(skills=[{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}])
        strong = talent()
        j = job()
        self.assertLess(self.fit(weak, j), self.fit(mid, j))
        self.assertLess(self.fit(mid, j), self.fit(strong, j))

    def test_skill_level_is_monotone_and_below_the_level_gets_partial_credit(self):
        j = job()
        fits = [self.fit(with_skill(talent(), "Python", lvl), j) for lvl in (0, 1, 2, 3, 4, 5)]
        self.assertEqual(fits, sorted(fits))
        self.assertLess(fits[0], fits[3])
        res = self.f1.evaluate_job_fit(with_skill(talent(), "Python", 2), j)
        item = next(i for i in res["skill_breakdown"] if i["name"] == "Python")
        self.assertEqual(item["status"], "below")
        self.assertTrue(0.0 < item["credit"] < 1.0)
        self.assertEqual(item["need_level"], 4.0)

    def test_exact_skill_beats_a_related_skill_and_a_related_skill_beats_nothing(self):
        j = job(required_skills=[{"name": "Apache Airflow", "level": 3, "must": True}])
        tax = self.tax
        related = sorted(tax.related.get("Apache Airflow", []))
        self.assertTrue(related, "the taxonomy has no related skill for Apache Airflow")
        exact = self.f1.evaluate_job_fit(talent(skills=[{"name": "Apache Airflow", "level": 3}]), j)
        rel = self.f1.evaluate_job_fit(talent(skills=[{"name": related[0], "level": 4}]), j)
        none = self.f1.evaluate_job_fit(talent(skills=[{"name": "Figma", "level": 4}]), j)
        c = lambda r: r["skill_breakdown"][0]["credit"]
        self.assertGreater(c(exact), c(rel))
        self.assertGreater(c(rel), c(none))
        self.assertEqual(rel["skill_breakdown"][0]["status"], "related")
        self.assertEqual(none["skill_breakdown"][0]["status"], "missing")
        self.assertLessEqual(c(rel), self.f1.RELATED_MAX + 1e-9)

    def test_a_missing_must_skill_costs_more_than_a_missing_nice_skill(self):
        t = talent(skills=[{"name": "SQL", "level": 4}])
        j_must = job(required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Docker", "level": 4, "must": True}])
        j_nice = job(required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Docker", "level": 4, "must": False}])
        self.assertLess(self.fit(t, j_must), self.fit(t, j_nice))

    def test_a_level_gap_lowers_the_credit(self):
        t = talent(level="Mid", years_experience=4)
        fits = {lvl: self.fit(t, job(level=lvl, min_years=None, max_years=None)) for lvl in ("Intern", "Junior", "Mid", "Senior", "Lead", "Principal")}
        # below the level of the talent: the over-qualified penalty is small. Above: the penalty is larger.
        self.assertGreater(fits["Mid"], fits["Senior"])
        self.assertGreater(fits["Senior"], fits["Lead"])
        self.assertGreater(fits["Lead"], fits["Principal"])
        self.assertGreater(fits["Mid"], fits["Junior"])
        # a gap upward costs more than the same gap downward
        up, down = self.f1.level_fit(2, 3), self.f1.level_fit(2, 1)
        self.assertLess(up, down)
        self.assertEqual(self.f1.level_fit(3, 3), 1.0)
        self.assertIsNone(self.f1.level_fit(None, 3))

    def test_years_of_experience_are_monotone_below_the_minimum_and_smooth(self):
        j = job(min_years=5, max_years=8, level="Senior")
        values = [self.f1.years_fit(y / 4.0, 5, 8) for y in range(0, 21)]
        self.assertEqual(values, sorted(values))
        self.assertLess(values[0], 0.2)
        self.assertLess(max(abs(b - a) for a, b in zip(values, values[1:])), 0.12)
        self.assertTrue(0.99 <= self.f1.years_fit(8, 5, 8) <= 1.0)
        self.assertLess(self.f1.years_fit(25, 5, 8), 0.9)       # a large surplus costs a little
        self.assertGreater(self.f1.years_fit(25, 5, 8), 0.7)
        fits = [self.fit(talent(years_experience=y, level="Senior"), j) for y in (0, 1, 2, 3, 4, 5)]
        self.assertEqual(fits, sorted(fits))
        # the multiplier of the old call (years, ANZSCO skill level) still works and it rises with the years
        mult = [self.f1.calculate_experience_multiplier(y, 1) for y in (0.5, 1, 2, 3, 5, 8, 12, 20)]
        self.assertEqual(mult, sorted(mult))
        self.assertTrue(all(0.75 <= m <= 1.15 for m in mult))

    def test_education_is_a_soft_factor_and_never_a_hard_limit(self):
        j = job(education_min="Doctorate (PhD)")
        fits = {}
        for edu in ("Doctorate (PhD)", "Master's degree", "Bachelor's degree", "Diploma", ""):
            r = self.f1.evaluate_job_fit(talent(highest_education=edu), j)
            fits[edu] = r["fit"]
            part = r["parts"]["education"]
            self.assertTrue(20.0 <= part <= 100.0, (edu, part))      # the part never goes below 20
        ordered = [fits[k] for k in ("Doctorate (PhD)", "Master's degree", "Bachelor's degree", "Diploma", "")]
        self.assertEqual(ordered, sorted(ordered, reverse=True))
        self.assertGreater(ordered[-1], 20.0, "a missing degree must not zero the fit")
        self.assertLess(ordered[0] - ordered[-1], 12.0, "education is a small part of the fit")
        j2 = job(education_min="Bachelor's degree")
        self.assertGreater(self.fit(talent(highest_education="Bachelor's degree"), j2), self.fit(talent(highest_education=""), j2))
        self.assertIsNone(self.f1.evaluate_job_fit(talent(), job(education_min=None))["parts"]["education"])

    def test_a_job_with_no_maximum_of_years_is_open_ended(self):
        values = [self.f1.years_fit(y, 5, None) for y in (5, 6, 8, 12, 30)]
        self.assertEqual(values, sorted(values))
        self.assertLessEqual(max(values), 1.0)
        self.assertTrue(all(v >= 0.92 for v in values))
        j = job(level="Senior", min_years=5, max_years=None)
        self.assertEqual(self.C.prepare_job(j)["max_years"], None)
        self.assertGreaterEqual(self.fit(talent(level="Senior", years_experience=15), j), self.fit(talent(level="Senior", years_experience=6), j) - 0.5)

    def test_a_method_skill_that_is_not_listed_gets_a_small_assumed_credit(self):
        j = job(required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Communication", "level": 3, "must": True},
                                 {"name": "Teamwork", "level": 2, "must": True}])
        t = talent(skills=[{"name": "SQL", "level": 4}])
        r = self.f1.evaluate_job_fit(t, j)
        self.assertTrue(0.0 < r["parts"]["methods"] < 40.0)
        senior = self.f1.evaluate_job_fit(talent(skills=[{"name": "SQL", "level": 4}], level="Senior", years_experience=8), j)
        self.assertGreater(senior["parts"]["methods"], r["parts"]["methods"])
        listed = self.f1.evaluate_job_fit(talent(skills=[{"name": "SQL", "level": 4}, {"name": "Communication", "level": 4}, {"name": "Teamwork", "level": 3}]), j)
        self.assertGreater(listed["parts"]["methods"], 80.0)
        # the assumed credit does not change the per-skill match that an employer sees
        self.assertEqual({i["name"]: i["status"] for i in r["skill_breakdown"]}["Communication"], "missing")
        self.assertEqual({i["name"]: i["credit"] for i in r["skill_breakdown"]}["Communication"], 0.0)

    def test_aliases_and_case_give_the_same_result(self):
        j = job()
        a = self.f1.evaluate_job_fit(talent(skills=[{"name": "SQL", "level": 4}, {"name": "Python", "level": 4}, {"name": "Apache Spark", "level": 3}]), j)
        b = self.f1.evaluate_job_fit(talent(skills=[{"name": "sql", "level": 4}, {"name": "PY", "level": 4}, {"name": "apache spark", "level": 3}]), j)
        self.assertEqual(a["fit"], b["fit"])
        self.assertEqual([i["status"] for i in a["skill_breakdown"]], [i["status"] for i in b["skill_breakdown"]])

    def test_a_held_required_certification_removes_the_gap_and_raises_the_fit(self):
        cert = next(c for c in self.tax.certs if "Databricks" in c)
        j = job(certifications_required=[cert])
        without = talent()
        holds = talent(certifications=[{"name": cert.lower(), "issuer": "x", "year": 2025}])   # a different case is the same certification
        self.assertGreater(self.fit(holds, j), self.fit(without, j))
        gaps_without = [g for g in self.f2.evaluate_skill_gaps(without, j)["gaps"] if g["kind"] == "certification"]
        gaps_holds = [g for g in self.f2.evaluate_skill_gaps(holds, j)["gaps"] if g["kind"] == "certification"]
        self.assertEqual(len(gaps_without), 1)
        self.assertEqual(gaps_holds, [])
        # the fit of a job with no certification is not lower than the fit of the same job with a missing required one
        self.assertGreater(self.fit(without, job()), self.fit(without, j))

    def test_a_preferred_award_gives_a_small_capped_bonus(self):
        j = job(awards_preferred=["hackathon", "open-source"])
        base = self.fit(talent(), j)
        one = self.fit(talent(awards=[{"name": "Demo hackathon winner", "kind": "hackathon", "year": 2025}]), j)
        two = self.fit(talent(awards=[{"name": "A", "kind": "hackathon", "year": 2025}, {"name": "B", "kind": "open-source", "year": 2025}]), j)
        other = self.fit(talent(awards=[{"name": "Z", "kind": "patent", "year": 2025}]), j)
        self.assertGreater(one, base)
        self.assertGreater(two, one)
        self.assertLessEqual(two - base, self.f1.AWARD_BONUS_POINTS + 0.11)
        self.assertEqual(other, base)

    def test_remote_fits_everyone(self):
        for city in ("Sydney", "Melbourne", "Perth", "Hobart", "", "Nowhere"):
            t = talent(preferred_location=city, locations=[city] if city else [], work_modes=["Onsite"])
            r = self.f1.evaluate_job_fit(t, job(work_mode="Remote", city="Remote", location="Remote (Australia)"))
            self.assertEqual(r["parts"]["location"], 100.0, city)

    def test_the_location_part_falls_with_distance(self):
        t = talent(preferred_location="Sydney", locations=["Sydney"], work_modes=["Onsite"])
        parts = [self.f1.evaluate_job_fit(t, job(city=c, location=c, work_mode="Onsite"))["parts"]["location"]
                 for c in ("Sydney", "Canberra", "Melbourne", "Adelaide", "Perth")]
        self.assertEqual(parts, sorted(parts, reverse=True))
        self.assertEqual(parts[0], 100.0)
        self.assertLess(parts[-1], parts[0] - 40)
        hybrid = self.f1.evaluate_job_fit(t, job(city="Melbourne", location="Melbourne", work_mode="Hybrid"))["parts"]["location"]
        self.assertGreater(hybrid * 1.0, parts[2] * 0.9)   # a hybrid job is not harder to reach than an onsite one far away

    def test_the_result_is_deterministic_and_does_not_depend_on_the_order_of_skills(self):
        t, j = talent(), job()
        a, b = self.f1.evaluate_job_fit(t, j), self.f1.evaluate_job_fit(json.loads(json.dumps(t)), json.loads(json.dumps(j)))
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        shuffled = dict(t, skills=list(reversed(t["skills"])))
        self.assertEqual(self.fit(shuffled, dict(j, required_skills=list(reversed(j["required_skills"])))), a["fit"])

    def test_the_skill_breakdown_has_one_item_for_each_required_skill(self):
        res = self.f1.evaluate_job_fit(talent(), job())
        self.assertEqual([i["name"] for i in res["skill_breakdown"]], ["SQL", "Python", "Apache Spark"])
        for item in res["skill_breakdown"]:
            for key in ("name", "need_level", "have_level", "must", "credit", "weight", "status", "group"):
                self.assertIn(key, item)
            self.assertIn(item["status"], ("meets", "below", "related", "missing"))

    def test_the_skill_match_keeps_the_old_keys_and_takes_an_anzsco_code(self):
        res = self.f1.evaluate_skill_match(talent(), "262111")
        for key in ("candidate_id", "target_anzsco_code", "target_anzsco_title", "sub_metrics", "competency_breakdown", "base_composite_score",
                    "final_match_score", "overall_score", "match_tier", "match_tier_code", "is_direct_ready"):
            self.assertIn(key, res)
        for key in ("s_tree_taxonomy", "s_direct_competency", "s_trans_methodology", "phi_experience_multiplier"):
            self.assertIn(key, res["sub_metrics"])
        self.assertEqual(res["final_match_score"], res["overall_score"])
        self.assertEqual(res["target_anzsco_code"], "262111")

    def test_the_occupation_distance_is_not_a_five_step_scale(self):
        t = talent(target_roles=[], current_title="Data Engineer")
        vals = set()
        for title, code in (("Data Engineer", "262111"), ("Data Analyst", "224114"), ("Software Engineer", "261313"), ("Machine Learning Engineer", "261399"),
                            ("Web Developer", "261212"), ("DevOps Engineer", "261316"), ("ICT Business Analyst", "261111")):
            vals.add(self.f1.evaluate_skill_match(t, job(title=title, anzsco_code=code, category=None))["sub_metrics"]["s_tree_taxonomy"])
        self.assertGreaterEqual(len(vals), 6)
        # an unknown code does not give one fixed value: the title and the domain still count
        a = self.f1.evaluate_skill_match(t, job(title="Data Engineer", anzsco_code="999999"))["sub_metrics"]["s_tree_taxonomy"]
        b = self.f1.evaluate_skill_match(t, job(title="Chef", anzsco_code="999999", category="Hospitality", specialisation=None))["sub_metrics"]["s_tree_taxonomy"]
        self.assertGreater(a, b)


# =====================================================================
# Formula 2
# =====================================================================
class Formula2Tests(EngineTestCase):
    def test_gap_items_and_strength_items(self):
        t = talent(level="Mid", years_experience=3, skills=[{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}])
        j = job(level="Senior", min_years=5, max_years=9,
                required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True}, {"name": "Docker", "level": 3, "must": True}],
                certifications_required=[next(c for c in self.tax.certs if "Databricks" in c)])
        res = self.f2.evaluate_skill_gaps(t, j)
        kinds = {g["kind"] for g in res["gaps"]}
        self.assertEqual(kinds, {"missing", "below_level", "experience", "level", "certification"})
        for g in res["gaps"]:
            for key in ("kind", "item", "have_level", "need_level", "months", "must"):
                self.assertIn(key, g)
            self.assertGreater(g["months"], 0.0)
        names = {s["item"] for s in res["strengths"]}
        self.assertIn("SQL", names)
        self.assertNotIn("Docker", names)
        self.assertEqual(res["total_gaps_count"], len(res["gaps"]))
        for key in ("classified_gaps", "gap_severity_index", "job_readiness_score", "estimated_bridge_months", "estimated_closing_months",
                    "has_statutory_blocker", "readiness_tier", "readiness_tier_code", "skill_gap_pct"):
            self.assertIn(key, res)
        for g in res["classified_gaps"]:      # the keys of the old gap item
            for key in ("gap_name", "category_code", "category_name", "weight", "duration_months", "is_statutory_blocker", "severity_points"):
                self.assertIn(key, g)

    def test_months_come_from_months_to_learn_the_level_difference_and_prep_months(self):
        tax = self.tax
        entry = tax.skills["Docker"]
        t = talent(skills=[{"name": "SQL", "level": 4}], years_experience=0, level="Mid", highest_education="")
        # a missing skill at level 3: months = monthsToLearn x learner factor
        res = self.f2.evaluate_skill_gaps(t, job(required_skills=[{"name": "Docker", "level": 3, "must": True}], min_years=None, max_years=None, level="Mid"))
        gap = next(g for g in res["gaps"] if g["item"] == "Docker")
        learner = self.f2.learner_factor(0.0, None)
        related_held = [x for x in tax.related.get("Docker", []) if x in {s["name"] for s in t["skills"]}]
        self.assertFalse(related_held)
        self.assertAlmostEqual(gap["months"], round(entry["monthsToLearn"] * learner, 1), places=1)
        # a higher need level needs more months
        more = self.f2.evaluate_skill_gaps(t, job(required_skills=[{"name": "Docker", "level": 5, "must": True}], min_years=None, max_years=None))
        self.assertGreater(next(g for g in more["gaps"] if g["item"] == "Docker")["months"], gap["months"])
        # a skill that is held at a level below the need takes less time than a missing skill
        part = self.f2.evaluate_skill_gaps(with_skill(t, "Docker", 2), job(required_skills=[{"name": "Docker", "level": 3, "must": True}], min_years=None, max_years=None))
        self.assertLess(next(g for g in part["gaps"] if g["item"] == "Docker")["months"], gap["months"])
        # a larger level difference between the talent and the job takes more months
        g1 = next(g for g in self.f2.evaluate_skill_gaps(talent(level="Mid"), job(level="Senior"))["gaps"] if g["kind"] == "level")
        g2 = next(g for g in self.f2.evaluate_skill_gaps(talent(level="Mid"), job(level="Principal"))["gaps"] if g["kind"] == "level")
        self.assertGreater(g2["months"], g1["months"])
        # a certification takes about prepMonths
        cert = next(c for c in tax.certs if "Databricks" in c)
        res = self.f2.evaluate_skill_gaps(talent(), job(certifications_required=[cert]))
        cg = next(g for g in res["gaps"] if g["kind"] == "certification")
        self.assertTrue(0.3 * tax.certs[cert]["prepMonths"] <= cg["months"] <= tax.certs[cert]["prepMonths"] + 0.05)
        self.assertTrue(cg["must"])
        self.assertFalse(res["has_statutory_blocker"], "a missing certification is not a legal block")

    def test_the_parallel_learning_rule(self):
        f2 = self.f2
        self.assertAlmostEqual(f2.parallel_months([4.0, 2.0, 1.0]), 4.0 + 0.18 * 3.0, places=9)
        self.assertEqual(f2.parallel_months([]), 0.0)
        self.assertEqual(f2.parallel_months([3.0]), 3.0)
        t = talent(skills=[{"name": "SQL", "level": 4}], years_experience=1, level="Junior")
        j = job(level="Senior", min_years=5, max_years=9, required_skills=[{"name": "Docker", "level": 4, "must": True}, {"name": "Kubernetes", "level": 3, "must": True},
                                                                         {"name": "Terraform", "level": 3, "must": True}])
        res = f2.evaluate_skill_gaps(t, j)
        months = sorted((g["months"] for g in res["gaps"]), reverse=True)
        self.assertAlmostEqual(res["estimated_bridge_months"], months[0] + 0.18 * sum(months[1:]), delta=0.2)
        self.assertLess(res["estimated_bridge_months"], sum(months))
        self.assertEqual(res["estimated_bridge_months"], res["estimated_closing_months"])

    def test_readiness_is_bounded_falls_with_more_gaps_and_has_no_projection(self):
        t = talent(skills=[{"name": "SQL", "level": 4}])
        values = []
        names = ["SQL", "Docker", "Kubernetes", "Terraform", "Apache Kafka", "Go"]
        for n in range(1, len(names) + 1):
            j = job(required_skills=[{"name": s, "level": 4, "must": True} for s in names[:n]], min_years=None, max_years=None)
            r = self.f2.evaluate_skill_gaps(t, j)
            self.assertBounded(r["job_readiness_score"])
            self.assertBounded(r["gap_severity_index"])
            self.assertAlmostEqual(r["job_readiness_score"] + r["gap_severity_index"], 100.0, delta=0.11)
            values.append(r["job_readiness_score"])
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertGreater(len(set(values)), 4)
        self.assertNotIn("projection", r)
        self.assertNotIn("projection", self.f2.evaluate_path(t, job()))

    def test_no_job_gives_a_legal_block_for_a_health_or_finance_word(self):
        for words in ("AHPRA registered nurse", "CPA accountant", "Engineers Australia chartered engineer"):
            r = self.f2.evaluate_skill_gaps(talent(), job(title=words, requirements=[words], required_skills=[]))
            self.assertFalse(r["has_statutory_blocker"])
            self.assertTrue(all(not g["is_statutory_blocker"] for g in r["classified_gaps"]))

    def test_the_path_object(self):
        cert = next(c for c in self.tax.certs if "Databricks" in c)
        t = talent(level="Mid", years_experience=3, skills=[{"name": "SQL", "level": 5}, {"name": "Python", "level": 3}, {"name": "Communication", "level": 3}])
        j = job(level="Senior", min_years=5, max_years=9, certifications_required=[cert],
                required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True}, {"name": "Docker", "level": 3, "must": False},
                                 {"name": "Communication", "level": 3, "must": False}])
        path = self.f2.evaluate_path(t, j)
        self.assertEqual(set(path), {"axes", "fit", "gaps", "summary"})
        self.assertEqual(set(path["summary"]), {"fitCount", "gapCount", "monthsToClose", "readinessTier"})
        self.assertEqual(path["summary"]["fitCount"], len(path["fit"]))
        self.assertEqual(path["summary"]["gapCount"], len(path["gaps"]))
        keys = [a["key"] for a in path["axes"]]
        self.assertIn("languages", keys)
        self.assertIn("experience", keys)
        self.assertIn("level", keys)
        self.assertIn("certifications", keys)
        self.assertEqual(len(keys), len(set(keys)))
        for a in path["axes"]:
            self.assertEqual(set(a), {"key", "label", "group", "required", "have", "status"})
            self.assertTrue(0 <= a["required"] <= 100 and 0 <= a["have"] <= 100)
            expect = "above" if a["have"] >= a["required"] + 15 else ("fit" if a["have"] >= a["required"] else "gap")
            self.assertEqual(a["status"], expect, a)
        langs = next(a for a in path["axes"] if a["key"] == "languages")
        # SQL and Python are languages: weights are equal (both must, same need), so required = mean of 80 and 80, have = mean of 100 and 60
        self.assertEqual(langs["required"], 80.0)
        self.assertEqual(langs["have"], 80.0)
        self.assertEqual(langs["status"], "fit")
        exp_axis = next(a for a in path["axes"] if a["key"] == "experience")
        self.assertEqual((exp_axis["required"], exp_axis["have"], exp_axis["status"]), (50.0, 30.0, "gap"))
        lvl_axis = next(a for a in path["axes"] if a["key"] == "level")
        self.assertEqual((lvl_axis["required"], lvl_axis["have"]), (60.0, 40.0))
        for item in path["fit"]:
            self.assertEqual(set(item), {"kind", "label", "have", "need", "note"})
            self.assertIn(item["kind"], ("skill", "experience", "level", "certification", "award"))
        for item in path["gaps"]:
            self.assertEqual(set(item), {"kind", "label", "have", "need", "months", "must", "note"})
            self.assertIn(item["kind"], ("missing", "below_level", "experience", "level", "certification"))
            self.assertGreater(item["months"], 0)
        labels = {i["label"] for i in path["fit"]}
        self.assertIn("SQL", labels)
        self.assertIn("Communication", labels)
        gap_labels = {(i["kind"], i["label"]) for i in path["gaps"]}
        self.assertIn(("below_level", "Python"), gap_labels)
        self.assertIn(("missing", "Docker"), gap_labels)
        self.assertIn(("experience", "Experience"), gap_labels)
        self.assertIn(("level", "Level"), gap_labels)
        self.assertIn(("certification", cert), gap_labels)
        sql = next(i for i in path["fit"] if i["label"] == "SQL")
        self.assertEqual((sql["have"], sql["need"]), ("Expert", "Advanced"))
        json.dumps(path)     # it must be plain JSON

    def test_the_path_has_no_certification_axis_when_the_job_lists_none(self):
        path = self.f2.evaluate_path(talent(), job())
        self.assertNotIn("certifications", [a["key"] for a in path["axes"]])

    def test_the_path_months_equal_the_readiness_months(self):
        t = talent(skills=[{"name": "SQL", "level": 3}], years_experience=1, level="Junior")
        j = job(level="Senior", min_years=5, max_years=9)
        self.assertEqual(self.f2.evaluate_path(t, j)["summary"]["monthsToClose"], self.f2.evaluate_skill_gaps(t, j)["estimated_bridge_months"])

    def test_old_shapes_still_work(self):
        old_c = {"skills": ["python", "sql"], "years_experience": 3, "cv_raw_text": "python sql", "highest_education": "Bachelor's degree"}
        old_j = {"title": "Software Engineer", "category": "Technology & Data", "anzsco_code": "261313", "requirements": ["Python", "Docker", "Kubernetes"]}
        res = self.f2.evaluate_skill_gaps(old_c, old_j, explicit_missing_skills=["Terraform"])
        self.assertBounded(res["job_readiness_score"])
        self.assertTrue(any(g["item"] == "Terraform" for g in res["gaps"]))
        self.assertTrue(any(g["item"] == "Docker" for g in res["gaps"]))


# =====================================================================
# Formula 3
# =====================================================================
class Formula3Tests(EngineTestCase):
    def test_the_index_is_symmetric_bounded_and_100_for_the_same_job(self):
        a = job(id="a")
        b = job(id="b", title="Data Analyst", anzsco_code="224114", level="Senior", city="Melbourne", location="Melbourne", work_mode="Remote",
                required_skills=[{"name": "SQL", "level": 3, "must": True}, {"name": "Tableau", "level": 4, "must": True}], salary_min=100000, salary_max=120000)
        c = job(id="c", title="Machine Learning Engineer", anzsco_code="261399", category="AI & Machine Learning", specialisation="Machine learning engineering",
                required_skills=[{"name": "PyTorch", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True}], salary_min=150000, salary_max=180000)
        for x, y in ((a, b), (a, c), (b, c)):
            ab, ba = self.f3.compare_two_jobs(x, y), self.f3.compare_two_jobs(y, x)
            self.assertEqual(ab["job_proximity_index"], ba["job_proximity_index"])
            self.assertBounded(ab["job_proximity_index"])
            for key, v in ab["sub_metrics"].items():
                if v is not None:
                    self.assertBounded(v, key)
            self.assertEqual(ab["sub_metrics"], ba["sub_metrics"])
        self.assertEqual(self.f3.compare_two_jobs(a, dict(a, id="a2"))["job_proximity_index"], 100.0)
        self.assertGreater(self.f3.compare_two_jobs(a, b)["job_proximity_index"], self.f3.compare_two_jobs(a, c)["job_proximity_index"] - 100)

    def test_level_work_mode_and_skill_levels_count(self):
        base = job(id="a")
        same = self.f3.compare_two_jobs(base, job(id="b"))["job_proximity_index"]
        higher = self.f3.compare_two_jobs(base, job(id="b", level="Principal"))["job_proximity_index"]
        self.assertGreater(same, higher)
        lvl = [self.f3.compare_two_jobs(base, job(id="b", level=l))["job_proximity_index"] for l in ("Mid", "Senior", "Lead", "Principal")]
        self.assertEqual(lvl, sorted(lvl, reverse=True))
        modes = {m: self.f3.compare_two_jobs(job(id="a", work_mode="Remote", city="Remote", location="Remote"),
                                              job(id="b", work_mode=m, city="Sydney" if m != "Remote" else "Remote", location="Sydney"))["sub_metrics"]["s_geo_alignment"]
                 for m in ("Remote", "Hybrid", "Onsite")}
        self.assertGreater(modes["Remote"], modes["Hybrid"])
        self.assertGreater(modes["Hybrid"], modes["Onsite"])
        # the same skills at a different required level overlap less than the same skills at the same level
        low = job(id="b", required_skills=[{"name": "SQL", "level": 2, "must": True}, {"name": "Python", "level": 2, "must": True}, {"name": "Apache Spark", "level": 1, "must": False}])
        s_same = self.f3.compare_two_jobs(base, job(id="b"))["sub_metrics"]["s_req_jaccard"]
        s_low = self.f3.compare_two_jobs(base, low)["sub_metrics"]["s_req_jaccard"]
        self.assertGreater(s_same, s_low)
        self.assertGreater(s_low, 0.0)

    def test_annual_salary_is_one_function_for_year_day_and_hour(self):
        f3, C = self.f3, self.C
        self.assertEqual(f3.annual_salary(100000, 120000, "year"), (100000.0, 120000.0))
        self.assertEqual(f3.annual_salary(700, 800, "day"), (154000.0, 176000.0))        # 220 working days
        self.assertEqual(f3.annual_salary(60, 80, "hour"), (117000.0, 156000.0))         # 1950 hours
        self.assertEqual(f3.annual_salary(700, 800, "Day"), f3.annual_salary(700, 800, "daily"))
        self.assertEqual(f3.annual_salary(None, None, "year"), (0.0, 0.0))
        self.assertIs(f3.annual_salary, C.annual_salary)
        # the unit comes with the job: the job keys, or a salary object
        a = {"salary_min": 700, "salary_max": 800, "salary_unit": "day"}
        b = {"salary": {"min": 700, "max": 800, "unit": "day"}}
        self.assertEqual(f3.get_job_salary_midpoint(a), 165000.0)
        self.assertEqual(f3.get_job_salary_midpoint(b), 165000.0)
        # Formula 5 uses the same yearly pay: a day rate of 700 to 800 is a good Senior pay, not a very low one
        senior = job(level="Senior", salary_min=700, salary_max=800, salary_unit="day", category="Data")
        low = job(level="Senior", salary_min=700, salary_max=800, salary_unit="year", category="Data")
        t = talent(level="Senior", years_experience=7)
        up_day = self.f5.compute_feed_job_score(t, senior)["sub_metrics"]["s_wage_upside"]
        up_low = self.f5.compute_feed_job_score(t, low)["sub_metrics"]["s_wage_upside"]
        self.assertGreater(up_day, 50.0)
        self.assertLess(up_low, 5.0)

    def test_salary_helpers(self):
        f3 = self.f3
        self.assertEqual(f3.get_job_salary_midpoint({"salary_min": 100000, "salary_max": 120000}), 110000.0)
        self.assertEqual(f3.get_job_salary_midpoint({"salary_min": 60, "salary_max": 80}), 70 * 1950.0)       # an hourly rate
        self.assertEqual(f3.get_job_salary_midpoint({"salary_min": 700, "salary_max": 800}), 750 * 220.0)     # a day rate
        self.assertEqual(f3.get_job_salary_midpoint({"salary_min": 100, "salary_max": 200, "salary_unit": "day"}), 150 * 220.0)
        self.assertGreater(f3.get_job_salary_midpoint({"category": "Data", "level": "Senior"}), f3.get_job_salary_midpoint({"category": "Data", "level": "Junior"}))
        self.assertEqual(f3.calculate_salary_parity(100000, 100000), 100.0)
        self.assertEqual(f3.calculate_salary_parity(100000, 150000), f3.calculate_salary_parity(150000, 100000))

    def test_the_matrix_and_the_old_weights(self):
        jobs = [job(id="a"), job(id="b", level="Senior"), job(id="c", title="Data Analyst", anzsco_code="224114")]
        m = self.f3.compare_multiple_jobs(jobs)
        self.assertEqual(m["total_jobs_compared"], 3)
        mat = m["pairwise_proximity_matrix"]
        for i in range(3):
            self.assertEqual(mat[i][i], 100.0)
            for k in range(3):
                self.assertEqual(mat[i][k], mat[k][i])
        old = self.f3.compare_two_jobs(jobs[0], jobs[1], weights=(0.30, 0.35, 0.15, 0.10, 0.10))
        self.assertBounded(old["job_proximity_index"])

    def test_old_shape_jobs(self):
        a = {"id": "a", "title": "Software Engineer", "category": "Technology & Data", "location": "Sydney", "anzsco_code": "261313", "requirements": ["Python"],
             "description": "write python services", "salary_min": 130000, "salary_max": 150000}
        b = {"id": "b", "title": "Software Developer", "category": "Technology & Data", "location": "Sydney", "anzsco_code": "261312", "requirements": ["Python"],
             "description": "python services and tests", "salary_min": 125000, "salary_max": 150000}
        c = {"id": "c", "title": "Chef", "category": "Hospitality", "location": "Perth", "anzsco_code": "351311", "requirements": ["Cooking"],
             "description": "cook meals", "salary_min": 70000, "salary_max": 80000}
        ab, ba, ac = (self.f3.compare_two_jobs(a, b), self.f3.compare_two_jobs(b, a), self.f3.compare_two_jobs(a, c))
        self.assertEqual(ab["job_proximity_index"], ba["job_proximity_index"])
        self.assertGreater(ab["job_proximity_index"], ac["job_proximity_index"])
        for key in ("job_a", "job_b", "job_proximity_index", "sub_metrics", "differentials", "operational_tier", "career_mobility_advice"):
            self.assertIn(key, ab)
        for key in ("salary_delta_aud", "salary_delta_label", "shared_competency_sample", "unique_to_b_sample"):
            self.assertIn(key, ab["differentials"])


# =====================================================================
# Formula 4
# =====================================================================
class Formula4Tests(EngineTestCase):
    def merit(self, t, **kw):
        return self.f4.calculate_candidate_merit_score(t, **kw)

    def test_the_dimensions_are_bounded_and_the_old_keys_stay(self):
        res = self.merit(talent())
        for key in ("candidate_id", "relative_merit_score", "overall_score", "sub_metrics", "verified_years_exp", "has_statutory_gap"):
            self.assertIn(key, res)
        for key in ("skill_depth", "experience_maturity", "evidence_rigor", "transferable_agility", "gap_penalty_deduction", "education_bonus"):
            self.assertIn(key, res["sub_metrics"])
        for key, v in res["sub_metrics"].items():
            if v is not None and key != "education_bonus":
                self.assertBounded(v, key)
        self.assertBounded(res["relative_merit_score"])
        self.assertFalse(res["has_statutory_gap"])

    def test_merit_rises_with_level_years_skill_levels_certifications_and_awards(self):
        def parts(**kw):
            return self.merit(talent(**kw))["sub_metrics"]
        lv = [parts(level=l)["level_standing"] for l in ("Intern", "Junior", "Mid", "Senior", "Lead", "Principal")]
        self.assertEqual(lv, sorted(lv))
        self.assertEqual(len(set(lv)), 6)
        yrs = [parts(years_experience=y)["experience_maturity"] for y in (0, 1, 2, 4, 8, 16)]
        self.assertEqual(yrs, sorted(yrs))
        self.assertEqual(len(set(yrs)), 6)
        depth = [parts(skills=[{"name": "SQL", "level": l}, {"name": "Python", "level": l}])["skill_depth"] for l in (1, 2, 3, 4, 5)]
        self.assertEqual(depth, sorted(depth))
        self.assertEqual(len(set(depth)), 5)
        more = parts(skills=[{"name": n, "level": 3} for n in ("SQL", "Python", "Docker", "Git")])["skill_depth"]
        self.assertGreater(more, parts(skills=[{"name": "SQL", "level": 3}, {"name": "Python", "level": 3}])["skill_depth"])
        cert = next(iter(self.tax.certs))
        e0, e1 = parts()["evidence_rigor"], parts(certifications=[{"name": cert, "year": 2025}])["evidence_rigor"]
        e2 = parts(certifications=[{"name": cert, "year": 2025}], awards=[{"name": "Demo", "kind": "hackathon", "year": 2025}])["evidence_rigor"]
        self.assertLess(e0, e1)
        self.assertLess(e1, e2)
        self.assertLess(parts()["certification_strength"], parts(certifications=[{"name": cert, "year": 2025}])["certification_strength"])
        self.assertLess(parts()["award_strength"], parts(awards=[{"name": "Demo", "kind": "hackathon", "year": 2025}])["award_strength"])

    def test_evidence_rigor_does_not_use_the_cv_text(self):
        short = self.merit(talent(cv_raw_text="x"))["sub_metrics"]["evidence_rigor"]
        long_text = self.merit(talent(cv_raw_text=("Improved latency by 40% for 3 million users. " * 300), rawResume="Led a team of 12 and saved $2m. " * 200))["sub_metrics"]["evidence_rigor"]
        self.assertEqual(short, long_text)
        self.assertEqual(self.merit(talent())["relative_merit_score"], self.merit(talent(cv_raw_text="a long text " * 500))["relative_merit_score"])

    def test_the_depth_for_a_job_uses_the_skills_that_the_job_asks_for(self):
        t = talent()
        j = job(required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Docker", "level": 3, "must": True}])
        d_job = self.merit(t, job=j)
        self.assertEqual(d_job["depth_basis"], "job")
        self.assertEqual(self.merit(t)["depth_basis"], "profile")
        self.assertLess(d_job["sub_metrics"]["skill_depth"], self.merit(with_skill(t, "Docker", 4), job=j)["sub_metrics"]["skill_depth"])

    def test_head_to_head_and_cohort(self):
        a = talent(id="a", alias="A", level="Senior", years_experience=9, skills=[{"name": n, "level": 5} for n in ("SQL", "Python", "Docker", "Apache Spark")])
        b = talent(id="b", alias="B", level="Junior", years_experience=1, skills=[{"name": "SQL", "level": 2}])
        ab, ba = self.f4.compare_two_candidates(a, b), self.f4.compare_two_candidates(b, a)
        self.assertAlmostEqual(ab["score_delta"], -ba["score_delta"], places=1)
        self.assertGreater(ab["score_delta"], 8.0)
        self.assertEqual(ab["recommended_candidate"], "A")
        coh = self.f4.rank_candidate_cohort([b, a])
        self.assertEqual([x["candidate_id"] for x in coh["ranked_shortlist"]], ["a", "b"])
        self.assertEqual(coh["ranked_shortlist"][0]["cohort_rank"], 1)

    def test_old_shape_candidate(self):
        res = self.merit({"id": "x", "skills": ["python", "sql", {"name": "Excel", "type": "Transferable"}], "years_of_experience": 3, "highest_education": "Master's degree",
                          "rawResume": "Reduced cost by 20%."})
        self.assertBounded(res["relative_merit_score"])
        self.assertEqual(res["verified_years_exp"], 3.0)


# =====================================================================
# Formula 5
# =====================================================================
class Formula5Tests(EngineTestCase):
    def frs(self, t, j, **kw):
        return self.f5.compute_feed_job_score(t, j, **kw)

    def test_the_feed_score_and_its_parts_are_bounded(self):
        res = self.frs(talent(), job())
        for key in ("job_id", "job_title", "employer_name", "job_sector", "feed_ranking_score", "overall_score", "sub_metrics"):
            self.assertIn(key, res)
        for key in ("s_cap_capability", "s_wage_upside", "s_loc_location", "s_rec_recency", "employer_diversity_penalty"):
            self.assertIn(key, res["sub_metrics"])
        for key in ("s_cap_capability", "s_wage_upside", "s_loc_location", "s_rec_recency"):
            self.assertBounded(res["sub_metrics"][key], key)
        self.assertBounded(res["feed_ranking_score"])

    def test_capability_is_level_aware(self):
        j = job(level="Senior", min_years=5, max_years=9)
        caps = [self.frs(talent(level=l, years_experience=y), j)["sub_metrics"]["s_cap_capability"]
                for l, y in (("Junior", 1), ("Mid", 3), ("Senior", 6))]
        self.assertEqual(caps, sorted(caps))
        self.assertLess(caps[0], caps[2] - 5)
        # more skill level gives more capability
        c1 = self.frs(with_skill(talent(), "Python", 2), job())["sub_metrics"]["s_cap_capability"]
        c2 = self.frs(with_skill(talent(), "Python", 4), job())["sub_metrics"]["s_cap_capability"]
        self.assertLess(c1, c2)

    def test_wage_upside_uses_a_benchmark_for_each_domain_and_level(self):
        t = talent(level="Mid")
        same_pay = {"salary_min": 140000, "salary_max": 140000}
        junior = self.frs(t, job(level="Junior", **same_pay))["sub_metrics"]["s_wage_upside"]
        mid = self.frs(t, job(level="Mid", **same_pay))["sub_metrics"]["s_wage_upside"]
        principal = self.frs(t, job(level="Principal", **same_pay))["sub_metrics"]["s_wage_upside"]
        self.assertGreater(junior, mid)
        self.assertGreater(mid, principal)
        data = self.frs(talent(domain="Data"), job(category="Data", **same_pay))["sub_metrics"]["s_wage_upside"]
        ai = self.frs(talent(domain="AI & Machine Learning"), job(category="AI & Machine Learning", **same_pay))["sub_metrics"]["s_wage_upside"]
        self.assertGreater(data, ai)        # the AI benchmark is higher
        pays = [self.frs(t, job(salary_min=p, salary_max=p))["sub_metrics"]["s_wage_upside"] for p in range(60000, 260001, 20000)]
        self.assertEqual(pays, sorted(pays))
        self.assertEqual(len(set(pays)), len(pays))
        self.assertTrue(0.0 < pays[0] and pays[-1] < 100.0, "the pay score has no flat ends in this range")

    def test_location_uses_city_and_work_mode_and_remote_fits_everyone(self):
        t = talent(preferred_location="Perth", locations=["Perth"], work_modes=["Onsite"])
        remote = self.frs(t, job(work_mode="Remote", city="Remote", location="Remote"))["sub_metrics"]["s_loc_location"]
        onsite = self.frs(t, job(work_mode="Onsite", city="Sydney", location="Sydney"))["sub_metrics"]["s_loc_location"]
        same = self.frs(t, job(work_mode="Onsite", city="Perth", location="Perth"))["sub_metrics"]["s_loc_location"]
        self.assertEqual(remote, 100.0)
        self.assertEqual(same, 100.0)
        self.assertLess(onsite, 50.0)

    def test_recency_falls_smoothly_with_the_age_of_the_posting(self):
        values = [self.frs(talent(), job(days_old=d))["sub_metrics"]["s_rec_recency"] for d in (0, 1, 2, 5, 10, 20, 40)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(len(set(values)), len(values))

    def test_the_diversity_penalty_for_one_employer(self):
        jobs = [job(id=f"j{i}", company="Acme", salary_min=120000 + i * 1000, salary_max=130000 + i * 1000) for i in range(5)]
        res = self.f5.rank_job_feed_for_candidate(talent(), jobs, 5)["top_feed"]
        scores = [r["feed_ranking_score"] for r in res]
        self.assertEqual(scores, sorted(scores, reverse=True))
        pens = sorted(r["sub_metrics"]["employer_diversity_penalty"] for r in res)
        self.assertEqual(pens, [0.0, 0.15, 0.30, 0.40, 0.40])
        self.assertEqual([r["feed_position"] for r in res], [1, 2, 3, 4, 5])
        other = [job(id=f"k{i}", company=f"Co{i}") for i in range(3)]
        res2 = self.f5.rank_job_feed_for_candidate(talent(), other, 3)["top_feed"]
        self.assertTrue(all(r["sub_metrics"]["employer_diversity_penalty"] == 0.0 for r in res2))

    def test_the_feed_is_deterministic_and_the_ties_are_stable(self):
        jobs = [job(id=f"j{i}") for i in range(4)]
        a = self.f5.rank_job_feed_for_candidate(talent(), jobs, 4)
        b = self.f5.rank_job_feed_for_candidate(talent(), list(reversed(jobs)), 4)
        self.assertEqual([r["job_id"] for r in a["top_feed"]], [r["job_id"] for r in b["top_feed"]])

    def test_old_shape_input(self):
        cand = {"skills": [{"skill_name": "SQL"}], "target_anzsco_code": "261313", "preferred_location": "sydney", "cv_raw_text": "sql"}
        jobs = [{"id": f"j{i}", "title": "Data Engineer", "company": "Acme", "category": "Technology & Data", "anzsco_code": "261313", "location": "Sydney",
                 "salary_min": 100000, "salary_max": 120000, "requirements": ["SQL"], "days_old": 2.0} for i in range(3)]
        res = self.f5.rank_job_feed_for_candidate(cand, jobs, 3)["top_feed"]
        scores = [r["feed_ranking_score"] for r in res]
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[1], scores[2])
        self.assertEqual(res[0]["sub_metrics"]["employer_diversity_penalty"], 0.0)


# =====================================================================
# Formula 6
# =====================================================================
class Formula6Tests(EngineTestCase):
    def tss(self, t, j, **kw):
        return self.f6.compute_talent_search_score(t, j, **kw)

    def test_keys_and_bounds(self):
        res = self.tss(talent(), job())
        for key in ("candidate_id", "target_role", "talent_search_score", "overall_score", "sub_metrics", "target_years_demanded", "candidate_years_held"):
            self.assertIn(key, res)
        for key in ("s_req_fit", "s_sen_parity", "s_evid_rigor", "s_reg_readiness", "s_audit_contract"):
            self.assertBounded(res["sub_metrics"][key], key)
        self.assertBounded(res["talent_search_score"])
        self.assertNotIn("candidate_origin", res)

    def test_a_better_profile_has_a_higher_score(self):
        j = job(level="Senior", min_years=5, max_years=9)
        weak = self.tss(talent(level="Junior", years_experience=1, skills=[{"name": "SQL", "level": 2}]), j)["talent_search_score"]
        good = self.tss(talent(level="Mid", years_experience=4), j)["talent_search_score"]
        best = self.tss(talent(level="Senior", years_experience=7, skills=[{"name": "SQL", "level": 5}, {"name": "Python", "level": 5}, {"name": "Apache Spark", "level": 4}]), j)["talent_search_score"]
        self.assertLess(weak, good)
        self.assertLess(good, best)

    def test_seniority_comes_from_level_and_years_not_from_title_words(self):
        t = talent(level="Mid", years_experience=3)
        a = self.tss(t, job(title="Senior Data Engineer", level="Mid", min_years=2, max_years=5))
        b = self.tss(t, job(title="Data Engineer", level="Mid", min_years=2, max_years=5))
        self.assertEqual(a["sub_metrics"]["s_sen_parity"], b["sub_metrics"]["s_sen_parity"])
        lvl = [self.tss(talent(level="Mid", years_experience=4), job(level=l, min_years=None, max_years=None))["sub_metrics"]["s_sen_parity"]
               for l in ("Mid", "Senior", "Lead", "Principal")]
        self.assertEqual(lvl, sorted(lvl, reverse=True))
        yrs = [self.tss(talent(level="Senior", years_experience=y), job(level="Senior", min_years=5, max_years=9))["sub_metrics"]["s_sen_parity"] for y in (1, 2, 3, 4, 5)]
        self.assertEqual(yrs, sorted(yrs))
        self.assertEqual(len(set(yrs)), 5)

    def test_evidence_rigor_uses_levels_certifications_and_awards_and_not_the_text_length(self):
        j = job()
        base = self.tss(talent(), j)["sub_metrics"]["s_evid_rigor"]
        self.assertEqual(base, self.tss(talent(cv_raw_text="word " * 5000), j)["sub_metrics"]["s_evid_rigor"])
        self.assertEqual(base, self.tss(talent(rawResume="Led 12 people. Saved $2m. " * 300), j)["sub_metrics"]["s_evid_rigor"])
        higher = self.tss(talent(skills=[{"name": "SQL", "level": 5}, {"name": "Python", "level": 5}, {"name": "Apache Spark", "level": 5}]), j)["sub_metrics"]["s_evid_rigor"]
        self.assertGreater(higher, base)
        cert = next(c for c in self.tax.certs if "Databricks" in c)
        with_cert = self.tss(talent(certifications=[{"name": cert, "year": 2025}]), j)["sub_metrics"]["s_evid_rigor"]
        with_award = self.tss(talent(awards=[{"name": "Demo", "kind": "hackathon", "year": 2025}]), j)["sub_metrics"]["s_evid_rigor"]
        self.assertGreater(with_cert, base)
        self.assertGreater(with_award, base)

    def test_required_certification_readiness(self):
        cert = next(c for c in self.tax.certs if "Databricks" in c)
        j = job(certifications_required=[cert])
        no = self.tss(talent(), j)
        yes = self.tss(talent(certifications=[{"name": cert, "year": 2025}]), j)
        self.assertGreater(yes["sub_metrics"]["s_reg_readiness"], no["sub_metrics"]["s_reg_readiness"])
        self.assertEqual(yes["sub_metrics"]["s_reg_readiness"], 100.0)
        self.assertGreater(yes["talent_search_score"], no["talent_search_score"])
        # no legal block: a job that names AHPRA or CPA in its title gives the same readiness as any job without a certification
        base = self.tss(talent(), job())["sub_metrics"]["s_reg_readiness"]
        self.assertEqual(base, self.tss(talent(), job(title="AHPRA registered clinician CPA"))["sub_metrics"]["s_reg_readiness"])

    def test_it_reads_the_shared_profile_only(self):
        t = talent()
        noisy = dict(t, cv_raw_text="private text with python sql docker kubernetes terraform " * 50, evidence=["a private evidence line"], rawResume="python " * 100)
        self.assertEqual(json.dumps(self.tss(t, job()), sort_keys=True), json.dumps(self.tss(noisy, job()), sort_keys=True))

    def test_the_pool_is_ranked_and_the_order_value_is_returned(self):
        j = job(level="Senior", min_years=5, max_years=9)
        pool = [talent(id="a", skills=[{"name": "SQL", "level": 2}]), talent(id="b"), talent(id="c", level="Senior", years_experience=8,
                skills=[{"name": "SQL", "level": 5}, {"name": "Python", "level": 5}, {"name": "Apache Spark", "level": 5}])]
        res = self.f6.rank_candidates_for_job_requisition(j, pool, top_limit=3)
        self.assertEqual([r["candidate_id"] for r in res["ranked_shortlist"]][0], "c")
        self.assertEqual([r["candidate_id"] for r in res["ranked_shortlist"]][-1], "a")
        for r in res["ranked_shortlist"]:
            self.assertAlmostEqual(r["order_value"], 0.6 * r["skill_coverage"] + 0.4 * r["tss_exact"], delta=0.06)

    def test_old_shape_input(self):
        base = {"skills": [{"skill_name": "Excel", "skill_type": "Direct"}], "anzsco_code": "511112", "cv_raw_text": "excel scheduling", "highest_education": "Bachelor's degree"}
        j = {"title": "Operations Coordinator", "category": "Operations & Administration", "anzsco_code": "511112", "requirements": ["Excel", "Scheduling"], "min_years": 3}
        low = self.f6.compute_talent_search_score({**base, "years_experience": 1.0}, j)["talent_search_score"]
        high = self.f6.compute_talent_search_score({**base, "years_experience": 5.0}, j)["talent_search_score"]
        self.assertGreater(high, low)


# =====================================================================
# Privacy: no private field is read
# =====================================================================
PRIVATE_FIELDS = {"name": "Real Person", "full_name": "Real Person", "email": "real.person@example.test", "phone": "+61 400 000 000", "origin": "Vietnam",
                  "origin_country": "Vietnam", "country": "Vietnam", "nationality": "Vietnamese", "visa": "Subclass 482", "visa_status": "temporary", "gender": "female",
                  "age": 52, "date_of_birth": "1973-01-01", "birth_year": 1973, "photo": "http://example.test/p.png", "studyCountry": ["Vietnam"],
                  "religion": "x", "ethnicity": "y"}


class PrivacyTests(EngineTestCase):
    def test_private_fields_change_no_result(self):
        t, j = talent(), job()
        noisy = dict(t, **PRIVATE_FIELDS)
        noisy_job = dict(j, **{"country": "Vietnam", "email": "x@example.test"})
        pool = [t, talent(id="t2", level="Senior", years_experience=8)]
        noisy_pool = [dict(c, **PRIVATE_FIELDS) for c in pool]

        def dump(x):
            return json.dumps(x, sort_keys=True, default=str)
        self.assertEqual(dump(self.f1.evaluate_job_fit(t, j)), dump(self.f1.evaluate_job_fit(noisy, noisy_job)))
        self.assertEqual(dump(self.f1.evaluate_skill_match(t, j)), dump(self.f1.evaluate_skill_match(noisy, noisy_job)))
        self.assertEqual(dump(self.f2.evaluate_skill_gaps(t, j)), dump(self.f2.evaluate_skill_gaps(noisy, noisy_job)))
        self.assertEqual(dump(self.f2.evaluate_path(t, j)), dump(self.f2.evaluate_path(noisy, noisy_job)))
        self.assertEqual(dump(self.f4.calculate_candidate_merit_score(t)), dump(self.f4.calculate_candidate_merit_score(noisy)))
        self.assertEqual(dump(self.f5.rank_job_feed_for_candidate(t, [j], 1)), dump(self.f5.rank_job_feed_for_candidate(noisy, [noisy_job], 1)))
        self.assertEqual(dump(self.f6.rank_candidates_for_job_requisition(j, pool)), dump(self.f6.rank_candidates_for_job_requisition(noisy_job, noisy_pool)))

    def test_no_output_has_a_private_value(self):
        noisy = dict(talent(), **PRIVATE_FIELDS)
        outputs = [self.f1.evaluate_job_fit(noisy, job()), self.f2.evaluate_skill_gaps(noisy, job()), self.f4.calculate_candidate_merit_score(noisy),
                   self.f5.compute_feed_job_score(noisy, job()), self.f6.compute_talent_search_score(noisy, job())]
        text = json.dumps(outputs, default=str)
        for value in ("Real Person", "real.person", "Vietnam", "Vietnamese", "Subclass", "+61 400", "1973"):
            self.assertNotIn(value, text, value)

    def test_the_engine_code_does_not_read_a_private_key(self):
        tokens = ("full_name", "email", "phone", "origin", "origin_country", "nationality", "visa", "gender", "age", "dob", "birth", "photo", "country",
                  "studyCountry", "religion", "ethnicity", "date_of_birth")
        pattern = re.compile(r"""(\.get\(\s*|\[\s*)["'](%s)["']""" % "|".join(re.escape(t) for t in tokens))
        for name in list(_FILES.values()) + ["engine_common.py"]:
            source = (ENGINE_DIR / name).read_text(encoding="utf-8")
            hits = pattern.findall(source)
            self.assertEqual(hits, [], f"{name} reads a private key: {hits}")


# =====================================================================
# Words for the user: "Talent", never "job seeker", "candidate" or "applicant" in a text that a user reads
# =====================================================================
BANNED_WORDS = re.compile(r"job[ -]?seeker|candidate|applicant|recruiter", re.I)


def string_values(obj):
    """All text values (not the keys) of a result."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from string_values(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from string_values(v)


class UserTextTests(EngineTestCase):
    def test_no_result_text_says_job_seeker_candidate_or_applicant(self):
        cert = next(c for c in self.tax.certs if "Databricks" in c)
        t = talent(level="Mid", years_experience=3, certifications=[], awards=[{"name": "Demo", "kind": "hackathon", "year": 2025}],
                   skills=[{"name": "SQL", "level": 5}, {"name": "Python", "level": 3}, {"name": "Communication", "level": 4}])
        j = job(level="Senior", min_years=5, max_years=9, certifications_required=[cert], awards_preferred=["hackathon"],
                required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True},
                                {"name": "Apache Airflow", "level": 3, "must": True}, {"name": "Communication", "level": 3, "must": False}])
        outputs = [self.f1.evaluate_job_fit(t, j), self.f1.evaluate_skill_match(t, j), self.f2.evaluate_skill_gaps(t, j), self.f2.evaluate_path(t, j),
                   self.f4.calculate_candidate_merit_score(t), self.f4.compare_two_candidates(talent(id="a", alias="Alias A"), talent(id="b", alias="Alias B", level="Senior", years_experience=9)),
                   self.f5.compute_feed_job_score(t, j), self.f6.compute_talent_search_score(t, j)]
        # the three advice texts and the three tiers of Formula 3
        for other in (dict(j, id="same"), dict(j, id="near", level="Mid", min_years=2, max_years=5, city="Melbourne", location="Melbourne"),
                      job(id="far", title="Software Engineer", category="Software Engineering", specialisation="Backend", anzsco_code="261313", level="Principal",
                          city="Perth", location="Perth", work_mode="Onsite", required_skills=[{"name": "Go", "level": 5, "must": True}])):
            outputs.append(self.f3.compare_two_jobs(j, other))
        texts = [x for out in outputs for x in string_values(out)]
        self.assertGreater(len(texts), 50)
        bad = [x for x in texts if BANNED_WORDS.search(x)]
        self.assertEqual(bad, [])
        advice = {o["career_mobility_advice"] for o in outputs if "career_mobility_advice" in o}
        self.assertGreaterEqual(len(advice), 2)

    def test_no_text_in_the_engine_code_says_job_seeker_candidate_or_applicant(self):
        import ast
        for name in list(_FILES.values()) + ["engine_common.py"]:
            tree = ast.parse((ENGINE_DIR / name).read_text(encoding="utf-8"))
            docstrings = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body and isinstance(node.body[0], ast.Expr)                         and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    docstrings.add(id(node.body[0].value))
            bad = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                    text = node.value
                    if BANNED_WORDS.search(text) and " " in text.strip():      # a sentence or a label, not a key such as "candidate_id"
                        bad.append(text)
            self.assertEqual(bad, [], name)


# =====================================================================
# Old shapes and a run without the taxonomy
# =====================================================================
class OldShapeAndNoTaxonomyTests(EngineTestCase):
    OLD_CAND = {"id": "old1", "name": "Old Shape", "skills": ["python", "sql", {"name": "Docker"}, {"skill_name": "Excel", "type": "Transferable"}],
                "years_experience": 4, "highest_education": "Bachelor's degree", "target_anzsco_code": "261313", "preferred_location": "sydney",
                "cv_raw_text": "python sql docker excel"}
    OLD_JOB = {"id": "oldjob", "title": "Software Engineer", "company": "Acme", "category": "Technology & Data", "location": "Sydney NSW", "anzsco_code": "261313",
               "requirements": ["Python", "SQL", "Kubernetes"], "salary_min": 120000, "salary_max": 150000, "description": "Build services in Python."}

    def run_all(self):
        out = {}
        out["f1"] = self.f1.evaluate_skill_match(self.OLD_CAND, self.OLD_JOB)
        out["fit"] = self.f1.evaluate_job_fit(self.OLD_CAND, self.OLD_JOB)
        out["f2"] = self.f2.evaluate_skill_gaps(self.OLD_CAND, self.OLD_JOB, explicit_missing_skills=["Kubernetes"])
        out["path"] = self.f2.evaluate_path(self.OLD_CAND, self.OLD_JOB)
        out["f3"] = self.f3.compare_two_jobs(self.OLD_JOB, dict(self.OLD_JOB, id="b", title="Data Engineer"))
        out["f4"] = self.f4.calculate_candidate_merit_score(self.OLD_CAND)
        out["f5"] = self.f5.compute_feed_job_score(self.OLD_CAND, self.OLD_JOB)
        out["f6"] = self.f6.compute_talent_search_score(self.OLD_CAND, self.OLD_JOB)
        return out

    def test_old_dictionary_shapes_run_and_keep_the_old_keys(self):
        out = self.run_all()
        for key in ("overall_score", "sub_metrics", "final_match_score"):
            self.assertIn(key, out["f1"])
        self.assertBounded(out["f1"]["overall_score"])
        self.assertBounded(out["fit"]["fit"])
        self.assertIn("job_readiness_score", out["f2"])
        self.assertIn("job_proximity_index", out["f3"])
        self.assertIn("relative_merit_score", out["f4"])
        self.assertIn("feed_ranking_score", out["f5"])
        self.assertIn("talent_search_score", out["f6"])
        names = [i["name"] for i in out["fit"]["skill_breakdown"]]
        self.assertEqual(names, ["Python", "SQL", "Kubernetes"])
        self.assertEqual(out["fit"]["skill_breakdown"][0]["status"], "meets")
        self.assertIn(out["fit"]["skill_breakdown"][2]["status"], ("missing", "related"))     # Docker is related to Kubernetes

    def test_empty_dictionaries_do_not_crash(self):
        for c, j in (({}, {}), ({"skills": None}, {"requirements": None}), ({"skills": [None, "", {}]}, {"required_skills": [None, "", {}]})):
            r = self.f1.evaluate_job_fit(c, j)
            self.assertBounded(r["fit"])
            self.assertBounded(self.f2.evaluate_skill_gaps(c, j)["job_readiness_score"])
            self.f2.evaluate_path(c, j)
            self.assertBounded(self.f5.compute_feed_job_score(c, j)["feed_ranking_score"])
            self.assertBounded(self.f6.compute_talent_search_score(c, j)["talent_search_score"])
            self.assertBounded(self.f4.calculate_candidate_merit_score(c)["relative_merit_score"])
            self.assertBounded(self.f3.compare_two_jobs(j, j)["job_proximity_index"])

    def test_the_engine_runs_without_the_taxonomy_file(self):
        C = self.C
        try:
            C.set_taxonomy({})        # the same as a missing file
            self.assertFalse(C.get_taxonomy().loaded)
            out = self.run_all()
            self.assertBounded(out["fit"]["fit"])
            self.assertBounded(out["f1"]["overall_score"])
            self.assertEqual(out["fit"]["skill_breakdown"][0]["status"], "meets")        # Python is matched by its own name
            self.assertGreater(len(out["path"]["axes"]), 0)
            self.assertBounded(out["f5"]["feed_ranking_score"])
            for c, j in ((talent(), job()), ({}, {})):
                self.assertBounded(self.f6.compute_talent_search_score(c, j)["talent_search_score"])
            # case-insensitive match of the names still works
            r = self.f1.evaluate_job_fit({"skills": [{"name": "PYTHON", "level": 4}]}, {"required_skills": [{"name": "python", "level": 4}]})
            self.assertEqual(r["skill_breakdown"][0]["status"], "meets")
        finally:
            C.set_taxonomy(None)
        self.assertTrue(C.get_taxonomy().loaded)


if __name__ == "__main__":
    unittest.main()
