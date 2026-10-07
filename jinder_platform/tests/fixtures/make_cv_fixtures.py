#!/usr/bin/env python3
"""Make the fixture CVs for the CV reader tests (feedback item R1).

  python tests/fixtures/make_cv_fixtures.py

The script writes the files in tests/fixtures/cv/ and the file expected.json. It uses only the Python standard library.
The files are committed, so a test run does not need this script. Run it again only when you change a fixture.

All people, employers, e-mail addresses and phone numbers are made up. No real data is in these files.

What is tested: the TEXT ORDER problems of real CV files (two columns with interleaved text, a sidebar that is written first,
a title above the name, a header in a form XObject, a flipped page, ligatures, private-use bullets, hyphenated words, words with no
space glyph, odd font encodings) and the many ways in which a CV writes a job title, dates, a wish for a job, certifications and awards.
expected.json holds the TRUE values (what a person sees in the CV), not what the reader gives.
"""
import io
import json
import os
import zipfile
import zlib
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cv")
AS_OF = date(2026, 10, 6)       # the tests read the CVs "as of" this day, so that the expected years do not change with time

# The widths of the Helvetica glyphs for the codes 32 to 126 (1000 units to the font size)
HELV = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]
DIFF_CODES = {"•": 127, "–": 128, "—": 129, "ﬁ": 130, "ﬂ": 131}   # /Differences of the font "Fx" (bullet endash emdash fi fl)
DIFF_NAMES = ["bullet", "endash", "emdash", "fi", "fl"]


def char_width(ch: str, bold: bool = False) -> float:
    w = HELV[ord(ch) - 32] if 32 <= ord(ch) <= 126 else (500 if ch == "–" else 556)
    return w * (1.06 if bold else 1.0)


def text_width(text: str, size: float, bold: bool = False) -> float:
    return sum(char_width(c, bold) for c in text) * size / 1000.0


# =====================================================================
# A small PDF writer
# =====================================================================
def pdf_string(raw: bytes) -> bytes:
    out = bytearray(b"(")
    for b in raw:
        if b in (0x28, 0x29, 0x5C):
            out += b"\\" + bytes([b])
        elif 32 <= b < 127:
            out.append(b)
        else:
            out += b"\\%03o" % b
    return bytes(out) + b")"


class Page:
    def __init__(self, pdf: "Pdf"):
        self.pdf = pdf
        self.ops: List[Dict[str, Any]] = []
        self.forms: List[List[Dict[str, Any]]] = []     # form XObjects: each is a list of ops

    def t(self, x: float, y: float, text: str, size: float = 10, bold: bool = False, how: str = "tj") -> None:
        """Draw one line. how: "tj" (one string), "kern" (words with the space as a number in a TJ array), "words" (each word alone, no space glyph)."""
        if text.strip():
            self.ops.append(dict(x=x, y=y, size=size, bold=bold, text=text, how=how))

    def form(self, ops: List[Dict[str, Any]]) -> None:
        """Draw these ops inside a form XObject. ops are made with Page.op()."""
        self.forms.append(ops)
        self.ops.append(dict(form=len(self.forms)))

    @staticmethod
    def op(x: float, y: float, text: str, size: float = 10, bold: bool = False, how: str = "tj") -> Dict[str, Any]:
        return dict(x=x, y=y, size=size, bold=bold, text=text, how=how)


class Pdf:
    def __init__(self, compress: bool = False, flipped: bool = False, diff_encoding: bool = False):
        self.compress = compress
        self.flipped = flipped
        self.diff_encoding = diff_encoding
        self.pages: List[Page] = []
        self.cid: Dict[str, int] = {}

    def page(self) -> Page:
        p = Page(self)
        self.pages.append(p)
        return p

    # ----- encoding of a string for the content stream -----
    def _needs_unicode(self, text: str) -> bool:
        for ch in text:
            if self.diff_encoding and ch in DIFF_CODES:
                continue
            try:
                ch.encode("cp1252")
            except UnicodeEncodeError:
                return True
        return False

    def _simple(self, text: str) -> bytes:
        raw = bytearray()
        for ch in text:
            if self.diff_encoding and ch in DIFF_CODES:
                raw.append(DIFF_CODES[ch])
            else:
                raw += ch.encode("cp1252")
        return pdf_string(bytes(raw))

    def _hex(self, text: str) -> bytes:
        return b"<" + "".join(f"{self.cid[c]:04X}" for c in text).encode() + b">"

    def _collect_chars(self) -> None:
        all_ops = [op for p in self.pages for op in p.ops if "text" in op] + [op for p in self.pages for f in p.forms for op in f]
        for op in all_ops:
            if self._needs_unicode(op["text"]):
                for c in op["text"]:
                    self.cid.setdefault(c, len(self.cid) + 1)

    def _ops_stream(self, ops: List[Dict[str, Any]], form_names: Optional[Dict[int, str]] = None) -> bytes:
        lines: List[bytes] = []
        for op in ops:
            if "form" in op:
                lines.append(f"/{form_names[op['form']]} Do".encode())
                continue
            x, y, size, text = op["x"], op["y"], op["size"], op["text"]
            uni = self._needs_unicode(text)
            font = "F3" if uni else ("F2" if op["bold"] else "F1")
            if self.diff_encoding and not uni:
                font = "F4"
            yy = (842 - y) if self.flipped else y
            flip = -1 if self.flipped else 1

            def tm(px: float) -> bytes:
                return f"1 0 0 {flip} {px:.2f} {yy:.2f} Tm".encode()

            def enc(s: str) -> bytes:
                return self._hex(s) if uni else self._simple(s)

            if op["how"] == "words":
                px = x
                for word in text.split(" "):
                    if word:
                        lines.append(b"BT /" + font.encode() + f" {size} Tf ".encode() + tm(px) + b" " + enc(word) + b" Tj ET")
                    px += text_width(word + " ", size, op["bold"])
            elif op["how"] == "kern":
                parts = text.split(" ")
                arr = b" -278 ".join(enc(w) for w in parts)
                lines.append(b"BT /" + font.encode() + f" {size} Tf ".encode() + tm(x) + b" [" + arr + b"] TJ ET")
            else:
                lines.append(b"BT /" + font.encode() + f" {size} Tf ".encode() + tm(x) + b" " + enc(text) + b" Tj ET")
        return b"\n".join(lines)

    def build(self) -> bytes:
        self._collect_chars()
        objs: Dict[int, bytes] = {}
        next_num = [1]

        def alloc() -> int:
            n = next_num[0]
            next_num[0] += 1
            return n

        def stream(body: bytes, extra: str = "") -> bytes:
            data = zlib.compress(body, 9) if self.compress else body
            filt = "/Filter /FlateDecode " if self.compress else ""
            return f"<< {extra}{filt}/Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream"

        cat, pages_n, f1, f2 = alloc(), alloc(), alloc(), alloc()
        font_res = f"/F1 {f1} 0 R /F2 {f2} 0 R"
        widths = " ".join(str(HELV[i]) for i in range(95))
        bold_widths = " ".join(str(int(HELV[i] * 1.06)) for i in range(95))
        objs[f1] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding /FirstChar 32 /LastChar 126 /Widths [{widths}] >>".encode()
        objs[f2] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding /FirstChar 32 /LastChar 126 /Widths [{bold_widths}] >>".encode()
        if self.cid:
            f3, desc, tou = alloc(), alloc(), alloc()
            font_res += f" /F3 {f3} 0 R"
            order = sorted(self.cid, key=lambda c: self.cid[c])
            wlist = " ".join(str(278 if c == " " else int(char_width(c))) for c in order)
            objs[f3] = (f"<< /Type /Font /Subtype /Type0 /BaseFont /FixtureSans /Encoding /Identity-H /DescendantFonts [{desc} 0 R] /ToUnicode {tou} 0 R >>").encode()
            objs[desc] = (f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /FixtureSans /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
                          f"/DW 556 /W [1 [{wlist}]] /CIDToGIDMap /Identity >>").encode()
            bf = "\n".join(f"<{self.cid[c]:04X}> <{''.join(f'{u:04X}' for u in _utf16(c))}>" for c in order)
            cmap = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n/CMapName /Adobe-Identity-UCS def /CMapType 2 def\n"
                    f"1 begincodespacerange <0000> <FFFF> endcodespacerange\n{len(order)} beginbfchar\n{bf}\nendbfchar\nendcmap end end").encode()
            objs[tou] = stream(cmap)
        if self.diff_encoding:
            f4 = alloc()
            font_res += f" /F4 {f4} 0 R"
            diffs = " ".join(f"/{n}" for n in DIFF_NAMES)
            objs[f4] = (f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /FirstChar 32 /LastChar 126 /Widths [{widths}] "
                        f"/Encoding << /Type /Encoding /BaseEncoding /WinAnsiEncoding /Differences [127 {diffs}] >> >>").encode()
        page_nums: List[int] = []
        for page in self.pages:
            form_names: Dict[int, str] = {}
            xobj = ""
            for i, ops in enumerate(page.forms, 1):
                n = alloc()
                form_names[i] = f"Fm{i}"
                xobj += f"/Fm{i} {n} 0 R "
                objs[n] = stream(self._ops_stream(ops), f"/Type /XObject /Subtype /Form /BBox [0 0 595 842] /Matrix [1 0 0 1 0 0] /Resources << /Font << {font_res} >> >> ")
            body = self._ops_stream(page.ops, form_names)
            content = alloc()
            if self.flipped:
                objs[content] = stream(b"q 1 0 0 -1 0 842 cm\n" + body + b"\nQ")
            else:
                objs[content] = stream(body)
            pn = alloc()
            page_nums.append(pn)
            res = f"/Font << {font_res} >>" + (f" /XObject << {xobj}>>" if xobj else "")
            objs[pn] = f"<< /Type /Page /Parent {pages_n} 0 R /MediaBox [0 0 595 842] /Contents {content} 0 R /Resources << {res} >> >>".encode()
        objs[cat] = f"<< /Type /Catalog /Pages {pages_n} 0 R >>".encode()
        kids = " ".join(f"{n} 0 R" for n in page_nums)
        objs[pages_n] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_nums)} >>".encode()
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: Dict[int, int] = {}
        for num in sorted(objs):
            offsets[num] = len(out)
            out += f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
        for num in sorted(objs):
            out += f"{offsets[num]:010d} 00000 n \n".encode()
        out += f"trailer\n<< /Size {len(objs) + 1} /Root {cat} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        return bytes(out)


def _utf16(ch: str) -> List[int]:
    b = ch.encode("utf-16-be")
    return [int.from_bytes(b[i:i + 2], "big") for i in range(0, len(b), 2)]


# =====================================================================
# A small DOCX writer
# =====================================================================
def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def d_par(text: str, size: Optional[int] = None, bold: bool = False, tab_after: Optional[str] = None, sym_bullet: bool = False) -> str:
    """A paragraph. size is in half points (20 = 10 pt). tab_after is text that follows a tab (a date on the right)."""
    rpr = ""
    if size or bold:
        rpr = "<w:rPr>" + ("<w:b/>" if bold else "") + (f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else "") + "</w:rPr>"
    runs = ""
    if sym_bullet:
        runs += '<w:r><w:sym w:font="Symbol" w:char="F0B7"/></w:r><w:r><w:tab/></w:r>'
    runs += f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'
    if tab_after:
        runs += f'<w:r><w:tab/></w:r><w:r>{rpr}<w:t xml:space="preserve">{_esc(tab_after)}</w:t></w:r>'
    return f"<w:p>{runs}</w:p>"


def d_table(cells: List[List[str]]) -> str:
    """One row. cells: a list of cells, each a list of paragraph xml strings."""
    tcs = "".join("<w:tc><w:tcPr><w:tcW w:w=\"4000\" w:type=\"dxa\"/></w:tcPr>" + ("".join(c) or "<w:p/>") + "</w:tc>" for c in cells)
    return f"<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tr>{tcs}</w:tr></w:tbl>"


def d_textbox(paragraphs: List[str]) -> str:
    """A text box. Word stores it twice: for new Word (Choice) and for old Word (Fallback)."""
    inner = "".join(paragraphs)
    return ('<w:p><w:r><mc:AlternateContent><mc:Choice Requires="wps"><w:drawing><wp:anchor><a:graphic><a:graphicData><wps:wsp><wps:txbx>'
            f"<w:txbxContent>{inner}</w:txbxContent></wps:txbx></wps:wsp></a:graphicData></a:graphic></wp:anchor></w:drawing></mc:Choice>"
            f'<mc:Fallback><w:pict><v:shape><v:textbox><w:txbxContent>{inner}</w:txbxContent></v:textbox></v:shape></w:pict></mc:Fallback>'
            "</mc:AlternateContent></w:r></w:p>")


def make_docx(body: List[str], header: Optional[List[str]] = None) -> bytes:
    ns = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:v="urn:schemas-microsoft-com:vml"')
    sect = '<w:sectPr>' + ('<w:headerReference w:type="default" r:id="rId2"/>' if header else "") + '<w:pgSz w:w="11906" w:h="16838"/></w:sectPr>'
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {ns}><w:body>{"".join(body)}{sect}</w:body></w:document>'
    types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
             + ('<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>' if header else "")
             + "</Types>")
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + ('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>' if header else "")
                + "</Relationships>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        def put(name: str, data: str) -> None:
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        put("[Content_Types].xml", types)
        put("_rels/.rels", rels)
        put("word/_rels/document.xml.rels", doc_rels)
        put("word/document.xml", document)
        if header:
            put("word/header1.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {ns}>{"".join(header)}</w:hdr>')
    return buf.getvalue()


# =====================================================================
# The people: the true positions (so that the expected years are computed, not typed)
# =====================================================================
Ym = Tuple[int, int]


def true_years(spans: List[Tuple[Ym, Optional[Ym]]]) -> float:
    """The years of work in the union of the spans, up to AS_OF. A span is (start (year, month), end (year, month) or None for "now")."""
    now = AS_OF.year + (AS_OF.month - 1) / 12.0 + AS_OF.day / 365.0
    pts = []
    for (sy, sm), end in spans:
        a = sy + (sm - 1) / 12.0
        b = now if end is None else end[0] + end[1] / 12.0
        pts.append((a, min(b, now)))
    pts.sort()
    total, cur_a, cur_b = 0.0, pts[0][0], pts[0][1]
    for a, b in pts[1:]:
        if a <= cur_b:
            cur_b = max(cur_b, b)
        else:
            total += cur_b - cur_a
            cur_a, cur_b = a, b
    return round(total + cur_b - cur_a, 1)


# =====================================================================
# A single-column page layout (for the CVs that are one column)
# =====================================================================
def N(text: str, size: float = 10, bold: bool = False, before: float = 0, x: float = 0, how: str = "tj") -> Dict[str, Any]:
    return dict(t=text, size=size, bold=bold, before=before, x=x, how=how)


def H(text: str) -> Dict[str, Any]:
    return dict(t=text, size=11, bold=True, before=10, x=0, how="tj")


def B(text: str, ch: str = "•", how: str = "tj") -> Dict[str, Any]:
    return dict(t=text, size=10, bold=False, before=0, x=0, bullet=ch, how=how)


def single_column(pdf: Pdf, items: List[Dict[str, Any]], left: float = 50, top: float = 790, bottom: float = 50) -> None:
    page = pdf.page()
    y = top
    for item in items:
        size = item["size"]
        y -= item["before"] + size * 1.38
        if y < bottom:
            page = pdf.page()
            y = top - size * 1.38
        x = left + item["x"]
        if "bullet" in item:
            page.t(x, y, item["bullet"], size, False)
            page.t(x + 14, y, item["t"], size, item["bold"], item["how"])
        else:
            page.t(x, y, item["t"], size, item["bold"], item["how"])


def column(items: List[Dict[str, Any]], x: float, top: float, size_default: float = 10) -> List[Dict[str, Any]]:
    """Lay out items in a column and return the ops (they are not added to the page: the caller decides the stream order)."""
    ops = []
    y = top
    for item in items:
        size = item.get("size", size_default)
        y -= item.get("before", 0) + size * 1.38
        ix = x + item.get("x", 0)
        if "bullet" in item:
            ops.append(Page.op(ix, y, item["bullet"], size))
            ops.append(Page.op(ix + 12, y, item["t"], size, item.get("bold", False), item.get("how", "tj")))
        else:
            ops.append(Page.op(ix, y, item["t"], size, item.get("bold", False), item.get("how", "tj")))
    return ops


def emit(page: Page, ops: List[Dict[str, Any]]) -> None:
    for op in ops:
        page.t(op["x"], op["y"], op["text"], op["size"], op["bold"], op["how"])


# =====================================================================
# The fixtures
# =====================================================================
FIXTURES: List[Dict[str, Any]] = []     # each: name, data (bytes), expected (dict), layout (text)


def add(name: str, data: bytes, layout: str, **expected: Any) -> None:
    exp = dict(currentRole=None, level=None, targetRole=None, statesTarget=False, yearsExperience=None, certifications=[], awards=[], skills=[], skillLevels={})
    exp.update(expected)
    FIXTURES.append(dict(name=name, data=data, layout=layout, expected=exp))


def aw(name: str, kind: str, year: Optional[int]) -> Dict[str, Any]:
    return dict(name=name, kind=kind, year=year)


def f01() -> None:
    pdf = Pdf()
    spans = [((2021, 1), None), ((2018, 3), (2020, 12)), ((2016, 2), (2018, 2))]
    items = [
        N("ALEX TESTWOOD", 20, True), N("Sydney, NSW | alex.testwood@example.test | +61 400 000 001 | linkedin.com/in/alex-testwood-example", 9),
        H("PROFESSIONAL SUMMARY"),
        N("Senior data engineer with 10 years of experience building batch and streaming pipelines on AWS."),
        N("Strong in Python, SQL and Apache Spark. Mentors junior engineers and leads the delivery of data products."),
        H("EXPERIENCE"),
        N("Senior Data Engineer | Northwind Analytics Pty Ltd | Jan 2021 – Present", bold=True, before=3),
        B("Built an Apache Spark and Apache Airflow platform that processes 2 TB of events each day."),
        B("Cut the cost of the warehouse by 31% by moving to Snowflake and partitioning large tables."),
        B("Mentored 4 junior engineers and ran weekly design reviews."),
        N("Data Engineer | Bluegum Software Pty Ltd | Mar 2018 – Dec 2020", bold=True, before=6),
        B("Wrote Python ETL jobs and SQL models for the finance reports."),
        B("Moved the nightly batch jobs to Apache Airflow on AWS."),
        N("Data Analyst | Wattle & Co | Feb 2016 – Feb 2018", bold=True, before=6),
        B("Built Tableau dashboards for 12 sales teams."),
        H("EDUCATION"), N("Bachelor of Science (Computer Science), University of Westbank, 2012 – 2015"),
        H("SKILLS"), N("Python (8 yrs), SQL (8 yrs), Apache Spark, Apache Airflow, Snowflake, AWS, Docker, Terraform, Tableau"),
        H("CERTIFICATIONS"),
        N("AWS Certified Data Engineer - Associate | Amazon Web Services | 2023"),
        N("Databricks Certified Data Engineer Associate | Databricks | 2022"),
    ]
    single_column(pdf, items)
    add("cv01_single_classic.pdf", pdf.build(), "One column. Header with name and contact line. Caps headings. Job lines 'Title | Company | Mon YYYY – Present'. Bullets. Skills with years.",
        currentRole="Senior Data Engineer", level="Senior", yearsExperience=true_years(spans),
        certifications=["AWS Certified Data Engineer - Associate", "Databricks Certified Data Engineer Associate"],
        skills=["Python", "SQL", "Apache Spark", "Apache Airflow", "Snowflake", "Docker", "Terraform"], skillLevels={"Python": 5, "SQL": 5})


def f02() -> None:
    pdf = Pdf(compress=True)
    spans = [((2022, 3), None), ((2019, 6), (2022, 2))]
    page = pdf.page()
    page.t(40, 790, "MIRA SAMPLE", 24, True)
    page.t(40, 766, "Machine Learning Engineer", 13)
    page.t(40, 750, "Melbourne, VIC | mira.sample@example.test | +61 400 000 002", 9)
    left = [
        dict(t="SKILLS", size=11, bold=True), dict(t="Python"), dict(t="PyTorch"), dict(t="TensorFlow"), dict(t="scikit-learn"), dict(t="Docker"), dict(t="MLflow"),
        dict(t="Amazon SageMaker"), dict(t="SQL"),
        dict(t="CERTIFICATIONS", size=11, bold=True, before=12), dict(t="Google Cloud Professional"), dict(t="Machine Learning Engineer, 2024"),
        dict(t="AWARDS", size=11, bold=True, before=12), dict(t="1st place, AI Hackathon 2023"),
        dict(t="LANGUAGES", size=11, bold=True, before=12), dict(t="English, Vietnamese"),
    ]
    right = [
        dict(t="PROFILE", size=11, bold=True),
        dict(t="Machine learning engineer who ships NLP and ranking models. Looking for a Senior MLOps"), dict(t="Engineer role where I can run models in production."),
        dict(t="EXPERIENCE", size=11, bold=True, before=12),
        dict(t="Machine Learning Engineer — Fernhill Systems", bold=True), dict(t="03/2022 – Present"),
        dict(t="Built a ranking model that raised click-through by 9%.", bullet="•"), dict(t="Moved training to Amazon SageMaker with MLflow tracking.", bullet="•"),
        dict(t="Data Scientist — Quokka Labs", bold=True, before=6), dict(t="06/2019 – 02/2022"),
        dict(t="Forecast demand for 3,000 products with PyTorch and SQL.", bullet="•"),
        dict(t="EDUCATION", size=11, bold=True, before=12), dict(t="Master of Data Science, University of Westbank, 2017 – 2019"),
    ]
    lops = column(left, 40, 730)
    rops = column(right, 240, 730)
    for a, b in zip(lops + [None] * 40, rops + [None] * 40):      # the stream alternates a left line and a right line
        if a:
            emit(page, [a])
        if b:
            emit(page, [b])
    add("cv02_two_column_interleaved.pdf", pdf.build(), "Full-width header (name, title, contact). Then two columns. The stream alternates a left line and a right line, so the text of the columns is mixed in file order.",
        currentRole="Machine Learning Engineer", level="Senior", targetRole="MLOps Engineer", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["Google Cloud Professional Machine Learning Engineer"], awards=[aw("1st place, AI Hackathon", "hackathon", 2023)],
        skills=["Python", "PyTorch", "TensorFlow", "scikit-learn", "Docker", "MLflow", "Amazon SageMaker", "SQL"])


def f03() -> None:
    pdf = Pdf()
    spans = [((2023, 8), None), ((2022, 1), (2023, 7))]
    page = pdf.page()
    side = [
        dict(t="CONTACT", size=11, bold=True), dict(t="Melbourne, VIC"), dict(t="sofia.example@example.test"), dict(t="+61 400 000 003"),
        dict(t="SKILLS", size=11, bold=True, before=14), dict(t="JavaScript"), dict(t="TypeScript"), dict(t="React"), dict(t="Node.js"), dict(t="PostgreSQL"), dict(t="Docker"),
        dict(t="EDUCATION", size=11, bold=True, before=14), dict(t="Bachelor of Software"), dict(t="Engineering"), dict(t="University of Westbank"), dict(t="2017 – 2020"),
    ]
    main = [
        dict(t="SOFIA EXAMPLE", size=24, bold=True), dict(t="Full Stack Developer", size=13),
        dict(t="PROFILE", size=11, bold=True, before=12),
        dict(t="Full stack developer who builds web apps with React, Node.js and PostgreSQL."), dict(t="I like small teams that ship every week."),
        dict(t="WORK EXPERIENCE", size=11, bold=True, before=12),
        dict(t="Full Stack Developer | Tidewater Digital | Aug 2023 – Present", bold=True),
        dict(t="Built a booking app in React and Node.js used by 40 clinics.", bullet="•"), dict(t="Cut page load time by 45% with caching in Redis.", bullet="•"),
        dict(t="Junior Web Developer | Marlin Cloud Pty Ltd | Jan 2022 – Jul 2023", bold=True, before=6),
        dict(t="Wrote REST APIs in Node.js and tests in Jest.", bullet="•"),
    ]
    emit(page, column(side, 30, 790))        # the sidebar is written first
    emit(page, column(main, 210, 790))
    add("cv03_sidebar_first.pdf", pdf.build(), "Narrow sidebar on the left (contact, skills, education) is written first in the file. The name is in the wide right column.",
        currentRole="Full Stack Developer", level="Mid", yearsExperience=true_years(spans), skills=["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "Docker"])


def f04() -> None:
    pdf = Pdf()
    spans = [((2024, 3), None), ((2022, 2), (2024, 2))]
    items = [
        N("KENJI EXAMPLE | Software Engineer", 16, True), N("Brisbane, QLD · kenji.example@example.test · +61 400 000 004", 9),
        H("CAREER OBJECTIVE"),
        N("Seeking a Site Reliability Engineer position where I can improve system reliability and automate operations."),
        H("EXPERIENCE"),
        N("Software Engineer, Redfern Data Co, Brisbane — 2024 – to date", bold=True, before=3),
        B("Ran the on-call rota for 12 services and cut incidents by 35%."), B("Wrote Terraform modules and Prometheus alerts."),
        N("Junior Developer, Kestrel Analytics, Brisbane — 2022 – 2024", bold=True, before=6),
        B("Built internal tools in Python and Go."),
        H("EDUCATION"), N("Bachelor of Information Technology, University of Westbank, 2018 – 2021"),
        H("SKILLS"), N("Python, Go, Kubernetes, Terraform, Prometheus, Linux"),
    ]
    single_column(pdf, items)
    add("cv04_header_pipe_objective.pdf", pdf.build(), "Name and title on one line separated by '|'. 'Career objective' says 'Seeking a ... position'. Dates end with 'to date'. Years only.",
        currentRole="Software Engineer", level="Mid", targetRole="Site Reliability Engineer", statesTarget=True, yearsExperience=true_years(spans),
        skills=["Python", "Go", "Kubernetes", "Terraform", "Prometheus", "Linux"])


def f05() -> None:
    pdf = Pdf(compress=True)
    spans = [((2024, 3), None), ((2022, 7), (2024, 2))]
    items = [
        N("DATA SCIENTIST", 11, True, how="kern"), N("Nguyễn Minh Anh", 22, True), N("Hà Nội · minhanh.example@example.test · +84 90 000 0005", 9),
        H("PROFILE"),
        N("Focused on demand forecasting and natural language processing. Open to Machine Learning Engineer roles"), N("in Sydney or Melbourne."),
        H("EXPERIENCE"),
        N("Lyrebird AI, Hà Nội", bold=True, before=3, ), N("2024 – Present"),
        B("Forecast demand for 800 stores with Python and scikit-learn."), B("Built a Vietnamese text classifier with PyTorch."),
        N("Banksia Health Tech, Hà Nội", bold=True, before=6), N("2022 – 2024"),
        B("Cleaned and joined clinic data with SQL and Pandas."),
        H("EDUCATION"), N("Bachelor of Statistics, Đại học Westbank, 2018 – 2022"),
        H("CERTIFICATIONS"),
        N("Machine Learning Specialization — DeepLearning.AI and Stanford Online (2023)"),
        N("Microsoft Certified: Azure Data Scientist Associate (DP-100), 2024"),
    ]
    single_column(pdf, items)
    add("cv05_title_above_name_vi.pdf", pdf.build(), "The title 'DATA SCIENTIST' is ABOVE the name. Vietnamese name and place with diacritics (Type0 font). The jobs list the employer and dates but no title. 'Open to ... roles'.",
        currentRole="Data Scientist", level="Mid", targetRole="Machine Learning Engineer", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["Machine Learning Specialization", "Microsoft Certified: Azure Data Scientist Associate"],
        skills=["Python", "scikit-learn", "PyTorch", "SQL", "Pandas"])


def f06() -> None:
    pdf = Pdf()
    spans = [((2020, 3), None), ((2017, 8), (2020, 2))]
    items = [
        N("PRIYA NAIRN", 20, True), N("SENIOR FRONTEND ENGINEER", 12, True), N("Perth, WA ▪ priya.nairn@example.test ▪ +61 400 000 006", 9),
        H("SUMMARY"), N("Frontend engineer who cares about accessibility and fast pages."),
        H("EXPERIENCE"),
        N("SENIOR FRONTEND ENGINEER – FERNHILL SYSTEMS (03/2020 – now)", bold=True, before=3),
        B("Led the move of a 200-page app to React and TypeScript.", "▪"), B("Raised the Lighthouse score from 52 to 94.", "▪"),
        N("FRONTEND DEVELOPER – QUOKKA LABS (08/2017 – 02/2020)", bold=True, before=6),
        B("Built a design system used by 6 teams.", "●"), B("Wrote end-to-end tests with Cypress.", "●"),
        H("SKILLS"), N("React ●●●●●"), N("TypeScript ●●●●○"), N("GraphQL ●●●○○"), N("Cypress, Web accessibility"),
        H("AWARDS & HONOURS"), N("– Employee of the Year 2022, Fernhill Systems"),
        H("EDUCATION"), N("– Bachelor of Design Computing, University of Westbank, 2013 – 2016"),
    ]
    single_column(pdf, items)
    add("cv06_caps_bullets_mixed.pdf", pdf.build(), "All-caps headings and all-caps job lines. Bullet glyphs '▪', '●', '–' and '•' (Type0 font). Dates 'MM/YYYY – now'. Skill ratings written with dots.",
        currentRole="Senior Frontend Engineer", level="Senior", yearsExperience=true_years(spans),
        awards=[aw("Employee of the Year", "employer-recognition", 2022)], skills=["React", "TypeScript", "GraphQL", "Cypress"], skillLevels={"React": 5, "TypeScript": 4, "GraphQL": 3})


def f07() -> None:
    pdf = Pdf()
    spans = [((2022, 3), None), ((2019, 6), (2022, 2))]
    page = pdf.page()
    side = [
        dict(t="Contact", size=11, bold=True), dict(t="www.linkedin.com/in/"), dict(t="lena-placeholder-example"), dict(t="(LinkedIn)"),
        dict(t="Top Skills", size=11, bold=True, before=12), dict(t="Natural Language Processing"), dict(t="PyTorch"), dict(t="MLOps"),
        dict(t="Languages", size=11, bold=True, before=12), dict(t="English (Native or Bilingual)"), dict(t="German (Limited Working)"),
        dict(t="Certifications", size=11, bold=True, before=12), dict(t="Machine Learning Specialization"), dict(t="Certified Kubernetes Administrator"), dict(t="(CKA)"),
        dict(t="Honors-Awards", size=11, bold=True, before=12), dict(t="Regional Hackathon Winner"), dict(t="Best Paper, Applied AI Workshop"),
    ]
    main = [
        dict(t="Lena Placeholder", size=24, bold=True),
        dict(t="Lead Machine Learning Engineer at Fernhill Systems | NLP | MLOps", size=11),
        dict(t="Sydney, New South Wales, Australia", size=10),
        dict(t="Summary", size=13, bold=True, before=14),
        dict(t="I build NLP and recommendation systems for retail. Open to AI Research Scientist roles."),
        dict(t="Experience", size=13, bold=True, before=14),
        dict(t="Fernhill Systems", bold=True), dict(t="4 years 7 months"),
        dict(t="Lead Machine Learning Engineer"), dict(t="March 2024 - Present (2 years 7 months)"),
        dict(t="Sydney, New South Wales, Australia"),
        dict(t="Machine Learning Engineer", before=4), dict(t="March 2022 - February 2024 (2 years)"),
        dict(t="Quokka Labs", bold=True, before=8), dict(t="Data Scientist"), dict(t="June 2019 - February 2022 (2 years 9 months)"),
        dict(t="Melbourne, Victoria, Australia"),
        dict(t="Education", size=13, bold=True, before=14),
        dict(t="University of Westbank", bold=True), dict(t="Master of Science - MS, Computer Science · (2017 - 2019)"),
    ]
    emit(page, column(side, 30, 790))        # LinkedIn writes the sidebar first
    emit(page, column(main, 230, 790))
    add("cv07_linkedin_export.pdf", pdf.build(), "LinkedIn-style export: sidebar with Contact, Top Skills, Certifications, Honors-Awards is written first. Main column: name, headline 'Title at Company | ...', Summary, Experience in the order company / title / dates, two roles in one company.",
        currentRole="Lead Machine Learning Engineer", level="Lead", targetRole="AI Research Scientist", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["Machine Learning Specialization", "Certified Kubernetes Administrator"],
        awards=[aw("Regional Hackathon Winner", "hackathon", None), aw("Best Paper, Applied AI Workshop", "conference-talk", None)],
        skills=["Natural language processing", "PyTorch", "MLOps"])


def f08() -> None:
    pdf = Pdf()
    spans = [((2022, 3), None), ((2019, 9), (2022, 2))]
    items = [
        N("Curriculum Vitae", 9), N("Tomas Example", 22, True), N("Brisbane, Australia   tomas.example@example.test   Mobile +61 400 000 008", 9),
        N("JOB APPLIED FOR", 9, True, before=8), N("Backend Engineer", 12),
        H("WORK EXPERIENCE"),
        N("01/03/2022 – Present   Software Engineer", bold=True, before=3), N("Marlin Cloud Pty Ltd, Brisbane (Australia)"),
        B("Designed REST APIs in Java and Spring Boot for a payments product.", "▪"), B("Wrote integration tests and ran the CI/CD pipeline in GitLab.", "▪"),
        N("Business or sector Information and communication", 9),
        N("01/09/2019 – 28/02/2022   Junior Software Developer", bold=True, before=6), N("Tidewater Digital, Brisbane (Australia)"),
        B("Fixed bugs and added features to a Java web shop.", "▪"),
        H("EDUCATION AND TRAINING"), N("01/09/2015 – 30/06/2019   Bachelor of Information Technology   Level 6 EQF", bold=True), N("University of Westbank, Brisbane (Australia)"),
        H("PERSONAL SKILLS"), N("Mother tongue(s): English"), N("Job-related skills: Java, Spring Boot, PostgreSQL, Git, CI/CD, Docker"),
    ]
    single_column(pdf, items)
    add("cv08_europass_like.pdf", pdf.build(), "Europass-like: 'JOB APPLIED FOR' label with a role. Work experience lines start with the date range 'DD/MM/YYYY – Present' and then the title. Employer on the next line. Label 'Job-related skills'.",
        currentRole="Software Engineer", level="Senior", targetRole="Backend Engineer", statesTarget=True, yearsExperience=true_years(spans),
        skills=["Java", "Spring Boot", "PostgreSQL", "Git", "CI/CD", "Docker"])


def f09() -> None:
    spans = [((2025, 2), None), ((2024, 6), (2024, 12))]
    body = [
        d_par("NOOR TESTFIELD", 44, True), d_par("Graduate Software Developer", 26),
        d_par("Adelaide, SA | noor.testfield@example.test | +61 400 000 009", 18),
        d_par("PROFILE", 24, True), d_par("Graduate developer who likes clean code and small pull requests. I aspire to grow into a Software Engineer role that works on cloud products."),
        d_par("EXPERIENCE", 24, True),
        d_par("Graduate Software Developer, Banksia Health Tech", 22, True, tab_after="Feb 2025 – Present"),
        d_par("Built features for a patient portal in Java and React.", sym_bullet=True), d_par("Wrote unit tests with JUnit.", sym_bullet=True),
        d_par("Software Engineering Intern, Lyrebird AI", 22, True, tab_after="Jun 2024 – Dec 2024"),
        d_par("Added tests to a Python data library.", sym_bullet=True),
        d_par("EDUCATION", 24, True), d_par("Bachelor of Information Technology, University of Westbank, 2021 – 2024"),
        d_par("SKILLS", 24, True), d_par("Java, React, Python, JUnit, Git"),
    ]
    add("cv09_docx_simple.docx", make_docx(body), "DOCX, one column. Title under the name. Job line with a tab and the date on the right. List bullets are Symbol glyphs. Sentence 'I aspire to grow into a ... role'.",
        currentRole="Graduate Software Developer", level="Junior", targetRole="Software Engineer", statesTarget=True, yearsExperience=true_years(spans),
        skills=["Java", "React", "Python", "JUnit", "Git"])


def f10() -> None:
    spans = [((2024, 7), None), ((2022, 1), (2024, 6))]
    left = [d_par("CONTACT", 22, True), d_par("Perth, WA", 20), d_par("ravi.sampleton@example.test", 20), d_par("SKILLS", 22, True), d_par("SQL", 20), d_par("Power BI", 20), d_par("Tableau", 20),
            d_par("Python", 20), d_par("Microsoft Excel", 20), d_par("CERTIFICATIONS", 22, True), d_par("Microsoft Certified: Power BI Data Analyst Associate (PL-300), 2023", 20)]
    right = [d_par("RAVI SAMPLETON", 52, True), d_par("Data Analyst", 28), d_par("PROFILE", 24, True), d_par("Analyst who turns messy sales data into clear dashboards."),
             d_par("EXPERIENCE", 24, True), d_par("Data Analyst | Wattle & Co | Jul 2024 – Present", 22, True), d_par("Built Power BI reports for 8 regional managers.", sym_bullet=True),
             d_par("Reporting Analyst | Bluegum Software Pty Ltd | Jan 2022 – Jun 2024", 22, True), d_par("Wrote SQL views and refreshed Tableau extracts each night.", sym_bullet=True),
             d_par("EDUCATION", 24, True), d_par("Bachelor of Commerce (Information Systems), University of Westbank, 2018 – 2021")]
    body = [d_table([left, right])]
    add("cv10_docx_table_two_column.docx", make_docx(body), "DOCX two-column layout made with a table. The left cell (small text: contact, skills, certifications) comes first in the file. The name is in the right cell with the big font.",
        currentRole="Data Analyst", level="Mid", yearsExperience=true_years(spans),
        certifications=["Microsoft Certified: Power BI Data Analyst Associate"], skills=["SQL", "Power BI", "Tableau", "Python", "Microsoft Excel"])


def f11() -> None:
    spans = [((2020, 9), None), ((2018, 1), (2020, 8))]
    header = [d_par("HANA PLACEHOLDER", 40, True), d_par("Sr. Cloud Engineer", 26)]
    body = [
        d_textbox([d_par("Sydney, NSW", 18), d_par("hana.placeholder@example.test", 18), d_par("+61 400 000 011", 18)]),
        d_par("SUMMARY", 24, True), d_par("Cloud engineer who designs secure AWS landing zones. Seeking a Solutions Architect role in a product company."),
        d_par("EXPERIENCE", 24, True),
        d_par("Sr. Cloud Engineer — Marlin Cloud Pty Ltd — Sep 2020 – Present", 22, True), d_par("Designed a multi-account AWS setup with Terraform for 14 teams.", sym_bullet=True),
        d_par("Cloud Engineer — Tidewater Digital — Jan 2018 – Aug 2020", 22, True), d_par("Moved 30 services to Kubernetes on AWS.", sym_bullet=True),
        d_par("CERTIFICATIONS", 24, True), d_par("AWS Certified Solutions Architect - Associate (2021)"), d_par("HashiCorp Certified: Terraform Associate (2022)"),
        d_par("SKILLS", 24, True), d_par("AWS, Terraform, Kubernetes, Docker, Linux, Python"),
    ]
    add("cv11_docx_textbox_header.docx", make_docx(body, header), "DOCX where the name and the title are in the page HEADER part, and the contact details are in a TEXT BOX that Word stores twice (Choice and Fallback). Title with the abbreviation 'Sr.'.",
        currentRole="Sr. Cloud Engineer", level="Senior", targetRole="Solutions Architect", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["AWS Certified Solutions Architect - Associate", "HashiCorp Certified: Terraform Associate"], skills=["AWS", "Terraform", "Kubernetes", "Docker", "Linux", "Python"])


def f12() -> None:
    pdf = Pdf()
    spans = [((2025, 11), (2026, 2)), ((2025, 2), (2025, 6))]
    items = [
        N("MEI STUDENT", 20, True), N("Computer science student | Sydney | mei.student@example.test | +61 400 000 012", 9),
        H("OBJECTIVE"), N("Looking for a graduate Software Engineer role that starts in 2027."),
        H("EXPERIENCE"),
        N("Software Engineering Intern | Lyrebird AI | Nov 2025 – Feb 2026", bold=True, before=3), B("Added an export feature to a React dashboard."), B("Wrote 40 unit tests in Jest."),
        N("Teaching Assistant | University of Westbank | Feb 2025 – Jun 2025", bold=True, before=6), B("Helped 60 first-year students with Python exercises."),
        H("EDUCATION"), N("Bachelor of Computer Science (expected 2027), University of Westbank, 2024 – 2027"),
        H("AWARDS"), N("Dean's List 2024"), N("Winner, University Hackathon 2025"),
        H("CERTIFICATIONS"), N("AWS Certified Cloud Practitioner (2025)"),
        H("SKILLS"), N("Python, JavaScript, React, Git, SQL"),
    ]
    single_column(pdf, items)
    add("cv12_student_intern.pdf", pdf.build(), "Student CV. Current role is an internship that ended (latest end date). Objective: 'Looking for a graduate ... role'. Awards and a certification.",
        currentRole="Software Engineering Intern", level="Intern", targetRole="Software Engineer", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["AWS Certified Cloud Practitioner"], awards=[aw("Dean's List", "academic-excellence", 2024), aw("Winner, University Hackathon", "hackathon", 2025)],
        skills=["Python", "JavaScript", "React", "Git", "SQL"])


def f13() -> None:
    pdf = Pdf()
    spans = [((2020, 6), None), ((2015, 6), (2020, 5))]
    items = [
        N("OMAR SAMPLETON", 20, True), N("Data Platform Technical Lead", 12), N("Canberra, ACT | omar.sampleton@example.test | +61 400 000 013", 9),
        H("SUMMARY"), N("Technical lead who has worked on lakehouse platforms for 11 years."),
        H("EXPERIENCE"),
        N("Data Platform Technical Lead | Kestrel Analytics | 2020 – Present", bold=True, before=3),
        B("Looking after a team of 5 engineers and 2 analysts."), B("Moved 300 tables to Delta Lake on Databricks."), B("Set the roadmap and the on-call rules for the platform."),
        N("Senior Data Engineer | Redfern Data Co | 2015 – 2020", bold=True, before=6), B("Built Apache Kafka streams for 20 million events a day."),
        H("AWARDS"), N("Excellence in Delivery Award, Kestrel Analytics, 2023"), N("Speaker, Data Engineering Summit, 2024"), N("Top 10, National Forecasting Challenge, 2022"),
        H("CERTIFICATIONS"), N("Certified Kubernetes Administrator (CKA) — 2021"),
        H("SKILLS"), N("Databricks, Apache Kafka, Apache Spark, Python, SQL, Terraform"),
        N("Looking forward to hearing from you.", before=10),
    ]
    single_column(pdf, items)
    add("cv13_no_target_awards.pdf", pdf.build(), "No wish for a job. Words 'Looking after a team' and 'Looking forward to hearing from you' must NOT give a target role. Awards section with three kinds. Lead by title.",
        currentRole="Data Platform Technical Lead", level="Lead", yearsExperience=true_years(spans), certifications=["Certified Kubernetes Administrator"],
        awards=[aw("Excellence in Delivery Award", "employer-recognition", 2023), aw("Speaker, Data Engineering Summit", "conference-talk", 2024), aw("Top 10, National Forecasting Challenge", "data-science-competition", 2022)],
        skills=["Databricks", "Apache Kafka", "Apache Spark", "Python", "SQL", "Terraform"])


def f14() -> None:
    pdf = Pdf(compress=True)
    spans = [((2019, 7), None), ((2013, 3), (2019, 6)), ((2010, 7), (2013, 2))]
    items = [
        N("DR ELENA PLACEHOLDER", 20, True), N("Principal Applied Scientist", 12), N("Sydney, NSW | elena.placeholder@example.test | +61 400 000 014", 9),
        H("PROFILE"), N("Scientist who leads applied research on language models. Open to Head of AI roles."),
        H("EXPERIENCE"),
        N("Principal Applied Scientist | Fernhill Systems | 2019 – Present", bold=True, before=3), B("Lead 12 scientists and engineers across three products."), B("Cut the cost of model serving by 40%."),
        N("Senior Research Scientist | Lyrebird AI | 2013 – 2019", bold=True, before=6), B("Published 9 papers on text ranking."),
        N("Research Engineer | University of Westbank | 2010 – 2013", bold=True, before=6),
        H("EDUCATION"), N("PhD in Computer Science, University of Westbank, 2006 – 2010"),
        H("HONOURS AND AWARDS"), N("Best Paper Award, Applied AI Workshop, 2023"), N("Patent Filed: Low-latency Model Serving Method, 2025"),
        H("SKILLS"), N("PyTorch, Natural language processing, Python, Distributed training, MLflow"),
    ]
    single_column(pdf, items)
    add("cv14_principal.pdf", pdf.build(), "Principal level from the title word. 'Open to Head of AI roles' names a role that is not in the role list: the reader must leave the target empty.",
        currentRole="Principal Applied Scientist", level="Principal", yearsExperience=true_years(spans),
        awards=[aw("Best Paper Award, Applied AI Workshop", "conference-talk", 2023), aw("Patent Filed: Low-latency Model Serving Method", "patent", 2025)],
        skills=["PyTorch", "Python", "MLflow"])


def f15() -> None:
    pdf = Pdf()
    spans = [((2018, 2), (2020, 3)), ((2020, 4), (2023, 8)), ((2023, 9), None)]
    items = [
        N("CHRIS FIXTURE", 20, True), N("Adelaide, SA | chris.fixture@example.test | +61 400 000 015", 9),
        H("EXPERIENCE (OLDEST FIRST)"),
        N("Graduate Developer | Quokka Labs | Feb 2018 – Mar 2020", bold=True, before=3), B("Built forms and reports in C# and SQL Server."),
        N("Software Engineer | Marlin Cloud Pty Ltd | Apr 2020 – Aug 2023", bold=True, before=6), B("Moved a monolith to .NET microservices."),
        N("Senior Software Engineer | Fernhill Systems | Sep 2023 – Present", bold=True, before=6), B("Lead the design of an event-driven billing service."),
        H("EDUCATION"), N("Bachelor of Engineering (Software), University of Westbank, 2014 – 2017"),
        H("SKILLS"), N("C#, .NET, SQL, Docker, Azure"),
    ]
    single_column(pdf, items)
    add("cv15_oldest_first.pdf", pdf.build(), "Jobs are listed from the oldest to the newest. The current job (Present) is the LAST one.",
        currentRole="Senior Software Engineer", level="Senior", yearsExperience=true_years(spans), skills=["C#", ".NET", "SQL", "Docker", "Azure"])


def f16() -> None:
    pdf = Pdf()
    spans = [((2022, 1), None), ((2019, 7), (2021, 12))]
    page = pdf.page()
    pua = "\uf0b7"
    rows = [
        (50, 790, "DANIEL PLACEHOLDER", 20, True, "tj"),
        (50, 768, "Sr Backend Developer", 12, False, "tj"),
        (50, 754, "Hobart, TAS | daniel.placeholder@example.test | +61 400 000 016", 9, False, "tj"),
        (50, 728, "SUMMARY", 11, True, "tj"),
        (50, 713, "Experienced engi-", 10, False, "tj"),
        (50, 700, "neer who builds payment platforms with a focus on ﬁnancial rules and ﬂow control.", 10, False, "tj"),
        (50, 676, "EXPERIENCE", 11, True, "tj"),
        (50, 661, "Sr Backend Developer | Tidewater Digital | Jan 2022 – Present", 10, True, "tj"),
        (50, 646, pua, 10, False, "tj"), (64, 646, "Built a payment platform that handled 4 mil-", 10, False, "words"),
        (64, 633, "lion transactions per day with PostgreSQL and Redis.", 10, False, "words"),
        (50, 620, pua, 10, False, "tj"), (64, 620, "Wrote the ledger service in Go and Kubernetes manifests.", 10, False, "kern"),
        (50, 600, "Backend Developer | Wattle & Co | 2019 – 2021", 10, True, "tj"),
        (50, 585, pua, 10, False, "tj"), (64, 585, "Kept a Java web shop fast and tested.", 10, False, "kern"),
        (50, 560, "CERTIFICATIONS", 11, True, "tj"),
        (50, 545, "Certiﬁed Kubernetes Administrator (CKA)", 10, False, "tj"),
        (50, 520, "SKILLS", 11, True, "tj"),
        (50, 505, "Go, Java, PostgreSQL, Redis, Kubernetes", 10, False, "tj"),
    ]
    for x, y, text, size, bold, how in rows:
        page.t(x, y, text, size, bold, how)
    add("cv16_ligatures_hyphen_pua.pdf", pdf.build(), "Ligature glyphs (ﬁ, ﬂ), bullets that are private-use characters, words cut with a hyphen at the end of a line, words drawn one by one with no space glyph, spaces written as TJ numbers. Title 'Sr Backend Developer'.",
        currentRole="Sr Backend Developer", level="Senior", yearsExperience=true_years(spans), certifications=["Certified Kubernetes Administrator"],
        skills=["Go", "Java", "PostgreSQL", "Redis", "Kubernetes"])


def f17() -> None:
    pdf = Pdf()
    items = [
        N("FATIMA SAMPLETON", 20, True), N("Darwin, NT | fatima.sampleton@example.test | +61 400 000 017", 9),
        H("PROFILE"), N("Data analyst with 6 years of experience in retail analytics and reporting."), N("Interested in moving into Analytics Engineer roles."),
        H("EXPERIENCE"),
        N("Data Analyst, Wattle & Co", bold=True, before=3), B("Built the weekly sales report in SQL and Power BI."), B("Cleaned product data with Python."),
        N("Business Analyst, Bluegum Software Pty Ltd", bold=True, before=6), B("Wrote requirements for a stock system."),
        H("EDUCATION"), N("Bachelor of Commerce, University of Westbank"),
        H("SKILLS"), N("SQL, Power BI, Python, Microsoft Excel, Tableau"),
    ]
    single_column(pdf, items)
    add("cv17_no_dates_statement.pdf", pdf.build(), "No dates at all. The role and the years come from the summary sentence 'Data analyst with 6 years of experience'. 'Interested in moving into ... roles'.",
        currentRole="Data Analyst", level="Senior", targetRole="Analytics Engineer", statesTarget=True, yearsExperience=6.0,
        skills=["SQL", "Power BI", "Python", "Microsoft Excel", "Tableau"])


def f18() -> None:
    pdf = Pdf()
    items = [
        N("LEO BLANK", 20, True), N("Hobart, TAS | leo.blank@example.test | +61 400 000 018", 9),
        H("EDUCATION"), N("Bachelor of Science (Computer Science), University of Westbank, 2012 – 2015"),
        H("SKILLS"), N("Python, SQL, Git"),
    ]
    single_column(pdf, items)
    add("cv18_minimal.pdf", pdf.build(), "Almost empty CV: name, contact, a degree with dates, and three skills. Nothing about jobs. Every field must stay empty (no guess).",
        skills=["Python", "SQL", "Git"])


def f19() -> None:
    spans = [((2024, 8), None), ((2022, 1), (2024, 7))]
    body = [
        d_par("MINA SAMPLER", 44, True), d_par("Brisbane, QLD | mina.sampler@example.test | +61 400 000 019", 18),
        d_par("Profile", 26, True), d_par("Reporting specialist with a focus on clean data models. Open to Analytics Engineer or Data Engineer roles in Brisbane or remote."),
        d_par("Work History", 26, True),
        d_par("Wattle & Co", 22, True), d_par("BI Developer"), d_par("August 2024 - Present"), d_par("Brisbane, Queensland, Australia"),
        d_par("Built a dbt project with 120 models on Snowflake.", sym_bullet=True),
        d_par("Bluegum Software Pty Ltd", 22, True), d_par("Reporting Analyst"), d_par("January 2022 - July 2024"), d_par("Brisbane, Queensland, Australia"),
        d_par("Wrote SQL reports for the finance team.", sym_bullet=True),
        d_par("Education", 26, True), d_par("Bachelor of Business (Analytics), University of Westbank, 2018 – 2021"),
        d_par("Technical Skills", 26, True), d_par("Languages: SQL, Python"), d_par("Tools: dbt, Snowflake, Power BI, Git"),
    ]
    add("cv19_docx_stacked_open_to.docx", make_docx(body), "DOCX. Jobs are stacked: company, title, dates (full month names), place. 'Open to A or B roles': two target roles. Mixed-case headings. Skills with labels.",
        currentRole="BI Developer", level="Mid", targetRole="Analytics Engineer", statesTarget=True, yearsExperience=true_years(spans),
        skills=["SQL", "Python", "dbt", "Snowflake", "Power BI", "Git"])


def f20() -> None:
    pdf = Pdf(flipped=True)
    spans = [((2021, 4), None), ((2017, 6), (2021, 3))]
    page = pdf.page()
    page.form([Page.op(50, 790, "IMANI SAMPLE", 22, True), Page.op(50, 770, "Staff Software Engineer", 13), Page.op(50, 756, "Melbourne, VIC | imani.sample@example.test | +61 400 000 020", 9)])
    items = [
        H("SUMMARY"), N("Engineer who designs reliable distributed systems."),
        H("EXPERIENCE"),
        N("Staff Software Engineer | Fernhill Systems | Apr 2021 – Present", bold=True, before=3), B("Designed the event backbone on Apache Kafka for 9 teams."), B("Set the design review process for 40 engineers."),
        N("Senior Software Engineer | Quokka Labs | Jun 2017 – Mar 2021", bold=True, before=6), B("Built a Go service that handles 5,000 requests per second."),
        H("EDUCATION"), N("Bachelor of Computer Science, University of Westbank, 2012 – 2016"),
        H("SKILLS"), N("Go, Apache Kafka, Kubernetes, PostgreSQL, System design"),
    ]
    y = 730
    for item in items:
        y -= item["before"] + item["size"] * 1.38
        if "bullet" in item:
            page.t(50, y, item["bullet"], item["size"])
            page.t(64, y, item["t"], item["size"])
        else:
            page.t(50, y, item["t"], item["size"], item["bold"])
    add("cv20_flipped_form_header.pdf", pdf.build(), "The page is drawn with a flipped y axis (1 0 0 -1 0 842 cm, like Cairo). The name and the title are in a form XObject. Title 'Staff ...' is the Lead level.",
        currentRole="Staff Software Engineer", level="Lead", yearsExperience=true_years(spans), skills=["Go", "Apache Kafka", "Kubernetes", "PostgreSQL", "System design"])


def f21() -> None:
    pdf = Pdf()
    spans = [((2019, 7), None)]
    items = [
        N("Samir Testcase", 18, True), N("Cairns, QLD · samir.testcase@example.test", 9),
        H("Summary"), N("Backend and data engineer. Currently looking for roles in MLOps."),
        H("Experience"),
        N("Software Engineer at Bluegum Software (2019–2022)", bold=True, before=3), B("Built REST APIs in Python and FastAPI."),
        N("Data Engineer at Northwind Analytics (2022 – Present)", bold=True, before=6), B("Ran Apache Airflow pipelines that load a Snowflake warehouse."),
        H("Technical Skills"), N("Languages: Python, SQL"), N("Cloud: AWS, Google Cloud Platform"), N("Data: Apache Airflow, Snowflake, dbt"),
        H("Education"), N("BSc Information Systems, University of Westbank (2015–2018)"),
    ]
    single_column(pdf, items)
    add("cv21_inline_at_dates.pdf", pdf.build(), "Job lines 'Title at Company (YYYY–YYYY)'. Sentence 'Currently looking for roles in MLOps' names no known role (MLOps alone is a skill, not a role). Skills in 'Label: items' lines.",
        currentRole="Data Engineer", level="Senior", yearsExperience=true_years(spans),
        skills=["Python", "SQL", "AWS", "Google Cloud Platform", "Apache Airflow", "Snowflake", "dbt"])


def f22() -> None:
    pdf = Pdf(diff_encoding=True)
    spans = [((2022, 3), None), ((2019, 6), (2022, 2))]
    page = pdf.page()
    cx = lambda s, size, bold=False: (595 - text_width(s, size, bold)) / 2.0     # noqa: E731
    page.t(cx("YUKI TYPESET", 24, True), 790, "YUKI TYPESET", 24, True, "kern")
    page.t(cx("Machine Learning Engineer", 12), 770, "Machine Learning Engineer", 12, False, "kern")
    page.t(cx("Sydney, Australia – yuki.typeset@example.test – +61 400 000 022", 9), 755, "Sydney, Australia – yuki.typeset@example.test – +61 400 000 022", 9, False, "kern")
    page.t(40, 725, "Experience", 13, True, "kern")
    page.t(40, 705, "2022 – present", 10, False, "kern")
    page.t(150, 705, "Machine Learning Engineer, Fernhill Systems", 10, True, "kern")
    page.t(150, 692, "Sydney, Australia", 9, False, "kern")
    page.t(150, 679, "Trained ranking models with PyTorch and served them with Kubernetes.", 10, False, "kern")
    page.t(40, 655, "2019 – 2022", 10, False, "kern")
    page.t(150, 655, "Data Scientist, Quokka Labs", 10, True, "kern")
    page.t(150, 642, "Melbourne, Australia", 9, False, "kern")
    page.t(150, 629, "Forecast demand with scikit-learn and tracked runs in MLflow.", 10, False, "kern")
    page.t(40, 605, "Education", 13, True, "kern")
    page.t(40, 585, "2017 – 2019", 10, False, "kern")
    page.t(150, 585, "Master of Science in Computer Science, University of Westbank", 10, False, "kern")
    page.t(40, 560, "Honours", 13, True, "kern")
    page.t(40, 540, "2018", 10, False, "kern")
    page.t(150, 540, "Gold medal, ICPC Regional Programming Contest", 10, False, "kern")
    page.t(40, 515, "Skills", 13, True, "kern")
    page.t(150, 515, "Python, PyTorch, scikit-learn, MLflow, Kubernetes, SQL", 10, False, "kern")
    add("cv22_latex_timeline.pdf", pdf.build(), "LaTeX-like (moderncv): centred name and title, a timeline with the DATES in a left column and the text in a right column, spaces as TJ kerning numbers, font with an /Encoding /Differences list (en dash, fi).",
        currentRole="Machine Learning Engineer", level="Senior", yearsExperience=true_years(spans),
        awards=[aw("Gold medal, ICPC Regional Programming Contest", "competitive-programming", 2018)], skills=["Python", "PyTorch", "scikit-learn", "MLflow", "Kubernetes", "SQL"])


def f23() -> None:
    pdf = Pdf()
    spans = [((2025, 1), None)]
    page = pdf.page()
    page.t(40, 790, "ZARA MOCKUP", 22, True)
    page.t(40, 770, "Junior Data Analyst | Python · SQL · Power BI", 12)
    page.t(40, 755, "Sydney, NSW | zara.mockup@example.test | +61 400 000 023", 9)
    left = [
        dict(t="EXPERIENCE", size=11, bold=True),
        dict(t="Junior Data Analyst — Banksia Health Tech", bold=True), dict(t="Jan 2025 – Present"),
        dict(t="Built a Power BI report for 14 clinics.", bullet="•"), dict(t="Wrote SQL to find late payments.", bullet="•"),
        dict(t="Cleaned 5 years of patient visit data.", bullet="•"),
    ]
    right = [
        dict(t="EDUCATION", size=11, bold=True), dict(t="Bachelor of Science (Statistics),"), dict(t="University of Westbank, 2021 – 2024"),
        dict(t="SKILLS", size=11, bold=True, before=12), dict(t="Python, SQL, Power BI, Microsoft Excel"),
        dict(t="CERTIFICATIONS", size=11, bold=True, before=12), dict(t="Microsoft Certified: Azure Fundamentals"), dict(t="(AZ-900), 2025"),
    ]
    lops = column(left, 40, 725)
    rops = column(right, 310, 725)
    emit(page, rops)      # the right column is written first
    emit(page, lops)
    add("cv23_two_equal_columns_right_first.pdf", pdf.build(), "Two equal columns under a full-width header with a headline 'Junior Data Analyst | skills'. The right column (education, skills, certifications) is written first in the file.",
        currentRole="Junior Data Analyst", level="Junior", yearsExperience=true_years(spans), certifications=["Microsoft Certified: Azure Fundamentals"],
        skills=["Python", "SQL", "Power BI", "Microsoft Excel"])


def f24() -> None:
    """One column on two pages, with a band of two columns (CERTIFICATIONS | LANGUAGES) at the end of page 1 that goes on in a band at the top of page 2
    (the left column goes on with the certifications, the right column starts WORK RIGHTS AND AVAILABILITY). The layout of a CV that was found in use:
    a page-wide gutter cannot be found because most lines cross the middle of the page. All people and employers are made up."""
    pdf = Pdf()
    spans = [((2021, 3), None), ((2018, 6), (2021, 2)), ((2018, 1), (2018, 5))]
    p1 = pdf.page()
    p1.t(45, 771, "MAYA TESTBRIDGE", 24, True)
    p1.t(45, 750, "Senior Data Analyst | Power BI, SQL and Python", 11.5, True)
    p1.t(45, 732, "Sydney, NSW | maya.testbridge@example.test | +61 400 000 024 | linkedin.com/in/maya-testbridge-example", 9.4)
    p1.t(45, 698, "PROFILE", 11.5, True)
    for y, line in ((677, "Data analyst with 8 years of experience turning messy operational data into dashboards that managers use every week."),
                    (663, "Strong in SQL, Power BI and Python. Works with finance, retail and health teams to define the numbers and keep them right."),
                    (649, "Seeking a Data Analyst role where I can keep working with clear questions, clean data and honest charts."),
                    (635, "Comfortable with stakeholders, requirements workshops and teaching colleagues how to read a report.")):
        p1.t(45, y, line, 10.2)
    p1.t(45, 609, "EXPERIENCE", 11.5, True)
    jobs = [(588, "Senior Data Analyst, Quokka Insights Pty Ltd", "Mar 2021 – Present",
             ["Own the revenue and churn dashboards in Power BI for 6 business units, used by 200 managers each week.",
              "Rebuilt the monthly forecast in Python and SQL; the error fell from 14% to 6%.",
              "Ran requirements workshops with finance and operations and documented the definitions of 40 measures."]),
            (461, "Data Analyst, Banksia Retail Group", "Jun 2018 – Feb 2021",
             ["Built 25 Tableau and Excel reports for store managers and cut the weekly reporting time from 2 days to 3 hours.",
              "Wrote SQL to reconcile sales and stock between 3 systems and fixed the root causes of mismatches."]),
            (363, "Business Analyst Intern, Wattle Health Demo", "Jan 2018 – May 2018",
             ["Mapped the intake process of 3 clinics and wrote 20 user stories with acceptance criteria."])]
    for y, title, dates, bullets in jobs:
        p1.t(45, y, title, 10.2, True)
        p1.t(471, y, dates, 10.2)
        for k, b in enumerate(bullets):
            p1.t(58, y - 16 * (k + 1), "• " + b, 10.2)
    p1.t(45, 306, "EDUCATION", 11.5, True)
    p1.t(45, 285, "Bachelor of Information Systems, University of Westbank", 10.2)
    p1.t(500, 285, "2014 – 2017", 10.2)
    p1.t(45, 229, "SKILLS", 11.5, True)
    p1.t(45, 208, "Analytics and BI: SQL, Power BI, Tableau, Excel (advanced), Data visualisation, Dashboard design", 10.2)
    p1.t(45, 194, "Programming and tools: Python (pandas, NumPy), Git, Jira, ETL pipelines, Data modelling, Data quality", 10.2)
    p1.t(45, 177, "Professional skills: Stakeholder management, Requirements gathering, Problem solving, Presentation", 10.2)
    # the band of two columns at the bottom of page 1
    p1.t(45, 105, "CERTIFICATIONS", 11.5, True)
    p1.t(306, 105, "LANGUAGES", 11.5, True)
    p1.t(58, 84, "Microsoft Certified: Azure Data Scientist", 10.2)
    p1.t(320, 84, "English - native speaker", 10.2)
    p1.t(58, 70, "Associate (DP-100), 2024", 10.2)
    p1.t(320, 70, "Spanish - professional working proficiency", 10.2)
    # page 2: the band goes on, then one column again
    p2 = pdf.page()
    p2.t(58, 786, "Northwind Analytics Professional Certificate,", 10.2)
    p2.t(306, 786, "WORK RIGHTS AND AVAILABILITY", 11.5, True)
    p2.t(58, 771, "2022", 10.2)
    p2.t(320, 763, "Full work rights in Australia; no sponsorship needed", 10.2)
    p2.t(58, 756, "Short course: Intro to Statistics, 2021", 10.2)
    p2.t(320, 747, "Available with one month of notice", 10.2)
    p2.t(320, 732, "Open to remote and hybrid roles", 10.2)
    p2.t(45, 705, "PROJECTS", 11.5, True)
    p2.t(58, 684, "• Public transport delay explorer: joined timetable and real-time feeds for 3 cities and built a Power BI report and a Python model.", 10.2)
    p2.t(58, 670, "• Household energy dashboard: forecast electricity use with Python and compared 4 models on 2 years of data from a public source.", 10.2)
    p2.t(58, 654, "• Open data pipeline: loads city data into a SQL database every night and checks it before it reaches the dashboards.", 10.2)
    p2.t(45, 625, "AWARDS", 11.5, True)
    p2.t(58, 604, "Winner, Sydney Open Data Hackathon, 2023", 10.2)
    add("cv24_two_page_band.pdf", pdf.build(),
        "One column on two pages with a band of two columns (CERTIFICATIONS | LANGUAGES) at the end of page 1 that goes on at the top of page 2 (certifications on the left, WORK RIGHTS AND AVAILABILITY on the right). No gutter for the whole page: most lines cross the middle.",
        currentRole="Senior Data Analyst", level="Senior", targetRole="Data Analyst", statesTarget=True, yearsExperience=true_years(spans),
        certifications=["Microsoft Certified: Azure Data Scientist Associate", "Northwind Analytics Professional Certificate"],
        awards=[aw("Winner, Sydney Open Data Hackathon", "hackathon", 2023)],
        skills=["SQL", "Power BI", "Tableau", "Python", "Git", "Microsoft Excel"])


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23, f24):
        fn()
    expected = {"asOf": AS_OF.isoformat(), "note": "TRUE values of the fixture CVs (what a person sees), made by tests/fixtures/make_cv_fixtures.py. All people and employers are made up.",
                "fixtures": {}}
    for fx in FIXTURES:
        with open(os.path.join(OUT, fx["name"]), "wb") as f:
            f.write(fx["data"])
        expected["fixtures"][fx["name"]] = dict(layout=fx["layout"], **fx["expected"])
    with open(os.path.join(OUT, "expected.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(expected, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(FIXTURES)} fixtures written to {OUT}")


if __name__ == "__main__":
    main()
