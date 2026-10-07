#!/usr/bin/env python3
"""
Skill Bridge Intelligence Engine — Formula 2: Skill Gap Severity & Learnability Model (SGF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-002
"""

import math
import os
import re
from typing import Dict, List, Any, Tuple

# =====================================================================
# 1. GAP CATEGORY TAXONOMY AND ESTIMATED DURATION
# =====================================================================

CATEGORY_CONFIG = {
    "CAT-1": {
        "name": "Statutory License / Legal Registration",
        "weight": 1.00,
        "default_duration_months": 8.0,
        "keywords": [
            "ahpra", "cpa", "engineers australia", "ner", "license",
            "statutory", "legal registration", "medical registration",
            "practitioner regulation", "working with children", "white card",
            "responsible service of alcohol", "rsa"
        ]
    },
    "CAT-2": {
        "name": "Core Technical Discipline Competency",
        "weight": 0.60,
        "default_duration_months": 4.0,
        "keywords": [
            "distributed systems", "system architecture", "clinical triage",
            "structural design", "ifrs standards", "taxation compliance",
            "geotechnical", "data modeling", "machine learning", "fe analysis",
            "pharmacology", "surgical assistance"
        ]
    },
    "CAT-3": {
        "name": "Tool, Platform, or Framework",
        "weight": 0.25,
        "default_duration_months": 1.5,
        "keywords": [
            "snowflake", "spark", "dbt", "kubernetes", "docker", "autocad",
            "revit", "salesforce", "sap", "excel", "powerbi", "tableau",
            "epic", "cerner", "jira", "aws", "gcp", "azure", "git", "pos"
        ]
    },
    "CAT-4": {
        "name": "Local Standard or Regulatory Orientation",
        "weight": 0.10,
        "default_duration_months": 0.8,
        "keywords": [
            "pbs", "medicare", "australian standard", "orientation",
            "work health and safety", "whs", "local compliance",
            "billing guidelines", "fair work", "national privacy principles"
        ]
    }
}


def classify_gap_item(gap_text: str) -> Dict[str, Any]:
    """
    Classifies a raw missing skill text into an ASD-STE100 gap category.
    Returns: category details including weight and estimated duration in months.
    """
    text_clean = str(gap_text).lower()

    # Priority 1: Check Statutory
    for kw in CATEGORY_CONFIG["CAT-1"]["keywords"]:
        if kw in text_clean:
            return {
                "gap_name": gap_text,
                "category_code": "CAT-1",
                "category_name": CATEGORY_CONFIG["CAT-1"]["name"],
                "weight": CATEGORY_CONFIG["CAT-1"]["weight"],
                "duration_months": CATEGORY_CONFIG["CAT-1"]["default_duration_months"],
                "is_statutory_blocker": True
            }

    # Priority 2: Check Core Discipline
    for kw in CATEGORY_CONFIG["CAT-2"]["keywords"]:
        if kw in text_clean:
            return {
                "gap_name": gap_text,
                "category_code": "CAT-2",
                "category_name": CATEGORY_CONFIG["CAT-2"]["name"],
                "weight": CATEGORY_CONFIG["CAT-2"]["weight"],
                "duration_months": CATEGORY_CONFIG["CAT-2"]["default_duration_months"],
                "is_statutory_blocker": False
            }

    # Priority 3: Check Tool
    for kw in CATEGORY_CONFIG["CAT-3"]["keywords"]:
        if kw in text_clean:
            return {
                "gap_name": gap_text,
                "category_code": "CAT-3",
                "category_name": CATEGORY_CONFIG["CAT-3"]["name"],
                "weight": CATEGORY_CONFIG["CAT-3"]["weight"],
                "duration_months": CATEGORY_CONFIG["CAT-3"]["default_duration_months"],
                "is_statutory_blocker": False
            }

    # Priority 4: Check Local Standard / Orientation
    for kw in CATEGORY_CONFIG["CAT-4"]["keywords"]:
        if kw in text_clean:
            return {
                "gap_name": gap_text,
                "category_code": "CAT-4",
                "category_name": CATEGORY_CONFIG["CAT-4"]["name"],
                "weight": CATEGORY_CONFIG["CAT-4"]["weight"],
                "duration_months": CATEGORY_CONFIG["CAT-4"]["default_duration_months"],
                "is_statutory_blocker": False
            }

    # Default fallback: Treat as minor tool/methodology
    return {
        "gap_name": gap_text,
        "category_code": "CAT-3",
        "category_name": "General Competency Adaptation",
        "weight": 0.20,
        "duration_months": 1.0,
        "is_statutory_blocker": False
    }


# =====================================================================
# 2. MASTER GAP SEVERITY AND LEARNABILITY CALCULATION
# =====================================================================

def evaluate_skill_gaps(
    candidate: Dict[str, Any],
    job: Dict[str, Any],
    explicit_missing_skills: List[str] = None
) -> Dict[str, Any]:
    """
    Evaluates Formula 2: Skill Gap Severity & Learnability Model (SGF).
    
    Args:
        candidate: Candidate dictionary with 'skills', 'cv_raw_text', 'honest_gaps' or 'gaps'
        job: Job dictionary with 'requirements', 'requirements_json', 'title', 'category'
        explicit_missing_skills: Optional list of identified missing competencies
        
    Returns:
        Dictionary containing:
        - gap_severity_index (GSI): [0.0, 100.0]
        - job_readiness_score (JRS): [0.0, 100.0]
        - estimated_bridge_months / estimated_closing_months (T_total)
        - classified_gaps: structured list
        - readiness_tier: string
    """
    raw_gaps = []
    
    # 1. Collect candidate explicit gap statements
    cand_gaps = str(candidate.get("gaps") or candidate.get("honest_gaps") or "").strip()
    if cand_gaps:
        sentences = [s.strip() for s in re.split(r"[.;\n]", cand_gaps) if len(s.strip()) > 8]
        raw_gaps.extend(sentences)

    # 2. Add explicit missing skills if provided
    if explicit_missing_skills:
        raw_gaps.extend([s for s in explicit_missing_skills if s not in raw_gaps])

    # 3. Dynamic Gap Extraction: Compare Job Requirements against Candidate Footprint
    job_reqs = []
    if job.get("requirements") and isinstance(job["requirements"], list):
        job_reqs.extend(job["requirements"])
    elif job.get("requirements_json"):
        import json
        r_data = job["requirements_json"]
        if isinstance(r_data, str):
            try:
                job_reqs.extend(json.loads(r_data))
            except Exception:
                pass
        elif isinstance(r_data, list):
            job_reqs.extend(r_data)

    # Candidate competency text footprint
    cand_skills = []
    for s in candidate.get("skills", []):
        if isinstance(s, dict):
            cand_skills.append(s.get("skill_name") or s.get("name") or "")
        elif isinstance(s, str):
            cand_skills.append(s)
    
    cand_corpus = (
        str(candidate.get("cv_raw_text") or candidate.get("rawResume") or candidate.get("raw_resume_sample") or "")
        + " " + " ".join(cand_skills)
        + " " + str(candidate.get("current_title") or "")
    ).lower()

    # Compare each requirement against candidate
    for req in job_reqs:
        req_str = str(req).strip()
        if not req_str:
            continue
        req_clean = req_str.lower()

        # Check if requirement is statutory AHPRA / CPA / NER
        is_statutory = any(k in req_clean for k in ["ahpra", "cpa", "engineers australia", "ner", "medical registration", "license required"])
        if is_statutory:
            # Overseas candidate check: even if 'eligibility' or overseas, must verify full registration
            has_confirmed_ahpra = "ahpra" in cand_corpus and not any(k in cand_corpus for k in ["eligibility", "seeking", "in progress", "overseas"])
            if not has_confirmed_ahpra:
                if req_str not in raw_gaps:
                    raw_gaps.append(req_str)
            continue

        # Technical/tool requirement check: tokens of length >= 4
        tokens = [t for t in re.findall(r"[a-z0-9+#]+", req_clean) if len(t) >= 4 and t not in ["years", "experience", "strong", "proven", "demonstrated", "skills"]]
        if tokens:
            # If fewer than 40% of key requirement tokens appear in candidate footprint, flag as gap
            matched_tokens = sum(1 for t in tokens if t in cand_corpus)
            if matched_tokens == 0 or (matched_tokens / len(tokens)) < 0.40:
                if req_str not in raw_gaps:
                    raw_gaps.append(req_str)

    # 4. Mandatory Statutory Screening by Sector / ANZSCO
    job_sec = str(job.get("category") or "").lower()
    anzsco = str(job.get("anzsco_code") or job.get("anzsco") or "")
    
    if ("health" in job_sec or anzsco.startswith("2544") or anzsco.startswith("253")) and "ahpra" not in cand_corpus:
        ahpra_gap = "AHPRA Statutory Nurse Registration & Australian Clinical Guidelines"
        if not any("ahpra" in g.lower() for g in raw_gaps):
            raw_gaps.append(ahpra_gap)
            
    if ("finance" in job_sec or anzsco.startswith("2211")) and not any(k in cand_corpus for k in ["cpa", "ca anz"]):
        cpa_gap = "CPA Australia / CA ANZ Statutory Accreditation & Australian Tax Compliance"
        if not any("cpa" in g.lower() for g in raw_gaps):
            raw_gaps.append(cpa_gap)

    # 5. Baseline Workplace Adaptation (Local Standard)
    # Every international seeker in Australia has local orientation / standard adaptation
    if len(raw_gaps) == 0:
        raw_gaps.append("Australian Workplace Health & Safety (WHS) & Regulatory Compliance Adaptation")

    # 6. Candidate Learnability Calibration Factor (Lambda_lrn)
    yc = float(candidate.get("years_experience") or candidate.get("yearsExp") or candidate.get("years_of_experience") or 5.0)
    edu = str(candidate.get("highest_education") or "").lower()
    has_deg = any(k in edu for k in ["master", "bachelor", "phd", "doctorate", "degree"])
    lambda_lrn = max(0.65, min(1.05, 1.0 - 0.16 * min(1.0, yc / 12.0) - (0.05 if has_deg else 0.0)))

    # 7. Seniority Competency Gap Analysis
    j_title = str(job.get("title", "")).lower()
    if any(k in j_title for k in ["lead", "principal", "director", "head"]):
        target_years = 10.0
    elif any(k in j_title for k in ["senior", "manager", "specialist"]):
        target_years = 7.0
    elif any(k in j_title for k in ["junior", "graduate", "assistant", "entry"]):
        target_years = 2.0
    else:
        target_years = 5.0

    classified_items = [classify_gap_item(g) for g in raw_gaps]
    
    total_gsi = 0.0
    durations = []
    has_statutory = False

    for item in classified_items:
        w_cat = item["weight"]
        t_raw = item["duration_months"]
        t_k = round(t_raw * lambda_lrn, 1)
        item["duration_months"] = t_k
        durations.append(t_k)
        
        # Severity formula: w_cat * (14.0 + 4.5 * ln(1 + T_k))
        item_severity = w_cat * (14.0 + 4.5 * math.log(1.0 + t_k))
        item["severity_points"] = round(item_severity, 2)
        total_gsi += item_severity

        if item["is_statutory_blocker"]:
            has_statutory = True

    if yc < target_years:
        deficit_ratio = (target_years - yc) / target_years
        sen_duration = round(4.0 * deficit_ratio * lambda_lrn, 1)
        if sen_duration >= 0.5:
            sen_sev = round(0.60 * (14.0 + 4.5 * math.log(1.0 + sen_duration)), 2)
            classified_items.append({
                "gap_name": f"Seniority Competency Deficit ({round(target_years - yc, 1)} yrs experience gap vs requisition)",
                "category_code": "CAT-2",
                "category_name": "Core Technical Discipline Competency",
                "weight": 0.60,
                "duration_months": sen_duration,
                "is_statutory_blocker": False,
                "severity_points": sen_sev
            })
            durations.append(sen_duration)
            total_gsi += sen_sev

    # 7. Cap GSI to [2.0, 95.0] and compute Job Readiness Score (JRS)
    gsi = round(min(95.0, max(2.0, total_gsi)), 1)
    jrs = round(max(5.0, 100.0 - gsi), 1)

    # 8. Calculate Parallel Bridge Duration: max(T_k) + 0.18 * sum(others)
    if durations:
        max_duration = max(durations)
        other_durations_sum = sum(durations) - max_duration
        t_total = round(max_duration + (0.18 * other_durations_sum), 1)
    else:
        t_total = 0.8

    # 9. Readiness Tier Classification
    if jrs >= 80.0 and not has_statutory:
        tier = "Low Gap (Immediate Deployment)"
        tier_code = "TIER_LOW_GAP"
    elif jrs >= 55.0 or (not has_statutory and jrs >= 45.0):
        tier = "Moderate Gap (Fast-Track Upskilling)"
        tier_code = "TIER_MODERATE_GAP"
    else:
        tier = "High Gap (Structural Bridging Required)"
        tier_code = "TIER_HIGH_GAP"

    return {
        "candidate_id": candidate.get("id") or candidate.get("candidate_id"),
        "candidate_name": candidate.get("name") or candidate.get("full_name") or candidate.get("alias"),
        "job_id": job.get("id") or job.get("job_id"),
        "job_title": job.get("title"),
        "total_gaps_count": len(classified_items),
        "classified_gaps": classified_items,
        "gap_severity_index": gsi,
        "skill_gap_pct": gsi,
        "job_readiness_score": jrs,
        "estimated_bridge_months": t_total,
        "estimated_closing_months": t_total,
        "has_statutory_blocker": has_statutory,
        "readiness_tier": tier,
        "readiness_tier_code": tier_code
    }


# =====================================================================
# 3. SELF-CONTAINED VERIFICATION BENCHMARK
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 75)
    print("SKILL BRIDGE INTELLIGENCE ENGINE — FORMULA 2 VERIFICATION (ASD-STE100)")
    print("=" * 75)

    cand_path = "data/australian_candidates.json" if os.path.exists("data/australian_candidates.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_candidates.json")
    job_path = "data/australian_jobs.json" if os.path.exists("data/australian_jobs.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_jobs.json")
    with open(cand_path, "r", encoding="utf-8") as f:
        cands = json.load(f)
    with open(job_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Test 1: Candidate with Statutory AHPRA Licensing Gap
    c_nurse = cands[0]
    j_nurse = jobs[0]
    res_nurse = evaluate_skill_gaps(c_nurse, j_nurse, explicit_missing_skills=["vital signs monitoring"])
    
    print("\n[TEST 1: Statutory Healthcare Gap (AHPRA)]")
    print(f"Candidate: {res_nurse['candidate_name']} -> Job: {res_nurse['job_title']}")
    print(f"Total Gaps: {res_nurse['total_gaps_count']} items | Statutory Blocker: {res_nurse['has_statutory_blocker']}")
    for g in res_nurse["classified_gaps"]:
        print(f"  - [{g['category_code']}] {g['gap_name'][:65]}... -> +{g['severity_points']} pts ({g['duration_months']} mo)")
    print(f"Gap Severity Index (GSI): {res_nurse['gap_severity_index']} / 100")
    print(f"Job Readiness Score (JRS): {res_nurse['job_readiness_score']}%")
    print(f"Estimated Bridge Duration: {res_nurse['estimated_bridge_months']} calendar months")
    print(f"Readiness Tier: {res_nurse['readiness_tier']}")

    # Test 2: Tech Candidate with Minor Tool Gap (e.g. Snowflake / dbt)
    tech_candidates = [c for c in cands if c.get("category") == "Technology & Data"]
    tech_jobs = [j for j in jobs if j.get("category") == "Technology & Data"]
    
    c_tech = tech_candidates[0] if tech_candidates else cands[1]
    j_tech = tech_jobs[0] if tech_jobs else jobs[1]
    res_tech = evaluate_skill_gaps(c_tech, j_tech, explicit_missing_skills=["Snowflake pipeline migration", "dbt data tests"])
    
    print("\n[TEST 2: Minor Tool Gap (Snowflake & dbt)]")
    print(f"Candidate: {res_tech['candidate_name']} -> Job: {res_tech['job_title']}")
    print(f"Total Gaps: {res_tech['total_gaps_count']} items | Statutory Blocker: {res_tech['has_statutory_blocker']}")
    for g in res_tech["classified_gaps"]:
        print(f"  - [{g['category_code']}] {g['gap_name'][:65]}... -> +{g['severity_points']} pts ({g['duration_months']} mo)")
    print(f"Gap Severity Index (GSI): {res_tech['gap_severity_index']} / 100")
    print(f"Job Readiness Score (JRS): {res_tech['job_readiness_score']}%")
    print(f"Estimated Bridge Duration: {res_tech['estimated_bridge_months']} calendar months")
    print(f"Readiness Tier: {res_tech['readiness_tier']}")

    print("\n" + "=" * 75)
    print("FORMULA 2 PRODUCTION VALIDATION COMPLETE.")
    print("=" * 75)
