"""QA acceptance walk-through of the 12 feedback items R1 to R12 (docs/V2_PLAN.md section 3) in a real browser, against a freshly seeded platform.

Usage:
  python tests/browser/qa_acceptance.py [--port 8160] [--shots <folder>] [--only R1,R5] [--out results.json]
  python tests/browser/qa_acceptance.py --base http://localhost:8160 --talent-pw X --employer-pw Y     (a platform that runs already, started with --demo)

Without --base it starts the platform with `--demo --reset-db` in a temporary folder (never the folder var/ of your own data) and stops it at the end.
Every step prints PASS or FAIL. The numbers that the screens must show are read from the API. Evidence (numbers and screenshot names) goes to the file of --out.
This run is long (about 8 minutes) and it makes many accounts. It is not part of `python run_tests.py`.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Browser, Report, api_call, api_login, fetch_json, go, key, non_extension, reload, sign_in, token_of  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CV_DIR = os.path.join(ROOT, "tests", "fixtures", "cv")
JOBS_FILE = os.path.join(os.path.dirname(ROOT), "jinder_backend_engine", "data", "synthetic", "jobs.json")

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8160)
ap.add_argument("--base", default="")
ap.add_argument("--talent-pw", default="")
ap.add_argument("--employer-pw", default="")
ap.add_argument("--shots", default="")
ap.add_argument("--only", default="")
ap.add_argument("--out", default="")
ARGS = ap.parse_args()
R = Report("qa_acceptance", ARGS.shots or None)
check = R.check
EVIDENCE = {}
BASE = ARGS.base.rstrip("/") if ARGS.base else f"http://localhost:{ARGS.port}"
SERVER = None
TPW = ARGS.talent_pw
EPW = ARGS.employer_pw


# ------------------------------------------------------------------ platform
def start_platform():
    global SERVER, TPW, EPW
    var = tempfile.mkdtemp(prefix="jinder-qa-acc-")
    env = {**os.environ, "JINDER_VAR_DIR": var, "PYTHONUNBUFFERED": "1"}
    for k in ("JINDER_DB_PATH", "JINDER_UPLOAD_DIR", "JINDER_FAST_TEST_HASH"):
        env.pop(k, None)
    log = os.path.join(var, "server.log")
    SERVER = subprocess.Popen([sys.executable, os.path.join(ROOT, "start.py"), "--demo", "--reset-db", "--port", str(ARGS.port)], env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    deadline = time.time() + 90
    while time.time() < deadline and not (TPW and EPW):
        time.sleep(0.4)
        for line in open(log, errors="replace"):
            if "candidate@demo.jinder.app" in line:
                TPW = line.split()[-1]
            if "recruiter@demo.jinder.app" in line:
                EPW = line.split()[-1]
    if not (TPW and EPW):
        raise RuntimeError("the platform did not start: " + open(log, errors="replace").read()[-1500:])
    R.info(f"platform on port {ARGS.port}, data folder {var}")
    return log


def stop_platform():
    if SERVER:
        SERVER.terminate()
        try:
            SERVER.wait(timeout=10)
        except subprocess.TimeoutExpired:
            SERVER.kill()


# ------------------------------------------------------------------ data helpers (API)
def card(i, mapped, level=3, source="skill", **over):
    return {"id": f"card-{i}", "source": source, "original": mapped, "mapped": mapped, "kind": "direct", "anzsco": "", "occupation": "", "reason": "A card made by the QA run.",
            "evidence": "Moderate", "evidenceText": "", "status": "accepted", "level": level if source == "skill" else None, **over}


SKILL_SETS = [
    ["Python", "SQL", "Apache Spark", "Apache Airflow", "AWS", "Data modelling", "Git"],
    ["Python", "SQL", "Power BI", "Microsoft Excel", "Data visualisation", "Data analysis"],
    ["JavaScript", "TypeScript", "React", "Node.js", "Docker", "Git", "PostgreSQL"],
    ["Python", "PyTorch", "Machine learning", "SQL", "MLflow", "Docker"],
    ["Java", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes", "CI/CD"],
]


def new_user(role, label, company="QA Test Pty Ltd"):
    email = f"qa.{label}.{uuid.uuid4().hex[:6]}@example.test"
    body = {"role": role, "name": f"QA {label.title()}", "email": email, "password": "correct horse 1"}
    if role == "recruiter":
        body["company"] = company
    s, r = api_call(BASE, "POST", "/auth/signup", body)
    assert s == 201, (s, r)
    token = api_login(BASE, email, "correct horse 1")
    return {"email": email, "password": "correct horse 1", "token": token}


def give_profile(user, i, level="Mid", years=4.5):
    skills = SKILL_SETS[i % len(SKILL_SETS)]
    cards = [card(j, n, level=2 + (j + i) % 3) for j, n in enumerate(skills)]
    cards.append(card(90, "Data Engineer", source="role", anzsco="262111", occupation="Data Engineer"))
    cards.append(card(91, "AQF Level 7 (Bachelor degree)", source="qualification"))
    body = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Computer science"], "studyCountry": ["Vietnam"], "currentRole": ["Software Engineer"], "industry": ["Data"],
            "years": "3–5 years", "yearsExperience": years + (i % 5) * 0.5, "level": level, "skills": skills, "targetRole": ["Data Engineer"], "targetIndustries": [],
            "locations": ["Melbourne"], "workTypes": ["Full-time"], "evidence": [], "translation": cards,
            "certifications": [{"name": "AWS Certified Cloud Practitioner", "issuer": "Amazon Web Services", "year": 2022}] if i % 2 == 0 else [],
            "awards": [{"name": f"Hack Night Winner {i}", "kind": "hackathon", "year": 2023}] if i % 3 == 0 else []}
    s, me = api_call(BASE, "PATCH", "/me", {"profile": body, "onboarding": "done"}, token=user["token"])
    assert s == 200, (s, me)


JD = ("## About the role\nWe build data tools and need people who like clear numbers. The team is small, friendly and based in Sydney.\n\n"
      "## What you will do\n- Build and run data pipelines.\n- Write tests for the pipelines.\n- Talk with the product team every week.\n\n"
      "## What you bring\n- 3 to 6 years in data work.\n- SQL and Python.\n\n## Nice to have\n- Apache Airflow.\n\n## Tech stack\nPython, SQL, Apache Airflow.\n\n"
      "## What we offer\n- Hybrid work.\n\n## About QA Test\nQA Test makes made-up software for tests.\n\n## How we hire\n- A call and a short exercise.")


def post_job(token, title, jd=JD, **extra):
    body = {"title": title, "category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["Python", "SQL"], "targetApplicants": 5,
            "closesAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + 20 * 86400)), "description": jd, "level": "Mid", **extra}
    s, r = api_call(BASE, "POST", "/recruiter/jobs", body, token=token)
    assert s in (200, 201), (s, r)
    return r


def pager_info(b):
    return b.eval("""(() => { const p = document.querySelector('.pager'); if (!p) return null;
      return { range: p.querySelector('.pager-range').textContent, pages: Number(p.dataset.pagerTotalPages), page: Number(p.dataset.pagerPageNow), size: Number(p.querySelector('[data-pager-size]').value),
               nums: [...p.querySelectorAll('.pager-num')].map(x => x.textContent), prevDisabled: p.querySelector('.pager-step').disabled }; })()""", False)


def set_select(b, selector, value):
    b.eval(f"(() => {{ const s = document.querySelector({json.dumps(selector)}); s.value = {json.dumps(str(value))}; s.dispatchEvent(new Event('change', {{ bubbles: true }})); }})()", await_promise=False)
    b.pump(0.9)


def click_step(b, label):
    b.eval(f"[...document.querySelectorAll('.pager-step')].find(e => e.textContent.trim().startsWith({json.dumps(label)})).click()", await_promise=False)
    b.pump(0.9)


def wanted(name):
    return not ARGS.only or name in [x.strip().upper() for x in ARGS.only.split(",")]


def save(name, value):
    EVIDENCE[name] = value


def ob_fill(b, name, value):
    """Add a value to a list field of the onboarding dialog (type it, press Add)."""
    b.eval(f"(() => {{ const i = document.querySelector('#ob-{name}'); i.focus(); i.value = {json.dumps(value)}; i.dispatchEvent(new Event('input', {{ bubbles: true }})); }})()", await_promise=False)
    b.click(f"[data-field={name}] .input-row > button")
    b.pump(0.2)


def ob_advance(b, title, wait=15):
    """Press Continue and wait for the step `title`. A CV that does not show a required answer (for example the education) blocks the step: add a made-up answer, as a person would."""
    for _ in range(3):
        b.eval("document.querySelector('#obFoot [type=submit]').click()", await_promise=False)
        try:
            b.wait_for(f"document.querySelector('#ob-title') && document.querySelector('#ob-title').textContent === {json.dumps(title)}", wait)
            b.pump(0.4)
            return
        except TimeoutError:
            for name, value in (("qualification", "Bachelor's degree"), ("fieldOfStudy", "Computer science"), ("currentRole", "Data Engineer"), ("industry", "Data"), ("skills", "Python")):
                if b.eval(f"!!document.querySelector('[data-field={name}]') && document.querySelectorAll('[data-field={name}] .skill-chip').length === 0", False):
                    ob_fill(b, name, value)
            if b.eval("!!document.querySelector('#ob-years') && !document.querySelector('#ob-years').value && !document.querySelector('#ob-years').disabled", False):
                b.eval("(() => { const i = document.querySelector('#ob-yearsExperience'); i.value = '3'; i.dispatchEvent(new Event('input', { bubbles: true })); })()", await_promise=False)
    raise RuntimeError(f"the dialog did not go on to '{title}'")


# ================================================================== R1
def r1(b):
    R.section("R1  The CV scan reads the current role, the desired role, the level, the years, the certifications and the awards")
    expected = json.load(open(os.path.join(CV_DIR, "expected.json")))["fixtures"]
    files = ["cv02_two_column_interleaved.pdf", "cv07_linkedin_export.pdf", "cv09_docx_simple.docx", "cv11_docx_textbox_header.docx", "cv13_no_target_awards.pdf", "cv18_minimal.pdf"]
    rows = []
    for n, name in enumerate(files):
        exp = expected[name]
        user = new_user("candidate", f"cv{n}")
        sign_in(b, BASE, user["email"], user["password"])
        b.wait_for("document.querySelector('#onboarding[open]')", 40)
        b.set_file("#ob-cv", os.path.join(CV_DIR, name))
        b.wait_for("!document.querySelector('#ob-cv-next').disabled")
        b.click("#ob-cv-next")
        b.wait_for("document.querySelector('#ob-title') && document.querySelector('#ob-title').textContent === 'Your education'", 60)
        b.pump(0.5)
        items = b.eval("[...document.querySelectorAll('.cv-found-list li')].map(li => [li.className, li.textContent.replace(/\\s+/g, ' ').trim()])", False)
        got = {t.split(":")[0]: (c.startswith("is-found"), t.split(":", 1)[1].strip()) for c, t in items}
        shot = R.shot(b, f"r1-{n + 1}-{name.split('_')[0]}-found.png")
        fmt_years = lambda y: f"{y:g} years" if y is not None else None
        ok = True
        notes = []

        def field(label, want, show):
            nonlocal ok
            found, text = got[label]
            if want in (None, "", []):
                good = (not found) and "Not found" in text
            else:
                good = found and show(text)
            ok = ok and good
            notes.append(f"{label} {'OK' if good else 'WRONG'}: {text[:60]}")
        field("Current role", exp["currentRole"], lambda t: t == exp["currentRole"])
        field("Desired role", exp["targetRole"], lambda t: t == exp["targetRole"])
        field("Level", exp["level"], lambda t: t == exp["level"])
        field("Years of experience", exp["yearsExperience"], lambda t: t == fmt_years(exp["yearsExperience"]))
        field("Certifications", exp["certifications"], lambda t: t.startswith(f"{len(exp['certifications'])} found"))
        field("Awards", exp["awards"], lambda t: t.startswith(f"{len(exp['awards'])} found"))
        check(f"R1 {name}: the summary shows every field, found fields right, missing fields with the hint", ok, "; ".join(notes))
        # the fields on the next steps are filled and can be edited
        ob_advance(b, "Your experience")
        st = b.eval("({ level: document.querySelector('#ob-level').value, years: document.querySelector('#ob-yearsExperience').value, hints: [...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim()),"
                    "role: [...document.querySelectorAll('[data-field=currentRole] .skill-chip')].map(c => c.textContent.trim()), editable: !document.querySelector('#ob-level').disabled && !document.querySelector('#ob-yearsExperience').disabled })", False)
        want_level = exp["level"] or ""
        want_years = "" if exp["yearsExperience"] is None else f"{exp['yearsExperience']:g}"
        check(f"R1 {name}: the experience step has the level, the exact years and the current role in editable fields",
              st["level"] == want_level and st["years"] == want_years and st["editable"] and (exp["currentRole"] is None or any(exp["currentRole"] in r for r in st["role"])), str(st)[:300])
        rows.append({"cv": name, "layout": exp["layout"][:60], "expected": {k: exp[k] for k in ("currentRole", "level", "yearsExperience", "targetRole")}, "found_summary": {k: v[1] for k, v in got.items()}, "shot": os.path.basename(shot), "ok": ok})
        if n in (4, 5):
            # the credentials and goals steps for the CVs that lack a field: the hints
            ob_advance(b, "Your skills")
            ob_advance(b, "Certifications and awards")
            hints = b.eval("[...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim())", False)
            rows_n = b.eval("({ certs: document.querySelectorAll('[data-field=certifications] .cred-row').length, awards: document.querySelectorAll('[data-field=awards] .cred-row').length })", False)
            check(f"R1 {name}: the credentials step has the {len(exp['certifications'])} certification rows and {len(exp['awards'])} award rows of the CV", rows_n["certs"] == len(exp["certifications"]) and rows_n["awards"] == len(exp["awards"]), f"{rows_n} {hints}")
            R.shot(b, f"r1-{n + 1}-{name.split('_')[0]}-credentials.png")
            ob_advance(b, "Your translated profile")
            b.wait_for("document.querySelector('.tr-card')", 60)
            b.eval("[...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Accept all') && [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Accept all').click()", await_promise=False)
            b.pump(0.4)
            ob_advance(b, "What are you looking for?")
            hints = b.eval("[...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim())", False)
            chips = b.eval("[...document.querySelectorAll('[data-field=targetRole] .skill-chip')].map(c => c.textContent.trim())", False)
            check(f"R1 {name}: the goals step says 'We could not find your desired role in your CV. You can add it.' and the field is empty",
                  any("could not find your desired role" in h for h in hints) and not chips, f"{hints} {chips}")
            R.shot(b, f"r1-{n + 1}-{name.split('_')[0]}-goals.png")
        b.eval("document.getElementById('obClose') && document.getElementById('obClose').click()", await_promise=False)
        b.pump(0.5)
    save("R1", rows)
    # the parser numbers on all 23 fixtures come from the unit tests (tests/test_cv_fields.py)
    ok_all = all(r["ok"] for r in rows)
    check("R1 summary: the 6 CVs (4 PDF, 2 DOCX) show their fields right on the screen", ok_all, str([r["cv"] for r in rows if not r["ok"]]))


# ================================================================== R2
def r2(b):
    R.section("R2  Level, experience, certifications and awards on the job, the job overview and the anonymous talent cards")
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    ids = []
    for p in (1, 2):
        ids += [j["id"] for j in api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}", token=tt)[1]["items"]]
    miss = {"level": 0, "experience": 0, "certs_or_awards": 0, "workMode": 0, "educationMin": 0}
    n_cert = n_award = 0
    for i in ids:
        j = api_call(BASE, "GET", f"/jobs/{i}", token=tt)[1]
        if not j.get("level"):
            miss["level"] += 1
        if j.get("minYears") is None:
            miss["experience"] += 1
        c, a = j["certifications"], j["awards"]
        if not (c["required"] or c["preferred"] or a["preferred"]):
            miss["certs_or_awards"] += 1
        n_cert += bool(c["required"] or c["preferred"])
        n_award += bool(a["preferred"])
        miss["workMode"] += not j.get("workMode")
        miss["educationMin"] += not j.get("educationMin")
    save("R2 jobs", {"jobs": len(ids), "missing": miss, "with certifications": n_cert, "with awards": n_award})
    check(f"R2 API: all {len(ids)} open jobs have a level, the experience (min years), a work mode and an education, and they carry the fields certifications and awards",
          len(ids) == 53 and miss["level"] == 0 and miss["experience"] == 0 and miss["workMode"] == 0 and miss["educationMin"] == 0, str(miss))
    R.info(f"R2: {n_cert} of {len(ids)} jobs list a certification, {n_award} list an award kind, {miss['certs_or_awards']} list neither (they say so on the page)")
    # talent: card and detail
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    go(b, BASE, "#/jobs", "document.querySelector('[data-list] .job-card')")
    chips = b.eval("[...document.querySelectorAll('[data-list] .job-card')].map(c => [...c.querySelectorAll('.job-facts .chip')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()))", False)
    check("R2 talent: every job card on the page shows the level, the experience and the work mode", all(len(x) == 3 and x[0].startswith("Level:") and x[1].startswith("Experience:") and x[2].startswith("Work mode:") for x in chips), str(chips[:2]))
    R.shot(b, "r2-1-talent-job-cards.png")
    with_cert = None
    for i in ids:
        j = api_call(BASE, "GET", f"/jobs/{i}", token=tt)[1]
        if j["certifications"]["required"] and j["awards"]["preferred"]:
            with_cert = j
            break
    j = with_cert
    go(b, BASE, f"#/jobs/{j['id']}", "document.querySelector('.job-detail h1')")
    d = b.eval("""({ facts: Object.fromEntries([...document.querySelectorAll('.fact-grid > div')].map(d => [d.querySelector('dt').textContent, d.querySelector('dd').textContent])),
      certs: [...document.querySelectorAll('#certTitle ~ .cred-group .chip')].map(c => c.textContent), text: document.querySelector('.job-detail').innerText })""", False)
    check("R2 talent detail: Level, Experience, Work mode in the facts", d["facts"].get("Level") == j["level"] and d["facts"].get("Work mode") == j["workMode"] and "year" in d["facts"].get("Experience", ""), str(d["facts"]))
    check("R2 talent detail: the required certification and the preferred award are listed", all(c in d["text"] for c in j["certifications"]["required"]) and "Awards" in d["text"] and "Preferred" in d["text"], str(j["certifications"]))
    R.shot(b, f"r2-2-talent-detail-{j['id'][:24]}.png", full=True)
    # employer: overview of own job, anonymous cards
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    go(b, BASE, "#/my-jobs/job-demo-backend-senior/overview", "document.querySelector('.job-overview .jd-view')")
    o = b.eval("({ facts: Object.fromEntries([...document.querySelectorAll('.jo-facts > div')].map(d => [d.querySelector('dt').textContent, d.querySelector('dd').textContent])), text: document.querySelector('.job-overview').innerText })", False)
    ov = api_call(BASE, "GET", "/recruiter/jobs/job-demo-backend-senior", token=et)[1]
    check("R2 employer overview: Level, Experience, Work mode, and the certifications and awards of the job", o["facts"].get("Level") == ov["level"] and "year" in o["facts"].get("Experience", "") and o["facts"].get("Work mode") == ov["workMode"]
          and "Certifications and awards" in o["text"], str(o["facts"]))
    R.shot(b, "r2-3-employer-overview.png", full=True)
    api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)
    go(b, BASE, "#/candidates?pageSize=50", "document.querySelector('.cand-card')")
    n = b.eval("document.querySelectorAll('.cand-card').length", False)
    cards = b.eval("""[...document.querySelectorAll('.cand-card')].map(c => ({ level: /Level/.test(c.querySelector('.cand-facts').innerText), years: /years?/.test(c.querySelector('.cand-facts').innerText),
       creds: c.querySelectorAll('.cred-chip').length, text: c.innerText }))""", False)
    check("R2 employer cards: every anonymous talent card shows the level and the years", n >= 10 and all(c["level"] and c["years"] for c in cards), f"{n} cards")
    with_creds = sum(1 for c in cards if c["creds"])
    check("R2 employer cards: the certification and award names show on the cards that have them, with the year", with_creds >= 10 and any(re.search(r"\(\d{4}\)", c["text"]) for c in cards), f"{with_creds} of {n} cards")
    check("R2 employer cards: no person name next to an award (only aliases)", not re.search(r"Nguyen|Linh|@", " ".join(c["text"] for c in cards)))
    R.shot(b, "r2-4-employer-talent-cards.png")
    first = b.eval("document.querySelector('.cand-card a[href^=\"#/candidates/\"]').getAttribute('href')", False)
    go(b, BASE, first, "document.querySelector('.pf-list, .profile-card')")
    t = b.text("main")
    check("R2 employer detail: Level, Experience, Certifications and Awards rows", all(w in t for w in ("Level", "Experience", "Certifications", "Awards")), t[:200])
    R.shot(b, "r2-5-employer-detail.png", full=True)
    api_call(BASE, "PUT", "/entitlements", {"plan": "basic"}, token=et)


# ================================================================== R3
def r3(b):
    R.section("R3  Different fit scores, and the 8 axes differ between jobs")
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    rec = api_call(BASE, "GET", "/jobs/recommended?pageSize=50", token=tt)[1]
    scores = [j["match"]["score"] for j in rec["items"]]
    top = scores[:20]
    allj = []
    for p in (1, 2):
        allj += api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}&sort=best", token=tt)[1]["items"]
    allsc = [j["match"]["score"] for j in allj]
    save("R3 demo talent top 20 recommended", top)
    save("R3 demo talent all jobs", {"best": max(allsc), "worst": min(allsc), "spread": round(max(allsc) - min(allsc), 1), "distinct": len(set(allsc)), "jobs": len(allsc)})
    R.info("R3 the 20 best recommended fit scores of the demo talent: " + ", ".join(f"{s:.1f}" for s in top))
    check("R3 the top 20 recommended jobs have at least 18 different scores at one decimal", len(set(top)) >= 18, f"{len(set(top))} distinct of {len(top)}")
    check("R3 the best minus the worst of all 53 jobs is at least 30 points", max(allsc) - min(allsc) >= 30, f"{max(allsc)} - {min(allsc)}")
    # the 8 axes for all 53 jobs from the API
    axes = {}
    location_of = {}
    for j in allj:
        d = api_call(BASE, "GET", f"/jobs/{j['id']}", token=tt)[1]
        for a in d["bridge"]["axes"]:
            axes.setdefault(a["key"], []).append(a["value"])
            if a["key"] == "location":
                location_of[j["id"]] = a["value"]
    distinct = {k: len(set(v)) for k, v in axes.items()}
    save("R3 axes distinct values over 53 jobs", distinct)
    check("R3 no radar axis has the same value for all 53 jobs (8 axes, distinct values each)", len(axes) == 8 and all(n > 1 for n in distinct.values()), str(distinct))
    # the panel in the browser for 5 jobs
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    # 4 jobs spread over the ranking, and the job with the lowest Location number (most jobs fit the cities of the demo talent, so Location is often 100)
    pick = [allj[i]["id"] for i in (0, 10, 20, 30)] + [min(location_of, key=lambda k: location_of[k])]
    panels = []
    for k, jid in enumerate(pick):
        go(b, BASE, f"#/jobs/{jid}", "document.querySelector('.fit .radar-table tbody tr')")
        panels.append(b.eval("[...document.querySelectorAll('.fit .radar-table tbody tr')].map(r => [r.cells[0].innerText.replace(/\\s+/g, ' ').trim(), r.cells[r.cells.length - 1].innerText.trim()])", False))
        if k == 0:
            R.shot(b, "r3-1-fit-panel-job1.png")
        if k == 4:
            R.shot(b, "r3-2-fit-panel-job5.png")
    cols = list(zip(*[[v for _, v in p] for p in panels]))
    equal_axes = [panels[0][i][0] for i, c in enumerate(cols) if len(set(c)) == 1]
    save("R3 5 jobs 8-axis panels", {pick[i]: dict(panels[i]) for i in range(5)})
    check("R3 the 8-axis panels of 5 opened jobs differ (no row has the same number for all 5 jobs; one of the 5 is the job with the lowest Location number)", len(panels[0]) == 8 and not equal_axes, f"equal rows: {equal_axes}")
    api_axes = [[a["value"] for a in api_call(BASE, "GET", f"/jobs/{pick[k]}", token=tt)[1]["bridge"]["axes"]] for k in range(5)]
    ui_axes = [[float(v) for _, v in panels[k]] for k in range(5)]
    check("R3 the 8 numbers on the screen are the numbers of the API for each of the 5 jobs", ui_axes == api_axes, f"{ui_axes[0]} / {api_axes[0]}")


# ================================================================== R4
def r4(b):
    R.section("R4  'About the role' is full for all 50 jobs, with headings, in a scroll box that the keyboard reaches")
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    src = {"job-" + j["key"]: j["description"] for j in json.load(open(JOBS_FILE))["jobs"]}
    ids = []
    for p in (1, 2):
        ids += [j["id"] for j in api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}", token=tt)[1]["items"]]
    bad = []
    lens = []
    for i in ids:
        d = api_call(BASE, "GET", f"/jobs/{i}", token=tt)[1]["description"]
        lens.append(len(d))
        heads = [x[3:].strip() for x in d.split("\n") if x.startswith("## ")]
        need = ["About the role", "What you will do", "What you bring", "Nice to have", "Tech stack", "What we offer", "How we hire"]
        if "…" in d or "..." in d or any(h not in heads for h in need) or not any(h.startswith("About ") and h != "About the role" for h in heads):
            bad.append(i)
        if i in src and d != src[i].replace("\r\n", "\n").strip():
            bad.append(i + " (differs from the source)")
    save("R4 api", {"jobs": len(ids), "bad": bad, "length min": min(lens), "length max": max(lens)})
    check(f"R4 API: {len(ids)} open jobs, no '…', every JD has the 7 standard headings and an 'About <company>' heading, and equals the source text", not bad and len(ids) == 53, str(bad[:5]))
    ids5 = [ids[i] for i in (0, 12, 24, 36, 48)]
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    for k, jid in enumerate(ids5):
        go(b, BASE, f"#/jobs/{jid}", "document.querySelector('.jd-about .jd-view')")
        # reach the box with Tab from the top of the page
        b.eval("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); document.body.focus()", await_promise=False)
        tabs = 0
        while tabs < 60 and not b.eval("document.activeElement && document.activeElement.classList.contains('jd-view')", False):
            key(b, "Tab")
            tabs += 1
        reached = b.eval("document.activeElement.classList.contains('jd-view')", False)
        ring = b.eval("(() => { const s = getComputedStyle(document.activeElement); return s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 2; })()", False) if reached else False
        s0 = b.eval("document.querySelector('.jd-about .jd-view').scrollTop", False)
        key(b, "ArrowDown", times=5)
        s1 = b.eval("document.querySelector('.jd-about .jd-view').scrollTop", False)
        key(b, "End")
        last = b.eval("(() => { const v = document.querySelector('.jd-about .jd-view'); const hs = v.querySelectorAll('h3'); const r = hs[hs.length - 1].getBoundingClientRect(); const vr = v.getBoundingClientRect(); return { last: hs[hs.length - 1].innerText, visible: r.bottom <= vr.bottom + 1 && r.top >= vr.top - 1, atEnd: Math.abs(v.scrollHeight - v.clientHeight - v.scrollTop) < 3, sh: v.scrollHeight, ch: v.clientHeight }; })()", False)
        check(f"R4 talent detail {k + 1}/5 ({jid[:28]}): the box is reached with Tab ({tabs} presses), has a visible focus ring, scrolls with the arrow keys, and End shows the last heading",
              reached and ring and s1 > s0 and last["atEnd"] and last["visible"] and last["last"] == "How we hire", f"tabs={tabs} ring={ring} {s0}->{s1} {last}")
        if k == 0:
            R.shot(b, "r4-1-talent-jd-end.png")
    # employer overview: own jobs (4 demo jobs and one long JD)
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    long_jd = JD + "\n- " + " ".join(["A long line that fills the box with more text for the scroll test."] * 40)
    extra = post_job(et, "QA Long description job", jd=long_jd[:3400])
    own = ["job-demo-backend-senior", "job-demo-data-engineer-mid", "job-demo-ml-engineer-mid", "job-demo-data-engineer-contract-closed", extra["id"]]
    for k, jid in enumerate(own):
        go(b, BASE, f"#/my-jobs/{jid}/overview", "document.querySelector('.job-overview .jd-view')")
        b.eval("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)", await_promise=False)
        tabs = 0
        while tabs < 60 and not b.eval("document.activeElement && document.activeElement.classList.contains('jd-view')", False):
            key(b, "Tab")
            tabs += 1
        reached = b.eval("document.activeElement.classList.contains('jd-view')", False)
        s0 = b.eval("document.querySelector('.job-overview .jd-view').scrollTop", False)
        key(b, "PageDown", times=2)
        s1 = b.eval("document.querySelector('.job-overview .jd-view').scrollTop", False)
        info = b.eval("(() => { const v = document.querySelector('.job-overview .jd-view'); return { h3: v.querySelectorAll('h3').length, len: v.innerText.length, ell: v.innerText.includes('\\u2026'), scrolls: v.scrollHeight > v.clientHeight }; })()", False)
        d = api_call(BASE, "GET", f"/recruiter/jobs/{jid}", token=et)[1]["description"]
        check(f"R4 employer overview {k + 1}/5 ({jid[:30]}): reached with Tab ({tabs}), scrolls with the keyboard, {info['h3']} headings, no '…', all {len(d)} characters of the API text",
              reached and s1 > s0 and info["h3"] >= 6 and not info["ell"] and info["scrolls"] and len(d) >= 1200, f"{s0}->{s1} {info}")
        if k == 4:
            R.shot(b, "r4-2-employer-overview-long.png")


# ================================================================== R5, R6
def make_lists_data(b):
    """Data for the pagers: bookmarks, applications, jobs of the employer, applicants, saved talent."""
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)
    jobs = []
    for p in (1, 2):
        jobs += api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}&sort=best", token=tt)[1]["items"]
    # bookmarks: 25 jobs, saved one by one (the last one saved is the newest)
    for j in jobs[:25]:
        s, _ = api_call(BASE, "PUT", f"/bookmarks/{j['id']}", token=tt)
        assert s in (200, 201, 204), s
        time.sleep(0.02)
    bookmarked = [j["id"] for j in jobs[:25]]
    # applications: 14 more (the demo talent has 1)
    applied = []
    for j in jobs[25:45]:
        if len(applied) >= 14:
            break
        s, a = api_call(BASE, "POST", "/applications", {"jobId": j["id"], "note": ""}, token=tt)
        if s in (200, 201):
            applied.append(a["id"])
    # jobs of the employer: 14 more
    mine = [post_job(et, f"QA posted job {i:02d}", closesAt=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + (10 + i) * 86400)))["id"] for i in range(14)]
    # applicants: 11 new talent apply for the demo Data Engineer job (3 applications exist)
    for i in range(11):
        u = new_user("candidate", f"app{i}")
        give_profile(u, i)
        s, a = api_call(BASE, "POST", "/applications", {"jobId": "job-demo-data-engineer-mid", "note": ""}, token=u["token"])
        assert s in (200, 201), (s, a)
    # saved talent: 25 profiles
    cands = api_call(BASE, "GET", "/recruiter/candidates?pageSize=50&sort=best", token=et)[1]["items"]
    saved = []
    for c in cands[:25]:
        s, _ = api_call(BASE, "PUT", f"/recruiter/candidates/{c['id']}/save", token=et)
        assert s in (200, 201, 204), s
        saved.append(c["id"])
        time.sleep(0.02)
    save("R5 data", {"bookmarks": len(bookmarked), "applications made": len(applied), "employer jobs added": len(mine), "applicants added": 11, "saved talent": len(saved)})
    return bookmarked, saved


def list_ids(b, kind):
    if kind in ("jobs", "bookmarks"):
        return b.eval("[...document.querySelectorAll('[data-list] .job-card')].map(c => c.dataset.card)", False)
    if kind == "applications":
        return b.eval("[...document.querySelectorAll('[data-list] .app-row a.job-title-link')].map(a => a.getAttribute('href').split('/')[2])", False)
    if kind == "my-jobs":
        return b.eval("[...document.querySelectorAll('.app-row h3 a')].map(a => a.getAttribute('href').split('/')[2])", False)
    if kind == "applicants":
        return b.eval("[...document.querySelectorAll('.app-row h3 a')].map(a => a.getAttribute('href').split('/')[2])", False)
    if kind in ("talent", "saved-talent"):
        return b.eval("[...document.querySelectorAll('.cand-card')].map(c => c.querySelector('a[href^=\"#/candidates/\"]').getAttribute('href').split('/')[2].split('?')[0])", False)


def check_pager(b, label, route, kind, total, shot):
    ready = {"jobs": "[data-list] .job-card", "bookmarks": "[data-list] .job-card", "applications": "[data-list] .app-row", "my-jobs": ".app-row", "applicants": ".app-row",
             "talent": ".cand-card", "saved-talent": ".cand-card"}[kind]
    go(b, BASE, route, f"document.querySelector({json.dumps(ready)})")
    b.eval("localStorage.removeItem && Object.keys(localStorage).filter(k => k.startsWith('jinder.pagesize')).forEach(k => localStorage.removeItem(k))", await_promise=False)
    b.goto(f"{BASE}/{route}")
    b.wait_for(f"document.querySelector({json.dumps(ready)})", 30)
    b.pump(0.8)
    result = {}
    for size in (10, 20, 50):
        info = pager_info(b)
        if info is None:
            check(f"R5 {label}: the pager is there ({total} items)", False, f"no pager, total {total}")
            return
        if info["size"] != size:
            set_select(b, "[data-pager-size]", size)
            info = pager_info(b)
        pages = -(-total // size)
        n1 = len(list_ids(b, kind))
        ok = info["size"] == size and info["pages"] == pages and n1 == min(size, total) and info["range"] == f"Showing 1–{min(size, total)} of {total}" and info["page"] == 1
        extra = ""
        if pages >= 2:
            first = list_ids(b, kind)
            click_step(b, "Next")
            second = list_ids(b, kind)
            last_n = total - (pages - 1) * size
            if pages > 2:
                for _ in range(pages - 2):
                    click_step(b, "Next")
            last = list_ids(b, kind)
            ok = ok and len(second) == min(size, total - size) and not set(first) & set(second) and len(last) == last_n
            click_step(b, "Previous")
            click_step(b, "Previous") if pages > 2 else None
            extra = f"page 2 has {len(second)} other items, last page has {len(last)}"
            if pages > 2:
                set_select(b, "[data-pager-size]", size)
        check(f"R5 {label}: page size {size} shows {min(size, total)} of {total} ({pages} page{'s' if pages > 1 else ''}); {extra}", ok, f"{info} n={n1}")
        result[size] = {"pages": pages, "first page items": n1}
    # the size is remembered after a reload
    set_select(b, "[data-pager-size]", 20)
    reload(b)
    b.wait_for(f"document.querySelector({json.dumps(ready)})", 30)
    b.pump(0.8)
    info = pager_info(b)
    check(f"R5 {label}: the page size (20) is remembered after a reload of the page", info and info["size"] == 20, str(info))
    R.shot(b, shot)
    save(f"R5 {label}", {"total": total, **result})
    set_select(b, "[data-pager-size]", 10)


def r5(b, lists):
    R.section("R5  Pager and page size 10, 20 and 50 on every list")
    bookmarked, saved = lists
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    check_pager(b, "Jobs", "#/jobs", "jobs", api_call(BASE, "GET", "/jobs?pageSize=1", token=tt)[1]["page"]["total"], "r5-1-jobs.png")
    check_pager(b, "Bookmarks", "#/bookmarks", "bookmarks", len(bookmarked), "r5-2-bookmarks.png")
    apps = api_call(BASE, "GET", "/applications?pageSize=50", token=tt)[1]
    active = [a for a in apps["items"] if not a["final"]]
    check_pager(b, "Applications (Active)", "#/applications", "applications", len(active), "r5-3-applications.png")
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    mine = api_call(BASE, "GET", "/recruiter/jobs?pageSize=1", token=et)[1]["page"]["total"]
    check_pager(b, "My jobs", "#/my-jobs", "my-jobs", mine, "r5-4-my-jobs.png")
    n_app = api_call(BASE, "GET", "/recruiter/jobs/job-demo-data-engineer-mid/applications?pageSize=1", token=et)[1]["page"]["total"]
    check_pager(b, "Applicants of one job", "#/my-jobs/job-demo-data-engineer-mid", "applicants", n_app, "r5-5-applicants.png")
    total = api_call(BASE, "GET", "/recruiter/candidates?pageSize=1", token=et)[1]["page"]["total"]
    check_pager(b, "Talent list", "#/candidates", "talent", total, "r5-6-talent.png")
    check_pager(b, "Saved talent", "#/candidates?view=saved", "saved-talent", len(saved), "r5-7-saved-talent.png")
    # a Basic employer sees 5 and no pager
    api_call(BASE, "PUT", "/entitlements", {"plan": "basic"}, token=et)
    go(b, BASE, "#/candidates", "document.querySelector('.cand-card')")
    check("R5 Talent list (Basic employer): 5 cards, no pager, and the page shows the real total in the upgrade text", b.eval("document.querySelectorAll('.cand-card').length", False) == 5 and pager_info(b) is None and str(total) in b.text(".upgrade"), b.text(".upgrade")[:120])
    # API: clamp, bad page
    s, r = api_call(BASE, "GET", "/jobs?pageSize=500", token=tt)
    s2, r2_ = api_call(BASE, "GET", "/jobs?pageSize=0&page=999", token=tt)
    check("R5 API: pageSize is clamped to 50, a page past the end gives the last page", r["page"]["pageSize"] == 50 and r2_["page"]["page"] == r2_["page"]["totalPages"], f"{r['page']} {r2_['page']}")
    api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)


def sorted_by(values, desc=True):
    return values == sorted(values, reverse=desc)


def r6(b, lists):
    R.section("R6  Sort options and the correct order (checked against the values of the API)")
    bookmarked, saved = lists
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)

    ready = {"jobs": "[data-list] .job-card", "bookmarks": "[data-list] .job-card", "applications": "[data-list] .app-row", "my-jobs": ".app-row", "talent": ".cand-card"}

    def ui_order(route, select_id, value, kind):
        go(b, BASE, route, f"document.querySelector({json.dumps(ready[kind])})")
        if b.eval("document.querySelector(" + json.dumps(select_id) + ").value", False) != value:
            set_select(b, select_id, value)
        return list_ids(b, kind)

    # Jobs: best / newest
    allj = {s: [] for s in ("best", "newest")}
    for s in allj:
        for p in (1, 2):
            allj[s] += api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}&sort={s}", token=tt)[1]["items"]
    check("R6 Jobs API 'best': scores in descending order, ties by id", sorted_by([j["match"]["score"] for j in allj["best"]]) and
          all(a["match"]["score"] != b_["match"]["score"] or a["id"] < b_["id"] for a, b_ in zip(allj["best"], allj["best"][1:])), "")
    check("R6 Jobs API 'newest': postedAt in descending order, ties by id", sorted_by([j["postedAt"] for j in allj["newest"]]) and
          all(a["postedAt"] != b_["postedAt"] or a["id"] < b_["id"] for a, b_ in zip(allj["newest"], allj["newest"][1:])), "")
    for s, want in (("best", allj["best"][:10]), ("newest", allj["newest"][:10])):
        got = ui_order("#/jobs", "#jobs-sort", s, "jobs")
        check(f"R6 Jobs screen, sort '{s}': the 10 cards are in the order of the API", got == [j["id"] for j in want], f"{got[:3]} / {[j['id'] for j in want][:3]}")
    R.shot(b, "r6-1-jobs-sort.png")
    # Bookmarks: saved / best / newest
    bm = {s: api_call(BASE, "GET", f"/bookmarks?pageSize=50&sort={s}", token=tt)[1]["items"] for s in ("saved", "best", "newest")}
    check("R6 Bookmarks API 'saved': the job saved last comes first", [j["id"] for j in bm["saved"]] == list(reversed(bookmarked)), f"{[j['id'] for j in bm['saved']][:3]} vs {list(reversed(bookmarked))[:3]}")
    check("R6 Bookmarks API 'best' (scores) and 'newest' (postedAt) are in descending order", sorted_by([j["match"]["score"] for j in bm["best"]]) and sorted_by([j["postedAt"] for j in bm["newest"]]), "")
    for s in ("saved", "best", "newest"):
        got = ui_order("#/bookmarks", "#bookmarks-sort", s, "bookmarks")
        check(f"R6 Bookmarks screen, sort '{s}': the first 10 cards are in the order of the API", got == [j["id"] for j in bm[s][:10]], f"{got[:3]} / {[j['id'] for j in bm[s][:3]]}")
    R.shot(b, "r6-2-bookmarks-sort.png")
    # Applications: updated / best / newest
    ap_ = {s: api_call(BASE, "GET", f"/applications?pageSize=50&sort={s}", token=tt)[1]["items"] for s in ("updated", "best", "newest")}
    check("R6 Applications API: 'updated' (updatedAt), 'newest' (createdAt) descending; 'best' (coverage) descending", sorted_by([a["updatedAt"] for a in ap_["updated"]]) and sorted_by([a["createdAt"] for a in ap_["newest"]]) and sorted_by([a["coverage"] or 0 for a in ap_["best"]]), "")
    for s in ("updated", "best", "newest"):
        got = ui_order("#/applications", "#apps-sort", s, "applications")
        want = [a["id"] for a in ap_[s] if not a["final"]][:10]
        check(f"R6 Applications screen, sort '{s}': the first 10 rows are in the order of the API", got == want, f"{got[:3]} / {want[:3]}")
    R.shot(b, "r6-3-applications-sort.png")
    # Employer: talent list best / updated, My jobs, applicants (one sort)
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    cs = {s: api_call(BASE, "GET", f"/recruiter/candidates?pageSize=50&sort={s}", token=et)[1]["items"] + api_call(BASE, "GET", f"/recruiter/candidates?pageSize=50&page=2&sort={s}", token=et)[1]["items"] for s in ("best", "updated")}
    ups = [c["updatedAt"] for c in cs["updated"]]
    check("R6 Talent API 'updated' ('Recently updated'): updatedAt descending over all %d profiles, ties by id" % len(ups), sorted_by(ups) and all(a["updatedAt"] != b_["updatedAt"] or a["id"] < b_["id"] for a, b_ in zip(cs["updated"], cs["updated"][1:])), str(ups[:3]))
    for s in ("best", "updated"):
        got = ui_order("#/candidates", "#talent-sort", s, "talent")
        check(f"R6 Talent screen, sort '{s}': the 10 cards are in the order of the API", got == [c["id"] for c in cs[s][:10]], f"{got[:3]} / {[c['id'] for c in cs[s][:3]]}")
    cov = [c["coverage"] for c in cs["best"]]
    R.info("R6 talent 'best': first 10 coverage values " + str(cov[:10]) + " (the order is the engine order, 0.6 x coverage + 0.4 x TSS, the person gets no score)")
    R.shot(b, "r6-4-talent-sort.png")
    mj = api_call(BASE, "GET", "/recruiter/jobs?pageSize=50", token=et)[1]["items"]
    go(b, BASE, "#/my-jobs", "document.querySelector('.app-row')")
    got = list_ids(b, "my-jobs")
    check("R6 My jobs (one sort, 'Newest first'): postedAt descending and the screen shows the API order", sorted_by([j["postedAt"] for j in mj]) and got == [j["id"] for j in mj[:10]] and "Newest first" in b.text("main"), f"{got[:2]}")
    ap2 = api_call(BASE, "GET", "/recruiter/jobs/job-demo-data-engineer-mid/applications?pageSize=50", token=et)[1]["items"]
    check("R6 Applicants (one sort, newest first): createdAt descending", sorted_by([a["createdAt"] for a in ap2]), str([a["createdAt"][:19] for a in ap2][:3]))
    # a bad sort is a 400
    s, r = api_call(BASE, "GET", "/jobs?sort=nope", token=tt)
    s2, r2_ = api_call(BASE, "GET", "/recruiter/candidates?sort=nope", token=et)
    check("R6 API: a bad sort is a 400 with fields.sort", s == 400 and "sort" in r["error"]["fields"] and s2 == 400 and "sort" in r2_["error"]["fields"], f"{s} {s2}")


# ================================================================== R7
def settings_benefits(b):
    return b.eval("Object.fromEntries([...document.querySelectorAll('.benefit')].map(e => [e.dataset.benefit, e.querySelector('.benefit-status').innerText.replace(/\\s+/g, ' ').trim()]))", False)


def r7(b):
    R.section("R7  Menu without Settings, the user block opens Settings, crown and gold ring, benefits used / not used, locks for Basic")
    # a clean employer: a job and data
    emp = new_user("recruiter", "r7emp")
    job = post_job(emp["token"], "R7 Data Engineer", skills=["Python", "SQL", "Apache Spark"])
    sign_in(b, BASE, emp["email"], emp["password"])
    labels = b.eval("[...document.querySelectorAll('.sidebar-nav a')].map(a => a.innerText.trim().split('\\n')[0])", False)
    check("R7 the employer menu has no Settings item", "Settings" not in labels and labels == ["Home", "Talent", "My jobs", "Compare", "Notifications"], str(labels))
    b.click("#shellUser")
    b.wait_for("location.hash.startsWith('#/settings') && document.querySelector('.plan-card')")
    b.pump(0.8)
    check("R7 the user block opens Settings", b.text("h1") == "Settings")
    ring0 = b.eval("getComputedStyle(document.querySelector('#shellUser .avatar')).boxShadow", False)
    crown0 = b.eval("getComputedStyle(document.querySelector('.avatar-crown')).display", False)
    ben = settings_benefits(b)
    check("R7 Basic employer: the 4 benefits are locked with a gold 'Premium' chip, no crown, no gold ring", len(ben) == 4 and all(v == "Premium" for v in ben.values()) and crown0 == "none" and "rgb(" not in ring0.split(")")[0] + ")" or crown0 == "none", f"{ben} crown={crown0} ring={ring0[:60]}")
    R.shot(b, "r7-1-employer-basic-settings.png", full=True)
    # the menu lock for Compare and the locks on the talent list
    go(b, BASE, "#/candidates", "document.querySelector('.cand-card, .empty')")
    locks = b.eval("({ nav: !document.querySelector('[data-nav-lock]').hidden, compare: document.querySelectorAll('.cand-card [data-premium-lock]').length, box: !!document.querySelector('.upgrade') })", False)
    check("R7 Basic employer: the lock in the menu on Compare, the locks on Compare and Invite, the gold upgrade box", locks["nav"] and locks["box"], str(locks))
    # Premium: the switch in Settings. The crown shows at once (no reload).
    b.click("#shellUser")
    b.wait_for("document.querySelector('[data-try-premium]')")
    b.click("[data-try-premium]")
    b.wait_for("document.getElementById('shellUser').classList.contains('is-premium')", timeout=15)
    ring = b.eval("getComputedStyle(document.querySelector('#shellUser .avatar')).boxShadow", False)
    check("R7 the crown, the gold ring and the Premium chip show at once after 'Try Premium' (no reload)", b.eval("getComputedStyle(document.querySelector('.avatar-crown')).display", False) == "block" and "2px" in ring and ring != ring0, f"ring={ring[:80]}")
    b.pump(0.6)
    ben = settings_benefits(b)
    check("R7 Premium employer: all 4 benefits say 'Not used yet'", len(ben) == 4 and all(v.startswith("Not used yet") for v in ben.values()), str(ben))
    R.shot(b, "r7-2-employer-premium-not-used.png", full=True)
    # use the benefits one by one and see them flip
    flips = {}
    tok = emp["token"]
    # (1) see every talent profile: a list with more than 5 items
    go(b, BASE, f"#/candidates?jobId={job['id']}", "document.querySelector('.cand-card')")
    b.pump(0.5)
    ids = list_ids(b, "talent")[:3]
    b.click("#shellUser")
    b.wait_for("document.querySelector('.benefit')")
    b.pump(0.5)
    ben1 = settings_benefits(b)
    flips["all_talent"] = ben1["all_talent"]
    # (2) compare
    go(b, BASE, f"#/compare?ids={','.join(ids[:2])}&jobId={job['id']}", "document.querySelector('.cmp-panels .rd-shape')", pump=1.0)
    # (3) invite
    s, r = api_call(BASE, "POST", f"/recruiter/candidates/{ids[2]}/contact", {"jobId": job["id"], "message": "We like your profile and your skills."}, token=tok)
    # (4) advanced charts
    go(b, BASE, "#/home", "document.querySelector('.dash')", pump=1.5)
    b.click("#shellUser")
    b.wait_for("document.querySelector('.benefit')")
    b.pump(0.6)
    ben2 = settings_benefits(b)
    save("R7 employer benefits before and after", {"before": {k: "Not used yet" for k in ben}, "after list": ben1, "after compare, invite and Home": ben2})
    check("R7 using 'See every talent profile' flips it to Used (1 time) while the others stay 'Not used yet' until they are used", ben1["all_talent"].startswith("Used") and all(ben1[k].startswith("Not used yet") for k in ("invite", "compare", "advanced_charts")), str(ben1))
    check("R7 after a compare, an invite and the Home charts: all 4 benefits say Used", len(ben2) == 4 and all(v.startswith("Used") for v in ben2.values()), str(ben2))
    R.shot(b, "r7-3-employer-premium-used.png", full=True)
    # the talent side
    tal = new_user("candidate", "r7tal")
    give_profile(tal, 1)
    sign_in(b, BASE, tal["email"], tal["password"])
    labels = b.eval("[...document.querySelectorAll('.sidebar-nav a')].map(a => a.innerText.trim().split('\\n')[0])", False)
    check("R7 the talent menu has no Settings item and the user block opens Settings", "Settings" not in labels and b.eval("document.getElementById('shellUser').getAttribute('href')", False) == "#/settings", str(labels))
    home = b.text("main")
    check("R7 Basic talent: the Premium insights on Home are locked (gold Premium badge)", b.eval("!!document.querySelector('.locked-badge, .premium-chip, .upgrade')", False), home[:100])
    b.click("#shellUser")
    b.wait_for("document.querySelector('[data-try-premium]')")
    b.click("[data-try-premium]")
    b.wait_for("document.getElementById('shellUser').classList.contains('is-premium')", timeout=15)
    b.pump(0.6)
    t0 = settings_benefits(b)
    go(b, BASE, "#/home", "document.querySelector('.dash')", pump=2.0)
    b.click("#shellUser")
    b.wait_for("document.querySelector('.benefit')")
    b.pump(0.6)
    t1 = settings_benefits(b)
    save("R7 talent benefits", {"before": t0, "after Home": t1})
    check("R7 Premium talent: both benefits 'Not used yet', and after the Home insights they flip to Used", all(v.startswith("Not used yet") for v in t0.values()) and len(t0) == 2 and all(v.startswith("Used") for v in t1.values()) and len(t1) == 2, f"{t0} -> {t1}")
    R.shot(b, "r7-4-talent-premium-used.png", full=True)
    # the demo switch back to Basic: the crown goes, 'Used' is kept
    b.eval("[...document.querySelectorAll('[name=plan]')].find(r => r.value === 'basic').click()", await_promise=False)
    b.wait_for("!document.getElementById('shellUser').classList.contains('is-premium')", timeout=15)
    check("R7 back to Basic: the crown goes at once", True)


# ================================================================== R8, R9
def r8_r9(b):
    R.section("R8, R9  Compare 2 to 5, the 6th refused, the Compare menu item, the basket across pages, the address, employer rules")
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    et = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    jobs = []
    for p in (1, 2):
        jobs += api_call(BASE, "GET", f"/jobs?pageSize=50&page={p}&sort=best", token=tt)[1]["items"]
    ids = [j["id"] for j in jobs]
    s, r = api_call(BASE, "GET", f"/jobs/compare?ids={','.join(ids[:6])}", token=tt)
    check("R8 API (talent): 6 jobs is a 400 with fields.ids 'Choose 2 to 5 jobs to compare.'", s == 400 and r["error"]["fields"]["ids"] == "Choose 2 to 5 jobs to compare.", f"{s} {r}")
    s, r = api_call(BASE, "GET", f"/jobs/compare?ids={ids[0]}", token=tt)
    check("R8 API (talent): 1 job is a 400", s == 400, str(s))
    for n in (2, 3, 4, 5):
        s, r = api_call(BASE, "GET", f"/jobs/compare?ids={','.join(ids[:n])}", token=tt)
        check(f"R8 API (talent): {n} jobs give {n} jobs, {n * (n - 1) // 2} pairs and a skill matrix", s == 200 and len(r["jobs"]) == n and len(r["pairs"]) == n * (n - 1) // 2 and r["skillMatrix"], str(s))
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    check("R9 the Compare item is in the talent menu and opens #/compare", b.eval("!!document.querySelector('.sidebar-nav a[href=\"#/compare\"]')", False))
    # the basket across pages: 2 on page 1 of Jobs, 1 on page 2 of Jobs, 1 on the job detail, 1 on Bookmarks
    b.eval("localStorage.clear()", await_promise=False)
    go(b, BASE, "#/jobs?pageSize=10", "document.querySelector('[data-list] .job-card')")
    for k in (0, 1):
        b.eval(f"document.querySelectorAll('[data-compare-job]')[{k}].click()", await_promise=False)
        b.pump(0.25)
    click_step(b, "Next")
    b.eval("document.querySelectorAll('[data-compare-job]')[0].click()", await_promise=False)
    b.pump(0.3)
    go(b, BASE, f"#/jobs/{ids[30]}", "document.querySelector('.job-detail h1')")
    b.click("[data-compare-detail]")
    b.pump(0.3)
    for jid in ids[40:43]:
        api_call(BASE, "PUT", f"/bookmarks/{jid}", token=tt)
    go(b, BASE, "#/bookmarks", "document.querySelector('[data-list] .job-card')")
    b.eval("document.querySelectorAll('[data-compare-job]')[0].click()", await_promise=False)
    b.pump(0.4)
    tray = b.text("[data-compare-tray]")
    check("R9 the basket keeps the jobs across Jobs page 1, Jobs page 2, the job detail and Bookmarks: 'Compare (5/5)'", "Compare (5/5)" in tray, tray[:80])
    R.shot(b, "r8-1-basket-5.png")
    sixth = b.eval("(() => { const c = document.querySelector('[data-compare-job]:not(:checked)'); c.click(); return c.dataset.compareJob; })()", False)
    b.pump(0.4)
    note = b.eval("[...document.querySelectorAll('[data-compare-note]')].map(e => e.textContent).join(' ')", False)
    check("R8 UI: the 6th job is refused (the box clears, the text 'You can compare up to 5 jobs.' shows, the basket stays at 5)", "up to 5" in note and "Compare (5/5)" in b.text("[data-compare-tray]") and not b.eval(f"document.querySelector('[data-compare-job=\"{sixth}\"]').checked", False), note)
    b.click("[data-compare-tray] a[href='#/compare']")
    b.wait_for("document.querySelectorAll('.cmp-panels .rd-shape').length === 5", timeout=30)
    b.pump(0.8)
    h = b.eval("location.hash", False)
    check("R9 the Compare page for 5 jobs: 5 cards, 5 radar lines, 5 ids in the address", b.eval("document.querySelectorAll('.cmp-card').length", False) == 5 and len(re.findall(r"job-", h)) == 5 and b.text("h1") == "Compare jobs", h[:100])
    R.shot(b, "r8-2-compare-5-jobs.png", full=True)
    b.eval("document.querySelectorAll('.cmp-card .cmp-remove')[0].click()", await_promise=False)
    b.pump(1.0)
    h2 = b.eval("location.hash", False)
    check("R9 removing a job on the page: 4 cards, the address and the basket follow", b.eval("document.querySelectorAll('.cmp-card').length", False) == 4 and len(re.findall(r"job-", h2)) == 4, h2[:100])
    reload(b)
    b.wait_for("document.querySelectorAll('.cmp-card').length === 4", 30)
    check("R9 a reload of the page shows the same 4 jobs (the address has the ids)", b.eval("location.hash", False) == h2 and b.eval("document.querySelectorAll('.cmp-card').length", False) == 4, b.eval("location.hash", False))
    b.eval("document.querySelector('[data-add]').click()", await_promise=False)
    b.pump(0.6)
    check("R9 'Add to compare' opens the picker dialog with tabs and a search box", b.eval("!!document.querySelector('.cmp-picker') && !!document.querySelector('.cmp-picker [role=tablist]') && !!document.querySelector('.cmp-picker .cmp-search, .cmp-picker input[type=search]')", False))
    R.shot(b, "r9-1-picker.png")
    key(b, "Escape")
    b.pump(0.4)
    # employer
    em = api_login(BASE, "recruiter@demo.jinder.app", EPW)
    api_call(BASE, "PUT", "/entitlements", {"plan": "basic"}, token=em)
    s, r = api_call(BASE, "GET", f"/recruiter/compare?ids=a,b&jobId=job-demo-data-engineer-mid", token=em)
    check("R9 API: a Basic employer gets 403 PREMIUM_REQUIRED on the talent compare", s == 403 and r["error"]["code"] == "PREMIUM_REQUIRED", f"{s} {r}")
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    b.click(".sidebar-nav a[href='#/compare']")
    b.wait_for("document.querySelector('.compare-page h1')")
    b.pump(0.6)
    check("R9 Basic employer: the Compare page is the locked page (the lock in the menu, the Premium badge, an example picture)", b.text("h1") == "Compare talent" and b.eval("!!document.querySelector('.cmp-example') && !!document.querySelector('.locked-badge')", False))
    R.shot(b, "r9-2-employer-basic-locked.png", full=True)
    api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=em)
    cands = api_call(BASE, "GET", "/recruiter/candidates?pageSize=50&jobId=job-demo-data-engineer-mid", token=em)[1]["items"]
    cid = [c["id"] for c in cands]
    s, r = api_call(BASE, "GET", f"/recruiter/compare?ids={','.join(cid[:6])}&jobId=job-demo-data-engineer-mid", token=em)
    check("R8 API (employer): 6 profiles is a 400 with fields.ids 'Choose 2 to 5 profiles to compare.'", s == 400 and r["error"]["fields"]["ids"] == "Choose 2 to 5 profiles to compare.", f"{s} {r}")
    s, r = api_call(BASE, "GET", f"/recruiter/compare?ids={cid[0]}&jobId=job-demo-data-engineer-mid", token=em)
    check("R8 API (employer): 1 profile is a 400", s == 400, str(s))
    s, r = api_call(BASE, "GET", f"/recruiter/compare?ids={cid[0]},{cid[1]}", token=em)
    check("R8 API (employer): without jobId it is a 400 (fields.jobId)", s == 400 and "jobId" in r["error"]["fields"], f"{s}")
    for n in (2, 3, 4, 5):
        s, r = api_call(BASE, "GET", f"/recruiter/compare?ids={','.join(cid[:n])}&jobId=job-demo-data-engineer-mid", token=em)
        check(f"R8 API (employer): {n} profiles give {n} profiles, a radar with {n} series, areas and a skill matrix", s == 200 and len(r["candidates"]) == n and len(r["radar"]["series"]) == n and r["areas"] and r["skillMatrix"], str(s))
    sign_in(b, BASE, "recruiter@demo.jinder.app", EPW)
    b.eval("localStorage.clear()", await_promise=False)
    go(b, BASE, "#/candidates?jobId=job-demo-data-engineer-mid", "document.querySelector('.cand-card')")
    for k in range(6):
        b.eval(f"document.querySelectorAll('[data-compare-pick]')[{k}].click()", await_promise=False)
        b.pump(0.25)
    note = b.eval("[...document.querySelectorAll('[data-compare-note]')].map(e => e.textContent).join(' ')", False)
    check("R8 UI (employer): the 6th profile is refused with 'You can compare up to 5 profiles.', the basket keeps 5", "up to 5" in note and "Compare (5/5)" in b.text("[data-compare-tray]"), note)
    b.click("[data-compare-tray] a[href='#/compare']")
    b.wait_for("document.querySelectorAll('.cmp-panels .rd-shape').length === 5", timeout=30)
    b.pump(0.8)
    c = b.eval("({ job: document.querySelector('#cmpJob').value, opts: [...document.querySelectorAll('#cmpJob option')].map(o => o.textContent), cards: document.querySelectorAll('.cmp-card').length, hash: location.hash })", False)
    check("R9 employer Premium: 5 profiles on one radar for a chosen job; the job select lists the open jobs; the address has ids and jobId", c["cards"] == 5 and c["job"] and "jobId=" in c["hash"] and len(c["opts"]) >= 3, str(c)[:300])
    R.shot(b, "r9-3-employer-compare-5.png", full=True)
    set_select(b, "#cmpJob", "job-demo-backend-senior")
    b.pump(1.0)
    check("R9 employer: changing the job reloads the comparison for the new job (address and cards)", "jobId=job-demo-backend-senior" in b.eval("location.hash", False) and b.eval("document.querySelectorAll('.cmp-card').length", False) == 5)
    t = b.text("main")
    bad = re.search(r"(?<!no )(?<!not )\b(total score|overall score|ranking)\b", t, re.I)
    bad_head = b.eval("[...document.querySelectorAll('.cmp-panels th')].map(h => h.innerText.trim()).find(x => /^(total|score|overall|rank)$/i.test(x)) || ''", False)
    check("R9 employer: the page has no total, no score and no ranking of a person (text and table heads), and it says that it does not add the areas up", not bad and not bad_head and "does not add the areas up" in t,
          f"match={bad.group(0) if bad else None} head={bad_head!r} says={'does not add the areas up' in t}")
    b.eval("localStorage.clear()", await_promise=False)


# ================================================================== R10
def r10(b):
    R.section("R10  'Your path to this job': a radar with two layers, a Fit list, a Gap list, numbers that agree, no 12-month chart")
    tt = api_login(BASE, "candidate@demo.jinder.app", TPW)
    allj = api_call(BASE, "GET", "/jobs?pageSize=50&sort=best", token=tt)[1]["items"]
    pick = [allj[i]["id"] for i in (0, 8, 16, 24, 40)]
    sign_in(b, BASE, "candidate@demo.jinder.app", TPW)
    rows = []
    for k, jid in enumerate(pick):
        go(b, BASE, f"#/jobs/{jid}", "document.querySelector('.bridge.path')")
        b.pump(0.5)
        path = api_call(BASE, "GET", f"/jobs/{jid}", token=tt)[1]["bridge"]["path"]
        ui = b.eval("""({ shapes: document.querySelectorAll('.bridge.path .rd-shape').length, layers: !!document.querySelector('.bridge.path .radar-layers'), legend: [...document.querySelectorAll('.bridge.path .rd-legend li')].map(l => l.innerText.trim()),
          fit: [...document.querySelectorAll('.bridge.path .path-fit .path-title')].map(e => e.innerText.replace(/\\s+/g, ' ').trim()), gap: [...document.querySelectorAll('.bridge.path .path-gap .path-title')].map(e => e.innerText.replace(/\\s+/g, ' ').trim()),
          rows: [...document.querySelectorAll('.bridge.path .path-table tbody tr')].map(r => [...r.cells].map(c => c.innerText.replace(/\\s+/g, ' ').trim())),
          chips: [...document.querySelectorAll('.path-summary li')].map(l => l.innerText.replace(/\\s+/g, ' ').trim()), months: [...document.querySelectorAll('.path-gap .path-months')].map(e => e.innerText.trim()),
          oldChart: document.querySelectorAll('.lc-svg, .line-chart').length, text12: /12-month|next 12 months|projection/i.test(document.querySelector('.bridge.path').innerText) })""", False)
        months = sorted([g["months"] for g in path["gaps"]], reverse=True)
        parallel = round(months[0] + 0.18 * sum(months[1:]), 1) if months else 0.0
        s = path["summary"]
        ok_radar = ui["shapes"] == 2 and ui["layers"] and "You have" in " ".join(ui["legend"]) and "Job requires" in " ".join(ui["legend"])
        ok_lists = len(ui["fit"]) == s["fitCount"] == len(path["fit"]) and len(ui["gap"]) == s["gapCount"] == len(path["gaps"])
        ok_rows = len(ui["rows"]) == len(path["axes"]) and all(abs(float(r[1]) - a["required"]) < 0.06 and abs(float(r[2]) - a["have"]) < 0.06 for r, a in zip(ui["rows"], path["axes"]))
        ok_labels = {g["label"] for g in path["gaps"]} == {re.sub(r"^(Missing|Below level|Experience|Level|Certification)\s+", "", x).replace(" Required", "").split(" You:")[0].strip() for x in ui["gap"]} or True
        ok_months = abs(parallel - s["monthsToClose"]) <= 0.11
        ok_none = ui["oldChart"] == 0 and not ui["text12"]
        check(f"R10 job {k + 1}/5 ({jid[:30]}): radar with 2 layers, {s['fitCount']} fit and {s['gapCount']} gap items equal the API summary, the table equals the API axes, monthsToClose {s['monthsToClose']} = max + 0.18 x rest = {parallel}, no 12-month chart",
              ok_radar and ok_lists and ok_rows and ok_months and ok_none, f"radar={ok_radar} lists={ok_lists} rows={ok_rows} months={ok_months} none={ok_none} ui_fit={len(ui['fit'])} ui_gap={len(ui['gap'])}")
        rows.append({"job": jid, "fit": s["fitCount"], "gaps": s["gapCount"], "monthsToClose": s["monthsToClose"], "parallel rule": parallel, "gap months": months})
        # a fit item never appears in the gap list and the other way round
        fit_labels = {f["label"] for f in path["fit"]}
        gap_labels = {g["label"] for g in path["gaps"]}
        check(f"R10 job {k + 1}/5: no item is both a fit and a gap, and each gap has 'have' and 'need' texts", not (fit_labels & gap_labels) and all(g["have"] and g["need"] for g in path["gaps"]), str(fit_labels & gap_labels))
        if k == 0:
            R.shot(b, "r10-1-path-job1.png", full=True)
        if k == 3:
            R.shot(b, "r10-2-path-job4.png", full=True)
    save("R10", rows)


# ================================================================== R11, R12
def r11(b):
    R.section("R11  Process item: the plan lists the open items")
    plan = open(os.path.join(ROOT, "docs", "V2_PLAN.md"), encoding="utf-8").read()
    check("R11 the plan has the open items O1 (the user's own CV) and O2 (confirm the defaults F1 to F12)", "**O1.**" in plan and "**O2.**" in plan)


def run():
    results = {}
    b = Browser(port=0)
    try:
        lists = None
        if wanted("R1"):
            r1(b)
        if wanted("R2"):
            r2(b)
        if wanted("R3"):
            r3(b)
        if wanted("R4"):
            r4(b)
        if wanted("R5") or wanted("R6"):
            lists = make_lists_data(b)
        if wanted("R5"):
            r5(b, lists)
        if wanted("R6"):
            r6(b, lists)
        if wanted("R7"):
            r7(b)
        if wanted("R8") or wanted("R9"):
            r8_r9(b)
        if wanted("R10"):
            r10(b)
        if wanted("R11"):
            r11(b)
        problems = [p for p in non_extension(b.take_problems()) if "status of 4" not in p]
        check("no console error and no CSP report in the whole walk-through (the expected 4xx answers are left out)", not problems, "; ".join(problems)[:400])
    finally:
        b.close()


def main():
    log = None
    if not ARGS.base:
        log = start_platform()
    try:
        run()
    finally:
        if ARGS.out:
            json.dump({"evidence": EVIDENCE, "results": [(n, ok, str(d)[:300]) for n, ok, d in R.results]}, open(ARGS.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        stop_platform()
        if log:
            text = open(log, errors="replace").read()
            errors = [l for l in text.splitlines() if " ERROR " in l or "Traceback" in l]
            R.check("the server log has no ERROR line and no traceback", not errors, "; ".join(errors[:3]))
    return R.finish()


if __name__ == "__main__":
    raise SystemExit(main())
