"""Small helpers that all modules use: time, ids, JSON, text and API errors."""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple


# ---------- Errors ----------
class ApiError(Exception):
    """An error that the API sends to the client as { "error": { code, message, fields?, suggestion? } }."""

    def __init__(self, status: int, code: str, message: str, fields: Optional[Dict[str, str]] = None,
                 suggestion: Optional[str] = None, extra: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields
        self.suggestion = suggestion
        self.extra = extra          # more keys at the top level of the body, next to "error" (for example { "missing": [ids] })

    def to_body(self) -> Dict[str, Any]:
        err: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.fields:
            err["fields"] = self.fields
        if self.suggestion:
            err["suggestion"] = self.suggestion
        body: Dict[str, Any] = {"error": err}
        if self.extra:
            body.update(self.extra)
        return body


def validation(fields: Dict[str, str]) -> None:
    """Raise VALIDATION_ERROR with only the fields that have a message."""
    bad = {k: v for k, v in fields.items() if v}
    if bad:
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", bad)


# ---------- Pages and sorting (V2_PLAN.md, section 5.1) ----------
PAGE_SIZE_DEFAULT = 10
PAGE_SIZE_MAX = 50


class PageParams(NamedTuple):
    page: int
    page_size: int
    sort: str


def _whole_number(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def page_params(query: Dict[str, Any], sorts: Sequence[str]) -> PageParams:
    """Read `page`, `pageSize` and `sort` from a query string. The first item of `sorts` is the default sort.

    page      a whole number from 1 (default 1). A bad value gives 1.
    pageSize  a whole number, set to the range 1 to 50 (default 10). A bad value gives the default.
    sort      one of `sorts`. Any other value is a 400 error with the field "sort".
    """
    sort = str(query.get("sort") or "").strip() or sorts[0]
    if sort not in sorts:
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", {"sort": "Use one of these: " + ", ".join(sorts) + "."})
    page = max(1, _whole_number(query.get("page"), 1))
    size = min(max(_whole_number(query.get("pageSize"), PAGE_SIZE_DEFAULT), 1), PAGE_SIZE_MAX)
    return PageParams(page, size, sort)


def paginate(items: Sequence[Any], params: PageParams, cap: Optional[int] = None) -> Tuple[List[Any], Dict[str, int]]:
    """The items of one page, and the `page` object { page, pageSize, total, totalPages } of the API.

    A page number above the last page gives the last page (`page.page` tells which page it is).
    With `cap` (the Basic plan of an employer) there is only one page with the first `cap` items.
    `total` is always the real number of items.
    """
    total = len(items)
    if cap is not None:
        return list(items[:cap]), {"page": 1, "pageSize": cap, "total": total, "totalPages": 1}
    pages = max(1, -(-total // params.page_size))
    page = min(params.page, pages)
    start = (page - 1) * params.page_size
    return list(items[start:start + params.page_size]), {"page": page, "pageSize": params.page_size, "total": total, "totalPages": pages}


def not_found(message: str) -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def conflict(message: str) -> ApiError:
    return ApiError(409, "CONFLICT", message)


# ---------- Time ----------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    """ISO 8601 with milliseconds and a Z suffix, for example 2026-10-06T03:45:04.120Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def now_iso() -> str:
    return iso(utcnow())


def parse_iso(value: Any) -> Optional[datetime]:
    """Parse an ISO 8601 string. Return None if the value is empty or not a date."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # A plain date or a date with a space between date and time
        try:
            dt = datetime.strptime(text[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(text[:10], "%Y-%m-%d")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def days_from_now(days: float) -> str:
    return iso(utcnow() + timedelta(days=days))


# ---------- Ids ----------
def new_id() -> str:
    return str(uuid.uuid4())


def short_id(n: int = 8) -> str:
    return uuid.uuid4().hex[:n]


# ---------- JSON ----------
def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def jload(text: Any, default: Any = None) -> Any:
    if text is None or text == "":
        return default
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return default


# ---------- Text ----------
def as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", False):
        return []
    return [value]


def norm(text: Any) -> str:
    return str(text or "").lower().strip()


def clean_text(text: Any, max_len: int = 1000) -> str:
    """Remove control characters and cut the text to max_len. The text stays plain text."""
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(text or ""))
    return value.strip()[:max_len]


def clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    if number == 0:
        number = default if default else 0
    return min(max(number, low), high)


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_email(value: Any) -> bool:
    text = str(value or "")
    return len(text) <= 254 and bool(EMAIL_RE.match(text))


# Contact details must never reach the other side in free text (AI_Rule Rule 5, item 12).
_EMAIL_IN_TEXT = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_PHONE_IN_TEXT = re.compile(r"\+?\(?\d[\d\s().-]{7,}\d")
# These look like a phone number to the pattern, but they are not: a date, a range of years, a number after a dollar sign
_NOT_A_PHONE = re.compile(r"^(?:(?:19|20)\d{2}[-/. ]\d{1,2}[-/. ]\d{1,2}|\d{1,2}[-/. ]\d{1,2}[-/. ](?:19|20)\d{2}|(?:19|20)\d{2}\s*[-.]\s*(?:19|20)\d{2})$")


def _phone_or_keep(m: "re.Match[str]") -> str:
    found = m.group(0)
    before = m.string[max(0, m.start() - 1):m.start()]
    if before == "$" or _NOT_A_PHONE.match(found.strip()) or len(re.sub(r"\D", "", found)) < 8:
        return found
    return "[phone removed]"


def scrub_contact(text: Any) -> str:
    value = str(text or "")
    value = _EMAIL_IN_TEXT.sub("[email removed]", value)
    return _PHONE_IN_TEXT.sub(_phone_or_keep, value)


def unique(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
