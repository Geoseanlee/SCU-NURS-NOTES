# Study-note style guide

These notes are a **study text**, not a summary. A reader should be able to learn
the module from the note alone, then use the source map to return to the exact
document or video for more detail.

## Structure (both languages)

1. `# <Module title>` — the course code and module number.
2. `## Overview` — 1–2 paragraphs: what the module is about and why it matters.
3. `## What you should be able to do` — 5–8 learning outcomes, each starting with
   a verb (explain, compare, apply, calculate, justify).
4. Numbered content sections (`## 1. ...`, `## 2. ...`) following the module's own
   sequence. Each section:
   - starts with a plain-language explanation;
   - then the mechanism, process, or comparison in detail;
   - then an applied/clinical example or a "why this matters" paragraph;
   - ends with the source markers for that section.
5. `## Key takeaways` — 6–12 compact points; no new material.
6. `## Common confusions` — only where the sources show a real trap; explain the
   distinction, do not invent exam questions.
7. `## Source map` — a table with marker, title, type, and path/ID.
8. `## Go deeper` — 3–8 original documents or videos, with one line on what each
   adds.

## Depth

- Explain *why* and *how*. A definition alone is not enough; show the mechanism,
  the sequence, or the consequence.
- Enumerate lists. Do not write "etc." or "and others" when the source lists items.
- Use tables for comparisons: drug class / mechanism / main ADRs / cautions;
  policy / year / effect; receptor / location / response.
- Include the numbers, drug names, receptor names, and policy names from the source.
- Work through at least one example per major concept (for example, "a patient on
  an NSAID with …" only when the source supplies the scenario).
- Do not pad. If the source is thin, write a shorter note and add a visible
  `Source gaps` paragraph.

## Citations

- Every factual paragraph ends with one or more markers: `[S3]`, `[V12]`, `[R2]`.
- A marker may cover a whole paragraph only when every claim in it comes from that
  source. Otherwise split the paragraph or add multiple markers.
- The source map must define every marker used. Do not cite a marker that is not
  in the source map.
- The source map must not list a source that is never cited, unless the note's
  `Source gaps` paragraph explains why it was not used.
- Video claims: cite the video marker; if the claim is a mechanism also covered by
  a document, cite both.

## Paraphrase

- Never copy more than 25 consecutive words.
- Short definitions may be quoted (under 25 words) with quotation marks and a
  marker.
- Do not reproduce a whole slide, table, or paragraph.

## English version

- All English, including headings, tables, and the source map.
- Use Australian English spelling (organisation, behaviour, haematology) unless the
  source uses a different spelling in a drug or policy name.
- Prefer short sentences; define a term the first time it appears.

## Chinese version

- Chinese prose, not a sentence-by-sentence translation of the English file.
- Keep these in English, with a Chinese explanation around them:
  drug names, receptor names, enzyme names, legislation/policy names, assessment
  terminology, and abbreviations such as SEWB, ADR, RAAS, NSAID.
- On first use: `药物名（English name）`; afterwards use the English name alone when
  that is what the student will see in the exam.
- Explain cultural concepts in Chinese, but keep terms such as Country, cultural
  safety, cultural competence, and cultural awareness in English.
- The Chinese file must have the same section order and source map as the English
  file. It may expand an explanation, but it must not add new facts.

## Forbidden

- "In summary", "It is important to note", "This shows that", empty transitions.
- "etc.", "and so on", "various", "several" when the source gives a list.
- Unsourced general knowledge, invented doses, invented statistics, invented
  policy detail.
- Placeholders: `TODO`, `TBD`, `[insert]`, `lorem ipsum`.
- Copying the corpus or another module's note.
- A source map that is only a list of links with no citation in the body.

## Source gaps

When the module does not cover a topic that the learning outcomes imply, write:

> **Source gaps:** The module does not provide detail on … . The background below
> is included for orientation only and is not examinable from this module.

Then keep the background short and never present it as a sourced claim.

## Go deeper

Use the local path and the document title, for example:

- `material/03 - Activity- Overview of antacids.epub` — the activity that walks
  through the three antacid mechanisms.
- `videos/yt_<id>.txt` — the full transcript of the embedded lecture.

Do not use a GitHub URL; the raw course files are not committed.
