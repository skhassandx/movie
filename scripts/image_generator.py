"""
image_generator.py
-------------------
Calls Pollinations.ai (https://gen.pollinations.ai) to turn each scene's
image_prompt into a picture, then crops/resizes it to a 1280x720 landscape
frame for the video.
"""

import os
import io
import time
import requests
import json
from urllib.parse import quote
from PIL import Image

# 🌟 ডাইনামিক পাথ (নতুন প্রজেক্ট স্ট্রাকচার অনুযায়ী)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

# 🌟 ভিডিওর রেজোলিউশন (লং ভিডিওর জন্য 1280x720, শর্টসের জন্য 720x1280 করে নেবেন)
TARGET_SIZE = (1280, 720) 

STYLE_SUFFIX = (
    ", cinematic lighting, moody atmosphere, highly detailed digital painting, "
    "dramatic composition, dark suspense mystery tone, no text, no watermark"
)

BASE_URL = "https://image.pollinations.ai/prompt/"
MODEL = "flux"
MAX_RETRIES = 4

def pollinations_generate_image(prompt):
    encoded_prompt = quote(prompt[:2000])
    url = f"{BASE_URL}{encoded_prompt}"
    params = {
        "model": MODEL,
        "width": TARGET_SIZE[0],
        "height": TARGET_SIZE[1],
        "nologo": "true",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=90)

            if resp.status_code == 429:
                wait = 16 * attempt
                print(
                    f"[image_generator] 429 (anonymous rate limit - বিনামূল্যে key নিলে এটা "
                    f"হবে না) - {wait}s অপেক্ষা করে আবার চেষ্টা ({attempt}/{MAX_RETRIES})..."
                )
                time.sleep(wait)
                continue

            resp.raise_for_status()
            content = resp.content
            if len(content) < 500:
                raise ValueError(f"খুব ছোট রেসপন্স পাওয়া গেছে, ইমেজ মনে হচ্ছে না: {content[:200]}")
            return content
        except requests.exceptions.HTTPError as e:
            print(f"[image_generator] HTTP এরর ডিটেইল: {resp.text[:300]}")
            print(f"[image_generator] চেষ্টা {attempt}/{MAX_RETRIES} ব্যর্থ: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(5 * attempt)
        except Exception as e:
            print(f"[image_generator] চেষ্টা {attempt}/{MAX_RETRIES} ব্যর্থ: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(5 * attempt)

def crop_to_landscape(image_bytes, target_size=TARGET_SIZE):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_ratio = target_size[0] / target_size[1]
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize(target_size, Image.LANCZOS)

def generate_all():
    if not os.path.exists(SCRIPT_DATA_PATH):
        print(f"❌ Error: {SCRIPT_DATA_PATH} পাওয়া যায়নি! আগে script_generator.py রান করুন।")
        return

    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    scenes = data.get("scenes", [])
    total = len(scenes)

    for i, scene in enumerate(scenes, start=1):
        out_path = os.path.join(IMAGES_DIR, f"scene_{i:03d}.jpg")
        if os.path.exists(out_path):
            continue 

        print(f"[image_generator] ছবি তৈরি হচ্ছে {i}/{total}...")
        prompt = scene["image_prompt"] + STYLE_SUFFIX
        img_bytes = pollinations_generate_image(prompt)
        img = crop_to_landscape(img_bytes)
        img.save(out_path, "JPEG", quality=90)

        time.sleep(15) 

    print(f"[image_generator] সম্পন্ন - {total}টা ছবি তৈরি হয়েছে।")

if __name__ == "__main__":
    generate_all()
