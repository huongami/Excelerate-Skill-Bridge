"""
Australian ANZSCO Taxonomy Classifier
Maps raw occupational titles and industry sectors to the official
Australian and New Zealand Standard Classification of Occupations (ANZSCO).
"""

import re

ANZSCO_TAXONOMY = {
    "Healthcare & Nursing": {
        "default_code": "254411",
        "default_title": "Registered Nurse / Health Specialist",
        "rules": [
            (r'nurse|clinical|triage|hospital|patient', "254411", "Registered Nurse / Clinical Specialist"),
            (r'medical administrator|practice manager|health admin', "254423", "Medical Practice Manager"),
            (r'paramedic|emergency', "254415", "Emergency & Critical Care Nurse")
        ]
    },
    "Finance & Accounting": {
        "default_code": "221111",
        "default_title": "Accountant (General) / Financial Analyst",
        "rules": [
            (r'auditor|internal audit', "221214", "Internal Auditor"),
            (r'tax accountant|taxation', "221113", "Taxation Accountant"),
            (r'financial analyst|investment|banking', "222311", "Financial Investment Analyst"),
            (r'accountant|ledger|bookkeeper|cpa', "221111", "Accountant (General)")
        ]
    },
    "Marketing & Communications": {
        "default_code": "225113",
        "default_title": "Marketing Specialist / Communications Manager",
        "rules": [
            (r'public relations|pr|media relations', "225311", "Public Relations Professional"),
            (r'digital marketing|seo|social media|growth', "225113", "Marketing Specialist"),
            (r'advertising|brand manager', "225111", "Advertising Specialist")
        ]
    },
    "Supply Chain & Logistics": {
        "default_code": "133611",
        "default_title": "Supply and Distribution Manager",
        "rules": [
            (r'procurement|sourcing|buyer', "133612", "Procurement Manager"),
            (r'warehouse|inventory|logistics|freight', "133611", "Supply and Distribution Manager"),
            (r'fleet|transport', "133611", "Transport and Distribution Manager")
        ]
    },
    "Engineering & Construction": {
        "default_code": "233211",
        "default_title": "Civil Engineer / Construction Project Manager",
        "rules": [
            (r'civil engineer|structural|infrastructure', "233211", "Civil Engineer"),
            (r'site manager|construction manager|superintendent', "133111", "Construction Project Manager"),
            (r'electrical engineer|electronics', "233311", "Electrical Engineer"),
            (r'mechanical engineer', "233512", "Mechanical Engineer")
        ]
    },
    "Operations & Administration": {
        "default_code": "223111",
        "default_title": "Human Resource Adviser / Operations Manager",
        "rules": [
            (r'hr|human resources|recruiter|people', "223111", "Human Resource Adviser"),
            (r'legal|compliance|regulatory|paralegal', "271299", "Judicial and Legal Professional nec"),
            (r'operations manager|business operations', "111211", "Corporate General Manager / Operations Lead")
        ]
    },
    "Technology & Data": {
        "default_code": "261313",
        "default_title": "Software Engineer / Data Specialist",
        "rules": [
            (r'data engineer|data analyst|database|sql|bi', "261313", "Software and Applications Programmer (Data)"),
            (r'software engineer|developer|frontend|backend|fullstack', "261313", "Software Engineer"),
            (r'systems analyst|business analyst|product owner', "261111", "ICT Business and Systems Analyst"),
            (r'cloud|devops|security|sre', "262112", "ICT Security / Cloud Infrastructure Specialist")
        ]
    },
    "Hospitality & Service": {
        "default_code": "351311",
        "default_title": "Chef / Hospitality Operations Specialist",
        "rules": [
            (r'chef|cook|culinary|kitchen', "351311", "Chef"),
            (r'restaurant manager|food and beverage|f&b', "141111", "Cafe and Restaurant Manager"),
            (r'hotel manager|guest relations|hospitality', "141999", "Accommodations and Hospitality Manager")
        ]
    }
}

def classify_anzsco(title: str, sector: str) -> tuple:
    """Returns (anzsco_code, anzsco_title) based on occupational title and sector."""
    title_lower = (title or "").lower()
    sector_norm = sector or "Technology & Data"

    # Find sector config
    matched_sector = None
    for sec_key, conf in ANZSCO_TAXONOMY.items():
        if sec_key.lower() in sector_norm.lower() or sector_norm.lower() in sec_key.lower():
            matched_sector = conf
            break

    if not matched_sector:
        matched_sector = ANZSCO_TAXONOMY["Technology & Data"]

    for pattern, code, off_title in matched_sector.get("rules", []):
        if re.search(pattern, title_lower):
            return code, off_title

    return matched_sector["default_code"], matched_sector["default_title"]
