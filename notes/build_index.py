"""Build NOTES_INDEX.md from the 12 module note files."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = json.load(open(os.path.join(ROOT, "notes", "modules.json")))
CJK = re.compile(r"[\u4e00-\u9fff]")


def words(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))


def link(path, label):
    return f"[{label}](<{path}>)" if " " in path else f"[{label}]({path})"


def main():
    rows = {"PHAR2001": [], "INDG6002": []}
    missing = 0
    for m in MODULES:
        en = os.path.join(m["course"], m["path"], "study_notes.en.md")
        zh = os.path.join(m["course"], m["path"], "study_notes.zh.md")
        src = os.path.join("notes", "corpora", m["course"], f"{m['id']}.sources.json")
        for p in (en, zh):
            if not os.path.exists(os.path.join(ROOT, p)):
                print(f"missing {p}")
                missing += 1
        if missing:
            continue
        en_text = open(os.path.join(ROOT, en), encoding="utf-8").read()
        zh_text = open(os.path.join(ROOT, zh), encoding="utf-8").read()
        sources = len(json.load(open(os.path.join(ROOT, src)))) if os.path.exists(os.path.join(ROOT, src)) else 0
        number = m["path"].split(" - ")[0]
        title = m["path"].split(" - ", 1)[1]
        rows[m["course"]].append(
            f"| {number} | {title} | {link(en, 'English')} | {link(zh, '中文')} | "
            f"{words(en_text):,} | {len(CJK.findall(zh_text)):,} | {sources} |"
        )
    if missing:
        print(f"{missing} file(s) missing; index not written")
        return 1

    out = [
        "# SCU Study Notes — PHAR2001 and INDG6002",
        "",
        "Detailed, textbook-style study guides for the 12 modules, each in English and",
        "Chinese. The Chinese files keep drug, receptor, legislation and clinical terms in",
        "English so they match the exam language.",
        "",
        "These notes are synthesized from the course documents and videos. They are not a",
        "replacement for the original sources; every note ends with a source map and a",
        "`Go deeper` list. Raw course files are kept locally and are not committed.",
        "",
        "## PHAR2001",
        "",
        "| Module | Title | English | 中文 | EN words | ZH chars | Sources |",
        "|---|---|---|---|---|---|---|",
        *rows["PHAR2001"],
        "",
        "## INDG6002",
        "",
        "| Module | Title | English | 中文 | EN words | ZH chars | Sources |",
        "|---|---|---|---|---|---|---|",
        *rows["INDG6002"],
        "",
        "## How to use",
        "",
        "- Read the English file first if you are preparing for the English exam; use the",
        "  Chinese file when a mechanism needs a faster explanation.",
        "- The source map at the end of each file maps `[S#]` to a document and `[V#]` to a",
        "  video. Use the `Go deeper` list to return to the original material.",
        "- Source gaps are marked explicitly; do not treat background paragraphs as",
        "  examinable course content.",
        "",
    ]
    open(os.path.join(ROOT, "NOTES_INDEX.md"), "w").write("\n".join(out))
    total = sum(len(v) for v in rows.values())
    print(f"{total} modules, {total * 2} files, 0 missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
