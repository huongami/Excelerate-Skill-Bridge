"""Drive the real frontend in a real browser against a running platform that was started with --demo (Jinder V2).

Usage:  python tests/browser/e2e_demo.py http://localhost:8123 <talent password> <employer password> [screenshot folder]

It walks through the demo story of the seed data:
  * the demo talent Teal Heron (Linh Nguyen): Home, the menu without Settings, Jobs with the pager and the sort, a job with the facts, the
    certifications, the awards, the scroll box of the job description, the 8-axis panel and the "Your path" panel (a radar with two layers, a Fit
    list and a Gap list, no 12-month chart), the compare basket and the compare page, Applications, Settings (the user block) and the Premium switch;
  * the demo employer Alex Morgan at Bluebushworks (4 demo jobs): My jobs, the job overview with the job description, the talent list as a Basic
    employer (5 cards, locks), the same list as a Premium employer (pager, sort "Recently updated", the order of the API), talent compare, applicants.
Every step prints PASS or FAIL. The browser console must have no error and no CSP report. Needs Chrome or Edge.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Browser, Report, api_call, api_login, fetch_json, go, key, non_extension, reload, sign_in, token_of  # noqa: E402

BASE = sys.argv[1].rstrip("/")
TALENT_PW, EMPLOYER_PW = sys.argv[2], sys.argv[3]
R = Report("e2e_demo", sys.argv[4] if len(sys.argv) > 4 else None)
check = R.check

LIST_IDS = "[...document.querySelectorAll('[data-list] .job-card')].map(c => c.dataset.card)"
CAND_IDS = "[...document.querySelectorAll('.cand-card')].map(c => c.querySelector('a[href^=\"#/candidates/\"]').getAttribute('href').split('/')[2].split('?')[0])"
FIT_TABLE = "[...document.querySelectorAll('.fit .radar-table tbody tr')].map(r => r.cells[r.cells.length - 1].innerText.trim())"


def set_select(b, selector, value):
    b.eval(f"(() => {{ const s = document.querySelector({json.dumps(selector)}); s.value = {json.dumps(str(value))}; s.dispatchEvent(new Event('change', {{ bubbles: true }})); }})()", await_promise=False)
    b.pump(0.8)


def click_pager(b, label):
    b.eval(f"[...document.querySelectorAll('.pager-step')].find(e => e.textContent.trim().startsWith({json.dumps(label)})).click()", await_promise=False)
    b.pump(0.8)


def no_problems(b, name, ignore=()):
    problems = [p for p in non_extension(b.take_problems()) if not any(i in p for i in ignore)]
    check(name, not problems, "; ".join(problems)[:500])


def main():
    b = Browser()
    try:
        # ------------------------------------------------------------------ landing
        R.section("Landing")
        b.goto(f"{BASE}/")
        b.wait_for("document.querySelector('main, .hero, h1')")
        check("landing renders", "Jinder" in b.text("body"))
        no_problems(b, "landing: no console or CSP errors")
        R.shot(b, "01-landing.png")

        # ------------------------------------------------------------------ talent: Home and the shell
        R.section("Talent: Home, menu, user block")
        sign_in(b, BASE, "candidate@demo.jinder.app", TALENT_PW)
        b.wait_for("document.querySelector('.dash')")
        b.wait_for("document.querySelectorAll('.job-card').length >= 1", timeout=30)
        b.pump(0.8)
        txt = b.text("main")
        check("home: the demo talent sees the alias Teal Heron and the name Linh", "Teal Heron" in txt and "Linh" in txt, txt[:200])
        check("home: 'What employers see' has the level, the years, the certifications and the awards",
              all(w in txt for w in ("Level: Mid", "Certifications:", "Awards:")) and "· Advanced" in txt, txt[:600])
        cards = b.eval("document.querySelectorAll('.job-card').length", False)
        check("home: 5 recommended jobs, with a link to all jobs, and no pager", cards == 5 and "See all jobs" in txt and b.eval("!document.querySelector('.pager')", False), f"cards={cards}")
        facts = b.eval("[...document.querySelectorAll('.job-card')].map(c => c.querySelectorAll('.job-facts .chip').length)", False)
        check("home: every job card shows the level, the experience and the work mode", facts and all(n == 3 for n in facts), str(facts))
        R.shot(b, "02-talent-home.png", full=True)
        labels = b.eval("[...document.querySelectorAll('.sidebar-nav a')].map(a => a.innerText.trim().split('\\n')[0])", False)
        check("menu: Home, Jobs, Bookmarks, Applications, Compare, Notifications (no Settings)", labels == ["Home", "Jobs", "Bookmarks", "Applications", "Compare", "Notifications"], str(labels))
        check("user block: one link to Settings with the name, the role and the alias",
              b.eval("(() => { const a = document.getElementById('shellUser'); return a.getAttribute('href') === '#/settings' && a.innerText.includes('Linh Nguyen') && a.innerText.includes('Talent') && a.innerText.includes('Teal Heron'); })()", False))
        check("a Basic talent has no crown", b.eval("!document.getElementById('shellUser').classList.contains('is-premium') && getComputedStyle(document.querySelector('.avatar-crown')).display === 'none'", False))
        no_problems(b, "talent home: no console or CSP errors")

        # ------------------------------------------------------------------ talent: Jobs, pager, sort
        R.section("Talent: Jobs list, pager, sort")
        go(b, BASE, "#/jobs", "document.querySelector('[data-list] .job-card')")
        rng = b.text(".pager-range")
        check("jobs: 10 cards and 'Showing 1–10 of 53'", b.eval("document.querySelectorAll('[data-list] .job-card').length", False) == 10 and rng == "Showing 1–10 of 53", rng)
        opts = b.eval("[...document.querySelectorAll('#jobs-sort option')].map(o => o.textContent)", False)
        check("jobs: the sort select offers 'Best match' and 'Newest posted'", opts == ["Best match", "Newest posted"], str(opts))
        scores = b.eval("[...document.querySelectorAll('[data-list] .fit-score strong')].map(e => e.textContent)", False)
        check("jobs: the fit scores of the 10 jobs on the page are all different", len(scores) == 10 and len(set(scores)) == 10, str(scores))
        page1 = b.eval(LIST_IDS, False)
        click_pager(b, "Next")
        page2 = b.eval(LIST_IDS, False)
        check("jobs: page 2 has 10 other jobs and the address has page=2", len(page2) == 10 and not set(page1) & set(page2) and "page=2" in b.eval("location.hash", False), b.eval("location.hash", False))
        check("jobs: the range says 'Showing 11–20 of 53' and the current page is marked", b.text(".pager-range") == "Showing 11–20 of 53" and b.eval("document.querySelector('.pager-num.is-current').getAttribute('aria-current')", False) == "page")
        set_select(b, "[data-pager-size]", 20)
        check("jobs: page size 20 shows 20 cards from page 1", b.eval("document.querySelectorAll('[data-list] .job-card').length", False) == 20 and b.text(".pager-range") == "Showing 1–20 of 53", b.text(".pager-range"))
        set_select(b, "[data-pager-size]", 50)
        check("jobs: page size 50 shows 50 cards and 2 pages", b.eval("document.querySelectorAll('[data-list] .job-card').length", False) == 50 and b.eval("document.querySelector('.pager').dataset.pagerTotalPages", False) == "2")
        reload(b)
        b.wait_for("document.querySelector('[data-list] .job-card')")
        b.pump(0.6)
        check("jobs: the page size is remembered (50 after a reload of the page)", b.eval("document.querySelectorAll('[data-list] .job-card').length", False) == 50)
        set_select(b, "[data-pager-size]", 10)
        set_select(b, "#jobs-sort", "newest")
        ui_newest = b.eval(LIST_IDS, False)
        api_newest = [j["id"] for j in fetch_json(b, "/jobs?pageSize=10&sort=newest")["items"]]
        every = fetch_json(b, "/jobs?pageSize=50&sort=newest")["items"]
        dates = [j["postedAt"] for j in every]
        check("jobs: sort 'Newest posted' shows the order of the API", ui_newest == api_newest, f"{ui_newest[:3]} / {api_newest[:3]}")
        check("jobs: 'Newest posted' is in date order (newest first, the id breaks a tie)", dates == sorted(dates, reverse=True), str(dates[:4]))
        set_select(b, "#jobs-sort", "best")
        ui_best = b.eval(LIST_IDS, False)
        best = fetch_json(b, "/jobs?pageSize=50&sort=best")["items"]
        sc = [j["match"]["score"] for j in best]
        check("jobs: sort 'Best match' is in fit order and equals the API", ui_best == [j["id"] for j in best[:10]] and sc == sorted(sc, reverse=True), str(sc[:5]))
        R.shot(b, "03-jobs-list.png")

        # ------------------------------------------------------------------ talent: job detail (facts, certifications, JD box, fit panel, path panel)
        R.section("Talent: job detail")
        job_id = ui_best[0]
        go(b, BASE, f"#/jobs/{job_id}", "document.querySelector('.job-detail h1') && document.querySelector('.bridge.path')")
        b.pump(0.8)
        d = b.eval("""({ facts: [...document.querySelectorAll('.fact-grid dt')].map(e => e.textContent),
          certs: !!document.querySelector('#certTitle'), awards: !!document.querySelector('#awardTitle'),
          jd: (() => { const v = document.querySelector('.jd-about .jd-view'); return v ? { h3: v.querySelectorAll('h3').length, len: v.innerText.length, role: v.getAttribute('role'), tab: v.getAttribute('tabindex'),
             label: v.getAttribute('aria-label'), scroll: v.scrollHeight > v.clientHeight, ov: getComputedStyle(v).overflowY, ell: v.innerText.includes('\\u2026') || v.innerText.includes('...') } : null; })(),
          skills: document.querySelectorAll('.skill-match li').length, fitRows: document.querySelectorAll('.fit .radar-table tbody tr').length,
          oldChart: document.querySelectorAll('.lc-svg, .line-chart').length, twelve: /12-month|next 12 months|projection/i.test(document.body.innerText) })""", False)
        check("detail: Job facts show the level, the experience and the work mode", all(k in d["facts"] for k in ("Level", "Experience", "Work mode")), str(d["facts"]))
        check("detail: the Certifications and Awards parts are there", d["certs"] and d["awards"])
        jd = d["jd"] or {}
        check("detail: 'About the role' is the full text in a labelled, focusable, scrolling box with the headings of the JD",
              jd and jd["h3"] >= 6 and jd["len"] > 1200 and jd["role"] == "region" and jd["tab"] == "0" and jd["scroll"] and jd["ov"] == "auto" and not jd["ell"], str(jd))
        check("detail: skill by skill list, and the 8 numbers of 'How this job fits you'", d["skills"] >= 5 and d["fitRows"] == 8, str(d["skills"]) + "/" + str(d["fitRows"]))
        check("detail: no 12-month chart and no projection text", d["oldChart"] == 0 and not d["twelve"])
        # a skill that the talent has below the asked level says "Below level" (QA fix F-2), a related skill says "Related"
        skills_api = fetch_json(b, f"/jobs/{job_id}")["match"]["skills"]
        want_below = sum(1 for x in skills_api if x.get("fitStatus") == "below")
        want_related = sum(1 for x in skills_api if x.get("fitStatus") == "related")
        ui_skills = b.eval("({ below: [...document.querySelectorAll('.skill-match li.sm-partial')].filter(li => li.querySelector('.sm-state').textContent === 'Below level').length,"
                           " related: [...document.querySelectorAll('.skill-match li.sm-partial')].filter(li => li.querySelector('.sm-state').textContent === 'Related').length,"
                           " detail: [...document.querySelectorAll('.skill-match li.sm-partial .sm-via')].map(e => e.textContent) })", False)
        check("detail: 'Skill by skill' says 'Below level' (with 'You: ... Needs: ...') for a skill below the asked level and 'Related' (with 'via ...') for a related skill, as the API says",
              ui_skills["below"] == want_below and ui_skills["related"] == want_related and want_below + want_related > 0
              and sum(1 for t in ui_skills["detail"] if t.startswith("You: ") and "Needs: " in t) == want_below, f"{ui_skills} api below={want_below} related={want_related}")
        # the keyboard reaches the box and scrolls it
        b.eval("document.querySelector('.jd-about .jd-view').scrollIntoView({block: 'center'}); document.querySelector('.jd-about .jd-view').focus()", await_promise=False)
        b.pump(0.2)
        before = b.eval("document.querySelector('.jd-about .jd-view').scrollTop", False)
        key(b, "PageDown", times=2)
        after = b.eval("document.querySelector('.jd-about .jd-view').scrollTop", False)
        key(b, "End")
        end = b.eval("(() => { const v = document.querySelector('.jd-about .jd-view'); return Math.abs(v.scrollHeight - v.clientHeight - v.scrollTop) < 3; })()", False)
        check("detail: the keyboard scrolls the job description box (Page Down, End)", after > before and end, f"{before} -> {after}, end={end}")
        R.shot(b, "04-job-detail-jd.png")
        # the path panel
        path = fetch_json(b, f"/jobs/{job_id}")["bridge"]["path"]
        p = b.eval("""({ layers: document.querySelectorAll('.bridge.path .radar-layers').length, shapes: document.querySelectorAll('.bridge.path .rd-shape').length,
          fit: document.querySelectorAll('.bridge.path .path-fit').length, gap: document.querySelectorAll('.bridge.path .path-gap').length,
          chips: [...document.querySelectorAll('.path-summary li')].map(l => l.innerText.replace(/\\s+/g, ' ').trim()),
          rows: document.querySelectorAll('.bridge.path .path-table tbody tr').length, legend: [...document.querySelectorAll('.bridge.path .rd-legend li')].map(l => l.innerText.trim()) })""", False)
        check("path: a radar with two layers (You have, Job requires)", p["layers"] == 1 and p["shapes"] == 2 and "You have" in " ".join(p["legend"]) and "Job requires" in " ".join(p["legend"]), str(p))
        check("path: the Fit list and the Gap list have the sizes of the API summary", p["fit"] == path["summary"]["fitCount"] == len(path["fit"]) and p["gap"] == path["summary"]["gapCount"] == len(path["gaps"]), f"{p['fit']}/{p['gap']} vs {path['summary']}")
        check("path: the table of the radar has one row for each axis of the API", p["rows"] == len(path["axes"]), f"{p['rows']} vs {len(path['axes'])}")
        check("path: the summary chips say the numbers", any(c.startswith(str(path["summary"]["fitCount"])) for c in p["chips"]) and any(f"{path['summary']['monthsToClose']:g}" in c for c in p["chips"]) , str(p["chips"]))
        R.shot(b, "05-job-detail-path.png", full=True)
        # the 8 numbers differ between jobs
        panels = []
        for jid in ui_best[:3]:
            go(b, BASE, f"#/jobs/{jid}", "document.querySelector('.fit .radar-table tbody tr')")
            panels.append(b.eval(FIT_TABLE, False))
        same = [i for i in range(8) if len({p_[i] for p_ in panels}) == 1]
        check("detail: the 8 numbers of the fit panel differ between 3 jobs (at most 1 axis can be equal)", len(same) <= 1, f"equal axes {same}: {panels}")
        no_problems(b, "job detail: no console or CSP errors")

        # ------------------------------------------------------------------ talent: bookmark, compare basket, compare page
        R.section("Talent: bookmark, compare basket, Compare page")
        b.click("[data-bookmark]")
        b.wait_for("document.querySelector('[data-bookmark]').getAttribute('aria-pressed') === 'true' && !document.querySelector('[data-bookmark]').disabled")
        go(b, BASE, "#/bookmarks", "document.querySelector('.job-card')")
        check("bookmarks: the saved job is listed", b.eval("document.querySelectorAll('[data-list] .job-card').length", False) == 1)
        go(b, BASE, "#/jobs", "document.querySelector('[data-list] .job-card')")
        for k in range(3):
            b.eval(f"document.querySelectorAll('[data-compare-job]')[{k}].click()", await_promise=False)
            b.pump(0.25)
        check("basket: the bar shows 'Compare (3/5)' and the three jobs", "Compare (3/5)" in b.text("[data-compare-tray]"), b.text("[data-compare-tray]"))
        click_pager(b, "Next")
        b.eval("document.querySelectorAll('[data-compare-job]')[0].click()", await_promise=False)
        b.pump(0.3)
        check("basket: the basket stays when the page changes (4 jobs after a tick on page 2)", "Compare (4/5)" in b.text("[data-compare-tray]"), b.text("[data-compare-tray]"))
        b.click("[data-compare-tray] a[href='#/compare']")
        b.wait_for("document.querySelector('.compare-page .cmp-panels') && document.querySelectorAll('.cmp-panels .rd-shape').length >= 2", timeout=30)
        b.pump(0.8)
        ids_in_url = re.findall(r"job-[a-z0-9-]+", b.eval("location.hash", False))
        c = b.eval("({ cards: document.querySelectorAll('.cmp-card').length, series: document.querySelectorAll('.cmp-panels .rd-shape').length, h1: document.querySelector('h1').innerText, tables: document.querySelectorAll('.cmp-table').length })", False)
        check("compare: the page for 4 jobs has 4 cards, 4 radar lines and the 4 ids in the address", c["cards"] == 4 and c["series"] == 4 and len(ids_in_url) == 4 and c["h1"] == "Compare jobs", f"{c} {ids_in_url}")
        api = fetch_json(b, "/jobs/compare?ids=" + ",".join(ids_in_url))
        check("compare: the skill matrix of the page has the rows of the API", b.eval("document.querySelectorAll('#cmpSkills tbody tr').length", False) >= len(api["skillMatrix"]), f"{len(api['skillMatrix'])}")
        R.shot(b, "06-compare-jobs.png", full=True)
        b.eval("document.querySelector('.cmp-card [data-cmp-remove], .cmp-card .cmp-remove').click()", await_promise=False)
        b.pump(1.0)
        check("compare: removing one job leaves 3 and changes the address", b.eval("document.querySelectorAll('.cmp-card').length", False) == 3 and len(re.findall(r"job-[a-z0-9-]+", b.eval("location.hash", False))) == 3)
        no_problems(b, "compare jobs: no console or CSP errors")
        # the sixth job is refused
        b.eval("localStorage.clear()", await_promise=False)
        go(b, BASE, "#/jobs", "document.querySelector('[data-list] .job-card')")
        for k in range(6):
            b.eval(f"document.querySelectorAll('[data-compare-job]')[{k}].click()", await_promise=False)
            b.pump(0.25)
        note = b.eval("[...document.querySelectorAll('[data-compare-note]')].map(e => e.textContent).join(' ')", False)
        check("basket: the sixth job is refused with a text, and the bar keeps 5", "Compare (5/5)" in b.text("[data-compare-tray]") and "up to 5" in note, note)
        b.eval("localStorage.clear()", await_promise=False)

        # ------------------------------------------------------------------ talent: applications, notifications
        R.section("Talent: Applications, Notifications")
        go(b, BASE, "#/applications", "document.querySelector('.dash h1')")
        t = b.text("main")
        check("applications: the interview needs action", "Action needed" in t and "Interview" in t and "Data Engineer, Solar Analytics" in t, t[:300])
        check("applications: sort select with Recently updated, Best skill match, Newest application", b.eval("[...document.querySelectorAll('select option')].map(o => o.textContent).filter(t => /updated|match|application/i.test(t)).length", False) >= 3)
        R.shot(b, "07-applications.png", full=True)
        go(b, BASE, "#/notifications", "document.querySelector('.dash h1')")
        check("notifications: interview times", "Interview times" in b.text("main"), b.text("main")[:200])

        # ------------------------------------------------------------------ talent: Settings through the user block, the Premium switch
        R.section("Talent: Settings (user block), Premium")
        b.click("#shellUser")
        b.wait_for("location.hash.startsWith('#/settings') && document.querySelector('.plan-card')")
        b.pump(0.8)
        t = b.text("main")
        check("settings: the user block opens Settings with the plan card (Basic) and the two Premium benefits locked",
              b.text("h1") == "Settings" and "Your current plan:" in t and b.eval("document.querySelectorAll('.benefit .premium-chip').length", False) == 2, t[:200])
        check("settings: 'What employers see' shows the level, the years, the certifications, the awards and the skill levels",
              b.eval("(() => { const t = document.querySelector('[data-shared-body]').innerText; return t.includes('Level: Mid') && t.includes('Certifications:') && t.includes('Awards:') && t.includes('Advanced'); })()", False), b.text("[data-shared-body]")[:300])
        R.shot(b, "08-settings-basic.png", full=True)
        b.click("[data-try-premium]")
        b.wait_for("document.getElementById('shellUser').classList.contains('is-premium')", timeout=15)
        check("premium: the crown and the gold ring show at once", b.eval("getComputedStyle(document.querySelector('.avatar-crown')).display !== 'none' && !!document.querySelector('#shellUser .premium-chip:not([hidden])')", False))
        b.pump(0.6)
        states = b.eval("[...document.querySelectorAll('.benefit')].map(e => e.querySelector('.benefit-status').innerText.replace(/\\s+/g, ' ').trim())", False)
        check("premium: each benefit says Used or Not used yet", len(states) == 2 and all(s.startswith(("Used", "Not used yet")) for s in states), str(states))
        R.shot(b, "09-settings-premium.png", full=True)
        b.eval("[...document.querySelectorAll('[name=plan]')].find(r => r.value === 'basic').click()", await_promise=False)
        b.wait_for("!document.getElementById('shellUser').classList.contains('is-premium')", timeout=15)
        check("premium: switching back to Basic takes the crown away", True)
        # a talent cannot open employer pages
        go(b, BASE, "#/my-jobs", "document.querySelector('main')")
        check("talent cannot open employer pages", "access" in b.text("body").lower(), b.text("body")[:200])
        no_problems(b, "talent settings and access: no console or CSP errors", ignore=("status of 403",))

        # ------------------------------------------------------------------ employer
        R.section("Employer: Home, My jobs, job overview")
        sign_in(b, BASE, "recruiter@demo.jinder.app", EMPLOYER_PW)
        b.pump(1.0)
        txt = b.text("main")
        check("employer home: Alex, Bluebushworks and the 4 demo jobs", "Alex" in txt and "Bluebushworks" in txt and "Data Engineer, Solar Analytics" in txt and "Contract Data Engineer, Billing Migration" in txt, txt[:300])
        labels = b.eval("[...document.querySelectorAll('.sidebar-nav a')].map(a => a.innerText.trim().split('\\n')[0])", False)
        check("employer menu: Home, Talent, My jobs, Compare, Notifications (no Settings), and a lock on Compare", labels == ["Home", "Talent", "My jobs", "Compare", "Notifications"] and b.eval("!document.querySelector('[data-nav-lock]').hidden", False), str(labels))
        R.shot(b, "10-employer-home.png", full=True)
        go(b, BASE, "#/my-jobs", "document.querySelectorAll('main li, main article').length > 3")
        txt = b.text("main")
        check("my jobs: the 4 jobs with their state (Open, Closes in, Closed)", "Closes in" in txt and "Closed" in txt and "Open" in txt and txt.count("Bluebushworks") >= 0 and "Newest first" in txt, txt[:300])
        go(b, BASE, "#/my-jobs/job-demo-data-engineer-mid/overview", "document.querySelector('.job-overview .jd-view')")
        o = b.eval("""(() => { const v = document.querySelector('.job-overview .jd-view'); return { h3: v.querySelectorAll('h3').length, scroll: v.scrollHeight > v.clientHeight, tab: v.tabIndex, len: v.innerText.length,
          ell: v.innerText.includes('\\u2026'), facts: [...document.querySelectorAll('.jo-facts dt')].map(e => e.textContent), skills: document.querySelectorAll('.job-overview table tbody tr').length }; })()""", False)
        check("overview: the full job description in a scroll box that the keyboard reaches, no cut", o["h3"] >= 6 and o["scroll"] and o["tab"] == 0 and o["len"] > 1200 and not o["ell"], str(o))
        check("overview: the facts (Level, Experience, Work mode) and the skills table", all(k in o["facts"] for k in ("Level", "Experience", "Work mode")) and o["skills"] >= 5, str(o))
        R.shot(b, "11-job-overview.png", full=True)

        R.section("Employer: talent list (Basic)")
        go(b, BASE, "#/candidates", "document.querySelector('.cand-card')")
        b.pump(0.6)
        txt = b.text("main")
        check("talent list (Basic): 5 cards, no pager, the upgrade box and the locks", b.eval("document.querySelectorAll('.cand-card').length", False) == 5 and b.eval("!document.querySelector('.pager')", False)
              and b.eval("!!document.querySelector('.upgrade') && document.querySelectorAll('[data-premium-lock]').length >= 5", False), txt[:200])
        check("talent list: only aliases (no name, no e-mail, no country)", not re.search(r"Linh|Nguyen|@|Vietnam", txt.replace("Bluebushworks", "")), txt[:200])
        check("talent list: each card shows the level, the years and when the profile changed",
              b.eval("[...document.querySelectorAll('.cand-card')].every(c => c.querySelector('.cand-facts') && /Level/.test(c.innerText) && /Updated/.test(c.innerText))", False))
        check("talent list: no score or rank on a person", not re.search(r"\b(score|rank|rating)\b", txt, re.I), txt[:200])
        R.shot(b, "12-talent-basic.png", full=True)
        b.click(".sidebar-nav a[href='#/compare']")
        b.wait_for("document.querySelector('.compare-page') && document.querySelector('h1')")
        b.pump(0.6)
        check("compare (Basic employer): the locked page with the Premium badge and no data request", b.text("h1") == "Compare talent" and "Premium" in b.text("main"), b.text("main")[:200])
        R.shot(b, "13-compare-locked.png", full=True)

        R.section("Employer: Premium talent list, sort, compare")
        tok = token_of(b)
        status, _ = api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=tok)
        check("the demo switch sets the plan to Premium", status == 200, str(status))
        go(b, BASE, "#/candidates", "document.querySelector('.cand-card')")
        b.pump(0.8)
        total = fetch_json(b, "/recruiter/candidates?pageSize=10")["page"]["total"]
        check("talent list (Premium): the pager says 'Showing 1–10 of N' with the real total", b.text(".pager-range") == f"Showing 1–10 of {total}" and total >= 50 and b.eval("document.querySelectorAll('.cand-card').length", False) == 10, b.text(".pager-range"))
        first = b.eval(CAND_IDS, False)
        click_pager(b, "Next")
        second = b.eval(CAND_IDS, False)
        check("talent list (Premium): page 2 has 10 other profiles", len(second) == 10 and not set(first) & set(second), f"{first[:2]} {second[:2]}")
        set_select(b, "#talent-sort", "updated")
        ui = b.eval(CAND_IDS, False)
        every = fetch_json(b, "/recruiter/candidates?pageSize=50&sort=updated")["items"]
        stamps = [c.get("updatedAt") for c in every]
        check("talent list: sort 'Recently updated' shows the order of the API", ui == [c["id"] for c in every[:10]], f"{ui[:3]} / {[c['id'] for c in every[:3]]}")
        check("talent list: 'Recently updated' is in date order (newest first)", all(s for s in stamps) and stamps == sorted(stamps, reverse=True), str(stamps[:4]))
        set_select(b, "[data-pager-size]", 20)
        check("talent list: page size 20", b.eval("document.querySelectorAll('.cand-card').length", False) == 20)
        set_select(b, "[data-pager-size]", 10)
        b.eval("document.querySelectorAll('[data-compare-pick]')[0].click(); document.querySelectorAll('[data-compare-pick]')[1].click(); document.querySelectorAll('[data-compare-pick]')[2].click()", await_promise=False)
        b.pump(0.4)
        check("talent basket: the bar shows 'Compare (3/5)'", "Compare (3/5)" in b.text("[data-compare-tray]"), b.text("[data-compare-tray]"))
        b.click("[data-compare-tray] a[href='#/compare']")
        b.wait_for("document.querySelector('.compare-page .cmp-panels') && document.querySelectorAll('.cmp-panels .rd-shape').length >= 2", timeout=30)
        b.pump(0.8)
        c = b.eval("({ cards: document.querySelectorAll('.cmp-card').length, series: document.querySelectorAll('.cmp-panels .rd-shape').length, heads: [...document.querySelectorAll('.cmp-panels th')].map(t => t.innerText.trim()), job: (document.querySelector('#cmpJob') || {}).value })", False)
        check("compare talent: 3 profiles on one radar, for a chosen job, with no total column",
              c["cards"] == 3 and c["series"] == 3 and c["job"] and not any(re.fullmatch(r"(total|score|overall|rank)", h.lower()) for h in c["heads"]), str(c)[:300])
        R.shot(b, "14-compare-talent.png", full=True)
        no_problems(b, "employer screens: no console or CSP errors", ignore=("status of 403",))

        R.section("Employer: applicants and review")
        go(b, BASE, "#/my-jobs/job-demo-data-engineer-mid", "document.querySelector('.dash h1') && document.querySelectorAll('a[href^=\"#/review/\"]').length")
        txt = b.text("main")
        check("applicants: the three aliases of the demo story, and no name", all(a in txt for a in ("Plum Heron", "Jade Koala", "Teal Heron")) and "Linh" not in txt, txt[:300])
        href = b.eval("document.querySelector('a[href^=\"#/review/\"]').getAttribute('href')", False)
        go(b, BASE, href, "document.querySelector('.dash h1') && document.querySelector('.skill-table')")
        t = b.text("main")
        check("review: the profile with level, years, certifications and awards, and the skill table without a score", all(w in t for w in ("Level", "Experience", "Certifications", "Awards")) and "Skill by skill" in t and not re.search(r"\bscore\b", t, re.I), t[:300])
        R.shot(b, "15-review.png", full=True)
        no_problems(b, "applicants and review: no console or CSP errors")
    finally:
        b.close()
    return R.finish()


if __name__ == "__main__":
    raise SystemExit(main())
