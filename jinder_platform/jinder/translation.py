"""The cross-border and cross-industry skill translation engine (Feature 2; version 2: ICT only).

Input: the talent's profile (roles, skills, qualifications, countries) and the CV evidence lines.
Output: translated skills, each with a plain-language reason, an evidence level and a skill level (1 to 5). No score on the person.

Every name in the output is a name of the taxonomy (`taxonomy.py`): a role of the role list, a skill of the skill list.
A role gets the occupation (code and title) from the taxonomy. A skill that the taxonomy does not know keeps its name.

This module never uses nationality, ethnicity, gender, age or visa status. The country of study is used
only for the AQF note on qualifications and for the word "cross-border" (PRD: no formal credential verification).
"""
import hashlib
import re
from typing import Any, Dict, List, Optional

from . import skills as skills_module
from . import taxonomy
from .util import as_list

_T = taxonomy.get()

# A skill with no level gets the level of its evidence (rule F8)
EVIDENCE_LEVEL = {"Strong": 4, "Moderate": 3, "Limited": 2}

# Mapping library. "test" runs on one role title or one skill (lower case). "mapped" is a name of the taxonomy.
# kind: "cross-border" (an overseas title, tool or standard), "cross-industry" (the same competency in a different field of work)
# or "direct" (a common name for the same thing).
# "overseas": the pair is used only when the talent studied or worked overseas, or the title has a place in brackets, for example
# "Software Developer (Vietnam)". In that case the kind is "cross-border". If not, the title is read as a title of the role list.
_ROLES = [
    dict(test=r"\b(sde|swe|software development engineer)\b", mapped="Software Engineer", kind="cross-border",
         reason="SDE and SWE are common overseas titles. In Australia the same work is a Software Engineer role."),
    dict(test=r"^software developer\b", mapped="Software Engineer", kind="cross-border", overseas=True,
         reason="Software Developer is a common title overseas for what Australian employers call a Software Engineer."),
    dict(test=r"analyst[- ]programmer|application programmer|applications developer|software programmer", mapped="Software Developer", kind="cross-border",
         reason="Programmer titles overseas match the Australian Software Developer role: you design, write and test code."),
    dict(test=r"^(computer |web |application )?programmer$|^coder$", mapped="Software Developer", kind="cross-border",
         reason="Programmer is an older title for the Australian Software Developer role."),
    dict(test=r"j2ee|java (developer|engineer|programmer)", mapped="Java Developer", kind="direct", reason="Java Developer has the same meaning in Australia."),
    dict(test=r"\.net|dotnet|c# (developer|engineer)|asp\.net", mapped=".NET Developer", kind="direct", reason=".NET Developer has the same meaning in Australia."),
    dict(test=r"python (developer|engineer|programmer)", mapped="Python Developer", kind="direct", reason="Python Developer has the same meaning in Australia."),
    dict(test=r"(front[- ]?end|ui|react|angular|vue) (developer|engineer)", mapped="Frontend Engineer", kind="direct",
         reason="Front-end work has the same meaning in Australia. Australian ads call the role Frontend Engineer."),
    dict(test=r"(back[- ]?end|server[- ]side|api) (developer|engineer)", mapped="Backend Engineer", kind="direct",
         reason="Back-end work has the same meaning in Australia. Australian ads call the role Backend Engineer."),
    dict(test=r"full[- ]?stack", mapped="Full-stack Engineer", kind="direct", reason="Full-stack work has the same meaning in Australia."),
    dict(test=r"web (developer|designer|master)|website developer|wordpress developer", mapped="Web Developer", kind="direct",
         reason="Web development has the same meaning in Australia."),
    dict(test=r"(android|ios|mobile|flutter|react native)( app| application)? (developer|engineer)", mapped="Mobile Developer", kind="direct",
         reason="Mobile development has the same meaning in Australia."),
    dict(test=r"(system|systems|network|infrastructure|it infrastructure) (administrator|admin|engineer)|sysadmin", mapped="Platform Engineer", kind="cross-industry",
         reason="Running servers and networks is close to platform engineering in Australia, where teams also write code to run the platform.",
         gaps=["Infrastructure as code (for example Terraform)"]),
    dict(test=r"devops|release engineer|build (and release )?engineer", mapped="DevOps Engineer", kind="direct", reason="DevOps Engineer has the same meaning in Australia."),
    dict(test=r"\bsre\b|site reliability|reliability engineer", mapped="Site Reliability Engineer", kind="direct", reason="Site Reliability Engineer has the same meaning in Australia."),
    dict(test=r"cloud (engineer|administrator|developer|specialist)|(aws|azure|gcp) (engineer|developer)", mapped="Cloud Engineer", kind="direct",
         reason="Cloud Engineer has the same meaning in Australia."),
    dict(test=r"(solution|solutions|enterprise|technical) architect|solution designer", mapped="Solutions Architect", kind="direct",
         reason="Solutions Architect has the same meaning in Australia."),
    dict(test=r"software architect|technical architect|application architect", mapped="Software Architect", kind="direct", reason="Software Architect has the same meaning in Australia."),
    dict(test=r"test automation|automation (test )?(engineer|tester)|\bsdet\b", mapped="Test Automation Engineer", kind="direct",
         reason="Test automation work has the same meaning in Australia."),
    dict(test=r"(qa|quality assurance|quality) (engineer|analyst|specialist)|test engineer", mapped="QA Engineer", kind="direct", reason="QA Engineer has the same meaning in Australia."),
    dict(test=r"\btester\b|testing engineer|software tester", mapped="Software Tester", kind="direct", reason="Software Tester has the same meaning in Australia."),
    dict(test=r"(information|cyber|network|application|it) security (engineer|analyst|specialist|officer)|infosec|soc analyst", mapped="Security Engineer",
         kind="cross-border", reason="Security analyst and officer titles overseas match the Australian Security Engineer role."),
    dict(test=r"machine learning (engineer|developer)|\bml engineer\b", mapped="Machine Learning Engineer", kind="direct", reason="Machine Learning Engineer has the same meaning in Australia."),
    dict(test=r"(ai|artificial intelligence) (engineer|developer|specialist)|ai/ml (engineer|developer)", mapped="AI Engineer", kind="direct", reason="AI Engineer has the same meaning in Australia."),
    dict(test=r"(gen(erative)? ?ai|llm|prompt|chatbot|conversational ai) (engineer|developer)", mapped="Generative AI Engineer", kind="direct",
         reason="Generative AI work has the same meaning in Australia."),
    dict(test=r"mlops|ml platform|machine learning platform", mapped="MLOps Engineer", kind="direct", reason="MLOps work has the same meaning in Australia."),
    dict(test=r"nlp (engineer|specialist|developer)|natural language", mapped="NLP Engineer", kind="direct", reason="NLP work has the same meaning in Australia."),
    dict(test=r"computer vision|image processing (engineer|developer)", mapped="Computer Vision Engineer", kind="direct", reason="Computer vision work has the same meaning in Australia."),
    dict(test=r"applied scientist|research scientist|ai researcher|research engineer", mapped="Applied Scientist", kind="cross-industry",
         reason="Research roles in machine learning match the Australian Applied Scientist role: you test ideas and build models that ship."),
    dict(test=r"etl (developer|engineer)|informatica|datastage|ssis developer|talend", mapped="ETL Developer", kind="cross-border",
         reason="ETL titles and tools overseas match the Australian ETL Developer and Data Engineer roles."),
    dict(test=r"data warehouse (developer|engineer|specialist)|dwh|datawarehouse", mapped="Data Warehouse Engineer", kind="direct", reason="Data warehouse work has the same meaning in Australia."),
    dict(test=r"(big data|hadoop|spark) (engineer|developer)|big data", mapped="Big Data Engineer", kind="direct", reason="Big data work has the same meaning in Australia."),
    dict(test=r"data (engineer|developer|pipeline engineer|integration engineer)|analytics engineer", mapped="Data Engineer", kind="direct", reason="Data Engineer has the same meaning in Australia."),
    dict(test=r"database (administrator|admin|developer|engineer)|\bdba\b|sql developer", mapped="Database Administrator", kind="direct",
         reason="Database work has the same meaning in Australia. Many teams ask for data engineering skills in the same role.", gaps=["Cloud data platforms (for example Snowflake or Databricks)"]),
    dict(test=r"\bbi (specialist|executive|officer|consultant)|business intelligence (specialist|executive|officer|consultant)", mapped="Data Analyst", kind="cross-border",
         reason="BI Specialist and BI Executive are common overseas titles. In Australia the same work (reports, dashboards, finding answers in data) is a Data Analyst role."),
    dict(test=r"\bmis (executive|analyst|officer|specialist|developer)|management information", mapped="Data Analyst", kind="cross-border",
         reason="MIS titles overseas describe reporting and analysis of company data. In Australia this is a Data Analyst role."),
    dict(test=r"(business intelligence|\bbi) (analyst|developer)|power bi developer|tableau developer|report(ing)? (developer|analyst|specialist)|reporting analyst", mapped="Business Intelligence Analyst",
         kind="direct", reason="Business Intelligence Analyst has the same meaning in Australia."),
    dict(test=r"data (analyst|analytics (specialist|executive))|analytics (analyst|executive|specialist)", mapped="Data Analyst", kind="direct", reason="Data Analyst has the same meaning in Australia."),
    dict(test=r"product analyst|growth analyst", mapped="Product Analyst", kind="direct", reason="Product Analyst has the same meaning in Australia."),
    dict(test=r"quantitative (analyst|researcher|developer)|\bquant\b", mapped="Data Scientist", kind="cross-industry",
         reason="Quantitative work uses statistics and models on data. Australian Data Scientist roles ask for the same skills."),
    dict(test=r"data scien(tist|ce (executive|specialist|engineer))|machine learning scientist", mapped="Data Scientist", kind="direct", reason="Data Scientist has the same meaning in Australia."),
    dict(test=r"statistic(ian|al (analyst|programmer))|biostatistician", mapped="Statistician", kind="direct", reason="Statistician has the same meaning in Australia."),
    dict(test=r"business systems? analyst|(system|systems|functional|it business) analyst", mapped="Business Systems Analyst", kind="cross-border",
         reason="Systems Analyst is a common overseas title. In Australia the same work is a Business Systems Analyst role."),
    dict(test=r"business analyst|requirements analyst|\bba\b", mapped="Business Analyst", kind="direct", reason="Business Analyst has the same meaning in Australia."),
    # The last choice. A title that only ends with "Engineer" is NOT enough: the engineer titles of other fields of work are not ICT titles, and a title that is not an ICT title
    # gives no role card (plan V2_PLAN.md, F11). The tests in tests/test_qa_fixes.py have the list of titles. The title must be a bare "Engineer" or "Developer" (with "Software", "Application" or "Systems" before it), start with "Software",
    # or have a word of ICT work before "Engineer" or "Developer" (for example "PHP Developer", "Embedded Software Engineer", "Unity Developer").
    dict(test=(r"^(software |application |applications |systems )?(engineer|developer)$|^software [a-z ]*(engineer|developer|programmer)\b|"
               r"\b(web|mobile|game|app|embedded|firmware|cloud|data|ml|ai|devops|sre|security|network|database|back-?end|front-?end|full[- ]?stack|platform|automation|"
               r"python|java|javascript|typescript|php|ruby|golang|go|rust|swift|kotlin|node(\.js)?|react|angular|vue|\.net|c\+\+|c#|sap|salesforce|unity|unreal|blockchain|ios|android|api|sql|etl)\b.*\b(engineer|developer)\b"),
         mapped="Software Engineer", kind="direct", reason="Software work has the same meaning in Australia.", weak=True),
]

# Skills that need a pair: another word or an overseas tool for a skill of the taxonomy. A skill name or alias of the taxonomy needs no pair.
_SKILLS = [
    dict(test=r"spreadsheets?|google sheets|advanced excel|excel macros?|\bms excel\b", mapped="Microsoft Excel", kind="direct", reason="Spreadsheet skills are listed as Microsoft Excel in most Australian job ads."),
    dict(test=r"kanban|sprint|backlog|stand-?ups?|scrum master|jira", mapped="Agile delivery", kind="direct", reason="Backlogs, sprints and Kanban boards are part of agile delivery."),
    dict(test=r"qlik(view|sense)?|cognos|microstrategy|business objects|crystal reports|dashboards?|bi tools|reporting tools", mapped="Data visualisation", kind="cross-border",
         reason="Overseas reporting and dashboard tools match the data visualisation skills that Australian job ads list as Power BI or Tableau."),
    dict(test=r"data (cleaning|cleansing|wrangling|preparation|munging)", mapped="Data analysis", kind="direct", reason="Cleaning and preparing data is part of data analysis."),
    dict(test=r"predictive (model(l)?ing|analytics)|ml models?|machine-learning models?", mapped="Machine learning", kind="direct", reason="Predictive models are what Australian job ads call machine learning."),
    dict(test=r"oracle( db| database| 1[0-9]c| 19c)?$|oracle sql", mapped="Oracle Database", kind="direct", reason="Oracle Database has the same name in Australia."),
    dict(test=r"bash scripting|unix scripting|shell scripts?|linux administration|unix administration", mapped="Linux", kind="direct", reason="Linux and Unix administration is listed as Linux in Australian job ads."),
    dict(test=r"rest(ful)? (apis?|services?)|web services|web apis?", mapped="API design", kind="direct", reason="Building web services is what Australian job ads call API design."),
    dict(test=r"regression testing|test cases?|test plans?|test scripts?|\buat\b|manual qa", mapped="Manual testing", kind="direct", reason="Writing and running test cases by hand is manual testing."),
    dict(test=r"unit tests?|unit testing|tdd|integration tests?|junit", mapped="Unit and integration testing", kind="direct", reason="Unit and integration tests have the same meaning in Australia."),
    dict(test=r"copilot|prompt design|prompt writing|chatgpt prompts?", mapped="Prompt engineering", kind="direct", reason="Writing prompts for AI models is called prompt engineering."),
    dict(test=r"algorithms?|leetcode|competitive programming|data structures", mapped="Data structures and algorithms", kind="direct", reason="This is the skill that Australian job ads list as data structures and algorithms."),
    dict(test=r"design patterns|solid principles|clean code|oop|object[- ]oriented", mapped="Object-oriented design", kind="direct", reason="Design patterns and OOP are listed as object-oriented design."),
    dict(test=r"build automation|release management|deployment automation|ci ?/ ?cd|continuous (integration|delivery|deployment)", mapped="CI/CD", kind="direct", reason="Automated builds and releases are listed as CI/CD."),
    dict(test=r"containeri[sz]ation|docker containers?|containers?", mapped="Docker", kind="direct", reason="Containers are listed as Docker in Australian job ads."),
    dict(test=r"container orchestration|openshift|k8s|helm", mapped="Kubernetes", kind="direct", reason="Container orchestration is listed as Kubernetes."),
    dict(test=r"infrastructure automation|cloudformation|iac|infrastructure[- ]as[- ]code", mapped="Infrastructure as code", kind="direct", reason="Automating infrastructure is listed as infrastructure as code."),
    dict(test=r"monitoring|alerting|logging|splunk|datadog|new relic|\belk\b", mapped="Observability", kind="direct", reason="Monitoring, logging and alerting are listed as observability."),
    dict(test=r"team management|people management|managing (a )?team|line management|supervis(ing|ion)|people (and|&) team leadership", mapped="Team leadership", kind="cross-industry",
         reason="Leading people transfers to any Australian role that leads a team, also in technology."),
    dict(test=r"coaching|training (junior|new)|onboarding (new|junior)|knowledge transfer", mapped="Mentoring", kind="cross-industry", reason="Coaching and training colleagues is called mentoring."),
    dict(test=r"client communication|presentation skills|written communication|verbal communication|report writing|communication skills", mapped="Communication", kind="direct", reason="Communication has the same meaning in Australia."),
    dict(test=r"stakeholder (engagement|communication)|client management|customer management|vendor management|supplier management|cross[- ](department|functional)",
         mapped="Stakeholder management", kind="cross-industry", reason="Working with clients, vendors and other teams is what Australian employers call stakeholder management."),
    dict(test=r"project (coordination|planning|delivery|management)|\bpmo\b|prince2|waterfall", mapped="Project management", kind="direct", reason="Planning and delivering projects is project management."),
    dict(test=r"root cause|troubleshoot|incident (debugging|analysis)|bug fixing", mapped="Debugging and troubleshooting", kind="direct", reason="Finding and fixing faults is listed as debugging and troubleshooting."),
    dict(test=r"escalation|issue resolution|problem resolution|analytical (thinking|skills)|critical thinking", mapped="Problem solving", kind="direct", reason="Fixing escalated issues shows problem solving."),
    dict(test=r"requirements (gathering|elicitation|analysis)|process mapping|use cases?|user stories|business requirements|\bbrd\b", mapped="Requirements analysis", kind="direct",
         reason="These are standard requirements analysis tasks."),
    dict(test=r"technical writing|documentation|confluence|api docs", mapped="Technical documentation", kind="direct", reason="Writing guides and specifications is technical documentation."),
    dict(test=r"statistical (analysis|modell?ing)|hypothesis testing|regression analysis|\bspss\b|\bstata\b|\bsas\b", mapped="Statistics", kind="cross-border",
         reason="Statistical analysis and tools such as SPSS or SAS are listed as statistics in Australian job ads."),
    dict(test=r"data pipelines?|data integration|pentaho|ssis|informatica|datastage|talend", mapped="ETL and ELT pipelines", kind="cross-border",
         reason="Overseas integration tools and data pipelines match the ETL and ELT skills of Australian job ads."),
    dict(test=r"data warehouse|datawarehouse|\bdwh\b|star schema|dimensional model", mapped="Data warehousing", kind="direct", reason="Data warehouse design has the same meaning in Australia."),
    dict(test=r"er diagrams?|schema design|database schema|entity[- ]relationship", mapped="Data modelling", kind="direct", reason="Designing schemas is data modelling."),
    dict(test=r"query optimi[sz]ation|database tuning|performance tuning|indexing", mapped="Database design and tuning", kind="direct", reason="Tuning queries and indexes is database design and tuning."),
    dict(test=r"data protection|privacy compliance|\bgdpr\b|privacy act", mapped="Data privacy and compliance", kind="cross-border",
         reason="Data protection rules overseas (for example GDPR) match the privacy and compliance skills that Australian employers ask for."),
    dict(test=r"pen[- ]?tests?|pentest|vulnerability (assessment|scanning)|ethical hacking", mapped="Penetration testing", kind="direct", reason="Testing systems for weak points is penetration testing."),
    dict(test=r"secure coding|appsec|owasp", mapped="Application security", kind="direct", reason="Secure coding is listed as application security."),
    dict(test=r"ldap|active directory|single sign[- ]on|identity management", mapped="Authentication and authorisation", kind="direct", reason="Identity and access work is listed as authentication and authorisation."),
    dict(test=r"neural networks?|\bcnn\b|\brnn\b|deep nets?", mapped="Deep learning", kind="direct", reason="Neural networks are deep learning."),
    dict(test=r"image (processing|recognition|classification)|opencv|object detection", mapped="Computer vision", kind="direct", reason="Working with images is computer vision."),
    dict(test=r"text mining|sentiment analysis|text classification|chatbots?", mapped="Natural language processing", kind="direct", reason="Working with text is natural language processing."),
    dict(test=r"recommendation (engines?|systems?)|recommender|collaborative filtering", mapped="Recommender systems", kind="direct", reason="Recommendation engines are recommender systems."),
    dict(test=r"model (deployment|serving)|ml pipelines?|machine learning pipelines?", mapped="MLOps", kind="direct", reason="Deploying and running models is MLOps."),
]

for _item in _ROLES:
    _item["re"] = re.compile(_item["test"])
    _item.setdefault("overseas", False)
    _item.setdefault("weak", False)
    _occ = _T.occupation_of_role(_item["mapped"])
    assert _occ is not None, f"The role {_item['mapped']!r} is not in the taxonomy"
    _item["anzsco"], _item["occupation"] = str(_occ["code"]), _occ["title"]
for _item in _SKILLS:
    _item["re"] = re.compile(_item["test"])
    assert _T.skill(_item["mapped"]) is not None, f"The skill {_item['mapped']!r} is not in the taxonomy"

# Indicative AQF levels. Not a formal assessment (PRD: formal credential verification is out of scope).
_AQF = [
    (r"doctor|phd", "AQF Level 10 (Doctoral degree)"),
    (r"master|mba", "AQF Level 9 (Masters degree)"),
    (r"graduate (certificate|diploma)", "AQF Level 8 (Graduate certificate or diploma)"),
    (r"honours", "AQF Level 8 (Bachelor honours degree)"),
    (r"bachelor", "AQF Level 7 (Bachelor degree)"),
    (r"advanced diploma|associate degree", "AQF Level 6"),
    (r"\bdiploma\b", "AQF Level 5 (Diploma)"),
    (r"certificate (iii|iv)", "AQF Level 3–4 (Certificate III or IV)"),
]
_AQF = [(re.compile(p), label) for p, label in _AQF]

# The highest level first, so that the formulas can pick the highest qualification
AQF_RANK = {"AQF Level 10": 10, "AQF Level 9": 9, "AQF Level 8": 8, "AQF Level 7": 7, "AQF Level 6": 6, "AQF Level 5": 5, "AQF Level 3": 3}

# Words that show a level in a title. They are not part of the role.
_LEVEL_WORDS = re.compile(r"\b(intern(ship)?|trainee|junior|jr|jnr|graduate|grad|senior|sr|snr|lead|principal|staff|mid[- ]?level|ii|iii|iv)\b\.?", re.I)
_PLACE_IN_BRACKETS = re.compile(r"\(([^)]*)\)")


def _lower(s: Any) -> str:
    return str(s or "").lower()


def aqf_of(qualification: str) -> str:
    text = _lower(qualification)
    for pattern, label in _AQF:
        if pattern.search(text):
            return label
    return ""


def aqf_level(label: str) -> int:
    for prefix, rank in AQF_RANK.items():
        if str(label).startswith(prefix):
            return rank
    return 0


def _slug(s: Any) -> str:
    """A short id part from letters and digits. A text with no Latin letter (for example Chinese) gets a hash, so that its id is not empty."""
    base = re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", _lower(s)))
    return base or "u" + hashlib.sha1(str(s).encode("utf-8")).hexdigest()[:8]


_EVIDENCE_RANK = {"Limited": 0, "Moderate": 1, "Strong": 2}


def role_base(title: Any) -> str:
    """A job title without the place in brackets, the company and the level words: "Senior Data Engineer, Lakehouse (Vietnam)" gives "data engineer"."""
    text = _PLACE_IN_BRACKETS.sub(" ", _lower(title))
    text = re.split(r"\s[-–—@|]\s|,|\sat\s", text)[0]
    text = _LEVEL_WORDS.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip(" -").rstrip(". ")     # the leading dot of ".NET" stays


def _levels_of(profile: Dict[str, Any]) -> Dict[str, int]:
    """The levels that the profile already has for skills: from `skillLevels` ([{name, level}], the form of a CV result)
    or from a skill that is a dictionary ({name, level}). The key is the lower case name."""
    out: Dict[str, int] = {}
    entries = list(as_list(profile.get("skillLevels"))) + [s for s in as_list(profile.get("skills")) if isinstance(s, dict)]
    for e in entries:
        if not isinstance(e, dict):
            continue
        lvl = e.get("level")
        if isinstance(lvl, bool) or not isinstance(lvl, (int, float)) or int(lvl) != lvl or not 1 <= int(lvl) <= 5:
            continue
        name = str(e.get("name") or "").strip()
        if name:
            out[name.lower()] = int(lvl)
            canon = skills_module.canonical_skill_name(name)
            if canon:
                out[canon.lower()] = int(lvl)
    return out


def _skill_names(profile: Dict[str, Any]) -> List[str]:
    names = []
    for s in as_list(profile.get("skills")):
        text = str(s.get("name") if isinstance(s, dict) else s).strip()
        if text and text not in names:
            names.append(text)
    return names


def translate(profile: Dict[str, Any], evidence: List[str] = None) -> Dict[str, Any]:
    """Return { "skills": [TranslatedSkill], "gaps": [str] } for a draft profile."""
    p = profile or {}
    ev = [str(x) for x in as_list(evidence)]
    from_cv = len(ev) > 0
    overseas = any(c and c != "Australia" for c in as_list(p.get("studyCountry")))
    given_levels = _levels_of(p)
    out: Dict[str, Dict[str, Any]] = {}
    gaps: Dict[str, None] = {}

    def evidence_line(item_re: Optional["re.Pattern[str]"], mapped: str, original: str) -> Optional[str]:
        """The first evidence line that shows this skill or role: by the pattern of the pair, by the taxonomy name, or by the words of the talent."""
        def shows(line: str) -> bool:
            low = _lower(line)
            if item_re is not None and item_re.search(low):
                return True
            if mapped in skills_module.skills_in(line):
                return True
            # a name is a whole word, never a part of another word (the skill "R" is not in "Built dashboards")
            return any(len(w) > 3 and re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", low) for w in (mapped.lower(), _lower(original)))
        return next((l for l in ev if shows(l)), None)

    def add(item: Dict[str, Any], original: str, source: str, item_re: Optional["re.Pattern[str]"] = None) -> None:
        skill_id = f"{_slug(item['mapped'])}--{_slug(original)}"
        if skill_id in out and out[skill_id]["mapped"] != item["mapped"]:
            # "C++" and "C#" give the same letters. A short hash keeps the ids different and stable.
            skill_id += "-" + hashlib.sha1(f"{item['mapped']}|{original}".encode("utf-8")).hexdigest()[:6]
        line = evidence_line(item_re, item["mapped"], original)
        level = "Strong" if line else ("Moderate" if source == "skill" else ("Moderate" if from_cv else "Limited"))
        skill_level: Optional[int] = None
        if source == "skill":
            skill_level = given_levels.get(item["mapped"].lower()) or given_levels.get(original.lower()) or EVIDENCE_LEVEL[level]
        # One card for each taxonomy name. A second source can make the evidence stronger.
        same = next((s for s in out.values() if s["mapped"] == item["mapped"] and s["source"] == source), None)
        if same:
            if _EVIDENCE_RANK[level] > _EVIDENCE_RANK[same["evidence"]]:
                same["evidence"] = level
                same["evidenceText"] = line or same["evidenceText"]
                if source == "skill" and not given_levels.get(item["mapped"].lower()):
                    same["level"] = EVIDENCE_LEVEL[level]
            if original not in same["original"]:
                same["original"] += f"; {original}"
            return
        out[skill_id] = {
            "id": skill_id, "source": source, "original": original, "mapped": item["mapped"], "kind": item["kind"],
            "anzsco": item.get("anzsco", ""), "occupation": item.get("occupation", ""),
            "reason": item["reason"], "evidence": level, "evidenceText": line or "", "status": "suggested", "level": skill_level, "years": None,
        }
        for g in item.get("gaps", []):
            gaps[g] = None

    # ----- roles: the role list of the taxonomy, an occupation, and the pairs of the library -----
    for role in as_list(p.get("currentRole")):
        text = str(role)
        base = role_base(text)
        if not base:
            continue
        has_place = bool(_PLACE_IN_BRACKETS.search(text))
        found = None
        # 1. a pair for an overseas title ("Software Developer (Vietnam)") 2. a title of the role list 3. the other pairs 4. a general pair
        for item in _ROLES:
            if item["overseas"] and (has_place or overseas) and item["re"].search(base):
                found = {**item, "kind": "cross-border"}
                break
        if found is None:
            exact = _T.role_title(base)
            if exact:
                occ = _T.occupation_of_role(exact)
                found = dict(mapped=exact, kind="direct", anzsco=str(occ["code"]), occupation=occ["title"], reason=f"{exact} has the same meaning in Australia.")
        if found is None:
            for item in _ROLES:
                if not item["overseas"] and not item["weak"] and item["re"].search(base):
                    found = dict(item)
                    break
        if found is None:
            weak = next((i for i in _ROLES if i["weak"] and i["re"].search(base)), None)
            if weak:
                found = {**weak, "kind": "direct"}
        if found is not None:
            add(found, text, "role", found.get("re"))

    # ----- skills: the name or alias of the taxonomy, a pair of the library, or the name as it is -----
    for name in _skill_names(p):
        canon = skills_module.canonical_skill_name(name)
        if canon:
            same_name = canon.lower() == name.lower()
            add(dict(mapped=canon, kind="direct", reason=(f"{canon} has the same name in Australia." if same_name
                                                           else f"Australian job ads list this skill as {canon}.")), name, "skill")
            continue
        hit = next((i for i in _SKILLS if i["re"].search(_lower(name))), None)
        if hit:
            add(hit, name, "skill", hit["re"])
            continue
        shown = skills_module.skills_in(name)
        if len(shown) == 1:
            add(dict(mapped=shown[0], kind="direct", reason=f"Australian job ads list this skill as {shown[0]}."), name, "skill")
        else:
            # A skill with no translation keeps its name, so the talent can still choose to share it
            add({"mapped": name, "kind": "direct", "reason": "Australian employers use the same name for this skill."}, name, "skill",
                re.compile(re.escape(name), re.I))

    # ----- qualifications: indicative AQF level -----
    for q in as_list(p.get("qualification")):
        level = aqf_of(q)
        if not level:
            continue
        skill_id = f"aqf--{_slug(q)}"
        out[skill_id] = {
            "id": skill_id, "source": "qualification", "original": f"{q}{' (overseas)' if overseas else ''}", "mapped": level,
            "kind": "cross-border" if overseas else "direct", "anzsco": "", "occupation": "",
            "reason": ("Qualifications of this type from overseas are usually close to this Australian (AQF) level. This is a guide, not a formal assessment."
                       if overseas else "This is the Australian Qualifications Framework (AQF) level of this qualification."),
            "evidence": "Moderate" if from_cv else "Limited", "evidenceText": "", "status": "suggested", "level": None, "years": None,
        }
    return {"skills": list(out.values()), "gaps": list(gaps.keys())}


def translate_keeping(profile: Dict[str, Any], evidence: List[str] = None) -> Dict[str, Any]:
    """Run the engine again. The decisions (accepted, edited, removed) and the skill levels that the talent set stay."""
    result = translate(profile, evidence)
    before = {s.get("id"): s for s in as_list((profile or {}).get("translation")) if isinstance(s, dict)}
    skills = []
    for s in result["skills"]:
        old = before.get(s["id"])
        if old and old.get("status") in ("suggested", "accepted", "edited", "removed"):
            keep_text = old["status"] == "edited" and old.get("mapped")
            old_level = old.get("level")
            keep_level = s["source"] == "skill" and isinstance(old_level, int) and not isinstance(old_level, bool) and 1 <= old_level <= 5
            old_years = old.get("years")
            keep_years = s["source"] == "skill" and isinstance(old_years, (int, float)) and not isinstance(old_years, bool) and 0 <= old_years <= 40
            s = {**s, "status": old["status"], "mapped": old["mapped"] if keep_text else s["mapped"], "level": old_level if keep_level else s["level"],
                 "years": old_years if keep_years else s.get("years")}
        skills.append(s)
    return {"skills": skills, "gaps": result["gaps"]}
