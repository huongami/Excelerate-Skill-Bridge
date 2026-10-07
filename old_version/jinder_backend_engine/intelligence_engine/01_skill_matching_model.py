#!/usr/bin/env python3
"""
Skill Bridge Intelligence Engine — Formula 1: Candidate vs ANZSCO Skill Match Model (SMF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-001
"""

import math
import os
import re
from typing import Dict, List, Any, Tuple, Set

# =====================================================================
# 1. ABS ANZSCO OCCUPATIONAL BENCHMARK TAXONOMY & CORE COMPETENCIES
# =====================================================================

ANZSCO_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "254411": {
        "title": "Registered Nurse",
        "sector": "Healthcare & Nursing",
        "skill_level": 1,
        "core_skills": [
            "clinical triage", "patient assessment", "infection control",
            "medication administration", "care planning", "acute care",
            "wound management", "vital signs monitoring", "clinical documentation", "patient care"
        ],
        "statutory_requirements": ["AHPRA Registration"],
        "transferable_methodologies": [
            "sop compliance", "cross-functional communication",
            "crisis stabilization", "quality assurance", "multidisciplinary coordination"
        ]
    },
    "261313": {
        "title": "Software Engineer",
        "sector": "Technology & Data",
        "skill_level": 1,
        "core_skills": [
            "software development", "python", "sql", "data pipelines",
            "system architecture", "api design", "database management",
            "version control", "unit testing", "debugging", "cloud infrastructure"
        ],
        "statutory_requirements": [],
        "transferable_methodologies": [
            "agile", "scrum", "ci cd", "code review", "system documentation", "stakeholder collaboration"
        ]
    },
    "221111": {
        "title": "General Accountant",
        "sector": "Finance & Accounting",
        "skill_level": 1,
        "core_skills": [
            "financial reporting", "general ledger", "balance sheet reconciliation",
            "taxation compliance", "budget forecasting", "variance analysis",
            "ifrs standards", "audit preparation", "cash flow management"
        ],
        "statutory_requirements": ["CPA / CA Australia accreditation"],
        "transferable_methodologies": [
            "internal controls", "financial governance", "executive reporting", "risk management"
        ]
    },
    "233211": {
        "title": "Civil Engineer",
        "sector": "Engineering & Construction",
        "skill_level": 1,
        "core_skills": [
            "structural design", "autocad", "civil infrastructure",
            "site supervision", "fe analysis", "construction management",
            "geotechnical evaluation", "bills of quantities", "engineering drawings"
        ],
        "statutory_requirements": ["Engineers Australia Stage 1 / NER"],
        "transferable_methodologies": [
            "work health and safety", "project management", "quality assurance", "vendor coordination"
        ]
    },
    "225113": {
        "title": "Marketing Specialist",
        "sector": "Marketing & Communications",
        "skill_level": 1,
        "core_skills": [
            "digital marketing", "campaign management", "seo", "sem",
            "content strategy", "brand positioning", "market research",
            "google analytics", "social media strategy", "conversion optimization"
        ],
        "statutory_requirements": [],
        "transferable_methodologies": [
            "stakeholder management", "budget management", "cross-functional collaboration", "kpi reporting"
        ]
    },
    "511112": {
        "title": "Program or Project Administrator",
        "sector": "Operations & Administration",
        "skill_level": 3,
        "core_skills": [
            "project administration", "workflow coordination", "schedule tracking",
            "resource allocation", "records management", "procurement support",
            "meeting facilitation", "status reporting", "documentation control"
        ],
        "statutory_requirements": [],
        "transferable_methodologies": [
            "sop adherence", "stakeholder coordination", "process improvement", "office governance"
        ]
    },
    "141111": {
        "title": "Cafe or Restaurant Manager",
        "sector": "Hospitality & Service",
        "skill_level": 2,
        "core_skills": [
            "hospitality operations", "staff rostering", "inventory control",
            "food safety standards", "customer service management", "vendor negotiation",
            "pos management", "revenue optimization", "cost of goods sold"
        ],
        "statutory_requirements": ["Responsible Service of Alcohol", "Food Safety Supervisor"],
        "transferable_methodologies": [
            "team leadership", "conflict resolution", "haccp compliance", "cash handling"
        ]
    },
    "312211": {
        "title": "Civil Engineering Draftsperson / Supply Logistics",
        "sector": "Supply Chain & Logistics",
        "skill_level": 2,
        "core_skills": [
            "supply chain operations", "logistics tracking", "warehouse management",
            "freight forwarding", "inventory replenishment", "customs documentation",
            "erp systems", "distribution planning", "fleet coordination"
        ],
        "statutory_requirements": [],
        "transferable_methodologies": [
            "vendor compliance", "continuous improvement", "cost control", "cross-docking"
        ]
    }
}

DEFAULT_BENCHMARK_YEARS: Dict[int, float] = {
    1: 5.0,
    2: 3.0,
    3: 2.0,
    4: 1.0,
    5: 0.5
}

COMMON_SKILL_IDF: Dict[str, float] = {
    "snowflake": 2.8, "spark": 2.6, "pyspark": 2.7, "dbt": 2.5, "kubernetes": 2.4,
    "ahpra": 3.0, "clinical triage": 2.9, "autocad": 2.4, "cpa": 2.7, "ifrs": 2.6,
    "seo": 2.1, "google analytics": 2.2, "logistics": 2.0, "python": 1.8, "sql": 1.7,
    "data analysis": 1.6, "financial reporting": 1.9, "patient care": 2.1, "supply chain": 1.9,
    "agile": 1.4, "scrum": 1.5, "project management": 1.3, "stakeholder management": 1.4,
    "quality assurance": 1.5, "compliance": 1.4, "sop": 1.6, "leadership": 1.3
}


# =====================================================================
# 2. TOKENIZATION AND EXTRACTION UTILITIES
# =====================================================================

def extract_candidate_text_corpus(candidate: Dict[str, Any]) -> str:
    """Aggregates all candidate textual records into a single clean corpus string."""
    parts = []
    skills = candidate.get("skills", [])
    if isinstance(skills, list):
        for s in skills:
            if isinstance(s, dict):
                parts.append(f"{s.get('name', '')} {s.get('skill_name', '')} {s.get('evidence', '')} {s.get('evidence_quote', '')}")
            else:
                parts.append(str(s))
    
    parts.append(str(candidate.get("direct_skills", "")))
    parts.append(str(candidate.get("transferable_skills", "")))
    parts.append(str(candidate.get("skill_evidence_excerpts", "")))
    parts.append(str(candidate.get("rawResume", "")))
    parts.append(str(candidate.get("raw_resume_sample", "")))
    parts.append(str(candidate.get("cv_raw_text", "")))
    parts.append(str(candidate.get("original_job_title", "")))
    parts.append(str(candidate.get("current_title", "")))
    parts.append(str(candidate.get("originRole", "")))
    parts.append(str(candidate.get("highest_education", "")))
    
    return " ".join(parts).lower()


def tokenize_text(text: str) -> Set[str]:
    """Extracts lowercase tokens, bigrams, and clean words."""
    clean = re.sub(r"[^\w\s-]", " ", str(text).lower()).strip()
    words = clean.split()
    tokens = set()
    for w in words:
        if len(w) >= 2:
            tokens.add(w)
    for i in range(len(words) - 1):
        tokens.add(f"{words[i]} {words[i+1]}")
    return tokens


# =====================================================================
# 3. SUB-METRIC CALCULATION FUNCTIONS (ASD-STE100 SPECIFICATION)
# =====================================================================

def calculate_taxonomy_tree_score(cand_code: str, target_code: str) -> float:
    """Calculates S_tree based on ABS ANZSCO 6-digit hierarchical tree distance."""
    c_m = re.search(r"\d{4,6}", str(cand_code or ""))
    t_m = re.search(r"\d{4,6}", str(target_code or ""))
    c = c_m.group(0) if c_m else str(cand_code or "").strip()
    t = t_m.group(0) if t_m else str(target_code or "").strip()

    if not c or not t:
        return 10.0

    if c == t and len(c) >= 6:
        return 100.0
    if len(c) >= 4 and len(t) >= 4 and c[:4] == t[:4]:
        return 85.0
    if len(c) >= 3 and len(t) >= 3 and c[:3] == t[:3]:
        return 65.0
    if len(c) >= 2 and len(t) >= 2 and c[:2] == t[:2]:
        return 40.0
    if len(c) >= 1 and len(t) >= 1 and c[0] == t[0]:
        return 20.0
    return 10.0


def calculate_competency_overlap(cand_corpus: str, required_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Evaluates candidate corpus against standard required competencies.
    Returns: (Score in [0.0, 100.0], List of matched skills, List of missing skills)
    """
    if not required_skills:
        return 75.0, [], []

    cand_tokens = tokenize_text(cand_corpus)
    matched = []
    missing = []

    for req in required_skills:
        req_clean = req.lower().strip()
        req_words = req_clean.split()
        
        # Exact phrase or all component words present in candidate text
        if req_clean in cand_corpus or all(w in cand_tokens for w in req_words):
            matched.append(req)
        elif any(w in cand_tokens for w in req_words if len(w) > 3):
            # Partial soft-match for significant word root
            matched.append(req)
        else:
            missing.append(req)

    # Weighted scoring with IDF
    num = sum(COMMON_SKILL_IDF.get(s, 1.5) for s in matched)
    den = sum(COMMON_SKILL_IDF.get(s, 1.5) for s in required_skills)
    
    score = (num / den * 100.0) if den > 0 else 50.0
    return round(min(100.0, max(0.0, score)), 1), matched, missing


def calculate_experience_multiplier(years_exp: float, skill_level: int) -> float:
    """Calculates Phi(Y_C, L_O) experience calibration multiplier with realistic smooth variance."""
    req_years = DEFAULT_BENCHMARK_YEARS.get(skill_level, 5.0)
    years = max(0.5, float(years_exp or 1.0))
    ratio = years / req_years
    multiplier = 0.80 + 0.15 * math.log(1.0 + ratio) + 0.05 * min(2.0, ratio)
    return round(min(1.15, max(0.75, multiplier)), 3)


# =====================================================================
# 4. MASTER SKILL MATCH FUNCTION (SMF)
# =====================================================================

def evaluate_skill_match(
    candidate: Dict[str, Any],
    target_occupation_code_or_dict: Any,
    weights: Tuple[float, float, float] = (0.25, 0.50, 0.25)
) -> Dict[str, Any]:
    """
    Evaluates Formula 1: Candidate vs ANZSCO Skill Match Score (SMF).
    Follows ASD-STE100 specification IE-SPEC-001.
    """
    w1, w2, w3 = weights
    assert abs(w1 + w2 + w3 - 1.0) < 1e-4, "Weights must sum to 1.00"

    # Resolve target occupation profile
    if isinstance(target_occupation_code_or_dict, dict):
        target_dict = target_occupation_code_or_dict
        target_code = str(target_dict.get("anzsco_code") or target_dict.get("anzscoCode") or "")
    else:
        target_code = str(target_occupation_code_or_dict).strip()
        target_dict = ANZSCO_TAXONOMY.get(target_code, {})

    target_code_clean = (re.search(r"\d{6}", target_code) or re.search(r"\d{4}", target_code))
    target_code_num = target_code_clean.group(0) if target_code_clean else target_code

    target_profile = ANZSCO_TAXONOMY.get(target_code_num, target_dict)
    target_title = target_profile.get("title") or target_profile.get("occupation_title") or "Certified Occupation"
    skill_level = target_profile.get("skill_level", 1)
    core_skills = target_profile.get("core_skills") or target_dict.get("required_skills", [])
    trans_skills = target_profile.get("transferable_methodologies", [
        "sop compliance", "quality assurance", "stakeholder management", "team leadership"
    ])

    cand_code = str(candidate.get("anzscoCode") or candidate.get("anzsco_code") or candidate.get("target_anzsco_code") or "")
    years_exp = float(candidate.get("yearsExp") or candidate.get("years_of_experience") or candidate.get("years_experience") or 0.0)

    # 1. Compute Sub-Metrics
    s_tree = calculate_taxonomy_tree_score(cand_code, target_code)

    cand_corpus = extract_candidate_text_corpus(candidate)
    s_direct, matched_core, missing_core = calculate_competency_overlap(cand_corpus, core_skills)
    s_trans, matched_trans, missing_trans = calculate_competency_overlap(cand_corpus, trans_skills)
    phi = calculate_experience_multiplier(years_exp, skill_level)

    # 2. Master Composite Equation
    base_composite = (w1 * s_tree) + (w2 * s_direct) + (w3 * s_trans)
    final_score = min(100.0, base_composite * phi)
    final_score = round(max(0.0, final_score), 1)

    # 3. Tier Classification
    if final_score >= 85.0:
        tier = "Direct Industry Alignment"
        tier_code = "TIER_1_DIRECT"
    elif final_score >= 70.0:
        tier = "Transferable Cross-Sector Capability"
        tier_code = "TIER_2_TRANSFERABLE"
    else:
        tier = "Emerging Career Bridge"
        tier_code = "TIER_3_BRIDGE"

    return {
        "candidate_id": candidate.get("id") or candidate.get("candidate_id"),
        "candidate_name": candidate.get("name") or candidate.get("full_name") or candidate.get("alias"),
        "target_anzsco_code": target_code_num,
        "target_anzsco_title": target_title,
        "sub_metrics": {
            "s_tree_taxonomy": round(s_tree, 1),
            "s_direct_competency": round(s_direct, 1),
            "s_trans_methodology": round(s_trans, 1),
            "phi_experience_multiplier": round(phi, 3)
        },
        "competency_breakdown": {
            "matched_core_skills": matched_core,
            "missing_core_skills": missing_core,
            "matched_transferable_skills": matched_trans,
            "missing_transferable_skills": missing_trans,
            "statutory_requirements": target_profile.get("statutory_requirements", [])
        },
        "base_composite_score": round(base_composite, 1),
        "final_match_score": final_score,
        "overall_score": final_score,
        "match_tier": tier,
        "match_tier_code": tier_code,
        "is_direct_ready": final_score >= 85.0
    }


# =====================================================================
# 5. SELF-CONTAINED VERIFICATION BENCHMARK
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 75)
    print("SKILL BRIDGE INTELLIGENCE ENGINE — FORMULA 1 VERIFICATION (ASD-STE100)")
    print("=" * 75)

    cand_path = "data/australian_candidates.json" if os.path.exists("data/australian_candidates.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_candidates.json")
    with open(cand_path, "r", encoding="utf-8") as f:
        cands = json.load(f)

    # Benchmark Candidate 1: Minh Tuan Nguyen (Healthcare Nurse 254411)
    c0 = cands[0]
    res_direct = evaluate_skill_match(c0, "254411")
    print("\n[BENCHMARK 1: Direct Sector Alignment]")
    print(f"Candidate: {res_direct['candidate_name']} ({c0['anzscoCode']}) -> Target: {res_direct['target_anzsco_title']} ({res_direct['target_anzsco_code']})")
    print(f"Sub-metrics: S_tree={res_direct['sub_metrics']['s_tree_taxonomy']}%, S_direct={res_direct['sub_metrics']['s_direct_competency']}%, S_trans={res_direct['sub_metrics']['s_trans_methodology']}%, Phi={res_direct['sub_metrics']['phi_experience_multiplier']}")
    print(f"Matched Skills ({len(res_direct['competency_breakdown']['matched_core_skills'])}): {res_direct['competency_breakdown']['matched_core_skills']}")
    print(f"Missing Skills: {res_direct['competency_breakdown']['missing_core_skills']}")
    print(f"Final Score: {res_direct['final_match_score']}% | Tier: {res_direct['match_tier']}")

    # Benchmark Candidate 2: Same Candidate against Divergent Tech ANZSCO (261313 Software Engineer)
    res_divergent = evaluate_skill_match(c0, "261313")
    print("\n[BENCHMARK 2: Cross-Sector Divergent Test]")
    print(f"Candidate: {res_divergent['candidate_name']} -> Target: {res_divergent['target_anzsco_title']} ({res_divergent['target_anzsco_code']})")
    print(f"Sub-metrics: S_tree={res_divergent['sub_metrics']['s_tree_taxonomy']}%, S_direct={res_divergent['sub_metrics']['s_direct_competency']}%, S_trans={res_divergent['sub_metrics']['s_trans_methodology']}%, Phi={res_divergent['sub_metrics']['phi_experience_multiplier']}")
    print(f"Final Score: {res_divergent['final_match_score']}% | Tier: {res_divergent['match_tier']}")

    print("\n" + "=" * 75)
    print("FORMULA 1 PRODUCTION VALIDATION COMPLETE.")
    print("=" * 75)
