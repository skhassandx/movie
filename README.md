# MysteryTales-Bangla

সম্পূর্ণ ফ্রি অটোমেটেড পাইপলাইন: প্রতি রানে Gemini একটা পাবলিক-ডোমেইন গল্প
(পশ্চিমা ক্লাসিক অথবা বাংলা রূপকথা - দুটোই মিক্স, Gemini নিজেই বেছে নেয়) বেছে
বাংলা সাসপেন্স/মিস্ট্রি এক্সপ্লেইনার স্ক্রিপ্ট লেখে → Cloudflare দিয়ে ছবি বানায়
→ Edge-TTS দিয়ে ভয়েসওভার বানায় → MoviePy দিয়ে ১০-১৫ মিনিটের ল্যান্ডস্কেপ ভিডিও
অ্যাসেম্বল করে → YouTube-এ আপলোড করে। পুরোটাই GitHub Actions এ চলে, কোনো
আসল মুভি/সিনেমার ফুটেজ ব্যবহার হয় না, তাই কপিরাইট স্ট্রাইকের ঝুঁকি নেই।

## ফোল্ডার স্ট্রাকচার

```
MysteryTales-Bangla/
├── .github/workflows/main.yml   # শিডিউল অনুযায়ী পুরো পাইপলাইন চালায়
├── scripts/
│   ├── script_generator.py      # Gemini দিয়ে স্ক্রিপ্ট
│   ├── image_generator.py       # Cloudflare Workers AI দিয়ে ছবি
│   ├── audio_generator.py       # Edge-TTS দিয়ে ভয়েসওভার
│   ├── video_editor.py          # MoviePy দিয়ে ভিডিও অ্যাসেম্বলি
│   └── youtube_uploader.py      # YouTube আপলোড
├── data/used_stories.json       # কোন গল্প আগে ব্যবহার হয়েছে তার লিস্ট (পুনরাবৃত্তি এড়াতে)
├── main.py                      # সব ধাপ একসাথে চালায়
└── requirements.txt
```

## প্রয়োজনীয় GitHub Secrets

Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret নাম | কোথা থেকে পাবে |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio (তোমার ToonMagic প্রজেক্টেরটাও ব্যবহার করতে পারো, অথবা নতুন key বানাও) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → ডান পাশে Account ID দেখা যায় |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → My Profile → API Tokens → Workers AI অনুমতি দিয়ে নতুন token |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` | Google Cloud Console → OAuth client (YouTube Data API v3 enabled) |
| `YOUTUBE_REFRESH_TOKEN` | নতুন চ্যানেলের জন্য OAuth Playground দিয়ে refresh token বানাও - ToonMagic এর জন্য যেভাবে করেছিলে ঠিক সেই একই প্রসেস, শুধু নতুন চ্যানেল/Google account সিলেক্ট করবে |

⚠️ কখনো এই keys সরাসরি কোডে বা GitHub web editor এ পেস্ট করো না - শুধু Secrets এ রাখো।

## চালানোর আগে

1. এই পুরো ফোল্ডারটা একটা নতুন (বা পুরনো) GitHub রিপোতে push করো।
2. উপরের Secrets গুলো যোগ করো।
3. Actions ট্যাব থেকে ম্যানুয়ালি একবার "Run workflow" চেপে টেস্ট করো (schedule এর জন্য অপেক্ষা না করে)।
4. প্রথমবার ভিডিও ঠিকঠাক এসেছে কিনা YouTube Studio তে চেক করো, তারপর নিশ্চিন্তে অটো-শিডিউলে ছেড়ে দাও।

## কাস্টমাইজেশন

- **আপলোডের ফ্রিকোয়েন্সি**: `.github/workflows/main.yml` এর `cron` লাইন বদলাও।
- **ভিডিওর দৈর্ঘ্য**: `scripts/script_generator.py` এর `TARGET_MINUTES` বদলাও (মনে রাখবে - বেশি
  দৈর্ঘ্য মানে বেশি ছবি, Cloudflare এর দৈনিক ফ্রি কোটার (~১৫০-৩০০ ছবি/দিন) মধ্যে রাখা ভালো)।
- **কণ্ঠস্বর**: `scripts/audio_generator.py` এর `VOICE` বদলে `bn-BD-NabanitaNeural` (মহিলা কণ্ঠ) করা যায়।
- **থাম্বনেইল/ট্যাগ স্টাইল**: `scripts/script_generator.py` এর প্রম্পটে নিজের চাহিদামতো এডিট করো।

## গুরুত্বপূর্ণ - কপিরাইট নিরাপত্তা

- শুধু পাবলিক ডোমেইন (কপিরাইট মেয়াদ শেষ হওয়া) গল্প ব্যবহার হয় - কোনো আধুনিক বই/মুভি/সিরিজ না।
- সব ছবি এবং ভয়েস ১০০% AI-generated, কোনো আসল ফুটেজ/অডিও কপি করা হয় না, তাই Content ID
  ক্লেইম বা কপিরাইট স্ট্রাইকের ঝুঁকি নেই।
- ভিডিও বিবরণে একটা ছোট AI-ডিসক্লোজার লাইন অটোমেটিক যোগ হয় (স্বচ্ছতার জন্য)।

## নোট: তোমার আগের script_generator.py

তুমি বলেছিলে script_generator.py আগেই বানানো আছে। এখানে আমি একটা সম্পূর্ণ, স্বয়ংসম্পূর্ণ ভার্সন
দিয়েছি যা বাকি সব স্ক্রিপ্টের (image/audio/video) সাথে ম্যাচ করে। যদি তোমার আগেরটার আউটপুট
ফরম্যাট আলাদা হয়, হয় এই ফাইলটা দিয়ে replace করো, অথবা আমাকে তোমার পুরনো ফাইলটা পাঠাও -
তাহলে আমি বাকি স্ক্রিপ্টগুলোর parsing regex তোমার ফরম্যাটের সাথে মিলিয়ে দেব।
