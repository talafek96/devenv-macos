# duckduckgo-search

Search DuckDuckGo from the command line and get clean, readable results. No API key required.

## Setup

No setup needed — the script uses DuckDuckGo's public search API.

## Usage

```bash
uv run duckduckgo-search/scripts/search.py "your search query"
```

### Options

| Flag | Description |
|------|-------------|
| `-n`, `--min-results N` | Minimum number of results to request (default: 25) |
| `-r`, `--region CODE` | Region code, e.g. `us-en`, `uk-en`, `wt-wt` for global (default: `wt-wt`) |
| `-t`, `--time {d,w,m,y}` | Time range: `d`=day, `w`=week, `m`=month, `y`=year |
| `--md`, `--markdown` | Output as Markdown instead of JSON (default: JSON) |
| `--out-dir DIR` | Save to DIR instead of `.research/prior-art-search/` (also honors `PRIOR_ART_OUT_DIR`) |

### Output files

Results are automatically saved to `.research/prior-art-search/` in the current directory (as `<timestamp>_duckduckgo-search_<slug>_<hash>.json`, or `.md` with `--md`). On a successful search, the result payload is never printed to stdout — only a `Results saved to <path> (<chars>, <KB>)` receipt is printed; `read` the file for the content. Empty or failed searches write no payload file and instead print a status line (e.g. `[duckduckgo-search] empty: no results found`).

### Examples

```bash
# Basic search
uv run duckduckgo-search/scripts/search.py "python asyncio tutorial"

# Top 10 results from the past week
uv run duckduckgo-search/scripts/search.py "rust vs go performance" -n 10 -t w

# Markdown output
uv run duckduckgo-search/scripts/search.py "best static site generators" --md

# Region-specific search
uv run duckduckgo-search/scripts/search.py "local news" -r uk-en
```

## As an Agent Skill

Install into Devin or any compatible agent:

```bash
devin skills install duckduckgo-search
```

Once installed, the agent can invoke it via the `/duckduckgo-search` command or autonomously when it needs to search the web.
