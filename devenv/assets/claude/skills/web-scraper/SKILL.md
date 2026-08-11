---
name: web-scraper
description: Fetch a web page and extract its main content (article text, headings, lists, tables) as clean readable text, stripped of navigation, ads, and scripts. Use whenever the user gives a URL and wants its content, or asks to read, summarize, quote, or scrape a page, extract its links, or compare pages — including Reddit listing and comment threads, which are handled specially. Results are saved as JSON under `.research/prior-art-search/` (pass `--md` for Markdown).
allowed-tools: Bash(uv run *) Read
---

# Web Scraper

Fetch a web page and return its main content, stripped of navigation, ads, scripts, and boilerplate.

## Step 1: Fetch and extract

```
uv run $SKILL_DIR/scripts/scrape.py "$1"
```

### Options

- `--links` — preserve hyperlinks in the output
- `--images` — include image references
- `--no-tables` — exclude tables
- `--language en` — filter to a specific language
- `--md` / `--markdown` — output Markdown instead of JSON (default: JSON)

For multiple URLs, run the command once per URL.

## Output files

Scraped content is saved to `.research/prior-art-search/` (relative to the current working directory; override with `--out-dir` or the `PRIOR_ART_OUT_DIR` env var). Each **successful** scrape writes one file `<timestamp>_web-scraper_<slug>_<hash>.json` (or `.md` with `--md`) and appends a line to `.research/prior-art-search/index.jsonl`. **Failed or empty extractions write no payload file**, but are still recorded in `index.jsonl` (`status:"empty"|"error"`, `out_path: null`) and the status is printed to stdout (e.g. `[web-scraper] error: …`) so you know immediately. On success the only stdout is the `Results saved to …` receipt — `read` the file for the content.

Envelope: `{schema_version, skill, kind:"document", query, args, generated_at, status, message, count:null, payload:{url, title, author, date, sitename, description, content}}`. `--no-metadata` suppresses only `description` (and the `categories`/`tags` extras); `author`/`date`/`sitename` are still populated. All envelope keys stay present regardless, so the schema is stable. Each `index.jsonl` line: `{ts, skill, kind, query, status, message, count, out_path, schema_version, run_id}` with an absolute `out_path`. See the **prior-art** skill's "Output contract" for the full cross-skill schema.

## Step 2: Present the content

Based on what the user asked for:

- **"Summarize this page"** — read the extracted content and provide a concise summary.
- **"What does this page say about X?"** — find and quote the relevant sections.
- **"Extract all links"** — re-run with `--links` (JSON is the default) and list them.
- **"Compare these pages"** — scrape each URL, then compare the content side by side.
- If the user just gave a URL with no instruction, present the title, metadata, and a brief summary, then ask what they'd like to know.

## Part of a research loop — feed what you extract back in

**If the user just wanted this one page read or summarized, do that and stop — the steps below apply when you're actively researching a topic, not fetching a single page.** When you are researching, scraping is one step in a loop, and what you pull out should drive your next move:

1. **Mine it for the next query.** A good page names things — specific algorithms, projects, authors, papers. Those names are your next, more specific search terms (via `duckduckgo-search`, or the `github-search` skill if it is available); vague queries return vaguer pages, so harvest the specifics here.
2. **Judge the source's provenance.** Is the author someone who built, operated, or studied the thing (a maintainer, paper author, postmortem writer), or a third party summarizing them? Prefer the former; treat an outsider explainer as a pointer toward the primary source, not the source itself.
3. **Follow the citation graph — this is the tool that does it.** Re-run with `--links` to pull a page's references, then scrape the ones it cites, compares against, or credits — the route to sources a plain query won't surface.
4. **Stop on convergence.** When further pages stop changing your answer, you're done; if it keeps shifting, the question is under-specified — say so rather than scraping forever.

Full method: the **prior-art** skill's "query-craft loop".

## Reddit support

Reddit URLs are handled specially — the script parses old.reddit.com HTML directly:

- **Listing pages** (subreddit, front page, /top, /hot, etc.) return a numbered list of posts with scores, comment counts, authors, and URLs.
- **Post pages** (/r/.../comments/...) return the post title, selftext or link URL, and all comments with author and body text.

This works without Reddit API credentials.

## Error handling

- If the script says "Failed to fetch", the URL may be behind authentication, geo-blocked, or down. Tell the user.
- If "No extractable content found", the page may be a SPA that requires JavaScript rendering. Explain this to the user — trafilatura works on static/server-rendered HTML.
- For paywalled sites, the extraction will typically get whatever content is visible without login.

## Guidelines

- Do not dump the entire extracted text to the user unless they ask for it. Summarize or answer their question.
- If the content is very long (>5000 words), summarize it section by section.
- Preserve the original structure (headings, lists) when presenting content.
- If the page is in a language the user didn't request, mention this.

User arguments: $ARGUMENTS
