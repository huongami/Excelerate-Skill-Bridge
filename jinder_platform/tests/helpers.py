"""Test helpers: a real server on a free port with a temporary database, and a small API client.

Every test module imports this file first. It sets the environment before the platform is imported.
"""
import io
import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TMP = tempfile.mkdtemp(prefix="jinder-test-")
os.environ["JINDER_VAR_DIR"] = _TMP
os.environ["JINDER_DB_PATH"] = str(Path(_TMP) / "test.db")
os.environ["JINDER_UPLOAD_DIR"] = str(Path(_TMP) / "uploads")
# A weak and fast password hash, only for the test accounts (many tests make a user). It is never the default of the server.
if os.environ.get("JINDER_REAL_HASH_IN_TESTS") != "1":      # set it to 1 to run the tests with the real (slow) hash
    os.environ["JINDER_FAST_TEST_HASH"] = "1"

from jinder import app as platform_app  # noqa: E402
from jinder import config, db, security  # noqa: E402
from jinder.http_server import make_server  # noqa: E402


class Api:
    """A tiny HTTP client. It returns (status, json)."""

    def __init__(self, base: str):
        self.base = base

    def call(self, method, path, body=None, token=None, raw=None, headers=None, absolute=False):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        h = {} if raw is not None else ({"Content-Type": "application/json"} if body is not None else {})
        h.update(headers or {})
        if token:
            h["Authorization"] = "Bearer " + token
        url = self.base + ("" if absolute else "/api") + path
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req) as r:
                b = r.read()
                if not b:
                    return r.status, None
                return r.status, (json.loads(b) if r.headers.get_content_type() == "application/json" else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b) if b else None
            except ValueError:
                return e.code, b

    def raw_headers(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def upload(self, path, filename, data, token, field="file", content_type="application/octet-stream"):
        boundary = "----jinder" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {content_type}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        return self.call("POST", path, raw=body, token=token, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})


class Platform:
    """Start the platform once for a test module."""
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            info = platform_app.prepare(demo=True, reset=True)
            server = make_server("127.0.0.1", 0)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            p = cls()
            p.server = server
            p.api = Api(f"http://127.0.0.1:{server.server_address[1]}")
            p.demo = info["demo"]
            cls._instance = p
        return cls._instance

    def conn(self):
        return db.connect()

    def sign_up_and_in(self, role="candidate", name="Test Person", email=None, password="correct horse 1", company="Test Co Pty Ltd", alias=None):
        email = email or f"{uuid.uuid4().hex[:10]}@example.test"
        body = {"role": role, "name": name, "email": email, "password": password}
        if role == "recruiter":
            body["company"] = company
        if alias:
            body["alias"] = alias
        s, r = self.api.call("POST", "/auth/signup", body)
        assert s == 201, (s, r)
        s, r = self.api.call("POST", "/auth/login", {"email": email, "password": password, "remember": False})
        assert s == 200, (s, r)
        return {"token": r["token"], "user": r["user"], "email": email, "password": password}

    def login_demo(self, email):
        s, r = self.api.call("POST", "/auth/login", {"email": email, "password": self.demo[email]})
        assert s == 200, (s, r)
        return {"token": r["token"], "user": r["user"]}


def make_docx(paragraphs):
    """A small valid DOCX file with these paragraphs."""
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = ("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
           f"<w:body>{body}</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"/>")
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def make_pdf(lines):
    """A small valid PDF (one page, Helvetica) with one line of text for each item in lines."""
    def esc(t):
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = "BT /F1 11 Tf 14 TL 50 780 Td " + " ".join(f"({esc(l)}) Tj T*" for l in lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /FirstChar 32 /LastChar 126 /Widths ["
        + " ".join(["556"] * 95) + "] >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


CV_LINES = [
    "PROFILE",
    "Data Analyst with 4 years of experience in reporting and analytics. Looking for a Data Engineer role.",
    "EXPERIENCE",
    "Data Analyst - North Star Retail (2020 - 2024)",
    "Built weekly Power BI dashboards for 6 regional teams and cut manual reporting time by 40%.",
    "Wrote SQL queries and Python scripts to clean and join data from 5 source systems.",
    "BI Specialist - Blue Harbour Software (2018 - 2020)",
    "Designed ER diagrams and a reporting data model for the finance data warehouse.",
    "EDUCATION",
    "Bachelor of Information Systems, University of Technology, Vietnam, 2014 - 2018",
    "SKILLS",
    "SQL, Python, Power BI, Microsoft Excel, Data modelling, Git, Data visualisation",
]
