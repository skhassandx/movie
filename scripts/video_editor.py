"""
video_editor.py
----------------
Combines per-scene images + per-scene audio into the final 1280x720 mp4:
- each image is shown for exactly its scene's audio duration
- a slow "Ken Burns" zoom is applied for a less static feel
- Subtitles have been REMOVED for faster processing and to rely on YouTube's auto-captions.
"""

import os
import json
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
FINAL_VIDEO_PATH = os.path.join(OUTPUT_DIR, "final_video.mp4")

FRAME_SIZE = (1280, 720)
FPS = 24


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

        # 🌟 সাবটাইটেল ছাড়া শুধুমাত্র ছবি এবং অডিও কম্পোজ করা হচ্ছে
        scene_clip = CompositeVideoClip([base], size=FRAME_SIZE)
        scene_clip = scene_clip.set_audio(audio_clip)
        clips.append(scene_clip)

    if not clips:
        raise RuntimeError("কোনো scene clip তৈরি হয়নি - image/audio জেনারেশন ধাপ চেক করো।")

    print("[video_editor] সব scene জোড়া দিয়ে ফাইনাল ভিডিও রেন্ডার হচ্ছে (সাবটাইটেল ছাড়া দ্রুত রেন্ডার হবে)...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        FINAL_VIDEO_PATH,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="faster",  
    )
    print(f"[video_editor] সম্পন্ন - {FINAL_VIDEO_PATH}")
    return FINAL_VIDEO_PATH


if __name__ == "__main__":
    build_video()
