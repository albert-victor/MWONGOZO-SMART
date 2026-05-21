"""Download news portfolio images into backend/static/news/."""
from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "static" / "news"
OUT.mkdir(parents=True, exist_ok=True)

ITEMS = {
    "tcu.jpg": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=900&q=80",
    "heslb.jpg": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=900&q=80",
    "necta.jpg": "https://images.unsplash.com/photo-1434030216411-718904896271?auto=format&fit=crop&w=900&q=80",
    "institutions.jpg": "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=900&q=80",
    "mwongozo.jpg": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=900&q=80",
}


def main() -> None:
    for name, url in ITEMS.items():
        dest = OUT / name
        if dest.is_file() and dest.stat().st_size > 8000:
            print("skip", name)
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MwongozoSmart/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            print("OK", name, dest.stat().st_size)
        except Exception as exc:
            print("fail", name, exc)


if __name__ == "__main__":
    main()
