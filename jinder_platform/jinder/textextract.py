"""Read the text of a PDF or a DOCX file with the Python standard library only.

The text is DATA. Nothing in it is ever run or followed as an instruction (AI_Rule Rule 5, item 10).
The readers are made for CVs and job descriptions: plain text in reading order is enough.
If the optional package `pypdf` is installed, it is used when the built-in PDF reader finds almost no text.
"""
import html
import io
import math
import re
import unicodedata
import zipfile
import zlib
from typing import Any, Callable, Dict, List, Optional, Tuple

MAX_TEXT_CHARS = 200_000          # more text than this is cut. A CV has far less
_MAX_DECOMPRESSED = 40_000_000    # a guard against compressed "bombs". All streams of one file share this limit
_MAX_PREDICTOR_BYTES = 8_000_000  # the PNG predictor runs in Python. A larger stream is left as it is
_MAX_PAGES = 40                   # a CV or a job description has fewer pages. More pages are not read (time)


class UnreadableFile(Exception):
    """The file is not a real PDF or DOCX, or it has no text that we can read."""


# =====================================================================
# File type checks. We trust the first bytes, not the file name or the type that the browser sent.
# =====================================================================
def sniff(data: bytes) -> str:
    """Return "pdf", "docx" or "" from the first bytes."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" in z.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            return ""
    return ""


def extract_text(data: bytes) -> str:
    kind = sniff(data)
    if kind == "docx":
        text = _docx_text(data)
    elif kind == "pdf":
        text = _pdf_text(data)
    else:
        raise UnreadableFile("This is not a PDF or a DOCX file.")
    text = _tidy(text)
    if len(text) < 20:
        raise UnreadableFile("We could not find text in this file.")
    return text[:MAX_TEXT_CHARS]


# Characters that a PDF or a Word file gives for a letter or a space, but that a reader of text does not want
_TRANSLATE = {
    0xFB00: "ff", 0xFB01: "fi", 0xFB02: "fl", 0xFB03: "ffi", 0xFB04: "ffl", 0xFB05: "st", 0xFB06: "st",   # ligatures
    0x00A0: " ", 0x2002: " ", 0x2003: " ", 0x2004: " ", 0x2005: " ", 0x2006: " ", 0x2007: " ", 0x2008: " ", 0x2009: " ",
    0x200A: " ", 0x202F: " ", 0x205F: " ", 0x3000: " ", 0x2028: "\n", 0x2029: "\n",                          # spaces and breaks
    0x200B: None, 0x200C: None, 0x200D: None, 0x2060: None, 0xFEFF: None, 0x200E: None, 0x200F: None,       # zero width marks
    0x2010: "-", 0x2011: "-", 0x2012: "-",                                                                   # hyphens
}
_PRIVATE_USE = re.compile("[\ue000-\uf8ff]")
# A hyphen that cuts a word at the end of a line. These words are real compound words: keep the hyphen.
_COMPOUND_HEADS = {
    "full", "back", "front", "end", "data", "cloud", "open", "real", "multi", "cross", "self", "non", "high", "low", "event",
    "test", "model", "user", "time", "large", "small", "mid", "well", "long", "short", "state", "built", "cost", "e", "x",
    "ci", "ml", "ai", "co", "pre", "post", "re", "anti", "semi", "long",
}


def _fix_private_use(text: str) -> str:
    """A bullet from a symbol font arrives as a private-use character. A bullet at the start of a line stays a bullet. Elsewhere it is an icon: drop it."""
    if not _PRIVATE_USE.search(text):
        return text
    out = []
    for line in text.split("\n"):
        stripped = line.lstrip(" \t")
        if stripped and "\ue000" <= stripped[0] <= "\uf8ff":
            line = "• " + _PRIVATE_USE.sub(" ", stripped[1:]).strip()
        else:
            line = _PRIVATE_USE.sub(" ", line)
        out.append(line)
    return "\n".join(out)


def _join_hyphenated(text: str) -> str:
    """A word that was cut with a hyphen at the end of a line gets its two parts back: "engi-" and "neering" give "engineering".
    The rest of the next line stays on its own line."""
    lines = text.split("\n")
    emptied = set()
    for i in range(len(lines) - 1):
        line, nxt = lines[i], lines[i + 1]
        m = re.search(r"([^\W\d_]+)([-\u00ad])$", line)
        if not m or not nxt or not nxt[0].islower() or not m.group(1)[-1].islower():
            continue
        first, _, rest = nxt.partition(" ")
        if not re.fullmatch(r"[^\W\d_]+[.,;:)]*", first):
            continue
        keep = m.group(2) == "-" and m.group(1).lower() in _COMPOUND_HEADS
        lines[i] = line[:-1] + ("-" if keep else "") + first
        lines[i + 1] = rest
        if not rest.strip():
            emptied.add(i + 1)
    return "\n".join(ln for k, ln in enumerate(lines) if k not in emptied)


def _tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = unicodedata.normalize("NFC", text).translate(_TRANSLATE)
    text = _fix_private_use(text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = _join_hyphenated(text)
    text = text.replace("\u00ad", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =====================================================================
# DOCX
# =====================================================================
_MAX_DOCX_HEADERS = 6


def _name_cell_first(row_xml: str) -> str:
    """A table row with two or more cells is often a two-column CV. The cell with the biggest text (the name) is read first, like in a PDF."""
    if "<w:tbl>" in row_xml or "<w:tbl " in row_xml:        # a table inside a table: leave it
        return row_xml
    parts = re.split(r"(<w:tc(?:\s[^>]*)?>.*?</w:tc>)", row_xml, flags=re.S)
    cells = parts[1::2]
    if len(cells) < 2:
        return row_xml
    sizes = [max([int(s) for s in re.findall(r'<w:sz w:val="(\d+)"', c)] or [0]) for c in cells]
    first = max(range(len(cells)), key=lambda i: (sizes[i], -i))
    if first == 0 or sizes[first] < sizes[0] + 4:           # the font size is in half points: 4 is 2 points
        return row_xml
    parts[1::2] = [cells[first]] + [c for i, c in enumerate(cells) if i != first]
    return "".join(parts)


def _docx_xml_text(xml: str) -> str:
    """The text of one Word XML part, in document order. Regular expressions are used instead of an XML parser, so that entity tricks cannot do harm."""
    # A text box is stored twice: once for new Word and once as a fallback for old Word. Read it once.
    xml = re.sub(r"<mc:Fallback\b.*?</mc:Fallback>", "", xml, flags=re.S)
    xml = re.sub(r"<w:tr\b.*?</w:tr>", lambda m: _name_cell_first(m.group(0)), xml, flags=re.S)
    xml = re.sub(r"<w:tab\s*/>", "\t", xml)
    xml = re.sub(r"<w:(br|cr)\b[^>]*/>", "\n", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:noBreakHyphen\s*/>", "\x01-\x02", xml)
    xml = re.sub(r"<w:softHyphen\s*/>", "\x01\u00ad\x02", xml)
    # A symbol (a bullet from the Symbol or Wingdings font) is a private-use character: _tidy turns it into a bullet
    xml = re.sub(r"<w:sym\b[^>]*\bw:char=\"([0-9A-Fa-f]{4})\"[^>]*/>", lambda m: "\x01" + chr(int(m.group(1), 16)) + "\x02", xml)
    xml = re.sub(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", lambda m: "\x01" + m.group(1) + "\x02", xml)
    pieces = re.findall(r"\x01([^\x02]*)\x02|(\n|\t)", xml)
    out = []
    for text, sep in pieces:
        out.append(html.unescape(text) if text else sep)
    return "".join(out)


def _docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.getinfo("word/document.xml")
            if info.file_size > _MAX_DECOMPRESSED:
                raise UnreadableFile("This file is too large to read.")
            body = _docx_xml_text(z.read("word/document.xml").decode("utf-8", errors="replace"))
            # Many templates put the name and the title in the page header. Read the header parts too.
            headers: List[str] = []
            names = sorted(n for n in z.namelist() if re.fullmatch(r"word/header\d*\.xml", n))[:_MAX_DOCX_HEADERS]
            budget = _MAX_DECOMPRESSED
            for name in names:
                size = z.getinfo(name).file_size
                if size > budget:
                    break
                budget -= size
                headers.append(_docx_xml_text(z.read(name).decode("utf-8", errors="replace")))
    except (zipfile.BadZipFile, KeyError) as exc:
        raise UnreadableFile("This is not a valid DOCX file.") from exc
    # The header of every page repeats. Keep each line once, and not the lines that the body has already.
    seen = {ln.strip() for ln in body.split("\n") if ln.strip()}
    head_lines: List[str] = []
    for part in headers:
        for ln in part.split("\n"):
            if ln.strip() and ln.strip() not in seen:
                seen.add(ln.strip())
                head_lines.append(ln)
    return "\n".join(head_lines + [body]) if head_lines else body


# =====================================================================
# PDF: a small reader. It handles compressed streams, object streams, ToUnicode maps and glyph widths.
# =====================================================================
_OBJ_RE = re.compile(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\b")
_STREAM_RE = re.compile(rb"\s*stream(\r\n|\n|\r)")
_REF_TAIL = re.compile(rb"\s+(\d+)\s+R(?![A-Za-z0-9])")
_WS = b" \t\r\n\x0c\x00"
_DELIM = b"()<>[]{}/%"


class _Ref:
    __slots__ = ("num",)

    def __init__(self, num: int):
        self.num = num

    def __repr__(self):
        return f"Ref({self.num})"


class _Name(str):
    """A PDF name such as /F1."""


def _skip_ws(buf: bytes, i: int) -> int:
    n = len(buf)
    while i < n and buf[i] in _WS:
        i += 1
    return i


def _parse_value(buf: bytes, i: int) -> Tuple[Any, int]:
    """Parse one PDF object at position i. Returns (value, next position)."""
    n = len(buf)
    i = _skip_ws(buf, i)
    if i >= n:
        return None, i
    c = buf[i:i + 1]
    if buf[i:i + 2] == b"<<":
        d: Dict[str, Any] = {}
        i += 2
        while i < n:
            i = _skip_ws(buf, i)
            if buf[i:i + 2] == b">>":
                return d, i + 2
            key, i2 = _parse_value(buf, i)
            if i2 <= i:
                i += 1
                continue
            i = i2
            if not isinstance(key, _Name):
                continue
            val, i = _parse_value(buf, i)
            d[str(key)] = val
        return d, i
    if c == b"[":
        arr: List[Any] = []
        i += 1
        while i < n:
            i = _skip_ws(buf, i)
            if buf[i:i + 1] == b"]":
                return arr, i + 1
            v, i2 = _parse_value(buf, i)
            if i2 <= i:
                i += 1
                continue
            arr.append(v)
            i = i2
        return arr, i
    if c == b"/":
        j = i + 1
        while j < n and buf[j] not in _WS and buf[j] not in _DELIM:
            j += 1
        name = buf[i + 1:j].decode("latin-1")
        name = re.sub(r"#([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), name)
        return _Name(name), j
    if c == b"(":
        return _read_literal_string(buf, i)
    if c == b"<":
        j = buf.find(b">", i)
        if j < 0:
            return b"", n
        hexs = re.sub(rb"\s+", b"", buf[i + 1:j])
        if len(hexs) % 2:
            hexs += b"0"
        try:
            return bytes.fromhex(hexs.decode("ascii")), j + 1
        except ValueError:
            return b"", j + 1
    if c == b"%":
        j = i
        while j < n and buf[j] not in b"\r\n":
            j += 1
        return _parse_value(buf, j)
    # a number, a reference, or a keyword
    j = i
    while j < n and buf[j] not in _WS and buf[j] not in _DELIM:
        j += 1
    if j == i:
        return None, i + 1
    token = buf[i:j]
    if re.fullmatch(rb"[+-]?\d+", token):
        m = _REF_TAIL.match(buf, j)
        if m and token[:1] not in (b"-", b"+"):
            return _Ref(int(token)), m.end()
        return int(token), j
    if re.fullmatch(rb"[+-]?(\d+\.\d*|\.\d+)", token):
        return float(token), j
    if token == b"true":
        return True, j
    if token == b"false":
        return False, j
    if token == b"null":
        return None, j
    return token.decode("latin-1"), j


_ESCAPES = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12, ord("("): 40, ord(")"): 41, 0x5C: 0x5C}


def _read_literal_string(buf: bytes, i: int) -> Tuple[bytes, int]:
    out = bytearray()
    n = len(buf)
    i += 1
    depth = 1
    while i < n:
        ch = buf[i]
        if ch == 0x5C:  # backslash
            i += 1
            if i >= n:
                break
            e = buf[i]
            if e in _ESCAPES:
                out.append(_ESCAPES[e])
            elif 0x30 <= e <= 0x37:
                k = i
                digits = bytearray()
                while k < n and len(digits) < 3 and 0x30 <= buf[k] <= 0x37:
                    digits.append(buf[k])
                    k += 1
                out.append(int(digits, 8) & 0xFF)
                i = k - 1
            elif e in b"\r\n":
                if e == 13 and i + 1 < n and buf[i + 1] == 10:
                    i += 1
            else:
                out.append(e)
        elif ch == 0x28:
            depth += 1
            out.append(ch)
        elif ch == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    return bytes(out), i


def _inflate(raw: bytes, limit: int = _MAX_DECOMPRESSED) -> bytes:
    """Decompress a stream, up to `limit` bytes. A damaged stream gives what can be read."""
    if limit <= 0:
        return b""  # zlib treats a limit of 0 as "no limit", so an empty budget must stop here
    d = zlib.decompressobj()
    try:
        return d.decompress(raw, limit)
    except zlib.error:
        d = zlib.decompressobj()
        out = b""
        try:
            for k in range(0, len(raw), 512):
                out += d.decompress(raw[k:k + 512], max(0, limit - len(out)))
                if len(out) >= limit:
                    break
        except zlib.error:
            pass
        return out


def _png_unpredict(raw: bytes, columns: int) -> bytes:
    row = columns + 1
    out = bytearray()
    prev = bytearray(columns)
    for k in range(0, len(raw) - row + 1, row):
        f = raw[k]
        cur = bytearray(raw[k + 1:k + row])
        if f == 2:      # up
            for x in range(columns):
                cur[x] = (cur[x] + prev[x]) & 0xFF
        elif f == 1:    # sub
            for x in range(1, columns):
                cur[x] = (cur[x] + cur[x - 1]) & 0xFF
        out += cur
        prev = cur
    return bytes(out)


class _Pdf:
    def __init__(self, data: bytes):
        self.data = data
        self.objs: Dict[int, Tuple[Any, Optional[bytes]]] = {}   # object number -> (value, decoded stream)
        self._budget = _MAX_DECOMPRESSED                          # all streams of one file share this limit
        self._fonts: Dict[int, Dict[str, Any]] = {}
        self._scan()

    # ----- objects -----
    def _scan(self) -> None:
        data = self.data
        n = len(data)
        pos = 0
        while True:
            m = _OBJ_RE.search(data, pos)
            if not m:
                break
            num = int(m.group(1))
            value, after = _parse_value(data, m.end())
            stream = None
            end = after
            if isinstance(value, dict):
                sm = _STREAM_RE.match(data, after)
                if sm:
                    start = sm.end()
                    length = value.get("Length")
                    stop = -1
                    if isinstance(length, int) and length >= 0 and data[start + length:start + length + 12].lstrip(b"\r\n ").startswith(b"endstream"):
                        stop = start + length
                    if stop < 0:
                        stop = data.find(b"endstream", start)
                        if stop < 0:
                            stop = n
                    stream = self._decode_stream(value, data[start:stop])
                    end = stop
            self.objs[num] = (value, stream)
            pos = max(end, m.end())
        # Object streams hold more objects (PDF 1.5 and later)
        for _num, (value, stream) in list(self.objs.items()):
            if isinstance(value, dict) and value.get("Type") == "ObjStm" and stream:
                self._read_objstm(value, stream)

    def _decode_stream(self, d: Dict[str, Any], raw: bytes) -> bytes:
        filters = d.get("Filter")
        filters = filters if isinstance(filters, list) else ([filters] if filters else [])
        names = [str(self.resolve(f)) for f in filters]
        if any(f in ("FlateDecode", "Fl") for f in names):
            raw = _inflate(raw, self._budget)
            self._budget = max(0, self._budget - len(raw))
            parms = self.resolve(d.get("DecodeParms"))
            if isinstance(parms, list):
                parms = self.resolve(parms[0]) if parms else None
            if (isinstance(parms, dict) and isinstance(parms.get("Predictor"), int) and parms["Predictor"] >= 10
                    and isinstance(parms.get("Columns", 1), int) and 0 < parms.get("Columns", 1) <= 65536 and len(raw) <= _MAX_PREDICTOR_BYTES):
                raw = _png_unpredict(raw, int(parms.get("Columns", 1)))
        elif names:
            return b""  # an image, or a filter that we do not need
        return raw

    def _read_objstm(self, d: Dict[str, Any], stream: bytes) -> None:
        count = self.resolve(d.get("N"))
        first = self.resolve(d.get("First"))
        if not isinstance(count, int) or not isinstance(first, int):
            return
        head = stream[:first].split()
        for k in range(0, min(len(head) - 1, count * 2), 2):
            if head[k].isdigit() and head[k + 1].isdigit():
                value, _ = _parse_value(stream, first + int(head[k + 1]))
                self.objs.setdefault(int(head[k]), (value, None))

    def resolve(self, v: Any) -> Any:
        depth = 0
        while isinstance(v, _Ref) and depth < 20:
            entry = self.objs.get(v.num)
            v = entry[0] if entry else None
            depth += 1
        return v

    def stream_of(self, v: Any) -> bytes:
        if isinstance(v, _Ref):
            entry = self.objs.get(v.num)
            return (entry[1] or b"") if entry else b""
        return b""

    # ----- fonts -----
    def font_for(self, font: Any) -> Optional[Dict[str, Any]]:
        """What we need from a font: how to turn a code into text, and how wide a code is."""
        f = self.resolve(font)
        if not isinstance(f, dict):
            return None
        key = id(f)
        if key in self._fonts:
            return self._fonts[key]
        info = None
        tu = f.get("ToUnicode")
        if tu is not None:
            data = self.stream_of(tu)
            if data:
                info = _parse_cmap(data)
        sub = str(self.resolve(f.get("Subtype")) or "")
        if info is None:
            info = {"map": {}, "bytes": 2 if sub == "Type0" else 1, "none": True}
        info["type0"] = sub == "Type0"
        info["width"] = self._width_function(f, sub)
        info["enc"] = None if sub == "Type0" else self._encoding_of(f)
        self._fonts[key] = info
        return info

    def _encoding_of(self, f: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """How a simple font turns a code into a letter, when the font has no ToUnicode map: a code page and a table of changes."""
        enc = self.resolve(f.get("Encoding"))
        codec = "mac_roman" if str(enc) == "MacRomanEncoding" else None
        table: Dict[int, str] = {}
        if isinstance(enc, dict):
            if str(self.resolve(enc.get("BaseEncoding"))) == "MacRomanEncoding":
                codec = "mac_roman"
            diffs = self.resolve(enc.get("Differences"))
            code = 0
            for item in diffs if isinstance(diffs, list) else []:
                item = self.resolve(item)
                if isinstance(item, int) and not isinstance(item, bool):
                    code = item
                elif isinstance(item, _Name):
                    ch = _glyph_char(str(item))
                    if ch:
                        table[code] = ch
                    code += 1
        if codec is None and not table:
            return None
        return {"codec": codec, "table": table}

    def _width_function(self, f: Dict[str, Any], sub: str) -> Callable[[int], float]:
        """A function: code -> glyph width in 1/1000 of the font size."""
        if sub == "Type0":
            desc = self.resolve(f.get("DescendantFonts"))
            desc = self.resolve(desc[0]) if isinstance(desc, list) and desc else None
            dw = 1000
            table: Dict[int, float] = {}
            if isinstance(desc, dict):
                dw = self.resolve(desc.get("DW")) or 1000
                arr = self.resolve(desc.get("W"))
                arr = [self.resolve(x) for x in arr] if isinstance(arr, list) else []
                i = 0
                while i < len(arr):
                    c = arr[i]
                    nxt = arr[i + 1] if i + 1 < len(arr) else None
                    if isinstance(c, int) and isinstance(nxt, list):
                        for k, w in enumerate(nxt):
                            table[c + k] = self.resolve(w)
                        i += 2
                    elif isinstance(c, int) and isinstance(nxt, int) and i + 2 < len(arr):
                        for cid in range(c, min(nxt, c + 70000) + 1):
                            table[cid] = arr[i + 2]
                        i += 3
                    else:
                        i += 1
            return lambda code: float(table.get(code, dw))
        first = self.resolve(f.get("FirstChar")) or 0
        widths = self.resolve(f.get("Widths"))
        widths = [self.resolve(w) for w in widths] if isinstance(widths, list) else []
        missing = 500.0
        fd = self.resolve(f.get("FontDescriptor"))
        if isinstance(fd, dict):
            mw = self.resolve(fd.get("MissingWidth"))
            if isinstance(mw, (int, float)) and mw:
                missing = float(mw)
        # A standard font (Helvetica, Arial, Times) may come with no Widths list. Use the widths of Helvetica then.
        base = _HELVETICA_WIDTHS if not widths else None

        def width(code: int) -> float:
            k = code - first
            if 0 <= k < len(widths) and isinstance(widths[k], (int, float)):
                return float(widths[k])
            if base is not None and 32 <= code <= 126:
                return float(base[code - 32])
            return missing

        return width

    # ----- pages -----
    def pages(self) -> List[Dict[str, Any]]:
        """The pages in reading order (the page tree). If the tree cannot be read, the pages in file order."""
        ordered: List[Dict[str, Any]] = []
        seen: set = set()

        def walk(node: Any, depth: int = 0) -> None:
            node = self.resolve(node)
            if not isinstance(node, dict) or depth > 30 or id(node) in seen:
                return
            seen.add(id(node))
            if node.get("Type") == "Page" or ("Kids" not in node and "Contents" in node):
                ordered.append(node)
                return
            kids = self.resolve(node.get("Kids"))
            for kid in kids if isinstance(kids, list) else []:
                walk(kid, depth + 1)

        catalog = next((v for v, _ in self.objs.values() if isinstance(v, dict) and v.get("Type") == "Catalog"), None)
        if catalog:
            walk(catalog.get("Pages"))
        if ordered:
            return ordered
        return [v for num in sorted(self.objs) for v in [self.objs[num][0]] if isinstance(v, dict) and v.get("Type") == "Page"]

    def page_fonts(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """The fonts of a page. A page with no resources takes them from its parent."""
        node: Any = page
        for _ in range(10):
            if not isinstance(node, dict):
                break
            res = self.resolve(node.get("Resources"))
            if isinstance(res, dict):
                fonts = self.resolve(res.get("Font"))
                return fonts if isinstance(fonts, dict) else {}
            node = self.resolve(node.get("Parent"))
        return {}

    def page_resources(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """The resources of a page (fonts, form XObjects). A page with no resources takes them from its parent."""
        node: Any = page
        for _ in range(10):
            if not isinstance(node, dict):
                break
            res = self.resolve(node.get("Resources"))
            if isinstance(res, dict):
                return res
            node = self.resolve(node.get("Parent"))
        return {}

    def page_streams(self, page: Dict[str, Any]) -> List[bytes]:
        contents = page.get("Contents")
        refs = contents if isinstance(contents, list) else [contents]
        out = []
        for r in refs:
            if isinstance(r, _Ref):
                s = self.stream_of(r)
                if s:
                    out.append(s)
        return out


def _parse_cmap(data: bytes) -> Dict[str, Any]:
    """Read a ToUnicode CMap. Returns { map: {code: text}, bytes: width of a code in bytes }."""
    text = data.decode("latin-1")
    mapping: Dict[int, str] = {}
    width = 1
    for block in re.findall(r"begincodespacerange(.*?)endcodespacerange", text, re.S):
        for lo, _hi in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            width = max(width, len(lo) // 2)

    def u16(hexs: str) -> str:
        try:
            return bytes.fromhex(hexs if len(hexs) % 2 == 0 else hexs + "0").decode("utf-16-be", errors="replace")
        except ValueError:
            return ""

    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", block):
            mapping[int(src, 16)] = u16(dst)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for m in re.finditer(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]*>|\[[^\]]*\])", block):
            lo, hi, dst = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
            if dst.startswith("["):
                for k, item in enumerate(re.findall(r"<([0-9A-Fa-f]*)>", dst)):
                    if lo + k <= hi:
                        mapping[lo + k] = u16(item)
            else:
                base = u16(dst[1:-1])
                if not base:
                    continue
                for code in range(lo, min(hi, lo + 65535) + 1):
                    last = ord(base[-1]) + (code - lo)
                    mapping[code] = base[:-1] + chr(last) if last < 0x110000 else base
    return {"map": mapping, "bytes": width, "none": False}


def _simple_char(code: int, enc: Optional[Dict[str, Any]]) -> str:
    """The letter for a code of a simple font that has no ToUnicode map. Windows code page 1252 is the default."""
    if enc:
        ch = enc["table"].get(code)
        if ch is not None:
            return ch
        if enc["codec"]:
            return bytes([code]).decode(enc["codec"], errors="replace")
    return bytes([code]).decode("cp1252", errors="replace")


def _decode_codes(s: bytes, font: Optional[Dict[str, Any]]) -> List[Tuple[int, str]]:
    """Split a string into (code, text) pairs for a font."""
    if font is None:
        return [(b, bytes([b]).decode("cp1252", errors="replace")) for b in s]
    if font["bytes"] == 2 and len(s) % 2 == 0:
        codes = [(s[k] << 8) | s[k + 1] for k in range(0, len(s), 2)]
    else:
        codes = list(s)
    if font.get("none"):
        if font.get("type0"):
            return [(c, "") for c in codes]  # a CID font with no map: we know the width, not the letters
        enc = font.get("enc")
        return [(c, _simple_char(c, enc)) for c in codes]
    m = font["map"]
    simple = not font.get("type0") and font["bytes"] == 1
    # A code that the map does not know is dropped, but a simple font that has no entry for code 32 still has a space there
    return [(c, m.get(c, " " if (c == 32 and simple) else "")) for c in codes]


_GLYPHS = {
    "space": " ", "exclam": "!", "quotedbl": '"', "numbersign": "#", "dollar": "$", "percent": "%", "ampersand": "&", "quotesingle": "'",
    "parenleft": "(", "parenright": ")", "asterisk": "*", "plus": "+", "comma": ",", "hyphen": "-", "minus": "−", "period": ".",
    "slash": "/", "colon": ":", "semicolon": ";", "less": "<", "equal": "=", "greater": ">", "question": "?", "at": "@",
    "bracketleft": "[", "backslash": "\\", "bracketright": "]", "asciicircum": "^", "underscore": "_", "grave": "`",
    "braceleft": "{", "bar": "|", "braceright": "}", "asciitilde": "~", "bullet": "•", "endash": "–", "emdash": "—",
    "quoteleft": "‘", "quoteright": "’", "quotedblleft": "“", "quotedblright": "”", "quotesinglbase": "‚",
    "quotedblbase": "„", "ellipsis": "…", "periodcentered": "·", "middot": "·", "copyright": "©",
    "registered": "®", "trademark": "™", "degree": "°", "section": "§", "paragraph": "¶", "multiply": "×",
    "divide": "÷", "plusminus": "±", "Euro": "€", "sterling": "£", "yen": "¥", "cent": "¢",
    "guillemotleft": "«", "guillemotright": "»", "dagger": "†", "daggerdbl": "‡", "nbspace": " ",
    "fi": "fi", "fl": "fl", "ff": "ff", "ffi": "ffi", "ffl": "ffl", "germandbls": "ß", "AE": "Æ", "ae": "æ",
    "OE": "Œ", "oe": "œ", "Oslash": "Ø", "oslash": "ø", "Lslash": "Ł", "lslash": "ł", "dotlessi": "ı",
    "Eth": "Ð", "eth": "ð", "Thorn": "Þ", "thorn": "þ", "zero": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}
_ACCENT_MARKS = {
    "acute": "́", "grave": "̀", "circumflex": "̂", "dieresis": "̈", "tilde": "̃", "ring": "̊",
    "cedilla": "̧", "caron": "̌", "breve": "̆", "ogonek": "̨", "macron": "̄", "dotaccent": "̇",
    "hungarumlaut": "̋",
}


def _glyph_char(name: str) -> str:
    """The text for a glyph name from an /Encoding /Differences list ("bullet", "endash", "eacute", "uni1EC5"). Empty if unknown."""
    if len(name) == 1:
        return name
    if name in _GLYPHS:
        return _GLYPHS[name]
    m = re.fullmatch(r"uni((?:[0-9A-Fa-f]{4})+)", name)
    if m:
        digits = m.group(1)
        return "".join(chr(int(digits[k:k + 4], 16)) for k in range(0, len(digits), 4))
    m = re.fullmatch(r"u([0-9A-Fa-f]{4,6})", name)
    if m and int(m.group(1), 16) < 0x110000:
        return chr(int(m.group(1), 16))
    m = re.fullmatch(r"([A-Za-z])(" + "|".join(_ACCENT_MARKS) + ")", name)
    if m:
        return unicodedata.normalize("NFC", m.group(1) + _ACCENT_MARKS[m.group(2)])
    return ""


# The widths of the Helvetica glyphs for the codes 32 to 126 (1000 units to the font size)
_HELVETICA_WIDTHS = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]


class _Run:
    """A piece of text that was drawn in one go: where it starts and ends (page units, y goes up), the font size, and the text."""
    __slots__ = ("x0", "x1", "y", "size", "text")

    def __init__(self, x0: float, x1: float, y: float, size: float, text: str):
        self.x0, self.x1, self.y, self.size, self.text = x0, x1, y, size or 1.0, text


def _matmul(m: List[float], n: List[float]) -> List[float]:
    """The matrix m followed by the matrix n (PDF order)."""
    return [m[0] * n[0] + m[1] * n[2], m[0] * n[1] + m[1] * n[3],
            m[2] * n[0] + m[3] * n[2], m[2] * n[1] + m[3] * n[3],
            m[4] * n[0] + m[5] * n[2] + n[4], m[4] * n[1] + m[5] * n[3] + n[5]]


_IDENTITY = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
_MAX_FORMS = 300          # the most form XObjects that one page may draw
_RUN_BREAK_SPACES = 4     # this many spaces in a row cut a run: the text on the two sides is in different cells
_RUN_BREAK_KERN = -900    # a TJ number below this (a gap of 0.9 em) also cuts a run


def _page_runs(pdf: _Pdf, page: Dict[str, Any]) -> List[_Run]:
    """All the text of a page as runs with a position. The pen position is tracked with the glyph widths."""
    runs: List[_Run] = []
    forms = [_MAX_FORMS]

    def interpret(stream: bytes, resources: Dict[str, Any], base_ctm: List[float], depth: int) -> None:
        fonts = pdf.resolve(resources.get("Font"))
        fonts = fonts if isinstance(fonts, dict) else {}
        xobjects = pdf.resolve(resources.get("XObject"))
        xobjects = xobjects if isinstance(xobjects, dict) else {}
        ctm = list(base_ctm)
        gstack: List[Tuple[Any, ...]] = []
        font: Optional[Dict[str, Any]] = None
        fs, tc, tw, tz, leading = 1.0, 0.0, 0.0, 1.0, 0.0
        tm = list(_IDENTITY)        # the text matrix: a b c d e f
        lm = list(tm)               # the line matrix
        cur: Dict[str, Any] = {}    # the run that is being drawn: x0, y, size, chars, x1, trail (spaces at its end)

        def origin() -> Tuple[float, float]:
            return (tm[4] * ctm[0] + tm[5] * ctm[2] + ctm[4], tm[4] * ctm[1] + tm[5] * ctm[3] + ctm[5])

        def flush() -> None:
            if cur:
                text = "".join(cur["chars"]).rstrip()
                if text:
                    runs.append(_Run(cur["x0"], cur["x1"], cur["y"], cur["size"], text))
                cur.clear()

        def show(pieces: List[Any]) -> None:
            a, b = tm[0] * ctm[0] + tm[1] * ctm[2], tm[0] * ctm[1] + tm[1] * ctm[3]
            c, d = tm[2] * ctm[0] + tm[3] * ctm[2], tm[2] * ctm[1] + tm[3] * ctm[3]
            size = abs(fs) * math.sqrt(abs(a * d - b * c))
            horizontal = abs(a) >= abs(b)       # text that runs up or down the page is not read
            for el in pieces:
                if isinstance(el, (bytes, bytearray)):
                    for code, ch in _decode_codes(bytes(el), font):
                        w = (font["width"](code) if font else 500.0) / 1000.0
                        one_byte = font is None or font["bytes"] == 1
                        adv = (w * fs + tc + (tw if code == 32 and one_byte else 0.0)) * tz
                        if horizontal and ch:
                            if ch.strip() == "":
                                if cur:
                                    cur["chars"].append(" ")
                                    cur["trail"] += 1
                            else:
                                if cur and cur["trail"] >= _RUN_BREAK_SPACES:
                                    flush()
                                if not cur:
                                    x, y = origin()
                                    cur.update(x0=x, y=y, size=size, chars=[], x1=x, trail=0)
                                cur["chars"].append(ch)
                                cur["trail"] = 0
                        tm[4] += adv * tm[0]
                        tm[5] += adv * tm[1]
                        if horizontal and cur and ch and ch.strip():
                            cur["x1"] = origin()[0]
                elif isinstance(el, (int, float)) and not isinstance(el, bool):
                    tm[4] -= (el / 1000.0) * fs * tz * tm[0]
                    tm[5] -= (el / 1000.0) * fs * tz * tm[1]
                    if el < _RUN_BREAK_KERN:
                        flush()
                    elif el < -180 and cur:
                        cur["chars"].append(" ")
                        cur["trail"] += 1
            flush()

        i, n = 0, len(stream)
        operands: List[Any] = []
        while i < n:
            i = _skip_ws(stream, i)
            if i >= n:
                break
            ch = stream[i:i + 1]
            if ch in (b"(", b"<", b"[", b"/") or ch.isdigit() or ch in (b"+", b"-", b"."):
                v, i2 = _parse_value(stream, i)
                i = i2 if i2 > i else i + 1
                operands.append(v)
                if len(operands) > 64:
                    operands = operands[-32:]
                continue
            if ch == b"%":
                while i < n and stream[i] not in b"\r\n":
                    i += 1
                continue
            j = i
            while j < n and stream[j] not in _WS and stream[j] not in _DELIM:
                j += 1
            if j == i:
                i += 1
                continue
            op = stream[i:j].decode("latin-1")
            i = j
            nums = [float(o) for o in operands if isinstance(o, (int, float)) and not isinstance(o, bool)]
            if op == "BI":      # an inline image: skip to EI
                k = stream.find(b"EI", i)
                i = n if k < 0 else k + 2
            elif op == "q":
                if len(gstack) < 64:
                    gstack.append((list(ctm), font, fs, tc, tw, tz, leading))
            elif op == "Q":
                if gstack:
                    saved = gstack.pop()
                    ctm, font, fs, tc, tw, tz, leading = list(saved[0]), saved[1], saved[2], saved[3], saved[4], saved[5], saved[6]
            elif op == "cm" and len(nums) >= 6:
                ctm = _matmul(nums[-6:], ctm)
            elif op == "Do" and operands and isinstance(operands[-1], _Name) and depth < 4 and forms[0] > 0:
                ref = xobjects.get(str(operands[-1]))
                xo = pdf.resolve(ref)
                if isinstance(xo, dict) and str(pdf.resolve(xo.get("Subtype"))) == "Form":
                    forms[0] -= 1
                    data = pdf.stream_of(ref)
                    if data:
                        mtx = pdf.resolve(xo.get("Matrix"))
                        vals = [pdf.resolve(v) for v in mtx] if isinstance(mtx, list) and len(mtx) == 6 else []
                        matrix = [float(v) for v in vals] if len(vals) == 6 and all(isinstance(v, (int, float)) for v in vals) else _IDENTITY
                        res = pdf.resolve(xo.get("Resources"))
                        interpret(data, res if isinstance(res, dict) else resources, _matmul(matrix, ctm), depth + 1)
            elif op == "BT":
                tm = list(_IDENTITY)
                lm = list(tm)
            elif op == "Tf" and len(operands) >= 2:
                name = operands[-2]
                font = pdf.font_for(fonts.get(str(name))) if isinstance(name, _Name) else None
                fs = float(operands[-1]) if isinstance(operands[-1], (int, float)) else fs
            elif op == "Tc" and nums:
                tc = nums[-1]
            elif op == "Tw" and nums:
                tw = nums[-1]
            elif op == "Tz" and nums:
                tz = nums[-1] / 100.0
            elif op == "TL" and nums:
                leading = nums[-1]
            elif op in ("Td", "TD") and len(nums) >= 2:
                tx, ty = nums[-2], nums[-1]
                if op == "TD":
                    leading = -ty
                lm[4] += tx * lm[0] + ty * lm[2]
                lm[5] += tx * lm[1] + ty * lm[3]
                tm = list(lm)
            elif op == "Tm" and len(nums) >= 6:
                tm = nums[-6:]
                lm = list(tm)
            elif op == "T*":
                lm[4] += -leading * lm[2]
                lm[5] += -leading * lm[3]
                tm = list(lm)
            elif op == "Tj" and operands and isinstance(operands[-1], (bytes, bytearray)):
                show([operands[-1]])
            elif op == "TJ" and operands and isinstance(operands[-1], list):
                show(operands[-1])
            elif op in ("'", '"') and operands and isinstance(operands[-1], (bytes, bytearray)):
                if op == '"' and len(nums) >= 2:
                    tw, tc = nums[-2], nums[-1]
                lm[4] += -leading * lm[2]
                lm[5] += -leading * lm[3]
                tm = list(lm)
                show([operands[-1]])
            operands = []

    # The streams of a page are one stream: a graphics state can start in one part and end in the next
    joined = b"\n".join(pdf.page_streams(page))
    interpret(joined, pdf.page_resources(page), _IDENTITY, 0)
    return runs


# ----- reading order -----
class _Cell:
    """Runs on one line that are so near that they belong together (the words of a phrase)."""
    __slots__ = ("runs", "x0", "x1", "y", "size", "text")

    def __init__(self, runs: List[_Run]):
        self.runs = runs
        self.x0 = min(r.x0 for r in runs)
        self.x1 = max(r.x1 for r in runs)
        self.y = runs[0].y
        self.size = max(r.size for r in runs)
        self.text = " ".join(r.text for r in runs)


def _rows(runs: List[_Run]) -> List[List[_Run]]:
    """Group runs into lines (top to bottom). The runs of a line are sorted from left to right."""
    rows: List[List[_Run]] = []
    for r in sorted(runs, key=lambda r: (-r.y, r.x0)):
        if rows and rows[-1][0].y - r.y <= 0.45 * min(rows[-1][0].size, r.size):
            rows[-1].append(r)
        else:
            rows.append([r])
    for row in rows:
        row.sort(key=lambda r: r.x0)
    return rows


def _row_cells(row: List[_Run]) -> List[_Cell]:
    cells: List[List[_Run]] = []
    for r in row:
        if cells and r.x0 - cells[-1][-1].x1 <= 0.7 * max(r.size, cells[-1][-1].size):
            cells[-1].append(r)
        else:
            cells.append([r])
    return [_Cell(c) for c in cells]


_DATE_WORDS = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b|\b(present|current|now|to|date|ongoing|today|until|since|from)\b",
                         re.I)


def _substantive(text: str) -> bool:
    """Text of a column. A date, a number or a few letters is not: those are in the margin of a line, not in a column."""
    return len(re.sub(r"[^A-Za-z]", "", _DATE_WORDS.sub("", text))) >= 4


def _share(values: List[float]) -> float:
    """The share of the values that lie within 4 units of the most common value."""
    if not values:
        return 0.0
    buckets: Dict[int, int] = {}
    for v in values:
        buckets[int(v // 4)] = buckets.get(int(v // 4), 0) + 1
    best = max(buckets, key=lambda k: (buckets[k] + buckets.get(k - 1, 0) + buckets.get(k + 1, 0), buckets[k]))
    return (buckets[best] + buckets.get(best - 1, 0) + buckets.get(best + 1, 0)) / float(len(values))


def _is_column(cells: List[_Cell]) -> bool:
    """Do these cells start at the same x? Text in a column does. A margin of dates or places is aligned at its end instead."""
    return _share([c.x0 for c in cells]) >= 0.4 and _share([c.x0 for c in cells]) >= _share([c.x1 for c in cells]) - 0.05


def _is_margin(side: List[_Cell], dates: List[_Cell], other: List[_Cell]) -> bool:
    """Is this side only a margin of the other side? That is a timeline (the dates, and the headings of the sections, are at the left of the
    text of each job): the cells are mostly dates, or they are short (headings) and each has a cell on the other side on the same baseline."""
    if dates and len(dates) >= 0.5 * len(side):
        return True
    mine = side + dates
    if sum(len(c.text) for c in mine) / float(len(mine)) >= 20:
        return False
    shared = sum(1 for c in mine if any(abs(c.y - o.y) <= 0.4 * min(c.size, o.size) for o in other))
    return shared >= 0.7 * len(mine)


def _find_gutter(row_cells: List[List[_Cell]]) -> Optional[float]:
    """The x of the empty strip between two columns of text, or None if the page has one column."""
    cells = [c for row in row_cells for c in row]
    if len(cells) < 10 or len(row_cells) < 8:
        return None
    xmin, xmax = min(c.x0 for c in cells), max(c.x1 for c in cells)
    if xmax - xmin < 200:
        return None
    sizes = sorted(c.size for c in cells)
    median = sizes[len(sizes) // 2]
    lo = int(xmin)
    nbins = int(math.ceil(xmax)) - lo + 1
    diff = [0] * (nbins + 1)
    for row in row_cells:       # how many lines have text at each x (a line counts once)
        merged: List[List[float]] = []
        for a, b in sorted((c.x0, c.x1) for c in row):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for a, b in merged:
            diff[max(0, int(a) - lo)] += 1
            diff[min(nbins, int(math.ceil(b)) - lo)] -= 1
    cover, total = [], 0
    for k in range(nbins):
        total += diff[k]
        cover.append(total)
    allow = max(2, int(0.08 * len(row_cells)))      # a few full-width lines (a name, a title) may cross the gutter
    min_width = max(8.0, 0.9 * median)
    substantive = [c for c in cells if _substantive(c.text)]
    dated = [c for c in cells if not _substantive(c.text) and re.search(r"\d", c.text)]
    best: Optional[Tuple[int, float, float]] = None
    k, end = int(0.12 * nbins), int(0.88 * nbins)
    while k < end:
        if cover[k] > allow:
            k += 1
            continue
        j = k
        while j < nbins and cover[j] <= allow:
            j += 1
        if j - k >= min_width:
            gx = lo + (k + j) / 2.0
            left = [c for c in substantive if c.x1 <= gx]
            right = [c for c in substantive if c.x0 >= gx]
            need = max(5, int(0.12 * len(substantive)))
            if len(left) >= need and len(right) >= need and _is_column(left) and _is_column(right):
                ld = [c for c in dated if c.x1 <= gx]
                rd = [c for c in dated if c.x0 >= gx]
                if _is_margin(left, ld, right + rd) or _is_margin(right, rd, left + ld):
                    k = j + 1
                    continue
                cand = (min(len(left), len(right)), float(j - k), gx)
                if best is None or cand[:2] > best[:2]:
                    best = cand
        k = j + 1
    return best[2] if best else None


def _blocks(runs: List[_Run], depth: int = 0) -> List[List[List[_Run]]]:
    """The lines of the runs in reading order, as blocks. A page with two columns gives the left column and then the right column.
    A full-width line (a name, a title) comes before the columns that are under it."""
    rows = _rows(runs)
    if depth < 2:
        row_cells = [_row_cells(row) for row in rows]
        gx = _find_gutter(row_cells)
        if gx is not None:
            left: List[_Run] = []
            right: List[_Run] = []
            spanning: List[_Run] = []
            for row in row_cells:
                for c in row:
                    if c.x0 < gx < c.x1:
                        spanning.extend(c.runs)
                    elif (c.x0 + c.x1) / 2.0 < gx:
                        left.extend(c.runs)
                    else:
                        right.extend(c.runs)
            span_rows = _rows(spanning)
            zones: List[List[List[_Run]]] = [[[], []] for _ in range(len(span_rows) + 1)]
            for side, group in ((0, left), (1, right)):
                for r in group:
                    zones[sum(1 for sr in span_rows if sr[0].y > r.y + 0.3 * r.size)][side].append(r)
            out: List[List[List[_Run]]] = []
            pending: List[List[_Run]] = []
            for zi, (zl, zr) in enumerate(zones):
                if zl or zr:
                    if pending:
                        out.append(pending)
                        pending = []
                    order = [zl, zr]
                    if zl and zr and max(r.size for r in zr) > max(r.size for r in zl) + 0.5:
                        order = [zr, zl]        # the column with the biggest text (the name) is read first
                    for side_runs in order:
                        if side_runs:
                            out.extend(_blocks(side_runs, depth + 1))
                if zi < len(span_rows):
                    pending.append(span_rows[zi])
            if pending:
                out.append(pending)
            return out
    return [rows]


def _row_strip(cells: List[_Cell], s0: float, s1: float, min_strip: float) -> Optional[Tuple[float, float]]:
    """The free vertical strip (s0, s1) that is left when this line is added to a band, or None if a cell of the line crosses it."""
    for c in sorted(cells, key=lambda c: c.x0):
        if c.x1 <= s0 or c.x0 >= s1:
            continue
        if c.x0 <= s0 and c.x1 >= s1:
            return None
        if (c.x0 + c.x1) / 2.0 < (s0 + s1) / 2.0:
            s0 = max(s0, c.x1)
        else:
            s1 = min(s1, c.x0)
    return (s0, s1) if s1 - s0 >= min_strip else None


def _band_ok(slice_cells: List[List[_Cell]], strip: Tuple[float, float]) -> bool:
    """Is this block of lines two columns of text? Both sides need at least 2 cells of real text (not dates or numbers) on 2 lines, the cells are long
    (a table of short cells is read line by line), they start at the same x, and neither side is only a margin of the other (a timeline)."""
    mid = (strip[0] + strip[1]) / 2.0
    cells = [c for row in slice_cells for c in row]
    left = [c for c in cells if c.x1 <= mid and _substantive(c.text)]
    right = [c for c in cells if c.x0 >= mid and _substantive(c.text)]
    if len(left) < 2 or len(right) < 2:
        return False
    for side in (left, right):
        if len({round(c.y) for c in side}) < 2 or sum(len(c.text) for c in side) / float(len(side)) < 18:
            return False
        if not _is_column(side):
            return False
    ld = [c for c in cells if c.x1 <= mid and not _substantive(c.text) and re.search(r"\d", c.text)]
    rd = [c for c in cells if c.x0 >= mid and not _substantive(c.text) and re.search(r"\d", c.text)]
    return not (_band_margin(left, ld, right + rd) or _band_margin(right, rd, left + ld))


def _band_margin(side: List[_Cell], dates: List[_Cell], other: List[_Cell]) -> bool:
    """Is this side only a margin (the dates of a timeline, short headings) of the other side? Its cells are on the same lines as the cells of the
    other side. A column that has a year under an entry ("Google Data Analytics Professional Certificate" / "2021") is not a margin."""
    mine = side + dates
    shared = sum(1 for c in mine if any(abs(c.y - o.y) <= 0.4 * min(c.size, o.size) for o in other))
    if dates and len(dates) >= 0.5 * len(side):
        return shared >= 0.7 * len(mine)
    if sum(len(c.text) for c in mine) / float(len(mine)) >= 20:
        return False
    return shared >= 0.7 * len(mine)


def _find_bands(rows: List[List[_Run]], row_cells: List[List[_Cell]]) -> List[Tuple[int, int, float, float]]:
    """Blocks of 3 lines or more with two columns, in a page that is otherwise one column (a "CERTIFICATIONS | LANGUAGES" block at the end of a page).
    Returns (first line, last line, strip start, strip end) for each. A band is a run of lines that share a free vertical strip. The lines at the
    edge of the run that have text on one side only are cut off when they look like the start of the next part (a bigger heading, a text that starts
    left of the column, a gap of more than a line before it)."""
    n = len(rows)
    sizes = sorted(c.size for row in row_cells for c in row)
    if n < 3 or not sizes:
        return []
    median = sizes[len(sizes) // 2]
    min_strip = max(12.0, 1.2 * median)
    min_seed = max(16.0, 1.6 * median)
    bands: List[Tuple[int, int, float, float]] = []
    taken: set = set()

    def too_far(upper: int, lower: int) -> bool:
        return rows[upper][0].y - rows[lower][0].y > 3.5 * max(rows[upper][0].size, rows[lower][0].size)

    for i in range(n):
        if i in taken:
            continue
        cells = sorted(row_cells[i], key=lambda c: c.x0)
        seed: Optional[Tuple[float, float]] = None
        for a, b in zip(cells, cells[1:]):
            if b.x0 - a.x1 >= min_seed and (seed is None or b.x0 - a.x1 > seed[1] - seed[0]):
                seed = (a.x1, b.x0)
        if seed is None:
            continue
        lo = hi = i
        strip = seed
        j = i - 1
        while j >= 0 and j not in taken and not too_far(j, j + 1):
            ns = _row_strip(row_cells[j], strip[0], strip[1], min_strip)
            if ns is None:
                break
            strip, lo, j = ns, j, j - 1
        j = i + 1
        while j < n and j not in taken and not too_far(j - 1, j):
            ns = _row_strip(row_cells[j], strip[0], strip[1], min_strip)
            if ns is None:
                break
            strip, hi, j = ns, j, j + 1
        mid = (strip[0] + strip[1]) / 2.0
        explored = (lo, hi)

        def sides(k: int) -> Tuple[List[_Cell], List[_Cell]]:
            return [c for c in row_cells[k] if (c.x0 + c.x1) / 2.0 < mid], [c for c in row_cells[k] if (c.x0 + c.x1) / 2.0 >= mid]

        left_x0 = [c.x0 for k in range(lo, hi + 1) for c in sides(k)[0]]
        right_x0 = [c.x0 for k in range(lo, hi + 1) for c in sides(k)[1]]

        def mode(values: List[float]) -> float:
            if not values:
                return 0.0
            buckets: Dict[int, int] = {}
            for v in values:
                buckets[int(v // 4)] = buckets.get(int(v // 4), 0) + 1
            best = max(buckets, key=lambda b: (buckets[b], b))
            return best * 4 + 2.0

        left_mode, right_mode = mode(left_x0), mode(right_x0)

        def edge_ok(k: int, neighbour: int) -> bool:
            left_cells, right_cells = sides(k)
            if left_cells and right_cells:
                return True
            cs = left_cells or right_cells
            column_x0 = left_mode if left_cells else right_mode
            body = max(c.size for c in cs)
            return (body <= median + 0.5 and min(c.x0 for c in cs) >= column_x0 - 6
                    and rows[min(k, neighbour)][0].y - rows[max(k, neighbour)][0].y <= 1.6 * body)

        while lo < hi and not edge_ok(lo, lo + 1):
            lo += 1
        while hi > lo and not edge_ok(hi, hi - 1):
            hi -= 1
        if hi - lo + 1 >= 3 and _band_ok([row_cells[k] for k in range(lo, hi + 1)], strip):
            bands.append((lo, hi, strip[0], strip[1]))
            taken.update(range(lo, hi + 1))
        elif explored[1] - explored[0] >= 20:
            taken.update(range(explored[0], explored[1] + 1))       # a long run of lines with no text across the strip that is not a band: do not try it again
    bands.sort()
    return bands


class _Piece:
    """A piece of the text of a page: a block of lines ("text"), or the left or the right column of a band of two columns."""
    __slots__ = ("kind", "text", "strip", "at_top", "at_bottom")

    def __init__(self, kind: str, rows: List[List[_Run]], strip: Optional[Tuple[float, float]] = None, at_top: bool = False, at_bottom: bool = False):
        self.kind, self.strip, self.at_top, self.at_bottom = kind, strip, at_top, at_bottom
        self.text = _render_rows(rows)


def _page_pieces(runs: List[_Run]) -> List[_Piece]:
    """The pieces of a page in reading order. A page with two columns all over is split by _blocks. A page that has bands of two columns in the
    middle of one column text is cut into text pieces and the left and the right column of each band."""
    rows = _rows(runs)
    row_cells = [_row_cells(row) for row in rows]
    if _find_gutter(row_cells) is None:
        bands = _find_bands(rows, row_cells)
        if bands:
            pieces: List[_Piece] = []
            cursor = 0
            for lo, hi, s0, s1 in bands:
                if lo > cursor:
                    pieces.append(_Piece("text", rows[cursor:lo]))
                mid = (s0 + s1) / 2.0
                left = [r for k in range(lo, hi + 1) for c in row_cells[k] if (c.x0 + c.x1) / 2.0 < mid for r in c.runs]
                right = [r for k in range(lo, hi + 1) for c in row_cells[k] if (c.x0 + c.x1) / 2.0 >= mid for r in c.runs]
                pieces.append(_Piece("left", _rows(left), (s0, s1), lo == 0, hi == len(rows) - 1))
                pieces.append(_Piece("right", _rows(right), (s0, s1), lo == 0, hi == len(rows) - 1))
                cursor = hi + 1
            if cursor < len(rows):
                pieces.append(_Piece("text", rows[cursor:]))
            return pieces
    return [_Piece("text", block) for block in _blocks(runs)]


def _continues(before: List[_Piece], after: List[_Piece]) -> bool:
    """Does a band of two columns at the end of a page go on in a band at the top of the next page? (the same strip, the band touches the edge of the page)"""
    if len(before) < 2 or len(after) < 2:
        return False
    b_left, b_right, a_left, a_right = before[-2], before[-1], after[0], after[1]
    if (b_left.kind, b_right.kind, a_left.kind, a_right.kind) != ("left", "right", "left", "right"):
        return False
    if not (b_right.at_bottom and a_left.at_top) or b_left.strip is None or a_left.strip is None:
        return False
    return min(b_left.strip[1], a_left.strip[1]) - max(b_left.strip[0], a_left.strip[0]) >= 8.0


def _join_join(a: str, b: str) -> str:
    return (a.rstrip("\n") + "\n" + b.lstrip("\n")) if a.strip() and b.strip() else (a or b)


def _join_row(row: List[_Run]) -> str:
    out = ""
    last: Optional[_Run] = None
    for r in row:
        if last is not None:
            gap = r.x0 - last.x1
            size = max(r.size, last.size)
            if not out.endswith(" ") and not r.text.startswith(" ") and gap > 0.15 * size:
                out += "  " if gap > 3.0 * size else " "
        out += r.text
        last = r
    return out


def _render_rows(rows: List[List[_Run]]) -> str:
    lines: List[str] = []
    prev: Optional[_Run] = None
    for row in rows:
        text = _join_row(row)
        if not text.strip():
            continue
        if prev is not None and prev.y - row[0].y > 1.9 * max(prev.size, row[0].size):
            lines.append("")        # a gap that is bigger than a line: a new paragraph
        lines.append(text)
        prev = row[0]
    return "\n".join(lines)


def _unique_runs(runs: List[_Run]) -> List[_Run]:
    """Bold text is sometimes drawn twice at almost the same place. Keep one."""
    seen = set()
    out = []
    for r in runs:
        key = (r.text, int(r.x0 // 2), int(r.y // 2))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _page_pieces_of(pdf: _Pdf, page: Dict[str, Any]) -> List[_Piece]:
    """The pieces of text of one page, in reading order. Spaces and line breaks come from the glyph widths and the positions."""
    runs = _unique_runs(_page_runs(pdf, page))
    if not runs:
        return []
    try:
        return _page_pieces(runs)
    except Exception:  # noqa: BLE001 - a layout that we do not understand: use the order of the file
        return [_Piece("text", [[r] for r in runs])]


def _page_text(pdf: _Pdf, page: Dict[str, Any]) -> str:
    return "\n\n".join(p.text for p in _page_pieces_of(pdf, page) if p.text.strip())


def _pdf_text(data: bytes) -> str:
    pdf = _Pdf(data)
    pieces: List[_Piece] = []
    for page in pdf.pages()[:_MAX_PAGES]:
        try:
            page_pieces = _page_pieces_of(pdf, page)
        except Exception:  # noqa: BLE001 - a bad page must not stop the other pages
            continue
        if _continues(pieces, page_pieces):
            # the two columns of a band go on at the top of this page: the left columns are read together, then the right columns
            pieces[-2].text = _join_join(pieces[-2].text, page_pieces[0].text)
            pieces[-1].text = _join_join(pieces[-1].text, page_pieces[1].text)
            pieces[-2].at_bottom = pieces[-1].at_bottom = page_pieces[1].at_bottom
            pieces[-2].strip = pieces[-1].strip = page_pieces[1].strip
            page_pieces = page_pieces[2:]
        pieces.extend(page_pieces)
    text = "\n\n".join(p.text for p in pieces if p.text.strip())
    if len(text.strip()) < 20:
        text = _pdf_text_optional(data) or text
    return text


def _pdf_text_optional(data: bytes) -> str:
    """Use pypdf when it is installed. The platform does not need it."""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:  # noqa: BLE001
        return ""
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages[:30])
    except Exception:  # noqa: BLE001
        return ""
