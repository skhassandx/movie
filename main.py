"""
main.py
-------
Runs the full MysteryTales-Bangla pipeline in order:
script -> images -> audio -> video -> upload.

Each stage fails loudly (non-zero exit) so a broken stage shows up clearly
as a failed GitHub Actions run instead of silently producing a bad video.
"""

import sys
import traceback

from scripts import script_generator, image_generator, audio_generator, video_editor, youtube_uploader


def run_stage(name, fn):
    print(f"\n===== ধাপ: {name} =====")
    try:
        return fn()
    except Exception:
        print(f"[main] ধাপ '{name}' ব্যর্থ হয়েছে:")
        traceback.print_exc()
        sys.exit(1)


def main():
    run_stage("স্ক্রিপ্ট জেনারেশন (Gemini)", script_generator.generate)
    run_stage("ইমেজ জেনারেশন (Cloudflare)", image_generator.generate_all)
    run_stage("ভয়েসওভার জেনারেশন (Edge-TTS)", audio_generator.generate_all)
    run_stage("ভিডিও অ্যাসেম্বলি (MoviePy)", video_editor.build_video)
    video_id = run_stage("ইউটিউব আপলোড", youtube_uploader.upload)

    print(f"\n✅ সম্পূর্ণ পাইপলাইন সফল! ভিডিও: https://youtu.be/{video_id}")


if __name__ == "__main__":
    main()
