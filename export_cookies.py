"""Export the SCU cookies from Chrome so the scraper can authenticate.

macOS only. Reads Chrome's cookie database, decrypts the v10 values with the
"Chrome Safe Storage" Keychain item, and writes the SCU / Panopto cookies to
/tmp/scu_cookies.json.

The output contains live session credentials. Do not commit it, do not paste it
into a chat, and delete it when you are done scraping.

    python3 export_cookies.py
    scp /tmp/scu_cookies.json macmini:/tmp/scu_cookies.json
"""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess

src = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
shutil.copy(src, "/tmp/ck_air.db")
pw = subprocess.check_output(
    ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage", "-a", "Chrome"]
).strip()
key = hashlib.pbkdf2_hmac("sha1", pw, b"saltysalt", 1003, 16).hex()


def dec(blob, host):
    if not blob.startswith(b"v10"):
        return ""
    p = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", "-d", "-K", key, "-iv", "20" * 16, "-nopad"],
        input=blob[3:], capture_output=True,
    )
    out = p.stdout
    if not out:
        return ""
    out = out[:-out[-1]]  # strip PKCS7
    if out.startswith(hashlib.sha256(host.encode()).digest()):
        out = out[32:]  # Chrome >=80 binds the cookie to the host
    try:
        return out.decode()
    except UnicodeDecodeError:
        return ""


rows = []
db = sqlite3.connect("/tmp/ck_air.db")
for host, name, enc, path, secure, http, expires in db.execute(
    "select host_key,name,encrypted_value,path,is_secure,is_httponly,expires_utc "
    "from cookies where host_key like '%scu.edu.au%' or host_key like '%panopto%'"
):
    val = dec(enc, host)
    if not val:
        continue
    rows.append({
        "name": name, "value": val, "domain": host, "path": path or "/",
        "secure": bool(secure), "httpOnly": bool(http),
        # Chrome epoch: microseconds since 1601-01-01
        "expires": (expires / 1_000_000 - 11644473600) if expires else -1,
    })
json.dump(rows, open("/tmp/scu_cookies.json", "w"), indent=1)
print("exported", len(rows), "cookies")
for r in rows:
    print(" ", r["domain"], r["name"])
