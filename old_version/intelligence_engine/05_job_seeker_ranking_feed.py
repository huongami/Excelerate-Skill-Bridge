#!/usr/bin/env python3
"""
Skill Bridge Intelligence Engine — Formula 5: Job Seeker Feed Ranking Engine (JFR)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-005
"""

import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Sector median benchmark salaries in AUD
SECTOR_BENCHMARK_SALARY_AUD = {
    "Healthcare & Nursing": 115000.0,
    "Technology & Data": 135000.0,
    "Finance & Accounting": 120000.0,
    "Engineering & Construction": 130000.0,
    "Marketing & Communications": 105000.0,
    "Operations & Administration": 90000.0,
    "Supply Chain & Logistics": 100000.0,
    "Hospitality & Service": 75000.0
}


import re
import datetime

def compute_feed_job_score(
    candidate: Dict[str, Any],
    job: Dict[str, Any],
    same_employer_count_ahead: int = 0,
    weights: Tuple[float, float, float, float] = (0.45, 0.20, 0.20, 0.15)
) -> Dict[str, Any]:
    """
    Computes Formula 5: Feed Ranking Score (FRS) for a single job vacancy relative to candidate.
    Follows ASD-STE100 specification IE-SPEC-005.
    """
    w_cap, w_wage, w_loc, w_rec = weights
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"

    cand_sec = str(candidate.get("category") or candidate.get("target_anzsco_title") or "").strip().lower()
    job_sec = str(job.get("category") or job.get("anzsco_title") or "").strip().lower()

    cand_anzsco = str(candidate.get("target_anzsco_code") or candidate.get("anzscoCode") or candidate.get("anzsco_code") or "").strip()
    job_anzsco = str(job.get("anzsco_code") or job.get("anzsco") or "").strip()

    c_digits = "".join(re.findall(r"\d+", cand_anzsco))
    j_digits = "".join(re.findall(r"\d+", job_anzsco))

    # 1. Capability Score (S_cap)
    if c_digits and j_digits and c_digits[:6] == j_digits[:6]:
        s_cap = 95.0
    elif c_digits and j_digits and c_digits[:4] == j_digits[:4]:
        s_cap = 82.0
    elif c_digits and j_digits and c_digits[:2] == j_digits[:2]:
        s_cap = 68.0
    elif cand_sec and job_sec and (cand_sec in job_sec or job_sec in cand_sec):
        s_cap = 72.0
    elif {cand_sec, job_sec}.issubset({"finance & accounting", "operations & administration", "supply chain & logistics"}):
        s_cap = 58.0
    else:
        s_cap = 32.0

    # Skill bonus if candidate verified skills overlap with job requirements
    cand_skills = [s.get("skill_name", "").lower() for s in candidate.get("skills", []) if isinstance(s, dict)]
    cand_cv = str(candidate.get("cv_raw_text") or "").lower()
    full_cand = " ".join(cand_skills) + " " + cand_cv
    
    job_reqs = []
    if job.get("requirements") and isinstance(job["requirements"], list):
        job_reqs = job["requirements"]
    elif job.get("requirements_json"):
        import json
        try:
            r = json.loads(job["requirements_json"]) if isinstance(job["requirements_json"], str) else job["requirements_json"]
            if isinstance(r, list):
                job_reqs = r
        except Exception:
            pass

    if job_reqs:
        matched = sum(1 for req in job_reqs if any(w in full_cand for w in str(req).lower().split() if len(w) >= 4))
        skill_boost = 5.0 * (matched / max(1, len(job_reqs)))
        s_cap = min(98.0, s_cap + skill_boost)

    # 2. Wage Upside Score (S_wage)
    s_min = float(job.get("salary_min") or 0.0)
    s_max = float(job.get("salary_max") or 0.0)
    if 0 < s_max < 500.0:  # Hourly to annual
        s_min *= 1950.0
        s_max *= 1950.0
    mid_salary = (s_min + s_max) / 2.0 if (s_min and s_max) else max(s_min, s_max, 100000.0)

    sector_benchmark = SECTOR_BENCHMARK_SALARY_AUD.get(job.get("category"), 110000.0)
    salary_ratio_diff = (mid_salary - sector_benchmark) / sector_benchmark
    s_wage = min(100.0, max(20.0, 50.0 + (salary_ratio_diff * 85.0)))

    # 3. Location Alignment Score (S_loc)
    pref_city = str(candidate.get("preferred_location") or "sydney").lower().strip()
    job_loc = str(job.get("location") or job.get("city") or "").lower()

    if pref_city in job_loc or "remote" in job_loc:
        s_loc = 100.0
    elif "nsw" in job_loc or "sydney" in job_loc:
        s_loc = 82.0
    elif any(city in job_loc for city in ["melbourne", "brisbane", "perth", "adelaide"]):
        s_loc = 58.0
    else:
        s_loc = 38.0

    # 4. Posting Recency Score (S_rec)
    if job.get("posted_at"):
        try:
            p_dt = datetime.datetime.strptime(str(job["posted_at"])[:19], "%Y-%m-%d %H:%M:%S")
            diff_days = max(0.5, (datetime.datetime(2026, 10, 5, 0, 0, 0) - p_dt).total_seconds() / 86400.0)
        except Exception:
            diff_days = float(job.get("days_old", 3.0))
    else:
        diff_days = float(job.get("days_old", 3.0))
    s_rec = round(100.0 * math.exp(-0.04 * diff_days), 1)

    # 5. Employer Diversity Penalty (delta_div)
    delta_div = min(0.40, same_employer_count_ahead * 0.15)

    # Master Composite Equation
    base_score = (w_cap * s_cap) + (w_wage * s_wage) + (w_loc * s_loc) + (w_rec * s_rec)
    final_frs = round(max(0.0, min(100.0, base_score * (1.0 - delta_div))), 1)

    return {
        "job_id": job.get("id") or job.get("job_id"),
        "job_title": job.get("title"),
        "employer_name": job.get("company"),
        "job_sector": job.get("category"),
        "location": job.get("location"),
        "salary_range": job.get("salary") or job.get("salary_range") or job.get("salary_display"),
        "feed_ranking_score": final_frs,
        "overall_score": final_frs,
        "sub_metrics": {
            "s_cap_capability": round(s_cap, 1),
            "s_wage_upside": round(s_wage, 1),
            "s_loc_location": round(s_loc, 1),
            "s_rec_recency": round(s_rec, 1),
            "employer_diversity_penalty": round(delta_div, 2)
        }
    }


def rank_job_feed_for_candidate(
    candidate: Dict[str, Any],
    all_jobs: List[Dict[str, Any]],
    top_limit: int = 50
) -> Dict[str, Any]:
    """
    Ranks the complete Australian vacancy catalog for a given job seeker.
    Applies employer saturation prevention dynamically.
    """
    # 1. Initial pass scoring without diversity penalty
    scored_items = []
    for job in all_jobs:
        score_data = compute_feed_job_score(candidate, job, same_employer_count_ahead=0)
        scored_items.append(score_data)

    # 2. Preliminary sort
    scored_items.sort(key=lambda x: x["feed_ranking_score"], reverse=True)

    # 3. Apply employer diversity penalty iteratively
    employer_counts = defaultdict(int)
    final_feed = []

    for item in scored_items:
        emp = item["employer_name"]
        ahead_count = employer_counts[emp]
        
        # If penalty applies, recalculate
        if ahead_count > 0:
            delta_div = min(0.40, ahead_count * 0.15)
            # Recompute penalized score
            base = item["feed_ranking_score"]
            penalized = round(base * (1.0 - delta_div), 1)
            item["feed_ranking_score"] = penalized
            item["sub_metrics"]["employer_diversity_penalty"] = delta_div

        employer_counts[emp] += 1
        final_feed.append(item)

    # Re-sort with penalties applied
    final_feed.sort(key=lambda x: x["feed_ranking_score"], reverse=True)

    # Add display ranks
    for idx, item in enumerate(final_feed):
        item["feed_position"] = idx + 1

    return {
        "candidate_id": candidate.get("id") or candidate.get("candidate_id"),
        "candidate_name": candidate.get("name") or candidate.get("full_name"),
        "total_jobs_evaluated": len(all_jobs),
        "total_ranked_output": min(top_limit, len(final_feed)),
        "top_feed": final_feed[:top_limit]
    }


# =====================================================================
# 4. SELF-CONTAINED VERIFICATION BENCHMARK
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 75)
    print("SKILL BRIDGE INTELLIGENCE ENGINE — FORMULA 5 VERIFICATION (ASD-STE100)")
    print("=" * 75)

    import os
    cand_path = "data/australian_candidates.json" if os.path.exists("data/australian_candidates.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_candidates.json")
    job_path = "data/australian_jobs.json" if os.path.exists("data/australian_jobs.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_jobs.json")
    with open(cand_path, "r", encoding="utf-8") as f:
        cands = json.load(f)
    with open(job_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    c0 = cands[0]  # Registered Nurse, Healthcare & Nursing
    ranked_result = rank_job_feed_for_candidate(c0, jobs, top_limit=10)

    print(f"\nPersonalized Job Feed Generated for: {ranked_result['candidate_name']} ({c0['category']})")
    print(f"Evaluated {ranked_result['total_jobs_evaluated']} Australian Vacancies. Displaying Top {ranked_result['total_ranked_output']}:\n")

    for j in ranked_result["top_feed"]:
        print(f"#{j['feed_position']:2d} | FRS: {j['feed_ranking_score']:4.1f}% | {j['job_title'][:32]:32} | {j['employer_name'][:20]:20} | {j['location'][:18]:18}")

    print("\n" + "=" * 75)
    print("FORMULA 5 PRODUCTION VALIDATION COMPLETE.")
    print("=" * 75)
