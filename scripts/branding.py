"""
branding.py
-----------
Generates a simple, automated intro/outro card for every video - no manual
editing, no external logo/asset files. Uses PIL to draw text on a plain
background, then video_editor.py prepends/appends these as clips.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip

FRAME_SIZE = (1280, 720)

# 🌟 এখানে তোমার আসল চ্যানেলের নাম/ট্যাগলাইন/আউট্রো টেক্সট বসাও - শুধু এই ৩ লাইন বদলালেই
# প্রতিটা ভবিষ্যৎ ভিডিওতে অটোমেটিক নতুন ব্র্যান্ডিং প্রযোজ্য হবে।
CHANNEL_NAME = "MysteryTales Bangla"
TAGLINE = "রহস্য আর সাসপেন্সের জগতে স্বাগতম"
OUTRO_TEXT = "ভালো লাগলে সাবস্ক্রাইব করুন"

INTRO_DURATION = 3
OUTRO_DURATION = 5

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def find_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()  # শেষ ভরসা, যাতে ফন্ট না পেলেও ক্র্যাশ না করে


def _text_card(lines, bg_color=(10, 10, 15)):
    W, H = FRAME_SIZE
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    total_h = sum(size + 20 for _, size, _ in lines)
    y = (H - total_h) // 2
    for text, size, color in lines:
        font = find_font(size)
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y), text, font=font, fill=color)
        y += size + 20

    return np.array(img)


def make_intro_clip():
    frame = _text_card([
        (CHANNEL_NAME, 64, (255, 255, 255)),
        (TAGLINE, 32, (200, 60, 60)),
    ])
    return ImageClip(frame).set_duration(INTRO_DURATION).fadein(0.5).fadeout(0.3)


def make_outro_clip():
    frame = _text_card([
        (OUTRO_TEXT, 48, (255, 255, 255)),
        (CHANNEL_NAME, 32, (200, 60, 60)),
    ])
    return ImageClip(frame).set_duration(OUTRO_DURATION).fadein(0.3)
