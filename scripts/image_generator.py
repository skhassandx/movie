"""
image_generator.py
-------------------
Calls Pollinations AI (FLUX model) to generate images.
It is completely free, requires no API keys, and has no strict rate limits!
"""

import os
import json
import time
import urllib.parse
import requests
import io
from PIL import Image

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
TARGET_SIZE = (1280, 720)

# ছবির কোয়ালিটি ও ভৌতিক থিম ঠিক রাখার জন্য স্টাইল
STYLE_SUFFIX = (
    ", cinematic lighting, moody atmosphere, highly detailed digital painting, "
    "dramatic composition, dark suspense mystery tone, no text"
)

SAFE_PROMPT = "A dark mysterious empty cinematic room, shadows, scary suspenseful atmosphere, faint light" + STYLE_SUFFIX

def pollinations_generate_image(prompt):
    # প্রম্পটটি URL-এ বসানোর জন্য এনকোড করা
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Pollinations URL - সরাসরি 1280x720 এবং flux মডেল সেট করা
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&nologo=true"
    
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content  # বাইট হিসেবে ছবি রিটার্ন করবে
        except Exception as e:
            print(f"[image_generator] চেষ্টা {attempt}/3 ব্যর্থ: {e}")
            if attempt == 3:
                raise RuntimeError(f"ছবি তৈরি করা সম্ভব হয়নি: {e}")
            time.sleep(5)

def process_and_save_image(image_bytes, out_path):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # সাইজ নিশ্চিত করা
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(out_path, "JPEG", quality=90)

def generate_all():
    # Cloudflare API Key এর আর কোনো প্রয়োজন নেই!
    
    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    scenes = data["scenes"]
    total = len(scenes)

    for i, scene in enumerate(scenes, start=1):
        out_path = os.path.join(IMAGES_DIR, f"scene_{i:03d}.jpg")
        if os.path.exists(out_path):
            continue  # আগের তৈরি করা ছবি থাকলে স্কিপ করবে

        print(f"[image_generator] ছবি তৈরি হচ্ছে {i}/{total}...")
        prompt = scene["image_prompt"] + STYLE_SUFFIX
        
        try:
            img_bytes = pollinations_generate_image(prompt)
            process_and_save_image(img_bytes, out_path)
        except Exception as e:
            print(f"[image_generator] ⚠️ সমস্যা: {e}")
            print(f"[image_generator] সেফ প্রম্পট দিয়ে আবার চেষ্টা করা হচ্ছে...")
            img_bytes = pollinations_generate_image(SAFE_PROMPT)
            process_and_save_image(img_bytes, out_path)

        # Pollinations-এ লিমিট নেই, তবুও সার্ভার যেন ব্লক না করে তাই ৩ সেকেন্ড গ্যাপ
        time.sleep(3)

    print(f"[image_generator] সম্পন্ন - {total}টা ছবি তৈরি হয়েছে।")

if __name__ == "__main__":
    generate_all()
