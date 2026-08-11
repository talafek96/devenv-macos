# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ddgs>=7.0.0",
# ]
# ///
"""Search DuckDuckGo and return a versioned JSON envelope (or Markdown with --md)."""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 stdout so non-ASCII output doesn't crash on piped/Windows (cp1252) consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SCHEMA_VERSION = 1
SKILL = "duckduckgo-search"
MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]


# --- output plumbing (kept self-contained per skill; mirror changes across skills) ---

def _iso_now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def _out_dir() -> Path:
    """Where artifacts are written. Override with --out-dir (handled in main) or
    the PRIOR_ART_OUT_DIR env var; otherwise CWD-relative .research/prior-art-search/."""
    base = os.environ.get("PRIOR_ART_OUT_DIR")
    return Path(base) if base else Path(".research") / "prior-art-search"


def _emit(envelope: dict, label: str, *, markdown: bool, md_text: str | None,
          out_dir: Path) -> int:
    """Write a valid-JSON envelope (or Markdown) on success; on empty/error write no
    payload file. Every run — success, empty, or error — is recorded as one line in
    index.jsonl, and the status is printed to stdout. Returns a process exit code."""
    status = envelope["status"]
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Can't write anywhere — degrade to stdout so fetched data isn't lost.
        if status == "ok":
            print(f"[{SKILL}] could not write to {out_dir}: {e}", file=sys.stderr)
            print(json.dumps(envelope, ensure_ascii=False, indent=2))
        else:
            print(f"[{SKILL}] {status}: {envelope.get('message') or 'no results'} "
                  f"(query: {envelope.get('query', '')})")
        return 1 if status == "error" else 0

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_path_str = None
    if status == "ok":
        slug = re.sub(r"[^\w\-.]", "_", label)[:80].strip("_") or "query"
        uniq = hashlib.sha1(f"{label}{os.getpid()}{ts}".encode("utf-8")).hexdigest()[:8]
        ext = ".md" if markdown else ".json"
        out_path = out_dir / f"{ts}_{SKILL}_{slug}_{uniq}{ext}"
        content = md_text if markdown else json.dumps(envelope, ensure_ascii=False, indent=2)
        out_path.write_text(content, encoding="utf-8")
        out_path_str = out_path.resolve().as_posix()

    # Record every run in the manifest — absolute, POSIX out_path; null for empty/error.
    index_line = json.dumps({
        "ts": ts, "skill": SKILL, "kind": envelope.get("kind"),
        "query": envelope.get("query", ""), "status": status,
        "message": envelope.get("message"), "count": envelope.get("count"),
        "out_path": out_path_str, "schema_version": SCHEMA_VERSION,
        "run_id": os.environ.get("PRIOR_ART_RUN_ID"),
    }, ensure_ascii=False) + "\n"
    try:  # single O_APPEND syscall — the most atomic append for parallel writers
        fd = os.open(str(out_dir / "index.jsonl"),
                     os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, index_line.encode("utf-8"))
        finally:
            os.close(fd)
    except Exception:
        pass

    if status == "ok":
        size_kb = len(content.encode("utf-8")) / 1024
        print(f"Results saved to {out_path} ({len(content):,} chars, {size_kb:.1f} KB)")
    else:
        print(f"[{SKILL}] {status}: {envelope.get('message') or 'no results'} "
              f"(query: {envelope.get('query', '')})")
    return 1 if status == "error" else 0


# --- search ---

def _fetch(query: str, *, max_results: int, region: str, time_range: str | None) -> list[dict]:
    from ddgs import DDGS

    ddgs = DDGS()
    return list(
        ddgs.text(query, region=region, timelimit=time_range, max_results=max_results)
    )


def search(query: str, *, min_results: int = 25, region: str = "wt-wt",
           time_range: str | None = None) -> tuple[list[dict], str | None]:
    """Return (raw_results, error_message). error_message is None on success,
    even when the result set is empty."""
    request_size = min_results * 2
    results: list[dict] = []
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            results = _fetch(query, max_results=request_size, region=region, time_range=time_range)
            if len(results) >= min_results:
                break
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"Only {len(results)} results (want >={min_results}), "
                      f"retrying in {delay}s...", file=sys.stderr)
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"Error: {e} (attempt {attempt + 1}/{MAX_RETRIES}), "
                      f"retrying in {delay}s...", file=sys.stderr)
                time.sleep(delay)

    if not results and last_error is not None:
        return [], f"Search failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    return results, None


def _normalize(results: list[dict]) -> list[dict]:
    """Map ddgs fields to the shared result schema: title, url, snippet."""
    return [
        {
            "title": r.get("title", "") or "",
            "url": r.get("href", "") or "",
            "snippet": r.get("body", "") or "",
        }
        for r in results
    ]


def _to_markdown(query: str, items: list[dict]) -> str:
    md = [f"# DuckDuckGo search: {query}", ""]
    for i, it in enumerate(items, 1):
        md.append(f"## {i}. {it['title'] or '(untitled)'}")
        if it["url"]:
            md.append(f"<{it['url']}>")
        if it["snippet"]:
            md.append("")
            md.append(it["snippet"])
        md.append("")
    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search DuckDuckGo")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("-n", "--min-results", type=int, default=25,
                        help="Minimum number of results to request (default: 25)")
    parser.add_argument("-r", "--region", default="wt-wt",
                        help="Region code, e.g. us-en, uk-en, wt-wt for global (default: wt-wt)")
    parser.add_argument("-t", "--time", choices=["d", "w", "m", "y"], default=None,
                        help="Time range: d=day, w=week, m=month, y=year")
    parser.add_argument("--md", "--markdown", dest="markdown", action="store_true",
                        help="Output as Markdown instead of JSON (default: JSON)")
    parser.add_argument("--out-dir", default=None,
                        help="Directory for saved results (overrides PRIOR_ART_OUT_DIR)")

    args = parser.parse_args()
    query = " ".join(args.query)

    raw, error = search(query, min_results=args.min_results, region=args.region,
                        time_range=args.time)
    items = _normalize(raw)
    if error:
        status, message = "error", error
    elif not items:
        status, message = "empty", "no results found"
    else:
        status, message = "ok", None

    envelope = {
        "schema_version": SCHEMA_VERSION,
        "skill": SKILL,
        "kind": "list",
        "query": query,
        "args": {"region": args.region, "time": args.time, "min_results": args.min_results},
        "generated_at": _iso_now(),
        "status": status,
        "message": message,
        "count": len(items),
        "payload": items,
    }
    out_dir = Path(args.out_dir) if args.out_dir else _out_dir()
    md_text = _to_markdown(query, items) if args.markdown else None
    sys.exit(_emit(envelope, query, markdown=args.markdown, md_text=md_text, out_dir=out_dir))


if __name__ == "__main__":
    main()
