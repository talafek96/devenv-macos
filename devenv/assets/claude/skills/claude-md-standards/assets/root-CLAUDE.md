<!--
  Root CLAUDE.md starter. Copy to the repo root as CLAUDE.md, fill the brackets,
  DELETE any section that doesn't earn its place, then run the linter:
    python .claude/skills/claude-md-standards/scripts/lint_claude_md.py CLAUDE.md --opinionated
  Keep it short: aim under ~200 lines. Delete anything the agent can infer from code.
  (This HTML comment is stripped before the file enters context — zero token cost.)
-->

# [Project name]

[One or two sentences: what this project is and its purpose, in plain language.]

## Stack & layout

- **Stack:** [languages + frameworks WITH versions, e.g. "Python 3.12, FastAPI, Postgres 16"]
- **Layout:** [top-level dirs that matter, e.g. "`src/` app, `tests/` pytest, `infra/` terraform"]
- [For a monorepo: name the apps and shared packages.]

## Commands

```sh
[build command]        # e.g. make build
[test command]         # e.g. pytest -q  (and: how to run ONE test)
[run/dev command]      # e.g. npm run dev -- --port 3000
[lint/format command]  # e.g. make fmt
```

## Conventions

[ONLY conventions that differ from language/framework defaults. One real example
beats a paragraph. Let a formatter/linter own the rest.]

## Testing

[Preferred runner, how to run a single test, coverage expectation.]

## Git workflow

[Branch naming, commit message format, PR/review expectations.]

## Boundaries

- ✅ **Always**: [e.g. run the formatter before committing; add a test with each fix]
- ⚠️ **Ask first**: [e.g. adding a dependency; changing the public API; a DB migration]
- 🚫 **Never**: [e.g. commit secrets; edit generated files; force-push main]

## Deeper docs (read when relevant)

- `[docs/foo.md]` — [one line: what it covers and when to read it]
