"""Reading text from PDF and DOCX files, and the CV and job description readers."""
import io
import unittest
import zipfile
import zlib

import helpers as H
from jinder import cv_parser, jd_parser, textextract as T


def type0_pdf(text: str) -> bytes:
    """A PDF with a Type0 font, a ToUnicode CMap, a compressed content stream and an object stream (like a browser's PDF)."""
    chars = sorted(set(text))
    code = {c: i + 1 for i, c in enumerate(chars)}
    cmap = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n1 begincodespacerange <0000> <FFFF> endcodespacerange\n"
            f"{len(chars)} beginbfchar\n" + "\n".join(f"<{code[c]:04X}> <{ord(c):04X}>" for c in chars) + "\nendbfchar\nendcmap end end").encode()
    hexs = "".join(f"{code[c]:04X}" for c in text)
    # Letters at 500 units, spaces at 250 units, in a TJ array with one number between the words
    content = f"BT /F1 12 Tf 1 0 0 1 50 780 Tm [<{hexs}>] TJ ET".encode()
    w_array = "[" + " ".join(f"{code[c]} [{250 if c == ' ' else 500}]" for c in chars) + "]"
    font_dicts = [
        "<< /Type /Font /Subtype /Type0 /BaseFont /Test /Encoding /Identity-H /DescendantFonts [6 0 R] /ToUnicode 7 0 R >>",
        f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /Test /DW 1000 /W {w_array} >>",
    ]
    # Objects 5 and 6 live inside an object stream (number 8)
    parts, offsets, pos = [], [], 0
    for d in font_dicts:
        offsets.append(pos)
        parts.append(d + "\n")
        pos += len(d) + 1
    head = f"5 {offsets[0]} 6 {offsets[1]} "
    objstm = (head + "".join(parts)).encode()
    objs = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    }
    out = b"%PDF-1.5\n"
    for n, body in objs.items():
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    for n, data, extra in ((4, content, ""), (7, cmap, ""), (8, objstm, f"/Type /ObjStm /N 2 /First {len(head)} ")):
        z = zlib.compress(data)
        out += f"{n} 0 obj\n<< {extra}/Filter /FlateDecode /Length {len(z)} >>\nstream\n".encode() + z + b"\nendstream\nendobj\n"
    return out + b"trailer\n<< /Size 9 /Root 1 0 R >>\n%%EOF"


class ExtractTests(unittest.TestCase):
    def test_sniff_trusts_the_bytes(self):
        self.assertEqual(T.sniff(H.make_docx(["hello world"])), "docx")
        self.assertEqual(T.sniff(H.make_pdf(["hello world"])), "pdf")
        self.assertEqual(T.sniff(b"hello"), "")
        self.assertEqual(T.sniff(b"PK\x03\x04 not a zip"), "")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("other.txt", "x")
        self.assertEqual(T.sniff(buf.getvalue()), "")  # a zip file that is not a DOCX

    def test_docx_text_entities_and_breaks(self):
        data = H.make_docx(["Fish &amp; Chips Manager", "Line two with a tab"])
        text = T.extract_text(data)
        self.assertEqual(text.splitlines()[0], "Fish & Chips Manager")
        self.assertEqual(len(text.splitlines()), 2)

    def test_docx_with_an_entity_bomb_is_harmless(self):
        xml = ('<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>'
               '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>&lol2;&lol2; visible text here ok</w:t></w:r></w:p></w:body></w:document>')
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml", xml)
        text = T.extract_text(buf.getvalue())
        self.assertIn("visible text here ok", text)
        self.assertLess(len(text), 200)

    def test_an_empty_or_broken_file_raises(self):
        for data in (b"", b"hello world this is plain text", b"%PDF-1.4\n%%EOF", H.make_docx([""])):
            with self.assertRaises(T.UnreadableFile):
                T.extract_text(data)

    def test_simple_pdf(self):
        text = T.extract_text(H.make_pdf(["First line of the CV", "Second line follows here"]))
        self.assertEqual(text.splitlines(), ["First line of the CV", "Second line follows here"])

    def test_pdf_with_type0_font_to_unicode_and_object_streams(self):
        text = T.extract_text(type0_pdf("Operations Team Lead at North Star"))
        self.assertEqual(text, "Operations Team Lead at North Star")

    def test_pdf_escape_sequences(self):
        pdf = H.make_pdf(["Plus (parentheses) and a back\\slash in text", "Café résumé"])
        text = T.extract_text(pdf)
        self.assertIn("Plus (parentheses) and a back\\slash in text", text)

    def test_the_text_is_cut_at_a_limit(self):
        long = H.make_docx(["word " * 100] * 3000)
        self.assertLessEqual(len(T.extract_text(long)), T.MAX_TEXT_CHARS)


class CvReaderTests(unittest.TestCase):
    def test_roles_and_noise(self):
        text = "\n".join(["Jane Doe", "jane@example.test | +61 400 000 000", "EXPERIENCE", "Senior Business Analyst - Example Bank Ltd (Jan 2018 - Present)",
                          "Led requirements gathering for a loan system change used by 3,000 staff.", "Business Analyst, Sample Finance (2014 - 2017)",
                          "EDUCATION", "Master of Statistics, University of Pune, India, 2012 - 2014", "SKILLS", "SQL, Power BI, UAT, Process mapping"])
        r = cv_parser.parse_cv(text)
        f = r["fields"]
        self.assertEqual(f["currentRole"][0], "Senior Business Analyst")
        self.assertEqual(f["qualification"], ["Master's degree"])
        self.assertEqual(f["studyCountry"], ["India"])
        self.assertEqual(f["years"], "More than 10 years")  # 2014 to 2017 and 2018 to now: about 12 years
        self.assertNotIn("jane@example.test", str(r))

    def test_years_band_from_overlapping_ranges(self):
        text = "EXPERIENCE\nAnalyst - A Pty Ltd (2020 - 2022)\nAnalyst - B Pty Ltd (2021 - 2023)\nEDUCATION\nBachelor of Commerce, Some University, 2015 - 2019"
        years, total = cv_parser.read_years(text.splitlines()[:3], text.splitlines())
        self.assertEqual(years, "3–5 years")      # 2020 to 2023 counted once
        self.assertLess(total, 5)

    def test_nothing_is_invented(self):
        r = cv_parser.parse_cv("Just a few words about me and my hobbies, nothing about work or school at all here.")
        self.assertEqual(r["fields"].get("years"), None)
        self.assertIn("years", r["missing"])
        self.assertIn("qualification", r["missing"])
        self.assertEqual(r["evidence"], [])

    def test_evidence_has_no_contact_details(self):
        r = cv_parser.parse_cv("EXPERIENCE\nOperations Lead - X (2019 - 2022)\nManaged the team and emailed boss@example.test about 12 projects every month.\nCalled suppliers on +61 400 123 456 to fix 4 delivery issues.")
        for line in r["evidence"]:
            self.assertNotIn("@", line)
            self.assertNotRegex(line, r"\d{3} \d{3}")

    def test_job_description_reader(self):
        r = jd_parser.parse_jd("Data Analyst\nA 6-month contract in Sydney. Build dashboards in Power BI, write SQL queries and clean data with Python. $700 per day.")
        f = r["fields"]
        self.assertEqual((f["title"], f["type"], f["location"], f["salary"]), ("Data Analyst", "Contract", "Sydney", "$700 per day"))
        self.assertIn(f["category"], ("Technology & Data", "Data"))        # the list of categories is the platform's: the old name or the domain
        self.assertEqual(f["domain"], "Data")
        self.assertIn("SQL", f["skills"])
        self.assertEqual(r["missing"], [])
        r = jd_parser.parse_jd("Warehouse Supervisor\nLead a team of 12 and plan daily schedules and inventory accuracy for our distribution centre.")
        self.assertIn("location", r["missing"])
        self.assertIn("salary", r["missing"])
        self.assertIn(r["fields"].get("category", ""), ("Supply Chain & Logistics", ""))


if __name__ == "__main__":
    unittest.main()


class BrowserPdfTests(unittest.TestCase):
    """A PDF that a browser made (compressed streams, Type0 fonts, ToUnicode maps, object streams). The people are made up."""

    def test_browser_made_cv(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "fixtures", "cv-browser-made.pdf")
        text = T.extract_text(open(path, "rb").read())
        self.assertIn("Senior Business Analyst – Example Bank Ltd | Jan 2018 – Present", text)
        self.assertIn("Master of Statistics, University of Pune, India, 2012 – 2014", text)
        f = cv_parser.parse_cv(text)["fields"]
        self.assertEqual((f["qualification"], f["studyCountry"], f["fieldOfStudy"]), (["Master's degree"], ["India"], ["Statistics"]))
        self.assertEqual(f["currentRole"], ["Senior Business Analyst", "Business Analyst"])
        self.assertIn("Power BI", f["skills"])


# =====================================================================
# Version 2 (item R1): the reading order of a page, the glyphs, the encodings, and the DOCX parts
# =====================================================================
import importlib.util  # noqa: E402
import os  # noqa: E402

_spec = importlib.util.spec_from_file_location("make_cv_fixtures", os.path.join(os.path.dirname(__file__), "fixtures", "make_cv_fixtures.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)
_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "cv")


def fixture_text(name):
    with open(os.path.join(_FIXTURES, name), "rb") as f:
        return T.extract_text(f.read())


def _raw_pdf(content, font="<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"):
    """A one-page PDF with this content stream and this font dictionary (no /Widths in the default font)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}\nendstream", font]
    out = b"%PDF-1.4\n"
    for i, o in enumerate(objs, 1):
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    return out + b"trailer\n<< /Size 6 /Root 1 0 R >>\n%%EOF"


def _docx_with_parts(body_xml, header_paragraphs):
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"/>")
        z.writestr("word/document.xml", f"<w:document {ns}><w:body>{body_xml}</w:body></w:document>")
        for k, p in enumerate(header_paragraphs, 1):
            z.writestr(f"word/header{k}.xml", f"<w:hdr {ns}>{p}</w:hdr>")
    return buf.getvalue()


class ReadingOrderTests(unittest.TestCase):
    def test_two_columns_are_read_one_after_the_other(self):
        text = fixture_text("cv02_two_column_interleaved.pdf")
        for line in text.splitlines():       # no line has text of the left column and of the right column
            self.assertFalse("Python" in line and "ranking" in line, line)
        self.assertLess(text.index("SKILLS"), text.index("Amazon SageMaker"))
        self.assertLess(text.index("Amazon SageMaker"), text.index("LANGUAGES"))
        self.assertLess(text.index("LANGUAGES"), text.index("PROFILE"))        # the whole left column, then the right column
        self.assertLess(text.index("PROFILE"), text.index("EXPERIENCE"))

    def test_a_header_over_two_columns_comes_first(self):
        self.assertEqual(fixture_text("cv02_two_column_interleaved.pdf").splitlines()[:2], ["MIRA SAMPLE", "Machine Learning Engineer"])

    def test_a_sidebar_that_is_written_first_is_read_after_the_column_with_the_name(self):
        text = fixture_text("cv03_sidebar_first.pdf")
        self.assertEqual(text.splitlines()[:2], ["SOFIA EXAMPLE", "Full Stack Developer"])
        self.assertLess(text.index("WORK EXPERIENCE"), text.index("CONTACT"))
        text = fixture_text("cv07_linkedin_export.pdf")
        self.assertEqual(text.splitlines()[0], "Lena Placeholder")
        self.assertLess(text.index("Experience"), text.index("Top Skills"))

    def test_the_right_column_that_is_written_first_is_read_second(self):
        text = fixture_text("cv23_two_equal_columns_right_first.pdf")
        self.assertLess(text.index("EXPERIENCE"), text.index("EDUCATION"))
        self.assertLess(text.index("Built a Power BI report"), text.index("EDUCATION"))

    def test_dates_in_a_margin_stay_on_the_line_of_their_text(self):
        text = fixture_text("cv22_latex_timeline.pdf")          # dates in a left column, headings in the margin
        self.assertIn("2022 – present Machine Learning Engineer, Fernhill Systems", text)
        self.assertIn("2019 – 2022 Data Scientist, Quokka Labs", text)
        self.assertIn("Skills Python, PyTorch, scikit-learn, MLflow, Kubernetes, SQL", text)

    def test_dates_at_the_right_margin_stay_on_the_line_of_their_title(self):
        pdf = G.Pdf()
        page = pdf.page()
        y = 780
        for k in range(14):
            page.t(50, y, f"Senior Data Engineer number {k} | Acme Pty Ltd", 10, True)
            page.t(470, y, f"Jan 20{10 + k} – Present", 10)
            page.t(60, y - 13, "• Built pipelines for the finance team and the sales team every day.", 10)
            y -= 40
        text = T.extract_text(pdf.build())
        for k in range(14):
            self.assertIn(f"Senior Data Engineer number {k} | Acme Pty Ltd Jan 20{10 + k} – Present", text)

    def test_the_visual_order_wins_over_the_order_in_the_file(self):
        pdf = G.Pdf()
        page = pdf.page()
        page.t(50, 600, "SUMMARY", 11, True)
        page.t(50, 585, "Builds data platforms for small teams.", 10)
        page.t(50, 790, "ALEX SAMPLE", 20, True)       # the title is drawn last, but it is at the top of the page
        page.t(50, 770, "Data Engineer", 12)
        text = T.extract_text(pdf.build())
        self.assertEqual(text.splitlines()[:2], ["ALEX SAMPLE", "Data Engineer"])

    def test_a_page_with_a_flipped_y_axis_and_a_form_xobject(self):
        text = fixture_text("cv20_flipped_form_header.pdf")
        self.assertEqual(text.splitlines()[:2], ["IMANI SAMPLE", "Staff Software Engineer"])
        self.assertLess(text.index("EXPERIENCE"), text.index("EDUCATION"))

    def test_only_the_first_pages_are_read(self):
        pdf = G.Pdf()
        for k in range(45):
            pdf.page().t(50, 700, f"Text of page number {k} in a long file", 10)
        text = T.extract_text(pdf.build())
        self.assertIn("page number 39 ", text)
        self.assertNotIn("page number 41 ", text)

    def test_text_that_is_drawn_twice_to_look_bold_is_read_once(self):
        pdf = G.Pdf()
        page = pdf.page()
        page.t(50, 700, "Senior Data Engineer", 12, True)
        page.t(50.4, 700.3, "Senior Data Engineer", 12, True)
        self.assertEqual(T.extract_text(pdf.build()).count("Senior Data Engineer"), 1)

    def test_a_long_gap_inside_one_string_cuts_the_text_into_two_columns(self):
        content = ["BT /F1 10 Tf"]
        for k in range(14):
            content.append(f"1 0 0 1 50 {780 - 16 * k} Tm [(Left column text for the line number {k}) -9000 (Right column text for the line number {k})] TJ")
        content.append("ET")
        text = T.extract_text(_raw_pdf("\n".join(content)))
        self.assertLess(text.index("Left column text for the line number 13"), text.index("Right column text for the line number 0"))
        self.assertNotIn("number 0 Right", text)

    def test_short_cells_that_share_a_line_stay_in_their_row(self):
        # A table of short cells (a title and a place, a skill and a level) is read row by row, not column by column
        content = ["BT /F1 10 Tf"]
        for k in range(14):
            content.append(f"1 0 0 1 50 {780 - 16 * k} Tm [(Skill {k}) -9000 (Level {k})] TJ")
        content.append("ET")
        text = T.extract_text(_raw_pdf("\n".join(content)))
        self.assertIn("Skill 0 Level 0", text)
        self.assertIn("Skill 13 Level 13", text)

    # ----- a band of two columns in a page of one column (D-1 of QA: the own CV of the user) -----
    @staticmethod
    def _one_column_page(page, top=780, lines=14, x=45):
        """Lines that cross the middle of the page (a page of one column)."""
        y = top
        for k in range(lines):
            page.t(x, y, f"Line {k} of a long paragraph in one column that goes over the middle of the page and ends near the right edge ok", 10)
            y -= 14
        return y

    def test_a_band_of_two_columns_in_one_column_text_is_read_column_by_column(self):
        text = fixture_text("cv24_two_page_band.pdf")
        for line in text.splitlines():           # no line has text of the left column and of the right column
            self.assertFalse(("Certificate" in line and "WORK RIGHTS" in line) or ("Associate" in line and "Spanish" in line), line)
        self.assertLess(text.index("CERTIFICATIONS"), text.index("Microsoft Certified: Azure Data Scientist\nAssociate (DP-100), 2024"))
        self.assertLess(text.index("Associate (DP-100), 2024"), text.index("Northwind Analytics Professional Certificate,\n2022"))     # the left column goes on on page 2
        self.assertLess(text.index("Northwind Analytics Professional Certificate"), text.index("LANGUAGES"))                                 # before the right column
        self.assertLess(text.index("LANGUAGES"), text.index("WORK RIGHTS AND AVAILABILITY"))
        self.assertLess(text.index("WORK RIGHTS AND AVAILABILITY"), text.index("PROJECTS"))                                                 # then the one column again
        self.assertLess(text.index("Open to remote and hybrid roles"), text.index("PROJECTS"))

    def test_the_text_before_and_after_a_band_keeps_its_place(self):
        text = fixture_text("cv24_two_page_band.pdf")
        self.assertEqual(text.splitlines()[0], "MAYA TESTBRIDGE")
        self.assertLess(text.index("Professional skills:"), text.index("CERTIFICATIONS"))
        self.assertLess(text.index("PROJECTS"), text.index("AWARDS"))
        self.assertIn("Senior Data Analyst, Quokka Insights Pty Ltd Mar 2021 – Present", text)         # a title and its dates stay on one line

    def test_a_band_on_one_page_is_split_and_a_band_of_two_lines_is_not(self):
        pdf = G.Pdf()
        page = pdf.page()
        y = self._one_column_page(page)
        for k in range(3):
            page.t(45, y - 14 * k, f"Left column of the band, line number {k}", 10)
            page.t(306, y - 14 * k, f"Right column of the band, line number {k}", 10)
        y -= 14 * 3
        page.t(45, y - 14, "Back in one column: a long line that crosses the middle of the page and goes on to the right edge", 10)
        text = T.extract_text(pdf.build())
        self.assertLess(text.index("Left column of the band, line number 2"), text.index("Right column of the band, line number 0"))
        pdf = G.Pdf()
        page = pdf.page()
        y = self._one_column_page(page)
        for k in range(2):
            page.t(45, y - 14 * k, f"Left column of two lines, number {k}", 10)
            page.t(306, y - 14 * k, f"Right column of two lines, number {k}", 10)
        text = T.extract_text(pdf.build())
        self.assertIn("Left column of two lines, number 0 Right column of two lines, number 0", text)

    def test_a_table_of_short_cells_or_a_timeline_is_not_a_band(self):
        pdf = G.Pdf()
        page = pdf.page()
        y = self._one_column_page(page)
        for k in range(5):
            page.t(45, y - 14 * k, f"Skill {k}", 10)
            page.t(306, y - 14 * k, f"Expert {k}", 10)
        for k in range(4):
            page.t(45, y - 100 - 30 * k, f"Jan 20{10 + k} – Dec 20{11 + k}", 10)
            page.t(306, y - 100 - 30 * k, f"Senior Analyst number {k}, Acme Pty Ltd, Sydney, Australia", 10)
        text = T.extract_text(pdf.build())
        self.assertIn("Skill 0 Expert 0", text)
        self.assertIn("Skill 4 Expert 4", text)
        self.assertIn("Jan 2010 – Dec 2011 Senior Analyst number 0, Acme Pty Ltd, Sydney, Australia", text)

    def test_a_heading_at_the_left_edge_below_a_band_is_not_part_of_the_left_column(self):
        pdf = G.Pdf()
        page = pdf.page()
        y = self._one_column_page(page)
        for k in range(3):
            page.t(58, y - 14 * k, f"Left column entry {k} with a few more words", 10)
            page.t(320, y - 14 * k, f"Right column entry {k} with a few more words", 10)
        page.t(45, y - 70, "NEXT HEADING", 11.5, True)
        page.t(58, y - 90, "A long line of the next part of the page that goes over the middle of the page and on to the right side", 10)
        text = T.extract_text(pdf.build())
        self.assertLess(text.index("Right column entry 2"), text.index("NEXT HEADING"))
        self.assertLess(text.index("NEXT HEADING"), text.index("A long line of the next part"))

    def test_two_bands_on_two_pages_are_joined_only_when_they_touch_the_edges_and_share_a_strip(self):
        def band(page, y0, x_right, label, words):
            for k in range(3):
                page.t(58, y0 - 14 * k, f"Left {label} entry {k} {words}", 10)
                page.t(x_right, y0 - 14 * k, f"Right {label} entry {k} {words}", 10)

        def two_pages(closing_line, right_two, words_two):
            pdf = G.Pdf()
            p1 = pdf.page()
            y = self._one_column_page(p1, top=780, lines=46) if not closing_line else self._one_column_page(p1)
            band(p1, y if closing_line else 130, 320, "one", "and some words")
            if closing_line:
                p1.t(45, y - 90, "Closing line of page one that is long and goes over the middle of the page to the right side ok", 10)
            p2 = pdf.page()
            band(p2, 786, right_two, "two", words_two)
            self._one_column_page(p2, top=700)
            return T.extract_text(pdf.build())

        # the same strip, the first band at the bottom of page 1 and the second at the top of page 2: the left columns, then the right columns
        text = two_pages(False, 320, "and some words")
        self.assertLess(text.index("Left two entry 2"), text.index("Right one entry 0"))
        self.assertLess(text.index("Left one entry 2"), text.index("Left two entry 0"))
        # the band of page 1 does not touch the bottom of the page: not joined
        text = two_pages(True, 320, "and some words")
        self.assertLess(text.index("Right one entry 2"), text.index("Left two entry 0"))
        # the strips are not the same: not joined
        text = two_pages(False, 200, "abc")
        self.assertLess(text.index("Right one entry 2"), text.index("Left two entry 0"))

    def test_a_cv_with_a_band_gives_both_certifications(self):
        # The certifications of the two columns of the band are found, and nothing of the other column is in their names
        r = cv_parser.parse_cv(fixture_text("cv24_two_page_band.pdf"))
        names = [c["name"] for c in r["certifications"]]
        self.assertEqual(names, ["Microsoft Certified: Azure Data Scientist Associate", "Northwind Analytics Professional Certificate"])
        self.assertEqual([c["year"] for c in r["certifications"]], [2024, 2022])

    def test_the_widths_of_helvetica_are_used_when_a_font_has_no_widths(self):
        # Each word is drawn alone. Without the widths of the font, the space between two words cannot be found.
        words = ["Senior", "Data", "Engineer", "at", "Kestrel", "Analytics"]
        content = ["BT /F1 12 Tf"]
        x = 50.0
        for w in words:
            content.append(f"1 0 0 1 {x:.2f} 700 Tm ({w}) Tj")
            x += sum(G.HELV[ord(c) - 32] for c in w + " ") * 12 / 1000.0
        content.append("ET")
        self.assertEqual(T.extract_text(_raw_pdf("\n".join(content) + "\n% padding to be long enough")), "Senior Data Engineer at Kestrel Analytics")


class GlyphAndEncodingTests(unittest.TestCase):
    def test_ligatures_become_letters(self):
        text = fixture_text("cv16_ligatures_hyphen_pua.pdf")
        self.assertIn("financial rules and flow control", text)
        self.assertIn("Certified Kubernetes Administrator", text)
        self.assertNotRegex(text, "[ﬀ-ﬆ]")

    def test_a_bullet_from_a_symbol_font_becomes_a_bullet(self):
        text = fixture_text("cv16_ligatures_hyphen_pua.pdf")
        self.assertIn("• Built a payment platform", text)
        self.assertNotRegex(text, "[\ue000-\uf8ff]")
        self.assertEqual(T._tidy("\uf0b7 Led a team\nphone \uf095 +61 400"), "• Led a team\nphone +61 400")

    def test_a_word_cut_at_the_end_of_a_line_is_joined(self):
        text = fixture_text("cv16_ligatures_hyphen_pua.pdf")
        self.assertIn("Experienced engineer\nwho builds payment platforms", text)
        self.assertIn("handled 4 million\ntransactions per day", text)

    def test_a_hyphenated_compound_keeps_its_hyphen(self):
        self.assertEqual(T._tidy("a full-\nstack developer"), "a full-stack\ndeveloper")
        self.assertEqual(T._tidy("a data-\ndriven team"), "a data-driven\nteam")
        self.assertEqual(T._tidy("an experi-\nenced engineer"), "an experienced\nengineer")
        self.assertEqual(T._tidy("an expe\u00ad\nrienced engineer"), "an experienced\nengineer")

    def test_a_dash_with_a_space_is_not_a_cut_word(self):
        self.assertEqual(T._tidy("Python -\nSQL"), "Python -\nSQL")
        self.assertEqual(T._tidy("2019 -\n2021"), "2019 -\n2021")
        self.assertEqual(T._tidy("Skills:\n- Python"), "Skills:\n- Python")

    def test_odd_spaces_and_zero_width_marks(self):
        self.assertEqual(T._tidy("Senior\u00a0Data\u2009Engineer\u200b ok"), "Senior Data Engineer ok")

    def test_letters_with_marks_are_composed(self):
        self.assertEqual(T._tidy("Nguyễn"), "Nguyễn")
        self.assertIn("Nguyễn Minh Anh", fixture_text("cv05_title_above_name_vi.pdf"))

    def test_an_encoding_with_a_differences_list(self):
        text = fixture_text("cv22_latex_timeline.pdf")           # the en dash is code 128, named endash
        self.assertIn("Sydney, Australia – yuki.typeset@example.test – +61 400 000 022", text)
        self.assertEqual(T._glyph_char("bullet"), "•")
        self.assertEqual(T._glyph_char("endash"), "–")
        self.assertEqual(T._glyph_char("eacute"), "é")
        self.assertEqual(T._glyph_char("uni1EC5"), "ễ")
        self.assertEqual(T._glyph_char("fi"), "fi")
        self.assertEqual(T._glyph_char("g123"), "")

    def test_the_mac_roman_encoding(self):
        font = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /MacRomanEncoding >>"
        data = _raw_pdf("BT /F1 12 Tf 1 0 0 1 50 700 Tm (Caf\\216 and na\\225ve bullet \\245) Tj ET", font)
        self.assertEqual(T.extract_text(data + b"\n% pad pad pad pad pad"), "Café and naïve bullet •")

    def test_windows_code_page_is_the_default(self):
        data = _raw_pdf("BT /F1 12 Tf 1 0 0 1 50 700 Tm (Senior \\226 Data \\225 Engineer) Tj ET")
        self.assertEqual(T.extract_text(data + b"\n% pad pad pad pad pad"), "Senior – Data • Engineer")


class DocxPartsTests(unittest.TestCase):
    def test_the_header_part_is_read_first_and_once(self):
        text = fixture_text("cv11_docx_textbox_header.docx")
        self.assertEqual(text.splitlines()[:2], ["HANA PLACEHOLDER", "Sr. Cloud Engineer"])
        self.assertEqual(text.count("HANA PLACEHOLDER"), 1)

    def test_a_header_line_that_the_body_has_is_not_repeated(self):
        body = '<w:p><w:r><w:t>Alex Sample</w:t></w:r></w:p><w:p><w:r><w:t>Data Engineer</w:t></w:r></w:p>'
        data = _docx_with_parts(body, ['<w:p><w:r><w:t>Alex Sample</w:t></w:r></w:p>', '<w:p><w:r><w:t>Alex Sample</w:t></w:r></w:p>'])
        self.assertEqual(T.extract_text(data).splitlines(), ["Alex Sample", "Data Engineer"])

    def test_a_text_box_is_read_once(self):
        text = fixture_text("cv11_docx_textbox_header.docx")
        self.assertEqual(text.count("hana.placeholder@example.test"), 1)
        self.assertEqual(text.count("+61 400 000 011"), 1)

    def test_in_a_table_row_the_cell_with_the_biggest_text_is_read_first(self):
        text = fixture_text("cv10_docx_table_two_column.docx")
        self.assertEqual(text.splitlines()[:2], ["RAVI SAMPLETON", "Data Analyst"])
        self.assertLess(text.index("EXPERIENCE"), text.index("CONTACT"))

    def test_a_table_row_with_equal_text_keeps_its_order(self):
        def cell(t):
            return f'<w:tc><w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{t}</w:t></w:r></w:p></w:tc>'
        body = f"<w:tbl><w:tr>{cell('First cell')}{cell('Second cell')}</w:tr></w:tbl><w:p><w:r><w:t>and some more text</w:t></w:r></w:p>"
        self.assertEqual(T.extract_text(_docx_with_parts(body, [])).splitlines()[:2], ["First cell", "Second cell"])

    def test_a_symbol_bullet_and_a_tab(self):
        text = fixture_text("cv09_docx_simple.docx")
        self.assertIn("• Built features for a patient portal in Java and React.", text)
        self.assertIn("Graduate Software Developer, Banksia Health Tech Feb 2025 – Present", text)

    def test_soft_and_hard_hyphens_in_a_docx(self):
        body = '<w:p><w:r><w:t>Full</w:t><w:noBreakHyphen/><w:t>stack engi</w:t><w:softHyphen/><w:t>neer with enough text here</w:t></w:r></w:p>'
        self.assertEqual(T.extract_text(_docx_with_parts(body, [])), "Full-stack engineer with enough text here")

    def test_at_most_6_header_parts_are_read(self):
        body = '<w:p><w:r><w:t>Alex Sample, a data engineer with a short text</w:t></w:r></w:p>'
        headers = ['<w:p><w:r><w:t>Header %d</w:t></w:r></w:p>' % k for k in range(20)]
        text = T.extract_text(_docx_with_parts(body, headers))
        self.assertLessEqual(text.count("Header"), 6)


class JobDescriptionFilesTests(unittest.TestCase):
    def test_a_long_paragraph_of_a_docx_job_description_is_not_cut(self):
        paragraph = "We build a platform for water utilities and regional councils. " * 12        # 780 characters in one paragraph
        data = H.make_docx(["Data Engineer", "About the role", paragraph, "What you bring:", "- 5 to 9 years in data engineering.", "- Python at an advanced level (4 of 5)."])
        r = jd_parser.parse_jd(T.extract_text(data))["fields"]
        self.assertIn(paragraph.strip(), r["description"])
        self.assertTrue(r["description"].startswith("## About the role"))
        self.assertIn("## What you bring", r["description"])
        self.assertEqual((r["minYears"], r["maxYears"]), (5, 9))
