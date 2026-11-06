"""Turn resolved video ids into per-module summaries.

Reads video_jobs.json and resolved.json written by scrape_scu.py / resolve.mjs,
fetches Panopto DeliveryInfo (which carries the AI summary, key points and
chapters) and writes videos.md for every module plus videos/<id>.json.
YouTube videos get their description, chapters and caption transcript.
"""
import html
import json
import os
import re

import requests

OUT = os.environ.get("SCU_OUT", os.path.expanduser("~/scu_export"))
COOKIES = os.environ.get("SCU_COOKIES", "/tmp/scu_cookies.json")
VID = os.path.join(OUT, "videos")

session = requests.Session()
for c in json.load(open(COOKIES)):
    if c["domain"].lstrip(".").endswith("scu.edu.au") or "panopto" in c["domain"]:
        session.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])


def mmss(sec):
    sec = int(sec or 0)
    return f"{sec // 60}:{sec % 60:02d}"


def delivery(sid):
    url = ("https://scu.au.panopto.com/Panopto/Pages/Viewer/DeliveryInfo.aspx"
           f"?deliveryId={sid}&responseType=json&isLive=false")
    r = session.get(url, timeout=60)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def vtt_text(path):
    """Strip a WebVTT file down to unique spoken lines."""
    if not os.path.exists(path):
        return ""
    lines, seen = [], set()
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if (not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
                or "-->" in line or re.fullmatch(r"\d+", line)):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line).strip()
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return " ".join(lines)


def youtube_extras(vid):
    meta_path = os.path.join(VID, f"yt_{vid}.json")
    if not os.path.exists(meta_path):
        return None, ""
    meta = json.load(open(meta_path))
    transcript = vtt_text(os.path.join(VID, f"yt_{vid}.en.vtt"))
    if not transcript:
        for name in os.listdir(VID):
            if name.startswith(f"yt_{vid}.") and name.endswith(".vtt"):
                transcript = vtt_text(os.path.join(VID, name))
                if transcript:
                    break
    if transcript:
        open(os.path.join(VID, f"yt_{vid}.txt"), "w").write(transcript + "\n")
    return meta, transcript


def render_panopto(job, info):
    d = (info or {}).get("Delivery") or {}
    sid = (info or {}).get("SessionId") or (job.get("resolved") or {}).get("id")
    lines = [f"## {job.get('title') or d.get('SessionName') or 'Video'}"]
    if sid:
        lines.append(f"- Link: https://scu.au.panopto.com/Panopto/Pages/Viewer.aspx?id={sid}")
    lines.append("- Source: Panopto")
    if d.get("Duration"):
        lines.append(f"- Duration: {mmss(d['Duration'])}")
    if d.get("SessionName") and d.get("SessionName") != job.get("title"):
        lines.append(f"- Panopto title: {d['SessionName']}")
    if not info or (info.get("ErrorCode") and info.get("ErrorCode") != 0):
        lines.append("- Summary: not available (video not resolved or not accessible)")
        return "\n".join(lines)
    if d.get("AISummary"):
        lines += ["", "**AI summary**", "", d["AISummary"]]
    if d.get("AIKeyPoints"):
        lines += ["", "**Key points**"] + [f"- {p}" for p in d["AIKeyPoints"]]
    if d.get("AIChapters"):
        lines += ["", "**Chapters**"]
        for ch in d["AIChapters"]:
            lines.append(f"- {mmss(ch.get('Start'))} {ch.get('Summary')}")
    return "\n".join(lines)


def render_youtube(job):
    vid = job["video_id"]
    meta, transcript = youtube_extras(vid)
    title = (meta or {}).get("title") or job.get("title") or vid
    lines = [f"## {title}",
             f"- Link: https://www.youtube.com/watch?v={vid}",
             "- Source: YouTube"]
    if meta:
        if meta.get("duration"):
            lines.append(f"- Duration: {mmss(meta['duration'])}")
        if meta.get("uploader"):
            lines.append(f"- Channel: {meta['uploader']}")
        desc = (meta.get("description") or "").strip()
        if desc:
            lines += ["", "**Description**", "", desc[:1500]]
    if transcript:
        lines += ["", "**Transcript (auto-captions)**",
                  "", transcript[:2000] + ("…" if len(transcript) > 2000 else "")]
        lines.append(f"\nFull transcript: `../../videos/yt_{vid}.txt`")
    return "\n".join(lines)


def render(job, info):
    return render_panopto(job, info) if job["kind"] == "panopto" else render_youtube(job)


def main():
    jobs = json.load(open(os.path.join(OUT, "video_jobs.json")))
    resolved_path = os.path.join(OUT, "resolved.json")
    resolved = json.load(open(resolved_path)) if os.path.exists(resolved_path) else {}
    os.makedirs(VID, exist_ok=True)

    # doc id -> module folder
    doc_section = {}
    for code in ("PHAR2001", "INDG6002"):
        path = os.path.join(OUT, code, "documents.json")
        if not os.path.exists(path):
            continue
        for d in json.load(open(path)):
            doc_section[d["id"]] = (code, d["section"])

    by_section = {}
    for job in jobs:
        if job["kind"] == "youtube":
            title = (youtube_extras(job["video_id"])[0] or {}).get("title")
            if title:
                job["title"] = title
            by_section.setdefault(doc_section.get(job["doc"], ("?", "?")), []).append((job, None))
            continue
        res = resolved.get(job["key"]) or {}
        sid = res.get("id")
        job["resolved"] = res
        info = None
        if sid:
            path = os.path.join(VID, sid + ".json")
            if os.path.exists(path):
                info = json.load(open(path))
            else:
                info = delivery(sid)
                if info:
                    json.dump(info, open(path, "w"), indent=1)
        by_section.setdefault(doc_section.get(job["doc"], ("?", "?")), []).append((job, info))

    for (code, section), entries in sorted(by_section.items()):
        sec_dir = os.path.join(OUT, code, section)
        os.makedirs(sec_dir, exist_ok=True)
        lines = [f"# Videos — {section}", ""]
        for job, info in entries:
            lines.append(render(job, info))
            lines.append("")
        open(os.path.join(sec_dir, "videos.md"), "w").write("\n".join(lines))

    for code in ("PHAR2001", "INDG6002"):
        index = [f"# {code} — video index", ""]
        for (c, section), entries in sorted(by_section.items()):
            if c != code:
                continue
            index.append(f"## {section}")
            for job, _ in entries:
                index.append(f"- {job.get('title')} ({job['kind']})")
            index.append("")
        open(os.path.join(OUT, code, "VIDEOS.md"), "w").write("\n".join(index))

    json.dump(jobs, open(os.path.join(OUT, "video_jobs.json"), "w"), indent=1)
    pan = sum(1 for j in jobs if j["kind"] == "panopto")
    print("videos:", pan, "panopto,", len(jobs) - pan, "youtube;",
          len(by_section), "sections")


if __name__ == "__main__":
    main()
