#!/usr/bin/env python3
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FFMPEG_BIN = "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
font_path_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
font_path_reg = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_badge = ImageFont.truetype(font_path_bold, 16)
font_title = ImageFont.truetype(font_path_bold, 44)
font_sub = ImageFont.truetype(font_path_reg, 24)
font_caption = ImageFont.truetype(font_path_bold, 21)

scenes = [
    {
        "index": 0,
        "step": "STEP 01 OF 09 • TALENT ONBOARDING",
        "title": "Account Creation & Role Selection",
        "sub": "Role Picker • Anonymous Wildlife Persona • National Standards",
        "img": "Presentation/audio/yt_00_signup.png",
        "audio": "Presentation/audio/yt_audio_0.mp3",
        "subtitle": "To get started with Jinder, talents and employers can create an account in seconds. Candidates select their role, choose an anonymous Australian wildlife persona like Teal Heron to protect privacy and eliminate bias, and enter their details under strict national standards."
    },
    {
        "index": 1,
        "step": "STEP 02 OF 09 • PLATFORM ACCESS",
        "title": "Dual-Role Authentication",
        "sub": "Instant 1-Click Platform Access for Talents & Hiring Teams",
        "img": "Presentation/audio/yt_01_login.png",
        "audio": "Presentation/audio/yt_audio_1.mp3",
        "subtitle": "Welcome to Jinder, the autonomous capability alignment platform for Australia. Let's sign into the live application as candidate Linh Nguyen."
    },
    {
        "index": 2,
        "step": "STEP 03 OF 09 • TALENT WORKSPACE",
        "title": "Overseas Qualification Harmonisation",
        "sub": "ANZSCO 224114 Data Analyst • AQF Level 7 Benchmarking",
        "img": "Presentation/audio/yt_02_talent_home.png",
        "audio": "Presentation/audio/yt_audio_2.mp3",
        "subtitle": "Linh's overseas BI Specialist title is harmonised to ANZSCO 224114 Data Analyst (AQF Level 7), masked under anonymous persona Teal Heron."
    },
    {
        "index": 3,
        "step": "STEP 04 OF 09 • OPPORTUNITY DISCOVERY",
        "title": "Continuous Feed Ranking (Formula F-05)",
        "sub": "Continuous Match Engine Across Melbourne, Sydney & Canberra",
        "img": "Presentation/audio/yt_03_jobs_feed.png",
        "audio": "Presentation/audio/yt_audio_3.mp3",
        "subtitle": "Jinder executes Formula F-05 to rank open roles across Melbourne, Sydney, and Canberra by skill coverage, fit score, and salary upside."
    },
    {
        "index": 4,
        "step": "STEP 05 OF 09 • EXPLAINABLE TELEMETRY",
        "title": "Skill Overlap & Gap Analysis",
        "sub": "Transparent Mathematical Breakdown • Targeted Course Actions",
        "img": "Presentation/audio/yt_04_job_detail.png",
        "audio": "Presentation/audio/yt_audio_4.mp3",
        "subtitle": "Reviewing the Data Analyst role at Stringybark Data: 76% skill coverage, verified SQL & Python competencies, and transparent gap flagging."
    },
    {
        "index": 5,
        "step": "STEP 06 OF 09 • VACANCY BENCHMARKING",
        "title": "Multi-Role Comparison Tray",
        "sub": "Benchmarking Opportunities Across Remuneration & Flexibility",
        "img": "Presentation/audio/yt_05_job_compare.png",
        "audio": "Presentation/audio/yt_audio_5.mp3",
        "subtitle": "Candidates benchmark multiple job opportunities side-by-side across salary, hybrid work flexibility, and long-term capability growth."
    },
    {
        "index": 6,
        "step": "STEP 07 OF 09 • EMPLOYER PORTAL",
        "title": "Zero-PII Wildlife Candidate Feed",
        "sub": "Eliminating Demographic Hiring Bias With Masked Personas",
        "img": "Presentation/audio/yt_06_wildlife_candidates.png",
        "audio": "Presentation/audio/yt_audio_6.mp3",
        "subtitle": "Switching to Employer portal: Hiring managers discover talent masked under wildlife personas like Violet Koala to eliminate demographic bias."
    },
    {
        "index": 7,
        "step": "STEP 08 OF 09 • CAPABILITY PROVENANCE",
        "title": "Verified Evidence & CV Citations",
        "sub": "Concrete CV Tracing • Statutory Blocker Audit Trail",
        "img": "Presentation/audio/yt_07_candidate_detail.png",
        "audio": "Presentation/audio/yt_audio_7.mp3",
        "subtitle": "In-depth candidate profile: Every claimed competency is anchored to concrete CV citations, certifications, and Australian benchmarks."
    },
    {
        "index": 8,
        "step": "STEP 09 OF 09 • RADAR BENCHMARKING",
        "title": "Multi-Candidate Radar Comparison",
        "sub": "Identical Radar Axes • Skill Fit, Seniority & Certifications",
        "img": "Presentation/audio/yt_08_recruiter_compare.png",
        "audio": "Presentation/audio/yt_audio_8.mp3",
        "subtitle": "Multi-candidate compare tray: Contrasting candidate profiles on identical radar axes across skill fit, seniority, and certification readiness."
    }
]

w, h = 1920, 1080

def create_transition_frame(step_text, title_text, sub_text, out_path, step_num):
    y, x = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    r_norm = np.clip(dist / 950.0, 0, 1)

    r_ch = (15 + (1 - r_norm) * 26).astype(np.uint8)
    g_ch = (17 + (1 - r_norm) * 22).astype(np.uint8)
    b_ch = (36 + (1 - r_norm) * 48).astype(np.uint8)

    img_arr = np.dstack([r_ch, g_ch, b_ch])
    img = Image.fromarray(img_arr, mode="RGB").convert("RGBA")

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Ambient glowing orbs
    draw.ellipse([cx - 450, cy - 350, cx + 450, cy + 450], fill=(104, 104, 247, 32))
    draw.ellipse([cx - 220, cy - 220, cx + 220, cy + 220], fill=(255, 163, 64, 28))

    # Center Glass Card
    card_w, card_h = 1040, 360
    x0 = (w - card_w) // 2
    y0 = (h - card_h) // 2
    x1, y1 = x0 + card_w, y0 + card_h

    draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(18, 21, 46, 238), outline=(104, 104, 247, 180), width=2)

    # Step Badge
    draw.rounded_rectangle([x0 + 44, y0 + 44, x0 + 420, y0 + 86], radius=20, fill=(104, 104, 247, 65), outline=(104, 104, 247, 210), width=1)
    draw.text((x0 + 64, y0 + 54), step_text, fill=(165, 180, 252, 255), font=font_badge)

    # Main Title
    draw.text((x0 + 44, y0 + 115), title_text, fill=(255, 255, 255, 255), font=font_title)

    # Subtitle
    draw.text((x0 + 44, y0 + 195), sub_text, fill=(148, 163, 184, 255), font=font_sub)

    # Progress bar indicator
    total_bar_w = card_w - 88
    active_bar_w = int(total_bar_w * ((step_num + 1) / 9.0))
    draw.rounded_rectangle([x0 + 44, y1 - 44, x0 + 44 + active_bar_w, y1 - 38], radius=3, fill=(255, 163, 64, 255))
    draw.rounded_rectangle([x0 + 44 + active_bar_w, y1 - 44, x1 - 44, y1 - 38], radius=3, fill=(255, 255, 255, 35))

    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(out_path)


def create_app_frame(img_path, subtitle_text, out_path):
    base = Image.open(img_path).convert("RGBA")
    if base.size != (1920, 1080):
        base = base.resize((1920, 1080), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # NOTICE: NO TOP CHAPTER BAR! KEEP THE APP SCREEN 100% CLEAN!
    # Bottom Subtitle Box only:
    sub_x0, sub_y0, sub_x1, sub_y1 = 80, 960, 1840, 1050
    draw.rounded_rectangle([sub_x0, sub_y0, sub_x1, sub_y1], radius=16, fill=(10, 12, 28, 238), outline=(255, 255, 255, 60), width=1)

    lines = textwrap.wrap(subtitle_text, width=130)
    line_y = sub_y0 + (45 - (len(lines) * 14))
    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font_caption)
        text_w = bbox[2] - bbox[0]
        text_x = 960 - (text_w // 2)
        draw.text((text_x, line_y), l, fill=(255, 255, 255, 255), font=font_caption)
        line_y += 28

    final_img = Image.alpha_composite(base, overlay).convert("RGB")
    final_img.save(out_path)


print("=== 1. Generating Frames for 9 Scenes ===")
trans_files = []
app_files = []

for sc in scenes:
    i = sc["index"]
    t_out = f"Presentation/audio/v2_trans_{i}.png"
    create_transition_frame(sc["step"], sc["title"], sc["sub"], t_out, i)
    trans_files.append(t_out)
    print(f"Created transition frame: {t_out}")

    a_out = f"Presentation/audio/v2_app_{i}.png"
    create_app_frame(sc["img"], sc["subtitle"], a_out)
    app_files.append(a_out)
    print(f"Created app frame: {a_out}")

print("\n=== 2. Encoding Video Clips with Synchronized Audio Settings (44.1kHz Stereo) ===")
clip_list = []

for sc in scenes:
    i = sc["index"]
    t_frame = trans_files[i]
    a_frame = app_files[i]
    audio_file = sc["audio"]

    t_clip = f"Presentation/audio/v2_tclip_{i}.mp4"
    a_clip = f"Presentation/audio/v2_aclip_{i}.mp4"

    # 1. Transition clip: 1.2s duration, silent audio at 44.1kHz stereo
    cmd_trans = [
        FFMPEG_BIN, "-y",
        "-loop", "1", "-t", "1.2",
        "-i", t_frame,
        "-f", "lavfi", "-t", "1.2", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p",
        "-shortest",
        t_clip
    ]
    subprocess.run(cmd_trans, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    clip_list.append(t_clip)
    print(f"Rendered transition clip {i} -> {t_clip}")

    # 2. App clip: looped image with matching voiceover audio resampled to 44.1kHz stereo
    cmd_app = [
        FFMPEG_BIN, "-y",
        "-loop", "1",
        "-i", a_frame,
        "-i", audio_file,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p",
        "-shortest",
        a_clip
    ]
    subprocess.run(cmd_app, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    clip_list.append(a_clip)
    print(f"Rendered app clip {i} -> {a_clip}")

print("\n=== 3. Concatenating all 18 clips into intermediate video ===")
concat_txt = "Presentation/audio/v2_concat.txt"
with open(concat_txt, "w") as f:
    for c in clip_list:
        f.write(f"file '{os.path.abspath(c)}'\n")

intermediate_mp4 = "Presentation/audio/v2_intermediate.mp4"
subprocess.run([
    FFMPEG_BIN, "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_txt,
    "-c", "copy",
    intermediate_mp4
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"Intermediate concatenated video: {intermediate_mp4}")

print("\n=== 4. Mixing Continuous Ambient Background Music ===")
master_mp4 = "Presentation/jinder_demo_video.mp4"
bg_music = "Presentation/audio/ambient_bg_music.wav"

cmd_mix = [
    FFMPEG_BIN, "-y",
    "-i", intermediate_mp4,
    "-i", bg_music,
    "-filter_complex",
    "[1:a]volume=0.12[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-ar", "44100",
    "-map", "0:v",
    "-map", "[aout]",
    master_mp4
]
subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

size_mb = os.path.getsize(master_mp4) / (1024 * 1024)
print(f"\n==========================================")
print(f"SUCCESS! Master Video: {master_mp4} ({size_mb:.2f} MB)")
print(f"==========================================")
