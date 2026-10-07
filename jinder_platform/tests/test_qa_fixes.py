"""Tests for the defects that QA found and fixed in wave 5 (docs/changes/QA.md, section "Fixed by QA")."""
import socket
import struct
import threading
import time
import unittest
from unittest import mock

import helpers as H
from jinder import http_server
from jinder.http_server import make_server


class ClosedConnectionTests(unittest.TestCase):
    """A browser that closes a connection is not an error of the server (no traceback in the log)."""

    def test_a_reset_connection_is_dropped_without_a_log_line(self):
        server = make_server("127.0.0.1", 0)
        try:
            for exc in (ConnectionResetError(10054, "reset"), BrokenPipeError(32, "pipe"), ConnectionAbortedError(10053, "aborted"), TimeoutError("timeout")):
                with mock.patch.object(http_server.log, "error") as error:
                    try:
                        raise exc
                    except Exception:
                        server.handle_error(None, ("127.0.0.1", 1))
                    error.assert_not_called()
        finally:
            server.server_close()

    def test_another_error_is_still_logged(self):
        server = make_server("127.0.0.1", 0)
        try:
            with mock.patch.object(http_server.log, "error") as error:
                try:
                    raise ValueError("a real bug")
                except ValueError:
                    server.handle_error(None, ("127.0.0.1", 1))
                self.assertEqual(error.call_count, 1)
                self.assertNotIn("a real bug", str(error.call_args))      # the message can hold data of the request: only the type is logged
        finally:
            server.server_close()

    def test_a_client_that_resets_in_the_middle_of_a_request_does_not_stop_the_server(self):
        p = H.Platform.get()
        host, port = p.server.server_address
        for _ in range(5):
            s = socket.create_connection((host, port), timeout=5)
            s.sendall(b"GET /api/health HTTP/1.1\r\nHost: x\r\n")        # an unfinished request
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))      # close with a reset
            s.close()
        time.sleep(0.3)
        status, body = p.api.call("GET", "/health")
        self.assertEqual(status, 200)


class RoleCardTests(unittest.TestCase):
    """A title that is not an ICT title gives NO role card (plan F11). The last role pair of the library used to map every title that ends with "Engineer" to Software Engineer."""

    def roles(self, title):
        from jinder import translation
        result = translation.translate({"currentRole": [title], "skills": [], "qualification": [], "years": ""}, [])
        return [c["mapped"] for c in result["skills"] if c["source"] == "role"]

    def test_a_title_that_is_not_an_ict_title_gives_no_role_card(self):
        for title in ("Civil Engineer", "Mechanical Engineer", "Registered Nurse", "Chef", "Marketing Manager", "Teacher", "Electrical Engineer", "Chemical Engineer",
                      "Structural Engineer", "Sales Engineer", "Process Engineer", "Industrial Engineer", "Mining Engineer", "Biomedical Engineer", "Engineering Manager",
                      "Accountant", "Warehouse Supervisor", "Software Sales Manager"):
            self.assertEqual(self.roles(title), [], title)

    def test_an_ict_title_gives_a_role_card(self):
        for title in ("Software Developer", "Backend Engineer", "Data Engineer", "ML Engineer", "DevOps Engineer", "PHP Developer", "Unity Developer", "Node.js Developer",
                      "Embedded Software Engineer", "Firmware Engineer", "Staff Engineer", "Principal Engineer", "Developer", "Engineer", "Application Developer", "SAP Developer",
                      "Senior Software Engineer II", "Full Stack Developer", "Programmer", "Site Reliability Engineer"):
            self.assertEqual(len(self.roles(title)), 1, title)

    def test_the_engineer_title_of_another_field_keeps_the_skills_of_the_profile(self):
        p = H.Platform.get()
        t = p.sign_up_and_in()
        s, r = p.api.call("POST", "/profile/translate", {"profile": {"currentRole": ["Civil Engineer"], "skills": ["SQL", "Python"], "qualification": ["Bachelor's degree"],
                                                                      "years": "3–5 years"}, "evidence": []}, token=t["token"])
        self.assertEqual(s, 200, r)
        sources = [c["source"] for c in r["skills"]]
        self.assertNotIn("role", sources)
        self.assertEqual(sources.count("skill"), 2)


class JobFormMessageTests(unittest.TestCase):
    def test_the_message_for_a_missing_domain_says_domain(self):
        p = H.Platform.get()
        e = p.sign_up_and_in(role="recruiter")
        s, r = p.api.call("POST", "/recruiter/jobs", {"title": "Data Engineer", "category": "Technology & Data"}, token=e["token"])
        self.assertEqual(s, 400)
        self.assertEqual(r["error"]["fields"]["category"], "Choose a domain.")


if __name__ == "__main__":
    unittest.main()
