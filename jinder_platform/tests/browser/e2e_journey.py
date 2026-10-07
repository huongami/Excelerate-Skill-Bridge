"""A full journey in a real browser (Jinder V2): a new talent signs up and uploads a CV (a DOCX file with the layout of a table), checks what the scan
found (current role, level, years, certifications; the desired role is NOT in this CV, so the hint shows), accepts the translated skills and applies for a job;
a new employer posts a job with the V2 fields (domain, level, years, work mode, skill levels, a job description with headings), reviews the application
and moves it through the hiring flow (interview, offer); the talent deletes the account.

Usage:  python tests/browser/e2e_journey.py http://localhost:8123 [screenshot folder]
Needs Chrome or Edge, and a running platform. The CV is a DOCX file in tests/fixtures/cv (a made-up person). Every step prints PASS or FAIL.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Browser, Report, api_call, go, non_extension, sign_in  # noqa: E402

BASE = sys.argv[1].rstrip("/")
R = Report("e2e_journey", sys.argv[2] if len(sys.argv) > 2 else None)
check = R.check
CV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "cv", "cv10_docx_table_two_column.docx"))
CV_NAME = "Data Analyst"          # the current role in that CV
FOUND_LABELS = ("Current role:", "Desired role:", "Level:", "Years of experience:", "Certifications:", "Awards:")


def sign_up(b, role, name, email, password, company=None):
    b.goto(f"{BASE}/#/signup")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{BASE}/#/signup")
    b.wait_for("document.querySelector('#name')")
    if role == "recruiter":
        b.click('[data-role="recruiter"]')
        b.fill("#company", company)
    b.fill("#name", name)
    b.fill("#email", email)
    b.fill("#password", password)
    b.fill("#confirm", password)
    b.eval("document.querySelector('input[name=terms]').click()", await_promise=False)
    b.click("form [type=submit]")
    b.wait_for("location.hash.includes('registered=1')")
    b.wait_for("document.querySelector('#email')")
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", timeout=30)
    b.pump(1.0)


def ob_wait(b, title, timeout=40):
    b.wait_for(f"document.querySelector('#ob-title') && document.querySelector('#ob-title').textContent === {json.dumps(title)}", timeout)
    b.pump(0.3)


def ob_next(b):
    b.eval("document.querySelector('#obFoot [type=submit]').click()", await_promise=False)
    b.pump(0.5)


def set_field(b, name, value):
    """Set a field of the open form by its name and send the events of the browser."""
    b.eval(f"""(() => {{ const el = document.querySelector('form').elements[{json.dumps(name)}]; if (!el) throw new Error('no field ' + {json.dumps(name)});
      el.value = {json.dumps(str(value))}; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }})()""", await_promise=False)
    b.pump(0.1)


def main():
    stamp = uuid.uuid4().hex[:8]
    b = Browser()
    try:
        # ================================================================ talent
        R.section("Talent: sign up, CV scan, onboarding")
        talent_email = f"journey.talent.{stamp}@example.test"
        sign_up(b, "candidate", "Priya Sharma", talent_email, "journey pass 123")
        b.wait_for("document.querySelector('#onboarding[open]')")
        check("onboarding dialog opens for a new talent", True)
        b.set_file("#ob-cv", CV)
        b.wait_for("!document.querySelector('#ob-cv-next').disabled")
        R.shot(b, "j01-onboarding-cv.png")
        b.click("#ob-cv-next")
        ob_wait(b, "Your education")
        t = b.text("#obBody")
        check("the scan shows 'What we found in your CV' with current role, desired role, level, years, certifications and awards",
              "What we found in your CV" in t and all(k in t for k in FOUND_LABELS), t[:400])
        items = b.eval("[...document.querySelectorAll('.cv-found-list li')].map(li => li.className + '|' + li.textContent.replace(/\\s+/g, ' ').trim())", False)
        found = [x for x in items if x.startswith("is-found|")]
        check("what was found: the current role, the level, the years and the certification are filled",
              any("Current role: Data Analyst" in x for x in found) and any("Level: Mid" in x for x in found) and any("4.8 years" in x for x in found)
              and any("Certifications: 1 found" in x for x in found), str(items))
        check("what was not found shows a hint (no desired role in this CV)", any(x.endswith("Not found. You can add it in the next steps.") and "Desired role:" in x for x in items), str(items))
        check("the fields from the CV are marked AI-detected", "AI-detected" in t, t[:200])
        R.shot(b, "j02-education.png")
        ob_next(b)
        ob_wait(b, "Your experience")
        r = b.eval("({ level: document.querySelector('#ob-level').value, years: document.querySelector('#ob-yearsExperience').value, band: document.querySelector('#ob-years').value, text: document.querySelector('#obBody').innerText })", False)
        check("experience: the level (Mid) and the exact years (4.8) from the CV are in the fields, and the band follows (3–5 years)", r["level"] == "Mid" and r["years"] == "4.8" and r["band"] == "3–5 years", str(r)[:300])
        check("experience: the current role from the CV", CV_NAME in r["text"], r["text"][:300])
        check("experience: the word is Domain (not Industry)", "Domain" in r["text"] and "ndustr" not in r["text"], r["text"][:300])
        set_field_level = b.eval("(() => { const s = document.querySelector('#ob-level'); s.value = 'Senior'; s.dispatchEvent(new Event('change', { bubbles: true })); return s.value; })()", False)
        check("experience: the level can be edited", set_field_level == "Senior")
        b.eval("(() => { const s = document.querySelector('#ob-level'); s.value = 'Mid'; s.dispatchEvent(new Event('change', { bubbles: true })); })()", await_promise=False)
        ob_next(b)
        ob_wait(b, "Your skills")
        check("skills: from the CV", "Power BI" in b.text("#obBody") and "SQL" in b.text("#obBody"))
        ob_next(b)
        ob_wait(b, "Certifications and awards")
        rows = b.eval("[...document.querySelectorAll('[data-field=certifications] .cred-row input[id$=-name]')].map(i => i.value)", False)
        check("credentials: the certification of the CV is a row that can be edited", rows == ["Microsoft Certified: Power BI Data Analyst Associate"], str(rows))
        ob_next(b)
        ob_wait(b, "Your translated profile")
        b.wait_for("document.querySelector('.tr-card')", 40)
        cards = b.eval("document.querySelectorAll('.tr-card').length", False)
        check("translation: cards from the API (skills and the role)", cards >= 5, str(cards))
        check("translation: each skill has a level select", b.eval("document.querySelectorAll('.tr-level-select').length", False) >= 4)
        check("translation: no demo banner in real mode", "Demo mode" not in b.text("#onboarding"))
        R.shot(b, "j03-translation.png")
        b.click_text("button", "Accept all")
        ob_next(b)
        ob_wait(b, "What are you looking for?")
        hint = b.eval("[...document.querySelectorAll('.cv-hint')].map(h => h.textContent.trim())", False)
        check("goals: the hint says that the desired role was not found in the CV", any("could not find your desired role" in h for h in hint), str(hint))
        b.fill("#ob-targetRole", "Data Engineer")
        b.click('button[aria-label="Add to Target roles"]')
        b.eval("[...document.querySelectorAll('[data-field=locations] .choice')].find(c => c.textContent.trim() === 'Melbourne').click()", await_promise=False)
        b.eval("[...document.querySelectorAll('[data-field=workTypes] .choice')].find(c => c.textContent.trim() === 'Full-time').click()", await_promise=False)
        ob_next(b)
        ob_wait(b, "Check your answers")
        vals = b.eval("Object.fromEntries([...document.querySelectorAll('.review-row')].map(r => [r.querySelector('dt').firstChild.textContent, r.querySelector('dd').textContent]))", False)
        check("review: Level, Exact years, Certifications and Target roles", vals.get("Level") == "Mid" and vals.get("Exact years") == "4.8 years" and "Power BI" in vals.get("Certifications", "") and "Data Engineer" in vals.get("Target roles", ""), str(vals)[:300])
        ob_next(b)
        b.wait_for("!document.querySelector('#onboarding[open]')", 40)
        b.pump(1.5)
        check("profile saved: home shows recommended jobs", b.eval("document.querySelectorAll('.job-card').length", False) >= 1, b.text("main")[:300])
        check("home: the alias is shown, and 'What employers see' has the level and the certification", "Employers see you as" in b.text("body") and "Level: Mid" in b.text("main") and "Power BI Data Analyst" in b.text("main"))
        R.shot(b, "j04-talent-home.png", full=True)
        first = b.eval("document.querySelector('.job-card .job-title-link').getAttribute('href')", False)
        go(b, BASE, first, "document.querySelector('.job-detail h1') && document.querySelector('.bridge.path')")
        check("job detail: 'Your path to this job' has two radar layers and no 12-month chart", b.eval("document.querySelectorAll('.bridge.path .rd-shape').length === 2 && !document.querySelector('.lc-svg')", False))
        check("no console errors in the talent part", not non_extension(b.take_problems()), str(b.problems))

        # ================================================================ employer
        R.section("Employer: sign up, post a job")
        company = f"Journey Data {stamp}"
        emp_email = f"journey.employer.{stamp}@example.test"
        sign_up(b, "recruiter", "Sam Taylor", emp_email, "journey pass 456", company)
        go(b, BASE, "#/my-jobs/new", "document.querySelector('form')")
        b.pump(0.5)
        closes = (datetime.now(timezone.utc) + timedelta(days=21)).strftime("%Y-%m-%d")
        jd = ("## About the role\nWe need a data analyst who builds dashboards in Power BI and writes SQL every day. The team is small and friendly.\n"
              "## What you will do\n- Build and own Power BI dashboards for the sales team.\n- Write SQL queries and clean data with Python.\n"
              "## What you bring\n- 2 to 5 years as a data analyst.\n- SQL and Power BI at an advanced level.\n"
              "## What we offer\n- Hybrid work and a learning budget.\n## How we hire\n- A call, a SQL exercise and a talk with the team.")
        b.fill("#jf-title", "Data Analyst, Journey")
        set_field(b, "category", "Data")
        set_field(b, "specialisation", "Data analytics")
        set_field(b, "level", "Mid")
        set_field(b, "minYears", "2")
        set_field(b, "maxYears", "5")
        set_field(b, "workMode", "Hybrid")
        set_field(b, "educationMin", "Bachelor's degree")
        set_field(b, "location", "Melbourne")
        set_field(b, "type", "Full-time")
        set_field(b, "closesAt", closes)
        set_field(b, "targetApplicants", "3")
        set_field(b, "description", jd)
        for name in ("SQL", "Power BI", "Python"):
            b.fill("#jf-skill", name)
            b.eval("document.querySelector('[data-add]').click()", await_promise=False)
            b.pump(0.15)
        rows = b.eval("document.querySelectorAll('.skill-req').length", False)
        check("job form: 3 skill rows, each with a level and a Must check box", rows == 3 and b.eval("document.querySelectorAll('.skill-req select').length", False) == 3, str(rows))
        b.eval("(() => { const s = document.querySelector('[data-level=\"0\"]'); s.value = '4'; s.dispatchEvent(new Event('change', { bubbles: true })); })()", await_promise=False)
        b.eval("document.querySelector('[data-preview]').click()", await_promise=False)
        b.pump(0.5)
        check("job form: the preview shows the job description with its headings", b.eval("document.querySelectorAll('#jf-preview .jd-view h3').length", False) >= 5)
        R.shot(b, "j05-job-form.png", full=True)
        b.click("form [type=submit]")
        b.wait_for("location.hash.includes('/overview')", timeout=20)
        b.pump(1.0)
        job_id = b.eval("location.hash", False).split("/")[2]
        o = b.text("main")
        check("job posted: the overview shows the level, the experience and the work mode", all(w in o for w in ("Mid", "2 to 5 years", "Hybrid")) and "Data Analyst, Journey" in o, o[:300])
        check("job posted: the overview has the full job description in the scroll box", b.eval("document.querySelectorAll('.job-overview .jd-view h3').length", False) >= 5)
        R.shot(b, "j06-job-overview.png", full=True)

        go(b, BASE, f"#/candidates?jobId={job_id}", "document.querySelector('.cand-card')")
        body = b.text("body")
        check("employer sees no name or e-mail of the talent", "Priya" not in body and "Sharma" not in body and talent_email not in body)
        R.shot(b, "j07-employer-talent.png")
        check("no console errors on the employer side", not non_extension(b.take_problems()), str(b.problems))

        # ================================================================ the talent applies
        R.section("Talent applies, employer reviews and hires")
        sign_in(b, BASE, talent_email, "journey pass 123")
        go(b, BASE, f"#/jobs/{job_id}", "document.querySelector('.job-detail h1')")
        check("the new job is in the catalogue for talent, with its level and facts", "Data Analyst, Journey" in b.text("h1") and "Hybrid" in b.text(".fact-grid"))
        b.click("a.btn-primary.btn-lg")
        b.wait_for("document.querySelector('form')")
        b.pump(0.8)
        R.shot(b, "j08-apply.png")
        b.fill("textarea[name=note]", "I build Power BI dashboards. Call me on 0400 123 456.")
        b.click_text("button", "Send application")
        b.wait_for("location.hash.startsWith('#/applications/')")
        b.pump(1.0)
        check("application sent, contact details removed from the note", "[phone removed]" in b.text("body"), b.text("body")[:400])
        app_id = b.eval("location.hash.split('?')[0]", False).split("/")[2]

        sign_in(b, BASE, emp_email, "journey pass 456")
        go(b, BASE, f"#/review/{app_id}", "document.querySelector('.dash h1')", pump=1.0)
        txt = b.text("body")
        check("review: the alias is the title, no name yet", "Priya" not in txt and "Sharma" not in txt)
        check("review: the level, the years and the certification of the talent, and the skill table", all(w in txt for w in ("Level", "Experience", "Certification")) and b.eval("!!document.querySelector('.skill-table')", False))
        b.click_text("button", "Start review")
        b.wait_for("document.body.innerText.includes('In review')")
        check("status moved to In review", True)
        R.shot(b, "j09-review.png", full=True)
        slot_time = (datetime.now() + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
        b.fill("#slot-1", slot_time)
        b.click_text("button", "Send interview times")
        b.wait_for("document.body.innerText.includes('Waiting for them to choose a time')")
        check("employer sent an interview time", True)

        sign_in(b, BASE, talent_email, "journey pass 123")
        go(b, BASE, f"#/applications/{app_id}", "document.body.innerText.includes('Choose an interview time')")
        b.eval("document.querySelector('input[name=slotId]').click(); document.querySelector('input[name=shareIdentity]').click()", await_promise=False)
        b.click_text("button", "Choose this time")
        b.wait_for("document.body.innerText.includes('Waiting for the employer to confirm')")
        check("talent chose a time and shared their identity", True)
        R.shot(b, "j10-talent-slot.png")

        sign_in(b, BASE, emp_email, "journey pass 456")
        go(b, BASE, f"#/review/{app_id}", "document.body.innerText.includes('Confirm the interview time')")
        txt = b.text("body")
        check("the identity shows only after the talent agreed", "Priya Sharma" in txt and talent_email in txt, txt[:300])
        b.click_text("button", "Confirm time")
        b.wait_for("document.body.innerText.includes('Record the interview result')")
        b.click_text("button", "Accept")
        b.wait_for("document.body.innerText.includes('Send an offer')")
        b.fill("textarea[name=offer]", "Full-time Data Analyst at $95,000, starting next month. Welcome to the team.")
        b.click_text("button", "Send offer")
        b.wait_for("document.body.innerText.includes('Waiting for an answer to the offer')")
        check("employer accepted and sent an offer", True)

        sign_in(b, BASE, talent_email, "journey pass 123")
        go(b, BASE, f"#/applications/{app_id}", "document.body.innerText.includes('You have an offer')")
        b.click_text("button", "Accept offer")
        b.wait_for("document.body.innerText.includes('Application finished')")
        check("talent accepted the offer: Confirmed", "Confirmed" in b.text("body"), b.text("body")[:300])
        b.fill("textarea[name=toOther]", "A clear and friendly process.")
        b.click_text("button", "Send feedback")
        b.wait_for("document.body.innerText.includes('Thank you')")
        check("talent sent feedback", True)
        sign_in(b, BASE, emp_email, "journey pass 456")
        go(b, BASE, f"#/review/{app_id}", "document.body.innerText.includes('Application finished')")
        check("employer sees the feedback of the talent", "A clear and friendly process." in b.text("body"))
        b.fill("textarea[name=toOther]", "Great interview. Welcome.")
        b.click_text("button", "Send feedback")
        b.wait_for("document.body.innerText.includes('Thank you') || document.body.innerText.includes('You sent feedback')")
        check("employer sent feedback", True)
        R.shot(b, "j11-finished.png", full=True)

        # ================================================================ delete the account
        R.section("Talent deletes the account")
        sign_in(b, BASE, talent_email, "journey pass 123")
        b.click("#shellUser")
        b.wait_for("document.querySelector('[data-delete]')")
        b.pump(0.5)
        check("settings (user block): the Your data section", "Download my data" in b.text("body") and "Delete my account" in b.text("body"))
        b.click("[data-delete]")
        b.wait_for("document.querySelector('dialog[open] #del-pw')")
        b.fill("#del-pw", "a wrong password")
        b.click_text("button", "Delete account")
        b.wait_for("document.querySelector('dialog[open] .form-alert.show')")
        check("delete: a wrong password is refused", "not correct" in b.text("dialog[open]"), b.text("dialog[open]"))
        b.fill("#del-pw", "journey pass 123")
        b.click_text("button", "Delete account")
        b.wait_for("!document.querySelector('dialog[open]')")
        b.pump(0.8)
        check("delete: the user is signed out", b.eval("!sessionStorage.getItem('jinder.session') && !localStorage.getItem('jinder.session')", False))
        b.goto(f"{BASE}/#/login")
        b.wait_for("document.querySelector('#email')")
        b.fill("#email", talent_email)
        b.fill("#password", "journey pass 123")
        b.click("form [type=submit]")
        b.wait_for("document.querySelector('.form-alert.show')")
        check("delete: the account can no longer sign in", "Incorrect email or password" in b.text("body"))
        status, _ = api_call(BASE, "GET", "/health")
        check("the platform still answers", status == 200)
        problems = [x for x in non_extension(b.take_problems()) if "status of 4" not in x]   # the browser logs the expected 400 and 401 answers of this test
        check("no console errors in the full journey", not problems, str(problems))
    finally:
        b.close()
    return R.finish()


if __name__ == "__main__":
    raise SystemExit(main())
