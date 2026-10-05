---
name: defuddle
description: "Use when you need to extract the main article content, clean prose, or metadata from a web page (HTML file or URL) and convert it to Markdown or JSON. Wraps the real `defuddle` / `defuddle-cli` library (kepano/defuddle) so Hermes can pull readable content instead of raw, cluttered page HTML. Trigger: 'extract the article', 'clean this page', 'get the readable text from this URL', 'convert this page to markdown'."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [web, extraction, content, readability, markdown, scraping, defuddle]
    related_skills: [web-search, web_extract]
---

# Defuddle — clean article/content extraction from web pages

## Overview

[Defuddle](https://github.com/kepano/defuddle) (by kepano) is a library that extracts the
main content from a web page, stripping comments, sidebars, headers, footers, nav, and ads,
and returns clean, readable HTML/Markdown plus metadata (title, description, author, domain,
word count, etc.).

This skill is a **transparent wrapper** around the real CLI/library. Upstream ships no
SKILL.md, so this skill teaches Hermes exactly how to call the real `defuddle` binary.
There is no fabricated behavior — every command below maps directly to the installed tool.

## When to Use

- User pastes a URL or HTML file and wants the readable article, not the full page chrome.
- You need clean Markdown for summarization, RAG ingestion, or note-taking.
- You want page metadata (title, author, description, domain, published time, word count).
- Don't use for: structured DOM scraping of specific elements (use a real scraper / browser);
  authenticated/JS-only pages that render behind a login (defuddle may fetch a fallback but
  won't bypass auth).

## Installation (one-time, per environment)

The CLI used to be `defuddle-cli` but was **merged into the `defuddle` package**. Install the
current package so the `defuddle` binary is available:

```bash
npm install -g defuddle        # provides the `defuddle` CLI
# or, run without installing: npx -y defuddle <args>
```

Verify with: `defuddle --version` (or `npx -y defuddle --version`).

> Note: the old `defuddle-cli@0.7.0` is deprecated ("merged into defuddle"). Prefer `defuddle`.

## Core command: `defuddle parse`

Parse HTML from a **file path or URL** and emit clean content.

```bash
defuddle parse [options] <source>
```

`<source>` — a local `.html` file path OR a URL.

### Options (real, from `defuddle parse --help`)

| Flag | Meaning |
|------|---------|
| `-o, --output <file>` | Write to a file instead of stdout |
| `-m, --markdown` | Convert extracted content to Markdown |
| `--md` | Alias for `--markdown` |
| `-j, --json` | Emit JSON with `content` + metadata (title, description, author, domain, wordCount, publishedTime, siteName, image, favicon, …) |
| `-p, --property <name>` | Print just one field (e.g. `title`, `description`, `domain`, `author`, `wordCount`) |
| `--debug` | Emit debug info / diagnostic output |
| `-h, --help` | Help |

## Recipes (copy-paste)

1. **URL → clean Markdown (to stdout):**
   ```bash
   defuddle parse "https://example.com/article" --markdown
   ```

2. **URL → Markdown saved to a file:**
   ```bash
   defuddle parse "https://example.com/article" -m -o /tmp/article.md
   ```

3. **URL → JSON with metadata + content:**
   ```bash
   defuddle parse "https://example.com/article" --json -o /tmp/article.json
   ```

4. **Local HTML file → Markdown:**
   ```bash
   defuddle parse ./page.html --md -o /tmp/page.md
   ```

5. **Just the title / domain / word count:**
   ```bash
   defuddle parse "https://example.com/article" -p title
   defuddle parse "https://example.com/article" -p domain
   defuddle parse "https://example.com/article" -p wordCount
   ```

6. **Capture a live page first with curl, then parse (use when URL fetch is blocked):**
   ```bash
   curl -sL "https://example.com/article" -o /tmp/page.html
   defuddle parse /tmp/page.html --markdown -o /tmp/article.md
   ```

## Behavior notes / pitfalls

- **URL fetching is best-effort.** If the local HTML has no usable content (client-rendered
  SPA), defuddle may hit third-party fallbacks (e.g. FxTwitter for X/Twitter posts). If offline
  or in a restricted env, pass a local HTML file instead.
- **Markdown vs JSON:** use `--markdown` for human-readable output, `--json` when you need the
  structured metadata alongside content (e.g. to cite author/date).
- **Redirects / large pages:** pipe to a file (`-o`) rather than relying on terminal stdout for
  very large articles.
- **Source flag order:** `<source>` is a positional argument — put the URL/file after the flags
  or at the end. `--property` only takes one field name per invocation.
- **Bulk extraction:** loop over a list of URLs, one `defuddle parse` per URL, writing each to
  `<slug>.md`. Don't assume a built-in batch mode exists.

## Verification checklist

- [ ] `defuddle --version` succeeds (or `npx -y defuddle --version`).
- [ ] `defuddle parse <url> --markdown` returns clean prose, not nav/footer/ads.
- [ ] JSON mode (`--json`) contains expected `content` + at least `title`/`domain`.
- [ ] Output file exists at the `-o` path when used.
