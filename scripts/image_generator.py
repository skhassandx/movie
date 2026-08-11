"""
image_generator.py
-------------------
Calls Cloudflare Workers AI to turn each scene's image_prompt into a picture.
Includes a Safe Prompt fallback if the original prompt triggers a Content Filter (400 Bad Request).
"""

import os
import io
import json
import time
import base64
import requests
from PIL import Image

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
TARGET_SIZE = (1280, 720)

# Appended to every prompt to keep a consistent visual style across scenes.
STYLE_SUFFIX = (
    ", cinematic lighting, moody atmosphere, highly detailed digital painting, "
    "dramatic composition, dark suspense mystery tone, no text, no watermark"
)

# যদি মূল প্রম্পট ব্লক হয়, তখন এই নিরাপদ (Safe) প্রম্পটটি দিয়ে ছবি বানানো হবে
SAFE_PROMPT = "A dark mysterious empty cinematic room, shadows, scary suspenseful atmosphere, faint light" + STYLE_SUFFIX

# একাধিক মডেলের তালিকা (প্রথমটি ব্যর্থ হলে পরেরগুলোতে চেষ্টা করবে)
MODELS = [
    "@cf/black-forest-labs/flux-1-schnell",
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/runwayml/stable-diffusion-v1-5"
]
MAX_RETRIES = 5

def cloudflare_generate_image(prompt, account_id, api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"prompt": prompt[:2000]}

    for model in MODELS:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)

                # 429 (GPU ব্যস্ত) - সাময়িক সার্ভার লোড
                if resp.status_code == 429:
                    wait = 20 * attempt
                    print(f"[image_generator] 429 (GPU ব্যস্ত) - '{model}' এর জন্য {wait} সেকেন্ড অপেক্ষা করা হচ্ছে ({attempt}/{MAX_RETRIES})...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                result = resp.json()
                
                if not result.get("success"):
                    raise RuntimeError(result.get("errors"))
                    
                b64_image = result["result"]["image"]
                return base64.b64decode(b64_image)
                
            except requests.exceptions.HTTPError as e:
                # 400 Bad Request (Content Filter) বা অন্য এরর হলে পরের মডেলে ট্রাই করবে
                print(f"[image_generator] HTTP Error মডেলে '{model}': {e}")
                break 
            except Exception as e:
                print(f"[image_generator] '{model}' চেষ্টা {attempt}/{MAX_RETRIES} ব্যর্থ: {e}")
                if attempt == MAX_RETRIES:
                    print(f"[image_generator] '{model}' পুরোপুরি ব্যর্থ, বিকল্প মডেল খোঁজা হচ্ছে...")
                    break
                time.sleep(5 * attempt)

    # যদি কোনো মডেলই কাজ না করে
    raise RuntimeError("সবগুলো মডেল এবং রিট্রাই শেষ হয়ে গেছে, এই প্রম্পট দিয়ে ছবি তৈরি করা যায়নি।")


def crop_to_landscape(image_bytes, target_size=TARGET_SIZE):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_ratio = target_size[0] / target_size[1]
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize(target_size, Image.LANCZOS)


def generate_all():
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account_id or not api_token:
        raise EnvironmentError(
            "CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN সেট করা নেই (GitHub Secrets এ যোগ করো)।"
        )

    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    scenes = data["scenes"]
    total = len(scenes)

    for i, scene in enumerate(scenes, start=1):
        out_path = os.path.join(IMAGES_DIR, f"scene_{i:03d}.jpg")
        if os.path.exists(out_path):
            continue  # allows resuming a partially completed run

        print(f"[image_generator] ছবি তৈরি হচ্ছে {i}/{total}...")
        prompt = scene["image_prompt"] + STYLE_SUFFIX
        
        try:
            # প্রথমে মূল ভৌতিক প্রম্পট দিয়ে চেষ্টা করা হবে
            img_bytes = cloudflare_generate_image(prompt, account_id, api_token)
        except RuntimeError as e:
            # যদি কন্টেন্ট ফিল্টার ব্লক করে দেয়, তখন সেফ প্রম্পট (SAFE_PROMPT) দিয়ে আবার চেষ্টা করবে
            print(f"[image_generator] ⚠️ সতর্কতা: প্রম্পট ব্লক হয়েছে বা ব্যর্থ হয়েছে! সেফ প্রম্পট ব্যবহার করা হচ্ছে...")
            img_bytes = cloudflare_generate_image(SAFE_PROMPT, account_id, api_token)
            
        img = crop_to_landscape(img_bytes)
        img.save(out_path, "JPEG", quality=90)

        # API লিমিট বাঁচাতে এবং 429 এরর ঠেকাতে ১৫ সেকেন্ডের গ্যাপ
        time.sleep(15)

    print(f"[image_generator] সম্পন্ন - {total}টা ছবি তৈরি হয়েছে।")


if __name__ == "__main__":
    generate_all()
