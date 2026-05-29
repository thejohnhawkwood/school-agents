"""
Emit IMAGE-INTEGRITY CONTRACT artifacts and verify DOCX embedded media.

Used by test build scripts. DOCX files are ZIP archives; embedded pictures live under
word/media/. Note: Word may re-encode some formats; ``sha256_in_docx`` compares extracted
bytes to the on-disk import file.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def extract_docx_media_hashes(docx_path: Path) -> list[dict[str, Any]]:
    """Return sha256 for each file under word/media/ in the DOCX package."""
    out: list[dict[str, Any]] = []
    with zipfile.ZipFile(docx_path, "r") as zf:
        for name in zf.namelist():
            if not name.startswith("word/media/"):
                continue
            if name.endswith("/"):
                continue
            data = zf.read(name)
            out.append(
                {
                    "zip_path": name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                }
            )
    return out


def docx_image_integrity_check(
    *,
    docx_path: Path,
    evidence_items: list[dict[str, Any]],
    run_dir: Path,
) -> dict[str, Any]:
    """
    For each evidence_required item, confirm the imported file's sha256 appears among
    embedded media blobs in the DOCX (byte-identical embedding).
    """
    embedded = extract_docx_media_hashes(docx_path)
    embedded_shas = {e["sha256"] for e in embedded}
    checks: list[dict[str, Any]] = []
    all_ok = True
    for it in evidence_items:
        iid = it.get("id")
        img = it.get("image") or {}
        rel = img.get("relative_path")
        exp_sha = img.get("sha256")
        if not rel or not exp_sha:
            checks.append({"item_id": iid, "ok": False, "reason": "missing relative_path or sha256"})
            all_ok = False
            continue
        src = run_dir / rel
        if not src.exists():
            checks.append({"item_id": iid, "ok": False, "reason": f"import missing: {rel}"})
            all_ok = False
            continue
        disk_sha = sha256_file(src)
        if disk_sha != exp_sha:
            checks.append({"item_id": iid, "ok": False, "reason": "disk sha256 drifted vs item JSON"})
            all_ok = False
            continue
        in_docx = exp_sha in embedded_shas
        checks.append(
            {
                "item_id": iid,
                "import_sha256": exp_sha,
                "sha256_present_in_docx_media": in_docx,
                "ok": bool(in_docx),
            }
        )
        all_ok = all_ok and in_docx
    return {
        "docx_path": str(docx_path.resolve()),
        "embedded_media_count": len(embedded),
        "embedded_media": embedded,
        "per_item_checks": checks,
        "gate_pass": all_ok,
    }


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_image_qa_report_md(path: Path, rows: list[dict[str, str]], *, footer: str = "") -> None:
    """Markdown table: Item ID | Intended concept | ... per contract."""
    headers = [
        "Item ID",
        "Intended concept",
        "Source figure / caption",
        "What the image actually shows",
        "Stem alignment verdict",
        "Counts toward 25% quota?",
        "Required teacher review?",
    ]
    lines = ["# Image QA report", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        cells = [r.get(h, "") for h in [
            "item_id",
            "intended_concept",
            "source_figure_caption",
            "actual_shows",
            "verdict",
            "counts_quota",
            "teacher_review",
        ]]
        esc = [c.replace("|", "\\|").replace("\n", " ") for c in cells]
        lines.append("| " + " | ".join(esc) + " |")
    lines.append("")
    if footer.strip():
        lines.append(footer.rstrip() + "\n")
    path.write_text("\n".join(lines), encoding="utf-8")
