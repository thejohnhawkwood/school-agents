#!/usr/bin/env python3
"""
Teacher introduction deck — aligns with focus packs (Water, Atmosphere, Food, Soil).
Uses pptx_kit: four subsystem cards per focus, Gemini prompts, diagrams, Q&A, poster, bibliography.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import urllib.request

from pptx_kit.layouts import (
    layout_comparison,
    layout_four_subsystem_cards,
    layout_image_text_split,
    layout_process_timeline,
    layout_section_divider,
    layout_title_slide,
    init_widescreen_deck,
)
from pptx_kit.qa import validate_deck
from pptx_kit.tokens import DEFAULT_TOKENS

IMAGE_SPECS = (
    ("mars_surface_PIA25443.jpg", "https://images-assets.nasa.gov/image/PIA25443/PIA25443~large.jpg"),
)

# --- Diagram “must show” summaries (Pack Section 5.1), tightened for cards ---
WATER_CARDS = [
    (
        "W1",
        "Crew water reclamation",
        "Trace urine, sweat, breath, grey water → capture, treatment, back to potable. Flow arrows + stages.",
    ),
    (
        "W2",
        "Mars in-situ water harvesting",
        "Ice / minerals / polar sources → extraction → strip contaminants (e.g. perchlorates) → enter habitat loop.",
    ),
    (
        "W3",
        "Crop & irrigation loop",
        "Hydro / aeroponics / soil: supply → plants → transpiration → condense → return; show producers moving water.",
    ),
    (
        "W4",
        "Shield + thermal mass",
        "Reservoirs / pipes near crew & seed bank: drinking + radiation shield + temperature stability — one diagram.",
    ),
]

ATM_CARDS = [
    (
        "M1",
        "Crew respiratory gas loop",
        "O₂ use / CO₂ production per person vs air volume; exhaust to scrubber or crops; rough moles or volume.",
    ),
    (
        "M2",
        "Greenhouse gas exchange",
        "Day/night photosynthesis vs crop respiration; airflow; O₂ to crew, CO₂ back from crew.",
    ),
    (
        "M3",
        "Backup life support",
        "Mechanical CO₂ scrub / O₂ gen (e.g. electrolysis). Why biology still matters if machines fail.",
    ),
    (
        "M4",
        "Interior vs exterior Mars + UV",
        "Thin CO₂ outside vs hab air; UV risk to crops under glass; regolith cover vs transparency.",
    ),
]

FOOD_CARDS = [
    (
        "F1",
        "Crop production module",
        "Greenhouse / controlled farm: lights (sun vs LED), CO₂ tap, hydro or soil — matter → producer biomass.",
    ),
    (
        "F2",
        "Trophic strategy & diet",
        "Pyramid or flow: why mostly plants; energy steps; rough kcal per person per day.",
    ),
    (
        "F3",
        "Nutrient recycling",
        "Close N & P: compost / bioprocessing, legume fixation if used, supplements → hydroponics or soil.",
    ),
    (
        "F4",
        "Shielded growth & storage",
        "Seed bank, cold storage, buried / shielded greenhouse — protect germination & stored food (Q8).",
    ),
]

SOIL_CARDS = [
    (
        "B1",
        "Growth substrate production",
        "Regolith / simulant: perchlorate handling, amendments, delivery to beds — matter into producers.",
    ),
    (
        "B2",
        "Organic waste → decomposition",
        "Waste streams → compost / reactors; heat & CO₂ ties to habitat; label major decomposers.",
    ),
    (
        "B3",
        "Mineralization & soil food web",
        "N & P from organic matter through microbes / fungi to plant-available forms (20-A2.1k).",
    ),
    (
        "B4",
        "Shielded / controlled exposure",
        "UV shielding, walls, buried compost — protect microbes; limit forward contamination (Q8).",
    ),
]

PACK1_PROMPTS = [
    "1.1 Outcome framing",
    "1.2 Per-person water budget",
    "1.3 ISS water recovery benchmark",
    "1.4 Mars in-situ water resources",
    "1.5 Water chemistry for biology",
    "1.6 Radiation shielding (hydrogen-rich water)",
    "1.7 The Martian case study",
    "1.8 Adversarial verification",
]

PACK2_PROMPTS = [
    "2.1 Outcome framing",
    "2.2 Biosphere 2 oxygen crash",
    "2.3 Photosynthetic biomass per person",
    "2.4 Mars atmosphere today",
    "2.5 Stromatolites / Great Oxidation",
    "2.6 Radiation / UV / ozone & crops",
    "2.7 The Martian case study",
    "2.8 Adversarial verification",
]

PACK3_PROMPTS = [
    "3.1 Outcome framing",
    "3.2 10% rule on Mars",
    "3.3 NASA ISS crop trials (Veggie)",
    "3.4 Solar flux vs photosynthesis",
    "3.5 Nitrogen & phosphorus cycles",
    "3.6 Radiation vs crops / storage",
    "3.7 The Martian case study",
    "3.8 Adversarial verification",
]

PACK4_PROMPTS = [
    "4.1 Outcome framing",
    "4.2 Regolith vs soil (numbers)",
    "4.3 Perchlorates & biology",
    "4.4 Closed-habitat food web",
    "4.5 Compost safety & pathogens",
    "4.6 Biosphere 2 / soil lessons",
    "4.7 The Martian case study",
    "4.8 Adversarial verification",
]


def download_assets(dest_dir: Path) -> dict[str, Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for fname, url in IMAGE_SPECS:
        target = dest_dir / fname
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Bio20TeacherDeckBuilder/1.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if len(data) < 5000 or data[:2] != b"\xff\xd8":
                continue
            target.write_bytes(data)
            out[fname] = target
        except OSError:
            continue
    return out


def main() -> None:
    tokens = DEFAULT_TOKENS
    out_dir = ROOT / "outputs" / "labs" / "bio20-unitA-mars-research"
    asset_dir = out_dir / "_teacher_intro_assets"
    tmp_dir = out_dir / "_teacher_intro_tmp"
    assets = download_assets(asset_dir)
    temps: list[Path] = []

    prs = init_widescreen_deck(tokens)
    hero = assets.get("mars_surface_PIA25443.jpg")

    layout_title_slide(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Mars Settlement Research — Teacher briefing",
        subtitle="Bio 20 Unit A • Four focus packs • Same deliverables structure",
        hero_image=hero,
        speaker_notes="Match each section to the printed/DOCX pack.",
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Four research focuses (one pack each)",
        bullets=[
            "Pack 1 — Water: closed-loop hydrology, Mars ice, irrigation, water as shield (W1–W4).",
            "Pack 2 — Atmosphere: O₂/CO₂ balance, crops, backup scrubbers, exterior Mars (M1–M4).",
            "Pack 3 — Food: trophic efficiency, crops, nutrients, radiation vs food (F1–F4).",
            "Pack 4 — Soil & food webs: substrates, compost, mineralization, shielded biology (B1–B4).",
        ],
        image_path=None,
        speaker_notes="Students receive pack-01 … pack-04 DOCX from the course folder.",
    )

    layout_four_subsystem_cards(
        prs,
        tokens,
        title="Focus A — Water (Pack 1)",
        subtitle="Every student draws one diagram; the team covers all four sub-systems. LASTNAME-W#.png",
        cards=WATER_CARDS,
        speaker_notes="Section 5 of pack-01-water.",
    )

    layout_four_subsystem_cards(
        prs,
        tokens,
        title="Focus B — Atmosphere (Pack 2)",
        subtitle="Diagram filenames: LASTNAME-M#.png",
        cards=ATM_CARDS,
        speaker_notes="Section 5 of pack-02-atmosphere.",
    )

    layout_four_subsystem_cards(
        prs,
        tokens,
        title="Focus C — Food (Pack 3)",
        subtitle="Diagram filenames: LASTNAME-F#.png",
        cards=FOOD_CARDS,
        speaker_notes="Section 5 of pack-03-food.",
    )

    layout_four_subsystem_cards(
        prs,
        tokens,
        title="Focus D — Soil & food webs (Pack 4)",
        subtitle="Diagram filenames: LASTNAME-B#.png",
        cards=SOIL_CARDS,
        speaker_notes="Section 5 of pack-04-soil-food-web.",
    )

    layout_section_divider(
        prs,
        tokens,
        section_title="Universal AI workflow (all packs)",
        kicker="Section 4",
        speaker_notes="Gemini is scaffolding only — verify every claim.",
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Gemini rules (identical in every pack §4.1)",
        bullets=[
            "Verify every fact against non-AI sources before it goes on a slide or poster.",
            "Log prompts & responses; complete the disclosure appendix — AI must not write final prose.",
            "One numbered prompt at a time; use each pack’s §4.2 setup prompt once per thread.",
            "*The Martian* is narrative only — never cited as a science source for facts.",
        ],
        image_path=None,
        speaker_notes="Stress verification and honesty.",
    )

    layout_comparison(
        prs,
        tokens,
        title="Gemini prompt lists — Packs 1 & 2 (§4.3)",
        left_title="Pack 1 — Water",
        left_bullets=PACK1_PROMPTS,
        right_title="Pack 2 — Atmosphere",
        right_bullets=PACK2_PROMPTS,
        speaker_notes="Full prompt text lives in each DOCX.",
    )

    layout_comparison(
        prs,
        tokens,
        title="Gemini prompt lists — Packs 3 & 4 (§4.3)",
        left_title="Pack 3 — Food",
        left_bullets=PACK3_PROMPTS,
        right_title="Pack 4 — Soil",
        right_bullets=PACK4_PROMPTS,
        speaker_notes="Students run 3.1–3.8 or 4.1–4.8 in order.",
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Diagrams & filenames (Section 5 — all packs)",
        bullets=[
            "One labelled habitat diagram per student; together cover all four letter codes for that focus.",
            "Each diagram: title, scale, legend, flows, ≥1 quantitative annotation, outcome sentence.",
            "Submit PNG using your pack’s pattern (e.g. Lee-W2.png, Chen-M3.png).",
            "Poster clusters every teammate’s diagrams as the visual centerpiece.",
        ],
        image_path=None,
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Anchor questions Q1–Q10 → slideshow spine",
        bullets=[
            "Every pack lists ten curriculum-aligned questions (Section 6) mapped to Slides 5–14.",
            "Each answer needs evidence from the APA bibliography — not vibes.",
            "Radiation sub-question is Q8 in each pack (topic varies by focus).",
            "Q10 integrates all four sub-system diagrams into one habitat story.",
        ],
        image_path=None,
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Slide deck requirements (§8 — all packs)",
        bullets=[
            "§8.0 Intro block after title: habitat + focus; Martian environment facts (cited, not *The Martian*).",
            "Roughly 14–17 slides total including intros, Q1–Q10, unknowns, bibliography.",
            "≤30 words per slide body where possible; diagram or image on every slide.",
        ],
        image_path=None,
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Q&A preparation (Section 9 pattern)",
        bullets=[
            "Prepare plain-language answers for Grade 6 plus technical depth for peers.",
            "Expect questions on failure modes, mass budgets, and trade-offs between biology vs machines.",
            "Reuse your pack’s sample prompts — adjust wording to your focus.",
        ],
        image_path=None,
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Poster requirements (Section 7)",
        bullets=[
            "Physical tri-fold / board OR digital ≥ 24×36 inches.",
            "Must show outcomes, big question, all four diagrams, key findings, *Martian* critique, bibliography, AI note.",
        ],
        image_path=None,
    )

    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Bibliography & integrity",
        bullets=[
            "Minimum five sources; majority strong (NASA, peer-reviewed, government). APA 7 throughout.",
            "Cite Alberta Biology 20 Program of Studies for outcome codes.",
            "Include AI disclosure appendix + honest “what we don’t know yet” slide.",
        ],
        image_path=None,
    )

    layout_process_timeline(
        prs,
        tokens,
        title="Suggested pacing (adapt to your calendar)",
        steps=[
            "Week 1 — Groups, read pack, §4.2 Gemini setup, assign diagram codes, start sources.",
            "Week 2 — Run §4.3 prompts, draft diagrams & outline, verify citations.",
            "Week 3 — Poster + slides + rehearsal (add Week 4 if using long timeline).",
            "Final — Presentations + Grade 6 + optional scientist Q&A.",
        ],
        speaker_notes="Mirror the week tables inside each pack.",
    )

    credit = [
        "NASA/JPL-Caltech Mars imagery (images.nasa.gov) — optional hero only.",
        "Regenerate: python scripts/build_bio20_teacher_intro_pptx.py",
    ]
    layout_image_text_split(
        prs,
        tokens,
        tmp_dir,
        temps,
        title="Credits / rebuild",
        bullets=credit,
        image_path=hero,
        image_side="right",
    )

    out_path = out_dir / "teacher-intro-bio20-unitA-mars-research.pptx"
    try:
        prs.save(out_path)
    except PermissionError:
        alt = out_dir / "teacher-intro-bio20-unitA-mars-research-GENERATED.pptx"
        prs.save(alt)
        print(f"WARNING: could not overwrite {out_path} (file open?). Wrote {alt}")
        out_path = alt

    reports = validate_deck(prs, tokens)
    for r in reports:
        if r.errors or r.warnings:
            print(f"Slide {r.slide_index}: {r.errors} {r.warnings}")

    print(f"Wrote {out_path}")
    print(f"PIL temp renders: {len(temps)} | slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
