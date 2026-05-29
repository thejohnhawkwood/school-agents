"""
Reusable PowerPoint design system for school-agents slide generators.

Provides tokens, text fitting, image composition (cover/contain via PIL),
layout builders, and QA helpers for 16:9 educational decks.
"""

from pptx_kit.tokens import DEFAULT_TOKENS, DesignTokens
from pptx_kit.qa import SlideQAReport, validate_slide, validate_deck

__all__ = ["DesignTokens", "DEFAULT_TOKENS", "SlideQAReport", "validate_slide", "validate_deck"]
