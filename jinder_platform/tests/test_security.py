"""Security headers, the static file allow-list, input limits and CORS (AI_Rule Rule 7)."""
import json
import unittest
import urllib.request

import helpers as H


class StaticAndHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_frontend_files_have_security_headers(self):
        s, h, body = self.api.raw_headers("/")
        self.assertEqual(s, 200)
        self.assertIn(b"<title>Jinder", body)
        csp = h["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn("unsafe-inline", csp.split("style-src")[0])
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertEqual(h["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertIn("camera=()", h["Permissions-Policy"])

    def test_file_types_and_content_types(self):
        for path, ctype in (("/js/main.js", "application/javascript"), ("/styles.css", "text/css"), ("/icons.svg", "image/svg+xml"), ("/logo.svg", "image/svg+xml")):
            s, h, _ = self.api.raw_headers(path)
            self.assertEqual(s, 200, path)
            self.assertTrue(h["Content-Type"].startswith(ctype), path)
        s, h, _ = self.api.raw_headers("/icons.svg")
        self.assertEqual(h["Content-Security-Policy"], "default-src 'none'; style-src 'unsafe-inline'")

    def test_other_files_return_404(self):
        for path in ("/serve.ps1", "/nope.js", "/js/", "/js", "/../start.py", "/%2e%2e/start.py", "/js/../../start.py", "/..%2f..%2fstart.py",
                     "/js/%2e%2e/%2e%2e/jinder_platform/start.py", "/data/australian_jobs_dataset.csv", "/%00", "/var/jinder.db"):
            s, _, body = self.api.raw_headers(path)
            self.assertEqual(s, 404, path)

    def test_static_files_are_read_only(self):
        for method in ("POST", "PUT", "DELETE"):
            req = urllib.request.Request(self.api.base + "/", method=method, data=b"x")
            try:
                urllib.request.urlopen(req)
                self.fail("expected an error")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 405)

    def test_the_upload_folder_is_never_served(self):
        t = self.p.sign_up_and_in()
        self.api.upload("/cv", "cv.docx", H.make_docx(H.CV_LINES), t["token"])
        from jinder import config
        name = next(config.UPLOAD_DIR.iterdir()).name
        for path in (f"/uploads/{name}", f"/{name}", f"/api/uploads/{name}"):
            self.assertIn(self.api.raw_headers(path)[0], (404,))


class ApiInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_unknown_endpoint_is_json_404(self):
        s, r = self.api.call("GET", "/nope")
        self.assertEqual((s, r["error"]["code"]), (404, "NOT_FOUND"))

    def test_bad_json(self):
        s, r = self.api.call("POST", "/auth/login", raw=b"{not json", headers={"Content-Type": "application/json"})
        self.assertEqual((s, r["error"]["code"]), (400, "VALIDATION_ERROR"))
        s, r = self.api.call("POST", "/auth/login", raw=b"[1,2,3]", headers={"Content-Type": "application/json"})
        self.assertEqual(s, 400)

    def test_wrong_types_do_not_crash(self):
        s, r = self.api.call("POST", "/auth/signup", {"role": ["candidate"], "name": 5, "email": {"a": 1}, "password": 12345678})
        self.assertEqual(s, 400)
        s, r = self.api.call("POST", "/auth/login", {"email": 5, "password": ["x"]})
        self.assertEqual(s, 401)
        t = self.p.sign_up_and_in()
        for body in ({"profile": "text"}, {"profile": [1]}, {"profile": {"translation": "x", "skills": 5}}, {"name": ["a"]}, {"onboarding": ["done"]}):
            s, r = self.api.call("PATCH", "/me", body, token=t["token"])
            self.assertIn(s, (200, 400), body)
        s, r = self.api.call("POST", "/profile/translate", {"profile": "x"}, token=t["token"])
        self.assertEqual(s, 400)
        s, r = self.api.call("POST", "/profile/translate", {"profile": {"skills": [1, None, "SQL"], "currentRole": 7}, "evidence": "line"}, token=t["token"])
        self.assertEqual(s, 200)

    def test_oversize_json_is_refused(self):
        s, r = self.api.call("POST", "/auth/login", raw=b'{"email": "' + b"a" * (2 * 1024 * 1024) + b'"}', headers={"Content-Type": "application/json"})
        self.assertEqual((s, r["error"]["code"]), (413, "TOO_LARGE"))

    def test_error_bodies_do_not_leak_internals(self):
        t = self.p.sign_up_and_in()
        for path in ("/jobs/%27%20OR%201%3D1%20--", "/jobs/..%2f..%2fetc", "/applications/%27%3B%20DROP%20TABLE%20users%3B--"):
            s, r = self.api.call("GET", path, token=t["token"])
            self.assertIn(s, (404,), path)
            text = json.dumps(r)
            for leak in ("Traceback", "sqlite", ".py", "File \""):
                self.assertNotIn(leak, text)

    def test_sql_injection_is_not_possible(self):
        t = self.p.sign_up_and_in()
        s, r = self.api.call("GET", "/jobs?q=%27%20OR%201%3D1%20--", token=t["token"])
        self.assertEqual((s, r["total"]), (200, 0))
        s, r = self.api.call("POST", "/auth/login", {"email": "' OR '1'='1", "password": "' OR '1'='1"})
        self.assertEqual(s, 401)
        s, r = self.api.call("POST", "/reports", {"targetType": "job", "targetId": "x'); DROP TABLE users;--", "reason": "other"}, token=t["token"])
        self.assertEqual(s, 200)
        n = self.p.conn().execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertGreater(n, 50)        # the 50 sample profiles and the other users: the table is still there

    def test_no_cors_by_default(self):
        req = urllib.request.Request(self.api.base + "/api/health", headers={"Origin": "http://evil.example"})
        with urllib.request.urlopen(req) as r:
            self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        req = urllib.request.Request(self.api.base + "/api/me", method="OPTIONS", headers={"Origin": "http://evil.example"})
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 204)
            self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_cors_only_for_allowed_origins(self):
        from jinder import config
        config.CORS_ORIGINS.append("http://localhost:5173")
        try:
            req = urllib.request.Request(self.api.base + "/api/health", headers={"Origin": "http://localhost:5173"})
            with urllib.request.urlopen(req) as r:
                self.assertEqual(r.headers["Access-Control-Allow-Origin"], "http://localhost:5173")
            req = urllib.request.Request(self.api.base + "/api/health", headers={"Origin": "http://evil.example"})
            with urllib.request.urlopen(req) as r:
                self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        finally:
            config.CORS_ORIGINS.remove("http://localhost:5173")

    def test_api_responses_are_not_cached(self):
        s, h, _ = self.api.raw_headers("/api/health")
        self.assertEqual(h["Cache-Control"], "no-store")

    def test_the_server_does_not_log_personal_data(self):
        import logging
        records = []

        class Grab(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        h = Grab()
        logging.getLogger().addHandler(h)
        logging.getLogger().setLevel(logging.INFO)
        try:
            t = self.p.sign_up_and_in(name="Logcheck Person", email="logcheck.person@example.test")
            self.api.call("GET", "/aliases/check?alias=Logcheck%20Person&name=Logcheck%20Person")
            self.api.call("POST", "/auth/login", {"email": "logcheck.person@example.test", "password": "wrong password"})
        finally:
            logging.getLogger().removeHandler(h)
        text = "\n".join(records)
        for secret in ("Logcheck", "logcheck.person", "correct horse", t["token"]):
            self.assertNotIn(secret, text)
        self.assertTrue(any("/aliases/check" in r for r in records))  # the path is logged, the query is not


if __name__ == "__main__":
    unittest.main()
