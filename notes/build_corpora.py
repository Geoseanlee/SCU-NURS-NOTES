"""Build one source corpus per module for the study-note writers.

Each corpus is a plain Markdown file with labelled blocks:

    ## [S1] 01 - Module overview
    ## [V1] Video title
    ## [R1] Reading title

Documents come from ``extracted_content.txt`` (ePub text) in course order.
Videos come from the module's ``videos.md`` (Panopto AI summaries and direct
YouTube links) plus the 65 embedded YouTube videos found by
``fetch_embedded_media.py``.  Readings are optional PDFs in the module's
``files/`` directory.

Usage:
    python3 notes/build_corpora.py --all
    python3 notes/build_corpora.py --all --readings
    python3 notes/build_corpora.py --verify
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = json.load(open(os.path.join(ROOT, "notes", "modules.json")))
VIDEOS = os.path.join(ROOT, "videos")
MANIFEST = os.path.join(ROOT, "notes", "embedded_manifest.json")
OUT = os.path.join(ROOT, "notes", "corpora")


def words(text):
    return len(text.split())


def parse_epubs(text):
    parts = re.split(r"^===== FILE: (.+?) =====\s*$", text, flags=re.M)
    docs = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        docs.append((title, body))
    return docs


def parse_videos_md(path):
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8", errors="ignore").read()
    blocks = re.split(r"^## ", text, flags=re.M)[1:]
    out = []
    for block in blocks:
        lines = block.splitlines()
        title = lines[0].strip()
        source = ""
        link = ""
        for line in lines:
            if line.startswith("- Source:"):
                source = line.split(":", 1)[1].strip()
            elif line.startswith("- Link:"):
                link = line.split(":", 1)[1].strip()
        body = "\n".join(lines[1:]).strip()
        body = re.sub(r"\nFull transcript:.*$", "", body, flags=re.M).strip()
        out.append({"title": title, "source": source, "link": link, "body": body})
    return out


def yt_id(link):
    m = re.search(r"(?:v=|embed/|youtu\.be/)([A-Za-z0-9_-]{11})", link or "")
    return m.group(1) if m else ""


def yt_meta(vid):
    path = os.path.join(VIDEOS, f"yt_{vid}.json")
    if not os.path.exists(path):
        return {}
    try:
        return json.load(open(path))
    except ValueError:
        return {}


def yt_text(vid):
    path = os.path.join(VIDEOS, f"yt_{vid}.txt")
    if os.path.exists(path):
        return open(path, encoding="utf-8", errors="ignore").read().strip()
    return ""


def pdf_text(path, cap_words=8000):
    try:
        out = subprocess.check_output(
            ["pdftotext", "-layout", path, "-"], stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"\n{3,}", "\n\n", out).strip()
    if words(text) > cap_words:
        text = " ".join(text.split()[:cap_words]) + "\n\n[reading truncated at 8,000 words]"
    return text


def build(module, with_readings=False):
    course = module["course"]
    base = os.path.join(ROOT, course, module["path"])
    epub_txt = os.path.join(base, "extracted_content.txt")
    if not os.path.exists(epub_txt):
        raise SystemExit(f"missing {epub_txt}")

    sources = {}
    blocks = []
    counter = {"S": 0, "V": 0, "R": 0}

    def add(kind, title, meta, body):
        counter[kind] += 1
        key = f"{kind}{counter[kind]}"
        sources[key] = {"title": title, **meta, "words": words(body)}
        blocks.append(f"## [{key}] {title}\n" + "\n".join(
            f"{k}: {v}" for k, v in meta.items() if v) + f"\n\n{body}\n")

    for title, body in parse_epubs(open(epub_txt, encoding="utf-8", errors="ignore").read()):
        add("S", title.removesuffix(".epub"), {
            "type": "document",
            "path": f"material/{title}",
        }, body)

    seen_videos = set()
    for video in parse_videos_md(os.path.join(base, "videos.md")):
        if video["source"] == "YouTube":
            vid = yt_id(video["link"])
            if vid and vid in seen_videos:
                continue
            if vid:
                seen_videos.add(vid)
            full = yt_text(vid)
            body = full or video["body"]
            add("V", video["title"], {
                "type": "video",
                "source": "youtube",
                "id": vid,
                "path": f"videos/yt_{vid}.txt" if full else "",
            }, body)
        else:
            add("V", video["title"], {
                "type": "video",
                "source": "panopto",
                "path": "",
            }, video["body"])

    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST))
        key = f"{course}/{module['path']}"
        for vid in manifest.get("per_module", {}).get(key, []):
            if vid in seen_videos:
                continue
            seen_videos.add(vid)
            meta = yt_meta(vid)
            body = yt_text(vid)
            if not body:
                body = (meta.get("description") or "").strip()
            add("V", meta.get("title") or vid, {
                "type": "video",
                "source": "youtube (embedded)",
                "id": vid,
                "path": f"videos/yt_{vid}.txt" if body else "",
            }, body)

    if with_readings:
        files_dir = os.path.join(base, "files")
        if os.path.isdir(files_dir):
            for name in sorted(os.listdir(files_dir)):
                path = os.path.join(files_dir, name)
                if not name.lower().endswith(".pdf") or not os.path.isfile(path):
                    continue
                body = pdf_text(path)
                if body:
                    add("R", name.removesuffix(".pdf"), {
                        "type": "reading",
                        "path": f"files/{name}",
                    }, body)

    total = sum(words(b.split("\n\n", 1)[-1]) for b in blocks)
    header = (
        f"# Corpus — {course} / {module['path']}\n"
        f"Source words: {total}\n"
        f"Documents: {counter['S']}, Videos: {counter['V']}, Readings: {counter['R']}\n\n"
    )
    os.makedirs(os.path.join(OUT, course), exist_ok=True)
    name = f"{module['id']}.md"
    with open(os.path.join(OUT, course, name), "w") as fh:
        fh.write(header + "---\n\n" + "\n---\n\n".join(blocks))
    with open(os.path.join(OUT, course, f"{module['id']}.sources.json"), "w") as fh:
        json.dump(sources, fh, indent=1)
    return counter, total


def verify():
    failures = 0
    for module in MODULES:
        path = os.path.join(OUT, module["course"], f"{module['id']}.md")
        src = os.path.join(OUT, module["course"], f"{module['id']}.sources.json")
        if not os.path.exists(path) or not os.path.exists(src):
            print(f"FAIL missing {path}")
            failures += 1
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        sources = json.load(open(src))
        if "access_token=" in text:
            print(f"FAIL token leak {path}")
            failures += 1
        if words(text) < 2000:
            print(f"FAIL short corpus {path} ({words(text)} words)")
            failures += 1
        missing = re.findall(r"\[([SVR]\d+)\]", text)
        undefined = sorted({m for m in missing if m not in sources})
        if undefined:
            print(f"FAIL undefined {path}: {undefined}")
            failures += 1
        print(f"OK {module['id']}: {words(text):,} words, {len(sources)} sources")
    print(f"{len(MODULES) - failures}/{len(MODULES)} corpora pass")
    return 0 if failures == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--readings", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        sys.exit(verify())
    for module in MODULES:
        counter, total = build(module, args.readings)
        print(f"{module['id']}: {counter['S']} docs, {counter['V']} videos, "
              f"{counter['R']} readings, {total:,} words")


if __name__ == "__main__":
    main()
