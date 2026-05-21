"""Compress hero JPGs for web (run once: saves ~50MB+ on landing)."""
from __future__ import annotations

from pathlib import Path

HERO = Path(__file__).resolve().parents[1] / "backend" / "static" / "hero"
MAX_W = 1600
QUALITY = 82


def main() -> None:
    try:
        from PIL import Image
    except ImportError:
        print("pip install Pillow first")
        return
    for path in sorted(HERO.glob("*.jpg")):
        before = path.stat().st_size
        im = Image.open(path)
        im.load()
        if im.width > MAX_W:
            ratio = MAX_W / im.width
            im = im.resize((MAX_W, int(im.height * ratio)), Image.Resampling.LANCZOS)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        after = path.stat().st_size
        print(f"{path.name}: {before // 1024}KB -> {after // 1024}KB")


if __name__ == "__main__":
    main()
