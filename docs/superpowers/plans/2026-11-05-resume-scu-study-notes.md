# SCU Study Notes Continuation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish quality review and the remaining bilingual study guides registered for PHAR2001 and INDG6002.

**Architecture:** Reuse the prepared per-module corpora, `notes/modules.json`, style guide, and checker. Repair existing PHAR review findings first, then finish the interrupted module and assessment-guide writing and review work, followed by INDG Modules 1–6. Generate the index and publish only after all in-scope guides pass automated and source-based review.

**Tech Stack:** Markdown, Python 3 (`notes/check_notes.py`, `notes/build_index.py`), local course corpora, OpenCode subagents.

**Spec:** `docs/superpowers/specs/2026-11-05-scu-module-study-notes.md`; execution baseline: `docs/superpowers/plans/2026-11-05-scu-module-study-notes.md`.

## Global Constraints

- The original spec covers 12 modules; this continuation adds Module 0 for both courses, for 14 in-scope study-guide entries. The current `notes/modules.json` also registers two assessment guides, which the user explicitly excluded.
- The interrupted OpenCode run and nine child sessions failed with a free-model quota error. Resume generation only after quota is available or an authorized alternative model is selected.
- Use the exact per-entry minimums in `notes/modules.json`; do not pad notes to meet a target.
- Every factual claim must be traceable to `[S#]` or `[V#]`; never copy more than 25 consecutive words from a source.
- Thin INDG Modules 4–5 need clearly labelled `Background` and `Source gaps` sections.
- Raw course material stays local. `origin` is public and about 5.3 GB; it must not receive ePubs, HTML, PDFs, media, transcripts, corpora, credentials, cookies, launch URLs, or access tokens. The 245 MB Indigenous health plan and 130 MB PHAR workshop recording must never be staged.
- Do not push until all in-scope English and Chinese files pass automated checks and source-based review.

## Review Focus

- Thin INDG Modules 4–5: verify the source gaps are explicit and background is not presented as course content; review 10 claims in each module.
- Video-only facts and auto-caption drug names: check drug/mechanism table rows against a course document or Panopto summary, not captions alone.
- Cross-module repetition: run `python3 notes/check_notes.py --duplicates`; expect no pair over 15%.
- Chinese meaning drift and retained English terminology: check each Chinese file against its English counterpart and the style guide.
- Citation theatre: sample at least one factual claim per section against its cited corpus source; remove or correct unsupported claims.

---

### Task 1: Repair PHAR Modules 2–4

**Files:**
- Modify the English and Chinese study notes for PHAR Modules 2–4 under `PHAR2001/07`–`PHAR2001/09`.
- Read: `notes/reviews/phar-m2.md`, `notes/reviews/phar-m3.md`, `notes/reviews/phar-m4.md`.

**Interfaces:**
- Consumes: the existing PHAR corpora and the three reviewer reports, which contain the specific unsupported/partly supported claims and fixes.
- Produces: corrected bilingual notes that pass both automated checks and fresh source-based review.

- [ ] Apply every blocking finding in the three review reports; preserve source gaps rather than adding unsupported facts.
- [ ] Run `python3 notes/check_notes.py --module phar-m2 --lang en` and `--lang zh`; repeat for `phar-m3` and `phar-m4`. Expected: all six checks pass.
- [ ] Have a fresh reviewer verify the reported fixes and sample 10 claims per module. Expected: no unsupported claims remain; any partly supported claims are either sourced precisely or removed.
- [ ] Commit only the six named `study_notes` files after review passes.

### Task 2: Review PHAR Modules 5–6

**Files:**
- Modify as needed: PHAR Module 5 and 6 English/Chinese study notes under `PHAR2001/10` and `PHAR2001/11`.
- Create: `notes/reviews/phar-m5.md`, `notes/reviews/phar-m6.md`.

**Interfaces:**
- Consumes: `notes/corpora/PHAR2001/phar-m5.md`, `phar-m6.md`, their `.sources.json` files, and the style guide.
- Produces: two reviewed note pairs and reviewer reports; automated checks already pass for all four note files.

- [ ] Have a fresh reviewer sample 10 claims per module, verify drug tables against documents/Panopto summaries, and write the two reports.
- [ ] Fix any unsupported claim or Chinese meaning drift; rerun `python3 notes/check_notes.py --module phar-m5 --lang en` and `--lang zh`, then repeat for `phar-m6`.
- [ ] Commit only the four note files after both reviews pass; keep the two review reports local.

### Task 3: Finish Module 0 notes

**Files:**
- Create: `PHAR2001/00 - Module 0- Unit Orientation/study_notes.en.md`, `study_notes.zh.md`.
- Create: `INDG6002/00 - Module 0- Unit Orientation/study_notes.zh.md`.
- Review: existing `INDG6002/00 - Module 0- Unit Orientation/study_notes.en.md`.
- Create: `notes/reviews/phar-m0.md`, `notes/reviews/indg-m0.md`.

**Interfaces:**
- Consumes: `notes/corpora/PHAR2001/phar-m0.md`, `notes/corpora/INDG6002/indg-m0.md`, source maps, and `notes/modules.json`.
- Produces: complete bilingual module 0 pairs. Current registered minimums: PHAR 3,000 English words / 5,000 Chinese characters; INDG 2,000 / 3,000.

- [ ] Write the missing PHAR pair and INDG Chinese file using `notes/GENERATION_PROMPT.md`.
- [ ] Run `check_notes.py` for both languages of `phar-m0` and `indg-m0`. Expected: four checks pass.
- [ ] Review 10 claims per module and check Chinese/English parity; fix and rerun checks before committing these note files. Keep the two review reports local.

### Task 4: Align the registry with the confirmed scope

**Files:**
- Modify: `notes/modules.json`.

**Interfaces:**
- Consumes: the user's confirmed scope: PHAR2001 and INDG6002 Module 0–6 only.
- Produces: a registry with 14 guide entries; the two local assessment corpora remain untouched and uncommitted.

- [ ] Remove only the `phar-assess` and `indg-assess` entries from `notes/modules.json`; do not delete the local corpora or any source material.
- [ ] Validate that the registry contains exactly the 14 requested module entries and that no assessment-guide output is included in the index or final commit.

### Task 5: INDG Module 1 — Contrasting Indigenous and western health perspectives

**Files:**
- Create: `INDG6002/12 - Module 1- Contrasting Indigenous and western health perspectives/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m1.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m1.md`, its source map, and `notes/GENERATION_PROMPT.md`.
- Produces: bilingual notes at the registered minimum of 3,500 English words / 5,500 Chinese characters.

- [ ] Write both files using the generation prompt; preserve the module's Indigenous terminology and use the four embedded YouTube transcripts for SEWB and yarning.
- [ ] Run `python3 notes/check_notes.py --module indg-m1 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims, verify citations and Chinese/English parity, and write `notes/reviews/indg-m1.md`; fix findings, rerun checks, and commit only the two note files.

### Task 6: INDG Module 2 — Colonisation and health

**Files:**
- Create: `INDG6002/13 - Module 2- Colonisation and health/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m2.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m2.md`, its source map, and the generation prompt.
- Produces: bilingual notes at the registered minimum of 3,500 English words / 5,500 Chinese characters.

- [ ] Write both files using the module focus in the baseline plan; use the two embedded videos and include policy dates only when stated in the corpus.
- [ ] Run `python3 notes/check_notes.py --module indg-m2 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims, verify citations and language parity, and write `notes/reviews/indg-m2.md`; fix findings, rerun checks, and commit only the two note files.

### Task 7: INDG Module 3 — Social and cultural determinants of health

**Files:**
- Create: `INDG6002/14 - Module 3- Social and cultural determinants of health/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m3.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m3.md`, its source map, and the generation prompt.
- Produces: bilingual notes at the registered minimum of 3,500 English words / 5,500 Chinese characters.

- [ ] Write both files using the module focus in the baseline plan; include determinants and policy links only where the corpus supports them.
- [ ] Run `python3 notes/check_notes.py --module indg-m3 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims, verify citations and language parity, and write `notes/reviews/indg-m3.md`; fix findings, rerun checks, and commit only the two note files.

### Task 8: INDG Module 4 — Cultural safety

**Files:**
- Create: `INDG6002/15 - Module 4- Cultural safety/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m4.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m4.md`, its source map, and the generation prompt.
- Produces: bilingual notes at the registered minimum of 3,000 English words / 5,000 Chinese characters.

- [ ] Write both files using the module focus in the baseline plan; distinguish cultural safety, cultural competence, and cultural awareness without importing unsupported background.
- [ ] Run `python3 notes/check_notes.py --module indg-m4 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims, verify citations, language parity, and required `Background` / `Source gaps` sections; write `notes/reviews/indg-m4.md`, fix findings, rerun checks, and commit only the two note files.

### Task 9: INDG Module 5 — Decolonising your practice

**Files:**
- Create: `INDG6002/16 - Module 5- Decolonising your practice/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m5.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m5.md`, its source map, and the generation prompt.
- Produces: bilingual notes at the registered minimum of 2,500 English words / 4,000 Chinese characters.

- [ ] Write both files using the module focus in the baseline plan; clearly label `Background` and `Source gaps` because this module has no video.
- [ ] Run `python3 notes/check_notes.py --module indg-m5 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims and check that background is not represented as course content; write `notes/reviews/indg-m5.md`, fix findings, rerun checks, and commit only the two note files.

### Task 10: INDG Module 6 — Working with Indigenous communities

**Files:**
- Create: `INDG6002/17 - Module 6- Working with Indigenous communities/study_notes.en.md`, `study_notes.zh.md`.
- Create locally: `notes/reviews/indg-m6.md`.

**Interfaces:**
- Consumes: `notes/corpora/INDG6002/indg-m6.md`, its source map, and the generation prompt.
- Produces: bilingual notes at the registered minimum of 3,000 English words / 5,000 Chinese characters.

- [ ] Write both files using the module focus in the baseline plan; cover engagement, partnership, and ethics only as supported by sources.
- [ ] Run `python3 notes/check_notes.py --module indg-m6 --lang en` and `--lang zh`; expected: both pass.
- [ ] Have a fresh reviewer sample 10 claims, verify citations and language parity, and write `notes/reviews/indg-m6.md`; fix findings, rerun checks, and commit only the two note files.

### Task 11: Reconcile the registry, index, and publication set

**Files:**
- Modify: `notes/build_index.py` so its description and generated index use the registered module count instead of hard-coding 12.
- Create/update: `NOTES_INDEX.md`, `PHAR2001/README.md`, `INDG6002/README.md` as needed.
- Review: `.gitignore` and the complete staged diff.

**Interfaces:**
- Consumes: the final `notes/modules.json` and every in-scope bilingual note pair.
- Produces: an index whose count matches the chosen scope, and a public-safe commit/push.

- [ ] Run `python3 notes/build_index.py`. Expected: it reports the exact registered module and file counts, with no missing files, and the generated index uses that same count.
- [ ] Run `python3 notes/check_notes.py --all`, `python3 notes/check_notes.py --duplicates`, and `python3 notes/build_corpora.py --verify`. Expected: every registered language file passes, no duplicate pair exceeds 15%, all registered corpora verify.
- [ ] Inspect `git status --short` and stage only approved notes, index, scripts, READMEs, and `.gitignore`; verify no raw course material, media, corpora, secrets, or files over 100 MB are staged.
- [ ] Commit the approved set, then push `main` to `origin` only after all quality and publication checks pass.
