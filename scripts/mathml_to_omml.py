"""
Custom MathML -> OMML converter that produces clean Word-friendly output.

We avoid `mathml2omml` v0.0.2 because it (a) emits malformed
<m:groupChrPr> blocks, and (b) wraps content in <m:box> elements without
required <m:boxPr> children -- which Word renders as visible empty
boxes. This converter:

  * Produces no <m:box> wrappers at all.
  * Uses <m:acc> for stretched-arrow accents (e.g. \\vec{F}) instead of
    <m:groupChr>, which gives correct rendering in Word.
  * Handles the subset of MathML emitted by latex2mathml that we use.

Input:  a MathML string (as produced by latex2mathml.converter.convert).
Output: an XML string starting with <m:oMath xmlns:m="..."> ... </m:oMath>.
"""

from __future__ import annotations
from lxml import etree

MATHML_NS = "http://www.w3.org/1998/Math/MathML"
OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _local(elem) -> str:
    return etree.QName(elem.tag).localname


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _children(elem):
    return list(elem)


def _text(elem) -> str:
    return (elem.text or "").strip()


def _r_italic(text: str) -> str:
    """Italic math run (variables)."""
    return (f'<m:r><m:rPr><m:sty m:val="i"/></m:rPr>'
            f'<m:t xml:space="preserve">{_esc(text)}</m:t></m:r>')


def _r_upright(text: str) -> str:
    """Upright math run (operators, numbers, units, text)."""
    return (f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr>'
            f'<m:t xml:space="preserve">{_esc(text)}</m:t></m:r>')


def _convert_one(elem) -> str:
    tag = _local(elem)

    if tag == "math":
        body = "".join(_convert_one(c) for c in _children(elem))
        return f'<m:oMath xmlns:m="{OMML_NS}">{body}</m:oMath>'

    if tag == "mrow":
        return "".join(_convert_one(c) for c in _children(elem))

    if tag == "mi":
        # Math identifier - italic by default in math mode.
        text = elem.text or ""
        # Single-letter -> italic; multi-letter (like 'sin') -> upright.
        if len(text.strip()) <= 1:
            return _r_italic(text)
        return _r_upright(text)

    if tag == "mn":
        text = elem.text or ""
        return _r_upright(text)

    if tag == "mo":
        text = elem.text or ""
        return _r_upright(text)

    if tag == "mtext":
        text = elem.text or ""
        # mtext is upright text; preserve internal whitespace.
        return _r_upright(text)

    if tag == "mspace":
        # Width attribute -> insert a thin upright run.
        width = elem.get("width", "")
        if "thin" in width or "thick" in width or width:
            return _r_upright("\u2009")
        return ""

    if tag == "mfrac":
        cs = _children(elem)
        if len(cs) >= 2:
            num = _convert_one(cs[0])
            den = _convert_one(cs[1])
            return (f'<m:f><m:num>{num}</m:num>'
                    f'<m:den>{den}</m:den></m:f>')
        return ""

    if tag == "msub":
        cs = _children(elem)
        if len(cs) >= 2:
            base = _convert_one(cs[0])
            sub = _convert_one(cs[1])
            return (f'<m:sSub><m:e>{base}</m:e>'
                    f'<m:sub>{sub}</m:sub></m:sSub>')
        return ""

    if tag == "msup":
        cs = _children(elem)
        if len(cs) >= 2:
            base = _convert_one(cs[0])
            sup = _convert_one(cs[1])
            return (f'<m:sSup><m:e>{base}</m:e>'
                    f'<m:sup>{sup}</m:sup></m:sSup>')
        return ""

    if tag == "msubsup":
        cs = _children(elem)
        if len(cs) >= 3:
            base = _convert_one(cs[0])
            sub = _convert_one(cs[1])
            sup = _convert_one(cs[2])
            return (f'<m:sSubSup><m:e>{base}</m:e>'
                    f'<m:sub>{sub}</m:sub>'
                    f'<m:sup>{sup}</m:sup></m:sSubSup>')
        return ""

    if tag == "msqrt":
        body = "".join(_convert_one(c) for c in _children(elem))
        return ('<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr>'
                f'<m:deg/><m:e>{body}</m:e></m:rad>')

    if tag == "mroot":
        cs = _children(elem)
        if len(cs) >= 2:
            radicand = _convert_one(cs[0])
            degree = _convert_one(cs[1])
            return ('<m:rad><m:radPr></m:radPr>'
                    f'<m:deg>{degree}</m:deg>'
                    f'<m:e>{radicand}</m:e></m:rad>')
        return ""

    if tag == "mover":
        # Accent / over-character. Use <m:acc> for stretched arrows like
        # \\vec{}; better Word rendering than <m:groupChr>.
        cs = _children(elem)
        if len(cs) >= 2:
            base = _convert_one(cs[0])
            # Get the accent character from the second child.
            accent_char = (cs[1].text or "\u2192").strip() or "\u2192"
            return ('<m:acc>'
                    f'<m:accPr><m:chr m:val="{_esc(accent_char)}"/></m:accPr>'
                    f'<m:e>{base}</m:e></m:acc>')
        return ""

    if tag == "munder":
        cs = _children(elem)
        if len(cs) >= 2:
            base = _convert_one(cs[0])
            under = (cs[1].text or "_").strip() or "_"
            # Use <m:bar> for underline-style under.
            return ('<m:bar><m:barPr><m:pos m:val="bot"/></m:barPr>'
                    f'<m:e>{base}</m:e></m:bar>')
        return ""

    if tag == "mfenced":
        # Parens / brackets / pipes
        open_chr = elem.get("open", "(")
        close_chr = elem.get("close", ")")
        # Note: mfenced may have multiple children separated by separators.
        # For our content (single-arg fences), just concatenate children.
        body = "".join(_convert_one(c) for c in _children(elem))
        return (f'<m:d><m:dPr>'
                f'<m:begChr m:val="{_esc(open_chr)}"/>'
                f'<m:endChr m:val="{_esc(close_chr)}"/>'
                f'</m:dPr><m:e>{body}</m:e></m:d>')

    if tag == "mstyle":
        # Just pass through children.
        return "".join(_convert_one(c) for c in _children(elem))

    if tag == "menclose":
        # Just pass through children (we don't support enclose decorations).
        return "".join(_convert_one(c) for c in _children(elem))

    # Unknown element -> render its children
    return "".join(_convert_one(c) for c in _children(elem))


def convert(mathml_str: str) -> str:
    """Convert a MathML string to an OMML XML string."""
    # Parse MathML
    root = etree.fromstring(mathml_str.encode("utf-8") if isinstance(mathml_str, str)
                            else mathml_str)
    return _convert_one(root)
