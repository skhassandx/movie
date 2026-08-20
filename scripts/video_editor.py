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
import random
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


def ken_burns(clip, mode):
    """
    Varied zoom (no true character animation - see chat for why that isn't
    realistically free/automatable). Randomly picking zoom-in vs zoom-out
    and slightly different speeds per scene at least avoids every single
    scene feeling like the exact same motion.
    """
    duration = max(clip.duration, 0.01)

    if mode == "zoom_in_slow":
        return clip.resize(lambda t: 1.0 + 0.05 * (t / duration))
    elif mode == "zoom_in_fast":
        return clip.resize(lambda t: 1.0 + 0.09 * (t / duration))
    elif mode == "zoom_out":
        return clip.resize(lambda t: 1.09 - 0.07 * (t / duration))
    else:  # "zoom_in_slow" fallback
        return clip.resize(lambda t: 1.0 + 0.06 * (t / duration))


MOTION_MODES = ["zoom_in_slow", "zoom_in_fast", "zoom_out"]


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
        base = base.resize(height=FRAME_SIZE[1] + 60)  # overscan for zoom room
        base = ken_burns(base, random.choice(MOTION_MODES))
        base = base.set_position(("center", "center"))

        # 🌟 সাবটাইটেল ছাড়া শুধুমাত্র ছবি এবং অডিও কম্পোজ করা হচ্ছে
        scene_clip = CompositeVideoClip([base], size=FRAME_SIZE)
        scene_clip = scene_clip.set_audio(audio_clip)
        clips.append(scene_clip)

    if not clips:
        raise RuntimeError("কোনো scene clip তৈরি হয়নি - image/audio জেনারেশন ধাপ চেক করো।")

    print("[video_editor] সব scene জোড়া দিয়ে ফাইনাল ভিডিও রেন্ডার হচ্ছে (সাবটাইটেল ছাড়া দ্রুত রেন্ডার হবে)...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        FINAL_VIDEO_PATH,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="faster",
        bitrate="3000k",  # ফিক্স: আগে বিটরেট বলা ছিল না, ffmpeg ডিফল্টে অনেক কম
                           # (~৬০kbps) বেছে নিচ্ছিল - এটাই ঝাপসা/ব্লকি ভিডিওর কারণ ছিল।
    )
    print(f"[video_editor] সম্পন্ন - {FINAL_VIDEO_PATH}")
    return FINAL_VIDEO_PATH


if __name__ == "__main__":
    build_video()
