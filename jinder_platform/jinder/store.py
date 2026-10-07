"""Data access for accounts, profiles and the shared (employer-safe) profile.

Rules that this module enforces in one place:
  * A user view never has the password hash.
  * The shared profile is an ALLOWLIST. It never has a name, an email, contact details, a country, an employer name,
    the CV or the evidence lines (Feature 5 AC3, AC4).
"""
import math
import re
import sqlite3
from typing import Any, Dict, Iterable, List, Optional

from . import config, security
from .reference import (ALL_SPECIALISATIONS, AWARD_KINDS, AWARD_LABELS, DOMAINS, LEVELS, LOCATIONS, WORK_MODES, WORK_TYPES, YEARS)
from .util import (ApiError, as_list, clean_text, jdump, jload, new_id, now_iso, scrub_contact, unique, utcnow)

PROFILE_LISTS = {  # profile key -> column
    "qualification": "qualification", "fieldOfStudy": "field_of_study", "studyCountry": "study_country",
    "currentRole": "current_role", "industry": "industry", "skills": "skills", "targetRole": "target_role",
    "targetIndustries": "target_industries", "locations": "locations", "workTypes": "work_types", "workModes": "work_modes",
}
SKILL_SOURCES = ("role", "skill", "qualification")
SKILL_KINDS = ("cross-border", "cross-industry", "direct")
SKILL_EVIDENCE = ("Strong", "Moderate", "Limited")
SKILL_STATUS = ("suggested", "accepted", "edited", "removed")
SHARED_STATUS = ("accepted", "edited")
MAX_LIST_ITEMS = 30

# Version 2 (V2_PLAN.md, section 4.3)
MAX_CERTIFICATIONS = 20
MAX_AWARDS = 20
FIRST_YEAR = 1990                                  # the earliest year for a certification or an award
MAX_YEARS_EXPERIENCE = 40
# A skill with no level counts as this level (F8): the evidence of the skill gives the level
EVIDENCE_LEVEL = {"Strong": 4, "Moderate": 3, "Limited": 2}
DEFAULT_SKILL_LEVEL = 3


# =====================================================================
# Users and sessions
# =====================================================================
def get_user(conn: sqlite3.Connection, user_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def user_for_token(conn: sqlite3.Connection, token: Optional[str]) -> Optional[sqlite3.Row]:
    """The user of a session token. An expired session is deleted."""
    if not token:
        return None
    th = security.hash_token(token)
    s = conn.execute("SELECT user_id, expires_at FROM sessions WHERE token_hash = ?", (th,)).fetchone()
    if not s:
        return None
    from .util import parse_iso, utcnow
    expires = parse_iso(s["expires_at"])
    if expires is None or expires < utcnow():
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (th,))
        return None
    return get_user(conn, s["user_id"])


# =====================================================================
# Profile
# =====================================================================
def cv_record(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    r = conn.execute("SELECT name, size, added_at FROM cv_files WHERE user_id = ? ORDER BY added_at DESC LIMIT 1", (user_id,)).fetchone()
    return {"name": r["name"], "size": r["size"], "addedAt": r["added_at"]} if r else None


def _translation_dicts(rows) -> List[Dict[str, Any]]:
    return [{
        "id": r["skill_id"], "source": r["source"], "original": r["original"], "mapped": r["mapped"], "kind": r["kind"],
        "anzsco": r["anzsco"], "occupation": r["occupation"], "reason": r["reason"], "evidence": r["evidence"],
        "evidenceText": r["evidence_text"], "status": r["status"], "level": r["level"], "years": r["years"],
    } for r in rows]


def _profile_dict(r: sqlite3.Row, translation: List[Dict[str, Any]]) -> Dict[str, Any]:
    profile: Dict[str, Any] = {key: jload(r[col], []) for key, col in PROFILE_LISTS.items()}
    profile["years"] = r["years"] or ""
    profile["level"] = r["level"] or ""
    profile["specialisation"] = r["specialisation"] or ""
    profile["yearsExperience"] = _plain_number(r["years_exact"])
    profile["certifications"] = jload(r["certifications"], [])
    profile["awards"] = jload(r["awards"], [])
    profile["translation"] = translation
    profile["evidence"] = jload(r["evidence"], [])
    return profile


def _plain_number(value: Any) -> Any:
    """A number for JSON: a whole number has no ".0"."""
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def load_profile(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    r = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if not r:
        return None
    rows = conn.execute("SELECT * FROM translated_skills WHERE user_id = ? ORDER BY position", (user_id,)).fetchall()
    return _profile_dict(r, _translation_dicts(rows))


def _clean_list(value: Any, max_len: int = 120, allowed: Optional[Iterable[str]] = None) -> List[str]:
    items = []
    for v in as_list(value):
        if isinstance(v, dict) and isinstance(v.get("name"), str):
            v = v["name"]                     # a skill with a level ({name, level}): the level goes to the translated skill
        if not isinstance(v, (str, int, float)):
            continue
        text = scrub_contact(clean_text(v, max_len))   # these lists can reach employers (skills, fields, industries, target roles)
        if text and (allowed is None or text in allowed):
            items.append(text)
    return unique(items)[:MAX_LIST_ITEMS]


def years_band(years: float) -> str:
    """The band (one of YEARS) for a number of years."""
    return YEARS[0] if years < 1 else YEARS[1] if years < 3 else YEARS[2] if years < 6 else YEARS[3] if years <= 10 else YEARS[4]


def _whole(value: Any) -> Optional[int]:
    """A whole number from an int, or from a float without a fraction. Anything else (a bool, text) gives None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def clean_skill_level(value: Any) -> Optional[int]:
    """A skill level from 1 to 5, or None."""
    n = _whole(value)
    return n if n is not None and 1 <= n <= 5 else None


def clean_year(value: Any) -> Optional[int]:
    """The year of a certification or an award: from 1990 to next year, or None."""
    if isinstance(value, str) and re.fullmatch(r"\s*\d{4}\s*", value):
        value = int(value)
    n = _whole(value)
    return n if n is not None and FIRST_YEAR <= n <= utcnow().year + 1 else None


def clean_years_experience(value: Any) -> Optional[float]:
    """Exact years of experience: a number from 0 to 40 with one decimal, or None."""
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        years = float(value)
    except (TypeError, ValueError, OverflowError):    # OverflowError: a whole number with hundreds of digits
        return None
    return round(years, 1) if 0 <= years <= MAX_YEARS_EXPERIENCE else None


def award_kind(text: Any) -> str:
    """The kind of an award as a slug of the taxonomy ("hackathon"). The slug or the label ("Hackathon") is accepted. Anything else gives ""."""
    value = str(text or "").strip()
    if value in AWARD_KINDS:
        return value
    low = value.lower()
    for slug, label in AWARD_LABELS.items():
        if low == label.lower() or low == slug:
            return slug
    return ""


def _clean_named_items(value: Any, second_key: str, second_limit: int, second_fn=None) -> List[Dict[str, Any]]:
    """The items of a certification list ({name, issuer, year}) or an award list ({name, kind, year}).

    The text goes through scrub_contact: these items reach employers. A bare text counts as a name.
    `second_fn` checks the second value (the award kind).
    """
    out, seen = [], set()
    for item in as_list(value):
        if isinstance(item, str):
            item = {"name": item}
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        name = scrub_contact(clean_text(item["name"], 120))
        if not name:
            continue
        second_raw = item.get(second_key)
        second = scrub_contact(clean_text(second_raw, second_limit)) if isinstance(second_raw, str) else ""
        if second_fn is not None:
            second = second_fn(second)
        year = clean_year(item.get("year"))
        key = (name.lower(), second.lower(), year)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, second_key: second, "year": year})
    return out


def clean_certifications(value: Any) -> List[Dict[str, Any]]:
    return _clean_named_items(value, "issuer", 120)[:MAX_CERTIFICATIONS]


def clean_awards(value: Any) -> List[Dict[str, Any]]:
    """The award kind must be a kind of the taxonomy (a slug, or its label). Any other kind becomes "". The name stays (free text)."""
    return _clean_named_items(value, "kind", 40, award_kind)[:MAX_AWARDS]


def _clean_translation(value: Any) -> List[Dict[str, Any]]:
    out, seen = [], set()
    for s in as_list(value):
        if not isinstance(s, dict):
            continue
        skill_id = clean_text(s.get("id"), 200)
        mapped = scrub_contact(clean_text(s.get("mapped"), 200))
        original = clean_text(s.get("original"), 400)
        if not skill_id or not mapped or not original or skill_id in seen:
            continue
        if s.get("source") not in SKILL_SOURCES or s.get("kind") not in SKILL_KINDS or s.get("status") not in SKILL_STATUS:
            continue
        evidence = s.get("evidence") if s.get("evidence") in SKILL_EVIDENCE else "Limited"
        anzsco = str(s.get("anzsco") or "")
        seen.add(skill_id)
        out.append({
            "id": skill_id, "source": s["source"], "original": original, "mapped": mapped, "kind": s["kind"],
            "anzsco": anzsco if re.fullmatch(r"\d{0,6}", anzsco) else "", "occupation": scrub_contact(clean_text(s.get("occupation"), 120)),
            "reason": clean_text(s.get("reason"), 600), "evidence": evidence,
            "evidenceText": scrub_contact(clean_text(s.get("evidenceText"), 400)), "status": s["status"],
            # a level is for skills only, not for the rows of roles and qualifications
            "level": clean_skill_level(s.get("level")) if s["source"] == "skill" else None,
            # the years that the talent used the skill (0 to 40, one decimal). Skills only.
            "years": clean_years_experience(s.get("years")) if s["source"] == "skill" else None,
        })
    return out[:80]


def effective_level(skill: Dict[str, Any]) -> int:
    """The level of a translated skill: the level that the talent set, or the level that its evidence gives (F8)."""
    return clean_skill_level(skill.get("level")) or EVIDENCE_LEVEL.get(skill.get("evidence"), DEFAULT_SKILL_LEVEL)


def save_profile(conn: sqlite3.Connection, user_id: str, profile: Dict[str, Any], updated_at: Optional[str] = None) -> None:
    """Replace the profile and the translated skills. The input is cleaned: only known keys and values are kept.

    `updated_at` is for the seed (sample profiles with an older date). The server sets it to now when it is missing."""
    if not isinstance(profile, dict):
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", {"profile": "The profile is not valid."})
    clean: Dict[str, Any] = {
        "qualification": _clean_list(profile.get("qualification")),
        "fieldOfStudy": _clean_list(profile.get("fieldOfStudy")),
        "studyCountry": _clean_list(profile.get("studyCountry")),
        "currentRole": _clean_list(profile.get("currentRole")),
        "industry": _clean_list(profile.get("industry"), allowed=DOMAINS),
        "skills": _clean_list(profile.get("skills")),
        "targetRole": _clean_list(profile.get("targetRole")),
        "targetIndustries": _clean_list(profile.get("targetIndustries"), allowed=DOMAINS),
        "locations": _clean_list(profile.get("locations"), allowed=LOCATIONS),
        "workTypes": _clean_list(profile.get("workTypes"), allowed=WORK_TYPES),
        "workModes": _clean_list(profile.get("workModes"), allowed=WORK_MODES),
    }
    years = profile.get("years")
    clean["years"] = years if years in YEARS else ""
    # Version 2. The exact years set the band: the band never disagrees with the exact number.
    level = profile.get("level")
    clean["level"] = level if isinstance(level, str) and level in LEVELS else ""
    specialisation = profile.get("specialisation")
    clean["specialisation"] = specialisation if isinstance(specialisation, str) and specialisation in ALL_SPECIALISATIONS else ""
    clean["yearsExperience"] = clean_years_experience(profile.get("yearsExperience"))
    if clean["yearsExperience"] is not None:
        clean["years"] = years_band(clean["yearsExperience"])
    clean["certifications"] = clean_certifications(profile.get("certifications"))
    clean["awards"] = clean_awards(profile.get("awards"))
    evidence = [scrub_contact(clean_text(e, 300)) for e in as_list(profile.get("evidence")) if isinstance(e, str)]
    clean["evidence"] = [e for e in evidence if e][:30]
    translation = _clean_translation(profile.get("translation"))

    conn.execute(
        """INSERT INTO profiles (user_id, qualification, field_of_study, study_country, current_role, industry, years, skills,
                                 target_role, target_industries, locations, work_types, evidence, updated_at,
                                 level, years_exact, certifications, awards, specialisation, work_modes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET qualification=excluded.qualification, field_of_study=excluded.field_of_study,
             study_country=excluded.study_country, current_role=excluded.current_role, industry=excluded.industry,
             years=excluded.years, skills=excluded.skills, target_role=excluded.target_role,
             target_industries=excluded.target_industries, locations=excluded.locations, work_types=excluded.work_types,
             evidence=excluded.evidence, updated_at=excluded.updated_at, level=excluded.level, years_exact=excluded.years_exact,
             certifications=excluded.certifications, awards=excluded.awards, specialisation=excluded.specialisation,
             work_modes=excluded.work_modes""",
        (user_id, jdump(clean["qualification"]), jdump(clean["fieldOfStudy"]), jdump(clean["studyCountry"]),
         jdump(clean["currentRole"]), jdump(clean["industry"]), clean["years"], jdump(clean["skills"]),
         jdump(clean["targetRole"]), jdump(clean["targetIndustries"]), jdump(clean["locations"]),
         jdump(clean["workTypes"]), jdump(clean["evidence"]), updated_at or now_iso(),
         clean["level"], clean["yearsExperience"], jdump(clean["certifications"]), jdump(clean["awards"]),
         clean["specialisation"], jdump(clean["workModes"])))
    conn.execute("DELETE FROM translated_skills WHERE user_id = ?", (user_id,))
    conn.executemany(
        """INSERT INTO translated_skills (user_id, skill_id, position, source, original, mapped, kind, anzsco, occupation,
                                          reason, evidence, evidence_text, status, level, years)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(user_id, s["id"], i, s["source"], s["original"], s["mapped"], s["kind"], s["anzsco"], s["occupation"],
          s["reason"], s["evidence"], s["evidenceText"], s["status"], s["level"], s["years"]) for i, s in enumerate(translation)])


def public_user(conn: sqlite3.Connection, u: sqlite3.Row) -> Dict[str, Any]:
    """What GET /me returns. An allowlist: the password hash never leaves the server."""
    is_candidate = u["role"] == "candidate"
    return {
        "id": u["id"], "role": u["role"], "name": u["name"], "email": u["email"], "company": u["company"],
        "alias": u["alias"], "profile": load_profile(conn, u["id"]) if is_candidate else None,
        "cv": cv_record(conn, u["id"]) if is_candidate else None, "onboarding": u["onboarding"], "createdAt": u["created_at"],
    }


# =====================================================================
# The shared profile (what employers see)
# =====================================================================
def is_shared(skill: Dict[str, Any]) -> bool:
    return skill.get("status") in SHARED_STATUS


def _half_year(value: Any) -> Optional[float]:
    """Years of experience, rounded to 0.5. An employer sees this, not the exact number."""
    if value is None:
        return None
    return _plain_number(math.floor(float(value) * 2 + 0.5) / 2)


def shared_profile(alias: str, profile: Optional[Dict[str, Any]], updated_at: Optional[str] = None) -> Dict[str, Any]:
    """Build the allowlist view from a profile. This is the only function that makes an employer-safe profile.

    Version 2 adds: level, yearsExperience (to 0.5), skillLevels, certifications, awards (names, issuer or kind, and years)
    and updatedAt (the date of the last change of the profile). Still no name, email, country, CV text or evidence line.
    """
    p = profile or {}
    shared = [s for s in as_list(p.get("translation")) if is_shared(s)]
    roles = []
    for s in shared:
        if s.get("source") == "role" and s.get("anzsco"):
            role = {"title": s.get("occupation") or s["mapped"], "anzsco": s["anzsco"]}
            if role not in roles:
                roles.append(role)
    # The skills are the cards of skills only (a role card names a role, not a skill)
    skills = unique([s["mapped"] for s in shared if s.get("source") == "skill"])
    # One level for each skill name. A skill with no level of its own gets the level of its evidence (F8).
    levels: Dict[str, int] = {}
    years: Dict[str, Optional[float]] = {}
    for s in shared:
        if s.get("source") == "skill":
            levels[s["mapped"]] = max(levels.get(s["mapped"], 0), effective_level(s))
            if s.get("years") is not None:
                years[s["mapped"]] = max(years.get(s["mapped"], 0.0), float(s["years"]))
    return {
        "alias": alias,
        "roles": roles,
        "skills": skills,
        "qualifications": [s["mapped"] for s in shared if s.get("source") == "qualification"],
        "fieldsOfStudy": as_list(p.get("fieldOfStudy")),
        "industries": as_list(p.get("industry")),
        "years": p.get("years") or None,
        "targetRoles": as_list(p.get("targetRole")),
        "locations": as_list(p.get("locations")),
        "workTypes": as_list(p.get("workTypes")),
        "workModes": as_list(p.get("workModes")),
        "specialisation": p.get("specialisation") or None,
        "level": p.get("level") or None,
        "yearsExperience": _half_year(p.get("yearsExperience")),
        "skillLevels": [{"name": name, "level": levels[name], "years": _plain_number(years.get(name))} for name in skills],
        "certifications": [{"name": c["name"], "issuer": c.get("issuer", ""), "year": c.get("year")} for c in as_list(p.get("certifications"))],
        "awards": [{"name": a["name"], "kind": a.get("kind", ""), "year": a.get("year")} for a in as_list(p.get("awards"))],
        "updatedAt": updated_at,
    }


def shared_profile_of(conn: sqlite3.Connection, u: sqlite3.Row) -> Dict[str, Any]:
    row = conn.execute("SELECT updated_at FROM profiles WHERE user_id = ?", (u["id"],)).fetchone()
    return shared_profile(u["alias"], load_profile(conn, u["id"]), row["updated_at"] if row else None)


def candidate_pool(conn: sqlite3.Connection, only_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every talent with a finished profile and at least one shared skill (or only the talent with this id).

    Each item: { id, alias, profile (private, for the server only), shared (the allowlist view), updated_at }.
    The caller must send only the "shared" part, or values that come from it, to an employer.
    """
    who = "" if only_id is None else " AND id = ?"
    args: tuple = () if only_id is None else (only_id,)
    users = conn.execute(f"SELECT id, alias FROM users WHERE role = 'candidate' AND onboarding = 'done'{who} ORDER BY alias", args).fetchall()
    if not users:
        return []
    ids = tuple(u["id"] for u in users) if only_id is not None else None
    scope = "WHERE user_id IN (SELECT id FROM users WHERE role = 'candidate' AND onboarding = 'done')" if ids is None else "WHERE user_id = ?"
    scope_args: tuple = () if ids is None else (only_id,)
    profiles = {r["user_id"]: r for r in conn.execute(f"SELECT * FROM profiles {scope}", scope_args).fetchall()}
    skills: Dict[str, list] = {}
    for r in conn.execute(f"SELECT * FROM translated_skills {scope} ORDER BY user_id, position", scope_args).fetchall():
        skills.setdefault(r["user_id"], []).append(r)
    out = []
    for u in users:
        row = profiles.get(u["id"])
        if not row:
            continue
        profile = _profile_dict(row, _translation_dicts(skills.get(u["id"], [])))
        shared = shared_profile(u["alias"], profile, row["updated_at"])
        if shared["skills"]:
            out.append({"id": u["id"], "alias": u["alias"], "profile": profile, "shared": shared, "updated_at": row["updated_at"]})
    return out


# =====================================================================
# Notifications, tracking events, plans
# =====================================================================
def notify(conn: sqlite3.Connection, user_id: str, type_: str, title: str, body: str = "", link: str = "", email: bool = False) -> None:
    """An in-app alert. With email=True the message also goes to the outbox (it is sent later, and a failure never blocks the user)."""
    nid = new_id()
    now = now_iso()
    conn.execute(
        "INSERT INTO notifications (id, user_id, type, title, body, link, email, read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)",
        (nid, user_id, type_, clean_text(title, 200), clean_text(body, 500), link, 1 if email else 0, now))
    if email:
        conn.execute(
            """INSERT INTO email_outbox (id, user_id, notification_id, subject, body, status, attempts, next_attempt_at, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)""",
            (new_id(), user_id, nid, clean_text(title, 200), clean_text(body, 500), now, now))


def track(conn: sqlite3.Connection, type_: str, target_type: str, target_id: str, actor_id: Optional[str]) -> None:
    """A tracking event (Feature 7 AC4). It must never block or fail the user action."""
    try:
        conn.execute("INSERT INTO events (type, target_type, target_id, actor_id, at) VALUES (?, ?, ?, ?, ?)",
                     (type_, target_type, target_id, actor_id, now_iso()))
    except sqlite3.Error:
        pass


# The Premium benefits that Settings shows (V2_PLAN.md, section 5.4). Each benefit has the tracking event that marks it "used".
# The label and the description are for the user. They are in simple English.
BENEFITS = {
    "recruiter": [
        ("all_talent", "talent_list_full", "See every talent profile, not only the top 5",
         "Basic shows the 5 best profiles for a job. Premium shows every profile, page by page."),
        ("invite", "invite", "Invite talent to apply",
         "Send a message to a talent who did not apply. The talent can accept or decline."),
        ("compare", "compare_view", "Compare up to 5 talent profiles",
         "See 2 to 5 profiles side by side for one of your jobs, skill by skill."),
        ("advanced_charts", "advanced_charts_view", "Pipeline by stage and interest per job",
         "See how many applications are in each stage, and how many talent saw, saved and applied to each job."),
    ],
    "candidate": [
        ("skills_to_learn", "insights_view", "Skills to learn next",
         "See the skills that your best-fit jobs ask for and that you do not have yet."),
        ("skill_demand", "insights_view", "Demand for your skills",
         "See which of your skills your best-fit jobs ask for most."),
    ],
}


def plan_flags(conn: sqlite3.Connection, u: sqlite3.Row) -> Dict[str, Any]:
    """What the plan of this user allows. A small and cheap check: the routes use it to decide."""
    row = conn.execute("SELECT plan FROM plans WHERE user_id = ?", (u["id"],)).fetchone()
    plan = "premium" if row and row["plan"] == "premium" else "basic"
    premium = plan == "premium"
    is_recruiter = u["role"] == "recruiter"
    return {
        "plan": plan,
        "topN": (None if premium else config.TOP_N) if is_recruiter else None,
        "canContact": is_recruiter and premium,
        "canCompare": is_recruiter and premium,
        "advancedCharts": premium,
    }


def benefits_of(conn: sqlite3.Connection, u: sqlite3.Row, premium: bool) -> List[Dict[str, Any]]:
    """The Premium benefits of this user, with a flag for each: is it in the plan (available) and did the user use it (used).

    The counts come from the events where this user is the actor. The user sees only their own counts.
    """
    items = BENEFITS.get(u["role"], [])
    events = sorted({event for _, event, _, _ in items})
    counts: Dict[str, int] = {}
    if events:
        marks = ",".join("?" for _ in events)
        rows = conn.execute(f"SELECT type, COUNT(*) AS n FROM events WHERE actor_id = ? AND type IN ({marks}) GROUP BY type", (u["id"], *events)).fetchall()
        counts = {r["type"]: r["n"] for r in rows}
    return [{"key": key, "label": label, "description": text, "available": premium, "used": counts.get(event, 0) > 0,
             "usedCount": counts.get(event, 0)} for key, event, label, text in items]


def entitlements_of(conn: sqlite3.Connection, u: sqlite3.Row) -> Dict[str, Any]:
    """GET /entitlements: the flags of the plan, the crown (Premium) and the list of Premium benefits."""
    ent = plan_flags(conn, u)
    premium = ent["plan"] == "premium"
    ent["crown"] = premium
    ent["compareMax"] = config.COMPARE_MAX
    ent["benefits"] = benefits_of(conn, u, premium)
    return ent


def require_premium(conn: sqlite3.Connection, u: sqlite3.Row, feature: str) -> Dict[str, Any]:
    ent = plan_flags(conn, u)
    if not ent.get(feature):
        raise ApiError(403, "PREMIUM_REQUIRED", "This feature is part of Premium. Upgrade in Settings to use it.")
    return ent
