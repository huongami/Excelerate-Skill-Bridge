#!/usr/bin/env python3
"""
Jinder - verification of the six formulas (version 2)
=====================================================
Path: jinder_backend_engine/run_verification.py
Run:  python run_verification.py

What it does
  1. Runs the self-check of each formula file.
  2. Checks the properties of the formulas and prints PASS or FAIL for each one:
     bounds from 0 to 100, monotonic effects of level, years and skill level, the symmetry of Formula 3, determinism,
     the `path` object, the old dictionary shapes, a run without the taxonomy file, and that no private field is read.
  3. Runs the differentiation checks on the sample data: the 50 jobs and 50 talents of data/synthetic (if the files exist),
     else on 4 jobs and 4 talents that are built into this script.
  4. Imports the legacy wrapper backend/scores.py (the old prototype).

The exit code is 0 if all checks pass and 1 if one check fails.
"""

import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
ENGINE_DIR = os.path.join(PACKAGE_ROOT, "intelligence_engine")
BACKEND_DIR = os.path.join(PACKAGE_ROOT, "backend")
SYNTHETIC_DIR = os.path.join(PACKAGE_ROOT, "data", "synthetic")
FILES = {"f1": "01_skill_matching_model.py", "f2": "02_skill_gap_analysis.py", "f3": "03_job_to_job_comparison.py",
         "f4": "04_candidate_benchmarking.py", "f5": "05_job_seeker_ranking_feed.py", "f6": "06_recruiter_candidate_ranking.py"}

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, (" - " + str(detail)) if detail else ""))
    return bool(ok)


def load(key):
    spec = importlib.util.spec_from_file_location("verify_" + key, os.path.join(ENGINE_DIR, FILES[key]))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------
def job_from_file(j):
    sal, occ, certs = j.get("salary") or {}, j.get("occupation") or {}, j.get("certifications") or {}
    return {"id": j.get("key") or j.get("id"), "title": j["title"], "company": j["company"], "category": j["domain"], "specialisation": j.get("specialisation"),
            "level": j.get("level"), "min_years": j.get("minYears"), "max_years": j.get("maxYears"), "city": j.get("city"), "location": j.get("area") or j.get("city"),
            "work_mode": j.get("workMode"), "type": j.get("type"), "anzsco_code": occ.get("code", ""), "anzsco_title": occ.get("title", ""),
            "salary_min": sal.get("min"), "salary_max": sal.get("max"), "salary_unit": sal.get("unit"),
            "required_skills": [{"name": s["name"], "level": s["level"], "must": s["must"]} for s in j.get("skills") or []],
            "certifications_required": list(certs.get("required") or []), "certifications_preferred": list(certs.get("preferred") or []),
            "awards_preferred": list((j.get("awards") or {}).get("preferred") or []), "education_min": j.get("educationMin"), "days_old": j.get("postedDaysAgo")}


def talent_from_file(t, i):
    quals = t.get("qualification") or []
    best = ""
    for word in ("doctor", "phd", "master", "bachelor", "diploma", "certificate"):
        found = [q for q in quals if word in str(q).lower()]
        if found:
            best = found[0]
            break
    locs = list(t.get("locations") or [])
    return {"id": t.get("alias") or "talent-%d" % i, "alias": t.get("alias"), "current_title": t.get("currentRole"), "level": t.get("level"),
            "years_experience": t.get("yearsExperience"), "domain": t.get("domain"), "specialisation": t.get("specialisation"),
            "target_roles": list(t.get("targetRole") or []), "highest_education": best, "field_of_study": list(t.get("fieldOfStudy") or []),
            "skills": [{"name": s["name"], "level": s.get("level"), "years": s.get("years")} for s in t.get("skills") or []],
            "certifications": list(t.get("certifications") or []), "awards": list(t.get("awards") or []),
            "preferred_location": locs[0] if locs else "", "locations": locs, "work_modes": list(t.get("workModes") or []), "work_types": list(t.get("workTypes") or [])}


def built_in_sample():
    """Small samples, used only if the synthetic files are missing. All names are made up."""
    def job(i, title, domain, spec, level, lo, hi, city, mode, salary, skills, code, days):
        return {"id": "sample-job-%d" % i, "title": title, "company": "Sample Co %d" % i, "category": domain, "specialisation": spec, "level": level,
                "min_years": lo, "max_years": hi, "city": city, "location": city, "work_mode": mode, "type": "Full-time", "anzsco_code": code,
                "salary_min": salary[0], "salary_max": salary[1], "salary_unit": "year", "days_old": days, "education_min": "Bachelor's degree",
                "required_skills": [{"name": n, "level": l, "must": m} for n, l, m in skills],
                "certifications_required": [], "certifications_preferred": [], "awards_preferred": []}
    jobs = [
        job(1, "Data Engineer", "Data", "Data engineering", "Mid", 2, 5, "Sydney", "Hybrid", (120000, 140000), [("SQL", 4, True), ("Python", 3, True), ("Apache Airflow", 3, False)], "262111", 3),
        job(2, "Senior Backend Engineer", "Software Engineering", "Backend", "Senior", 5, 9, "Melbourne", "Remote", (160000, 185000), [("Python", 4, True), ("PostgreSQL", 4, True), ("Docker", 3, True), ("Kubernetes", 3, False)], "261313", 8),
        job(3, "Machine Learning Engineer", "AI & Machine Learning", "Machine learning engineering", "Mid", 2, 5, "Brisbane", "Onsite", (140000, 165000), [("Python", 4, True), ("PyTorch", 3, True), ("Machine learning", 4, True)], "261399", 12),
        job(4, "Junior Data Analyst", "Data", "Data analytics", "Junior", 0, 2, "Perth", "Hybrid", (75000, 90000), [("SQL", 3, True), ("Tableau", 2, True)], "224114", 5),
    ]
    talents = [
        {"id": "sample-talent-1", "alias": "Sample One", "current_title": "Data Analyst", "level": "Mid", "years_experience": 4.0, "domain": "Data", "specialisation": "Data analytics",
         "target_roles": ["Data Engineer"], "highest_education": "Bachelor's degree", "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}, {"name": "Tableau", "level": 3}],
         "preferred_location": "Sydney", "locations": ["Sydney"], "work_modes": ["Hybrid"], "work_types": ["Full-time"]},
        {"id": "sample-talent-2", "alias": "Sample Two", "current_title": "Software Engineer", "level": "Senior", "years_experience": 7.0, "domain": "Software Engineering",
         "specialisation": "Backend", "target_roles": ["Backend Engineer"], "highest_education": "Master's degree",
         "skills": [{"name": "Python", "level": 5}, {"name": "PostgreSQL", "level": 4}, {"name": "Docker", "level": 4}, {"name": "Kubernetes", "level": 2}],
         "preferred_location": "Melbourne", "locations": ["Melbourne"], "work_modes": ["Remote", "Hybrid"], "work_types": ["Full-time"]},
        {"id": "sample-talent-3", "alias": "Sample Three", "current_title": "Junior Developer", "level": "Junior", "years_experience": 1.0, "domain": "AI & Machine Learning",
         "specialisation": "Machine learning engineering", "target_roles": ["Machine Learning Engineer"], "highest_education": "Bachelor's degree",
         "skills": [{"name": "Python", "level": 3}, {"name": "Machine learning", "level": 2}, {"name": "PyTorch", "level": 1}],
         "preferred_location": "Brisbane", "locations": ["Brisbane"], "work_modes": ["Onsite"], "work_types": ["Full-time"]},
        {"id": "sample-talent-4", "alias": "Sample Four", "current_title": "Data Analyst", "level": "Junior", "years_experience": 1.5, "domain": "Data", "specialisation": "Data analytics",
         "target_roles": ["Data Analyst"], "highest_education": "Bachelor's degree", "skills": [{"name": "SQL", "level": 3}, {"name": "Tableau", "level": 3}],
         "preferred_location": "Perth", "locations": ["Perth"], "work_modes": ["Hybrid"], "work_types": ["Full-time"]},
    ]
    return jobs, talents


def sample_data():
    jobs_path, talents_path = os.path.join(SYNTHETIC_DIR, "jobs.json"), os.path.join(SYNTHETIC_DIR, "talents.json")
    if os.path.isfile(jobs_path) and os.path.isfile(talents_path):
        with open(jobs_path, encoding="utf-8") as f:
            jobs = [job_from_file(j) for j in json.load(f)["jobs"]]
        with open(talents_path, encoding="utf-8") as f:
            talents = [talent_from_file(t, i) for i, t in enumerate(json.load(f)["talents"])]
        return jobs, talents, "data/synthetic (%d jobs, %d talents)" % (len(jobs), len(talents))
    jobs, talents = built_in_sample()
    return jobs, talents, "built-in samples (%d jobs, %d talents)" % (len(jobs), len(talents))


# ---------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------
def in_range(v):
    return v is None or 0.0 <= v <= 100.0


def run_self_checks():
    print("\n[1] Self-check of each formula file")
    for key, name in sorted(FILES.items()):
        start = time.time()
        res = subprocess.run([sys.executable, name], cwd=ENGINE_DIR, capture_output=True, text=True)
        check("%s runs to the end" % name, res.returncode == 0, "%.0f ms%s" % ((time.time() - start) * 1000, "" if res.returncode == 0 else "\n" + (res.stderr or res.stdout)))


def run_property_checks(m, jobs, talents):
    f1, f2, f3, f4, f5, f6 = (m[k] for k in ("f1", "f2", "f3", "f4", "f5", "f6"))
    C = sys.modules["jinder_engine_common"]
    print("\n[2] Properties of the formulas")
    check("the taxonomy file is loaded", C.get_taxonomy().loaded, "%d skills" % len(C.get_taxonomy().skills))

    # bounds
    bad = []
    for t in talents[:12]:           # the bounds of all 2500 pairs are tested in section 3 and in the unit tests
        feed = f5.rank_job_feed_for_candidate(t, jobs, top_limit=len(jobs))["top_feed"]
        for item in feed:
            if not in_range(item["feed_ranking_score"]) or not all(in_range(v) for k, v in item["sub_metrics"].items() if k.startswith("s_")):
                bad.append(("F5", t["id"], item["job_id"]))
        for j in jobs:
            fit = f1.evaluate_job_fit(t, j)
            m1 = f1.evaluate_skill_match(t, j)
            g = f2.evaluate_skill_gaps(t, j)
            s6 = f6.compute_talent_search_score(t, j)
            values = [("F1 fit", fit["fit"]), ("F1 smf", m1["overall_score"]), ("F2 jrs", g["job_readiness_score"]), ("F2 gsi", g["gap_severity_index"]),
                      ("F6", s6["talent_search_score"])] + [("F1 part " + k, v) for k, v in fit["parts"].items()]
            bad.extend((name, t["id"], j["id"]) for name, v in values if not in_range(v))
    for t in talents:
        res = f4.calculate_candidate_merit_score(t)
        bad.extend(("F4", t["id"], k) for k, v in res["sub_metrics"].items() if k != "education_bonus" and not in_range(v))
    for a in jobs[:6]:
        for b in jobs[:6]:
            if not in_range(f3.compare_two_jobs(a, b)["job_proximity_index"]):
                bad.append(("F3", a["id"], b["id"]))
    check("all scores are between 0 and 100 (6 formulas, every pair)", not bad, bad[:3])

    # symmetry of F3
    asym = [(a["id"], b["id"]) for a in jobs for b in jobs if f3.compare_two_jobs(a, b)["job_proximity_index"] != f3.compare_two_jobs(b, a)["job_proximity_index"]]
    check("Formula 3 is symmetric: JPI(A, B) = JPI(B, A)", not asym, asym[:3])
    same = f3.compare_two_jobs(jobs[0], dict(jobs[0], id="copy"))["job_proximity_index"]
    check("Formula 3 gives 100 for two equal jobs", same == 100.0, same)

    # determinism
    t, j = talents[0], jobs[0]
    a = json.dumps([f1.evaluate_job_fit(t, j), f2.evaluate_path(t, j), f5.compute_feed_job_score(t, j), f6.compute_talent_search_score(t, j)], sort_keys=True, default=str)
    b = json.dumps([f1.evaluate_job_fit(json.loads(json.dumps(t)), json.loads(json.dumps(j))), f2.evaluate_path(t, j), f5.compute_feed_job_score(t, j),
                    f6.compute_talent_search_score(t, j)], sort_keys=True, default=str)
    check("the same input gives the same output (determinism)", a == b)

    # monotone in level, years, skill level
    base_t = dict(talents[0], level="Mid", years_experience=3.0, skills=[{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}])
    base_j = dict(jobs[0], level="Senior", min_years=5, max_years=9, required_skills=[{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True}],
                  city="Sydney", location="Sydney", work_mode="Remote", certifications_required=[], certifications_preferred=[], awards_preferred=[])
    levels = ["Intern", "Junior", "Mid", "Senior"]
    fits = [f1.evaluate_job_fit(dict(base_t, level=l), base_j)["fit"] for l in levels]
    check("the fit rises with the level of the talent up to the level of the job", fits == sorted(fits) and len(set(fits)) == 4, fits)
    ladder = [f1.evaluate_job_fit(base_t, dict(base_j, level=l, min_years=None, max_years=None))["fit"] for l in ("Mid", "Senior", "Lead", "Principal")]
    check("a level gap upward lowers the fit", ladder == sorted(ladder, reverse=True) and len(set(ladder)) == 4, ladder)
    years = [f1.evaluate_job_fit(dict(base_t, years_experience=y, level="Senior"), base_j)["fit"] for y in (0, 1, 2, 3, 4, 5)]
    check("the fit rises with the years below the minimum", years == sorted(years) and len(set(years)) == 6, years)
    skill = [f1.evaluate_job_fit(dict(base_t, skills=[{"name": "SQL", "level": 4}, {"name": "Python", "level": l}]), base_j)["fit"] for l in (1, 2, 3, 4)]
    check("the fit rises with the skill level", skill == sorted(skill) and len(set(skill)) == 4, skill)
    ev = [f4.calculate_candidate_merit_score(dict(base_t, years_experience=y))["sub_metrics"]["experience_maturity"] for y in (0, 1, 3, 8, 15)]
    check("Formula 4: experience rises with the years", ev == sorted(ev) and len(set(ev)) == 5, ev)
    lv = [f4.calculate_candidate_merit_score(dict(base_t, level=l))["sub_metrics"]["level_standing"] for l in ("Intern", "Junior", "Mid", "Senior", "Lead", "Principal")]
    check("Formula 4: the level standing rises with the level", lv == sorted(lv) and len(set(lv)) == 6, lv)
    cert = next(iter(C.get_taxonomy().certs), None)
    if cert:
        jc = dict(base_j, certifications_required=[cert])
        no = f2.evaluate_skill_gaps(base_t, jc)
        yes = f2.evaluate_skill_gaps(dict(base_t, certifications=[{"name": cert.upper(), "year": 2025}]), jc)
        check("a held required certification removes the gap", any(g["kind"] == "certification" for g in no["gaps"]) and not any(g["kind"] == "certification" for g in yes["gaps"]))
        check("a missing certification is not a legal block", not no["has_statutory_blocker"])
    remote = [f1.evaluate_job_fit(dict(base_t, preferred_location=c, locations=[c]), dict(base_j, work_mode="Remote", city="Remote"))["parts"]["location"] for c in ("Sydney", "Perth", "Hobart")]
    check("a Remote job fits every city", remote == [100.0, 100.0, 100.0], remote)
    check("the salary unit: day x 220, hour x 1950, year x 1", f3.annual_salary(700, 800, "day") == (154000.0, 176000.0) and f3.annual_salary(60, 80, "hour") == (117000.0, 156000.0)
          and f3.annual_salary(100000, 120000, "year") == (100000.0, 120000.0))

    # the path object
    path = f2.evaluate_path(base_t, dict(base_j, certifications_required=[cert] if cert else []))
    ok_axes = all(0 <= x["required"] <= 100 and 0 <= x["have"] <= 100 and x["status"] == ("above" if x["have"] >= x["required"] + 15 else ("fit" if x["have"] >= x["required"] else "gap"))
                  for x in path["axes"])
    check("the path object has axes, fit, gaps and summary, with the status rule", set(path) == {"axes", "fit", "gaps", "summary"} and ok_axes and "projection" not in path)
    check("the path has a certification axis only when the job lists certifications",
          ("certifications" in [x["key"] for x in path["axes"]]) == bool(cert) and "certifications" not in [x["key"] for x in f2.evaluate_path(base_t, base_j)["axes"]])

    # privacy
    private = {"name": "Real Person", "full_name": "Real Person", "email": "x@example.test", "phone": "+61 400 000 000", "origin": "Vietnam", "country": "Vietnam",
               "nationality": "x", "visa": "x", "gender": "x", "age": 50, "date_of_birth": "1970-01-01", "photo": "x"}
    noisy = dict(talents[0], **private)

    def dump(x):
        return json.dumps(x, sort_keys=True, default=str)
    same_out = (dump(f1.evaluate_job_fit(talents[0], jobs[0])) == dump(f1.evaluate_job_fit(noisy, jobs[0]))
                and dump(f6.compute_talent_search_score(talents[0], jobs[0])) == dump(f6.compute_talent_search_score(noisy, jobs[0]))
                and dump(f5.rank_job_feed_for_candidate(talents[0], jobs, 3)) == dump(f5.rank_job_feed_for_candidate(noisy, jobs, 3))
                and dump(f4.calculate_candidate_merit_score(talents[0])) == dump(f4.calculate_candidate_merit_score(noisy)))
    check("no private field changes a result (name, email, country, visa, age, gender, ...)", same_out)
    long_text = dict(talents[0], cv_raw_text="long text " * 2000)
    check("Formula 6 and Formula 4 do not read the CV text",
          dump(f6.compute_talent_search_score(talents[0], jobs[0])) == dump(f6.compute_talent_search_score(long_text, jobs[0]))
          and dump(f4.calculate_candidate_merit_score(talents[0])) == dump(f4.calculate_candidate_merit_score(long_text)))

    # old shapes
    old_c = {"id": "old", "skills": ["python", {"name": "sql"}, {"skill_name": "docker", "type": "Transferable"}], "years_experience": 4, "highest_education": "Bachelor's degree",
             "target_anzsco_code": "261313", "preferred_location": "sydney", "cv_raw_text": "python sql docker"}
    old_j = {"id": "oldj", "title": "Software Engineer", "company": "Old Co", "category": "Technology & Data", "location": "Sydney NSW", "anzsco_code": "261313",
             "requirements": ["Python", "SQL", "Kubernetes"], "salary_min": 120000, "salary_max": 150000, "description": "Build services."}
    try:
        outs = [f1.evaluate_skill_match(old_c, old_j), f1.evaluate_job_fit(old_c, old_j), f2.evaluate_skill_gaps(old_c, old_j, ["Terraform"]), f2.evaluate_path(old_c, old_j),
                f3.compare_two_jobs(old_j, dict(old_j, id="b")), f4.calculate_candidate_merit_score(old_c), f5.compute_feed_job_score(old_c, old_j),
                f6.compute_talent_search_score(old_c, old_j), f1.evaluate_skill_match(old_c, "261313")]
        ok = all(k in outs[0] for k in ("overall_score", "sub_metrics")) and "job_readiness_score" in outs[2] and "job_proximity_index" in outs[4]
        check("the old dictionary shapes still work (strings as skills, no level, no years of skill)", ok)
    except Exception as e:  # noqa: BLE001
        check("the old dictionary shapes still work", False, repr(e))

    # no taxonomy
    try:
        C.set_taxonomy({})
        r = f1.evaluate_job_fit(talents[0], jobs[0])
        r5 = f5.compute_feed_job_score(talents[0], jobs[0])
        r6 = f6.compute_talent_search_score(talents[0], jobs[0])
        ok = in_range(r["fit"]) and in_range(r5["feed_ranking_score"]) and in_range(r6["talent_search_score"]) and not C.get_taxonomy().loaded
        check("the engine runs without the taxonomy file (simple defaults)", ok, "fit %.1f" % r["fit"])
    except Exception as e:  # noqa: BLE001
        check("the engine runs without the taxonomy file", False, repr(e))
    finally:
        C.set_taxonomy(None)


def run_differentiation(m, jobs, talents, label):
    f1, f2, f5, f6 = m["f1"], m["f2"], m["f5"], m["f6"]
    print("\n[3] Differentiation on %s" % label)
    distinct, spreads, const_axes = [], [], 0
    for t in talents:
        feed = f5.rank_job_feed_for_candidate(t, jobs, top_limit=len(jobs))["top_feed"]
        frs = {x["job_id"]: x for x in feed}
        scores, axes = [], {k: [] for k in ("occupation", "skills", "methods", "readiness", "capability", "pay", "location", "freshness")}
        for j in jobs:
            fit = f1.evaluate_job_fit(t, j)["fit"]
            scores.append(round(0.55 * fit + 0.45 * frs[j["id"]]["feed_ranking_score"], 1))
            sm = f1.evaluate_skill_match(t, j)["sub_metrics"]
            sub = frs[j["id"]]["sub_metrics"]
            for k, v in (("occupation", sm["s_tree_taxonomy"]), ("skills", sm["s_direct_competency"]), ("methods", sm["s_trans_methodology"]),
                         ("readiness", f2.evaluate_skill_gaps(t, j)["job_readiness_score"]), ("capability", sub["s_cap_capability"]), ("pay", sub["s_wage_upside"]),
                         ("location", sub["s_loc_location"]), ("freshness", sub["s_rec_recency"])):
                axes[k].append(round(v, 1))
        scores.sort(reverse=True)
        top = scores[:20]
        distinct.append(len(set(top)) if len(jobs) >= 20 else len(set(scores)))
        spreads.append(scores[0] - scores[-1])
        const_axes += sum(1 for v in axes.values() if len(set(v)) < 2)
    big = len(jobs) >= 20
    need = 18 if big else len(jobs) - 0
    print("      top-20 distinct scores: min %d, mean %.2f | best minus worst: min %.1f, mean %.1f | radar axes with one value for all jobs: %d"
          % (min(distinct), statistics.mean(distinct), min(spreads), statistics.mean(spreads), const_axes))
    check("each talent has %s different scores in the top %s" % (">= 18" if big else "all", "20" if big else "list"), min(distinct) >= need, "min %d" % min(distinct))
    check("best minus worst is %s" % (">= 30 points for each talent" if big else ">= 5 points for each talent"), min(spreads) >= (30.0 if big else 5.0), "min %.1f" % min(spreads))
    check("no radar axis has the same value for all jobs", const_axes == 0, "%d axes" % const_axes)
    ties = []
    for j in jobs:
        order = sorted((round(0.6 * r["skill_coverage"] + 0.4 * r["talent_search_score"], 1) for r in (f6.compute_talent_search_score(t, j) for t in talents)), reverse=True)[:10]
        ties.append(len(order) - len(set(order)))
    check("the order of the talents has at most 2 exact ties in the top 10 for each job", max(ties) <= 2, "max %d" % max(ties))


def run_backend_wrapper():
    print("\n[4] Legacy backend wrapper")
    if not os.path.isdir(BACKEND_DIR):
        print("      (no backend folder)")
        return
    res = subprocess.run([sys.executable, "-c", "import scores; print('scores.py imported')"], cwd=BACKEND_DIR, capture_output=True, text=True)
    check("backend/scores.py imports the formulas", res.returncode == 0, (res.stderr or "").strip()[-200:])


def main():
    print("=" * 75)
    print("JINDER INTELLIGENCE ENGINE - VERIFICATION (version 2)")
    print("=" * 75)
    run_self_checks()
    models = {k: load(k) for k in FILES}
    jobs, talents, label = sample_data()
    print("\nSample data: %s" % label)
    run_property_checks(models, jobs, talents)
    run_differentiation(models, jobs, talents, label)
    run_backend_wrapper()
    failed = RESULTS.count(False)
    print("\n" + "=" * 75)
    print("%d checks: %d PASS, %d FAIL" % (len(RESULTS), RESULTS.count(True), failed))
    print("ALL CHECKS PASSED." if not failed else "SOME CHECKS FAILED. Read the lines that start with [FAIL].")
    print("=" * 75)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
