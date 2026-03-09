#!/usr/bin/env python3
"""Generate RSS 2.0 feed from OpenClaw security news data.

Reads all sections from README.md (Government Warnings, OpenClaw Headlines,
Vendor Advisories), filters out blocked URLs from never_add.csv, sorts by
date descending (most recently added first), and writes feed.xml.
"""

import csv
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

REPO_ROOT = Path(__file__).parent.parent

FEED_TITLE = "OpenClaw Security News"
FEED_LINK = "https://github.com/joylarkin/openclaw-security-news"
FEED_DESCRIPTION = (
    "Curated security news about OpenClaw vulnerabilities, exploits, and advisories. "
    "Updated twice daily."
)
FEED_SELF_URL = (
    "https://raw.githubusercontent.com/joylarkin/openclaw-security-news/main/feed.xml"
)


def load_blocked_urls(never_add_path: Path) -> set:
    """Return set of URLs that must never appear in the feed."""
    blocked = set()
    if not never_add_path.exists():
        return blocked
    with open(never_add_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                url = row[0].strip()
                if url.startswith("http"):
                    blocked.add(url)
    return blocked


def parse_date_from_text(text: str):
    """Extract a date from trailing text like '... - March 5, 2026'."""
    # Match "Month DD, YYYY" or "Month DD YYYY" at end of string
    m = re.search(r"(\w+\.?\s+\d{1,2},?\s*\d{4})\s*$", text.strip())
    if not m:
        return None
    raw = m.group(1).replace(",", "").strip()
    for fmt in ("%B %d %Y", "%b %d %Y", "%B. %d %Y", "%b. %d %Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def parse_readme(readme_path: Path, blocked_urls: set) -> list:
    """
    Parse all link sections from README and return a list of entry dicts.
    Each dict: {title, url, pub_date (datetime|None), section}

    Handles deletions gracefully: only URLs present in the current README
    are included, so any manually removed URL simply won't appear.
    """
    content = readme_path.read_text(encoding="utf-8")
    entries = []
    seen_urls = set()

    # ── Headlines (between HEADLINES_START / HEADLINES_END markers) ──────────
    headlines_block_m = re.search(
        r"<!-- HEADLINES_START -->(.*?)<!-- HEADLINES_END -->",
        content,
        re.DOTALL,
    )
    if headlines_block_m:
        current_date = None
        for line in headlines_block_m.group(1).split("\n"):
            # Date header: ### 2026-03-05
            date_m = re.match(r"^###\s+(\d{4}-\d{2}-\d{2})", line)
            if date_m:
                try:
                    current_date = datetime.strptime(
                        date_m.group(1), "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    current_date = None
                continue

            # Bullet with link: - [Title](url)
            link_m = re.match(r"^-\s+\[([^\]]+)\]\((https?://[^\)]+)\)", line)
            if link_m:
                title = link_m.group(1).strip()
                url = link_m.group(2).strip()
                if url in blocked_urls or url in seen_urls:
                    continue
                seen_urls.add(url)
                entries.append(
                    {
                        "title": title,
                        "url": url,
                        "pub_date": current_date,
                        "section": "OpenClaw Headlines",
                    }
                )

    # ── Government Warnings ───────────────────────────────────────────────────
    gov_m = re.search(
        r"^## Government Warnings About OpenClaw\n(.*?)(?=\n---|\n## )",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if gov_m:
        for line in gov_m.group(1).split("\n"):
            link_m = re.match(r"^-\s+\[([^\]]+)\]\((https?://[^\)]+)\)", line)
            if link_m:
                title = link_m.group(1).strip()
                url = link_m.group(2).strip()
                if url in blocked_urls or url in seen_urls:
                    continue
                seen_urls.add(url)
                entries.append(
                    {
                        "title": title,
                        "url": url,
                        "pub_date": parse_date_from_text(title),
                        "section": "Government Warnings",
                    }
                )

    # ── Vendor Advisories ─────────────────────────────────────────────────────
    vendor_m = re.search(
        r"^## OpenClaw Security Vendor Advisories\n(.*?)(?=\n---|\n## )",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if vendor_m:
        for line in vendor_m.group(1).split("\n"):
            # Vendor section uses * bullets
            link_m = re.match(r"^\*\s+\[([^\]]+)\]\((https?://[^\)]+)\)", line)
            if link_m:
                title = link_m.group(1).strip()
                url = link_m.group(2).strip()
                if url in blocked_urls or url in seen_urls:
                    continue
                seen_urls.add(url)
                entries.append(
                    {
                        "title": title,
                        "url": url,
                        "pub_date": parse_date_from_text(title),
                        "section": "Vendor Advisories",
                    }
                )

    return entries


def sort_entries(entries: list) -> list:
    """Most recently dated entries first; undated entries at the end."""
    dated = [e for e in entries if e["pub_date"]]
    undated = [e for e in entries if not e["pub_date"]]
    dated.sort(key=lambda e: e["pub_date"], reverse=True)
    return dated + undated


def build_rss(entries: list) -> str:
    """Build a pretty-printed RSS 2.0 XML string."""
    now = datetime.now(timezone.utc)

    rss = Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = FEED_TITLE
    SubElement(channel, "link").text = FEED_LINK
    SubElement(channel, "description").text = FEED_DESCRIPTION
    SubElement(channel, "language").text = "en-us"
    SubElement(channel, "lastBuildDate").text = format_datetime(now)

    atom_link = SubElement(channel, "atom:link")
    atom_link.set("href", FEED_SELF_URL)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for entry in entries:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = entry["title"]
        SubElement(item, "link").text = entry["url"]
        SubElement(item, "guid", isPermaLink="true").text = entry["url"]
        if entry.get("pub_date"):
            SubElement(item, "pubDate").text = format_datetime(entry["pub_date"])

    raw = tostring(rss, encoding="unicode")
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="  ", encoding=None)

    # Replace minidom's declaration with a clean one
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

    return "\n".join(lines)


def main():
    blocked = load_blocked_urls(REPO_ROOT / "never_add.csv")
    entries = parse_readme(REPO_ROOT / "README.md", blocked)
    sorted_entries = sort_entries(entries)
    xml_content = build_rss(sorted_entries)

    output = REPO_ROOT / "feed.xml"
    output.write_text(xml_content, encoding="utf-8")

    dated_count = sum(1 for e in sorted_entries if e["pub_date"])
    undated_count = len(sorted_entries) - dated_count
    print(
        f"Generated {output.name} with {len(sorted_entries)} items "
        f"({dated_count} dated, {undated_count} undated)"
    )


if __name__ == "__main__":
    main()
