# PRD-001: Lesson Homework Engine (V1)

## 1. Purpose
Generate a trustworthy homework set from tightly bounded lesson source material, with explicit traceability and uncertainty reporting.

## 2. Primary user and moment
A classroom teacher creating same-day or next-day homework from a specific lesson file and an explicit slide/page range.

## 3. Problem statement
Generic AI output often drifts outside lesson boundaries, produces vague prompts, or includes unsupported answer keys. Teachers need bounded, auditable homework they can use immediately.

## 4. V1 scope
In scope:
- One lesson source per run (`.pdf` or plain text export).
- Explicit allowed range required (pages or slides).
- Fixed output shape: 5 short-answer + 1 diagram question.
- Student homework DOCX (student-facing only, no audit/meta content in sheet).
- Separate teacher key DOCX.
- Separate project report artifacts (`audit.json`, `issues.json`, and human-readable report).
- Image-heavy slide ingestion review (coverage tracking + uncertainty flags).

Out of scope for V1:
- Multi-file synthesis.
- Automatic range detection.
- Multiple differentiated homework variants.

## 5. Inputs
Required:
- `source_file_path`: lesson source file.
- `source_type`: `pdf` or `text`.
- `allowed_range`: explicit range (example: `slides 6-14` or `pages 3-7`).

Optional:
- `question_constraints`: formatting or emphasis instructions.
- `reading_level_note`: class-specific readability note.
- `image_ingestion_mode`: `text-only`, `ocr-when-available`, or `manual-review-required`.

Validation rules:
- Reject run if `allowed_range` is missing.
- Reject run if source file is unreadable or missing.
- Flag segments with low extraction confidence; do not treat as reliable source.

## 6. Outputs
Human-readable output:
- Homework sheet with exactly 6 questions:
  - 5 short-answer
  - 1 diagram question
- Student-facing wording only.
- Numbering format `1.` to `6.`.
- Required pagination: questions 1-5 on page 1; page break; question 6 at top of page 2.
- Separate teacher key DOCX.
- Separate report Markdown file for summary, traceability, and uncertainty.

Machine-readable artifacts:
- `audit.json` with:
  - input metadata
  - allowed range used
  - question-to-source mapping
  - excluded/uncertain segments
  - QA decision (`pass` or `revise`)
- `issues.json` listing unresolved items requiring teacher review.

## 7. Minimal V1 workflow
1. Load input config and validate required fields.
2. Extract text segments from source in allowed range only.
3. Score segment readability/confidence (simple heuristic for V1).
4. Build a verified segment list (exclude low-confidence segments from generation).
5. Generate 5 short-answer + 1 diagram question from verified segments only.
6. Run image-ingestion review for in-range slides (text coverage, image-heavy detection, OCR/notes availability).
7. Generate teacher key tied to the same segments.
8. Run QA check for boundary drift, unsupported claims, and image-coverage gaps.
9. Write student DOCX, teacher-key DOCX, report Markdown, `audit.json`, and `issues.json`.

## 8. Data flow (V1)
1. `data/incoming/<lesson-file>` + run config
2. `scripts/extract_text.py` -> structured segments (`id`, `range_ref`, `text`, `confidence`)
3. generator step -> draft questions + key
4. QA step -> validation result + issue list
5. outputs:
   - `outputs/homework/<run-id>-student.docx`
   - `outputs/homework/<run-id>-teacher-key.docx`
   - `outputs/homework/<run-id>-report.md`
   - `outputs/homework/<run-id>-audit.json`
   - `outputs/homework/<run-id>-issues.json`

## 9. Constraints
- Never use content outside `allowed_range`.
- Never invent facts not present in verified segments.
- Exclude uncertain text instead of guessing.
- Questions must be concrete and answerable from cited segments.
- Teacher key must not include claims absent from mapped segments.

## 10. Acceptance criteria (V1 release gate)
- Output contains exactly 5 short-answer and 1 diagram question.
- Every question maps to at least one verified source segment.
- Student sheet contains no teacher-facing audit/meta language.
- Student sheet uses `1.`...`6.` numbering and required page break layout.
- QA reports `pass` for boundary and support checks.
- `audit.json` and `issues.json` are always emitted.
- Human-readable report is emitted for each run.
- Image-heavy in-range slides are explicitly covered or flagged.
- Unreadable/uncertain source is surfaced in issues, not silently ignored.

## 11. Failure modes and handling
- Boundary drift -> hard fail QA (`revise`) with offending question IDs.
- Generic filler question -> mark for revision and regenerate once.
- Unsupported key claim -> hard fail QA and require teacher review.
- Too little readable content in range -> stop generation; return issues only.
- Image-heavy slide without reliable extractable evidence -> flag review requirement and restrict claims to supported content.

## 12. Minimal implementation plan (no coding yet)
Phase 1 (smallest useful slice):
- Define run config format and output contract.
- Implement range-bounded text extraction with segment IDs.
- Implement markdown output generator with fixed question count.
- Emit `audit.json` and `issues.json` with placeholder QA checks.

Phase 2 (tighten reliability):
- Add explicit QA rules for unsupported claims and drift detection.
- Add confidence thresholds and excluded-segment reporting.
- Improve question specificity checks (heuristic lint pass).

Phase 3 (classroom readiness polish):
- Add clearer teacher-facing flags and next-action suggestions.
- Stabilize templates and naming conventions for repeat use.

## 13. Golden test cases (V1)
1. Clean source in-range:
   - Input: readable lesson PDF, pages 2-5.
   - Expect: full output + pass QA.
2. Partial unreadable range:
   - Input: mixed-quality file, pages 3-7 with faint text on one page.
   - Expect: output generated from readable segments; unreadable page in issues.
3. Too little content:
   - Input: allowed range with mostly images/unreadable text.
   - Expect: no homework generation; clear blocked reason in issues.
4. Boundary pressure:
   - Input: strong content just outside allowed range.
   - Expect: zero citations outside range; pass only if bounded.

## 14. Future improvements
- DOCX export and teacher print formatting.
- Diagram-aware extraction support.
- Multiple homework variants from same bounded source.
