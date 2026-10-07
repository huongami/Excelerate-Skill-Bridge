"""Read a CV text and pre-fill the profile fields (Feature 2, AC2 and AC6; version 2: item R1).

This is a rule-based reader. It does not call an AI service, so no CV text leaves the server.
The text of a CV is DATA: nothing in it is followed as an instruction (AI_Rule Rule 5, item 10).

A field that the CV does not show stays empty and is listed in "missing". The reader never invents a value.

Version 2 adds the current role, the wish for a job (the target role), the level, the exact years, the certifications, the awards and the
level of each skill. The rules for each field are in docs/changes/CV.md. In short:

  current role  1 a position with an open end (Present, Current, Now, to date)  2 the position with the latest end date
                3 the title under or above the name (the headline)  4 a label ("Occupation or position held: ...")
                5 a sentence "Data analyst with 6 years of experience"
  target role   a role of the role list that stands in a sentence of wish ("seeking", "looking for", "open to" ...) or after a label
  level         1 the level words in the title of the current role  2 the level words in the headline  3 a student or a graduate
                4 the years (under 2: Junior, 2 to 5: Mid, from 5: Senior). Lead and Principal come only from title words.
  years         the work years of the positions (overlaps are counted once), or the "N years" sentences. The bigger number.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import cv_lexicon
from . import reference as R
from .util import scrub_contact

_YEARS = list(getattr(R, "YEARS", ["Less than 1 year", "1–2 years", "3–5 years", "6–10 years", "More than 10 years"]))     # the bands of the profile
_MAX_LINES = 1500
_MAX_LINE = 300
_STRICT = False        # a test sets this to True: an error in a reader is raised. Without it, the reader of one field never stops the others.

# =====================================================================
# Sections
# =====================================================================
# Each heading is written as a key: lower case, letters only, "&" and "/" are "and". The first kind that matches wins.
_HEADINGS: List[Tuple[str, str]] = [
    ("objective", r"(?:(?:career|job|professional|employment|personal|main) )?(?:objectives?|goals?|aims?)|looking for|what i am looking for|what i'm looking for|"
                  r"desired (?:position|role|job)|target (?:role|position|job)|career intent"),
    ("summary", r"(?:(?:professional|career|executive|personal|candidate) )?(?:summary|profile|overview|statement)|about|about me|personal statement|introduction|bio|"
                r"who i am|summary and objective|profile summary"),
    ("experience", r"(?:(?:professional|relevant|work|employment|career|industry|selected|recent|related|practical|technical|research) )?"
                   r"(?:experience|work history|employment history|employment record|career history|positions held|history)|"
                   r"work|employment|career|internships?|professional background|professional history|experience summary|"
                   r"(?:work )?experience and (?:internships|projects)|work and (?:internships|projects)|employment and experience"),
    ("education", r"education(?: and (?:training|qualifications|certifications|certificates|courses|professional development))?|"
                  r"academic(?: background| qualifications| record| history)?|qualifications(?: and education)?|studies|training and education|"
                  r"educational background|academic and professional qualifications"),
    ("skills", r"(?:(?:key|core|technical|professional|relevant|personal|top|main|it|computer|digital|job related) )?(?:skills|competencies|competences)|"
               r"skills and (?:tools|abilities|competencies|technologies|languages|expertise|interests)|areas of expertise|expertise|technologies|tech stack|"
               r"technical (?:proficiency|proficiencies|expertise|summary|knowledge|stack)|tools(?: and technologies)?|programming languages|"
               r"languages and (?:frameworks|tools|technologies)"),
    ("certs", r"(?:(?:professional|technical|industry|relevant) )?(?:certifications?|certificates?|licen[cs]es?|accreditations?)"
              r"(?: and (?:licen[cs]es?|certifications?|training|courses))?|licen[cs]es and certifications|courses(?: and certifications?)?|"
              r"training(?: and certifications?| courses)?|professional development|online courses|certifications? and training|courses and training"),
    ("awards", r"(?:awards?|honou?rs?|accolades|recognition|prizes?|scholarships?|competitions?|hackathons?)"
               r"(?: and (?:awards?|honou?rs?|achievements?|recognition|scholarships?|prizes?))?|honou?rs and awards|honou?rs awards?|"
               r"achievements? and awards?|awards? and (?:achievements?|recognition|honou?rs?|publications)|honou?rs and scholarships"),
    ("awards_weak", r"(?:(?:key|major|notable|selected) )?(?:achievements?|accomplishments?)|"
                    r"(?:(?:selected|recent|key|peer reviewed|refereed|journal|conference|research|academic|representative) )*(?:publications?|papers)"),
    ("projects", r"(?:(?:personal|side|selected|academic|key|notable|open source|relevant|technical) )?(?:projects?|portfolio)|open source(?: contributions?)?|"
                 r"selected (?:shipped )?(?:titles|games|releases|works?)|shipped titles|key deliverables|selected deliverables|"
                 r"projects and (?:publications|achievements)"),
    ("languages", r"languages?|language skills|spoken languages|languages spoken"),
    ("contact", r"contact(?: details| information| me)?|personal (?:details|information|data)"),
    ("other", r"interests?|hobbies|hobbies and interests|interests and hobbies|activities|extracurricular activities|volunteer(?:ing)?(?: experience| work)?|"
              r"community(?: involvement)?|references?|referees?|publications?|patents?|additional information|other|miscellaneous|extra"),
]
# More names that people give to the parts of a CV (found when the reader was tried on CVs that it had not seen)
_MORE_HEADINGS = {
    "objective": r"where i want to go|where i am heading|next step|next role|what i am after|what i want|my goals?|career aims?|the next step",
    "summary": r"(?:career|professional|personal) snapshot|snapshot|at a glance|in brief|my story|what i do|a little about me|personal summary|my profile|"
               r"about me and my work",
    "experience": r"roles held|roles|positions|jobs|past roles|previous roles|where i worked|what i have done|what i've done|what i did|my experience|work record|"
                  r"track record|my career|professional roles|roles and responsibilities|relevant work|employment history and experience|"
                  r"(?:(?:professional|relevant|work(?:ing)?|employment|career|industry|selected|recent|related|practical|technical|contract(?:ing)?|freelance|consulting|"
                  r"full time|permanent|past|previous|prior|part time|casual|temporary|summer|student) (?:and )?){1,3}(?:experience|history|record|engagements?|assignments?|roles|positions|work|jobs)",
    "education": r"formal learning|study|degrees|schooling|formal education|education and qualifications|academic study",
    "skills": r"toolbox|toolkit|tool kit|technical toolkit|stack|technology|tech skills|what i work with|capabilities|strengths|core strengths|"
              r"technical strengths|software|tools and languages|languages and tools|tooling|knowledge skills and abilities|ksas?|tools and methods|methods and tools|"
              r"tools and techniques|hardware and tools|software and tools|skills and tools|skills matrix|competency matrix",
    "certs": r"credentials|professional credentials|badges|learning|courses and certificates|certificates and courses|certifications and courses|"
             r"licen[cs]es and certificates|accreditation|training and development|short courses|"
             r"professional development and (?:certifications?|certificates?|training|courses)|"
             r"(?:(?:professional|technical|industry|relevant|additional|other|short|online|specialised|specialized) )*"
             r"(?:(?:trainings?|courses?|workshops?|seminars?|certifications?|certificates?|licen[cs]es?|accreditations?|credentials|badges)(?: and | )?){1,3}",
    "awards": r"papers and prizes|prizes and papers|papers|talks|talks and papers|patents|patents and talks|talks and patents|publications and awards|"
              r"recognitions|papers and awards|talks and publications|awards and talks",
    "other": r"career break|career gap|gap year|declaration|extras|volunteer|teaching|teaching experience|academic service|professional service|service|mentoring|outreach|"
             r"research interests|reviewing|professional memberships?|memberships?|affiliations?|professional affiliations?|personal particulars|"
             r"character references?|references and declaration|referees? and declaration|hobbies|interests and activities|leadership and activities|additional|"
             r"additional details|supporting information|personal|availability|work authori[sz]ation|extra curricular|extra curricular activities|extracurricular activities|"
             r"community involvement|community and leadership",
}
_HEADING_RE = [(kind, re.compile(rf"^(?:{rx}|{_MORE_HEADINGS.get(kind, '(?!)')})$")) for kind, rx in _HEADINGS]


def _header_of(line: str) -> Optional[str]:
    """The kind of section that a heading line starts, or None if the line is not a heading."""
    if len(line) > 48 or "@" in line or _RANGE_RE.search(line):
        return None                    # a heading has no dates: "Career break (Apr 2018 – Sep 2019)" is an entry of a list
    key = re.sub(r"\([^)]*\)", " ", line.lower())
    key = re.sub(r"\s*[&/+]\s*", " and ", key)
    key = re.sub(r"[^a-z' ]", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    if not key or len(key.split()) > 6:
        return None
    for kind, rx in _HEADING_RE:
        if rx.match(key):
            return kind
    words = [w for w in key.split() if w != "and"]
    if words and all(_AWARD_HEAD_WORD.match(w) for w in words) and any(_AWARD_HEAD_STRONG.match(w) for w in words):
        return "awards"                # "Patents and Awards", "Awards and Fellowships": names of lists of awards, put together
    return None


_AWARD_HEAD_WORD = re.compile(r"^(?:awards?|honou?rs?|accolades|recognitions?|prizes?|scholarships?|fellowships?|competitions?|hackathons?|achievements?|"
                              r"patents?|talks?|papers?|distinctions?|grants?|speaking|presentations?|publications?|contributions?|medals?|"
                              r"extracurricular|extra|curricular|leadership|activities|community|open|source|and)$")
_AWARD_HEAD_STRONG = re.compile(r"^(?:awards?|honou?rs?|accolades|recognitions?|prizes?|scholarships?|fellowships?|competitions?|hackathons?|patents?|distinctions?|medals?)$")


class _Sec:
    """A part of the CV: the lines[start:end] after a heading (kind "top" is the part before the first heading)."""
    __slots__ = ("kind", "start", "end", "head")

    def __init__(self, kind: str, start: int, end: int, head: str = ""):
        self.kind, self.start, self.end, self.head = kind, start, end, head      # head: the text of the heading


def _split_sections(lines: List[str]) -> List[_Sec]:
    secs = [_Sec("top", 0, 0)]
    for i, line in enumerate(lines):
        kind = _header_of(line)
        if kind == "awards_weak" and secs[-1].kind in ("experience", "projects"):
            kind = None          # "Achievements" inside a job is a list of bullets of that job, not a section
        if kind:
            secs[-1].end = i
            secs.append(_Sec(kind, i + 1, i + 1, line))
    secs[-1].end = len(lines)
    return secs


_INLINE_HEADING = re.compile(r"^(skills|technical skills|key skills|core skills|technologies|tech stack|tools)(\s*:\s*|\s+)(\S.*[,|·].*)$", re.I)


def _split_inline_headings(lines: List[str]) -> List[str]:
    """A heading that shares its line with the list ("Skills   Python, SQL, Docker", a heading in the margin) becomes two lines.
    With a colon ("Skills: Python, SQL") it is a heading too, unless the line is inside a job or a project ("Technologies: Python, Spark")."""
    out: List[str] = []
    kind = "top"
    for line in lines:
        m = _INLINE_HEADING.match(line)
        if m and len(m.group(3).split()) >= 2 and (":" not in m.group(2) or kind not in ("experience", "projects")):
            out.extend([m.group(1), m.group(3)])
            kind = "skills"
            continue
        if _GAP in line:
            # A row of a form ("Certifications<gap>Oracle Certified Professional", as in the Europass CV): the label is the heading, the value is the list
            label, _, value = line.partition(_GAP)
            label_kind = _header_of(label) if len(label.split()) <= 4 and not label.rstrip().endswith(":") else None
            if label_kind == "languages" and kind == "skills":
                label_kind = None             # "Languages   Python, SQL" inside the skills: the programming languages, not the spoken ones
            if (label_kind in ("skills", "certs", "awards", "education", "summary", "objective", "languages")
                    and value.strip() and not value.lstrip().startswith((":", "-", "=")) and _header_of(value.strip()) is None):
                out.extend([label, value.strip()])
                kind = label_kind
                continue
        head = _header_of(line)
        if head and not (head == "awards_weak" and kind in ("experience", "projects")):
            kind = head
        out.append(line)
    return out


def _lines_of(lines: List[str], secs: List[_Sec], *kinds: str) -> List[str]:
    return [l for s in secs if s.kind in kinds for l in lines[s.start:s.end]]


def _indices_of(secs: List[_Sec], *kinds: str) -> List[int]:
    return [i for s in secs if s.kind in kinds for i in range(s.start, s.end)]


# =====================================================================
# Qualifications
# =====================================================================
_QUAL_RULES = [
    (re.compile(r"\b(ph\.?\s?d|doctorate|doctor of)\b"), "Doctorate (PhD)"),
    (re.compile(r"\bmba\b|master of business administration"), "MBA"),
    (re.compile(r"\b(master|masters|master's|m\.?sc|m\.?eng|m\.?a\.|msc|postgraduate degree)\b"), "Master's degree"),
    (re.compile(r"graduate diploma"), "Graduate diploma"),
    (re.compile(r"graduate certificate"), "Graduate certificate"),
    (re.compile(r"\bbachelor.{0,40}honou?rs|\bhonou?rs degree"), "Bachelor's degree (Honours)"),
    (re.compile(r"\b(bachelor|bachelors|bachelor's|b\.?sc|bsc|b\.?eng|b\.?tech|btech|b\.?com|bcom|b\.?a\.|undergraduate degree|b\.e\.)\b"), "Bachelor's degree"),
    (re.compile(r"advanced diploma"), "Advanced diploma"),
    (re.compile(r"associate degree"), "Associate degree"),
    (re.compile(r"certificate (iii|iv|3|4)\b|cert\.? (iii|iv)\b"), "Certificate III or IV"),
    (re.compile(r"\bdiploma\b"), "Diploma"),
    (re.compile(r"high school|secondary school|\bhsc\b|year 12|higher school certificate"), "High school"),
]
_QUAL_ORDER = {q: i for i, q in enumerate([
    "Doctorate (PhD)", "MBA", "Master's degree", "Graduate diploma", "Graduate certificate", "Bachelor's degree (Honours)",
    "Bachelor's degree", "Advanced diploma", "Associate degree", "Diploma", "Certificate III or IV", "High school"])}

# ---------- Fields of study: the list names, and other words that point to a list name ----------
_FIELD_ALIASES = {
    # Only names of the field list of the platform (the taxonomy). A word that is not here is not turned into a name of another field (no nursing, no law ...).
    "information technology": "Information technology", "computer science": "Computer science", "software engineering": "Software engineering",
    "information systems": "Information systems", "data science": "Data science", "cyber security": "Cyber security", "cybersecurity": "Cyber security",
    "economics": "Economics", "mathematics": "Mathematics", "applied mathematics": "Mathematics", "statistics": "Statistics", "physics": "Physics",
    "artificial intelligence": "Artificial intelligence", "machine learning": "Artificial intelligence",
    "electrical and computer engineering": "Electrical and computer engineering", "computer engineering": "Electrical and computer engineering",
    "electrical engineering": "Electrical and computer engineering", "informatics": "Information technology", "computing": "Computer science",
    "information security": "Cyber security",
}
for _f in list(R.FIELDS_OF_STUDY) + [f for f in cv_lexicon.get().fields_of_study]:
    _FIELD_ALIASES.setdefault(_f.lower(), _f)
_FIELD_KEYS = sorted(_FIELD_ALIASES, key=len, reverse=True)

# ---------- Roles (the words of old: kept, because the reader of the roles for the list and read_roles use them) ----------
_TITLE_WORDS = (
    "manager|engineer|analyst|coordinator|officer|lead|leader|specialist|assistant|executive|director|supervisor|owner|developer|"
    "accountant|nurse|teacher|consultant|administrator|architect|designer|technician|scientist|representative|associate|intern|"
    "head|chef|clerk|planner|buyer|auditor|programmer|tester|trainer|recruiter|advisor|adviser|controller|superintendent|foreman|"
    "therapist|pharmacist|lecturer|tutor|researcher|operator|driver|agent|writer|strategist|producer|editor|bookkeeper|surveyor"
)
_TITLE_RE = re.compile(rf"\b({_TITLE_WORDS})\b", re.I)
_COMPANY_WORDS = re.compile(r"\b(ltd|limited|pty|inc|llc|co\.|company|corporation|corp|group|bank|university|college|school|institute|"
                            r"hospital|clinic|council|department|ministry|plc|gmbh|jsc|holdings|solutions|services|agency)\b", re.I)
_VERB_START = re.compile(r"^(managed|led|developed|built|created|designed|responsible|worked|ran|handled|prepared|improved|reduced|"
                         r"increased|delivered|supported|coordinated|implemented|maintained|achieved|provided|performed|conducted|"
                         r"owned|oversaw|trained|negotiated|analysed|analyzed|wrote|launched|organised|organized|processed)\b", re.I)

# The first word of a bullet that tells what a person did (not a title)
_VERBS = set("""managed led developed built created designed responsible worked ran handled prepared improved reduced increased delivered supported coordinated
implemented maintained achieved provided performed conducted owned oversaw trained negotiated analysed analyzed wrote launched organised organized processed
collaborated mentored migrated optimised optimized automated architected spearheaded drove established introduced integrated authored deployed configured
monitored tested debugged refactored documented presented published contributed partnered streamlined engineered orchestrated modelled modeled evaluated
defined shipped scaled leveraged utilised utilized assisted helped participated reviewed resolved researched investigated identified initiated mapped moved
cut raised kept set fixed added used applied ensured enabled enhanced expanded executed facilitated formulated generated guided operated planned produced
proposed reported rebuilt replaced restructured secured simplified standardised standardized supervised updated upgraded validated came joined started
became took gave made saw taught drove cleaned forecast forecasted reported""".split())
_VERB_TITLE_OK = {"managed", "applied", "integrated", "embedded"}       # a title can start with these words ("Applied Scientist")
_GERUND_OK = {"engineering", "consulting", "marketing", "accounting", "programming", "testing", "training", "operating", "learning", "manufacturing",
              "computing", "networking", "recruiting", "staffing", "trading", "planning", "reporting", "scheduling", "publishing", "sourcing", "advertising",
              "banking", "lecturing", "teaching", "building"}
_SENT_STOP = {"to", "the", "with", "that", "which", "who", "where", "when", "using", "by", "across", "into", "from", "a", "an", "i", "my", "our", "we",
              "is", "are", "was", "were", "has", "have", "had", "will", "you", "your", "their", "this", "these", "those", "as", "on", "for", "about",
              "than", "per", "over", "under", "while", "through", "between", "within", "around", "its", "it", "be", "been", "being", "can", "could",
              "should", "would", "may"}
_STRONG_NOUNS = {"engineer", "developer", "analyst", "scientist", "architect", "intern", "programmer", "consultant", "administrator", "researcher",
                 "specialist", "designer", "tester", "technician", "statistician", "trainee", "apprentice", "manager", "owner", "dev", "sre", "dba", "cto",
                 "swe", "sde"}
_DOMAIN_WORDS = {"data", "software", "machine", "learning", "ai", "ml", "cloud", "devops", "backend", "frontend", "fullstack", "full", "stack", "web", "security",
                 "analytics", "business", "bi", "platform", "mobile", "qa", "test", "research", "applied", "systems", "network", "embedded", "database", "etl",
                 "nlp", "vision", "computer", "deep", "big", "site", "reliability", "solutions", "technical", "engineering", "product", "quality", "automation",
                 "infrastructure", "mlops", "generative", "java", "python", ".net", "ios", "android", "sql", "reporting"}
_CASING = {"devops": "DevOps", "mlops": "MLOps", "dataops": "DataOps", "ios": "iOS", "javascript": "JavaScript", "typescript": "TypeScript", ".net": ".NET",
           "llmops": "LLMOps", "fullstack": "Fullstack", "nodejs": "Node.js", "qa": "QA", "ai": "AI", "ml": "ML", "bi": "BI", "etl": "ETL", "nlp": "NLP",
           "ui": "UI", "ux": "UX", "it": "IT", "sre": "SRE", "dba": "DBA", "cto": "CTO", "cio": "CIO", "cdo": "CDO", "ciso": "CISO", "sdet": "SDET",
           "swe": "SWE", "llm": "LLM", "sql": "SQL", "aws": "AWS", "gcp": "GCP", "api": "API", "php": "PHP", "sr": "Sr", "jr": "Jr"}
_SMALL = {"of", "in", "and", "for", "the", "a", "an", "at", "to", "on"}

_INDUSTRY_WORDS = {
    # Only the three domains of the platform (the profile keeps nothing else). The domain of a CV comes from cv_lexicon.domains_of; these words are the
    # fallback for a short text (the job description reader uses them for the category when the taxonomy gives no domain).
    "Software Engineering": r"software|developer|programming|\bapi\b|devops|back[- ]?end|front[- ]?end|full[- ]?stack|mobile|\bsre\b|microservice|\bqa\b|cloud|embedded|firmware",
    "AI & Machine Learning": r"machine learning|deep learning|\bnlp\b|computer vision|\bllm|generative ai|data scientist|mlops|neural|pytorch|tensorflow",
    "Data": r"data engineer|data analy|analytics|business intelligence|\bsql\b|data warehouse|\betl\b|dashboard|power bi|tableau|\bbi\b|data pipeline|database",
}
_INDUSTRY_RE = {k: re.compile(v, re.I) for k, v in _INDUSTRY_WORDS.items()}

_EDU_LINE = re.compile(r"universit|college|bachelor|master|diploma|degree|school|gpa|graduat|certificate|campus|academy|institute", re.I)
_BULLET_START = re.compile(r"^[•·▪●○◦‣⁃∙■□◆◇➢➤➔▶►✓✔*]+\s*|^[-–—]\s+")
_CONTACT_RE = re.compile(r"@|https?://|www\.|linkedin\.com|github\.com|\+?\d[\d ()-]{7,}\d")


# =====================================================================
# Dates
# =====================================================================
_MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_MON = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_Y = r"(?:19|20)\d{2}"
_DATE = (rf"(?:\d{{1,2}}[/.]\d{{1,2}}[/.]{_Y}|{_Y}[-/.]\d{{1,2}}(?:[-/.]\d{{1,2}})?|\d{{1,2}}[/.]{_Y}|"
         rf"{_MON}[\s\-./]*(?:\d{{1,2}}(?:st|nd|rd|th)?,?\s+)?{_Y}|{_MON}\s*['’]\d{{2}}|{_MON}\s*[-/]\s*\d{{2}}(?!\d)|[Qq][1-4][\s\-]*{_Y}|{_Y})")
_NOW = r"(?:present|current(?:ly)?|now|ongoing|continuing|today|to date|till date|till now|till present|until now|until present|up to date|up to now|date)"
_SEP = r"\s*(?:-|–|—|‒|―|→|->|to|until|till|through|thru)\s*"
_RANGE_RE = re.compile(rf"(?<![\w/.-])({_DATE}){_SEP}({_DATE}|{_NOW})(?![\w])", re.I)
_SINCE_RE = re.compile(rf"\bsince\s+({_DATE})(?![\w])", re.I)
_NOW_WORDS = {"present", "current", "currently", "now", "ongoing", "continuing", "today", "to date", "till date", "till now", "till present", "until now",
              "until present", "up to date", "up to now", "date"}


def _now_point(now: Any) -> float:
    return now.year + (now.month - 1) / 12.0 + (getattr(now, "day", 1) - 1) / 365.25


def _to_point(token: str, is_end: bool, now: Any) -> Optional[float]:
    """A date as a number of years (2021.5 is the middle of 2021). A month is the start of the month, or the end of the month for the end of a range.
    A year with no month is the middle of the year."""
    t = token.strip().lower().rstrip(".")
    if t in _NOW_WORDS:
        return _now_point(now)
    m = re.fullmatch(r"(\d{1,2})[/.](\d{1,2})[/.]((?:19|20)\d{2})", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if mo > 12 >= d:
            d, mo = mo, d
        return y + (mo - 1) / 12.0 + (d - 1) / 365.25 if 1 <= mo <= 12 and 1 <= d <= 31 else None
    m = re.fullmatch(r"((?:19|20)\d{2})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?", t)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if not 1 <= mo <= 12:
            return None
        return y + (mo - 1) / 12.0 + (1 / 12.0 if is_end and not m.group(3) else 0.0)
    m = re.fullmatch(r"(\d{1,2})[/.]((?:19|20)\d{2})", t)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        return y + (mo - 1) / 12.0 + (1 / 12.0 if is_end else 0.0) if 1 <= mo <= 12 else None
    m = re.fullmatch(r"q([1-4])[\s\-]*((?:19|20)\d{2})", t)
    if m:
        return int(m.group(2)) + (int(m.group(1)) - (0 if is_end else 1)) / 4.0
    m = re.match(r"([a-z]{3})[a-z]*\.?[\s\-./]*(?:\d{1,2}(?:st|nd|rd|th)?,?\s+)?['’]?((?:19|20)\d{2}|\d{2})$", t)
    if m and m.group(1) in _MONTHS:
        y = int(m.group(2))
        y = y if y > 99 else (2000 + y if y < 70 else 1900 + y)
        mo = _MONTHS[m.group(1)]
        return y + (mo - 1) / 12.0 + (1 / 12.0 if is_end else 0.0)
    if re.fullmatch(_Y, t):
        return int(t) + 0.5
    return None


class _Range:
    __slots__ = ("a", "b", "current", "start", "end")

    def __init__(self, a: float, b: float, current: bool, start: int, end: int):
        self.a, self.b, self.current, self.start, self.end = a, b, current, start, end


_NOT_WORK = re.compile(r"\b(?:career break|gap year|sabbatical|parental leave|maternity|paternity|carer'?s? leave|break from work|unemployed|between (?:roles|jobs)|"
                       r"full-time parenting|family leave|time off|travell?ed|travelling|backpacking|full-time carer|family care|no paid work)\b", re.I)


def find_ranges(line: str, now: Any) -> List[_Range]:
    """The date ranges of a line ("Jan 2021 – Present", "03/2020 – now", "2019–2022", "since 2019"). A range that makes no sense is left out.
    A line about a break from work ("Career break (Apr 2018 – Sep 2019)") has no range: the time is not work."""
    out: List[_Range] = []
    if _NOT_WORK.search(line):
        return out
    top = _now_point(now)
    for m in _RANGE_RE.finditer(line):
        a, b = _to_point(m.group(1), False, now), _to_point(m.group(2), True, now)
        if a is None or b is None:
            continue
        current = m.group(2).strip().lower() in _NOW_WORDS
        if b == a and re.fullmatch(_Y, m.group(1).strip()) and re.fullmatch(_Y, m.group(2).strip()):
            b = a + 0.5                  # "2021 – 2021": less than a year
        if b < a or a < 1960 or a > top + 0.05 or b - a > 55:
            continue
        out.append(_Range(a, min(b, top), current, m.start(), m.end()))
    if not out:
        m = _SINCE_RE.search(line)
        if m:
            a = _to_point(m.group(1), False, now)
            if a is not None and 1960 <= a <= top:
                out.append(_Range(a, top, True, m.start(), m.end()))
    return out


def _strip_ranges(line: str) -> str:
    """The line without its date ranges (a bar takes the place of a range, so that the other parts stay apart)."""
    text = _RANGE_RE.sub(" | ", line)
    text = _SINCE_RE.sub(" | ", text)
    return re.sub(r"\(\s*\)|\[\s*\]", " ", text)


def _union_years(ranges: Iterable[Tuple[float, float]]) -> float:
    """The years in the union of the ranges. Overlapping jobs are counted once."""
    spans = sorted(ranges)
    if not spans:
        return 0.0
    total = 0.0
    cur_a, cur_b = spans[0]
    for a, b in spans[1:]:
        if a <= cur_b:
            cur_b = max(cur_b, b)
        else:
            total += cur_b - cur_a
            cur_a, cur_b = a, b
    return total + cur_b - cur_a


# =====================================================================
# Helpers for lines
# =====================================================================
def _is_lowercase_text(text: str) -> bool:
    """Is the whole CV in small letters (no capitals)? Then the first letter of each word is made a capital, so that the checks for names and titles work."""
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 200 and sum(1 for c in letters if c.isupper()) < 0.015 * len(letters)


def _capitalise_words(line: str) -> str:
    return re.sub(r"(?<![A-Za-z0-9'’])([a-z])", lambda m: m.group(1).upper(), line)


_GAP = chr(0x2003)        # a wide gap in a line (a tab, or two spaces or more): the pieces of the line are in different cells ("Title<gap>Company<gap>Dates")


_PUA_START = re.compile("^[\\s" + chr(0xe000) + "-" + chr(0xf8ff) + "]*[" + chr(0xe000) + "-" + chr(0xf8ff) + "]\\s*")        # a bullet of a symbol font (Wingdings): a private-use character
_PUA_ANY = re.compile("[" + chr(0xe000) + "-" + chr(0xf8ff) + chr(0xfeff) + chr(0x200b) + chr(0x200c) + chr(0x200d) + chr(0xad) + "]")
_MD_HEADING = re.compile(r"^#{1,6}\s+(?=\S)")
_MD_BOLD = re.compile(r"\*\*([^*\n]+?)\*\*")
_MD_RULE = re.compile(r"^\s*(?:[-_=*~]\s*){3,}$")


def _markdown(line: str) -> str:
    """A line from a Markdown file: the signs for headings, bold text and code are taken away. A line of text without signs is not changed."""
    line = _MD_HEADING.sub("", line)
    line = _MD_BOLD.sub(lambda m: m.group(1), line)
    return line.replace("`", "")


def _clean_lines(text: str) -> List[str]:
    """The lines of a text without blank lines. Spaces are one space, but a tab or a run of spaces stays as one wide gap (_GAP)."""
    lines = []
    for raw in text.replace("\r", "\n").split("\n")[:_MAX_LINES]:
        if _MD_RULE.match(raw):
            continue                                      # a line of dashes or stars between the parts
        raw = _PUA_ANY.sub("", _PUA_START.sub("• ", raw)) if _PUA_ANY.search(raw) else raw
        raw = _markdown(raw)
        line = re.sub(r"[ \t]*\t[ \t]*|  +", _GAP, raw)
        line = re.sub("[^\\S" + _GAP + "]+", " ", line).strip(" " + _GAP)
        line = re.sub(" ?" + _GAP + "[ " + _GAP + "]*", _GAP, line)
        if line:
            lines.append(_deglue(line)[:_MAX_LINE])
    return lines


_GLUED = re.compile(r"(?<=[a-z]{3})(?=(?:Data|Engineer|Developer|Analyst|Scientist|Manager|Architect|Software|Machine|Associate|Professional|Specialist|"
                    r"Administrator|Consultant|Lead|Intern|Cloud|Business)\b)|,(?=[A-Z])")


def _deglue(line: str) -> str:
    """Words that a bad text reader glued together ("SeniorData Engineer", "Analyst,Halcyon") get their space back. Only before a word of a job title."""
    return _GLUED.sub(lambda m: " " if m.group(0) == "" else ", ", line)


def _flat(text: str) -> str:
    """The text with a wide gap as one space (for the values that go into the result)."""
    return text.replace(_GAP, " ")


def _unbullet(line: str) -> str:
    return _BULLET_START.sub("", line).strip()


def _nice_case(text: str) -> str:
    """A title in capitals, or in small letters only, gets normal capitals. A title that already has both is left as it is."""
    if text != text.upper() and text != text.lower():
        return text
    out = []
    for k, w in enumerate(text.split()):
        low = w.lower()
        core = low.strip(".,")
        if core in _CASING:
            out.append(low.replace(core, _CASING[core]))
        elif k and core in _SMALL:
            out.append(low)
        elif (w.isupper() and len(core) <= 3 and "." not in w) or re.fullmatch(r"[A-Z]{2,5}-?[0-9]", w):
            out.append(w)                                       # an acronym, or a code like SDE-2
        else:
            out.append(low[:1].upper() + low[1:])
    return " ".join(out)


def _titleize(text: str) -> str:
    """A role from a sentence ("data analyst") gets capitals for each word."""
    out = []
    for k, w in enumerate(text.split()):
        core = w.lower().strip(".,")
        if core in _CASING:
            out.append(w.lower().replace(core, _CASING[core]))
        elif k and core in _SMALL:
            out.append(w.lower())
        elif w.isupper() and len(core) <= 4:
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


# =====================================================================
# Job titles
# =====================================================================
_SEG_SPLIT = re.compile(r"\s*[|·•▪●]\s*|\s+[–—‒―\-]\s+|\s+at\s+|\s*@\s*|\s*[,;]\s*|\s+/\s+|[()\[\]{}]|\s{2,}|\u2003", re.I)
_LABEL_RE = re.compile(r"^(?:position|job title|role|title|designation|occupation(?: or position held)?|position held|current (?:role|position|title|job))\s*[:\-–]?\s+", re.I)
_SENT_END = re.compile(r"\b(?:sr|jr|snr|mgr|eng|dev|eng\.)\.$", re.I)


def _segments(text: str) -> List[str]:
    return [s.strip() for s in _SEG_SPLIT.split(text) if s and s.strip()]


def _score_title(seg: str, lex: cv_lexicon.Lexicon) -> Optional[Tuple[float, str]]:
    """Is this piece of a line a job title? Returns (score, title as written) or None. A title ends with a word like "Engineer" or "Lead"."""
    s = _LABEL_RE.sub("", seg.strip())
    s = s.strip(" .:;,-–—|•·▪●*\"'")
    if not s or len(s) > 90:
        return None
    words = s.split()
    if len(words) > 8:
        return None
    if re.match(r"^(?:dear|hi|hello|to whom|hiring|regards|sincerely)\b", s, re.I):
        return None                               # a greeting ("Dear Hiring Manager") is not a title
    if len(words) >= 3 and lex.canonical_skill(words[0]) and lex.level_of_title(words[1]) and words[1].lower().strip(".") in (
            "senior", "sr", "junior", "jr", "lead", "principal", "staff", "graduate", "mid"):
        words = words[1:]                         # the text of a neighbour column can stand in front of a title: "Selenium Senior QA Engineer"
        s = " ".join(words)
    core = [w.lower().strip(".,") for w in words]
    if len(core) > 1 and re.fullmatch(r"(?:i{1,3}|iv|v|[1-5]|[lep]-?[1-9])", core[-1]):
        core = core[:-1]                          # "Engineer II", "Engineer L5"
    elif core and re.fullmatch(r"[a-z]+-?[1-5]", core[-1]) and lex.is_role_noun(re.sub(r"-?[1-5]$", "", core[-1])):
        core[-1] = re.sub(r"-?[1-5]$", "", core[-1])        # "SDE-2"
    if re.search(r"\d", re.sub(r"\b(?:level|tier|grade|band)\s*\d\b", " ", " ".join(core))) \
            or any(w in _SENT_STOP and not (w == "it" and "IT" in words) for w in core):       # "Level 2 Service Desk Analyst" and "Head of IT" are titles
        return None
    if s.endswith(".") and len(words) > 3 and not _SENT_END.search(s):
        return None
    if core[0] in _VERBS and not (core[0] in _VERB_TITLE_OK and len(core) <= 5):
        return None
    if core[0].endswith("ing") and len(core) >= 4 and core[0] not in _GERUND_OK:
        return None
    if re.search(r"\b(?:pty|ltd|inc|llc|gmbh|corp|limited|plc|university|college)\b", s, re.I):
        return None
    last = core[-1]
    special = re.match(r"^(?:(?:associate|assistant|deputy|regional|global|senior|executive)\s+)?(?:head|director|vp|vice president|chief|manager|lead|principal)\s+of\s+\S",
                       s, re.I) is not None
    in_test = re.search(r"\bengineer in test$", s, re.I) is not None or re.search(r"\b(?:scrum|agile|kanban|release|build|sprint|delivery)\s+master$", s, re.I) is not None
    if not (lex.is_role_noun(last) or special or in_test):
        # a title that ends with its field: "Software Engineer Backend", "Data Scientist NLP"
        for k in range(len(core) - 2, max(-1, len(core) - 4), -1):
            if lex.is_role_noun(core[k]) and all(w in _DOMAIN_WORDS for w in core[k + 1:]):
                last = core[k]
                break
        else:
            return None
    if len(core) == 1 and last not in _STRONG_NOUNS:
        return None
    score = 5.0
    if lex.canonical_role(s):
        score += 2
    if lex.level_of_title(s):
        score += 1
    if any(w in _DOMAIN_WORDS for w in core):
        score += 1
    score -= 0.5 * max(0, len(core) - 5)
    if len(core) == 1:
        score -= 1
    return score, _nice_case(s)


def _best_title(text: str, lex: cv_lexicon.Lexicon) -> Optional[Tuple[float, str]]:
    best: Optional[Tuple[float, str]] = None
    for seg in _segments(text):
        r = _score_title(seg, lex)
        if r and (best is None or r[0] > best[0]):
            best = r
    return best


# =====================================================================
# Positions: the jobs of the CV
# =====================================================================
class _Pos:
    """One job. title is None if the reader found dates but no title."""
    __slots__ = ("title", "a", "b", "current", "first", "last")

    def __init__(self, title: Optional[str], rng: Optional[_Range], first: int, last: int):
        self.title = title
        self.a = rng.a if rng else None
        self.b = rng.b if rng else None
        self.current = bool(rng and rng.current)
        self.first, self.last = first, last      # the first and the last line of the heading of the job


def _read_positions(lines: List[str], region: List[int], now: Any, lex: cv_lexicon.Lexicon) -> Tuple[List[_Pos], List[Tuple[int, str]]]:
    """The jobs of the region, in the order of the text, and the titles that have no dates.

    A job is a line with a date range. Its title is in the same line, or in the lines just before it (Title / Company / Dates),
    or just after it (Dates / Title / Company). The CV is read in the way that pairs most dates with a title."""
    info: Dict[int, Tuple[List[_Range], Optional[Tuple[float, str]], bool]] = {}
    for i in region:
        line = lines[i]
        if len(line) > 170:
            continue
        bullet = _BULLET_START.match(line) is not None
        ranges = find_ranges(line, now)
        title = _best_title(_strip_ranges(line) if ranges else line, lex)
        if title and _ASPIRING.search(line):
            title = None                       # "Aspiring Data Scientist" is a wish, not a job
        if ranges:
            first = _segments(_unbullet(_strip_ranges(line)))[:1]
            if _EDU_LINE.search(line) and not title:
                ranges = []                    # a degree with years: it is not a job
            elif bullet and not (first and _score_title(first[0], lex)):
                ranges = []                    # a bullet is something that the person did, unless it starts with a title
            elif not title and _VERB_START.match(_unbullet(line)):
                ranges = []
        if bullet and not ranges:
            title = None
        info[i] = (ranges, title, bullet)
    anchors = [i for i in region if i in info and info[i][0]]
    inline = {i for i in anchors if info[i][1]}
    pending = [i for i in anchors if i not in inline]
    title_lines = [i for i in region if i in info and info[i][1] and not info[i][0]]

    def pair(direction: str) -> Dict[int, int]:
        used: set = set()
        out: Dict[int, int] = {}
        for a in pending:
            if direction == "before":
                low = max([x for x in anchors if x < a], default=-1)
                pick = max([t for t in title_lines if low < t < a and a - t <= 4 and t not in used], default=None)
            else:
                high = min([x for x in anchors if x > a], default=10 ** 9)
                pick = min([t for t in title_lines if a < t < high and t - a <= 4 and t not in used], default=None)
            if pick is not None:
                used.add(pick)
                out[a] = pick
        return out

    before, after = pair("before"), pair("after")
    chosen = before if len(before) >= len(after) else after
    positions: List[_Pos] = []
    for a in anchors:
        rng = info[a][0][0]
        if a in inline:
            positions.append(_Pos(info[a][1][1], rng, a, a))          # type: ignore[index]
        elif a in chosen:
            t = chosen[a]
            positions.append(_Pos(info[t][1][1], rng, min(a, t), max(a, t)))   # type: ignore[index]
        else:
            positions.append(_Pos(None, rng, a, a))
    taken = set(chosen.values())
    undated = [(t, info[t][1][1]) for t in title_lines if t not in taken]      # type: ignore[index]
    positions.sort(key=lambda p: p.first)
    return positions, undated


def _pair_timeline(positions: List[_Pos], undated: List[Tuple[int, str]], lines: List[str], secs: List[_Sec], now: Any) -> List[_Pos]:
    """A template that has the dates in a block of their own (a "Timeline" in the sidebar) and the jobs without dates: the first date range goes to the
    first job, the second to the second, and so on (the newest first, as the template writes them). Only when there are at least as many ranges as jobs."""
    skip = set(_indices_of(secs, "experience", "education"))
    ranges: List[_Range] = []
    for i, line in enumerate(lines):
        if i in skip or _header_of(line):
            continue
        found = find_ranges(line, now)
        if found and not re.search(r"[A-Za-z0-9]", _strip_ranges(line)):
            ranges.append(found[0])                   # a line that is only a date range
    if not ranges or len(ranges) < len(undated):
        return positions
    return [_Pos(title, rng, idx, idx) for (idx, title), rng in zip(undated, ranges)]


_NOT_JOB_HEAD = re.compile(r"volunteer|communit|hobb|interest|activit|reference|referee|declaration|publication|patent|teaching|service|mentoring|outreach|"
                           r"membership|affiliation|personal|character", re.I)


def _fallback_region(secs: List[_Sec]) -> List[int]:
    """The lines where jobs are looked for when the CV has no heading for its experience: the top, the summary and the parts that have an unknown
    heading. Volunteering, hobbies, references and the like are not jobs."""
    out = _indices_of(secs, "top", "summary", "objective")
    for s in secs:
        if s.kind == "other" and not _NOT_JOB_HEAD.search(s.head):
            out.extend(range(s.start, s.end))
    return out


_STUDENT_ROLE = re.compile(r"\b(?:(?:research|teaching|lab(?:oratory)?|graduate|student|undergraduate)\s+(?:assistant|associate|fellow|tutor)|tutor|demonstrator)\b", re.I)


def _study_ranges(lines: List[str], secs: List[_Sec], now: Any) -> List[Tuple[float, float]]:
    """The years of study: the date ranges in the lines of the education part."""
    out: List[Tuple[float, float]] = []
    for i in _indices_of(secs, "education"):
        for r in find_ranges(lines[i], now):
            if r.a is not None and r.b is not None:
                out.append((r.a, r.b))
    return out


def _is_study_role(p: "_Pos", study: List[Tuple[float, float]]) -> bool:
    """A research assistant, teaching assistant or tutor whose dates are inside the years of a degree: it belongs to the study, it is not work."""
    if not p.title or p.a is None or p.b is None or not _STUDENT_ROLE.search(p.title):
        return False
    length = max(p.b - p.a, 0.01)
    return any(min(p.b, b) - max(p.a, a) >= 0.7 * length for a, b in study)


def _current_position(positions: List[_Pos]) -> Tuple[Optional[_Pos], str]:
    """The current job: rule 1, the job that has an open end (the latest start, if there are more); rule 2, the job with the latest end date.
    If that job has no title, there is no answer (an older job is not the current job)."""
    open_ = [p for p in positions if p.current]
    if open_:
        best = max(open_, key=lambda p: (p.a or 0.0, -p.first))
        return (best if best.title else None), "open-position"
    dated = [p for p in positions if p.b is not None]
    if dated:
        best = max(dated, key=lambda p: (p.b or 0.0, p.a or 0.0, -p.first))
        return (best if best.title else None), "latest-end"
    return None, ""


# =====================================================================
# The headline, the summary sentence and the wish for a job
# =====================================================================
_ASPIRING = re.compile(r"\b(aspiring|seeking|looking for|looking to|open to|prospective|in search of|hoping|aspire)\b", re.I)
_TARGET_LABEL = re.compile(r"^(?:job applied for|position applied for|preferred job|preferred role|preferred position|desired (?:job|position|role|occupation|employment)|"
                           r"occupational field|target (?:job|role|position)|applying for|role sought|position sought|job target|desired role)\s*[:\-–]?\s*(.*)$", re.I)
_NAME_WORD = re.compile(r"^[^\W\d_](?:[^\W\d_]|['’.-])*$")


def _looks_like_name(line: str, lex: cv_lexicon.Lexicon) -> bool:
    words = line.split()
    if not 2 <= len(words) <= 4 or _CONTACT_RE.search(line) or re.search(r"\d", line):
        return False
    if not all(_NAME_WORD.match(w) and (w[0].isupper()) for w in words):
        return False
    return not any(lex.is_role_noun(w) for w in words) and _header_of(line) is None


def _read_headline(lines: List[str], secs: List[_Sec], lex: cv_lexicon.Lexicon) -> Tuple[Optional[str], str, Optional[str]]:
    """The title in the lines at the top (under or above the name, or on the line of the name: "Name | Title").
    Returns (title, kind, line) where kind is "current", or "target" if the headline is a wish ("Aspiring Data Scientist")."""
    top = list(range(secs[0].start, secs[0].end))[:10]
    candidates = top
    if not any(_best_title(lines[i], lex) for i in top):
        # The file starts with a sidebar (a heading comes first). Look for a name that stands next to a title.
        outside = set(_indices_of(secs, "experience", "education", "skills", "certs", "awards", "projects"))
        candidates = []
        for i in range(0, min(len(lines) - 1, 60)):
            if i in outside or i + 1 in outside:
                continue
            if (_looks_like_name(lines[i], lex) and _best_title(lines[i + 1], lex)) or (_best_title(lines[i], lex) and _looks_like_name(lines[i + 1], lex)):
                candidates = [i, i + 1]
                break
    previous = ""
    for i in candidates:
        line = lines[i]
        label_only = _TARGET_LABEL.match(previous)
        previous = line
        if label_only and not label_only.group(1):
            continue                  # the line that follows "JOB APPLIED FOR" is the wish, not the title that the person has
        best = _best_title(line, lex)
        if best:
            if _ASPIRING.search(line):
                return best[1], "target", line
            return best[1], "current", line
    return None, "", None


_ADJECTIVES = re.compile(r"^(?:(?:passionate|experienced|motivated|results[- ]driven|dedicated|accomplished|skilled|talented|seasoned|versatile|creative|innovative|"
                         r"detail[- ]oriented|highly|proven|enthusiastic|ambitious|driven|dynamic|adaptable|hardworking|self[- ]motivated|professional|recent|aspiring|"
                         r"curious|analytical|results[- ]oriented|energetic|reliable|resourceful)\s+)+", re.I)
_SUMMARY_ROLE_RX = [
    re.compile(r"(?:^|[.;!]\s+|\b(?:i am|i'm|am)\s+)(?:an?\s+|the\s+)?(?P<role>[A-Za-z][A-Za-z0-9+#./& '-]{2,70}?)\s+(?:with|who has|having)\s+"
               r"(?:(?:over|more than|nearly|almost|around|about|approximately)\s+)?\d{1,2}(?:\.\d)?\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"\b(?:working|work|worked|employed|currently|serving)\s+as\s+(?:an?\s+|the\s+)?(?P<role>[A-Za-z][A-Za-z0-9+#./& '-]{2,60}?)"
               r"(?=\s+(?:at|for|in|with|since|where|and)\b|[,.;]|$)", re.I),
    re.compile(r"\b(?:i am|i'm)\s+(?:an?\s+|the\s+)(?P<role>[A-Za-z][A-Za-z0-9+#./& '-]{2,60}?)"
               r"(?=\s+(?:at|for|in|with|who|that|based|passionate|specialising|specializing|focused)\b|[,.;]|$)", re.I),
]


def _role_in_sentence(text: str, lex: cv_lexicon.Lexicon) -> Optional[str]:
    """A role that a sentence of the summary says about the person: "Data analyst with 6 years of experience", "I am a data engineer"."""
    for line in text.split("\n"):             # one line at a time: the name above a sentence is not a part of the role
        for rx in _SUMMARY_ROLE_RX:
            for m in rx.finditer(line):
                phrase = _ADJECTIVES.sub("", m.group("role").strip())
                scored = _score_title(phrase, lex)
                if scored:
                    return _titleize(scored[1])
    return None


_WISH = re.compile(r"\b(?:seeking|looking for|looking to|search(?:ing)? for|in search of|aiming|aspir(?:e|es|ing)|hoping|interested in|open to|targeting|pursuing|"
                   r"applying for|want(?:s)? to|wish(?:es)? to|eager to|transition(?:ing)?|move into|moving into|my goal|goal is|objective is|career change|"
                   r"keen to|would like|would love|i'd like|i'd love|next (?:role|step|move|job|position)|ideally|grow(?:ing)? (?:into|towards?)|drawn to|"
                   r"moving towards?|dream (?:job|role)|where i want to go|i am after|i'm after)\b"
                   r"(?P<rest>[^.;!\n]{0,170})", re.I)
_ROLE_WORD = re.compile(r"\b(?:roles?|positions?|opportunit\w*|jobs?|posts?|vacanc\w+)\b", re.I)
_ARTICLE_BEFORE = re.compile(r"(?:\b(?:an?|the|as|become|be|into)\s+(?:[\w+#./-]+\s+){0,2})$", re.I)
_DIRECT_BEFORE = re.compile(r"^[\s:\-–—]*(?:is\s+|would be\s+|to be\s+)?(?:an?\s+|the\s+)?(?:(?:senior|junior|lead|principal|staff|graduate|mid[- ]level)\s+)?$", re.I)


def _roles_of_wish(text: str, lex: cv_lexicon.Lexicon, label: bool = False) -> List[str]:
    """The known roles that a wish sentence names. A role counts when a word of job follows ("... Engineer roles") or an article stands before it."""
    found: List[str] = []
    for m in ([_WISH_ALL.match(text)] if label else _WISH.finditer(text)):
        if not m:
            continue
        rest = m.group("rest")
        for start, end, role in lex.find_roles(rest):
            before = rest[:start]
            ok = (label or _ROLE_WORD.search(rest[end:]) is not None or _ARTICLE_BEFORE.search(before) is not None
                  or _DIRECT_BEFORE.match(before) is not None)         # "Next role: Backend Developer": the role comes right after the words of a wish
            if ok and role not in found:
                found.append(role)
    return found


_WISH_ALL = re.compile(r"(?P<rest>.*)", re.S)


def read_target_roles(lines: List[str], secs: List[_Sec], lex: Optional[cv_lexicon.Lexicon] = None) -> Tuple[List[str], str]:
    """The roles that the CV says that the person wants. Returns (roles, how). Only roles of the role list count. The reader never guesses."""
    lex = lex or cv_lexicon.get()
    # 1. A label: "Desired role: Data Engineer", or "JOB APPLIED FOR" and the next line
    for k, line in enumerate(lines[:80]):
        m = _TARGET_LABEL.match(line)
        if m:
            value = m.group(1).strip() or (lines[k + 1] if k + 1 < len(lines) else "")
            roles = _roles_of_wish(value, lex, label=True)
            if roles:
                return roles[:3], "label"
    # 2. A sentence of wish in the parts of the CV that talk about the person (not in the jobs, the school, the lists)
    parts = []
    for s in secs:
        if s.kind in ("top", "summary", "objective", "other", "languages", "contact"):
            parts.append((s.kind, " ".join(lines[s.start:s.end][:12] if s.kind == "top" else lines[s.start:s.end])))
    for kind, text in parts:
        roles = _roles_of_wish(text, lex)
        if not roles and kind == "objective":
            for start, end, role in lex.find_roles(text):          # the heading is the wish: any known role in it counts, with the same care
                if (_ROLE_WORD.search(text[end:]) or _ARTICLE_BEFORE.search(text[:start])) and role not in roles:
                    roles.append(role)
        if roles:
            return roles[:3], "sentence"
    return [], ""


# =====================================================================
# Years
# =====================================================================
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
                 "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
_YEARS_NUM = re.compile(r"\b(\d{1,2}(?:\.\d)?|" + "|".join(_NUMBER_WORDS) + r")\s*\+?\s*(?:years?|yrs?)\b", re.I)
_MONTHS_AFTER = re.compile(r"\s*(?:and\s+)?(\d{1,2})\s*(?:months?|mos?)\b", re.I)
_SINCE_STATEMENT = re.compile(r"\b(?:working|worked|career|experience|employed|developing|coding|programming|in (?:software|data|it|tech\w*|engineering|analytics))\b"
                              r"[^.\n]{0,50}?\bsince\s+(?:[A-Za-z]{3,9}\.?\s+)?((?:19|20)\d{2})", re.I)


def _number_of(token: str) -> float:
    return float(_NUMBER_WORDS[token.lower()]) if token.lower() in _NUMBER_WORDS else float(token)


_EXPERIENCE_AFTER = re.compile(r"\s*(?:of\s+|[’']s\s+)?(?:(?:professional|relevant|industry|work|total|hands[- ]on|commercial|combined|progressive|proven|extensive|solid|"
                               r"practical|overall|working|real[- ]world|paid|related)\s+)*(?:experience|exp\b|expertise|in (?:the )?industry|working in|"
                               r"in (?:software|data|it|ict|technology|tech|engineering|analytics|machine learning|ai|insurance|finance|financial|banking|retail|healthcare|health|telecom\w*|"
                               r"logistics|consulting|e-?commerce|education|government|media|manufacturing|energy|mining|security|devops|testing|reporting|business intelligence|"
                               r"product|digital|web|mobile|cloud|embedded)\b)(?P<tail>.{0,50})", re.I)
_SKILL_BEFORE_EXPERIENCE = re.compile(r"[ ]*(?:of[ ]+)?(?P<skill>[A-Za-z0-9+#.]{2,20}(?:[ ][A-Za-z0-9+#.]{2,20}){0,2}?)[ ]+experience\b", re.I)
_EXPERIENCE_COLON = re.compile(r"(?:total |overall |professional |work |relevant )?(?:experience|years of experience)\s*[:\-–]\s*(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)?", re.I)
_DECADE = re.compile(r"\b(?:a|one|over a|more than a|nearly a|almost a)\s+decade\b(?=\s+(?:of|in|working|as|with)\b|[^.]{0,40}experience)|\b(two|three) decades\b", re.I)


def read_year_statements(text: str, lex: Optional[cv_lexicon.Lexicon] = None, now: Any = None) -> Tuple[List[float], Dict[str, float]]:
    """The "N years" sentences ("8 years", "eight years", "3 years 6 months", "working in data since 2016").
    Returns (years of work in total, years with a skill). "8 years of experience in data engineering" is in total.
    "5 years of experience with Python" is for the skill."""
    lex = lex or cv_lexicon.get()
    overall: List[float] = []
    per_skill: Dict[str, float] = {}
    for m in _YEARS_NUM.finditer(text):
        value = _number_of(m.group(1))
        end = m.end()
        extra = _MONTHS_AFTER.match(text, end)
        if extra:
            value += int(extra.group(1)) / 12.0
            end = extra.end()
        if not 0 < value <= 45:
            continue
        after = text[end:end + 80]
        am = _EXPERIENCE_AFTER.match(after)
        if am:
            tail = re.match(r"\s*(?:in|with|using|on|across)\s+(.{0,40})", am.group("tail"), re.I)
            hit = lex.skills_in(tail.group(1))[:1] if tail else []
            first_word = tail.group(1).split()[:3] if tail else []
            skill = lex.canonical_skill(" ".join(first_word)) or lex.canonical_skill(first_word[0]) if first_word else None
            if hit and hit[0][0] < 3 and lex.skill_kind(hit[0][1]) == "hard":
                per_skill[hit[0][1]] = max(per_skill.get(hit[0][1], 0.0), value)
            elif skill and lex.skill_kind(skill) == "hard":
                per_skill[skill] = max(per_skill.get(skill, 0.0), value)
            else:
                overall.append(value)
            continue
        sm = _SKILL_BEFORE_EXPERIENCE.match(after)
        if sm:
            skill = lex.canonical_skill(sm.group("skill"))
            if skill:
                per_skill[skill] = max(per_skill.get(skill, 0.0), value)
            else:
                overall.append(value)
    for m in _EXPERIENCE_COLON.finditer(text):
        value = float(m.group(1))
        if 0 < value <= 45:
            overall.append(value)
    if now is not None:
        for m in _SINCE_STATEMENT.finditer(text):
            value = _now_point(now) - (int(m.group(1)) + 0.5)
            if 0 < value <= 45:
                overall.append(round(value, 1))
    for m in _DECADE.finditer(text):
        if m.group(1) or re.search(r"experience|career|industry|software|data|engineering|technology|\bit\b|ict|\bi\b|\bmy\b", text[max(0, m.start() - 60):m.end() + 60], re.I):
            overall.append(20.0 if m.group(1) and m.group(1).lower() == "two" else 30.0 if m.group(1) else 10.0)
    return overall, per_skill


def read_years(experience_lines: List[str], all_lines: List[str], today: Any = None) -> Tuple[str, float]:
    """The total work experience, as a band from the YEARS list. Overlapping jobs are counted once."""
    now = today or datetime.now(timezone.utc)
    spans: List[Tuple[float, float]] = []
    for line in experience_lines:
        if _EDU_LINE.search(line) and not _TITLE_RE.search(line):
            continue
        for r in find_ranges(line, now):
            spans.append((r.a, r.b))
    total = _union_years(spans)
    if total <= 0:
        overall, _ = read_year_statements(" ".join(all_lines), None, now)
        if overall:
            total = max(overall)
    return _band(total) if total > 0 else "", max(total, 0.0)


def _band(total: float) -> str:
    if total < 1:
        return _YEARS[0]
    if total < 3:
        return _YEARS[1]
    if total < 6:
        return _YEARS[2]
    if total <= 10:
        return _YEARS[3]
    return _YEARS[4]


# =====================================================================
# Level
# =====================================================================
_STUDENT = re.compile(r"\b(?:student|undergraduate|currently (?:studying|enrolled|pursuing)|final[- ]year|penultimate year|expected (?:graduation|completion)|"
                      r"anticipated graduation|graduating (?:in )?20\d\d|expected (?:in )?20\d\d|\(expected)\b", re.I)
_GRADUATE = re.compile(r"\b(?:recent graduate|fresh graduate|new graduate|recently graduated|graduate (?:seeking|looking)|just graduated|entry[- ]level)\b", re.I)


def level_from_years(years: float) -> str:
    """Junior under 2 years, Mid from 2 to 5, Senior from 5. Lead and Principal come from the words of a title only."""
    return "Junior" if years < 2 else "Mid" if years < 5 else "Senior"


# =====================================================================
# Qualifications, fields of study, countries, roles for the list
# =====================================================================
def read_qualifications(lines: List[str]) -> List[str]:
    found: Dict[str, None] = {}
    for line in lines:
        low = line.lower()
        for rx, label in _QUAL_RULES:
            if rx.search(low):
                # "Bachelor ... Honours" also matches the plain bachelor rule. Keep the most specific one only.
                if label == "Bachelor's degree" and "Bachelor's degree (Honours)" in found:
                    continue
                if label == "Diploma" and ("Advanced diploma" in found or "Graduate diploma" in found):
                    continue
                if label == "Master's degree" and "MBA" in found and re.search(r"master of business", low):
                    continue
                found[label] = None
                break
    return sorted(found, key=lambda q: _QUAL_ORDER.get(q, 99))


def read_fields_of_study(lines: List[str]) -> List[str]:
    found: Dict[str, None] = {}
    for line in lines:
        low = line.lower()
        if not _EDU_LINE.search(low):
            continue
        for key in _FIELD_KEYS:
            if re.search(rf"\b{re.escape(key)}\b", low):
                found[_FIELD_ALIASES[key]] = None
                break
        else:
            m = re.search(r"(?:bachelor|master|diploma|degree|bsc|msc)(?: of| in)?(?: [a-z]+)?\s+(?:in|of)\s+([a-z][a-z &-]{3,40})", low)
            if m:
                phrase = re.split(r"\b(from|at|university|college|gpa|major|minor)\b|[,(]", m.group(1))[0].strip()
                if len(phrase) >= 4:
                    found[phrase.capitalize()] = None
    return list(found)[:3]


def read_study_countries(lines: List[str]) -> List[str]:
    found: Dict[str, None] = {}
    for line in lines:
        if not _EDU_LINE.search(line):
            continue
        for country in R.COUNTRIES:
            if re.search(rf"\b{re.escape(country)}\b", line, re.I):
                found[country] = None
        if re.search(r"\bUK\b", line):
            found["United Kingdom"] = None
        if re.search(r"\bUSA\b|\bU\.S\.A?\b", line):
            found["United States"] = None
        if re.search(r"\bUAE\b", line):
            found["United Arab Emirates"] = None
    return list(found)[:3]


def read_roles(lines: List[str], whole_text: str) -> List[str]:
    """Job titles, most recent first. The words of the person come first. A standard title is added only if it is not already in one."""
    titles: Dict[str, None] = {}
    # 1. A title in a heading line: "Operations Team Lead - ABC Logistics (2019 - 2023)"
    for line in lines:
        if len(line) > 110 or line[:1] in "•-*·▪●" or _VERB_START.match(line):
            continue
        for segment in re.split(r"\s[|–—@-]\s|\sat\s|[|•·@()]|,", line):
            seg = segment.strip(" .:;")
            words = seg.split()
            if not (1 < len(words) <= 6) or re.search(r"\d", seg) or not _TITLE_RE.search(seg) or _COMPANY_WORDS.search(seg):
                continue
            if _VERB_START.match(seg) or seg.lower().startswith(("responsible", "experience", "skills", "key ")):
                continue
            title = _nice_case(seg)
            if title.lower() not in {t.lower() for t in titles}:
                titles[title] = None
            break
    # 2. A title from the standard list that the text shows
    return _with_standard_roles(list(titles), whole_text)


def _with_standard_roles(titles: List[str], whole_text: str) -> List[str]:
    low = whole_text.lower()
    standard = [r for r in R.ROLES if re.search(rf"\b{re.escape(r.lower())}\b", low)
                and not any(r.lower() in t.lower() for t in titles)]
    return (titles + standard)[:4]


def read_industries(text: str) -> List[str]:
    """The domains (Software Engineering, AI & Machine Learning, Data) that a text shows: at most 2, the strongest first, [] when nothing fits.
    The profile keeps only these three (the platform has no other industry). For a whole CV, parse_cv adds the roles and the skills to the points."""
    lex = cv_lexicon.get()
    return lex.domains_of(skills=[name for _, name in lex.skills_in(text)], text=text)


# =====================================================================
# Skills
# =====================================================================
_WORD_LEVELS = [
    (5, re.compile(r"\b(expert|expert[- ]level|mastery|master|deep expertise|specialist|guru)\b", re.I)),
    (4, re.compile(r"\b(advanced|strong|extensive|in[- ]depth|highly proficient|very good|excellent)\b", re.I)),
    (3, re.compile(r"\b(proficient|competent|solid|good|hands[- ]on|experienced|intermediate|fluent)\b", re.I)),
    (2, re.compile(r"\b(working knowledge|working|some experience|limited)\b", re.I)),
    (1, re.compile(r"\b(beginner|basic|novice|learning|currently learning|fundamentals?|familiar(?:ity)?(?: with)?|exposure(?: to)?|awareness|entry)\b", re.I)),
]
_RATING_RE = re.compile(r"([●⬤◉★■▰]+)([○☆□▱◌]*)|([○☆□▱◌]+)")
_SCORE_RE = re.compile(r"\b([1-5])\s*/\s*5\b|\b(\d{2,3})\s*%")
_SKILL_YEARS = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?|y)\b", re.I)
_SKILL_ITEM_SPLIT = re.compile(r"\s*[,;|•·▪]\s*|\s*(?<![●○★☆■□])●(?![●○★☆■□])\s*|\s+[-–—]\s+|\s{2,}|" + _GAP)   # a run of dots is a rating, a lone dot is a separator


def level_from_skill_years(years: float) -> int:
    return 1 if years < 1 else 2 if years < 2 else 3 if years < 4 else 4 if years < 7 else 5


def _word_level(text: str) -> Optional[int]:
    for level, rx in _WORD_LEVELS:
        if rx.search(text):
            return level
    return None


def _split_skill_items(line: str, lex: cv_lexicon.Lexicon) -> List[str]:
    items: List[str] = []
    # A comma inside brackets ("Python (Advanced, 5 yrs)") does not end the item
    guarded = re.sub(r"\([^)]*\)", lambda m: m.group(0).replace(",", "\x00").replace(";", "\x01"), line)
    for part in _SKILL_ITEM_SPLIT.split(guarded):
        part = part.replace("\x00", ",").replace("\x01", ";")
        part = part.strip(" .-–—*")
        if not part:
            continue
        if "/" in part and not lex.canonical_skill(part):
            pieces = [p.strip() for p in part.split("/")]
            if len(pieces) <= 4 and all(1 <= len(p) <= 14 and " " not in p for p in pieces):
                items.extend(pieces)
                continue
        items.append(part)
    return items


_LEVEL_WORD_ONLY = r"expert|advanced|proficient|intermediate|basic|beginner|familiar|strong|working knowledge|novice"


def _parse_skill_item(item: str, lex: cv_lexicon.Lexicon) -> Optional[Dict[str, Any]]:
    """One item of a skills section: {name, level, years}. An item that is only a level ("Expert", "5 yrs") has the name "": it belongs to the item before."""
    text = _flat(item).strip()
    level: Optional[int] = None
    years: Optional[float] = None
    rm = _RATING_RE.search(text)
    if rm:
        filled = len(rm.group(1) or "")
        empty = len(rm.group(2) or "") or len(rm.group(3) or "")
        if rm.group(1) and ((filled + empty) in (3, 4, 5, 10) or (not empty and 1 <= filled <= 5)):
            level = max(1, min(5, int(round(filled / float(filled + empty if empty else 5) * 5))))
        text = text[:rm.start()] + " " + text[rm.end():]
    sm = _SCORE_RE.search(text)
    if sm:
        level = int(sm.group(1)) if sm.group(1) else max(1, min(5, int(round(int(sm.group(2)) / 20.0))))
        text = text[:sm.start()] + " " + text[sm.end():]
    ym = _SKILL_YEARS.search(text)
    if ym:
        years = float(ym.group(1))
        text = text[:ym.start()] + " " + text[ym.end():]
    word = _word_level(" ".join(re.findall(r"\(([^)]*)\)", text)))
    rest = re.sub(r"\([^)]*\)", " ", text)
    rest = re.sub(r"\s+", " ", rest).strip(" .:-–—,")
    m = re.match(rf"^(.*?)[\s:]*\b({_LEVEL_WORD_ONLY})$", rest, re.I)
    if m:
        word = word or _word_level(m.group(2))
        rest = m.group(1).strip(" .:-–—,")
    else:
        m = re.match(rf"^({_LEVEL_WORD_ONLY})\s+(?:in\s+|with\s+|at\s+)?(.+)$", rest, re.I)
        if m and len(m.group(2).split()) <= 4:
            word = word or _word_level(m.group(1))
            rest = m.group(2).strip()
    if not rest:
        return {"name": "", "level": level or word, "years": years} if (level or word or years) else None
    if not (len(rest) >= 2 or lex.canonical_skill(rest)) or len(rest) > 40 or len(rest.split()) > 5 or not re.search(r"[A-Za-z]", rest) or re.search(r"@|http|www\.", rest):
        return None
    return {"name": lex.canonical_skill(rest) or rest, "level": level or word, "years": years}


def read_skill_entries(skill_lines: List[str], lex: Optional[cv_lexicon.Lexicon] = None) -> List[Dict[str, Any]]:
    """The items of a skills section: {name, level, years}. The name is the name of the list when the list has the skill, else as written.
    A level comes from the words, the dots or the "N yrs" that stand next to the skill, or from a line label ("Expert: Python, SQL")."""
    lex = lex or cv_lexicon.get()
    out: List[Dict[str, Any]] = []
    joined: List[str] = []
    for raw in skill_lines:
        line = _unbullet(raw)
        # An item that the page broke in two ("... ETL pipelines, Data" / "modelling"): a list line that has no comma at its end, and a short line that
        # starts with a small letter and is not a skill by itself, are one line
        if (joined and re.search(r"[,;]", joined[-1]) and not re.search(r"[,;:|•·]\s*$", joined[-1]) and line[:1].islower() and len(line.split()) <= 3
                and ":" not in line and not lex.canonical_skill(line)):
            joined[-1] += " " + line
        else:
            joined.append(line)
    for line in joined:
        label_level: Optional[int] = None
        m = re.match(r"^([^:]{2,32}):\s*(.+)$", line)
        if m and not re.search(r"\d", m.group(1)):
            label_level = _word_level(m.group(1))
            line = m.group(2)
        for item in _split_skill_items(line, lex):
            entry = _parse_skill_item(item, lex)
            if entry is None:
                continue
            if not entry["name"]:                  # "Python – Expert": the level belongs to the skill before
                if out and out[-1]["level"] is None and out[-1]["years"] is None:
                    out[-1]["level"], out[-1]["years"] = entry["level"], entry["years"]
                continue
            if entry["level"] is None and label_level is not None:
                entry["level"] = label_level
            out.append(entry)
    return out


def read_skills(skill_lines: List[str], whole_text: str) -> List[str]:
    """Skills from the skills section (the name of the list when the list has the skill, else as written), then the skill names that the text shows."""
    lex = cv_lexicon.get()
    out: Dict[str, None] = {}
    for entry in read_skill_entries(skill_lines, lex):
        if not any(entry["name"].lower() == k.lower() for k in out):
            out[entry["name"]] = None
    for _, name in lex.skills_in(whole_text):
        if not any(name.lower() == k.lower() for k in out):
            out[name] = None
    # The skills that are methods and soft skills ("Agile delivery", "Code review", "Mentoring") come last: the words of the taxonomy for them are phrases
    for _, name in lex.skills_in(whole_text, hard_only=False):
        if lex.skill_kind(name) != "hard" and not any(name.lower() == k.lower() for k in out):
            out[name] = None
    return list(out)[:25]


def _skill_levels(names: List[str], entries: List[Dict[str, Any]], positions: List[_Pos], bodies: List[str], skill_years: Dict[str, float],
                  now: Any, lex: cv_lexicon.Lexicon) -> List[Dict[str, Any]]:
    """The level (1 to 5) of each skill, or None when the CV gives no evidence. Rules, the first that fits:
    1 a word, dots or a score next to the skill  2 years next to the skill ("Python (5 yrs)", "5 years with Python")
    3 the jobs that mention the skill: the years of those jobs, and how long ago the last one ended."""
    explicit = {e["name"].lower(): e for e in entries}
    top = _now_point(now)
    result = []
    for name in names:
        e = explicit.get(name.lower(), {})
        level: Optional[int] = e.get("level")
        source = "words" if level else ""
        if level is None:
            years = e.get("years") or skill_years.get(name)
            if years:
                level, source = level_from_skill_years(years), "years"
        if level is None and name in lex.skills and lex.skill_kind(name) != "hard":
            result.append({"name": name, "level": None})
            continue
        if level is None:
            rx = lex.mention_pattern(name)
            used = [(p, b) for p, b in zip(positions, bodies) if rx.search(b)]
            if used:
                dated = [(p.a, p.b) for p, _ in used if p.a is not None and p.b is not None]
                if dated:
                    span = _union_years(dated)
                    level = 2 if span < 1 else 3 if span < 3 else 4        # a job that names a skill does not prove expertise: 5 needs the person's own words or years
                    gap = top - max(b for _, b in dated)
                    level = max(1, level - (2 if gap > 6 else 1 if gap > 3 else 0))
                else:
                    level = 3 if len(used) == 1 else 4
                source = "jobs"
        result.append({"name": name, "level": level})
    return result


# =====================================================================
# Certifications
# =====================================================================
_YEAR_IN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_EXPIRY = re.compile(r"(?:expires?|expiry|expiration|valid (?:until|through|to)|until|renewed|recertified|re-certified)\s*:?\s*(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}", re.I)
_CERT_WORDS = re.compile(r"\b(?:certified|certification|certificate|specialization|specialisation|professional certificate|nanodegree|badge|credential|licen[cs]e|"
                         r"accredited|practitioner|associate|professional|expert|foundations?|fundamentals|bootcamp|course|exam)\b", re.I)
# A line under an entry of a list that only tells who gave it and when. It is not an entry itself.
_DETAIL_START = re.compile(r"^[\s·•|,;\-–—]*(?:issued(?: by)?|expires?|expiry|expiration|valid (?:until|through|to|from)|credential(?: id)?|no expiration|never expires|"
                           r"issuer|awarded by|presented by|associated with|id\s*:)\b", re.I)
_DATE_ONLY = re.compile(r"^[\s(·|,\-–—]*(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}[\s)·|,.\-–—]*$")
_NOT_CERT = re.compile(r"\b(?:higher school|school certificate|high school|secondary school|hsc|vce|atar|bachelor|master of|diploma of|degree|"
                       r"no certificate|not certified|without (?:a )?certificate|in progress|currently|audited|working with children|driver'?s? licen[cs]e|"
                       r"driving licen[cs]e|police check|first aid|blue card|white card|spanish|french|german|italian|japanese|chinese|mandarin|cantonese|korean|"
                       r"vietnamese|arabic|hindi|ielts|toefl|language course|seminars?|webinars?|cambridge english|toeic|jlpt|english|goethe|delf|dele|diploma|"
                       r"courses?|training attended|attendance|completion statement|completion badge|short programme|executive education|university extension|extension|"
                       r"rank|clearance|military training|mandatory training)\b", re.I)
# A certification that the person does not hold (yet): the exam is booked, the study goes on, the certificate ran out
_CERT_STATUS = re.compile(r"\b(?:in progress|ongoing|studying|working towards|pending|lapsed|planned|booked|scheduled|exam (?:not|date)|"
                          r"not (?:yet )?(?:taken|passed|completed|booked|obtained|sat)|yet to|expected (?:in|by|\d)|to be completed|part[- ]qualified)\b", re.I)
_DASH_IN_NAME = re.compile(r"\s[-–—]\s(?=(?:Associate|Professional|Specialty|Specialist|Expert|Foundational?|Practitioner|Fundamentals|Advanced|Intermediate)\b)")
_ACRONYM = re.compile(r"^[A-Z][A-Z0-9+]{2,9}$")


def _year_of(text: str) -> Optional[int]:
    clean = _EXPIRY.sub(" ", text)
    m = _YEAR_IN.search(clean)
    return int(m.group(1)) if m else None


def _issuer_of(text: str, lex: cv_lexicon.Lexicon) -> str:
    low = text.lower()
    for issuer in lex.issuers:
        if re.search(rf"(?<![A-Za-z]){re.escape(issuer.lower())}(?![A-Za-z])", low):
            return issuer
    return ""


def _is_detail(line: str, lex: cv_lexicon.Lexicon) -> bool:
    """A line under an entry that only gives the issuer or the dates ("Issued Mar 2021 · Expires Mar 2024", "2022", "Scrum.org")."""
    text = _unbullet(line).strip()
    if not text:
        return False
    if _DETAIL_START.match(text) or _DATE_ONLY.match(text):
        return True
    low = text.lower().strip(" .")
    return any(low == issuer.lower() for issuer in lex.issuers)


_OPEN, _CLOSE = chr(2), chr(3)           # marks for a bracket that is part of a name
# A piece after a comma that goes on with the name ("Oracle Certified Professional, Java SE 8 Programmer"). Other pieces are the issuer ("..., Scrum Alliance").
_NAME_CONTINUATION = re.compile(r"\d|\b(?:programmer|developer|engineer|administrator|architect|analyst|associate|professional|specialist|expert|foundations?|"
                                r"fundamentals|practitioner|essentials|level|exam|master|tester|manager|consultant|editions?|version|management|service|services|"
                                r"security|operations|networking|cloud|analytics|design)\b", re.I)
_ORG_WORDS = re.compile(r"\b(?:academy|institute|university|college|society|association|council|foundation|inc|ltd|group|alliance|board|authority|body|school|"
                        r"centre|center|labs?|company|corporation|corp|programme|program)\b", re.I)
# A line of a list of publications: a tag ("[C6]"), "et al", or a list of authors ("M. Rinaldi, K. Aoki. ...")
_CITATION = re.compile(r"^(?i:publication|article|paper|journal article|book chapter|blog post|blog)\s*:|^\[[A-Za-z]{0,2}\d{1,3}\]|\bet al\b|^\(?\d{1,3}[.)]\s+(?:[A-Z]\.\s?){1,3}[A-Z][\w'’-]+|^(?:[A-Z]\.\s?){1,3}[A-Z][\w'’-]+,\s")


def _cert_parts(body: str, lex: cv_lexicon.Lexicon) -> List[str]:
    """The pieces of a line of a certification: the name first, then the issuer. A piece after a comma that goes on with the name
    ("Oracle Certified Professional, Java SE 8 Programmer") is joined to the name."""
    pieces = re.split(r"(\s*[|—–]\s*|\s+-\s+|\s*,\s*|\(|\))", body)
    out: List[str] = []
    for k in range(0, len(pieces), 2):
        text = pieces[k].strip(" ()-–—|,.:;")
        if not text:
            continue
        sep = pieces[k - 1].strip() if k else ""
        if len(out) == 1 and sep in (",", "-", "–", "—") and not _issuer_of(text, lex) and len(text.split()) <= 6 and _NAME_CONTINUATION.search(text) and _CERT_WORDS.search(out[0]) \
                and not _ORG_WORDS.search(text):
            out[0] = f"{out[0]}, {text}" if sep == "," else f"{out[0]} {sep} {text}"
            continue
        out.append(text)
    return out


def _free_cert(line: str, lex: cv_lexicon.Lexicon) -> Optional[Dict[str, Any]]:
    """An entry of a list of certifications that the taxonomy does not know: the name, the issuer (if the line has it) and the year.
    A line that is not shaped like a name of a certification (a sentence, a job title, a degree) gives None."""
    text = _flat(_unbullet(line)).strip()
    first_word = text.split()[0].strip(",.:;") if text.split() else ""
    brand = re.match(r"^[a-z]+[A-Z]", text) is not None or bool(first_word and lex.canonical_skill(first_word))      # "freeCodeCamp ...", "dbt Fundamentals"
    if (not 3 <= len(text) <= 110 or _is_detail(text, lex) or _NOT_CERT.search(text) or (text[:1].islower() and not brand)
            or _RANGE_RE.search(text) or _CITATION.search(text) or _CERT_STATUS.search(text)):
        return None
    year = _year_of(text)
    body = _EXPIRY.sub(" ", text)
    body = re.sub(r"\b(?:issued|completed|obtained|earned)\b\s*:?\s*(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}", " ", body, flags=re.I)
    body = _YEAR_IN.sub(" ", body)
    body = _DASH_IN_NAME.sub(" \u0001 ", body)
    body = re.sub(r"\(([^()]*)\)(?=\s+[A-Za-z])", lambda m: _OPEN + m.group(1) + _CLOSE, body)       # "SQL (Advanced) Certificate": the bracket is in the name
    parts = [p.replace("\u0001", "-").strip(" ()-–—|,.:;") for p in _cert_parts(body, lex) if p.strip(" ()-–—|,.:;")]
    parts = [re.sub(r"\s*-\s*$", "", p).replace(_OPEN, "(").replace(_CLOSE, ")") for p in parts]
    if not parts:
        return None
    name = re.sub(r"\s+-\s+", " - ", parts[0].replace(" - ", " - "))
    abbreviation = re.match(re.escape(name) + r"\s*\(([A-Z][A-Z0-9+-]{1,9}(?: [A-Za-z0-9+]{1,12}){0,2})\)", text)
    if abbreviation and len(name.split()) >= 2:
        name = f"{name} ({abbreviation.group(1)})"          # "Certified Scrum Master (CSM)": the short name is part of the name
    words = name.split()
    if name.lower().split()[0] in _VERBS or (name.endswith(".") and len(words) > 4) or len(words) > 12 or len(name) < 3:
        return None
    issuer = ""
    for p in parts[1:]:
        found = _issuer_of(p, lex)
        if found:
            issuer = found
            break
    if not issuer and not _issuer_of(name, lex):
        issuer = _issuer_of(body, lex)
    if not issuer and len(words) >= 2 and len(parts) > 1 and len(parts[1].split()) <= 4 and re.match(r"[A-Z]", parts[1]) and not parts[1].isupper() and not _CERT_WORDS.search(parts[1]):
        issuer = parts[1]
    if _score_title(name, lex) and not (_CERT_WORDS.search(name) or year is not None or re.search(r"\([A-Z0-9]{2,8}\)", text) or _issuer_of(text, lex)):
        return None                          # a job title ("Data Analyst"), not a certification
    shaped = (_ACRONYM.match(name) is not None or _CERT_WORDS.search(name) is not None or bool(issuer) or bool(_issuer_of(name, lex))
              or (2 <= len(words) <= 8 and sum(1 for w in words if w[:1].isupper()) >= 0.6 * len(words) and not _looks_like_name(name, lex)))
    if not shaped:
        return None
    return {"name": scrub_contact(name)[:100], "issuer": scrub_contact(issuer)[:60], "year": year}


def read_certifications(lines: List[str], secs: List[_Sec], lex: Optional[cv_lexicon.Lexicon] = None) -> List[Dict[str, Any]]:
    """The certifications: {name, issuer, year}. The names of the taxonomy (and its aliases) are found in any line, also when a long name is cut over
    two lines. Other entries of a list of certifications, and lines that start with "Certified ...", are kept as they are written.
    The lines under an entry that only tell the issuer and the dates give the year of the entry (the year of expiry is not used)."""
    lex = lex or cv_lexicon.get()
    out: List[Dict[str, Any]] = []
    seen: set = set()
    skip = set(_indices_of(secs, "experience", "skills", "projects"))
    in_cert = set(_indices_of(secs, "certs"))
    consumed: set = set()

    def add(name: str, issuer: str, year: Optional[int]) -> None:
        key = cv_lexicon.cert_key(name)
        if key and key not in seen:
            seen.add(key)
            out.append({"name": name, "issuer": issuer, "year": year})

    def details_after(end: int) -> Optional[int]:
        year: Optional[int] = None
        k = end
        while k < len(lines) and k < end + 3 and k not in skip and _is_detail(lines[k], lex):
            consumed.add(k)
            if year is None and not re.match(r"^[\s·•|,;\-–—]*(?:expires?|expiry|expiration|valid)", lines[k], re.I):
                year = _year_of(lines[k])
            k += 1
        return year

    for i in range(len(lines)):
        if i in skip or i in consumed or _header_of(lines[i]):
            continue
        done = False
        for size in (1, 2, 3):
            window = lines[i:i + size]
            if len(window) < size or any((i + k) in skip for k in range(size)):
                continue
            joined = " ".join(window)
            hits = lex.find_certs(joined)
            if not hits:
                continue
            if size > 1 and (lex.find_certs(" ".join(window[1:])) or lex.find_certs(lines[i])):
                continue                   # the name is not cut over the lines: a shorter window will find it
            consumed.update(range(i, i + size))
            if _CERT_STATUS.search(joined):
                done = True                    # "CompTIA Network+: planned for 2027", "exam booked": the person does not hold it
                break
            year = _year_of(joined)
            later = details_after(i + size)
            for cert in hits:
                add(cert["name"], cert["issuer"], year if year is not None else later)
            done = True
            break
        if done:
            continue
        line = lines[i]
        if i in in_cert:
            entry = _free_cert(line, lex)
            if entry and not _DATE_ONLY.match(line):
                later = details_after(i + 1)
                add(entry["name"], entry["issuer"], entry["year"] if entry["year"] is not None else later)
        elif re.match(r"^(?:[A-Z][\w+.#&-]*\s+){0,3}(?:Certified|Certification|Certificate|Professional Certificate)\b", _unbullet(line)) and len(line) <= 110 \
                and _best_title(line, lex) is None and not any(rx.search(line.lower()) for rx, _ in _QUAL_RULES[:11]) and not line.endswith("."):
            entry = _free_cert(line, lex)
            if entry:
                later = details_after(i + 1)
                add(entry["name"], entry["issuer"], entry["year"] if entry["year"] is not None else later)
    # A name that is cut over two lines, when the second line has a code that the list knows ("Microsoft Certified: Power BI Data Analyst" / "Associate (PL-300), 2023"),
    # gives the name of the list for the second line and the first part as an entry of its own. The first part goes.
    names = [c["name"].lower() for c in out]
    out = [c for c in out if not any(other.startswith(c["name"].lower() + " ") for other in names)]
    return out[:12]


# =====================================================================
# Awards
# =====================================================================
# Words of a line that names a prize or a place. Outside a list of awards only these count. In a list, a line also counts with the words of
# _AWARD_TRIGGER_LIST ("Speaker, ... Summit", "Maintainer of ..."): in a list they are awards, in a sentence they are only a job or a hobby.
_AWARD_TRIGGER = re.compile(r"\b(?:winner|won|finalist|runner[- ]up|1st place|first place|2nd place|second place|3rd place|third place|top \d+|ranked (?:\d+|top)|"
                            r"gold medal|silver medal|bronze medal|awarded|award|prize|dean'?s (?:honou?r )?(?:list|roll)|scholarship|medal|champion|best paper|"
                            r"patent|hall of fame|employee of the|engineer of the|valedictorian|\w+ of the (?:year|quarter|month|half))\b", re.I)
_AWARD_TRIGGER_LIST = re.compile(_AWARD_TRIGGER.pattern + r"|\b(?:speaker|keynote|maintainer|core contributor|top contributor|first[- ]class honou?rs|fellowship|top performer|"
                                 r"star performer|spotlight|honou?r roll|invited talk)\b", re.I)
_AWARD_NOUN = re.compile(r"\b(?:award|prize|medal|scholarship|fellowship)s?\b", re.I)
_AWARD_NOT = re.compile(r"award[- ]winning|prize[- ]winning|\bwinning\b", re.I)


_EXTRA_PLACES = """new zealand|united kingdom|uk|england|scotland|wales|ireland|united states|usa|us|canada|mexico|brazil|argentina|chile|colombia|peru|japan|china|india|
singapore|malaysia|indonesia|philippines|thailand|vietnam|south korea|taiwan|hong kong|israel|turkey|egypt|nigeria|kenya|south africa|ghana|morocco|uae|
united arab emirates|saudi arabia|pakistan|bangladesh|sri lanka|nepal|sweden|norway|denmark|finland|iceland|germany|france|spain|portugal|italy|netherlands|
belgium|luxembourg|switzerland|austria|poland|czechia|czech republic|slovakia|hungary|romania|bulgaria|greece|croatia|serbia|slovenia|estonia|latvia|
lithuania|ukraine|russia|ontario|quebec|alberta|british columbia|bavaria|catalonia"""
_PLACES = ({c.lower() for c in R.LOCATIONS} | {c.lower() for c in R.COUNTRIES} | {"nsw", "vic", "qld", "wa", "sa", "tas", "act", "nt", "australia"}
           | {w.strip() for w in _EXTRA_PLACES.split("|")})


def _employers(lines: List[str], positions: List[_Pos], lex: cv_lexicon.Lexicon, now: Any) -> List[str]:
    """The names of the employers of the CV: the pieces of the heading of a job that are not the title, the dates or a place.
    Only names of two words or more (or with a word like Pty, Ltd, Labs). They are cut out of the name of an award: the shared profile shows the names
    of the awards to employers, and the name of a former employer is career data of the talent (AI_Rule Rule 5)."""
    found: List[str] = []
    for p in positions:
        for i in range(max(0, p.first - 1), min(len(lines), p.last + 2)):
            line = lines[i]
            if i == p.first - 1 and (len(line.split()) > 6 or _BULLET_START.match(line) or find_ranges(line, now)):
                continue
            if i > p.last and (len(line.split()) > 8 or _BULLET_START.match(line) or find_ranges(line, now)):
                continue                          # the line after the heading of a job is the employer ("Title  Dates" / "Employer, Place"), or a bullet
            for seg in _segments(_strip_ranges(line)):
                words = seg.split()
                if (not 1 <= len(words) <= 6 or not seg[:1].isupper() or re.search(r"\d", seg) or seg.lower() in _PLACES or _score_title(seg, lex)
                        or all(w.lower().strip(",") in _PLACES for w in words) or words[0].lower() in _VERBS):
                    continue
                if len(words) >= 2 or re.search(r"\b(?:pty|ltd|inc|llc|labs?|gmbh|corp)\b", seg, re.I):
                    if seg.lower() not in {f.lower() for f in found}:
                        found.append(seg)
    for name in list(found):                       # "Altair Cloudworks Demo Inc." is also written "Altair Cloudworks Demo"
        short = name
        while True:
            cut = re.sub(r"[\s,]+(?:inc|ltd|llc|plc|gmbh|ag|sa|pty|pvt|corp|co|limited|kk|ab|bv|nv|oy)\.?$", "", short, flags=re.I).strip(" ,.")
            if cut == short:
                break
            short = cut
        if short != name and len(short.split()) >= 2 and short.lower() not in {f.lower() for f in found}:
            found.append(short)
    return sorted(found, key=len, reverse=True)


_GENERIC_AWARD_HEAD = re.compile(r"award|honou?r|achievement|recogni|prize|accolade|distinction", re.I)
_AWARD_LABEL = re.compile(r"^([A-Za-z][A-Za-z ]{2,28}):\s+(?=\S)")
_ID_IN_BRACKETS = re.compile(r"\s*\((?:[A-Z]{1,3}\s*)?[0-9][0-9\s/.-]{5,}\)")
_ENDING_WORDS = re.compile(r"[,;]?\s*\b(?:granted|filed|pending|awarded|issued)\s*$", re.I)


def _trim_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip(" ,-–—|:·")
    name = name.rstrip(" (").lstrip(" )")
    if name.count("(") < name.count(")"):
        name = name.rstrip(") ")
    if name.count("(") > name.count(")"):
        name = name[:name.rfind("(")]              # a bracket that was cut by the year ("Star Performer of the Quarter (Q3 2024)")
    return name.strip(" ,-–—|:·")


def _award_entry(line: str, lex: cv_lexicon.Lexicon, employers: Iterable[str] = (), heading: str = "") -> Optional[Dict[str, Any]]:
    text = _flat(_unbullet(line))
    sentences = [p.strip() for p in re.split(r"(?<=[a-z0-9)])\.\s+(?=[A-Z])", text) if p.strip()]
    if len(sentences) > 1 and sum(1 for p in sentences if len(p.split()) >= 3) > 1:
        hits = [p for p in sentences if _AWARD_TRIGGER_LIST.search(p) or lex.award_kind(p)]
        if len(hits) == 1:
            text = hits[0].rstrip(".")                # "Dissertation: A tool for routes. Dean's List 2023." gives the sentence that names the award
    if not 5 <= len(text) <= 140 or re.fullmatch(r"[\W\d_]*(?:19|20)\d{2}[\W\d_]*", text):
        return None
    year = _year_of(text)
    label = _AWARD_LABEL.match(text)
    quoted = re.search(r'["“]([^"”]{3,90})["”]', text)
    heading_kind = "" if (not heading or _GENERIC_AWARD_HEAD.search(heading)) else lex.award_kind(heading)     # "Patents" gives a kind, "Awards and Scholarships" does not
    kind = (lex.award_kind(label.group(1)) if label else "") or lex.award_kind(text) or heading_kind
    text = _ID_IN_BRACKETS.sub("", text)
    if (label and quoted and len(label.group(1).split()) <= 3) or (quoted and kind == "patent"):
        name = quoted.group(1)                       # 'Conference talk: "Forecasting at Scale", DataFest 2022': the name is the title
    else:
        if label and len(label.group(1).split()) == 1 and lex.award_kind(label.group(1)):
            text = text[label.end():]                # 'Patent: Method for ...': the one word before the colon is the kind, not the name
        if year is not None:
            before = _YEAR_IN.split(text)[0]
            name = before if len(before.split()) >= 2 else _YEAR_IN.sub(" ", text)
        else:
            name = text
    name = _trim_name(_ENDING_WORDS.sub("", _trim_name(name)))
    if kind == "employer-recognition" and "," in name:
        head = name.split(",")[0].strip()
        if len(head.split()) >= 2:
            name = head                     # the part after the comma is the employer: it is not part of the name
    for employer in employers:
        cut = re.sub(rf"\s*(?:[,|@–—-]|\bat\b|\bfrom\b|\bwith\b)?\s*(?<![A-Za-z]){re.escape(employer)}(?![A-Za-z])", "", name, flags=re.I)
        cut = _trim_name(cut)
        if cut != name and len(cut) >= 4:
            name = cut
    if len(name) < 4:
        return None
    return {"name": scrub_contact(name)[:100], "kind": kind, "year": year}


def _award_shaped(line: str, entry: Dict[str, Any], lex: cv_lexicon.Lexicon, plain: bool = False) -> bool:
    """Is a line of an awards section really an award? A sentence, a job title or a piece of another column is not."""
    text = _unbullet(line).strip()
    if not text or text[:1].islower() or _CITATION.search(text):
        return False
    first = text.split()[0].lower().strip(".,:")
    strong = lex.award_kind(text) != "" or _AWARD_TRIGGER_LIST.search(text) is not None        # the words of the line, not the heading of the list
    if strong:
        return True
    if first in _VERBS or _best_title(text, lex):
        return False
    words = text.split()
    if " " not in text.strip() and re.search(r"\d", text):
        return False                                    # an identifier ("US11234567B2"), not a name
    if text.count("|") >= 2 or _looks_like_name(text, lex) or _is_place_line(text) or re.match(r"^graduated\b", text, re.I):
        return False                                    # the name or the headline or the place of a person (the end of a sidebar), not an award
    if re.search(r"\b(?:courses?|certificates?|certifications?|certified|training)\b", text, re.I):
        return False                                    # a course or a certificate is not an award
    # A dated entry, or an entry in a list that names a kind ("Patents"). An entry with no year, no kind and no word of a prize ("Captain of the badminton team")
    # is an award only in a list that is only about awards ("Awards", "Honours and Prizes"), not in "Extra-curricular activities and awards".
    if plain and entry["year"] is None and entry["kind"] == "":
        return 2 <= len(words) <= 10 and not text.endswith(".")
    return (entry["year"] is not None or entry["kind"] != "") and 2 <= len(words) <= 14 and not text.endswith(".")


def _plain_awards_heading(heading: str) -> bool:
    """Is the heading of the list only about awards ("Awards", "Honours and Prizes"), and not also about activities, community, talks or publications?"""
    return bool(heading) and re.search(r"award|honou?r|prize|recogni|accolade|distinction", heading, re.I) is not None \
        and re.search(r"activit|extra|curricular|communit|volunteer|interest|leadership|open source|publication|talk|patent|paper", heading, re.I) is None


def _is_place_line(text: str) -> bool:
    """A line that is a place ("Toronto, Ontario, Canada"): short pieces with capitals, and the last one is a country or a known place."""
    pieces = [p.strip() for p in text.split(",") if p.strip()]
    if not 1 <= len(pieces) <= 4 or any(len(p.split()) > 3 or re.search(r"\d", p) or not p[:1].isupper() for p in pieces):
        return False
    return pieces[-1].lower() in _PLACES or (len(pieces) == 1 and pieces[0].lower() in _PLACES)


def read_awards(lines: List[str], secs: List[_Sec], lex: Optional[cv_lexicon.Lexicon] = None, employers: Iterable[str] = ()) -> List[Dict[str, Any]]:
    """The awards: {name, kind, year}. A line of an awards section is an award when it is shaped like one. A line in another part of the CV counts when
    it names a prize, a win or a place AND a kind of award that the taxonomy knows (or the word award, prize, medal or scholarship).
    A line under an award that only tells who gave it and when ("Issued by ... · Oct 2023", "2022") gives the year. The kind is "" when no kind fits."""
    lex = lex or cv_lexicon.get()
    strong = set(_indices_of(secs, "awards"))
    weak = set(_indices_of(secs, "awards_weak"))
    opensource = [sec for sec in secs if sec.kind == "projects" and re.search(r"open[- ]source", sec.head, re.I)]
    weak |= {i for sec in opensource for i in range(sec.start, sec.end)}      # a part with the heading "Open source": its entries are contributions (a kind of award)
    skip = set(_indices_of(secs, "skills", "contact", "summary", "objective", "top", "languages", "certs"))
    community = {i for sec in secs if sec.kind == "other" and re.search(r"communit|volunteer|activit|extra|leadership|involvement", sec.head, re.I)
                 for i in range(sec.start, sec.end)}
    out: List[Dict[str, Any]] = []
    last: Optional[Tuple[int, Dict[str, Any]]] = None
    seen: set = set()
    heading_of = {i: sec.head for sec in secs if sec.kind in ("awards", "awards_weak") or sec in opensource for i in range(sec.start, sec.end)}
    for i, line in enumerate(lines):
        if i in skip or _AWARD_NOT.search(line) or _header_of(line):
            continue
        in_list = i in strong or i in weak
        if in_list and last is not None and last[0] == i - 1 and _is_detail(line, lex):
            item = last[1]
            if item["year"] is None and not re.match(r"^[\s·•|,;\-–—]*(?:expires?|expiry|valid)", line, re.I):
                item["year"] = _year_of(line)
            if not item["kind"]:
                item["kind"] = lex.award_kind(item["name"] + " " + line)
            last = (i, item)
            continue
        dated = lex.award_kind(line, specific=True) != "" and _year_of(line) is not None           # "Organiser, DevFest Nairobi 2023": a kind and a year
        general = (_AWARD_TRIGGER.search(line) is not None and (bool(lex.award_kind(line)) or _AWARD_NOUN.search(line) is not None)
                   and len(line) <= 120 and not _CONTACT_RE.search(line) and not _RANGE_RE.search(line))     # a line with dates is an activity, not an award
        if i in strong:
            ok = _CITATION.search(_unbullet(line)) is None
        elif i in weak:
            ok = (_AWARD_TRIGGER_LIST.search(line) is not None or dated) and _CITATION.search(_unbullet(line)) is None
        elif i in community:
            ok = (general or (dated and not _RANGE_RE.search(line))) and _CITATION.search(_unbullet(line)) is None      # a part about the community: dated entries of a kind
        else:
            ok = general
        if not ok:
            continue
        entry = _award_entry(line, lex, employers, heading_of.get(i, ""))
        if not entry or not (not in_list or _award_shaped(line, entry, lex, _plain_awards_heading(heading_of.get(i, "")))) or entry["name"].lower() in seen:
            continue
        seen.add(entry["name"].lower())
        out.append(entry)
        last = (i, entry)
    return out[:12]


# =====================================================================
# Evidence
# =====================================================================
def read_evidence(experience_lines: List[str]) -> List[str]:
    """Bullet lines that show what the person did. Private to the talent. Contact details are removed."""
    scored = []
    for k, line in enumerate(experience_lines):
        text = _flat(re.sub(r"^[•·▪●*\-–—\s]+", "", line))
        if not (25 <= len(text) <= 240):
            continue
        if _RANGE_RE.search(text) and not _VERB_START.match(text):
            continue  # a heading with dates (a job title and a company), not something the person did
        if re.search(r"@|https?://|www\.", text):
            continue
        has_verb = bool(_VERB_START.match(text))
        has_number = bool(re.search(r"\d", text))
        words = text.split()
        if not has_verb and not has_number and len(words) < 7:
            continue
        scored.append((-(2 if has_verb else 0) - (1 if has_number else 0), k, scrub_contact(text)))
    scored.sort()
    picked = sorted(scored[:8], key=lambda t: t[1])
    return [t[2] for t in picked]


# =====================================================================
# Main entry
# =====================================================================
FIELD_ORDER = ["qualification", "fieldOfStudy", "studyCountry", "currentRole", "industry", "years", "skills"]
_NEW_FIELDS = ["targetRole", "level", "yearsExperience", "certifications", "awards"]


def _safe(fn, default, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:  # noqa: BLE001 - the reader of one field must not stop the others
        if _STRICT:
            raise
        return default


def parse_cv(text: str, today: Any = None) -> Dict[str, Any]:
    """Return { fields, detected, missing, evidence, ... } for a CV text. Never raises for odd text.

    fields    the profile keys that the CV shows. The old keys stay. New keys (only when the CV shows them): targetRole (list), level,
              yearsExperience, certifications [{name, issuer, year}], awards [{name, kind, year}]. fields.currentRole is a list: the current role first.
    detected  the keys of fields.   missing  the old keys that the CV does not show.
    currentRole, targetRole, level, yearsExperience, certifications, awards   the same values as plain values (empty when not found)
    skills    [{name, level}] with the level 1 to 5 of each skill, or null when the CV gives no evidence
    found     {currentRole, targetRole, level, yearsExperience, certifications, awards}: true when the reader found the field
    sources   how each new field was found (the name of the rule)
    domain    the domain of the CV (Software Engineering, AI & Machine Learning or Data), when the reader can tell
    today     the day that "Present" means (a test sets it, so that the years do not change with time)
    """
    lex = cv_lexicon.get()
    now = today or datetime.now(timezone.utc)
    lines = _split_inline_headings(_clean_lines(text))
    if _is_lowercase_text(text):
        lines = [_capitalise_words(l) for l in lines]
    secs = _split_sections(lines)
    exp_idx = _indices_of(secs, "experience")
    has_exp = bool(exp_idx)
    region = exp_idx if has_exp else _fallback_region(secs)
    edu_lines = _lines_of(lines, secs, "education") or [l for l in lines if _EDU_LINE.search(l)]
    skill_lines = _lines_of(lines, secs, "skills") + [l for l in lines if re.match(r"^(?:tools?|tech|stack|technologies|tech stack|environment|built with)\s*:", l, re.I)]
    exp_lines = [lines[i] for i in exp_idx] if has_exp else [lines[i] for i in region if not _EDU_LINE.search(lines[i]) or _TITLE_RE.search(lines[i])]
    whole = "\n".join(lines)
    work_text = "\n".join(exp_lines) if exp_lines else whole
    sources: Dict[str, str] = {}

    # ----- the jobs -----
    positions, undated = _safe(_read_positions, ([], []), lines, region, now, lex)
    if undated and not any(p.a is not None for p in positions):
        positions = _safe(_pair_timeline, positions, positions, undated, lines, secs, now)
    study = _study_ranges(lines, secs, now)
    positions = [p for p in positions if not _is_study_role(p, study)]       # a research assistant in the years of the degree is study, not a job
    # ----- years -----
    spans = [(p.a, p.b) for p in positions if p.a is not None and p.b is not None]
    years_dates = _union_years(spans)
    overall, skill_years = _safe(read_year_statements, ([], {}), whole, lex, now)
    years_stmt = max(overall) if overall else 0.0
    years: Optional[float] = None
    if years_dates > 0 or years_stmt > 0:
        years = round(min(40.0, max(years_dates, years_stmt)), 1)
        sources["yearsExperience"] = "statement" if years_stmt > years_dates else "dates"
    # ----- the current role -----
    current: Optional[str] = None
    pos, rule = _current_position(positions)
    if pos:
        current, sources["currentRole"] = pos.title, rule
    headline, headline_kind, _ = _safe(_read_headline, (None, "", None), lines, secs, lex)
    if not current and headline and headline_kind == "current":
        current, sources["currentRole"] = headline, "headline"
    if not current:
        for k, line in enumerate(lines[:80]):
            m = re.match(r"^(?:current (?:role|position|title|job)|occupation or position held|position held|job title|current occupation)\s*[:\-–]?\s*(.*)$", line, re.I)
            if m:
                value = m.group(1).strip() or (lines[k + 1] if k + 1 < len(lines) else "")
                best = _best_title(value, lex)
                if best:
                    current, sources["currentRole"] = best[1], "label"
                    break
    if not current:
        said = _safe(_role_in_sentence, None, "\n".join(_lines_of(lines, secs, "top", "summary", "objective")[:14]), lex)
        if said:
            current, sources["currentRole"] = said, "summary"
    if not current and undated and not positions:
        current, sources["currentRole"] = undated[0][1], "first-listed"
    # ----- the target role -----
    targets, how = _safe(read_target_roles, ([], ""), lines, secs, lex)
    if not targets and headline and headline_kind == "target":
        role = lex.canonical_role(headline) or next(iter([r for _, _, r in lex.find_roles(headline)]), None)
        if role:
            targets, how = [role], "headline"
    if targets:
        sources["targetRole"] = how
    # ----- the level -----
    level: Optional[str] = None
    if current:
        level = lex.level_of_title(current)
        if level:
            sources["level"] = "title"
    if not level and headline and headline_kind == "current":
        level = lex.level_of_title(headline)
        if level:
            sources["level"] = "headline"
    if not level and (years is None or years < 1):
        if _STUDENT.search(whole) and not _GRADUATE.search(whole):
            level, sources["level"] = "Intern", "student"
        elif _GRADUATE.search(whole):
            level, sources["level"] = "Junior", "graduate"
    if not level and years is not None and years > 0:
        level, sources["level"] = level_from_years(years), "years"
    # ----- the lists -----
    certs = _safe(read_certifications, [], lines, secs, lex)
    employers = _safe(_employers, [], lines, positions, lex, now)
    awards = _safe(read_awards, [], lines, secs, lex, employers)
    # ----- the roles for the list "current and past roles" -----
    titles: List[str] = []
    for t in ([current] if current else []) + [p.title for p in positions if p.title] + [t for _, t in undated]:
        if t and t.lower() not in {x.lower() for x in titles}:
            titles.append(t)
    roles = _with_standard_roles(titles, work_text) if titles else read_roles(exp_lines if has_exp else lines[:60], work_text)
    if current and roles and roles[0] != current:
        roles = [current] + [r for r in roles if r != current][:3]
    # ----- skills -----
    entries = _safe(read_skill_entries, [], skill_lines, lex)
    skills = read_skills(skill_lines, whole)
    bodies = []
    ordered = sorted(positions, key=lambda p: p.first)
    for k, p in enumerate(ordered):
        stop = ordered[k + 1].first if k + 1 < len(ordered) else (max(region) + 1 if region else len(lines))
        bodies.append("\n".join(lines[p.first:stop]))
    skill_levels = _safe(_skill_levels, [{"name": s, "level": None} for s in skills], skills, entries, ordered, bodies, skill_years, now, lex)

    # ----- the domains (the profile key "industry" holds the domains of the platform) -----
    domains = _safe(lex.domains_of, [], titles, targets, headline or "", skills, whole)

    fields: Dict[str, Any] = {
        "qualification": read_qualifications(edu_lines if _lines_of(lines, secs, "education") else lines),
        "fieldOfStudy": read_fields_of_study(edu_lines),
        "studyCountry": read_study_countries(edu_lines),
        "currentRole": roles,
        "industry": domains,
        "skills": skills,
    }
    fields["years"] = _band(years) if years else ""
    new_values = {"targetRole": targets, "level": level or "", "yearsExperience": years, "certifications": certs, "awards": awards}

    detected, missing, result = [], [], {}
    for key in FIELD_ORDER:
        value = fields.get(key)
        if value:
            detected.append(key)
            result[key] = value
        else:
            missing.append(key)
    for key in _NEW_FIELDS:
        value = new_values[key]
        if value or value == 0:
            detected.append(key)
            result[key] = value
    domain = domains[0] if domains else ""
    return {
        "fields": result, "detected": detected, "missing": missing, "evidence": read_evidence(exp_lines),
        "currentRole": current or "", "targetRole": targets[0] if targets else "", "level": level or "", "yearsExperience": years,
        "certifications": certs, "awards": awards, "skills": skill_levels,
        "found": {"currentRole": bool(current), "targetRole": bool(targets), "level": bool(level), "yearsExperience": years is not None,
                  "certifications": bool(certs), "awards": bool(awards)},
        "sources": sources, "domain": domain,
    }
