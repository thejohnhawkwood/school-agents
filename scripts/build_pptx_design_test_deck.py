#!/usr/bin/env python3
"""
Stress-test deck for pptx_kit — exercises layouts, text fitting, image cover, QA.
Run from repo: python scripts/build_pptx_design_test_deck.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pptx_kit.layouts import (
    layout_big_idea,
    layout_comparison,
    layout_image_text_split,
    layout_process_timeline,
    layout_quote,
    layout_section_divider,
    layout_three_point,
    layout_title_slide,
    init_widescreen_deck,
)
from pptx_kit.qa import validate_deck
from pptx_kit.tokens import DEFAULT_TOKENS


def download_one_nasa_mars(dest: Path) -> Path | None:
    import urllib.request

    url = "https://images-assets.nasa.gov/image/PIA25443/PIA25443~medium.jpg"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / "test_mars.jpg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pptx-kit-test/1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if len(data) > 5000 and data[:2] == b"\xff\xd8":
            p.write_bytes(data)
            return p
    except OSError:
        pass
    return None


def main() -> None:
    tokens = DEFAULT_TOKENS
    out_dir = ROOT / "outputs" / "labs" / "bio20-unitA-mars-research"
    tmp_dir = out_dir / "_pptx_kit_test_assets"
    temps: list[Path] = []

    img = download_one_nasa_mars(tmp_dir)

    prs = init_widescreen_deck(tokens)

    layout_title_slide(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Design System Test Deck",
        subtitle="pptx_kit • 16:9 • safe margins • native text",
        hero_image=img,
        speaker_notes="QA: title hero + overlay band.",
    )

    layout_section_divider(
        prs,
        tokens,
        section_title="Layout gallery",
        kicker="Section",
        speaker_notes="Section divider stress.",
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Image + text split (cover crop)",
        bullets=[
            "Native text boxes with padding and NO auto-fit shrink.",
            "Image panel ~46% width — center crop preserves aspect.",
            "Later shapes draw above earlier shapes — text stays readable.",
        ],
        image_path=img,
        image_side="right",
        speaker_notes="Verify body left, image right.",
    )

    layout_big_idea(
        prs,
        tokens,
        tmp_dir,
        temps,
        headline="One idea per slide beats ten cramped bullets.",
        image_path=img,
        speaker_notes="Big idea + optional banner image.",
    )

    layout_three_point(
        prs,
        tokens,
        title="Three cards (max three)",
        points=[
            ("Hierarchy", "Titles at 24 pt; body never below 16 pt unless forced."),
            ("Rhythm", "Generous margins — nothing touches the slide edge."),
            ("Safety", "Overflow splits to continuation slides or shorter copy."),
        ],
        speaker_notes="Three-point rule enforced.",
    )

    layout_process_timeline(
        prs,
        tokens,
        title="Process steps",
        steps=[
            "Estimate lines from character width heuristics.",
            "Shrink font between 20 pt and 16 pt before splitting.",
            "Paginate bullets when still too tall.",
        ],
        speaker_notes="Timeline layout.",
    )

    layout_quote(
        prs,
        tokens,
        quote="Energy and matter don’t vanish — they move through trophic levels and cycles.",
        source="Alberta Biology 20 — Unit A (paraphrase for layout test)",
        speaker_notes="Quote slide.",
    )

    layout_comparison(
        prs,
        tokens,
        title="Comparison",
        left_title="Bad habits",
        left_bullets=[
            "Tiny floating JPEGs",
            "Placeholder template walls of text",
            "Stretching photos to fit boxes",
        ],
        right_title="This system",
        right_bullets=[
            "PIL cover crop + intentional panels",
            "Split slides when content overflows",
            "QA checks bounds + minimum font",
        ],
        speaker_notes="Two-column layout.",
    )

    # --- Stress tests ---
    layout_title_slide(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Extraordinarily long title that must truncate cleanly without breaking mid-word awkwardly " * 2,
        subtitle="Subtitle also rather long but should stay inside safe horizontal margins",
        hero_image=None,
        speaker_notes="Long title truncation.",
    )

    long_bullets = [
        "This is a deliberately long bullet that keeps going so we exercise word wrap and height estimation across multiple lines without clipping any characters off the bottom of the text box.",
        "Second long bullet: Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Third bullet pushes pagination — max five bullets then split.",
        "Fourth bullet continues pagination stress.",
        "Fifth bullet should trigger continuation slide logic when combined height exceeds body region.",
        "Sixth bullet forces a second slide via bullet count split.",
    ]
    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Stress: many bullets + continuation",
        bullets=long_bullets,
        image_path=img,
        speaker_notes="Should produce continuation slides.",
    )

    out_path = out_dir / "pptx-design-system-test-deck.pptx"
    prs.save(out_path)
    print(f"Wrote {out_path}")

    reports = validate_deck(prs, tokens)
    bad = [r for r in reports if not r.ok or r.warnings]
    for r in bad:
        print(f"Slide {r.slide_index}: errors={r.errors} warnings={r.warnings}")
    ok_all = all(r.ok for r in reports)
    print(f"QA strict pass: {ok_all} ({len(reports)} slides)")


if __name__ == "__main__":
    main()
