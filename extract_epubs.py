"""Extract text from the downloaded Ally ePubs, same format as extract_all.py.

Run after scrape_scu.py:

    python3 extract_epubs.py ~/scu_export

Every section folder that has a material/ directory gets an
extracted_content.txt built from its .epub files.
"""
import glob
import html as html_lib
import os
import re
import sys
import zipfile


def html_to_text(html_content):
    html_content = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_content, flags=re.S | re.I)
    html_content = re.sub(r"<(br|/p|/div|/li|/h[1-6])\s*/?>", "\n", html_content, flags=re.I)
    html_content = re.sub(r"<li[^>]*>", "- ", html_content, flags=re.I)
    text = re.sub(r"<[^>]+>", "", html_content)
    text = html_lib.unescape(text)
    lines = [l.strip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l)


def numeric_prefix(path):
    m = re.match(r"^(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 9999


def extract_section(section_dir):
    epub_files = sorted(glob.glob(os.path.join(section_dir, "material", "*.epub")),
                        key=numeric_prefix)
    if not epub_files:
        return 0
    output = []
    for epub in epub_files:
        name = os.path.basename(epub)
        try:
            with zipfile.ZipFile(epub) as z:
                target = next((n for n in z.namelist() if n.lower().endswith("index.html")), None)
                if not target:
                    target = next((n for n in z.namelist()
                                   if n.lower().endswith((".html", ".xhtml"))), None)
                if target:
                    text = html_to_text(z.read(target).decode("utf-8", errors="ignore"))
                else:
                    text = "[ERROR: No HTML or XHTML content found inside the EPUB]"
        except Exception as e:
            text = f"[ERROR extracting or parsing EPUB: {e}]"
        output.append(f"===== FILE: {name} =====\n{text}\n")
    with open(os.path.join(section_dir, "extracted_content.txt"), "w") as f:
        f.write("\n\n".join(output))
    return len(epub_files)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/scu_export")
    total = 0
    for section in sorted(glob.glob(os.path.join(root, "*", "*"))):
        if not os.path.isdir(os.path.join(section, "material")):
            continue
        n = extract_section(section)
        if n:
            total += n
            print(f"{os.path.relpath(section, root)}: {n} epubs")
    print(f"total {total} epubs extracted")


if __name__ == "__main__":
    main()
