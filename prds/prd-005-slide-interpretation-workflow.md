# PRD-005: Slide Interpretation Workflow (Text + Image)

## Purpose
Build a local, auditable workflow that interprets lesson slides as combined text and visuals, then generates contextual homework grounded in what is actually taught.

## V1 goals
- Treat each slide/page as `text + image evidence`.
- Produce structured per-slide summaries with traceability.
- Generate classroom-ready homework (5 standard + 1 diagram/image question), teacher key, and audit.
- Homework language should read like a teacher wrote it: specific, student-facing, and visual-aware
  (not internal generation phrasing or “teaching point” boilerplate).
- Avoid invented details from ambiguous visuals.
- Flag low-confidence slides for teacher review.

## Proposed file structure

```text
school-agents/
  data/
    incoming/
      <lesson>.pptx|pdf
    processed/
      <run-id>/
        slide-images/
          slide-001.png
          slide-002.png
          ...
        slide-summaries.json
        lesson-interpretation-report.md
  scripts/
    interpret_slides.py
    generate_homework_from_summaries.py   # next step
    qa_homework_traceability.py            # next step
  prompts/
    homework-builder.md
    qa-auditor.md
  templates/
    slide-summary-template.json
  outputs/
    homework/
      <run-id>-student.docx
      <run-id>-teacher-key.docx
      <run-id>-audit.json
      <run-id>-issues.json
```

## Version-1 workflow
1. **Ingest source** (`.pptx` or `.pdf`) and allowed range.
2. **Extract slide/page text**:
   - visible text (title + body where possible),
   - OCR from visuals.
3. **Export slide image evidence**:
   - PPTX: image objects in slide + rendered slide image if available.
   - PDF: page render to PNG.
4. **Interpret visuals in context**:
   - classify visuals as instructional (`diagram/map/graph/chart/process`) vs likely decorative.
   - combine text + OCR + visual type into a short teaching-summary.
5. **Emit structured slide summaries** with confidence + flags.
6. **Generate homework** from structured summaries only:
   - 5 standard questions,
   - 1 diagram/image-based question.
7. **Generate teacher key + audit** with slide mapping.
8. **QA pass**:
   - no out-of-range citations,
   - no unsupported visual claims,
   - low-confidence slides flagged.

## PowerPoint processing (V1)
- Parse slide XML for visible text runs and approximate title.
- Parse slide relationships to find embedded media.
- OCR media images.
- Keep per-slide evidence package:
  - `visible_text`,
  - `ocr_image_text`,
  - `image_count`,
  - `visual_relevance` and confidence.

## PDF processing (V1)
- Extract text layer where present.
- Render each page to image and OCR the rendered page.
- Combine:
  - text-layer content,
  - OCR content.
- Derive page summary with confidence:
  - high when text layer + OCR align,
  - medium when OCR only but coherent,
  - low when OCR noisy or sparse.

## Image interpretation rules (V1)
- **Use as question source** when visual is clearly instructional:
  - labeled diagrams,
  - graphs/charts with axes/series,
  - maps with labels/legend,
  - process illustrations with arrows/steps.
- **Do not use as source** when image appears decorative:
  - stock photos,
  - unlabeled background art,
  - unrelated icons without instructional labels.
- **Never invent labels** from fuzzy images; mark `low_confidence`.
- If visual is likely instructional but unreadable, add teacher-review flag.

## Structured per-slide output example

```json
{
  "slide_number": 12,
  "source_ref": "slides 12",
  "title": "The Water Cycle",
  "visible_text": [
    "evaporation",
    "condensation",
    "precipitation"
  ],
  "images": [
    {
      "image_id": "slide12_img1",
      "ocr_text": "sun clouds rain arrows collection basin",
      "visual_type": "process_diagram",
      "instructional_relevance": "high",
      "confidence": "medium"
    }
  ],
  "teaching_summary": "The slide teaches the 3 main water-cycle stages and uses a circular process diagram to show flow between stages and water collection.",
  "question_worthy_points": [
    "Define evaporation, condensation, and precipitation",
    "Explain the role of the sun in driving the cycle",
    "Identify where water collects after precipitation"
  ],
  "flags": []
}
```

## V1 guardrails
- Never generate claims not supported by `visible_text` or reliable OCR.
- Never generate image-based questions from decorative visuals.
- Never silently cross allowed range.
- Always output unresolved issues for low-confidence slides.

## Next implementation increments
- Add `generate_homework_from_summaries.py` that consumes `slide-summaries.json`.
- Add QA script to validate question-to-slide support.
- Add unit tests for slide interpretation heuristics.
