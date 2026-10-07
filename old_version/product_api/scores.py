"""
Skill Bridge 2.0 — Intelligence Engine Wrapper & Behavioural Scoring
Path: product_api/scores.py
Follows specification in app/spec/04_DATA_AND_SCORING_SPEC.md § 5 & § 6
Directly imports Formulas 1 through 6 without weight tampering or client approximation.
"""

import sys
import os
import math
from typing import Dict, Any, List

# Add parent directory to path so intelligence_engine can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import importlib
    f1 = importlib.import_module("intelligence_engine.01_skill_matching_model")
    f2 = importlib.import_module("intelligence_engine.02_skill_gap_analysis")
    f3 = importlib.import_module("intelligence_engine.03_job_to_job_comparison")
    f4 = importlib.import_module("intelligence_engine.04_candidate_benchmarking")
    f5 = importlib.import_module("intelligence_engine.05_job_seeker_ranking_feed")
    f6 = importlib.import_module("intelligence_engine.06_recruiter_candidate_ranking")
except Exception as e:
    print(f"Warning: Failed to dynamically import intelligence_engine modules: {e}")
    raise


# =====================================================================
# 1. FORMULA 1: Candidate vs ANZSCO Skill Match Model (SMF)
# =====================================================================
def get_skill_match_score(candidate: Dict[str, Any], anzsco_code: str) -> Dict[str, Any]:
    """Evaluates candidate skill match vs benchmark ANZSCO code."""
    res = f1.evaluate_skill_match(candidate, anzsco_code)
    if "overall_score" not in res and "final_match_score" in res:
        res["overall_score"] = res["final_match_score"]
    return res


# =====================================================================
# 2. FORMULA 2: Skill Gap Severity & Job Readiness Score (GSI & JRS)
# =====================================================================
def get_skill_gap_analysis(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes competency deficit and estimates months to close."""
    res = f2.evaluate_skill_gaps(candidate, job)
    if "estimated_closing_months" not in res and "estimated_bridge_months" in res:
        res["estimated_closing_months"] = res["estimated_bridge_months"]
    if "skill_gap_pct" not in res and "gap_severity_index" in res:
        res["skill_gap_pct"] = res["gap_severity_index"]
    return res


# =====================================================================
# 3. FORMULA 3: Job vs Job Comparison Matrix & Overlaid Proximity (JPI)
# =====================================================================
def compare_jobs(job_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compares 2 to 4 jobs across ANZSCO proximity, salary parity, and requirements."""
    if len(job_list) == 2:
        two_way = f3.compare_two_jobs(job_list[0], job_list[1])
        multi_way = f3.compare_multiple_jobs(job_list)
        multi_way["pairwise_analysis"] = two_way
        return multi_way
    return f3.compare_multiple_jobs(job_list)


# =====================================================================
# 4. FORMULA 4: Candidate vs Candidate Head-to-Head & Cohort Benchmarking (RMS)
# =====================================================================
def compare_candidates(candidate_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compares 2 to 4 candidates across skills, experience, and merit score."""
    if len(candidate_list) == 2:
        return f4.compare_two_candidates(candidate_list[0], candidate_list[1])
    return f4.rank_candidate_cohort(candidate_list)


# =====================================================================
# 5. FORMULA 5: Job Seeker Feed Ranking (FRS) & Behavioural Loop (FRS★)
# =====================================================================
def calculate_feed_score(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Computes base Feed Ranking Score (Formula 5)."""
    return f5.compute_feed_job_score(candidate, job)


def apply_behavioural_ranking(
    base_frs: float,
    job: Dict[str, Any],
    saved_employer_ids: set,
    saved_categories: set,
    ignored_employer_counts: Dict[str, int]
) -> float:
    """
    Applies behavioral feedback adjustments (REQ-S16):
    - Save affinity: +10% for saved employer, +5% for saved sector
    - Ignore penalty: -25% if >= 3 jobs ignored from employer
    - Clamped to [0.0, 100.0]
    """
    adjusted_score = base_frs
    emp = job.get("company", "").strip().lower()
    cat = job.get("category", "").strip().lower()

    # Employer affinity boost
    if emp and emp in saved_employer_ids:
        adjusted_score *= 1.10

    # Sector affinity boost
    if cat and cat in saved_categories:
        adjusted_score *= 1.05

    # Ignored employer demotion
    if emp and ignored_employer_counts.get(emp, 0) >= 3:
        adjusted_score *= 0.75

    return round(min(100.0, max(0.0, adjusted_score)), 2)


# =====================================================================
# 6. FORMULA 6: Recruiter Talent Search Score (TSS)
# =====================================================================
def calculate_talent_search_score(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Computes Recruiter Talent Search Score (Formula 6)."""
    res = f6.compute_talent_search_score(candidate, job)
    if "overall_score" not in res and "talent_search_score" in res:
        res["overall_score"] = res["talent_search_score"]
    return res


# =====================================================================
# 7. DUAL LINE CHART MATHEMATICS (Spec 04 § 7, REQ-S09, REQ-S10)
# =====================================================================
def generate_projection_chart_data(
    base_match: float,
    base_gap: float,
    months_horizon: int = 12
) -> Dict[str, Any]:
    """
    Generates 12-month trajectory curves:
    - Match Progression SMF(t) = SMF_0 + (100 - SMF_0) * (1 - exp(-0.25 * t))
    - Gap Reduction GSI(t) = GSI_0 * exp(-0.30 * t)
    """
    labels = ["Current", "1 Mo", "2 Mos", "3 Mos", "4 Mos", "6 Mos", "9 Mos", "12 Mos"]
    t_points = [0, 1, 2, 3, 4, 6, 9, 12]

    match_series = []
    gap_series = []

    for t in t_points:
        # Match curve
        smf_t = base_match + (100.0 - base_match) * (1.0 - math.exp(-0.25 * t))
        match_series.append(round(min(100.0, smf_t), 1))

        # Gap curve
        gsi_t = base_gap * math.exp(-0.30 * t)
        gap_series.append(round(max(0.0, gsi_t), 1))

    return {
        "labels": labels,
        "time_points_months": t_points,
        "match_projection": match_series,
        "gap_reduction": gap_series,
        "asymptotic_match_target": 100.0,
        "projected_readiness_month_6": match_series[5]
    }
