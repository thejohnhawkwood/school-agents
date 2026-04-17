"""Interpret lesson slides as text + image evidence.

Supports `.pptx` and `.pdf` sources.
Outputs structured slide summaries with traceability and confidence flags.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from PIL import Image
import pytesseract


TESSERACT_CANDIDATES = [
    Path(r"C:\Users\pbird\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
]


@dataclass
class ImageEvidence:
    image_id: str
    ocr_text: str
    visual_type: str
    instructional_relevance: str
    confidence: str


@dataclass
class SlideSummary:
    slide_number: int
    source_ref: str
    title: str
    visible_text: list[str]
    images: list[ImageEvidence]
    teaching_summary: str
    question_worthy_points: list[str]
    confidence: str
    flags: list[str]


def configure_tesseract() -> None:
    for candidate in TESSERACT_CANDIDATES:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def parse_range(range_text: str) -> tuple[int, int]:
    match = re.search(r"(\d+)\s*-\s*(\d+)", range_text)
    if not match:
        raise ValueError("allowed range must contain a numeric span like 5-14")
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        raise ValueError("range start cannot be greater than range end")
    return start, end


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def short_text(text: str, word_limit: int = 32) -> str:
    words = clean_text(text).split()
    if not words:
        return ""
    out = " ".join(words[:word_limit])
    if len(words) > word_limit:
        out += " ..."
    return out


def ocr_image_bytes(data: bytes) -> str:
    try:
        with Image.open(io.BytesIO(data)) as img:
            return clean_text(pytesseract.image_to_string(img))
    except Exception:
        return ""


def classify_visual(text: str) -> tuple[str, str]:
    lower = text.lower()
    if any(k in lower for k in ["axis", "graph", "trend", "x-", "y-", "bar", "line chart", "scatter"]):
        return "graph_or_chart", "high"
    if any(k in lower for k in ["map", "legend", "region", "latitude", "longitude"]):
        return "map", "high"
    if any(k in lower for k in ["step", "process", "arrow", "cycle", "pathway"]):
        return "process_diagram", "high"
    if any(k in lower for k in ["label", "anatomy", "structure", "parts", "system"]):
        return "labeled_diagram", "high"
    if len(lower) < 25:
        return "unknown_or_decorative", "low"
    return "illustration", "medium"


def is_instructional_visual(visual_type: str, ocr_text: str, slide_text: str) -> bool:
    if visual_type == "unknown_or_decorative":
        return False
    if len(ocr_text) < 20 and len(slide_text) < 20:
        return False
    return True


def summarize_slide(title: str, visible_text: list[str], images: list[ImageEvidence]) -> tuple[str, list[str], str, list[str]]:
    flags: list[str] = []
    joined_text = " ".join(visible_text)
    instructional_images = [img for img in images if img.instructional_relevance == "high"]

    points: list[str] = []
    for line in visible_text[:4]:
        if line and len(line) > 6:
            points.append(line)
    for img in instructional_images[:2]:
        snippet = short_text(img.ocr_text, 16)
        if snippet:
            points.append(f"Visual evidence: {snippet}")

    if not points:
        points = ["Insufficient reliable evidence to generate detailed questions."]
        flags.append("low-confidence-slide")

    summary = f"{title or 'Untitled slide'}: {short_text(joined_text, 24)}"
    if instructional_images:
        summary += f" Visual focus includes {', '.join(sorted({img.visual_type for img in instructional_images}))}."
    elif images:
        summary += " Visuals detected, but instructional relevance is uncertain."

    confidence = "high"
    if not visible_text and not instructional_images:
        confidence = "low"
        flags.append("no-reliable-text-or-visual-evidence")
    elif any(img.confidence == "low" for img in images):
        confidence = "medium"

    return summary, points[:4], confidence, flags


def extract_pptx(source_path: Path, start: int, end: int) -> list[SlideSummary]:
    ns = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    summaries: list[SlideSummary] = []

    with zipfile.ZipFile(source_path) as zf:
        for slide_num in range(start, end + 1):
            slide_path = f"ppt/slides/slide{slide_num}.xml"
            rel_path = f"ppt/slides/_rels/slide{slide_num}.xml.rels"
            if slide_path not in zf.namelist():
                continue

            root = ET.fromstring(zf.read(slide_path))
            texts = [clean_text(t.text or "") for t in root.findall(".//a:t", ns) if clean_text(t.text or "")]
            title = texts[0] if texts else f"Slide {slide_num}"

            rel_map: dict[str, str] = {}
            if rel_path in zf.namelist():
                rel_root = ET.fromstring(zf.read(rel_path))
                for rel in rel_root.findall("pr:Relationship", ns):
                    rid = rel.attrib.get("Id")
                    target = rel.attrib.get("Target", "")
                    if rid and target.startswith("../media/"):
                        rel_map[rid] = f"ppt/media/{Path(target).name}"

            images: list[ImageEvidence] = []
            image_idx = 0
            for blip in root.findall(".//a:blip", ns):
                rid = blip.attrib.get(f"{{{ns['r']}}}embed")
                media_path = rel_map.get(rid or "")
                if not media_path or media_path not in zf.namelist():
                    continue
                image_idx += 1
                ocr_text = ocr_image_bytes(zf.read(media_path))
                visual_type, base_conf = classify_visual(ocr_text)
                relevance = "high" if is_instructional_visual(visual_type, ocr_text, " ".join(texts)) else "low"
                conf = base_conf if ocr_text else "low"
                images.append(
                    ImageEvidence(
                        image_id=f"slide{slide_num}_img{image_idx}",
                        ocr_text=short_text(ocr_text, 40),
                        visual_type=visual_type,
                        instructional_relevance=relevance,
                        confidence=conf,
                    )
                )

            summary, points, confidence, flags = summarize_slide(title, texts, images)
            summaries.append(
                SlideSummary(
                    slide_number=slide_num,
                    source_ref=f"slides {slide_num}",
                    title=title,
                    visible_text=texts[:12],
                    images=images,
                    teaching_summary=summary,
                    question_worthy_points=points,
                    confidence=confidence,
                    flags=flags,
                )
            )
    return summaries


def extract_pdf(source_path: Path, start: int, end: int) -> list[SlideSummary]:
    try:
        import pypdfium2 as pdfium
    except ImportError as err:
        raise RuntimeError("PDF mode requires pypdfium2. Install with: python -m pip install pypdfium2") from err

    summaries: list[SlideSummary] = []
    pdf = pdfium.PdfDocument(str(source_path))
    page_count = len(pdf)
    for page_num in range(start, min(end, page_count) + 1):
        page = pdf.get_page(page_num - 1)
        pil_img = page.render(scale=2).to_pil()
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        ocr_text = ocr_image_bytes(buf.getvalue())
        lines = [x for x in re.split(r"[.;]\s+|\n", ocr_text) if clean_text(x)]
        title = clean_text(lines[0]) if lines else f"Page {page_num}"

        visual_type, base_conf = classify_visual(ocr_text)
        relevance = "high" if is_instructional_visual(visual_type, ocr_text, ocr_text) else "low"
        image_evidence = ImageEvidence(
            image_id=f"page{page_num}_render",
            ocr_text=short_text(ocr_text, 40),
            visual_type=visual_type,
            instructional_relevance=relevance,
            confidence=base_conf if ocr_text else "low",
        )

        summary, points, confidence, flags = summarize_slide(title, lines[:12], [image_evidence])
        summaries.append(
            SlideSummary(
                slide_number=page_num,
                source_ref=f"pages {page_num}",
                title=title,
                visible_text=lines[:12],
                images=[image_evidence],
                teaching_summary=summary,
                question_worthy_points=points,
                confidence=confidence,
                flags=flags,
            )
        )
    return summaries


def write_report(report_path: Path, source_file: Path, allowed_range: str, summaries: list[SlideSummary]) -> None:
    low = [s for s in summaries if s.confidence == "low" or s.flags]
    lines = [
        "# Slide Interpretation Report",
        "",
        f"- Source: `{source_file.name}`",
        f"- Allowed range: `{allowed_range}`",
        f"- Slides/pages processed: {len(summaries)}",
        f"- Low-confidence slides/pages: {len(low)}",
        "",
        "## Low-confidence flags",
    ]
    for s in low:
        lines.append(f"- {s.source_ref}: confidence={s.confidence}; flags={', '.join(s.flags) if s.flags else 'none'}")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interpret lesson slides as text + images.")
    parser.add_argument("--source", required=True, help="Path to .pptx or .pdf lesson file")
    parser.add_argument("--allowed-range", required=True, help="Range like slides 26-34 or pages 3-12")
    parser.add_argument("--outdir", required=True, help="Output directory for summaries/report")
    args = parser.parse_args()

    configure_tesseract()

    source_path = Path(args.source)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    start, end = parse_range(args.allowed_range)
    suffix = source_path.suffix.lower()
    if suffix == ".pptx":
        summaries = extract_pptx(source_path, start, end)
        source_type = "pptx"
    elif suffix == ".pdf":
        summaries = extract_pdf(source_path, start, end)
        source_type = "pdf"
    else:
        raise ValueError("source must be .pptx or .pdf")

    payload = {
        "source_file": str(source_path),
        "source_type": source_type,
        "allowed_range": args.allowed_range,
        "slides": [asdict(s) for s in summaries],
        "issues": [
            {
                "source_ref": s.source_ref,
                "reason": "low-confidence visual/text interpretation",
                "flags": s.flags,
            }
            for s in summaries
            if s.confidence == "low" or s.flags
        ],
    }

    summary_path = outdir / "slide-summaries.json"
    report_path = outdir / "lesson-interpretation-report.md"
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(report_path, source_path, args.allowed_range, summaries)
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()
