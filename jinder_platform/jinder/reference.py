"""Reference lists. The lists of the product come from the taxonomy (`taxonomy.py`), so that the API, the forms, the formulas and the
CV reader use the same names. The Jinder frontend has the same lists in `js/data/reference.js`.

The product covers three domains only: Software Engineering, AI & Machine Learning and Data.
Do not add lists for sensitive data (nationality, visa status, age, gender). See AI_Rule Rule 5.
"""
from collections import Counter

from . import taxonomy

_T = taxonomy.get()

# ---------- From the taxonomy ----------
DOMAINS = list(_T.domains)                                   # the 3 domains
INDUSTRIES = DOMAINS                                         # the profile keys `industry` and `targetIndustries` hold domains (the screens say "Domain")
SPECIALISATIONS = {d: list(v) for d, v in _T.specialisations.items()}
ALL_SPECIALISATIONS = list(_T.all_specialisations)
LOCATIONS = list(_T.cities)                                  # the cities and "Remote"
CITIES = LOCATIONS
WORK_TYPES = list(_T.work_types)
WORK_MODES = list(_T.work_modes)
LEVELS = list(_T.levels)                                     # Intern, Junior, Mid, Senior, Lead, Principal (rank 0 to 5)
SKILL_LEVEL_LABELS = dict(_T.skill_levels)                   # {1: "Beginner", ... 5: "Expert"}
ROLES = list(_T.role_titles)                                 # the pick-list of roles (no level word in a role)
FIELDS_OF_STUDY = list(_T.fields_of_study)
CERTIFICATIONS = list(_T.certification_names)
AWARD_KINDS = list(_T.award_kinds)                           # slugs, for example "hackathon"
AWARD_LABELS = dict(_T.award_labels)
SKILL_NAMES = [s["name"] for s in _T.skills]

# A few skills to suggest for each domain: the skills that most occupations of the domain ask for
_by_domain = {d: Counter() for d in DOMAINS}
for _o in _T.occupations.values():
    for _c in _o.get("coreSkills", []):
        if _o["domain"] in _by_domain and _T.skill(_c["name"]) and _T.kind_of(_c["name"]) == "hard":
            _by_domain[_o["domain"]][_c["name"]] += 1 + (1 if _c.get("must") else 0)
SKILL_SUGGESTIONS = {d: [name for name, _ in sorted(c.items(), key=lambda t: (-t[1], t[0]))[:7]] for d, c in _by_domain.items()}

# ---------- Not in the taxonomy ----------
QUALIFICATIONS = [
    "High school", "Certificate III or IV", "Diploma", "Advanced diploma", "Associate degree",
    "Bachelor's degree", "Bachelor's degree (Honours)", "Graduate certificate", "Graduate diploma",
    "Master's degree", "MBA", "Doctorate (PhD)",
]

# Countries where qualifications are often earned. Used only for the AQF note, never for ranking.
COUNTRIES = [
    "Australia", "Bangladesh", "Brazil", "Canada", "Chile", "China", "Colombia", "Egypt", "France", "Germany",
    "Ghana", "Hong Kong", "India", "Indonesia", "Iran", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
    "Mexico", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Pakistan", "Peru", "Philippines", "Singapore",
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Taiwan", "Thailand", "Turkey", "United Arab Emirates",
    "United Kingdom", "United States", "Vietnam", "Zimbabwe",
]

YEARS = ["Less than 1 year", "1–2 years", "3–5 years", "6–10 years", "More than 10 years"]
# The middle of each range, in years. Used only when a profile has no exact number of years.
YEARS_MIDPOINT = {"Less than 1 year": 0.5, "1–2 years": 1.5, "3–5 years": 4.0, "6–10 years": 8.0, "More than 10 years": 12.0}

# A job category is a domain. The map is the identity: it stays so that old code that reads it keeps working.
JOB_CATEGORIES = DOMAINS
CATEGORY_MAP = {d: [d] for d in DOMAINS}
INDUSTRY_TO_CATEGORY = {d: d for d in DOMAINS}

PLANS = ("basic", "premium")
