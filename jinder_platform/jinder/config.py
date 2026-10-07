"""Settings for the Jinder platform.

Every value can be changed with an environment variable, or with a `.env` file in the
`jinder_platform` folder. The `.env` file is never committed (see `.gitignore`).
"""
import os
from pathlib import Path

PLATFORM_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PLATFORM_DIR.parent


def _load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines. A value that is already in the environment wins."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(PLATFORM_DIR / ".env")


def _env_path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name) or default).resolve()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# ---------- Folders ----------
# The formulas, the datasets and the frontend stay in their own folders. The platform only reads them.
ENGINE_DIR = _env_path("JINDER_ENGINE_DIR", WORKSPACE_DIR / "jinder_backend_engine" / "intelligence_engine")
DATA_DIR = _env_path("JINDER_DATA_DIR", WORKSPACE_DIR / "jinder_backend_engine" / "data")
APP_DIR = _env_path("JINDER_APP_DIR", WORKSPACE_DIR / "Skill Bridge" / "app")

# The taxonomy: the one list of names (skills, roles, certifications, domains ...). The formulas and the CV reader load the same file.
TAXONOMY_PATH = _env_path("JINDER_TAXONOMY_PATH", DATA_DIR / "reference" / "ict_taxonomy.json")
# The synthetic demo data: 50 jobs, 50 sample talents and the demo employer jobs
SYNTHETIC_DIR = _env_path("JINDER_SYNTHETIC_DIR", DATA_DIR / "synthetic")

VAR_DIR = _env_path("JINDER_VAR_DIR", PLATFORM_DIR / "var")
DB_PATH = _env_path("JINDER_DB_PATH", VAR_DIR / "jinder.db")
UPLOAD_DIR = _env_path("JINDER_UPLOAD_DIR", VAR_DIR / "uploads")

# ---------- Server ----------
HOST = os.environ.get("JINDER_HOST", "127.0.0.1")
PORT = _env_int("JINDER_PORT", _env_int("PORT", 8095))
# Origins (comma separated) that may call the API from another port, for example http://localhost:5173
CORS_ORIGINS = [o.strip() for o in os.environ.get("JINDER_CORS_ORIGINS", "").split(",") if o.strip()]

# ---------- Limits ----------
MAX_JSON_BYTES = 1 * 1024 * 1024
MAX_UPLOAD_BYTES = 10 * 1024 * 1024            # a CV or a job description file
MAX_REQUEST_BYTES = 25 * 1024 * 1024           # the whole multipart body
SESSION_HOURS = 8
REMEMBER_DAYS = 30
LOGIN_MAX_FAILURES = 5                         # for each email and address
LOGIN_WINDOW_SECONDS = 15 * 60

# ---------- Product rules ----------
TOP_N = 5                                      # basic plan: the number of talent profiles an employer sees
COMPARE_MAX = 5                                # the most jobs (talent) or profiles (employer) in one comparison
JOB_OPEN_DAYS = 30                             # a catalogue job closes this many days after it was posted

# ---------- Optional email (SMTP). Without these values the outbox only records the message. ----------
SMTP_HOST = os.environ.get("JINDER_SMTP_HOST", "")
SMTP_PORT = _env_int("JINDER_SMTP_PORT", 587)
SMTP_USER = os.environ.get("JINDER_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("JINDER_SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("JINDER_SMTP_FROM", "no-reply@jinder.local")

# The Basic/Premium switch in Settings is a demo toggle. A real service changes the plan through billing: set this to 0.
_PLAN_SWITCH = os.environ.get("JINDER_ALLOW_PLAN_SWITCH", "")
# Default: on when the server is only for this computer, off when it listens on other addresses (a public service must not give Premium for free)
ALLOW_PLAN_SWITCH = (_PLAN_SWITCH != "0") if _PLAN_SWITCH else (os.environ.get("JINDER_HOST", "127.0.0.1") in ("127.0.0.1", "localhost", "::1"))

# Keep the sample catalogue dates fresh, so that the demo jobs do not all close. Set to 1 to turn it off.
FREEZE_CATALOGUE_DATES = os.environ.get("JINDER_FREEZE_DATES", "") == "1"
