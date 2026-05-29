"""
Download OpenStax Biology 2e raster figures from the official osbooks-biology-bundle
GitHub mirror (same assets used in the web textbook build).

License: CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
Textbook: https://openstax.org/details/books/biology-2e
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

OPENSTAX_BIOLOGY_2E_BOOK = "https://openstax.org/details/books/biology-2e"

# Verified distribution path for Biology 2e media (OpenStax / Rice University).
OPENSTAX_OSBOOKS_BIOLOGY_BUNDLE_MEDIA = (
    "https://raw.githubusercontent.com/openstax/osbooks-biology-bundle/main/media/"
)

DEFAULT_UA = "school-agents-test-builder/1.0 (+https://openstax.org)"


def media_url(filename: str) -> str:
    return OPENSTAX_OSBOOKS_BIOLOGY_BUNDLE_MEDIA + filename.lstrip("/")


def download_media_file(
    filename: str,
    dest: Path,
    *,
    user_agent: str = DEFAULT_UA,
    timeout_s: float = 60.0,
) -> tuple[Path, str]:
    """
    Download ``filename`` from the OpenStax osbooks-biology-bundle media folder.

    Returns ``(dest_path, sha256_hex)`` of the saved bytes.
    """
    url = media_url(filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = resp.read()
    dest.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    return dest, digest
