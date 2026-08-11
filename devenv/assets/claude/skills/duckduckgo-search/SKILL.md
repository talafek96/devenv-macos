---
name: duckduckgo-search
description: Search the web via DuckDuckGo (no API key) and return structured results (title, URL, snippet), then optionally scrape the top hits for a cited answer. Use whenever the user wants to look something up online, research a topic, find current information, verify a fact, or says "search for" / "google it" / "what's the latest on" — especially for information beyond your knowledge cutoff or that needs a source. Results are saved as JSON under `.research/prior-art-search/` (pass `--md` for Markdown).
allowed-tools: Bash(uv run *) Read
---

# DuckDuckGo Search

Search DuckDuckGo from the command line and return clean, readable results.

## Prerequisites

The **web-scraper** skill is optional but recommended: if it is installed alongside this skill, Step 3 uses it to fetch full page content from the top search results. If it isn't installed, this skill still works — Step 3 degrades gracefully and synthesizes the answer from the search snippets alone.

## Usage

```
uv run $SKILL_DIR/scripts/search.py <query> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `-n`, `--min-results N` | Minimum number of results to request (default: 25) |
| `-r`, `--region CODE` | Region code, e.g. `us-en`, `uk-en`, `wt-wt` for global (default: `wt-wt`) |
| `-t`, `--time {d,w,m,y}` | Time range: `d`=day, `w`=week, `m`=month, `y`=year |
| `--md`, `--markdown` | Output as Markdown instead of JSON (default: JSON) |

## Output files

Results are saved to `.research/prior-art-search/` (relative to the current working directory; override with `--out-dir` or the `PRIOR_ART_OUT_DIR` env var). Each **successful** run writes one file `<timestamp>_duckduckgo-search_<slug>_<hash>.json` (or `.md` with `--md`) and appends a line to `.research/prior-art-search/index.jsonl`. **Empty or failed searches write no payload file**, but are still recorded in `index.jsonl` (`status:"empty"|"error"`, `out_path: null`) and the status is printed to stdout (e.g. `[duckduckgo-search] empty: no results found`) so you know immediately. On success the only stdout is the `Results saved to …` receipt — `read` the file for the content.

Envelope: `{schema_version, skill, kind:"list", query, args, generated_at, status, message, count, payload:[{title, url, snippet}]}`. Each `index.jsonl` line: `{ts, skill, kind, query, status, message, count, out_path, schema_version, run_id}` with an absolute `out_path`. See the **prior-art** skill's "Output contract" for the full cross-skill schema.

## Instructions

### Step 1: Search wide

Run the search with at least 25 results (the default) to get a broad set:

```
uv run $SKILL_DIR/scripts/search.py <query>
```

### Step 2: Triage — pick which results to scrape

You now have 25+ titles, URLs, and snippets. **Do not scrape them all.** Read the titles and snippets carefully and select **3-7 results** to actually scrape based on these preferences (in priority order):

1. **Primary sources over aggregators.** Prefer official docs, original blog posts, research papers, and manufacturer pages over SEO content farms, listicles, or news aggregators that just summarize other sources.
2. **Technical depth over marketing.** A benchmark review with actual numbers beats a press release or product announcement. Look for words like "review", "benchmark", "tested", "measured", "hands-on", "in-depth" in titles.
3. **Source diversity.** Pick results from different domains and perspectives. Don't scrape 4 articles from the same site. Mix independent reviewers, official sources, community forums, and technical blogs.
4. **Recency.** When multiple results cover the same ground, prefer the most recent one — it likely incorporates earlier findings. Check dates in snippets.
5. **Specificity to the query.** If the user asked about performance, prioritize benchmark articles. If they asked "what is X", prioritize overviews and official pages. Match the source type to the user's intent.
6. **Skip low-signal pages.** Skip results that are clearly paywalled, login-walled, video-only (YouTube), pure forums with no structured answer, or link aggregators (e.g. HackerNews, Reddit listing pages with no real content in the snippet).

### Step 3: Scrape selected results

Use the `web-scraper` skill to fetch the full content of each selected result. **Scrape all selected pages in parallel** — do not scrape them one at a time.

```
uv run $SKILL_DIR/../web-scraper/scripts/scrape.py "<url>"
```

This reaches into the sibling `web-scraper` skill via a relative path. If that script doesn't exist, `web-scraper` isn't installed — say so and synthesize from the search snippets alone rather than failing.

### Step 4: Synthesize

Read all scraped content and produce a thorough answer:

- Lead with a direct answer to the user's question.
- Support claims with specifics from the sources (numbers, quotes, dates).
- Cite sources inline so the user knows where information comes from.
- Note any contradictions or disagreements between sources.
- If the scraped content doesn't fully answer the question, say what's missing.
- **Before you settle:** if this pass surfaced sharper terms or names worth chasing, loop once more (see "Search like a researcher" below); finalize only once fresh queries stop changing the answer. For a quick one-off lookup, just answer and skip the loop.

## Search like a researcher — iterate, don't one-shot

Steps 1-4 above are **one pass of a loop**, not the whole job; strong research repeats the pass, sharpening each time:

1. **Probe, then sharpen.** Treat the first query as a probe. Note which terms returned primary sources vs. noise (SEO blogspam, generic tutorials, AI-generated summaries); the next query drops the noise and adds *domain-specific* terms — names of specific algorithms, modules, paper authors, or titles you spotted in the good hits. Each iteration measurably more specific than the last. (Step 2 triage ranks the hits you already have; this governs what to query *next*.)
2. **Follow the citation graph.** When a source proves useful, chase what *it* references next: re-run the search on the names, projects, and references the scraped pages surfaced — the route to sources a plain keyword query won't surface.
3. **Stop on convergence.** When fresh queries stop changing the answer, you're done; if it keeps shifting, the question is ambiguous — say so instead of searching forever.

Full method: the **prior-art** skill's "query-craft loop"; for a deep multi-iteration design question, hand off to the **prior-art-researcher** agent.

### Error handling

- If the search returns no results, try rephrasing the query or broadening the terms.
- If the script fails, check network connectivity and retry once before reporting the error.
- If a scrape fails (paywall, blocking), skip it and note which source was inaccessible.
- When the query is ambiguous, prefer broader searches and let the user refine.

User arguments: $ARGUMENTS
