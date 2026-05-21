"""Resize/compress partner PNGs for fast landing display (max height 128px)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "backend" / "static" / "partners"
MAX_H = 128
MIN_BYTES = 400


def _png_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


def optimize_with_pillow(path: Path) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    if path.stat().st_size < MIN_BYTES:
        return False
    im = Image.open(path)
    im.load()
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    w, h = im.size
    if h <= MAX_H and path.stat().st_size < 80_000:
        return False
    ratio = MAX_H / h
    nw = max(1, int(w * ratio))
    im = im.resize((nw, MAX_H), Image.Resampling.LANCZOS)
    if im.mode == "RGBA":
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg.convert("RGB")
    else:
        im = im.convert("RGB")
    im.save(path, "PNG", optimize=True)
    return True


def main() -> None:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Install Pillow: pip install Pillow")
        print("Skipping resize — CSS will still display logos.")
        return
    for path in sorted(OUT.glob("*.png")):
        if path.stat().st_size < MIN_BYTES:
            print("skip (too small/broken):", path.name)
            continue
        before = path.stat().st_size
        if optimize_with_pillow(path):
            after = path.stat().st_size
            sz = _png_size(path.read_bytes())
            print(f"OK {path.name}: {before} -> {after} bytes, size={sz}")
        else:
            print(f"keep {path.name} ({before} bytes)")


if __name__ == "__main__":
    main()
