"""QA keyboard and accessibility spot-check, and the narrow screen check (390 px), in a real browser (Chrome DevTools Protocol).

Usage:  python tests/browser/qa_a11y.py [--port 8160] [--shots <folder>] [--out evidence.json]

It starts a platform with the demo accounts in a temporary folder. It is not part of `python run_tests.py`.
Checks: the Tab order (user block, sort select, cards, pager, basket bar); a visible focus and an accessible name on every control that the Tab key reaches;
the compare picker (the focus goes into the dialog, stays inside it, and Esc gives it back); the job description box (focus, arrow keys); the table of the path panel;
the names of ALL visible controls on the main screens; and no sideways scroll of the page at 390 px on 8 screens.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Browser, Report, api_call, api_login, go, key, non_extension, sign_in, start_demo_platform, stop_demo_platform  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8160)
ap.add_argument("--shots", default="")
ap.add_argument("--out", default="")
ARGS = ap.parse_args()
R = Report("qa_a11y", ARGS.shots or None)
check = R.check
BASE = f"http://localhost:{ARGS.port}"
EVIDENCE = {}

NAME_JS = """
function accName(e) {
  const lb = e.getAttribute('aria-labelledby');
  if (lb) { const t = lb.split(/\\s+/).map(id => (document.getElementById(id) || {}).textContent || '').join(' ').replace(/\\s+/g, ' ').trim(); if (t) return t; }
  const al = e.getAttribute('aria-label'); if (al && al.trim()) return al.trim();
  if (e.labels && e.labels.length) { const t = [...e.labels].map(l => l.textContent).join(' ').replace(/\\s+/g, ' ').trim(); if (t) return t; }
  if (e.tagName === 'INPUT' && ['submit', 'button', 'reset'].includes(e.type) && e.value) return e.value;
  const txt = (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim(); if (txt) return txt;
  const img = e.querySelector('img[alt]'); if (img && img.alt) return img.alt;
  if (e.title && e.title.trim()) return e.title.trim();
  return '';
}
function visible(e) {
  for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
    if (n.hidden || n.getAttribute('aria-hidden') === 'true') return false;
    const s = getComputedStyle(n);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
  }
  const r = e.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
}
"""



CONTRAST_JS = r"""
(() => {
  function parse(c) { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(x => parseFloat(x)); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; }
  function lum(c) { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); }
  function blend(top, bottom) { const a = top.a; return { r: top.r * a + bottom.r * (1 - a), g: top.g * a + bottom.g * (1 - a), b: top.b * a + bottom.b * (1 - a), a: 1 }; }
  function bgOf(e) { const stack = []; for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; } }
    let base = { r: 255, g: 255, b: 255, a: 1 }; for (let i = stack.length - 1; i >= 0; i--) base = blend(stack[i], base); return base; }
  const seen = new Map(); let checked = 0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue; const e = t.parentElement; if (!e) continue;
    let hidden = false; for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const s = getComputedStyle(n); if (s.display === 'none' || s.visibility === 'hidden' || n.hidden) { hidden = true; break; } }
    if (hidden) continue; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
    const cs = getComputedStyle(e); if (cs.position === 'absolute' && /sr-only/.test(e.className)) continue;
    const fg = parse(cs.color); if (!fg) continue; const bg = bgOf(e); const f = blend(fg, bg);
    const L1 = lum(f), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700; const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3 : 4.5; checked++;
    if (ratio < need) { const k = (typeof e.className === 'string' ? e.className.split(' ').slice(0, 2).join('.') : '') + ' ' + e.tagName.toLowerCase() + ' ' + (Math.round(ratio * 10) / 10) + ':' + need; if (!seen.has(k)) seen.set(k, t.textContent.trim().slice(0, 30)); }
  }
  return { checked, low: [...seen.entries()].map(([k, v]) => k + ' "' + v + '"') };
})()
"""


def focus_info(b):
    """The focused element: a short description, its accessible name, and whether a focus indicator is drawn."""
    return b.eval("(() => {" + NAME_JS + """
      const e = document.activeElement; if (!e || e === document.body) return null;
      const s = getComputedStyle(e);
      const ring = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 1) || (s.boxShadow && s.boxShadow !== 'none');
      const parentRing = (() => { const p = e.closest('label, .combo, .check, .tab, .radio, .plan-option'); if (!p) return false; const ps = getComputedStyle(p); return ps.boxShadow !== 'none' || (ps.outlineStyle !== 'none' && parseFloat(ps.outlineWidth) >= 1); })();
      return { tag: e.tagName.toLowerCase(), id: e.id || '', cls: (typeof e.className === 'string' ? e.className : '').split(' ').slice(0, 3).join('.'), name: accName(e), ring: !!(ring || parentRing),
               type: e.getAttribute('type') || '', role: e.getAttribute('role') || '', href: e.getAttribute('href') || '' }; })()""", False)


def tab_through(b, limit=120, stop=None):
    """Press Tab until `stop(info)` is true or the limit. Returns the list of focus stops."""
    stops = []
    b.eval("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)", await_promise=False)
    for _ in range(limit):
        key(b, "Tab")
        info = focus_info(b)
        if info is None:
            continue
        stops.append(info)
        if stop and stop(info):
            break
    return stops


def unnamed_controls(b):
    return b.eval("(() => {" + NAME_JS + """
      const sel = 'button, a[href], input:not([type=hidden]), select, textarea, [role=button], [role=tab], [role=checkbox], [role=radio], [role=combobox], [role=switch], [role=link], summary, [tabindex]:not([tabindex="-1"])';
      return [...document.querySelectorAll(sel)].filter(visible).filter(e => !accName(e)).map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + '.' + (typeof e.className === 'string' ? e.className.split(' ').slice(0, 2).join('.') : '')); })()""", False)


def overflow_info(b):
    return b.eval("""(() => { const w = innerWidth, de = document.documentElement;
      const wide = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > w + 1 && getComputedStyle(e).position !== 'fixed'; })
        .slice(0, 6).map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + '.' + (typeof e.className === 'string' ? e.className.split(' ').slice(0, 2).join('.') : '') + ' right=' + Math.round(e.getBoundingClientRect().right));
      return { inner: w, doc: de.scrollWidth, body: document.body.scrollWidth, wide }; })()""", False)


def set_viewport(b, w, h, mobile=False):
    b.call("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile})
    b.pump(0.4)


def run():
    proc, tpw, epw, log = start_demo_platform(ARGS.port)
    R.info(f"platform on port {ARGS.port}")
    b = Browser(port=0)
    try:
        # ------------------------------------------------------------------ Tab order on the Jobs list
        R.section("Keyboard: the Tab order of the Jobs list (user block, sort select, cards, pager, basket bar)")
        sign_in(b, BASE, "candidate@demo.jinder.app", tpw)
        go(b, BASE, "#/jobs", "document.querySelector('[data-list] .job-card')")
        b.eval("document.querySelectorAll('[data-compare-job]')[0].click(); document.querySelectorAll('[data-compare-job]')[1].click()", await_promise=False)
        b.pump(0.4)
        stops = tab_through(b, limit=140, stop=lambda i: i["cls"].startswith("btn.btn-ghost.btn-sm") and "Clear" in i["name"])
        seq = [f"{s['tag']}{('#' + s['id']) if s['id'] else ''}:{s['name'][:28]}" for s in stops]
        EVIDENCE["tab order jobs list (first 40 stops)"] = seq[:40]
        names = [s["name"] for s in stops]
        i_sort = next((i for i, s in enumerate(stops) if s["id"] == "jobs-sort"), -1)
        i_card = next((i for i, s in enumerate(stops) if s["cls"].startswith("job-title-link")), -1)
        i_size = next((i for i, s in enumerate(stops) if s["tag"] == "select" and "Rows per page" in s["name"]), -1)
        i_next = next((i for i, s in enumerate(stops) if s["name"].startswith("Next")), -1)
        i_open = next((i for i, s in enumerate(stops) if "Open compare" in s["name"]), -1)
        # The router moves the focus to the page heading after a page change (as screen reader users expect). So a Tab press goes into the page.
        # The menu is before the heading in the page. Shift+Tab from the heading shows its order, backwards.
        check("Tab: after a page change the focus is on the page heading, and the first Tab press goes into the page content (the search box)", stops[0]["id"] == "job-q", seq[:3])
        b.eval("document.querySelector('h1').focus()", await_promise=False)
        back = []
        for _ in range(12):
            key(b, "Tab", shift=True)
            back.append(focus_info(b))
        back_seq = [f"{x['tag']}{('#' + x['id']) if x['id'] else ''}:{x['name'][:26]}" for x in back if x]
        EVIDENCE["Shift+Tab from the heading (backwards through the menu)"] = back_seq
        check("Tab: backwards from the heading: Sign out, the user block (ONE link 'Account settings, <name>'), then the 6 menu links, the menu button and the logo",
              back[0]["name"] == "Sign out" and back[1]["id"] == "shellUser" and back[1]["name"].startswith("Account settings") and [x["name"].split(",")[0].splitlines()[0] for x in back[2:8]] == ["Notifications", "Compare", "Applications", "Bookmarks", "Jobs", "Home"], str(back_seq))
        check("Tab: the sort select is before the first job card, the pager after the cards (rows per page, then Next), then the basket bar",
              0 <= i_sort < i_card < i_size < i_next and i_open > i_next, f"sort {i_sort}, card {i_card}, size {i_size}, next {i_next}, open compare {i_open}")
        no_name = [f"{s['tag']}#{s['id']}.{s['cls']}" for s in stops if not s["name"]]
        no_ring = [f"{s['tag']}#{s['id']}.{s['cls']}:{s['name'][:20]}" for s in stops if not s["ring"]]
        check(f"Tab: every one of the {len(stops)} stops has an accessible name", not no_name, str(no_name[:5]))
        check(f"Tab: every one of the {len(stops)} stops shows a focus indicator (outline or ring)", not no_ring, str(no_ring[:8]))
        EVIDENCE["tab stops without a visible indicator"] = no_ring
        R.shot(b, "a11y-1-tab-jobs-list.png")
        # the keyboard changes the sort and the page size
        b.eval("document.getElementById('jobs-sort').focus()", await_promise=False)
        b.eval("(() => { const s = document.getElementById('jobs-sort'); s.value = 'newest'; s.dispatchEvent(new Event('change', { bubbles: true })); })()", await_promise=False)
        b.pump(0.8)
        check("Keyboard: the sort select keeps the focus after a change and the list says it is sorted (live region)", b.eval("document.activeElement.id", False) == "jobs-sort" and "Sorted by" in b.text("#announcer"), b.text("#announcer"))

        # ------------------------------------------------------------------ compare page: basket bar and picker dialog
        R.section("Keyboard: the compare basket bar and the picker dialog (focus trap, Esc)")
        b.click("[data-compare-tray] a[href='#/compare']")
        b.wait_for("document.querySelector('.compare-page .cmp-panels .rd-shape')", 30)
        b.pump(0.8)
        trigger_ok = b.eval("(() => { const t = document.querySelector('[data-add]'); t.focus(); return document.activeElement === t; })()", False)
        key(b, "Enter")
        b.pump(0.8)
        in_dialog = b.eval("!!document.querySelector('dialog[open]') && document.querySelector('dialog[open]').contains(document.activeElement)", False)
        check("Picker: Enter on 'Add to compare' opens the dialog and the focus moves into it", trigger_ok and in_dialog, active_text(b))
        # A native modal dialog makes the page behind it inert. When the Tab key goes past the last control, the focus can go to the browser's own bar
        # (then the active element is the page body) and come back. It must never land on a control of the page behind the dialog.
        where = {"dialog": 0, "body (the browser bar)": 0, "the page behind": 0}
        behind = []
        for direction in (False, True):
            for k in range(30):
                key(b, "Tab", shift=direction)
                st = b.eval("(() => { const d = document.querySelector('dialog[open]'); const a = document.activeElement; if (d && d.contains(a)) return 'dialog'; if (!a || a === document.body || a === document.documentElement) return 'body'; return a.tagName.toLowerCase() + '#' + a.id; })()", False)
                if st == "dialog":
                    where["dialog"] += 1
                elif st == "body":
                    where["body (the browser bar)"] += 1
                else:
                    where["the page behind"] += 1
                    behind.append(st)
        EVIDENCE["picker: where the focus was after 60 Tab and Shift+Tab presses"] = where
        check("Picker: in 60 Tab and Shift+Tab presses the focus never lands on the page behind the dialog (%d in the dialog, %d on the browser bar)" % (where["dialog"], where["body (the browser bar)"]), not behind, str(behind[:5]))
        check("Picker: the focus is in the dialog for most presses (it cycles through the controls of the dialog)", where["dialog"] >= 50, str(where))
        no_name = b.eval("(() => {" + NAME_JS + "return [...document.querySelectorAll('dialog[open] button, dialog[open] input, dialog[open] select, dialog[open] [role=tab]')].filter(visible).filter(e => !accName(e)).length; })()", False)
        check("Picker: every control in the dialog has a name", no_name == 0, str(no_name))
        R.shot(b, "a11y-2-picker.png")
        key(b, "Escape")
        b.pump(0.6)
        check("Picker: Esc closes the dialog and the focus goes back to the 'Add to compare' button", not b.eval("!!document.querySelector('dialog[open]')", False) and b.eval("document.activeElement.hasAttribute('data-add')", False), active_text(b))
        # the remove buttons of the cards have names that include the job title
        names = b.eval("[...document.querySelectorAll('.cmp-card .cmp-remove')].map(x => x.getAttribute('aria-label'))", False)
        check("Compare: each Remove button names its job ('Remove <title> from compare')", names and all(n.startswith("Remove ") and n.endswith(" from compare") and len(n) > 20 for n in names), str(names))

        # ------------------------------------------------------------------ job detail: JD box and the path table
        R.section("Keyboard and names: job detail (JD box, path table)")
        go(b, BASE, "#/jobs/job-data-analytics-mid-01", "document.querySelector('.bridge.path')")
        t = b.eval("""(() => { const tb = document.querySelector('.path-table'); if (!tb) return null; const th = [...tb.querySelectorAll('th')];
          return { caption: !!(tb.querySelector('caption') && tb.querySelector('caption').textContent.trim()), colScopes: th.filter(x => x.scope === 'col').length, rowScopes: th.filter(x => x.scope === 'row').length, headers: th.map(x => x.textContent.trim()).slice(0, 4),
                   wrap: tb.closest('[role=region], .table-wrap') ? (tb.closest('[role=region], .table-wrap').getAttribute('role') || 'table-wrap') : '', status: [...tb.querySelectorAll('.path-status')].map(x => x.innerText.replace(/\\s+/g, ' ').trim()).slice(0, 6) }; })()""", False)
        EVIDENCE["path table"] = t
        check("Path table: it has a caption, column headers with scope, a row header for each skill group, and the status is a word (not only an icon)",
              t and t["caption"] and t["colScopes"] >= 3 and t["rowScopes"] >= 3 and all(s and s.split()[-1] in ("Fit", "Gap", "Above") for s in t["status"]), str(t))
        chart_names = b.eval("[...document.querySelectorAll('svg.rd-svg')].map(s => (s.getAttribute('role') || '') + '|' + (s.getAttribute('aria-label') || '').slice(0, 40))", False)
        check("Radar charts: each chart has role 'img' and a label that holds the numbers", chart_names and all(c.startswith("img|") and len(c) > 8 for c in chart_names), str(chart_names))
        un = unnamed_controls(b)
        check("Job detail: every visible control has an accessible name", not un, str(un[:8]))
        EVIDENCE["unnamed controls"] = {"job detail": un}
        stops = tab_through(b, limit=90, stop=lambda i: "jd-view" in i["cls"])
        check("JD box: the Tab key reaches it (a region with a label) and the focus indicator shows", stops and "jd-view" in stops[-1]["cls"] and stops[-1]["ring"] and stops[-1]["name"] == "Job description", str(stops[-1:]))
        s0 = b.eval("document.activeElement.scrollTop", False)
        key(b, "ArrowDown", times=8)
        key(b, "PageDown")
        s1 = b.eval("document.activeElement.scrollTop", False)
        key(b, "Home")
        s2 = b.eval("document.activeElement.scrollTop", False)
        check("JD box: ArrowDown and PageDown scroll it, Home goes back to the top", s1 > s0 and s2 == 0, f"{s0} -> {s1} -> {s2}")

        # ------------------------------------------------------------------ names on the main screens
        R.section("Accessible names of all visible controls on the main screens")
        screens_t = [("Home", "#/home", ".dash"), ("Jobs", "#/jobs", "[data-list] .job-card"), ("Bookmarks", "#/bookmarks", ".dash"), ("Applications", "#/applications", ".dash"),
                     ("Compare (empty)", "#/compare", ".compare-page"), ("Notifications", "#/notifications", ".dash"), ("Settings", "#/settings", ".plan-card")]
        for label, route, wait in screens_t:
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=0.8)
            un = unnamed_controls(b)
            EVIDENCE["unnamed controls"][label] = un
            check(f"Names (talent): {label}: every visible control has an accessible name", not un, str(un[:6]))
        sign_in(b, BASE, "recruiter@demo.jinder.app", epw)
        et = api_login(BASE, "recruiter@demo.jinder.app", epw)
        api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)
        screens_e = [("Employer Home", "#/home", ".dash"), ("My jobs", "#/my-jobs", ".app-row"), ("Job overview", "#/my-jobs/job-demo-data-engineer-mid/overview", ".job-overview .jd-view"),
                     ("Job form", "#/my-jobs/new", "form.job-form"), ("Talent list", "#/candidates", ".cand-card"), ("Applicants", "#/my-jobs/job-demo-data-engineer-mid", ".app-row"),
                     ("Compare (Premium, empty)", "#/compare", ".compare-page")]
        for label, route, wait in screens_e:
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=0.8)
            un = unnamed_controls(b)
            EVIDENCE["unnamed controls"][label] = un
            check(f"Names (employer): {label}: every visible control has an accessible name", not un, str(un[:6]))
        # Tab order of the talent list (Premium): compare check boxes have names with the alias
        go(b, BASE, "#/candidates", "document.querySelector('.cand-card')")
        names = b.eval("[...document.querySelectorAll('[data-compare-pick]')].map(c => (c.closest('label') || {}).innerText.replace(/\\s+/g, ' ').trim())", False)
        check("Talent list: each 'Compare' check box has the alias in its name (hidden text)", names and all(len(n) > 8 for n in names[:10]), str(names[:3]))

        # ------------------------------------------------------------------ colour contrast of the text (WCAG AA: 4.5 for normal text, 3 for large text)
        R.section("Colour contrast of the visible text on the main screens (WCAG 2.1 AA)")
        low_all = {}
        sign_in(b, BASE, "candidate@demo.jinder.app", tpw)
        for label, route, wait in [("Home", "#/home", ".dash"), ("Jobs", "#/jobs", "[data-list] .job-card"), ("Job detail", "#/jobs/job-data-analytics-mid-01", ".bridge.path"),
                                   ("Settings (Basic)", "#/settings", ".plan-card"), ("Applications", "#/applications", ".dash")]:
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=1.0)
            r = b.eval(CONTRAST_JS, False)
            low_all["talent " + label] = r["low"]
            R.info(f"contrast, talent {label}: {r['checked']} text items, {len(r['low'])} kinds below AA: {r['low'][:6]}")
        sign_in(b, BASE, "recruiter@demo.jinder.app", epw)
        for label, route, wait in [("Home", "#/home", ".dash"), ("Talent list", "#/candidates", ".cand-card"), ("Job overview", "#/my-jobs/job-demo-data-engineer-mid/overview", ".job-overview .jd-view"),
                                   ("Job form", "#/my-jobs/new", "form.job-form"), ("Review", None, None)]:
            if route is None:
                href = api_call(BASE, "GET", "/recruiter/jobs/job-demo-data-engineer-mid/applications", token=et)[1]["items"][0]["id"]
                route, wait = f"#/review/{href}", ".skill-table"
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=1.0)
            r = b.eval(CONTRAST_JS, False)
            low_all["employer " + label] = r["low"]
            R.info(f"contrast, employer {label}: {r['checked']} text items, {len(r['low'])} kinds below AA: {r['low'][:6]}")
        EVIDENCE["text below WCAG AA contrast"] = low_all
        kinds = sorted({x.split(" ")[0] + " " + x.split(" ")[1] for v in low_all.values() for x in v})
        # Known design debt (docs/changes/QA.md, finding A11Y-1): the token --muted is #868e96 (3.3:1 on white) and some links and badges have 3.7 to 4.3:1.
        # This is reported, not failed: the fix is a change of the design tokens in Docs/DESIGN.md. The number is printed so that a later run can compare it.
        R.info(f"Contrast FINDING (design debt, not fixed by QA): {len(kinds)} kinds of text on the 10 screens are below AA. The root cause is the token --muted (#868e96, 3.3:1) and accent text (4.3:1)")

        # ------------------------------------------------------------------ 390 px: no sideways scroll of the page
        R.section("390 px wide: no sideways scroll of the page")
        et_jobs = api_call(BASE, "GET", "/recruiter/jobs", token=et)[1]["items"]
        tt = api_login(BASE, "candidate@demo.jinder.app", tpw)
        sign_in(b, BASE, "candidate@demo.jinder.app", tpw)
        set_viewport(b, 390, 800, mobile=False)
        narrow = []
        talent_screens = [("Home", "#/home", ".dash"), ("Jobs list", "#/jobs", "[data-list] .job-card"), ("Job detail", "#/jobs/job-data-analytics-mid-01", ".bridge.path"),
                          ("Settings", "#/settings", ".plan-card")]
        for label, route, wait in talent_screens:
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=1.0)
            o = overflow_info(b)
            narrow.append((label, o))
            check(f"390 px (talent) {label}: the page does not scroll sideways (document {o['doc']} px, window {o['inner']} px)", o["doc"] <= o["inner"] and o["body"] <= o["inner"], str(o))
            R.shot(b, f"a11y-390-{label.lower().replace(' ', '-')}.png")
        # compare with 3 jobs
        b.eval("localStorage.clear()", await_promise=False)
        go(b, BASE, "#/compare?ids=job-data-analytics-mid-01,job-data-eng-mid-02,job-demo-data-engineer-mid", "document.querySelector('.cmp-panels .rd-shape')", pump=1.0)
        o = overflow_info(b)
        narrow.append(("Compare (3 jobs)", o))
        check(f"390 px (talent) Compare with 3 jobs: the page does not scroll sideways (document {o['doc']} px); the wide tables scroll inside their own region", o["doc"] <= o["inner"] and o["body"] <= o["inner"], str(o))
        scroll_regions = b.eval("[...document.querySelectorAll('.cmp-scroll')].map(r => [r.scrollWidth > r.clientWidth, r.getAttribute('role'), r.tabIndex])", False)
        check("390 px Compare: each wide table is in a focusable, labelled scroll region", scroll_regions and all(x[0] is not None and x[1] == "region" and x[2] == 0 for x in scroll_regions), str(scroll_regions))
        R.shot(b, "a11y-390-compare.png")
        sign_in(b, BASE, "recruiter@demo.jinder.app", epw)
        set_viewport(b, 390, 800, mobile=False)
        employer_screens = [("Talent list", "#/candidates", ".cand-card"), ("Job form", "#/my-jobs/new", "form.job-form"), ("Job overview", "#/my-jobs/job-demo-data-engineer-mid/overview", ".job-overview .jd-view")]
        for label, route, wait in employer_screens:
            go(b, BASE, route, f"document.querySelector({json.dumps(wait)})", pump=1.0)
            o = overflow_info(b)
            narrow.append((label, o))
            check(f"390 px (employer) {label}: the page does not scroll sideways (document {o['doc']} px, window {o['inner']} px)", o["doc"] <= o["inner"] and o["body"] <= o["inner"], str(o))
            R.shot(b, f"a11y-390-employer-{label.lower().replace(' ', '-')}.png")
        EVIDENCE["390 px"] = {label: o for label, o in narrow}
        # the touch targets at 390 px: buttons and selects are at least 44 px high (the pager and the sort)
        go(b, BASE, "#/candidates", "document.querySelector('.cand-card')")
        small = b.eval("""[...document.querySelectorAll('.pager-btn, .pager-select, .sort-select-input, .btn')].filter(e => e.getBoundingClientRect().width > 0).filter(e => e.getBoundingClientRect().height < 44)
            .map(e => (e.className || '').toString().split(' ').slice(0, 2).join('.') + ':' + Math.round(e.getBoundingClientRect().height))""", False)
        EVIDENCE["controls under 44 px at 390 px (employer talent list)"] = small
        check("390 px: the pager, the sort and the buttons are at least 44 px high (touch targets)", not small, str(small[:8]))
        problems = [p for p in non_extension(b.take_problems()) if "status of 4" not in p]
        check("no console error and no CSP report", not problems, str(problems[:3]))
    finally:
        b.close()
        stop_demo_platform(proc)
        text = open(log, errors="replace").read()
        errors = [l for l in text.splitlines() if " ERROR " in l or "Traceback" in l]
        R.check("the server log has no ERROR line and no traceback", not errors, "; ".join(errors[:3]))
        if ARGS.out:
            json.dump(EVIDENCE, open(ARGS.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def active_text(b):
    return b.eval("(() => { const e = document.activeElement; return e ? e.tagName.toLowerCase() + '#' + e.id + ' ' + (e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 40) : ''; })()", False)


if __name__ == "__main__":
    run()
    raise SystemExit(R.finish())
