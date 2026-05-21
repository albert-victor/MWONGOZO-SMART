"""Generate crisp SVG partner marks when PNG fetch fails."""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "backend" / "static" / "partners"

PARTNERS = [
    ("gov.svg", "TZ", "Serikali"),
    ("tcu.svg", "TCU", "Universities"),
    ("necta.svg", "NECTA", "Examinations"),
    ("heslb.svg", "HESLB", "Loans"),
    ("nacte.svg", "NACTE", "Technical"),
    ("nactvet.svg", "NACTVET", "Vocational"),
    ("tveta.svg", "TVETA", "Skills"),
    ("rita.svg", "RITA", "Registration"),
    ("moe.svg", "MoE", "Education"),
]


def svg(acronym: str, sub: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="160" height="64" viewBox="0 0 160 64" role="img">
  <rect width="160" height="64" rx="12" fill="#1e293b"/>
  <text x="80" y="30" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#2dd4bf">{acronym}</text>
  <text x="80" y="48" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" fill="#94a3b8">{sub}</text>
</svg>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, acr, sub in PARTNERS:
        (OUT / name).write_text(svg(acr, sub), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
