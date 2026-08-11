# Structure & templates

Canonical structure for a root CLAUDE.md and a nested one. Copyable skeletons
live in [`../assets/root-CLAUDE.md`](../assets/root-CLAUDE.md) and
[`../assets/nested-CLAUDE.md`](../assets/nested-CLAUDE.md); this file explains
what goes in each section and why, and what to leave out.

Synthesized from Anthropic's include/exclude table, HumanLayer's WHY/WHAT/HOW
framing, and GitHub's "six core areas" from 2,500+ repos. Section order is a
recommendation, not a lint-enforced requirement — AGENTS.md explicitly allows any
headings. Adapt it; don't pad the file to hit every section.

## Root CLAUDE.md — recommended section order

1. **Project identity** — one short paragraph: what this is, in plain language
   (the "WHY"). Orientation, not marketing. 1–3 sentences.
2. **Tech stack / architecture map** — the "WHAT": stack *with versions* ("React
   18 + TypeScript + Vite", not "a React app"), directory layout, module
   boundaries. Most valuable in monorepos — name the apps and shared packages.
3. **Build / test / run commands** — put these **early**; it's the highest-signal
   section. Include flags and options, not just tool names (`npm run test -- --watch`,
   not "run the tests"). Commands the agent cannot guess are Anthropic's #1
   include-column item.
4. **Conventions that differ from language/framework defaults *only*** — not a
   restatement of general best practice. One real code snippet beats a paragraph.
   If a formatter/linter can enforce it, let it — keep only the handful of
   non-default rules a tool can't express.
5. **Testing** — preferred runner, how to run a *single* test, coverage
   expectations.
6. **Repository etiquette / git workflow** — branch naming, commit format, PR
   conventions.
7. **Boundaries / constraints** — the highest-value section in GitHub's data.
   Use the three-tier block (below). This is where "never touch the generated
   client", "ask before a schema migration", "always run the formatter" live.
8. **Pointers to deeper docs (progressive disclosure)** — a short list of
   self-describing files with one-line descriptions ("`docs/db-schema.md` — table
   layout; read before touching migrations"), telling the agent to read them only
   when relevant. Do not inline their contents.
9. **(Optional) maintainer notes in HTML comments** — block-level HTML comments
   are stripped before the file enters context, so `<!-- TODO: revisit after v2 -->`
   costs zero tokens and is a free human-only channel.

### The boundaries block — ready to paste

GitHub's data found this three-tier format in the most successful files. It is
the single most reusable fragment here:

```markdown
## Boundaries

- ✅ **Always**: run `make fmt` before committing; add a test with every bug fix.
- ⚠️ **Ask first**: adding a dependency; changing the public API; a DB migration.
- 🚫 **Never**: commit secrets; edit generated files in `gen/`; force-push `main`.
```

### Exclude from the root file

Anthropic's exclude column + HumanLayer's "Claude is not an expensive linter":

- Anything the agent can infer by reading the code.
- Standard language/framework idioms ("use async/await", "prefer const").
- Detailed API docs — **link** instead.
- Volatile / frequently-changing info (version numbers, current sprint, counts).
- Long tutorials, file-by-file walkthroughs.
- Generic platitudes ("write clean code", "be thorough").
- Full code-style rulebooks a formatter/linter should own — wire a hook instead.

## Nested / per-directory CLAUDE.md — what changes

A nested `CLAUDE.md` (e.g. `src/infra/panic/CLAUDE.md`) loads **on demand** — only
when the agent touches a file in that subtree — not at session start. Two
consequences:

- **It can be denser than the root file** without taxing unrelated sessions.
  Deep, specific detail (a subsystem's non-obvious invariants, async-signal-safety
  rules) belongs here, not in the root.
- **Scope, don't restate.** Include *only* what's specific to this directory.
  Project-wide conventions stay in the root and are inherited automatically
  (root-to-cwd concatenation). Restating them triggers the duplicate-ancestor
  lint rule.

Open a nested file with one line stating its jurisdiction ("This file governs
`src/infra/lock/` only.") so a human or model immediately knows the scope. Then
use the same identity → commands → conventions → constraints shape as the root,
scoped to the subtree.

## `.claude/rules/` files

A rule file is topic-coherent, cross-cutting guidance (a fail-fast policy, a
commit convention) that isn't tied to one directory. Key mechanic:

- **No `paths:` frontmatter → loaded in every session.** Fine for genuinely
  universal rules (git conventions).
- **With a `paths:` glob → loaded only for matching files.** Use this for
  language/type-specific rules so a pure-docs or pure-Python session doesn't pay
  for C-only style rules.

```markdown
---
paths: ["src/**/*.c", "src/**/*.h"]
---

# C style
...
```

Same include/exclude discipline as CLAUDE.md applies — a rule file is just
context loaded conditionally.

## How this maps to AGENTS.md

`AGENTS.md` is the same idea under a cross-vendor filename (backed by a working
group now under the Linux Foundation). The content advice transfers directly.
Differences that matter: Claude Code reads `CLAUDE.md`, **not** `AGENTS.md`,
natively — don't assume a rename works for Claude Code. Precedence/merge semantics
differ per tool (Claude Code concatenates root→cwd; the AGENTS.md draft defines a
named precedence chain; GitHub Copilot's formats are purely additive). Don't port
a precedence mental model from one tool to another — see the anti-patterns table.
