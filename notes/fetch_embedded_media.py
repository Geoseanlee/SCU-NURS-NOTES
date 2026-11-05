"""Find YouTube videos hidden inside Ultra embedded-HTML wrappers.

Ultra stores some activities as an ``embedded-unsafe-html`` anchor whose target
is a small HTML file on bbcswebdav.  The file usually contains a YouTube iframe,
so the video never appears in the document body and is missed by a normal scan.

Usage:
    python3 notes/fetch_embedded_media.py --scan
    python3 notes/fetch_embedded_media.py --check
    python3 notes/fetch_embedded_media.py --fetch-transcripts --ytdlp /path/to/yt-dlp

The scan writes ``notes/embedded_manifest.json`` and
``notes/new_youtube_ids.txt``.  Cookies are read from ``/tmp/scu_cookies.json``
and are never written to the manifest.
"""
import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIES = os.environ.get("SCU_COOKIES", "/tmp/scu_cookies.json")
MANIFEST = os.path.join(ROOT, "notes", "embedded_manifest.json")
IDS_FILE = os.path.join(ROOT, "notes", "new_youtube_ids.txt")
VIDEOS = os.path.join(ROOT, "videos")
YT_RE = re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]{11})")


def session():
    s = requests.Session()
    for c in json.load(open(COOKIES)):
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
    return s


def wrappers():
    """(module_path, document_html, wrapper_url) for every embedded HTML anchor."""
    out = []
    for course in ("PHAR2001", "INDG6002"):
        for path in sorted(
            os.path.join(ROOT, course, d, "html", f)
            for d in os.listdir(os.path.join(ROOT, course))
            if os.path.isdir(os.path.join(ROOT, course, d, "html"))
            for f in os.listdir(os.path.join(ROOT, course, d, "html"))
            if f.endswith(".html")
        ):
            html = open(path, encoding="utf-8", errors="ignore").read()
            for m in re.finditer(
                r'<a[^>]+data-bbtype="embedded-unsafe-html"[^>]*href="([^"]+)"', html
            ):
                module = os.path.relpath(os.path.dirname(os.path.dirname(path)), ROOT)
                out.append((module, path, m.group(1)))
    return out


def fetch(url):
    try:
        r = session().get(url, timeout=60)
        return url, r.status_code, r.text
    except requests.RequestException as exc:
        return url, 0, str(exc)


def scan():
    anchors = wrappers()
    unique = {url for _, _, url in anchors}
    print(f"{len(anchors)} anchors, {len(unique)} unique wrapper URLs")
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for url, status, text in pool.map(fetch, unique):
            results[url] = {
                "status": status,
                "ids": sorted(set(YT_RE.findall(text))),
            }
    per_module = {}
    for module, doc, url in anchors:
        per_module.setdefault(module, set()).update(results[url]["ids"])
    existing = {
        name[3:-5]
        for name in os.listdir(VIDEOS)
        if name.startswith("yt_") and name.endswith(".json")
    }
    all_ids = sorted({i for d in results.values() for i in d["ids"]})
    new_ids = sorted(set(all_ids) - existing)
    manifest = {
        "embeds": {u: {**d, "files": sorted({f for m, f, x in anchors if x == u})}
                   for u, d in results.items()},
        "per_module": {k: sorted(v) for k, v in per_module.items()},
        "all_ids": all_ids,
        "new_ids": new_ids,
    }
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    json.dump(manifest, open(MANIFEST, "w"), indent=1)
    with open(IDS_FILE, "w") as fh:
        fh.write("\n".join(new_ids) + "\n")
    print(f"{len(all_ids)} unique YouTube IDs, {len(new_ids)} new")
    for module in sorted(per_module):
        print(f"  {len(per_module[module]):3d}  {module}")
    print(f"wrote {MANIFEST} and {IDS_FILE}")


def transcript_ok(vid):
    meta = os.path.join(VIDEOS, f"yt_{vid}.json")
    text = os.path.join(VIDEOS, f"yt_{vid}.txt")
    if not os.path.exists(meta) or not os.path.exists(text):
        return False
    return len(open(text, encoding="utf-8", errors="ignore").read().split()) >= 40


def vtt_text(path):
    """Strip a WebVTT file down to unique spoken lines."""
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


def finalize():
    """Rename .info.json and turn .vtt captions into .txt transcripts."""
    ids = [line.strip() for line in open(IDS_FILE) if line.strip()]
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    no_captions = set(manifest.get("no_captions", []))
    for vid in ids:
        info = os.path.join(VIDEOS, f"yt_{vid}.info.json")
        target = os.path.join(VIDEOS, f"yt_{vid}.json")
        if os.path.exists(info):
            if os.path.exists(target):
                os.remove(info)
            else:
                os.replace(info, target)
        txt = os.path.join(VIDEOS, f"yt_{vid}.txt")
        if not os.path.exists(txt):
            vtts = sorted(glob.glob(os.path.join(VIDEOS, f"yt_{vid}.*.vtt")))
            for vtt in vtts:
                text = vtt_text(vtt)
                if text:
                    open(txt, "w").write(text + "\n")
                    break
        if not os.path.exists(txt) and os.path.exists(target):
            meta = json.load(open(target))
            desc = (meta.get("description") or "").strip()
            if desc:
                open(txt, "w").write(
                    "[No English captions available. YouTube description follows.]\n\n" + desc
                )
            no_captions.add(vid)
        print(("OK   " if transcript_ok(vid) else "MISS ") + vid)
    if os.path.exists(MANIFEST):
        manifest["no_captions"] = sorted(no_captions)
        json.dump(manifest, open(MANIFEST, "w"), indent=1)


def check():
    if not os.path.exists(MANIFEST):
        sys.exit("run --scan first")
    manifest = json.load(open(MANIFEST))
    ids = manifest["new_ids"]
    allowed = set(manifest.get("no_captions", []))
    ok = [i for i in ids if transcript_ok(i)]
    missing = [i for i in ids if not transcript_ok(i)]
    hard = [i for i in missing if i not in allowed]
    print(f"{len(ids)} new IDs; {len(ok)} with usable transcript; "
          f"{len(missing) - len(hard)} description-only; {len(hard)} missing")
    if hard:
        print("missing:", " ".join(hard))
    return 0 if not hard else 1


def fetch_transcripts(ytdlp):
    ids = [line.strip() for line in open(IDS_FILE) if line.strip()]
    cmd = [
        ytdlp, "-a", IDS_FILE, "--skip-download",
        "--write-info-json", "--write-auto-subs", "--write-subs",
        "--sub-langs", "en", "--sub-format", "vtt",
        "-o", os.path.join(VIDEOS, "yt_%(id)s"),
    ]
    print("running", " ".join(cmd))
    return subprocess.call(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--fetch-transcripts", action="store_true")
    ap.add_argument("--ytdlp", default="yt-dlp")
    args = ap.parse_args()
    if args.fetch_transcripts:
        sys.exit(fetch_transcripts(args.ytdlp))
    if args.finalize:
        finalize()
        sys.exit(0)
    if args.check:
        sys.exit(check())
    scan()


if __name__ == "__main__":
    main()
