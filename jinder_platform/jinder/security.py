"""Passwords, session tokens and the sign-in rate limit.

Passwords use scrypt with a random salt (AI_Rule Rule 6, item 7). A session token is a random value.
The database stores only the SHA-256 hash of the token, so a stolen database cannot be used to sign in.
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from . import config

# The cost of the password hash. The tests set the variable JINDER_FAST_TEST_HASH=1 (run_tests.py and tests/helpers.py do it) to make
# many test accounts quickly. The value is NEVER the default, and a server that starts with it writes a loud warning.
FAST_TEST_HASH = os.environ.get("JINDER_FAST_TEST_HASH") == "1"
_SCRYPT_N = 2 ** 4 if FAST_TEST_HASH else 2 ** 14
if FAST_TEST_HASH:
    logging.getLogger("jinder.security").warning("JINDER_FAST_TEST_HASH is on: password hashes are weak. Use it only in tests.")
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 32
NO_LOGIN = "!"  # the hash of a sample account: it never matches a password


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_KEY_LEN)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password: str, stored: str) -> bool:
    """Check a password in constant time. A sample account (hash "!") always fails."""
    if not stored or stored == NO_LOGIN or not stored.startswith("scrypt$"):
        # Do the same work as a real check, so that the time does not show if the account exists
        hashlib.scrypt(password.encode("utf-8"), salt=b"jinder-dummy-salt", n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_KEY_LEN)
        return False
    try:
        _, n, r, p, salt_b64, digest_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------- Sign-in rate limit (in memory, for one server process) ----------
class RateLimiter:
    """Allow a small number of failed sign-ins in a time window, for each key (email or address)."""

    def __init__(self, max_failures: int, window_seconds: int):
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _trim(self, key: str, now: float) -> Deque[float]:
        q = self._failures[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def blocked(self, *keys: str) -> bool:
        now = time.monotonic()
        with self._lock:
            return any(len(self._trim(k, now)) >= self.max_failures for k in keys)

    def fail(self, *keys: str) -> None:
        now = time.monotonic()
        with self._lock:
            for k in keys:
                self._trim(k, now).append(now)
            if len(self._failures) > 5000:   # many different keys (probing): forget the old ones
                for k in [k for k in self._failures if not self._trim(k, now)]:
                    del self._failures[k]

    def reset(self, *keys: str) -> None:
        with self._lock:
            for k in keys:
                self._failures.pop(k, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_limiter = RateLimiter(config.LOGIN_MAX_FAILURES, config.LOGIN_WINDOW_SECONDS)       # one address with one email
# A looser limit for each address, so that one address cannot try many emails
address_limiter = RateLimiter(config.LOGIN_MAX_FAILURES * 4, config.LOGIN_WINDOW_SECONDS)
# The loosest limit is for one email from all addresses. It stops a spread attack, but it is too high to lock the owner out
email_limiter = RateLimiter(config.LOGIN_MAX_FAILURES * 6, config.LOGIN_WINDOW_SECONDS)


def make_demo_password() -> str:
    """A random password for a demo account. It is shown once and never stored in plain text."""
    return secrets.token_urlsafe(9)
