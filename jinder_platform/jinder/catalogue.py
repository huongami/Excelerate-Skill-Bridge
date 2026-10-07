"""The job catalogue and the recommendations (Feature 3; version 2: the formulas decide the fit).

Jobs live in the database (catalogue jobs and jobs that employers post). This module reads them and
ranks them for one talent. The fit of a job is the `fit` of Formula 1. The feed score is Formula 5, with its employer diversity
penalty and then the feedback loop. match.score = round(0.55 x fit + 0.45 x FRS*, 1). All job data is internal Jinder data (AI_Rule Rule 11).

The match uses only skills with their levels, roles, level, years, certifications, awards, domains, locations, work modes and work types.
It never uses nationality, ethnicity, gender, age, visa status or country of study.
"""
import re
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from . import engine_bridge as eb
from .reference import ALL_SPECIALISATIONS, LEVELS, WORK_MODES
from .skills import _js_round, job_skills, results_from_breakdown, skill_match
from .store import DEFAULT_SKILL_LEVEL, award_kind, clean_skill_level
from .util import as_list, clean_text, jdump, jload, norm, parse_iso, scrub_contact, unique, utcnow

FIT_WEIGHT = 0.55   # the fit of Formula 1
FRS_WEIGHT = 0.45   # Formula 5, after its feedback loop


# =====================================================================
# Reading jobs
# =====================================================================
def _plain_number(value: Any) -> Any:
    """A number for JSON: a whole number has no ".0". None stays None."""
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _row_to_job(row: sqlite3.Row, skill_rows: List[sqlite3.Row]) -> Dict[str, Any]:
    """A job as the API shows it. The keys of version 2 are null (or empty) for a job that has no value: nothing is invented."""
    return {
        "id": row["id"], "ownerId": row["owner_id"], "title": row["title"], "company": row["company"],
        "category": row["category"], "location": row["location"], "area": row["area"], "type": row["type"],
        "anzsco": row["anzsco"], "occupation": row["occupation"], "salary": row["salary"],
        "salaryMin": row["salary_min"], "salaryMax": row["salary_max"], "salaryUnit": row["salary_unit"],
        "postedAt": row["posted_at"], "closesAt": row["closes_at"], "summary": row["summary"],
        "description": row["description"], "skills": [r["skill"] for r in skill_rows], "targetApplicants": row["target_applicants"],
        "editedAt": row["edited_at"],
        "level": row["level"], "specialisation": row["specialisation"],
        "minYears": _plain_number(row["min_years"]), "maxYears": _plain_number(row["max_years"]),
        "workMode": row["work_mode"], "educationMin": row["education_min"],
        # the skills that have a level. A job with no skill level has an empty list: use "skills" then (see requirements_of)
        "skillRequirements": [{"name": r["skill"], "level": r["level"], "must": bool(r["must"])} for r in skill_rows if r["level"] is not None],
        "certifications": {"required": jload(row["certs_required"], []), "preferred": jload(row["certs_preferred"], [])},
        "awards": {"preferred": jload(row["awards_preferred"], [])},
    }


def load_jobs(conn: sqlite3.Connection, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """All jobs (open and closed), or one job. Each job has its skills in order."""
    if job_id is None:
        rows = conn.execute("SELECT * FROM jobs").fetchall()
        skill_rows = conn.execute("SELECT job_id, skill, level, must FROM job_skills ORDER BY job_id, position").fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchall()
        skill_rows = conn.execute("SELECT job_id, skill, level, must FROM job_skills WHERE job_id = ? ORDER BY position", (job_id,)).fetchall()
    by_job: Dict[str, List[sqlite3.Row]] = {}
    for r in skill_rows:
        by_job.setdefault(r["job_id"], []).append(r)
    return [_row_to_job(r, by_job.get(r["id"], [])) for r in rows]


def requirements_of(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The skills that a job asks for, each with a level (1 to 5) and "must".

    A job with skill levels gives them. A job without gives its skill names with level 3 and must=true.
    """
    reqs = job.get("skillRequirements") or []
    return [dict(r) for r in reqs] if reqs else [{"name": s, "level": DEFAULT_SKILL_LEVEL, "must": True} for s in job.get("skills") or []]


def find_job(conn: sqlite3.Connection, job_id: str) -> Optional[Dict[str, Any]]:
    found = load_jobs(conn, job_id)
    return found[0] if found else None


def is_open(job: Dict[str, Any]) -> bool:
    closes = parse_iso(job.get("closesAt"))
    return closes is None or closes >= utcnow()


def job_source(jobs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    jobs = list(jobs)
    latest = max((j["postedAt"] for j in jobs if j.get("postedAt")), default=None)
    return {"openCount": sum(1 for j in jobs if is_open(j)), "updatedAt": latest}


# =====================================================================
# The keys of version 2 of a job (V2_PLAN.md, section 4.4): check, clean and save
# =====================================================================
JOB_EXTRA_KEYS = ("level", "specialisation", "minYears", "maxYears", "workMode", "skillRequirements", "certifications", "awards", "educationMin")
MAX_JOB_SKILLS = 12
MAX_JOB_CERTIFICATIONS = 10      # for each list (required, preferred)
MAX_JOB_AWARD_KINDS = 10
MAX_DESCRIPTION = 10000          # the description is never cut: a longer text is refused with a message


def _years_value(value: Any) -> Optional[float]:
    """A number of years from 0 to 40 with one decimal. Raises ValueError for anything else."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("not a number")
    number = float(value)
    if not 0 <= number <= 40:
        raise ValueError("out of range")
    return round(number, 1)


def _name_list(value: Any, limit: int, name_len: int, label: str):
    """A list of names (certifications or award kinds). The text is scrubbed: it reaches talent. Returns (names, error)."""
    if value is None:
        return [], ""
    if not isinstance(value, list):
        return [], f"Send {label} as a list."
    names = unique([scrub_contact(clean_text(v, name_len)) for v in value if isinstance(v, str)])
    names = [n for n in names if n]
    return (names, "") if len(names) <= limit else ([], f"Add {limit} or fewer {label}.")


def clean_job_extras(body: Dict[str, Any], current: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Check and clean the keys of version 2 of a job. Returns (values, errors).

    `values` has only the keys that are in `body` and are valid. A key that is missing, or None, is left out
    (a new job gets its default from the caller; an edit keeps the old value). `errors` has a message for each bad key.
    `current` is the job as stored. It is used for the check "minYears is not more than maxYears" when only one of them is sent.
    """
    values: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    # The level cannot be cleared: a missing or null level is "not sent" (a new job gets "Mid" from the caller).
    level = body.get("level")
    if level is not None:
        if isinstance(level, str) and level in LEVELS:
            values["level"] = level
        else:
            errors["level"] = "Choose a level."
    # These keys can be cleared: null (or an empty text) sets the value to "not set".
    for key in ("specialisation", "educationMin"):
        if key in body:
            if body[key] is None or isinstance(body[key], str):
                values[key] = scrub_contact(clean_text(body[key], 80)) or None
            else:
                errors[key] = "Enter this as text."
    # The specialisation must be one of the taxonomy (the check against the domain of the job is in the job form)
    if values.get("specialisation") and values["specialisation"] not in ALL_SPECIALISATIONS:
        errors["specialisation"] = "Choose a specialisation from the list."
        values.pop("specialisation")
    if "workMode" in body:
        if body["workMode"] is None or body["workMode"] == "":
            values["workMode"] = None
        elif isinstance(body["workMode"], str) and body["workMode"] in WORK_MODES:
            values["workMode"] = body["workMode"]
        else:
            errors["workMode"] = "Choose a work mode."
    for key in ("minYears", "maxYears"):
        if key in body:
            if body[key] is None or body[key] == "":
                values[key] = None
                continue
            try:
                values[key] = _years_value(body[key])
            except (ValueError, OverflowError):
                errors[key] = "Enter a number of years from 0 to 40."
    if "minYears" in body or "maxYears" in body:
        # compare with the value that the job has or will have. A key that failed its own check is not compared.
        def effective(key: str) -> Optional[float]:
            return None if key in errors else (values[key] if key in values else (current or {}).get(key))

        low, high = effective("minYears"), effective("maxYears")
        if low is not None and high is not None and low > high:
            errors["maxYears"] = "The maximum years must be the same as or more than the minimum years."
            values.pop("maxYears", None)

    if "skillRequirements" in body and body["skillRequirements"] is not None:
        reqs, problem = [], ""
        if not isinstance(body["skillRequirements"], list):
            problem = "Send the skills as a list."
        for item in body["skillRequirements"] if isinstance(body["skillRequirements"], list) else []:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                problem = "Each skill needs a name."
                break
            name = scrub_contact(clean_text(item["name"], 60))
            level_in = item.get("level")
            level_out = DEFAULT_SKILL_LEVEL if level_in is None else clean_skill_level(level_in)
            must = True if item.get("must") is None else item.get("must")
            if not name:
                problem = "Each skill needs a name."
            elif level_out is None:
                problem = "Choose a skill level from 1 to 5."
            elif not isinstance(must, bool):
                problem = "Say if each skill is required (true or false)."
            if problem:
                break
            if norm(name) not in {norm(r["name"]) for r in reqs}:
                reqs.append({"name": name, "level": level_out, "must": must})
        if not problem and len(reqs) > MAX_JOB_SKILLS:
            problem = f"Add {MAX_JOB_SKILLS} or fewer skills."
        if problem:
            errors["skillRequirements"] = problem
        else:
            values["skillRequirements"] = reqs

    if body.get("certifications") is not None:
        c = body["certifications"]
        if not isinstance(c, dict):
            errors["certifications"] = "Send the certifications as required and preferred lists."
        else:
            required, e1 = _name_list(c.get("required"), MAX_JOB_CERTIFICATIONS, 120, "required certifications")
            preferred, e2 = _name_list(c.get("preferred"), MAX_JOB_CERTIFICATIONS, 120, "preferred certifications")
            if e1 or e2:
                errors["certifications"] = e1 or e2
            else:
                values["certifications"] = {"required": required, "preferred": preferred}
    if body.get("awards") is not None:
        a = body["awards"]
        if not isinstance(a, dict):
            errors["awards"] = "Send the awards as a preferred list."
        else:
            preferred, e1 = _name_list(a.get("preferred"), MAX_JOB_AWARD_KINDS, 40, "preferred awards")
            kinds = unique([award_kind(x) for x in preferred]) if not e1 else []
            if e1:
                errors["awards"] = e1
            elif "" in kinds:
                errors["awards"] = "Choose award kinds from the list."
            else:
                values["awards"] = {"preferred": kinds}
    return values, errors


def extras_to_columns(values: Dict[str, Any]) -> Dict[str, Any]:
    """The database columns for clean values of version 2 (not the skills: see save_job_skills)."""
    cols: Dict[str, Any] = {}
    for key, col in (("level", "level"), ("specialisation", "specialisation"), ("minYears", "min_years"), ("maxYears", "max_years"),
                     ("workMode", "work_mode"), ("educationMin", "education_min")):
        if key in values:
            cols[col] = values[key]
    if "certifications" in values:
        cols["certs_required"] = jdump(values["certifications"]["required"])
        cols["certs_preferred"] = jdump(values["certifications"]["preferred"])
    if "awards" in values:
        cols["awards_preferred"] = jdump(values["awards"]["preferred"])
    return cols


def save_job_skills(conn: sqlite3.Connection, job_id: str, skills: List[str], requirements: Optional[List[Dict[str, Any]]] = None) -> None:
    """Replace the skills of a job. With `requirements` each skill has its level and "must". Without, the levels are NULL."""
    conn.execute("DELETE FROM job_skills WHERE job_id = ?", (job_id,))
    if requirements:
        rows = [(job_id, i, r["name"], r["level"], 1 if r["must"] else 0) for i, r in enumerate(requirements)]
    else:
        rows = [(job_id, i, s, None, 1) for i, s in enumerate(skills)]
    conn.executemany("INSERT INTO job_skills (job_id, position, skill, level, must) VALUES (?, ?, ?, ?, ?)", rows)


def clean_import_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """The `fields` of a job description that the reader found. The keys of version 2 go through the same checks as the job form.

    A value that is not valid is left out (the result is a draft: the employer can fill it in).
    """
    out = {k: v for k, v in fields.items() if k not in JOB_EXTRA_KEYS}
    values, _errors = clean_job_extras({k: fields[k] for k in JOB_EXTRA_KEYS if k in fields})
    out.update({k: v for k, v in values.items() if v is not None})
    if values.get("skillRequirements") and not out.get("skills"):
        out["skills"] = [r["name"] for r in values["skillRequirements"]]
    return out


_MONEY_RANGE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:-|–|—|to)\s*\$?\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?", re.I)
_MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?", re.I)
_UNIT_DAY = re.compile(r"per day|a day|/\s?day|daily|per diem|day rate", re.I)
_UNIT_HOUR = re.compile(r"per hour|an hour|/\s?(?:hour|hr)|hourly|p\.?h", re.I)


def parse_salary(text: Any) -> Tuple[Optional[float], Optional[float], str]:
    """(minimum, maximum, unit) from the pay text of a job, for example "$900 per day" or "$150,000 - $170,000 per year".

    The numbers are the numbers in the text (never changed). The unit is "day" for "per day", "a day" and similar, "hour" for "per hour"
    and similar, else "year". A text with no amount gives (None, None, unit). The formulas change the amounts to a yearly pay in one place."""
    t = str(text or "")
    unit = "day" if _UNIT_DAY.search(t) else "hour" if _UNIT_HOUR.search(t) else "year"

    def number(digits: str, k: Optional[str]) -> float:
        value = float(digits.replace(",", ""))
        return value * 1000 if k else value

    m = _MONEY_RANGE.search(t)
    if m:
        low = number(m.group(1), m.group(2))
        high = number(m.group(3), m.group(4))
        if m.group(4) and not m.group(2) and low < 1000 <= high:
            low *= 1000          # "$80-100k": the "k" is for both numbers
        return (low, high, unit) if low <= high else (high, low, unit)
    m = _MONEY.search(t)
    if m:
        value = number(m.group(1), m.group(2))
        return value, value, unit
    return None, None, unit


def money_text(smin: Optional[float], smax: Optional[float], unit: str) -> str:
    """The pay text of a job: "$900 per day", "$150,000 – $170,000 per year". "Market competitive" if there is no amount."""
    if not smin or not smax:
        return "Market competitive"
    fmt = lambda n: f"${n:,.0f}"  # noqa: E731
    span = fmt(smin) if smin == smax else f"{fmt(smin)} – {fmt(smax)}"
    return f"{span} per {unit}"


def suggest_skills(title: str, description: str) -> List[str]:
    """Skill names for a job form (for employers: "Suggest skills from the description"). Up to 10."""
    return job_skills(title, description, 10)


def summary_of(text: str, max_len: int = 200) -> str:
    """A short text for a job card: at most `max_len` characters. The full description is stored and shown without a cut.

    The headings ("## About the role") and the bullet marks of the description markup are left out. The text is the first
    sentences that fit in `max_len` characters. If the first sentence alone is longer, it is cut at a word and ends with the mark "…".
    """
    lines = [re.sub(r"^\s*[-*•]\s+", "", l) for l in str(text or "").splitlines() if not l.lstrip().startswith("#")]
    flat = re.sub(r"\s+", " ", " ".join(lines)).strip() or re.sub(r"\s+", " ", re.sub(r"^\s*#+\s*", "", str(text or ""), flags=re.M)).strip()
    if len(flat) <= max_len:
        return flat
    kept = ""
    for sentence in re.split(r"(?<=[.!?])\s+", flat):
        if len((kept + " " + sentence).strip()) > max_len:
            break
        kept = (kept + " " + sentence).strip()
    if kept:
        return kept
    cut = flat[:max_len - 1]                       # one place stays free for the "…" mark
    cut = cut[:cut.rfind(" ")] if " " in cut else cut
    return re.sub(r"[,.;:]$", "", cut) + "…"


def card(job: Dict[str, Any], match: Dict[str, Any]) -> Dict[str, Any]:
    """The job card fields. No full description, no owner and no internal fields."""
    out = {k: v for k, v in job.items() if k not in ("description", "ownerId", "targetApplicants", "editedAt", "salaryMin", "salaryMax")}
    out["status"] = "open" if is_open(job) else "closed"
    out["match"] = match
    return out


# =====================================================================
# The talent context: everything the ranking needs about one talent
# =====================================================================
RECOMMEND_MIN_SCORE = 45.0   # a job is "recommended" when its match score (0.55 fit + 0.45 FRS*) is at least this


class TalentContext:
    """A talent's profile, skills and behaviour (saved and skipped jobs), ready for ranking against the jobs.

    The ranking uses the formulas: `fit` of Formula 1 and the feed score of Formula 5 (with its employer diversity penalty, then the
    feedback loop). The feed ranks ALL the open jobs together, so that the score of a job is the same in a list and on its page.
    """

    def __init__(self, user_id: str, alias: str, profile: Optional[Dict[str, Any]], shared: List[Dict[str, Any]],
                 saved_companies: Set[str], saved_categories: Set[str], ignored_counts: Dict[str, int],
                 index: Any = None, jobs: Optional[List[Dict[str, Any]]] = None):
        self.user_id = user_id
        self.alias = alias
        self.profile = profile
        self.shared = shared
        self.saved_companies = saved_companies
        self.saved_categories = saved_categories
        self.ignored_counts = ignored_counts
        self.jobs: List[Dict[str, Any]] = jobs or []
        p = profile or {}
        self.industries = set(as_list(p.get("targetIndustries")) + as_list(p.get("industry")))
        self.locations = set(as_list(p.get("locations")))
        self.modes = set(as_list(p.get("workModes")))
        self.types = set(as_list(p.get("workTypes")))
        self._engine_candidate: Optional[Dict[str, Any]] = None
        self._prepared: Optional[Dict[str, Any]] = None
        self._open: Optional[Dict[str, Dict[str, Any]]] = None      # job id -> {"jd": prepared job, "fit": F1 result, "feed": F5 item}
        self._matches: Dict[str, Dict[str, Any]] = {}

    # ----- the dictionaries for the formulas -----
    @property
    def engine_candidate(self) -> Dict[str, Any]:
        """The dictionary for Formulas 1, 2 and 5. It is for this talent's own screens, so it has the whole profile."""
        if self._engine_candidate is None:
            self._engine_candidate = eb.candidate_dict(self.profile or {}, self.shared, self.alias, self.user_id, private=True)
        return self._engine_candidate

    @property
    def prepared(self) -> Dict[str, Any]:
        """The talent dictionary after the cleaning of the engine (made once)."""
        if self._prepared is None:
            self._prepared = eb.prepare_candidate(self.engine_candidate)
        return self._prepared

    def level_of(self, skill: str) -> Optional[int]:
        """The talent's level (1 to 5) in a skill, or None if the talent does not have the skill. A related skill does not count.
        A skill with no level of its own has the level of its evidence (F8). A skill that the talent only typed is level 3."""
        entry = eb._load("f1").C.skill_entry(skill)
        held = self.prepared["skills"].get(entry["key"]) if entry else None
        return int(round(held["level"])) if held else None

    # ----- the formulas for all open jobs -----
    def _analyse_open(self) -> Dict[str, Dict[str, Any]]:
        if self._open is None:
            self._open = {}
            if self.profile:
                cand = self.prepared
                prepared = {j["id"]: eb.prepare_job(eb.job_dict(j)) for j in self.jobs if is_open(j)}
                feed = eb.feed_scores(cand, list(prepared.values()))
                for jid, pj in prepared.items():
                    fit = eb.job_fit(cand, pj)
                    if fit is not None and jid in feed:
                        self._open[jid] = {"jd": pj, "fit": fit, "feed": feed[jid]}
        return self._open

    def analyse(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """{jd, fit, feed} for one job: the prepared job and the results of Formulas 1 and 5. None if there is no profile or a formula fails.

        An open job is ranked in the list of all open jobs. A closed job is ranked with the open jobs, but it does not change their scores."""
        if not self.profile:
            return None
        found = self._analyse_open().get(job["id"])
        if found is not None:
            return found
        if is_open(job):
            return None
        pj = eb.prepare_job(eb.job_dict(job))
        feed = eb.feed_scores(self.prepared, [v["jd"] for v in self._analyse_open().values()] + [pj]).get(job["id"])
        fit = eb.job_fit(self.prepared, pj)
        return {"jd": pj, "fit": fit, "feed": feed} if fit is not None and feed is not None else None

    # ----- the match of one job -----
    def match_for(self, job: Dict[str, Any]) -> Dict[str, Any]:
        found = self._matches.get(job["id"])
        if found is not None:
            return found
        a = self.analyse(job)
        match = self._match(job, a) if a else self._empty_match(job)
        self._matches[job["id"]] = match
        return match

    def _empty_match(self, job: Dict[str, Any]) -> Dict[str, Any]:
        items = skill_match([{"name": r["name"], "level": r["level"], "must": r["must"]} for r in requirements_of(job)], {})
        return {"coverage": items["coverage"], "skills": items["items"], "matchedSkills": [], "partialSkills": [],
                "gaps": [i["name"] for i in items["items"]], "reasons": [], "notes": ["Add skills to your profile to see how this job fits you"],
                "rank": 0, "score": 0.0, "recommended": False}

    def _match(self, job: Dict[str, Any], a: Dict[str, Any]) -> Dict[str, Any]:
        fit, feed = a["fit"], a["feed"]
        frs = round(eb.behavioural_adjust(feed["feed_ranking_score"], job["company"], job["category"],
                                          self.saved_companies, self.saved_categories, self.ignored_counts), 1)
        score = round(FIT_WEIGHT * fit["fit"] + FRS_WEIGHT * frs, 1)
        res = results_from_breakdown(fit["skill_breakdown"], fit.get("skill_coverage"))
        items = res["items"]
        reasons, notes = self._reasons(job, fit, res)
        return {
            "coverage": res["coverage"], "skills": items,
            "matchedSkills": [i["name"] for i in items if i["fitStatus"] == "meets"],
            "partialSkills": [i["name"] for i in items if i["status"] == "partial"],
            "gaps": [i["name"] for i in items if i["status"] == "gap"],
            "reasons": reasons, "notes": notes, "rank": _js_round(score), "score": score,
            "recommended": score >= RECOMMEND_MIN_SCORE,
        }

    def _reasons(self, job: Dict[str, Any], fit: Dict[str, Any], res: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        reasons: List[str] = []
        notes: List[str] = []
        parts = fit.get("parts") or {}
        if (parts.get("occupation") or 0) >= 70:
            reasons.append(f"Matches your target role ({job['occupation']})" if job.get("occupation") else "Matches your target role")
        n = len(res["items"])
        meets = sum(1 for i in res["items"] if i["fitStatus"] == "meets")
        below = sum(1 for i in res["items"] if i["fitStatus"] == "below")
        related = sum(1 for i in res["items"] if i["fitStatus"] == "related")
        if meets or below or related:
            text = f"You meet {meets} of the {n} skills" if meets else f"You have some of the {n} skills"
            extra = ([f"{below} below the asked level"] if below else []) + ([f"{related} related"] if related else [])
            reasons.append(text + (" (" + ", ".join(extra) + ")" if extra else ""))
        if job.get("level") and (parts.get("level") or 0) >= 85:
            reasons.append(f"The level of this job fits you ({job['level']})")
        if job["category"] in self.industries:
            reasons.append(f"In a domain you chose: {job['category']}")
        location_hit = job["location"] in self.locations or (job.get("workMode") == "Remote" and "Remote" in self.modes | self.locations)
        if location_hit:
            reasons.append(f"Location you prefer: {job['location']}")
        if self.types and job["type"] not in self.types:
            notes.append(f"This role is {job['type']}")
        if self.locations and not location_hit:
            notes.append(f"Location: {job['location']}")
        if not job["skills"]:
            notes.append("This job lists no skills yet")
        return reasons, notes

    def frs_star(self, jobs: List[Dict[str, Any]]) -> Dict[str, float]:
        """FRS* for each job id: the feed score of Formula 5 (with the diversity penalty) after the feedback loop."""
        out = {}
        for j in jobs:
            a = self.analyse(j)
            if a:
                out[j["id"]] = round(eb.behavioural_adjust(a["feed"]["feed_ranking_score"], j["company"], j["category"],
                                                           self.saved_companies, self.saved_categories, self.ignored_counts), 1)
        return out

    def rank_all(self, jobs: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """[(job, match)] for these jobs, in the same order. match.score = round(0.55 fit + 0.45 FRS*, 1), one decimal (0 to 100).

        The ranking is made with all open jobs, so a job has the same score in every list and on its page."""
        return [(j, self.match_for(j)) for j in jobs]


def _posted_ts(job: Dict[str, Any]) -> float:
    d = parse_iso(job.get("postedAt"))
    return d.timestamp() if d else 0.0


def _by_rank(pair: Tuple[Dict[str, Any], Dict[str, Any]]):
    job, match = pair
    return (-match["score"], -_posted_ts(job), job["id"])


# The sort values of the job lists (V2_PLAN.md, section 5.1). Ties are broken by the id, so that the order is stable.
def _sort_key_best(pair: Tuple[Dict[str, Any], Dict[str, Any]]):
    return (-pair[1]["score"], pair[0]["id"])


def _sort_key_newest(pair: Tuple[Dict[str, Any], Dict[str, Any]]):
    return (-_posted_ts(pair[0]), pair[0]["id"])


def sort_pairs(pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]], sort: str) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Sort (job, match) pairs. `best`: the fit score, highest first. `newest`: the posting date, newest first."""
    return sorted(pairs, key=_sort_key_newest if sort == "newest" else _sort_key_best)


# =====================================================================
# Recommend, search, detail
# =====================================================================
def recommended_pairs(ctx: TalentContext, jobs: List[Dict[str, Any]], exclude: Set[str]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """All open jobs that are not skipped or applied, with match.recommended (Feature 3 AC1, AC2), as (job, match). Not sorted."""
    if not ctx.profile:
        return []
    pool = [j for j in jobs if is_open(j) and j["id"] not in exclude]
    return [(j, m) for j, m in ctx.rank_all(pool) if m["recommended"]]


def recommend(ctx: TalentContext, jobs: List[Dict[str, Any]], limit: int, exclude: Set[str]) -> List[Dict[str, Any]]:
    """The `limit` best recommended jobs as cards, best rank first. The lists of the API use recommended_pairs and a page."""
    ranked = sorted(recommended_pairs(ctx, jobs, exclude), key=_by_rank)
    return [card(j, m) for j, m in ranked[:limit]]


def search_pairs(ctx: TalentContext, jobs: List[Dict[str, Any]], q: str, location: str, exclude: Set[str]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Keyword search over title, company, occupation, category, skills and area. Open jobs that are not skipped. As (job, match), not sorted."""
    terms = [t for t in norm(q).split() if t]
    hits = []
    for j in jobs:
        if not is_open(j) or j["id"] in exclude:
            continue
        if location and j["location"] != location:
            continue
        hay = norm(f"{j['title']} {j['company']} {j['occupation']} {j['category']} {j.get('specialisation') or ''} {' '.join(j['skills'])} {j['area']}")
        if all(t in hay for t in terms):
            hits.append(j)
    return ctx.rank_all(hits)


def similar_jobs(ctx: TalentContext, job: Dict[str, Any], jobs: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """Up to 3 open jobs with the same ANZSCO code or 2 or more shared skills, in order of Formula 3 (JPI)."""
    mine = set(job["skills"])
    near = [j for j in jobs if j["id"] != job["id"] and is_open(j)
            and ((job["anzsco"] and j["anzsco"] == job["anzsco"]) or len(mine.intersection(j["skills"])) >= 2)]
    ranked = sorted(ctx.rank_all(near), key=_by_rank)[:60]  # Formula 3 runs on the 60 best-ranked jobs only
    base = eb.job_dict(job)
    out = []
    for j, m in ranked:
        res = eb.proximity(base, eb.job_dict(j))
        jpi = res["job_proximity_index"] if res else 0.0
        out.append((jpi, j, m, res))
    out.sort(key=lambda t: (-t[0], -t[2]["rank"], -_posted_ts(t[1]), t[1]["id"]))
    cards = []
    for jpi, j, m, res in out[:limit]:
        c = card(j, m)
        if res:
            c["similarity"] = {"index": jpi, "tier": res["operational_tier"],
                               "salaryChange": res["differentials"]["salary_delta_label"] if (job.get("salaryMax") and j.get("salaryMax")) else None}
        cards.append(c)
    return cards


def formula_values(ctx: TalentContext, job: Dict[str, Any]):
    """Formulas 1, 2 and 5 for one talent and one job: (F1 skill match, F2 gaps, F5 feed item, prepared job). None if one of them fails."""
    a = ctx.analyse(job)
    if not a:
        return None
    f1 = eb.smf(ctx.prepared, a["jd"])
    f2 = eb.gap_analysis(ctx.prepared, a["jd"])
    return (f1, f2, a["feed"], a["jd"]) if f1 and f2 else None


def fit_axes_for(ctx: TalentContext, job: Dict[str, Any], match: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
    """The radar values for one job (see engine_bridge.JOB_FIT_AXES)."""
    if not ctx.profile:
        return None
    found = formula_values(ctx, job)
    return eb.job_fit_axes(*found[:3]) if found else None


def bridge_for(ctx: TalentContext, job: Dict[str, Any], match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formulas 1, 2 and 5 for one job: how well the job fits, which gaps matter, and how long they take to close.

    `path` is the answer of Formula 2 for "Your path to this job": a radar of the requirements, the list of what fits and the list of gaps.
    This is for the talent only. It describes the talent's own path to this job. Employers never get it.
    """
    if not ctx.profile:
        return None
    found = formula_values(ctx, job)
    if not found:
        return None
    f1, f2, f5, jd = found
    gaps = [{
        "name": g["gap_name"], "category": g["category_code"], "categoryName": g["category_name"],
        "months": g["duration_months"], "blocker": bool(g["is_statutory_blocker"]),
    } for g in sorted(f2["classified_gaps"], key=lambda g: -g["severity_points"])]
    return {
        "occupation": {
            "anzsco": jd["code"], "title": jd["anzsco_title"] or job["occupation"] or job["title"],
            "alignment": f1["final_match_score"], "tier": f1["match_tier"], "tierCode": f1["match_tier_code"],
        },
        "readiness": {
            "gapSeverity": f2["gap_severity_index"], "readiness": f2["job_readiness_score"],
            "months": f2["estimated_bridge_months"], "tier": f2["readiness_tier"], "tierCode": f2["readiness_tier_code"],
            "statutoryBlocker": bool(f2["has_statutory_blocker"]),
        },
        "gaps": gaps,
        "path": eb.path(ctx.prepared, jd),
        "axes": eb.job_fit_axes(f1, f2, f5),
        "score": match["score"],
    }


def job_detail(ctx: TalentContext, jobs: List[Dict[str, Any]], job_id: str) -> Optional[Dict[str, Any]]:
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return None
    match = ctx.match_for(job)
    out = card(job, match)
    out["description"] = job["description"]
    out["similar"] = similar_jobs(ctx, job, jobs)
    out["bridge"] = bridge_for(ctx, job, match)
    return out
