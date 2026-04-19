#!/usr/bin/env python3
"""Volvo 99th Anniversary v5 - custom crop positions for each image."""

from moviepy import VideoClip, ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np, os, subprocess

W, H = 1080, 1920

# Crop positions: {name: (horizontal_ratio, vertical_ratio)}
# horizontal: 0=far-left, 1=far-right
# vertical: 0=top, 1=bottom
CROPS = {
    "ov4_1927":   (0.35, 0.5),   # center-L
    "pv444_1944": (0.35, 0.5),   # center
    "duett_1953": (0.75, 0.5),   # far-R
    "240_1974":   (0.55, 0.5),   # center-R
    "ex90_2024":  (0.35, 0.5),   # center-L
}

scenes = [
    {"key": "ov4_1927",   "img": "images/ov4_1927.jpeg",  "year": "1927", "text": "第一辆 Volvo ÖV4",       "dur": 3.5, "effect": "zoom_in"},
    {"key": "pv444_1944", "img": "images/pv444_1944.jpg",  "year": "1944", "text": "PV444 · 两周2300台订单",   "dur": 3.5, "effect": "slide_right"},
    {"key": "duett_1953", "img": "images/duett_1953.jpg",  "year": "1959", "text": "三点式安全带 挽救超100万生命", "dur": 3.5, "effect": "zoom_out"},
    {"key": "240_1974",   "img": "images/240_1974.jpg",   "year": "1974", "text": "240系列 · 全球安全标杆",   "dur": 3.5, "effect": "slide_left"},
    {"key": "ex90_2024",  "img": "images/ex90_zhihu.jpg",   "year": "2024", "text": "EX90 · 电动化旗舰",       "dur": 3.5, "effect": "zoom_in"},
]

TRANSITION = 0.5
CLOSING_DUR = 5.0  # 5*3.5 + 5 - 5*0.5 = 20


def fit_image(img_path, hx, hy):
    """Cover-fill to WxH with custom crop anchor."""
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
    nw, nh = img.size
    max_x = max(0, nw - W)
    max_y = max(0, nh - H)
    left = int(hx * max_x)
    top = int(hy * max_y)
    return img.crop((left, top, left + W, top + H))


def render_text(text, fontsize, y, alpha=255):
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", fontsize)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    a = max(0, min(255, alpha))
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0, a), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, a), font=font)
    return frame


def make_scene_clip(scene):
    hx, hy = CROPS[scene["key"]]
    base_img = fit_image(scene["img"], hx, hy)
    dur = scene["dur"]
    effect = scene["effect"]

    def make_frame(t):
        p = t / dur

        if effect == "zoom_in":
            zoom = 1.0 + 0.12 * p
            zw, zh = int(W * zoom), int(H * zoom)
            big = base_img.resize((zw, zh), Image.LANCZOS)
            cropped = big.crop((zw // 2 - W // 2, zh // 2 - H // 2, zw // 2 + W // 2, zh // 2 + H // 2))

        elif effect == "zoom_out":
            zoom = 1.12 - 0.12 * p
            zw, zh = int(W * zoom), int(H * zoom)
            big = base_img.resize((zw, zh), Image.LANCZOS)
            frame = Image.new("RGB", (W, H), (0, 0, 0))
            frame.paste(big, ((W - zw) // 2, (H - zh) // 2))
            cropped = frame

        elif effect == "slide_right":
            big_w = int(W * 1.15)
            big = base_img.resize((big_w, H), Image.LANCZOS)
            max_off = big_w - W
            off = int(max_off * (1 - p))
            cropped = big.crop((off, 0, off + W, H))

        elif effect == "slide_left":
            big_w = int(W * 1.15)
            big = base_img.resize((big_w, H), Image.LANCZOS)
            max_off = big_w - W
            off = int(max_off * p)
            cropped = big.crop((off, 0, off + W, H))

        else:
            cropped = base_img

        # Text with fade
        if t < 0.3:
            alpha = int(255 * t / 0.3)
        elif t > dur - 0.3:
            alpha = int(255 * (dur - t) / 0.3)
        else:
            alpha = 255

        txt_year = render_text(scene["year"], 72, 80, alpha)
        txt_sub = render_text(scene["text"], 28, H - 100, alpha)

        frame = Image.fromarray(np.array(cropped)).convert("RGBA")
        frame = Image.alpha_composite(frame, txt_year)
        frame = Image.alpha_composite(frame, txt_sub)
        return np.array(frame.convert("RGB"))

    return VideoClip(make_frame, duration=dur)


if __name__ == "__main__":
    os.chdir("/tmp/volvo99")

    clips = []
    for i, s in enumerate(scenes):
        print(f"Scene {i + 1}: {s['year']} ({s['key']} crop={CROPS[s['key']]})")
        clips.append(make_scene_clip(s))

    print("Closing...")
    closing_img = fit_image("images/closing.jpg", 0.5, 0.5)
    closing = ImageClip(np.array(closing_img), duration=CLOSING_DUR)
    clips.append(closing)

    print("Concatenating...")
    final = concatenate_videoclips(clips, method="compose", padding=-TRANSITION)
    final = final.with_duration(20.0)

    print("BGM...")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=220:duration=20",
                    "-f", "lavfi", "-i", "sine=frequency=330:duration=20",
                    "-f", "lavfi", "-i", "sine=frequency=262:duration=20",
                    "-filter_complex",
                    "[0]volume=0.04[a];[1]volume=0.03[b];[2]volume=0.02[c];"
                    "[a][b][c]amix=inputs=3:duration=longest,"
                    "afade=t=in:d=2,afade=t=out:st=17:d=3",
                    "-c:a", "aac", "-b:a", "128k", "video/bgm.m4a"],
                   capture_output=True)

    audio = AudioFileClip("video/bgm.m4a").subclipped(0, 20.0)
    final = final.with_audio(audio)

    print("Exporting...")
    final.write_videofile("output/volvo99_v5.mp4", fps=30, codec="libx264",
                          audio_codec="aac", preset="medium", logger="bar")
    print("Done!")
