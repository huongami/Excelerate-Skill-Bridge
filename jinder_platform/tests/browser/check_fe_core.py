"""Browser checks for the FE-Core work of Jinder V2: shared components, menu, user block, Settings plan card, compare route and API fallbacks.

Usage:
  python tests/browser/check_fe_core.py                      start the platform on port 8120 (temp data folder), run, stop it
  python tests/browser/check_fe_core.py --base http://localhost:8120 --talent-pw X --employer-pw Y   use a platform that runs already
Options: --shots <folder> (screenshots), --debug-port 9320 (Chrome remote debugging port)

It needs Chrome or Edge (see cdp.py). The component checks import the real ES modules in the page, so they test the real code.
Parts that need data that the backend does not have yet (the `benefits` list) run against a clearly marked stub, and say so.
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

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.abspath(os.path.join(HERE, "..", ".."))
results = []
SHOTS_DIR = [""]   # the screenshot folder, set in main()


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def info(text):
    print("INFO " + text)


# ---------------------------------------------------------------- contrast helpers
def _rgb(css):
    """Red, green, blue (0 to 255) from a computed colour: rgb(...), rgba(...) or color(srgb r g b) with 0 to 1 values."""
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
        self.var = tempfile.mkdtemp(prefix="jinder-fe-core-")
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
                    raise RuntimeError("The platform stopped at start:\n" + open(self.log, encoding="utf-8").read())
                time.sleep(0.5)
        else:
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


def nav_labels(b):
    return b.eval("[...document.querySelectorAll('.sidebar-nav .nav-label')].map(e => e.textContent.trim())", False)


def set_viewport(b, width, height, mobile=False):
    b.call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile})
    b.pump(0.4)


def shot(b, shots, name, full=False):
    if shots:
        b.screenshot(os.path.join(shots, name), full=full)


def no_problems(b, name, ignore=()):
    """Check that the browser console has no error, exception or CSP report since the last call.
    Errors that come from a browser extension (chrome-extension://) are not from the app and are skipped.
    `ignore` lists other texts to skip (for example the mock's optional CSV file, which gives a 404 in the console)."""
    problems = [p for p in b.take_problems() if "chrome-extension://" not in p and not any(i in p for i in ignore)]
    check(name, not problems, "; ".join(problems)[:600])


def pick_plan(b, value):
    """Click a radio of the demo plan switch. The switch is off while a change runs, so wait for it first."""
    b.wait_for("document.querySelector('[data-plans]') && !document.querySelector('[data-plans]').disabled")
    b.click(f'[data-plans] input[value={value}]')


# A testbed: a visible box at the top of the page where components are drawn
TESTBED = """
(() => {
  document.getElementById('fe-testbed')?.remove();
  const d = document.createElement('div');
  d.id = 'fe-testbed';
  d.className = 'dash';
  document.querySelector('.app-content')?.prepend(d);
  if (!d.isConnected) document.body.prepend(d);
  return true;
})()
"""


# ---------------------------------------------------------------- the checks
def check_static(base):
    for name in ("styles.css", "styles-core.css", "styles-talent.css", "styles-employer.css", "styles-compare.css", "icons.svg"):
        with urllib.request.urlopen(f"{base}/{name}", timeout=10) as r:
            body = r.read().decode("utf-8")
            check(f"static: {name} is served (200, {r.headers.get_content_type()})", r.status == 200)
            if name.startswith("styles-") and name != "styles-core.css":
                check(f"static: {name} has the owner line", body.startswith("/* owned by "))
            if name == "icons.svg":
                check("icons.svg has i-crown and i-lock", 'id="i-crown"' in body and 'id="i-lock"' in body)
    html = urllib.request.urlopen(f"{base}/index.html", timeout=10).read().decode("utf-8")
    order = [html.find(f'href="{n}"') for n in ("styles.css", "styles-core.css", "styles-talent.css", "styles-employer.css", "styles-compare.css")]
    check("index.html links the 5 style files in order, after styles.css", all(o > 0 for o in order) and order == sorted(order), str(order))


def check_pagination(b, shots):
    r = b.eval("""(async () => {
      const m = await import('/js/components/pagination.js');
      const box = document.getElementById('fe-testbed');
      const out = {};
      out.zero = m.pagerHtml({ page: 1, pageSize: 10, total: 0 });
      out.small = m.pagerHtml({ page: 1, pageSize: 10, total: 8 });
      out.ten = m.pagerHtml({ page: 1, pageSize: 10, total: 10 });
      out.oneBig = m.pagerHtml({ page: 1, pageSize: 50, total: 15 }) !== '';
      box.innerHTML = m.pagerHtml({ page: 2, pageSize: 10, total: 134 });
      out.range = box.querySelector('.pager-range').textContent;
      out.navLabel = box.querySelector('nav').getAttribute('aria-label');
      out.sizeLabel = box.querySelector('label[for="' + box.querySelector('select').id + '"]').textContent;
      out.sizes = [...box.querySelectorAll('select option')].map(o => o.value);
      out.selected = box.querySelector('select').value;
      out.current = [...box.querySelectorAll('[aria-current="page"]')].map(e => e.textContent);
      out.prevDisabled = box.querySelector('[data-pager-page="1"]').textContent.includes('Previous') ? box.querySelector('[data-pager-page="1"]').disabled : null;
      // number of numbered buttons for many pages
      const counts = [];
      for (const [page, total] of [[1, 134], [2, 134], [4, 134], [5, 134], [7, 134], [10, 134], [12, 134], [14, 134], [1, 60], [3, 70]]) {
        box.innerHTML = m.pagerHtml({ page, pageSize: 10, total });
        counts.push([page, total, box.querySelectorAll('.pager-num').length, box.querySelector('[aria-current="page"]')?.textContent, box.querySelectorAll('.pager-gap').length]);
      }
      out.counts = counts;
      // last page: Next is disabled and the range ends at the total
      box.innerHTML = m.pagerHtml({ page: 14, pageSize: 10, total: 134 });
      out.last = box.querySelector('.pager-range').textContent;
      out.nextDisabled = [...box.querySelectorAll('.pager-step')].pop().disabled;
      // a page outside the range is moved into it; an odd total text is escaped
      box.innerHTML = m.pagerHtml({ page: 99, pageSize: 10, total: 25 });
      out.clamped = box.querySelector('.pager-range').textContent;
      // handlers
      box.innerHTML = m.pagerHtml({ page: 2, pageSize: 10, total: 134 });
      const log = [];
      m.bindPager(box, { onPage: (p) => log.push('page' + p), onPageSize: (s) => log.push('size' + s), pageSizeKey: 'fe-core-test' });
      m.bindPager(box, { onPage: (p) => log.push('PAGE' + p), onPageSize: (s) => log.push('SIZE' + s), pageSizeKey: 'fe-core-test' });  // second call replaces the handlers
      box.querySelector('[data-pager-page="3"]').click();
      box.querySelector('[data-pager-page="1"]').click();
      const sel = box.querySelector('select'); sel.value = '20'; sel.dispatchEvent(new Event('change', { bubbles: true }));
      out.log = log;
      out.saved = m.loadPageSize('fe-core-test');
      // storage key
      out.storageKeys = Object.keys(localStorage).filter(k => k.startsWith('jinder.pagesize.'));
      m.savePageSize('fe-core-test', 7);
      out.afterBad = m.loadPageSize('fe-core-test');
      localStorage.setItem(out.storageKeys[0], 'abc');
      out.corrupt = m.loadPageSize('fe-core-test');
      m.savePageSize('fe-core-test', 50);
      out.fifty = m.loadPageSize('fe-core-test');
      out.slots = [m.pageSlots(1, 5), m.pageSlots(8, 20), m.pageSlots(20, 20)];
      box.innerHTML = m.pagerHtml({ page: 3, pageSize: 10, total: 134 });
      return out;
    })()""")
    check("pager: total 0 renders nothing", r["zero"] == "")
    check("pager: a list that the plan limits (limitedTo) renders nothing", b.eval("(async () => { const m = await import('/js/components/pagination.js'); return m.pagerHtml({ page: 1, pageSize: 5, total: 134, limitedTo: 5 }) === '' && m.pagerHtml({ page: 1, pageSize: 10, total: 134, limitedTo: null }) !== ''; })()"))
    check("pager: one page and total at most 10 renders nothing", r["small"] == "" and r["ten"] == "")
    check("pager: one page but total above 10 still shows the size select", r["oneBig"])
    check("pager: text 'Showing 11–20 of 134'", r["range"] == "Showing 11–20 of 134", r["range"])
    check("pager: nav has aria-label", r["navLabel"] == "Pagination")
    check("pager: visible label 'Rows per page' is tied to the select", r["sizeLabel"] == "Rows per page")
    check("pager: sizes 10, 20, 50 and the size is selected", r["sizes"] == ["10", "20", "50"] and r["selected"] == "10", str(r["sizes"]))
    check("pager: current page has aria-current", r["current"] == ["2"], str(r["current"]))
    check("pager: never more than 7 numbered buttons", all(c[2] <= 7 for c in r["counts"]), str(r["counts"]))
    check("pager: the current page is always in the row", all(str(c[0]) == c[3] for c in r["counts"]), str(r["counts"]))
    check("pager: many pages use gaps (ellipsis)", all(c[4] >= 1 for c in r["counts"] if c[1] == 134), str(r["counts"]))
    check("pager: last page range and Next disabled", r["last"] == "Showing 131–134 of 134" and r["nextDisabled"] is True, r["last"])
    check("pager: a page past the end is moved to the last page", r["clamped"] == "Showing 21–25 of 25", r["clamped"])
    check("pager: handlers fire; a second bindPager replaces the first", r["log"] == ["PAGE3", "PAGE1", "SIZE20"], str(r["log"]))
    check("pager: the page size is saved per list and user in localStorage", r["saved"] == 20 and any(k.startswith("jinder.pagesize.fe-core-test.") for k in r["storageKeys"]), str(r["storageKeys"]))
    check("pager: a size that is not 10/20/50 is ignored, a broken stored value gives 10", r["afterBad"] == 20 and r["corrupt"] == 10 and r["fifty"] == 50, f"{r['afterBad']} {r['corrupt']} {r['fifty']}")
    check("pager: slots for 5, 20 pages", r["slots"] == [[1, 2, 3, 4, 5], [1, None, 7, 8, 9, None, 20], [1, None, 16, 17, 18, 19, 20]], str(r["slots"]))
    shot(b, shots, "pager.png")
    # touch size on a small screen
    set_viewport(b, 390, 800, mobile=False)
    h = b.eval("(() => { const e = document.querySelector('#fe-testbed .pager-num'); return e ? e.getBoundingClientRect().height : 0; })()", False)
    check("pager: 44px touch target on small screens", h >= 44, str(h))
    set_viewport(b, 1280, 900)
    b.eval("localStorage.removeItem(Object.keys(localStorage).find(k => k.startsWith('jinder.pagesize.fe-core-test')) || '')", False)


def check_sort(b):
    r = b.eval("""(async () => {
      const m = await import('/js/components/sort-select.js');
      const box = document.getElementById('fe-testbed');
      box.innerHTML = m.sortSelectHtml({ id: 'fe-sort', value: 'newest', options: [{ value: 'best', label: 'Best match' }, { value: 'newest', label: 'Newest posted' }] });
      const sel = box.querySelector('select');
      const label = box.querySelector('label');
      const got = [];
      m.bindSort(box, 'fe-sort', (v) => got.push(v));
      m.bindSort(box, 'fe-sort', (v) => got.push('twice' + v));   // a second bind must not double the calls
      sel.value = 'best'; sel.dispatchEvent(new Event('change', { bubbles: true }));
      box.innerHTML = m.sortSelectHtml({ id: 'x<y', value: 'zzz', options: [{ value: 'a"b', label: '<b>One</b>' }] });
      return { tag: sel.tagName, labelFor: label.getAttribute('for'), id: sel.id, labelText: label.textContent, value0: 'newest', got,
               escaped: box.innerHTML.includes('<b>One</b>') === false && box.querySelector('option').textContent === '<b>One</b>',
               selectedDefault: box.querySelector('option').selected };
    })()""")
    check("sort: native select with a label tied by for/id", r["tag"] == "SELECT" and r["labelFor"] == r["id"] == "fe-sort" and r["labelText"] == "Sort by")
    check("sort: onChange gets the value, once per change", r["got"] == ["best"], str(r["got"]))
    check("sort: text is escaped; unknown value falls back to the first option", r["escaped"] and r["selectedDefault"])


def check_jd(b, shots):
    long_jd = "## About the role\n" + "We build a payments platform. " * 30 + "\n\n## What you will do\n" + "\n".join(f"- Task number {i} with some words" for i in range(40)) + "\n\n## Tech stack\n- Python\n- <script>window.__xss=1</script>\n\nPlain closing line\nsecond line of the same paragraph"
    r = b.eval("""(async (jd) => {
      const m = await import('/js/components/jd-view.js');
      const box = document.getElementById('fe-testbed');
      box.innerHTML = m.jdViewHtml(jd, { label: 'Job description box' });
      const el = box.querySelector('.jd-view');
      const cs = getComputedStyle(el);
      const out = {
        tag: el.tagName, tabindex: el.getAttribute('tabindex'), role: el.getAttribute('role'), label: el.getAttribute('aria-label'),
        h3: [...el.querySelectorAll('h3')].map(e => e.textContent), ul: el.querySelectorAll('ul').length, li: el.querySelectorAll('li').length,
        p: el.querySelectorAll('p').length, maxHeight: cs.maxHeight, overflowY: cs.overflowY, clientH: el.clientHeight, scrollH: el.scrollHeight,
        xss: window.__xss === undefined, scriptTag: el.querySelector('script') === null,
        lastP: [...el.querySelectorAll('p')].pop().textContent,
      };
      el.focus();
      const fs = getComputedStyle(el);
      out.focused = document.activeElement === el;
      out.outlineWidth = fs.outlineWidth; out.outlineStyle = fs.outlineStyle;
      el.scrollTop = 99999;
      out.scrolled = el.scrollTop > 0;
      // no headings: plain text
      box.innerHTML = m.jdViewHtml('Just some text.\\n\\nAnother paragraph.');
      out.plainH3 = box.querySelectorAll('h3').length; out.plainP = box.querySelectorAll('p').length;
      box.innerHTML = m.jdViewHtml('');
      out.emptyText = box.textContent.trim();
      box.innerHTML = m.jdViewHtml(null);
      out.nullOk = box.querySelector('.jd-view') !== null;
      box.innerHTML = m.jdViewHtml(jd);
      out.defaultLabel = box.querySelector('.jd-view').getAttribute('aria-label');
      box.innerHTML = m.jdViewHtml('## A "quoted" <b>heading</b>\\n- item & more');
      out.escaped = box.querySelector('h3').textContent === 'A "quoted" <b>heading</b>' && box.querySelector('li').textContent === 'item & more' && !box.querySelector('b');
      box.innerHTML = m.jdViewHtml(jd, { label: 'Job description box' });
      return out;
    })(%s)""" % json.dumps(long_jd))
    check("jd: a focusable region with a label", r["tag"] == "SECTION" and r["tabindex"] == "0" and r["role"] == "region" and r["label"] == "Job description box" and r["defaultLabel"] == "Job description")
    check("jd: headings are h3, bullets are ul", r["h3"] == ["About the role", "What you will do", "Tech stack"] and r["ul"] == 2 and r["li"] == 42, f"{r['h3']} ul={r['ul']} li={r['li']}")
    check("jd: blank line splits paragraphs, lines in one paragraph stay together", r["p"] == 2 and r["lastP"] == "Plain closing line\nsecond line of the same paragraph", f"p={r['p']} {r['lastP']!r}")
    check("jd: max height 32rem and a scroll bar", r["maxHeight"] == "512px" and r["overflowY"] == "auto" and r["scrollH"] > r["clientH"], f"{r['maxHeight']} {r['overflowY']} {r['clientH']} {r['scrollH']}")
    check("jd: the box scrolls", r["scrolled"])
    check("jd: visible focus ring", r["focused"] and r["outlineStyle"] != "none" and r["outlineWidth"] not in ("0px", ""), f"{r['outlineStyle']} {r['outlineWidth']}")
    check("jd: all text is escaped (no script runs, no tag made)", r["xss"] and r["scriptTag"] and r["escaped"])
    check("jd: no headings gives plain paragraphs; empty and null do not break", r["plainH3"] == 0 and r["plainP"] == 2 and "no description" in r["emptyText"].lower() and r["nullOk"])
    shot(b, shots, "jd-view.png")


def check_premium(b):
    r = b.eval("""(async () => {
      const m = await import('/js/components/premium.js');
      const box = document.getElementById('fe-testbed');
      box.innerHTML = m.crownIconHtml() + m.premiumChipHtml() + m.premiumChipHtml('Gold <b>') + m.lockedBadgeHtml('Invite talent') + m.lockedBadgeHtml('Compare', { static: true }) + m.crownIconHtml({ decorative: true });
      const crown = box.querySelector('.crown[role="img"]');
      const chip = box.querySelector('.premium-chip');
      const lock = box.querySelector('button.locked-badge');
      const stat = box.querySelector('span.locked-badge');
      const out = {
        crownLabel: crown.getAttribute('aria-label'), crownUse: crown.querySelector('use').getAttribute('href'),
        chipText: chip.textContent, chip2: box.querySelectorAll('.premium-chip')[1].textContent, chip2Safe: box.querySelectorAll('.premium-chip')[1].querySelector('b') === null,
        lockUse: lock.querySelector('use').getAttribute('href'), lockText: lock.textContent, lockAttr: lock.dataset.premiumLock, staticTag: stat.tagName,
        decorative: box.querySelectorAll('.crown[aria-hidden="true"]').length,
      };
      m.bindPremiumLocks(box); m.bindPremiumLocks(box);
      lock.click();
      await new Promise(r => setTimeout(r, 200));
      const dlg = document.querySelector('dialog.modal-small[open]');
      out.dialogTitle = dlg ? dlg.querySelector('h2').textContent : null;
      out.dialogText = dlg ? dlg.querySelector('.modal-sub').textContent : null;
      out.dialogCount = document.querySelectorAll('dialog.modal-small').length;
      out.goBtn = dlg ? dlg.querySelector('[type=submit]').textContent : null;
      if (dlg) dlg.close();
      return out;
    })()""")
    check("premium: crown has a text alternative", r["crownLabel"] == "Premium" and r["crownUse"].endswith("#i-crown") and r["decorative"] == 1)
    check("premium: gold chip text, escaped", r["chipText"] == "Premium" and r["chip2"] == "Gold <b>" and r["chip2Safe"])
    check("premium: lock badge has the lock icon, the name of the feature, and a static variant", r["lockUse"].endswith("#i-lock") and "Invite talent" in r["lockText"] and r["lockAttr"] == "Invite talent" and r["staticTag"] == "SPAN")
    check("premium: a click on a locked feature opens the 'Premium feature' dialog (once)", r["dialogTitle"] == "Premium feature" and "Invite talent is part of Premium" in (r["dialogText"] or "") and r["dialogCount"] == 1 and r["goBtn"] == "Go to Settings", str(r))
    cols = b.eval("""(() => { const box = document.getElementById('fe-testbed'); box.innerHTML = '<span class="chip chip-gold" id="gc">Premium</span>'; const e = document.getElementById('gc'); const cs = getComputedStyle(e); return { fg: cs.color, bg: cs.backgroundColor }; })()""", False)
    ratio = contrast(cols["fg"], cols["bg"])
    check(f"premium: gold chip text contrast is at least 4.5:1 (is {ratio:.2f})", ratio >= 4.5)


def check_compare_store(b):
    r = b.eval("""(async () => {
      const { compareStore } = await import('/js/core/compare-store.js');
      const { session } = await import('/js/core/session.js');
      const uid = session.user.id;
      compareStore.clear('job'); compareStore.clear('talent');
      const events = [];
      const on = (e) => events.push(e.detail.kind + ':' + e.detail.action);
      window.addEventListener('jinder:compare-change', on);
      const out = { uid };
      out.addResults = [1, 2, 3, 4, 5, 6].map(i => compareStore.add('job', { id: 'j' + i, title: 'Job ' + i }));
      out.count = compareStore.items('job').length;
      out.dup = compareStore.add('job', { id: 'j1', title: 'Job 1 again' }); out.countAfterDup = compareStore.items('job').length;
      out.has = [compareStore.has('job', 'j3'), compareStore.has('job', 'j6'), compareStore.has('talent', 'j3')];
      out.kindsSeparate = compareStore.add('talent', { id: 't1', alias: 'Teal Heron' }) && compareStore.items('talent')[0].title;
      out.badKind = compareStore.add('other', { id: 'x' });
      out.badItem = [compareStore.add('job', null), compareStore.add('job', {}), compareStore.add('job', { id: '' })];
      out.key = Object.keys(localStorage).filter(k => k.startsWith('jinder.compare.'));
      compareStore.remove('job', 'j2'); out.afterRemove = compareStore.items('job').map(i => i.id);
      out.addAfterRemove = compareStore.add('job', { id: 'j7', title: 'Job 7' });
      compareStore.remove('job', 'nope');
      out.events = events.slice();
      // stored text is plain and short
      compareStore.add('talent', { id: 't2', alias: 'X'.repeat(500), extra: { nested: 1 }, fn: () => 1 });
      out.longTitle = compareStore.items('talent')[1].title.length; out.noNested = compareStore.items('talent')[1].extra === undefined;
      // corrupted storage
      const jobKey = 'jinder.compare.' + uid + '.job';
      localStorage.setItem(jobKey, '{not json'); out.corrupt1 = compareStore.items('job').length;
      localStorage.setItem(jobKey, '"text"'); out.corrupt2 = compareStore.items('job').length;
      localStorage.setItem(jobKey, JSON.stringify([null, 5, { id: 'ok', title: 'Fine' }, { id: 'ok' }, { title: 'no id' }])); out.corrupt3 = compareStore.items('job').map(i => i.id);
      localStorage.setItem(jobKey, JSON.stringify(Array.from({ length: 9 }, (_, i) => ({ id: 'm' + i })))); out.cap = compareStore.items('job').length;
      compareStore.clear('job');
      out.afterClear = [compareStore.items('job').length, localStorage.getItem(jobKey)];
      window.removeEventListener('jinder:compare-change', on);
      compareStore.clear('talent');
      return out;
    })()""")
    check("store: add returns true up to 5 and false for the 6th", r["addResults"] == [True] * 5 + [False] and r["count"] == 5, str(r["addResults"]))
    check("store: the same id twice does not add a copy", r["dup"] is True and r["countAfterDup"] == 5)
    check("store: has() and separate kinds", r["has"] == [True, False, False] and r["kindsSeparate"] == "Teal Heron")
    check("store: wrong kind or wrong item is refused", r["badKind"] is False and r["badItem"] == [False, False, False])
    check("store: storage key jinder.compare.<userId>.<kind>", sorted(r["key"]) == sorted([f"jinder.compare.{r['uid']}.job", f"jinder.compare.{r['uid']}.talent"]), str(r["key"]))
    check("store: remove works and frees a place", r["afterRemove"] == ["j1", "j3", "j4", "j5"] and r["addAfterRemove"] is True)
    check("store: event jinder:compare-change for each change (not for a no-op)", r["events"] == ["job:add"] * 5 + ["talent:add", "job:remove", "job:add"], str(r["events"]))
    check("store: stored text is cut and not nested", r["longTitle"] <= 120 and r["noNested"])
    check("store: corrupted storage is ignored", r["corrupt1"] == 0 and r["corrupt2"] == 0 and r["corrupt3"] == ["ok"] and r["cap"] == 5, f"{r['corrupt1']} {r['corrupt2']} {r['corrupt3']} {r['cap']}")
    check("store: clear empties the basket and the key", r["afterClear"] == [0, None], str(r["afterClear"]))


def check_tray(b, shots, kind, item_a, item_b):
    """The tray is mounted by the shell. Kind 'job' (talent) or 'talent' (employer)."""
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('job'); compareStore.clear('talent'); })()")
    b.pump(0.3)
    hidden0 = b.eval("(() => { const t = document.querySelector('[data-compare-tray]'); return !!t && t.hidden && getComputedStyle(t).display === 'none'; })()", False)
    check(f"tray ({kind}): hidden when the basket is empty", hidden0)
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.add(%s, %s); })()" % (json.dumps(kind), json.dumps(item_a)))
    b.pump(0.3)
    one = b.eval("""(() => { const t = document.querySelector('[data-compare-tray]'); const open = t.querySelector('[data-compare-open-disabled], a[href="#/compare"]');
      return { visible: !t.hidden && getComputedStyle(t).display !== 'none', title: t.querySelector('.compare-tray-title').textContent, chips: [...t.querySelectorAll('.compare-chip > span')].map(e => e.textContent),
        removeLabel: t.querySelector('[data-compare-remove]').getAttribute('aria-label'), openTag: open.tagName, ariaDisabled: open.getAttribute('aria-disabled'), hint: t.querySelector('.compare-tray-hint')?.textContent,
        describedBy: open.getAttribute('aria-describedby'), clear: !!t.querySelector('[data-compare-clear]'), shell: document.querySelector('.app-shell').classList.contains('has-compare-tray') }; })()""", False)
    check(f"tray ({kind}): shows 'Compare (1/5)', the item as a chip with a remove button", one["visible"] and one["title"] == "Compare (1/5)" and one["chips"] == [item_a.get("title") or item_a.get("alias")] and "Remove" in one["removeLabel"], str(one))
    check(f"tray ({kind}): 'Open compare' is disabled with an explanation when there is 1 item", one["openTag"] == "BUTTON" and one["ariaDisabled"] == "true" and one["hint"] and one["describedBy"] == "compare-tray-hint" and one["clear"], str(one))
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.add(%s, %s); })()" % (json.dumps(kind), json.dumps(item_b)))
    b.pump(0.3)
    two = b.eval("""(() => { const t = document.querySelector('[data-compare-tray]'); const a = t.querySelector('a[href="#/compare"]');
      return { title: t.querySelector('.compare-tray-title').textContent, link: !!a, linkText: a?.textContent, disabledLeft: !!t.querySelector('[data-compare-open-disabled]') }; })()""", False)
    check(f"tray ({kind}): with 2 items 'Open compare' is a link to #/compare", two["title"] == "Compare (2/5)" and two["link"] and two["linkText"] == "Open compare" and not two["disabledLeft"], str(two))
    # the bar covers no content
    b.eval("window.scrollTo(0, 1e7)", False)
    b.pump(0.3)
    cover = b.eval("""(() => { const t = document.querySelector('[data-compare-tray]').getBoundingClientRect();
      let last = document.querySelector('.app-content'); while (last.lastElementChild && !last.lastElementChild.hidden) last = last.lastElementChild;
      const lb = last.getBoundingClientRect(); const pad = parseFloat(getComputedStyle(document.querySelector('.app-content')).paddingBottom);
      return { trayTop: t.top, trayLeft: t.left, trayHeight: t.height, lastBottom: lb.bottom, pad, sidebarW: document.querySelector('.sidebar').getBoundingClientRect().width, vh: innerHeight }; })()""", False)
    check(f"tray ({kind}): the bar covers no content (last element ends above the bar) and the main area has bottom padding", cover["lastBottom"] <= cover["trayTop"] + 1 and cover["pad"] >= cover["trayHeight"], str(cover))
    check(f"tray ({kind}): the bar starts at the right of the menu and sits at the bottom", abs(cover["trayLeft"] - cover["sidebarW"]) <= 1 and abs(cover["trayTop"] + cover["trayHeight"] - cover["vh"]) <= 1, str(cover))
    shot(b, shots, f"tray-{kind}.png")
    # remove and clear
    b.click("[data-compare-remove]")
    one_left = b.eval("document.querySelector('[data-compare-tray] .compare-tray-title').textContent", False)
    check(f"tray ({kind}): the remove button of a chip removes it", one_left == "Compare (1/5)", one_left)
    b.click("[data-compare-clear]")
    gone = b.eval("document.querySelector('[data-compare-tray]').hidden && !document.querySelector('.app-shell').classList.contains('has-compare-tray')", False)
    check(f"tray ({kind}): Clear empties the basket and hides the bar", gone)
    # survives a reload
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.add(%s, %s); })()" % (json.dumps(kind), json.dumps(item_a)))
    b.eval("window.__qa_before_reload = true", False)       # the old page is still there for a moment after the reload starts: wait for the new page (QA fix of a race)
    b.call("Page.reload")
    b.wait_for("!window.__qa_before_reload && document.querySelector('[data-compare-tray] .compare-tray-title')", 30)
    b.pump(0.3)
    after = b.eval("document.querySelector('[data-compare-tray] .compare-tray-title').textContent", False)
    check(f"tray ({kind}): the basket survives a reload", after == "Compare (1/5)", after)
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('job'); compareStore.clear('talent'); })()")


def check_collapsed(b, shots):
    """The menu hidden to icons only (72px): the lock stays, the user link is still one link, and the basket bar moves with the menu."""
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('talent'); compareStore.add('talent', { id: 'c1', alias: 'Teal Heron' }); })()")
    b.click(".sidebar-toggle")
    b.pump(0.6)
    r = b.eval("""(() => { const lock = document.querySelector('[data-nav-lock]'); const lr = lock.getBoundingClientRect(); const u = document.getElementById('shellUser').getBoundingClientRect();
      const t = document.querySelector('[data-compare-tray]').getBoundingClientRect();
      return { sidebar: document.querySelector('.sidebar').getBoundingClientRect().width, lockVisible: lr.width > 0 && lr.height > 0, lockPos: getComputedStyle(lock).position, textHidden: getComputedStyle(lock.querySelector('.nav-premium-text')).display === 'none',
        iconVisible: lock.querySelector('.icon').getBoundingClientRect().width > 0, userWidth: u.width, trayLeft: t.left, linkName: document.getElementById('shellUser').getAttribute('aria-label'), navTitle: lock.closest('a').title }; })()""", False)
    check("collapsed menu: the lock on Compare stays as a small icon (text hidden), and the link keeps a title", r["sidebar"] == 72 and r["lockVisible"] and r["lockPos"] == "absolute" and r["textHidden"] and r["iconVisible"] and "Premium" in r["navTitle"], str(r))
    check("collapsed menu: the user block is still one link with its name, and the basket bar starts at the right of the 72px menu", r["linkName"].startswith("Account settings, ") and abs(r["trayLeft"] - 72) <= 1, str(r))
    shot(b, shots, "shell-collapsed.png")
    b.click(".sidebar-toggle")
    b.pump(0.4)
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('talent'); })()")


def check_icons(b, shots):
    """The crown must be easy to know at 16px. This only draws the icons at 3 sizes for a screenshot, and checks that the symbols have shapes."""
    # Sizes are set with the DOM (CSSOM), because the CSP blocks style attributes
    b.eval(TESTBED)
    r = b.eval("""(() => { const box = document.getElementById('fe-testbed'); box.replaceChildren();
      const ns = 'http://www.w3.org/2000/svg'; const rows = {};
      for (const [id, cls] of [['i-crown', 'crown'], ['i-lock', 'lock-row']]) {
        const row = document.createElement('div'); row.className = cls; box.append(row); rows[id] = row;
        for (const s of [16, 20, 32, 64]) {
          const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('class', 'icon'); svg.style.width = svg.style.height = s + 'px'; svg.style.margin = '8px';
          const use = document.createElementNS(ns, 'use'); use.setAttribute('href', 'icons.svg#' + id); svg.append(use); row.append(svg);
        }
      }
      return { w: rows['i-crown'].firstChild.getBoundingClientRect().width, n: [...box.querySelectorAll('svg')].length }; })()""", False)
    check("icons: crown and lock draw at 16, 20, 32 and 64px", r["w"] == 16 and r["n"] == 8)
    if shots:
        import base64
        box = b.eval("(() => { const r = document.getElementById('fe-testbed').getBoundingClientRect(); return { x: r.x, y: r.y + scrollY, w: 360, h: 190 }; })()", False)
        data = b.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True, "clip": {"x": box["x"] + 24, "y": box["y"] + 40, "width": box["w"], "height": box["h"], "scale": 3}})["data"]
        with open(os.path.join(shots, "icons-crown-lock.png"), "wb") as f:
            f.write(base64.b64decode(data))


def check_radar(b, shots):
    r = b.eval("""(async () => {
      const m = await import('/js/components/radar.js');
      const box = document.getElementById('fe-testbed');
      box.style.width = '640px';
      const names = ['Languages', 'Frameworks & libraries', 'Cloud & DevOps', 'Data & storage', 'ML & AI', 'Engineering practices', 'Collaboration', 'Experience', 'Level', 'Certifications'];
      const overlap = (a, b) => !(a.right <= b.left + 0.5 || b.right <= a.left + 0.5 || a.bottom <= b.top + 0.5 || b.bottom <= a.top + 0.5);
      const out = { perCount: {} };
      for (let n = 3; n <= 10; n++) {
        for (const ns of [1, 5]) {
          const axes = names.slice(0, n).map(l => ({ label: l }));
          const series = Array.from({ length: ns }, (_, k) => ({ name: 'Series ' + (k + 1), values: axes.map((_, i) => 20 + ((i * 17 + k * 23) % 80)) }));
          box.innerHTML = m.radarHtml({ axes, series });
          const svg = box.querySelector('svg'); const sr = svg.getBoundingClientRect();
          const labels = [...svg.querySelectorAll('.rd-label')].map(e => e.getBoundingClientRect());
          let overlaps = 0; for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) if (overlap(labels[i], labels[j])) overlaps++;
          const outside = labels.filter(r => r.left < sr.left - 0.5 || r.right > sr.right + 0.5 || r.top < sr.top - 0.5 || r.bottom > sr.bottom + 0.5).length;
          out.perCount[n + 'x' + ns] = { labels: labels.length, overlaps, outside, shapes: svg.querySelectorAll('.rd-shape').length };
        }
      }
      // long label wraps
      box.innerHTML = m.radarHtml({ axes: names.slice(0, 7).map(l => ({ label: l })), series: [{ name: 'A', values: [10, 20, 30, 40, 50, 60, 70] }] });
      const second = box.querySelectorAll('.rd-label')[1];
      out.wrapLines = second.querySelectorAll('tspan').length; out.wrapTitle = second.querySelector('title').textContent;
      box.innerHTML = m.radarHtml({ axes: [{ label: 'Infrastructure-as-code-and-everything-else' }, { label: 'A very long label that goes on and on and on and on and on and on' }, { label: 'x' }], series: [{ name: 'A', values: [1, 2, 3] }] });
      out.longLabels = [...box.querySelectorAll('.rd-label')].map(e => e.querySelectorAll('tspan').length + ':' + e.textContent.length);
      // 5 series: colour, dash, marker
      const axes = names.slice(0, 6).map(l => ({ label: l }));
      const series = ['One', 'Two', 'Three', 'Four', 'Five', 'Six'].map((name, k) => ({ name, values: axes.map((_, i) => 30 + ((i * 11 + k * 19) % 60)) }));
      box.innerHTML = m.radarHtml({ axes, series }, { caption: 'Five things' });
      out.shapesFor6 = box.querySelectorAll('.rd-shape').length;
      const sh = [...box.querySelectorAll('.rd-shape')].map(e => { const cs = getComputedStyle(e); return { stroke: cs.stroke, dash: cs.strokeDasharray, fillOp: cs.fillOpacity, w: cs.strokeWidth, cap: cs.strokeLinecap }; });
      out.series = sh;
      out.markers = [...new Set([...box.querySelectorAll('.rd-series')].map(g => { const d = g.querySelector('.rd-dot'); return d.tagName + (d.getAttribute('points') || '').split(' ').length + (d.classList.contains('rd-dot-cross') ? 'x' : ''); }))].length;
      out.legend = [...box.querySelectorAll('.rd-legend li')].map(li => li.textContent.trim());
      out.legendSwatch = [...box.querySelectorAll('.rd-swatch-line')].map(e => getComputedStyle(e).strokeDasharray);
      out.aria = box.querySelector('svg').getAttribute('aria-label');
      out.role = box.querySelector('svg').getAttribute('role');
      out.caption = box.querySelector('figcaption').textContent;
      out.table = (() => { box.insertAdjacentHTML('beforeend', m.radarTableHtml({ axes, series })); const t = box.querySelector('table'); return { rows: t.querySelectorAll('tbody tr').length, cols: t.querySelectorAll('thead th').length, first: t.querySelector('tbody tr td').textContent }; })();
      box.innerHTML = m.radarHtml({ axes, series: series.slice(0, 5) });
      out.shot5 = true;
      return out;
    })()""")
    for key, v in sorted(r["perCount"].items()):
        pass
    bad = {k: v for k, v in r["perCount"].items() if v["overlaps"] or v["outside"]}
    check("radar: 3 to 10 axes render, with 1 and 5 series", len(r["perCount"]) == 16 and all(v["shapes"] == int(k.split("x")[1]) for k, v in r["perCount"].items()))
    check("radar: no axis labels overlap, and all labels are inside the chart, for 3 to 10 axes", not bad, str(bad))
    check("radar: a long label ('Frameworks & libraries') wraps to 2 lines and keeps its full text as a title", r["wrapLines"] == 2 and r["wrapTitle"] == "Frameworks & libraries", f"{r['wrapLines']} {r['wrapTitle']}")
    check("radar: very long labels are cut to at most 3 lines", all(int(x.split(':')[0]) <= 3 for x in r["longLabels"]), str(r["longLabels"]))
    check("radar: at most 5 series are drawn", r["shapesFor6"] == 5)
    strokes = [s["stroke"] for s in r["series"]]
    dashes = [s["dash"] for s in r["series"]]
    check("radar: 5 distinct colours", len(set(strokes)) == 5, str(strokes))
    check("radar: 5 distinct line styles (solid, dashed, dotted, dash-dot, long-dash)", len(set(dashes)) == 5 and dashes[0] == "none", str(dashes))
    check("radar: 5 distinct marker shapes", r["markers"] == 5, str(r["markers"]))
    ratios = [contrast(s, "rgb(255, 255, 255)") for s in strokes]
    check("radar: every series colour has at least 3:1 contrast on white (graphics)", all(x >= 3.0 for x in ratios), ", ".join(f"{x:.2f}" for x in ratios))
    info("radar series contrast on white: " + ", ".join(f"{x:.2f}" for x in ratios))
    check("radar: legend lists the series; its swatches use the same line styles", r["legend"][:2] == ["One", "Two"] and len(r["legend"]) == 5 and r["legendSwatch"] == dashes, f"{r['legend']} {r['legendSwatch']} vs {dashes}")
    check("radar: aria-label lists every value of every series; role img; caption", r["role"] == "img" and r["aria"].count("Languages") == 5 and r["aria"].startswith("One: Languages ") and r["caption"] == "Five things")
    check("radar: table has one row per axis and one column per series", r["table"]["rows"] == 6 and r["table"]["cols"] == 6 and re.match(r"^\d+\.\d$", r["table"]["first"]))
    shot(b, shots, "radar-5-series.png")
    # axis count screenshots
    b.eval("""(async () => { const m = await import('/js/components/radar.js'); const box = document.getElementById('fe-testbed');
      const names = ['Languages', 'Frameworks & libraries', 'Cloud & DevOps', 'Data & storage', 'ML & AI', 'Engineering practices', 'Collaboration', 'Experience', 'Level', 'Certifications'];
      const axes = names.map(l => ({ label: l })); const s = (k) => ({ name: 'Series ' + k, values: axes.map((_, i) => 25 + ((i * 13 + k * 7) % 70)) });
      box.innerHTML = m.radarHtml({ axes, series: [s(1), s(2)] }); })()""")
    shot(b, shots, "radar-10-axes.png")
    # two-layer mode
    l = b.eval("""(async () => {
      const m = await import('/js/components/radar.js'); const box = document.getElementById('fe-testbed');
      const axes = ['Languages', 'Frameworks & libraries', 'Cloud & DevOps', 'Data & storage', 'ML & AI', 'Engineering practices', 'Collaboration'].map(l => ({ label: l }));
      const data = { axes, series: [{ name: 'You have', values: [60, 40, 30, 50, 20, 70, 80] }, { name: 'Job requires', values: [80, 60, 60, 50, 40, 60, 60] }] };
      const res = {};
      for (const how of ['data', 'option']) {
        box.innerHTML = how === 'data' ? m.radarHtml({ ...data, layers: true }) : m.radarHtml(data, { layers: true });
        const s1 = getComputedStyle(box.querySelector('.rd-shape.series-1')), s2 = getComputedStyle(box.querySelector('.rd-shape.series-2'));
        res[how] = { fig: box.querySelector('figure').className, fill1: parseFloat(s1.fillOpacity), fill2: s2.fill, w1: parseFloat(s1.strokeWidth), w2: parseFloat(s2.strokeWidth), legend: [...box.querySelectorAll('.rd-legend li')].map(li => li.textContent.trim()),
          swatchFill: box.querySelectorAll('.rd-swatch-fill').length };
      }
      box.innerHTML = m.radarHtml({ ...data, layers: true });
      res.aria = box.querySelector('svg').getAttribute('aria-label').slice(0, 60);
      // old call, no options
      box.innerHTML = m.radarHtml({ axes, series: [data.series[0]] });
      res.old = { fig: box.querySelector('figure').className, shapes: box.querySelectorAll('.rd-shape').length, fill: parseFloat(getComputedStyle(box.querySelector('.rd-shape')).fillOpacity) };
      box.innerHTML = m.radarHtml({ axes: [{ label: 'a' }, { label: 'b' }], series: [data.series[0]] }) + '|' + m.radarHtml({ axes, series: [] });
      res.tooFew = box.textContent.trim() === '|';
      box.innerHTML = m.radarHtml({ ...data, layers: true });
      return res;
    })()""")
    for how in ("data", "option"):
        v = l[how]
        check(f"radar layers ({how}): series 1 filled, series 2 outline only and thicker", v["fill1"] > 0.2 and v["fill2"] == "none" and v["w2"] > v["w1"], str(v))
        check(f"radar layers ({how}): legend names come from the series", v["legend"] == ["You have", "Job requires"] and v["swatchFill"] == 1, str(v["legend"]))
    check("radar layers: aria-label starts with the series name", l["aria"].startswith("You have: Languages 60.0"), l["aria"])
    check("radar: the old call radarHtml({axes, series}) still works; fewer than 3 axes or no series gives an empty string", l["old"]["shapes"] == 1 and "radar-layers" not in l["old"]["fig"] and 0.05 < l["old"]["fill"] < 0.2 and l["tooFew"], str(l["old"]))
    shot(b, shots, "radar-layers.png")


def check_shell_employer(b, base, pw, shots):
    sign_in(b, base, "recruiter@demo.jinder.app", pw)
    labels = nav_labels(b)
    check("employer menu: Home, Talent, My jobs, Compare, Notifications (no Settings)", labels == ["Home", "Talent", "My jobs", "Compare", "Notifications"], str(labels))
    sidebar_links = b.eval("[...document.querySelectorAll('.sidebar a[href=\"#/settings\"]')].map(a => a.id)", False)
    check("exactly one link to Settings in the menu: the user block", sidebar_links == ["shellUser"], str(sidebar_links))
    user = b.eval("""(() => { const a = document.getElementById('shellUser'); const nested = a.querySelectorAll('a, button, input, select, [tabindex]').length;
      return { tag: a.tagName, href: a.getAttribute('href'), label: a.getAttribute('aria-label'), nested, initials: a.querySelector('.avatar').textContent, text: a.innerText.replace(/\\s+/g, ' ').trim(),
        premium: a.classList.contains('is-premium'), chipHidden: getComputedStyle(a.querySelector('.premium-chip')).display === 'none', crownHidden: getComputedStyle(a.querySelector('.avatar-crown')).display === 'none' }; })()""", False)
    check("user block: ONE focusable link to #/settings with the name 'Account settings, <name>'", user["tag"] == "A" and user["href"] == "#/settings" and user["nested"] == 0 and user["label"].startswith("Account settings, "), str(user))
    check("user block: avatar initials, name and role", len(user["initials"]) >= 1 and "Employer" in user["text"], user["text"])
    check("Basic employer: no crown, no gold ring, no Premium chip", not user["premium"] and user["chipHidden"] and user["crownHidden"])
    lock = b.eval("""(() => { const l = document.querySelector('[data-nav-lock]'); const a = l.closest('a'); return { shown: getComputedStyle(l).display !== 'none', text: l.textContent.trim(), href: a.getAttribute('href'), title: a.title }; })()""", False)
    check("Basic employer: 'Compare' has a gold lock and 'Premium' badge, and still links to #/compare", lock["shown"] and lock["text"] == "Premium" and lock["href"] == "#/compare", str(lock))
    so = b.eval("(() => { const s = document.querySelector('.nav-signout'); s.focus(); return { focus: document.activeElement === s, visible: s.getBoundingClientRect().height > 0, text: s.textContent.trim() }; })()", False)
    check("'Sign out' stays visible and reachable by keyboard", so["focus"] and so["visible"] and so["text"] == "Sign out", str(so))
    # keyboard: tab from the last nav link goes to the user link, then to Sign out.
    # The router moves focus to the page heading when a page has loaded. Wait for that first, so that it does not take our focus.
    try:
        b.wait_for("document.activeElement && document.activeElement.tagName === 'H1'", timeout=8)
    except TimeoutError:
        pass
    b.eval("document.querySelector('.sidebar-nav li:last-child a').focus()", False)
    b.call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    b.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    b.pump(0.2)
    first = b.eval("document.activeElement.id || document.activeElement.className", False)
    b.call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    b.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9})
    b.pump(0.2)
    second = b.eval("document.activeElement.className", False)
    check("keyboard: Tab goes from the menu to the user link, then to Sign out", first == "shellUser" and "nav-signout" in second, f"{first} / {second}")
    shot(b, shots, "shell-employer-basic.png")
    # Compare page
    b.click('.sidebar-nav a[href="#/compare"]')
    b.wait_for("location.hash === '#/compare' && document.querySelector('h1')")
    # FE-Compare replaced the stub: a Basic employer gets the locked page (h1 "Compare talent", the Premium badge)
    check("Compare opens #/compare: a Basic employer gets the locked page (h1 'Compare talent' and the Premium badge)",
          b.text("h1") == "Compare talent" and "Premium" in b.text("main"), b.text("main")[:100])
    check("Compare page: the menu marks Compare as the current page and the basket bar is not shown there", b.eval("document.querySelector('.sidebar-nav a[href=\"#/compare\"]').getAttribute('aria-current') === 'page' && document.querySelector('[data-compare-tray]') === null", False))
    # Old routes redirect and keep the ids
    b.eval("location.hash = '#/jobs/compare?ids=a,b,c'", False)
    b.wait_for("location.hash.startsWith('#/compare')")
    h1 = b.eval("location.hash", False)
    check("old route #/jobs/compare?ids=a,b,c goes to #/compare?ids=a%2Cb%2Cc", h1 in ("#/compare?ids=a%2Cb%2Cc", "#/compare?ids=a,b,c"), h1)
    b.eval("location.hash = '#/candidates/compare?a=x1&b=y2&jobId=job9'", False)
    b.wait_for("location.hash.startsWith('#/compare') && location.hash.includes('jobId')")
    h2 = b.eval("location.hash", False)
    check("old route #/candidates/compare?a=&b=&jobId= goes to #/compare?ids=a,b&jobId=", h2.startswith("#/compare?") and "ids=x1%2Cy2" in h2 and "jobId=job9" in h2, h2)
    b.pump(0.4)
    check("redirects leave a working page (h1 Compare talent)", b.text("h1") == "Compare talent")
    # user block opens Settings
    b.click("#shellUser")
    b.wait_for("location.hash.startsWith('#/settings') && document.querySelector('h1')")
    check("the user block opens Settings", b.text("h1") == "Settings")
    check("Settings: the user link is marked as the current page", b.eval("document.getElementById('shellUser').getAttribute('aria-current') === 'page'", False))
    return b


def check_plan_and_crown(b, shots, who):
    """On the Settings page: switch to Premium with the demo switch and see the crown; then back to Basic."""
    b.eval("location.hash = '#/settings?section=plan'", False)
    b.wait_for("document.querySelector('[data-plans] input[value=premium]')")
    b.pump(0.6)
    plan_first = b.eval("document.querySelector('#plan').id === 'plan' && document.querySelector('.settings > section:nth-of-type(1)')?.id", False)
    check(f"settings ({who}): the plan section is the first section and has id plan", plan_first == "plan", str(plan_first))
    pick_plan(b, "premium")
    b.wait_for("document.getElementById('shellUser').classList.contains('is-premium')")
    b.pump(0.3)
    crown = b.eval("""(() => { const a = document.getElementById('shellUser'); const c = a.querySelector('.avatar-crown'); const av = a.querySelector('.avatar');
      return { crown: getComputedStyle(c).display !== 'none', ring: getComputedStyle(av).boxShadow, chip: getComputedStyle(a.querySelector('.premium-chip')).display !== 'none', note: document.getElementById('shellPlanNote').textContent,
        label: a.getAttribute('aria-label'), lockGone: (() => { const l = document.querySelector('[data-nav-lock]'); return !l || getComputedStyle(l).display === 'none'; })() }; })()""", False)
    check(f"{who}: after Premium the crown shows on the avatar, with a gold ring and a 'Premium' chip", crown["crown"] and "rgb(255, 163, 64)" in crown["ring"] and crown["chip"], str(crown))
    check(f"{who}: the Premium crown has a text alternative and the link name stays 'Account settings, <name>'", crown["note"] == "Premium plan" and crown["label"].startswith("Account settings, "))
    if who == "employer":
        check("employer: the lock on Compare is gone for Premium", crown["lockGone"])
    shot(b, shots, f"shell-{who}-premium.png")
    # the crown stays on the next page
    b.eval("location.hash = '#/home'", False)
    b.wait_for("location.hash === '#/home' && document.getElementById('shellUser')")
    b.pump(0.4)
    check(f"{who}: the crown stays after a page change", b.eval("document.getElementById('shellUser').classList.contains('is-premium')", False))
    # back to Basic
    b.eval("location.hash = '#/settings'", False)
    b.wait_for("document.querySelector('[data-plans] input[value=basic]')")
    b.pump(0.5)
    pick_plan(b, "basic")
    b.wait_for("!document.getElementById('shellUser').classList.contains('is-premium')")
    check(f"{who}: back to Basic the crown goes away", True)


def check_plan_card_stub(b, shots, who):
    """The plan card with a STUB for the entitlements (the backend of this wave has no `benefits` yet). Says so in the output."""
    stub = """(async () => {
      const { api } = await import('/js/api/index.js');
      window.__plan = 'basic';
      const list = (p) => (%s).map((k, i) => ({ key: k[0], label: k[1], description: k[2], available: p, used: p && i === 0, usedCount: p && i === 0 ? 3 : 0 }));
      api.entitlements.get = async () => ({ plan: window.__plan, crown: window.__plan === 'premium', topN: null, canContact: window.__plan === 'premium', canCompare: window.__plan === 'premium', advancedCharts: window.__plan === 'premium', compareMax: 5, benefits: list(window.__plan === 'premium') });
      api.entitlements.set = async (plan) => { window.__plan = plan; const e = await api.entitlements.get(); window.dispatchEvent(new CustomEvent('jinder:plan-change', { detail: e })); return e; };
      return true; })()"""
    items = ("[['all_talent','See all talent','See every talent that fits your job, not only the top 5.'],['invite','Invite talent','Send a message to talent that you like.'],['compare','Compare talent','Compare up to 5 anonymous profiles side by side.'],['advanced_charts','Advanced charts','See the pipeline and the interest for each job.']]"
             if who == "employer" else
             "[['skills_to_learn','Skills to learn next','See which skills open the most jobs for you.'],['skill_demand','Demand for your skills','See how many jobs ask for your skills.']]")
    b.eval(stub % items)
    b.eval("location.hash = '#/home'", False)
    b.wait_for("location.hash === '#/home'")
    b.pump(0.3)
    b.eval("location.hash = '#/settings?section=plan'", False)
    b.wait_for("document.querySelector('.plan-card')")
    basic = b.eval("""(() => { const c = document.querySelector('.plan-card'); return { rows: c.querySelectorAll('.benefit').length, locks: c.querySelectorAll('.benefit-icon use[href$="#i-lock"]').length,
      chips: [...c.querySelectorAll('.benefit .chip-gold')].map(e => e.textContent), labels: [...c.querySelectorAll('.benefit-label')].map(e => e.textContent), descs: c.querySelectorAll('.benefit-desc').length,
      btn: c.querySelector('[data-try-premium]')?.textContent, head: c.querySelector('h3').textContent.trim(), premiumClass: c.classList.contains('is-premium'),
      demoText: document.querySelector('[data-plan-demo-text]').hidden, radio: document.querySelector('[data-plans] input:checked')?.value,
      order: (() => { const a = c.getBoundingClientRect().top, d = document.querySelector('[data-plans]').getBoundingClientRect().top; return a < d; })() }; })()""", False)
    n = 4 if who == "employer" else 2
    check(f"plan card Basic ({who}, stub): lists each benefit with a lock, label, description and a gold 'Premium' chip", basic["rows"] == n and basic["locks"] == n and basic["chips"] == ["Premium"] * n and basic["descs"] == n, str(basic))
    check(f"plan card Basic ({who}, stub): primary button 'Try Premium (demo)'; the demo switch is below the card and says Basic", basic["btn"] == "Try Premium (demo)" and basic["order"] and basic["radio"] == "basic" and basic["demoText"] is False, str(basic))
    shot(b, shots, f"plan-card-basic-{who}.png")
    b.click("[data-try-premium]")
    b.wait_for("document.querySelector('.plan-card.is-premium')")
    b.pump(0.4)
    prem = b.eval("""(() => { const c = document.querySelector('.plan-card'); const rows = [...c.querySelectorAll('.benefit')].map(r => ({ icon: r.querySelector('.benefit-icon use').getAttribute('href').split('#')[1], chips: [...r.querySelectorAll('.chip')].map(e => e.textContent), count: r.querySelector('.benefit-count')?.textContent || null }));
      return { crown: !!c.querySelector('.plan-card-head .crown'), chip: c.querySelector('h3 .chip-gold')?.textContent, rows, btn: !!c.querySelector('[data-try-premium]'), radio: document.querySelector('[data-plans] input:checked')?.value,
        shellPremium: document.getElementById('shellUser').classList.contains('is-premium'), focus: document.activeElement.tagName + (document.activeElement.hasAttribute('data-plan-title') ? ':title' : ''), alert: document.querySelector('[data-plan-alert]').textContent }; })()""", False)
    first = prem["rows"][0]
    others = prem["rows"][1:]
    check(f"plan card Premium ({who}, stub): crown, gold 'Premium' chip, no Try button, radio follows", prem["crown"] and prem["chip"] == "Premium" and not prem["btn"] and prem["radio"] == "premium", str(prem))
    check(f"plan card Premium ({who}, stub): a used benefit shows 'Used' (green) and '3 times'; the others 'Not used yet'", first["chips"] == ["Used"] and first["count"] == "3 times" and all(r["chips"] == ["Not used yet"] and r["count"] is None for r in others), str(prem["rows"]))
    check(f"plan card Premium ({who}, stub): the button click sets the plan, the menu gets the crown, focus moves to the card title, a success message shows", prem["shellPremium"] and prem["focus"] == "H3:title" and prem["alert"] == "Your plan is now Premium.", str(prem))
    cols = b.eval("""(() => { const c = document.querySelector('.benefit .chip-green'); const n = document.querySelector('.benefit .chip-neutral'); const g = document.querySelector('.plan-card h3 .chip-gold');
      const f = (e) => { const cs = getComputedStyle(e); return [cs.color, cs.backgroundColor]; }; return { green: f(c), neutral: f(n), gold: f(g) }; })()""", False)
    low = {k: round(contrast(*v), 2) for k, v in cols.items() if contrast(*v) < 4.5}
    check("plan card: chip text contrast is at least 4.5:1 (Used, Not used yet, Premium)", not low, str({k: round(contrast(*v), 2) for k, v in cols.items()}))
    shot(b, shots, f"plan-card-premium-{who}.png")
    # radio back to Basic
    pick_plan(b, "basic")
    b.wait_for("document.querySelector('.plan-card:not(.is-premium)')")
    check(f"plan card ({who}, stub): the demo switch back to Basic draws the Basic card again", b.eval("!document.getElementById('shellUser').classList.contains('is-premium')", False))
    b.call("Page.reload")
    b.wait_for("document.querySelector('#shellUser')")


def check_real_api(b, role):
    """The client methods against the real backend: list pages, sort, compare. (Skips what the backend does not have yet and says so.)"""
    if role == "talent":
        r = b.eval("""(async () => {
          const { api } = await import('/js/api/index.js');
          const out = {};
          const a = await api.jobs.search({ pageSize: 10, page: 1, sort: 'best' });
          const c = await api.jobs.search({ pageSize: 10, page: 2, sort: 'best' });
          out.search = { p1: a.page, p2: c.page, n1: a.items.length, n2: c.items.length, different: a.items[0].id !== c.items[0].id, sort: a.sort };
          const nw = await api.jobs.search({ pageSize: 20, page: 1, sort: 'newest' });
          out.newest = { n: nw.items.length, pageSize: nw.page.pageSize, sort: nw.sort };
          const rec = await api.jobs.recommended(3);
          out.rec = { n: rec.items.length, page: rec.page };
          const rec2 = await api.jobs.recommended({ page: 2, pageSize: 10, sort: 'newest' });
          out.rec2 = { page: rec2.page.page, n: rec2.items.length };
          out.lists = { bookmarks: !!(await api.bookmarks.list({ page: 1, pageSize: 10 })).page, applications: !!(await api.applications.list({ page: 1, pageSize: 10, sort: 'updated' })).page };
          const ids = a.items.slice(0, 3).map(j => j.id);
          try { const cmp = await api.jobs.compare(ids); out.cmp = { jobs: cmp.jobs.length, axes: Array.isArray(cmp.axes), pairs: Array.isArray(cmp.pairs), matrix: Array.isArray(cmp.skillMatrix) }; }
          catch (e) { out.cmpError = e.status + ' ' + e.code + ' ' + e.message; }
          try { await api.jobs.compare(ids.slice(0, 1)); out.one = 'no error'; } catch (e) { out.one = { status: e.status, ids: e.fields && e.fields.ids }; }
          return out;
        })()""")
        s = r["search"]
        check("real API (talent): jobs.search page 1 and 2 are different pages with a right page object", s["p1"]["page"] == 1 and s["p2"]["page"] == 2 and s["p1"]["pageSize"] == 10 and s["different"] and s["n1"] == 10 and s["n2"] == 10 and s["p1"]["total"] > 20 and s["sort"] == "best", str(s))
        check("real API (talent): pageSize 20 and sort=newest are passed on", r["newest"]["n"] == 20 and r["newest"]["pageSize"] == 20 and r["newest"]["sort"] == "newest", str(r["newest"]))
        check("real API (talent): the old call recommended(3) gives 3 items; the new call gives page 2", r["rec"]["n"] == 3 and r["rec"]["page"]["pageSize"] == 3 and r["rec2"]["page"] == 2 and r["rec2"]["n"] == 10, f"{r['rec']} {r['rec2']}")
        check("real API (talent): bookmarks and applications lists have a page object", r["lists"] == {"bookmarks": True, "applications": True}, str(r["lists"]))
        if "cmp" in r:
            check("real API (talent): jobs.compare with 3 ids returns jobs, axes, pairs, skillMatrix", r["cmp"] == {"jobs": 3, "axes": True, "pairs": True, "matrix": True}, str(r["cmp"]))
        else:
            info("real API (talent): jobs.compare is not in the backend yet: " + r["cmpError"])
        check("real API (talent): jobs.compare with 1 id is refused at once with fields.ids", r["one"]["status"] == 400 and r["one"]["ids"], str(r["one"]))
    else:
        r = b.eval("""(async () => {
          const { api } = await import('/js/api/index.js');
          const { pagerHtml } = await import('/js/components/pagination.js');
          const out = {};
          await api.entitlements.set('basic');
          const l = await api.recruiter.candidates.list({ page: 1, pageSize: 10, sort: 'best' });
          out.basic = { n: l.items.length, limitedTo: l.limitedTo, page: l.page, pager: pagerHtml({ ...l.page, limitedTo: l.limitedTo }) };
          try { await api.recruiter.compare(l.items.slice(0, 2).map(c => c.id), l.job.id); out.basicCompare = 'no error'; } catch (e) { out.basicCompare = e.status + ' ' + e.code; }
          await api.entitlements.set('premium');
          const p1 = await api.recruiter.candidates.list({ page: 1, pageSize: 20, sort: 'best' });
          const p2 = await api.recruiter.candidates.list({ page: 2, pageSize: 20, sort: 'best' });
          const up = await api.recruiter.candidates.list({ page: 1, pageSize: 10, sort: 'updated' });
          out.premium = { n1: p1.items.length, n2: p2.items.length, p1: p1.page, p2: p2.page.page, different: p1.items[0].id !== p2.items[0].id, limitedTo: p1.limitedTo, updatedSort: up.sort };
          const ids = p1.items.slice(0, 3).map(c => c.id);
          try { const cmp = await api.recruiter.compare(ids, p1.job.id); out.cmp = { candidates: cmp.candidates.length, radar: !!cmp.radar && Array.isArray(cmp.radar.series), areas: Array.isArray(cmp.areas), matrix: Array.isArray(cmp.skillMatrix), noName: cmp.candidates.every(c => !['name', 'email', 'phone', 'country', 'visa', 'age', 'gender', 'cv', 'cvText', 'evidence'].some(k => k in c)) && !JSON.stringify(cmp).includes('@') }; }
          catch (e) { out.cmpError = e.status + ' ' + e.code + ' ' + e.message; }
          try { await api.recruiter.compare(ids.slice(0, 1), p1.job.id); out.one = 'no error'; } catch (e) { out.one = { status: e.status, ids: e.fields && e.fields.ids }; }
          const old = await api.recruiter.candidates.compare(ids[0], ids[1], p1.job.id).then(() => 'ok', (e) => e.code);
          out.oldAlias = old;
          const jobs = await api.recruiter.jobs.list({ page: 1, pageSize: 10 });
          out.jobs = !!jobs.page;
          await api.entitlements.set('basic');
          return out;
        })()""")
        b_ = r["basic"]
        check("real API (employer): a Basic list has 5 items, limitedTo 5, one page, and the pager draws nothing", b_["n"] == 5 and b_["limitedTo"] == 5 and b_["page"]["totalPages"] == 1 and b_["page"]["total"] > 5 and b_["pager"] == "", str(b_))
        check("real API (employer): a Basic employer gets PREMIUM_REQUIRED (403) from compare", r["basicCompare"] == "403 PREMIUM_REQUIRED", str(r["basicCompare"]))
        p = r["premium"]
        check("real API (employer): Premium list pages 1 and 2 (size 20) differ; sort is passed on", p["n1"] == 20 and p["n2"] == 20 and p["p2"] == 2 and p["different"] and not p["limitedTo"] and p["updatedSort"] == "updated" and p["p1"]["total"] > 40, str(p))
        if "cmp" in r:
            check("real API (employer): recruiter.compare with 3 ids returns candidates, radar.series, areas, skillMatrix, with no name or email", r["cmp"] == {"candidates": 3, "radar": True, "areas": True, "matrix": True, "noName": True}, str(r["cmp"]))
        else:
            info("real API (employer): recruiter.compare is not in the backend yet: " + r["cmpError"])
        check("real API (employer): recruiter.compare with 1 id is refused at once with fields.ids", r["one"]["status"] == 400 and r["one"]["ids"], str(r["one"]))
        check("real API (employer): the old candidates.compare(a, b, jobId) now calls the new endpoint", r["oldAlias"] == "ok", str(r["oldAlias"]))
        check("real API (employer): recruiter jobs list has a page object", r["jobs"])


def check_real_used_benefit(b):
    """Real backend: after the compare calls of check_real_api the 'compare' benefit of the employer is used. The card must say 'Used' and the count."""
    b.eval("(async () => { const { api } = await import('/js/api/index.js'); await api.entitlements.set('premium'); })()")
    b.eval("location.hash = '#/home'", False)
    b.pump(0.4)
    b.eval("location.hash = '#/settings?section=plan'", False)
    b.wait_for("document.querySelector('.plan-card.is-premium')")
    rows = b.eval("""(() => Object.fromEntries([...document.querySelectorAll('.benefit')].map(r => [r.dataset.benefit, { chips: [...r.querySelectorAll('.chip')].map(e => e.textContent), count: r.querySelector('.benefit-count')?.textContent || null }])))()""", False)
    info("real backend benefits on the Premium card: " + json.dumps(rows))
    cmp_row = rows.get("compare")
    # check_real_api made 2 compare calls (the new one and the old alias), so the count is 2. Other benefits depend on earlier calls: only the shape is checked.
    shape = all(v["chips"] in (["Used"], ["Not used yet"]) and ((v["chips"] == ["Used"]) == bool(v["count"])) for v in rows.values())
    check("real backend: the 'compare' benefit shows 'Used' and '2 times' after 2 compare calls; 'invite' (never used) shows 'Not used yet'; every row is 'Used' + a count or 'Not used yet'",
          bool(cmp_row) and cmp_row["chips"] == ["Used"] and cmp_row["count"] == "2 times" and rows.get("invite", {}).get("chips") == ["Not used yet"] and shape, str(rows))
    shot(b, SHOTS_DIR[0], "plan-card-premium-real.png")
    pick_plan(b, "basic")
    b.wait_for("document.querySelector('.plan-card:not(.is-premium)')")


def check_real_entitlements(b):
    r = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const e = await api.entitlements.get();
      return { keys: Object.keys(e).sort(), benefits: Array.isArray(e.benefits) ? e.benefits.length : null, crown: e.crown, compareMax: e.compareMax }; })()""")
    info("real backend entitlements keys: " + ", ".join(r["keys"]))
    if r["benefits"] is None:
        info("real backend has no 'benefits' yet: the plan card was tested with the stub only (see check_plan_card_stub)")
    else:
        check("real backend: entitlements.benefits is a list", r["benefits"] >= 1, str(r))
        b.eval("location.hash = '#/home'", False)
        b.pump(0.3)
        b.eval("location.hash = '#/settings?section=plan'", False)
        b.wait_for("document.querySelector('.plan-card')")
        n = b.eval("document.querySelectorAll('.plan-card .benefit').length", False)
        check("real backend: Settings plan card shows every benefit of the API", n == r["benefits"], f"{n} vs {r['benefits']}")
    return r["benefits"] is not None


def check_talent(b, base, pw, shots):
    sign_in(b, base, "candidate@demo.jinder.app", pw)
    labels = nav_labels(b)
    check("talent menu: Home, Jobs, Bookmarks, Applications, Compare, Notifications (no Settings)", labels == ["Home", "Jobs", "Bookmarks", "Applications", "Compare", "Notifications"], str(labels))
    check("talent menu: no lock on Compare (job compare is free)", b.eval("document.querySelector('[data-nav-lock]') === null", False))
    check("talent: the user block shows the alias and the 'Talent' role", "Talent" in b.text("#shellUser") and "Alias:" in b.text("#shellUser"), b.text("#shellUser"))
    b.click("#shellUser")
    b.wait_for("location.hash.startsWith('#/settings') && document.querySelector('h1')")
    check("talent: the user block opens Settings", b.text("h1") == "Settings")
    b.eval("location.hash = '#/home'", False)
    b.wait_for("location.hash === '#/home' && document.getElementById('shellUser')")
    b.click('.sidebar-nav a[href="#/compare"]')
    b.wait_for("location.hash === '#/compare' && document.querySelector('h1')")
    b.wait_for("document.querySelector('h1') && document.querySelector('h1').innerText.startsWith('Compare')")
    check("talent: Compare opens #/compare (h1 'Compare jobs')", b.text("h1") == "Compare jobs", b.text("h1"))
    b.eval("location.hash = '#/jobs/compare?ids=j1,j2'", False)
    b.wait_for("location.hash.startsWith('#/compare')")
    check("talent: the old route #/jobs/compare keeps its ids", "ids=j1" in b.eval("location.hash", False), b.eval("location.hash", False))
    b.pump(0.8)     # the real compare page asks the API for the two made-up ids: a 404 on purpose (the page shows its error panel)
    b.eval("location.hash = '#/home'", False)
    # settings sections
    b.eval("location.hash = '#/settings'", False)
    b.wait_for("document.querySelector('[data-signout]')")
    check("talent: Sign out is also in Settings", b.eval("!!document.querySelector('[data-signout]')", False))
    # alias update goes to the user block
    return b


def check_mobile(b, shots):
    set_viewport(b, 390, 800, mobile=False)
    b.eval("location.hash = '#/home'", False)
    b.wait_for("document.querySelector('.app-topbar')")
    b.pump(0.4)
    top = b.eval("getComputedStyle(document.querySelector('.app-topbar')).display", False)
    b.click(".app-topbar button")
    b.pump(0.4)
    r = b.eval("""(() => { const a = document.getElementById('shellUser'); const rect = a.getBoundingClientRect(); const so = document.querySelector('.nav-signout').getBoundingClientRect();
      return { open: document.querySelector('.app-shell').classList.contains('nav-open'), userVisible: rect.width > 0 && rect.right <= innerWidth && rect.bottom <= innerHeight, nested: a.querySelectorAll('a,button').length,
        signOutVisible: so.height > 0 && so.bottom <= innerHeight, textVisible: getComputedStyle(a.querySelector('.nav-label')).display !== 'none' }; })()""", False)
    check("mobile: the topbar shows, the menu opens, the user link and Sign out are visible", top == "flex" and r["open"] and r["userVisible"] and r["signOutVisible"] and r["textVisible"] and r["nested"] == 0, str(r))
    shot(b, shots, "shell-mobile-menu.png")
    b.click("#shellUser")
    b.wait_for("location.hash.startsWith('#/settings')")
    check("mobile: the user link opens Settings and closes the menu", b.eval("!document.querySelector('.app-shell').classList.contains('nav-open')", False))
    set_viewport(b, 1280, 900)


def check_mobile_tray(b, shots, kind, item):
    set_viewport(b, 390, 800)
    b.eval("location.hash = '#/home'", False)
    b.wait_for("location.hash === '#/home' && document.querySelector('.app-topbar')")
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('job'); compareStore.clear('talent'); compareStore.add(%s, %s); compareStore.add(%s, {id:'zz2', title:'Second long title for the small screen', alias:'Second'}); })()" % (json.dumps(kind), json.dumps(item), json.dumps(kind)))
    b.pump(0.4)
    r = b.eval("(() => { const t = document.querySelector('[data-compare-tray]').getBoundingClientRect(); return { left: t.left, width: t.width, vw: innerWidth, bottom: t.bottom, vh: innerHeight }; })()", False)
    check("mobile: the compare bar spans the screen width at the bottom", r["left"] == 0 and abs(r["width"] - r["vw"]) <= 1 and abs(r["bottom"] - r["vh"]) <= 1, str(r))
    shot(b, shots, "tray-mobile.png")
    b.eval("(async () => { const { compareStore } = await import('/js/core/compare-store.js'); compareStore.clear('job'); compareStore.clear('talent'); })()")
    set_viewport(b, 1280, 900)


def check_api_mock(b, base, shots):
    """Mock mode: the old screens work, lists get a page object, compare says it needs the real backend."""
    sign_in(b, base, "candidate@demo.jinder.app", "demo1234", mock=True)
    labels = nav_labels(b)
    check("mock: the menu has Compare and no Settings", "Compare" in labels and "Settings" not in labels, str(labels))
    r = b.eval("""(async () => {
      const { api } = await import('/js/api/index.js');
      const out = {};
      const all = await api.bookmarks.list();
      out.noParams = { hasPage: !!all.page, items: Array.isArray(all.items), pageOne: all.page && all.page.page, totalPages: all.page && all.page.totalPages, total: all.page && all.page.total, n: all.items.length };
      const s1 = await api.jobs.search({ q: '', location: '', pageSize: 10, page: 1, sort: 'best' });
      const s2 = await api.jobs.search({ q: '', location: '', pageSize: 10, page: 2, sort: 'best' });
      const s3 = await api.jobs.search({ q: '', location: '', pageSize: 20, page: 1, sort: 'newest' });
      out.search = { p1: s1.page, p2: s2.page, n1: s1.items.length, n2: s2.items.length, different: s1.items[0].id !== s2.items[0].id, n3: s3.items.length, pageSize3: s3.page.pageSize,
        newestOrder: s3.items.every((j, i, a) => i === 0 || Date.parse(a[i - 1].postedAt) >= Date.parse(j.postedAt)) };
      const last = await api.jobs.search({ pageSize: 10, page: 999 });
      out.lastPage = last.page.page === last.page.totalPages;
      const rec = await api.jobs.recommended(3);
      out.rec = { n: rec.items.length, pageSize: rec.page.pageSize };
      const rec2 = await api.jobs.recommended({ page: 1, pageSize: 5, sort: 'best' });
      out.rec2 = { n: rec2.items.length, page: rec2.page };
      const apps = await api.applications.list({ page: 1, pageSize: 10, sort: 'updated' });
      out.apps = { hasPage: !!apps.page, n: apps.items.length };
      const errs = {};
      for (const [k, f] of [['jobs', () => api.jobs.compare(['a', 'b'])], ['one', () => api.jobs.compare(['a'])], ['six', () => api.jobs.compare(['a', 'b', 'c', 'd', 'e', 'f'])], ['talent', () => api.recruiter.compare(['a', 'b'], 'job1')]]) {
        try { await f(); errs[k] = 'no error'; } catch (e) { errs[k] = { status: e.status, code: e.code, message: e.message, ids: e.fields && e.fields.ids }; }
      }
      out.errs = errs;
      const ent = await api.entitlements.get();
      out.ent = { crown: ent.crown, compareMax: ent.compareMax, benefits: ent.benefits === undefined };
      return out;
    })()""")
    check("mock: a list without page parameters returns all items and a page object", r["noParams"]["hasPage"] and r["noParams"]["items"] and r["noParams"]["pageOne"] == 1 and r["noParams"]["totalPages"] == 1, str(r["noParams"]))
    s = r["search"]
    total = s["p1"]["total"]
    check("mock: jobs.search page 1 and 2 hold different items; the page object is right", s["n1"] == 10 and s["n2"] == min(10, total - 10) and s["different"] and s["p1"]["page"] == 1 and s["p2"]["page"] == 2 and s["p1"]["pageSize"] == 10 and total > 10 and s["p1"]["totalPages"] == -(-total // 10), str(s))
    check("mock: pageSize 20 and sort=newest work (date order)", s["n3"] == min(20, total) and s["pageSize3"] == 20 and s["newestOrder"], str(s))
    check("mock: a page past the end is moved to the last page", r["lastPage"])
    check("mock: old call recommended(3) still works (3 items, page size 3); new call with page and sort works", r["rec"]["n"] == 3 and r["rec"]["pageSize"] == 3 and r["rec2"]["n"] == 5 and r["rec2"]["page"]["pageSize"] == 5, f"{r['rec']} {r['rec2']}")
    check("mock: applications.list has a page object", r["apps"]["hasPage"])
    e = r["errs"]
    check("mock: jobs.compare and recruiter.compare fail with a clear NEEDS_REAL_BACKEND error", e["jobs"]["code"] == "NEEDS_REAL_BACKEND" and e["talent"]["code"] == "NEEDS_REAL_BACKEND" and "real" in e["jobs"]["message"].lower(), str(e))
    check("compare: fewer than 2 or more than 5 ids is refused with fields.ids (400)", e["one"]["status"] == 400 and e["six"]["status"] == 400 and e["one"]["ids"] and e["six"]["ids"], str(e))
    check("mock: entitlements has crown and compareMax but no benefits", r["ent"] == {"crown": False, "compareMax": 5, "benefits": True}, str(r["ent"]))
    # old screens still work in mock mode
    for route, sel in (("#/jobs", ".job-card"), ("#/bookmarks", ".panel"), ("#/applications", ".dash"), ("#/home", ".dash")):
        b.eval(f"location.hash = {json.dumps(route)}", False)
        b.wait_for(f"location.hash === {json.dumps(route)} && document.querySelector({json.dumps(sel)})")
        b.pump(0.5)
    no_problems(b, "mock: the old screens (Jobs, Bookmarks, Applications, Home) render without a console error", ignore=("australian_jobs_dataset.csv",))
    # settings: the old plan section only
    b.eval("location.hash = '#/settings?section=plan'", False)
    b.wait_for("document.querySelector('[data-plans]')")
    b.pump(0.6)
    sec = b.eval("({ card: !!document.querySelector('.plan-card'), radios: document.querySelectorAll('[data-plans] input').length, checked: document.querySelector('[data-plans] input:checked')?.value, intro: document.querySelector('[data-plan-intro]').textContent })", False)
    check("mock: Settings shows the old plan section only (no card), with the demo switch", not sec["card"] and sec["radios"] == 2 and sec["checked"] == "basic" and "Demo only" in sec["intro"], str(sec))
    pick_plan(b, "premium")
    b.wait_for("document.getElementById('shellUser').classList.contains('is-premium')")
    check("mock: the crown shows after the demo switch to Premium", True)
    shot(b, shots, "mock-settings-premium.png")
    pick_plan(b, "basic")
    b.wait_for("!document.getElementById('shellUser').classList.contains('is-premium')")
    # mock recruiter: compare is locked, basic
    sign_in(b, base, "recruiter@demo.jinder.app", "demo1234", mock=True)
    check("mock employer: Compare has the lock for Basic", b.eval("(() => { const l = document.querySelector('[data-nav-lock]'); return !!l && getComputedStyle(l).display !== 'none'; })()", False))
    # paging of the employer talent list (limitedTo)
    r2 = b.eval("""(async () => { const { api } = await import('/js/api/index.js'); const c = await api.recruiter.candidates.list({ page: 1, pageSize: 10, sort: 'best' });
      return { limitedTo: c.limitedTo, n: c.items.length, page: c.page }; })()""")
    check("mock: a Basic employer list keeps limitedTo and has one page", r2["limitedTo"] == 5 and r2["n"] <= 5 and r2["page"]["totalPages"] == 1, str(r2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--talent-pw", default="")
    ap.add_argument("--employer-pw", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--debug-port", type=int, default=9320)
    ap.add_argument("--port", type=int, default=8120)
    args = ap.parse_args()
    shots = args.shots
    SHOTS_DIR[0] = shots
    if shots:
        os.makedirs(shots, exist_ok=True)

    platform = None
    if args.base:
        base, talent_pw, employer_pw = args.base.rstrip("/"), args.talent_pw, args.employer_pw
    else:
        platform = Platform(args.port)
        base = platform.base
        talent_pw, employer_pw = platform.pw.get("candidate@demo.jinder.app", ""), platform.pw.get("recruiter@demo.jinder.app", "")
        info(f"started the platform on {base} (data folder {platform.var})")
    b = None
    try:
        check_static(base)
        b = Browser(port=args.debug_port)
        # ---- employer
        check_shell_employer(b, base, employer_pw, shots)
        b.eval(TESTBED)
        check_pagination(b, shots)
        check_sort(b)
        check_jd(b, shots)
        check_premium(b)
        check_icons(b, shots)
        check_radar(b, shots)
        check_compare_store(b)
        b.eval("location.hash = '#/home'", False)
        b.wait_for("location.hash === '#/home' && document.getElementById('shellUser')")
        b.pump(0.5)
        check_tray(b, shots, "talent", {"id": "t-1", "alias": "Teal Heron"}, {"id": "t-2", "alias": "Amber Finch"})
        check_mobile_tray(b, shots, "talent", {"id": "t-1", "alias": "Teal Heron"})
        check_collapsed(b, shots)
        check_plan_and_crown(b, shots, "employer")
        real_benefits = check_real_entitlements(b)
        check_real_api(b, "employer")
        check_real_used_benefit(b)
        check_plan_card_stub(b, shots, "employer")
        no_problems(b, "employer screens: no console error, no CSP error", ignore=("/api/recruiter/compare",))  # the 403 of a Basic employer is on purpose (see check_real_api)
        # ---- talent
        check_talent(b, base, talent_pw, shots)
        b.eval("location.hash = '#/home'", False)
        b.wait_for("location.hash === '#/home' && document.getElementById('shellUser')")
        b.pump(0.5)
        check_tray(b, shots, "job", {"id": "job-1", "title": "Backend Engineer"}, {"id": "job-2", "title": "Data Engineer"})
        check_real_api(b, "talent")
        check_plan_and_crown(b, shots, "talent")
        check_plan_card_stub(b, shots, "talent")
        check_mobile(b, shots)
        no_problems(b, "talent screens: no console error, no CSP error", ignore=("/api/jobs/compare?ids=j1",))   # the 404 for the made-up ids is on purpose
        # ---- mock
        check_api_mock(b, base, shots)
        no_problems(b, "mock screens: no console error, no CSP error", ignore=("australian_jobs_dataset.csv",))
    finally:
        if b:
            b.close()
        if platform:
            platform.stop()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    for name, _, detail in failed:
        print("  FAIL:", name, detail)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
