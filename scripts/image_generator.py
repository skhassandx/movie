"""
image_generator.py
-------------------
Calls Cloudflare Workers AI (@cf/black-forest-labs/flux-1-schnell) to turn
each scene's image_prompt into a picture, then crops/resizes it to a
1280x720 landscape frame for the video.

Free tier note: Cloudflare gives 10,000 Neurons/day. flux-1-schnell costs
~4.8 neurons per 512x512 tile + ~9.6 neurons per step. At the default
4 steps that's ~43 neurons/image, so ~230 images/day free - comfortably
enough for one 10-15 min video (~70-85 images).
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

MODEL = "@cf/black-forest-labs/flux-1-schnell"
MAX_RETRIES = 6


def cloudflare_generate_image(prompt, account_id, api_token):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"prompt": prompt[:2000], "steps": 4}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)

            # 429 = Cloudflare's shared free GPU capacity is temporarily busy.
            # This is common for free-tier image models and usually clears
            # within a minute or two - so wait it out instead of failing fast.
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else min(15 * (2 ** (attempt - 1)), 120)
                print(
                    f"[image_generator] 429 (Cloudflare GPU ব্যস্ত) - {wait:.0f} সেকেন্ড "
                    f"অপেক্ষা করে আবার চেষ্টা করা হচ্ছে ({attempt}/{MAX_RETRIES})..."
                )
                time.sleep(wait)
                continue

            resp.raise_for_status()
            result = resp.json()
            if not result.get("success"):
                raise RuntimeError(result.get("errors"))
            b64_image = result["result"]["image"]
            return base64.b64decode(b64_image)
        except requests.exceptions.HTTPError:
            raise  # non-429 HTTP errors (401/403/etc.) are real problems, don't hide them
        except Exception as e:
            print(f"[image_generator] চেষ্টা {attempt}/{MAX_RETRIES} ব্যর্থ: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(5 * attempt)

    raise RuntimeError("সবগুলো রিট্রাই শেষ হয়ে গেছে, ছবি তৈরি করা যায়নি।")


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
        img_bytes = cloudflare_generate_image(prompt, account_id, api_token)
        img = crop_to_landscape(img_bytes)
        img.save(out_path, "JPEG", quality=90)

        time.sleep(0.5)  # small delay to be gentle on the free-tier rate limit

    print(f"[image_generator] সম্পন্ন - {total}টা ছবি তৈরি হয়েছে।")


if __name__ == "__main__":
    generate_all()
