# SCU Module Study Notes — Spec

## Goal

Turn the scraped PHAR2001 and INDG6002 material into **12 detailed, textbook-style
module study guides**, each in two independent files:

- `study_notes.en.md` — all English
- `study_notes.zh.md` — Chinese prose, English drug/clinical terms kept in English

The guides are meant to be read as the primary study text. They must be detailed
enough to learn from, with source markers so the reader can return to the original
document or video when they need more.

## Audience and use

- A student revising for SCU assessments.
- English is the course language; the Chinese version is for faster understanding,
  not a literal translation.
- The reader should be able to read one module guide end-to-end, then jump back to
  a cited source for the exact wording, diagram, or video segment.

## Source hierarchy

1. **Module documents** — `extracted_content.txt` (ePub text) and `html/*.html`.
   These are authoritative for definitions, lists, and assessment instructions.
2. **Video content** — Panopto `DeliveryInfo` AI summaries/key points/chapters and
   YouTube transcripts. Video-only explanations must be integrated, not ignored.
3. **Attachments and readings** — PDF/PPTX text where the module links to it.
4. **Course-wide readings** (INDG6002 Unit Orientation reports) only when a module
   explicitly relies on them.

## Output contract

Each `study_notes.<lang>.md` contains:

1. Title and a 1–2 paragraph module overview.
2. **What you should be able to do** — 5–8 learning outcomes derived from the module.
3. Numbered content sections that follow the module's own sequence.
4. Explanations: definitions, mechanisms step by step, comparisons, tables, and
   clinical/applied links. No "etc." lists; enumerate what the source enumerates.
5. **Key takeaways** — a compact recap, not new material.
6. **Common confusions / exam traps** — only where the source supports it.
7. **Source map** — `[S#]` / `[V#]` table with title, type, and local path or video ID.
8. **Go deeper** — the 3–8 most useful original documents/videos for this module.

Length targets (do not pad to hit them):

- English: 4,000–7,000 words, scaled by source size.
- Chinese: 6,000–11,000 characters, scaled the same way.
- Thin modules (INDG Modules 4–5) may be shorter, but must include a clearly
  labelled `Background` section and a `Source gaps` note.

## Quality bar

- Every factual claim is traceable to `[S#]` or `[V#]`.
- Drug names, mechanisms, law/policy names, and numbers are exact.
- Explain *why* and *how*, not only *what*.
- Paraphrase. Never copy more than 25 consecutive words from a source.
- Do not invent content to fill space. Mark gaps explicitly.
- The Chinese version keeps English terms for drugs, receptors, legislation, and
  assessment terminology, with a Chinese explanation around them.

## Non-goals

- No practice exams or quiz banks (the user chose textbook-style notes only).
- No full translation of the course.
- No commit of raw course material to the public repo.

## Publishing constraint

`origin` is a **public** GitHub repository (`Geoseanlee/SCU-NURS-NOTES`) and is
already about 5.3 GB. Two local files exceed GitHub's 100 MB per-file limit:

- `INDG6002/02 - Unit orientation/files/national-aboriginal-and-torres-strait-islander-health-plan-2021-2031 Aus Govt Dept Health` (245 MB)
- `PHAR2001/13 - Workshops/files/GMT20261029-214503_Recording_1920x1080.mp4` (130 MB)

Therefore only the synthesized notes, index, scripts, style guide, and READMEs are
committed and pushed. Scraped ePubs, HTML, PDFs, media, transcripts, and corpora
stay local and are covered by `.gitignore`.
