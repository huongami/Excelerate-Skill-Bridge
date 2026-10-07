# Backend architecture: Jinder platform

| | |
|---|---|
| Code | `jinder_platform/jinder/` |
| Start | `python start.py` (or `start.bat` on Windows) |
| Language | Python 3.9 or later. Standard library only. |
| Third-party packages | None. `requirements.txt` lists one optional package (`pypdf`) for unusual PDF files. |
| Diagram | [`diagrams/03_backend_architecture.png`](diagrams/03_backend_architecture.png). Source: [`diagrams/03_backend_architecture.html`](diagrams/03_backend_architecture.html) |

All paths in this file are relative to `jinder_platform/`, unless the text says otherwise.

---

## 1. Overview

The backend is one Python process. It does four jobs:

1. It serves the frontend files from `jinder_frontend/app`.
2. It answers the REST API under `/api`.
3. It stores data in one SQLite file, `var/jinder.db`.
4. It calls the six formula files in `jinder_backend_engine/intelligence_engine`.

The server uses only the standard library: `http.server`, `sqlite3`, `hashlib`, `smtplib` and `concurrent.futures`. There is no web framework.

![Backend architecture](diagrams/03_backend_architecture.png)

To make the PNG again, open the HTML source in headless Chrome. Use a window of 1600 x 1680 and a device scale factor of 2.

---

## 2. Module layout

```
jinder_platform/
├── start.py              Starts the platform. Flags: --host, --port, --reset-db
├── start.bat             Runs start.py on Windows
├── run_tests.py          Runs the tests (unit and API; options for formulas and browser)
├── requirements.txt      No required package
├── var/                  Runtime data (made at start)
│   ├── jinder.db         SQLite database (WAL mode)
│   └── uploads/          Private CV and job description files
├── tests/                test_*.py files and browser checks
└── jinder/
    ├── __init__.py       Version "1.0.0"
    ├── app.py            main(): logging, database, seed, email worker, server
    ├── config.py         Settings from environment variables and .env
    ├── http_server.py    Server, routing, bodies, headers, static files
    ├── guards.py         require_user, require_role
    ├── security.py       scrypt passwords, session tokens, sign-in rate limits
    ├── store.py          Shared queries: users, sessions, profiles, plans, notifications
    ├── db.py             Connections, schema version, transactions
    ├── schema.sql        22 tables (schema version 2)
    ├── seed.py           Job catalogue and sample talent profiles
    ├── routes/           65 API routes in 6 modules (section 4)
    ├── parsing.py        Background file reading (thread pool)
    ├── textextract.py    Text from PDF and DOCX files
    ├── cv_parser.py      Fields from CV text
    ├── cv_lexicon.py     Word lists for the CV and job readers
    ├── jd_parser.py      Fields from job description text
    ├── translation.py    CV lines to taxonomy skills
    ├── aliases.py        Animal aliases for talent
    ├── catalogue.py      Job feed, fit and job checks
    ├── skills.py         Skill names and skill match
    ├── taxonomy.py       Reads ict_taxonomy.json
    ├── reference.py      Fixed lists (levels, work modes, countries)
    ├── engine_bridge.py  Loads and calls the six formulas
    ├── mailer.py         Email outbox worker
    └── util.py           ApiError, ids, dates, text clean-up
```

---

## 3. One request, step by step

### 3.1 Start-up (`app.py`)

1. `main()` reads the flags `--host`, `--port` and `--reset-db`.
2. It starts a log queue thread (`QueueHandler` and `QueueListener`). A slow log output cannot stop a request.
3. It checks that the frontend folder and the formula folder exist. If a folder is missing, it stops with exit code 2.
4. `db.init_db()` creates the tables and sets `journal_mode = WAL`. A database with schema version 1 is renamed to `<name>.v1.bak`. Nothing is deleted.
5. `seed.seed_all()` adds the job catalogue and the sample talent profiles, if they are missing.
6. `parsing.cleanup()` marks stopped file readings as failed. It also deletes unused upload files that are older than one day.
7. `mailer.start_worker()` starts the email thread.
8. `make_server()` starts the HTTP server. Ctrl+C stops the email worker and closes the server.

### 3.2 HTTP server (`http_server.py`)

- `JinderServer` is a `ThreadingHTTPServer`. Each request runs in its own thread. The threads are daemon threads.
- The handler speaks HTTP/1.1. A connection with no data for 30 seconds closes.
- A path that is `/api` or starts with `/api/` goes to the API. All other paths go to the static files.
- There is no version prefix. The API path is `/api/jobs`, not `/api/v1/jobs`.

### 3.3 Static files

- The server reads files from `jinder_frontend/app` (setting `JINDER_APP_DIR`).
- Only `GET` and `HEAD` are allowed. Other methods get 405.
- Only these types are served: `.html`, `.css`, `.js`, `.svg`, `.png`, `.jpg`, `.ico`, `.json`. Other files get 404.
- The resolved path must stay inside the folder. This blocks path traversal.
- Each file gets a `Content-Security-Policy` header and `Cache-Control: no-cache`.
- The folder `var/uploads` is never served.

### 3.4 API dispatch

1. `OPTIONS` gets 204 with the CORS headers (section 6.4).
2. The server reads the token from `Authorization: Bearer <token>`. There are no cookies.
3. `find_route()` finds the route. Routes are regular expressions. The server checks them in registration order. No match gives 404 `NOT_FOUND`.
4. A `multipart/form-data` request with no token gets 401 before the server reads the body.
5. The server reads the body (limits in section 3.5). A JSON body must be an object.
6. The server opens one SQLite connection for this request. It builds a `Ctx` object (method, path, query, body, files, token, IP, connection).
7. For a write verb (`POST`, `PUT`, `PATCH`, `DELETE`), the server runs `BEGIN IMMEDIATE` before the handler and `COMMIT` after it.
8. A route with `tx=False` opens its own transaction. These routes use it: `/auth/signup`, `/auth/login`, `/me/password`, `/me/delete`, `/admin/sql` and `/admin/action`. The first four do the slow password hash first, so they do not hold the write lock during the hash.
9. If the handler fails, the server runs `ROLLBACK`.
10. After `COMMIT`, the server runs the `after_commit` tasks. The upload routes use this to start the file reading.
11. The server closes the connection and sends the answer.

### 3.5 Body limits (`config.py`)

| Limit | Value |
|---|---|
| JSON body | 1 MB (`MAX_JSON_BYTES`) |
| Multipart body | 25 MB (`MAX_REQUEST_BYTES`) |
| One CV or job description file | 10 MB (`MAX_UPLOAD_BYTES`) |
| File types | PDF and DOCX. The server checks the file bytes, not only the name. |

A body that is too large gets 413 `TOO_LARGE`.

### 3.6 Answers and errors

- A handler returns a dictionary (200), a tuple `(status, body)`, or `None` (204).
- An error has this form: `{"error": {"code": "...", "message": "..."}}`. The client never gets a stack trace.
- A locked or failed database gives 503 `BUSY`. An unknown error gives 500 `INTERNAL`.
- Every JSON answer has `Cache-Control: no-store`.

### 3.7 Guards (`guards.py`, `store.py`)

The guards are not middleware. Each handler calls the guard that it needs.

| Guard | Result if the check fails |
|---|---|
| `require_user(ctx)` | 401 `UNAUTHORIZED` |
| `require_role(ctx, "candidate")` (Talent) | 403 `FORBIDDEN` |
| `require_role(ctx, "recruiter")` (Employer) | 403 `FORBIDDEN` |
| `store.require_premium(conn, user, feature)` | 403 `PREMIUM_REQUIRED` |

`store.user_for_token()` hashes the token with SHA-256 and looks up the hash in the `sessions` table. It deletes an expired session. The guard caches the user row for the request.

---

## 4. API routes

`routes/__init__.py` imports the modules in this order: `account`, `jobs`, `applications`, `recruiter`, `platform`, `admin`. There are 65 routes. All paths below start with `/api`.

### 4.1 `routes/account.py` (14 routes)

| Method | Path | Access |
|---|---|---|
| POST | `/auth/signup` | Public |
| POST | `/auth/login` | Public |
| POST | `/auth/logout` | Public (deletes the session of the token, if any) |
| GET | `/aliases/suggest` | Public |
| GET | `/aliases/check` | Public |
| GET, PATCH | `/me` | Signed in |
| POST | `/me/password` | Signed in |
| POST | `/cv` | Talent |
| GET | `/cv/parse/:id` | Talent |
| POST | `/profile/translate` | Talent |
| GET | `/me/shared-profile` | Talent |
| GET | `/me/export` | Signed in |
| POST | `/me/delete` | Signed in |

### 4.2 `routes/jobs.py` (10 routes)

| Method | Path | Access |
|---|---|---|
| GET | `/jobs/recommended` | Talent |
| GET | `/jobs` | Talent |
| GET | `/jobs/compare` | Talent |
| GET | `/jobs/:id` | Talent |
| PUT, DELETE | `/jobs/:id/skip` | Talent |
| GET | `/bookmarks` | Talent |
| PUT, DELETE | `/bookmarks/:jobId` | Talent |
| POST | `/reports` | Signed in |

### 4.3 `routes/applications.py` (8 routes, all Talent)

| Method | Path |
|---|---|
| POST, GET | `/applications` |
| GET, PATCH | `/applications/:id` |
| POST | `/applications/:id/slot` |
| POST | `/applications/:id/offer-reply` |
| POST | `/applications/:id/decline` |
| POST | `/applications/:id/feedback` |

### 4.4 `routes/recruiter.py` (20 routes, all Employer)

| Method | Path | Note |
|---|---|---|
| GET, POST | `/recruiter/jobs` | |
| POST | `/recruiter/jobs/suggest-skills` | |
| POST | `/recruiter/jobs/import` | Job description file. Returns 202 and a parse id. |
| GET | `/recruiter/jobs/import/:id` | Result of the file reading |
| GET, PATCH | `/recruiter/jobs/:id` | |
| GET | `/recruiter/jobs/:id/applications` | |
| GET | `/recruiter/applications/:id` | |
| POST | `/recruiter/applications/:id/status` | |
| POST | `/recruiter/applications/:id/confirm-slot` | |
| POST | `/recruiter/applications/:id/feedback` | |
| GET | `/recruiter/candidates` | |
| GET | `/recruiter/candidates/:id` | |
| PUT, DELETE | `/recruiter/candidates/:id/save` | |
| PUT | `/recruiter/candidates/:id/skip` | |
| DELETE | `/recruiter/candidates/skipped` | |
| POST | `/recruiter/candidates/:id/contact` | Premium (`canContact`) |
| GET | `/recruiter/compare` | Premium (`canCompare`) |

### 4.5 `routes/platform.py` (6 routes)

| Method | Path | Access |
|---|---|---|
| GET | `/health` | Public. Checks the database and the formula files. |
| GET | `/notifications` | Signed in |
| POST | `/notifications/read` | Signed in |
| GET | `/entitlements` | Signed in |
| PUT | `/entitlements` | Signed in. Works only when `JINDER_ALLOW_PLAN_SWITCH` allows it. |
| GET | `/stats` | Signed in |

### 4.6 `routes/admin.py` (7 routes, no access check)

| Method | Path | What it does |
|---|---|---|
| GET | `/admin/overview` | Row counts and summary data |
| GET | `/admin/tables` | List of tables |
| GET | `/admin/table-data` | Rows of a table |
| GET | `/admin/traffic` | Request counters and latency (in memory) |
| GET | `/admin/dataflow` | Data flow figures |
| POST | `/admin/sql` | Runs a query that starts with `SELECT`, `PRAGMA` or `EXPLAIN`. Returns 100 rows at most. |
| POST | `/admin/action` | `wal_checkpoint` runs a WAL checkpoint. `vacuum` does nothing. |

**Known gap.** These routes do not call a guard. They do not check a session or a role. A caller who can reach the port can read every table, including emails and private CV data. The default host `127.0.0.1` limits the risk to the local computer. Fix this gap before the server runs on a shared computer, a network or in public. See `Document/GAP_ANALYSIS.md`, section 1.

---

## 5. Data and formulas

### 5.1 Database (`db.py`, `schema.sql`)

- The file is `var/jinder.db` (setting `JINDER_DB_PATH`).
- `init_db()` sets `journal_mode = WAL`. In WAL mode, readers do not block the writer.
- Each request opens its own connection. Threads never share a connection.
- Each connection sets `foreign_keys = ON` and `busy_timeout = 8000` (8 seconds).
- The schema has 22 tables. The schema version is 2.
- Details of the tables are in [`DATA_MODELING_ARCHITECTURE_DETAIL.md`](DATA_MODELING_ARCHITECTURE_DETAIL.md).

### 5.2 Shared logic

- `store.py` has the shared queries. Examples: `user_for_token()`, `shared_profile()`, `notify()`, `entitlements_of()`.
- `catalogue.py` builds the job feed and the job fit. It calls the formulas through `engine_bridge.py`.
- `taxonomy.py` reads `jinder_backend_engine/data/reference/ict_taxonomy.json` once.

### 5.3 Formula bridge (`engine_bridge.py`)

- The bridge loads the six formula files by path with `importlib`. It loads each file once, under a lock.
- The folder is `jinder_backend_engine/intelligence_engine` (setting `JINDER_ENGINE_DIR`).
- The bridge builds the talent and job dictionaries that the formulas expect.
- A talent dictionary never has a name, an email, a country of origin or a visa status.
- For an employer, the bridge uses only the shared profile.
- The API uses a talent score only to put profiles in order. It never sends the score to an employer.

---

## 6. Security

### 6.1 Passwords (`security.py`)

- The hash is scrypt with N = 2^14, r = 8, p = 1, a 16-byte random salt and a 32-byte key.
- The check uses `hmac.compare_digest` (constant time).
- For an unknown email, the server still runs one scrypt hash. The answer time does not show if the account exists.
- A password has 8 to 200 characters.
- The tests set `JINDER_FAST_TEST_HASH=1` for a fast, weak hash. A server with this setting writes a warning. Do not use it outside tests.

### 6.2 Sessions

- `POST /auth/login` makes a random token with `secrets.token_urlsafe(32)`.
- The `sessions` table stores only the SHA-256 hash of the token.
- A session lasts 8 hours (`SESSION_HOURS`). With "remember", it lasts 30 days (`REMEMBER_DAYS`).
- `POST /auth/logout` deletes the session.
- A password change deletes the other sessions of the user. The current session stays.

### 6.3 Sign-in rate limits

`security.RateLimiter` keeps a list (a `deque`) of failure times for each key. A failure older than 15 minutes drops out of the list. Only failed tries count.

| Limiter | Key | Limit |
|---|---|---|
| `login_limiter` | IP address + email | 5 failures in 15 minutes |
| `address_limiter` | IP address | 20 failures in 15 minutes |
| `email_limiter` | Email | 30 failures in 15 minutes |
| `login_limiter` | `pw:<user id>` (current password check on `/me/password` and `/me/delete`) | 5 failures in 15 minutes |

- A blocked sign-in gets 429 `RATE_LIMITED`.
- A good sign-in resets only the IP address + email key.
- The limits apply only to sign-in and to the current password check. There is no general request rate limit.
- The counters are in memory. They are for one process. A restart clears them.

### 6.4 Response headers and CORS (`http_server.py`)

Every response has these headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

Static files also get this `Content-Security-Policy`:

```
default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com;
font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self';
object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
```

An SVG file gets `default-src 'none'; style-src 'unsafe-inline'`. API answers do not get a CSP header.

CORS headers go only to origins in `JINDER_CORS_ORIGINS`. The list is empty by default.

The API uses a Bearer header, not cookies. For this reason the server has no CSRF token and no origin check.

### 6.5 Logs

- A log line has the method, the path, the status and the time in ms.
- A log line never has a query string, a body or a token.
- The same data goes to in-memory counters (`TRAFFIC`). `/admin/traffic` reads them.

---

## 7. Background work

### 7.1 File reading (`parsing.py`)

- Uploaded files go to `var/uploads/` (setting `JINDER_UPLOAD_DIR`). The server makes the file name. The file mode is 600.
- `POST /cv` and `POST /recruiter/jobs/import` write a `parses` row with status `parsing`. They answer at once.
- After `COMMIT`, an `after_commit` task gives the job to a `ThreadPoolExecutor` with 2 workers (`jinder-parse`).
- A worker reads the text (`textextract.py`) and the fields (`cv_parser.py` or `jd_parser.py`).
- The worker sets the status to `done` or `failed`. The browser polls `GET /cv/parse/:id` or `GET /recruiter/jobs/import/:id`.
- A job description file is deleted after the reading. A CV file stays until the talent replaces it or deletes the account.

### 7.2 Email outbox (`mailer.py`)

- `store.notify(..., email=True)` writes a row to `email_outbox` in the same transaction as the event.
- The thread `jinder-outbox` runs every 20 seconds. It takes up to 20 due rows.
- If `JINDER_SMTP_HOST` is set, the worker sends the email with SMTP and STARTTLS. The status becomes `sent`.
- If `JINDER_SMTP_HOST` is empty, nothing leaves the server. The status becomes `recorded`.
- A failed send waits 2^n minutes (n = number of tries). After 5 tries, the status becomes `failed`.
- A failed email never blocks the action that caused it.

---

## 8. Settings (`config.py`)

| Variable | Default |
|---|---|
| `JINDER_HOST` | `127.0.0.1` |
| `JINDER_PORT` (or `PORT`) | `8095` |
| `JINDER_APP_DIR` | `../jinder_frontend/app` |
| `JINDER_ENGINE_DIR` | `../jinder_backend_engine/intelligence_engine` |
| `JINDER_DATA_DIR` | `../jinder_backend_engine/data` |
| `JINDER_DB_PATH` | `var/jinder.db` |
| `JINDER_UPLOAD_DIR` | `var/uploads` |
| `JINDER_CORS_ORIGINS` | empty |
| `JINDER_SMTP_HOST`, `_PORT`, `_USER`, `_PASSWORD`, `_FROM` | empty, 587, empty, empty, `no-reply@jinder.local` |
| `JINDER_ALLOW_PLAN_SWITCH` | On when the host is `127.0.0.1`, `localhost` or `::1`. Off for other hosts. |

A `.env` file in `jinder_platform/` can set these values. A value in the environment wins.

---

## 9. Tests

- `python run_tests.py` runs the unit and API tests in `tests/test_*.py`. These files have 691 test methods.
- `--formulas` also runs the self-checks of the six formula files.
- `--browser` also runs the browser checks in `tests/browser/`. `--browser-quick` runs only the two journey checks.

---

## 10. Limits of this design

- The rate limits and the traffic counters are in memory. Two server processes do not share them.
- SQLite allows one writer at a time. A write waits up to 8 seconds for the lock. Then the request gets 503 `BUSY`.
- The parse pool has 2 workers. More uploads wait in the pool queue.
- The admin routes have no access check (section 4.6).
- No performance numbers are measured in this document.
