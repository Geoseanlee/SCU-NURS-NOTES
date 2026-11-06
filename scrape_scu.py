"""Scrape SCU Blackboard Ultra courses (INDG6002, PHAR2001).

Content is fetched from the same JSON API the Ultra web app uses, plus the
Ally alternative-format endpoint for the ePub versions. Requires a cookie
export of an authenticated browser session (see export_cookies.py).
"""
import html
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

import requests

BASE = "https://learn.scu.edu.au"
OUT = os.environ.get("SCU_OUT", os.path.expanduser("~/scu_export"))
COOKIES = os.environ.get("SCU_COOKIES", "/tmp/scu_cookies.json")
COURSES = [("PHAR2001", "_156105_1"), ("INDG6002", "_156096_1")]

ALLY = "https://prod-ap-southeast-2.ally.ac"
ALLY_CLIENT = "239"

session = requests.Session()
for c in json.load(open(COOKIES)):
    domain = c["domain"]
    if domain.lstrip(".").endswith("scu.edu.au") or "panopto" in domain:
        session.cookies.set(c["name"], c["value"], domain=domain, path=c["path"])


def get(url, **kw):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=60, **kw)
            if r.status_code < 500:  # 4xx (e.g. "no children") is final
                if r.status_code in (401, 403):
                    raise SystemExit(f"Not authenticated ({r.status_code}) for {url}")
                return r
        except requests.RequestException as e:
            if attempt == 3:
                raise
            print("  retry", attempt + 1, e, file=sys.stderr)
        time.sleep(1 + attempt)
    return r


def api(cid, content_id=None):
    if content_id:
        url = f"{BASE}/learn/api/v1/courses/{cid}/contents/{content_id}/children?limit=1000"
    else:
        url = f"{BASE}/learn/api/v1/courses/{cid}/contents?limit=1000"
    return get(url).json().get("results", [])


def walk(cid, items, depth=0):
    for it in items:
        yield depth, it
        handler = it.get("contentHandler", "")
        if depth < 8 and ("folder" in handler or "lesson" in handler):
            try:
                yield from walk(cid, api(cid, it["id"]), depth + 1)
            except Exception as e:
                print("  ! children failed", it["id"], e, file=sys.stderr)


def safe(name, limit=90):
    name = re.sub(r"[\\/:*?\"<>|]+", "-", (name or "untitled")).strip(" .")
    name = re.sub(r"\s+", " ", name)
    return name[:limit] or "untitled"


def html_to_text(content):
    content = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", content, flags=re.S | re.I)
    content = re.sub(r"<(br|/p|/div|/li|/h[1-6])\s*/?>", "\n", content, flags=re.I)
    content = re.sub(r"<li[^>]*>", "- ", content, flags=re.I)
    text = re.sub(r"<[^>]+>", "", content)
    text = html.unescape(text)
    lines = [l.strip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l)


_token_cache = {}


def ally_token(cid):
    cached = _token_cache.get(cid)
    if cached and cached[0] > time.time():
        return cached[1]
    token = get(f"{BASE}/learn/api/v1/courses/{cid}/ally/token").json()["authToken"]
    # Ally JWTs last 5 minutes; refresh well before that.
    _token_cache[cid] = (time.time() + 240, token)
    return token


def save_epub(cid, content_id, dest):
    if os.path.exists(dest):
        return "cached"
    url = (f"{ALLY}/api/v1/{ALLY_CLIENT}/courses/{cid}/rich-content/"
           f"content%3A{content_id}/formats/Epub"
           f"?acceptTOU=true&formatParam=&asAttachment=true&contentHash=")
    for _ in range(3):
        token = ally_token(cid)
        r = session.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=120)
        if r.status_code == 202:
            # Ally generates first-time formats asynchronously; poll then re-ask.
            pid = r.json().get("processId")
            for _ in range(60):
                time.sleep(2)
                p = session.get(f"{ALLY}/api/v1/processes/{pid}",
                                headers={"Authorization": f"Bearer {ally_token(cid)}"}, timeout=60)
                if p.status_code == 200 and p.json().get("status") == "Succeeded":
                    break
            continue
        if r.status_code != 200:
            return f"error {r.status_code}"
        data = r.json()
        if not data.get("url"):
            continue
        blob = get(data["url"]).content
        if not blob.startswith(b"PK"):
            return "bad file"
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(blob)
        return "ok"
    return "unavailable"


VIDEO_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([\w-]{6,})")


def scan_html(raw, cid, it, jobs, assets):
    """Collect embedded videos and external links from a document body."""
    for m in VIDEO_RE.finditer(raw):
        jobs.append({"kind": "youtube", "key": "yt:" + m.group(1), "video_id": m.group(1),
                     "title": it.get("title"), "doc": it["id"], "doc_title": it.get("title")})

    for blob in re.findall(r'data-bbfile="([^"]*)"', raw):
        try:
            d = json.loads(html.unescape(blob))
        except Exception:
            continue
        bbtype = d.get("bbtype")
        url = d.get("url", "")
        if bbtype == "embedded-app" and "panopto" in url:
            params = {
                "cim_placement_id": d.get("linkRefId"),
                "course_id": cid,
                "url": url,
                "deploymentId": d.get("deploymentId", ""),
                "custom_parameters": json.dumps(d.get("customParameters", {}), separators=(",", ":")),
                "parent_id": it.get("parentId") or it["id"],
                "blti_placement_uuid": d.get("linkRefUuid", ""),
                "from_ultra": "true",
            }
            launch = f"{BASE}/webapps/blackboard/execute/blti/launchLink?" + urlencode(
                {k: v for k, v in params.items() if v})
            jobs.append({"kind": "panopto", "key": f"{it['id']}#{d.get('linkRefId')}",
                         "launch": launch, "title": d.get("title") or it.get("title"),
                         "doc": it["id"], "doc_title": it.get("title")})
        elif bbtype == "embedded-app" and url:
            assets.append({"type": "external-app", "url": url, "title": d.get("title")})
        elif bbtype == "embedded-unsafe-html":
            src = d.get("resourceUrl") or d.get("href")
            if src:
                try:
                    inner = get(src).text
                except Exception:
                    inner = ""
                for m in VIDEO_RE.finditer(inner):
                    jobs.append({"kind": "youtube", "key": "yt:" + m.group(1),
                                 "video_id": m.group(1), "title": d.get("linkName") or it.get("title"),
                                 "doc": it["id"], "doc_title": it.get("title")})
                for m in re.finditer(r'<iframe[^>]+src="([^"]+)"', inner):
                    assets.append({"type": "iframe", "url": html.unescape(m.group(1)),
                                   "title": it.get("title")})

    for u in sorted(set(re.findall(r'href="(https?://[^"]+)"', raw))):
        if "bbcswebdav" not in u and "learn.scu.edu.au" not in u:
            assets.append({"type": "link", "url": html.unescape(u), "title": it.get("title")})


def process_course(code, cid, all_jobs, all_assets):
    print(f"\n=== {code} ({cid}) ===")
    course_dir = os.path.join(OUT, code)
    os.makedirs(course_dir, exist_ok=True)
    top = api(cid)
    json.dump(top, open(os.path.join(course_dir, "course.json"), "w"), indent=1)

    progress_path = os.path.join(course_dir, "_progress.json")
    progress = json.load(open(progress_path)) if os.path.exists(progress_path) else {}
    documents = []

    for n, section in enumerate(top, 1):
        sec_name = f"{n:02d} - {safe(section['title'])}"
        sec_dir = os.path.join(course_dir, sec_name)
        for sub in ("material", "html", "files"):
            os.makedirs(os.path.join(sec_dir, sub), exist_ok=True)
        rows, texts = [], []
        epub_tasks = []
        counter = 0
        stack = {}
        print(f"[{code}] {sec_name}", flush=True)

        for depth, it in walk(cid, [section]):
            if depth == 0:
                continue
            handler = it.get("contentHandler", "")
            body = (it.get("body") or {}).get("rawText") or ""
            title = (it.get("title") or "").strip()
            if title in ("", "ultraDocumentBody", "untitled"):
                title = stack.get(depth - 1) or section["title"]
            stack[depth] = title
            for deeper in [d for d in stack if d > depth]:
                del stack[deeper]
            parent_path = " / ".join(stack[d] for d in sorted(stack) if d < depth)
            rows.append({"depth": depth, "title": title, "handler": handler,
                         "id": it["id"], "body": bool(body)})

            if handler == "resource/x-bb-document" and body:
                counter += 1
                name = f"{counter:02d} - {safe(title)}"
                htmldoc = (f"<!doctype html><html><head><meta charset='utf-8'>"
                           f"<title>{html.escape(title)}</title>"
                           f"<style>body{{max-width:52rem;margin:2rem auto;padding:0 1rem;"
                           f"font:16px/1.6 system-ui,sans-serif}}img,iframe,video{{max-width:100%}}</style>"
                           f"</head><body><h1>{html.escape(title)}</h1>"
                           f"{body}</body></html>")
                open(os.path.join(sec_dir, "html", name + ".html"), "w").write(htmldoc)
                texts.append(f"\n\n===== {name} =====\n{html_to_text(body)}")
                epub_tasks.append((it["id"], os.path.join(sec_dir, "material", name + ".epub"), name))
                documents.append({"section": sec_name, "name": name, "id": it["id"],
                                  "title": title, "path": parent_path})
                scan_html(body, cid, it, all_jobs, all_assets)
            elif handler == "resource/x-bb-file":
                f = (it.get("contentDetail", {}).get("resource/x-bb-file", {}) or {}).get("file", {})
                if f.get("permanentUrl"):
                    dest = os.path.join(sec_dir, "files", safe(f.get("fileName") or it["title"]))
                    if not os.path.exists(dest):
                        open(dest, "wb").write(get(BASE + f["permanentUrl"]).content)
                        print("   file", os.path.basename(dest))
            elif handler == "resource/x-bb-folder" and body:
                counter += 1
                name = f"{counter:02d} - {safe(title)}"
                open(os.path.join(sec_dir, "html", name + ".html"), "w").write(
                    f"<!doctype html><meta charset='utf-8'><h1>{html.escape(title)}</h1>{body}")
                scan_html(body, cid, it, all_jobs, all_assets)

        open(os.path.join(sec_dir, "extracted_content.txt"), "w").write("".join(texts).strip() + "\n")

        if epub_tasks:
            with ThreadPoolExecutor(max_workers=6) as pool:
                futures = {pool.submit(save_epub, cid, t[0], t[1]): t[2] for t in epub_tasks}
                for fut, name in futures.items():
                    try:
                        print(f"   epub {name}: {fut.result()}", flush=True)
                    except Exception as e:
                        print(f"   epub {name}: error {e}", flush=True)

        with open(os.path.join(sec_dir, "structure.md"), "w") as f:
            f.write(f"# {section['title']}\n\n")
            for r in rows:
                f.write("  " * r["depth"] + f"- {r['title']} `{r['handler'].split('/')[-1]}`\n")

    json.dump(documents, open(os.path.join(course_dir, "documents.json"), "w"), indent=1)
    json.dump(progress, open(progress_path, "w"), indent=1)
    return documents


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs, assets = [], []
    docs = []
    for code, cid in COURSES:
        docs += process_course(code, cid, jobs, assets)
    seen, unique = set(), []
    for j in jobs:
        if j["key"] not in seen:
            seen.add(j["key"])
            unique.append(j)
    json.dump(unique, open(os.path.join(OUT, "video_jobs.json"), "w"), indent=1)
    json.dump(assets, open(os.path.join(OUT, "assets.json"), "w"), indent=1)
    print(f"\nDONE documents={len(docs)} video_jobs={len(unique)} assets={len(assets)}")


if __name__ == "__main__":
    main()
