import os
import json
import random
import time
from google import genai
from google.genai import types

# 🌟 ডাইনামিক পাথ (নতুন প্রজেক্ট স্ট্রাকচার অনুযায়ী)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
USED_STORIES_PATH = os.path.join(DATA_DIR, "used_stories.json")

def load_used_stories():
    if os.path.exists(USED_STORIES_PATH):
        with open(USED_STORIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used_story(title):
    used = load_used_stories()
    used.append(title)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USED_STORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=4)

def generate_script():
    print("🎬 Generating Cinematic Movie Explainer / Thriller Story...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ CRITICAL ERROR: GEMINI_API_KEY not found!")
        return False

    client = genai.Client(api_key=api_key)

    # 🌟 মুভি এক্সপ্লেইনার / থ্রিলার ক্যাটাগরি লিস্ট
    genres = [
        "সাইকোলজিক্যাল থ্রিলার ও রহস্যময় ঘটনা (Psychological Thriller)",
        "শার্লক হোমসের মত ডিটেকটিভ রহস্য (Detective Mystery)",
        "স্পেস স্টেশন ও মহাকাশের সার্ভাইভাল থ্রিলার (Space Survival)",
        "ডার্ক ফ্যান্টাসি ও জাদুকরী সাম্রাজ্য (Dark Fantasy)",
        "টাইম লুপ ও রহস্যময় সময় ভ্রমণ (Time Loop Mystery)",
        "নিঝুম দ্বীপের সারভাইভাল অ্যাডভেঞ্চার (Island Survival)",
        "প্যারানরমাল ও ভুতুড়ে রহস্যজনক ঘটনা (Paranormal Mystery)",
        "গভীর সমুদ্রের রহস্য ও হারিয়ে যাওয়া জাহাজ (Deep Sea Mystery)",
        "প্রাচীন পিরামিড ও অভিশপ্ত ধনসম্পদ (Ancient Curse)"
    ]
    
    selected_genre = random.choice(genres)
    scene_count = random.randint(8, 15) 

    # 🌟 মুভি এক্সপ্লেইনার টোনের অ্যাডভান্সড মাস্টার প্রম্পট
    prompt = f"""
    You are a professional YouTube Movie Explainer & Cinematic Storyteller. Write an intense, suspenseful, and engaging story recap in Bengali.

    Target Genre/Topic: {selected_genre}
    The script must be divided into exactly {scene_count} scenes.

    🔥 CRITICAL RULE FOR SCENE 1 (THE MOVIE HOOK):
    - Scene 1 MUST start like a dramatic movie recap to hook the audience instantly.
    - "narration" for Scene 1: Must create instant suspense in Bengali (e.g., 'গল্পের শুরুতে আমরা দেখতে পাই এক নিঝুম রাত...').

    For EVERY scene's "image_prompt", combine these elements into a single English string:
    - [Style]: Photorealistic movie still, 8k resolution, unreal engine 5 render.
    - [Subject & Motion]: Describe the character's exact action and emotional expression clearly.
    - [Lighting & Atmosphere]: Dark and moody, dramatic shadows, neon contrast, or fog.
    - [Camera Movement]: Mention camera framing (e.g., "Slow dolly zoom", "Extreme close-up", "Low-angle cinematic shot").

    Rules:
    - The story must be in Bengali.
    - Output MUST be valid JSON only following the exact structure below.

    JSON Format:
    {{
        "title": "গল্পের একটি আকর্ষণীয় বাংলা টাইটেল (Movie Explainer Style)",
        "genre": "{selected_genre}",
        "scenes": [
            {{
                "scene_number": 1,
                "narration": "গল্পের শুরুতে আমরা দেখতে পাই এক নির্জন পাহাড়, যেখানে একা দাঁড়িয়ে ছিল অয়ন।",
                "image_prompt": "Cinematic movie still, wide landscape shot, a young man standing on a foggy lonely cliff, dramatic dark sunset, intense mood, dynamic framing, 8k resolution, hyper-realistic, highly detailed"
            }}
        ]
    }}
    """

    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-pro']

    for attempt in range(3): 
        for model_name in models_to_try:
            try:
                print(f"🔄 Generating with {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.9
                    )
                )

                story_text = response.text.strip()
                if story_text.startswith("```json"):
                    story_text = story_text.replace("```json", "").replace("```", "").strip()
                elif story_text.startswith("```"):
                    story_text = story_text.replace("```", "").strip()

                story_data = json.loads(story_text)
                
                # চেক করুন এই গল্প আগে ব্যবহার হয়েছে কিনা
                used_stories = load_used_stories()
                if story_data["title"] in used_stories:
                    print(f"⚠️ গল্পটি ('{story_data['title']}') আগে ব্যবহার হয়েছে। আবার চেষ্টা করছি...")
                    continue

                os.makedirs(OUTPUT_DIR, exist_ok=True)
                with open(SCRIPT_DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=4)
                
                save_used_story(story_data["title"])
                print(f"✅ Success! Script Generated | Genre: {selected_genre}")
                return True

            except Exception as e:
                print(f"⚠️ {model_name} failed: {e}")
                time.sleep(5) 

    print("❌ Failed to generate script after all retries.")
    return False

if __name__ == "__main__":
    generate_script()
