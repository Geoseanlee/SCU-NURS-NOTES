"""Check study notes for length, citations, language, and duplication.

Usage:
    python3 notes/check_notes.py --module phar-m1 --lang en
    python3 notes/check_notes.py --all
    python3 notes/check_notes.py --duplicates
    python3 notes/check_notes.py --self-test
"""
import argparse
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = json.load(open(os.path.join(ROOT, "notes", "modules.json")))
CJK = re.compile(r"[\u4e00-\u9fff]")
MARKER = re.compile(r"\[([SVR]\d+)\]")
STOP = set("""the a an and or but if then that this these those of to in on for with as at by
from is are was were be been being it its their they we you i he she not no can may
will would should could have has had do does did than which who whom whose what when
where why how all any both each few more most other some such only own same so too very
just also into about after before between during through over under again further once
here there when where why how""".split())


def words(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))


def cjk_count(text):
    return len(CJK.findall(text))


def resolve(arg):
    for m in MODULES:
        if arg in (m["id"], m["path"], f"{m['course']}/{m['path']}"):
            return m
    for m in MODULES:
        if arg.lower() in m["path"].lower():
            return m
    raise SystemExit(f"unknown module: {arg}")


def paths(module, lang):
    note = os.path.join(ROOT, module["course"], module["path"], f"study_notes.{lang}.md")
    sources = os.path.join(ROOT, "notes", "corpora", module["course"],
                           f"{module['id']}.sources.json")
    return note, sources


def section(text, name):
    m = re.search(rf"^##\s+{re.escape(name)}\s*$", text, flags=re.M | re.I)
    if not m:
        return None
    rest = text[m.end():]
    n = re.search(r"^##\s+", rest, flags=re.M)
    return rest[:n.start()] if n else rest


def duplicates_in(text):
    paras = []
    for p in re.split(r"\n\s*\n", text):
        p = re.sub(r"^##\s+.*$", "", p, flags=re.M)
        norm = re.sub(r"\s+", " ", p.lower()).strip()
        if len(norm.split()) >= 40:
            paras.append(norm)
    return len(paras) - len(set(paras))


def check_file(module, lang, note=None, sources_path=None, min_en=None, min_zh=None,
               quiet=False):
    note = note or paths(module, lang)[0]
    sources_path = sources_path or paths(module, lang)[1]
    min_en = module.get("min_en", 0) if min_en is None else min_en
    min_zh = module.get("min_zh", 0) if min_zh is None else min_zh
    errors, warnings = [], []

    if not os.path.exists(note):
        return [f"file missing: {note}"], [], {}
    text = open(note, encoding="utf-8", errors="ignore").read().strip()
    if not text:
        return [f"file empty: {note}"], [], {}

    wc, cc = words(text), cjk_count(text)
    headings = len(re.findall(r"^##\s+", text, flags=re.M))
    sm = section(text, "Source map")
    gd = section(text, "Go deeper")
    if not sm:
        errors.append("missing '## Source map'")
    if not gd:
        errors.append("missing '## Go deeper'")
    if headings < 6:
        errors.append(f"only {headings} level-2 headings (need 6)")

    body = text[:text.lower().find("## source map")] if sm else text
    cited = set(MARKER.findall(body))
    defined = set(MARKER.findall(sm or ""))
    undefined = sorted(cited - defined)
    if undefined:
        errors.append(f"citations not in source map: {undefined}")
    uncited_map = sorted(defined - cited)
    if uncited_map:
        warnings.append(f"source map entries never cited: {uncited_map}")

    sources = {}
    if os.path.exists(sources_path):
        sources = json.load(open(sources_path))
        unknown = sorted(cited - set(sources))
        if unknown:
            errors.append(f"citations not in corpus sources: {unknown}")
        coverage = len(cited & set(sources)) / max(1, len(sources))
        if len(sources) >= 8 and coverage < 0.5:
            warnings.append(f"low source coverage: {coverage:.0%} of {len(sources)} sources")

    if re.search(r"\b(TODO|TBD|lorem ipsum|\[insert|XXX)\b", text, flags=re.I):
        errors.append("placeholder text present")
    dups = duplicates_in(body)
    if dups:
        errors.append(f"{dups} duplicate paragraph(s)")

    if lang == "en":
        if wc < min_en:
            errors.append(f"EN word count {wc} < {min_en}")
        cjk = cjk_count(body)
        if cjk > 20:
            errors.append(f"EN file contains {cjk} CJK characters")
    else:
        if cc < min_zh:
            errors.append(f"ZH character count {cc} < {min_zh}")
        terms = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", body)}
        terms -= STOP
        if len(terms) < 30:
            errors.append(f"only {len(terms)} English clinical terms (need 30)")
        for para in re.split(r"\n\s*\n", body):
            if (len(para.split()) > 120 and cjk_count(para) == 0
                    and not para.lstrip().startswith(("|", "#", "-", ">"))):
                errors.append("English-only paragraph in Chinese file")
                break

    stats = {"words": wc, "cjk": cc, "headings": headings,
             "sources": len(sources), "cited": len(cited)}
    if not quiet:
        print(f"{'PASS' if not errors else 'FAIL'} {os.path.relpath(note, ROOT)} "
              f"({wc} words, {cc} CJK, {len(cited)} citations)")
        for e in errors:
            print("  error:", e)
        for w in warnings:
            print("  warn:", w)
    return errors, warnings, stats


def shingles(text, n=8):
    toks = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))}


def duplicate_pairs(threshold=0.15):
    files = []
    for m in MODULES:
        p = paths(m, "en")[0]
        if os.path.exists(p):
            files.append((m["id"], shingles(open(p, encoding="utf-8", errors="ignore").read())))
    bad = 0
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            a, b = files[i][1], files[j][1]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac > threshold:
                print(f"DUPLICATE {files[i][0]} vs {files[j][0]}: {jac:.0%}")
                bad += 1
    print(f"{len(files)} English files compared; {bad} pair(s) over {threshold:.0%}")
    return 0 if bad == 0 else 1


def self_test():
    import shutil
    tmp = tempfile.mkdtemp(prefix="notes-check-")
    fake = {"id": "fake", "course": "X", "path": "Y", "min_en": 20, "min_zh": 5}
    src = os.path.join(tmp, "sources.json")
    json.dump({"S1": {"title": "one", "type": "document"}}, open(src, "w"))

    short = os.path.join(tmp, "short.en.md")
    open(short, "w").write("# T\n\n## Overview\nA few words only. [S1]\n\n"
                           "## Source map\n[S1]\n\n## Go deeper\nx\n")
    e1, _, _ = check_file(fake, "en", note=short, sources_path=src, quiet=True)

    uncited = os.path.join(tmp, "uncited.en.md")
    open(uncited, "w").write("# T\n\n" + "\n\n".join(f"## H{i}\nword " * 1 for i in range(6))
                             + "\n\nThe claim is here. [S9]\n\n## Source map\n[S1]\n\n## Go deeper\nx\n")
    e2, _, _ = check_file(fake, "en", note=uncited, sources_path=src, quiet=True)

    dup = os.path.join(tmp, "dup.en.md")
    para = "one two three four five six seven eight nine ten " * 4
    open(dup, "w").write("# T\n\n" + "\n\n".join(f"## H{i}\n{para} [S1]" for i in range(6))
                         + "\n\n## Source map\n[S1]\n\n## Go deeper\nx\n")
    e3, _, _ = check_file(fake, "en", note=dup, sources_path=src, quiet=True)

    good = os.path.join(tmp, "good.en.md")
    open(good, "w").write("# T\n\n## Overview\n" + "word " * 30 + "[S1]\n\n"
                           + "\n\n".join(f"## H{i}\n" + "text " * 10 + "[S1]" for i in range(5))
                           + "\n\n## Source map\n| [S1] | one |\n\n## Go deeper\n- one\n")
    e4, _, _ = check_file(fake, "en", note=good, sources_path=src, quiet=True)

    cases = [("short fails", bool(e1)), ("uncited fails", bool(e2)),
             ("duplicate fails", bool(e3)), ("valid passes", not e4)]
    bad = 0
    for name, ok in cases:
        print(("PASS " if ok else "FAIL ") + name)
        bad += 0 if ok else 1
    shutil.rmtree(tmp)
    print(f"4 cases, {4 - bad} passed, {bad} failed")
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module")
    ap.add_argument("--lang", choices=["en", "zh"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--duplicates", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if args.duplicates:
        sys.exit(duplicate_pairs())
    if args.all:
        total = failures = 0
        for m in MODULES:
            for lang in ("en", "zh"):
                errs, _, _ = check_file(m, lang, quiet=False)
                total += 1
                failures += 1 if errs else 0
        print(f"\n{total - failures}/{total} files pass")
        sys.exit(0 if failures == 0 else 1)
    if not args.module or not args.lang:
        ap.error("--module and --lang are required (or use --all)")
    m = resolve(args.module)
    errs, _, _ = check_file(m, args.lang)
    sys.exit(0 if not errs else 1)


if __name__ == "__main__":
    main()
