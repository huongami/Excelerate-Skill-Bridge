"""
On-Premises Capability & Gap Extraction Engine.
Dissects professional resume text into:
- Direct Technical Competencies (explicit match)
- Transferable Foundational Skills (methodology, leadership, analytics)
- Honest Gaps (statutory accreditation, local Australian compliance standards)
"""

import re

GAP_KNOWLEDGE_BASE = {
    "Healthcare & Nursing": "Requires AHPRA (Australian Health Practitioner Regulation Agency) registration and bridging course on Australian PBS/Medicare billing guidelines.",
    "Finance & Accounting": "Needs CPA Australia / CA ANZ conversion assessment, and hands-on familiarity with Australian GST, PAYG withholding, and ATO portal reporting.",
    "Marketing & Communications": "Needs acclimatization to the Australian cultural consumer landscape, local Australian media networks, and ACMA spam/privacy compliance regulations.",
    "Supply Chain & Logistics": "Requires familiarity with Australian domestic freight lanes (National Freight and Supply Chain Strategy) and Australian Border Force customs import/export documentation.",
    "Engineering & Construction": "Requires Engineers Australia Stage 1 CDR assessment, and familiarity with Australian National Construction Code (NCC) and Australian Standards (AS 3600 / AS 4100).",
    "Operations & Administration": "Requires practical mastery of the Australian Fair Work Act 2009, Modern Awards system, and Superannuation Guarantee compliance.",
    "Technology & Data": "Minor gap in Australian data sovereignty frameworks (Privacy Act 1988, Essential Eight cyber maturity), easily bridged via standard security onboarding.",
    "Hospitality & Service": "Requires Australian Food Safety Supervisor certification (HACCP) and state-level Responsible Service of Alcohol (RSA) licensing."
}

def extract_skills_from_text(raw_text: str, default_skills: str = "") -> list:
    """Extract list of distinct, clean skills."""
    if default_skills and isinstance(default_skills, str):
        skills = [s.strip() for s in default_skills.replace('|', ',').split(',') if s.strip()]
        if len(skills) >= 3:
            return skills[:8]

    # Keyword extraction fallback from text
    found = []
    candidates = re.findall(r'\b[A-Z][a-zA-Z0-9\+\#\.\-]{2,20}(?:\s[A-Z][a-zA-Z0-9\+\#\.\-]{2,20})?\b', raw_text[:1000])
    for c in candidates:
        if c.lower() not in ['summary', 'education', 'experience', 'highlights', 'skills', 'company', 'state', 'city'] and len(c) > 3:
            if c not in found:
                found.append(c)
    return found[:6] or ["Project Management", "Process Optimization", "Quality Assurance", "Cross-Functional Collaboration"]

def get_honest_gap_for_sector(sector: str) -> str:
    """Lookup statutory gap for an Australian sector."""
    for key, gap in GAP_KNOWLEDGE_BASE.items():
        if key.lower() in (sector or "").lower() or (sector or "").lower() in key.lower():
            return gap
    return "Requires general Australian workplace culture and local regulatory compliance onboarding."
