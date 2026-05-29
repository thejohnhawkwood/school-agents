"""
Heuristic text measurement and fitting for native PPTX text boxes.
Text is always native OOXML text (not rendered as images).
"""

from __future__ import annotations

from typing import Sequence

from pptx_kit.tokens import DEFAULT_TOKENS, DesignTokens

# Calibri-ish average char width as fraction of font size (pt) for mixed Latin text
AVG_CHAR_WIDTH_FACTOR = 0.52

PT_PER_INCH = 72.0


def inches_to_pt(inches: float) -> float:
    return inches * PT_PER_INCH


def pt_to_inches(pt: float) -> float:
    return pt / PT_PER_INCH


def usable_width_in(box_width_in: float, padding_in: float, tokens: DesignTokens = DEFAULT_TOKENS) -> float:
    return max(0.25, box_width_in - 2 * padding_in)


def chars_per_line(box_width_in: float, font_pt: float, padding_in: float, tokens: DesignTokens = DEFAULT_TOKENS) -> int:
    uw = usable_width_in(box_width_in, padding_in, tokens)
    uw_pt = inches_to_pt(uw)
    cap = int(max(10, uw_pt / (font_pt * AVG_CHAR_WIDTH_FACTOR)))
    return cap


def wrap_text_to_lines(text: str, max_chars_per_line: int) -> list[str]:
    """Greedy word-wrap; prefers breaking at spaces."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        add_len = len(w) + (1 if cur else 0)
        if cur_len + add_len <= max_chars_per_line:
            cur.append(w)
            cur_len += add_len
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
            if len(w) > max_chars_per_line:
                # Hard-split pathological token
                chunk = max_chars_per_line
                while len(w) > chunk:
                    lines.append(w[:chunk])
                    w = w[chunk:]
                cur = [w] if w else []
                cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def estimate_lines_for_paragraph(
    text: str,
    box_width_in: float,
    font_pt: float,
    padding_in: float,
    tokens: DesignTokens = DEFAULT_TOKENS,
) -> int:
    cpl = chars_per_line(box_width_in, font_pt, padding_in, tokens)
    lines = wrap_text_to_lines(text.strip(), cpl)
    return max(1, len(lines))


def estimate_text_height_lines(
    lines: int,
    font_pt: float,
    line_spacing: float,
    paragraph_spacing_lines: float = 0.15,
) -> float:
    """Returns total height in inches for n lines of body text."""
    line_h_in = pt_to_inches(font_pt * line_spacing)
    return lines * line_h_in * (1.0 + paragraph_spacing_lines * 0.1)


def estimate_bullets_height(
    bullets: Sequence[str],
    box_width_in: float,
    font_pt: float,
    padding_in: float,
    tokens: DesignTokens = DEFAULT_TOKENS,
) -> float:
    cpl = chars_per_line(box_width_in, font_pt, padding_in, tokens)
    total_lines = 0
    for b in bullets:
        n = len(wrap_text_to_lines(b.strip(), cpl))
        total_lines += max(1, n)
    # small gap between bullets
    gap = pt_to_inches(tokens.bullet_spacing_after_pt) * (len(bullets) - 1 if len(bullets) > 1 else 0)
    return estimate_text_height_lines(total_lines, font_pt, tokens.line_spacing) + gap


def summarize_bullet(s: str, max_words: int) -> str:
    words = s.split()
    if len(words) <= max_words:
        return s
    return " ".join(words[: max_words - 1]) + "…"


def split_bullets_across_pages(
    bullets: list[str],
    max_bullets: int,
) -> list[list[str]]:
    out: list[list[str]] = []
    cur: list[str] = []
    for b in bullets:
        if len(cur) >= max_bullets:
            out.append(cur)
            cur = []
        cur.append(b)
    if cur:
        out.append(cur)
    return out or [[]]


def fit_bullets_to_box(
    bullets: list[str],
    box_width_in: float,
    box_height_in: float,
    title_height_reserved_in: float,
    font_start: int,
    font_min: int,
    tokens: DesignTokens = DEFAULT_TOKENS,
) -> tuple[list[str], int, list[list[str]]]:
    """
    Returns (display_bullets, font_size, pages) where pages is list of bullet groups
    if content must be split across multiple slides.
    """
    pages: list[list[str]] = []
    work = [summarize_bullet(b, tokens.max_words_per_bullet) for b in bullets]

    for font in range(font_start, font_min - 1, -1):
        h = estimate_bullets_height(
            work,
            box_width_in,
            float(font),
            tokens.text_padding_in,
            tokens,
        )
        if h + title_height_reserved_in <= box_height_in and len(work) <= tokens.max_bullets_per_slide:
            return work, font, [work]
        if h + title_height_reserved_in <= box_height_in and len(work) > tokens.max_bullets_per_slide:
            # need page split, not font shrink
            break

    # Split into pages of max bullets
    chunks = split_bullets_across_pages(work, tokens.max_bullets_per_slide)
    if len(chunks) > 1:
        for font in range(font_start, font_min - 1, -1):
            h = estimate_bullets_height(
                chunks[0],
                box_width_in,
                float(font),
                tokens.text_padding_in,
                tokens,
            )
            if h + title_height_reserved_in <= box_height_in:
                return chunks[0], font, chunks
        return chunks[0], font_min, chunks

    # Shrink font to minimum
    for font in range(font_start, font_min - 1, -1):
        h = estimate_bullets_height(
            work,
            box_width_in,
            float(font),
            tokens.text_padding_in,
            tokens,
        )
        if h + title_height_reserved_in <= box_height_in:
            return work, font, [work]

    # Truncate last bullets aggressively
    trimmed: list[str] = []
    for b in work:
        t = b
        while (
            estimate_bullets_height(trimmed + [t], box_width_in, float(font_min), tokens.text_padding_in, tokens)
            + title_height_reserved_in
            > box_height_in
            and len(t) > 40
        ):
            t = summarize_bullet(t, max(6, tokens.max_words_per_bullet // 2))
        trimmed.append(t)
    return trimmed, font_min, [trimmed]


def truncate_title(title: str, max_chars: int = 72) -> str:
    t = title.strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def estimateTextHeight(
    text: str,
    fontSize: int,
    boxWidthIn: float,
    paddingIn: float | None = None,
    tokens: DesignTokens = DEFAULT_TOKENS,
) -> float:
    """Estimated height in inches for one wrapped paragraph (heuristic)."""
    pad = paddingIn if paddingIn is not None else tokens.text_padding_in
    n_lines = estimate_lines_for_paragraph(text, boxWidthIn, float(fontSize), pad, tokens)
    return estimate_text_height_lines(n_lines, float(fontSize), tokens.line_spacing)


def splitBulletsAcrossSlides(bullets: list[str], max_per_slide: int) -> list[list[str]]:
    """Public alias."""
    return split_bullets_across_pages(bullets, max_per_slide)
