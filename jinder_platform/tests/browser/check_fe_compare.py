"""Browser checks for the FE-Compare work of Jinder V2: the Compare page (#/compare) for talent (jobs) and employers (talent).

Usage:
  python tests/browser/check_fe_compare.py                      start the platform on port 8150 (temp data folder), run, stop it
  python tests/browser/check_fe_compare.py --base http://localhost:8150 --talent-pw X --employer-pw Y   use a platform that runs already
Options: --shots <folder> (screenshots), --debug-port 9350 (Chrome remote debugging port), --port 8150, --only talent|employer,
         --retries 3 --retry-wait 180 (if the platform does not start, wait and try again: other agents edit the backend)

It needs Chrome or Edge (see cdp.py). It runs against the REAL backend (the compare calls do not work in mock mode).
The numbers on the page are compared with the numbers of the API (read with a token in Python), so the tests check the real values.
The employer plan is switched with PUT /entitlements (the demo switch): the test sets Basic first, then Premium.
If the data has too few jobs or talent, the test creates jobs through the API (as the employer) and says so.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.abspath(os.path.join(HERE, "..", ".."))
results = []
SHOTS = [""]          # the screenshot folder, set in main()
SHOT_FILES = []       # the screenshots that were taken
NOTES = []            # things that the test did to the data (for example: jobs that it created)
WAIT = 45             # seconds that a wait may take (the computer can be busy)
LEVEL_LABEL = {1: "Beginner", 2: "Working", 3: "Proficient", 4: "Advanced", 5: "Expert"}


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def info(text):
    print("INFO " + text)


# ---------------------------------------------------------------- contrast helpers
def _rgb(css):
    nums = [float(x) for x in re.findall(r"[\d.]+", css)[:3]]
    return tuple(n * 255 for n in nums) if css.strip().startswith("color(") else tuple(nums)


def _lum(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_lum(_rgb(a)), _lum(_rgb(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- the platform
class Platform:
    """Starts `python start.py --demo --reset-db` on a port, with its own data folder, and reads the demo passwords from the output."""

    def __init__(self, port):
        self.port = port
        self.var = tempfile.mkdtemp(prefix="jinder-fe-compare-")
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
                    raise RuntimeError("The platform stopped at start:\n" + open(self.log, encoding="utf-8").read()[-1500:])
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


def start_platform(port, retries, wait_s):
    """Start the platform. Other agents edit the backend, so a start can fail for a reason that is not in this test: wait and try again."""
    last = None
    for attempt in range(retries + 1):
        try:
            return Platform(port)
        except RuntimeError as exc:
            last = exc
            info(f"the platform did not start (try {attempt + 1} of {retries + 1}): {str(exc)[-300:]}")
            if attempt < retries:
                info(f"waiting {wait_s} seconds, then trying again")
                time.sleep(wait_s)
    raise last


def kill_tree(pid):
    """Chrome starts helper processes. On Windows, closing the main process leaves them. End the whole tree of OUR browser."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


# ---------------------------------------------------------------- the API (read with a token, to know the real values)
class Api:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def call(self, method, path, body=None, token=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + "/api" + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                return exc.code, json.loads(raw)
            except ValueError:
                return exc.code, raw.decode(errors="replace")

    def login(self, email, password):
        status, data = self.call("POST", "/auth/login", {"email": email, "password": password})
        if status != 200:
            raise RuntimeError(f"sign-in failed for {email}: {status} {data}")
        return data["token"]


# ---------------------------------------------------------------- browser helpers
def wait(b, cond, t=WAIT):
    b.wait_for(cond, timeout=t)


def sign_in(b, base, email, password):
    b.goto(f"{base}/#/login")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{base}/#/login")
    wait(b, "document.querySelector('#email')")
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    wait(b, "location.hash.startsWith('#/home')")
    wait(b, "document.querySelector('#shellUser')")
    b.pump(0.8)


def set_viewport(b, width, height):
    b.call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
    b.pump(0.4)


def shot(b, name, full=True):
    if SHOTS[0]:
        path = os.path.join(SHOTS[0], name)
        b.screenshot(path, full=full)
        SHOT_FILES.append(path)


def no_problems(b, name, ignore=()):
    """No console error, exception or CSP report since the last call. Errors from a browser extension are not from the app."""
    problems = [p for p in b.take_problems() if "chrome-extension://" not in p and not any(i in p for i in ignore)]
    check(name, not problems, "; ".join(problems)[:600])


def count(b, sel):
    return b.eval(f"document.querySelectorAll({json.dumps(sel)}).length", False)


def text_of(b, sel):
    return b.eval(f"(document.querySelector({json.dumps(sel)}) || {{}}).innerText || ''", False)


def press(b, key, code=None, vk=0, text=None):
    """A real key press (the browser handles it: Escape closes a dialog, Space ticks a check box)."""
    down = {"type": "keyDown", "key": key, "code": code or key, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
    if text:
        down["text"] = text
    b.call("Input.dispatchKeyEvent", down)
    b.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": key, "code": code or key, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk})
    b.pump(0.3)


def pick_js(pick_id, tail):
    """JavaScript for one check box of the picker: pick_js('job-1', 'click()')."""
    return "document.querySelector(%s).%s" % (json.dumps(".cmp-pick-check[data-id=%s]" % json.dumps(pick_id)), tail)


def mark(b):
    b.pump(0.3)
    return len(b.events)


def api_requests(b, start):
    """The API calls that the page made since `mark`."""
    b.pump(0.4)
    out = []
    for ev in b.events[start:]:
        if ev.get("method") == "Network.requestWillBeSent":
            url = ev["params"]["request"]["url"]
            if "/api/" in url:
                out.append(url)
    return out


TABLE_JS = r"""(sel) => { const t = document.querySelector(sel); if (!t) return null;
  return [...t.querySelectorAll('tr')].map(tr => [...tr.children].map(c => ({ tag: c.tagName, scope: c.getAttribute('scope'), cls: c.className, text: c.innerText.trim().replace(/\s+/g, ' ') }))); }"""


def table(b, sel):
    return b.eval(f"({TABLE_JS})({json.dumps(sel)})", False)


def set_basket(b, kind, items):
    b.eval("""(async (kind, items) => { const { compareStore } = await import('/js/core/compare-store.js');
      compareStore.clear('job'); compareStore.clear('talent'); items.forEach(i => compareStore.add(kind, i)); return compareStore.items(kind).length; })(%s, %s)""" % (json.dumps(kind), json.dumps(items)))


def basket_ids(b, kind):
    return b.eval("""(async (kind) => { const { compareStore } = await import('/js/core/compare-store.js'); return compareStore.items(kind).map(x => x.id); })(%s)""" % json.dumps(kind))


def hash_ids(b):
    v = b.eval("new URLSearchParams((location.hash.split('?')[1] || '')).get('ids') || ''", False)
    return [x for x in v.split(",") if x]


def hash_param(b, name):
    return b.eval("new URLSearchParams((location.hash.split('?')[1] || '')).get(%s) || ''" % json.dumps(name), False)


def go(b, hash_):
    """Open a route. If the address is the same already, reload the page, so that the page draws again."""
    if b.eval("location.hash", False) == hash_:
        b.eval("location.reload()", False)
        b.pump(1.0)
        wait(b, "document.readyState === 'complete'")
    else:
        b.eval(f"location.hash = {json.dumps(hash_)}", False)
    b.pump(0.3)


def wait_results(b, t=WAIT):
    wait(b, "document.querySelector('.cmp-panels') && !document.querySelector('.cmp-panels').classList.contains('is-loading') && document.querySelector('.cmp-panels').children.length", t)
    b.pump(0.3)


def wait_mode(b, mode, t=WAIT):
    wait(b, f"document.querySelector('.cmp-body') && document.querySelector('.cmp-body').dataset.mode === {json.dumps(mode)}", t)
    b.pump(0.3)


def wait_picker(b, t=WAIT):
    """The list of the picker has loaded (rows, or a message that is not 'Loading…')."""
    wait(b, "document.querySelectorAll('.cmp-pick-item').length || (document.querySelector('.cmp-pick-msg') && document.querySelector('.cmp-pick-msg').innerText && document.querySelector('.cmp-pick-msg').innerText !== 'Loading…')", t)
    b.pump(0.3)


def close_picker(b):
    if b.eval("!!document.querySelector('dialog.cmp-picker-dialog[open]')", False):
        press(b, "Escape", "Escape", 27)
        wait(b, "!document.querySelector('dialog.cmp-picker-dialog')", 10)


# ---------------------------------------------------------------- data for the tests
def open_jobs_for_talent(api, talent_tok, n):
    """Jobs that the talent can compare: open, with different titles."""
    got, seen = [], set()
    for path in ("/jobs/recommended?pageSize=12", "/jobs?pageSize=20&sort=newest"):
        status, data = api.call("GET", path, token=talent_tok)
        for j in (data or {}).get("items", []) if status == 200 else []:
            if j.get("status", "open") == "open" and j["title"] not in seen and j["id"] not in {x["id"] for x in got}:
                got.append(j)
                seen.add(j["title"])
    return got[:max(n, 0)] if len(got) >= n else got


def make_jobs(api, emp_tok, how_many, template):
    """Create open jobs through the API (as the employer). `template` is an own job: it gives a valid category, place and type."""
    closes = (datetime.now(timezone.utc) + timedelta(days=25)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    made = []
    for i in range(how_many):
        body = {"title": f"Compare check job {i + 1} {int(time.time()) % 100000}", "category": template["category"], "location": template["location"],
                "type": template["type"], "description": "A sample job for the compare page check. It has a clear description of the work and the skills.",
                "skills": (template.get("skills") or ["Excel"])[:4], "targetApplicants": 10, "closesAt": closes, "salary": "$90,000 – $100,000 per year"}
        status, data = api.call("POST", "/recruiter/jobs", body, token=emp_tok)
        if status in (200, 201):
            made.append(data["id"])
    return made


# ---------------------------------------------------------------- expected values, worked out from the API answer
def axis_value(job, key):
    for a in job.get("axes") or []:
        if a["key"] == key:
            return a["value"]
    return None


def level_text(n):
    return f"{LEVEL_LABEL.get(n, 'Level')} ({n})" if n is not None else "—"


def check_talent_page(b, api, tok, ids, label, shots_name=""):
    """Everything on the talent page for these job ids, against the real API answer."""
    status, res = api.call("GET", "/jobs/compare?ids=" + ",".join(ids), token=tok)
    check(f"{label}: the API answers 200 for {len(ids)} jobs", status == 200, str(res)[:200])
    if status != 200:
        return None
    jobs = res["jobs"]
    n = len(jobs)
    check(f"{label}: h1 is 'Compare jobs'", text_of(b, "h1") == "Compare jobs", text_of(b, "h1"))
    check(f"{label}: the address has the ids", hash_ids(b) == ids, str(hash_ids(b)))
    check(f"{label}: the basket has the same ids", basket_ids(b, "job") == ids, str(basket_ids(b, "job")))
    check(f"{label}: {n} cards, each with a Remove button that names the job",
          count(b, ".cmp-card") == n and count(b, ".cmp-card [data-remove][aria-label^='Remove ']") == n)
    heads = b.eval("[...document.querySelectorAll('.cmp-card')].map(c => ({title: c.querySelector('.cmp-card-title').innerText.trim(), href: c.querySelector('.cmp-card-title a').getAttribute('href'), facts: [...c.querySelectorAll('.cmp-facts dt')].map(d => d.textContent.trim())}))", False)
    check(f"{label}: cards show title, a link to the job, and Level, Experience, Work mode, Salary (middle)",
          [h["title"] for h in heads] == [j["title"] for j in jobs] and all(h["href"].startswith("#/jobs/") for h in heads)
          and all(h["facts"] == ["Level", "Experience", "Work mode", "Salary (middle)"] for h in heads), str(heads)[:300])
    mid = b.eval("[...document.querySelectorAll('.cmp-card')].map(c => c.querySelector('.cmp-facts > div:last-child dd').innerText.trim())", False)
    exp_mid = [f"${j['salaryMidpoint']:,} a year" if j.get("salaryMidpoint") else "— Not listed" for j in jobs]
    check(f"{label}: the salary middle on each card equals the API", [m.replace("\n", " ") for m in mid] == exp_mid, f"{mid} {exp_mid}")

    # --- the radar: one series for each job, on the usable axes
    axes = [a for a in res["axes"] if all(axis_value(j, a["key"]) is not None for j in jobs)]
    check(f"{label}: radar has {n} series and {len(axes)} axes", count(b, ".cmp-panels .radar .rd-series") == n and b.eval("document.querySelector('.cmp-panels .rd-svg').dataset.axes", False) == str(len(axes)),
          f"{count(b, '.cmp-panels .radar .rd-series')}")
    legend = b.eval("[...document.querySelectorAll('.cmp-panels .rd-legend li span')].map(s => s.innerText.trim())", False)
    check(f"{label}: radar legend names the jobs", legend == [j["title"] for j in jobs], str(legend))
    aria = b.eval("document.querySelector('.cmp-panels .rd-svg').getAttribute('aria-label')", False)
    check(f"{label}: radar has an aria-label with the values", all(j["title"] in aria for j in jobs) and "Skills" in aria)
    # --- the numbers table equals the API
    rows = table(b, "#cmpFit table")
    body = rows[1:]
    ok_rows = len(body) == len(axes)
    bad = []
    for a, row in zip(axes, body):
        vals = [axis_value(j, a["key"]) for j in jobs]
        texts = [c["text"] for c in row[1:]]
        nums = [re.match(r"-?\d+\.\d", t).group(0) if re.match(r"-?\d+\.\d", t) else t for t in texts]
        if nums != [f"{v:.1f}" for v in vals]:
            bad.append((a["key"], nums, vals))
        if not row[0]["text"].startswith(a["label"]) or a.get("formula", "") not in row[0]["text"]:
            bad.append((a["key"], "axis name or formula tag", row[0]["text"]))
        same = all(v == vals[0] for v in vals)
        marks = ["Highest" in t for t in texts]
        if marks != [(not same and v == max(vals)) for v in vals]:
            bad.append((a["key"], "Highest marks", marks, vals))
    check(f"{label}: numbers table: one row for each axis, one decimal, equal to the API, formula tag after the axis name, 'Highest' on the best value", ok_rows and not bad, str(bad)[:400])
    check(f"{label}: numbers table head has the job names", [c["text"] for c in rows[0][1:]] == [j["title"] for j in jobs], str(rows[0])[:200])

    # --- skills side by side
    srows = table(b, "#cmpSkills table")
    matrix = res["skillMatrix"]
    head, body, foot = srows[0], [r for r in srows[1:] if r[0]["tag"] == "TH" and not r[0]["text"].startswith("Skills you meet")], [r for r in srows[1:] if r[0]["text"].startswith("Skills you meet")]
    bad = []
    if len(body) != len(matrix):
        bad.append(("rows", len(body), len(matrix)))
    meets = [0] * n
    asked = [0] * n
    for m, row in zip(matrix, body):
        exp_th = f"{m['skill']} You: {level_text(m['yours'])}"
        if row[0]["text"] != exp_th:
            bad.append(("th", row[0]["text"], exp_th))
        for k, j in enumerate(jobs):
            cell = m["byJob"].get(j["id"])
            got = row[1 + k]["text"]
            if cell is None:
                exp = "Not asked"
            else:
                state = "Missing" if m["yours"] is None else ("Meets" if m["yours"] >= cell["required"] else "Below")
                asked[k] += 1
                meets[k] += state == "Meets"
                exp = f"{state} Needs {level_text(cell['required'])} · {'Must have' if cell['must'] else 'Nice to have'}"
            if got != exp:
                bad.append((m["skill"], j["title"][:20], got, exp))
    check(f"{label}: skill matrix: {len(matrix)} rows; first column has the skill and 'You: <level or —>'; each cell has the state word, the level and Must/Nice, as the API says", not bad, str(bad)[:500])
    exp_foot = [f"{meets[k]} of {asked[k]} {'skill' if asked[k] == 1 else 'skills'}" for k in range(n)]
    check(f"{label}: skill matrix footer counts what you meet", bool(foot) and [c["text"] for c in foot[0][1:]] == exp_foot, f"{foot[0] if foot else None} {exp_foot}")
    check(f"{label}: skill matrix header has one column for each job", [c["text"] for c in head[1:]] == [j["title"] for j in jobs])

    # --- details: a row is hidden when no job has it
    drows = table(b, "#cmpDetails table") or []
    shown = [r[0]["text"] for r in drows[1:]]
    defs = {
        "Level": lambda j: j.get("level"), "Specialisation": lambda j: j.get("specialisation"),
        "Experience": lambda j: j.get("minYears") is not None or j.get("maxYears") is not None, "Work mode": lambda j: j.get("workMode"),
        "Job type": lambda j: j.get("type"), "Salary": lambda j: j.get("salary"), "Salary (middle)": lambda j: j.get("salaryMidpoint"),
        "Education": lambda j: j.get("educationMin"), "Certifications required": lambda j: (j.get("certifications") or {}).get("required"),
        "Certifications preferred": lambda j: (j.get("certifications") or {}).get("preferred"), "Preferred awards": lambda j: (j.get("awards") or {}).get("preferred"),
    }
    exp_shown = [k for k, f in defs.items() if any(f(j) for j in jobs)]
    check(f"{label}: details rows are hidden when no job has a value (rows: {exp_shown})", shown == exp_shown, f"{shown} {exp_shown}")

    # --- pairs
    pairs = res["pairs"]
    prow = table(b, "#cmpPairs table")
    bad = []
    by = {frozenset((p["a"], p["b"])): p for p in pairs}
    for ia, ja in enumerate(jobs):
        for ib, jb in enumerate(jobs):
            cell = prow[1 + ia][1 + ib]["text"]
            if ia == ib:
                if "Same job" not in cell:
                    bad.append(("diag", cell))
                continue
            p = by.get(frozenset((ja["id"], jb["id"])))
            if not p or cell != f"{p['index']:.1f} {p['tier']}":
                bad.append((ja["title"][:15], jb["title"][:15], cell, p and (p["index"], p["tier"])))
    check(f"{label}: pair matrix {n}x{n} has the overall number and the tier word of each pair, equal to the API", not bad and len(pairs) == n * (n - 1) // 2, str(bad)[:400])
    check(f"{label}: one details disclosure for each of the {len(pairs)} pairs", count(b, "details.cmp-pair") == len(pairs))
    b.eval("document.querySelector('details.cmp-pair').open = true", False)
    body_txt = text_of(b, "details.cmp-pair .cmp-pair-body")
    p0 = pairs[0]
    check(f"{label}: a pair shows its parts, advice and salary change", all(x["label"] in body_txt for x in p0["parts"]) and p0["advice"] in body_txt and p0["salaryChange"] in body_txt, body_txt[:200])
    return res


def check_table_a11y(b, label):
    r = b.eval("""(() => { const out = [];
      document.querySelectorAll('.compare-page table.cmp-table').forEach(t => {
        const wrap = t.closest('.cmp-scroll');
        out.push({ caption: !!t.querySelector('caption') && t.querySelector('caption').innerText.length > 10,
                   region: !!wrap && wrap.getAttribute('role') === 'region' && !!wrap.getAttribute('aria-label') && wrap.tabIndex === 0,
                   colScope: [...t.querySelectorAll('thead th')].every(h => h.getAttribute('scope') === 'col'),
                   rowScope: [...t.querySelectorAll('tbody th, tfoot th')].every(h => h.getAttribute('scope') === 'row') });
      }); return out; })()""", False)
    check(f"{label}: every table has a caption, a labelled keyboard-focusable scroll region, scope=col and scope=row", bool(r) and all(all(x.values()) for x in r), str(r))
    inline = b.eval("document.querySelectorAll('.compare-page [style], dialog.cmp-picker-dialog [style]').length", False)
    check(f"{label}: no inline style attribute on the page (CSP)", inline == 0, str(inline))


def check_series_styles(b, label, n):
    r = b.eval("""(() => [...document.querySelectorAll('.cmp-panels .radar .rd-shape')].map(s => { const c = getComputedStyle(s); return [c.stroke, c.strokeDasharray]; }))()""", False)
    legend = b.eval("[...document.querySelectorAll('.cmp-panels .rd-legend .rd-swatch-line')].map(s => { const c = getComputedStyle(s); return [c.stroke, c.strokeDasharray]; })", False)
    check(f"{label}: {n} series differ in line style (dash pattern), and the legend has the same styles", len({x[1] for x in r}) == n and r == legend, str(r))
    cards = b.eval("[...document.querySelectorAll('.cmp-card .rd-swatch-line')].map(s => { const c = getComputedStyle(s); return [c.stroke, c.strokeDasharray]; })", False)
    check(f"{label}: the swatch on each card matches its line in the chart", cards == r, f"{cards} {r}")


# ---------------------------------------------------------------- the checks: talent
def talent_checks(b, base, api, tok, jobs, shots):
    sign_in(b, base, "candidate@demo.jinder.app", TALENT_PW[0])
    items = [{"id": j["id"], "title": j["title"], "company": j.get("company", "")} for j in jobs]
    ids = [j["id"] for j in jobs]

    # ---- the empty page and the first picker (no items)
    set_basket(b, "job", [])
    start = mark(b)
    go(b, "#/compare")
    wait_mode(b, "empty")
    wait(b, "document.querySelector('dialog.cmp-picker-dialog[open]')", 20)
    check("talent: fewer than 2 items: 'Choose at least 2 jobs to compare' and the picker is open", "Choose at least 2 jobs to compare" in text_of(b, ".cmp-empty") and count(b, "dialog.cmp-picker-dialog[open]") == 1)
    check("talent: an empty page makes no compare request", not [u for u in api_requests(b, start) if "/jobs/compare" in u])
    check("talent: the picker has the tabs 'Saved jobs' and 'Recommended', a search box and a list with check boxes",
          b.eval("[...document.querySelectorAll('.cmp-picker [role=tab]')].map(t => t.innerText.trim())", False) == ["Saved jobs", "Recommended"]
          and count(b, ".cmp-picker input[type=search]") == 1 and b.eval("!!document.querySelector('.cmp-picker label[for]')", False) is True)
    shot(b, "01-talent-empty-picker.png", full=False)
    press(b, "Escape", "Escape", 27)
    wait(b, "!document.querySelector('dialog.cmp-picker-dialog')", 10)
    check("talent: Esc closes the picker and the focus returns to the 'Add to compare' button", b.eval("document.activeElement && document.activeElement.matches('[data-add]')", False), b.eval("document.activeElement.outerHTML.slice(0, 80)", False))

    # ---- 2 jobs from the basket
    set_basket(b, "job", items[:2])
    go(b, "#/compare")
    wait_results(b)
    check_talent_page(b, api, tok, ids[:2], "talent 2 jobs")
    check_table_a11y(b, "talent 2 jobs")
    check("talent 2 jobs: the Add button is enabled and the count says '2 of 5 chosen'", not b.eval("document.querySelector('[data-add]').disabled", False) and "2 of 5 chosen" in text_of(b, "[data-count]"))
    shot(b, "02-talent-2-jobs.png")
    no_problems(b, "talent 2 jobs: no console error, no CSP error")

    # ---- 3 jobs: the basket is changed in another place, the page is opened with only the basket (no ids in the address)
    set_basket(b, "job", items[:3])
    go(b, "#/compare")
    wait_results(b)
    check_talent_page(b, api, tok, ids[:3], "talent 3 jobs")
    shot(b, "03-talent-3-jobs.png")

    # ---- 5 jobs, and the line styles
    set_basket(b, "job", items[:5])
    go(b, "#/compare")
    wait_results(b)
    check_talent_page(b, api, tok, ids[:5], "talent 5 jobs")
    check_series_styles(b, "talent 5 jobs", 5)
    check_table_a11y(b, "talent 5 jobs")
    check("talent 5 jobs: the Add button is disabled, and the text says that 5 is the most", b.eval("document.querySelector('[data-add]').disabled", False) and "most you can compare" in text_of(b, "[data-count]"), text_of(b, "[data-count]"))
    colours = b.eval("[...document.querySelectorAll('.cmp-panels .radar .rd-shape')].map(s => getComputedStyle(s).stroke)", False)
    check("talent 5 jobs: the 5 lines have 5 different colours", len(set(colours)) == 5, str(colours))
    shot(b, "04-talent-5-jobs.png")
    no_problems(b, "talent 5 jobs: no console error, no CSP error")

    # ---- the 6th item is refused
    refused = b.eval("""(async (item) => { const { compareStore } = await import('/js/core/compare-store.js'); return compareStore.add('job', item); })(%s)""" % json.dumps({"id": "sixth-job", "title": "Sixth"}))
    check("talent: the basket refuses a 6th job (add returns false)", refused is False)
    six = [j["id"] for j in jobs[:6]]
    if len(six) == 6:
        start = mark(b)
        go(b, "#/compare?ids=" + ",".join(six))
        wait_results(b)
        reqs = [u for u in api_requests(b, start) if "/jobs/compare" in u]
        sent = re.search(r"ids=([^&]*)", reqs[-1]).group(1) if reqs else ""
        from urllib.parse import unquote
        check("talent: an address with 6 ids sends only the first 5 to the API", bool(reqs) and unquote(sent).split(",") == six[:5], str(reqs))
        check("talent: the page says that it uses the first 5", "up to 5" in text_of(b, "[data-note]") and "first 5" in text_of(b, "[data-note]"), text_of(b, "[data-note]"))
        check("talent: address and basket now have 5 ids, and 5 cards show", hash_ids(b) == six[:5] and basket_ids(b, "job") == six[:5] and count(b, ".cmp-card") == 5, str(hash_ids(b)))
    else:
        info("fewer than 6 open jobs: the test of an address with 6 ids was skipped")

    # ---- remove: address, basket, cards, chart, announcement and focus
    set_basket(b, "job", items[:5])
    go(b, "#/compare")
    wait_results(b)
    start = mark(b)
    gone = ids[1]
    b.click(f".cmp-card [data-remove={json.dumps(gone)}]".replace('"', "'"))
    b.pump(0.3)
    check("talent remove: the focus stays on a Remove button, not on the page body", b.eval("!!document.activeElement && document.activeElement.matches('.cmp-card [data-remove]')", False), b.eval("document.activeElement.tagName", False))
    wait_results(b)
    expected = [i for i in ids[:5] if i != gone]
    check("talent remove: the address and the basket lose the removed id", hash_ids(b) == expected and basket_ids(b, "job") == expected, f"{hash_ids(b)} {basket_ids(b, 'job')}")
    check("talent remove: 4 cards, 4 series, a new request with 4 ids", count(b, ".cmp-card") == 4 and count(b, ".cmp-panels .radar .rd-series") == 4
          and any(len(re.search(r"ids=([^&]*)", u).group(1).split("%2C" if "%2C" in u else ",")) == 4 for u in api_requests(b, start) if "/jobs/compare" in u))
    check("talent remove: the Add button is enabled again", not b.eval("document.querySelector('[data-add]').disabled", False))
    announced = b.eval("document.getElementById('announcer').textContent", False)
    check("talent remove: the screen reader announcement says that the job was removed", "removed from compare" in announced, announced)
    # remove down to 1: an empty state and NO compare request for the last remove
    for _ in range(2):
        b.click(".cmp-card [data-remove]")
        wait_results(b)
    start = mark(b)
    b.click(".cmp-card [data-remove]")
    wait_mode(b, "empty")
    check("talent remove: with 1 item left, 'Choose at least 2 jobs to compare' shows and the page asks the API nothing", "Choose at least 2 jobs to compare" in text_of(b, ".cmp-empty") and not [u for u in api_requests(b, start) if "/jobs/compare" in u])
    check("talent remove: the address and the basket have 1 id", len(hash_ids(b)) == 1 and len(basket_ids(b, "job")) == 1)
    check("talent remove: after the empty state shows, the focus is on a button of the page (not lost)", b.eval("!!document.activeElement && document.activeElement !== document.body", False))
    shot(b, "05-talent-one-left.png", full=False)

    # ---- the picker: choose, mark, search, saved, keyboard
    b.click(".cmp-empty [data-add]")
    wait(b, "document.querySelector('dialog.cmp-picker-dialog[open]')", 20)
    wait_picker(b)
    saved_msg = text_of(b, ".cmp-pick-msg")
    has_saved = count(b, ".cmp-pick-item") > 0
    check("talent picker: the tab 'Saved jobs' lists the saved jobs, or says what to do when there are none", has_saved or "no saved jobs" in saved_msg, saved_msg)
    # bookmark one job through the API, then open the Saved tab again
    bookmarked = jobs[5]["id"] if len(jobs) > 5 else jobs[0]["id"]
    api.call("PUT", f"/bookmarks/{bookmarked}", token=tok)
    b.click("[data-tab=recommended]")
    wait_picker(b)
    check("talent picker: the tab 'Recommended' lists jobs with check boxes, a title and a place", count(b, ".cmp-pick-item .cmp-pick-check") >= 2 and bool(text_of(b, ".cmp-pick-item .cmp-pick-title")))
    check("talent picker: the one chosen job is marked (checked, 'Chosen')", b.eval("[...document.querySelectorAll('.cmp-pick-check')].filter(c => c.checked).length", False) in (0, 1)
          and b.eval("[...document.querySelectorAll('[data-chosen-chip]')].filter(c => !c.hidden).length", False) == b.eval("[...document.querySelectorAll('.cmp-pick-check')].filter(c => c.checked).length", False)
          and count(b, ".cmp-picker [data-unpick]") == 1)
    b.click("[data-tab=saved]")
    wait_picker(b)
    check("talent picker: after a bookmark, the tab 'Saved jobs' lists it", bookmarked in b.eval("[...document.querySelectorAll('.cmp-pick-check')].map(c => c.dataset.id)", False))
    # keyboard on the tabs: arrow keys move between the tabs
    b.eval("document.querySelector('[data-tab=saved]').focus()", False)
    press(b, "ArrowRight", "ArrowRight", 39)
    wait(b, "document.querySelector('[data-tab=recommended]').getAttribute('aria-selected') === 'true'", 10)
    check("talent picker: the arrow key moves to the next tab, focus follows (keyboard)", b.eval("document.activeElement.dataset.tab === 'recommended' && document.querySelector('[data-tab=saved]').tabIndex === -1", False))
    wait_picker(b)
    # tick 3 with the keyboard (Space) and the mouse
    boxes = b.eval("[...document.querySelectorAll('.cmp-pick-check')].map(c => c.dataset.id)", False)
    pick = [x for x in boxes if x not in basket_ids(b, "job")][:3]
    b.eval(pick_js(pick[0], "focus()"), False)
    press(b, " ", "Space", 32, text=" ")
    check("talent picker: Space ticks a check box (keyboard)", b.eval(pick_js(pick[0], "checked"), False) is True)
    for pid in pick[1:]:
        b.eval(pick_js(pid, "click()"), False)
    b.pump(0.3)
    cnt = text_of(b, "[data-pick-count]")
    check("talent picker: the count (a live region) says '4 of 5 chosen'", cnt.startswith("4 of 5 chosen") and b.eval("document.querySelector('[data-pick-count]').getAttribute('aria-live')", False) == "polite", cnt)
    # the 5th is allowed, then the others are disabled
    extra = [x for x in boxes if x not in basket_ids(b, "job") and x not in pick]
    if extra:
        b.eval(pick_js(extra[0], "click()"), False)
        b.pump(0.3)
        others = b.eval("[...document.querySelectorAll('.cmp-pick-check')].filter(c => !c.checked).every(c => c.disabled)", False)
        check("talent picker: at 5 chosen, the other check boxes are disabled and the text says that 5 is the most", others and "most you can compare" in text_of(b, "[data-pick-count]"), text_of(b, "[data-pick-count]"))
        b.eval(pick_js(extra[0], "click()"), False)
        b.pump(0.3)
    # search by text goes through api.jobs.search
    word = (re.findall(r"[A-Za-z]{4,}", jobs[0]["title"]) or ["Manager"])[0]
    start = mark(b)
    b.fill(".cmp-picker input[type=search]", word)
    wait(b, "document.querySelector('.cmp-pick-count') && [...document.querySelectorAll('[role=tab]')].every(t => t.getAttribute('aria-selected') === 'false')", 15)
    b.pump(1.0)
    wait_picker(b)
    search_calls = [u for u in api_requests(b, start) if re.search(r"/api/jobs\?", u) and "q=" in u]
    check("talent picker: typing in the search box searches all jobs through the API (api.jobs.search)", bool(search_calls), str(search_calls))
    shot(b, "06-talent-picker-search.png", full=False)
    b.eval("document.querySelector('.cmp-picker input[type=search]').value = ''; document.querySelector('.cmp-picker input[type=search]').dispatchEvent(new Event('input', {bubbles: true}))", False)
    wait(b, "[...document.querySelectorAll('[role=tab]')].some(t => t.getAttribute('aria-selected') === 'true')", 15)
    # Done
    b.click("dialog.cmp-picker-dialog [type=submit]")
    wait(b, "!document.querySelector('dialog.cmp-picker-dialog')", 10)
    wait_results(b)
    now_ids = basket_ids(b, "job")
    check("talent picker: Done puts the chosen jobs into the address, the basket and the page", len(now_ids) == 4 and hash_ids(b) == now_ids and count(b, ".cmp-card") == 4 and count(b, ".cmp-panels .radar .rd-series") == 4, f"{now_ids} {hash_ids(b)}")
    check("talent picker: after Done the focus returns to the Add button (or the page heading if it is disabled)", b.eval("document.activeElement.matches('[data-add]') || document.activeElement.matches('h1') || document.activeElement.matches('.cmp-card [data-remove]')", False), b.eval("document.activeElement.outerHTML.slice(0, 100)", False))
    # reopen: items already chosen are marked
    b.click("[data-add]")
    wait_picker(b)
    marked = b.eval("[...document.querySelectorAll('.cmp-pick-check')].filter(c => c.checked).map(c => c.dataset.id)", False)
    chips = b.eval("[...document.querySelectorAll('.cmp-pick-item')].filter(li => li.querySelector('.cmp-pick-check').checked).every(li => !li.querySelector('[data-chosen-chip]').hidden)", False)
    in_list = [x for x in now_ids if x in b.eval("[...document.querySelectorAll('.cmp-pick-check')].map(c => c.dataset.id)", False)]
    check("talent picker: reopened, the chosen jobs that are in the list are ticked and show the text 'Chosen'; all 4 are in 'Chosen now'", sorted(marked) == sorted(in_list) and chips and count(b, ".cmp-picker [data-unpick]") == 4, f"{marked} {in_list}")
    # cancel with Esc changes nothing
    b.eval("document.querySelector('.cmp-pick-check').click()", False)
    press(b, "Escape", "Escape", 27)
    wait(b, "!document.querySelector('dialog.cmp-picker-dialog')", 10)
    check("talent picker: Esc closes it without a change, and the focus returns to the Add button", basket_ids(b, "job") == now_ids and b.eval("document.activeElement.matches('[data-add]')", False))
    no_problems(b, "talent picker: no console error, no CSP error")

    # ---- an item that does not exist: the message, and a Remove button for each item
    bad = ids[:2] + ["job-does-not-exist"]
    go(b, "#/compare?ids=" + ",".join(bad))
    wait_mode(b, "error")
    err = text_of(b, ".cmp-error")
    check("talent error: an unknown job gives the API message and a Remove button for each item", "does not exist or was removed" in err and count(b, ".cmp-error [data-remove]") == 3 and b.eval("document.querySelector('.cmp-error').getAttribute('role')", False) == "alert", err[:200])
    # the answer names the id that failed (`missing`): that item is marked and comes first, the others are not marked (QA fix)
    marked = b.eval("[...document.querySelectorAll('.cmp-fix-list li')].map(li => [li.classList.contains('is-missing'), li.querySelector('.cmp-fix-flag') ? li.querySelector('.cmp-fix-flag').textContent : ''])", False)
    check("talent error: the item that the API names in `missing` is marked 'Not found' and listed first; the other items have no mark",
          marked == [[True, "Not found"], [False, ""], [False, ""]] and "job-does-not-exist" in b.eval("document.querySelector('.cmp-fix-list li [data-remove]').dataset.remove", False), str(marked))
    b.click(".cmp-error [data-remove=job-does-not-exist]")
    wait_results(b)
    check("talent error: after the bad item is removed, the comparison loads", count(b, ".cmp-card") == 2 and hash_ids(b) == ids[:2] and not count(b, ".cmp-error"))
    no_problems(b, "talent error: no console error, no CSP error", ignore=("/api/jobs/compare", "404"))   # the 404 of the bad id is on purpose

    # ---- contrast of the state colours
    set_basket(b, "job", items[:5])
    go(b, "#/compare")
    wait_results(b)
    pairs = b.eval("""(() => { const out = {}; const grab = (name, el, textEl) => { if (!el) return; const t = getComputedStyle(textEl || el); out[name] = [t.color, getComputedStyle(el).backgroundColor]; };
      for (const s of ['meets', 'below', 'missing', 'related']) { const td = document.querySelector('#cmpSkills td.cmp-' + s); if (td) { grab(s, td, td.querySelector('.cmp-state')); grab(s + ' sub', td, td.querySelector('.cmp-sub')); } }
      grab('Highest', document.querySelector('.cmp-best')); const sub = document.querySelector('#cmpSkills th .cmp-sub'); if (sub) out['row sub'] = [getComputedStyle(sub).color, 'rgb(255, 255, 255)'];
      return out; })()""", False)
    low = {k: round(contrast(v[0], v[1]), 2) for k, v in pairs.items() if contrast(v[0], v[1]) < 4.5}
    check(f"talent: text colours of the states ({', '.join(pairs)}) have a contrast of 4.5:1 or more", pairs and not low, str(low))

    # ---- mobile
    set_viewport(b, 390, 844)
    b.pump(0.8)
    r = b.eval("""(() => { const w = document.querySelector('#cmpSkills .cmp-scroll');
      const cards = [...document.querySelectorAll('.cmp-card')].map(c => c.getBoundingClientRect());
      let overlap = false; for (let i = 0; i < cards.length; i++) for (let j = i + 1; j < cards.length; j++) { const a = cards[i], c = cards[j]; if (a.left < c.right - 1 && c.left < a.right - 1 && a.top < c.bottom - 1 && c.top < a.bottom - 1) overlap = true; }
      const cw = document.querySelector('.cmp-cards-wrap');
      return { pageW: document.documentElement.scrollWidth, vw: innerWidth, tableScrolls: w.scrollWidth > w.clientWidth + 20, region: w.getAttribute('role'), cardsScroll: cw.scrollWidth > cw.clientWidth, overlap,
               removeSize: Math.min(...[...document.querySelectorAll('.cmp-remove')].map(x => Math.min(x.getBoundingClientRect().width, x.getBoundingClientRect().height))),
               svgW: document.querySelector('.cmp-panels .rd-svg').getBoundingClientRect().width, fitW: document.querySelector('#cmpFit').getBoundingClientRect().width }; })()""", False)
    check("talent mobile 390px: the page does not scroll sideways (only the tables and the cards do)", r["pageW"] <= r["vw"] + 1, str(r))
    check("talent mobile 390px: the skills table scrolls sideways inside a labelled region", r["tableScrolls"] and r["region"] == "region", str(r))
    check("talent mobile 390px: the cards scroll sideways in a row and do not overlap", r["cardsScroll"] and not r["overlap"], str(r))
    check("talent mobile 390px: the Remove buttons are 44px or more, the chart fits its panel", r["removeSize"] >= 44 and r["svgW"] <= r["fitW"], str(r))
    # the first column stays in place while the table scrolls
    sticky = b.eval("""(() => { const w = document.querySelector('#cmpSkills .cmp-scroll'); w.scrollLeft = 160; const th = w.querySelector('tbody th'); const left = th.getBoundingClientRect().left - w.getBoundingClientRect().left;
      const next = w.querySelector('tbody td').getBoundingClientRect(); const first = th.getBoundingClientRect(); return { left, scrolled: w.scrollLeft, noOverlap: next.left >= first.right - 1 || next.right <= first.left + 1 || true }; })()""", False)
    check("talent mobile 390px: the first column stays at the left edge while the table is scrolled", sticky["scrolled"] > 100 and abs(sticky["left"]) <= 2, str(sticky))
    shot(b, "07-talent-mobile-5-jobs.png")
    b.eval("document.querySelector('#cmpSkills').scrollIntoView()", False)
    shot(b, "08-talent-mobile-skills-view.png", full=False)
    # the pair matrix and the 3 fit panels at small width: no horizontal overflow of the page
    no_problems(b, "talent mobile 390px: no console error, no CSP error")
    set_viewport(b, 1280, 900)
    set_basket(b, "job", [])


# ---------------------------------------------------------------- the checks: employer
def candidates_for(api, tok, job_id, n):
    status, data = api.call("GET", f"/recruiter/candidates?jobId={job_id}&pageSize=50&sort=best", token=tok)
    return (data or {}).get("items", [])[:n] if status == 200 else []


def check_employer_page(b, api, tok, ids, job_id, label):
    status, res = api.call("GET", f"/recruiter/compare?ids={','.join(ids)}&jobId={job_id}", token=tok)
    check(f"{label}: the API answers 200", status == 200, str(res)[:200])
    if status != 200:
        return None
    cands = res["candidates"]
    n = len(cands)
    check(f"{label}: h1 is 'Compare talent'", text_of(b, "h1") == "Compare talent")
    check(f"{label}: address has ids and jobId; basket has the ids", hash_ids(b) == ids and hash_param(b, "jobId") == job_id and basket_ids(b, "talent") == ids, f"{hash_ids(b)} {hash_param(b, 'jobId')}")
    cards = b.eval("[...document.querySelectorAll('.cmp-card')].map(c => ({alias: c.querySelector('.cmp-card-title').innerText.trim(), href: c.querySelector('.cmp-card-title a').getAttribute('href'), facts: [...c.querySelectorAll('.cmp-facts dt')].map(d => d.textContent.trim()), remove: c.querySelector('[data-remove]').getAttribute('aria-label')}))", False)
    check(f"{label}: {n} cards: alias, a link to the profile for this job, Level, Experience, Roles, skills; Remove names the alias",
          [c["alias"] for c in cards] == [c["alias"] for c in cands] and all(c["href"] == f"#/candidates/{cd['id']}?jobId={job_id}" for c, cd in zip(cards, cands))
          and all(c["facts"] == ["Level", "Experience", "Roles", "Skills for this job"] for c in cards) and all(c["remove"] == f"Remove {cd['alias']} from compare" for c, cd in zip(cards, cands)), str(cards)[:300])
    # radar
    radar = res["radar"]
    check(f"{label}: radar has {n} series on {len(radar['axes'])} axes, legend names the aliases",
          count(b, ".cmp-panels .radar .rd-series") == n and b.eval("document.querySelector('.cmp-panels .rd-svg').dataset.axes", False) == str(len(radar["axes"]))
          and b.eval("[...document.querySelectorAll('.cmp-panels .rd-legend li span')].map(s => s.innerText.trim())", False) == [s["alias"] for s in radar["series"]])
    rows = table(b, "#cmpRadar table")[1:]
    bad = []
    for i, (ax, row) in enumerate(zip(radar["axes"], rows)):
        nums = [re.match(r"-?\d+\.\d", c["text"]).group(0) if re.match(r"-?\d+\.\d", c["text"]) else c["text"] for c in row[1:]]
        if nums != [f"{s['values'][i]:.1f}" for s in radar["series"]]:
            bad.append((ax["key"], nums))
        note = {"F4": "merit model", "F6": "fit to the job", "skills": "from the skills table"}.get(ax["formula"], ax["formula"])
        if not row[0]["text"].startswith(ax["label"]) or note not in row[0]["text"]:
            bad.append((ax["key"], "name or note", row[0]["text"]))
    check(f"{label}: numbers table equals the API (one decimal) and has a note after each axis name", len(rows) == len(radar["axes"]) and not bad, str(bad)[:400])
    check(f"{label}: the numbers table marks no 'best' person (no ranking)", "Highest" not in text_of(b, "#cmpRadar"))
    # skill matrix
    srows = table(b, "#cmpSkills table")
    body = [r for r in srows[1:] if r[0]["tag"] == "TH" and not r[0]["text"].startswith(("Other skills", "Skills that meet"))]
    matrix = res["skillMatrix"]
    bad = []
    word = {"meets": "Meets", "below": "Below", "missing": "Missing", "related": "Related"}
    if len(body) != len(matrix):
        bad.append(("rows", len(body), len(matrix)))
    for m, row in zip(matrix, body):
        exp_th = f"{m['skill']} Job needs: {level_text(m['required'])} · {'Must have' if m['must'] else 'Nice to have'}"
        if row[0]["text"] != exp_th:
            bad.append(("th", row[0]["text"], exp_th))
        for k, c in enumerate(cands):
            cell = m["byCandidate"][c["id"]]
            got = row[1 + k]["text"]
            exp = word[cell["status"]]
            if not got.startswith(exp) or (cell["level"] is not None and f"Level: {level_text(cell['level'])}" not in got):
                bad.append((m["skill"], c["alias"], got, cell))
    check(f"{label}: skill matrix ({len(matrix)} rows): first column has the skill and the level that the job needs with Must/Nice; each cell has the state word and the level", not bad, str(bad)[:500])
    other = [r for r in srows if r[0]["text"].startswith("Other skills")]
    check(f"{label}: a row 'Other skills' and a footer 'Skills that meet the job' with counts like '5 of 6 skills'", bool(other) and any(r[0]["text"].startswith("Skills that meet") and all(re.match(r"\d+ of \d+ skills?$", c["text"]) for c in r[1:]) for r in srows))
    # qualifications
    q = table(b, "#cmpQuals table")
    bad = []
    for k, c in enumerate(cands):
        certs = [f"{x['name']} ({x['year']})" if x.get("year") else x["name"] for x in c.get("certifications", [])]
        awards = [f"{x['name']} ({x['year']})" if x.get("year") else x["name"] for x in c.get("awards", [])]
        for rowname, vals in (("Certifications", certs), ("Awards", awards)):
            row = next(r for r in q if r[0]["text"] == rowname)
            cell = row[1 + k]["text"]
            if vals and not all(v in cell for v in vals) or (not vals and "None listed" not in cell):
                bad.append((rowname, c["alias"], cell, vals))
    check(f"{label}: qualifications panel lists certifications and awards (names and years) or 'None listed'", not bad and any(r[0]["text"] == "Qualifications" for r in q), str(bad)[:300])
    check(f"{label}: qualifications panel does not show an issuer or a person name", "issuer" not in text_of(b, "#cmpQuals").lower())
    # areas
    arow = table(b, "#cmpAreas table")[1:]
    bad = []
    ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}
    for area, row in zip(res["areas"], arow):
        pos = {r["id"]: r["position"] for r in area["ranks"]}
        vals = list(pos.values())
        for k, c in enumerate(cands):
            p = pos[c["id"]]
            exp = "Equal" if all(v == vals[0] for v in vals) else ordinal[p] + (" Equal" if vals.count(p) > 1 else "")
            if row[1 + k]["text"] != exp:
                bad.append((area["area"], c["alias"], row[1 + k]["text"], exp))
    check(f"{label}: 'Where the profiles differ': positions inside each area ('1st', '2nd', ties 'Equal'), equal to the API", len(arow) == len(res["areas"]) and not bad, str(bad)[:300])
    check(f"{label}: the muted line says that Jinder does not add the areas up and does not rank people", "does not add the areas up and does not rank people" in text_of(b, "#cmpAreas"))
    page_text = text_of(b, ".compare-page")
    check(f"{label}: no total score, no percentage and no ranking number for a person on the page", not re.search(r"\d+\s?%|\btotal score:|\bscore\s*[:=]?\s*\d|\brank\s*#?\d", page_text, re.I), re.findall(r"\d+\s?%|\bscore\s*[:=]?\s*\d", page_text)[:3].__str__())
    return res


def employer_checks(b, base, api, emp_tok, jobs_own, shots):
    # ---------- Basic: the locked page
    api.call("PUT", "/entitlements", {"plan": "basic"}, token=emp_tok)
    sign_in(b, base, "recruiter@demo.jinder.app", EMPLOYER_PW[0])
    job_id = jobs_own[0]["id"]
    # a Basic list shows 5 talent: ids for the address
    cand5 = candidates_for(api, emp_tok, job_id, 5)
    basket = [{"id": c["id"], "alias": c["alias"]} for c in cand5[:2]]
    set_basket(b, "talent", basket)
    start = mark(b)
    go(b, f"#/compare?ids={','.join(x['id'] for x in basket)}&jobId={job_id}")
    wait_mode(b, "locked")
    b.pump(0.8)
    reqs = api_requests(b, start)
    check("employer Basic: the locked page makes NO compare request and no talent or job request", not [u for u in reqs if re.search(r"/recruiter/(compare|candidates|jobs)", u)], str(reqs))
    check("employer Basic: h1 is 'Compare talent' with a Premium lock badge", text_of(b, "h1") == "Compare talent" and count(b, ".cmp-lockline .locked-badge") == 1)
    txt = text_of(b, ".cmp-locked")
    check("employer Basic: the page explains what Compare does (choose a job, one chart, each skill, certifications and awards, no total and no ranking)",
          all(w in txt for w in ("Choose one of your jobs", "one chart", "each skill", "certifications and awards", "no total score and no ranking of people")), txt[:300])
    check("employer Basic: a sample picture is marked 'Example' and says that it shows no real people", "Example" in text_of(b, ".cmp-example figcaption") and "does not show real people" in text_of(b, ".cmp-example figcaption") and b.eval("document.querySelector('.cmp-example-table').getAttribute('aria-hidden')", False) == "true")
    check("employer Basic: a locked Premium call to action with 'See plans'", count(b, ".cmp-locked .upgrade .locked-badge") == 1 and b.eval("document.querySelector('.cmp-locked .upgrade a').getAttribute('href')", False) == "#/settings?section=plan")
    check("employer Basic: no visible 'Add to compare' button and no job select; the basket was not changed",
          b.eval("[...document.querySelectorAll('[data-add]')].every(e => e.offsetParent === null)", False) is True and not count(b, "#cmpJob") and basket_ids(b, "talent") == [x["id"] for x in basket])
    shot(b, "09-employer-basic-locked.png")
    b.click(".cmp-lockline .locked-badge")
    wait(b, "document.querySelector('dialog.modal[open] h2')", 10)
    check("employer Basic: the lock badge opens the 'Premium feature' dialog", "Premium feature" in text_of(b, "dialog.modal[open] h2"))
    press(b, "Escape", "Escape", 27)
    wait(b, "!document.querySelector('dialog.modal[open]')", 10)
    no_problems(b, "employer Basic: no console error, no CSP error")
    set_viewport(b, 390, 844)
    b.pump(0.6)
    r = b.eval("({ pageW: document.documentElement.scrollWidth, vw: innerWidth })", False)
    check("employer Basic mobile 390px: the locked page does not scroll sideways", r["pageW"] <= r["vw"] + 1, str(r))
    shot(b, "10-employer-basic-locked-mobile.png")
    set_viewport(b, 1280, 900)

    # ---------- Premium
    status, ent = api.call("PUT", "/entitlements", {"plan": "premium"}, token=emp_tok)
    check("employer: the demo switch to Premium works (PUT /entitlements)", status == 200 and ent.get("plan") == "premium", str(ent)[:150])
    cands = candidates_for(api, emp_tok, job_id, 50)
    if len(cands) < 5:
        info("fewer than 5 talent for the first job: employer tests with 5 talent are limited")
    items = [{"id": c["id"], "alias": c["alias"]} for c in cands]
    ids = [c["id"] for c in cands]
    status, jobs_data = api.call("GET", "/recruiter/jobs?pageSize=50", token=emp_tok)
    open_jobs = [j for j in jobs_data["items"] if j["badge"] != "closed"]
    try:
        b.eval("sessionStorage.removeItem(Object.keys(sessionStorage).find(k => k.startsWith('jinder.compare.lastJob')) || '')", False)
    except Exception:  # noqa: BLE001
        pass

    # --- 2 talent
    set_basket(b, "talent", items[:2])
    start = mark(b)
    go(b, "#/compare")
    wait_results(b)
    check("employer: the job select 'For which job?' lists the own non-closed jobs, and the first job is the default", text_of(b, ".cmp-job-field label") == "For which job?"
          and b.eval("[...document.querySelectorAll('#cmpJob option')].map(o => o.textContent.trim())", False) == [j["title"] for j in open_jobs] and b.eval("document.getElementById('cmpJob').value", False) == open_jobs[0]["id"],
          b.eval("[...document.querySelectorAll('#cmpJob option')].map(o => o.textContent.trim())", False).__str__())
    check_employer_page(b, api, emp_tok, ids[:2], open_jobs[0]["id"], "employer 2 talent")
    check_table_a11y(b, "employer 2 talent")
    shot(b, "11-employer-2-talent.png")
    no_problems(b, "employer 2 talent: no console error, no CSP error")

    # --- 5 talent
    set_basket(b, "talent", items[:5])
    go(b, "#/compare")
    wait_results(b)
    check_employer_page(b, api, emp_tok, ids[:5], open_jobs[0]["id"], "employer 5 talent")
    check_series_styles(b, "employer 5 talent", 5)
    check("employer 5 talent: the Add button is disabled at 5", b.eval("document.querySelector('[data-add]').disabled", False))
    shot(b, "12-employer-5-talent.png")

    # --- the 6th is refused
    if len(ids) >= 6:
        start = mark(b)
        go(b, f"#/compare?ids={','.join(ids[:6])}&jobId={open_jobs[0]['id']}")
        wait_results(b)
        reqs = [u for u in api_requests(b, start) if "/recruiter/compare" in u]
        from urllib.parse import unquote
        sent = unquote(re.search(r"ids=([^&]*)", reqs[-1]).group(1)).split(",") if reqs else []
        check("employer: an address with 6 ids sends only the first 5, says so, and keeps 5 in address and basket", sent == ids[:5] and "first 5" in text_of(b, "[data-note]") and hash_ids(b) == ids[:5] and basket_ids(b, "talent") == ids[:5], str(sent))
    else:
        info("fewer than 6 talent: the test of an address with 6 ids was skipped")

    # --- the job select changes the data
    if len(open_jobs) >= 2:
        second = open_jobs[1]
        set_basket(b, "talent", items[:3])
        go(b, "#/compare")
        wait_results(b)
        before = text_of(b, "#cmpSkills .muted")
        start = mark(b)
        b.eval("(() => { const s = document.getElementById('cmpJob'); s.value = %s; s.dispatchEvent(new Event('change', {bubbles: true})); })()" % json.dumps(second["id"]), False)
        b.pump(0.3)
        wait(b, f"document.querySelector('#cmpSkills .muted') && document.querySelector('#cmpSkills .muted').innerText.includes({json.dumps(second['title'])})", WAIT)
        wait_results(b)
        reqs = [u for u in api_requests(b, start) if "/recruiter/compare" in u]
        check("employer job select: changing the job sends a new request with the new jobId", bool(reqs) and f"jobId={second['id']}" in reqs[-1], str(reqs))
        check("employer job select: the address has the new jobId, the page text names the new job", hash_param(b, "jobId") == second["id"] and second["title"] in text_of(b, "#cmpSkills .muted") and second["title"] not in before, hash_param(b, "jobId"))
        check_employer_page(b, api, emp_tok, ids[:3], second["id"], "employer 3 talent, second job")
        stored = b.eval("Object.entries(sessionStorage).filter(([k]) => k.startsWith('jinder.compare.lastJob')).map(([k, v]) => v)", False)
        check("employer job select: the last used job is kept in sessionStorage", stored == [second["id"]], str(stored))
        # leave and come back: the last job is the default
        go(b, "#/notifications")
        wait(b, "location.hash === '#/notifications' && document.querySelector('h1')", 20)
        go(b, "#/compare")
        wait_results(b)
        check("employer job select: after leaving and coming back, the last used job is selected", b.eval("document.getElementById('cmpJob').value", False) == second["id"], b.eval("document.getElementById('cmpJob').value", False))
        # ?jobId= wins over sessionStorage
        go(b, f"#/compare?ids={','.join(ids[:2])}&jobId={open_jobs[0]['id']}")
        wait_results(b)
        check("employer job select: ?jobId= in the address wins over the last used job", b.eval("document.getElementById('cmpJob').value", False) == open_jobs[0]["id"])
        shot(b, "13-employer-3-talent-second-job.png")
    else:
        info("fewer than 2 open jobs for the employer: the job select test was skipped")

    # --- remove: address, basket
    set_basket(b, "talent", items[:4])
    go(b, "#/compare")
    wait_results(b)
    gone = ids[2]
    start = mark(b)
    b.click(f".cmp-card [data-remove='{gone}']")
    wait_results(b)
    expected = [i for i in ids[:4] if i != gone]
    check("employer remove: address and basket lose the id, the page shows 3 cards and 3 lines, a new request has 3 ids",
          hash_ids(b) == expected and basket_ids(b, "talent") == expected and count(b, ".cmp-card") == 3 and count(b, ".cmp-panels .radar .rd-series") == 3
          and bool([u for u in api_requests(b, start) if "/recruiter/compare" in u]))
    check("employer remove: the announcement says that the profile was removed", "removed from compare" in b.eval("document.getElementById('announcer').textContent", False))

    # --- the picker of the employer
    close_picker(b)
    b.click("[data-add]")
    wait_picker(b)
    tabs = b.eval("[...document.querySelectorAll('.cmp-picker [role=tab]')].map(t => t.innerText.trim())", False)
    check("employer picker: tabs 'Talent for this job' and 'Saved talent', a search box by alias, and a list with check boxes", tabs == ["Talent for this job", "Saved talent"] and count(b, ".cmp-picker input[type=search]") == 1 and count(b, ".cmp-pick-check") >= 3, str(tabs))
    first_alias = text_of(b, ".cmp-pick-item .cmp-pick-title")
    check("employer picker: the rows show the alias and short facts, and no name, no score", bool(first_alias) and not re.search(r"%|score", text_of(b, ".cmp-pick-list")))
    marked = b.eval("[...document.querySelectorAll('.cmp-pick-check')].filter(c => c.checked).length", False)
    check("employer picker: items that are chosen already are ticked and marked 'Chosen'", marked >= 1 and b.eval("[...document.querySelectorAll('.cmp-pick-item')].filter(li => li.querySelector('.cmp-pick-check').checked).every(li => !li.querySelector('[data-chosen-chip]').hidden)", False))
    all_before = count(b, ".cmp-pick-item")
    needle = first_alias.split()[0][:3]
    b.fill(".cmp-picker input[type=search]", needle)
    b.pump(0.8)
    shown = b.eval("[...document.querySelectorAll('.cmp-pick-title')].map(t => t.innerText.trim())", False)
    check("employer picker: search by alias filters the list", 0 < len(shown) <= all_before and all(needle.lower() in s.lower() for s in shown), f"{needle} {shown[:5]}")
    shot(b, "14-employer-picker.png", full=False)
    # a saved talent shows in the Saved tab
    api.call("PUT", f"/recruiter/candidates/{ids[-1]}/save", token=emp_tok)
    b.click("[data-tab=saved]")
    wait_picker(b)
    check("employer picker: after Save on a profile, the tab 'Saved talent' lists it", ids[-1] in b.eval("[...document.querySelectorAll('.cmp-pick-check')].map(c => c.dataset.id)", False))
    press(b, "Escape", "Escape", 27)
    wait(b, "!document.querySelector('dialog.cmp-picker-dialog')", 10)
    check("employer picker: Esc closes it and the focus returns to the Add button", b.eval("document.activeElement.matches('[data-add]')", False))
    no_problems(b, "employer picker: no console error, no CSP error")

    # --- mobile
    set_basket(b, "talent", items[:5])
    go(b, "#/compare")
    wait_results(b)
    set_viewport(b, 390, 844)
    b.pump(0.8)
    r = b.eval("""(() => { const w = document.querySelector('#cmpSkills .cmp-scroll'); w.scrollLeft = 160; const th = w.querySelector('tbody th');
      return { pageW: document.documentElement.scrollWidth, vw: innerWidth, scrolls: w.scrollWidth > w.clientWidth + 20, left: th.getBoundingClientRect().left - w.getBoundingClientRect().left, region: w.getAttribute('role'),
               select: document.getElementById('cmpJob').getBoundingClientRect().width <= innerWidth }; })()""", False)
    check("employer mobile 390px: no sideways scroll of the page; the skills table scrolls inside a region with a sticky first column", r["pageW"] <= r["vw"] + 1 and r["scrolls"] and abs(r["left"]) <= 2 and r["region"] == "region" and r["select"], str(r))
    shot(b, "15-employer-mobile-5-talent.png")
    set_viewport(b, 1280, 900)

    # --- the plan ends while the page is open: 403 PREMIUM_REQUIRED shows the locked page
    if len(open_jobs) >= 2:
        go(b, f"#/compare?ids={','.join(ids[:2])}&jobId={open_jobs[0]['id']}")
        wait_results(b)
        api.call("PUT", "/entitlements", {"plan": "basic"}, token=emp_tok)
        b.eval("(() => { const s = document.getElementById('cmpJob'); s.value = %s; s.dispatchEvent(new Event('change', {bubbles: true})); })()" % json.dumps(open_jobs[1]["id"]), False)
        wait_mode(b, "locked")
        check("employer: a 403 PREMIUM_REQUIRED during use shows the locked page with a message", "does not include Compare" in text_of(b, ".compare-page") and count(b, ".cmp-locked") == 1)
        shot(b, "16-employer-plan-ended.png", full=False)
        no_problems(b, "employer plan ended: no console error except the 403", ignore=("/recruiter/compare", "403"))
    api.call("PUT", "/entitlements", {"plan": "basic"}, token=emp_tok)


# ---------------------------------------------------------------- static files
def check_static(base):
    for name in ("styles-compare.css", "js/views/compare.js"):
        with urllib.request.urlopen(f"{base}/{name}", timeout=10) as r:
            body = r.read().decode("utf-8")
            check(f"static: {name} is served (200)", r.status == 200)
            if name.endswith(".css"):
                check("static: styles-compare.css has the owner line and no raw hex colour", body.startswith("/* owned by FE-Compare") and not re.search(r"#[0-9a-fA-F]{3,8}\b", body.split("*/", 1)[1]))
            else:
                check("compare.js: exports compareView, uses the shared radar and compare store, and has no inline style, eval or fetch", "export async function compareView(root, ctx)" in body and "radarHtml" in body and "compareStore" in body
                      and not re.search(r"\bstyle\s*=|\beval\(|new Function|\bfetch\(", body))
    html = urllib.request.urlopen(f"{base}/index.html", timeout=10).read().decode("utf-8")
    check("index.html links styles-compare.css", 'href="styles-compare.css"' in html)


TALENT_PW = [""]
EMPLOYER_PW = [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--talent-pw", default="")
    ap.add_argument("--employer-pw", default="")
    ap.add_argument("--shots", default=os.path.join(tempfile.gettempdir(), "jinder-fe-compare-shots"))
    ap.add_argument("--debug-port", type=int, default=9350)
    ap.add_argument("--port", type=int, default=8150)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--retry-wait", type=int, default=180)
    ap.add_argument("--only", choices=("talent", "employer"), default="", help="run only one part")
    args = ap.parse_args()
    SHOTS[0] = args.shots
    os.makedirs(args.shots, exist_ok=True)

    platform = None
    if args.base:
        base, TALENT_PW[0], EMPLOYER_PW[0] = args.base.rstrip("/"), args.talent_pw, args.employer_pw
    else:
        platform = start_platform(args.port, args.retries, args.retry_wait)
        base = platform.base
        TALENT_PW[0], EMPLOYER_PW[0] = platform.pw.get("candidate@demo.jinder.app", ""), platform.pw.get("recruiter@demo.jinder.app", "")
        info(f"started the platform on {base} (data folder {platform.var})")
    b = None
    try:
        check_static(base)
        api = Api(base)
        talent_tok = api.login("candidate@demo.jinder.app", TALENT_PW[0])
        emp_tok = api.login("recruiter@demo.jinder.app", EMPLOYER_PW[0])
        status, own = api.call("GET", "/recruiter/jobs?pageSize=50", token=emp_tok)
        jobs_own = [j for j in own["items"] if j["badge"] != "closed"]
        # data: 6 open jobs for the talent, at least 2 open jobs for the employer
        jobs = open_jobs_for_talent(api, talent_tok, 6)
        if len(jobs) < 6 and jobs_own:
            made = make_jobs(api, emp_tok, 6 - len(jobs), jobs_own[0])
            NOTES.append(f"created {len(made)} open jobs through POST /recruiter/jobs, because the data had only {len(jobs)} open jobs for the talent")
            jobs = open_jobs_for_talent(api, talent_tok, 6)
        if len(jobs_own) < 2 and jobs_own:
            made = make_jobs(api, emp_tok, 2 - len(jobs_own), jobs_own[0])
            NOTES.append(f"created {len(made)} jobs for the employer, because the employer had only {len(jobs_own)} open job")
            status, own = api.call("GET", "/recruiter/jobs?pageSize=50", token=emp_tok)
            jobs_own = [j for j in own["items"] if j["badge"] != "closed"]
        for note in NOTES:
            info(note)
        info(f"data: {len(jobs)} open jobs for the talent, {len(jobs_own)} open jobs for the employer")
        check("data: at least 5 open jobs for the talent and 1 open job for the employer", len(jobs) >= 5 and len(jobs_own) >= 1)
        b = Browser(port=args.debug_port)
        if args.only in ("", "talent"):
            talent_checks(b, base, api, talent_tok, jobs, args.shots)
        if args.only in ("", "employer"):
            employer_checks(b, base, api, emp_tok, jobs_own, args.shots)
    finally:
        if b:
            pid = b.proc.pid
            b.close()
            kill_tree(pid)
        if platform:
            platform.stop()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    for name, _, detail in failed:
        print("  FAIL:", name, detail)
    if SHOT_FILES:
        print("Screenshots:")
        for path in SHOT_FILES:
            print("  " + path)
    for note in NOTES:
        print("DATA NOTE: " + note)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
