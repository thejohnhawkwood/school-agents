"""Design tokens — slide geometry, typography, colours, spacing."""

from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches


@dataclass(frozen=True)
class DesignTokens:
    """
    Restrained educational 16:9 deck — high contrast, generous margins.
    All lengths in inches unless noted.
    """

    # --- Slide (Office widescreen default) ---
    slide_width_in: float = 13.333
    slide_height_in: float = 7.5

    # Safe content inset from slide edge (body text never closer than ~0.3in per spec)
    margin_in: float = 0.42
    column_gap_in: float = 0.35

    # Inner padding inside text boxes / cards (reduces usable width for wrapping)
    text_padding_in: float = 0.12

    # Typography (points)
    title_pt: int = 40
    title_min_pt: int = 34
    subtitle_pt: int = 24
    subtitle_min_pt: int = 22
    body_pt: int = 20
    body_min_pt: int = 16
    caption_pt: int = 12
    label_pt: int = 14

    line_spacing: float = 1.18
    bullet_spacing_before_pt: int = 4
    bullet_spacing_after_pt: int = 6

    # Layout splits
    image_panel_fraction: float = 0.46  # ~40–55% width for split slides

    # Content rules
    max_bullets_per_slide: int = 5
    max_words_per_bullet: int = 14  # prefer ≤12; allow slight overflow before split
    max_title_chars: int = 72

    # Palette (RGB)
    color_bg: RGBColor = RGBColor(248, 250, 252)  # slate-50
    color_bg_alt: RGBColor = RGBColor(255, 255, 255)
    color_text_primary: RGBColor = RGBColor(15, 23, 42)  # slate-900
    color_text_muted: RGBColor = RGBColor(71, 85, 105)  # slate-600
    color_accent: RGBColor = RGBColor(37, 99, 235)  # blue-600
    color_accent_dark: RGBColor = RGBColor(30, 64, 175)
    color_card: RGBColor = RGBColor(255, 255, 255)
    color_overlay: RGBColor = RGBColor(15, 23, 42)

    # Fonts (PowerPoint fallbacks on macOS / Windows)
    font_title: str = "Calibri Light"
    font_body: str = "Calibri"

    def slide_width(self) -> Emu:
        return Inches(self.slide_width_in)

    def slide_height(self) -> Emu:
        return Inches(self.slide_height_in)

    def margin(self) -> Emu:
        return Inches(self.margin_in)

    def safe_left(self) -> Emu:
        return Inches(self.margin_in)

    def safe_top(self) -> Emu:
        return Inches(self.margin_in)

    def safe_width(self) -> Emu:
        return Inches(self.slide_width_in - 2 * self.margin_in)

    def safe_height(self) -> Emu:
        return Inches(self.slide_height_in - 2 * self.margin_in)


DEFAULT_TOKENS = DesignTokens()
