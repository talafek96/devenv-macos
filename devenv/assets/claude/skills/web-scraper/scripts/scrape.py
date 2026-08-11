# /// script
# requires-python = ">=3.11"
# dependencies = ["trafilatura>=2.0.0", "courlan>=1.0.0"]
# ///
"""Fetch a web page and extract its main content as clean text.

Includes special handling for Reddit pages (listing pages and post/comment
threads) since Reddit's HTML is not well suited for generic content extraction.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path

import trafilatura

SCHEMA_VERSION = 1
SKILL = "web-scraper"

# Ensure UTF-8 stdout so non-ASCII output doesn't crash on piped/Windows (cp1252) consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _fetch(url: str) -> str | None:
    """Fetch URL with a browser-like user-agent to avoid bot detection."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return downloaded
    except Exception:
        pass
    return _fetch_raw(url)


def _fetch_raw(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode(errors="replace")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Reddit-specific parsing
# ---------------------------------------------------------------------------

_REDDIT_PATTERN = re.compile(
    r"^https?://(?:www\.|old\.|new\.)?reddit\.com(/.*)?$"
)
_REDDIT_POST_PATTERN = re.compile(
    r"/r/\w+/comments/\w+"
)


def _is_reddit(url: str) -> bool:
    return bool(_REDDIT_PATTERN.match(url))


def _is_reddit_post(url: str) -> bool:
    return bool(_REDDIT_POST_PATTERN.search(url))


def _old_reddit_url(url: str) -> str:
    """Convert any reddit URL to old.reddit.com for parsing."""
    return re.sub(
        r"^https?://(?:www\.|new\.)?reddit\.com",
        "https://old.reddit.com",
        url,
    )


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def _scrape_reddit_listing(url: str) -> dict:
    """Parse a Reddit listing page (subreddit, front page, etc.)."""
    old_url = _old_reddit_url(url)
    html = _fetch_raw(old_url)
    if not html:
        return {"error": f"Failed to fetch {url}", "url": url}

    # Extract subreddit name from title
    title_match = re.search(r"<title>([^<]+)</title>", html)
    title = _strip_html(title_match.group(1)) if title_match else ""

    # Extract posts: each post is in a div.thing with data attributes
    posts = []
    for match in re.finditer(
        r'<div[^>]*class="[^"]*\bthing\b[^"]*"([^>]*)>',
        html,
    ):
        attrs = match.group(0)

        def _attr(name: str) -> str:
            m = re.search(rf'data-{name}="([^"]*)"', attrs)
            return m.group(1) if m else ""

        post_url = _attr("url")
        score = _attr("score") or "0"
        author = _attr("author")

        # Find the title link and comment count after this div
        rest = html[match.end():match.end() + 3000]
        title_match = re.search(
            r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>', rest
        )
        comments_match = re.search(
            r'class="[^"]*comments[^"]*"[^>]*>(\d+)\s*comment', rest
        )
        n_comments = comments_match.group(1) if comments_match else "0"

        if title_match and post_url:
            post_title = _strip_html(title_match.group(1))
            full_url = post_url if post_url.startswith("http") else f"https://reddit.com{post_url}"
            posts.append({
                "title": post_title,
                "url": full_url,
                "score": score,
                "comments": n_comments,
                "author": author,
            })

    if not posts:
        return {"error": "No posts found on page", "url": url}

    lines = []
    for i, p in enumerate(posts, 1):
        lines.append(f"{i}. [{p['score']} pts, {p['comments']} comments] {p['title']}")
        lines.append(f"   by u/{p['author']} — {p['url']}")

    return {
        "url": url,
        "title": title,
        "author": "",
        "date": "",
        "sitename": "Reddit",
        "content": "\n".join(lines),
    }


def _scrape_reddit_post(url: str) -> dict:
    """Parse a Reddit post page with comments."""
    old_url = _old_reddit_url(url)
    html = _fetch_raw(old_url)
    if not html:
        return {"error": f"Failed to fetch {url}", "url": url}

    # Post title
    title_match = re.search(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>', html)
    title = _strip_html(title_match.group(1)) if title_match else ""

    # Post author
    author_match = re.search(
        r'<p class="tagline[^"]*"[^>]*>.*?class="author[^"]*"[^>]*>([^<]+)<', html, re.DOTALL
    )
    author = author_match.group(1) if author_match else ""

    # Self-text (post body) — look specifically inside the expando/post area,
    # not the sidebar.  The post body lives inside <div class="expando">
    selftext = ""
    expando_match = re.search(
        r'<div[^>]*class="[^"]*expando[^"]*"[^>]*>(.*?)</div>\s*<!--\s*/expando',
        html, re.DOTALL
    )
    if not expando_match:
        # Fallback: look for the entry div's usertext-body
        expando_match = re.search(
            r'<div[^>]*class="[^"]*entry[^"]*"[^>]*>(.*?)<div[^>]*class="[^"]*commentarea',
            html, re.DOTALL
        )
    if expando_match:
        body_match = re.search(
            r'<div class="[^"]*usertext-body[^"]*"[^>]*>\s*<div class="md">(.*?)</div>\s*</div>',
            expando_match.group(1), re.DOTALL
        )
        if body_match:
            selftext = _strip_html(body_match.group(1))

    # Link URL (for link posts)
    link_match = re.search(
        r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"', html
    )
    link_url = link_match.group(1) if link_match else ""

    # Comments
    comments = []
    for match in re.finditer(
        r'<div[^>]*class="[^"]*comment[^"]*"[^>]*data-author="([^"]*)"[^>]*>',
        html,
    ):
        comment_author = match.group(1)
        rest = html[match.end():match.end() + 5000]

        # Score
        score_match = re.search(r'title="(\d+) points?"', rest)
        score = score_match.group(1) if score_match else "?"

        # Comment body
        body_match = re.search(
            r'<div class="[^"]*usertext-body[^"]*"[^>]*>\s*<div class="md">(.*?)</div>\s*</div>',
            rest, re.DOTALL
        )
        body = _strip_html(body_match.group(1)) if body_match else ""

        if body:
            comments.append({
                "author": comment_author,
                "score": score,
                "body": body,
            })

    # Build output
    parts = []
    if selftext:
        parts.append(selftext)
    elif link_url and link_url != url:
        parts.append(f"Link: {link_url}")

    if comments:
        parts.append("")
        parts.append(f"--- Comments ({len(comments)} shown) ---")
        parts.append("")
        for c in comments:
            parts.append(f"u/{c['author']} ({c['score']} pts):")
            parts.append(c["body"])
            parts.append("")

    return {
        "url": url,
        "title": title,
        "author": author,
        "date": "",
        "sitename": "Reddit",
        "content": "\n".join(parts),
    }


# ---------------------------------------------------------------------------
# Generic scraping (trafilatura)
# ---------------------------------------------------------------------------

def scrape(url: str, *, include_links: bool = False, include_images: bool = False,
           include_tables: bool = True, with_metadata: bool = True,
           target_language: str | None = None) -> dict:
    """Download and extract the main content from a URL.

    Returns a dict with keys: url, title, author, date, content, and optionally
    description, sitename, categories, tags.
    """
    # Reddit-specific handling
    if _is_reddit(url):
        if _is_reddit_post(url):
            return _scrape_reddit_post(url)
        else:
            return _scrape_reddit_listing(url)

    downloaded = _fetch(url)
    if downloaded is None:
        return {"error": f"Failed to fetch {url}", "url": url}

    result = trafilatura.extract(
        downloaded,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        include_comments=False,
        output_format="txt",
        with_metadata=True,
        target_language=target_language,
        favor_recall=True,
    )

    if result is None:
        return {"error": "No extractable content found", "url": url}

    metadata = trafilatura.extract(
        downloaded,
        output_format="json",
        with_metadata=True,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        include_comments=False,
        target_language=target_language,
        favor_recall=True,
    )

    if metadata:
        meta = json.loads(metadata)
    else:
        meta = {}

    output = {
        "url": url,
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "date": meta.get("date", ""),
        "sitename": meta.get("sitename", ""),
        "content": result,
    }

    if with_metadata:
        for key in ("description", "categories", "tags"):
            val = meta.get(key, "")
            if val:
                output[key] = val

    return output


# ---------------------------------------------------------------------------
# File saving
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def _out_dir() -> Path:
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
        slug = re.sub(r"[^\w\-.]", "_", label)[:80].strip("_") or "page"
        uniq = hashlib.sha1(f"{label}{os.getpid()}{ts}".encode("utf-8")).hexdigest()[:8]
        ext = ".md" if markdown else ".json"
        out_path = out_dir / f"{ts}_{SKILL}_{slug}_{uniq}{ext}"
        content = md_text if markdown else json.dumps(envelope, ensure_ascii=False, indent=2)
        out_path.write_text(content, encoding="utf-8")
        out_path_str = out_path.resolve().as_posix()

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _format_text(result: dict) -> str:
    """Format a scrape result dict as readable text."""
    parts: list[str] = []
    if result.get("title"):
        parts.append(f"# {result['title']}")
        parts.append("")
    meta_parts = []
    if result.get("author"):
        meta_parts.append(f"By: {result['author']}")
    if result.get("date"):
        meta_parts.append(f"Date: {result['date']}")
    if result.get("sitename"):
        meta_parts.append(f"Source: {result['sitename']}")
    if meta_parts:
        parts.append(f"*{' | '.join(meta_parts)}*")
        parts.append("")
    if result.get("description"):
        parts.append(f"> {result['description']}")
        parts.append("")
    parts.append(result.get("content", ""))
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Extract clean content from a web page"
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--links", action="store_true",
                        help="Include hyperlinks in output")
    parser.add_argument("--images", action="store_true",
                        help="Include image references in output")
    parser.add_argument("--no-tables", action="store_true",
                        help="Exclude tables from output")
    parser.add_argument("--no-metadata", action="store_true",
                        help="Only return content, skip metadata fields")
    parser.add_argument("--language", type=str, default=None,
                        help="Target language (e.g. 'en', 'de')")
    parser.add_argument("--md", "--markdown", action="store_true", dest="markdown",
                        help="Output as Markdown instead of JSON (default: JSON)")
    parser.add_argument("--out-dir", default=None,
                        help="Directory for saved results (overrides PRIOR_ART_OUT_DIR)")

    args = parser.parse_args()

    result = scrape(
        args.url,
        include_links=args.links,
        include_images=args.images,
        include_tables=not args.no_tables,
        with_metadata=not args.no_metadata,
        target_language=args.language,
    )

    if "error" in result:
        status, message = "error", result["error"]
    elif not result.get("content"):
        status, message = "empty", "no extractable content found"
    else:
        status, message = "ok", None

    document = {
        "url": args.url,
        "title": result.get("title", ""),
        "author": result.get("author", ""),
        "date": result.get("date", ""),
        "sitename": result.get("sitename", ""),
        "description": result.get("description", ""),
        "content": result.get("content", ""),
    }
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "skill": SKILL,
        "kind": "document",
        "query": args.url,
        "args": {"links": args.links, "images": args.images,
                 "tables": not args.no_tables, "language": args.language},
        "generated_at": _iso_now(),
        "status": status,
        "message": message,
        "count": None,
        "payload": document,
    }
    out_dir = Path(args.out_dir) if args.out_dir else _out_dir()
    md_text = _format_text(result) if args.markdown else None
    sys.exit(_emit(envelope, args.url, markdown=args.markdown, md_text=md_text, out_dir=out_dir))


if __name__ == "__main__":
    main()
