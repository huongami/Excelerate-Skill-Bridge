"""Talent aliases. An employer sees a person only by alias.

An alias must not show a real name, or where a person is from (Feature 1, AC6 and AC13).
"""
import random
import re
import sqlite3
import unicodedata
from typing import Optional

from .reference import COUNTRIES
from .util import ApiError

# Neutral words only: no personality adjectives and no colours that describe skin or hair.
COLOURS = ["Amber", "Azure", "Cobalt", "Coral", "Cyan", "Indigo", "Jade", "Lilac", "Lime", "Mint", "Plum",
           "Saffron", "Sage", "Slate", "Teal", "Violet"]
ANIMALS = ["Badger", "Crane", "Dolphin", "Falcon", "Finch", "Fox", "Gecko", "Heron", "Kestrel", "Koala", "Llama",
           "Lynx", "Otter", "Owl", "Panda", "Puffin", "Robin", "Seal", "Swift", "Wombat"]

# Words that show origin. An alias with one of these words is not accepted.
_ORIGIN_WORDS = [w.lower() for w in COUNTRIES + [
    "Aboriginal", "African", "American", "Arab", "Asian", "Australian", "Brazilian", "British", "Chinese", "Colombian",
    "Egyptian", "English", "Filipino", "French", "German", "Indian", "Indonesian", "Iranian", "Irish", "Italian",
    "Japanese", "Kenyan", "Korean", "Latino", "Malaysian", "Mexican", "Nepali", "Nigerian", "Pakistani", "Persian",
    "Russian", "Spanish", "Sri Lankan", "Thai", "Turkish", "Vietnamese", "Hanoi", "Saigon", "Beijing", "Shanghai",
    "Delhi", "Mumbai", "Manila", "Jakarta", "Lagos", "Nairobi", "Kathmandu", "Dhaka", "Karachi", "Bangkok",
]]

_FORMAT = re.compile(r"^[A-Za-z][A-Za-z '-]*[A-Za-z]$")


def _fold(text: str) -> str:
    """Lower case, without accents (the letter "đ" becomes "d")."""
    text = str(text or "").lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def norm_alias(alias) -> str:
    return re.sub(r"\s+", " ", str(alias or "").strip())


def is_taken(conn: sqlite3.Connection, alias: str, except_user_id: Optional[str] = None) -> bool:
    row = conn.execute(
        "SELECT 1 FROM users WHERE alias = ? COLLATE NOCASE AND id != ? LIMIT 1", (norm_alias(alias), except_user_id or "")
    ).fetchone()
    return row is not None


def suggest_alias(conn: sqlite3.Connection) -> str:
    """A random "Colour Animal" that is free. If all tries fail, add a number."""
    for _ in range(40):
        alias = f"{random.choice(COLOURS)} {random.choice(ANIMALS)}"
        if not is_taken(conn, alias):
            return alias
    n = 2
    base = f"{COLOURS[0]} {ANIMALS[0]}"
    while is_taken(conn, f"{base} {n}"):
        n += 1
    return f"{base} {n}"


def alias_problem(alias: str, real_name: str = "") -> str:
    """Return an error message, or "" if the alias is good."""
    a = norm_alias(alias)
    if len(a) < 3 or len(a) > 30:
        return "Use 3 to 30 characters."
    if not _FORMAT.match(a):
        return "Use letters, spaces, hyphens and apostrophes only."
    words = re.split(r"[\s'-]+", _fold(a))
    name_folded = _fold(str(real_name or ""))
    name_words = [p for p in re.split(r"[\s'-]+", name_folded) if p]
    # A name part of 3 or more letters must not be a word of the alias. A short part (for example "Li" or "Wu")
    # is only a problem when the alias has the whole name. The letters are compared without accents ("Nguyễn" = "Nguyen").
    whole_name = " ".join(name_words)
    if (any(len(p) >= 3 and p in words for p in name_words)
            or (len(name_words) > 1 and f" {whole_name} " in f" {' '.join(words)} ")
            or (name_words and ' '.join(words) == whole_name)):
        return "Do not use your real name. Employers must not know who you are."
    padded = f" {' '.join(words)} "
    if any(f" {w} " in padded for w in _ORIGIN_WORDS):
        return "Do not use a country, nationality or city. Use a neutral alias."
    return ""


def assert_alias_free(conn: sqlite3.Connection, alias: str, except_user_id: Optional[str] = None) -> None:
    """Raise 409 ALIAS_TAKEN with a free alias to suggest (Feature 1, AC13)."""
    if not is_taken(conn, alias, except_user_id):
        return
    suggestion = suggest_alias(conn)
    message = f"This alias is taken. Try “{suggestion}”."
    raise ApiError(409, "ALIAS_TAKEN", message, {"alias": message}, suggestion)
