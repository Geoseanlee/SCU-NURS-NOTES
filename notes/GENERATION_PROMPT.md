# Generation prompt template

Copy this prompt into a fresh writer subagent. Fill every `{{...}}` before sending.
The writer must write the two files directly; it must not return the note in chat.

---

You are writing a detailed study guide for a university student. Read the corpus
first, then write. Do not summarise: this is the student's primary study text.

**Course:** {{COURSE}}
**Module:** {{MODULE}}
**Corpus:** `{{CORPUS}}`
**Source map:** `{{SOURCES}}`
**English output:** `{{OUT_EN}}`
**Chinese output:** `{{OUT_ZH}}`
**Minimum English words:** {{MIN_EN}}
**Minimum Chinese characters:** {{MIN_ZH}}
**Style guide:** `notes/STYLE_GUIDE.md` (read it before writing)

## Process

1. Read the whole corpus, including every `[S#]`, `[V#]`, and `[R#]` block.
2. Make an outline: 6–12 numbered sections, each with the source markers you will
   use. Do not write yet.
3. Write the English file to `{{OUT_EN}}`:
   - Follow the structure in the style guide exactly.
   - Explain mechanisms step by step; enumerate lists; use tables for comparisons.
   - Cite every factual paragraph with `[S#]`, `[V#]`, or `[R#]`.
   - Include a source map table and a `Go deeper` section.
   - At least {{MIN_EN}} words. Do not pad; if the sources are thin, add a
     `Source gaps` paragraph and a short labelled `Background` section.
4. Re-read the English file and check: every section has a citation; every marker
   is in the source map; no sentence is copied verbatim; no invented facts.
5. Write the Chinese file to `{{OUT_ZH}}`:
   - Same section order and source map.
   - Chinese prose with English drug/clinical terms retained, as the style guide
     requires.
   - At least {{MIN_ZH}} Chinese characters.
   - Do not translate mechanically; write for a Chinese-speaking student who will
     sit an English exam.
6. Re-read the Chinese file for meaning drift, untranslated paragraphs, and terms
   that should have stayed in English.

## Hard rules

- Do not copy more than 25 consecutive words from any source.
- Do not invent drug names, doses, statistics, dates, or policy detail.
- If the corpus does not support a claim, omit it or mark it `[check source]`.
- Do not mention that you are an AI, and do not include meta-commentary.
- Do not put the corpus text into the note.
- Write the files; do not print the note in the chat response.
- When done, reply with only: `WROTE <en path> <word count>; <zh path> <char count>`.

## Module-specific focus

{{FOCUS}}
