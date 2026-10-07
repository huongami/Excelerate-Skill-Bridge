"""QA check: text that a talent writes (award names, certification names, the application note, an alias) and text that an employer writes (job title, job description,
skills) is shown as text and never runs as HTML or script, on every screen that shows it. The test puts markup in each field and looks at the screens.

Usage:  python tests/browser/qa_xss.py [--port 8161]
It starts its own platform with the demo accounts. It is not part of `python run_tests.py`.
"""
import argparse
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Browser, Report, api_call, api_login, go, non_extension, sign_in, start_demo_platform, stop_demo_platform  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8161)
ARGS = ap.parse_args()
R = Report("qa_xss")
check = R.check
BASE = f"http://localhost:{ARGS.port}"

PAYLOAD = '<img src=x onerror="window.__xss=(window.__xss||0)+1">'
PAYLOAD2 = '"><script>window.__xss=(window.__xss||0)+1</script>'


def card(i, mapped, level=3, source="skill", **over):
    return {"id": f"card-{i}", "source": source, "original": mapped, "mapped": mapped, "kind": "direct", "anzsco": "", "occupation": "", "reason": "A card made by the QA run.",
            "evidence": "Moderate", "evidenceText": "", "status": "accepted", "level": level if source == "skill" else None, **over}


def main():
    proc, tpw, epw, log = start_demo_platform(ARGS.port)
    b = Browser(port=0)
    try:
        email = f"qa.xss.{uuid.uuid4().hex[:6]}@example.test"
        s, r = api_call(BASE, "POST", "/auth/signup", {"role": "candidate", "name": "QA Xss", "email": email, "password": "correct horse 1"})
        assert s == 201, (s, r)
        tok = api_login(BASE, email, "correct horse 1")
        skills = ["Python", "SQL", "Apache Spark", "Git"]
        cards = [card(i, n) for i, n in enumerate(skills)] + [card(90, "Data Engineer", source="role", anzsco="262111", occupation="Data Engineer")]
        body = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Computer science"], "studyCountry": ["Vietnam"], "currentRole": ["Data Engineer"], "industry": ["Data"], "years": "3–5 years",
                "yearsExperience": 4.0, "level": "Mid", "skills": skills, "targetRole": ["Data Engineer"], "targetIndustries": [], "locations": ["Sydney"], "workTypes": ["Full-time"], "evidence": [],
                "translation": cards, "certifications": [{"name": PAYLOAD, "issuer": PAYLOAD2, "year": 2022}], "awards": [{"name": PAYLOAD2, "kind": "hackathon", "year": 2023}]}
        s, me = api_call(BASE, "PATCH", "/me", {"profile": body, "onboarding": "done"}, token=tok)
        R.check("the API accepts markup in an award and a certification name (it is data)", s == 200, str(me)[:200])
        et = api_login(BASE, "recruiter@demo.jinder.app", epw)
        api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)
        s, job = api_call(BASE, "POST", "/recruiter/jobs", {"title": "Data Engineer " + PAYLOAD, "category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["Python", "SQL"],
                                                           "targetApplicants": 5, "closesAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + 20 * 86400)), "level": "Mid",
                                                           "description": "## About the role\n\n" + PAYLOAD + "\n\n## What you bring\n\n- " + PAYLOAD2 + "\n- SQL", "certifications": {"required": [PAYLOAD], "preferred": []}}, token=et)
        R.check("the API accepts markup in a job title and a job description (it is data)", s in (200, 201), str(job)[:200])
        job_id = job["id"] if s in (200, 201) else "job-demo-data-engineer-mid"
        s, app = api_call(BASE, "POST", "/applications", {"jobId": job_id, "note": PAYLOAD2}, token=tok)
        R.check("the talent applies with markup in the note", s in (200, 201), str(app)[:200])
        app_id = app["id"]
        cid = api_call(BASE, "GET", "/me", token=tok)[1]["id"]

        def screen(label, route, wait, who="employer"):
            b.eval("window.__xss = 0", await_promise=False)
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=1.2)
            hits = b.eval("window.__xss || 0", False)
            raw = b.eval("(() => { const t = document.body.innerText; return t.includes('onerror') || t.includes('<script') || t.includes('<img'); })()", False)
            inj = b.eval("document.querySelectorAll('img[src=x], main script, #app script').length", False)
            R.check(f"{label}: the markup is shown as text and does not run (script ran {hits} times, injected tags {inj}, the text shows the markup: {raw})", hits == 0 and inj == 0, f"hits={hits} injected={inj}")

        sign_in(b, BASE, "recruiter@demo.jinder.app", epw)
        screen("employer talent list", f"#/candidates?jobId={job_id}&pageSize=50", ".cand-card")
        screen("employer talent detail", f"#/candidates/{cid}?jobId={job_id}", ".pf-list, .profile-card")
        screen("employer review", f"#/review/{app_id}", ".skill-table, .skill-match")
        screen("employer applicants", f"#/my-jobs/{job_id}", ".app-row")
        screen("employer job overview", f"#/my-jobs/{job_id}/overview", ".job-overview .jd-view")
        screen("employer my jobs", "#/my-jobs", ".app-row")
        screen("employer job edit form", f"#/my-jobs/{job_id}/edit", "form.job-form")
        other = [c["id"] for c in api_call(BASE, "GET", "/recruiter/candidates?pageSize=5&jobId=" + job_id, token=et)[1]["items"] if c["id"] != cid][0]
        s_cmp, r_cmp = api_call(BASE, "GET", f"/recruiter/compare?ids={cid},{other}&jobId={job_id}", token=et)
        R.check("the compare API answers for a job whose title has markup", s_cmp == 200, str(r_cmp)[:300])
        screen("employer compare", f"#/compare?ids={cid},{other}&jobId={job_id}", ".cmp-panels .rd-shape")
        sign_in(b, BASE, email, "correct horse 1")
        screen("talent job detail", f"#/jobs/{job_id}", ".job-detail h1")
        screen("talent home (what employers see)", "#/home", ".dash")
        screen("talent settings (what employers see)", "#/settings", ".plan-card")
        screen("talent applications", f"#/applications/{app_id}", ".dash h1")
        screen("talent compare", f"#/compare?ids={job_id},job-data-analytics-mid-01", ".cmp-panels .rd-shape")
        problems = [p for p in non_extension(b.take_problems()) if "status of 4" not in p]
        R.check("no console error and no CSP report", not problems, str(problems[:3]))
    finally:
        b.close()
        stop_demo_platform(proc)
    return R.finish()


if __name__ == "__main__":
    raise SystemExit(main())
