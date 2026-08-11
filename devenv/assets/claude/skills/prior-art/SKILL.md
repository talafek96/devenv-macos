---
name: prior-art
description: >-
  Search for existing solutions before building, instead of reinventing the
  wheel. Use proactively whenever you are about to write non-trivial code, add
  or choose a dependency or library, or work out how to implement a feature —
  and for design and architecture questions and casual
  phrasings such as "how should I build X", "is there a better way", "how did
  others solve this", or "how do others do this".
  Routes research through dedicated search/extraction skills (duckduckgo-search
  and web-scraper, plus GitHub and YouTube search where installed) rather than
  ad-hoc searching, evaluates candidates (maintenance, adoption, license, fit),
  and reports findings before writing custom code. Skip for trivial
  project-local edits (renames, typos, formatting) and for logic fully
  determined by this codebase's own types, schema, or rules.
allowed-tools: Bash(uv run *) Read Grep Glob
---

# Prior Art

Before building anything non-trivial, find out how it's already been solved. The reason isn't
politeness toward existing work — it's that a maintained library or a real codebase has already
paid for the edge cases you haven't thought of yet (timezones, unicode, retries, partial
failures, the security bug someone filed two years ago). Reinventing silently is the default
failure mode; this skill exists to interrupt it with a quick, structured look before you commit
to custom code.

## The search ladder

Work top to bottom and **stop as soon as you have a defensible answer** — you don't need to run
every rung for every task.

1. **The codebase.** `Grep` / `Glob` for an existing utility, helper, or pattern that already
   does this or something close. The cheapest reuse is the code already in front of you.
2. **The project's dependencies.** Read the manifest — `package.json`, `Cargo.toml`,
   `requirements.txt`, `pyproject.toml`, `go.mod`, etc. — before adding anything new. A library
   you already depend on probably solves more than you're using it for, and adds zero new
   supply-chain surface.
3. **The web.** Use the **`duckduckgo-search`** skill for established packages and patterns, then
   **`web-scraper`** to read the promising hits in full so you reason from the primary source,
   not a search snippet.
4. **GitHub (optional enrichment).** For real repositories: **if the `github-search` skill is
   installed, use it** — it surfaces stars, license, and freshness, and its issue trackers are
   where you learn a library's actual failure modes before you adopt it. **If it isn't installed,
   search GitHub via `duckduckgo-search` scoped to `github.com` and read the promising repos and
   issue threads with `web-scraper`** — same evidence, one rung slower.
5. **Talks & walkthroughs (optional enrichment).** When a concept needs a proper explanation or
   you want the author's own design reasoning, find a conference talk or deep-dive: **if the
   `youtube-search` and `youtube-wisdom` skills are installed, use them** (`youtube-search` →
   `youtube-wisdom`) to find and mine it; **otherwise locate one with `duckduckgo-search`** and
   read its transcript or notes page with `web-scraper`.

**Prefer the skills over raw tools — including future ones.** The search/extraction skills
above are the current toolkit (`duckduckgo-search` and `web-scraper` are always available; the
`github-search`, `youtube-search`, and `youtube-wisdom` skills are used only when installed, per
the rungs above, and have a `duckduckgo-search` + `web-scraper` fallback when they are not); the
standing rule is broader: before defaulting to an ad-hoc web
fetch, check your available-skills list for anything that searches, fetches, or extracts an
external resource, and use it. A skill added later (say, one that searches a package registry or
arXiv) should slot into this ladder the same way, without editing this file.

## The query-craft loop — how to search, not just where

The ladder tells you *where* to look; this tells you *how* to query once you're there. Searching
is a loop, not a single shot — the first query rarely lands the best source. (If you only need a
single fact or one quick look, answer it and stop; this loop is for open research, not lookups.)

1. **Probe, then sharpen.** Treat the first query as a probe. Rate which terms returned primary
   sources versus noise (SEO blogspam, generic tutorials, AI-generated summaries of AI summaries).
   Each next query drops the noisy terms and adds *domain-specific* ones — names of specific
   algorithms, data structures, a project's internal modules, paper authors, or talk titles you
   saw in the good hits. Every iteration must be measurably more specific than the last.
2. **Test for primary sources.** Prefer material authored by someone who built, operated, or
   formally studied the thing — maintainers, paper authors, postmortem writers, conference
   speakers presenting their own work. A third-party tutorial is *scaffolding to locate* the
   primary source, not a substitute. If none exists after genuine searching, write "secondary, no
   primary located" rather than promoting a secondary source.
3. **Follow the citation graph.** When a source proves useful, your next move is to chase what
   *it* references — the papers it cites, the projects it benchmarks against, the people it
   credits, the issues it links — by re-querying on those names. It's the route to sources a plain
   keyword query won't surface.
4. **Stop on convergence.** When fresh queries stop changing your answer, stop — that's
   convergence (the per-query stop; the ladder's "stop when you have a defensible answer" still
   governs whether you climb another rung). If the answer keeps shifting, the question is ambiguous
   or under-specified; say so instead of searching forever.

**Query memory across sessions.** The `prior-art-researcher` agent logs query lessons to
`~/.claude/agent-memory/query-lessons.jsonl`, which the `query-librarian` agent compacts into a
ranked `query-playbook.md` (ordered by how few attempts each pattern took to reach a usable
source). If that playbook exists, skim it before improvising queries in a domain it already
covers and try its top-ranked patterns first.

## Where findings are saved

The search and extraction skills don't just print results — they write each one to
`.research/prior-art-search/` (relative to the directory you're working in) as a JSON file
named `<timestamp>_<skill>_<slug>.json` (pass `--md` to any of those skills to get Markdown
instead) — for example `20260618_142530_duckduckgo-search_fuzzy-string-matching.json`. That folder
becomes the **evidence
trail** for the task: what you searched, what came back, and which pages you read, all on disk
and greppable rather than trapped in the conversation. When you report a prior-art decision you
can point at these files instead of re-searching. Add `.research/` to the project's `.gitignore`
so the trail stays local and isn't committed.

Each saved file is a **versioned JSON envelope** — `{schema_version, skill, kind:"list"|"document",
query, status, count, payload}` — and every write also appends one line to
`.research/prior-art-search/index.jsonl`, which is the manifest to read if you (or a downstream
pipeline) want to enumerate findings without globbing filenames. Two behaviors worth knowing:
**empty or failed lookups write no payload file** (but are still recorded as one line in `index.jsonl` with `out_path: null`) — the skill prints the status to stdout (e.g.
`[duckduckgo-search] empty: no results found`), so absence of a file means "nothing found,"
not "look harder"; and large results print only a `Results saved to …` receipt, so `read` the
file when you need the content. To keep a whole task's artifacts in one place regardless of where
commands run, set `PRIOR_ART_OUT_DIR` to one absolute directory for the session (or pass
`--out-dir`).

## Output contract (for pipelines)

Every saved file is one JSON object — a **versioned envelope** — and `index.jsonl` is the
manifest to enumerate them. Pin to `schema_version` (currently `1`); these are the v1 fields.

**Envelope** (every successful file): `schema_version` (int), `skill`, `kind` (`"list"` |
`"document"`), `query` (search string or URL), `args` (invocation flags), `generated_at`
(ISO-8601 with offset), `status` (`"ok"`), `message` (null on ok), `count` (number of results
for `kind:"list"`; **null** for `kind:"document"`), and `payload` — an **array** for `list`, an
**object** for `document`.

**Shared list fields** (every `list` item): `title`, `url`, `snippet`. Extras by skill, present
only when that optional skill is installed and used: **if the `github-search` skill is
installed**, its list items add `stars, forks, language, license, updated`; **if the
`youtube-search` skill is installed**, its items add `duration, channel, published, score`.
**Document payloads:** web-scraper → `{url, title, author, date, sitename, description, content}`;
and **if the `youtube-wisdom` skill is installed**, its documents are
`{video_id, title, url, segments:[{timestamp, text}]}`.

**`index.jsonl`** — one line per run, including empty/error:
`{ts, skill, kind, query, status, message, count, out_path, schema_version, run_id}`. `out_path`
is an **absolute, POSIX-style** path on success and **null** on empty/error, so the manifest
distinguishes "ran, found nothing" (`status:"empty"`) from "never ran" (no line). `run_id`
echoes `PRIOR_ART_RUN_ID` when set, so a session's files group together. A consumer reads it as:
`for line in index.jsonl: rec=json.loads(line); data=json.load(open(rec["out_path"])) if rec["out_path"] else None`.
(If any run used `--md`, its `out_path` ends in `.md`, not `.json` — a JSON consumer should accept only `out_path` ending in `.json`, or just keep `--md` out of machine-consumed runs.)

## Evaluate what you find

A match isn't automatically the right answer. Weigh:

- **Maintenance** — last release, open-vs-closed issue ratio, is it abandoned?
- **Adoption** — stars, downloads, who depends on it. Battle-tested beats clever.
- **Scope fit** — a focused library that does exactly your thing beats a kitchen-sink framework
  you'd pull in for 5% of its surface.
- **License** — MIT/Apache/BSD are safe to depend on or learn from; GPL/AGPL or no-license carry
  obligations. Note it.
- **Security & quality** — known CVEs, sane API, tests present.

## Decide, in this order of preference

1. **Reuse an exact match** — existing code or a current dependency already does it.
2. **Depend on a well-maintained library** — when the problem is genuinely solved upstream.
3. **Extend a partial solution** — adapt or wrap something that gets you most of the way.
4. **Build custom** — only when nothing suitable exists, or every candidate fails the evaluation
   for a reason you can name.

## Report before you build

Never silently jump to custom code. Tell the user what you did, in one or two lines:

- "Found `X` (already a dependency / 4k★, MIT, active) — reusing it."
- "Searched npm + GitHub for a TOML parser; the maintained one is `Y`, using that."
- "Searched for an existing fuzzy-match lib; the candidates are unmaintained / wrong-scope, so
  building a small custom version — here's why."

This is the whole point of the pass: the user sees the decision *and* its evidence, not just the
result.

## Escalate the big questions

This skill is the lightweight, in-session check. When the decision is a genuine open
architectural / design question — multiple approaches with real tradeoffs across constraints,
needing several iterations and primary-source rigor — hand it to the **prior-art-researcher**
agent instead of trying to resolve it inline. The skill catches "is there a library for this?";
the agent answers "which of these five architectures fits our constraints, and why?".

**After the prior-art-researcher returns, act on its compaction flag.** That agent learns to
write better queries over time by recording lessons to `~/.claude/agent-memory/`. When its final
report says compaction is due (its `COMPACTION DUE` line, raised once `runs_since_compaction`
reaches 5), **spawn the `query-librarian` agent before you wrap up** — it distills the recorded
lessons into a sharper query playbook. That distillation is the only step that turns logged
lessons into faster future searches, so don't skip it when flagged. The librarian needs no
arguments; it reads the memory files and rewrites the playbook.

## When to skip

Don't run a search pass for trivial, project-local work: renaming a variable, fixing a typo,
reformatting, adjusting copy, or any change where there's nothing external to find. Prior-art
research has a cost; spend it where reuse is actually possible.
