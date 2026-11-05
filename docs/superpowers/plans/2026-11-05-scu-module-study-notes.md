# SCU Module Study Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce 12 detailed, textbook-style module study guides for PHAR2001 and INDG6002, each in English and Chinese, grounded in the scraped documents and videos.

**Architecture:** First fill the media gap (65 YouTube videos hidden inside Ultra embedded-HTML wrappers). Then build one self-contained source corpus per module: documents in course order, Panopto AI summaries, YouTube transcripts, and optional reading excerpts. A shared style guide and per-module prompt drive one isolated writing pass per language per module. Automated checks verify length, citations, coverage, language, and cross-module duplication; a fresh reviewer spot-checks factual accuracy. Only the synthesized notes, index, scripts, and READMEs are committed and pushed.

**Tech Stack:** Python 3 (`requests`, `pdftotext` CLI), Markdown, `yt-dlp` (on the Mac mini), Node (existing `resolve.mjs`), OpenCode subagents.

**Spec:** `docs/superpowers/specs/2026-11-05-scu-module-study-notes.md`

## Global Constraints

- Scope is exactly 12 modules: PHAR2001 Modules 1–6 and INDG6002 Modules 1–6.
- Every module produces two independent files: `study_notes.en.md` (all English) and `study_notes.zh.md` (Chinese prose, English drug/clinical terms retained).
- English length 4,000–7,000 words; Chinese 6,000–11,000 characters. Per-module minimums live in `notes/modules.json`. Never pad; a thin module gets a labelled `Background` section and `Source gaps`.
- Every content section cites `[S#]`, `[V#]`, or `[R#]`; every marker is defined in the source map and every mapped source is cited at least once.
- Paraphrase. No more than 25 consecutive words copied from any source.
- Never invent facts, drug names, doses, statistics, or policy names. Mark uncertainty as `[check source]`.
- Raw course material (ePubs, HTML, PDFs, media, transcripts, corpora) stays local. `origin` is public and about 5.3 GB; the two files over 100 MB must never enter git.
- No credentials, cookies, launch URLs, or `access_token` values in any committed file.
- Push only after all 24 notes pass checks and the final review.

## Review Focus

- **Thin INDG modules (4 and 5)** can tempt padding or invented policy detail. The notes must contain a `Source gaps` note and the reviewer verifies 10 sampled claims against the corpus.
- **Video-only facts** come from auto-captions that mishear drug names. The reviewer cross-checks every drug/mechanism table row against a document or a Panopto summary, not only a transcript.
- **Cross-module repetition** (PHAR 1 vs 2, INDG themes) can look like depth but be copy-paste. The 8-word shingle check fails any pair above 15% overlap.
- **Chinese version drift** can turn into a loose paraphrase or lose English terminology. The checker requires Chinese prose density plus at least 30 preserved English clinical terms; the reviewer reads two sections against the English file.
- **Citation theatre** (markers that resolve but do not support the sentence) is caught by the reviewer sampling one claim per section.

---

### Task 1: Fill the embedded-video gap (65 YouTube transcripts)

**Files:**
- Create: `notes/fetch_embedded_media.py`
- Create: `notes/embedded_manifest.json` (generated, not committed)
- Create: `notes/new_youtube_ids.txt` (generated, not committed)
- Modify: `videos/yt_<id>.json`, `videos/yt_<id>.en.vtt`, `videos/yt_<id>.txt` (65 new sets, local only)

**Interfaces:**
- Produces: `notes/embedded_manifest.json` with `{embeds: {url: {ids, files, status}}, per_module: {module_path: [ids]}, all_ids: [ids], new_ids: [ids]}`.
- Produces: `notes/new_youtube_ids.txt`, one 11-character YouTube ID per line.
- Consumes: `/tmp/scu_cookies.json` for the 66 `bbcswebdav` wrapper fetches; `/tmp/embedded_manifest.json` already contains a verified scan and may be used as a fixture.

- [ ] **Step 1: Write the scanner and transcript collector**

`notes/fetch_embedded_media.py` must:

1. Walk `PHAR2001/*/html/*.html` and `INDG6002/*/html/*.html`.
2. Find anchors with `data-bbtype="embedded-unsafe-html"` and their `href`.
3. Fetch each unique URL with the SCU cookies; extract `youtube.com/embed/<id>` IDs.
4. Map each wrapper's parent `NN - Section` to a module and write `notes/embedded_manifest.json`.
5. Write `notes/new_youtube_ids.txt` for IDs not already present as `videos/yt_<id>.json`.
6. Support `--scan` (default), `--fetch-transcripts`, and `--check`.
7. For transcripts, use `yt-dlp` from `--ytdlp` (default `yt-dlp`) with:
   `--skip-download --write-info-json --write-auto-subs --write-subs --sub-langs en --sub-format vtt -o "videos/yt_%(id)s"`.
8. Never write cookie values or tokens into the manifest.

- [ ] **Step 2: Run the scan and verify counts**

Run: `python3 notes/fetch_embedded_media.py --scan`
Expected: `66 embeds, 65 unique YouTube IDs, 65 new` and these per-module counts:

```
PHAR2001/06 - Module 1...: 42
PHAR2001/10 - Module 5...: 1
PHAR2001/11 - Module 6...: 2
PHAR2001/12 - Tutorials: 8
INDG6002/11 - Welcome to Gnibi: 1
INDG6002/12 - Module 1...: 4
INDG6002/13 - Module 2...: 2
INDG6002/14 - Module 3...: 2
INDG6002/15 - Module 4...: 1
INDG6002/17 - Module 6...: 2
```

- [ ] **Step 3: Fetch the 65 transcripts**

Run on the Mac mini (it has `yt-dlp` in `/tmp/scuvenv`):

```bash
scp notes/new_youtube_ids.txt macmini:/tmp/new_youtube_ids.txt
ssh macmini '/tmp/scuvenv/bin/yt-dlp -a /tmp/new_youtube_ids.txt --skip-download \
  --write-info-json --write-auto-subs --write-subs --sub-langs en --sub-format vtt \
  -o "$HOME/scu_export/videos/yt_%(id)s"'
rsync -az macmini:'scu_export/videos/yt_*' videos/
```

- [ ] **Step 4: Verify transcripts**

Run: `python3 notes/fetch_embedded_media.py --check`
Expected: `65 IDs listed, 65 info json, 63+ transcripts (max 2 without captions), 0 empty`.
For every transcript: `wc -w` is at least 40, or the manifest marks `no_captions` and the later corpus uses the video description.

- [ ] **Step 5: Commit the scanner only**

```bash
git add notes/fetch_embedded_media.py
git commit -m "Add embedded YouTube discovery for Ultra wrappers"
```

Do not add `notes/embedded_manifest.json`, `notes/new_youtube_ids.txt`, or `videos/`.

---

### Task 2: Build one source corpus per module

**Files:**
- Create: `notes/build_corpora.py`
- Create: `notes/modules.json`
- Create: `notes/corpora/<course>/<module>.md` (local only)
- Create: `notes/corpora/<course>/<module>.sources.json` (local only)

**Interfaces:**
- Consumes: `extracted_content.txt`, `html/*.html`, `videos.md`, `videos/yt_<id>.{json,txt}`, `videos/<panopto-session>.json`.
- Produces: a Markdown corpus whose blocks are labelled `[S1]`, `[S2]`, … for documents, `[V1]`, `[V2]`, … for videos, `[R1]`, … for reading excerpts.
- Produces: `.sources.json` of the form `{"S1": {"title": "...", "type": "document", "path": "...", "words": 123}, "V1": {...}}`.
- `notes/modules.json` is the single registry of the 12 modules: `id`, `course`, `path`, `min_en`, `min_zh`. The corpus and source paths are derived from `course` + `path`; `focus` is optional prose for the writer prompt.

- [ ] **Step 1: Write the corpus builder**

Requirements:

1. Split `extracted_content.txt` on `===== FILE: ... =====` markers; keep course order; strip navigation lines.
2. Add every video in `videos.md`: Panopto entries use the AI summary, key points, chapters, and duration; YouTube entries use the full `videos/yt_<id>.txt` transcript, not the 2,000-character excerpt.
3. Add the 65 new transcripts to the module named in `notes/embedded_manifest.json`; if a video is in `Tutorials`, leave it out of module corpora.
4. Optional `--readings`: run `pdftotext -layout` on PDFs referenced by the module; cap each module's reading excerpt at 8,000 words; label `[R#]` with PDF title and page range.
5. Write a header:
   ```
   # Corpus — <course> / <module>
   Source words: N
   Documents: n, Videos: n, Readings: n
   ```
6. Never include cookie values, `access_token`, or Blackboard launch URLs; replace any `access_token=...` with `access_token=REDACTED`.

- [ ] **Step 2: Create `notes/modules.json`**

Use these exact module entries and minimums (English words / Chinese characters):

```json
[
  {"id":"phar-m1","course":"PHAR2001","path":"06 - Module 1- Understanding Medications using the Gastrointestinal System","min_en":6000,"min_zh":9000},
  {"id":"phar-m2","course":"PHAR2001","path":"07 - Module 2- The Respiratory and Autonomic Nervous Systems","min_en":5000,"min_zh":8000},
  {"id":"phar-m3","course":"PHAR2001","path":"08 - Module 3- The Endocrine System","min_en":4000,"min_zh":6500},
  {"id":"phar-m4","course":"PHAR2001","path":"09 - Module 4- The Cardiovascular and Renal System","min_en":5000,"min_zh":8000},
  {"id":"phar-m5","course":"PHAR2001","path":"10 - Module 5- Analgesics and Psychotropic Drugs","min_en":4500,"min_zh":7000},
  {"id":"phar-m6","course":"PHAR2001","path":"11 - Module 6- Medications with Selective Toxicity","min_en":4000,"min_zh":6500},
  {"id":"indg-m1","course":"INDG6002","path":"12 - Module 1- Contrasting Indigenous and western health perspectives","min_en":3500,"min_zh":5500},
  {"id":"indg-m2","course":"INDG6002","path":"13 - Module 2- Colonisation and health","min_en":3500,"min_zh":5500},
  {"id":"indg-m3","course":"INDG6002","path":"14 - Module 3- Social and cultural determinants of health","min_en":3500,"min_zh":5500},
  {"id":"indg-m4","course":"INDG6002","path":"15 - Module 4- Cultural safety","min_en":3000,"min_zh":5000},
  {"id":"indg-m5","course":"INDG6002","path":"16 - Module 5- Decolonising your practice","min_en":3000,"min_zh":5000},
  {"id":"indg-m6","course":"INDG6002","path":"17 - Module 6- Working with Indigenous communities","min_en":3000,"min_zh":5000}
]
```

- [ ] **Step 3: Build and inspect the corpora**

Run: `python3 notes/build_corpora.py --all`
Expected: 12 corpora, each with at least 3,000 source words; print a table of documents/videos/readings/words per module.

- [ ] **Step 4: Verify coverage**

Run: `python3 notes/build_corpora.py --verify`
Expected: `12/12 corpora`, `0 missing documents`, `0 missing videos`, `0 token leaks`.
For PHAR Module 1, the corpus must include 42 embedded YouTube transcripts plus the two Panopto summaries.

- [ ] **Step 5: Commit the builder and registry**

```bash
git add notes/build_corpora.py notes/modules.json
git commit -m "Add per-module corpus builder"
```

Do not add `notes/corpora/`.

---

### Task 3: Write the style guide, generation prompt, and checker

**Files:**
- Create: `notes/STYLE_GUIDE.md`
- Create: `notes/GENERATION_PROMPT.md`
- Create: `notes/check_notes.py`
- Create: `notes/tests/fixtures/short.en.md`, `notes/tests/fixtures/uncited.en.md`, `notes/tests/fixtures/duplicate-a.md`, `notes/tests/fixtures/duplicate-b.md`

**Interfaces:**
- `check_notes.py --module <module_path> --lang en|zh --sources <sources.json>` exits non-zero with a readable reason.
- `check_notes.py --all` checks all 24 files from `notes/modules.json`.
- `check_notes.py --duplicates` compares English modules.
- `check_notes.py --self-test` runs the fixtures.

- [ ] **Step 1: Write `notes/STYLE_GUIDE.md`**

It must fix these decisions:

- Section order: title, overview, learning outcomes, numbered content, key takeaways, common confusions, source map, go deeper.
- Textbook prose, not bullets-only. Tables for comparisons (drug class/mechanism/ADRs/contraindications; policy/date/effect).
- Each section starts with a plain-language explanation, then the mechanism/detail, then an applied example.
- Inline citation at the end of every paragraph that makes a factual claim.
- Chinese version: Chinese sentences, English terms in parentheses on first use; do not translate drug names, receptor names, legislation, or assessment terminology.
- Forbidden: "In summary", "It is important to note", empty transition sentences, "etc." lists, unsourced general knowledge.
- Source-gap wording: `Source gaps: the module does not cover ...; the summary below is background only.`
- `Go deeper` entries use the document title and local path, not a URL that will break on GitHub.

- [ ] **Step 2: Write `notes/GENERATION_PROMPT.md`**

It must instruct the writer to:

1. Read the whole corpus before writing.
2. Produce an outline with section titles and the source markers for each section.
3. Write the English file first.
4. Write the Chinese file from the corpus and the English outline; it may expand explanations but must not add new facts.
5. Cite every section; include a source map that lists all `[S#]`/`[V#]`/`[R#]` used.
6. Respect the per-module minimum and the no-padding rule.
7. Save to the exact paths in `notes/modules.json`.

- [ ] **Step 3: Write `notes/check_notes.py`**

Assertions:

- File exists and is non-empty.
- English: `len(words) >= min_en`; at least 6 `##` headings; contains `## Source map` and `## Go deeper`; every `[S#]`/`[V#]`/`[R#]` is defined; no `TODO|TBD|lorem ipsum`; fewer than 100 CJK characters.
- Chinese: `len(CJK) >= min_zh`; at least 6 `##` headings; contains the source map and go-deeper headings; every marker defined; at least 30 ASCII clinical terms (drug/receptor/policy names); no paragraph longer than 900 characters that contains no CJK.
- Both: no duplicate paragraph (normalised, 40+ words) inside the file.
- `--duplicates`: 8-word shingles, Jaccard between any two English module files must be < 0.15.

- [ ] **Step 4: Run the self-test**

Run: `python3 notes/check_notes.py --self-test`
Expected: `4 fixtures, 4 expected results, 0 failures`.

- [ ] **Step 5: Commit**

```bash
git add notes/STYLE_GUIDE.md notes/GENERATION_PROMPT.md notes/check_notes.py notes/tests
git commit -m "Add study-note style guide and checker"
```

---

### Task 4: Pilot PHAR Module 1 (both languages)

**Files:**
- Create: `PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.en.md`
- Create: `PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.zh.md`
- Create: `notes/reviews/phar-m1.md` (local only)

**Interfaces:**
- Consumes: `notes/corpora/PHAR2001/06 - Module 1....md`, its `.sources.json`, `notes/STYLE_GUIDE.md`, `notes/GENERATION_PROMPT.md`.
- Produces: the two note files; the review file lists sampled claims and pass/fail.

- [ ] **Step 1: Run the checker before writing (expected failure)**

Run: `python3 notes/check_notes.py --module "PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System" --lang en`
Expected: FAIL `file missing`.

- [ ] **Step 2: Generate the English file**

Dispatch one writer subagent with the prompt from `notes/GENERATION_PROMPT.md` plus the corpus path. It must write the file, not paste the corpus. Then run the checker.
Expected: PASS with at least 6,000 words.

- [ ] **Step 3: Generate the Chinese file**

Dispatch a second writer (or the same writer with a fresh context) using the English file as an outline plus the corpus. Then run the checker.
Expected: PASS with at least 9,000 CJK characters and 30+ English terms.

- [ ] **Step 4: Fresh review**

Dispatch a reviewer subagent with only the two notes and the corpus. It must:

- Sample 10 claims across different sections; mark each `supported` / `unsupported` / `partly`.
- Check every drug table row against a document or a Panopto summary.
- Check the Chinese version's first two sections for meaning drift and untranslated terms.
- Write `notes/reviews/phar-m1.md` with the results.

Expected: 10/10 supported; no factual fixes required.

- [ ] **Step 5: Fix and re-run**

Fix any unsupported claim by citing the correct `[S#]`/`[V#]` or removing it. Re-run both checkers.
Expected: both PASS; review has no `unsupported`.

- [ ] **Step 6: User gate**

Show the two files to the user and ask for a depth/style verdict. Do not start Task 5 until the user confirms the pilot is the right level. If the user asks for more detail, update `notes/STYLE_GUIDE.md` and regenerate the pilot before continuing.

- [ ] **Step 7: Commit**

```bash
git add "PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.en.md" \
        "PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.zh.md"
git commit -m "Add PHAR2001 Module 1 study notes (EN/ZH)"
```

---

### Task 5: PHAR Module 2 — Respiratory and Autonomic Nervous Systems

**Files:**
- Create: `PHAR2001/07 - Module 2- The Respiratory and Autonomic Nervous Systems/study_notes.en.md`
- Create: `PHAR2001/07 - Module 2- The Respiratory and Autonomic Nervous Systems/study_notes.zh.md`
- Create: `notes/reviews/phar-m2.md`

**Interfaces:**
- Consumes: `notes/corpora/PHAR2001/07 - Module 2....md`, its `.sources.json`.
- Produces: the two note files.

- [ ] **Step 1: Checker red** — run `check_notes.py --module "PHAR2001/07 - Module 2- The Respiratory and Autonomic Nervous Systems" --lang en`; expect missing file.
- [ ] **Step 2: English** — writer subagent; minimum 5,000 words; include the autonomic receptor table and the respiratory drug classes; cite Panopto summaries for video-only content.
- [ ] **Step 3: Checker green** — run the English check.
- [ ] **Step 4: Chinese** — writer subagent; minimum 8,000 CJK; keep receptor/drug names in English.
- [ ] **Step 5: Checker green** — run the Chinese check.
- [ ] **Step 6: Review** — 10-claim spot-check; write `notes/reviews/phar-m2.md`; fix.
- [ ] **Step 7: Commit** — `git add` the two files; `git commit -m "Add PHAR2001 Module 2 study notes (EN/ZH)"`.

---

### Task 6: PHAR Module 3 — The Endocrine System

**Files:**
- Create: `PHAR2001/08 - Module 3- The Endocrine System/study_notes.en.md`
- Create: `PHAR2001/08 - Module 3- The Endocrine System/study_notes.zh.md`
- Create: `notes/reviews/phar-m3.md`

- [ ] **Step 1: Checker red** — expect missing file.
- [ ] **Step 2: English** — minimum 4,000 words; cover insulin/oral agents, thyroid, corticosteroids, and the feedback loops from the module; cite `[S#]` and `[V#]`.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 6,500 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/phar-m3.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add PHAR2001 Module 3 study notes (EN/ZH)"`.

---

### Task 7: PHAR Module 4 — Cardiovascular and Renal System

**Files:**
- Create: `PHAR2001/09 - Module 4- The Cardiovascular and Renal System/study_notes.en.md`
- Create: `PHAR2001/09 - Module 4- The Cardiovascular and Renal System/study_notes.zh.md`
- Create: `notes/reviews/phar-m4.md`

- [ ] **Step 1: Checker red** — expect missing file.
- [ ] **Step 2: English** — minimum 5,000 words; include the RAAS, diuretics, antihypertensives, anticoagulants, and lipid-lowering agents; use tables for site/mechanism/ADRs.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 8,000 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/phar-m4.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add PHAR2001 Module 4 study notes (EN/ZH)"`.

---

### Task 8: PHAR Module 5 — Analgesics and Psychotropic Drugs

**Files:**
- Create: `PHAR2001/10 - Module 5- Analgesics and Psychotropic Drugs/study_notes.en.md`
- Create: `PHAR2001/10 - Module 5- Analgesics and Psychotropic Drugs/study_notes.zh.md`
- Create: `notes/reviews/phar-m5.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 4,500 words; distinguish nociceptive/neuropathic pain, NSAIDs/paracetamol/opioids, antidepressant classes, antipsychotics, and the relevant adverse effects.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 7,000 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/phar-m5.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add PHAR2001 Module 5 study notes (EN/ZH)"`.

---

### Task 9: PHAR Module 6 — Medications with Selective Toxicity

**Files:**
- Create: `PHAR2001/11 - Module 6- Medications with Selective Toxicity/study_notes.en.md`
- Create: `PHAR2001/11 - Module 6- Medications with Selective Toxicity/study_notes.zh.md`
- Create: `notes/reviews/phar-m6.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 4,000 words; cover antibacterial classes, antifungals, antivirals, and selective toxicity; include the PPTX content if extracted, citing it as a document source.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 6,500 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/phar-m6.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add PHAR2001 Module 6 study notes (EN/ZH)"`.

---

### Task 10: INDG Module 1 — Contrasting Indigenous and western health perspectives

**Files:**
- Create: `INDG6002/12 - Module 1- Contrasting Indigenous and western health perspectives/study_notes.en.md`
- Create: `INDG6002/12 - Module 1- Contrasting Indigenous and western health perspectives/study_notes.zh.md`
- Create: `notes/reviews/indg-m1.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,500 words; use the 4 embedded YouTube transcripts for the SEWB and yarning content; keep Indigenous terminology exact; add a `Source gaps` note if the module relies on a reading not in the corpus.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,500 CJK; explain cultural concepts in Chinese but keep terms such as SEWB, Country, and cultural safety in English.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m1.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 1 study notes (EN/ZH)"`.

---

### Task 11: INDG Module 2 — Colonisation and health

**Files:**
- Create: `INDG6002/13 - Module 2- Colonisation and health/study_notes.en.md`
- Create: `INDG6002/13 - Module 2- Colonisation and health/study_notes.zh.md`
- Create: `notes/reviews/indg-m2.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,500 words; use the 2 embedded videos; include the policy timeline only where the module states it.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,500 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m2.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 2 study notes (EN/ZH)"`.

---

### Task 12: INDG Module 3 — Social and cultural determinants of health

**Files:**
- Create: `INDG6002/14 - Module 3- Social and cultural determinants of health/study_notes.en.md`
- Create: `INDG6002/14 - Module 3- Social and cultural determinants of health/study_notes.zh.md`
- Create: `notes/reviews/indg-m3.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,500 words; use the 2 embedded videos; structure the determinants as a table with evidence and policy links only when sourced.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,500 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m3.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 3 study notes (EN/ZH)"`.

---

### Task 13: INDG Module 4 — Cultural safety

**Files:**
- Create: `INDG6002/15 - Module 4- Cultural safety/study_notes.en.md`
- Create: `INDG6002/15 - Module 4- Cultural safety/study_notes.zh.md`
- Create: `notes/reviews/indg-m4.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,000 words; define cultural safety, cultural competence, and cultural awareness; include the one embedded video; do not pad.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,000 CJK; keep the three terms in English with Chinese explanations.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m4.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 4 study notes (EN/ZH)"`.

---

### Task 14: INDG Module 5 — Decolonising your practice

**Files:**
- Create: `INDG6002/16 - Module 5- Decolonising your practice/study_notes.en.md`
- Create: `INDG6002/16 - Module 5- Decolonising your practice/study_notes.zh.md`
- Create: `notes/reviews/indg-m5.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,000 words; this module has no video, so the notes must include a visible `Source gaps` note and a clearly labelled `Background` section. Do not invent policy detail.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,000 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m5.md`; fix any unsupported background claim.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 5 study notes (EN/ZH)"`.

---

### Task 15: INDG Module 6 — Working with Indigenous communities

**Files:**
- Create: `INDG6002/17 - Module 6- Working with Indigenous communities/study_notes.en.md`
- Create: `INDG6002/17 - Module 6- Working with Indigenous communities/study_notes.zh.md`
- Create: `notes/reviews/indg-m6.md`

- [ ] **Step 1: Checker red**.
- [ ] **Step 2: English** — minimum 3,000 words; use the 2 embedded videos; include community engagement, partnership, and ethical practice only as sourced.
- [ ] **Step 3: Checker green**.
- [ ] **Step 4: Chinese** — minimum 5,000 CJK.
- [ ] **Step 5: Checker green**.
- [ ] **Step 6: Review** — 10 claims; write `notes/reviews/indg-m6.md`; fix.
- [ ] **Step 7: Commit** — `git commit -m "Add INDG6002 Module 6 study notes (EN/ZH)"`.

---

### Task 16: Index, full QA, and push

**Files:**
- Create: `notes/build_index.py`
- Create: `NOTES_INDEX.md`
- Modify: `PHAR2001/README.md`, `INDG6002/README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `notes/modules.json` and the 24 note files.
- Produces: `NOTES_INDEX.md` with course, module, both file links, word/character counts, and source counts.

- [ ] **Step 1: Build the index**

`notes/build_index.py` writes one table per course: module, English link, Chinese link, EN words, ZH characters, sources. It must fail if any of the 24 files is missing.

Run: `python3 notes/build_index.py`
Expected: `12 modules, 24 files, 0 missing`.

- [ ] **Step 2: Run all checks**

Run: `python3 notes/check_notes.py --all --duplicates`
Expected: `24/24 pass`, `0 duplicate pairs over 15%`, `0 citation errors`, `0 language errors`.

- [ ] **Step 3: Final review**

Dispatch one reviewer for the whole set. It reads the index, opens 3 modules (PHAR 1, PHAR 4, INDG 5), and checks:

- Depth is consistent with the pilot.
- No module is a paraphrase of another.
- Chinese versions read naturally and keep English terms.
- Every `Go deeper` path exists locally.

Expected: no blocking issues; fix any `unsupported` claim and re-run Step 2.

- [ ] **Step 4: Update READMEs and `.gitignore`**

Add a `## Study notes` section to both course READMEs linking the 6 module files. Add to `.gitignore`:

```gitignore
# Raw SCU course material (copyright; local only)
PHAR2001/*/material/
PHAR2001/*/html/
PHAR2001/*/files/
INDG6002/*/material/
INDG6002/*/html/
INDG6002/*/files/
videos/
notes/corpora/
notes/reviews/
notes/embedded_manifest.json
notes/new_youtube_ids.txt
video_jobs.json
resolved.json
```

- [ ] **Step 5: Verify what will be committed**

Run: `git status --short`
Expected: only `study_notes.*.md`, `NOTES_INDEX.md`, `notes/*.py`, `notes/*.md`, `notes/tests/`, the two READMEs, and `.gitignore`. No `material/`, `html/`, `files/`, `videos/`, PDFs, MP4s, or `notes/corpora/`.

Run: `git status --short | grep -E 'material/|html/|files/|\.pdf$|\.mp4$|videos/'`
Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add NOTES_INDEX.md PHAR2001/README.md INDG6002/README.md .gitignore \
  notes/*.py notes/*.md notes/tests \
  "PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.en.md" \
  "PHAR2001/06 - Module 1- Understanding Medications using the Gastrointestinal System/study_notes.zh.md" \
  "PHAR2001/07 - Module 2- The Respiratory and Autonomic Nervous Systems/study_notes.en.md" \
  "PHAR2001/07 - Module 2- The Respiratory and Autonomic Nervous Systems/study_notes.zh.md" \
  "PHAR2001/08 - Module 3- The Endocrine System/study_notes.en.md" \
  "PHAR2001/08 - Module 3- The Endocrine System/study_notes.zh.md" \
  "PHAR2001/09 - Module 4- The Cardiovascular and Renal System/study_notes.en.md" \
  "PHAR2001/09 - Module 4- The Cardiovascular and Renal System/study_notes.zh.md" \
  "PHAR2001/10 - Module 5- Analgesics and Psychotropic Drugs/study_notes.en.md" \
  "PHAR2001/10 - Module 5- Analgesics and Psychotropic Drugs/study_notes.zh.md" \
  "PHAR2001/11 - Module 6- Medications with Selective Toxicity/study_notes.en.md" \
  "PHAR2001/11 - Module 6- Medications with Selective Toxicity/study_notes.zh.md" \
  "INDG6002/12 - Module 1- Contrasting Indigenous and western health perspectives/study_notes.en.md" \
  "INDG6002/12 - Module 1- Contrasting Indigenous and western health perspectives/study_notes.zh.md" \
  "INDG6002/13 - Module 2- Colonisation and health/study_notes.en.md" \
  "INDG6002/13 - Module 2- Colonisation and health/study_notes.zh.md" \
  "INDG6002/14 - Module 3- Social and cultural determinants of health/study_notes.en.md" \
  "INDG6002/14 - Module 3- Social and cultural determinants of health/study_notes.zh.md" \
  "INDG6002/15 - Module 4- Cultural safety/study_notes.en.md" \
  "INDG6002/15 - Module 4- Cultural safety/study_notes.zh.md" \
  "INDG6002/16 - Module 5- Decolonising your practice/study_notes.en.md" \
  "INDG6002/16 - Module 5- Decolonising your practice/study_notes.zh.md" \
  "INDG6002/17 - Module 6- Working with Indigenous communities/study_notes.en.md" \
  "INDG6002/17 - Module 6- Working with Indigenous communities/study_notes.zh.md"

git commit -m "Add detailed EN/ZH study notes for 12 PHAR2001 and INDG6002 modules"
```

- [ ] **Step 7: Push**

```bash
git push origin main
```

Expected: push succeeds. If GitHub rejects the push because the repository is over its size limit, stop and report the exact error; do not force-push and do not delete history.
