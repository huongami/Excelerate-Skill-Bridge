"""Accounts, aliases, sessions and role guards (Feature 1)."""
import unittest
from datetime import datetime, timedelta, timezone

import helpers as H
from jinder import security


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def setUp(self):
        security.login_limiter.clear()
        security.address_limiter.clear()
        security.email_limiter.clear()

    # ----- sign up -----
    def test_signup_validation_messages(self):
        s, r = self.api.call("POST", "/auth/signup", {})
        self.assertEqual(s, 400)
        self.assertEqual(r["error"]["code"], "VALIDATION_ERROR")
        f = r["error"]["fields"]
        self.assertEqual(f["role"], "Choose an account type.")
        self.assertEqual(f["name"], "Enter your name.")
        self.assertEqual(f["email"], "Enter a valid email address.")
        self.assertEqual(f["password"], "Use at least 8 characters.")
        s, r = self.api.call("POST", "/auth/signup", {"role": "recruiter", "name": "A", "email": "a@b.co", "password": "longenough1"})
        self.assertEqual(r["error"]["fields"], {"company": "Enter your company."})

    def test_signup_same_answer_for_existing_email(self):
        email = "dup.person@example.test"
        body = {"role": "candidate", "name": "Dup Person", "email": email, "password": "longenough1"}
        self.assertEqual(self.api.call("POST", "/auth/signup", body), (201, {"ok": True}))
        self.assertEqual(self.api.call("POST", "/auth/signup", body), (201, {"ok": True}))
        n = self.p.conn().execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,)).fetchone()[0]
        self.assertEqual(n, 1)

    def test_emails_are_lower_case_and_trimmed(self):
        self.api.call("POST", "/auth/signup", {"role": "candidate", "name": "Case Test", "email": "  Case.Test@Example.TEST ", "password": "longenough1"})
        s, r = self.api.call("POST", "/auth/login", {"email": "case.test@example.test", "password": "longenough1"})
        self.assertEqual(s, 200)

    def test_candidate_always_gets_an_alias(self):
        t = self.p.sign_up_and_in()
        alias = t["user"]["alias"]
        colour, animal = alias.split(" ")
        self.assertTrue(colour and animal)
        r = self.p.sign_up_and_in(role="recruiter")
        self.assertIsNone(r["user"]["alias"])
        self.assertEqual(r["user"]["company"], "Test Co Pty Ltd")

    def test_alias_rules(self):
        a = self.p.sign_up_and_in(alias="Quiet River")
        self.assertEqual(a["user"]["alias"], "Quiet River")
        # taken, in any case
        s, r = self.api.call("POST", "/auth/signup", {"role": "candidate", "name": "Other", "email": "other1@example.test", "password": "longenough1", "alias": "quiet river"})
        self.assertEqual((s, r["error"]["code"]), (409, "ALIAS_TAKEN"))
        self.assertTrue(r["error"]["suggestion"])
        self.assertIn(r["error"]["suggestion"], r["error"]["fields"]["alias"])
        # the real name
        s, r = self.api.call("POST", "/auth/signup", {"role": "candidate", "name": "Zelda Quixote", "email": "other2@example.test", "password": "longenough1", "alias": "Zelda Fox"})
        self.assertEqual(r["error"]["fields"]["alias"], "Do not use your real name. Employers must not know who you are.")
        # origin words
        for alias in ("Vietnamese Fox", "Hanoi Owl", "Sri Lankan Cat"):
            s, r = self.api.call("GET", f"/aliases/check?alias={alias.replace(' ', '%20')}")
            self.assertFalse(r["available"], alias)
            self.assertEqual(r["reason"], "Do not use a country, nationality or city. Use a neutral alias.")
        s, r = self.api.call("GET", "/aliases/check?alias=Fox42")
        self.assertEqual(r["reason"], "Use letters, spaces, hyphens and apostrophes only.")
        s, r = self.api.call("GET", "/aliases/check?alias=ab")
        self.assertEqual(r["reason"], "Use 3 to 30 characters.")
        s, r = self.api.call("GET", "/aliases/check?alias=Quiet%20RIVER")
        self.assertEqual((r["available"], r["reason"]), (False, "This alias is taken."))
        s, r = self.api.call("GET", "/aliases/check?alias=Misty%20Meadow")
        self.assertEqual(r, {"alias": "Misty Meadow", "available": True})
        s, r = self.api.call("GET", "/aliases/suggest")
        self.assertRegex(r["alias"], r"^[A-Z][a-z]+ [A-Z][a-z]+( \d+)?$")

    # ----- sign in -----
    def test_login_errors_do_not_say_which_field_is_wrong(self):
        t = self.p.sign_up_and_in()
        for body in ({"email": t["email"], "password": "wrong password"}, {"email": "nobody@example.test", "password": "wrong password"}):
            s, r = self.api.call("POST", "/auth/login", body)
            self.assertEqual(s, 401)
            self.assertEqual(r["error"], {"code": "INVALID_CREDENTIALS", "message": "Incorrect email or password."})

    def test_session_length_and_me(self):
        t = self.p.sign_up_and_in()
        s, r = self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"], "remember": False})
        hours = (parse(r["expiresAt"]) - datetime.now(timezone.utc)).total_seconds() / 3600
        self.assertAlmostEqual(hours, 8, delta=0.1)
        s, r2 = self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"], "remember": True})
        days = (parse(r2["expiresAt"]) - datetime.now(timezone.utc)).total_seconds() / 86400
        self.assertAlmostEqual(days, 30, delta=0.1)
        s, me = self.api.call("GET", "/me", token=r2["token"])
        self.assertEqual(s, 200)
        self.assertEqual(me["email"], t["email"])
        for banned in ("password", "pw", "hash", "password_hash"):
            self.assertNotIn(banned, me)
        self.assertEqual(set(me), {"id", "role", "name", "email", "company", "alias", "profile", "cv", "onboarding", "createdAt"})

    def test_tokens_are_stored_as_hashes(self):
        t = self.p.sign_up_and_in()
        rows = self.p.conn().execute("SELECT token_hash FROM sessions").fetchall()
        self.assertNotIn(t["token"], [r["token_hash"] for r in rows])
        self.assertIn(security.hash_token(t["token"]), [r["token_hash"] for r in rows])

    def test_passwords_are_hashed_with_scrypt(self):
        t = self.p.sign_up_and_in()
        h = self.p.conn().execute("SELECT password_hash FROM users WHERE email = ?", (t["email"],)).fetchone()[0]
        self.assertTrue(h.startswith("scrypt$"))
        self.assertNotIn(t["password"], h)

    def test_logout_ends_the_session(self):
        t = self.p.sign_up_and_in()
        self.assertEqual(self.api.call("POST", "/auth/logout", token=t["token"]), (204, None))
        s, r = self.api.call("GET", "/me", token=t["token"])
        self.assertEqual((s, r["error"]["code"]), (401, "UNAUTHORIZED"))

    def test_expired_session_is_rejected(self):
        t = self.p.sign_up_and_in()
        c = self.p.conn()
        c.execute("UPDATE sessions SET expires_at = '2020-01-01T00:00:00.000Z' WHERE token_hash = ?", (security.hash_token(t["token"]),))
        c.close()
        s, r = self.api.call("GET", "/me", token=t["token"])
        self.assertEqual(s, 401)

    def test_login_rate_limit(self):
        t = self.p.sign_up_and_in()
        for _ in range(5):
            self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": "bad password!"})[0], 401)
        s, r = self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})
        self.assertEqual((s, r["error"]["code"]), (429, "RATE_LIMITED"))

    # ----- password -----
    def test_change_password(self):
        t = self.p.sign_up_and_in()
        s, other = self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})
        s, r = self.api.call("POST", "/me/password", {"currentPassword": "nope nope", "newPassword": "brand new pw 1"}, token=t["token"])
        self.assertEqual(r["error"]["fields"]["currentPassword"], "Your current password is not correct.")
        s, r = self.api.call("POST", "/me/password", {"currentPassword": t["password"], "newPassword": "short"}, token=t["token"])
        self.assertEqual(r["error"]["fields"]["newPassword"], "Use at least 8 characters.")
        s, r = self.api.call("POST", "/me/password", {"currentPassword": t["password"], "newPassword": t["password"]}, token=t["token"])
        self.assertEqual(r["error"]["fields"]["newPassword"], "Use a password that is different from your current one.")
        self.assertEqual(self.api.call("POST", "/me/password", {"currentPassword": t["password"], "newPassword": "brand new pw 1"}, token=t["token"]), (204, None))
        self.assertEqual(self.api.call("GET", "/me", token=t["token"])[0], 200)          # this session stays
        self.assertEqual(self.api.call("GET", "/me", token=other["token"])[0], 401)      # other sessions end
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})[0], 401)
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": "brand new pw 1"})[0], 200)

    # ----- me -----
    def test_patch_me(self):
        t = self.p.sign_up_and_in()
        s, r = self.api.call("PATCH", "/me", {"name": "  "}, token=t["token"])
        self.assertEqual(r["error"]["fields"]["name"], "Enter your name.")
        s, r = self.api.call("PATCH", "/me", {"onboarding": "maybe"}, token=t["token"])
        self.assertEqual(r["error"]["fields"]["onboarding"], "Not a valid onboarding state.")
        s, r = self.api.call("PATCH", "/me", {"name": "New Name", "onboarding": "dismissed", "email": "x@y.zz", "role": "recruiter"}, token=t["token"])
        self.assertEqual((s, r["name"], r["onboarding"], r["role"], r["email"]), (200, "New Name", "dismissed", "candidate", t["email"]))
        s, r = self.api.call("PATCH", "/me", {"alias": t["user"]["alias"]}, token=t["token"])
        self.assertEqual(s, 200)  # the same alias for the same user is fine
        e = self.p.sign_up_and_in(role="recruiter")
        s, r = self.api.call("PATCH", "/me", {"alias": "Teal Fox"}, token=e["token"])
        self.assertEqual(r["error"]["fields"]["alias"], "Only talent accounts have an alias.")
        s, r = self.api.call("PATCH", "/me", {"company": " "}, token=e["token"])
        self.assertEqual(r["error"]["fields"]["company"], "Enter your company.")
        s, r = self.api.call("PATCH", "/me", {"company": "New Co"}, token=e["token"])
        self.assertEqual(r["company"], "New Co")

    # ----- role guards (on the server) -----
    def test_role_guards(self):
        talent = self.p.sign_up_and_in()
        boss = self.p.sign_up_and_in(role="recruiter")
        for path in ("/recruiter/jobs", "/recruiter/candidates", "/recruiter/compare?ids=1,2&jobId=x"):
            s, r = self.api.call("GET", path, token=talent["token"])
            self.assertEqual((s, r["error"]["code"]), (403, "FORBIDDEN"), path)
        for path in ("/jobs/recommended", "/jobs", "/applications", "/bookmarks", "/me/shared-profile"):
            s, r = self.api.call("GET", path, token=boss["token"])
            self.assertEqual((s, r["error"]["code"]), (403, "FORBIDDEN"), path)
        for path in ("/me", "/jobs", "/recruiter/jobs", "/notifications", "/stats", "/entitlements"):
            self.assertEqual(self.api.call("GET", path)[0], 401, path)


if __name__ == "__main__":
    unittest.main()
