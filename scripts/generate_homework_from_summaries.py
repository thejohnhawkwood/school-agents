"""Generate contextual homework from structured slide summaries.

Input: slide-summaries.json produced by interpret_slides.py
Output:
- student DOCX (questions only)
- teacher key DOCX
- report.md
- audit.json
- issues.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_BREAK
from docx.shared import Pt


def set_default_font(doc: Document, size: int = 11) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(size)


def add_title(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(16)


def add_question(doc: Document, number: int, topic: str, prompt: str) -> None:
    p = doc.add_paragraph()
    t = p.add_run(f"{number}. {topic}")
    t.bold = True
    doc.add_paragraph(prompt)
    doc.add_paragraph("\n\n")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def choose_text_point(slide: dict[str, Any]) -> str | None:
    points = [clean(x) for x in slide.get("question_worthy_points", []) if clean(x)]
    for p in points:
        if not p.lower().startswith("visual evidence:"):
            return p
    visible = [clean(x) for x in slide.get("visible_text", []) if clean(x)]
    return visible[1] if len(visible) > 1 else (visible[0] if visible else None)


def choose_visual_point(slide: dict[str, Any]) -> str | None:
    for img in slide.get("images", []):
        if img.get("instructional_relevance") == "high":
            ocr = clean(img.get("ocr_text", ""))
            if len(ocr) >= 20:
                return ocr
    return None


def build_standard_question(slide: dict[str, Any], idx: int) -> tuple[str, str, str]:
    title = clean(slide.get("title", f"Slide {slide.get('slide_number')}"))
    point = choose_text_point(slide) or "Explain the key idea taught on this slide."
    src = slide.get("source_ref", f"slides {slide.get('slide_number')}")
    topic = f"{title} - Core understanding"
    prompt = f"Using {src}, explain this teaching point in your own words: {point}"
    return topic, prompt, src


def build_diagram_question(slide: dict[str, Any]) -> tuple[str, str, str, bool]:
    src = slide.get("source_ref", f"slides {slide.get('slide_number')}")
    title = clean(slide.get("title", f"Slide {slide.get('slide_number')}"))
    visual = choose_visual_point(slide)
    if visual:
        topic = f"{title} - Diagram/Image interpretation"
        prompt = (
            f"Based on the instructional visual in {src}, draw and label the main parts or stages shown. "
            f"Then explain how the parts connect. Use this evidence as guidance: {visual}"
        )
        return topic, prompt, src, True
    topic = f"{title} - Diagram/Image interpretation"
    prompt = (
        f"Review the main visual on {src}. Draw a simplified version and label only parts that are clearly readable. "
        "If labels are unclear, identify what is uncertain instead of guessing."
    )
    return topic, prompt, src, False


def write_student_docx(path: Path, title: str, qs: list[tuple[str, str]], q6: tuple[str, str]) -> None:
    doc = Document()
    set_default_font(doc)
    add_title(doc, title)
    for i, (topic, prompt) in enumerate(qs, start=1):
        add_question(doc, i, topic, prompt)
    pb = doc.add_paragraph()
    pb.add_run().add_break(WD_BREAK.PAGE)
    add_question(doc, 6, q6[0], q6[1])
    doc.save(path)


def write_teacher_key_docx(path: Path, title: str, answers: list[str]) -> None:
    doc = Document()
    set_default_font(doc)
    add_title(doc, title)
    for i, ans in enumerate(answers, start=1):
        p = doc.add_paragraph()
        r = p.add_run(f"{i}. ")
        r.bold = True
        p.add_run(ans)
    doc.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate homework from slide summaries.")
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--lesson-title", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    slides: list[dict[str, Any]] = payload.get("slides", [])
    allowed_range = payload.get("allowed_range", "unknown")
    source_file = payload.get("source_file", "unknown")

    # Prefer higher-confidence slides for standard questions.
    rank = {"high": 0, "medium": 1, "low": 2}
    candidates = sorted(slides, key=lambda s: rank.get(s.get("confidence", "medium"), 1))
    standard_sources = candidates[:5] if len(candidates) >= 5 else slides[:5]

    standard_q: list[tuple[str, str]] = []
    key: list[str] = []
    mapping: dict[str, list[str]] = {}
    issues: list[dict[str, Any]] = []

    for i, slide in enumerate(standard_sources, start=1):
        topic, prompt, src = build_standard_question(slide, i)
        standard_q.append((topic, prompt))
        key.append(
            f"Expected answer should restate the key point from {src} accurately, using slide language where possible. "
            f"Primary support: {choose_text_point(slide) or slide.get('teaching_summary', '')}"
        )
        mapping[str(i)] = [src]
        if slide.get("confidence") == "low":
            issues.append(
                {"question": i, "source_ref": src, "reason": "low-confidence source slide", "action": "teacher review"}
            )

    # Prefer an instructional visual for Q6.
    visual_candidates = [
        s
        for s in slides
        if any(img.get("instructional_relevance") == "high" for img in s.get("images", []))
    ]
    q6_slide = visual_candidates[0] if visual_candidates else (slides[0] if slides else {})
    q6_topic, q6_prompt, q6_src, q6_supported = build_diagram_question(q6_slide)
    mapping["6"] = [q6_src]
    key.append(
        f"Student response should include only clearly visible/readable labels from {q6_src}, describe relationships among parts, "
        "and avoid invented labels where the image is fuzzy."
    )
    if not q6_supported:
        issues.append(
            {
                "question": 6,
                "source_ref": q6_src,
                "reason": "diagram evidence weak or unclear",
                "action": "teacher verify visual before assigning",
            }
        )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    student_doc = outdir / f"{args.run_id}-student.docx"
    teacher_doc = outdir / f"{args.run_id}-teacher-key.docx"
    report_md = outdir / f"{args.run_id}-report.md"
    audit_json = outdir / f"{args.run_id}-audit.json"
    issues_json = outdir / f"{args.run_id}-issues.json"

    write_student_docx(student_doc, args.lesson_title, standard_q, (q6_topic, q6_prompt))
    write_teacher_key_docx(teacher_doc, f"{args.lesson_title} - Teacher Key", key)

    report_lines = [
        f"# {args.lesson_title} - Generation Report",
        "",
        f"- Source file: `{Path(source_file).name}`",
        f"- Allowed range: `{allowed_range}`",
        f"- Questions generated: 6",
        f"- Low-confidence/teacher-review flags: {len(issues)}",
        "",
        "## Question-to-source mapping",
    ]
    for qid, refs in mapping.items():
        report_lines.append(f"- {qid} -> {', '.join(refs)}")
    report_lines.extend(["", "## Review flags"])
    if not issues:
        report_lines.append("- None")
    else:
        for item in issues:
            report_lines.append(
                f"- Q{item['question']} ({item['source_ref']}): {item['reason']} -> {item['action']}"
            )
    report_md.write_text("\n".join(report_lines), encoding="utf-8")

    audit_payload = {
        "source_file": source_file,
        "allowed_range": allowed_range,
        "question_to_source": mapping,
        "slide_count": len(slides),
        "qa_decision": "pass-with-flags" if issues else "pass",
    }
    audit_json.write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
    issues_json.write_text(json.dumps({"issues": issues}, indent=2), encoding="utf-8")

    print(f"Wrote: {student_doc}")
    print(f"Wrote: {teacher_doc}")
    print(f"Wrote: {report_md}")
    print(f"Wrote: {audit_json}")
    print(f"Wrote: {issues_json}")


if __name__ == "__main__":
    main()
