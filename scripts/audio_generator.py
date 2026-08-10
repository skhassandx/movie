"""
audio_generator.py
-------------------
Turns each scene's Bengali narration text into an MP3 using edge-tts
(free, no API key needed). Uses a male narrator voice with a slightly
slower rate, which suits suspense/mystery storytelling.
"""

import os
import json
import asyncio
import edge_tts

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")

# bn-BD-PradeepNeural = male Bangladeshi voice, good for a dramatic narrator.
# Swap to "bn-BD-NabanitaNeural" for a female narrator voice if preferred.
VOICE = "bn-BD-PradeepNeural"
RATE = "-8%"  # slightly slower for dramatic/suspense pacing


async def synthesize(text, out_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(out_path)


def generate_all():
    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(AUDIO_DIR, exist_ok=True)
    scenes = data["scenes"]
    total = len(scenes)

    async def run_all():
        for i, scene in enumerate(scenes, start=1):
            out_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.mp3")
            if os.path.exists(out_path):
                continue  # allows resuming a partially completed run

            print(f"[audio_generator] ভয়েসওভার তৈরি হচ্ছে {i}/{total}...")
            await synthesize(scene["narration"], out_path)

    asyncio.run(run_all())
    print(f"[audio_generator] সম্পন্ন - {total}টা অডিও ফাইল তৈরি হয়েছে।")


if __name__ == "__main__":
    generate_all()
