"""Browser checks for the FE-Talent work of Jinder V2: talent lists (pager and sort), job card and job detail, the compare basket on the cards,
"Your path to this job", onboarding with the new profile fields, and the shared profile card.

Usage:
  python tests/browser/check_fe_talent.py                      start the platform on port 8130 (temp data folder), run, stop it
  python tests/browser/check_fe_talent.py --base http://localhost:8130 --talent-pw X     use a platform that runs already
Options: --shots <folder> (screenshots), --debug-port 9330 (Chrome remote debugging port), --port 8130, --start-retries 3, --start-wait 180,
         --skip components,lists,detail,onboarding,mock (leave parts out for a quick run)

It needs Chrome or Edge (see cdp.py). It tests against the REAL backend. Where the backend does not send V2 data yet (job level, certifications, awards,
the JD headings, `bridge.path`) the check uses a clearly marked stub ("stub" in the check name): the page gets the real answer of the server with these
keys added, or the real module is called with a fixture (tests/browser/fixtures_path.json). The checks that use a stub say so.
The mock backend (?mock=1) is checked at the end, so that the old screens still work.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.abspath(os.path.join(HERE, "..", ".."))
TAXONOMY = os.path.abspath(os.path.join(PLATFORM, "..", "jinder_backend_engine", "data", "reference", "ict_taxonomy.json"))
CV_DIR = os.path.join(PLATFORM, "tests", "fixtures", "cv")
FIXTURES = os.path.join(HERE, "fixtures_path.json")
results = []
SHOTS_DIR = [""]
LONG_WAIT = 90   # the machine can be busy: the lists take a few seconds


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def info(text):
    print("INFO " + text)


# ---------------------------------------------------------------- the platform
class Platform:
    """Starts `python start.py --demo --reset-db` on a port, with its own data folder, and reads the demo passwords from the output."""

    def __init__(self, port):
        self.port = port
        self.var = tempfile.mkdtemp(prefix="jinder-fe-talent-")
        self.log = os.path.join(self.var, "server.log")
        env = dict(os.environ, JINDER_VAR_DIR=self.var)
        self.out = open(self.log, "w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, "start.py", "--demo", "--reset-db", "--port", str(port)], cwd=PLATFORM, env=env,
                                     stdout=self.out, stderr=subprocess.STDOUT)
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3).read()
                break
            except OSError:
                if self.proc.poll() is not None:
                    self.out.close()
                    raise RuntimeError("The platform stopped at start:\n" + open(self.log, encoding="utf-8").read()[-3000:])
                time.sleep(0.5)
        else:
            self.stop()
            raise RuntimeError("The platform did not start")
        text = open(self.log, encoding="utf-8").read()
        self.pw = dict(re.findall(r"(\S+@demo\.jinder\.app)\s+(\S+)", text))
        self.base = f"http://localhost:{port}"

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.out.close()


def start_platform(port, retries, wait):
    """The backend is edited by other agents at the same time. If it does not start, wait and try again."""
    last = None
    for attempt in range(1, retries + 1):
        try:
            return Platform(port)
        except RuntimeError as exc:
            last = exc
            info(f"the platform did not start (try {attempt} of {retries}): {str(exc)[-400:]}")
            if attempt < retries:
                info(f"waiting {wait} seconds before the next try")
                time.sleep(wait)
    raise last


def stop_browser(b):
    """Close the browser and every process of it (Browser.close only ends the first process; the others keep the debugging port)."""
    try:
        b.close()
    except Exception:  # noqa: BLE001
        pass
    subprocess.run(["taskkill", "/PID", str(b.proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- the API (set-up of data, not a test of the screens)
class Api:
    def __init__(self, base):
        self.base = base.rstrip("/") + "/api"

    def call(self, method, path, body=None, token=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, method=method, data=data,
                                     headers={"Content-Type": ctype, **({"Authorization": "Bearer " + token} if token else {})})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return {"_http": e.code, "_body": json.loads(e.read() or b"null")}

    def login(self, email, password):
        return self.call("POST", "/auth/login", {"email": email, "password": password})["token"]

    def new_talent(self, tag):
        email = f"fe.talent.{tag}.{uuid.uuid4().hex[:6]}@example.com"
        password = "Passw0rd!test"
        self.call("POST", "/auth/signup", {"role": "candidate", "name": "Test Person", "email": email, "password": password})
        return email, password


# ---------------------------------------------------------------- browser helpers
def sign_in(b, base, email, password, mock=False):
    suffix = "?mock=1" if mock else ""
    b.goto(f"{base}/{suffix}#/login")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{base}/{suffix}#/login")
    b.wait_for("document.querySelector('#email')", 30)
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", 40)
    b.wait_for("document.querySelector('#shellUser')", 40)
    b.pump(0.8)


def go(b, hash_, wait=None, timeout=LONG_WAIT):
    """Go to a route and wait until the router has drawn the new page (the old page has no `.dash` of the new page), then for `wait`."""
    same = b.eval("location.hash", False) == hash_
    b.eval(f"window.__stale = document.querySelector('.dash'); location.hash = {json.dumps(hash_)}", False)
    if not same:
        b.wait_for("document.querySelector('.dash') !== window.__stale", 30)
    if wait:
        b.wait_for(wait, timeout)
    b.pump(0.3)


def clear_basket(b):
    b.eval("import('/js/core/compare-store.js').then(m => { m.compareStore.clear('job'); m.compareStore.clear('talent'); return true; })")


def shot(b, name, full=False):
    if SHOTS_DIR[0]:
        b.screenshot(os.path.join(SHOTS_DIR[0], name), full=full)


def set_viewport(b, width, height):
    b.call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
    b.pump(0.4)


def no_problems(b, name, ignore=()):
    """No console error, exception or CSP report since the last call. Errors of a browser extension (chrome-extension://) are not from the app."""
    problems = [p for p in b.take_problems() if "chrome-extension://" not in p and not any(i in p for i in ignore)]
    check(name, not problems, "; ".join(problems)[:600])


def set_select(b, selector, value):
    b.eval(f"(() => {{ const s = document.querySelector({json.dumps(selector)}); s.value = {json.dumps(value)}; s.dispatchEvent(new Event('change', {{bubbles: true}})); }})()", False)


def card_ids(b, scope="[data-list]"):
    return b.eval(f"[...document.querySelectorAll({json.dumps(scope + ' .job-card[data-card]')})].map(c => c.dataset.card)", False)


def range_text(b):
    return b.eval("(document.querySelector('.pager-range') || {}).textContent || ''", False)


def total_of(text):
    m = re.search(r"of (\d+)", text)
    return int(m.group(1)) if m else -1


def announcer(b):
    return b.eval("document.getElementById('announcer').textContent", False)


def set_testbed(b):
    """Put an empty box in the main area of the app (the shell stays), so that a component can be drawn alone."""
    b.eval("""(() => {
      const main = document.querySelector('.app-content');
      [...main.children].forEach(c => c.remove());
      const d = document.createElement('div'); d.id = 'fe-testbed'; d.className = 'dash'; main.append(d);
      window.scrollTo(0, 0);
      return true; })()""", False)


# ---------------------------------------------------------------- 1. the pick-lists
def check_reference(b):
    r = b.eval("""(async () => {
      const R = await import('/js/data/reference.js'); const L = await import('/js/data/levels.js');
      return { keys: Object.keys(R).sort(), domains: R.DOMAINS, spec: R.SPECIALISATIONS, roles: R.ROLES, fields: R.FIELDS_OF_STUDY, cities: R.CITIES, loc: R.LOCATIONS,
        modes: R.WORK_MODES, types: R.WORK_TYPES, quals: R.QUALIFICATIONS, years: R.YEARS, levels: R.LEVELS, certs: R.CERTIFICATIONS, awards: R.AWARD_KINDS,
        ind: R.INDUSTRIES, cat: R.JOB_CATEGORIES, skills: R.SKILLS, sameLevels: R.LEVELS === L.LEVELS, countries: R.COUNTRIES.length, sugg: R.SKILL_SUGGESTIONS };
    })()""")
    need = ["AWARD_KINDS", "CERTIFICATIONS", "CITIES", "COUNTRIES", "DOMAINS", "FIELDS_OF_STUDY", "INDUSTRIES", "JOB_CATEGORIES", "LEVELS", "LOCATIONS", "QUALIFICATIONS", "ROLES",
            "SPECIALISATIONS", "WORK_MODES", "WORK_TYPES", "YEARS"]
    check("reference.js: exports every list that the plan names (and the old names)", all(k in r["keys"] for k in need), str([k for k in need if k not in r["keys"]]))
    check("reference.js: INDUSTRIES and JOB_CATEGORIES are the 3 domains (old imports work)", r["ind"] == r["domains"] == r["cat"] and len(r["domains"]) == 3)
    check("reference.js: LOCATIONS is CITIES, WORK_MODES is the shared list, LEVELS comes from levels.js",
          r["loc"] == r["cities"] and r["modes"] == ["Onsite", "Hybrid", "Remote"] and r["sameLevels"] and r["levels"] == ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"])
    check("reference.js: YEARS, QUALIFICATIONS and WORK_TYPES are as before", len(r["years"]) == 5 and len(r["quals"]) == 12 and len(r["types"]) == 4 and r["countries"] == 41)
    check("reference.js: no non-ICT role or industry is left",
          not any(x in r["roles"] for x in ("Nurse", "Chef", "Accountant", "Teacher", "Civil engineer")) and "Healthcare" not in r["ind"]
          and all(set(v) <= set(r["skills"]) for v in r["sugg"].values()))
    if not os.path.exists(TAXONOMY):
        info("the taxonomy file was not found: the lists are not compared with it")
        return
    t = json.load(open(TAXONOMY, encoding="utf-8"))
    check("reference.js: version of the taxonomy is 2", str(t.get("version")) == "2", str(t.get("version")))
    check("reference.js: DOMAINS and SPECIALISATIONS equal the taxonomy", r["domains"] == [d["name"] for d in t["domains"]] and r["spec"] == {d["name"]: d["specialisations"] for d in t["domains"]})
    check("reference.js: ROLES, FIELDS_OF_STUDY and CITIES equal the taxonomy",
          r["roles"] == [x["title"] for x in t["roles"]] and r["fields"] == t["fieldsOfStudy"] and r["cities"] == t["cities"])
    check("reference.js: CERTIFICATIONS equal the taxonomy (name, issuer, domains, tier)",
          r["certs"] == [{"name": c["name"], "issuer": c["issuer"], "domains": c["domains"], "tier": c["tier"]} for c in t["certifications"]])
    check("reference.js: AWARD_KINDS equal the taxonomy (kind, label)", r["awards"] == [{"kind": a["kind"], "label": a["label"]} for a in t["awardKinds"]])
    check("reference.js: SKILLS holds every skill of the taxonomy", set(s["name"] for s in t["skills"]) <= set(r["skills"]), str(len(r["skills"])))


# ---------------------------------------------------------------- 2. job card: level, experience, work mode, compare box
JOB_V2 = {"id": "job-fe-1", "title": "Senior Backend Engineer <img src=x onerror=window.__xss=1>", "company": "Northwind Labs", "category": "Software Engineering",
          "location": "Sydney", "area": "Sydney", "type": "Full-time", "salary": "$150,000 - $170,000", "summary": "Build services.", "postedAt": "2026-10-01T00:00:00Z",
          "closesAt": "2026-11-01T00:00:00Z", "skills": ["Python"], "status": "open", "level": "Senior", "minYears": 5, "maxYears": 9, "workMode": "Hybrid",
          "match": {"coverage": 80, "skills": [], "reasons": [], "gaps": [], "notes": []}}
JOB_OLD = {"id": "job-fe-2", "title": "Old Job", "company": "Acme", "category": "Technology & Data", "location": "Perth", "type": "Full-time", "salary": "Market competitive",
           "skills": [], "status": "open", "level": None, "minYears": None, "maxYears": None, "workMode": None,
           "match": {"coverage": None, "skills": [], "reasons": [], "gaps": [], "notes": []}}


def check_card_functions(b, shots_name):
    r = b.eval("""(async (full, old) => {
      const m = await import('/js/components/job-card.js');
      const out = {};
      out.exp = [[5, 9], [5, null], [null, null], [0, 2], [2, 2], [1, 1], [null, 6], [5.5, 9], [9, 5], ['', ''], ['5', '9']].map(([a, b]) => m.experienceText(a, b));
      const box = document.getElementById('fe-testbed');
      box.innerHTML = '<ul class="job-list">' + m.jobCardHtml(full) + m.jobCardHtml(old) + '</ul>';
      const cards = box.querySelectorAll('.job-card');
      out.chips = [...cards[0].querySelectorAll('.job-facts li')].map(li => li.textContent.trim());
      out.chipClass = [...cards[0].querySelectorAll('.job-facts .chip')].map(c => c.className);
      out.oldFacts = cards[1].querySelectorAll('.job-facts').length;
      out.xss = window.__xss === undefined && cards[0].querySelector('.job-main img') === null;
      const label0 = cards[0].querySelector('label.compare-pick');
      out.compareLabel = label0 ? label0.textContent.trim() : null;
      out.compareBox = !!cards[0].querySelector('input[type=checkbox][data-compare-job="job-fe-1"]');
      out.compareTitle = label0 ? label0.getAttribute('title') : null;
      out.noCompare = (() => { const d = document.createElement('div'); d.innerHTML = m.jobCardHtml(full, { compare: false }); return d.querySelectorAll('[data-compare-job]').length; })();
      out.compact = (() => { const d = document.createElement('div'); d.innerHTML = m.jobCardHtml(full, { compact: true }); return { facts: d.querySelectorAll('.job-facts li').length, box: d.querySelectorAll('[data-compare-job]').length }; })();
      out.jobFactsEmpty = m.jobFactsHtml({});
      return out;
    })(%s, %s)""" % (json.dumps(JOB_V2), json.dumps(JOB_OLD)))
    check("job card: experienceText gives '5–9 years', '5+ years', '', '0–2 years', '2 years', '1 year', 'Up to 6 years', '5.5–9 years', '5+ years' (max below min), '' and '5–9 years'",
          r["exp"] == ["5–9 years", "5+ years", "", "0–2 years", "2 years", "1 year", "Up to 6 years", "5.5–9 years", "9+ years", "", "5–9 years"], str(r["exp"]))
    check("job card: chips Level, Experience and Work mode show (with a hidden word for screen readers)",
          r["chips"] == ["Level: Senior", "Experience: 5–9 years", "Work mode: Hybrid"], str(r["chips"]))
    check("job card: a job with no level, years and work mode (old data) has no chip row", r["oldFacts"] == 0 and r["jobFactsEmpty"] == "")
    check("job card: the title is escaped (no image, no script)", r["xss"])
    check("job card: has a 'Compare' check box for the basket (its name has the job title)", r["compareBox"] and r["compareLabel"].startswith("Compare Senior Backend Engineer"), str(r["compareLabel"]))
    check("job card: the check box can be left out; a compact card (similar jobs) has facts and the box", r["noCompare"] == 0 and r["compact"] == {"facts": 3, "box": 1}, str(r["compact"]))
    shot(b, shots_name)


# ---------------------------------------------------------------- 3. the profile card (what employers see)
def check_profile_card(b):
    shared = {"alias": "Teal Heron", "roles": [{"title": "Data Engineer", "anzsco": "262111"}], "skills": ["Python", "SQL", "dbt"],
              "skillLevels": [{"name": "Python", "level": 4}, {"name": "SQL", "level": 5}], "level": "Senior", "yearsExperience": 6.5, "years": "6–10 years",
              "certifications": [{"name": "AWS Certified Cloud Practitioner", "issuer": "Amazon Web Services", "year": 2023}],
              "awards": [{"name": "Regional Hackathon Winner 2024", "kind": "hackathon", "year": 2024}], "qualifications": ["Bachelor's degree"]}
    old = {"alias": "Teal Heron", "roles": [], "skills": ["Python"], "qualifications": [], "years": "3–5 years", "industries": ["Technology"]}
    r = b.eval("""(async (shared, old) => {
      const m = await import('/js/components/profile-card.js');
      const box = document.getElementById('fe-testbed');
      box.innerHTML = m.sharedProfileHtml(shared);
      const t1 = box.textContent.replace(/\\s+/g, ' ');
      const chips = [...box.querySelectorAll('.chip')].map(c => c.textContent.trim());
      const labels = [...box.querySelectorAll('dt')].map(d => d.textContent.trim());
      box.innerHTML = m.sharedProfileHtml(old);
      const labelsOld = [...box.querySelectorAll('dt')].map(d => d.textContent.trim());
      const facts = (() => { box.innerHTML = m.sharedFactsHtml(shared); return box.textContent.replace(/\\s+/g, ' '); })();
      return { t1, chips, labels, labelsOld, facts, exp: [m.experienceOf({ yearsExperience: 1 }), m.experienceOf({ years: '3–5 years' }), m.experienceOf({})] };
    })(%s, %s)""" % (json.dumps(shared), json.dumps(old)))
    check("profile card: shows level, exact years, certifications, awards (name and year) and skill levels",
          "Senior" in r["chips"] and "6.5 years" in r["chips"] and "AWS Certified Cloud Practitioner (2023)" in r["chips"]
          and "Regional Hackathon Winner 2024 (2024)" in r["chips"] and "Python · Advanced" in r["chips"] and "SQL · Expert" in r["chips"] and "dbt" in r["chips"], str(r["chips"]))
    check("profile card: an employer sees no issuer and no award kind (names and years only)", "Amazon Web Services" not in r["t1"] and "hackathon" not in r["t1"].replace("Hackathon Winner", ""), r["t1"][:300])
    check("profile card: rows Level, Experience, Skills, Certifications and Awards", all(k in r["labels"] for k in ["Level", "Experience", "Skills", "Certifications", "Awards"]), str(r["labels"]))
    check("profile card: a snapshot of an older application has no Level, Certifications or Awards row (and keeps the years range)",
          not any(k in r["labelsOld"] for k in ["Level", "Certifications", "Awards"]) and "Experience" in r["labelsOld"] and "Domains" in r["labelsOld"], str(r["labelsOld"]))
    check("profile card: short lines for the Home panel", "Level: Senior · 6.5 years" in r["facts"] and "Certifications: AWS Certified Cloud Practitioner (2023)" in r["facts"] and "Awards:" in r["facts"], r["facts"])
    check("profile card: experienceOf uses the exact years first, then the range", r["exp"] == ["1 year", "3–5 years", ""], str(r["exp"]))


# ---------------------------------------------------------------- 4. "Your path to this job" (fixtures of plan section 5.3)
PATH_EXPECT = {   # name: (axes, fit items, gap items)
    "axes10": (10, 7, 4), "axes8": (8, 2, 3), "axes6": (6, 3, 0), "axes3": (3, 1, 1), "emptyFit": (4, 0, 2), "emptyGap": (4, 2, 0), "longLabels": (5, 2, 3), "bothEmpty": (3, 0, 0),
}


def check_path(b, shots):
    fx = json.load(open(FIXTURES, encoding="utf-8"))["paths"]
    for name, (n_axes, n_fit, n_gap) in PATH_EXPECT.items():
        path = fx[name]
        set_testbed(b)
        r = b.eval("""(async (path) => {
          const m = await import('/js/components/bridge.js');
          const box = document.getElementById('fe-testbed');
          box.innerHTML = m.pathHtml(path);
          const panel = box.querySelector('.panel');
          const svg = panel.querySelector('svg.rd-svg');
          const q = (s) => [...panel.querySelectorAll(s)].map(e => e.textContent.replace(/\\s+/g, ' ').trim());
          return {
            h2: panel.querySelector('h2') && panel.querySelector('h2').textContent, muted: panel.querySelector('.panel-head .muted').textContent,
            labelledby: panel.getAttribute('aria-labelledby'), h2id: panel.querySelector('h2').id,
            chips: q('.path-summary .chip'), axes: svg ? Number(svg.dataset.axes) : 0, legend: q('.rd-legend li'), figureClass: panel.querySelector('figure') ? panel.querySelector('figure').className : '',
            rows: [...panel.querySelectorAll('.path-table tbody tr')].map(tr => [...tr.children].map(c => c.textContent.replace(/\\s+/g, ' ').trim())),
            statusIcons: panel.querySelectorAll('.path-status svg.icon').length, statusCount: panel.querySelectorAll('.path-status').length,
            fit: q('.path-fit'), gaps: q('.path-gap'), gapKinds: q('.path-gap .path-kind'), required: panel.querySelectorAll('.path-gap .path-required').length,
            headings: q('h3'), empties: q('.path-empty'),
            line: !!panel.querySelector('.lc-svg, .line-chart, .lc-legend') || /next 12 months|12-month/i.test(panel.textContent),
            overflow: panel.scrollWidth > panel.clientWidth + 1 || document.documentElement.scrollWidth > window.innerWidth,
            safe: panel.querySelectorAll('.path-note b').length === 0, text: panel.textContent.replace(/\\s+/g, ' '),
            tableHead: q('.path-table thead th'), caption: q('.path-table caption'),
          };
        })(%s)""" % json.dumps(path))
        tag = f"path [{name}]"
        check(f"{tag}: head has h2 'Your path to this job', a muted line and the panel is named by it", r["h2"] == "Your path to this job" and r["labelledby"] == r["h2id"] and "guide for you" in r["muted"])
        s = path["summary"]
        fit_n, gap_n = s["fitCount"], s["gapCount"]
        want = [f"{fit_n} fit", f"{gap_n} {'gap' if gap_n == 1 else 'gaps'}"]
        check(f"{tag}: summary chips '{want[0]}' and '{want[1]}'", r["chips"][:2] == want, str(r["chips"]))
        if gap_n:
            months = s["monthsToClose"]
            txt = f"about {months:g} {'month' if months <= 1.05 else 'months'} to close the gaps"
            check(f"{tag}: a chip says '{txt}'", txt in r["chips"], str(r["chips"]))
        else:
            check(f"{tag}: no months chip when there is no gap", not any("to close the gaps" in c for c in r["chips"]), str(r["chips"]))
        check(f"{tag}: the readiness tier is a chip", any(s["readinessTier"] in c for c in r["chips"]), str(r["chips"]))
        check(f"{tag}: two-layer radar with {n_axes} axes: 'You have' filled, 'Job requires' outline", r["axes"] == n_axes and "radar-layers" in r["figureClass"]
              and r["legend"] == ["You have", "Job requires"], f"axes={r['axes']} {r['figureClass']} {r['legend']}")
        check(f"{tag}: the numbers table has {n_axes} rows, with required and have", len(r["rows"]) == n_axes and r["tableHead"][:4] == ["Skill group (0 to 100)", "Job requires", "You have", "Status"], str(r["tableHead"]))
        want_rows = [[a["label"], f"{a['required']:g}", f"{a['have']:g}", {"fit": "Fit", "above": "Above", "gap": "Gap"}[a["status"]]] for a in path["axes"]]
        check(f"{tag}: each row has the numbers and a status in words (Fit, Above or Gap)", r["rows"] == want_rows, str(r["rows"][:3]))
        check(f"{tag}: every status has an icon next to the word (colour is not the only signal)", r["statusCount"] == n_axes and r["statusIcons"] == n_axes)
        check(f"{tag}: lists 'Where you fit' ({n_fit}) and 'Gaps to close' ({n_gap})", len(r["fit"]) == n_fit and len(r["gaps"]) == n_gap and "Where you fit" in r["headings"] and "Gaps to close" in r["headings"], f"{len(r['fit'])} {len(r['gaps'])}")
        if n_fit:
            f0 = path["fit"][0]
            check(f"{tag}: a fit item has the label and 'You: … · Needs: …'", f0["label"] in r["fit"][0] and f"You: {f0['have']} · Needs: {f0['need']}" in r["fit"][0], r["fit"][0])
        else:
            check(f"{tag}: an empty fit list gives a short text", any("Nothing in your profile meets" in e for e in r["empties"]), str(r["empties"]))
        if n_gap:
            g0 = path["gaps"][0]
            kind = {"missing": "Missing", "below_level": "Below level", "experience": "Experience", "level": "Level", "certification": "Certification"}[g0["kind"]]
            have = g0["have"][0].upper() + g0["have"][1:]
            months = g0["months"]
            mt = "less than 1 month" if months < 1 else f"about {months:g} {'month' if months <= 1.05 else 'months'}"
            check(f"{tag}: a gap item has the kind chip '{kind}', have and need, the months and 'Required' when it must be met",
                  r["gapKinds"][0] == kind and f"You: {have} · Needs: {g0['need']}" in r["gaps"][0] and mt in r["gaps"][0] and (r["required"] == sum(1 for g in path["gaps"] if g["must"])), f"{r['gapKinds']} {r['gaps'][0]} req={r['required']}")
        else:
            check(f"{tag}: an empty gap list says 'No gaps: you meet every requirement.'", "No gaps: you meet every requirement." in r["empties"], str(r["empties"]))
        check(f"{tag}: no 12-month line chart, no projection text", not r["line"])
        check(f"{tag}: nothing runs over the edge of the panel or the page", not r["overflow"])
        if name == "longLabels":
            check(f"{tag}: HTML in a note is shown as text, not as a tag", r["safe"] and "<b>not bold</b> & safe" in r["text"])
        shot(b, f"path_{name}.png", full=True)
    # small screen: the two columns become one and nothing runs over
    set_testbed(b)
    set_viewport(b, 390, 900)
    r = b.eval("""(async (path) => {
      const m = await import('/js/components/bridge.js');
      document.getElementById('fe-testbed').innerHTML = m.pathHtml(path);
      const g = document.querySelector('.path-grid');
      return { cols: getComputedStyle(g).gridTemplateColumns.split(' ').length, overflow: document.documentElement.scrollWidth > window.innerWidth,
               panelOver: document.querySelector('.panel.path').scrollWidth > document.querySelector('.panel.path').clientWidth + 1 };
    })(%s)""" % json.dumps(fx["longLabels"]))
    check("path: on a small screen it is one column and nothing runs over (long labels)", r["cols"] == 1 and not r["overflow"] and not r["panelOver"], str(r))
    shot(b, "path_small_screen.png", full=True)
    set_viewport(b, 1280, 900)
    # no path: a short note, no crash
    r = b.eval("""(async () => {
      const m = await import('/js/components/bridge.js');
      const out = {};
      for (const [k, v] of [['undefined', undefined], ['null', null], ['empty', {}], ['text', 'x'], ['badlists', { axes: 'a', fit: 5, gaps: null }]]) {
        const d = document.createElement('div'); d.innerHTML = m.pathHtml(v);
        out[k] = { note: (d.querySelector('.path-empty-note') || {}).textContent || null, h2: (d.querySelector('h2') || {}).textContent || null, chart: d.querySelectorAll('svg').length };
      }
      const old = document.createElement('div');
      old.innerHTML = m.bridgeHtml({ occupation: { tier: 'x', anzsco: '1', title: 't' }, readiness: { tier: 'y', months: 3 }, gaps: [{ name: 'a', months: 2 }], projection: { labels: ['Now', '1 mo'], months: [0, 1], match: [1, 2], gap: [3, 4] } });
      out.oldShape = { note: (old.querySelector('.path-empty-note') || {}).textContent || null, line: old.querySelectorAll('.lc-svg, .line-chart').length, fit: old.querySelectorAll('#fitTitle').length };
      const none = document.createElement('div'); none.innerHTML = m.bridgeHtml(undefined);
      out.none = (none.querySelector('.path-empty-note') || {}).textContent || null;
      return out;
    })()""")
    note = "A detailed path is not available for this job."
    check("path: a missing, empty or broken path gives the short note and no chart (no crash)", all(r[k]["note"] == note and r[k]["h2"] == "Your path to this job" and r[k]["chart"] == 0 for k in ["undefined", "null", "empty", "text"]), str(r))
    check("path: lists that are not lists do not crash (the panel still draws)", r["badlists"]["h2"] == "Your path to this job" or r["badlists"]["note"] == note, str(r["badlists"]))
    check("path: the old answer shape (no `path`, with `projection`) gives the note and no line chart", r["oldShape"]["note"] == note and r["oldShape"]["line"] == 0, str(r["oldShape"]))
    check("path: bridgeHtml(undefined) does not crash", r["none"] == note, str(r["none"]))
    # bridgeHtml with the 8 axes keeps the "How this job fits you" panel
    r = b.eval("""(async (path) => {
      const m = await import('/js/components/bridge.js');
      const axes = ['Occupation fit', 'Skills', 'Work methods', 'Readiness', 'Capability', 'Pay upside', 'Location', 'Freshness'].map((label, i) => ({ key: 'k' + i, label, formula: i < 3 ? 'F1' : i === 3 ? 'F2' : 'F5', value: 50 + i * 5 }));
      const d = document.createElement('div'); d.innerHTML = m.bridgeHtml({ axes, score: 71.4, path });
      return { fit: (d.querySelector('#fitTitle') || {}).textContent, radars: d.querySelectorAll('svg.rd-svg').length, axes: [...d.querySelectorAll('svg.rd-svg')].map(s => s.dataset.axes), chip: (d.querySelector('.fit .chip') || {}).textContent, pathH: (d.querySelector('#pathTitle') || {}).textContent };
    })(%s)""" % json.dumps(fx["axes8"]))
    check("path: the 8-axis panel 'How this job fits you' stays, with its own radar, before 'Your path to this job'",
          r["fit"] == "How this job fits you" and r["radars"] == 2 and r["axes"] == ["8", "8"] and r["chip"] == "Fit score 71.4" and r["pathH"] == "Your path to this job", str(r))


# ---------------------------------------------------------------- 5. lists against the real backend
def prepare_lists(api, talent_pw):
    """Data for the list checks: 12 bookmarks and 12 active applications for the demo talent. Returns the ids."""
    tok = api.login("candidate@demo.jinder.app", talent_pw)
    jobs = api.call("GET", "/jobs?pageSize=40&sort=newest", token=tok)
    free = [j["id"] for j in jobs["items"] if not j.get("applicationId")]
    saved = free[:12]
    for jid in saved:
        api.call("PUT", f"/bookmarks/{jid}", token=tok)
    applied = []
    for jid in free[12:23]:
        r = api.call("POST", "/applications", {"jobId": jid, "note": ""}, tok)
        if r.get("id"):
            applied.append(jid)
    return {"saved": saved, "applied": applied, "token": tok}


def check_home(b, base):
    go(b, "#/home", "document.querySelector('.recs .job-card')")
    b.pump(0.5)
    r = b.eval("""({ cards: document.querySelectorAll('.recs [data-recs-list] .job-card').length, pager: document.querySelectorAll('.recs .pager').length,
      more: (document.querySelector('.recs-more') || {}).textContent || '', link: (document.querySelector('.recs-more a') || {}).getAttribute ? document.querySelector('.recs-more a').getAttribute('href') : null,
      asked: performance.getEntriesByType('resource').map(e => e.name).filter(n => n.includes('/api/jobs/recommended')),
      boxes: document.querySelectorAll('.recs .job-card [data-compare-job]').length })""", False)
    check("home: the recommendations widget shows 5 cards and no pager", r["cards"] == 5 and r["pager"] == 0, str(r))
    check("home: the widget asks the API for pageSize=5 (sort best)", any("pageSize=5" in n and "sort=best" in n for n in r["asked"]), str(r["asked"]))
    check("home: a line tells that these are the best of the list and links to all jobs", "best of" in r["more"] and r["link"] == "#/jobs", r["more"])
    check("home: each card has the Compare check box", r["boxes"] == 5)
    r = b.eval("({ big: (document.querySelector('.activity .big-num') || {}).textContent || '', shared: (document.querySelector('[data-shared]') || {}).textContent || '' })", False)
    return r


def check_jobs(b, base, shots):
    # reset the memory of the page size, then open the list
    b.eval("Object.keys(localStorage).filter(k => k.startsWith('jinder.pagesize.')).forEach(k => localStorage.removeItem(k))", False)
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    ids1 = card_ids(b)
    total = total_of(range_text(b))
    pages = math.ceil(total / 10)
    check("jobs: page 1 has 10 cards and the pager says 'Showing 1–10 of N'", len(ids1) == 10 and range_text(b) == f"Showing 1–10 of {total}" and total > 20, f"{len(ids1)} {range_text(b)}")
    sort = b.eval("({ label: document.querySelector('.sort-select label').textContent, value: document.querySelector('#jobs-sort').value, opts: [...document.querySelectorAll('#jobs-sort option')].map(o => o.textContent), lblFor: document.querySelector('.sort-select label').getAttribute('for') })", False)
    check("jobs: sort select 'Sort by' with 'Best match' (default) and 'Newest posted'", sort == {"label": "Sort by", "value": "best", "opts": ["Best match", "Newest posted"], "lblFor": "jobs-sort"}, str(sort))
    check("jobs: the count line says 'Best fit first.'", "Best fit first." in b.text("[data-count]"), b.text("[data-count]"))
    shot(b, "jobs_page1.png")
    # chips come from the API: a job with a level has the chip, a job without has none (old data has none)
    api = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.jobs.search({ page: 1, pageSize: 10, sort: 'best' });
      return r.items.map(j => ({ id: j.id, level: j.level, min: j.minYears, max: j.maxYears, mode: j.workMode })); })()""")
    dom = b.eval("[...document.querySelectorAll('[data-list] .job-card')].map(c => ({ id: c.dataset.card, facts: [...c.querySelectorAll('.job-facts li')].map(li => li.textContent.trim()) }))", False)
    byid = {d["id"]: d["facts"] for d in dom}
    def facts_of(j):
        out = [f"Level: {j['level']}"] if j["level"] else []
        text = exp_text(j["min"], j["max"])
        if text:
            out.append(f"Experience: {text}")
        if j["mode"]:
            out.append(f"Work mode: {j['mode']}")
        return out
    ok = all(byid[j["id"]] == facts_of(j) for j in api if j["id"] in byid)
    check("jobs: the chips on each card (Level, Experience, Work mode) match the API; a fact that is null gives no chip", ok and len(api) == 10, str(list(zip(api, dom))[:2]))
    if not any(j["level"] for j in api):
        info("the backend has no job level yet (old catalogue): the chips are checked with a fixture and a stub only")
    # next page
    b.click("[data-pager-page='2']")
    b.wait_for("document.querySelector('.pager-range') && document.querySelector('.pager-range').textContent.startsWith('Showing 11')", LONG_WAIT)
    ids2 = card_ids(b)
    check("jobs: page 2 has other jobs than page 1", len(ids2) == 10 and not set(ids1) & set(ids2))
    h = b.eval("location.hash", False)
    check("jobs: the address keeps page, pageSize and sort", "page=2" in h and "pageSize=10" in h and "sort=best" in h, h)
    b.wait_for("document.getElementById('announcer').textContent.includes('Page 2')", 10)
    check(f"jobs: a screen reader hears 'Page 2 of {pages}'", announcer(b) == f"Page 2 of {pages}", announcer(b))
    check("jobs: after a page change the focus is on the list heading", b.eval("document.activeElement && document.activeElement.id", False) == "resultsTitle")
    check("jobs: the current page button has aria-current and the pager has a label", b.eval("(document.querySelector('.pager [aria-current=page]') || {}).textContent", False) == "2"
          and b.eval("document.querySelector('.pager nav').getAttribute('aria-label')", False) == "Pagination")
    # Back
    b.eval("history.back()", False)
    b.wait_for("location.hash === '#/jobs' && document.querySelector('.pager-range') && document.querySelector('.pager-range').textContent.startsWith('Showing 1–10')", LONG_WAIT)
    check("jobs: the Back button goes to page 1 with the same jobs", card_ids(b) == ids1)
    # a page past the end gives the last page, and the address is corrected
    go(b, "#/jobs?page=9999", "document.querySelector('.pager-range') && document.querySelector('.pager-range').textContent.includes('of')")
    b.pump(0.5)
    last = b.eval("location.hash", False)
    check("jobs: a page past the end shows the last page and the address says so", f"page={pages}" in last and range_text(b).endswith(f"of {total}") and 0 < len(card_ids(b)) <= 10, f"{last} {range_text(b)}")
    # page size
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    set_select(b, "[data-pager-size]", "20")
    b.wait_for("document.querySelectorAll('[data-list] .job-card').length === 20 && document.querySelector('.pager-range').textContent.startsWith('Showing 1–20')", LONG_WAIT)
    h = b.eval("location.hash", False)
    check("jobs: 20 rows per page gives 20 cards, page 1, and the address has pageSize=20", "pageSize=20" in h and "page=1" in h, h)
    key = b.eval("Object.keys(localStorage).filter(k => k.startsWith('jinder.pagesize.jobs.')).map(k => [k, localStorage.getItem(k)])", False)
    check("jobs: the page size is remembered for this list and user", len(key) == 1 and key[0][1] == "20", str(key))
    check("jobs: the size select keeps the focus after the change", b.eval("document.activeElement && document.activeElement.hasAttribute('data-pager-size')", False))
    go(b, "#/home", "document.querySelector('.recs .job-card')")
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    check("jobs: after leaving and coming back the size is still 20", b.eval("document.querySelector('[data-pager-size]').value", False) == "20" and len(card_ids(b)) == 20)
    # sort: newest
    set_select(b, "#jobs-sort", "newest")
    b.wait_for("location.hash.includes('sort=newest') && document.querySelector('[data-count]').textContent.includes('Newest first.')", LONG_WAIT)
    b.pump(0.5)
    dom_ids = card_ids(b)
    api = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.jobs.search({ page: 1, pageSize: 20, sort: 'newest' }); return r.items.map(j => [j.id, j.postedAt]); })()""")
    dates = [x[1] for x in api]
    check("jobs: sort 'Newest posted' puts the newest jobs first (the API order is by date)", dom_ids == [x[0] for x in api] and dates == sorted(dates, reverse=True), str(dates[:4]))
    check("jobs: a sort change goes to page 1 and the address has sort=newest", "sort=newest" in b.eval("location.hash", False) and "page=1" in b.eval("location.hash", False))
    check("jobs: a screen reader hears the new sort", "Sorted by Newest posted" in announcer(b), announcer(b))
    shot(b, "jobs_newest.png")
    set_select(b, "#jobs-sort", "best")
    b.wait_for("location.hash.includes('sort=best') && document.querySelector('[data-count]').textContent.includes('Best fit first.')", LONG_WAIT)
    b.pump(0.5)
    api = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.jobs.search({ page: 1, pageSize: 20, sort: 'best' }); return r.items.map(j => [j.id, j.match.score]); })()""")
    scores = [x[1] for x in api]
    check("jobs: sort 'Best match' puts the best fit first", card_ids(b) == [x[0] for x in api] and scores == sorted(scores, reverse=True), str(scores[:4]))
    # a sort change on page 3 goes back to page 1
    b.click("[data-pager-page='3']") if b.eval("!!document.querySelector('[data-pager-page=\"3\"]')", False) else None
    b.wait_for("location.hash.includes('page=3')", LONG_WAIT)
    set_select(b, "#jobs-sort", "newest")
    b.wait_for("location.hash.includes('sort=newest')", LONG_WAIT)
    check("jobs: a sort change on page 3 goes back to page 1", "page=1" in b.eval("location.hash", False), b.eval("location.hash", False))
    # the search words stay in the address when the user changes the page
    set_select(b, "[data-pager-size]", "10")
    b.wait_for("document.querySelectorAll('[data-list] .job-card').length === 10", LONG_WAIT)
    go(b, "#/jobs?q=manager", "document.querySelector('[data-count]') && document.querySelector('[data-count]').textContent.includes('manager')")
    b.wait_for("document.querySelector('[data-list] .job-card') || document.querySelector('[data-list] .empty')", LONG_WAIT)
    if b.eval("!!document.querySelector('[data-pager-page=\"2\"]')", False):
        b.click("[data-pager-page='2']")
        b.wait_for("location.hash.includes('page=2')", LONG_WAIT)
        h = b.eval("location.hash", False)
        check("jobs: the search word stays in the address on page 2", "q=manager" in h and "page=2" in h, h)
        check("jobs: the count line keeps the search words", "for “manager”" in b.text("[data-count]"), b.text("[data-count]"))
    else:
        info("the search 'manager' has one page only: the address check of page 2 is skipped")
    # empty state
    go(b, "#/jobs?q=zzqqxx", "document.querySelector('[data-list] .empty')")
    check("jobs: no result gives the empty state, a link to all jobs and no pager",
          "No open jobs match your search" in b.text("[data-list]") and b.eval("!!document.querySelector('[data-list] a[href=\"#/jobs\"]')", False) and b.eval("document.querySelectorAll('.pager').length", False) == 0)
    # error state: the answer of the server fails
    b.eval("window.__realFetch = window.fetch; window.fetch = (u, o) => String(u).includes('/api/jobs?') ? Promise.resolve(new Response(JSON.stringify({ error: { code: 'SERVER_ERROR', message: 'Stub failure.' } }), { status: 500, headers: { 'Content-Type': 'application/json' } })) : window.__realFetch(u, o);", False)
    go(b, "#/jobs?q=err", "document.querySelector('[data-list] .empty[role=alert]')")
    check("jobs (stub error): an error shows its message in an alert and no pager", "Stub failure." in b.text("[data-list]") and b.eval("document.querySelectorAll('.pager').length", False) == 0)
    b.eval("window.fetch = window.__realFetch", False)
    b.take_problems()   # the 500 of the stub is on purpose
    # a small screen
    set_viewport(b, 390, 900)
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    r = b.eval("({ over: document.documentElement.scrollWidth > window.innerWidth, selectH: document.querySelector('[data-pager-size]').getBoundingClientRect().height, sortH: document.querySelector('#jobs-sort').getBoundingClientRect().height, cmpH: document.querySelector('.compare-pick').getBoundingClientRect().height })", False)
    check("jobs: on a small screen nothing runs over and the controls are 44px high", not r["over"] and r["selectH"] >= 44 and r["sortH"] >= 44 and r["cmpH"] >= 44, str(r))
    shot(b, "jobs_small_screen.png")
    set_viewport(b, 1280, 900)
    b.eval("Object.keys(localStorage).filter(k => k.startsWith('jinder.pagesize.')).forEach(k => localStorage.removeItem(k))", False)


def check_bookmarks(b, prep):
    saved = prep["saved"]   # in the order of saving: the last one is the newest
    go(b, "#/bookmarks", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    ids1 = card_ids(b)
    check("bookmarks: 12 saved jobs, 10 on page 1, newest save first (default sort 'Recently saved')", len(ids1) == 10 and ids1[0] == saved[-1] and range_text(b) == "Showing 1–10 of 12", f"{range_text(b)} {ids1[:2]}")
    sort = b.eval("({ value: document.querySelector('#bookmarks-sort').value, opts: [...document.querySelectorAll('#bookmarks-sort option')].map(o => o.textContent) })", False)
    check("bookmarks: sort options 'Recently saved' (default), 'Best match', 'Newest posted'", sort == {"value": "saved", "opts": ["Recently saved", "Best match", "Newest posted"]}, str(sort))
    check("bookmarks: the count line says '12 saved jobs.'", b.text("[data-count]").startswith("12 saved jobs."), b.text("[data-count]"))
    check("bookmarks: the old compare picker is gone (no 'Compare jobs (n/3)' button, no pick boxes)",
          b.eval("document.querySelectorAll('[data-compare], [data-compare-pick], [data-picked]').length", False) == 0 and "Compare jobs (" not in b.text("main, .dash"))
    shot(b, "bookmarks_page1.png")
    b.click("[data-pager-page='2']")
    b.wait_for("document.querySelector('.pager-range').textContent.startsWith('Showing 11')", LONG_WAIT)
    ids2 = card_ids(b)
    check("bookmarks: page 2 has the 2 other jobs", len(ids2) == 2 and not set(ids1) & set(ids2) and set(ids1 + ids2) == set(saved), str(ids2))
    check("bookmarks: the address and the screen reader know page 2", "page=2" in b.eval("location.hash", False) and announcer(b) == "Page 2 of 2", announcer(b))
    # sort
    set_select(b, "#bookmarks-sort", "newest")
    b.wait_for("location.hash.includes('sort=newest') && document.querySelectorAll('[data-list] .job-card').length === 10", LONG_WAIT)
    b.pump(0.4)
    api = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.bookmarks.list({ page: 1, pageSize: 10, sort: 'newest' }); return r.items.map(j => [j.id, j.postedAt]); })()""")
    dates = [x[1] for x in api]
    check("bookmarks: sort 'Newest posted' shows the newest jobs first and goes to page 1", card_ids(b) == [x[0] for x in api] and dates == sorted(dates, reverse=True) and "page=1" in b.eval("location.hash", False))
    set_select(b, "#bookmarks-sort", "best")
    b.wait_for("location.hash.includes('sort=best')", LONG_WAIT)
    b.pump(0.6)
    api = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.bookmarks.list({ page: 1, pageSize: 10, sort: 'best' }); return r.items.map(j => [j.id, j.match.score]); })()""")
    scores = [x[1] for x in api]
    check("bookmarks: sort 'Best match' shows the best fit first", card_ids(b) == [x[0] for x in api] and scores == sorted(scores, reverse=True), str(scores[:4]))
    # remove two bookmarks on page 2: the list loads again; with 10 left there is one page and no pager
    set_select(b, "#bookmarks-sort", "saved")
    b.wait_for("location.hash.includes('sort=saved')", LONG_WAIT)
    b.wait_for("document.querySelector('.pager-range')", LONG_WAIT)
    b.click("[data-pager-page='2']")
    b.wait_for("document.querySelector('.pager-range').textContent.startsWith('Showing 11')", LONG_WAIT)
    first = card_ids(b)[0]
    b.eval(f"document.querySelector('[data-list] [data-bookmark={json.dumps(first)}]').click()", False)
    b.wait_for("document.querySelector('[data-count]').textContent.startsWith('11 saved jobs.')", LONG_WAIT)
    check("bookmarks: removing a bookmark removes its card and the count follows", first not in card_ids(b) and b.text("[data-count]").startswith("11 saved jobs."), b.text("[data-count]"))
    second = card_ids(b)[0]
    b.eval(f"document.querySelector('[data-list] [data-bookmark={json.dumps(second)}]').click()", False)
    b.wait_for("document.querySelector('[data-count]').textContent.startsWith('10 saved jobs.') && document.querySelectorAll('[data-list] .job-card').length === 10", LONG_WAIT)
    check("bookmarks: after the last card of page 2 is removed the list shows page 1 (10 jobs) and the pager is gone",
          b.eval("document.querySelectorAll('.pager').length", False) == 0 and "page=1" in b.eval("location.hash", False), b.eval("location.hash", False))
    check("bookmarks: the focus goes to the list heading, not to nowhere", b.eval("document.activeElement && document.activeElement.id", False) == "savedTitle", str(b.eval("document.activeElement && document.activeElement.tagName", False)))


def check_applications(b, prep):
    go(b, "#/applications", "document.querySelector('[data-list] .app-row')")
    b.wait_for("document.querySelector('.pager')", LONG_WAIT)
    counts = b.eval("({ active: document.querySelector('[data-n=active]').textContent, past: document.querySelector('[data-n=past]').textContent, rows: document.querySelectorAll('.app-row').length })", False)
    total_active = 1 + len(prep["applied"])
    check(f"applications: the tab 'Active' counts all {total_active} applications (not only one page), 'Past' counts 0", counts["active"] == str(total_active) and counts["past"] == "0", str(counts))
    check("applications: page 1 has 10 rows and the pager says 'Showing 1–10 of N'", counts["rows"] == 10 and range_text(b) == f"Showing 1–10 of {total_active}", range_text(b))
    sort = b.eval("({ value: document.querySelector('#apps-sort').value, opts: [...document.querySelectorAll('#apps-sort option')].map(o => o.textContent) })", False)
    check("applications: sort 'Recently updated' (default), 'Best skill match', 'Newest application'", sort == {"value": "updated", "opts": ["Recently updated", "Best skill match", "Newest application"]}, str(sort))
    rows1 = b.eval("[...document.querySelectorAll('.app-row .job-title-link')].map(a => a.getAttribute('href'))", False)
    shot(b, "applications_page1.png")
    b.click("[data-pager-page='2']")
    b.wait_for("document.querySelector('.pager-range').textContent.startsWith('Showing 11')", LONG_WAIT)
    rows2 = b.eval("[...document.querySelectorAll('.app-row .job-title-link')].map(a => a.getAttribute('href'))", False)
    check("applications: page 2 has the other applications", len(rows2) == total_active - 10 and not set(rows1) & set(rows2), str(rows2))
    check("applications: the address keeps page, size and tab, and the screen reader hears the page", "page=2" in b.eval("location.hash", False) and announcer(b) == "Page 2 of 2", b.eval("location.hash", False))
    # sort
    for value, key in (("best", "coverage"), ("newest", "createdAt")):
        set_select(b, "#apps-sort", value)
        b.wait_for(f"location.hash.includes('sort={value}') && document.querySelector('.pager-range').textContent.startsWith('Showing 1–10')", LONG_WAIT)
        b.pump(0.4)
        api = b.eval("""(async (sort) => { const { api } = await import('/js/api/index.js'); const r = await api.applications.list({ page: 1, pageSize: 50, sort }); return r.items.filter(a => !a.final).map(a => ['#/applications/' + a.id, a.coverage, a.createdAt]); })(%s)""" % json.dumps(value))
        dom = b.eval("[...document.querySelectorAll('.app-row .job-title-link')].map(a => a.getAttribute('href'))", False)
        col = [x[1] if key == "coverage" else x[2] for x in api]
        check(f"applications: sort '{value}' gives the order of the API ({key} first) and goes to page 1", dom == [x[0] for x in api][:10] and col == sorted(col, reverse=True), f"{dom[:2]} {col[:4]}")
    link = b.eval("document.querySelector('[data-tab=past]').getAttribute('href')", False)
    check("applications: the tab links keep the sort", "sort=newest" in link and "tab=past" in link, link)
    go(b, "#/applications?tab=past", "document.querySelector('[data-list] .empty')")
    check("applications: the 'Past' tab is empty with its own text and no pager", "No past applications" in b.text("[data-list]") and b.eval("document.querySelectorAll('.pager').length", False) == 0)
    # the Home counts every active application, not one page
    go(b, "#/home", "document.querySelector('.activity .big-num')")
    b.wait_for("document.querySelector('.activity .big-num') && /^\\d+/.test(document.querySelector('.activity .big-num').textContent)", LONG_WAIT)
    check("home: 'Active applications' counts all of them (all pages)", re.match(r"^(\d+)", b.text(".activity .big-num")).group(1) == str(total_active), b.text(".activity .big-num"))


# ---------------------------------------------------------------- 6. the compare basket on the cards
def check_basket(b, shots):
    clear_basket(b)
    go(b, "#/jobs?page=1", "document.querySelector('[data-list] .job-card') && document.querySelector('.pager')")
    ids = card_ids(b)
    boxes = b.eval("document.querySelectorAll('[data-list] .job-card [data-compare-job]').length", False)
    check("compare: each card of the list has the 'Compare' check box", boxes == 10, str(boxes))
    names = b.eval("[...document.querySelectorAll('[data-list] .compare-pick')].slice(0, 2).map(l => l.textContent.trim())", False)
    check("compare: the box name has the job title for a screen reader", all(n.startswith("Compare ") and len(n) > 10 for n in names), str(names))
    for jid in ids[:5]:
        b.eval(f"document.querySelector('[data-compare-job={json.dumps(jid)}]').click()", False)
        b.pump(0.15)
    basket = b.eval("(() => { const k = Object.keys(localStorage).find(k => k.startsWith('jinder.compare.') && k.endsWith('.job')); return k ? JSON.parse(localStorage.getItem(k)).map(x => x.id) : null; })()", False)
    check("compare: 5 ticked jobs are in the basket (kind 'job')", basket == ids[:5], str(basket))
    check("compare: the basket bar shows 'Compare (5/5)'", "Compare (5/5)" in b.text(".compare-tray"), b.text(".compare-tray"))
    shot(b, "compare_basket_5.png")
    b.eval(f"document.querySelector('[data-compare-job={json.dumps(ids[5])}]').click()", False)
    b.pump(0.5)
    r = b.eval(f"({{ checked: document.querySelector('[data-compare-job={json.dumps(ids[5])}]').checked, note: document.querySelector('[data-compare-job={json.dumps(ids[5])}]').closest('.card-actions').querySelector('[data-compare-note]').textContent, said: document.getElementById('announcer').textContent }})", False)
    check("compare: the 6th job is refused (box cleared) with a text and a polite announcement 'You can compare up to 5 jobs.'",
          not r["checked"] and r["note"] == "You can compare up to 5 jobs." and r["said"] == "You can compare up to 5 jobs.", str(r))
    check("compare: the basket still has 5 jobs", b.eval("(() => { const k = Object.keys(localStorage).find(k => k.endsWith('.job')); return JSON.parse(localStorage.getItem(k)).length; })()", False) == 5)
    # remove one with the box, one with the bar
    b.eval(f"document.querySelector('[data-compare-job={json.dumps(ids[0])}]').click()", False)
    b.pump(0.3)
    check("compare: clearing a box takes the job out of the basket", "Compare (4/5)" in b.text(".compare-tray"), b.text(".compare-tray"))
    b.eval(f"document.querySelector('.compare-tray [aria-label*=\"Remove\"]').click()", False)
    b.pump(0.3)
    left = b.eval("[...document.querySelectorAll('[data-list] [data-compare-job]:checked')].length", False)
    check("compare: removing a job in the bar clears its box in the list", left == 3 and "Compare (3/5)" in b.text(".compare-tray"), f"{left} {b.text('.compare-tray')}")
    # the basket stays on page 2: the boxes of page 2 are free, and the 4th/5th can be added
    b.click("[data-pager-page='2']")
    b.wait_for("document.querySelector('.pager-range').textContent.startsWith('Showing 11')", LONG_WAIT)
    ids2 = card_ids(b)
    check("compare: on page 2 the basket is kept (3 jobs) and its boxes are not ticked", "Compare (3/5)" in b.text(".compare-tray") and b.eval("document.querySelectorAll('[data-list] [data-compare-job]:checked').length", False) == 0)
    b.eval(f"document.querySelector('[data-compare-job={json.dumps(ids2[0])}]').click()", False)
    b.pump(0.3)
    check("compare: a job of page 2 can be added to the basket", "Compare (4/5)" in b.text(".compare-tray"))
    clear_basket(b)


# ---------------------------------------------------------------- 7. job detail
V2_DESCRIPTION = "\n\n".join(
    ["## About the role\n" + "We build the payments platform of Northwind Labs. The team is small and works in the open. " * 4,
     "## What you will do\n" + "\n".join(f"- Design and ship service number {i} with tests and a clear owner" for i in range(1, 9)),
     "## What you bring\n" + "\n".join(f"- {t}" for t in ["5 to 9 years of backend work", "Strong Python", "SQL and data modelling", "Calm incident work"]),
     "## Nice to have\n- Kubernetes\n- Terraform\n- An open source contribution",
     "## Tech stack\n- Python\n- PostgreSQL\n- Docker\n- AWS",
     "## Certifications and awards\n" + "A cloud certification helps. A hackathon award is a plus. " * 5,
     "## What we offer\n" + "\n".join(f"- Benefit number {i} of the demo company" for i in range(1, 7)),
     "## About the company\n" + "Northwind Labs is a made-up company for this test. " * 6,
     "## How we hire\n" + "Two short calls and one paid task. " * 8])
JOB_STUB = {"level": "Senior", "specialisation": "Backend", "minYears": 5, "maxYears": 9, "workMode": "Hybrid", "educationMin": "Bachelor's degree",
            "skillRequirements": [{"name": "Python", "level": 4, "must": True}],
            "certifications": {"required": ["AWS Certified Solutions Architect - Associate"], "preferred": ["Certified Kubernetes Administrator", "HashiCorp Certified: Terraform Associate"]},
            "awards": {"preferred": ["hackathon", "open-source"]}, "description": V2_DESCRIPTION}

STUB_FETCH = """(stub) => {
  window.__realFetch = window.__realFetch || window.fetch;
  window.__stub = stub;
  window.fetch = async (url, opts) => {
    const res = await window.__realFetch(url, opts);
    const u = String(url);
    if (window.__stub && /\\/api\\/jobs\\/(?!recommended|compare)[^/?]+$/.test(u) && (!opts || !opts.method || opts.method === 'GET') && res.ok) {
      const data = await res.json();
      Object.assign(data, window.__stub.job);
      if (window.__stub.path) data.bridge = Object.assign({}, data.bridge || {}, { path: window.__stub.path });
      return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return res;
  };
  return true;
}"""


def exp_text(lo, hi):
    """The same text as experienceText() of the job card."""
    def n(v):
        v = round(float(v) * 10) / 10
        return str(int(v)) if v == int(v) else str(v)
    if lo is not None and hi is not None:
        if float(hi) < float(lo):
            return f"{n(lo)}+ years"
        return f"{n(lo)} {'year' if float(lo) == 1 else 'years'}" if n(lo) == n(hi) else f"{n(lo)}–{n(hi)} years"
    if lo is not None:
        return f"{n(lo)}+ years"
    return f"Up to {n(hi)} years" if hi is not None else ""


def award_labels():
    try:
        return {a["kind"]: a["label"] for a in json.load(open(TAXONOMY, encoding="utf-8"))["awardKinds"]}
    except OSError:
        return {}


def pick_job(api, tok, with_similar=True):
    jobs = api.call("GET", "/jobs?pageSize=20&sort=best", token=tok)
    for j in jobs["items"]:
        if j.get("applicationId"):
            continue
        d = api.call("GET", "/jobs/" + j["id"], token=tok)
        if not with_similar or d.get("similar"):
            return d
    return d


def check_detail(b, api, tok, shots):
    job = pick_job(api, tok)
    jid = job["id"]
    clear_basket(b)
    go(b, f"#/jobs/{jid}", "document.querySelector('.jd-view')")
    b.pump(0.8)
    r = b.eval("""({ jd: (() => { const e = document.querySelector('.jd-view'); return { tag: e.tagName, role: e.getAttribute('role'), tab: e.getAttribute('tabindex'), label: e.getAttribute('aria-label') }; })(),
      about: document.querySelector('#aboutTitle').textContent, aboutIn: !!document.querySelector('#aboutTitle').closest('.panel').querySelector('.jd-view'),
      facts: [...document.querySelectorAll('.fact-grid dt')].map(d => d.textContent), factVals: [...document.querySelectorAll('.fact-grid dd')].map(d => d.textContent),
      cert: !!document.querySelector('#certTitle'), award: !!document.querySelector('#awardTitle'), cmp: (document.querySelector('[data-compare-detail]') || {}).getAttribute ? document.querySelector('[data-compare-detail]').getAttribute('aria-pressed') : null,
      pathNote: (document.querySelector('.path-empty-note') || {}).textContent, pathH: (document.querySelector('#pathTitle') || {}).textContent, fitH: (document.querySelector('#fitTitle') || {}).textContent,
      line: document.querySelectorAll('.lc-svg, .line-chart').length, text12: /next 12 months/i.test(document.body.textContent),
      old: !!document.querySelector('.jd-text'),
      factMap: Object.fromEntries([...document.querySelectorAll('.fact-grid > div')].map(d => [d.querySelector('dt').textContent, d.querySelector('dd').textContent])),
      groups: [...document.querySelectorAll('.cred-group')].map(g => g.closest('.panel') && g.querySelector('.cred-label').textContent + ':' + [...g.querySelectorAll('.chip')].map(c => c.textContent).join('|')),
      h3: [...document.querySelectorAll('.jd-view h3')].map(h => h.textContent), jdText: document.querySelector('.jd-view').textContent.trim(),
      scrollH: document.querySelector('.jd-view').scrollHeight, clientH: document.querySelector('.jd-view').clientHeight,
      pathAxes: (() => { const s = document.querySelector('#pathTitle').closest('.panel').querySelector('svg.rd-svg'); return s ? Number(s.dataset.axes) : 0; })(),
      pathFit: document.querySelectorAll('.path-fit').length, pathGaps: document.querySelectorAll('.path-gap').length,
      pathRows: document.querySelectorAll('.path-table tbody tr').length })""", False)
    check("detail: 'About the role' panel holds the job description box (a focusable region with a label)", r["about"] == "About the role" and r["aboutIn"] and r["jd"] == {"tag": "SECTION", "role": "region", "tab": "0", "label": "Job description"}, str(r["jd"]))
    certs = job.get("certifications") or {}
    has_v2 = bool(job.get("level") or job.get("skillRequirements") or certs.get("required") or certs.get("preferred") or (job.get("awards") or {}).get("preferred"))
    want_facts = [k for k, on in [("Level", job.get("level")), ("Experience", job.get("minYears") is not None or job.get("maxYears") is not None), ("Work mode", job.get("workMode")),
                                  ("Place", True), ("Type", True), ("Salary", job.get("salary")), ("Education", job.get("educationMin"))] if on]
    check("detail: the facts block has only the facts that the job has (Place, Type and Salary always; Level, Experience, Work mode, Education when given)", r["facts"] == want_facts, f"{r['facts']} want {want_facts}")
    check("detail: the Certifications and Awards sections show only for a job that has the V2 data", r["cert"] == has_v2 and r["award"] == has_v2, f"has_v2={has_v2}")
    if not has_v2:
        info("the job of the backend has no V2 data yet (old catalogue): level, experience, certifications and awards are checked with a stub below")
    else:
        want_vals = {"Level": job.get("level"), "Work mode": job.get("workMode"), "Education": job.get("educationMin"), "Type": job.get("type")}
        want_vals = {k: v for k, v in want_vals.items() if v}
        if job.get("minYears") is not None or job.get("maxYears") is not None:
            want_vals["Experience"] = exp_text(job.get("minYears"), job.get("maxYears"))
        check("detail (real data): the facts have the values of the job (level, experience, work mode, education, type)", all(r["factMap"].get(k) == v for k, v in want_vals.items()), f"{r['factMap']} want {want_vals}")
        want_groups = []
        if certs.get("required"):
            want_groups.append("Required:" + "|".join(certs["required"]))
        if certs.get("preferred"):
            want_groups.append("Preferred:" + "|".join(certs["preferred"]))
        kinds = (job.get("awards") or {}).get("preferred") or []
        if kinds:
            labels = award_labels()
            want_groups.append("Preferred:" + "|".join(labels.get(k, k) for k in kinds))
        check("detail (real data): Certifications (Required, Preferred) and Awards (Preferred) list what the job asks for", r["groups"] == want_groups, f"{r['groups']} want {want_groups}")
        desc = job.get("description") or ""
        heads = [ln[3:].strip() for ln in desc.splitlines() if ln.startswith("## ")]
        check("detail (real data): the description shows in full with the headings of the JD, not cut with '…'", r["h3"] == heads and len(heads) >= 6 and not r["jdText"].endswith("…") and r["jdText"].endswith(desc.strip().splitlines()[-1].lstrip("- ").strip()[-20:]), f"{r['h3']} vs {heads}")
        check("detail (real data): the description box scrolls when the text is long", r["scrollH"] > r["clientH"] or len(desc) < 1500, f"{r['scrollH']} {r['clientH']} {len(desc)}")
    check("detail: a 'Compare' button for the basket (not pressed)", r["cmp"] == "false")
    path = (job.get("bridge") or {}).get("path")
    if path:
        check("detail (real data): 'Your path to this job' draws the path of the backend (axes, fit list, gap list) and has no note",
              r["pathH"] == "Your path to this job" and r.get("pathNote") is None and r["pathAxes"] == len(path["axes"]) and r["pathRows"] == len(path["axes"])
              and r["pathFit"] == len(path["fit"]) and r["pathGaps"] == len(path["gaps"]), f"{r['pathAxes']} {r['pathFit']} {r['pathGaps']} vs {len(path['axes'])} {len(path['fit'])} {len(path['gaps'])}")
    else:
        check("detail: 'Your path to this job' shows the short note when the backend sends no path", r["pathH"] == "Your path to this job" and r.get("pathNote") == "A detailed path is not available for this job.", str(r.get("pathNote")))
    check("detail: no 12-month line chart and the old text box is gone", r["line"] == 0 and not r["text12"] and not r["old"])
    shot(b, "detail_real.png", full=True)
    # the Compare button
    b.click("[data-compare-detail]")
    b.pump(0.3)
    check("detail: the Compare button puts the job in the basket (pressed) and the bar shows 1", b.eval("document.querySelector('[data-compare-detail]').getAttribute('aria-pressed')", False) == "true" and "Compare (1/5)" in b.text(".compare-tray"), b.text(".compare-tray"))
    b.click("[data-compare-detail]")
    b.pump(0.3)
    check("detail: a second click takes it out again", b.eval("document.querySelector('[data-compare-detail]').getAttribute('aria-pressed')", False) == "false" and b.eval("!document.querySelector('.compare-tray') || document.querySelector('.compare-tray').hidden", False))
    # Similar jobs -> Compare with these jobs
    sim = len(job["similar"])
    b.click("[data-compare-similar]")
    b.wait_for("location.hash.startsWith('#/compare')", 20)
    basket = b.eval("(() => { const k = Object.keys(localStorage).find(k => k.endsWith('.job')); return JSON.parse(localStorage.getItem(k)).map(x => x.id); })()", False)
    check("detail: 'Compare with these jobs' puts this job and the similar jobs (at most 5) in the basket and opens #/compare",
          basket == ([jid] + [s["id"] for s in job["similar"]])[:5] and len(basket) == min(5, 1 + sim), f"{basket} sim={sim}")
    clear_basket(b)
    # --- stub: a job with the V2 keys and the JD with headings; the real answer of the server with these keys added
    fx = json.load(open(FIXTURES, encoding="utf-8"))["paths"]
    b.eval("(" + STUB_FETCH + ")(%s)" % json.dumps({"job": JOB_STUB, "path": fx["axes10"]}), False)
    go(b, f"#/jobs/{jid}", "document.querySelector('.fact-grid') && document.querySelector('#pathTitle')")
    b.pump(0.8)
    r = b.eval("""(() => { const jd = document.querySelector('.jd-view');
      return { facts: [...document.querySelectorAll('.fact-grid > div')].map(d => d.querySelector('dt').textContent + '=' + d.querySelector('dd').textContent),
        certH: document.querySelector('#certTitle').textContent, awardH: document.querySelector('#awardTitle').textContent,
        groups: [...document.querySelectorAll('.cred-group')].map(g => g.querySelector('.cred-label').textContent + ':' + [...g.querySelectorAll('.chip')].map(c => c.textContent).join('|')),
        h3: [...jd.querySelectorAll('h3')].map(h => h.textContent), li: jd.querySelectorAll('li').length, scrollH: jd.scrollHeight, clientH: jd.clientHeight, overflowY: getComputedStyle(jd).overflowY,
        cut: jd.textContent.trim().endsWith('…'), tag: document.querySelector('.job-tags .chip').textContent,
        panels: [...document.querySelectorAll('.jd-grid .panel h2')].map(h => h.textContent), pathAxes: document.querySelector('#pathTitle').closest('.panel').querySelector('svg.rd-svg').dataset.axes,
        pathItems: document.querySelectorAll('.path-item').length, note: document.querySelectorAll('.path-empty-note').length };
    })()""", False)
    check("detail (stub): facts block shows Level, Experience '5–9 years', Work mode, Place, Type, Salary and Education",
          [x.split("=")[0] for x in r["facts"]] == ["Level", "Experience", "Work mode", "Place", "Type", "Salary", "Education"] and "Experience=5–9 years" in r["facts"] and "Level=Senior" in r["facts"]
          and "Work mode=Hybrid" in r["facts"] and "Education=Bachelor's degree" in r["facts"], str(r["facts"]))
    check("detail (stub): 'Certifications' has Required and Preferred lists, 'Awards' has Preferred with the readable kind names",
          r["certH"] == "Certifications" and r["awardH"] == "Awards" and r["groups"] == ["Required:AWS Certified Solutions Architect - Associate", "Preferred:Certified Kubernetes Administrator|HashiCorp Certified: Terraform Associate", "Preferred:Hackathon|Open source contribution"], str(r["groups"]))
    check("detail (stub): the description shows in full with the headings of the JD (9 headings, bullets) and the category chip has the specialisation",
          len(r["h3"]) == 9 and r["h3"][0] == "About the role" and r["h3"][-1] == "How we hire" and r["li"] >= 20 and "Backend" in r["tag"], f"{len(r['h3'])} {r['tag']}")
    check("detail (stub): the box scrolls (content taller than the box, overflow auto) and the text is not cut", r["scrollH"] > r["clientH"] and r["overflowY"] == "auto" and not r["cut"], f"{r['scrollH']} {r['clientH']}")
    check("detail (stub): the order of the panels: Job facts, About the role, then the skills panel", r["panels"][:3] == ["Job facts", "About the role", "Your skills for this job"], str(r["panels"]))
    check("detail (stub): 'Your path to this job' draws the fixture (10 axes, 7 fit, 4 gaps) and has no note", r["pathAxes"] == "10" and r["pathItems"] == 11 and r["note"] == 0, f"{r['pathAxes']} {r['pathItems']}")
    shot(b, "detail_stub_v2.png", full=True)
    # keyboard: the box takes focus and the arrow key scrolls it
    b.eval("document.querySelector('.jd-view').focus()", False)
    b.pump(0.2)
    for typ in ("keyDown", "keyUp"):
        b.call("Input.dispatchKeyEvent", {"type": typ, "key": "ArrowDown", "code": "ArrowDown", "windowsVirtualKeyCode": 40, "nativeVirtualKeyCode": 40})
    b.pump(0.5)
    r = b.eval("({ focus: document.activeElement.classList.contains('jd-view'), top: document.querySelector('.jd-view').scrollTop, ring: getComputedStyle(document.querySelector('.jd-view')).outlineStyle })", False)
    check("detail (stub): the keyboard focuses the description box, the arrow key scrolls it, and the focus ring shows", r["focus"] and r["top"] > 0 and r["ring"] != "none", str(r))
    # keyboard: tab order reaches the box (a short walk from the heading of the panel)
    b.eval("document.querySelector('#aboutTitle').setAttribute('tabindex', '-1'); document.querySelector('#aboutTitle').focus()", False)
    for typ in ("keyDown", "keyUp"):
        b.call("Input.dispatchKeyEvent", {"type": typ, "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    b.pump(0.3)
    check("detail (stub): Tab from the panel heading goes to the description box", b.eval("document.activeElement.classList.contains('jd-view')", False))
    # small screen: the box is still scrollable and the page does not run over
    set_viewport(b, 390, 800)
    b.pump(0.5)
    r = b.eval("""(() => { const jd = document.querySelector('.jd-view'); const cs = getComputedStyle(jd); return { max: cs.maxHeight, h: jd.clientHeight, scroll: jd.scrollHeight, over: document.documentElement.scrollWidth > window.innerWidth,
      cols: getComputedStyle(document.querySelector('.jd-grid')).gridTemplateColumns.split(' ').length, vh: window.innerHeight }; })()""", False)
    check("detail (stub, small screen): one column, the box has a maximum height of 70% of the screen and still scrolls, nothing runs over",
          r["cols"] == 1 and r["h"] <= r["vh"] * 0.7 + 2 and r["scroll"] > r["h"] and not r["over"], str(r))
    shot(b, "detail_stub_small_screen.png")
    # the path panel on the small screen (fixture) has no overflow either
    r = b.eval("({ over: document.documentElement.scrollWidth > window.innerWidth, path: document.querySelector('.panel.path').scrollWidth <= document.querySelector('.panel.path').clientWidth + 1 })", False)
    check("detail (stub, small screen): the path panel does not run over", not r["over"] and r["path"], str(r))
    set_viewport(b, 1280, 900)
    b.eval("window.__stub = null", False)
    return jid


# ---------------------------------------------------------------- 8. onboarding with the new fields (real CV parser)
def ob_title(b):
    return b.eval("(document.querySelector('#ob-title') || {}).textContent || ''", False)


def ob_wait(b, title, timeout=LONG_WAIT):
    b.wait_for(f"document.querySelector('#ob-title') && document.querySelector('#ob-title').textContent === {json.dumps(title)}", timeout)
    b.pump(0.3)


def ob_continue(b):
    b.eval("document.querySelector('#obFoot [type=submit]').click()", False)
    b.pump(0.5)


def ob_text(b):
    return b.text("#obBody")


def start_onboarding(b, base, email, pw, cv_name):
    sign_in(b, base, email, pw)
    b.wait_for("document.querySelector('#onboarding[open]')", 40)
    b.set_file("#ob-cv", os.path.join(CV_DIR, cv_name))
    b.pump(0.4)
    b.click("#ob-cv-next")
    ob_wait(b, "Your education")


def check_onboarding_found(b, base, api, shots):
    """User A: cv07 shows every field. The talent goes through every step and saves."""
    email, pw = api.new_talent("a")
    if not os.path.exists(os.path.join(CV_DIR, "cv07_linkedin_export.pdf")):
        info("the CV fixtures were not found: the onboarding checks with a real CV are skipped")
        return None
    start_onboarding(b, base, email, pw, "cv07_linkedin_export.pdf")
    t = ob_text(b)
    check("onboarding: after the scan 'What we found in your CV' lists current role, desired role, level, years, certifications and awards",
          "What we found in your CV" in t and all(k in t for k in ["Current role:", "Desired role:", "Level:", "Years of experience:", "Certifications:", "Awards:"]), t[:500])
    r = b.eval("[...document.querySelectorAll('.cv-found-list li')].map(li => li.className + '|' + li.textContent.replace(/\\s+/g, ' ').trim())", False)
    check("onboarding: every found field has a check and its value; the summary also holds the desired role of this CV",
          all(x.startswith("is-found|") for x in r) and any("Desired role: AI Research Scientist" in x for x in r) and any("Level: Lead" in x for x in r) and any("7.3 years" in x for x in r), str(r))
    shot(b, "onb_found_education.png")
    ob_continue(b)
    ob_wait(b, "Your experience")
    r = b.eval("""({ text: document.querySelector('#obBody').innerText, level: document.querySelector('#ob-level').value, years: document.querySelector('#ob-yearsExperience').value,
      band: document.querySelector('#ob-years').value, bandDisabled: document.querySelector('#ob-years').disabled,
      levelOpts: [...document.querySelectorAll('#ob-level option')].map(o => o.textContent), hints: [...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim()),
      labels: [...document.querySelectorAll('#obBody label')].map(l => l.textContent.trim()),
      levelLabel: document.querySelector('label[for=ob-level]').textContent, yearsLabel: document.querySelector('label[for=ob-yearsExperience]').textContent })""", False)
    check("onboarding: the word is 'Domains' (not 'Industries' or 'Industry') on the experience step", "Domains" in r["labels"] and not re.search(r"industr", r["text"], re.I), str(r["labels"]))
    chips = b.eval("[...document.querySelectorAll('[data-field=industry] .skill-chip')].map(c => c.textContent.trim())", False)
    check("onboarding: the domain comes from the CV result (`domain`) and is one of the 3 domains", len(chips) == 1 and chips[0] in ("Software Engineering", "AI & Machine Learning", "Data"), str(chips))
    check("onboarding: Level is a select with 'Not sure' and the 6 levels, filled from the CV (Lead)", r["levelOpts"] == ["Not sure", "Intern", "Junior", "Mid", "Senior", "Lead", "Principal"] and r["level"] == "Lead", str(r["levelOpts"]) + r["level"])
    check("onboarding: 'Exact years of experience' is filled from the CV (7.3) and chooses the band '6–10 years', which is then locked", r["years"] == "7.3" and r["band"] == "6–10 years" and r["bandDisabled"], str(r))
    check("onboarding: each new field says 'From your CV' (current role, level, exact years)", r["hints"].count("From your CV. Check it. Change it if it is wrong.") >= 3, str(r["hints"]))
    check("onboarding: the Level and Exact years labels are tied to their fields", r["levelLabel"].startswith("Your level") and r["yearsLabel"].startswith("Exact years"))
    shot(b, "onb_found_experience.png")
    ob_continue(b)
    ob_wait(b, "Your skills")
    ob_continue(b)
    ob_wait(b, "Certifications and awards")
    r = b.eval("""({ rows: document.querySelectorAll('#obBody .cred-row').length,
      certs: [...document.querySelectorAll('[data-field=certifications] .cred-row')].map(r => [r.querySelector('input[id$=-name]').value, r.querySelector('input[id$=-issuer]').value, r.querySelector('input[id$=-year]').value, r.querySelector('input[id$=-issuer]').readOnly]),
      awards: [...document.querySelectorAll('[data-field=awards] .cred-row')].map(r => [r.querySelector('input[id$=-name]').value, r.querySelector('select').value, r.querySelector('input[id$=-year]').value]),
      hints: [...document.querySelectorAll('.cred-hint')].map(h => h.textContent), cv: [...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim()),
      counts: [...document.querySelectorAll('.cred-field .list-count')].map(c => c.textContent) })""", False)
    check("onboarding: the CV's certifications show as rows with the issuer of a known certification (read-only)", len(r["certs"]) == 2 and all(c[0] and c[1] and c[3] for c in r["certs"]), str(r["certs"]))
    check("onboarding: the CV's awards show as rows with a name and a kind from the list", len(r["awards"]) == 2 and all(a[0] and a[1] for a in r["awards"]), str(r["awards"]))
    names_hint = "Employers see these names. Do not write your own name, your employer's name or contact details here."
    check("onboarding: both lists say 'Employers see these names. Do not write your own name, your employer's name or contact details here.'", r["hints"] == [names_hint, names_hint], str(r["hints"]))
    check("onboarding: the lists say 'From your CV' and count the rows ('2 of 20')", r["cv"].count("From your CV. Check it. Change it if it is wrong.") == 2 and r["counts"] == ["2 of 20", "2 of 20"], f"{r['cv']} {r['counts']}")
    shot(b, "onb_found_credentials.png")
    ob_continue(b)
    ob_wait(b, "Your translated profile")
    b.wait_for("document.querySelector('.tr-card')", LONG_WAIT)
    b.pump(0.4)
    r = b.eval("""({ cards: document.querySelectorAll('.tr-card').length, withLevel: document.querySelectorAll('.tr-card .tr-level').length,
      sel: [...document.querySelectorAll('.tr-level-select')].map(s => [s.value, s.options[s.selectedIndex].text]),
      opts: [...document.querySelector('.tr-level-select').options].map(o => o.text), fromCv: document.querySelectorAll('.tr-level-from:not([hidden])').length,
      roleCardsWithLevel: [...document.querySelectorAll('.tr-card')].filter(c => /From your role|From your qualification/.test(c.querySelector('.tr-from').textContent) && c.querySelector('.tr-level')).length,
      lbl: document.querySelector('.tr-level label').textContent })""", False)
    check("onboarding: each skill card has a Level select with 1 to 5 and their words, and the first option leaves it to the evidence",
          r["withLevel"] >= 5 and r["opts"][1:] == ["1 · Beginner", "2 · Working", "3 · Proficient", "4 · Advanced", "5 · Expert"] and r["opts"][0].startswith("From the evidence ("), str(r["opts"]))
    check("onboarding: a skill that the CV gave a level for starts with that level and says 'From your CV'", any(s[0] for s in r["sel"]) and r["fromCv"] >= 1, f"{r['sel']} {r['fromCv']}")
    check("onboarding: a card from a role or a qualification has no Level select; the label names the skill for a screen reader", r["roleCardsWithLevel"] == 0 and r["lbl"].startswith("Level for "), r["lbl"])
    # change one level: the preview of what employers see follows
    first = b.eval("document.querySelector('.tr-level-select').dataset.levelFor", False)
    b.eval("(() => { const s = document.querySelector('.tr-level-select'); s.value = '2'; s.dispatchEvent(new Event('change', { bubbles: true })); })()", False)
    b.pump(0.3)
    check("onboarding: changing a level hides the 'From your CV' tag of that card", b.eval("document.querySelector('.tr-level-select').closest('.tr-level').querySelector('.tr-level-from').hidden", False))
    b.click_text("button", "Accept all")
    b.pump(0.4)
    t = b.text(".tr-preview")
    check("onboarding: the 'What employers see' preview shows level, years, certifications, awards and the skill levels",
          "Level: Lead · 7.3 years" in t and "Certifications:" in t and "Awards:" in t and re.search(r"· (Beginner|Working|Proficient|Advanced|Expert)", t), t[:400])
    shot(b, "onb_found_translation.png")
    ob_continue(b)
    ob_wait(b, "What are you looking for?")
    r = b.eval("({ hint: [...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim()), chips: [...document.querySelectorAll('[data-field=targetRole] .skill-chip')].map(c => c.textContent.trim()), domains: [...document.querySelectorAll('[data-field=targetIndustries] .choice')].map(c => c.textContent), label: document.querySelector('#ob-targetIndustries-label').textContent })", False)
    check("onboarding: the desired role of this CV is filled and says 'From your CV'", "AI Research Scientist" in r["chips"] and "From your CV. Check it. Change it if it is wrong." in r["hint"], str(r))
    check("onboarding: 'Target domains' offers the 3 domains", r["label"].startswith("Target domains") and r["domains"] == ["Software Engineering", "AI & Machine Learning", "Data"], str(r["domains"]))
    b.eval("[...document.querySelectorAll('[data-field=locations] .choice')][0].click(); [...document.querySelectorAll('[data-field=workTypes] .choice')][0].click()", False)
    ob_continue(b)
    ob_wait(b, "Check your answers")
    rows = b.eval("[...document.querySelectorAll('.review-row dt')].map(d => d.firstChild.textContent)", False)
    vals = b.eval("Object.fromEntries([...document.querySelectorAll('.review-row')].map(r => [r.querySelector('dt').firstChild.textContent, r.querySelector('dd').textContent]))", False)
    check("onboarding: the review lists Domains, Level, Exact years, Certifications, Awards and Target domains (and no 'Industries')",
          all(k in rows for k in ["Domains", "Level", "Exact years", "Certifications", "Awards", "Target domains"]) and "Industries" not in rows, str(rows))
    check("onboarding: the review shows the values (Lead, 7.3 years, certification and award names)", vals["Level"] == "Lead" and vals["Exact years"] == "7.3 years" and vals["Certifications"] not in ("", "—") and vals["Awards"] not in ("", "—"), str(vals))
    shot(b, "onb_found_review.png")
    ob_continue(b)
    b.wait_for("!document.querySelector('#onboarding[open]')", LONG_WAIT)
    # what the server stored
    tok = api.login(email, pw)
    me = api.call("GET", "/me", token=tok)["profile"]
    skills_with_level = [s for s in me["translation"] if s.get("level")]
    check("onboarding: the saved profile has level Lead, exact years 7.3, 2 certifications, 2 awards (kind kept)",
          me["level"] == "Lead" and me["yearsExperience"] == 7.3 and len(me["certifications"]) == 2 and len(me["awards"]) == 2 and all(a["kind"] for a in me["awards"]),
          json.dumps({k: me.get(k) for k in ["level", "yearsExperience", "years", "certifications", "awards"]})[:300])
    check("onboarding: the saved profile keeps the levels of the skills (the CV's levels and the one the talent set to 2)", len(skills_with_level) >= 2 and any(s["level"] == 2 for s in skills_with_level), str([s.get("level") for s in me["translation"]]))
    shared = api.call("GET", "/me/shared-profile", token=tok)
    check("onboarding: what employers see has the level, years, certifications, awards and skill levels", shared.get("level") == "Lead" and shared.get("yearsExperience") is not None and len(shared.get("certifications", [])) == 2
          and len(shared.get("awards", [])) == 2 and len(shared.get("skillLevels", [])) >= 5, json.dumps({k: shared.get(k) for k in ["level", "yearsExperience"]}))
    return {"email": email, "pw": pw, "token": tok}


def check_after_save(b, user, api, shots):
    """The Home panel, the apply review and the edit mode, for the user who saved a full profile."""
    go(b, "#/home", "document.querySelector('[data-shared] .tr-preview-alias')")
    b.pump(0.8)
    t = b.text("[data-shared]")
    check("home: 'What employers see' shows the level, the years (rounded to 0.5, as the employer sees them) and the certifications and awards", "Level: Lead · 7.5 years" in t and "Certifications:" in t and "Awards:" in t, t[:500])
    check("home: the skill chips show the level of the skill ('Python · Expert')", b.eval("[...document.querySelectorAll('[data-shared] .chip-green')].some(c => / · (Beginner|Working|Proficient|Advanced|Expert)$/.test(c.textContent.trim()))", False))
    shot(b, "home_after_save.png")
    # the apply review uses the profile card
    jobs = api.call("GET", "/jobs?pageSize=5", token=user["token"])
    jid = jobs["items"][0]["id"]
    go(b, f"#/jobs/{jid}/apply", "document.querySelector('.profile-card')")
    labels = b.eval("[...document.querySelectorAll('.profile-card dt')].map(d => d.textContent)", False)
    check("apply: 'What the employer sees' has the rows Level, Experience, Skills, Certifications and Awards", all(k in labels for k in ["Level", "Experience", "Skills", "Certifications", "Awards"]), str(labels))
    chips = b.eval("[...document.querySelectorAll('.profile-card .chip')].map(c => c.textContent.trim())", False)
    check("apply: experience shows the exact years as the employer sees them ('7.5 years') and the awards and certifications show names only", "7.5 years" in chips and "Regional Hackathon Winner" in chips, str(chips))
    shot(b, "apply_profile_card.png")
    # edit mode: Home -> Edit profile -> Edit certifications -> remove one -> save
    go(b, "#/home", "document.querySelector('[data-edit-profile]')")
    b.click("[data-edit-profile]")
    ob_wait(b, "Your profile")
    r = b.eval("({ step: document.getElementById('obStep').textContent, rows: [...document.querySelectorAll('.review-row dt')].map(d => d.firstChild.textContent) })", False)
    check("onboarding (edit): 'Your profile' lists the new rows", "Certifications" in r["rows"] and "Level" in r["rows"] and r["step"].startswith("Edit profile"), str(r))
    b.eval("document.querySelector('.review-row button[aria-label=\"Edit Certifications\"]').click()", False)
    ob_wait(b, "Certifications and awards")
    check("onboarding (edit): 'Edit' on Certifications opens a short path (the step, then the profile)", b.eval("document.getElementById('obStep').textContent", False) == "Edit profile · Step 1 of 2")
    b.eval("document.querySelector('[data-field=certifications] .cred-remove').click()", False)
    b.pump(0.4)
    check("onboarding (edit): removing a row announces it, keeps the list count and moves the focus", "removed." in announcer(b) and b.text("[data-field=certifications] .list-count") == "1 of 20" and b.eval("document.activeElement.id", False).startswith("ob-certifications-0"), announcer(b))
    ob_continue(b)
    ob_wait(b, "Your profile")
    ob_continue(b)
    b.wait_for("!document.querySelector('#onboarding[open]')", LONG_WAIT)
    me = api.call("GET", "/me", token=user["token"])["profile"]
    check("onboarding (edit): after the save the profile has 1 certification", len(me["certifications"]) == 1, str(me["certifications"]))


def check_onboarding_validation(b, base, api, shots):
    """User B: cv01 does not show the desired role and awards. Validation of the new fields."""
    if not os.path.exists(os.path.join(CV_DIR, "cv01_single_classic.pdf")):
        return
    email, pw = api.new_talent("b")
    start_onboarding(b, base, email, pw, "cv01_single_classic.pdf")
    r = b.eval("[...document.querySelectorAll('.cv-found-list li')].map(li => li.className + '|' + li.textContent.replace(/\\s+/g, ' ').trim())", False)
    check("onboarding: a field that the CV does not show says 'Not found. You can add it in the next steps.'",
          any(x.startswith("is-missing|") and "Desired role:" in x and "Not found" in x for x in r) and any(x.startswith("is-missing|") and "Awards:" in x for x in r), str(r))
    ob_continue(b)
    ob_wait(b, "Your experience")
    # a domain must come from the list
    b.eval("""(() => { const i = document.querySelector('#ob-industry'); i.focus(); i.value = 'Healthcare'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    b.pump(0.3)
    opt = b.eval("[...document.querySelectorAll('#ob-industry-list li')].map(l => l.textContent)", False)
    check("onboarding: the domain list offers no 'Use \"Healthcare\"' (only the 3 domains can be added)", not any("Use" in o for o in opt), str(opt))
    b.click("[data-field=industry] .input-row > button")
    b.pump(0.3)
    err = b.eval("({ text: document.querySelector('#industry-error').textContent, invalid: document.querySelector('#ob-industry').getAttribute('aria-invalid'), by: document.querySelector('#ob-industry').getAttribute('aria-describedby') })", False)
    check("onboarding: a domain that is not in the list gives 'Choose a domain from the list.' tied to the field", err["text"] == "Choose a domain from the list." and err["invalid"] == "true" and "industry-error" in err["by"], str(err))
    b.eval("document.querySelector('#ob-industry').value = ''", False)
    # exact years: bad value, then a good one that locks the band
    b.eval("""(() => { const i = document.querySelector('#ob-yearsExperience'); i.value = '41'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    ob_continue(b)
    err = b.eval("({ text: document.querySelector('#yearsExperience-error').textContent, invalid: document.querySelector('#ob-yearsExperience').getAttribute('aria-invalid'), by: document.querySelector('#ob-yearsExperience').getAttribute('aria-describedby'), focus: document.activeElement.id })", False)
    check("onboarding: exact years 41 gives 'Enter a number from 0 to 40.', tied to the field, and the focus goes to the first error",
          err["text"] == "Enter a number from 0 to 40." and err["invalid"] == "true" and "yearsExperience-error" in err["by"] and err["focus"] == "ob-yearsExperience", str(err))
    b.eval("""(() => { const i = document.querySelector('#ob-yearsExperience'); i.value = '2.5'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    r = b.eval("({ band: document.querySelector('#ob-years').value, off: document.querySelector('#ob-years').disabled, toggleOff: document.querySelector('#ob-years').closest('.combo').querySelector('.combo-toggle').disabled })", False)
    check("onboarding: exact years 2.5 selects the band '1–2 years' and locks the band drop-down", r == {"band": "1–2 years", "off": True, "toggleOff": True}, str(r))
    b.eval("""(() => { const i = document.querySelector('#ob-yearsExperience'); i.value = ''; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    check("onboarding: clearing the exact years unlocks the band", b.eval("!document.querySelector('#ob-years').disabled", False))
    b.eval("""(() => { const s = document.querySelector('#ob-level'); s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); })()""", False)
    # certifications and awards
    b.eval("""(() => { const i = document.querySelector('#ob-yearsExperience'); i.value = '10.7'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    ob_continue(b)
    ob_wait(b, "Your skills")
    ob_continue(b)
    ob_wait(b, "Certifications and awards")
    # a certification with a free-text name: the issuer is editable. A known name locks the issuer.
    b.eval("document.querySelector('[data-field=certifications] .cred-remove').click()", False)
    b.pump(0.2)
    b.eval("document.querySelector('[data-field=certifications] .cred-remove').click()", False)
    b.pump(0.2)
    b.click("#ob-certifications-add")
    b.eval("""(() => { const i = document.querySelector('#ob-certifications-0-name'); i.focus(); i.value = 'My Own Course'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    r = b.eval("({ ro: document.querySelector('#ob-certifications-0-issuer').readOnly, opts: [...document.querySelectorAll('#ob-certifications-0-name-list li')].map(l => l.textContent) })", False)
    check("onboarding: a free-text certification name is allowed ('Use \"My Own Course\"') and its issuer is editable", not r["ro"] and any(o.startswith("Use") for o in r["opts"]), str(r))
    b.eval("""(() => { const i = document.querySelector('#ob-certifications-0-name'); i.value = 'Certified Kubernetes'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    sugg = b.eval("[...document.querySelectorAll('#ob-certifications-0-name-list li')].map(l => l.textContent)", False)
    check("onboarding: typing 'Certified Kubernetes' suggests the known certifications (Application Developer, Administrator)", any("Application Developer" in s for s in sugg) and any("Administrator" in s for s in sugg), str(sugg))
    b.eval("""[...document.querySelectorAll('#ob-certifications-0-name-list li')].find(l => l.textContent.includes('Administrator')).click()""", False)
    r = b.eval("({ name: document.querySelector('#ob-certifications-0-name').value, issuer: document.querySelector('#ob-certifications-0-issuer').value, ro: document.querySelector('#ob-certifications-0-issuer').readOnly })", False)
    check("onboarding: a known certification fills the issuer and locks it", r["name"] == "Certified Kubernetes Administrator" and r["issuer"] == "Cloud Native Computing Foundation" and r["ro"], str(r))
    # an award with a name and no kind, a bad year on the certification
    b.click("#ob-awards-add")
    b.eval("""(() => { const i = document.querySelector('#ob-awards-0-name'); i.value = 'Team Hack Night'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    b.eval("""(() => { const i = document.querySelector('#ob-certifications-0-year'); i.value = '1800'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    ob_continue(b)
    r = b.eval("""({ title: document.getElementById('ob-title').textContent,
      kindErr: document.querySelector('#ob-awards-0-kind-error').textContent, kindInvalid: document.querySelector('#ob-awards-0-kind').getAttribute('aria-invalid'), kindBy: document.querySelector('#ob-awards-0-kind').getAttribute('aria-describedby'),
      yearErr: document.querySelector('#ob-certifications-0-year-error').textContent, yearInvalid: document.querySelector('#ob-certifications-0-year').getAttribute('aria-invalid'),
      focus: document.activeElement.id })""", False)
    next_year = time.gmtime().tm_year + 1
    check("onboarding: an award without a kind gives 'Choose a kind.' under the field (aria-invalid and aria-describedby)", r["kindErr"] == "Choose a kind." and r["kindInvalid"] == "true" and "ob-awards-0-kind-error" in r["kindBy"], str(r))
    check(f"onboarding: a year outside 1990 to {next_year} gives a message, and the first error has the focus", r["yearErr"] == f"Enter a year from 1990 to {next_year}." and r["yearInvalid"] == "true" and r["focus"] == "ob-certifications-0-year" and r["title"] == "Certifications and awards", str(r))
    shot(b, "onb_credentials_errors.png")
    # a row with a name only for the award is not allowed without a name either
    b.eval("""(() => { const i = document.querySelector('#ob-awards-0-name'); i.value = ''; i.dispatchEvent(new Event('input', { bubbles: true })); const k = document.querySelector('#ob-awards-0-kind'); k.value = 'hackathon'; k.dispatchEvent(new Event('change', { bubbles: true })); })()""", False)
    b.eval("""(() => { const i = document.querySelector('#ob-certifications-0-year'); i.value = '2022'; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    ob_continue(b)
    check("onboarding: an award with a kind but no name gives 'Enter the name, or remove this row.'", b.eval("document.querySelector('#ob-awards-0-name-error').textContent", False) == "Enter the name, or remove this row.")
    # limit 20
    b.eval("document.querySelector('[data-field=awards] .cred-remove').click()", False)
    for _ in range(25):
        b.eval("(() => { const a = document.querySelector('#ob-awards-add'); if (!a.disabled) a.click(); })()", False)
    r = b.eval("({ rows: document.querySelectorAll('[data-field=awards] .cred-row').length, off: document.querySelector('#ob-awards-add').disabled, count: document.querySelector('[data-field=awards] .list-count').textContent })", False)
    check("onboarding: awards stop at 20 rows: the add button is disabled and the count says 'Maximum 20 reached'", r == {"rows": 20, "off": True, "count": "Maximum 20 reached"}, str(r))
    # empty rows are dropped, the step goes on
    b.eval("""(() => { const i = document.querySelector('#ob-certifications-0-year'); i.value = ''; i.dispatchEvent(new Event('input', { bubbles: true })); })()""", False)
    ob_continue(b)
    check("onboarding: empty rows do not stop the step (they are dropped); the next step is the translation", ob_title(b) == "Your translated profile", ob_title(b))
    shot(b, "onb_b_translation.png")
    b.eval("document.getElementById('obClose').click()", False)
    b.wait_for("!document.querySelector('#onboarding[open]')", 20)
    return email


def ob_fill(b, name, value):
    """Add a value to a list field of the onboarding dialog (type it, press Add)."""
    b.eval(f"(() => {{ const i = document.querySelector('#ob-{name}'); i.focus(); i.value = {json.dumps(value)}; i.dispatchEvent(new Event('input', {{ bubbles: true }})); }})()", False)
    b.click(f"[data-field={name}] .input-row > button")
    b.pump(0.2)


def ob_next(b, title):
    """Press Continue and wait for the next step. If a required answer is missing, add what the test knows and try again once."""
    ob_continue(b)
    try:
        ob_wait(b, title, 20)
    except TimeoutError:
        errs = b.eval("[...document.querySelectorAll('#obBody .field-error')].map(e => e.textContent).filter(Boolean)", False)
        for name, value in (("qualification", "Bachelor's degree"), ("fieldOfStudy", "Computer science"), ("currentRole", "Data Engineer"), ("skills", "Python")):
            if b.eval(f"!!document.querySelector('[data-field={name}]') && document.querySelectorAll('[data-field={name}] .skill-chip').length === 0", False):
                ob_fill(b, name, value)
        ob_continue(b)
        try:
            ob_wait(b, title, 20)
        except TimeoutError:
            raise RuntimeError(f"the step '{ob_title(b)}' did not go on to '{title}': {errs}")


def check_found_hints_target(b, base, api):
    """User C: cv13 has no desired role and 3 awards; the desired role hint on the goals step says it could not be found."""
    if not os.path.exists(os.path.join(CV_DIR, "cv13_no_target_awards.pdf")):
        return
    email, pw = api.new_talent("c")
    start_onboarding(b, base, email, pw, "cv13_no_target_awards.pdf")
    for step in ("Your experience", "Your skills", "Certifications and awards", "Your translated profile"):
        ob_next(b, step)
    b.wait_for("document.querySelector('.tr-card')", LONG_WAIT)
    b.click_text("button", "Accept all")
    ob_next(b, "What are you looking for?")
    hint = b.eval("[...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim())", False)
    check("onboarding: the goals step says 'We could not find your desired role in your CV. You can add it.' when the CV has none", "We could not find your desired role in your CV. You can add it." in hint, str(hint))
    ob_fill(b, "targetRole", "Data Engineer")
    check("onboarding: after the talent adds a desired role the hint goes away", not b.eval("[...document.querySelectorAll('.cv-hint')].some(h => h.textContent.includes('desired role'))", False))
    shot(b, "onb_c_goals.png")
    b.eval("document.getElementById('obClose').click()", False)
    b.wait_for("!document.querySelector('#onboarding[open]')", 20)


# ---------------------------------------------------------------- 9. the mock backend: the old screens still work
def check_mock(b, base, shots):
    sign_in(b, base, "candidate@demo.jinder.app", "demo1234", mock=True)
    b.wait_for("document.querySelector('.recs .job-card')", LONG_WAIT)
    r = b.eval("({ cards: document.querySelectorAll('.recs [data-recs-list] .job-card').length, pager: document.querySelectorAll('.recs .pager').length, boxes: document.querySelectorAll('.job-card [data-compare-job]').length, facts: document.querySelectorAll('.job-facts').length })", False)
    check("mock: the Home widget shows 5 cards, no pager, no compare box (the compare page needs the real backend) and one chip row (level, experience, work mode) on each card (the mock jobs have the V2 facts)", r["cards"] == 5 and r["pager"] == 0 and r["boxes"] == 0 and r["facts"] == 5, str(r))
    shot(b, "mock_home.png")
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card')")
    b.pump(0.5)
    r = b.eval("({ n: document.querySelectorAll('[data-list] .job-card').length, pager: !!document.querySelector('.pager'), range: (document.querySelector('.pager-range') || {}).textContent || '' })", False)
    check("mock: the Jobs list has a pager (the API client cuts the list) and 10 cards", r["n"] == 10 and r["pager"] and r["range"].startswith("Showing 1–10 of"), str(r))
    ids1 = card_ids(b)
    if b.eval("!!document.querySelector('[data-pager-page=\"2\"]')", False):
        b.click("[data-pager-page='2']")
        b.wait_for("document.querySelector('.pager-range').textContent.startsWith('Showing 11')", 30)
        check("mock: page 2 has other jobs", not set(ids1) & set(card_ids(b)) and "page=2" in b.eval("location.hash", False))
    set_select(b, "#jobs-sort", "newest")
    b.wait_for("location.hash.includes('sort=newest')", 30)
    b.pump(0.5)
    dates = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const r = await api.jobs.search({ page: 1, pageSize: 10, sort: 'newest' }); return r.items.map(j => j.postedAt); })()""")
    check("mock: sort 'Newest posted' works with the mock backend", card_ids(b) and dates == sorted(dates, reverse=True))
    shot(b, "mock_jobs.png")
    go(b, "#/bookmarks", "document.querySelector('[data-list] .job-card') || document.querySelector('[data-list] .empty')")
    check("mock: Bookmarks load with their sort select", b.eval("!!document.querySelector('#bookmarks-sort')", False))
    go(b, "#/applications", "document.querySelector('[data-list] .app-row') || document.querySelector('[data-list] .empty')")
    check("mock: Applications load with their sort select and the tab counts", b.eval("!!document.querySelector('#apps-sort') && /\\d/.test(document.querySelector('[data-n=active]').textContent)", False))
    # job detail
    go(b, "#/jobs", "document.querySelector('[data-list] .job-card')")
    href = b.eval("document.querySelector('[data-list] .job-card .job-title-link').getAttribute('href')", False)
    go(b, href, "document.querySelector('.jd-view')")
    b.pump(0.6)
    r = b.eval("({ jd: !!document.querySelector('.jd-view[role=region][tabindex=\"0\"]'), cmp: document.querySelectorAll('[data-compare-detail], [data-compare-similar]').length, facts: [...document.querySelectorAll('.fact-grid dt')].map(d => d.textContent), note: (document.querySelector('.path-empty-note') || {}).textContent, line: document.querySelectorAll('.lc-svg').length })", False)
    check("mock: the job detail has the description box, no compare buttons, the facts of the V2 data (Level, Experience, Work mode, Place, Type, Salary, Education) and the path note", r["jd"] and r["cmp"] == 0 and r["facts"] == ["Level", "Experience", "Work mode", "Place", "Type", "Salary", "Education"] and r["note"] == "A detailed path is not available for this job." and r["line"] == 0, str(r))
    shot(b, "mock_detail.png")
    # onboarding in the mock: edit the profile, see the new rows and fields
    go(b, "#/home", "document.querySelector('[data-edit-profile]')")
    b.click("[data-edit-profile]")
    ob_wait(b, "Your profile", 30)
    rows = b.eval("[...document.querySelectorAll('.review-row dt')].map(d => d.firstChild.textContent)", False)
    check("mock: the profile review has the new rows and says 'Domains'", all(k in rows for k in ["Domains", "Level", "Exact years", "Certifications", "Awards"]) and "Industries" not in rows, str(rows))
    b.eval("document.querySelector('.review-row button[aria-label=\"Edit Roles\"]').click()", False)
    ob_wait(b, "Your experience", 30)
    r = b.eval("({ level: !!document.querySelector('#ob-level'), years: !!document.querySelector('#ob-yearsExperience'), hints: document.querySelectorAll('.cv-hint:not(:empty)').length })", False)
    check("mock: the experience step has Level and Exact years and no 'not found' hint (the mock sends no `found`)", r["level"] and r["years"] and r["hints"] == 0, str(r))
    ob_continue(b)
    ob_wait(b, "Your translated profile", 30)
    b.wait_for("document.querySelector('.tr-card')", 40)
    r = b.eval("({ cards: document.querySelectorAll('.tr-card').length, levels: document.querySelectorAll('.tr-card .tr-level').length })", False)
    check("mock: the translation step has the Level select on the cards of skills", r["cards"] > 0 and r["levels"] > 0, str(r))
    shot(b, "mock_translation.png")
    b.eval("document.getElementById('obClose').click()", False)
    b.wait_for("!document.querySelector('#onboarding[open]')", 20)
    # the path panel with a fixture in the mock page too
    set_testbed(b)
    r = b.eval("""(async () => { const m = await import('/js/components/bridge.js'); document.getElementById('fe-testbed').innerHTML = m.bridgeHtml(undefined); return document.querySelector('.path-empty-note').textContent; })()""")
    check("mock: bridgeHtml of a job with no bridge gives the note", r == "A detailed path is not available for this job.")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--talent-pw", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--debug-port", type=int, default=9330)
    ap.add_argument("--port", type=int, default=8130)
    ap.add_argument("--start-retries", type=int, default=3)
    ap.add_argument("--start-wait", type=int, default=180)
    ap.add_argument("--skip", default="", help="parts to leave out, for a quick run: components,lists,detail,onboarding,mock")
    args = ap.parse_args()
    SHOTS_DIR[0] = args.shots
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)

    platform = None
    if args.base:
        base, talent_pw = args.base.rstrip("/"), args.talent_pw
    else:
        platform = start_platform(args.port, args.start_retries, args.start_wait)
        base = platform.base
        talent_pw = platform.pw.get("candidate@demo.jinder.app", "")
        info(f"started the platform on {base} (data folder {platform.var})")
    b = None
    try:
        api = Api(base)
        b = Browser(port=args.debug_port)
        skip = set(filter(None, args.skip.split(",")))
        # ---- components, with fixtures (the page is the real app, the modules are the real files)
        sign_in(b, base, "candidate@demo.jinder.app", talent_pw)
        if "components" not in skip:
            set_testbed(b)
            check_reference(b)
            check_card_functions(b, "job_card_v2.png")
            check_profile_card(b)
            check_path(b, args.shots)
            no_problems(b, "components: no console error, no CSP error")
        # ---- lists against the real backend
        if "lists" not in skip:
            prep = prepare_lists(api, talent_pw)
            go(b, "#/notifications", "document.querySelector('h1')")   # draws the page again (the test box is gone)
            go(b, "#/home", "document.querySelector('.recs .job-card')")
            check_home(b, base)
            check_jobs(b, base, args.shots)
            check_bookmarks(b, prep)
            check_applications(b, prep)
            shot(b, "applications_page2.png")
            check_basket(b, args.shots)
            no_problems(b, "talent lists: no console error, no CSP error")
        if "detail" not in skip:
            go(b, "#/notifications", "document.querySelector('h1')")
            check_detail(b, api, api.login("candidate@demo.jinder.app", talent_pw), args.shots)
            no_problems(b, "job detail: no console error, no CSP error")
        # ---- onboarding
        if "onboarding" not in skip:
            user = check_onboarding_found(b, base, api, args.shots)
            if user:
                check_after_save(b, user, api, args.shots)
            check_onboarding_validation(b, base, api, args.shots)
            check_found_hints_target(b, base, api)
            no_problems(b, "onboarding: no console error, no CSP error")
        # ---- mock
        if "mock" not in skip:
            check_mock(b, base, args.shots)
            no_problems(b, "mock screens: no console error, no CSP error", ignore=("australian_jobs_dataset.csv",))
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
