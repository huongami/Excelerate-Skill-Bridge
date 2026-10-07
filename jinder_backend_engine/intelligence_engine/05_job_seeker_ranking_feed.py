#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 5: Talent Feed Ranking Engine (JFR)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-005 (see 05_JOB_SEEKER_RANKING_FEED.md)

FRS = (w_cap S_cap + w_wage S_wage + w_loc S_loc + w_rec S_rec) x (1 - delta_div)
The platform shows no FRS number. It uses FRS (after the behaviour loop) with the product fit to put jobs in order.
"""

import importlib.util
import math
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


def _load_common():
    name = "jinder_engine_common"
    mod = sys.modules.get(name)
    if mod is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_common.py")
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return mod


C = _load_common()
F1 = C.load_sibling("f1")
F2 = C.load_sibling("f2")

# (capability, wage upside, location, recency). The four weights sum to 1.00.
DEFAULT_WEIGHTS = (0.43, 0.21, 0.18, 0.18)
CAP_WEIGHTS = (0.53, 0.27, 0.20)      # S_cap = 0.53 SMF + 0.27 JRS + 0.20 level-and-years fit
WAGE_SLOPE = 4.3                      # S_wage = 100 logistic(z, 0, 4.3)
RECENCY_RATE = 0.044                  # S_rec = 100 exp(-0.044 days)
DIVERSITY_STEP = 0.15
DIVERSITY_MAX = 0.40
UNKNOWN_DAYS = 14.0                   # a job with no posting date counts as 14 days old
SECTOR_BENCHMARK_SALARY_AUD = {"Software Engineering": 130000.0, "AI & Machine Learning": 150000.0, "Data": 125000.0}   # mid-level, per domain


# =====================================================================
# 1. SUB-METRICS
# =====================================================================

def wage_upside(job_mid: Optional[float], domain: str, job_rank: Optional[float], cand_rank: Optional[float]) -> float:
    """S_wage = 100 x logistic(z, 0, 4.3),  z = 0.6 ln(M / B(d, job level)) + 0.4 ln(M / B(d, talent level)).
    M is the middle of the job pay. B(d, r) = base(d) exp(0.20 (r - 2)) is the benchmark for a domain and a level.
    A job with no pay gives 50."""
    if not job_mid or job_mid <= 0:
        return 50.0
    b_job = C.salary_benchmark(domain, job_rank)
    b_me = C.salary_benchmark(domain, cand_rank if cand_rank is not None else job_rank)
    z = 0.6 * math.log(job_mid / b_job) + 0.4 * math.log(job_mid / b_me)
    return 100.0 * C.logistic(z, 0.0, WAGE_SLOPE)


def recency(days_old: Optional[float]) -> float:
    """S_rec = 100 exp(-0.044 D), D = age of the posting in days."""
    d = UNKNOWN_DAYS if days_old is None else max(0.0, float(days_old))
    return 100.0 * math.exp(-RECENCY_RATE * d)


def _capability(an: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    smf = F1.smf_from_analysis(an)["final"]
    gaps = F2.gaps_and_strengths(an)
    lv = an["level"] if an["level"] is not None else 0.6
    yr = an["years"] if an["years"] is not None else 0.6
    lvl_years = 100.0 * (0.5 * lv + 0.5 * yr)
    w1, w2, w3 = CAP_WEIGHTS
    return w1 * smf + w2 * gaps["jrs"] + w3 * lvl_years, {"smf": smf, "readiness": gaps["jrs"], "level_years_fit": lvl_years}


# =====================================================================
# 2. THE FEED SCORE OF ONE JOB
# =====================================================================

def _score(cand: Dict[str, Any], job: Dict[str, Any], same_employer_count_ahead: int, weights: Tuple[float, float, float, float]) -> Dict[str, Any]:
    w_cap, w_wage, w_loc, w_rec = weights
    an = F1.analyse(cand, job)
    jb = an["job"]
    s_cap, cap_parts = _capability(an)
    s_wage = wage_upside(jb["salary_mid"], jb["domain"], jb["level_rank"], cand["level_rank"])
    loc = an["location"]
    s_loc = 100.0 * (loc if loc is not None else 0.6)
    s_rec = recency(jb["days_old"])
    delta = min(DIVERSITY_MAX, same_employer_count_ahead * DIVERSITY_STEP)
    base = w_cap * s_cap + w_wage * s_wage + w_loc * s_loc + w_rec * s_rec
    exact = max(0.0, min(100.0, base * (1.0 - delta)))
    return {
        "job_id": jb["id"], "job_title": jb["title"], "employer_name": jb["company"], "job_sector": jb["category"] or jb["domain"],
        "location": job.get("location") if isinstance(job, dict) else None,
        "salary_range": (job.get("salary") or job.get("salary_range") or job.get("salary_display")) if isinstance(job, dict) else None,
        "feed_ranking_score": round(exact, 1), "overall_score": round(exact, 1), "frs_exact": exact, "base_exact": base,
        "sub_metrics": {
            "s_cap_capability": round(s_cap, 1), "s_wage_upside": round(s_wage, 1), "s_loc_location": round(s_loc, 1), "s_rec_recency": round(s_rec, 1),
            "employer_diversity_penalty": round(delta, 2),
            "capability_smf": round(cap_parts["smf"], 1), "capability_readiness": round(cap_parts["readiness"], 1),
            "capability_level_years": round(cap_parts["level_years_fit"], 1),
        },
    }


def compute_feed_job_score(candidate: Dict[str, Any], job: Dict[str, Any], same_employer_count_ahead: int = 0,
                           weights: Tuple[float, float, float, float] = DEFAULT_WEIGHTS) -> Dict[str, Any]:
    """Formula 5: the Feed Ranking Score (FRS) of one job for one candidate, from 0 to 100.

    S_cap  = 0.53 SMF + 0.27 JRS + 0.20 (level fit and years fit)         (Formulas 1 and 2)
    S_wage = 100 logistic(0.6 ln(M / B(d, job level)) + 0.4 ln(M / B(d, my level)), 0, 4.3)
    S_loc  = 100 x location fit (city distance and work mode; Remote = 100)
    S_rec  = 100 exp(-0.044 D)
    FRS    = (0.43 S_cap + 0.21 S_wage + 0.18 S_loc + 0.18 S_rec) x (1 - min(0.40, 0.15 k))     (k = jobs of the same employer ahead)
    """
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"
    return _score(C.prepare_candidate(candidate), job, same_employer_count_ahead, tuple(weights))


def rank_job_feed_for_candidate(candidate: Dict[str, Any], all_jobs: List[Dict[str, Any]], top_limit: int = 50,
                                weights: Tuple[float, float, float, float] = DEFAULT_WEIGHTS) -> Dict[str, Any]:
    """The feed of all jobs for one candidate, with the employer diversity penalty.

    Step 1: score each job with no penalty and sort (ties: job id).
    Step 2: going down the list, a job gets the penalty min(0.40, 0.15 k), k = jobs of the same employer above it.
    Step 3: sort again and number the positions.
    """
    cand = C.prepare_candidate(candidate)
    first = [_score(cand, j, 0, tuple(weights)) for j in all_jobs]
    first.sort(key=lambda x: (-x["base_exact"], str(x["job_id"])))
    employer_counts: Dict[str, int] = defaultdict(int)
    final = []
    for item in first:
        emp = C.norm_key(item["employer_name"])
        ahead = employer_counts[emp] if emp else 0
        if ahead > 0:
            delta = min(DIVERSITY_MAX, ahead * DIVERSITY_STEP)
            exact = max(0.0, min(100.0, item["base_exact"] * (1.0 - delta)))
            item["feed_ranking_score"] = item["overall_score"] = round(exact, 1)
            item["frs_exact"] = exact
            item["sub_metrics"]["employer_diversity_penalty"] = round(delta, 2)
        if emp:
            employer_counts[emp] += 1
        final.append(item)
    final.sort(key=lambda x: (-x["frs_exact"], str(x["job_id"])))
    for i, item in enumerate(final):
        item["feed_position"] = i + 1
    return {
        "candidate_id": cand["id"], "candidate_name": cand["alias"] or cand["id"],
        "total_jobs_evaluated": len(all_jobs), "total_ranked_output": min(top_limit, len(final)), "top_feed": final[:top_limit],
    }


# =====================================================================
# 3. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 5 SELF-CHECK")
    cand = {"id": "demo", "level": "Mid", "years_experience": 4, "current_title": "Data Analyst", "preferred_location": "Sydney",
            "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}]}
    jobs = [{"id": f"j{i}", "title": "Data Engineer", "company": "Acme" if i < 2 else f"Co{i}", "category": "Data", "level": "Mid", "city": "Sydney",
             "work_mode": "Hybrid", "salary_min": 110000 + 5000 * i, "salary_max": 130000 + 5000 * i, "days_old": 2 + 3 * i,
             "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 3, "must": True}]} for i in range(4)]
    for it in rank_job_feed_for_candidate(cand, jobs, 4)["top_feed"]:
        print(it["feed_position"], it["job_id"], it["employer_name"], it["feed_ranking_score"], it["sub_metrics"])
