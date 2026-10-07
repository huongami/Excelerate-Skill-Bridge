"""Regression tests for problems that a code review found. Each test says what went wrong before."""
import json
import socket
import unittest
import zlib
from datetime import datetime, timedelta, timezone

import helpers as H
from jinder import aliases, cv_parser, engine_bridge as eb, jd_parser, security, skills, store, textextract as T, translation
from jinder.util import scrub_contact
from test_talent_flow import onboard


def iso_in(days=0):
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class PureFunctionFixes(unittest.TestCase):
    def test_an_empty_decompression_budget_stops(self):
        # zlib treats "0" as "no limit". The budget must not.
        bomb = zlib.compress(b"0" * 5_000_000)
        self.assertEqual(T._inflate(bomb, 0), b"")
        self.assertEqual(len(T._inflate(bomb, 1000)), 1000)

    def test_a_pdf_with_many_bombs_stays_small(self):
        stream = zlib.compress(b"0" * 30_000_000)
        objs = b"".join(f"{n} 0 obj\n<< /Filter /FlateDecode /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n" for n in range(10, 22))
        pdf = T._Pdf(b"%PDF-1.4\n" + objs)
        total = sum(len(s or b"") for _, s in pdf.objs.values())
        self.assertLessEqual(total, T._MAX_DECOMPRESSED)

    def test_pdf_pages_follow_the_page_tree(self):
        def page(text):
            return f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Contents {{c}} 0 R /Resources << /Font << /F1 9 0 R >> >> >>"
        content = lambda t: f"BT /F1 12 Tf 50 700 Td ({t}) Tj ET"
        # the page that comes second in the tree has the lower object number
        objs = {1: "<< /Type /Catalog /Pages 2 0 R >>", 2: "<< /Type /Pages /Kids [4 0 R 3 0 R] /Count 2 >>",
                3: page("").format(c=5), 4: page("").format(c=6),
                5: f"<< /Length {len(content('SECOND PAGE words here'))} >>\nstream\n{content('SECOND PAGE words here')}\nendstream",
                6: f"<< /Length {len(content('FIRST PAGE words here'))} >>\nstream\n{content('FIRST PAGE words here')}\nendstream",
                9: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"}
        data = b"%PDF-1.4\n" + b"".join(f"{n} 0 obj\n{o}\nendobj\n".encode() for n, o in sorted(objs.items())) + b"trailer\n<< /Root 1 0 R >>\n%%EOF"
        text = T.extract_text(data)
        self.assertLess(text.index("FIRST PAGE"), text.index("SECOND PAGE"))

    def test_aliases_compare_names_without_accents(self):
        self.assertTrue(aliases.alias_problem("Nguyen Fox", "Nguyễn Văn An"))      # "Nguyễn" is "Nguyen"
        self.assertTrue(aliases.alias_problem("Li Wu", "Li Wu"))                   # the whole name, though each part is short
        self.assertEqual(aliases.alias_problem("Li Fox", "Li Wu"), "")             # one short part alone is fine
        self.assertEqual(aliases.alias_problem("Misty Meadow", "Nguyễn Văn An"), "")
        self.assertTrue(aliases.alias_problem("Duc Heron", "Đức Nguyễn"))           # "Đức" is "Duc"

    def test_translation_ids_do_not_collide(self):
        out = translation.translate({"skills": ["C++", "C#", "会计", "管理", "Node.js", "Kotlin"]})["skills"]
        self.assertEqual(len(out), 6)
        self.assertEqual(len({s["id"] for s in out}), 6)
        again = translation.translate({"skills": ["C++", "C#", "会计", "管理", "Node.js", "Kotlin"]})["skills"]
        self.assertEqual([s["id"] for s in out], [s["id"] for s in again])      # stable

    def test_related_skills_come_from_the_taxonomy(self):
        # a skill that the taxonomy lists as related gives a partial match, in both directions. A skill that is not related is a gap.
        for a in skills._T.skills[:12]:
            for b in a["related"][:2]:
                self.assertEqual(skills.skill_match([a["name"]], {b.lower(): b})["items"][0]["status"], "partial", (a["name"], b))
                self.assertEqual(skills.skill_match([b], {a["name"].lower(): a["name"]})["items"][0]["status"], "partial", (b, a["name"]))
        self.assertEqual(skills.skill_match(["SQL"], {"karate": "Karate"})["items"][0]["status"], "gap")

    def test_the_status_words_of_a_skill_result(self):
        # meets -> match, below -> partial, related -> partial, missing -> gap. fitStatus keeps the word of the formulas.
        r = skills.skill_match([{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 3, "must": False}, {"name": "Terraform", "level": 3, "must": True},
                                {"name": "Snowflake", "level": 3, "must": True}], {"sql": "SQL", "python": "Python", "postgresql": "PostgreSQL"}, {"sql": 2, "python": 4})
        got = {i["name"]: (i["status"], i["fitStatus"], i["required"], i["level"], i["must"]) for i in r["items"]}
        self.assertEqual(got["SQL"], ("partial", "below", 4, 2, True))
        self.assertEqual(got["Python"], ("match", "meets", 3, 4, False))
        self.assertEqual(got["Terraform"], ("gap", "missing", 3, None, True))
        self.assertEqual(got["Snowflake"][0], "gap")
        self.assertTrue(all(set(i) >= {"name", "status", "fitStatus", "required", "level", "must", "reason"} for i in r["items"]))

    def test_short_skill_names_are_found_only_as_whole_words(self):
        self.assertEqual(skills.skills_in("Customer service and plan C, R&D"), [])
        self.assertEqual(skills.skills_in("Skills: Python, R, SQL, C, Go"), ["Python", "R", "SQL", "C", "Go"])
        self.assertEqual(skills.skills_in("We use React and Node.js with C# and C++ and .NET"), ["React", "Node.js", "C#", "C++", ".NET"])
        self.assertEqual(skills.skills_in("Kubernetes.NETwork"), ["Kubernetes"])
        self.assertEqual(skills.skills_in("Go to market strategy"), [])
        self.assertEqual(skills.skills_in("golang"), ["Go"])
        self.assertEqual(skills.skills_in("R"), ["R"])

    def test_contact_details_are_removed_but_dates_and_pay_stay(self):
        self.assertEqual(scrub_contact("Start 2026-11-03, worked 2018 - 2022, ended 03.11.2026"), "Start 2026-11-03, worked 2018 - 2022, ended 03.11.2026")
        self.assertEqual(scrub_contact("Pay $120000-130000 a year"), "Pay $120000-130000 a year")
        self.assertEqual(scrub_contact("Call 0412 345 678 or +61 2 9876 5432"), "Call [phone removed] or [phone removed]")
        self.assertEqual(scrub_contact("(02) 9876 5432"), "[phone removed]")
        self.assertEqual(scrub_contact("write to a@b.co"), "write to [email removed]")

    def test_word_boundaries_in_patterns(self):
        # a stray backspace character had replaced "\b" in two patterns
        self.assertIn("Python", skills.job_skills("Python Developer", ""))
        self.assertIn("SQL", skills.job_skills("Data Analyst", "Write SQL queries every day."))
        for path in ("cv_parser.py", "skills.py"):
            with open(f"{H.ROOT}/jinder/{path}", "rb") as f:
                self.assertNotIn(b"\x08", f.read(), path)

    def test_a_salary_with_k_on_the_second_number(self):
        self.assertEqual(jd_parser.read_salary("Salary $80-100k per year"), "$80,000 – $100,000 per year")
        self.assertEqual(jd_parser.read_salary("$70 - $90 per hour"), "$70 – $90 per hour")

    def test_an_employer_input_has_the_shared_profile_only(self):
        profile = {"currentRole": ["Secret Role Title"], "qualification": ["PhD in Secrets"], "industry": ["Data"], "targetRole": ["Data Analyst"],
                   "years": "3–5 years", "locations": ["Sydney"], "evidence": ["PRIVATE EVIDENCE LINE"], "skills": [], "studyCountry": ["Kenya"]}
        shared = [{"source": "skill", "mapped": "SQL", "kind": "direct", "anzsco": "", "occupation": "", "status": "accepted", "level": 4}]
        emp = eb.candidate_dict({**profile, "translation": shared}, shared, "Teal Heron", "u1", None, private=False)
        text = json.dumps(emp)
        for secret in ("Secret Role Title", "PhD in Secrets", "PRIVATE EVIDENCE LINE", "Kenya"):
            self.assertNotIn(secret, text)
        self.assertNotIn("cv_raw_text", emp)
        # the talent's own screens: the text of the CV is only the fallback when there is no skill at all
        own = json.dumps(eb.candidate_dict(profile, [], "Teal Heron", "u1", None, private=True))
        self.assertIn("PRIVATE EVIDENCE LINE", own)
        with_skill = json.dumps(eb.candidate_dict({**profile, "skills": ["SQL"]}, [], "Teal Heron", "u1", None, private=True))
        self.assertNotIn("PRIVATE EVIDENCE LINE", with_skill)

    def test_the_plan_switch_default(self):
        import importlib
        import os
        from jinder import config
        saved = {k: os.environ.get(k) for k in ("JINDER_HOST", "JINDER_ALLOW_PLAN_SWITCH")}
        try:
            for host, flag, expected in (("127.0.0.1", None, True), ("0.0.0.0", None, False), ("0.0.0.0", "1", True), ("127.0.0.1", "0", False)):
                os.environ["JINDER_HOST"] = host
                os.environ.pop("JINDER_ALLOW_PLAN_SWITCH", None)
                if flag is not None:
                    os.environ["JINDER_ALLOW_PLAN_SWITCH"] = flag
                importlib.reload(config)
                self.assertEqual(config.ALLOW_PLAN_SWITCH, expected, (host, flag))
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v
            importlib.reload(config)


class ServerFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def setUp(self):
        security.login_limiter.clear()
        security.address_limiter.clear()
        security.email_limiter.clear()

    def raw(self, payload: bytes, wait=2.0) -> bytes:
        host, port = self.api.base.replace("http://", "").split(":")
        s = socket.create_connection((host, int(port)), timeout=wait)
        s.sendall(payload)
        data = b""
        try:
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        return data

    def test_a_bad_content_length_is_a_400(self):
        for value in (b"-1", b"abc", b"1.5"):
            data = self.raw(b"POST /api/auth/login HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: " + value + b"\r\n\r\n")
            self.assertIn(b" 400 ", data.split(b"\r\n")[0], value)

    def test_a_body_that_the_server_does_not_read_is_not_a_second_request(self):
        smuggled = b"GET /api/health HTTP/1.1\r\nHost: x\r\n\r\n"
        data = self.raw(b"POST /index.html HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(smuggled)).encode() + b"\r\n\r\n" + smuggled)
        self.assertEqual(data.count(b"HTTP/1.1 "), 1)
        self.assertIn(b" 405 ", data.split(b"\r\n")[0])
        # a GET with a body: the body is read and dropped, the next request on the connection still works
        body = b"x" * 10
        data = self.raw(b"GET /api/health HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\n\r\n" + body + b"GET /api/health HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
        self.assertEqual(data.count(b"HTTP/1.1 200"), 2)

    def test_an_upload_without_a_token_is_refused_at_once(self):
        s, r = self.api.upload("/cv", "cv.docx", H.make_docx(["x" * 50]), token=None)
        self.assertEqual((s, r["error"]["code"]), (401, "UNAUTHORIZED"))

    def test_the_owner_is_not_locked_out_by_a_few_wrong_tries(self):
        t = self.p.sign_up_and_in()
        # five wrong tries for one email from one address lock that pair. Another email from the same address still works.
        for _ in range(5):
            self.api.call("POST", "/auth/login", {"email": t["email"], "password": "wrong wrong"})
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})[0], 429)
        other = self.p.sign_up_and_in()
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": other["email"], "password": other["password"]})[0], 200)
        # a stranger's tries from a few other addresses do not lock the owner: the per-email limit is higher than 5
        security.login_limiter.clear()
        for i in range(8):
            security.email_limiter.fail(f"email:{t['email']}")
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})[0], 200)

    def test_password_checks_are_throttled(self):
        t = self.p.sign_up_and_in()
        for _ in range(5):
            self.assertEqual(self.api.call("POST", "/me/delete", {"password": "wrong wrong"}, token=t["token"])[0], 400)
        s, r = self.api.call("POST", "/me/delete", {"password": t["password"]}, token=t["token"])
        self.assertEqual((s, r["error"]["code"]), (429, "RATE_LIMITED"))

    def test_signup_does_not_hold_the_write_lock_while_it_hashes(self):
        import threading
        import time
        results = []

        def signup(i):
            t0 = time.time()
            s, _ = self.api.call("POST", "/auth/signup", {"role": "candidate", "name": f"Parallel {i}", "email": f"parallel{i}.{time.time_ns()}@example.test", "password": "longenough1"})
            results.append((s, time.time() - t0))

        threads = [threading.Thread(target=signup, args=(i,)) for i in range(6)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=60)
        self.assertEqual({s for s, _ in results}, {201})

    def test_removing_a_cv_removes_the_text_that_was_read_from_it(self):
        t = self.p.sign_up_and_in()
        onboard(self.p, t)
        c = self.p.conn()
        self.assertEqual(c.execute("SELECT COUNT(*) FROM parses WHERE user_id = ?", (t["user"]["id"],)).fetchone()[0], 1)
        self.api.call("PATCH", "/me", {"cv": None}, token=t["token"])
        self.assertEqual(c.execute("SELECT COUNT(*) FROM parses WHERE user_id = ?", (t["user"]["id"],)).fetchone()[0], 0)

    def test_a_job_description_file_is_deleted_also_when_it_fails(self):
        import time
        from jinder import config
        e = self.p.sign_up_and_in(role="recruiter")
        before = set(config.UPLOAD_DIR.iterdir())
        s, up = self.api.upload("/recruiter/jobs/import", "bad.pdf", b"%PDF-1.4\nnothing here", e["token"])
        for _ in range(100):
            s, res = self.api.call("GET", f"/recruiter/jobs/import/{up['parse']['id']}", token=e["token"])
            if res["status"] != "parsing":
                break
            time.sleep(0.05)
        time.sleep(0.2)
        self.assertEqual(res["status"], "failed")
        self.assertEqual(set(config.UPLOAD_DIR.iterdir()) - before, set())

    def test_edit_a_job_keeps_the_rules_of_create(self):
        e = self.p.sign_up_and_in(role="recruiter")
        base = {"category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["SQL"], "targetApplicants": 2, "closesAt": iso_in(9),
                "description": "Analyse data and report on it every single week."}
        s, job = self.api.call("POST", "/recruiter/jobs", {**base, "title": "Data Analyst"}, token=e["token"])
        t = self.p.sign_up_and_in()
        s, d1 = self.api.call("GET", f"/jobs/{job['id']}", token=t["token"])
        self.api.call("PATCH", f"/recruiter/jobs/{job['id']}", {"title": "Data Engineer", "salary": "  "}, token=e["token"])
        s, d2 = self.api.call("GET", f"/jobs/{job['id']}", token=t["token"])
        self.assertEqual(d2["salary"], "Market competitive")
        self.assertNotEqual(d1["anzsco"], d2["anzsco"])
        self.assertEqual((d1["anzsco"], d2["anzsco"]), ("224114", "262111"))      # the taxonomy occupation of the role in the title

    def test_one_cannot_invite_for_a_closed_job(self):
        e = self.p.sign_up_and_in(role="recruiter")
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        base = {"title": "Data Analyst", "category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["SQL"], "targetApplicants": 2,
                "closesAt": iso_in(9), "description": "Analyse data and report on it every single week."}
        s, job = self.api.call("POST", "/recruiter/jobs", base, token=e["token"])
        c = self.p.conn()
        c.execute("UPDATE jobs SET closes_at = '2020-01-01T00:00:00.000Z' WHERE id = ?", (job["id"],))
        c.close()
        s, r = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        cid = r["items"][0]["id"]
        s, r = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": job["id"], "message": "Please apply, we like you."}, token=e["token"])
        self.assertEqual((s, r["error"]["code"]), (409, "CONFLICT"))

    def test_talent_free_text_has_no_contact_details_for_employers(self):
        t = self.p.sign_up_and_in()
        s, me = self.api.call("PATCH", "/me", {"profile": {"skills": ["Call me 0412 345 678", "jane@x.com"], "industry": ["Technology"],
                                                           "fieldOfStudy": ["Mail jane@x.com"], "targetRole": ["Data analyst"]}}, token=t["token"])
        p = me["profile"]
        text = json.dumps(p)
        self.assertNotIn("0412", text)
        self.assertNotIn("jane@x.com", text)


if __name__ == "__main__":
    unittest.main()
