"""
video_editor.py
----------------
Combines per-scene images + per-scene audio into the final 1280x720 mp4:
- each image is shown for exactly its scene's audio duration
- a slow "Ken Burns" zoom is applied for a less static feel
- the narration text is burned in as a caption near the bottom (drawn with
  PIL/Bengali font instead of MoviePy's TextClip, to avoid needing
  ImageMagick in the CI environment)
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
FINAL_VIDEO_PATH = os.path.join(OUTPUT_DIR, "final_video.mp4")

FRAME_SIZE = (1280, 720)
FPS = 24

# Common locations for a Bengali-capable font on an Ubuntu GitHub Actions
# runner after `apt-get install -y fonts-beng fonts-noto-core`.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf",
    "/usr/share/fonts/truetype/fonts-bengali/Lohit-Bengali.ttf",
    "fonts/NotoSansBengali-Regular.ttf",  # fallback: bundle a font in the repo yourself
]


def find_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError(
        "কোনো বাংলা ফন্ট পাওয়া যায়নি। GitHub Actions workflow-এ "
        "`sudo apt-get install -y fonts-beng fonts-noto-core` যোগ আছে কিনা চেক করো, "
        "অথবা fonts/ ফোল্ডারে NotoSansBengali-Regular.ttf রাখো।"
    )


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_caption_image(text, size=FRAME_SIZE):
    W, H = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = find_font(38)

    lines = wrap_text(text, font, W - 120, draw)
    line_height = 48
    box_height = line_height * len(lines) + 40
    box_top = H - box_height - 40

    # semi-transparent background box for readability
    draw.rectangle([(0, box_top), (W, H - 20)], fill=(0, 0, 0, 140))

    y = box_top + 20
    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (W - text_width) / 2
        # simple outline for extra contrast against any background
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    return np.array(layer)


def ken_burns(clip, zoom_ratio=0.06):
    """Slow, subtle zoom-in over the clip's duration."""
    def resize_fn(t):
        return 1 + zoom_ratio * (t / max(clip.duration, 0.01))

    return clip.resize(resize_fn).set_position(("center", "center"))


def build_video():
    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data["scenes"]
    total = len(scenes)
    clips = []

    for i, scene in enumerate(scenes, start=1):
        img_path = os.path.join(IMAGES_DIR, f"scene_{i:03d}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.mp3")

        if not os.path.exists(img_path) or not os.path.exists(audio_path):
            print(f"[video_editor] scene {i} এর ফাইল অনুপস্থিত, স্কিপ করা হচ্ছে।")
            continue

        print(f"[video_editor] scene {i}/{total} জোড়া হচ্ছে...")
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration + 0.3  # tiny buffer so audio never gets cut

        base = ImageClip(img_path).set_duration(duration)
        base = ken_burns(base).resize(height=FRAME_SIZE[1] + 40)  # slight overscan for zoom room
        base = base.set_position(("center", "center"))

        caption_img = make_caption_image(scene["narration"])
        caption_clip = (
            ImageClip(caption_img)
            .set_duration(duration)
            .set_position(("center", "center"))
        )

        scene_clip = CompositeVideoClip([base, caption_clip], size=FRAME_SIZE)
        scene_clip = scene_clip.set_audio(audio_clip)
        clips.append(scene_clip)

    if not clips:
        raise RuntimeError("কোনো scene clip তৈরি হয়নি - image/audio জেনারেশন ধাপ চেক করো।")

    print("[video_editor] সব scene জোড়া দিয়ে ফাইনাল ভিডিও রেন্ডার হচ্ছে (কিছুটা সময় লাগবে)...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        FINAL_VIDEO_PATH,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )
    print(f"[video_editor] সম্পন্ন - {FINAL_VIDEO_PATH}")
    return FINAL_VIDEO_PATH


if __name__ == "__main__":
    build_video()
