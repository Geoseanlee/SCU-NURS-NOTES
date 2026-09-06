import zipfile, re, os, glob, html as html_lib

def html_to_text(html_content):
    # Remove script and style tags
    html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.S|re.I)
    # Replace line breaks and paragraph closing tags with newline characters
    html_content = re.sub(r'<(br|/p|/div|/li|/h[1-6])\s*/?>', '\n', html_content, flags=re.I)
    # Format list items
    html_content = re.sub(r'<li[^>]*>', '- ', html_content, flags=re.I)
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Unescape HTML entities
    text = html_lib.unescape(text)
    # Clean up whitespace
    lines = [l.strip() for l in text.splitlines()]
    return '\n'.join([l for l in lines if l])

def numeric_prefix(fname):
    m = re.match(r'^(\d+)', os.path.basename(fname))
    return int(m.group(1)) if m else 9999

# Locate module 2 material
folder = "NURS5009/module2/material"
files = glob.glob(os.path.join(folder, "*.epub"))
files.sort(key=numeric_prefix)

out = []
for f in files:
    name = os.path.basename(f)
    try:
        with zipfile.ZipFile(f) as z:
            names = z.namelist()
            target = None
            # Find the index.html file
            for n in names:
                if n.lower().endswith('index.html'):
                    target = n
                    break
            # Fallback to any html/xhtml file
            if not target:
                for n in names:
                    if n.lower().endswith('.html') or n.lower().endswith('.xhtml'):
                        target = n
                        break
            if target:
                content = z.read(target).decode('utf-8', errors='ignore')
                text = html_to_text(content)
            else:
                text = "[NO HTML FOUND]"
    except Exception as e:
        text = f"[ERROR: {e}]"
    out.append(f"===== FILE: {name} =====\n{text}\n")

# Save output to module2_extract.txt
output_path = "NURS5009/module2/module2_extract.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(out))

print("DONE", len(out), "files extracted to", output_path)
