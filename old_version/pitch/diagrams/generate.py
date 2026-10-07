"""Generate pitch-ready Skill Bridge diagrams.

The workflow uses the team-approved source PNG. The low-resolution data-model
JPG remains in assets/ as the visual reference, while this script redraws that
diagram at 1700x980 so all labels stay crisp and reproducible.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


DIAGRAM_DIR = Path(__file__).resolve().parent
ASSET_DIR = DIAGRAM_DIR / "assets"
WIDTH, HEIGHT = 1700, 980

BG = "#FFFFFF"
INK = "#20242A"
MUTED = "#6C737D"
LINE = "#C8CDD3"
RAW = "#5A6067"
REFERENCE = "#9A6515"
SILVER = "#50545A"
GOLD = "#A68A16"
RAW_FILL = "#F7F8F8"
REFERENCE_FILL = "#FFF8EE"
SILVER_FILL = "#F7F7F9"
GOLD_FILL = "#FFFCED"
BLUE = "#315EB0"
TEAL = "#087C6B"


def font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.ImageFont:
    """Load a readable font on macOS or Linux."""
    if bold:
        mac_name = "Arial Bold.ttf"
        linux_name = "DejaVuSans-Bold.ttf"
    elif italic:
        mac_name = "Arial Italic.ttf"
        linux_name = "DejaVuSans-Oblique.ttf"
    else:
        mac_name = "Arial.ttf"
        linux_name = "DejaVuSans.ttf"
    candidates = [
        Path("/System/Library/Fonts/Supplemental") / mac_name,
        Path("/usr/share/fonts/truetype/dejavu") / linux_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


TITLE = font(38, bold=True)
SUBTITLE = font(15)
COLUMN_TITLE = font(17, bold=True)
ITEM_TITLE = font(15, bold=True)
ITEM_BODY = font(11)
SECTION = font(17, bold=True)
LEGEND = font(11)
LEGEND_BOLD = font(11, bold=True)


def wrap(draw: ImageDraw.ImageDraw, text: str, max_width: int, text_font: ImageFont.ImageFont) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_item(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    number: int,
    title: str,
    body: str,
    accent: str,
) -> None:
    x1, y1, x2, y2 = bounds
    draw.rounded_rectangle(bounds, 8, fill=BG, outline=LINE, width=2)
    draw.ellipse((x1 + 14, y1 + 14, x1 + 38, y1 + 38), fill="#FFF7DB", outline=accent, width=2)
    label = str(number)
    label_box = draw.textbbox((0, 0), label, font=LEGEND_BOLD)
    draw.text(
        (x1 + 26 - (label_box[2] - label_box[0]) / 2, y1 + 26 - (label_box[3] - label_box[1]) / 2 - 1),
        label,
        font=LEGEND_BOLD,
        fill=accent,
    )
    draw.text((x1 + 50, y1 + 12), title, font=ITEM_TITLE, fill=INK)
    body_lines = wrap(draw, body, x2 - x1 - 68, ITEM_BODY)
    draw.multiline_text((x1 + 50, y1 + 37), "\n".join(body_lines[:2]), font=ITEM_BODY, fill=MUTED, spacing=3)


def draw_column(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    accent: str,
    fill: str,
    items: list[tuple[int, str, str]],
) -> None:
    x1, y1, x2, y2 = bounds
    draw.rounded_rectangle(bounds, 15, fill=fill, outline=accent, width=2)
    draw.text((x1 + 18, y1 + 16), title, font=COLUMN_TITLE, fill=accent)
    draw.text((x1 + 18, y1 + 43), subtitle, font=ITEM_BODY, fill=MUTED)
    item_y = y1 + 76
    for number, item_title, body in items:
        height = 78
        draw_item(draw, (x1 + 16, item_y, x2 - 16, item_y + height), number, item_title, body, accent)
        item_y += height + 14


def generate_workflow() -> Path:
    source = ASSET_DIR / "workflow-source.png"
    destination = DIAGRAM_DIR / "workflow.png"
    if not source.is_file():
        raise FileNotFoundError(f"Missing workflow source: {source}")
    with Image.open(source) as opened:
        ImageOps.exif_transpose(opened).convert("RGB").save(destination, "PNG", optimize=True)
    return destination


def generate_data_model() -> Path:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((56, 36), "Skill Bridge — Data Model", font=TITLE, fill=INK)
    draw.text(
        (58, 88),
        "Raw inputs become reviewed Reference and schema-conformant Silver artifacts before deterministic Gold views feed the UI.",
        font=SUBTITLE,
        fill=MUTED,
    )

    columns = [
        (
            (58, 145, 390, 680),
            "RAW",
            "unstructured, as submitted",
            RAW,
            RAW_FILL,
            [
                (1, "CV file (PDF/DOCX)", "Source: team-authored synthetic personas or consented candidate upload"),
                (2, "Ad hoc JD text", "Source: recruiter-owned JD or dated public job posting"),
            ],
        ),
        (
            (440, 145, 772, 680),
            "REFERENCE",
            "curated, static, human-reviewed",
            REFERENCE,
            REFERENCE_FILL,
            [
                (3, "Target role list", "Team decision: 2–3 roles chosen for the live demo"),
                (4, "Skill-pair mapping", "20–30 reviewed pairs grounded in ANZSCO, ESCO and O*NET"),
                (5, "Sample JD set", "Dated public SEEK, LinkedIn, Indeed or Jora postings by target role"),
            ],
        ),
        (
            (822, 145, 1154, 680),
            "SILVER",
            "structured, schema-conformant",
            SILVER,
            SILVER_FILL,
            [
                (6, "candidate_profile", "Derived by CV_EXTRACT_V1; field provenance and review state retained"),
                (7, "jd_profile_adhoc", "Derived by JD_EXTRACT_V1 from one recruiter-submitted JD"),
                (8, "jd_reference_skill_extract[]", "Derived offline by JD_EXTRACT_V1 from reviewed Reference JDs"),
            ],
        ),
        (
            (1204, 145, 1642, 680),
            "GOLD",
            "business-ready, feeds UI directly",
            GOLD,
            GOLD_FILL,
            [
                (9, "role_skill_frequency", "Deterministic count across reviewed JD Silver artifacts"),
                (10, "candidate_skill_profile", "Evidence-backed groups derived from Candidate Silver + Reference"),
                (11, "skill_gap_view", "Deterministic expected-skill difference with explicit empty state"),
                (12, "recruiter_match_view", "Per-skill match only; no aggregate candidate score"),
                (13, "recruiter_decision_log", "Append-only, recruiter-initiated human decision events"),
            ],
        ),
    ]
    for column in columns:
        draw_column(draw, *column)

    draw.text((58, 715), "How each artifact is produced", font=SECTION, fill=INK)
    draw.text((58, 743), "Numbers correspond to the badges above. Silver and Gold introduce no independent real-world facts.", font=SUBTITLE, fill=MUTED)

    legend_left = [
        ("[1] → [6]", "CV file → CV_EXTRACT_V1 → candidate_profile"),
        ("[2] → [7]", "Ad hoc JD → JD_EXTRACT_V1 → jd_profile_adhoc"),
        ("[5] → [8]", "Reference JDs → offline JD_EXTRACT_V1 batch"),
        ("[8] → [9]", "Deterministic per-role frequency aggregation"),
    ]
    legend_right = [
        ("[3]+[4]+[6] → [10]", "Target + mappings + evidence → candidate_skill_profile"),
        ("[9]+[10] → [11]", "Expected skills minus evidenced skills → skill_gap_view"),
        ("[7]+[10] → [12]", "One JD vs candidate skills → per-skill recruiter_match_view"),
        ("[12] → [13]", "Explicit recruiter action → append-only decision event"),
    ]
    for column_x, rows in ((58, legend_left), (870, legend_right)):
        y = 785
        for key, description in rows:
            draw.text((column_x, y), key, font=LEGEND_BOLD, fill=BLUE if column_x == 58 else TEAL)
            draw.text((column_x + 155, y), description, font=LEGEND, fill=INK)
            y += 35

    destination = DIAGRAM_DIR / "data-model.png"
    image.save(destination, "PNG", optimize=True)
    return destination


def validate(path: Path, expected_size: tuple[int, int]) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Diagram was not generated: {path}")
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != expected_size:
            raise RuntimeError(f"Invalid output {path}: {image.format}, {image.size}")


def main() -> None:
    workflow = generate_workflow()
    data_model = generate_data_model()
    validate(workflow, (1700, 980))
    validate(data_model, (WIDTH, HEIGHT))
    for output in (workflow, data_model):
        print(f"Generated {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
