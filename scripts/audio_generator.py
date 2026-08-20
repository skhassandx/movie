"""
audio_generator.py
-------------------
Turns each scene's Bengali narration text into an MP3 using edge-tts
(free, no API key needed). Uses a young female narrator voice tuned for a
more natural, energetic delivery.

Honest note on realism: edge-tts is a solid free neural TTS, but it is not
indistinguishable from a real human voice - that level of realism (e.g.
ElevenLabs-style cloning) isn't available for free at this scale. This is
the practical ceiling for a $0 pipeline; rate/pitch below are tuned to get
as close to natural/youthful as edge-tts allows.
"""

import os
import json
import asyncio
import edge_tts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")

# bn-BD-NabanitaNeural = female Bangladeshi voice. Sounds younger/brighter
# with a small pitch lift; rate kept close to natural (not slowed down a
# lot) so it doesn't sound robotic/over-dramatic.
VOICE = "bn-BD-NabanitaNeural"
RATE = "+2%"
PITCH = "+4Hz"


async def synthesize(text, out_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
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
