# Assessment 2 Context Notes

## Assessment Overview

- **Unit**: NURS5009 The Health Narrative Across the Lifespan
- **Task**: Assessment 2 — Critical Review
- **Due**: Monday 5 October 2026, 11:59 pm AEDT
- **Length**: 1,000 words (includes in-text citations, excludes reference list)
- **Weight**: 50%
- **Submission**: Word document (.docx) via Turnitin
- **File naming**: `SurnameFI_CriticalReview.doc` (e.g. `LiZ_CriticalReview.doc`)

## Task Structure

Three critical reflections (300–350 words each), one per module:
- Module 3 → Adolescent
- Module 4 → Middle Adulthood
- Module 5 → Older Adulthood

No introduction or conclusion required. AI statement on last page (not counted in word count).

## ULOs Addressed

- **ULO 1**: Critically analyse health, wellness, illness and disease meanings
- **ULO 3**: Demonstrate cultural responsivity and respect for identity and dignity
- **ULO 4**: Apply concepts of adaptation and change across the lifespan

## GenAI Policy (Level 2)

- ✅ Permitted: Grammarly for spelling/grammar only
- ❌ Not permitted: content or knowledge creation
- Required statement (Option 2 — no GenAI used):
  > "I acknowledge that I have not knowingly used GenAI to complete this assessment."

---

## Session Notes (2026-10-03)

### Section Heading Fix
The adolescent section heading was changed to match the pattern of the other two sections:

| Before | After |
|---|---|
| `Adolescent Mental Health and Suicide Risk` | `Adolescent: Mental Health and Suicide Risk` |

Pattern: `[Age Group]: [Topic]` — consistent across all three sections.

### HD Criteria Check

Word counts verified (all within 300–350):
- Adolescent: 346 words ✅
- Middle Adulthood: 348 words ✅
- Older Adulthood: 333 words ✅

**Issues identified:**

1. **Middle Adulthood section** — ends with third-person generic statement ("Nurses can use this evidence..."). HD requires *personal insights*. Needs a first-person statement, e.g.:
   > "In my practice, I would incorporate questions about social connection, neighbourhood resources and environmental barriers into holistic assessments, while recognising that the evidence supports population-level advocacy rather than individual intervention."

2. **GenAI acknowledgement statement** — not yet added to the document. Mandatory requirement — add as last page.

3. **Submission format** — must be `.docx`, not PDF. Use `pandoc` to convert:
   ```bash
   cd NURS5009/assessment/a2
   pandoc critical_reflection.tex -o critical_reflection.docx
   ```

### Build Setup
- `latexmk -pdf -pvc critical_reflection.tex` for auto-rebuild on save
- `.latexmkrc` configured: intermediate files → `build/`, PDF copied back to `a2/`
- `build/` added to `.gitignore`

---

## Articles

| Module | Authors | Year | Topic |
|---|---|---|---|
| 3 (Adolescent) | Calear et al. | 2026 | Multilevel risk/protective factors for self-harm and suicidal ideation in Australian adolescents |
| 4 (Middle Adulthood) | Learnihan et al. | 2026 | Neighbourhood social fragmentation and psychological distress, Brisbane HABITAT study |
| 5 (Older Adulthood) | Jayakody et al. | 2022 | Older adults' views on Facebook community for hearing-impaired psychosocial wellbeing |
