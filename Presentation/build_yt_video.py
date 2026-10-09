#!/usr/bin/env python3
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

FFMPEG_BIN = "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"

font_path_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
font_path_reg = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_title = ImageFont.truetype(font_path_bold, 17)
font_badge = ImageFont.truetype(font_path_bold, 13)
font_sub = ImageFont.truetype(font_path_bold, 21)

scenes = [
    (
        "Presentation/audio/yt_01_login.png",
        "CHAPTER 01/08 • PLATFORM ACCESS | 1-CLICK DUAL-ROLE AUTHENTICATION",
        "Welcome to Jinder, the autonomous capability alignment platform for Australia. Let's sign into the live application as candidate Linh Nguyen."
    ),
    (
        "Presentation/audio/yt_02_talent_home.png",
        "CHAPTER 02/08 • TALENT WORKSPACE | ANZSCO 224114 & AQF LEVEL 7 HARMONISATION",
        "Linh's overseas BI Specialist title is harmonised to ANZSCO 224114 Data Analyst (AQF Level 7), masked under anonymous persona Teal Heron."
    ),
    (
        "Presentation/audio/yt_03_jobs_feed.png",
        "CHAPTER 03/08 • CONTINUOUS FEED RANKING | FORMULA F-05 MATCH ENGINE",
        "Jinder executes Formula F-05 to rank open roles across Melbourne, Sydney, and Canberra by skill coverage, fit score, and salary upside."
    ),
    (
        "Presentation/audio/yt_04_job_detail.png",
        "CHAPTER 04/08 • EXPLAINABLE TELEMETRY | SKILL OVERLAP & GAP ANALYSIS",
        "Reviewing the Data Analyst role at Stringybark Data: 76% skill coverage, verified SQL & Python competencies, and transparent gap flagging."
    ),
    (
        "Presentation/audio/yt_05_job_compare.png",
        "CHAPTER 05/08 • VACANCY BENCHMARKING | MULTI-ROLE GROWTH & SALARY COMPARISON",
        "Candidates benchmark multiple job opportunities side-by-side across salary, hybrid work flexibility, and long-term capability growth."
    ),
    (
        "Presentation/audio/yt_06_wildlife_candidates.png",
        "CHAPTER 06/08 • EMPLOYER DISCOVERY | ZERO-PII ANONYMIZED WILDLIFE PERSONAS",
        "Switching to Employer portal: Hiring managers discover talent masked under wildlife personas like Violet Koala to eliminate demographic bias."
    ),
    (
        "Presentation/audio/yt_07_candidate_detail.png",
        "CHAPTER 07/08 • CAPABILITY PROVENANCE | VERIFIED EVIDENCE CITATIONS",
        "In-depth candidate profile: Every claimed competency is anchored to concrete CV citations, certifications, and Australian benchmarks."
    ),
    (
        "Presentation/audio/yt_08_recruiter_compare.png",
        "CHAPTER 08/08 • RADAR BENCHMARKING | MULTI-PROFILE RADAR COMPARE TRAY",
        "Multi-candidate compare tray: Contrasting candidate profiles on identical radar axes across skill fit, seniority, and certification readiness."
    )
]

print("=== 1. Composing 8 YouTube Demo Frames ===")
for idx, (img_in, chapter, subtitle) in enumerate(scenes, 1):
    base = Image.open(img_in).convert("RGBA")
    if base.size != (1920, 1080):
        base = base.resize((1920, 1080), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top YouTube Chapter Header Bar
    top_x0, top_y0, top_x1, top_y1 = 36, 20, 1884, 70
    draw.rounded_rectangle([top_x0, top_y0, top_x1, top_y1], radius=12, fill=(15, 17, 36, 235), outline=(104, 104, 247, 160), width=2)
    # Brand tag
    draw.rounded_rectangle([top_x0 + 12, top_y0 + 9, top_x0 + 104, top_y1 - 9], radius=6, fill=(104, 104, 247, 240))
    draw.text((top_x0 + 20, top_y0 + 15), "JINDER.", fill=(255, 255, 255, 255), font=font_title)
    # Chapter title
    draw.text((top_x0 + 122, top_y0 + 15), chapter, fill=(255, 255, 255, 255), font=font_title)
    # Right badge
    badge_text = "🔴 LIVE PRODUCT WALKTHROUGH • AUSTRALIA"
    draw.rounded_rectangle([top_x1 - 340, top_y0 + 9, top_x1 - 12, top_y1 - 9], radius=6, fill=(255, 255, 255, 25), outline=(255, 163, 64, 180), width=1)
    draw.text((top_x1 - 325, top_y0 + 17), badge_text, fill=(255, 163, 64, 255), font=font_badge)

    # Bottom Subtitle Box
    sub_x0, sub_y0, sub_x1, sub_y1 = 80, 960, 1840, 1050
    draw.rounded_rectangle([sub_x0, sub_y0, sub_x1, sub_y1], radius=16, fill=(10, 12, 28, 242), outline=(255, 255, 255, 60), width=1)

    # Subtitle Text (wrapped)
    lines = textwrap.wrap(subtitle, width=130)
    line_y = sub_y0 + (45 - (len(lines) * 14))
    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font_sub)
        text_w = bbox[2] - bbox[0]
        text_x = 960 - (text_w // 2)
        draw.text((text_x, line_y), l, fill=(255, 255, 255, 255), font=font_sub)
        line_y += 28

    final_img = Image.alpha_composite(base, overlay).convert("RGB")
    out_file = f"Presentation/audio/yt_prod_frame_{idx}.png"
    final_img.save(out_file)
    print(f"Rendered frame {idx}: {out_file}")

print("\n=== 2. Encoding Video Parts with FFmpeg ===")
part_files = []
for idx in range(1, 9):
    frame = f"Presentation/audio/yt_prod_frame_{idx}.png"
    audio = f"Presentation/audio/yt_audio_{idx}.mp3"
    part_out = f"Presentation/audio/yt_part_{idx}.mp4"
    part_files.append(part_out)

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-loop", "1",
        "-i", frame,
        "-i", audio,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        part_out
    ]
    print(f"Encoding part {idx}...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Part {idx} done -> {part_out}")

print("\n=== 3. Concatenating into Master MP4 ===")
concat_list = "Presentation/audio/yt_concat_list.txt"
with open(concat_list, "w") as f:
    for p in part_files:
        f.write(f"file '{os.path.abspath(p)}'\n")

master_mp4 = "Presentation/jinder_demo_video.mp4"
concat_cmd = [
    FFMPEG_BIN,
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list,
    "-c", "copy",
    master_mp4
]
print(f"Generating master video: {master_mp4}...")
subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

size_mb = os.path.getsize(master_mp4) / (1024 * 1024)
print(f"Master demo video generated successfully: {master_mp4} ({size_mb:.2f} MB)")
