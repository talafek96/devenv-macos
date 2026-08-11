# web-scraper

Fetch any web page and extract its main content as clean, readable text — no HTML noise, no nav bars, no cookie banners.

Uses [trafilatura](https://github.com/adbar/trafilatura) for general content extraction, with custom parsers for Reddit.

## Usage

Invoke as a skill:

```
/web-scraper https://example.com/article
```

Or run the script directly:

```bash
uv run $SKILL_DIR/scripts/scrape.py https://example.com/article
uv run $SKILL_DIR/scripts/scrape.py https://example.com/article --links --md
uv run $SKILL_DIR/scripts/scrape.py https://reddit.com/r/programming/top/?t=week
```

## Options

| Flag | Description |
|------|-------------|
| `--links` | Preserve hyperlinks in output |
| `--images` | Include image references |
| `--no-tables` | Exclude tables |
| `--no-metadata` | Only return content body |
| `--language XX` | Filter to a target language |
| `--md`, `--markdown` | Output as Markdown instead of JSON (default: JSON) |
| `--out-dir DIR` | Save to DIR instead of `.research/prior-art-search/` (also honors `PRIOR_ART_OUT_DIR`) |

## Output files

Scraped content is automatically saved to `.research/prior-art-search/` in the current directory (as `<timestamp>_web-scraper_<slug>_<hash>.json`, or `.md` with `--md`). On a successful scrape the script always writes the file and prints only a `Results saved to …` receipt (path, char count, KB) — `read` that file for the content. Failed or empty extractions write no payload file and instead print a `[web-scraper] error: …` / `[web-scraper] empty: …` status line.

## Reddit support

Reddit URLs get special handling via old.reddit.com HTML parsing (no API key needed):

- **Listing pages** — returns numbered posts with scores, comment counts, and links
- **Post pages** — returns title, body/link, and all comments with text

## Limitations

- JavaScript-rendered SPAs won't work (trafilatura fetches static HTML)
- Paywalled content returns only what's visible without login
- Some sites block automated requests via user-agent filtering
