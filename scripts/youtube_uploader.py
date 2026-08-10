"""
youtube_uploader.py
--------------------
Uploads output/final_video.mp4 to YouTube using a pre-authorized OAuth
refresh token (same pattern as the ToonMagic Bangla project - generate the
refresh token once locally/OAuth Playground, then store client id/secret/
refresh token as GitHub Secrets).
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUTPUT_DIR = "output"
SCRIPT_DATA_PATH = os.path.join(OUTPUT_DIR, "script_data.json")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "final_video.mp4")

CATEGORY_ID = "24"  # Entertainment

DISCLOSURE = (
    "\n\n---\nএই ভিডিওর বর্ণনা ও ভিজ্যুয়াল AI দিয়ে তৈরি, কপিরাইট-মুক্ত (পাবলিক ডোমেইন) "
    "সাহিত্য/লোককথা অবলম্বনে। বিনোদনের উদ্দেশ্যে তৈরি।"
)


def get_credentials():
    return Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )


def upload():
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"{VIDEO_PATH} পাওয়া যায়নি - video_editor ধাপ আগে চালাও।")

    with open(SCRIPT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": data["title"][:100],
            "description": (data["description"] + DISCLOSURE)[:5000],
            "tags": data.get("tags", []),
            "categoryId": CATEGORY_ID,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(VIDEO_PATH, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print("[youtube_uploader] আপলোড শুরু হচ্ছে...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube_uploader] আপলোড হয়েছে {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[youtube_uploader] সম্পন্ন! https://youtu.be/{video_id}")
    return video_id


if __name__ == "__main__":
    upload()
