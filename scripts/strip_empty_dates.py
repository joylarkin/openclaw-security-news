#!/usr/bin/env python3
"""Remove empty date headers from the HEADLINES block in README.md.

A date header is "empty" when it has no bullet-point entries before the next
date header (or the HEADLINES_END marker).  Running this script is idempotent.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"


def strip_empty_dates(text: str) -> str:
    """Return text with empty ### YYYY-MM-DD sections removed from HEADLINES block."""
    start_marker = "<!-- HEADLINES_START -->"
    end_marker = "<!-- HEADLINES_END -->"

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        return text

    before = text[: start_idx + len(start_marker)]
    block = text[start_idx + len(start_marker) : end_idx]
    after = text[end_idx:]

    # Split into per-date sections; keep the leading content before the first header.
    sections = re.split(r"(?=^### \d{4}-\d{2}-\d{2})", block, flags=re.MULTILINE)

    kept = []
    for section in sections:
        header_m = re.match(r"^### \d{4}-\d{2}-\d{2}", section)
        if not header_m:
            # Content before the first date header — always keep.
            kept.append(section)
            continue
        # Keep the section only if it contains at least one bullet entry.
        if re.search(r"^- \[", section, re.MULTILINE):
            kept.append(section)

    return before + "".join(kept) + after


def main():
    original = README.read_text(encoding="utf-8")
    cleaned = strip_empty_dates(original)
    if cleaned == original:
        print("No empty date headers found — nothing to do.")
        return
    removed = original.count("\n### ") - cleaned.count("\n### ")
    README.write_text(cleaned, encoding="utf-8")
    print(f"Removed {removed} empty date header(s) from {README.name}.")


if __name__ == "__main__":
    main()
