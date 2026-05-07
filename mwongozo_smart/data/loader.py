from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class GuidebookTextBlock:
    # A loose chunk of raw guidebook text grouped by heading.
    heading: str
    lines: list[str]


def load_guidebook_export(path: str | Path) -> list[str]:
    """Load a TCU guidebook JSON export that stores extracted lines."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = data.get("lines", [])
    return [str(line) for line in lines]


def split_institution_blocks(lines: list[str]) -> list[GuidebookTextBlock]:
    """Split raw guidebook lines into coarse institution/program sections."""
    blocks: list[GuidebookTextBlock] = []
    current_heading = "Unknown"
    buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Headings usually mark a new institution section.
        if stripped.startswith("Bachelor") and "Degree Admission Guidebook" in stripped:
            continue
        if "(" in stripped and ")" in stripped and any(marker in stripped for marker in ["University", "College", "Institute", "Centre"]):
            if buffer:
                blocks.append(GuidebookTextBlock(heading=current_heading, lines=buffer[:]))
                buffer.clear()
            current_heading = stripped
            continue
        buffer.append(stripped)

    if buffer:
        blocks.append(GuidebookTextBlock(heading=current_heading, lines=buffer[:]))

    return blocks
