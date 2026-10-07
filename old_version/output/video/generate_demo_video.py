"""Build a silent, captioned 720p Skill Bridge demo video from verified UI captures."""

from pathlib import Path
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"
OUTPUT = HERE / "Skill_Bridge_Khoa_Product_Owner_Demo.mp4"
WIDTH, HEIGHT, FPS = 1280, 720, 24
TEAL = "#073c3a"
MINT = "#8ce0d8"
ORANGE = "#f47b3c"
WHITE = "#ffffff"
INK = "#102a2a"


def font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def cover(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    scale = max(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def wrap(draw: ImageDraw.ImageDraw, text: str, text_font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
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


def caption(image: Image.Image, eyebrow: str, title: str, detail: str) -> Image.Image:
    image = image.copy().convert("RGB")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, HEIGHT - 170, WIDTH, HEIGHT), fill=(7, 60, 58, 242))
    draw.rectangle((0, HEIGHT - 170, 9, HEIGHT), fill=ORANGE)
    draw.text((40, HEIGHT - 145), eyebrow.upper(), font=font(17, True), fill=MINT)
    draw.text((40, HEIGHT - 112), title, font=font(31, True), fill=WHITE)
    detail_lines = wrap(draw, detail, font(18), WIDTH - 80)
    for index, line in enumerate(detail_lines[:2]):
        draw.text((40, HEIGHT - 67 + index * 24), line, font=font(18), fill="#d7ece9")
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def title_card() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), TEAL)
    draw = ImageDraw.Draw(image)
    draw.ellipse((900, -230, 1430, 300), outline="#0d6d67", width=70)
    draw.rounded_rectangle((72, 76, 145, 149), radius=18, outline=MINT, width=3)
    draw.text((89, 90), "SB", font=font(28, True), fill=WHITE)
    draw.text((72, 225), "SKILL BRIDGE", font=font(20, True), fill=ORANGE)
    draw.text((72, 268), "CV Khoa → Product Owner match", font=font(48, True), fill=WHITE)
    draw.text((72, 340), "A transparent, human-reviewed hiring demo", font=font(25), fill="#b9d9d6")
    draw.rounded_rectangle((72, 440, 720, 518), radius=16, fill="#0d514d")
    draw.text((101, 462), "No candidate score  •  No automated decision", font=font(22, True), fill=MINT)
    draw.text((72, 635), "Hackathon demo · deterministic local pipeline", font=font(17), fill="#9fc5c1")
    return image


def jd_card() -> Image.Image:
    page = Image.open(ROOT / "tmp/product-owner-jd-render/page-1.png").convert("RGB")
    image = Image.new("RGB", (WIDTH, HEIGHT), "#eef5f3")
    target_h = 620
    target_w = round(page.width * target_h / page.height)
    page = page.resize((target_w, target_h), Image.Resampling.LANCZOS)
    image.paste(page, (WIDTH - target_w - 65, 30))
    draw = ImageDraw.Draw(image)
    draw.text((65, 110), "UPLOAD-READY JD", font=font(18, True), fill=ORANGE)
    draw.text((65, 153), "Product Owner", font=font(43, True), fill=INK)
    lines = ["Backlog management", "Product discovery", "Stakeholder management", "Agile delivery", "SQL & analytics preferred"]
    y = 238
    for line in lines:
        draw.ellipse((68, y + 8, 78, y + 18), fill="#0b8a66")
        draw.text((94, y), line, font=font(21), fill="#365554")
        y += 48
    draw.rounded_rectangle((65, 525, 555, 598), radius=14, fill="#dff2ee")
    draw.text((88, 546), "Synthetic vacancy · safe for demo", font=font(19, True), fill="#096f69")
    return image


def outro_card() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f2f7f5")
    draw = ImageDraw.Draw(image)
    draw.text((78, 130), "SKILL BRIDGE", font=font(20, True), fill=ORANGE)
    draw.text((78, 180), "Skills are ranked.", font=font(52, True), fill=INK)
    draw.text((78, 244), "People are not.", font=font(52, True), fill="#08776e")
    items = ["Evidence-backed CV translation", "Transparent JD skill priorities", "Per-skill match explanations", "Recruiter-initiated decisions only"]
    y = 365
    for item in items:
        draw.rounded_rectangle((78, y, 112, y + 34), radius=9, fill="#dff2ee")
        draw.text((87, y + 3), "✓", font=font(20, True), fill="#08776e")
        draw.text((132, y + 3), item, font=font(22), fill="#365554")
        y += 54
    draw.text((78, 650), "Candidate: Phung Dang Khoa  •  Role: Product Owner", font=font(18, True), fill="#637775")
    return image


def screenshot_scene(name: str, eyebrow: str, title: str, detail: str) -> Image.Image:
    source = cover(Image.open(FRAMES / name))
    source = ImageEnhance.Contrast(source).enhance(1.02)
    return caption(source, eyebrow, title, detail)


SCENES = [
    (title_card(), 3.2),
    (screenshot_scene("02-khoa-profile.png", "1 · Candidate", "Khoa's CV becomes a reviewable profile", "Three roles are structured with source evidence; contact details stay out of the demo fixture."), 4.2),
    (screenshot_scene("03-translated-skills.png", "2 · Transferable skills", "Experience translates into Product Owner capability", "Backlog management, product discovery and stakeholder management remain linked to Khoa's evidence."), 4.2),
    (jd_card(), 3.8),
    (screenshot_scene("04-hr-jd-upload.png", "3 · HR workspace", "HR uploads the Product Owner JD", "Candidate and recruiter inputs stay separate; the confirmed candidate profile is reused, never re-parsed."), 3.5),
    (screenshot_scene("05-product-owner-weights.png", "4 · JD analysis", "Required skills receive transparent weights", "Eight Product Owner skills are normalised to 100% role priority - never a candidate score."), 4.2),
    (screenshot_scene("06-per-skill-match.png", "5 · Evidence match", "Every requirement is assessed skill by skill", "High, medium and low results include JD evidence and candidate rationale."), 4.2),
    (screenshot_scene("07-human-decision.png", "6 · Human in the loop", "The recruiter records the decision", "Skill Bridge explains. A person chooses Shortlist, Needs more info or Not a fit."), 3.5),
    (outro_card(), 3.5),
]


def blend(a: Image.Image, b: Image.Image, amount: float) -> Image.Image:
    return Image.blend(a, b, amount)


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-an",
        "-vcodec", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(OUTPUT),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    transition_frames = round(0.35 * FPS)
    for index, (scene, duration) in enumerate(SCENES):
        frame_count = round(duration * FPS)
        next_scene = SCENES[index + 1][0] if index + 1 < len(SCENES) else None
        for frame_index in range(frame_count):
            current = scene
            if next_scene is not None and frame_index >= frame_count - transition_frames:
                amount = (frame_index - (frame_count - transition_frames) + 1) / transition_frames
                current = blend(scene, next_scene, amount)
            process.stdin.write(current.tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(OUTPUT)


if __name__ == "__main__":
    main()
