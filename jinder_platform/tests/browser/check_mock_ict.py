"""Browser check of the MOCK backend (?mock=1) after the ICT conversion (decision D2: only Software Engineering, AI & Machine Learning and Data).

Usage:
  python tests/browser/check_mock_ict.py                      start the platform on port 8170 (temp data folder), run, stop it
  python tests/browser/check_mock_ict.py --app-dir <folder>   serve another copy of the app folder (to try a change before it is installed)
Options: --shots <folder> (screenshots), --debug-port 9370 (Chrome remote debugging port), --port 8170

It needs Chrome or Edge (see cdp.py). The mock runs inside the page, so the check imports the real files of js/api/mock in the page,
and then drives the real screens: a new talent signs up and goes through the onboarding with a mock CV sample, sees the recommended jobs, a job
detail, a bookmark and an application; the demo talent and the demo employer (Bluebushworks) are signed in; the employer posts a job and sees talent.
The check also tests the words of the screens: no word of an old field of work (the same list as tests/test_mock_ict.py).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.abspath(os.path.join(HERE, "..", ".."))
results = []
SHOTS_DIR = [""]
LONG = 40

# Words of the old fields of work (AI_Rule Rule 2). "data warehouse" is an ICT term, so it is allowed.
OLD_WORDS = re.compile(r"nurse|nursing|ahpra|accountant|accounting|\bcpa\b|hospitality|logistics|(?<!data )warehouse|\bcivil\b|\bchef\b|marketing|supply chain|patient|procurement|retail|construction|operations & administration|harbour", re.I)


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def info(text):
    print("INFO " + text)


# ---------------------------------------------------------------- the platform
class Platform:
    """Starts `python start.py --demo --reset-db` on a port, with its own data folder (and another app folder if asked)."""

    def __init__(self, port, app_dir=""):
        self.port = port
        self.var = tempfile.mkdtemp(prefix="jinder-mock-ict-")
        self.log = os.path.join(self.var, "server.log")
        env = dict(os.environ, JINDER_VAR_DIR=self.var)
        if app_dir:
            env["JINDER_APP_DIR"] = app_dir
        self.out = open(self.log, "w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, "start.py", "--demo", "--reset-db", "--port", str(port)], cwd=PLATFORM, env=env,
                                     stdout=self.out, stderr=subprocess.STDOUT)
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2).read()
                break
            except OSError:
                if self.proc.poll() is not None:
                    raise RuntimeError("The platform stopped at start:\n" + open(self.log, encoding="utf-8").read()[-3000:])
                time.sleep(0.5)
        else:
            raise RuntimeError("The platform did not start")
        self.base = f"http://localhost:{port}"

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.out.close()


def stop_browser(b):
    """Close the browser and every process of it (Browser.close only ends the first process; the others keep the debugging port)."""
    try:
        b.close()
    except Exception:  # noqa: BLE001
        pass
    subprocess.run(["taskkill", "/PID", str(b.proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- browser helpers
def js(b, expression):
    return b.eval(expression, await_promise=False)


def shot(b, name, full=False):
    if SHOTS_DIR[0]:
        b.screenshot(os.path.join(SHOTS_DIR[0], name), full=full)


def no_problems(b, name):
    """No console error, exception or CSP report since the last call. Errors of a browser extension (chrome-extension://) are not from the app."""
    problems = [p for p in b.take_problems() if "chrome-extension://" not in p]
    check(name, not problems, "; ".join(problems)[:600])


def go(b, hash_, wait="document.querySelector('.dash h1, main h1')"):
    """Open a route and wait for the page. The router draws the page again even when the hash is the same."""
    b.eval(f"window.__stale = document.querySelector('.dash'); location.hash = {json.dumps(hash_)}", False)
    b.wait_for(f"location.hash === {json.dumps(hash_)}", LONG)
    b.wait_for(wait, LONG)
    b.pump(0.5)


def fresh_start(b, base):
    """Open the mock with empty browser storage."""
    b.goto(f"{base}/?mock=1#/login")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{base}/?mock=1#/login")
    b.wait_for("document.querySelector('#email')", LONG)


def sign_in(b, base, email, password):
    fresh_start(b, base)
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", LONG)
    b.wait_for("document.querySelector('#shellUser')", LONG)
    b.pump(0.8)


def to_login(b):
    """Sign out and open the sign-in page in the same storage (the mock database stays)."""
    b.eval("(async () => { const { api } = await import('/js/api/index.js'); await api.auth.logout(); })()")
    b.eval("location.hash = '#/login'", False)
    b.wait_for("location.hash.startsWith('#/login') && document.querySelector('#email')", LONG)
    b.pump(0.3)


def sign_in_here(b, email, password):
    """Sign in again in the same storage (the mock database stays: the new talent and the posted jobs are still there)."""
    to_login(b)
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", LONG)
    b.wait_for("document.querySelector('#shellUser')", LONG)
    b.pump(0.8)


def page_words(b, name):
    """The words on the screen must not be words of an old field of work."""
    text = b.text("body")
    hit = OLD_WORDS.search(text)
    check(f"{name}: no word of an old field of work on the screen", not hit, hit.group(0) if hit else "")


def ob_title(b):
    return b.eval("(document.querySelector('#ob-title') || {}).textContent || ''", False)


def ob_wait(b, title, timeout=LONG):
    b.wait_for(f"document.querySelector('#ob-title') && document.querySelector('#ob-title').textContent === {json.dumps(title)}", timeout)
    b.pump(0.3)


def ob_continue(b):
    b.eval("document.querySelector('#obFoot [type=submit]').click()", False)
    b.pump(0.5)


def fill_form_field(b, name, value):
    js(b, f"""(() => {{ const f = document.querySelector('form.job-form'); const el = f.elements[{json.dumps(name)}]; el.focus();
      const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, {json.dumps(value)});
      el.dispatchEvent(new Event('input', {{bubbles: true}})); el.dispatchEvent(new Event('change', {{bubbles: true}})); }})()""")


# ---------------------------------------------------------------- 1. the files and the data (in the page)
DATA_SCRIPT = r"""
const R = await import('/js/data/reference.js');
const S = await import('/js/api/mock/seed-jobs.js');
const J = await import('/js/api/mock/jobs.js');
const T = await import('/js/api/mock/translation.js');
const C = await import('/js/api/mock/cv-samples.js');
const D = await import('/js/api/mock/jd-samples.js');
const names = new Set(R.SKILL_NAMES);
const certs = new Set(R.CERTIFICATIONS.map((c) => c.name));
const kinds = new Set(R.AWARD_KINDS.map((a) => a.kind));
const jobs = S.SEED_JOBS;
const out = {};
out.count = jobs.length;
out.domains = Object.fromEntries(R.DOMAINS.map((d) => [d, jobs.filter((j) => j.domain === d).length]));
out.otherDomain = jobs.filter((j) => !R.DOMAINS.includes(j.domain)).map((j) => j.key);
out.levels = [...new Set(jobs.map((j) => j.level))];
out.badLevel = jobs.filter((j) => !R.LEVELS.includes(j.level)).map((j) => j.key);
out.badCity = jobs.filter((j) => !R.CITIES.includes(j.city)).map((j) => j.key);
out.badType = jobs.filter((j) => !R.WORK_TYPES.includes(j.type)).map((j) => j.key);
out.badMode = jobs.filter((j) => !R.WORK_MODES.includes(j.workMode)).map((j) => j.key);
out.badSkills = [...new Set(jobs.flatMap((j) => j.skills.map((s) => s.name)).filter((n) => !names.has(n)))];
out.badSkillLevels = jobs.flatMap((j) => j.skills.filter((s) => !(Number.isInteger(s.level) && s.level >= 1 && s.level <= 5) || typeof s.must !== 'boolean').map((s) => j.key + ':' + s.name));
out.badCerts = [...new Set(jobs.flatMap((j) => [...j.certifications.required, ...j.certifications.preferred]).filter((n) => !certs.has(n)))];
out.badAwards = [...new Set(jobs.flatMap((j) => j.awards.preferred).filter((k) => !kinds.has(k)))];
out.withCerts = jobs.filter((j) => j.certifications.required.length || j.certifications.preferred.length).length;
out.withAwards = jobs.filter((j) => j.awards.preferred.length).length;
out.descriptions = jobs.map((j) => ({ key: j.key, len: j.description.length, heads: (j.description.match(/^## /gm) || []).length, bullets: (j.description.match(/^- /gm) || []).length,
  first: j.description.split('\n')[0], cut: /…|\.\.\.\s*$/.test(j.description.trim()) }));
out.dups = jobs.length - new Set(jobs.map((j) => j.key)).size;
const cat = J.catalogue({ postedJobs: [] });
out.catalogue = { n: cat.length, open: cat.filter(J.isOpen).length, ids: cat.every((j) => /^job-[a-z0-9-]+$/.test(j.id)), cats: [...new Set(cat.map((j) => j.category))],
  summaryMax: Math.max(...cat.map((j) => j.summary.length)), summaryOk: cat.every((j) => j.summary && !j.summary.includes('##')),
  descKept: cat.every((j) => j.description === jobs.find((s) => 'job-' + s.key === j.id).description), url: cat.some((j) => /https?:/.test(JSON.stringify(j))) };
const pageSource = await (await fetch('/js/api/mock/jobs.js')).text();
out.noCsv = !/australian_jobs|fetch\(|\.csv/.test(pageSource);
// word-safe skills
const sk = (t) => J.skillsIn(t);
out.words = {
  langs: sk('We use Python, R and SQL with Node.js and C# on .NET, plus CI/CD and C++.'),
  inside: sk('Built with javascript and mysql; also the Java Virtual Machine'),
  caps: sk('Swift and Rust and Ruby and Spark, but swift or rust or spark in small letters'),
  noCandR: sk('Experience in R&D and a go-getter attitude; see page C of the plan'),
  list: sk('Skills: C, R, Go'),
  alias: [J.canonicalSkillName('golang'), J.canonicalSkillName('Excel'), J.canonicalSkillName('csharp'), J.canonicalSkillName('k8s'), J.canonicalSkillName('Registered nurse')],
};
// translation
const tr = (p, ev) => T.translate(p, ev || []);
const roleOf = (title, country) => tr({ currentRole: [title], studyCountry: country ? [country] : [] }).skills.filter((s) => s.source === 'role');
out.roles = {
  nurse: roleOf('Registered Nurse').length, accountant: roleOf('Accountant').length, chef: roleOf('Chef').length, marketing: roleOf('Marketing Manager').length,
  teacher: roleOf('Teacher').length, civil: roleOf('Civil Engineer').length,
  bi: roleOf('BI Specialist', 'Vietnam').map((s) => [s.mapped, s.kind, s.anzsco, s.occupation]),
  two: tr({ currentRole: ['BI Specialist', 'MIS Executive'], studyCountry: ['Vietnam'] }).skills.filter((s) => s.source === 'role').map((s) => [s.mapped, s.original]),
  sde: roleOf('SDE II', 'India').map((s) => [s.mapped, s.kind]),
  dotnet: roleOf('Senior .NET Developer').map((s) => [s.mapped, s.kind, s.anzsco]),
  quant: roleOf('Quantitative Analyst').map((s) => [s.mapped, s.kind]),
  data: roleOf('Senior Data Engineer, Lakehouse (Vietnam)').map((s) => [s.mapped, s.kind, s.anzsco, s.occupation]),
};
const one = (n, ev) => tr({ skills: [n] }, ev).skills.filter((s) => s.source === 'skill').map((s) => [s.original, s.mapped, s.kind, s.level, s.evidence])[0];
out.skills = ['spreadsheets', 'Informatica', 'ER diagrams', 'dashboards', 'Qlik', 'C#', 'C++', 'Hyper-V', 'k8s'].map((n) => one(n, ['Designed the ER diagrams for the data warehouse.']));
out.levels2 = tr({ skills: [{ name: 'SQL', level: 5, years: 6 }, 'Python'] }, ['Wrote Python scripts every day.']).skills.filter((s) => s.source === 'skill').map((s) => [s.mapped, s.level, s.years, s.evidence]);
out.aqf = tr({ qualification: ["Bachelor's degree", "Master's degree"], studyCountry: ['Vietnam'] }).skills.filter((s) => s.source === 'qualification').map((s) => [s.mapped, s.kind]);
const byId = tr({ skills: ['C#', 'C++'] }).skills.map((s) => s.id);
out.sameIds = byId.length === new Set(byId).size;
// the CV samples
out.cv = Object.entries(C.CV_SAMPLES).map(([key, s]) => {
  const r = C.parseResultOf(s);
  const f = r.fields;
  const typed = (f.skills || []).map((n) => ({ name: n, level: (r.skills.find((x) => x.name === n) || {}).level }));
  const cards = tr({ ...f, skills: typed }, r.evidence).skills;
  return { key, label: s.label, domain: r.domain, domainOk: R.DOMAINS.includes(r.domain), industry: f.industry, level: f.level, levelOk: !f.level || R.LEVELS.includes(f.level),
    role: (f.currentRole || [])[0], target: f.targetRole || null, targetOk: !f.targetRole || f.targetRole.every((t) => R.ROLES.includes(t)),
    years: f.yearsExperience ?? null, certs: (f.certifications || []).length, certsOk: (f.certifications || []).every((c) => certs.has(c.name)),
    awards: (f.awards || []).length, awardsOk: (f.awards || []).every((a) => kinds.has(a.kind)), found: r.found, missing: r.missing,
    roleCards: cards.filter((c) => c.source === 'role').length, skillCards: cards.filter((c) => c.source === 'skill').length,
    strong: cards.filter((c) => c.evidence === 'Strong').length, unknown: cards.filter((c) => c.source === 'skill' && !names.has(c.mapped)).map((c) => c.mapped),
    levels: r.skills.every((x) => Number.isInteger(x.level) && x.level >= 1 && x.level <= 5) };
});
out.fileRules = Object.fromEntries(['cv.pdf', 'dev-software.pdf', 'ml-engineer.docx', 'business-analyst.pdf', 'sysadmin-cloud.pdf', 'data-analyst.pdf', 'fail.pdf'].map((f) => [f, (C.sampleFor(f) || {}).label || null]));
// the JD samples
out.jd = Object.entries(D.JD_SAMPLES).map(([key, s]) => ({ key, category: s.fields.category, categoryOk: R.DOMAINS.includes(s.fields.category), location: s.fields.location || null,
  locationOk: !s.fields.location || R.CITIES.includes(s.fields.location), type: s.fields.type, typeOk: R.WORK_TYPES.includes(s.fields.type), heads: (s.fields.description.match(/^## /gm) || []).length,
  skills: J.suggestSkills(s.fields.title + ' ' + s.fields.description).length, missing: s.missing }));
out.jdFiles = Object.fromEntries(['x.pdf', 'machine-learning.pdf', 'devops.docx', 'data-analyst.pdf', 'fail.pdf'].map((f) => [f, (D.jdSampleFor(f) || {}).label || null]));
return out;
"""


def check_data(b):
    r = b.eval("(async () => {" + DATA_SCRIPT + "})()")
    check("data: the embedded catalogue has 24 jobs, each key is used once", r["count"] == 24 and r["dups"] == 0, str(r["count"]))
    check("data: every job is in one of the 3 domains (no other category), and each domain has jobs", not r["otherDomain"] and all(v >= 5 for v in r["domains"].values()), str(r["domains"]))
    check("data: levels, cities, work types and work modes are the values of the pick-lists, and 5 or more levels are used",
          not (r["badLevel"] or r["badCity"] or r["badType"] or r["badMode"]) and len(r["levels"]) >= 5, str({k: r[k] for k in ("badLevel", "badCity", "badType", "badMode", "levels")}))
    check("data: every job skill is a taxonomy skill name with a level 1 to 5 and a must flag", not r["badSkills"] and not r["badSkillLevels"], str(r["badSkills"][:5]) + str(r["badSkillLevels"][:5]))
    check("data: certifications and awards of the jobs are names of the pick-lists, and some jobs have them", not r["badCerts"] and not r["badAwards"] and r["withCerts"] >= 5 and r["withAwards"] >= 3,
          f"{r['badCerts']} {r['badAwards']} {r['withCerts']} {r['withAwards']}")
    bad = [d["key"] for d in r["descriptions"] if not (1200 <= d["len"] <= 3600 and d["heads"] >= 6 and d["bullets"] >= 8 and d["first"] == "## About the role" and not d["cut"])]
    check("data: every description is full (1,200 to 3,600 characters, 6 or more headings, bullets, not cut)", not bad, str(bad))
    c = r["catalogue"]
    check("data: the catalogue has 24 open jobs with internal ids, a short summary (200 characters or less), the full description and no link",
          c["n"] == 24 and c["open"] == 24 and c["ids"] and c["summaryMax"] <= 200 and c["summaryOk"] and c["descKept"] and not c["url"] and set(c["cats"]) <= {"Software Engineering", "AI & Machine Learning", "Data"}, str(c))
    check("data: jobs.js does not read the old CSV file and does not call fetch()", r["noCsv"])
    w = r["words"]
    check("data: word-safe skills: C#, C++, .NET, Node.js, CI/CD, R, Python, SQL are found in a sentence", {"Python", "R", "SQL", "Node.js", "C#", ".NET", "CI/CD", "C++"} <= set(w["langs"]), str(w["langs"]))
    check("data: a word inside another word is not a skill ('java' in 'java virtual machine' counts, 'javascript' is not 'java')", "JavaScript" in w["inside"] and "MySQL" in w["inside"] and w["inside"].count("Java") <= 1, str(w["inside"]))
    check("data: Swift, Rust, Ruby and Spark count with a capital letter only", set(w["caps"]) == {"Swift", "Rust", "Ruby", "Apache Spark"}, str(w["caps"]))
    check("data: 'R&D', 'go-getter' and 'page C' are not the skills R, Go and C; 'C, R, Go' in a list is", "R" not in w["noCandR"] and "Go" not in w["noCandR"] and "C" not in w["noCandR"] and set(w["list"]) == {"C", "R", "Go"}, f"{w['noCandR']} {w['list']}")
    check("data: aliases give the taxonomy name (golang, Excel, csharp, k8s); a nurse title is not a skill", w["alias"] == ["Go", "Microsoft Excel", "C#", "Kubernetes", ""], str(w["alias"]))
    ro = r["roles"]
    check("data: a title of another field gives no role card (nurse, accountant, chef, marketing, teacher, civil)", all(ro[k] == 0 for k in ("nurse", "accountant", "chef", "marketing", "teacher", "civil")), str(ro))
    check("data: 'BI Specialist' (studied in Vietnam) is a cross-border Data Analyst (ANZSCO 224114) and 'BI Specialist' with 'MIS Executive' make one card",
          ro["bi"] == [["Data Analyst", "cross-border", "224114", "Data Analyst"]] and ro["two"] == [["Data Analyst", "BI Specialist; MIS Executive"]], str(ro["bi"]) + str(ro["two"]))
    check("data: 'SDE II' is a cross-border Software Engineer, '.NET Developer' is direct (261312), 'Quantitative Analyst' is a cross-industry Data Scientist, a title with a place and a level is read",
          ro["sde"] == [["Software Engineer", "cross-border"]] and ro["dotnet"] == [[".NET Developer", "direct", "261312"]] and ro["quant"] == [["Data Scientist", "cross-industry"]]
          and ro["data"] == [["Data Engineer", "direct", "262111", "Data Engineer"]], str(ro))
    sk = {x[0]: x for x in r["skills"]}
    check("data: skill pairs: spreadsheets is Microsoft Excel, ER diagrams is Data modelling, dashboards is Data visualisation, Qlik is a cross-border Data visualisation, Informatica is an ETL skill",
          sk["spreadsheets"][1] == "Microsoft Excel" and sk["ER diagrams"][1] == "Data modelling" and sk["dashboards"][1] == "Data visualisation" and sk["Qlik"][1] == "Data visualisation"
          and sk["Qlik"][2] == "cross-border" and sk["Informatica"][1] == "ETL and ELT pipelines" and sk["k8s"][1] == "Kubernetes", str(r["skills"]))
    check("data: a skill that the taxonomy does not know keeps its name; C# and C++ get different card ids", sk["Hyper-V"][1] == "Hyper-V" and r["sameIds"], str(sk.get("Hyper-V")))
    lv = {x[0]: x for x in r["levels2"]}
    check("data: a skill level and years that the talent gave are kept; without a level the evidence gives it (Strong 4, Moderate 3)", lv["SQL"][1] == 5 and lv["SQL"][2] == 6 and lv["Python"][1] == 4 and lv["Python"][3] == "Strong", str(r["levels2"]))
    check("data: qualifications keep the AQF rules (Bachelor is level 7, Master is level 9, cross-border from overseas)",
          r["aqf"] == [["AQF Level 7 (Bachelor degree)", "cross-border"], ["AQF Level 9 (Masters degree)", "cross-border"]], str(r["aqf"]))
    cv = r["cv"]
    check("data: there are 5 ICT CV samples, each with a domain, a level, a current role, certifications or awards, and levels for the skills",
          len(cv) == 5 and all(x["domainOk"] and x["levelOk"] and x["level"] and x["role"] and x["levels"] and x["targetOk"] and x["certsOk"] and x["awardsOk"] for x in cv), str(cv)[:600])
    check("data: every CV sample gives role cards and skill cards of taxonomy names, most with Strong evidence", all(x["roleCards"] >= 1 and x["skillCards"] >= 6 and not x["unknown"] and x["strong"] >= 3 for x in cv), str([(x["key"], x["roleCards"], x["skillCards"], x["unknown"], x["strong"]) for x in cv]))
    check("data: the CV samples have a desired role, a certification and an award in most cases, and one has none ('found' says so)",
          sum(1 for x in cv if x["found"]["targetRole"]) >= 4 and sum(1 for x in cv if x["found"]["certifications"]) >= 3 and sum(1 for x in cv if x["found"]["awards"]) >= 3
          and any(not x["found"]["targetRole"] for x in cv) and any(x["missing"] for x in cv), str([(x["key"], x["found"], x["missing"]) for x in cv]))
    fr = r["fileRules"]
    check("data: the file name chooses the CV sample (default data analyst; software, machine learning, business analyst, systems administrator; 'fail' fails)",
          fr["cv.pdf"] and fr["cv.pdf"] == fr["data-analyst.pdf"] and len({fr[k] for k in fr if fr[k]}) == 5 and fr["fail.pdf"] is None, str(fr))
    jd = r["jd"]
    check("data: the JD samples are ICT (domain, city and work type are pick-list values, 5 headings, skills are found)", len(jd) >= 4 and all(x["categoryOk"] and x["locationOk"] and x["typeOk"] and x["heads"] >= 5 and x["skills"] >= 4 for x in jd), str(jd))
    check("data: the file name chooses the JD sample, and 'fail' fails", len({v for v in r["jdFiles"].values() if v}) == 4 and r["jdFiles"]["fail.pdf"] is None, str(r["jdFiles"]))


def check_static(base):
    for path in ("/js/api/mock/jobs.js", "/js/api/mock/seed-jobs.js", "/js/api/mock/seed-demo.js", "/js/api/mock/translation.js", "/js/api/mock/cv-samples.js", "/js/api/mock/jd-samples.js"):
        with urllib.request.urlopen(base.replace("localhost", "127.0.0.1") + path, timeout=20) as r:
            ctype = r.headers.get("Content-Type", "")
            text = r.read().decode("utf-8")
        check(f"static: {path} is served as JavaScript and starts with the MOCK BACKEND comment", r.status == 200 and "javascript" in ctype and "MOCK BACKEND" in text.split("\n")[0], ctype)


# ---------------------------------------------------------------- 2. a new talent: sign up, onboarding with a mock CV, jobs, detail, bookmark, apply
def check_new_talent(b, base, shots):
    fresh_start(b, base)
    check("mock: the old storage key is gone and the new one is used (no data of the old non-ICT mock)", b.eval("localStorage.getItem('jinder.mock.db.v1') === null", False))
    email = f"mock.ict.{uuid.uuid4().hex[:6]}@example.com"
    password = "Passw0rd!mock"
    go(b, "#/signup", "document.querySelector('form')")
    b.fill("#name", "Test Person")
    b.fill("#email", email)
    b.fill("#password", password)
    b.fill("#confirm", password)
    js(b, "document.querySelector('input[name=terms]').click()")
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/login')", LONG)
    b.wait_for("document.querySelector('#email')", LONG)
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", LONG)
    b.wait_for("document.querySelector('#onboarding[open]')", LONG)
    check("mock talent: after sign up and sign in the onboarding opens", True)
    cv_dir = tempfile.mkdtemp(prefix="jinder-mock-cv-")
    cv_path = os.path.join(cv_dir, "linh-data-analyst-cv.pdf")
    open(cv_path, "wb").write(b"%PDF-1.4 made-up file for the mock")
    b.set_file("#ob-cv", cv_path)
    b.pump(0.4)
    b.click("#ob-cv-next")
    ob_wait(b, "Your education", 40)
    t = b.text("#obBody")
    check("onboarding (mock): the sample CV is the data analyst; the demo banner names it", "Demo mode" in t and "Data analyst (BI Specialist), Vietnam" in t, t[:300])
    check("onboarding (mock): 'What we found in your CV' lists the current role, desired role, level, years, certifications and awards",
          "What we found in your CV" in t and all(k in t for k in ["Current role:", "Desired role:", "Level:", "Years of experience:", "Certifications:", "Awards:"]), t[:500])
    shot(b, "mock_onb_education.png")
    ob_continue(b)
    ob_wait(b, "Your experience")
    r = b.eval("""({ level: document.querySelector('#ob-level').value, years: document.querySelector('#ob-yearsExperience').value, band: document.querySelector('#ob-years').value,
      roles: [...document.querySelectorAll('[data-field=currentRole] .skill-chip')].map(c => c.textContent.trim()), domains: [...document.querySelectorAll('[data-field=industry] .skill-chip')].map(c => c.textContent.trim()),
      label: [...document.querySelectorAll('#obBody label')].map(l => l.textContent.trim()) })""", False)
    check("onboarding (mock): the experience step has Mid, 4.5 years, the band '3–5 years', the domain Data and the two BI roles; the word is 'Domains'",
          r["level"] == "Mid" and r["years"] == "4.5" and r["band"] == "3–5 years" and r["domains"] == ["Data"] and any("BI Specialist" in x for x in r["roles"]) and "Domains" in r["label"], str(r))
    ob_continue(b)
    ob_wait(b, "Your skills")
    ob_continue(b)
    ob_wait(b, "Certifications and awards")
    r = b.eval("""({ certs: [...document.querySelectorAll('[data-field=certifications] .cred-row input[id$=-name]')].map(i => i.value),
      awards: [...document.querySelectorAll('[data-field=awards] .cred-row input[id$=-name]')].map(i => i.value) })""", False)
    check("onboarding (mock): the certification and the award of the CV are rows (names from the pick-lists)", r["certs"] == ["Microsoft Certified: Power BI Data Analyst Associate"] and r["awards"] == ["Smart City Hackathon Runner-up"], str(r))
    ob_continue(b)
    ob_wait(b, "Your translated profile")
    b.wait_for("document.querySelector('.tr-card')", LONG)
    b.pump(0.4)
    r = b.eval("""({ cards: [...document.querySelectorAll('.tr-card')].map(c => c.innerText.replace(/\\s+/g, ' ').trim()),
      levels: [...document.querySelectorAll('.tr-level-select')].map(s => s.value), fromCv: document.querySelectorAll('.tr-level-from:not([hidden])').length })""", False)
    cards = " | ".join(r["cards"])
    check("onboarding (mock): the translation has a cross-border Data Analyst card, Microsoft Excel (from Spreadsheets), Data visualisation, Data modelling and an AQF card",
          "Data Analyst" in cards and "Cross-border" in cards and "Microsoft Excel" in cards and "Data visualisation" in cards and "Data modelling" in cards and "AQF Level 7" in cards, cards[:600])
    check("onboarding (mock): the skill cards have the levels of the CV ('From your CV')", len([x for x in r["levels"] if x]) >= 6 and r["fromCv"] >= 6, str(r["levels"]) + str(r["fromCv"]))
    shot(b, "mock_onb_translation.png")
    b.click_text("button", "Accept all")
    b.pump(0.4)
    ob_continue(b)
    ob_wait(b, "What are you looking for?")
    r = b.eval("({ chips: [...document.querySelectorAll('[data-field=targetRole] .skill-chip')].map(c => c.textContent.trim()), hint: [...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim()) })", False)
    check("onboarding (mock): the desired role of the CV (Data Engineer) is filled and says 'From your CV'", any("Data Engineer" in c for c in r["chips"]) and "From your CV. Check it. Change it if it is wrong." in r["hint"], str(r))
    b.eval("[...document.querySelectorAll('[data-field=locations] .choice')].find(c => c.textContent.trim() === 'Sydney').click(); [...document.querySelectorAll('[data-field=workTypes] .choice')][0].click()", False)
    ob_continue(b)
    ob_wait(b, "Check your answers")
    page_words(b, "onboarding review")
    ob_continue(b)
    b.wait_for("!document.querySelector('#onboarding[open]')", LONG)
    no_problems(b, "onboarding (mock): no console error, no CSP error")
    # Home: recommended jobs
    go(b, "#/home", "document.querySelector('.recs .job-card')")
    b.pump(0.6)
    r = b.eval("""({ cards: document.querySelectorAll('.recs .job-card').length, titles: [...document.querySelectorAll('.recs .job-card .job-title-link')].map(a => a.textContent.trim()),
      chips: [...document.querySelectorAll('.recs .job-facts')].length })""", False)
    check("home (mock): 5 recommended jobs, all data jobs of the ICT catalogue, with the Level, Experience and Work mode chips", r["cards"] == 5 and r["chips"] == 5 and any("Data" in t for t in r["titles"]), str(r))
    t = b.text("[data-shared]")
    check("home (mock): 'What employers see' shows the level and the exact years that the talent gave (Mid, 4.5 years) and the skill levels",
          "Level: Mid" in t and "4.5 years" in t and re.search(r"SQL\s+·\s+(Beginner|Working|Proficient|Advanced|Expert)", t), t[:300])
    shot(b, "mock_home.png")
    page_words(b, "home")
    # Jobs: pager over the whole catalogue
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card')")
    b.pump(0.6)
    rng = b.eval("(document.querySelector('.pager-range') || {}).textContent || ''", False)
    total = int(re.search(r"of (\d+)", rng).group(1)) if re.search(r"of (\d+)", rng) else -1
    check("jobs (mock): the list holds the 24 catalogue jobs and the 3 open demo jobs (27), in pages of 10", rng.startswith("Showing 1–10 of") and total == 27, rng)
    page_words(b, "jobs list")
    # Job detail
    href = js(b, "document.querySelector('[data-list] .job-card .job-title-link').getAttribute('href')")
    go(b, href, "document.querySelector('.jd-view')")
    b.pump(0.6)
    r = b.eval("""({ heads: [...document.querySelectorAll('.jd-view h3')].map(h => h.textContent.trim()), bullets: document.querySelectorAll('.jd-view li').length,
      text: document.querySelector('.jd-view').innerText, tab: document.querySelector('.jd-view').getAttribute('tabindex'), facts: [...document.querySelectorAll('.fact-grid dt')].map(d => d.textContent),
      skills: document.querySelectorAll('.skill-match li, .skill-table tbody tr').length, h1: document.querySelector('h1').textContent })""", False)
    check("job detail (mock): the full description is in the scroll box with its headings and bullets, and is not cut", len(r["heads"]) >= 6 and r["heads"][0] == "About the role" and r["bullets"] >= 8 and not r["text"].rstrip().endswith("…") and r["tab"] == "0", str(r["heads"]))
    check("job detail (mock): the facts show Level, Experience and Work mode, and the skills list is there", all(k in r["facts"] for k in ("Level", "Experience", "Work mode")) and r["skills"] >= 5, str(r["facts"]) + str(r["skills"]))
    shot(b, "mock_detail.png", full=True)
    page_words(b, "job detail")
    job_id = href.split("/")[-1]
    # Bookmark
    js(b, "document.querySelector('.dash [data-bookmark]').click()")
    b.wait_for("document.querySelector('.dash [data-bookmark]').getAttribute('aria-pressed') === 'true'", LONG)
    go(b, "#/bookmarks", "document.querySelector('[data-list] .job-card') || document.querySelector('[data-list] .empty')")
    b.pump(0.5)
    check("bookmarks (mock): the saved job is in the list", js(b, f"!!document.querySelector('[data-bookmark={json.dumps(job_id)}]') || !!document.querySelector('[data-list] a[href$={json.dumps(job_id)}]')"), job_id)
    # Apply
    go(b, f"#/jobs/{job_id}/apply", "document.querySelector('[data-apply]')")
    b.pump(0.5)
    t = b.text("body")
    check("apply (mock): 'What the employer sees' has the alias and ICT skills, and the skills for this job are listed", "What the employer sees" in t and "Your skills for this job" in t, t[:200])
    js(b, "document.querySelector('[data-apply] [type=submit]').click()")
    b.wait_for("location.hash.startsWith('#/applications/')", LONG)
    b.pump(0.6)
    go(b, "#/applications", "document.querySelector('[data-list] .app-row') || document.querySelector('[data-list] .empty')")
    check("applications (mock): the new application is listed", js(b, "document.querySelectorAll('[data-list] .app-row').length") >= 1)
    page_words(b, "applications")
    no_problems(b, "new talent (mock): jobs, detail, bookmark and application without a console error")
    # the new talent is in the talent list that employers see (alias and skills only)
    return email, password


# ---------------------------------------------------------------- 3. the demo talent
def check_demo_talent(b, base, shots):
    sign_in_here(b, "candidate@demo.jinder.app", "demo1234")
    b.wait_for("document.querySelector('.recs .job-card')", LONG)
    b.pump(0.6)
    r = b.eval("""(async () => { const { api } = await import('/js/api/index.js');
      const me = await api.me.get(); const rec = await api.jobs.recommended({ pageSize: 50, sort: 'best' }); const apps = await api.applications.list(); const n = await api.notifications.list();
      return { alias: me.alias, name: me.name, level: me.profile.level, years: me.profile.yearsExperience, role: me.profile.currentRole, target: me.profile.targetRole, domain: me.profile.industry,
        skills: me.profile.translation.filter((s) => s.source === 'skill').map((s) => [s.mapped, s.level]), certs: me.profile.certifications.map((c) => c.name), awards: me.profile.awards.map((a) => a.name),
        roleCard: me.profile.translation.filter((s) => s.source === 'role').map((s) => [s.mapped, s.kind, s.anzsco]),
        rec: rec.items.map((j) => [j.title, j.match.coverage]), apps: apps.items.map((a) => [a.job.title, a.status]), notes: n.items.map((x) => x.title) }; })()""")
    check("demo talent: Teal Heron (Linh Nguyen), Mid, 4.5 years, a data analyst who wants to be a Data Engineer, 8 skills with levels, one certification and one award",
          r["alias"] == "Teal Heron" and r["name"] == "Linh Nguyen" and r["level"] == "Mid" and r["years"] == 4.5 and r["target"] == ["Data Engineer"] and r["domain"] == ["Data"] and len(r["skills"]) == 8
          and all(s[1] for s in r["skills"]) and r["certs"] == ["Microsoft Certified: Power BI Data Analyst Associate"] and r["awards"] == ["Smart City Hackathon Runner-up"], str(r)[:500])
    check("demo talent: her overseas titles are one cross-border Data Analyst card (ANZSCO 224114)", r["roleCard"] == [["Data Analyst", "cross-border", "224114"]], str(r["roleCard"]))
    check("demo talent: 5 or more jobs are recommended, and the best are data engineering and data analyst jobs", len(r["rec"]) >= 5 and any("Data Engineer" in t for t, _ in r["rec"][:3]), str(r["rec"][:5]))
    check("demo talent: she is in interview for the Data Engineer job of Bluebushworks and has the alert with the interview times",
          r["apps"] == [["Data Engineer, Solar Analytics", "interview"]] and r["notes"] == ["Interview times for Data Engineer, Solar Analytics"], str(r["apps"]) + str(r["notes"]))
    page_words(b, "demo talent home")
    shot(b, "mock_demo_talent_home.png")
    go(b, "#/applications", "document.querySelector('[data-list] .app-row')")
    t = b.text("[data-list]")
    check("demo talent: the Applications list shows the interview", "Data Engineer, Solar Analytics" in t and "Interview" in t, t[:200])
    no_problems(b, "demo talent (mock): no console error, no CSP error")


# ---------------------------------------------------------------- 4. the demo employer
def check_employer(b, base, new_talent, shots):
    to_login(b)
    body = b.text("body")
    check("sign in (mock): the demo account labels name Teal Heron and Bluebushworks, and not Harbour Logistics", "Teal Heron" in body and "Bluebushworks" in body and "Harbour" not in body, body[-300:])
    b.fill("#email", "recruiter@demo.jinder.app")
    b.fill("#password", "demo1234")
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", LONG)
    b.wait_for("document.querySelector('#shellUser')", LONG)
    b.pump(0.8)
    t = b.text("#shellUser")
    check("demo employer: Alex Morgan of Bluebushworks", "Alex Morgan" in t, t)
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    rows = b.eval("[...document.querySelectorAll('.app-row')].map(r => r.querySelector('h3 a').textContent.trim() + ' | ' + r.innerText.replace(/\\s+/g, ' ').slice(0, 160))", False)
    titles = [x.split(" | ")[0] for x in rows]
    check("my jobs (mock): the 4 jobs of Bluebushworks (Data Engineer, Backend, Machine Learning, Contract Data Engineer), one closing soon and one closed",
          sorted(titles) == sorted(["Data Engineer, Solar Analytics", "Senior Backend Engineer, Installer Platform", "Machine Learning Engineer, Solar Forecasting", "Contract Data Engineer, Billing Migration"])
          and js(b, "document.querySelectorAll('.app-row .chip-rose').length") == 1, str(rows))
    page_words(b, "my jobs")
    shot(b, "mock_my_jobs.png")
    # the overview of a demo job shows the full JD
    href = js(b, "[...document.querySelectorAll('.app-row h3 a')].find(a => a.textContent.startsWith('Data Engineer, Solar')).getAttribute('href')")
    go(b, href, "document.querySelector('.job-overview .jd-view')")
    h = b.eval("[...document.querySelectorAll('.jd-view h3')].map(h => h.textContent.trim())", False)
    check("job overview (mock): the full JD of the demo job has its headings (About the role to How we hire)", len(h) >= 8 and h[0] == "About the role" and h[-1] == "How we hire", str(h))
    page_words(b, "job overview")
    # post a job from a file: the sample is an ICT job, its domain is in the list
    go(b, "#/my-jobs/new", "document.querySelector('form.job-form')")
    pdf = os.path.join(tempfile.mkdtemp(prefix="jinder-mock-jd-"), "devops-platform-engineer.pdf")
    open(pdf, "wb").write(b"%PDF-1.4 made-up file for the mock")
    b.set_file("#jf-file", pdf)
    b.wait_for("!document.querySelector('[data-read]').disabled")
    js(b, "document.querySelector('[data-read]').click()")
    b.wait_for("document.querySelector('[data-import-status] .form-alert.success')", 20)
    r = b.eval("""({ title: document.querySelector('#jf-title').value, category: document.querySelector('#jf-category').value, location: document.querySelector('#jf-location').value,
      type: document.querySelector('#jf-type').value, skills: [...document.querySelectorAll('[data-skills] .chip')].map(c => c.textContent.replace('Remove', '').trim()), desc: document.querySelector('#jf-desc').value,
      domainMarker: document.querySelector('label[for=jf-category] .field-markers')?.textContent.trim() || '', banner: !!document.querySelector('.demo-banner') })""", False)
    check("post a job (mock): the file sample fills an ICT DevOps job (domain Software Engineering, Remote), skills of the taxonomy and the JD with its headings",
          "DevOps" in r["title"] and r["category"] == "Software Engineering" and r["location"] == "Remote" and len(r["skills"]) >= 5 and r["desc"].startswith("## About the role") and r["domainMarker"] != "Missing" and r["banner"], str(r)[:500])
    shot(b, "mock_import.png", full=True)
    # a failing file shows the error
    bad = os.path.join(tempfile.mkdtemp(prefix="jinder-mock-jd-"), "fail.pdf")
    open(bad, "wb").write(b"%PDF-1.4 made-up file for the mock")
    b.set_file("#jf-file", bad)
    b.wait_for("!document.querySelector('[data-read]').disabled")
    js(b, "document.querySelector('[data-read]').click()")
    b.wait_for("document.querySelector('[data-import-status] .form-alert.error, [data-import-status] .form-alert[class*=error], [data-import-status] [role=alert]')", 20)
    check("post a job (mock): a file that fails shows an error message", True)
    # post the job
    title = f"Mock ICT check job {uuid.uuid4().hex[:5]}"
    closes = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 21 * 86400))
    fill_form_field(b, "title", title)
    fill_form_field(b, "category", "Data")
    fill_form_field(b, "location", "Perth")
    fill_form_field(b, "type", "Full-time")
    fill_form_field(b, "closesAt", closes)
    fill_form_field(b, "description", "## About the role\n- A made-up job to check the mock backend with ICT data.\n\n## Tech stack\n- SQL, Python and Power BI")
    js(b, "[...document.querySelectorAll('[data-skills] [data-remove]')].forEach((x) => x.click())")
    for name in ("SQL", "Python", "Power BI"):
        b.fill("#jf-skill", name)
        js(b, "document.querySelector('[data-add]').click()")
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.wait_for("location.hash.includes('/overview')", LONG)
    b.wait_for("document.querySelector('.job-overview .jd-view')", LONG)
    check("post a job (mock): the job is posted and the overview shows it", js(b, "document.querySelector('h1').textContent") == title and "Tech stack" in js(b, "document.querySelector('.jd-view').innerText"))
    page_words(b, "posted job overview")
    # talent: the Basic list shows 5 cards; after the plan switch to Premium all talent are there (11 + the new one)
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    b.pump(0.5)
    r = b.eval("""({ cards: document.querySelectorAll('.cand-card').length, text: document.querySelector('main').innerText, aliases: [...document.querySelectorAll('.cand-card h3 a')].map(a => a.textContent.trim()),
      locks: document.querySelectorAll('.cand-card [data-premium-lock]').length })""", False)
    check("talent (mock): the Basic employer sees 5 anonymous cards (alias, roles, skills) and locks on Premium actions", r["cards"] == 5 and r["locks"] >= 5 and "Linh" not in r["text"] and "Nguyen" not in r["text"], str(r["aliases"]))
    page_words(b, "talent list")
    shot(b, "mock_talent_list.png", full=True)
    r = b.eval("""(async () => { const { api } = await import('/js/api/index.js');
      const first = await api.recruiter.candidates.list({ pageSize: 50, sort: 'best' });
      const detail = await api.recruiter.candidates.get(first.items[0].id, first.job.id);
      const text = JSON.stringify([first, detail]).toLowerCase();
      await api.entitlements.set('premium');
      const all = await api.recruiter.candidates.list({ pageSize: 50, sort: 'best' });
      await api.entitlements.set('basic');
      return { limited: first.limitedTo, n: first.items.length, total: first.total, job: first.job.title, premiumN: all.items.length, aliases: all.items.map((c) => c.alias),
        privateKeys: ['name', 'email', 'cv', 'evidence', 'studyCountry'].filter((k) => k in detail || first.items.some((c) => k in c)),
        leak: ['linh', 'nguyen', 'candidate@demo', 'vietnam', 'sample.jinder.app', '@'].filter((w) => text.includes(w)), roles: detail.roles, skills: detail.skills.slice(0, 5) }; })()""")
    check("talent (mock): Basic gets the top 5 of 12 for the first open job; Premium gets all talent (10 samples, Teal Heron and the new talent)", r["limited"] == 5 and r["n"] == 5 and r["total"] == 12 and r["premiumN"] == 12 and "Teal Heron" in r["aliases"] and "Plum Heron" in r["aliases"], str(r))
    check("talent (mock): an employer response has no name, email, country, CV or evidence", not r["privateKeys"] and not r["leak"], str(r["privateKeys"]) + str(r["leak"]))
    # the posted job is in the talent catalogue
    sign_in_here(b, new_talent[0], new_talent[1])
    r = b.eval(f"""(async () => {{ const {{ api }} = await import('/js/api/index.js'); const s = await api.jobs.search({{ q: {json.dumps(title)} }}); return {{ total: s.total, cat: s.items[0] && s.items[0].category, company: s.items[0] && s.items[0].company }}; }})()""")
    check("post a job (mock): the posted job is found by a talent (domain Data, company Bluebushworks)", r["total"] == 1 and r["cat"] == "Data" and r["company"] == "Bluebushworks", str(r))
    no_problems(b, "employer (mock): no console error, no CSP error")


def check_no_csv(b):
    names = b.eval("performance.getEntriesByType('resource').map(r => r.name)", False)
    check("network (mock): no request for a CSV file or for a data file of the old catalogue", not [n for n in names if ".csv" in n or "australian_" in n], str([n for n in names if ".csv" in n or "australian_" in n]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="")
    ap.add_argument("--debug-port", type=int, default=9370)
    ap.add_argument("--port", type=int, default=8170)
    ap.add_argument("--app-dir", default="")
    ap.add_argument("--base", default="", help="use a platform that runs already (for example http://localhost:8170)")
    args = ap.parse_args()
    SHOTS_DIR[0] = args.shots
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)
    platform = None
    if args.base:
        base = args.base.rstrip("/")
    else:
        platform = Platform(args.port, args.app_dir)
        base = platform.base
        info(f"started the platform on {base} (data folder {platform.var})")
    b = None
    try:
        check_static(base)
        b = Browser(port=args.debug_port)
        fresh_start(b, base)
        check_data(b)
        no_problems(b, "data checks: no console error, no CSP error")
        new_talent = check_new_talent(b, base, args.shots)
        check_demo_talent(b, base, args.shots)
        check_employer(b, base, new_talent, args.shots)
        check_no_csv(b)
    finally:
        if b:
            stop_browser(b)
        if platform:
            platform.stop()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    for name, _, detail in failed:
        print("  FAIL:", name, detail)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
