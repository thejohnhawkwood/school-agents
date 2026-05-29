"""Image composition: object-fit cover/contain via PIL (no stretching in PPT)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image


def _rgb(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        if im.mode == "P":
            im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
        return bg
    return im.convert("RGB")


def crop_cover_to_aspect(src: Path, aspect_w: float, aspect_h: float) -> Image.Image:
    """Center-crop source image to match aspect ratio (w:h)."""
    im = _rgb(Image.open(src))
    iw, ih = im.size
    target_ratio = aspect_w / aspect_h
    src_ratio = iw / ih
    if src_ratio > target_ratio:
        # wider — crop left/right
        new_w = int(ih * target_ratio)
        left = (iw - new_w) // 2
        im = im.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        top = (ih - new_h) // 2
        im = im.crop((0, top, iw, top + new_h))
    return im


def render_cover(src: Path, frame_w_in: float, frame_h_in: float, dpi: int = 144) -> Image.Image:
    """Resize cropped image to exactly fill frame pixels (cover behaviour)."""
    aspect_w, aspect_h = frame_w_in, frame_h_in
    cropped = crop_cover_to_aspect(src, aspect_w, aspect_h)
    px_w = max(2, int(frame_w_in * dpi))
    px_h = max(2, int(frame_h_in * dpi))
    return cropped.resize((px_w, px_h), Image.Resampling.LANCZOS)


def render_contain(src: Path, frame_w_in: float, frame_h_in: float, dpi: int = 144) -> tuple[Image.Image, tuple[float, float]]:
    """
    Fit entire image inside frame (contain); returns image and (offset_x_in, offset_y_in)
    for centering in frame when composed on slide (caller draws letterbox).
    """
    im = _rgb(Image.open(src))
    iw, ih = im.size
    px_fw = int(frame_w_in * dpi)
    px_fh = int(frame_h_in * dpi)
    scale = min(px_fw / iw, px_fh / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    off_x_px = (px_fw - nw) // 2
    off_y_px = (px_fh - nh) // 2
    canvas = Image.new("RGB", (px_fw, px_fh), (248, 250, 252))
    canvas.paste(resized, (off_x_px, off_y_px))
    off_x_in = off_x_px / dpi
    off_y_in = off_y_px / dpi
    return canvas, (off_x_in, off_y_in)


def save_temp_jpeg(im: Image.Image, directory: Path, prefix: str = "img") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".jpg", prefix=prefix + "_", dir=str(directory))
    import os

    os.close(fd)
    p = Path(path)
    im.save(p, format="JPEG", quality=88, optimize=True)
    return p


def add_image_cover(
    slide,
    image_path: Path,
    left: Emu,
    top: Emu,
    width: Emu,
    height: Emu,
    tmp_dir: Path,
    dpi: int = 144,
):
    """Crop+zoom to fill frame; aspect preserved; no stretch."""
    w_in = width.inches
    h_in = height.inches
    rendered = render_cover(image_path, w_in, h_in, dpi=dpi)
    tmp = save_temp_jpeg(rendered, tmp_dir, "cover")
    pic = slide.shapes.add_picture(str(tmp), left, top, width=width, height=height)
    return pic, tmp


def add_image_contain_centered(
    slide,
    image_path: Path,
    left: Emu,
    top: Emu,
    width: Emu,
    height: Emu,
    tmp_dir: Path,
    dpi: int = 144,
):
    """Letterboxed contain inside frame."""
    w_in = width.inches
    h_in = height.inches
    canvas, _ = render_contain(image_path, w_in, h_in, dpi=dpi)
    tmp = save_temp_jpeg(canvas, tmp_dir, "contain")
    pic = slide.shapes.add_picture(str(tmp), left, top, width=width, height=height)
    return pic, tmp
