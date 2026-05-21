"""Download partner logos into backend/static/partners/ (run once after deploy)."""
from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "static" / "partners"
OUT.mkdir(parents=True, exist_ok=True)

# Favicon / header assets from official sites (best-effort; fall back to generated PNG).
SOURCES: dict[str, str] = {
    "gov.png": "https://www.tanzania.go.tz/images/logo.png",
    "tamisemi.png": "https://www.tamisemi.go.tz/site/images/logo.png",
    "tcu.png": "https://www.tcu.go.tz/images/tcu-logo.png",
    "necta.png": "https://www.necta.go.tz/images/logo.png",
    "heslb.png": "https://www.heslb.go.tz/images/heslb_logo.png",
    "nacte.png": "https://www.nacte.go.tz/site/images/logo.png",
    "nactvet.png": "https://www.nactvet.go.tz/images/logo.png",
    "tveta.png": "https://www.tveta.go.tz/images/logo.png",
    "nida.png": "https://www.nida.go.tz/images/nida-logo.png",
    "rita.png": "https://www.rita.go.tz/images/logo.png",
    "moe.png": "https://www.moe.go.tz/images/moe-logo.png",
    "costech.png": "https://www.costech.or.tz/images/logo.png",
}


def _placeholder(name: str, path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return
    img = Image.new("RGBA", (160, 64), (15, 23, 42, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, 156, 60), radius=10, fill=(30, 41, 59, 230))
    draw.text((12, 22), name[:12], fill=(226, 232, 240))
    img.save(path, "PNG")


def main() -> None:
    for filename, url in SOURCES.items():
        dest = OUT / filename
        if dest.is_file() and dest.stat().st_size > 500:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MwongozoSmart/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            if len(data) > 200:
                dest.write_bytes(data)
                print(f"OK {filename}")
                continue
        except Exception as exc:
            print(f"skip {filename}: {exc}")
        label = filename.replace(".png", "").upper()
        _placeholder(label, dest)
        print(f"placeholder {filename}")


if __name__ == "__main__":
    main()
