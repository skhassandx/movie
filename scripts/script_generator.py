"""
script_generator.py
--------------------
Uses Gemini to pick a public-domain story (Western classic OR Bengali
folklore) and turn it into a Bengali "mystery/suspense explainer" script,
broken into narration scenes with an image prompt for each scene.

Output contract (plain delimited text from Gemini, parsed with regex -
kept deliberately simple/robust instead of asking Gemini for JSON, since
JSON responses from LLMs break parsing more often than a simple template):

TITLE: <bengali title>
DESCRIPTION: <youtube description>
TAGS: tag1, tag2, tag3
---SCENE---
NARRATION: <bengali narration line for this scene>
IMAGE_PROMPT: <english prompt describing the visual for this scene>
---END---
(...repeated for every scene...)

Final result is saved to output/script_data.json for the next stages.
"""

import os
import re
import json
from google import genai

MODEL_NAME = "gemini-3.5-flash"
OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
USED_STORIES_PATH = os.path.join("data", "used_stories.json")

# Target video length in minutes (medium length, as decided).
TARGET_MINUTES = (10, 15)
# Bengali narration speech rate assumption for edge-tts (approx words/min).
WPM = 155


def load_used_stories():
    if not os.path.exists(USED_STORIES_PATH):
        return []
    with open(USED_STORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("used_titles", [])


def save_used_stories(titles):
    os.makedirs(os.path.dirname(USED_STORIES_PATH), exist_ok=True)
    with open(USED_STORIES_PATH, "w", encoding="utf-8") as f:
        json.dump({"used_titles": titles}, f, ensure_ascii=False, indent=2)


def build_prompt(used_titles):
    min_words = TARGET_MINUTES[0] * WPM
    max_words = TARGET_MINUTES[1] * WPM
    avoid_block = ", ".join(used_titles) if used_titles else "(কোনোটা নেই - এটাই প্রথম ভিডিও)"

    return f"""তুমি একজন অভিজ্ঞ বাংলা ইউটিউব "Mystery/Suspense Explainer" চ্যানেলের স্ক্রিপ্ট রাইটার।

কাজ: নিচের দুই ধরনের যেকোনো একটি পাবলিক ডোমেইন (কপিরাইট-মুক্ত, ১০০+ বছরের পুরনো) গল্প বেছে নাও,
যেটা এখনো ব্যবহার হয়নি:
1. পশ্চিমা ক্লাসিক রহস্য/থ্রিলার সাহিত্য (যেমন: শার্লক হোমস গল্পগুলো, এডগার অ্যালান পো,
   ড্রাকুলা, ফ্র্যাঙ্কেনস্টাইন, দ্য টেল-টেল হার্ট, দ্য কাস্ক অফ অ্যামন্টিলাডো ইত্যাদি)
2. বাংলা রূপকথা/লোককথা, কিন্তু সাসপেন্স/রহস্য আঙ্গিকে নতুন করে বলা (ঠাকুরমার ঝুলি ধাঁচের
   পুরনো, কপিরাইট-মুক্ত গল্প)

ইতিমধ্যে ব্যবহৃত গল্পগুলো (এগুলো আবার বেছো না): {avoid_block}

এখন সেই গল্পটাকে বাংলা ভাষায় একটা ড্রামাটিক, হুক-ভিত্তিক "explainer" স্টাইলে ন্যারেশন স্ক্রিপ্টে
রূপান্তর করো। ভিডিওটা {TARGET_MINUTES[0]}-{TARGET_MINUTES[1]} মিনিটের হবে, তাই মোট ন্যারেশন
প্রায় {min_words}-{max_words} শব্দ হতে হবে (বাংলা TTS পড়ার গতি অনুযায়ী হিসাব করা)।

স্ক্রিপ্টকে ছোট ছোট "scene" এ ভাগ করো (প্রতিটা scene প্রায় ২০-৩০ শব্দের ন্যারেশন, প্রায় ৭-১০
সেকেন্ডের বলার সময়)। মোট scene সংখ্যা আনুমানিক ৬৫-৮৫টা হবে। প্রতিটা scene এর জন্য একটা
ডিটেইলড ইংরেজি ইমেজ প্রম্পট দাও যা AI ইমেজ জেনারেটরের জন্য উপযুক্ত - সিনেম্যাটিক, ড্রামাটিক
লাইটিং, একই ভিজ্যুয়াল স্টাইল ধরে রাখতে হবে পুরো ভিডিও জুড়ে।

নিয়ম:
- শুধু গল্পের বর্ণনা/সারমর্ম বলবে, কোনো আসল সিনেমা/মুভির নাম বা চরিত্র উল্লেখ করবে না।
- প্রথম ২-৩টা scene অবশ্যই একটা শক্তিশালী হুক দিয়ে শুরু করবে (দর্শক যাতে স্ক্রল না করে)।
- শেষে একটা সংক্ষিপ্ত টুইস্ট/উপসংহার/নৈতিক শিক্ষা রাখবে।
- আউটপুট অবশ্যই নিচের ফরম্যাট হুবহু মেনে চলবে, অন্য কোনো টেক্সট, মার্কডাউন, বা ব্যাখ্যা দিবে না।

ফরম্যাট:
TITLE: <আকর্ষণীয় বাংলা টাইটেল, ৬০ ক্যারেক্টারের কম>
DESCRIPTION: <২-৩ লাইনের ইউটিউব বিবরণ, বাংলায়>
TAGS: <৮-১২টা কমা দিয়ে আলাদা করা রিলেভেন্ট ট্যাগ>
---SCENE---
NARRATION: <বাংলা ন্যারেশন লাইন>
IMAGE_PROMPT: <English image prompt>
---END---
---SCENE---
NARRATION: <বাংলা ন্যারেশন লাইন>
IMAGE_PROMPT: <English image prompt>
---END---
(...সব scene এর জন্য একই প্যাটার্নে চালিয়ে যাও...)
"""


SCENE_RE = re.compile(
    r"---SCENE---\s*NARRATION:\s*(.*?)\s*IMAGE_PROMPT:\s*(.*?)\s*---END---",
    re.DOTALL,
)


def parse_response(text):
    title_m = re.search(r"TITLE:\s*(.+)", text)
    desc_m = re.search(r"DESCRIPTION:\s*(.+)", text)
    tags_m = re.search(r"TAGS:\s*(.+)", text)

    if not title_m:
        raise ValueError("Gemini আউটপুটে TITLE পাওয়া যায়নি - প্রম্পট/মডেল রেসপন্স চেক করো।")

    title = title_m.group(1).strip()
    description = desc_m.group(1).strip() if desc_m else title
    tags = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    scenes = []
    for m in SCENE_RE.finditer(text):
        narration = m.group(1).strip()
        image_prompt = m.group(2).strip()
        if narration and image_prompt:
            scenes.append({"narration": narration, "image_prompt": image_prompt})

    if len(scenes) < 20:
        raise ValueError(
            f"মাত্র {len(scenes)}টা scene পার্স হয়েছে - খুব কম। Gemini আউটপুট ফরম্যাট ঠিকমতো "
            "অনুসরণ করেনি, আবার চেষ্টা করো।"
        )

    return {"title": title, "description": description, "tags": tags, "scenes": scenes}


def generate():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY সেট করা নেই (GitHub Secrets এ যোগ করো)।")

    client = genai.Client(api_key=api_key)
    used_titles = load_used_stories()
    prompt = build_prompt(used_titles)

    print("[script_generator] Gemini দিয়ে স্ক্রিপ্ট জেনারেট করা হচ্ছে...")
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    data = parse_response(response.text)

    print(f"[script_generator] টাইটেল: {data['title']}")
    print(f"[script_generator] মোট {len(data['scenes'])}টা scene পাওয়া গেছে।")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SCRIPT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Remember this title so future runs don't repeat the same story.
    used_titles.append(data["title"])
    save_used_stories(used_titles)

    return data


if __name__ == "__main__":
    generate()
