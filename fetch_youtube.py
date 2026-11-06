"""Download metadata, description and captions for the YouTube videos found
in the courses (the ones the ePub export drops)."""
import json
import os
import re
import sys
import time

import yt_dlp

OUT = os.environ.get("SCU_OUT", os.path.expanduser("~/scu_export"))
VID = os.path.join(OUT, "videos")
os.makedirs(VID, exist_ok=True)

jobs = json.load(open(os.path.join(OUT, "video_jobs.json")))
ids = sorted({j["video_id"] for j in jobs if j["kind"] == "youtube"})
print(len(ids), "youtube videos", flush=True)

opts = {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en", "en-orig", "en-US", "en-AU"],
    "subtitlesformat": "vtt",
    "outtmpl": os.path.join(VID, "yt_%(id)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "retries": 3,
}

for i, vid in enumerate(ids, 1):
    dest = os.path.join(VID, f"yt_{vid}.json")
    if os.path.exists(dest):
        continue
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("no info")
            subs = info.get("subtitles") or {}
            auto = info.get("automatic_captions") or {}
            if subs or auto:
                ydl.download([url])
        rec = {
            "id": vid,
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "description": info.get("description"),
            "has_manual_captions": bool(subs),
            "has_auto_captions": bool(auto),
        }
        json.dump(rec, open(dest, "w"), indent=1)
        print(f"{i}/{len(ids)} {vid} ok subtitles={bool(subs or auto)}", flush=True)
    except Exception as e:
        print(f"{i}/{len(ids)} {vid} ERROR {e}", flush=True)
    time.sleep(0.3)
