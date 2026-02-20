---
name: openclaw_security_news
description: Fetch and summarize the latest OpenClaw security news. Use when someone asks about OpenClaw security, vulnerabilities, incidents, risks, or related tools. Triggers on "openclaw", "openclaw security", "clawdbot", "clawhub", "moltbot", or "openclaw news".
---

# OpenClaw Security News

Retrieve and present the latest OpenClaw security headlines from the curated news repository.

## Source

**Primary:** https://raw.githubusercontent.com/joylarkin/openclaw-security-news/main/README.md  
**Repo:** https://github.com/joylarkin/openclaw-security-news  
**Maintained by:** Joy Larkin — updated twice daily

## Workflow

### Step 1: Fetch the data

Use `web_fetch` to retrieve:
```
https://raw.githubusercontent.com/joylarkin/openclaw-security-news/main/README.md
```

If the raw URL is unavailable, fall back to:
```
https://github.com/joylarkin/openclaw-security-news
```

### Step 2: Filter by intent

| User asks about... | Return... |
|--------------------|-----------|
| Latest news | Most recent date section (top of file) |
| A specific date or range | That date's section(s) only |
| A specific topic (e.g., infostealers, ClawHub, ZTNA) | Matching headlines across all dates |
| General overview | Top 2 date sections + summary |

### Step 3: Format the response

- Lead with the date(s) covered
- List headlines as a bulleted list with source publication names
- Include hyperlinks where present in the source
- End with: *Source: [OpenClaw Security News](https://github.com/joylarkin/openclaw-security-news) — updated twice daily*

## Notes

- Do not fabricate or infer headlines not present in the source
- If the fetch fails, tell the user and link them directly to the repo
- The README is the single source of truth — prefer it over web search for OpenClaw security news
- Related terms tracked in this repo: OpenClaw, Moltbot, Clawdbot, ClawHub, ClawBands, SecureClaw, NanoClaw, Carapace
