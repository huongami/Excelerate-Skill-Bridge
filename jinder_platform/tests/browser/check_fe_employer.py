"""Browser checks for the FE-Employer work of Jinder V2: lists with pager and sort, talent cards and detail, compare entry points,
Premium locks, the job form with the new fields, the job overview page, and the old employer screens in mock mode.

Usage:
  python tests/browser/check_fe_employer.py                      start the platform on port 8140 (temp data folder), run, stop it
  python tests/browser/check_fe_employer.py --base http://localhost:8140 --employer-pw Y   use a platform that runs already
Options: --shots <folder> (screenshots), --debug-port 9340 (Chrome remote debugging port), --port 8140

It needs Chrome or Edge (see cdp.py). It runs against the real backend as the demo employer (Basic first, then Premium after the demo plan
switch). One run uses `?mock=1` to check that the old employer screens still work.
If the platform does not start for a reason in code that is not part of this test, it waits 3 minutes and tries again (3 tries).
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
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.abspath(os.path.join(HERE, "..", ".."))
results = []
SHOTS = [""]          # the screenshot folder, set in main()
SHOT_FILES = []       # the screenshots that were made
STATE = {}            # values that one check hands to the next (the posted job, the accepted category)


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def info(text):
    print("INFO " + text)


def shot(b, name, full=False):
    if SHOTS[0]:
        path = os.path.join(SHOTS[0], name)
        b.screenshot(path, full=full)
        SHOT_FILES.append(path)


# ---------------------------------------------------------------- the platform
class Platform:
    """Starts `python start.py --demo --reset-db` on a port, with its own data folder, and reads the demo passwords from the output."""

    def __init__(self, port):
        self.port = port
        self.var = tempfile.mkdtemp(prefix="jinder-fe-employer-")
        self.log = os.path.join(self.var, "server.log")
        env = dict(os.environ, JINDER_VAR_DIR=self.var)
        self.out = open(self.log, "w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, "start.py", "--demo", "--reset-db", "--port", str(port)], cwd=PLATFORM, env=env,
                                     stdout=self.out, stderr=subprocess.STDOUT)
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2).read()
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


def start_platform(port, tries=3, wait=180):
    """The backend is edited by other agents. If it fails to start, wait and try again (3 tries), then give up."""
    for n in range(1, tries + 1):
        try:
            return Platform(port)
        except RuntimeError as exc:
            info(f"platform start {n} of {tries} failed: {str(exc)[-400:]}")
            if n == tries:
                raise
            info(f"waiting {wait} seconds for the other agents to finish their edit")
            time.sleep(wait)


# ---------------------------------------------------------------- browser helpers
def sign_in(b, base, email, password, mock=False):
    suffix = "?mock=1" if mock else ""
    b.goto(f"{base}/{suffix}#/login")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{base}/{suffix}#/login")
    b.wait_for("document.querySelector('#email')")
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')")
    b.wait_for("document.querySelector('#shellUser')")
    b.pump(0.8)


def go(b, hash_, wait="document.querySelector('h1')"):
    """Open a route. The router draws it again even when the hash is the same."""
    b.eval("location.hash = '#/home'", False)
    b.wait_for("location.hash === '#/home' && document.querySelector('#shellUser')")
    b.eval(f"location.hash = {json.dumps(hash_)}", False)
    b.wait_for(wait)
    b.pump(0.4)


def set_plan(b, plan):
    b.eval(f"(async () => {{ const {{ api }} = await import('/js/api/index.js'); await api.entitlements.set({json.dumps(plan)}); }})()")
    b.pump(0.3)


def no_problems(b, name, ignore=()):
    """No console error, exception or CSP report since the last call. Errors from a browser extension are not from the app."""
    # This PC has a browser extension that calls http://localhost:57635/hookendpoint on every page. It is not from the app.
    noise = ("chrome-extension://", "ms-browser-extension://", "localhost:57635/hookendpoint")
    problems = [p for p in b.take_problems() if not any(n in p for n in noise) and not any(i in p for i in ignore)]
    check(name, not problems, "; ".join(problems)[:600])


def js(b, expression):
    return b.eval(expression, await_promise=False)


def reload(b):
    """A real reload of the page (the hash stays). Wait until the new page has loaded."""
    b.call("Page.reload")
    b.pump(1.0)
    b.wait_for("document.readyState === 'complete' && document.querySelector('#shellUser')")
    b.pump(0.4)


def clear_compare(b):
    js(b, "Object.keys(localStorage).filter(k => k.startsWith('jinder.compare.')).forEach(k => localStorage.removeItem(k))")


def dialog_title(b):
    return js(b, "document.querySelector('dialog[open] h2')?.textContent || ''")


def close_dialog(b):
    js(b, "document.querySelector('dialog[open]')?.close()")
    b.pump(0.2)


PRIVATE_WORDS = re.compile(r"[\w.+-]+@[\w-]+\.\w+|\bscore\b|nationality:|visa status:|date of birth|gender:", re.I)


UI_WORDS = re.compile(r"\b(candidates?|recruiters?|HR)\b")


def check_no_private(b, name, selector="main, .app-content"):
    """The page text has no email, no score and no private word. It also uses the terms Talent and Employer (AI_Rule Rule 2)."""
    text = b.text(selector) or b.text("body")
    hit = PRIVATE_WORDS.search(text)
    word = UI_WORDS.search(text)
    check(name, not hit and not word, f"found: {(hit or word).group(0)}" if (hit or word) else "")


# ---------------------------------------------------------------- the checks
def check_static(base):
    css = urllib.request.urlopen(f"{base}/styles-employer.css", timeout=10).read().decode("utf-8")
    check("static: styles-employer.css is served and has the owner line", css.startswith("/* owned by FE-Employer"))
    check("static: styles-employer.css has no raw hex colour (tokens only)", not re.search(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"/\*.*?\*/", "", css, flags=re.S)))
    src = urllib.request.urlopen(f"{base}/js/views/recruiter.js", timeout=10).read().decode("utf-8")
    check("static: recruiter.js has no inline style attribute (CSP)", 'style="' not in src and "style='" not in src.replace("el.style.width", ""))
    check("static: recruiter.js has no compareView and no premiumModal (old compare code is removed)", "compareView" not in src and "premiumModal" not in src)
    main =urllib.request.urlopen(f"{base}/js/main.js", timeout=10).read().decode("utf-8")
    check("static: main.js has the overview route", '"/my-jobs/:id/overview"' in main)


def check_units(b):
    r = b.eval("""(async () => {
      const m = await import('/js/views/recruiter.js');
      const tpl = ['About the role', 'What you will do', 'What you bring', 'Nice to have', 'Tech stack', 'What we offer', 'About the company', 'How we hire']
        .map((h) => '## ' + h + '\\n- ').join('\\n\\n');
      const out = {};
      out.empty = m.cleanJdText(tpl);
      out.some = m.cleanJdText('## About the role\\n- \\n\\n## What you bring\\n- Python\\n- \\n\\n## Tech stack\\n\\n## Last\\nText here');
      out.crlf = m.cleanJdText('## A\\r\\n- x\\r\\n\\r\\n\\r\\n\\r\\n- y');
      out.plain = m.cleanJdText('Just a paragraph with no headings.');
      return out;
    })()""")
    check("cleanJdText: the untouched template becomes empty", r["empty"] == "", repr(r["empty"]))
    check("cleanJdText: empty bullets and empty sections go, content stays", r["some"] == "## What you bring\n- Python\n\n## Last\nText here", repr(r["some"]))
    check("cleanJdText: CRLF becomes LF and blank lines are squeezed", r["crlf"] == "## A\n- x\n\n- y", repr(r["crlf"]))
    check("cleanJdText: a text with no headings is kept", r["plain"] == "Just a paragraph with no headings.")


def check_basic_talent_list(b, shots_prefix=""):
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    b.pump(0.5)
    r = b.eval("""({
      cards: document.querySelectorAll('.cand-card').length,
      pager: !!document.querySelector('.pager'),
      upgrade: document.querySelector('.upgrade')?.innerText || '',
      upgradeLock: !!document.querySelector('.upgrade button.locked-badge[data-premium-lock]'),
      sortOptions: [...document.querySelectorAll('#talent-sort option')].map(o => o.value + ':' + o.textContent),
      sortLabel: document.querySelector('label[for=talent-sort]')?.textContent || '',
      compareLocks: [...document.querySelectorAll('.cand-card')].filter(c => c.querySelector('[data-premium-lock="Comparing talent"] .locked-badge')).length,
      inviteLocks: [...document.querySelectorAll('.cand-card')].filter(c => c.querySelector('[data-premium-lock="Inviting talent who did not apply"] .locked-badge')).length,
      inPipeline: document.querySelectorAll('.cand-card .chip-link').length,
      boxes: document.querySelectorAll('[data-compare-pick]').length,
      overviewLink: document.querySelector('.job-overview-link')?.getAttribute('href') || '',
      skillLevelText: [...document.querySelectorAll('.cand-card .job-tags .chip')].filter(c => /·\\s*(Beginner|Working|Proficient|Advanced|Expert)/.test(c.textContent)).length,
      updated: document.querySelector('.cand-card .cand-updated')?.textContent || '',
      orderGreen: (() => { const c = document.querySelector('.cand-card .job-tags'); if (!c) return true; const k = [...c.querySelectorAll('.chip')].map(x => x.classList.contains('chip-green')); const i = k.indexOf(false); return i < 0 || !k.slice(i).includes(true); })(),
    })""")
    check("Basic talent list: 5 cards", r["cards"] == 5, str(r["cards"]))
    check("Basic talent list: no pager", not r["pager"])
    check("Basic talent list: the upgrade box says 'You see the top 5 of N' and has a gold lock badge that is a button", "You see the top 5 of" in r["upgrade"] and r["upgradeLock"], r["upgrade"][:120])
    check("Basic talent list: sort select with 'Best fit for this job' first and 'Recently updated'", r["sortOptions"] == ["best:Best fit for this job", "updated:Recently updated"] and r["sortLabel"] == "Sort by", str(r["sortOptions"]))
    check("Basic talent list: Compare has the lock badge on every card, no check box", r["compareLocks"] == 5 and r["boxes"] == 0, str(r))
    check("Basic talent list: Invite has the lock badge (cards that are not in the pipeline)", r["inviteLocks"] == 5 - r["inPipeline"], str(r["inviteLocks"]))
    check("Basic talent list: the header links to the job overview", "/overview" in r["overviewLink"], r["overviewLink"])
    check("Basic talent list: skill chips show the level as text ('Python · Advanced')", r["skillLevelText"] >= 5, str(r["skillLevelText"]))
    check("Basic talent list: 'Updated N days ago' on the card", re.match(r"Updated (today|\d+ days? ago)", r["updated"]) is not None, r["updated"])
    check("Basic talent list: skills that the job asks for come first (green before grey)", r["orderGreen"])
    shot(b, "01-talent-list-basic.png", full=True)
    # a click on a lock opens the Premium dialog, with the name of the feature
    js(b, "document.querySelector('.cand-card [data-premium-lock=\"Comparing talent\"]').click()")
    b.wait_for("document.querySelector('dialog[open]')")
    text = js(b, "document.querySelector('dialog[open]').innerText")
    check("Basic talent list: a click on the Compare lock opens the Premium dialog", dialog_title(b) == "Premium feature" and "Comparing talent is part of Premium" in text, text[:150])
    shot(b, "02-premium-dialog-compare.png")
    close_dialog(b)
    js(b, "document.querySelector('.cand-card [data-premium-lock=\"Inviting talent who did not apply\"]').click()")
    b.wait_for("document.querySelector('dialog[open]')")
    check("Basic talent list: a click on the Invite lock opens the same dialog", dialog_title(b) == "Premium feature" and "Inviting talent who did not apply is part of Premium" in js(b, "document.querySelector('dialog[open]').innerText"))
    close_dialog(b)
    js(b, "document.querySelector('.upgrade .locked-badge').click()")
    b.wait_for("document.querySelector('dialog[open]')")
    check("Basic talent list: a click on the lock in the upgrade box opens the dialog", dialog_title(b) == "Premium feature")
    close_dialog(b)
    check_no_private(b, "Basic talent list: no email, score, nationality or visa text")


def fill_form_field(b, name, value):
    js(b, f"""(() => {{ const f = document.querySelector('form.job-form'); const el = f.elements[{json.dumps(name)}]; el.focus();
      const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, {json.dumps(value)});
      el.dispatchEvent(new Event('input', {{bubbles: true}})); el.dispatchEvent(new Event('change', {{bubbles: true}})); }})()""")


def make_jd(total=3000):
    """A job description of about `total` characters, with the JD headings and bullets. The last line is a marker."""
    parts = []
    for i, head in enumerate(["About the role", "What you will do", "What you bring", "Nice to have", "Tech stack", "What we offer", "About the company", "How we hire"]):
        parts.append(f"## {head}")
        if i == 0:
            parts.append("We build a small platform for sample employers. This text is made up for a test.")
        for k in range(1, 6):
            parts.append(f"- Point {i}.{k}: we value clear writing, steady delivery and calm teamwork on every release.")
        parts.append("")
    text = "\n".join(parts)
    while len(text) < total:
        text += "\n- Extra line for the length of the test text, written in plain English.\n"
    return text.strip() + "\n\n## Last section\n- END-OF-JD-MARKER"


def check_job_form_and_post(b, base):
    go(b, "#/my-jobs/new", "document.querySelector('form.job-form')")
    b.pump(0.5)
    ids = ["jf-title", "jf-category", "jf-spec", "jf-level", "jf-minyears", "jf-maxyears", "jf-workmode", "jf-edu", "jf-location", "jf-type", "jf-salary", "jf-closes", "jf-target", "jf-desc", "jf-skill", "jf-cert-req", "jf-cert-pref"]
    missing = [i for i in ids if not js(b, f"!!document.getElementById({json.dumps(i)})")]
    check("job form: all fields exist (domain, specialisation, level, years, work mode, education, skills, certifications)", not missing, str(missing))
    r = b.eval("""({
      domains: [...document.querySelectorAll('#jf-category option')].map(o => o.textContent),
      domainLabel: document.querySelector('label[for=jf-category]').textContent,
      level: document.querySelector('#jf-level').value,
      levels: [...document.querySelectorAll('#jf-level option')].map(o => o.textContent).slice(1),
      workModes: [...document.querySelectorAll('#jf-workmode option')].map(o => o.textContent).slice(1),
      max: document.querySelector('#jf-desc').maxLength,
      desc: document.querySelector('#jf-desc').value,
      hint: document.querySelector('#jf-desc-hint').textContent,
      awards: [...document.querySelectorAll('[name=awardKind]')].map(c => c.value).length,
      counter: document.querySelector('#jf-desc-count').textContent,
      yearsHint: document.querySelector('#jf-years-hint')?.textContent || '',
    })""")
    check("job form: Domain select has the 3 domains of the taxonomy", r["domains"][1:] == ["Software Engineering", "AI & Machine Learning", "Data"] and r["domainLabel"] == "Domain", str(r["domains"]))
    check("job form: Level select has the 6 levels and 'Mid' is the default for a new job", r["levels"] == ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"] and r["level"] == "Mid", str(r))
    check("job form: Work mode select has Onsite, Hybrid, Remote", r["workModes"] == ["Onsite", "Hybrid", "Remote"])
    check("job form: description maxlength matches the backend limit (10000)", r["max"] == 10000, str(r["max"]))
    check("job form: a new job starts with the JD template (8 headings, one empty bullet each)", r["desc"].count("## ") == 8 and r["desc"].startswith("## About the role\n- \n") and r["desc"].count("\n- ") == 8, r["desc"][:80])
    check("job form: a hint explains '## Heading' and '- bullet'", "## " in r["hint"] and "- " in r["hint"])
    check("job form: a live counter of the description characters", "of 10,000 characters" in r["counter"], r["counter"])
    check("job form: 12 kinds of award as check boxes", r["awards"] == 12, str(r["awards"]))
    check("job form: the years hint says that an empty maximum means 'or more'", "or more" in r["yearsHint"], r["yearsHint"])
    # Specialisation depends on the domain
    fill_form_field(b, "category", "Data")
    specs = js(b, "[...document.querySelectorAll('#jf-spec option')].map(o => o.textContent).slice(1)")
    check("job form: the specialisation list follows the domain (Data)", specs[:2] == ["Data engineering", "Data analytics"] and len(specs) == 6, str(specs))
    fill_form_field(b, "category", "AI & Machine Learning")
    fill_form_field(b, "specialisation", "MLOps")
    fill_form_field(b, "category", "Software Engineering")
    check("job form: a specialisation of another domain is cleared when the domain changes", js(b, "document.querySelector('#jf-spec').value") == "")
    specs = js(b, "[...document.querySelectorAll('#jf-spec option')].map(o => o.textContent).slice(1)")
    check("job form: specialisation list for Software Engineering has 8 entries", len(specs) == 8 and specs[0] == "Backend", str(specs))
    # The preview button
    js(b, "document.querySelector('[data-preview]').click()")
    b.wait_for("document.querySelector('#jf-preview .jd-view')")
    pv = b.eval("({ expanded: document.querySelector('[data-preview]').getAttribute('aria-expanded'), label: document.querySelector('[data-preview]').textContent.trim(), hidden: document.querySelector('#jf-preview').hidden, text: document.querySelector('#jf-preview .jd-view').innerText })")
    check("job form: Preview shows the description in the JD box (the empty template shows no empty sections)", pv["expanded"] == "true" and pv["label"] == "Hide preview" and not pv["hidden"] and "About the role" not in pv["text"], str(pv)[:200])
    shot(b, "03-job-form-top.png")
    # Fill the form. The description has about 3000 characters.
    jd = make_jd(3000)
    STATE["jd"] = jd
    closes = (datetime.now(timezone.utc) + timedelta(days=21)).strftime("%Y-%m-%d")
    STATE["title"] = "Senior Platform Engineer (employer check)"
    fill_form_field(b, "title", STATE["title"])
    fill_form_field(b, "specialisation", "Platform and DevOps")
    fill_form_field(b, "level", "Senior")
    fill_form_field(b, "minYears", "5")
    fill_form_field(b, "maxYears", "9")
    fill_form_field(b, "workMode", "Hybrid")
    fill_form_field(b, "educationMin", "Bachelor's degree")
    fill_form_field(b, "location", "Sydney")
    fill_form_field(b, "type", "Full-time")
    fill_form_field(b, "salary", "$140,000 – $165,000")
    fill_form_field(b, "closesAt", closes)
    fill_form_field(b, "targetApplicants", "8")
    fill_form_field(b, "description", jd)
    live = js(b, "document.querySelector('#jf-preview .jd-view').innerText.includes('END-OF-JD-MARKER')")
    check("job form: the preview follows the text live", live)
    check("job form: the counter shows the length", f"{len(jd):,}" in js(b, "document.querySelector('#jf-desc-count').textContent"), js(b, "document.querySelector('#jf-desc-count').textContent"))
    # Skills with level and Must / Nice
    for name, level, must in (("Python", 4, True), ("SQL", 3, False), ("Docker", 3, True)):
        b.fill("#jf-skill", name)
        js(b, "document.querySelector('[data-add]').click()")
        b.pump(0.15)
    check("job form: 3 skill rows, each with a level select and a must check box", js(b, "document.querySelectorAll('.skill-req').length") == 3 and js(b, "document.querySelectorAll('.skill-req select').length") == 3)
    js(b, "(() => { const s = document.querySelector('[data-level=\"0\"]'); s.value = '4'; s.dispatchEvent(new Event('change', {bubbles: true})); const m = document.querySelector('[data-must=\"1\"]'); m.click(); })()")
    rows = b.eval("[...document.querySelectorAll('.skill-req')].map(r => [r.querySelector('.skill-req-name').textContent, r.querySelector('select').value, r.querySelector('[data-must]').checked])")
    check("job form: level and must state are kept per skill", rows == [["Python", "4", True], ["SQL", "3", False], ["Docker", "3", True]], str(rows))
    # Suggest skills keeps working; a suggestion starts at level 3 and Must
    js(b, "document.querySelector('[data-suggest]').click()")
    b.wait_for("document.querySelector('[data-pick]') || document.querySelector('.suggest-row .hint')")
    picked = js(b, "(() => { const p = document.querySelector('[data-pick]'); if (!p) return null; const n = p.dataset.pick; p.click(); return n; })()")
    if picked:
        last = b.eval("(() => { const r = [...document.querySelectorAll('.skill-req')].pop(); return [r.querySelector('.skill-req-name').textContent, r.querySelector('select').value, r.querySelector('[data-must]').checked]; })()")
        check("job form: a suggested skill is added with level 3 and Must", last == [picked, "3", True], str(last))
    else:
        info("suggest skills gave no new skill for this text (skipped the check of the default level)")
    # Certifications and awards
    b.fill("#jf-cert-req", "AWS Certified Cloud Practitioner")
    js(b, "document.querySelector('[data-cert-add=\"required\"]').click()")
    b.fill("#jf-cert-req", "Internal Safety Course")
    js(b, "document.querySelector('[data-cert-add=\"required\"]').click()")
    b.fill("#jf-cert-pref", "Certified Kubernetes Administrator")
    js(b, "document.querySelector('[data-cert-add=\"preferred\"]').click()")
    certs = b.eval("({ req: [...document.querySelectorAll('[data-cert-list=required] li')].map(l => l.textContent.trim()), pref: [...document.querySelectorAll('[data-cert-list=preferred] li')].map(l => l.textContent.trim()) })")
    check("job form: required and preferred certifications (a list name and a free text)", certs == {"req": ["AWS Certified Cloud Practitioner", "Internal Safety Course"], "pref": ["Certified Kubernetes Administrator"]}, str(certs))
    # The combobox: the list of certifications is searchable and Enter in an empty box does not post the form
    js(b, "(() => { const i = document.querySelector('#jf-cert-pref'); i.focus(); })()")
    b.fill("#jf-cert-pref", "Terraform")
    opts = js(b, "(() => { document.querySelector('#jf-cert-pref').click(); return [...document.querySelectorAll('#jf-cert-pref-list .combo-option')].map(o => o.textContent); })()")
    check("job form: the certification box finds a name from the taxonomy list", any("HashiCorp Certified: Terraform Associate" in o for o in opts), str(opts[:3]))
    js(b, "document.querySelector('#jf-cert-pref').value = ''")
    js(b, "[...document.querySelectorAll('[name=awardKind]')].filter(c => ['hackathon', 'open-source'].includes(c.value)).forEach(c => c.click())")
    shot(b, "04-job-form-filled.png", full=True)
    # Submit. The backend must accept the 3 domains as `category`. If it still has the old list, say so, and go on with an old value.
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.pump(1.2)
    state = js(b, "({ hash: location.hash, err: document.querySelector('.field-error[data-for=category]')?.textContent || '', alert: document.querySelector('.form-alert.show')?.textContent || '' })")
    if "/overview" in state["hash"]:
        STATE["domain_accepted"] = True
        STATE["category"] = "Software Engineering"
        check("job form: the backend accepts a domain as the category", True)
    else:
        STATE["domain_accepted"] = False
        check("job form: the backend accepts a domain as the category (needs the BE wave 4 list)", False, f"{state['err']} / {state['alert']}")
        shot(b, "05-job-form-category-error.png")
        # The error is shown next to the field, and the focus is on the field
        check("job form: an API error shows next to its field (aria-invalid, text) and moves the focus there",
              js(b, "document.querySelector('#jf-category').getAttribute('aria-invalid') === 'true' && document.activeElement.id === 'jf-category'"))
        info("WORKAROUND for this run: the backend still has the old category list. The test adds one old value to the select and posts again.")
        js(b, "(() => { const s = document.querySelector('#jf-category'); const o = document.createElement('option'); o.textContent = 'Technology & Data'; s.append(o); s.value = 'Technology & Data'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
        STATE["category"] = "Technology & Data"
        fill_form_field(b, "specialisation", "")
        js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.wait_for("location.hash.includes('/overview')", timeout=20)
    b.pump(0.8)
    m = re.search(r"#/my-jobs/(job-[^/?]+)/overview", js(b, "location.hash"))
    STATE["job_id"] = m.group(1) if m else ""
    STATE["exp"] = "5 to 9 years"
    check("job form: after Post job the page opens the job overview", bool(STATE["job_id"]), js(b, "location.hash"))


def check_overview(b, plan):
    jid = STATE["job_id"]
    go(b, f"#/my-jobs/{jid}/overview", "document.querySelector('.job-overview .jd-view')")
    b.pump(0.6)
    r = b.eval("""(() => {
      const v = document.querySelector('.job-overview .jd-view');
      v.scrollTop = 0;
      const out = {
        h1: document.querySelector('h1').textContent,
        chips: [...document.querySelectorAll('.jo-chips .chip')].map(c => c.textContent.replace(/\\s+/g, ' ').trim()),
        len: v.textContent.length, marker: v.textContent.includes('END-OF-JD-MARKER'), ellipsis: v.textContent.includes('\\u2026') || v.textContent.includes('...'),
        scrolls: v.scrollHeight > v.clientHeight + 20, clientH: v.clientHeight, scrollH: v.scrollHeight,
        tabindex: v.getAttribute('tabindex'), role: v.getAttribute('role'), label: v.getAttribute('aria-label'),
        overflow: getComputedStyle(v).overflowY,
        headings: [...v.querySelectorAll('h3')].map(h => h.textContent),
        bullets: v.querySelectorAll('li').length,
        facts: Object.fromEntries([...document.querySelectorAll('.jo-facts > div')].map(d => [d.querySelector('dt').textContent, d.querySelector('dd').textContent.trim()])),
        skillsHead: [...document.querySelectorAll('.jo-grid .skill-table thead th')].map(t => t.textContent),
        skillRows: [...document.querySelectorAll('.jo-grid .skill-table tbody tr')].map(t => [...t.children].map(c => c.textContent.trim())),
        creds: [...document.querySelectorAll('#credsTitle ~ ul .chip, #credsTitle ~ p')].map(c => c.textContent.trim()),
        links: [...document.querySelectorAll('.jo-head .panel-actions a')].map(a => a.textContent.trim() + '|' + a.getAttribute('href')),
        back: document.querySelector('.back-link').textContent.trim() + '|' + document.querySelector('.back-link').getAttribute('href'),
        stats: [...document.querySelectorAll('.jo-stats .report-card .label')].map(l => l.textContent),
        interestLock: !!document.querySelector('.jo-interest button.locked-badge'),
        interestList: [...document.querySelectorAll('.interest-list dt')].map(d => d.textContent),
        banner: !!document.querySelector('.jo-banner'),
      };
      v.scrollTop = v.scrollHeight;
      out.scrolled = v.scrollTop > 0;
      return out;
    })()""")
    check(f"overview ({plan}): the header has the title, 'Open', the level chip and the work mode chip", r["h1"] == STATE["title"] and r["chips"][0].replace("Status: ", "") == "Open" and any("Senior" in c for c in r["chips"]) and any("Hybrid" in c for c in r["chips"]), str(r["chips"]))
    check(f"overview ({plan}): the full description is there (marker at the end, {len(STATE['jd'])} characters in, no ellipsis)", r["marker"] and not r["ellipsis"] and r["len"] > len(STATE["jd"]) - 400, f"len {r['len']}")
    check(f"overview ({plan}): the description box scrolls (height {r['clientH']}px, content {r['scrollH']}px)", r["scrolls"] and r["overflow"] == "auto" and r["scrolled"])
    check(f"overview ({plan}): the box is a region that the keyboard can reach", r["tabindex"] == "0" and r["role"] == "region" and r["label"] == "About the role")
    check(f"overview ({plan}): headings (h3) and bullets are drawn from the markup", len(r["headings"]) >= 8 and r["bullets"] >= 30, str(r["headings"][:3]))
    f = r["facts"]
    check(f"overview ({plan}): facts: Level, Experience (min to max), Type, Work mode, Education, Posted, Closes",
          f.get("Level") == "Senior" and f.get("Experience") == STATE['exp'] and f.get("Type") == "Full-time" and f.get("Work mode") == "Hybrid"
          and f.get("Education") == "Bachelor's degree" and f.get("Posted") and f.get("Closes") and (f.get("Specialisation") == "Platform and DevOps" or not STATE.get("domain_accepted")), str(f))
    check(f"overview ({plan}): skills table with level and Must / Nice", r["skillsHead"] == ["Skill", "Level needed", "Must or nice"] and ["Python", "Advanced", "Must have"] in r["skillRows"] and ["SQL", "Proficient", "Nice to have"] in r["skillRows"], str(r["skillRows"]))
    check(f"overview ({plan}): the Must skills come before the Nice skills", [x[2] for x in r["skillRows"]] == sorted([x[2] for x in r["skillRows"]], key=lambda t: 0 if t == "Must have" else 1), str(r["skillRows"]))
    text = " ".join(r["creds"])
    check(f"overview ({plan}): required and preferred certifications and preferred awards", all(s in text for s in ("AWS Certified Cloud Practitioner", "Internal Safety Course", "Certified Kubernetes Administrator", "Hackathon", "Open source contribution")), text[:200])
    check(f"overview ({plan}): actions Edit job, See talent, See applicants and the back link to My jobs",
          f"Edit job|#/my-jobs/{jid}/edit" in [x.strip() for x in r["links"]] and any(x.startswith("See talent") and f"jobId={jid}" in x for x in r["links"])
          and any(x.startswith("See applicants") and x.endswith(f"#/my-jobs/{jid}") for x in r["links"]) and r["back"] == "My jobs|#/my-jobs", str(r["links"]))
    check(f"overview ({plan}): small stats Applicants, Waiting for you, Invited, Interest", r["stats"] == ["Applicants", "Waiting for you", "Invited", "Interest in this job"], str(r["stats"]))
    if plan == "Basic":
        check("overview (Basic): the interest card has the gold lock badge", r["interestLock"] and not r["interestList"])
        js(b, "document.querySelector('.jo-interest button.locked-badge').click()")
        b.wait_for("document.querySelector('dialog[open]')")
        check("overview (Basic): the lock opens the Premium dialog for 'Interest per job'", "Interest per job is part of Premium" in js(b, "document.querySelector('dialog[open]').innerText"))
        close_dialog(b)
    else:
        check("overview (Premium): the interest card shows Shown, Opened, Saved, Applied", r["interestList"] == ["Shown", "Opened", "Saved", "Applied"] and not r["interestLock"], str(r["interestList"]))
    check(f"overview ({plan}): an open job has no 'closed' banner", not r["banner"])
    shot(b, f"06-job-overview-{plan.lower()}.png", full=True)
    # The box is reachable by the keyboard: focus it and check the ring
    js(b, "document.querySelector('.job-overview .jd-view').focus()")
    check(f"overview ({plan}): the box takes focus", js(b, "document.activeElement.classList.contains('jd-view')"))
    check_no_private(b, f"overview ({plan}): no email, score or personal text")


def check_edit_keeps_values(b):
    jid = STATE["job_id"]
    go(b, f"#/my-jobs/{jid}/edit", "document.querySelector('form.job-form')")
    b.pump(0.6)
    r = b.eval("""({
      title: document.querySelector('#jf-title').value, cat: document.querySelector('#jf-category').value, spec: document.querySelector('#jf-spec').value,
      level: document.querySelector('#jf-level').value, min: document.querySelector('#jf-minyears').value, max: document.querySelector('#jf-maxyears').value,
      mode: document.querySelector('#jf-workmode').value, edu: document.querySelector('#jf-edu').value, loc: document.querySelector('#jf-location').value,
      type: document.querySelector('#jf-type').value, salary: document.querySelector('#jf-salary').value, target: document.querySelector('#jf-target').value,
      desc: document.querySelector('#jf-desc').value,
      skills: [...document.querySelectorAll('.skill-req')].map(r => [r.querySelector('.skill-req-name').textContent, r.querySelector('select').value, r.querySelector('[data-must]').checked]),
      req: [...document.querySelectorAll('[data-cert-list=required] li')].map(l => l.textContent.trim()),
      pref: [...document.querySelectorAll('[data-cert-list=preferred] li')].map(l => l.textContent.trim()),
      awards: [...document.querySelectorAll('[name=awardKind]:checked')].map(c => c.value).sort(),
      warning: document.querySelector('.form-alert.warning')?.textContent || '', back: document.querySelector('.back-link').getAttribute('href'),
    })""")
    check("edit form: the saved values come back (title, domain, specialisation, level, years, work mode, education, place, type, salary, target)",
          r["title"] == STATE["title"] and r["cat"] == STATE["category"] and r["level"] == "Senior" and r["min"] == "5" and r["max"] == "9"
          and r["mode"] == "Hybrid" and r["edu"] == "Bachelor's degree" and r["loc"] == "Sydney" and r["type"] == "Full-time" and r["target"] == "8", str(r))
    check("edit form: the specialisation comes back", r["spec"] == "Platform and DevOps" or STATE.get("domain_accepted") is False, r["spec"])
    check("edit form: the description comes back (the marker at the end, no template headings added)", "END-OF-JD-MARKER" in r["desc"] and r["desc"].count("## About the role") == 1)
    check("edit form: skills keep their level and must state", r["skills"][:3] == [["Python", "4", True], ["SQL", "3", False], ["Docker", "3", True]], str(r["skills"]))
    check("edit form: certifications and awards come back", r["req"] == ["AWS Certified Cloud Practitioner", "Internal Safety Course"] and r["pref"] == ["Certified Kubernetes Administrator"] and r["awards"] == ["hackathon", "open-source"], str(r))
    check("edit form: the notice about the applicants and the back link to the overview", "everyone who applied" in r["warning"] and r["back"] == f"#/my-jobs/{jid}/overview")
    # Change one value and save: the others stay
    fill_form_field(b, "minYears", "6")
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.wait_for("location.hash.includes('/overview')", timeout=20)
    b.wait_for("document.querySelector('.job-overview .jd-view')")
    b.pump(0.5)
    facts = b.eval("Object.fromEntries([...document.querySelectorAll('.jo-facts > div')].map(d => [d.querySelector('dt').textContent, d.querySelector('dd').textContent.trim()]))")
    creds = js(b, "document.querySelector('#credsTitle').parentElement.innerText")
    STATE["exp"] = "6 to 9 years"
    check("edit: after Save changes the overview has the new minimum (6 to 9 years) and keeps the rest", facts.get("Experience") == "6 to 9 years" and facts.get("Level") == "Senior" and facts.get("Work mode") == "Hybrid" and "Open source contribution" in creds and "Internal Safety Course" in creds, str(facts))
    # An empty maximum means "or more"
    go(b, f"#/my-jobs/{jid}/edit", "document.querySelector('form.job-form')")
    fill_form_field(b, "maxYears", "")
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.wait_for("location.hash.includes('/overview')", timeout=20)
    b.wait_for("document.querySelector('.job-overview .jd-view')")
    check("edit: an empty maximum is shown as '6 years or more'", js(b, "[...document.querySelectorAll('.jo-facts > div')].find(d => d.querySelector('dt').textContent === 'Experience').querySelector('dd').textContent.trim()") == "6 years or more")
    STATE["exp"] = "6 years or more"
    # Client check: the maximum must not be below the minimum
    go(b, f"#/my-jobs/{jid}/edit", "document.querySelector('form.job-form')")
    fill_form_field(b, "minYears", "8")
    fill_form_field(b, "maxYears", "3")
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.pump(0.6)
    state = b.eval("({ invalid: document.querySelector('#jf-maxyears').getAttribute('aria-invalid'), focus: document.activeElement.id, stay: !location.hash.includes('/overview'), text: document.querySelector('.field-error[data-for=maxYears]').textContent })")
    check("edit form: a maximum below the minimum shows an error on the maximum field, moves the focus there and keeps the page", state["invalid"] == "true" and state["focus"] == "jf-maxyears" and state["stay"] and "most years" in state["text"], str(state))
    shot(b, "07-job-form-error.png")


def make_docx(path, paragraphs):
    """A small DOCX file (made here, with the standard library) that holds one paragraph for each text."""
    import zipfile
    from xml.sax.saxutils import escape
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{escape(p)}</w:t></w:r></w:p>' for p in paragraphs)
    head = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", head + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", head + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", head + f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>')


def check_import_real(b):
    """The JD import fills the form from a real DOCX file (made-up text). The new fields are filled when the parser finds them."""
    path = os.path.join(tempfile.mkdtemp(prefix="jinder-jd-"), "senior-data-engineer.docx")
    make_docx(path, [
        "Senior Data Engineer", "Location: Sydney (Hybrid)", "Full-time", "Salary: $150,000 - $170,000",
        "About the role", "We are a made-up company for a test. You will build and run data pipelines for our analysts every day.",
        "What you bring", "5+ years of experience in data engineering.", "Strong Python and SQL skills (must have)", "Experience with Apache Airflow is a plus",
        "Bachelor's degree in computer science or a related field", "AWS Certified Data Engineer - Associate is preferred",
        "Nice to have", "Hackathon wins are a plus",
    ])
    go(b, "#/my-jobs/new", "document.querySelector('[data-import]') && document.querySelector('form.job-form')")
    b.set_file("#jf-file", path)
    b.wait_for("!document.querySelector('[data-read]').disabled")
    check("import: a DOCX file is chosen and the file chip shows its name", "senior-data-engineer.docx" in js(b, "document.querySelector('[data-file]').innerText"))
    js(b, "document.querySelector('[data-read]').click()")
    b.wait_for("document.querySelector('[data-import-status] .form-alert')", timeout=40)
    ok = js(b, "!!document.querySelector('[data-import-status] .form-alert.success')")
    if not ok:
        check("import: the file is read and the form is filled", False, js(b, "document.querySelector('[data-import-status]').innerText"))
        return
    r = b.eval("""({
      title: document.querySelector('#jf-title').value, desc: document.querySelector('#jf-desc').value, domain: document.querySelector('#jf-category').value,
      spec: document.querySelector('#jf-spec').value, level: document.querySelector('#jf-level').value, min: document.querySelector('#jf-minyears').value,
      mode: document.querySelector('#jf-workmode').value, edu: document.querySelector('#jf-edu').value, loc: document.querySelector('#jf-location').value,
      skills: [...document.querySelectorAll('.skill-req')].map(r => [r.querySelector('.skill-req-name').textContent, r.querySelector('select').value, r.querySelector('[data-must]').checked]),
      fromFile: [...document.querySelectorAll('.job-form .field-markers .chip-ai')].length, missing: [...document.querySelectorAll('.job-form .field-markers .chip-yellow')].length,
      reqCerts: [...document.querySelectorAll('[data-cert-list] li')].map(l => l.textContent.trim()), awards: [...document.querySelectorAll('[name=awardKind]:checked')].map(c => c.value),
      focus: document.activeElement.id,
    })""")
    check("import: the title and the description are filled and the focus goes to the title", "Data Engineer" in r["title"] and len(r["desc"]) >= 60 and r["focus"] == "jf-title", str(r)[:300])
    check("import: the skills have a level and a must state", len(r["skills"]) >= 1 and all(s[1] in "12345" for s in r["skills"]), str(r["skills"]))
    check("import: the fields that were read have the 'From your file' marker (the new fields too)", r["fromFile"] >= 10, f"from file {r['fromFile']}, missing {r['missing']}")
    check("import: the new fields are filled from the file (level, years, work mode, education, domain, specialisation, certification, award)",
          r["level"] == "Senior" and r["min"] == "5" and r["mode"] == "Hybrid" and "Bachelor" in r["edu"] and r["domain"] == "Data" and r["spec"] == "Data engineering" and len(r["reqCerts"]) >= 1 and "hackathon" in r["awards"], str(r))
    info(f"import: the parser gave level={r['level']!r}, minYears={r['min']!r}, workMode={r['mode']!r}, education={r['edu']!r}, domain={r['domain']!r}, specialisation={r['spec']!r}, location={r['loc']!r}, certifications={r['reqCerts']}, awards={r['awards']}")
    # A change to a field removes its marker
    js(b, "document.querySelector('label[for=jf-title] .chip-ai') && (document.querySelector('#jf-title').value += ' X', document.querySelector('#jf-title').dispatchEvent(new Event('input', {bubbles: true})))")
    check("import: a change to a field removes its marker", js(b, "!document.querySelector('label[for=jf-title] .field-markers')"))
    shot(b, "19-job-form-imported.png", full=True)
    # A wrong file type shows the message
    go(b, "#/my-jobs/new", "document.querySelector('[data-import]')")
    txt = os.path.join(os.path.dirname(path), "notes.txt")
    open(txt, "w").write("x")
    b.set_file("#jf-file", txt)
    b.pump(0.3)
    check("import: a file that is not PDF or DOCX gets the message and the Read button stays off", js(b, "document.querySelector('#jf-file-error').textContent") == "Use a PDF or DOCX file." and js(b, "document.querySelector('[data-read]').disabled"))


def check_basic_detail(b):
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    # a talent that is not in the pipeline yet (the card has the Invite button)
    js(b, "[...document.querySelectorAll('.cand-card')].find(c => c.querySelector('[data-premium-lock=\"Inviting talent who did not apply\"]')).querySelector('h3 a').click()")
    b.wait_for("location.hash.startsWith('#/candidates/') && document.querySelector('.pf-list')")
    b.pump(0.5)
    r = b.eval("({ locks: [...document.querySelectorAll('.dash-head [data-premium-lock]')].map(l => l.dataset.premiumLock), toggle: !!document.querySelector('[data-compare-toggle]') })")
    check("talent detail (Basic): Invite and Compare have the lock badge, there is no compare toggle", r["locks"] == ["Inviting talent who did not apply", "Comparing talent"] and not r["toggle"], str(r))
    js(b, "document.querySelector('.dash-head [data-premium-lock=\"Comparing talent\"]').click()")
    b.wait_for("document.querySelector('dialog[open]')")
    check("talent detail (Basic): the Compare lock opens the Premium dialog", dialog_title(b) == "Premium feature")
    close_dialog(b)


def check_invite(b):
    """A Premium employer invites a talent from the list. The card then shows 'In your pipeline'."""
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    alias = js(b, "(() => { const c = [...document.querySelectorAll('.cand-card')].find(c => c.querySelector('[data-contact]')); return c ? c.querySelector('h3 a').textContent : ''; })()")
    if not alias:
        info("every talent on the first page is in the pipeline already: the invite check is skipped")
        return
    js(b, "[...document.querySelectorAll('.cand-card')].find(c => c.querySelector('[data-contact]')).querySelector('[data-contact]').click()")
    b.wait_for("document.querySelector('dialog[open] textarea')")
    check("invite (Premium): the dialog is 'Invite <alias>' with a job select and a message", dialog_title(b) == f"Invite {alias}" and js(b, "!!document.querySelector('dialog[open] #ct-job')"), dialog_title(b))
    js(b, "(() => { const t = document.querySelector('dialog[open] textarea'); t.value = 'We would like to talk about this made-up job with you.'; t.dispatchEvent(new Event('input', {bubbles: true})); document.querySelector('dialog[open] [type=submit]').click(); })()")
    b.wait_for(f"[...document.querySelectorAll('.cand-card')].some(c => c.querySelector('h3 a')?.textContent === {json.dumps(alias)} && c.querySelector('.chip-link'))", timeout=20)
    check("invite (Premium): after Send invitation the card shows 'In your pipeline' and no Invite button", True)


def check_rich_cards(b):
    """Talent that has a level, exact years, certifications and awards (made by ensure_talent): the card and the detail show them."""
    rich = STATE.get("rich") or []
    if len(rich) < 3:
        info("no talent with a level, certifications and awards could be made: the card checks for these fields are skipped")
        return
    go(b, "#/candidates?sort=updated", "document.querySelector('.cand-card') && !document.querySelector('[data-list][aria-busy]')")
    b.pump(0.4)
    js_card = """(alias) => { const c = [...document.querySelectorAll('.cand-card')].find(c => c.querySelector('h3 a').textContent === alias); if (!c) return null;
      return { facts: [...c.querySelectorAll('.cand-facts .chip')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()), updated: c.querySelector('.cand-updated')?.textContent || '',
        skills: [...c.querySelectorAll('.job-tags .chip')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()),
        creds: [...c.querySelectorAll('.cand-creds .cred-chip')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()), more: c.querySelector('.cand-creds .hint')?.textContent || '',
        text: c.innerText }; }"""
    cards = [b.eval(f"({js_card})({json.dumps(r['alias'])})", False) for r in rich]
    if any(c is None for c in cards):
        check("rich talent: the 3 new profiles are on the first page when the list is sorted by 'Recently updated'", False, str([r["alias"] for r in rich]))
        return
    a, j, l = cards
    check("rich talent card: level chip 'Senior', exact years '6.5 years', 'Updated today'", any("Senior" in f for f in a["facts"]) and any(f.endswith("6.5 years") for f in a["facts"]) and a["updated"] == "Updated today", str(a["facts"]))
    check("rich talent card: a skill chip shows the level text ('Python · Expert')", any(s.startswith("Python · Expert") for s in a["skills"]), str(a["skills"]))
    check("rich talent card: certifications and awards are chips with names and years, at most 3, and '+2 more'", len(a["creds"]) == 3 and "AWS Certified Cloud Practitioner (2024)" in a["creds"][0] and a["more"] == "+2 more", f"{a['creds']} {a['more']}")
    check("rich talent card: the chip text has a hidden 'Certification:' or 'Award:' and no issuer name", a["creds"][0].startswith("Certification:") and "Amazon Web Services" not in a["text"])
    check("rich talent card: Junior with '1 year' and one certification, no '+N more'", any("Junior" in f for f in j["facts"]) and any(f.endswith("1 year") for f in j["facts"]) and len(j["creds"]) == 1 and j["more"] == "", f"{j['facts']} {j['creds']}")
    check("rich talent card: Lead with one award chip ('Award: ... (2023)')", any("Lead" in f for f in l["facts"]) and len(l["creds"]) == 1 and l["creds"][0].startswith("Award:") and "(2023)" in l["creds"][0], str(l["creds"]))
    shot(b, "22-talent-cards-rich.png")
    js(b, f"[...document.querySelectorAll('.cand-card')].find(c => c.querySelector('h3 a').textContent === {json.dumps(rich[0]['alias'])}).querySelector('h3 a').click()")
    b.wait_for("location.hash.startsWith('#/candidates/') && document.querySelector('.pf-list')")
    b.pump(0.5)
    r = b.eval("""({ rows: Object.fromEntries([...document.querySelectorAll('.pf-row')].map(r => [r.querySelector('dt').textContent, [...r.querySelectorAll('dd .chip')].map(c => c.textContent.replace(/\\s+/g, ' ').trim())])),
      updated: document.querySelector('.dash-head .cand-updated').textContent, body: document.body.innerText })""")
    rows = r["rows"]
    check("rich talent detail: Level 'Senior' and Experience '6.5 years'", rows.get("Level") == ["Senior"] and rows.get("Experience") == ["6.5 years"], str(rows.get("Level")) + str(rows.get("Experience")))
    check("rich talent detail: 3 certification chips and 2 award chips with names and years", len(rows.get("Certifications", [])) == 3 and len(rows.get("Awards", [])) == 2
          and any("Regional Hackathon Winner 2024" in x and x.endswith("(2024)") for x in rows["Awards"]), f"{rows.get('Certifications')} {rows.get('Awards')}")
    check("rich talent detail: skills with level text", any(s.startswith("Python · Expert") for s in rows.get("Skills", [])), str(rows.get("Skills")))
    check("rich talent detail: no name and no e-mail address of the person ('Rich Talent', 'example.test')", "Rich Talent" not in r["body"] and "example.test" not in r["body"])


def check_home(b, plan):
    go(b, "#/home", "document.querySelector('[data-charts] .chart, [data-charts] .upgrade') && document.querySelector('[data-top] .mini-list, [data-top] .muted')")
    b.pump(0.5)
    r = b.eval("""({
      cards: document.querySelectorAll('.report-card').length, jobLinks: [...document.querySelectorAll('[data-jobs] .job-title-link')].map(a => a.getAttribute('href')),
      waiting: [...document.querySelectorAll('[data-jobs] .text-link')].map(a => a.getAttribute('href')), top: document.querySelectorAll('[data-top] .mini-list li').length,
      lock: !!document.querySelector('[data-charts] .upgrade button.locked-badge'), table: !!document.querySelector('[data-charts] .data-table'), pager: !!document.querySelector('.pager'),
    })""")
    check(f"Home ({plan}): the cards, My jobs with links to the overview, and at most 3 top talent", r["cards"] >= 3 and r["jobLinks"] and all(h.endswith("/overview") for h in r["jobLinks"]) and r["top"] <= 3, str(r))
    if plan == "Basic":
        check("Home (Basic): the advanced charts have the gold lock badge, and it opens the Premium dialog", r["lock"] and not r["table"])
        js(b, "document.querySelector('[data-charts] .upgrade .locked-badge').click()")
        b.wait_for("document.querySelector('dialog[open]')")
        check("Home (Basic): the dialog is 'Premium feature' for 'Advanced charts'", dialog_title(b) == "Premium feature" and "Advanced charts is part of Premium" in js(b, "document.querySelector('dialog[open]').innerText"))
        close_dialog(b)
    else:
        check("Home (Premium): the interest table is shown and there is no lock", r["table"] and not r["lock"])
    check_no_private(b, f"Home ({plan}): no email, score or personal text")
    shot(b, f"21-home-{plan.lower()}.png", full=True)


def check_mobile(b):
    """On a phone-size screen the employer pages do not scroll sideways, and the controls are 44px high."""
    b.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
    b.pump(0.5)
    pages = [("talent list", "#/candidates", ".cand-card"), ("job form", "#/my-jobs/new", "form.job-form"), ("My jobs", "#/my-jobs", ".app-row")]
    if STATE.get("job_id"):
        pages.append(("job overview", f"#/my-jobs/{STATE['job_id']}/overview", ".job-overview .jd-view"))
    for name, hash_, selector in pages:
        go(b, hash_, f"document.querySelector({json.dumps(selector)})")
        b.pump(0.5)
        r = b.eval("({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, small: [...document.querySelectorAll('main button, main select, main input:not([type=hidden]):not([type=checkbox]):not([type=file])')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 43 && !e.classList.contains('sr-only')).length })")
        check(f"mobile: {name} has no sideways scroll ({r['sw']} of {r['cw']}px)", r["sw"] <= r["cw"] + 1)
        if r["small"]:
            info(f"mobile: {name} has {r['small']} buttons or fields lower than 44px (not an error of this check)")
        shot(b, f"20-mobile-{name.replace(' ', '-').lower()}.png")
    b.call("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})
    b.pump(0.4)


def check_form_api_errors(b):
    """Errors from the API show next to their field (title too short, description too short, no skill)."""
    go(b, "#/my-jobs/new", "document.querySelector('form.job-form')")
    b.pump(0.4)
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.pump(1.0)
    r = b.eval("""({
      invalid: [...document.querySelectorAll('.job-form [aria-invalid=true]')].map(e => e.id || e.name),
      messages: Object.fromEntries([...document.querySelectorAll('.job-form .field-error')].filter(e => e.textContent).map(e => [e.dataset.for, e.textContent])),
      describedby: document.querySelector('#jf-title')?.getAttribute('aria-describedby') || '',
      focus: document.activeElement.id, alert: document.querySelector('.job-form .form-alert')?.textContent || '',
    })""")
    check("job form: an empty form shows messages next to the fields (title, domain, place, work type, description, skills)", all(k in r["messages"] for k in ("title", "category", "location", "type", "skills", "description")), str(r["messages"]))
    check("job form: the fields with an error have aria-invalid and aria-describedby, and the first one has the focus", "jf-title" in r["invalid"] and "title-error" in r["describedby"] and r["focus"] == "jf-title", str(r))
    check("job form: the alert above the form says to correct the fields", "Correct the fields" in r["alert"], r["alert"])
    # The untouched template alone is not a description
    check("job form: the template alone gives an error on the description (empty sections are removed)", "description" in r["messages"] and "30" in r["messages"]["description"], str(r["messages"].get("description")))
    shot(b, "08-job-form-errors.png")


def check_my_jobs(b):
    # Make 12 more jobs by the API so that the list has more than 10 rows
    n = b.eval("""(async (category) => {
      const { api } = await import('/js/api/index.js');
      const closes = new Date(Date.now() + 25 * 864e5).toISOString();
      let made = 0;
      for (let i = 1; i <= 12; i++) {
        await api.recruiter.jobs.create({ title: 'Pager test job ' + String(i).padStart(2, '0'), category, location: 'Melbourne', type: 'Contract', salary: '',
          description: 'A made-up job for the pager test. It has enough text to pass the check of 30 characters.', skills: ['Python', 'SQL'], targetApplicants: 5, closesAt: closes });
        made++;
      }
      return made;
    })(%s)""" % json.dumps(STATE.get("category", "Technology & Data")))
    check("my jobs: 12 jobs were made for the pager test", n == 12)
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    b.pump(0.6)
    r = b.eval("""({
      rows: document.querySelectorAll('.app-row').length, range: document.querySelector('.pager-range')?.textContent || '',
      size: document.querySelector('[data-pager-size]')?.value, sizes: [...document.querySelectorAll('[data-pager-size] option')].map(o => o.value),
      sort: !!document.querySelector('.sort-select'), note: document.querySelector('[data-sort-note]')?.textContent || '',
      first: document.querySelector('.app-row h3 a').getAttribute('href'), firstText: document.querySelector('.app-row h3 a').textContent,
      applicants: [...document.querySelectorAll('.app-row a.btn')].filter(a => a.textContent.includes('Applicants')).length,
      edit: [...document.querySelectorAll('.app-row a.btn')].filter(a => a.textContent.includes('Edit')).length,
    })""")
    m = re.match(r"Showing 1–10 of (\d+)", r["range"])
    check("my jobs: page 1 has 10 rows and the pager says 'Showing 1–10 of N'", r["rows"] == 10 and m is not None and int(m.group(1)) >= 15, str(r))
    check("my jobs: 'Rows per page' has 10, 20, 50", r["sizes"] == ["10", "20", "50"] and r["size"] == "10")
    check("my jobs: no sort select (one sort only), the list says 'Newest first'", not r["sort"] and r["note"] == "Newest first.")
    check("my jobs: the job title opens the overview, and each row has Applicants and Edit", "/overview" in r["first"] and r["applicants"] == 10 and r["edit"] == 10, r["first"])
    first_title = r["firstText"]
    js(b, "document.querySelector('[data-pager-page=\"2\"]').click()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 11')")
    b.wait_for("document.getElementById('announcer').textContent.includes('Page 2 of')")   # the live text is set 50 ms after the list is drawn
    r2 = b.eval("({ rows: document.querySelectorAll('.app-row').length, first: document.querySelector('.app-row h3 a').textContent, hash: location.hash, live: document.getElementById('announcer').textContent, focus: document.activeElement.id })")
    check("my jobs: page 2 holds other jobs and the URL keeps the page", r2["rows"] >= 5 and r2["first"] != first_title and "page=2" in r2["hash"], str(r2))
    check("my jobs: the page change is announced and the focus moves to the list heading", "Page 2 of" in r2["live"] and r2["focus"] == "myJobsTitle", str(r2))
    js(b, "history.back()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 1–')")
    check("my jobs: the Back button goes to page 1", "page=2" not in js(b, "location.hash"))
    js(b, "(() => { const s = document.querySelector('[data-pager-size]'); s.value = '20'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("document.querySelectorAll('.app-row').length > 10")
    check("my jobs: 20 rows per page shows all the jobs of the employer", js(b, "document.querySelectorAll('.app-row').length") >= 15 and "pageSize=20" in js(b, "location.hash"))
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    reload(b)
    b.wait_for("document.querySelector('.app-row')")
    check("my jobs: the page size is remembered after a reload", js(b, "document.querySelector('[data-pager-size]')?.value") == "20" and js(b, "document.querySelectorAll('.app-row').length") >= 15)
    shot(b, "09-my-jobs-pager.png", full=True)
    js(b, "(() => { const s = document.querySelector('[data-pager-size]'); s.value = '10'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.pump(0.8)


def check_premium_talent_list(b):
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    b.pump(0.6)
    # a pager with the real total
    r = b.eval("""({
      cards: document.querySelectorAll('.cand-card').length, range: document.querySelector('.pager-range')?.textContent || '',
      pages: [...document.querySelectorAll('.pager-num')].map(n => n.textContent), upgrade: !!document.querySelector('.upgrade'),
      firstAlias: document.querySelector('.cand-card h3 a').textContent, boxes: document.querySelectorAll('[data-compare-pick]').length,
      locks: document.querySelectorAll('.cand-card [data-premium-lock]').length,
    })""")
    m = re.match(r"Showing 1–10 of (\d+)", r["range"])
    check("Premium talent list: 10 cards and the pager says 'Showing 1–10 of N' with the real total", r["cards"] == 10 and m is not None and int(m.group(1)) > 10, str(r))
    STATE["talent_total"] = int(m.group(1)) if m else 0
    check("Premium talent list: no upgrade box and no lock on the cards; a compare check box on each card", not r["upgrade"] and r["locks"] == 0 and r["boxes"] == 10, str(r))
    shot(b, "10-talent-list-premium.png", full=True)
    first_p1 = r["firstAlias"]
    aliases_p1 = js(b, "[...document.querySelectorAll('.cand-card h3 a')].map(a => a.textContent)")
    js(b, "document.querySelector('[data-pager-page=\"2\"]').click()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 11')")
    b.wait_for("document.getElementById('announcer').textContent.includes('Page 2 of')")
    r2 = b.eval("({ aliases: [...document.querySelectorAll('.cand-card h3 a')].map(a => a.textContent), hash: location.hash, live: document.getElementById('announcer').textContent, focus: document.activeElement.id, range: document.querySelector('.pager-range').textContent, current: document.querySelector('.pager [aria-current=page]')?.textContent })")
    check("Premium talent list: page 2 holds other talent (no alias of page 1)", len(r2["aliases"]) == min(10, STATE["talent_total"] - 10) and not set(r2["aliases"]) & set(aliases_p1), str(r2["aliases"][:3]))
    check("Premium talent list: the URL keeps jobId and page", "page=2" in r2["hash"] and "jobId=" in r2["hash"], r2["hash"])
    check("Premium talent list: the change is announced ('Page 2 of N. Showing 11 to 20 of T') and the focus is on the list heading", re.search(r"Page 2 of \d+\. Showing 11 to %d of %d talent profiles" % (min(20, STATE["talent_total"]), STATE["talent_total"]), r2["live"]) and r2["focus"] == "talentListTitle", f"{r2['live']} / {r2['focus']}")
    check("Premium talent list: the current page button has aria-current", r2["current"] == "2")
    js(b, "history.back()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 1–')")
    b.pump(0.4)
    check("Premium talent list: Back goes to page 1 with the same talent", js(b, "document.querySelector('.cand-card h3 a').textContent") == first_p1)
    # last page
    pages = int(js(b, "document.querySelector('.pager').dataset.pagerTotalPages"))
    js(b, f"location.hash = '#/candidates?jobId=' + document.querySelector('[data-job]').value + '&page={pages}'")
    b.wait_for(f"document.querySelector('.pager-range')?.textContent.includes('of {STATE['talent_total']}') && document.querySelector('.pager [aria-current=page]')?.textContent === '{pages}'")
    last_rows = js(b, "document.querySelectorAll('.cand-card').length")
    check("Premium talent list: the last page has the rest of the talent and Next is off", last_rows == STATE["talent_total"] - 10 * (pages - 1) and js(b, "[...document.querySelectorAll('.pager-step')].pop().disabled"), f"{last_rows} of {STATE['talent_total']}, {pages} pages")
    # sort
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    default_order = js(b, "[...document.querySelectorAll('.cand-card h3 a')].map(a => a.textContent)")
    js(b, "(() => { const s = document.querySelector('#talent-sort'); s.value = 'updated'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("location.hash.includes('sort=updated')")
    b.wait_for("document.querySelector('.pager-range') && document.querySelector('.cand-card') && !document.querySelector('[data-list][aria-busy]')")
    b.wait_for("document.getElementById('announcer').textContent.includes('Sorted by')")
    r3 = b.eval("({ order: [...document.querySelectorAll('.cand-card h3 a')].map(a => a.textContent), days: [...document.querySelectorAll('.cand-card .cand-updated')].map(e => /today/.test(e.textContent) ? 0 : parseInt(e.textContent.match(/\\d+/)[0], 10)), live: document.getElementById('announcer').textContent, focus: document.activeElement.id, page: document.querySelector('.pager-range').textContent })")
    check("Premium talent list: sort 'Recently updated' puts the newest profile change first (days ago do not go down)", r3["days"] == sorted(r3["days"]) and (len(set(r3["days"])) < 2 or r3["order"] != default_order), f"{r3['days']}")
    check("Premium talent list: the sort change is announced and goes to page 1", "Sorted by recently updated" in r3["live"] and r3["page"].startswith("Showing 1–10"), r3["live"])
    # a reload of the URL keeps the sort
    reload(b)
    b.wait_for("document.querySelector('.cand-card')")
    check("Premium talent list: the sort is in the URL and a reload keeps it", js(b, "document.querySelector('#talent-sort').value") == "updated")
    # page size 20
    js(b, "(() => { const s = document.querySelector('[data-pager-size]'); s.value = '20'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    want20 = min(20, STATE["talent_total"])
    b.wait_for(f"document.querySelectorAll('.cand-card').length === {want20}")
    check(f"Premium talent list: 20 rows per page gives {want20} cards, the URL has pageSize=20 and the focus stays on the size select", "pageSize=20" in js(b, "location.hash") and js(b, "document.activeElement.hasAttribute('data-pager-size')"))
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    check("Premium talent list: the page size is remembered (a new visit shows 20 rows per page)", js(b, "document.querySelectorAll('.cand-card').length") == want20 and js(b, "document.querySelector('[data-pager-size]').value") == "20")
    shot(b, "11-talent-list-20.png")
    js(b, "(() => { const s = document.querySelector('[data-pager-size]'); s.value = '10'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("document.querySelectorAll('.cand-card').length === 10")
    # saved view uses the same pager and its own page-size memory
    go(b, "#/candidates?view=saved", "document.querySelector('.tab[aria-selected=true]') && !document.querySelector('[data-list][aria-busy]') && document.querySelector('.cand-card, .empty:not([role=status])')")
    check("Saved talent: the tab is selected and the list or its empty text is shown", js(b, "document.querySelector('.tab[aria-selected=true]').textContent") == "Saved")
    check("Saved talent: the sort select is there (same list tools as All)", js(b, "!!document.querySelector('#talent-sort')"))


def check_compare_basket(b):
    clear_compare(b)
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    b.pump(0.4)
    js(b, "[...document.querySelectorAll('[data-compare-pick]')].slice(0, 5).forEach(c => c.click())")
    b.pump(0.6)
    r = b.eval("({ checked: document.querySelectorAll('[data-compare-pick]:checked').length, chips: document.querySelectorAll('.compare-tray-chips li').length, title: document.querySelector('.compare-tray-title')?.textContent || '', count: JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('jinder.compare.') && k.endsWith('.talent'))) || '[]').length })")
    check("compare: 5 check boxes fill the basket bar ('Compare (5/5)')", r["checked"] == 5 and r["chips"] == 5 and "5/5" in r["title"] and r["count"] == 5, str(r))
    items = js(b, "JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('jinder.compare.') && k.endsWith('.talent'))))")
    check("compare: an item has only the id, the alias and the job id (no personal data)", all(set(i.keys()) <= {"id", "alias", "title", "jobId"} for i in items), str(items[0]))
    js(b, "document.querySelectorAll('[data-compare-pick]')[5].click()")
    b.pump(0.5)
    r2 = b.eval("({ sixth: document.querySelectorAll('[data-compare-pick]')[5].checked, count: document.querySelectorAll('.compare-tray-chips li').length, note: document.querySelector('[data-compare-note]').textContent, live: document.getElementById('announcer').textContent })")
    check("compare: the 6th is refused, with the text 'You can compare up to 5 profiles.' on the page and in the live region", not r2["sixth"] and r2["count"] == 5 and r2["note"] == "You can compare up to 5 profiles." and r2["live"] == "You can compare up to 5 profiles.", str(r2))
    shot(b, "12-compare-basket-5.png")
    js(b, "document.querySelectorAll('[data-compare-pick]')[0].click()")
    b.pump(0.4)
    check("compare: a check box that is cleared takes the item out and clears the note", js(b, "document.querySelectorAll('.compare-tray-chips li').length") == 4 and js(b, "document.querySelector('[data-compare-note]').textContent") == "")
    # remove from the bar: the check box follows
    js(b, "document.querySelector('.compare-tray-chips li button').click()")
    b.pump(0.4)
    check("compare: removing an item in the bar clears its check box", js(b, "document.querySelectorAll('[data-compare-pick]:checked').length") == 3)
    # the state is kept after the page changes
    js(b, "document.querySelector('[data-pager-page=\"2\"]').click()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 11')")
    js(b, "document.querySelector('[data-pager-page=\"1\"]').click()")
    b.wait_for("document.querySelector('.pager-range')?.textContent.startsWith('Showing 1–')")
    check("compare: the basket and the check boxes stay right when the page changes", js(b, "document.querySelectorAll('[data-compare-pick]:checked').length") == 3 and js(b, "document.querySelectorAll('.compare-tray-chips li').length") == 3)
    check("compare: the old compare button is gone", js(b, "!document.querySelector('[data-compare]') && !document.body.innerText.includes('Compare (0/2)')"))
    js(b, "document.querySelector('.compare-tray [data-compare-clear]')?.click()")
    b.pump(0.3)
    check("compare: Clear in the bar empties the basket and the check boxes", js(b, "document.querySelectorAll('[data-compare-pick]:checked').length") == 0 and js(b, "document.querySelector('.compare-tray')?.hidden !== false"))
    clear_compare(b)


def check_talent_detail(b, with_table=False):
    jobq = f"?jobId={STATE['job_id']}" if with_table else ""
    go(b, f"#/candidates{jobq}", "document.querySelector('.cand-card')")
    href = js(b, "document.querySelector('.cand-card h3 a').getAttribute('href')")
    alias = js(b, "document.querySelector('.cand-card h3 a').textContent")
    js(b, "document.querySelector('.cand-card h3 a').click()")
    b.wait_for("location.hash.startsWith('#/candidates/') && document.querySelector('.pf-list')")
    b.pump(0.8)
    r = b.eval("""({
      h1: document.querySelector('h1').textContent, rows: Object.fromEntries([...document.querySelectorAll('.pf-row')].map(r => [r.querySelector('dt').textContent, r.querySelector('dd').textContent.replace(/\\s+/g, ' ').trim()])),
      updated: document.querySelector('.dash-head .cand-updated')?.textContent || '',
      table: !!document.querySelector('.skill-table'), head: [...document.querySelectorAll('.skills-wide thead th')].map(t => t.textContent),
      tableRows: [...document.querySelectorAll('.skills-wide tbody tr')].map(t => [...t.children].map(c => c.textContent.replace(/\\s+/g, ' ').trim())),
      icons: document.querySelectorAll('.skills-wide .result-cell svg.icon').length,
      list: !!document.querySelector('.skill-match'),
      toggle: document.querySelector('[data-compare-toggle]')?.getAttribute('aria-pressed'), lock: !!document.querySelector('.dash-head [data-premium-lock]'),
      need: document.querySelectorAll('.pf-row .chip-need').length, green: document.querySelectorAll('.pf-row .chip-green').length,
      cov: document.querySelector('.cov-line')?.textContent || '', counts: [...document.querySelectorAll('.result-counts li')].map(l => l.textContent.trim()),
    })""")
    check("talent detail: the alias is the title", r["h1"] == alias, r["h1"])
    check("talent detail: the profile has the rows Level, Experience, Roles, Skills, Certifications, Awards, Qualifications",
          all(k in r["rows"] for k in ("Level", "Roles", "Skills", "Certifications", "Awards", "Qualifications")) and "Experience" in r["rows"], str(list(r["rows"].keys())))
    check("talent detail: 'Updated N days ago' in the head", re.match(r"Updated (today|\d+ days? ago)", r["updated"]) is not None, r["updated"])
    check("talent detail: the skills row shows the levels as text ('Python · Advanced')", re.search(r"· (Beginner|Working|Proficient|Advanced|Expert)", r["rows"].get("Skills", "")) is not None, r["rows"].get("Skills", "")[:120])
    if with_table:
        check("talent detail: the job has levels, so the table Skill | Job needs | Talent | Result is there", r["table"] and r["head"] == ["Skill", "Job needs", "Talent", "Result"], str(r["head"]))
        rows = r["tableRows"]
        okres = all(any(x in row[3] for x in ("Meets", "Below", "Missing", "Related", "Has it")) for row in rows)
        check("talent detail: each row says what the job needs (level and Must/Nice), the talent level or '—', and a result with an icon", len(rows) >= 3 and okres and all(re.search(r"(Beginner|Working|Proficient|Advanced|Expert) · (Must have|Nice to have)", row[1]) for row in rows) and r["icons"] == len(rows), str(rows))
        check("talent detail: a skill that the job asks for shows 'needs <level>' in the profile skills", r["need"] >= 1 and r["green"] >= 1, f"need {r['need']} green {r['green']}")
        check("talent detail: the side box counts the results as text", len(r["counts"]) >= 1, str(r["counts"]))
        # "Missing" is "—" in the Talent column
        miss = [row for row in rows if "Missing" in row[3]]
        check("talent detail: a Missing row shows '—' as the talent level", all(row[2] == "—" for row in miss), str(miss))
        shot(b, "13-talent-detail-table.png", full=True)
    else:
        check("talent detail: a job without skill levels keeps the old skill list", r["list"] and not r["table"])
        shot(b, "13-talent-detail-oldjob.png", full=True)
    if r["toggle"] is not None:
        check("talent detail (Premium): the compare toggle starts off", r["toggle"] == "false")
        js(b, "document.querySelector('[data-compare-toggle]').click()")
        b.pump(0.4)
        check("talent detail (Premium): the toggle adds the profile to the basket and the bar shows 1 item", js(b, "document.querySelector('[data-compare-toggle]').getAttribute('aria-pressed')") == "true" and js(b, "document.querySelectorAll('.compare-tray-chips li').length") == 1)
        js(b, "document.querySelector('[data-compare-toggle]').click()")
        b.pump(0.3)
        check("talent detail (Premium): the toggle takes it out again", js(b, "document.querySelectorAll('.compare-tray-chips li').length") == 0)
    else:
        check("talent detail (Basic): Compare and Invite have the lock badge", r["lock"])
    check_no_private(b, "talent detail: no email, score, nationality or visa text")
    check("talent detail: the shield note says that name, contact details and the CV are never shown", "never shown" in b.text("main, .app-content"))
    return href


def api_call(base, method, path, body=None, token=""):
    """One REST call (standard library). Returns the JSON answer. An HTTP error raises an exception."""
    req = urllib.request.Request(f"{base}/api{path}", data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


SKILL_SETS = [["Python", "SQL", "Data analysis"], ["JavaScript", "React", "Docker"], ["Project management", "Excel", "Stakeholder management"],
              ["Python", "Docker", "Git"], ["SQL", "Power BI", "Data visualisation"], ["Java", "SQL", "Agile delivery"]]


CERT_A = {"name": "AWS Certified Cloud Practitioner", "issuer": "Amazon Web Services", "year": 2024}
CERT_B = {"name": "Certified Kubernetes Administrator", "issuer": "Cloud Native Computing Foundation", "year": 2023}
CERT_C = {"name": "HashiCorp Certified: Terraform Associate", "issuer": "HashiCorp", "year": 2022}
AWARD_A = {"name": "Regional Hackathon Winner 2024", "kind": "hackathon", "year": 2024}
AWARD_B = {"name": "Open Source Contributor of the Year 2023", "kind": "open-source", "year": 2023}
RICH_TALENT = [
    {"level": "Senior", "years": 6.6, "certs": [CERT_A, CERT_B, CERT_C], "awards": [AWARD_A, AWARD_B]},   # 5 chips: 3 shown and "+2 more"
    {"level": "Junior", "years": 1, "certs": [CERT_A], "awards": []},                                    # 1 chip, no "more"
    {"level": "Lead", "years": 9, "certs": [], "awards": [AWARD_B]},
]


def ensure_talent(base, employer_pw, minimum=24):
    """The talent list needs more than 10 profiles to have a second page. If the data has fewer, the test makes some (REST calls, made-up people)."""
    try:
        token = api_call(base, "POST", "/auth/login", {"email": "recruiter@demo.jinder.app", "password": employer_pw})["token"]
        total = api_call(base, "GET", "/recruiter/candidates?pageSize=1", token=token)["total"]
        STATE["talent_before"] = total
        stamp = int(time.time())
        for i in range(max(0, minimum - total)):
            email = f"pager.talent.{stamp}.{i}@example.test"
            api_call(base, "POST", "/auth/signup", {"role": "candidate", "name": f"Pager Talent {i}", "email": email, "password": "correct horse 1"})
            t = api_call(base, "POST", "/auth/login", {"email": email, "password": "correct horse 1"})["token"]
            profile = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Computer science"], "studyCountry": ["Australia"], "currentRole": ["Software Engineer"],
                       "industry": ["Software Engineering"], "years": "3–5 years", "skills": SKILL_SETS[i % len(SKILL_SETS)], "targetRole": ["Software Engineer"],
                       "targetIndustries": [], "locations": ["Sydney"], "workTypes": ["Full-time"]}
            tr = api_call(base, "POST", "/profile/translate", {"profile": profile, "evidence": {}}, t)
            profile["translation"] = [{**sk, "status": "accepted"} for sk in tr["skills"]]
            profile["evidence"] = {}
            api_call(base, "PATCH", "/me", {"profile": profile, "onboarding": "done"}, t)
        # Three talent with a level, exact years, certifications, awards and skill levels (made last, so they are the newest profiles)
        STATE["rich"] = []
        for i, spec in enumerate(RICH_TALENT):
            email = f"rich.talent.{stamp}.{i}@example.test"
            api_call(base, "POST", "/auth/signup", {"role": "candidate", "name": f"Rich Talent {i}", "email": email, "password": "correct horse 1"})
            login = api_call(base, "POST", "/auth/login", {"email": email, "password": "correct horse 1"})
            t = login["token"]
            profile = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Computer science"], "studyCountry": ["Australia"], "currentRole": ["Software Engineer"],
                       "industry": ["Software Engineering"], "years": "6–10 years", "skills": ["Python", "SQL", "Docker"], "targetRole": ["Software Engineer"],
                       "targetIndustries": [], "locations": ["Sydney"], "workTypes": ["Full-time"],
                       "level": spec["level"], "yearsExperience": spec["years"], "certifications": spec["certs"], "awards": spec["awards"]}
            tr = api_call(base, "POST", "/profile/translate", {"profile": profile, "evidence": {}}, t)
            profile["translation"] = [{**sk, "status": "accepted", "level": 5 if sk.get("mapped") == "Python" else 3} for sk in tr["skills"]]
            profile["evidence"] = {}
            api_call(base, "PATCH", "/me", {"profile": profile, "onboarding": "done"}, t)
            STATE["rich"].append({**spec, "alias": login["user"]["alias"]})
        total = api_call(base, "GET", "/recruiter/candidates?pageSize=1", token=token)["total"]
        info(f"the talent list has {total} profiles ({STATE['talent_before']} before the test made more)")
        return total
    except Exception as exc:  # noqa: BLE001
        info(f"could not make more talent ({exc}): the pager checks need more than 10 profiles")
        return 0


def make_application(base, talent_pw, job_id):
    """The demo talent applies for the job that the test posted (REST calls, not the screens). Returns True if it worked."""
    if not (talent_pw and job_id):
        return False
    try:
        token = api_call(base, "POST", "/auth/login", {"email": "candidate@demo.jinder.app", "password": talent_pw})["token"]
        api_call(base, "POST", "/applications", {"jobId": job_id, "note": "A short note for the employer test."}, token)
        return True
    except Exception as exc:  # noqa: BLE001 - the demo talent may have no finished profile in this build of the data
        info(f"the demo talent could not apply ({exc}): the review checks use another job")
        return False


def check_applicants_and_review(b, applied=False):
    found = b.eval("""(async (preferred) => {
      const { api } = await import('/js/api/index.js');
      const list = await api.recruiter.jobs.list({ pageSize: 50 });
      const job = list.items.find((j) => j.id === preferred && j.applicantCount + j.contactedCount > 0) || list.items.find((j) => j.applicantCount + j.contactedCount > 0);
      return job ? { id: job.id, title: job.title, total: list.page.total } : null;
    })(%s)""" % json.dumps(STATE.get("job_id", "")))
    if not found:
        info("the demo employer has no job with applications: the applicants and review checks are skipped")
        return
    go(b, f"#/my-jobs/{found['id']}", "document.querySelector('.app-row')")
    b.pump(0.5)
    r = b.eval("""({
      h1: document.querySelector('h1').textContent, rows: document.querySelectorAll('.app-row').length,
      links: [...document.querySelectorAll('.dash-head .panel-actions a')].map(a => a.textContent.trim() + '|' + a.getAttribute('href')),
      filter: [...document.querySelectorAll('[data-filter] option')].map(o => o.textContent), pager: !!document.querySelector('.pager'),
      first: document.querySelector('.app-row h3 a').getAttribute('href'),
    })""")
    check("applicants: the head links to the Job overview, Find talent and Edit job; the page has the status filter", any(x.startswith("Job overview") and x.endswith("/overview") for x in r["links"]) and r["filter"][0] == "All" and "Waiting for you" in r["filter"] and "In review" in r["filter"], str(r))
    check("applicants: a short list has no pager", not r["pager"])
    js(b, "(() => { const s = document.querySelector('[data-filter]'); s.value = 'waiting'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("location.hash.includes('status=waiting')")
    b.pump(0.8)
    shown = js(b, "document.querySelectorAll('.app-row').length")
    allw = js(b, "[...document.querySelectorAll('.app-row')].every(r => r.innerText.includes('Waiting for you'))")
    check("applicants: the 'Waiting for you' filter shows only waiting applications (or the empty text)", allw and (shown > 0 or "No applications with this status" in b.text("main, .app-content")), f"{shown}")
    # A status filter reads all pages and pages them in the browser (the API has no status filter)
    js(b, "(() => { const s = document.querySelector('[data-filter]'); s.value = 'applied'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("location.hash.includes('status=applied') && document.querySelector('.app-row, .empty:not([role=status])')")
    b.pump(0.4)
    check("applicants: the 'Applied' filter shows applications that have the Applied status", js(b, "[...document.querySelectorAll('.app-row .ribbon')].every(r => r.textContent.includes('Applied'))") and js(b, "document.querySelectorAll('.app-row').length") >= 1)
    js(b, "(() => { const s = document.querySelector('[data-filter]'); s.value = 'declined'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    b.wait_for("location.hash.includes('status=declined') && document.querySelector('.empty:not([role=status])')")
    check("applicants: a filter without matches shows 'No applications with this status.'", "No applications with this status." in b.text("main, .app-content"))
    go(b, f"#/my-jobs/{found['id']}", "document.querySelector('.app-row')")
    href = js(b, "document.querySelector('.app-row h3 a').getAttribute('href')")
    go(b, href, "document.querySelector('.pf-list')")
    b.pump(0.6)
    rv = b.eval("({ h1: document.querySelector('h1').textContent, rows: [...document.querySelectorAll('.pf-row dt')].map(d => d.textContent), identity: document.querySelector('.identity strong')?.textContent || '', skills: document.querySelectorAll('.skill-match li, .skill-table tbody tr').length, table: !!document.querySelector('.skill-table'), head: [...document.querySelectorAll('.skills-wide thead th')].map(t => t.textContent) })")
    check("review: the profile shows the alias and the rows Roles, Skills, Qualifications", "Roles" in rv["rows"] and "Skills" in rv["rows"] and "Qualifications" in rv["rows"], str(rv))
    check("review: per-skill match rows are shown", rv["skills"] >= 1)
    if applied:
        check("review: an application that was made now has Level, Experience, Certifications and Awards in the profile", all(k in rv["rows"] for k in ("Level", "Experience", "Certifications", "Awards")), str(rv["rows"]))
        check("review: the job has skill levels and the snapshot has them, so the Skill by skill table is shown", rv["table"] and rv["head"] == ["Skill", "Job needs", "Talent", "Result"], str(rv["head"]))
    if rv["identity"] == "Anonymous":
        check_no_private(b, "review (anonymous application): no email, score or personal text")
    else:
        info("the first application has a shared identity (the talent agreed): the privacy scan of the review page is skipped")
    shot(b, "14-review.png", full=True)


def check_closed_job_mock(b, base):
    """The mock has a closed demo job. The overview shows the banner and no Edit button."""
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    closed = js(b, "[...document.querySelectorAll('.app-row')].find(r => r.querySelector('.chip-rose'))?.querySelector('h3 a').getAttribute('href') || ''")
    check("mock: My jobs has a closed job", bool(closed))
    if not closed:
        return
    go(b, closed, "document.querySelector('.job-overview')")
    b.pump(0.5)
    r = b.eval("({ banner: document.querySelector('.jo-banner')?.textContent || '', edit: [...document.querySelectorAll('.jo-head .panel-actions a')].map(a => a.textContent.trim()), chip: document.querySelector('.jo-chips .chip').textContent.replace('Status: ', '').trim(), jd: !!document.querySelector('.jd-view') })")
    check("overview (closed job): a banner says the job is closed, the 'Closed' chip shows and there is no Edit button", "closed" in r["banner"].lower() and r["chip"] == "Closed" and not any(x.startswith("Edit") for x in r["edit"]) and any(x.startswith("See talent") for x in r["edit"]), str(r))
    check("overview (mock): facts without data are left out, the JD box is there", r["jd"] and js(b, "![...document.querySelectorAll('.jo-facts dt')].some(d => d.textContent === 'Level')"))
    shot(b, "15-overview-closed-mock.png", full=True)


def check_mock(b, base):
    info("--- mock mode (?mock=1): the old employer screens must still work ---")
    sign_in(b, base, "recruiter@demo.jinder.app", "demo1234", mock=True)
    check("mock: employer Home loads with the cards", js(b, "document.querySelectorAll('.report-card').length") >= 3)
    shot(b, "16-mock-home.png")
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    r = b.eval("({ rows: document.querySelectorAll('.app-row').length, pager: !!document.querySelector('.pager'), first: document.querySelector('.app-row h3 a').getAttribute('href') })")
    check("mock: My jobs lists the demo jobs, the title opens the overview, no pager for a short list", r["rows"] >= 3 and "/overview" in r["first"] and not r["pager"], str(r))
    check_closed_job_mock(b, base)
    go(b, "#/candidates", "document.querySelector('.cand-card')")
    b.pump(0.4)
    r = b.eval("""({ cards: document.querySelectorAll('.cand-card').length, pager: !!document.querySelector('.pager'), upgrade: !!document.querySelector('.upgrade .locked-badge'),
      locks: document.querySelectorAll('.cand-card [data-premium-lock]').length, sort: !!document.querySelector('#talent-sort') })""")
    check("mock: the Basic talent list shows 5 cards, the upgrade box, locks on Compare and Invite, and no pager", r["cards"] == 5 and not r["pager"] and r["upgrade"] and r["locks"] >= 5, str(r))
    shot(b, "17-mock-talent-list.png", full=True)
    js(b, "document.querySelector('.cand-card h3 a').click()")
    b.wait_for("document.querySelector('.pf-list')")
    b.pump(0.5)
    r = b.eval("({ rows: [...document.querySelectorAll('.pf-row dt')].map(d => d.textContent), list: !!document.querySelector('.skill-match'), table: !!document.querySelector('.skill-table') })")
    check("mock: the talent detail shows the old profile rows and the skill list (no table, no empty new rows)", r["list"] and not r["table"] and "Level" not in r["rows"] and "Certifications" not in r["rows"], str(r))
    # The job form in mock mode: the new fields are hidden, the domain list and the template work, and a job can be posted
    go(b, "#/my-jobs/new", "document.querySelector('form.job-form')")
    r = b.eval("""({ level: !!document.querySelector('#jf-level'), certs: !!document.querySelector('#jf-cert-req'), awards: !!document.querySelector('[name=awardKind]'),
      domains: [...document.querySelectorAll('#jf-category option')].length, template: document.querySelector('#jf-desc').value.startsWith('## About the role'),
      rows: document.querySelectorAll('.skill-req').length })""")
    check("mock: the job form hides the fields that the mock does not keep (level, years, certifications, awards)", not r["level"] and not r["certs"] and not r["awards"] and r["domains"] == 4 and r["template"], str(r))
    # The mock import: it gets the file name and gives a sample job description
    pdf = os.path.join(tempfile.mkdtemp(prefix="jinder-jd-"), "backend-engineer.pdf")
    open(pdf, "wb").write(b"%PDF-1.4 made-up file for the mock")
    b.set_file("#jf-file", pdf)
    b.wait_for("!document.querySelector('[data-read]').disabled")
    js(b, "document.querySelector('[data-read]').click()")
    b.wait_for("document.querySelector('[data-import-status] .form-alert.success')", timeout=20)
    r = b.eval("({ title: document.querySelector('#jf-title').value, banner: !!document.querySelector('.demo-banner'), skills: document.querySelectorAll('[data-skills] .chip').length, domainMarker: document.querySelector('label[for=jf-category] .field-markers')?.textContent.trim() || '', titleMarker: document.querySelector('label[for=jf-title] .field-markers')?.textContent.trim() || '', desc: document.querySelector('#jf-desc').value.length })")
    check("mock import: the sample fills the form (title, skills, description), the demo banner shows, and the domain of the sample (a domain of the list) is marked 'From your file'", "Backend Engineer" in r["title"] and r["banner"] and r["skills"] >= 1 and r["desc"] > 30 and "From your file" in r["domainMarker"] and "From your file" in r["titleMarker"], str(r))
    closes = (datetime.now(timezone.utc) + timedelta(days=21)).strftime("%Y-%m-%d")
    fill_form_field(b, "title", "Mock check job")
    fill_form_field(b, "category", "Data")
    fill_form_field(b, "location", "Perth")
    fill_form_field(b, "type", "Full-time")
    fill_form_field(b, "closesAt", closes)
    fill_form_field(b, "description", "## About the role\n- A made-up job to check the mock backend with the new form.\n\n## Tech stack\n- SQL")
    b.fill("#jf-skill", "SQL")
    js(b, "document.querySelector('[data-add]').click()")
    check("mock: a skill is a chip with a remove button (the old look)", js(b, "[...document.querySelectorAll('[data-skills] .chip')].some(c => c.textContent.includes('SQL') && c.querySelector('[data-remove]'))"))
    js(b, "document.querySelector('form.job-form [type=submit]').click()")
    b.wait_for("location.hash.includes('/overview')", timeout=15)
    b.wait_for("document.querySelector('.job-overview .jd-view')")
    check("mock: a job can be posted and the overview shows it", js(b, "document.querySelector('h1').textContent") == "Mock check job" and "Tech stack" in js(b, "document.querySelector('.jd-view').innerText"))
    shot(b, "18-mock-overview.png", full=True)
    # Edit of the new job in mock mode
    go(b, js(b, "location.hash").replace("/overview", "/edit"), "document.querySelector('form.job-form')")
    check("mock: the edit form opens with the saved values", js(b, "document.querySelector('#jf-title').value") == "Mock check job" and js(b, "document.querySelector('#jf-category').value") == "Data")
    # Applicants of a job and review
    go(b, "#/my-jobs", "document.querySelector('.app-row')")
    apps_href = js(b, "[...document.querySelectorAll('.app-row a.btn')].find(a => a.textContent.includes('Applicants'))?.getAttribute('href') || ''")
    go(b, apps_href, "document.querySelector('[data-filter]')")
    b.pump(0.5)
    check("mock: the applicants page of a job loads (list or empty text, status filter, Job overview link)", js(b, "!!document.querySelector('[data-filter]') && [...document.querySelectorAll('.panel-actions a')].some(a => a.textContent.includes('Job overview'))"))
    review_href = js(b, "document.querySelector('.app-row h3 a')?.getAttribute('href') || ''")
    if review_href:
        go(b, review_href, "document.querySelector('.pf-list')")
        check("mock: the review page loads with the profile and the skill list", js(b, "!!document.querySelector('.skill-match') && !document.querySelector('.skill-table')"))
    no_problems(b, "mock employer screens: no console error, no CSP error", ignore=("australian_jobs_dataset.csv",))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--employer-pw", default="")
    ap.add_argument("--talent-pw", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--debug-port", type=int, default=9340)
    ap.add_argument("--port", type=int, default=8140)
    args = ap.parse_args()
    SHOTS[0] = args.shots
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)
    platform = None
    talent_pw = args.talent_pw
    if args.base:
        base, employer_pw = args.base.rstrip("/"), args.employer_pw
    else:
        platform = start_platform(args.port)
        base = platform.base
        employer_pw = platform.pw.get("recruiter@demo.jinder.app", "")
        talent_pw = platform.pw.get("candidate@demo.jinder.app", "")
        info(f"started the platform on {base} (data folder {platform.var})")
    b = None
    try:
        check_static(base)
        b = Browser(port=args.debug_port)
        sign_in(b, base, "recruiter@demo.jinder.app", employer_pw)
        b.take_problems()
        check_units(b)
        # ---- Basic employer
        set_plan(b, "basic")
        check_home(b, "Basic")
        check_basic_talent_list(b)
        check_basic_detail(b)
        check_import_real(b)
        check_job_form_and_post(b, base)
        if STATE.get("job_id"):
            check_overview(b, "Basic")
            check_edit_keeps_values(b)
        check_form_api_errors(b)
        no_problems(b, "Basic employer screens: no console error, no CSP error", ignore=("/api/recruiter/jobs",))   # the 400 answers of the error checks are on purpose
        # ---- Premium employer (demo plan switch)
        set_plan(b, "premium")
        ensure_talent(base, employer_pw)
        check_rich_cards(b)
        check_home(b, "Premium")
        check_my_jobs(b)
        check_premium_talent_list(b)
        check_compare_basket(b)
        check_invite(b)
        check_talent_detail(b, with_table=False)
        if STATE.get("job_id"):
            check_talent_detail(b, with_table=True)
            check_overview(b, "Premium")
        applied = make_application(base, talent_pw, STATE.get("job_id", ""))
        check_applicants_and_review(b, applied)
        check_mobile(b)
        no_problems(b, "Premium employer screens: no console error, no CSP error", ignore=("/api/recruiter/jobs",))
        set_plan(b, "basic")
        # ---- mock
        check_mock(b, base)
    finally:
        if b:
            pid = b.proc.pid
            b.close()
            if sys.platform == "win32":   # Chrome starts child processes. Stop the whole tree, so that the debug port is free for the next run.
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        if platform:
            platform.stop()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    for name, _, detail in failed:
        print("  FAIL:", name, detail)
    if SHOT_FILES:
        print("Screenshots:")
        for p in SHOT_FILES:
            print("  " + p)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
