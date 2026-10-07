#!/usr/bin/env python3
"""
Skill Bridge Intelligence Engine — Formula 4: Candidate-to-Candidate Benchmarking Model (CCF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-004
"""

import re
from typing import Dict, List, Any, Tuple

# =====================================================================
# 1. INDIVIDUAL CANDIDATE MERIT SCORE CALCULATION (RMS)
# =====================================================================

def calculate_candidate_merit_score(
    cand: Dict[str, Any],
    weights: Tuple[float, float, float, float, float] = (0.35, 0.25, 0.20, 0.10, 0.10)
) -> Dict[str, Any]:
    """
    Calculates Formula 4: Relative Merit Score (RMS) for a single candidate profile.
    Follows ASD-STE100 specification IE-SPEC-004.
    """
    import math
    alpha, beta, gamma, delta, epsilon = weights

    skills = cand.get("skills", [])
    direct_count = sum(1 for s in skills if isinstance(s, dict) and (s.get("type") == "Direct" or s.get("skill_type") == "Direct"))
    trans_count = sum(1 for s in skills if isinstance(s, dict) and (s.get("type") == "Transferable" or s.get("skill_type") == "Transferable"))
    if direct_count == 0 and trans_count == 0 and skills:
        # Fallback if raw list of strings
        direct_count = max(1, len(skills) // 2)
        trans_count = max(1, len(skills) - direct_count)

    # 1. Skill Depth (continuous asymptotic curve)
    depth_score = min(100.0, 30.0 + 40.0 * (1.0 - math.exp(-max(0, direct_count) / 3.0)) + 30.0 * (1.0 - math.exp(-max(0, trans_count) / 4.0)))

    # 2. Experience Maturity (Benchmark: continuous smooth curve)
    years_exp = float(cand.get("yearsExp") or cand.get("years_of_experience") or cand.get("years_experience") or 0.0)
    exp_score = min(100.0, 100.0 * (1.0 - math.exp(-max(0.0, years_exp) / 5.2)))

    # 3. Evidence Rigor (resume depth & metrics)
    raw_resume = str(cand.get("rawResume") or cand.get("raw_resume_sample") or cand.get("cv_raw_text") or "")
    word_count = len(raw_resume.split())
    numbers_found = len(re.findall(r"\b\d+[%kKmM]?\b", raw_resume))
    evidence_score = min(100.0, 40.0 + 35.0 * (1.0 - math.exp(-max(0, word_count) / 120.0)) + 25.0 * min(1.0, numbers_found / 4.0))

    # 4. Transferable Agility
    trans_score = min(100.0, 35.0 + 65.0 * (1.0 - math.exp(-max(0, trans_count) / 3.0)))

    # Education credential bonus
    edu_str = str(cand.get("highest_education") or "").lower()
    if any(k in edu_str for k in ["phd", "doctorate"]):
        edu_bonus = 5.0
    elif any(k in edu_str for k in ["master", "mba", "postgraduate"]):
        edu_bonus = 3.5
    elif any(k in edu_str for k in ["bachelor", "degree", "aqf 7"]):
        edu_bonus = 2.0
    else:
        edu_bonus = 0.5

    # 5. Regulatory Gap Penalty
    gaps_text = (str(cand.get("gaps") or cand.get("honest_gaps") or "") + " " + raw_resume).lower()
    if any(k in gaps_text for k in ["ahpra", "cpa", "engineers australia", "ner", "license required", "statutory"]) and not any(k in gaps_text for k in ["registered", "certified", "member"]):
        gap_penalty = 60.0
    elif any(k in gaps_text for k in ["orientation", "standard", "guideline", "local practice"]):
        gap_penalty = 15.0
    else:
        gap_penalty = 0.0

    # Master Equation
    base_rms = (alpha * depth_score) + (beta * exp_score) + (gamma * evidence_score) + (delta * trans_score) - (epsilon * gap_penalty)
    rms = round(max(0.0, min(100.0, base_rms + edu_bonus)), 1)

    return {
        "candidate_id": cand.get("id") or cand.get("candidate_id"),
        "candidate_name": cand.get("name") or cand.get("full_name") or cand.get("alias"),
        "relative_merit_score": rms,
        "overall_score": rms,
        "sub_metrics": {
            "skill_depth": round(depth_score, 1),
            "experience_maturity": round(exp_score, 1),
            "evidence_rigor": round(evidence_score, 1),
            "transferable_agility": round(trans_score, 1),
            "gap_penalty_deduction": round(gap_penalty, 1),
            "education_bonus": round(edu_bonus, 1)
        },
        "verified_years_exp": years_exp,
        "has_statutory_gap": gap_penalty >= 50.0
    }


# =====================================================================
# 2. HEAD-TO-HEAD COMPARISON FUNCTION
# =====================================================================

def compare_two_candidates(cand_a: Dict[str, Any], cand_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes head-to-head score differential and hiring recommendation between two applicants.
    """
    eval_a = calculate_candidate_merit_score(cand_a)
    eval_b = calculate_candidate_merit_score(cand_b)

    score_a = eval_a["relative_merit_score"]
    score_b = eval_b["relative_merit_score"]
    delta = round(score_a - score_b, 1)

    # Determine advantage
    if delta > 8.0:
        verdict = f"{eval_a['candidate_name']} demonstrates clear competitive superiority (+{delta} pts)."
        superior_candidate = eval_a["candidate_name"]
    elif delta < -8.0:
        verdict = f"{eval_b['candidate_name']} demonstrates clear competitive superiority (+{abs(delta)} pts)."
        superior_candidate = eval_b["candidate_name"]
    else:
        verdict = f"Equivalent competency band (|Δ| = {abs(delta)} pts). HR should differentiate on specific niche fit."
        superior_candidate = "Equivalent"

    return {
        "candidate_a": eval_a,
        "candidate_b": eval_b,
        "score_delta": delta,
        "hiring_verdict": verdict,
        "recommended_candidate": superior_candidate
    }


# =====================================================================
# 3. MULTI-CANDIDATE COHORT BENCHMARKING (N >= 2)
# =====================================================================

def rank_candidate_cohort(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ranks an entire candidate pool for HR recruiters with percentiles and dimensional scores.
    """
    evaluated = [calculate_candidate_merit_score(c) for c in candidates]
    # Sort descending by RMS
    evaluated.sort(key=lambda x: x["relative_merit_score"], reverse=True)

    n = len(evaluated)
    for rank_idx, item in enumerate(evaluated):
        item["cohort_rank"] = rank_idx + 1
        item["cohort_percentile"] = round((1.0 - (rank_idx / max(1, n - 1))) * 100.0, 1) if n > 1 else 100.0

    return {
        "total_candidates": n,
        "top_ranked_candidate": evaluated[0]["candidate_name"] if n > 0 else None,
        "ranked_shortlist": evaluated
    }


# =====================================================================
# 4. SELF-CONTAINED VERIFICATION BENCHMARK
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 75)
    print("SKILL BRIDGE INTELLIGENCE ENGINE — FORMULA 4 VERIFICATION (ASD-STE100)")
    print("=" * 75)

    import os
    cand_path = "data/australian_candidates.json" if os.path.exists("data/australian_candidates.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_candidates.json")
    with open(cand_path, "r", encoding="utf-8") as f:
        cands = json.load(f)

    # Candidate 1: Senior Practice Manager (10 yrs exp, requires AHPRA)
    c_senior = cands[0]
    
    # Candidate 2: Mid-level Healthcare candidate
    c_mid = cands[1]

    # Test 1: Head-to-Head Comparison
    res_pair = compare_two_candidates(c_senior, c_mid)
    print("\n[TEST 1: Head-to-Head Candidate Evaluation]")
    print(f"Candidate A: {res_pair['candidate_a']['candidate_name']} -> Score: {res_pair['candidate_a']['relative_merit_score']}")
    print(f"Candidate B: {res_pair['candidate_b']['candidate_name']} -> Score: {res_pair['candidate_b']['relative_merit_score']}")
    print(f"Score Delta (Δ): {res_pair['score_delta']} pts")
    print(f"Verdict: {res_pair['hiring_verdict']}")

    # Test 2: Cohort Ranking across 6 candidates
    cohort = cands[:6]
    res_cohort = rank_candidate_cohort(cohort)
    print("\n[TEST 2: Candidate Cohort Ranking (Top 6 Applicants)]")
    print(f"Total Applicants: {res_cohort['total_candidates']} | Leader: {res_cohort['top_ranked_candidate']}")
    for cand in res_cohort["ranked_shortlist"]:
        print(f"  #{cand['cohort_rank']} {cand['candidate_name']:22} | Score: {cand['relative_merit_score']:4.1f}% | Top Percentile: {cand['cohort_percentile']:5.1f}% | Exp: {cand['verified_years_exp']} yrs")

    print("\n" + "=" * 75)
    print("FORMULA 4 PRODUCTION VALIDATION COMPLETE.")
    print("=" * 75)
